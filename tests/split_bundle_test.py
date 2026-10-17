#!/usr/bin/env python3
"""ทดสอบการแยกชุดดาวน์โหลดเป็นไฟล์ข้อความ (scripts/split_bundle_for_download.py)

ตรวจว่า
  - แบ่งเป็นหลายส่วนตามขนาดที่กำหนด และหัวไฟล์บอกส่วนที่/ทั้งหมด/แฮชถูกต้อง
  - รวมกลับด้วยวิธีที่เขียนใน REASSEMBLE.md ได้ไฟล์ไบต์เดิมและแฮชตรง
  - ตรวจเจอเมื่อชิ้นส่วนหายหรือถูกแก้
  - ชิ้นส่วนที่อยู่ใน downloads/parts รวมกลับได้ตรงกับ zip จริงในโปรเจกต์

    python3 tests/split_bundle_test.py
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import split_bundle_for_download as sp  # noqa: E402

failures: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {extra}" if extra else ""))
    if not ok:
        failures.append(name)


def capture(func, *args, **kwargs):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        value = func(*args, **kwargs)
    return value, buffer.getvalue()


def make_zip(path: Path, payload: bytes | None = None) -> bytes:
    # ใช้ข้อมูลสุ่มเพื่อไม่ให้ zip บีบอัดจนเล็กเกินไป (จำลองชุดจริง)
    payload = payload if payload is not None else os.urandom(200_000)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("a.txt", payload)
    return path.read_bytes()


def phase_build() -> None:
    print("== แบ่งชิ้นส่วน ==")
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        source = tmp / "bundle.zip"
        raw = make_zip(source)
        digest = sp.sha256(raw)

        files = sp.build_parts(source, part_kb=100)
        parts = [name for name in files if name.startswith("kopwang-part-")]
        check("ได้หลายส่วนตามขนาดที่กำหนด", 2 <= len(parts) <= 4, str(sorted(parts)))
        check("มีไฟล์วิธีรวมกลับ", "REASSEMBLE.md" in files)

        first = files[sorted(parts)[0]].decode("utf-8")
        check("หัวไฟล์บอกส่วนที่/ทั้งหมดและชื่อต้นทาง", "part 1/" in first and "bundle.zip" in first)
        check("หัวไฟล์บอกแฮชของไฟล์รวม", digest in first)
        check("หัวไฟล์บอกคำสั่งรวมกลับ", "base64 -d > kopwang-all-files.zip" in first)
        notes = files["REASSEMBLE.md"].decode("utf-8")
        check("REASSEMBLE.md มีแฮช ขนาด และคำสั่ง", digest in notes and str(len(raw)) in notes and "cat kopwang-part-*.txt" in notes)
        check("ขนาดแต่ละส่วนไม่เกินที่ขอ (บวกหัวไฟล์)", all(
            len(files[name]) <= 100 * 1024 + 512 for name in parts
        ), str([len(files[name]) for name in sorted(parts)]))

        outdir = tmp / "parts"
        sp.write_parts(outdir, files)
        check("เขียนไฟล์ครบตามที่สร้าง", sorted(p.name for p in outdir.iterdir()) == sorted(files))
        problems = sp.verify_parts(outdir, digest)
        check("รวมกลับได้ไฟล์เดิมและแฮชตรง", not problems, "; ".join(problems))

        # จำลอง pipeline ที่เขียนใน REASSEMBLE.md
        joined = []
        for name in sorted(parts):
            for line in (outdir / name).read_text(encoding="utf-8").splitlines():
                if not line.startswith("#"):
                    joined.append(line.strip())
        rebuilt = base64.b64decode("".join(joined), validate=True)
        check("คำสั่งที่เขียนในเอกสารใช้ได้จริง", rebuilt == raw, f"{len(rebuilt)} vs {len(raw)} ไบต์")

        # ชิ้นส่วนหาย → แฮชไม่ตรง
        moved = outdir / sorted(parts)[-1]
        backup = moved.read_bytes()
        moved.unlink()
        problems = sp.verify_parts(outdir, digest)
        check("ตรวจเจอเมื่อชิ้นส่วนหาย", bool(problems), "; ".join(problems)[:80])
        moved.write_bytes(backup)

        # เนื้อหาถูกแก้ → ถอด base64 ไม่ได้
        (outdir / sorted(parts)[1]).write_text("# comment\n%%%ไม่ใช่-base64%%%\n", encoding="utf-8")
        problems = sp.verify_parts(outdir, digest)
        check("ตรวจเจอเมื่อเนื้อหาถูกแก้", bool(problems), "; ".join(problems)[:80])


def phase_repo() -> None:
    print("\n== ชิ้นส่วนในโปรเจกต์ ==")
    part_dir = sp.DOWNLOAD_DIR / sp.PART_DIR_NAME
    manifest_path = sp.DOWNLOAD_DIR / "manifest.json"
    if not part_dir.exists() or not manifest_path.exists():
        check("มี downloads/parts และ manifest", False, "รัน scripts/split_bundle_for_download.py ก่อน")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems = sp.verify_parts(part_dir, manifest["zip_sha256"])
    check("ชิ้นส่วนในโปรเจกต์รวมกลับตรงกับ zip จริง", not problems, "; ".join(problems))
    check("มี REASSEMBLE.md ในโปรเจกต์", (part_dir / "REASSEMBLE.md").is_file())

    with tempfile.TemporaryDirectory() as tmp_name:
        try:
            sp.newest_zip(Path(tmp_name))
        except SystemExit as exc:
            message = str(exc)
        else:
            message = ""
        check("แจ้งชัดเจนเมื่อไม่มี zip ให้แยก", "ไม่พบ zip" in message, message[:70])


def main() -> int:
    phase_build()
    phase_repo()
    print()
    if failures:
        print(f"{len(failures)} รายการไม่ผ่าน")
        return 1
    print("ผ่านทั้งหมด")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
