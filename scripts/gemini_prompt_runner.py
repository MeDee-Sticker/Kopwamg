#!/usr/bin/env python3
"""Kopwang — รันพร้อมต์จากระบบพร้อมต์กับ Google Gemini จริง แล้วเก็บผลไว้ตรวจ

อ่านพร้อมต์ที่สร้างไว้แล้วใน prompts/generated/ ส่งเข้า Gemini (generateContent) ขอผลเป็น JSON
ตรวจด่านความปลอดภัย (คำสัญญารายได้ ฟิลด์ครบ ความยาวแคปชัน) แล้วเขียนผลลง content/ai-drafts/

ตั้งค่า API key (ห้ามคอมมิต):
    cp .env.example .env      # แล้วเติม GEMINI_API_KEY=...
    # หรือ export GEMINI_API_KEY=...

ตัวอย่าง
--------
    # ดูชื่อโมเดลที่บัญชีนี้ใช้ generateContent ได้ (ต้องมี key)
    python3 scripts/gemini_prompt_runner.py --list-models

    # ดู payload + คำสั่ง curl ที่จะส่งไป โดยไม่ยิง API จริง
    python3 scripts/gemini_prompt_runner.py --day 1 --platform tiktok --dry-run

    # รันจริง 1 งาน → content/ai-drafts/day-01-tiktok.{md,json}
    python3 scripts/gemini_prompt_runner.py --day 1 --platform tiktok

    # เลือกโมเดลเอง
    python3 scripts/gemini_prompt_runner.py --day 1 --platform facebook --model gemini-3.8-flash

หมายเหตุ: ตัวรันนี้รองรับขั้น "สคริปต์" (ข้อความ) เท่านั้น — พร้อมต์ภาพ/วิดีโอในไฟล์เดียวกัน
เป็นของโมเดลสร้างภาพ/วิดีโอ (Midjourney, Veo และอื่น ๆ) ซึ่งมี API คนละแบบ
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
PROMPTS_FILE = ROOT / "prompts" / "generated" / "prompts.json"
SYSTEM_FILE = ROOT / "prompts" / "system.json"
OUTDIR = ROOT / "content" / "ai-drafts"
RUN_LOG = Path(os.environ.get("GEMINI_RUN_LOG", ROOT / "state" / "gemini-runs.jsonl"))

API_BASE = os.environ.get("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
MODEL_CANDIDATES = ("gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-flash-latest")
BANGKOK = timezone(timedelta(hours=7))
PLATFORMS = ("facebook", "tiktok", "shopee")
REQUIRED_FIELDS = ("voice_over", "onscreen_text", "shot_list", "caption", "hashtags")
MAX_OUTPUT_TOKENS = 4096
MAX_ATTEMPTS = 2  # ถ้าคำตอบติดคำต้องห้าม ให้ลองใหม่พร้อมย้ำกติกาอีกครั้ง

SYSTEM_INSTRUCTION = (
    "คุณเป็นนักเขียนคอนเทนต์ให้แบรนด์ Kopwang (ระบบสร้างรายได้ใน 30 วัน) "
    "เขียนภาษาไทยที่พูดได้จริงตามเวลาที่กำหนด ตอบเป็น JSON ตามโครงที่ผู้ใช้ระบุเท่านั้น "
    "ห้ามใช้คำสัญญารายได้หรือผลลัพธ์เกินจริง ห้ามอ้างตัวเลขที่ไม่มีในข้อมูลที่ให้ "
    "ห้ามใส่ข้อความอื่นนอก JSON"
)


class GeminiError(RuntimeError):
    """ข้อผิดพลาดจาก Gemini ที่ผู้เรียกจัดการได้ (แยกจากบั๊กในสคริปต์)"""

    def __init__(self, status: int | None, message: str, *, network: bool = False):
        self.status = status
        self.message = message
        self.network = network
        super().__init__(message)

    @property
    def model_not_found(self) -> bool:
        return self.status == 404 or "not found" in self.message.lower()


# --------------------------------------------------------------------------- helpers


def load_env(path: Path = ENV_FILE) -> dict:
    """อ่าน .env แบบง่าย — ไม่ใช้ไลบรารีเพิ่ม และไม่พิมพ์ค่าใด ๆ ออกมา"""
    values = dict(os.environ)
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and val and not values.get(key):
                values[key] = val
    return values


def api_key(env: dict) -> str:
    return env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY") or env.get("GOOGLE_GENAI_API_KEY") or ""


def graph_path(path: str) -> str:
    return f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"


def display(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_prompts() -> dict:
    if not PROMPTS_FILE.exists():
        raise SystemExit(
            f"ยังไม่มี {display(PROMPTS_FILE)} — รัน: python3 scripts/build_prompts.py"
        )
    return json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))


def find_day(prompts: dict, day: int) -> dict:
    for item in prompts.get("days", []):
        if item.get("day") == day:
            return item
    raise SystemExit(f"ไม่พบวันที่ {day} ใน {display(PROMPTS_FILE)} (มี 1-{len(prompts.get('days', []))})")


# --------------------------------------------------------------------------- HTTP


def http_json(url: str, *, key: str, payload: dict | None = None, method: str = "GET") -> dict:
    """เรียก Gemini REST พร้อม backoff — โยน GeminiError ให้ผู้เรียกตัดสินใจ"""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if key:
        headers["x-goog-api-key"] = key

    delay = 2.0
    for attempt in range(4):
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            message = body
            try:
                message = json.loads(body).get("error", {}).get("message", body)
            except json.JSONDecodeError:
                pass
            retryable = exc.code in (429, 500, 502, 503)
            if retryable and attempt < 3:
                print(f"  [retry {attempt + 1}/3] HTTP {exc.code} — รอ {delay:.0f}s", file=sys.stderr)
                time.sleep(delay)
                delay *= 2
                continue
            raise GeminiError(exc.code, str(message)) from None
        except urllib.error.URLError as exc:
            if attempt < 3:
                print(f"  [retry {attempt + 1}/3] network: {exc} — รอ {delay:.0f}s", file=sys.stderr)
                time.sleep(delay)
                delay *= 2
                continue
            raise GeminiError(None, f"เชื่อมต่อ Gemini ไม่ได้: {exc}", network=True) from None
    raise GeminiError(None, "เรียก Gemini ไม่สำเร็จหลังลองซ้ำ")


def list_models(key: str) -> list[str]:
    models: list[str] = []
    page = ""
    for _ in range(5):
        url = graph_path("models?pageSize=200" + (f"&pageToken={page}" if page else ""))
        data = http_json(url, key=key)
        for model in data.get("models", []):
            methods = model.get("supportedGenerationMethods") or model.get("supportedActions") or []
            if "generateContent" in methods:
                models.append(str(model.get("name", "")).replace("models/", ""))
        page = data.get("nextPageToken", "")
        if not page:
            break
    return models


# --------------------------------------------------------------------------- payload / parsing


def build_payload(script_prompt: str) -> dict:
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": script_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }


def extract_text(response: dict) -> str:
    parts: list[str] = []
    for candidate in response.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if isinstance(part.get("text"), str):
                parts.append(part["text"])
    return "\n".join(parts).strip()


def parse_model_json(text: str) -> dict:
    cleaned = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.S)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        snippet = cleaned[:300].replace("\n", " ")
        raise SystemExit(f"โมเดลไม่ได้ตอบเป็น JSON ที่อ่านได้ ({exc})\n--- ต้นข้อความ ---\n{snippet}") from None
    if not isinstance(data, dict):
        raise SystemExit(f"โมเดลตอบ JSON ชนิด {type(data).__name__} แทน object")
    return data


def validate_output(data: dict, platform: str, config: dict) -> list[str]:
    """คืนรายการปัญหา — ว่างเปล่าคือผ่าน"""
    problems: list[str] = []
    missing = [key for key in REQUIRED_FIELDS if key not in data]
    if missing:
        problems.append("ขาดฟิลด์: " + ", ".join(missing))
    for key in ("voice_over", "caption"):
        if key in data and not (isinstance(data[key], str) and data[key].strip()):
            problems.append(f"{key} ต้องเป็นข้อความที่ไม่ว่าง")
    for key in ("onscreen_text", "shot_list"):
        value = data.get(key)
        if not isinstance(value, list) or not value:
            problems.append(f"{key} ต้องเป็น list ที่มีอย่างน้อย 1 รายการ")
    if not isinstance(data.get("hashtags"), list) or not data.get("hashtags"):
        problems.append("hashtags ต้องเป็น list ที่มีอย่างน้อย 1 อัน")

    strings: list[str] = []
    for value in data.values():
        if isinstance(value, str):
            strings.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    strings.append(item)
                elif isinstance(item, dict):
                    strings.extend(str(v) for v in item.values())
    banned = [word for word in config["safety"]["banned_claims"] if any(word in text for text in strings)]
    if banned:
        problems.append("พบคำต้องห้าม: " + ", ".join(banned))

    limit = config["platforms"][platform]["caption_limit"]
    caption = data.get("caption", "")
    if isinstance(caption, str) and len(caption) > limit:
        problems.append(f"แคปชันยาว {len(caption)} ตัวอักษร เกินเพดาน {limit} ของแพลตฟอร์ม")
    return problems


def banned_context(data: dict, config: dict, limit: int = 3) -> list[str]:
    """คืนประโยคที่มีคำต้องห้าม เพื่อให้เห็นว่าทำไมถูกปฏิเสธ"""
    banned = config["safety"]["banned_claims"]
    texts: list[str] = []
    for value in data.values():
        if isinstance(value, str):
            texts.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict):
                    texts.extend(str(v) for v in item.values() if isinstance(v, str))
    found: list[str] = []
    for text in texts:
        parts = re.split(r"(?<=[.!?\n])\s+|\n", text)
        for sentence in parts:
            hits = [word for word in banned if word in sentence]
            if hits:
                found.append(f"{'/'.join(hits)} → {sentence.strip()[:140]}")
    return found[:limit]


CORRECTION_NOTE = (
    "\n\nคำตอบก่อนหน้าถูกปฏิเสธเพราะมีคำต้องห้ามในรายการข้อห้าม ให้เขียนใหม่ทั้งชุดโดยไม่ใช้คำต่อไปนี้เลย "
    "แม้จะอยู่ในประโยคปฏิเสธหรือคำอธิบาย: {words} "
    "ถ้าต้องการบอกว่าผลลัพธ์ไม่รับประกัน ให้ใช้คำอื่น เช่น 'ไม่มีข้อรับประกันผลลัพธ์' หรือ 'ผลลัพธ์ขึ้นอยู่กับแต่ละคน' "
    "และตอบเป็น JSON ตามโครงเดิม"
)


def usage_of(response: dict) -> dict:
    usage = response.get("usageMetadata", {}) or {}
    return {
        "prompt_tokens": usage.get("promptTokenCount"),
        "output_tokens": usage.get("candidatesTokenCount"),
        "total_tokens": usage.get("totalTokenCount"),
    }


def write_outputs(outdir: Path, day: dict, platform: str, data: dict, meta: dict) -> tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"day-{day['day']:02d}-{platform}"
    json_path = outdir / f"{stem}.json"
    md_path = outdir / f"{stem}.md"

    record = {
        "day": day["day"],
        "date": day.get("date"),
        "platform": platform,
        "theme": day.get("theme"),
        "model": meta["model"],
        "created_at": meta["created_at"],
        "usage": meta["usage"],
        "draft": data,
    }
    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    onscreen = data.get("onscreen_text") or []
    shots = data.get("shot_list") or []
    hashtags = " ".join(str(h) for h in (data.get("hashtags") or []))
    lines = [
        f"# ร่างจาก AI — วันที่ {day['day']:02d} · {platform} · {day.get('theme', '')}",
        "",
        f"- สร้างเมื่อ: {meta['created_at']} · โมเดล: {meta['model']}",
        f"- โทเคน: {meta['usage'].get('total_tokens', '-')} (prompt {meta['usage'].get('prompt_tokens', '-')} / output {meta['usage'].get('output_tokens', '-')})",
        "- **ต้องตรวจก่อนใช้:** อ่านออกเสียงจริง แก้คำให้เป็นเสียงของแบรนด์ และตรวจข้อห้ามใน prompts/system.json อีกครั้ง",
        "- ไฟล์นี้ไม่ถูกนับเป็นฉบับร่างพร้อมโพสต์ — ถ้าจะใช้จริงให้ย้ายไป `content/drafts/` พร้อมเช็กลิสต์",
        "",
        "## สคริปต์พูด (voice over)",
        "",
        "```text",
        data.get("voice_over", ""),
        "```",
        "",
        "## ข้อความบนจอ",
        "",
        "| เวลา | ข้อความ |",
        "|---|---|",
    ]
    for item in onscreen:
        lines.append(f"| {item.get('time', '')} | {item.get('text', '')} |")
    lines += ["", "## ลำดับภาพ", "", "| เวลา | ช็อต | รายละเอียด |", "|---|---|---|"]
    for item in shots:
        lines.append(f"| {item.get('time', '')} | {item.get('shot', '')} | {item.get('detail', '')} |")
    lines += [
        "",
        "## แคปชัน",
        "",
        "```text",
        data.get("caption", ""),
        "```",
        "",
        f"แฮชแท็ก: {hashtags}",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, json_path


def log_run(meta: dict, md_path: Path, json_path: Path) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {**meta, "md": display(md_path), "json": display(json_path)}
    with RUN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- commands


def cmd_list_models(env: dict) -> int:
    key = api_key(env)
    if not key:
        raise SystemExit("ต้องมี GEMINI_API_KEY (หรือ GOOGLE_API_KEY) ใน .env ก่อนจึงจะดูรายการโมเดลได้")
    try:
        models = list_models(key)
    except GeminiError as exc:
        raise SystemExit(f"ดูรายการโมเดลไม่สำเร็จ: {exc.message}") from None
    if not models:
        print("ไม่พบโมเดลที่รองรับ generateContent")
        return 1
    print(f"โมเดลที่รองรับ generateContent ({len(models)} รายการ):")
    for name in models:
        marker = " ← แนะนำ" if name in MODEL_CANDIDATES else ""
        print(f"  - {name}{marker}")
    return 0


def cmd_dry_run(day: dict, platform: str, model: str) -> int:
    prompt = day["platforms"][platform]["script_prompt"]
    payload = build_payload(prompt)
    url = graph_path(f"models/{urllib.parse.quote(model, safe='')}:generateContent")
    print(f"โมเดล: {model}")
    print(f"ปลายทาง: {url}")
    print(f"ความยาวพร้อมต์: {len(prompt)} ตัวอักษร")
    print("\n--- header ---")
    print("x-goog-api-key: $GEMINI_API_KEY")
    print("Content-Type: application/json")
    print("\n--- body (JSON) ---")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("\n--- คำสั่ง curl (ไม่ต้องใช้สคริปต์ก็รันได้) ---")
    print(
        f"python3 scripts/gemini_prompt_runner.py --day {day['day']} --platform {platform} "
        "--dry-run --format body > /tmp/gemini-body.json\n"
        f"curl -X POST '{url}' \\\n"
        "  -H \"x-goog-api-key: $GEMINI_API_KEY\" \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  -d @/tmp/gemini-body.json"
    )
    print("\n(โหมด --dry-run ไม่ยิง API และไม่เขียนไฟล์)")
    return 0


def resolve_model(env: dict, explicit: str | None) -> str:
    if explicit:
        return explicit
    return env.get("GEMINI_MODEL") or MODEL_CANDIDATES[0]


def cmd_run(env: dict, day: dict, platform: str, model: str, config: dict, outdir: Path) -> int:
    key = api_key(env)
    if not key:
        raise SystemExit(
            "ยังไม่มี API key ของ Gemini\n"
            "ตั้งค่าได้ 2 ทาง (ห้ามคอมมิต):\n"
            "  1) สร้างไฟล์ .env แล้วใส่ GEMINI_API_KEY=...\n"
            "  2) export GEMINI_API_KEY=...\n"
            "ขอ key ได้ที่ https://aistudio.google.com/apikey"
        )

    prompt = day["platforms"][platform]["script_prompt"]
    url = graph_path(f"models/{urllib.parse.quote(model, safe='')}:generateContent")
    print(f"กำลังเรียก {model} สำหรับวันที่ {day['day']} · {platform} … ({len(prompt)} ตัวอักษร)")

    data: dict = {}
    response: dict = {}
    problems: list[str] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        payload = build_payload(prompt)
        if attempt > 1:
            words = ", ".join(config["safety"]["banned_claims"])
            payload["contents"][0]["parts"][0]["text"] += CORRECTION_NOTE.format(words=words)
            print("  คำตอบรอบแรกมีคำต้องห้าม — ลองใหม่พร้อมย้ำกติกา")
        try:
            response = http_json(url, key=key, payload=payload, method="POST")
        except GeminiError as exc:
            if exc.model_not_found:
                raise SystemExit(
                    f"ไม่พบโมเดล '{model}' กับบัญชีนี้ — ดูรายชื่อด้วย: "
                    "python3 scripts/gemini_prompt_runner.py --list-models"
                ) from None
            raise SystemExit(f"Gemini ตอบ error: {exc.message}") from None

        text = extract_text(response)
        if not text:
            raise SystemExit(f"Gemini ไม่ได้ส่งข้อความกลับมา: {json.dumps(response, ensure_ascii=False)[:300]}")
        data = parse_model_json(text)
        problems = validate_output(data, platform, config)
        if not problems:
            break
        if attempt == MAX_ATTEMPTS or not any("คำต้องห้าม" in item for item in problems):
            break

    if problems:
        print("ผลลัพธ์ไม่ผ่านด่านตรวจ — ยังไม่เขียนไฟล์:")
        for item in problems:
            print(f"  - {item}")
        for snippet in banned_context(data, config):
            print(f"    บริบท: {snippet}")
        print("ลองรันใหม่ หรือปรับพร้อมต์ใน prompts/system.json แล้วสร้างพร้อมต์ใหม่")
        return 1

    meta = {
        "day": day["day"],
        "platform": platform,
        "model": model,
        "created_at": datetime.now(BANGKOK).isoformat(timespec="seconds"),
        "usage": usage_of(response),
    }
    md_path, json_path = write_outputs(outdir, day, platform, data, meta)
    log_run(meta, md_path, json_path)
    print(f"✅ ผ่านด่านตรวจและบันทึกแล้ว:\n  - {display(md_path)}\n  - {display(json_path)}")
    tokens = meta["usage"].get("total_tokens")
    if tokens is not None:
        print(f"  โทเคนรวม: {tokens}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="รันพร้อมต์สคริปต์จาก prompts/generated/ กับ Google Gemini จริง",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--day", type=int, help="วันที่ในแคมเปญ (1-30)")
    parser.add_argument("--platform", choices=PLATFORMS, default="tiktok", help="แพลตฟอร์มของพร้อมต์")
    parser.add_argument("--model", help="โมเดล Gemini (ค่าเริ่มต้นจาก GEMINI_MODEL หรือ gemini-3.8-flash)")
    parser.add_argument("--outdir", type=Path, default=OUTDIR, help="โฟลเดอร์เก็บผลลัพธ์")
    parser.add_argument("--list-models", action="store_true", help="แสดงโมเดลที่บัญชีนี้ใช้ generateContent ได้")
    parser.add_argument("--dry-run", action="store_true", help="แสดง payload/คำสั่ง curl โดยไม่ยิง API")
    parser.add_argument(
        "--format",
        choices=("full", "body"),
        default="full",
        help="รูปแบบผลของ --dry-run (body = JSON body ล้วน สำหรับส่งใน curl)",
    )
    args = parser.parse_args()

    env = load_env()
    if args.list_models:
        return cmd_list_models(env)

    if args.day is None:
        parser.error("ต้องระบุ --day (หรือใช้ --list-models)")

    config = json.loads(SYSTEM_FILE.read_text(encoding="utf-8"))
    day = find_day(load_prompts(), args.day)
    model = resolve_model(env, args.model)

    if args.dry_run:
        if args.format == "body":
            print(json.dumps(build_payload(day["platforms"][args.platform]["script_prompt"]), ensure_ascii=False, indent=2))
            return 0
        return cmd_dry_run(day, args.platform, model)

    return cmd_run(env, day, args.platform, model, config, args.outdir)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:  # เช่นถูกตัดด้วย `| head`
        sys.stderr.close()
        raise SystemExit(0) from None
