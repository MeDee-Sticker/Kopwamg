#!/usr/bin/env python3
"""สัญญาคอนเทนต์ (content contract) สำหรับฉบับร่างโพสต์ Facebook ใน content/drafts/

ใช้เป็นด่านก่อนกดโพสต์: ทุกไฟล์ร่างต้องบอกชัดว่ายังไม่โพสต์ มีแคปชันที่พร้อมใช้
อยู่ในกรอบของแบรนด์ (ไม่มีคำสัญญารายได้) และมีเช็กลิสต์ให้คนตรวจติ๊กจริง

    python3 tests/content_draft_test.py
"""

from __future__ import annotations

import glob
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT_GLOB = str(ROOT / "content" / "drafts" / "*.md")

BANNED = ["รวย", "การันตีรายได้", "รับประกันรายได้", "รายได้แน่นอน", "รายได้ guaranteed"]
SECRETS = ["EAA", "access_token", "FB_PAGE_ACCESS_TOKEN"]
MIN_CAPTION, MAX_CAPTION = 300, 2200
MAX_HOOK = 120  # ข้อความบรรทัดแรกต้องเห็นได้ก่อน Facebook ตัดขึ้น "ดูเพิ่มเติม"


def section(text: str, heading: str) -> str:
    """เนื้อหาของหัวข้อ `## heading` จนถึงหัวข้อถัดไป"""
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1).strip() if match else ""


def draft_report(path: Path) -> list[tuple[str, bool, str]]:
    text = path.read_text(encoding="utf-8")
    caption = section(text, "แคปชัน (คัดลอกวางได้เลย)")
    hook = next((line.strip() for line in caption.splitlines() if line.strip()), "")
    meta = text  # ตาราง metadata อยู่บนสุดของไฟล์

    rules = [
        ("บอกสถานะว่ายังไม่โพสต์", "ยังไม่โพสต์" in text, ""),
        ("มีหัวข้อแคปชันที่คัดลอกได้", bool(caption), f"{len(caption)} ตัวอักษร"),
        ("ความยาวแคปชันอยู่ในช่วงที่อ่านจบ", MIN_CAPTION <= len(caption) <= MAX_CAPTION, str(len(caption))),
        ("ประโยคเปิดสั้นพอให้เห็นก่อนถูกตัด", 0 < len(hook) <= MAX_HOOK, hook[:60]),
        ("มีลายเซ็นแบรนด์", "— Kopwang |" in caption, ""),
        ("มีแฮชแท็กอย่างน้อย 3 อัน", len(re.findall(r"#\w+", caption)) >= 3, str(len(re.findall(r"#\w+", caption)))),
        ("มีคำเรียกให้ทำต่อ (ติดตาม/คอมเมนต์)", any(w in caption for w in ("ติดตาม", "คอมเมนต์")), ""),
        ("ไม่มีคำสัญญารายได้ต้องห้าม", not any(w in caption for w in BANNED), ", ".join(w for w in BANNED if w in caption)),
        ("ไม่มีข้อมูลลับในฉบับร่าง", not any(s in text for s in SECRETS), ""),
        ("มีเช็กลิสต์ให้ตรวจก่อนโพสต์ ≥ 5 ข้อ", len(re.findall(r"^- \[ \] ", text, re.M)) >= 5,
         str(len(re.findall(r"^- \[ \] ", text, re.M)))),
        ("ระบุเพจเป้าหมาย", bool(re.search(r"เพจเป้าหมาย", meta)), ""),
    ]
    return rules


def main() -> int:
    paths = [Path(p) for p in sorted(glob.glob(DRAFT_GLOB))]
    if not paths:
        print(f"ไม่พบฉบับร่างที่ {Path(DRAFT_GLOB).relative_to(ROOT)} — ยังไม่มีอะไรให้ตรวจ")
        return 1

    failures = 0
    for path in paths:
        print(f"\n{path.relative_to(ROOT)}")
        for name, ok, extra in draft_report(path):
            print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {extra}" if extra else ""))
            failures += 0 if ok else 1

    print("\nผ่านทั้งหมด" if not failures else f"\n{failures} รายการไม่ผ่าน")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
