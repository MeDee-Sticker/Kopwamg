#!/usr/bin/env python3
"""ทดสอบ API ของ scripts/dashboard_server.py แบบยิงเข้าเซิร์ฟเวอร์จริง (end-to-end)

ครอบคลุม: /api/status, /api/health, ไฟล์หน้าเว็บ, ปุ่มทดลองโพสต์, ปุ่มทดลองตั้งเวลา,
การกันโพสต์/ตั้งเวลาจริงเมื่อไม่ได้เปิดด้วย --live, การตรวจช่วงเวลาที่ Meta รับ,
การกัน CSRF, การตรวจค่าที่ส่งเข้ามา และการไม่รั่วค่าลับ

    python3 tests/dashboard_api_test.py

หมายเหตุความปลอดภัย: ถ้าเครื่องคุณมี .env ที่มีโทเคนจริงอยู่แล้ว
การทดสอบส่วน "โพสต์จริง" จะถูกข้ามอัตโนมัติ (รายงานว่า SKIP) เพื่อไม่ให้โพสต์ขึ้นเพจจริง
"""

from __future__ import annotations

import argparse
import contextlib
import http.client
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fb_scheduler as fb  # noqa: E402
SERVER = ROOT / "scripts" / "dashboard_server.py"
ENV_FILE = ROOT / ".env"
PORT = int(os.environ.get("KOPWANG_TEST_PORT", "3123"))
LOG_PATH = Path(tempfile.gettempdir()) / "kopwang-dashboard-server-test.log"

failures: list[str] = []
skips: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {extra}" if extra else ""))
    if not ok:
        failures.append(name)


def skip(name: str, why: str) -> None:
    print(f"SKIP  {name} — {why}")
    skips.append(name)


def request(method: str, path: str, body=None, headers: dict | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=30)
    payload = None
    hdrs = {}
    if body is not None:
        payload = body if isinstance(body, (bytes, str)) else json.dumps(body)
        hdrs["Content-Type"] = "application/json"
    if headers:
        hdrs.update(headers)
    conn.request(method, path, body=payload, headers=hdrs)
    response = conn.getresponse()
    raw = response.read().decode("utf-8", "replace")
    status = response.status
    ctype = response.getheader("Content-Type") or ""
    conn.close()
    return status, raw, ctype


def start_server(live: bool) -> subprocess.Popen:
    cmd = [sys.executable, str(SERVER), "--port", str(PORT)]
    if live:
        cmd.append("--live")
    log = open(LOG_PATH, "wb")
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
    deadline = time.time() + 25
    while time.time() < deadline:
        try:
            status, _, _ = request("GET", "/api/health")
            if status == 200:
                return proc
        except OSError:
            pass
        if proc.poll() is not None:
            break
        time.sleep(0.2)
    proc.terminate()
    print(f"เซิร์ฟเวอร์ไม่ตอบสนอง — ดู log ที่ {LOG_PATH}")
    print(LOG_PATH.read_text(encoding="utf-8", errors="replace")[-2000:])
    raise SystemExit(2)


