#!/usr/bin/env python3
"""Kopwang — เซิร์ฟเวอร์ในเครื่องสำหรับหน้าเว็บปฏิทิน + ปุ่มสั่งโพสต์ Facebook

หน้าเว็บ `dashboard/index.html` เป็นไฟล์ static จึงเรียกสคริปต์โพสต์เองไม่ได้
เซิร์ฟเวอร์นี้ทำหน้าที่เป็นตัวกลาง: เสิร์ฟไฟล์หน้าเว็บ แล้วเปิด API เล็ก ๆ
ที่เรียก `scripts/fb_scheduler.py` ให้ (สคริปต์โพสต์ตัวเดิม ไม่เขียนตรรกะซ้ำ)

    POST /api/post      {day, live}  → fb_scheduler.py --day N [--live]
    POST /api/schedule  {day, live}  → fb_scheduler.py --day N --schedule [--live]
    POST /api/draft     {day, live}  → fb_scheduler.py --day N --draft [--live]  (โพสต์ unpublished)
    GET  /api/status                 → สถานะโพสต์/ตั้งเวลา/ร่าง + ช่วงเวลาที่ตั้งได้ของแต่ละวัน

    python3 scripts/dashboard_server.py                 # โหมดดูตัวอย่าง (ปลอดภัย) — ปุ่มโพสต์จริงปิดอยู่
    python3 scripts/dashboard_server.py --live          # เปิดให้กดโพสต์ขึ้นเพจจริงได้
    python3 scripts/dashboard_server.py --port 3000 --host 0.0.0.0

แล้วเปิด http://localhost:3000

ความปลอดภัย
-----------
- ผูกกับ 127.0.0.1 เป็นค่าเริ่มต้น — เครื่องอื่นในเครือข่ายเข้าไม่ถึง
- การเขียนข้อมูลจริง (โพสต์ ตั้งเวลา และสร้างโพสต์ร่าง) ถูกปิดไว้ก่อน ต้องสั่ง --live ตอนเปิดเซิร์ฟเวอร์
  (หน้าเว็บจะเห็นว่าปุ่มเขียนจริงกดไม่ได้และบอกสาเหตุ)
- การตั้งเวลาจะถูกตรวจช่วงเวลาก่อน (ล่วงหน้า 10 นาที ถึง 30 วัน ตามที่ Meta รับ)
  เพื่อไม่ให้การกด "ตั้งเวลา" กลายเป็นการโพสต์ทันทีโดยไม่ตั้งใจ
- POST ที่มาจากคนละ origin ถูกปฏิเสธ กันเว็บอื่นแอบยิงคำสั่งเข้ามาที่เครื่องคุณ
- API ไม่เคยส่งค่าลับ (โทเคน) ออกไป มีแค่สถานะ "ตั้งค่าแล้ว/ยังไม่ตั้งค่า"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = ROOT / "dashboard"
SCHEDULER = ROOT / "scripts" / "fb_scheduler.py"
MAX_DAYS = 30
POST_TIMEOUT_SECONDS = 180

# ตั้งค่าใหม่ได้จาก main() เท่านั้น — ค่าเริ่มต้นคือ "ห้ามโพสต์จริง"
ALLOW_LIVE = False

sys.path.insert(0, str(ROOT / "scripts"))
import fb_scheduler as fb  # noqa: E402  (ใช้ตัวอ่าน .env และ state ตัวเดียวกับสคริปต์โพสต์)


def load_plan() -> dict:
    try:
        return json.loads(fb.PLAN.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def facebook_row(plan: dict, day: int) -> dict | None:
    for row in plan.get("rows", []):
        if row.get("platform") == "facebook" and row.get("day") == day:
            return row
    return None


def schedule_windows(plan: dict) -> dict:
    """กำหนดเวลาของแต่ละวัน + ตั้งเวลาได้หรือไม่ (ใช้ตัวตัดสินเดียวกับ fb_scheduler)"""
    windows = {}
    now = datetime.now(fb.BANGKOK)
    for row in plan.get("rows", []):
        if row.get("platform") != "facebook":
            continue
        try:
            at = fb.parse_slot(row)
        except (KeyError, ValueError):
            continue
        windows[str(row["day"])] = {
            "at": at.isoformat(timespec="minutes"),
            "window": fb.schedule_window(row, now),
        }
    return windows


def draft_days(state: dict) -> dict:
    """ร่าง unpublished ที่ผูกกับวันในแผน — คีย์เป็นเลขวัน (ไม่รวมไฟล์ร่างใน content/drafts/)"""
    out = {}
    for key, entry in (state.get("drafts") or {}).items():
        if not isinstance(entry, dict):
            continue
        day = entry.get("day")
        if day is None and str(key).startswith("day:"):
            try:
                day = int(str(key).split(":", 1)[1])
            except ValueError:
                continue
        if isinstance(day, int) and not isinstance(day, bool):
            out[str(day)] = entry
    return out


def status_payload() -> dict:
    """สถานะที่หน้าเว็บต้องรู้ — ไม่มีค่าลับใด ๆ ออกไป"""
    try:
        env = fb.load_env()
    except Exception:
        env = {}
    try:
        state = fb.load_state()
    except Exception:
        state = {"published": {}, "scheduled": {}, "drafts": {}, "history": []}
    return {
        "api": True,
        "credentials_ready": bool(env.get("FB_PAGE_ID") and env.get("FB_PAGE_ACCESS_TOKEN")),
        "live_allowed": ALLOW_LIVE,
        "published": state.get("published", {}),
        "scheduled": state.get("scheduled", {}),
        "drafts": draft_days(state),
        "schedule_window": schedule_windows(load_plan()),
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    # ---------------------------------------------------------------- utilities
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _same_origin(self) -> bool:
        """ถ้ามี Origin ต้องตรงกับ Host ของคำขอนี้ ถือเป็น same-origin"""
        origin = self.headers.get("Origin")
        if not origin:
            return True  # คำสั่งจากเครื่องเอง (curl/สคริปต์) ไม่มี Origin
        try:
            o = urlparse(origin)
        except ValueError:
            return False
        host = self.headers.get("Host", "")
        if not o.netloc:
            return False
        return o.netloc.lower() == host.lower()

    def log_message(self, fmt, *args):  # ไม่ต้องรก log ด้วยบรรทัด static file ทุกไฟล์
        if "/api/" in (self.path or ""):
            sys.stderr.write("  %s %s\n" % (self.address_string(), fmt % args))

    # ---------------------------------------------------------------- routes
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            self._json(200, status_payload())
            return
        if path == "/api/health":
            self._json(200, {"ok": True})
            return
        if path.startswith("/api/"):
            self._json(404, {"ok": False, "error": "ไม่พบปลายทางนี้"})
            return
        return super().do_GET()

    def _read_json(self) -> tuple[dict | None, str | None]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 4096:
            return None, "ต้องส่ง JSON body ขนาดไม่เกิน 4 KB"
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, "body ต้องเป็น JSON"
        if not isinstance(payload, dict):
            return None, "body ต้องเป็น JSON object"
        return payload, None

    def _run_scheduler(self, extra: list[str], *, day: int, mode: str, action: str) -> None:
        """เรียก fb_scheduler.py ตัวเดิม แล้วส่งผลลัพธ์กลับหน้าเว็บ"""
        cmd = [sys.executable, str(SCHEDULER), *extra]
        try:
            proc = subprocess.run(
                cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=POST_TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired:
            self._json(
                504,
                {"ok": False, "mode": mode, "error": f"สคริปต์ใช้เวลาเกิน {POST_TIMEOUT_SECONDS} วินาที"},
            )
            return

        output = (proc.stdout or "").strip()
        if proc.stderr.strip():
            output += ("\n\n[stderr]\n" + proc.stderr.strip()) if output else proc.stderr.strip()

        self._json(
            200,
            {
                "ok": proc.returncode == 0,
                "exit_code": proc.returncode,
                "mode": mode,
                "action": action,
                "day": day,
                "output": output or "(สคริปต์ไม่พิมพ์อะไรออกมา)",
                "status": status_payload(),
            },
        )

    def _schedule(self, day: int, live: bool) -> None:
        """ตั้งเวลาโพสต์ล่วงหน้า — ตรวจช่วงเวลาก่อน เพื่อไม่ให้ "ตั้งเวลา" กลายเป็นการโพสต์ทันที"""
        plan = load_plan()
        row = facebook_row(plan, day)
        if row is None:
            self._json(404, {"ok": False, "error": f"ไม่พบโพสต์ Facebook ของวันที่ {day} ใน content/plan.json"})
            return
        if not live:
            self._run_scheduler(
                ["--day", str(day), "--schedule"],
                day=day,
                mode="dry-run",
                action="ทดลองตั้งเวลา (ไม่ยิง API)",
            )
            return

        window = fb.schedule_window(row)
        when = fb.parse_slot(row).strftime("%Y-%m-%d %H:%M")
        if window == "past":
            self._json(
                400,
                {
                    "ok": False,
                    "window": window,
                    "error": (
                        f"เลยเวลาตั้งเวลาได้แล้ว: กำหนดโพสต์วันที่ {day} คือ {when} "
                        f"(Meta ต้องล่วงหน้าอย่างน้อย {fb.MIN_SCHEDULE_AHEAD_MINUTES} นาที) — "
                        "ถ้าต้องการโพสต์ตอนนี้ให้ใช้ปุ่ม \"โพสต์ขึ้นเพจทันที\""
                    ),
                },
            )
            return
        if window == "too_far":
            self._json(
                400,
                {
                    "ok": False,
                    "window": window,
                    "error": (
                        f"กำหนดโพสต์วันที่ {day} คือ {when} เกิน {fb.MAX_SCHEDULE_AHEAD_DAYS} วันล่วงหน้า "
                        "ซึ่ง Meta ไม่รับตั้งเวลา"
                    ),
                },
            )
            return

        state = fb.load_state()
        if str(day) in state.get("published", {}):
            self._json(409, {"ok": False, "error": f"วันที่ {day} โพสต์ขึ้นเพจจริงแล้ว — ไม่ต้องตั้งเวลาซ้ำ"})
            return
        existing = state.get("scheduled", {}).get(str(day))
        if existing:
            self._json(
                409,
                {
                    "ok": False,
                    "error": (
                        f"วันที่ {day} ตั้งเวลาไว้แล้วที่ {existing.get('scheduled_for', '-')} "
                        f"(id {existing.get('post_id', '-')}) — ตั้งซ้ำจะได้โพสต์ซ้ำในเพจ"
                    ),
                    "status": status_payload(),
                },
            )
            return

        self._run_scheduler(
            ["--day", str(day), "--schedule", "--live"],
            day=day,
            mode="live",
            action="ตั้งเวลาโพสต์",
        )

    def _draft(self, day: int, live: bool) -> None:
        """สร้างโพสต์ unpublished จากแคปชันของวันนั้น — ไม่ขึ้นเพจจนกว่าจะกดเผยแพร่เอง"""
        if facebook_row(load_plan(), day) is None:
            self._json(404, {"ok": False, "error": f"ไม่พบโพสต์ Facebook ของวันที่ {day} ใน content/plan.json"})
            return
        if not live:
            self._run_scheduler(
                ["--day", str(day), "--draft"],
                day=day,
                mode="dry-run",
                action="ทดลองสร้างร่าง (ไม่ยิง API)",
            )
            return

        existing = draft_days(fb.load_state()).get(str(day))
        if existing:
            self._json(
                409,
                {
                    "ok": False,
                    "error": (
                        f"วันที่ {day} มีร่าง unpublished อยู่แล้ว (id {existing.get('post_id', '-')}) — "
                        "สร้างซ้ำจะได้ร่างซ้ำในเพจ; ใช้ --force ผ่าน CLI ถ้าต้องการสร้างใหม่"
                    ),
                    "status": status_payload(),
                },
            )
            return

        self._run_scheduler(
            ["--day", str(day), "--draft", "--live"],
            day=day,
            mode="live",
            action="สร้างโพสต์ร่าง",
        )

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/post", "/api/schedule", "/api/draft"):
            self._json(404, {"ok": False, "error": "ไม่พบปลายทางนี้"})
            return
        if not self._same_origin():
            self._json(403, {"ok": False, "error": "ปฏิเสธคำขอจาก origin อื่น (กัน CSRF)"})
            return

        payload, error = self._read_json()
        if error:
            self._json(400, {"ok": False, "error": error})
            return

        day = payload.get("day")
        if not isinstance(day, int) or isinstance(day, bool) or not 1 <= day <= MAX_DAYS:
            self._json(400, {"ok": False, "error": f"day ต้องเป็นจำนวนเต็ม 1-{MAX_DAYS}"})
            return

        live = bool(payload.get("live"))
        if live and not ALLOW_LIVE:
            self._json(
                403,
                {
                    "ok": False,
                    "error": "เซิร์ฟเวอร์นี้ยังไม่เปิดโหมดเขียนจริง — เปิดใหม่ด้วย --live",
                    "mode": "dry-run",
                },
            )
            return

        if path == "/api/schedule":
            self._schedule(day, live)
            return
        if path == "/api/draft":
            self._draft(day, live)
            return

        self._run_scheduler(
            ["--day", str(day)] + (["--live"] if live else []),
            day=day,
            mode="live" if live else "dry-run",
            action="โพสต์จริง" if live else "ทดลอง (ไม่ยิง API)",
        )


def main(argv: list[str] | None = None) -> int:
    global ALLOW_LIVE

    parser = argparse.ArgumentParser(
        description="เสิร์ฟหน้าเว็บปฏิทิน Kopwang พร้อมปุ่มสั่งโพสต์ Facebook ผ่านสคริปต์เดิม",
    )
    parser.add_argument("--port", type=int, default=3000, help="พอร์ต (ค่าเริ่มต้น 3000)")
    parser.add_argument("--host", default="127.0.0.1", help="ที่อยู่ที่ผูก (ค่าเริ่มต้น 127.0.0.1)")
    parser.add_argument(
        "--live",
        action="store_true",
        help="เปิดให้ปุ่มบนหน้าเว็บโพสต์/ตั้งเวลาจริงได้ (ไม่มี = ทำได้แค่ทดลอง)",
    )
    args = parser.parse_args(argv)

    ALLOW_LIVE = args.live

    if not (DASHBOARD_DIR / "index.html").exists():
        print("ยังไม่มี dashboard/index.html — กำลังสร้างจากแผน…")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_dashboard.py")], cwd=str(ROOT))

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    live_note = "เปิด (กดโพสต์จริงได้)" if ALLOW_LIVE else "ปิด (ทดลองเท่านั้น)"
    print(f"เสิร์ฟหน้าเว็บปฏิทินที่ http://{args.host}:{args.port}")
    print(f"  โหมดโพสต์จริง     : {live_note}")
    print("  เปิดดูที่เบราว์เซอร์: " + (f"http://localhost:{args.port}" if args.host in ("0.0.0.0", "127.0.0.1") else f"http://{args.host}:{args.port}"))
    if not ALLOW_LIVE:
        print("  (ถ้าต้องการโพสต์จริง: หยุดเซิร์ฟเวอร์แล้วเปิดใหม่ด้วย --live)")
    print("  กด Ctrl+C เพื่อหยุด")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nหยุดเซิร์ฟเวอร์แล้ว")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
