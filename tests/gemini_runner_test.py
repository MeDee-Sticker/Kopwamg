#!/usr/bin/env python3
"""ทดสอบตัวรันพร้อมต์กับ Gemini (scripts/gemini_prompt_runner.py) ด้วยเซิร์ฟเวอร์จำลอง

ไม่มีการเชื่อมต่อ Google จริง: ใช้ HTTP server ในเครื่องแทน generativelanguage.googleapis.com
ครอบคลุม: รูปร่างคำขอ (โมเดล, ส่วนหัว API key, responseMimeType JSON), การแยก JSON ออกจากคำตอบ,
ด่านคำต้องห้าม/ฟิลด์ครบ/ความยาวแคปชัน, retry เมื่อโดน 429, โมเดลไม่มีจริง, และ CLI

    python3 tests/gemini_runner_test.py
"""

from __future__ import annotations

import contextlib
import http.server
import io
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gemini_prompt_runner as gem  # noqa: E402

RUNNER = ROOT / "scripts" / "gemini_prompt_runner.py"
DUMMY_KEY = "DUMMY_SECRET_KEY_FOR_TESTS"

failures: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {extra}" if extra else ""))
    if not ok:
        failures.append(name)


def capture(func, *args, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    value = None
    error = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            value = func(*args, **kwargs)
        except SystemExit as exc:
            error = str(exc)
    return value, out.getvalue() + err.getvalue(), error


GOOD_DRAFT = {
    "voice_over": "ถ้าคุณเคยทำคอนเทนต์แล้วไม่มีคนดู ลองเช็ก 3 ข้อนี้ก่อน",
    "onscreen_text": [{"time": "0-3", "text": "ทำไมไม่มีคนดู"}, {"time": "3-10", "text": "เช็ก 3 ข้อ"}],
    "shot_list": [{"time": "0-3", "shot": "hook", "detail": "พูดตรงกล้อง"}, {"time": "3-10", "shot": "teach", "detail": "ชี้ที่หน้าจอ"}],
    "caption": "3 ข้อที่ทำให้คอนเทนต์ไม่มีคนดู #Kopwang",
    "hashtags": ["#Kopwang", "#DAY1"],
}


class FakeGemini(http.server.BaseHTTPRequestHandler):
    posts: list[dict] = []
    gets: list[str] = []
    mode = "ok"
    models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
    draft: dict = GOOD_DRAFT
    fail_times = 1

    def log_message(self, *args) -> None:  # ปิด log ของเซิร์ฟเวอร์
        return

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        type(self).gets.append(self.path)
        if type(self).mode == "unauthorized":
            self._json({"error": {"message": "API key not valid. Please pass a valid API key."}}, 400)
            return
        if self.path.startswith("/v1beta/models"):
            self._json({"models": [{"name": f"models/{m}", "supportedGenerationMethods": ["generateContent"]} for m in self.models]})
        else:
            self._json({"error": {"message": "not found"}}, 404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        type(self).posts.append(
            {
                "path": self.path,
                "key": self.headers.get("x-goog-api-key"),
                "body": json.loads(raw) if raw.strip() else {},
            }
        )
        model = self.path.split("/models/")[-1].split(":")[0]
        if model not in type(self).models:
            self._json({"error": {"message": f"models/{model} is not found for API version v1beta"}}, 404)
            return
        if type(self).mode == "retry_429":
            if len(type(self).posts) <= type(self).fail_times:
                self._json({"error": {"message": "quota exceeded"}}, 429)
                return
        if type(self).mode == "unauthorized":
            self._json({"error": {"message": "API key not valid. Please pass a valid API key."}}, 400)
            return
        if type(self).mode == "invalid_json":
            self._json({"candidates": [{"content": {"parts": [{"text": "ขอโทษครับ ผมไม่สามารถ..."}]}}]})
            return
        draft = type(self).draft
        if type(self).mode == "banned_then_ok" and len(type(self).posts) == 1:
            draft = {**GOOD_DRAFT, "caption": "ทำตามแล้วการันตีรายได้แน่นอน #Kopwang"}
        if type(self).mode == "always_banned":
            draft = {**GOOD_DRAFT, "voice_over": "ระบบนี้การันตีรายได้จริง ทำตามได้เลย"}
        self._json(
            {
                "candidates": [{"content": {"parts": [{"text": json.dumps(draft, ensure_ascii=False)}]}}],
                "usageMetadata": {"promptTokenCount": 1200, "candidatesTokenCount": 260, "totalTokenCount": 1460},
            }
        )


def env_with(key: str = DUMMY_KEY) -> dict:
    return {"GEMINI_API_KEY": key}


def phase_payload(config: dict) -> None:
    print("== โครงคำขอ ==")
    prompts = gem.load_prompts()
    day = gem.find_day(prompts, 1)
    payload = gem.build_payload(day["platforms"]["tiktok"]["script_prompt"])
    check("มี systemInstruction และ contents", "systemInstruction" in payload and payload["contents"][0]["parts"][0]["text"])
    check("บังคับผลเป็น JSON", payload["generationConfig"]["responseMimeType"] == "application/json")
    check(
        "พร้อมต์ที่ส่งคือพร้อมต์จริงของวันนั้น",
        "ปักตะกร้า" in payload["contents"][0]["parts"][0]["text"]
        and day["theme"] in payload["contents"][0]["parts"][0]["text"],
    )
    check("ห้ามคำสัญญารายได้อยู่ใน system instruction", "ห้ามใช้คำสัญญารายได้" in payload["systemInstruction"]["parts"][0]["text"])

    problems = gem.validate_output(GOOD_DRAFT, "tiktok", config)
    check("ด่านตรวจผ่านกับผลที่ถูกต้อง", not problems, "; ".join(problems))
    flagged = gem.validate_output({**GOOD_DRAFT, "caption": "ทำแล้วรวยเร็วแน่นอน #Kopwang"}, "tiktok", config)
    check("ด่านตรวจจับคำต้องห้าม", any("คำต้องห้าม" in p for p in flagged), "; ".join(flagged))
    missing = gem.validate_output({"voice_over": "x"}, "tiktok", config)
    check("ด่านตรวจจับฟิลด์ที่ขาด", any("ขาดฟิลด์" in p for p in missing))
    too_long = gem.validate_output({**GOOD_DRAFT, "caption": "ก" * 3000}, "shopee", config)
    check("ด่านตรวจจับแคปชันยาวเกินเพดานแพลตฟอร์ม", any("เกินเพดาน" in p for p in too_long))
    parsed = gem.parse_model_json("```json\n" + json.dumps(GOOD_DRAFT, ensure_ascii=False) + "\n```")
    check("แกะ JSON ที่โมเดลห่อ code fence ได้", parsed == GOOD_DRAFT)


def phase_http(server: str, config: dict) -> None:
    print("\n== เรียก API จำลอง ==")
    gem.API_BASE = f"{server}/v1beta"
    prompts = gem.load_prompts()
    day = gem.find_day(prompts, 1)
    original_log, original_sleep = gem.RUN_LOG, gem.time.sleep
    gem.time.sleep = lambda _seconds: None

    with tempfile.TemporaryDirectory() as tmp_name:
        outdir = Path(tmp_name) / "ai-drafts"
        gem.RUN_LOG = Path(tmp_name) / "runs.jsonl"
        try:
            FakeGemini.mode = "ok"
            FakeGemini.posts = []
            rc, output, error = capture(gem.cmd_run, env_with(), day, "tiktok", "gemini-3.8-flash", config, outdir)
            check("รันสำเร็จและเขียนไฟล์", rc == 0 and error is None, error or output.strip().splitlines()[-1:] or "")
            md = outdir / "day-01-tiktok.md"
            js = outdir / "day-01-tiktok.json"
            check("ได้ไฟล์ .md และ .json ตามชื่อวันที่/แพลตฟอร์ม", md.is_file() and js.is_file(), str(md))
            record = json.loads(js.read_text(encoding="utf-8"))
            check("บันทึกโมเดล โทเคน และร่างไว้ครบ", record["model"] == "gemini-3.8-flash" and record["usage"]["total_tokens"] == 1460 and record["draft"] == GOOD_DRAFT)
            text = md.read_text(encoding="utf-8")
            check("ไฟล์ md มีสคริปต์ แคปชัน และคำเตือนให้ตรวจก่อนใช้", all(p in text for p in ("voice over", "แคปชัน", "ต้องตรวจก่อนใช้")))
            check("เขียน log การรัน", gem.RUN_LOG.read_text(encoding="utf-8").strip().startswith("{"))
            request = FakeGemini.posts[-1]
            check("ยิงไปที่โมเดลที่เลือก", request["path"].endswith("/models/gemini-3.8-flash:generateContent"), request["path"])
            check("ส่ง key ในส่วนหัว x-goog-api-key", request["key"] == DUMMY_KEY)
            check("ขอ JSON และส่งพร้อมต์ของวันนั้นจริง", request["body"]["generationConfig"]["responseMimeType"] == "application/json" and "ปักตะกร้า" in request["body"]["contents"][0]["parts"][0]["text"])

            # 429 แล้วสำเร็จ → ต้องลองซ้ำให้เอง
            FakeGemini.mode = "retry_429"
            FakeGemini.posts = []
            rc, output, error = capture(gem.cmd_run, env_with(), day, "tiktok", "gemini-3.8-flash", config, outdir)
            check("ลองซ้ำเมื่อโดน 429 แล้วสำเร็จ", rc == 0 and len(FakeGemini.posts) == 2, f"{len(FakeGemini.posts)} คำขอ")

            # result ที่มีคำต้องห้าม → ต้องไม่เขียนไฟล์
            FakeGemini.mode = "ok"
            FakeGemini.draft = {**GOOD_DRAFT, "caption": "ทำตามแล้วรวยแน่นอน #Kopwang"}
            before = sorted(p.name for p in outdir.iterdir())
            rc, output, error = capture(gem.cmd_run, env_with(), day, "tiktok", "gemini-3.8-flash", config, outdir)
            check("ผลที่มีคำต้องห้ามถูกปฏิเสธ", rc == 1 and "คำต้องห้าม" in output, output.strip().splitlines()[:2])
            check("ไม่เขียนไฟล์ทับเมื่อผลไม่ผ่านด่าน", sorted(p.name for p in outdir.iterdir()) == before)
            FakeGemini.draft = GOOD_DRAFT

            # รอบแรกติดคำต้องห้าม → ต้องลองใหม่เองพร้อมย้ำกติกา
            FakeGemini.mode = "banned_then_ok"
            FakeGemini.posts = []
            rc, output, error = capture(gem.cmd_run, env_with(), day, "tiktok", "gemini-3.8-flash", config, outdir)
            check("ลองใหม่เองเมื่อคำตอบแรกติดคำต้องห้าม", rc == 0 and len(FakeGemini.posts) == 2, f"{len(FakeGemini.posts)} คำขอ")
            check("รายงานว่าลองใหม่พร้อมย้ำกติกา", "ลองใหม่พร้อมย้ำกติกา" in output, output.strip().splitlines()[:2])
            check(
                "คำขอรอบสองเติมคำอธิบายข้อห้าม",
                "คำตอบก่อนหน้าถูกปฏิเสธ" in FakeGemini.posts[-1]["body"]["contents"][0]["parts"][0]["text"],
            )

            # ติดคำต้องห้ามทั้งสองรอบ → ต้องไม่เขียนไฟล์ และบอกบริบทให้เห็น
            FakeGemini.mode = "always_banned"
            FakeGemini.posts = []
            before = sorted(p.name for p in outdir.iterdir())
            rc, output, error = capture(gem.cmd_run, env_with(), day, "tiktok", "gemini-3.8-flash", config, outdir)
            check("ติดคำต้องห้ามทั้งสองรอบ → ไม่เขียนไฟล์", rc == 1 and sorted(p.name for p in outdir.iterdir()) == before)
            check("แสดงบริบทของคำต้องห้าม", "บริบท:" in output and "การันตีรายได้" in output, output.strip().splitlines()[-2:])

            # JSON พัง
            FakeGemini.mode = "invalid_json"
            rc, output, error = capture(gem.cmd_run, env_with(), day, "tiktok", "gemini-3.8-flash", config, outdir)
            check("จับคำตอบที่ไม่ใช่ JSON พร้อมบอกสาเหตุ", error is not None and "JSON" in error, (error or "")[:90])

            # โมเดลไม่มีจริง
            rc, output, error = capture(gem.cmd_run, env_with(), day, "tiktok", "gemini-does-not-exist", config, outdir)
            check("โมเดลไม่มีจริงบอกให้ใช้ --list-models", error is not None and "--list-models" in error, (error or "")[:90])

            # key ไม่ถูกต้อง → ต้องไม่หลุด key ออกมาในข้อความ
            FakeGemini.mode = "unauthorized"
            rc, output, error = capture(gem.cmd_run, env_with(), day, "tiktok", "gemini-3.8-flash", config, outdir)
            check("แจ้ง error จาก API ตามที่ได้", error is not None and "API key not valid" in error, (error or "")[:90])
            check("ไม่พิมพ์ค่า API key ออกมา", DUMMY_KEY not in (output + (error or "")))
        finally:
            gem.RUN_LOG = original_log
            gem.time.sleep = original_sleep
            FakeGemini.mode = "ok"
            FakeGemini.draft = GOOD_DRAFT

    # ไม่มี key → ต้องบอกวิธีตั้งค่า
    _, output, error = capture(gem.cmd_run, {}, day, "tiktok", "gemini-3.8-flash", config, Path(tempfile.gettempdir()) / "no-key")
    check("ไม่มี key แล้วบอกวิธีตั้งค่า", error is not None and "GEMINI_API_KEY" in error and "aistudio.google.com" in error, (error or "")[:80])
    _, output, error = capture(gem.cmd_list_models, {})
    check("--list-models ไม่มี key แล้วแจ้งชัดเจน", error is not None and "GEMINI_API_KEY" in error)

    models = gem.list_models(DUMMY_KEY)
    check("อ่านรายการโมเดลจาก API ได้", models == FakeGemini.models, str(models))

    # key ใช้ไม่ได้ → --list-models ต้องจบด้วยข้อความ ไม่ใช่ traceback
    FakeGemini.mode = "unauthorized"
    try:
        _, _, error = capture(gem.cmd_list_models, env_with())
    finally:
        FakeGemini.mode = "ok"
    check("key ใช้ไม่ได้ → --list-models แจ้ง error ชัดเจน", error is not None and "API key not valid" in error, (error or "")[:80])
    check("--list-models ไม่หลุด key ออกมา", DUMMY_KEY not in (error or ""))


def phase_cli(server: str) -> None:
    print("\n== CLI ==")
    import subprocess

    env = {k: v for k, v in os.environ.items() if not k.startswith(("GEMINI_", "GOOGLE_"))}
    env.update(
        {
            "GEMINI_API_BASE_URL": f"{server}/v1beta",
            "GEMINI_API_KEY": DUMMY_KEY,
            "GEMINI_RUN_LOG": str(Path(tempfile.mkdtemp()) / "gemini-runs.jsonl"),
        }
    )

    with tempfile.TemporaryDirectory() as tmp_name:
        outdir = Path(tmp_name) / "ai-drafts"
        proc = subprocess.run(
            [sys.executable, str(RUNNER), "--day", "2", "--platform", "facebook", "--outdir", str(outdir)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        check("CLI รันจริงจนได้ไฟล์", proc.returncode == 0 and (outdir / "day-02-facebook.md").is_file(), (proc.stdout + proc.stderr).strip()[-120:])
        check("CLI ไม่พิมพ์ key", DUMMY_KEY not in proc.stdout + proc.stderr)

    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--day", "1", "--platform", "tiktok", "--dry-run"],
        cwd=str(ROOT),
        env={k: v for k, v in os.environ.items() if not k.startswith(("GEMINI_", "GOOGLE_"))},
        capture_output=True,
        text=True,
        timeout=120,
    )
    check("--dry-run รันได้โดยไม่ต้องมี key", proc.returncode == 0, f"exit {proc.returncode}")
    check("--dry-run ไม่ยิง API และบอกว่าไม่เขียนไฟล์", "ไม่ยิง API และไม่เขียนไฟล์" in proc.stdout)
    body = subprocess.run(
        [sys.executable, str(RUNNER), "--day", "1", "--platform", "tiktok", "--dry-run", "--format", "body"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    check("--dry-run --format body ให้ JSON ที่ใช้ส่งต่อได้", json.loads(body.stdout)["generationConfig"]["responseMimeType"] == "application/json")

    proc = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    check("ไม่ระบุ --day แล้วใช้ผิด → exit 2", proc.returncode == 2, f"exit {proc.returncode}")


def main() -> int:
    config = json.loads(gem.SYSTEM_FILE.read_text(encoding="utf-8"))
    phase_payload(config)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeGemini)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    original_base = gem.API_BASE
    try:
        phase_http(url, config)
        phase_cli(url)
    finally:
        gem.API_BASE = original_base
        server.shutdown()

    print()
    if failures:
        print(f"{len(failures)} รายการไม่ผ่าน")
        return 1
    print("ผ่านทั้งหมด")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