def stop_server(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def credentials_present() -> bool:
    if not ENV_FILE.exists():
        return False
    values = {}
    for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    return bool(values.get("FB_PAGE_ID") and values.get("FB_PAGE_ACCESS_TOKEN"))


def json_body(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def phase_zero() -> None:
    """ตัวตัดสินช่วงเวลาตั้งเวลา (schedule_window) — ใช้ตัวเดียวกับทั้ง CLI และหน้าเว็บ"""
    now = fb.datetime.now(fb.BANGKOK)

    def row_at(moment):
        return {"date": moment.date().isoformat(), "post_time": moment.strftime("%H:%M")}

    check("อนาคต 2 ชั่วโมง → ตั้งเวลาได้ (ok)", fb.schedule_window(row_at(now + timedelta(hours=2)), now) == "ok")
    check("ผ่านมาแล้ว 1 ชั่วโมง → past", fb.schedule_window(row_at(now - timedelta(hours=1)), now) == "past")
    check(
        "อีก 5 นาที → past เพราะ Meta ต้องล่วงหน้าอย่างน้อย 10 นาที",
        fb.schedule_window(row_at(now + timedelta(minutes=5)), now) == "past",
        f"MIN_SCHEDULE_AHEAD_MINUTES={fb.MIN_SCHEDULE_AHEAD_MINUTES}",
    )
    check("อีก 31 วัน → too_far", fb.schedule_window(row_at(now + timedelta(days=31)), now) == "too_far")

    # วันที่ตั้งเวลาไว้แล้วต้องไม่ถูกตั้งซ้ำ (กันโพสต์ซ้ำในเพจ)
    original_state = fb.STATE_FILE
    fb.STATE_FILE = Path(tempfile.mkdtemp()) / "fb_state.json"
    try:
        fb.save_state(
            {
                "published": {},
                "scheduled": {"3": {"post_id": "x_y", "scheduled_for": "2026-10-18T12:00:00+07:00"}},
                "history": [],
            }
        )
        args = argparse.Namespace(
            day=None, today=False, from_day=3, to_day=3, schedule=True, draft=False, file=None, force=False, live=False
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fb.cmd_run({}, args)
        out = buf.getvalue()
        check(
            "วันที่ตั้งเวลาไว้แล้วถูกข้ามเมื่อสั่ง --schedule ซ้ำ",
            "ต้องทำ 0" in out and "ข้ามเพราะโพสต์หรือตั้งเวลาแล้ว 1" in out,
            out.strip().splitlines()[0] if out.strip() else "(ไม่มีผลลัพธ์)",
        )
    finally:
        fb.STATE_FILE = original_state


def phase_one() -> None:
    """เซิร์ฟเวอร์ปกติ (ไม่ได้เปิด --live)"""
    proc = start_server(live=False)
    try:
        status, raw, ctype = request("GET", "/api/status")
        payload = json_body(raw)
        check("GET /api/status ตอบ 200", status == 200, f"HTTP {status}")
        check("ตอบเป็น JSON", "application/json" in ctype, ctype)
        check(
            "มีคีย์ครบตามที่ตกลง และไม่มีคีย์เกิน",
            set(payload) == {
                "api",
                "credentials_ready",
                "live_allowed",
                "published",
                "scheduled",
                "drafts",
                "schedule_window",
            },
            str(sorted(payload)),
        )
        check("live_allowed = false เมื่อไม่เปิด --live", payload.get("live_allowed") is False)
        check("credentials_ready เป็นค่าบูลีน", isinstance(payload.get("credentials_ready"), bool))
        check("published/scheduled เป็น dict", isinstance(payload.get("published"), dict) and isinstance(payload.get("scheduled"), dict))
        check("drafts เป็น dict และยังว่าง", payload.get("drafts") == {}, str(payload.get("drafts")))

        windows = payload.get("schedule_window") or {}
        check(
            "schedule_window ครอบคลุมโพสต์ Facebook ทั้ง 30 วัน",
            len(windows) == 30 and all(str(i) in windows for i in range(1, 31)),
            f"ได้ {len(windows)} วัน",
        )
        check(
            "ทุกวันมีกำหนดเวลา (ISO) และผลตัดสินช่วงเวลา",
            all(
                set(v) == {"at", "window"} and v["window"] in {"ok", "past", "too_far"} and "T" in v["at"]
                for v in windows.values()
            ),
            str(sorted({v.get("window") for v in windows.values()})),
        )
        check(
            "ไม่ส่งค่าลับออกไป (ไม่มี EAA/TOKEN ในคำตอบ)",
            "EAA" not in raw and "TOKEN" not in raw.upper().replace("FB_PAGE_ACCESS_TOKEN", ""),
        )

        status, raw, _ = request("GET", "/api/health")
        check("GET /api/health ตอบ 200 {ok:true}", status == 200 and json_body(raw).get("ok") is True)

        status, raw, ctype = request("GET", "/")
        check("GET / เสิร์ฟหน้าเว็บปฏิทิน", status == 200 and "text/html" in ctype and "ปฏิทิน 30 วัน" in raw, f"HTTP {status} {ctype}")

        status, raw, ctype = request("GET", "/api/nope")
        check("GET ปลายทางที่ไม่มีตอบ 404 JSON", status == 404 and "application/json" in ctype, f"HTTP {status}")

        # ปุ่มทดลองโพสต์
        status, raw, _ = request("POST", "/api/post", {"day": 3})
        payload = json_body(raw)
        check("POST /api/post (ทดลอง) ตอบ 200 และ ok=true", status == 200 and payload.get("ok") is True, f"HTTP {status}")
        check("โหมดทดลองไม่ยิง API จริง", payload.get("mode") == "dry-run", str(payload.get("mode")))
        check(
            "ผลลัพธ์มีข้อความโพสต์ของวันที่ 3 จริง",
            "วันที่ 3" in payload.get("output", "") and "ข้อความโพสต์:" in payload.get("output", ""),
            payload.get("output", "")[:60].replace("\n", " "),
        )
        check("แนบสถานะล่าสุดกลับมาด้วย", isinstance(payload.get("status"), dict) and "credentials_ready" in payload.get("status", {}))

        # โพสต์จริงต้องถูกปฏิเสธเมื่อเซิร์ฟเวอร์ไม่ได้เปิด --live
        status, raw, _ = request("POST", "/api/post", {"day": 3, "live": True})
        payload = json_body(raw)
        check("POST live=true ถูกปฏิเสธ 403 เมื่อไม่ได้เปิด --live", status == 403 and payload.get("ok") is False, f"HTTP {status}")
        check("ข้อความบอกให้เปิดด้วย --live", "--live" in payload.get("error", ""), payload.get("error", ""))

        # ปุ่มทดลองสร้างร่าง (unpublished) — ไม่ยิง API
        status, raw, _ = request("POST", "/api/draft", {"day": 3})
        payload = json_body(raw)
        check("POST /api/draft (ทดลอง) ตอบ 200 และ ok=true", status == 200 and payload.get("ok") is True, f"HTTP {status}")
        check("ทดลองสร้างร่างไม่ยิง API จริง", payload.get("mode") == "dry-run", str(payload.get("mode")))
        check(
            "ผลลัพธ์เป็นโพสต์ unpublished",
            "published=false" in payload.get("output", "")
            and "unpublished_content_type=DRAFT" in payload.get("output", ""),
            payload.get("output", "")[:60].replace("\n", " "),
        )
        check(
            "ผลลัพธ์มีแคปชันของวันที่ 3",
            "วันที่ 3" in payload.get("output", "") and "ข้อความร่าง:" in payload.get("output", ""),
        )
        check(
            "แนบสถานะล่าสุดกลับมาหลังทดลองสร้างร่าง",
            isinstance(payload.get("status"), dict) and "drafts" in payload.get("status", {}),
        )

        # สร้างร่างจริงต้องถูกปฏิเสธเมื่อเซิร์ฟเวอร์ไม่ได้เปิด --live
        status, raw, _ = request("POST", "/api/draft", {"day": 3, "live": True})
        payload = json_body(raw)
        check(
            "POST /api/draft live=true ถูกปฏิเสธ 403 เมื่อไม่ได้เปิด --live",
            status == 403 and payload.get("ok") is False,
            f"HTTP {status}",
        )
        check("ข้อความบอกให้เปิดด้วย --live", "--live" in payload.get("error", ""), payload.get("error", ""))

        # ตรวจความถูกต้องของค่าที่ส่งเข้ามา
        for bad, label in [({"day": 0}, "day=0"), ({"day": 31}, "day=31"), ({"day": "3"}, 'day="3"'), ({}, "ไม่ส่ง day")]:
            status, raw, _ = request("POST", "/api/post", bad)
            check(f"ปฏิเสธ {label} ด้วย 400", status == 400, f"HTTP {status}")

        for bad, label in [({"day": 0}, "day=0"), ({"day": 31}, "day=31"), ({"day": "3"}, 'day="3"')]:
            status, raw, _ = request("POST", "/api/draft", bad)
            check(f"ปฏิเสธ /api/draft {label} ด้วย 400", status == 400, f"HTTP {status}")

        status, raw, _ = request("POST", "/api/post", "{ไม่ใช่ json".encode("utf-8"))
        check("ปฏิเสธ body ที่ไม่ใช่ JSON ด้วย 400", status == 400, f"HTTP {status}")

        # ปุ่มทดลองตั้งเวลา (ไม่ยิง API)
        status, raw, _ = request("POST", "/api/schedule", {"day": 3})
        payload = json_body(raw)
        check("POST /api/schedule (ทดลอง) ตอบ 200 และ ok=true", status == 200 and payload.get("ok") is True, f"HTTP {status}")
        check("ทดลองตั้งเวลาไม่ยิง API จริง", payload.get("mode") == "dry-run", str(payload.get("mode")))
        check(
            "ผลลัพธ์บอกกำหนดเวลาโพสต์ของวันที่ 3",
            "วันที่ 3" in payload.get("output", "") and "กำหนดโพสต์:" in payload.get("output", ""),
            payload.get("output", "")[:80].replace("\n", " "),
        )
        check(
            "แนบสถานะล่าสุดกลับมาหลังทดลองตั้งเวลา",
            isinstance(payload.get("status"), dict) and "schedule_window" in payload.get("status", {}),
        )

        # ตั้งเวลาจริงต้องถูกปฏิเสธเมื่อเซิร์ฟเวอร์ไม่ได้เปิด --live
        status, raw, _ = request("POST", "/api/schedule", {"day": 3, "live": True})
        payload = json_body(raw)
        check("POST /api/schedule live=true ถูกปฏิเสธ 403 เมื่อไม่ได้เปิด --live", status == 403 and payload.get("ok") is False, f"HTTP {status}")
        check("ข้อความบอกให้เปิดด้วย --live", "--live" in payload.get("error", ""), payload.get("error", ""))

        # ทดลองตั้งเวลาของวันที่เลยกำหนดแล้ว ต้องไม่เขียนสถานะใด ๆ ลง state
        status, raw, _ = request("POST", "/api/schedule", {"day": 1})
        payload = json_body(raw)
        check("ทดลองตั้งเวลาวันที่เลยกำหนดแล้วยังทำได้ (ไม่ยิง API)", status == 200 and payload.get("mode") == "dry-run", f"HTTP {status}")
        check(
            "ทดลองตั้งเวลาไม่บันทึกว่าตั้งเวลาแล้ว",
            "1" not in payload.get("status", {}).get("scheduled", {})
            and "1" not in payload.get("status", {}).get("published", {}),
            str(list(payload.get("status", {}).get("scheduled", {}))),
        )

        for bad, label in [({"day": 0}, "day=0"), ({"day": 31}, "day=31"), ({"day": "3"}, 'day="3"'), ({}, "ไม่ส่ง day")]:
            status, raw, _ = request("POST", "/api/schedule", bad)
            check(f"ปฏิเสธ /api/schedule {label} ด้วย 400", status == 400, f"HTTP {status}")

        status, raw, _ = request("POST", "/api/schedule", {"day": 3}, headers={"Origin": "http://evil.example"})
        check("ปฏิเสธ /api/schedule จาก origin อื่นด้วย 403", status == 403, f"HTTP {status}")

        status, raw, _ = request("POST", "/api/draft", {"day": 3}, headers={"Origin": "http://evil.example"})
        check("ปฏิเสธ /api/draft จาก origin อื่นด้วย 403 (กัน CSRF)", status == 403, f"HTTP {status}")
        status, raw, _ = request("POST", "/api/draft", {"day": 3}, headers={"Origin": f"http://127.0.0.1:{PORT}"})
        check("ยอมรับ /api/draft จาก origin เดียวกัน", status == 200, f"HTTP {status}")

        status, raw, _ = request("POST", "/api/other", {"day": 3})
        check("POST ปลายทางอื่นตอบ 404", status == 404, f"HTTP {status}")

        # กัน CSRF: origin อื่นต้องถูกปฏิเสธ, origin เดียวกันผ่าน
        status, raw, _ = request("POST", "/api/post", {"day": 3}, headers={"Origin": "http://evil.example"})
        check("ปฏิเสธ POST จาก origin อื่นด้วย 403", status == 403, f"HTTP {status}")
        status, raw, _ = request("POST", "/api/post", {"day": 3}, headers={"Origin": f"http://127.0.0.1:{PORT}"})
        check("ยอมรับ POST จาก origin เดียวกัน", status == 200, f"HTTP {status}")
    finally:
        stop_server(proc)


def phase_two() -> None:
    """เซิร์ฟเวอร์ที่เปิด --live"""
    proc = start_server(live=True)
    try:
        status, raw, _ = request("GET", "/api/status")
        payload = json_body(raw)
        check("live_allowed = true เมื่อเปิด --live", payload.get("live_allowed") is True, f"HTTP {status}")

        if credentials_present():
            skip("โพสต์จริงผ่าน API", "พบโทเคนจริงใน .env — ข้ามเพื่อไม่ให้โพสต์ขึ้นเพจจริง")
            return

        windows = payload.get("schedule_window") or {}
        ok_days = sorted(int(d) for d, v in windows.items() if v.get("window") == "ok")
        past_days = sorted(int(d) for d, v in windows.items() if v.get("window") == "past")

        # ตั้งเวลาจริง → ต้องวิ่งไปถึง fb_scheduler.py --schedule --live
        if ok_days:
            day = ok_days[0]
            status, raw, _ = request("POST", "/api/schedule", {"day": day, "live": True})
            payload = json_body(raw)
            check(
                "ตั้งเวลาจริงวิ่งไปถึง fb_scheduler.py --schedule --live",
                status == 200
                and payload.get("mode") == "live"
                and payload.get("action") == "ตั้งเวลาโพสต์"
                and payload.get("ok") is False,
                f"HTTP {status} exit={payload.get('exit_code')}",
            )
            check(
                "สคริปต์แจ้งว่าขาดค่าตั้งต้นใน .env แทนที่จะล้มเงียบ ๆ",
                "ขาดค่าตั้งต้น" in payload.get("output", ""),
                payload.get("output", "")[:80].replace("\n", " "),
            )
            status, raw, _ = request("GET", "/api/status")
            check(
                "ไม่บันทึกว่าตั้งเวลาแล้วเมื่อตั้งเวลาไม่สำเร็จ",
                str(day) not in json_body(raw).get("scheduled", {}),
                str(list(json_body(raw).get("scheduled", {}))),
            )

            # ตั้งซ้ำวันเดิมต้องถูกปฏิเสธ (ทดสอบด้วย state ชั่วคราว แล้วลบทิ้ง)
            if fb.STATE_FILE.exists():
                skip("ปฏิเสธการตั้งเวลาซ้ำ", "มี state/fb_state.json อยู่แล้ว — ไม่แตะไฟล์จริง")
            else:
                fb.save_state(
                    {
                        "published": {},
                        "scheduled": {
                            str(day): {"post_id": "1_2", "scheduled_for": windows[str(day)]["at"]}
                        },
                        "history": [],
                    }
                )
                try:
                    status, raw, _ = request("POST", "/api/schedule", {"day": day, "live": True})
                    payload = json_body(raw)
                    check(
                        "ตั้งเวลาซ้ำวันเดิมถูกปฏิเสธ 409 ไม่สร้างโพสต์ซ้ำ",
                        status == 409 and payload.get("ok") is False and "ตั้งเวลาไว้แล้ว" in payload.get("error", ""),
                        f"HTTP {status}",
                    )
                    check(
                        "ข้อความบอกเวลาและ id ที่ตั้งไว้แล้ว",
                        "1_2" in payload.get("error", ""),
                        payload.get("error", "")[:80],
                    )
                finally:
                    fb.STATE_FILE.unlink()
        else:
            skip("ตั้งเวลาจริงผ่าน API", "ไม่มีวันใดอยู่ในช่วงที่ Meta รับตั้งเวลาตอนรันเทสต์")

        # วันที่เลยกำหนด: ต้องปฏิเสธ ไม่ใช่กลายเป็นการโพสต์ทันที
        if past_days:
            day = past_days[0]
            status, raw, _ = request("POST", "/api/schedule", {"day": day, "live": True})
            payload = json_body(raw)
            check(
                "วันที่เลยกำหนดถูกปฏิเสธ 400 พร้อมชี้ไปที่ปุ่มโพสต์ทันที",
                status == 400
                and payload.get("window") == "past"
                and "โพสต์ขึ้นเพจทันที" in payload.get("error", ""),
                f"HTTP {status} {payload.get('error', '')[:60]}",
            )
            check(
                "ข้อความบอกวันที่และเวลาจริงของวันนั้น",
                windows[str(day)]["at"][:10] in payload.get("error", ""),
                payload.get("error", "")[:80],
            )
            status, raw, _ = request("GET", "/api/status")
            latest = json_body(raw)
            check(
                "การปฏิเสธไม่บันทึกโพสต์หรือตั้งเวลาใด ๆ",
                str(day) not in latest.get("published", {}) and str(day) not in latest.get("scheduled", {}),
            )
        else:
            skip("ปฏิเสธวันที่เลยกำหนด", "แผนปัจจุบันไม่มีวันที่ผ่านมาแล้ว")

        status, raw, _ = request("POST", "/api/post", {"day": 3, "live": True})
        payload = json_body(raw)
        check(
            "โพสต์จริงถูกส่งต่อไปยังสคริปต์ fb_scheduler.py (ok=false เพราะยังไม่มีโทเคน)",
            status == 200 and payload.get("ok") is False and payload.get("mode") == "live",
            f"HTTP {status} exit={payload.get('exit_code')}",
        )
        check(
            "สคริปต์แจ้งว่าขาดค่าตั้งต้นใน .env แทนที่จะล้มเงียบ ๆ",
            "ขาดค่าตั้งต้น" in payload.get("output", ""),
            payload.get("output", "")[:70].replace("\n", " "),
        )
        status, raw, _ = request("GET", "/api/status")
        published = json_body(raw).get("published", {})
        check("ไม่มีการบันทึกว่าโพสต์แล้วเมื่อโพสต์ไม่สำเร็จ", "3" not in published, str(list(published)))

        # ปุ่มสร้างร่าง (live) — ต้องวิ่งไปถึง fb_scheduler.py --draft --live
        status, raw, _ = request("POST", "/api/draft", {"day": 3, "live": True})
        payload = json_body(raw)
        check(
            "สร้างร่างจริงวิ่งไปถึง fb_scheduler.py --draft --live",
            status == 200
            and payload.get("mode") == "live"
            and payload.get("action") == "สร้างโพสต์ร่าง"
            and payload.get("ok") is False,
            f"HTTP {status} exit={payload.get('exit_code')}",
        )
        check(
            "สร้างร่างจริงแจ้งว่าขาดค่าตั้งต้นใน .env",
            "ขาดค่าตั้งต้น" in payload.get("output", ""),
            payload.get("output", "")[:80].replace("\n", " "),
        )
        status, raw, _ = request("GET", "/api/status")
        check(
            "ไม่บันทึกร่างเมื่อสร้างไม่สำเร็จ",
            "3" not in json_body(raw).get("drafts", {}),
            str(list(json_body(raw).get("drafts", {}))),
        )

        # ร่างซ้ำต้องถูกปฏิเสธ (ทดสอบด้วย state ชั่วคราว แล้วลบทิ้ง)
        if fb.STATE_FILE.exists():
            skip("ปฏิเสธการสร้างร่างซ้ำ", "มี state/fb_state.json อยู่แล้ว — ไม่แตะไฟล์จริง")
        else:
            fb.save_state(
                {
                    "published": {},
                    "scheduled": {},
                    "drafts": {
                        "day:3": {
                            "post_id": "9_9",
                            "source": "content/plan.json วันที่ 3",
                            "is_published": False,
                        }
                    },
                    "history": [],
                }
            )
            try:
                status, raw, _ = request("POST", "/api/draft", {"day": 3, "live": True})
                payload = json_body(raw)
                check(
                    "สร้างร่างซ้ำถูกปฏิเสธ 409 ไม่สร้างร่างซ้ำในเพจ",
                    status == 409 and payload.get("ok") is False and "ร่าง unpublished อยู่แล้ว" in payload.get("error", ""),
                    f"HTTP {status}",
                )
                check(
                    "ข้อความบอก post id ของร่างเดิม",
                    "9_9" in payload.get("error", ""),
                    payload.get("error", "")[:90],
                )
                check(
                    "สถานะที่ส่งกลับมาบอกร่างของวันนั้น",
                    "3" in payload.get("status", {}).get("drafts", {}),
                    str(list(payload.get("status", {}).get("drafts", {}))),
                )
            finally:
                fb.STATE_FILE.unlink()
    finally:
        stop_server(proc)


def main() -> int:
    print(f"ทดสอบ {SERVER.relative_to(ROOT)} ที่พอร์ต {PORT}\n")
    phase_zero()
    print()
    phase_one()
    print()
    phase_two()
    print()
    if skips:
        print("ข้าม: " + ", ".join(skips))
    print("ผ่านทั้งหมด" if not failures else f"{len(failures)} รายการไม่ผ่าน: " + ", ".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
