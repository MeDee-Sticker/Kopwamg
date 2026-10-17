#!/usr/bin/env python3
"""ทดสอบ scripts/daily_run.sh ว่าตรวจสถานะโพสต์ร่างอัตโนมัติและบันทึกผลลง log

รันสคริปต์จริงในโฟลเดอร์ชั่วคราว (ไม่แตะ state/ ของโปรเจกต์ และไม่ยิง Facebook จริง):
คัดลอกเฉพาะ daily_run.sh + fb_scheduler.py + content/plan.json ไปไว้ใน temp root
แล้วตรวจว่า

  - ตรวจสถานะร่างก่อนโพสต์ของวันนี้
  - ผลตรวจถูกเขียนต่อท้าย state/logs/draft-status-YYYY-MM.log (รันซ้ำไม่ทับข้อมูลเดิม)
  - ถ้าตรวจไม่ได้ (ไม่มีโทเคน แต่มีร่างค้าง) งานโพสต์ยังทำงานต่อ และเหตุผลอยู่ใน log

    python3 tests/daily_run_test.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAILY_RUN = ROOT / "scripts" / "daily_run.sh"

failures: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {extra}" if extra else ""))
    if not ok:
        failures.append(name)


def isolated_env() -> dict:
    """ตัดตัวแปร FB_* ของเครื่องจริงออก เพื่อไม่ให้เทสต์ยิง Facebook จริง"""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("FB_", "DAILY_LOG_DIR"))}
    env.setdefault("PATH", os.environ.get("PATH", "/usr/bin:/bin"))
    return env


def make_root(tmp: Path) -> None:
    (tmp / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp / "content").mkdir(parents=True, exist_ok=True)
    shutil.copy2(DAILY_RUN, tmp / "scripts" / "daily_run.sh")
    shutil.copy2(ROOT / "scripts" / "fb_scheduler.py", tmp / "scripts" / "fb_scheduler.py")
    shutil.copy2(ROOT / "content" / "plan.json", tmp / "content" / "plan.json")
    (tmp / "scripts" / "daily_run.sh").chmod(0o755)


def run_daily(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(root / "scripts" / "daily_run.sh")],
        cwd=str(root),
        env=isolated_env(),
        capture_output=True,
        text=True,
        timeout=180,
    )


def log_path(root: Path) -> Path:
    return root / "state" / "logs" / f"draft-status-{dt.date.today():%Y-%m}.log"


def draft_state() -> dict:
    return {
        "published": {},
        "scheduled": {},
        "drafts": {
            "file:fb-001-page-intro": {
                "post_id": "333_444",
                "source": "content/drafts/fb-001-page-intro.md",
                "chars": 791,
                "created_at": "2026-10-17T13:00:00+07:00",
                "is_published": False,
                "status": "draft",
            }
        },
        "history": [],
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        make_root(tmp)

        print("== รันครั้งแรก: ยังไม่มีร่าง ==")
        proc = run_daily(tmp)
        out = proc.stdout + proc.stderr
        check("daily_run จบสำเร็จแม้ไม่มีร่าง", proc.returncode == 0, f"exit {proc.returncode}")
        check("มีหัวข้อตรวจสถานะร่างอัตโนมัติ", "ตรวจสถานะโพสต์ร่าง (อัตโนมัติ)" in out)
        check("ตรวจสถานะก่อนโพสต์ของวันนี้", out.find("ตรวจสถานะโพสต์ร่าง") < out.find("โพสต์ Facebook ของวันนี้"))
        check("บอกว่าไม่มีร่างต้องตรวจ", "ยังไม่มีโพสต์ร่างที่บันทึกไว้" in out)
        relative_log = f"state/logs/draft-status-{dt.date.today():%Y-%m}.log"
        check("พิมพ์ path ของ log ให้เห็น", relative_log in out, relative_log)

        log = log_path(tmp)
        check("สร้างไฟล์ log ตาม path ที่ประกาศ", log.is_file(), str(log))
        text = log.read_text(encoding="utf-8") if log.is_file() else ""
        check("log มี timestamp ของรอบที่รัน", dt.date.today().isoformat() in text)
        check("log บันทึกผลว่าไม่มีร่าง", "ยังไม่มีโพสต์ร่างที่บันทึกไว้" in text)
        check("ไม่มี warning เรื่องตรวจไม่ครบ", "ตรวจสถานะร่างไม่ครบ" not in out)

        print("\n== รันครั้งที่สอง: ต้องต่อท้าย log ไม่ทับของเดิม ==")
        proc2 = run_daily(tmp)
        text2 = log.read_text(encoding="utf-8") if log.is_file() else ""
        check("รันซ้ำยังจบสำเร็จ", proc2.returncode == 0, f"exit {proc2.returncode}")
        check("log มีผลของทั้งสองรอบ", text2.count("===") >= 4 and len(text2) > len(text), f"{len(text)} → {len(text2)} ไบต์")

        print("\n== มีร่างค้างแต่ไม่มีโทเคน: ต้องบันทึกเหตุผลและโพสต์งานต่อ ==")
        (tmp / "state").mkdir(parents=True, exist_ok=True)
        (tmp / "state" / "fb_state.json").write_text(
            json.dumps(draft_state(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        proc3 = run_daily(tmp)
        out3 = proc3.stdout + proc3.stderr
        check("งานโพสต์ยังทำงานต่อแม้ตรวจร่างไม่ได้", proc3.returncode == 0, f"exit {proc3.returncode}")
        check("เตือนว่าตรวจสถานะร่างไม่ครบ", "ตรวจสถานะร่างไม่ครบ" in out3)
        check("ยังแสดงงานโพสต์ Facebook ต่อ", "โพสต์ Facebook ของวันนี้" in out3)
        text3 = log.read_text(encoding="utf-8")
        check(
            "log บันทึกเหตุผลว่าขาดโทเคน",
            "ขาดค่าตั้งต้นใน .env" in text3 and "FB_PAGE_ACCESS_TOKEN" in text3,
            [line for line in text3.splitlines() if "ขาดค่าตั้งต้น" in line][:1],
        )
        check("log ยังบันทึกว่ารันรอบล่าสุด", text3.count("===") >= 6)

    print()
    if failures:
        print(f"{len(failures)} รายการไม่ผ่าน")
        return 1
    print("ผ่านทั้งหมด")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
