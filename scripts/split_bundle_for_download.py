#!/usr/bin/env python3
"""Kopwang — แยก zip ชุดดาวน์โหลดเป็นไฟล์ข้อความหลายส่วน สำหรับช่องทางที่โหลดไฟล์ไบนารีไม่ได้

บางหน้าจอ/แชตดาวน์โหลดไฟล์ .zip ไม่ได้ แต่โหลดไฟล์ข้อความได้ ตัวนี้จึงแปลง zip เป็น base64
แบ่งเป็นหลายไฟล์ `.txt` ขนาดพอเหมาะ แล้วเขียนวิธีรวมกลับไว้ใน `REASSEMBLE.md`

    python3 scripts/split_bundle_for_download.py                 # ใช้ zip ล่าสุดใน downloads/
    python3 scripts/split_bundle_for_download.py --zip downloads/kopwang-all-files-20261017.zip
    python3 scripts/split_bundle_for_download.py --part-kb 400   # ขนาดต่อส่วน (ค่าเริ่มต้น 400 KB)

รวมกลับบนเครื่องปลายทาง (macOS/Linux):
    cat kopwang-part-*.txt | grep -v '^#' | base64 -d > kopwang-all-files.zip
    sha256sum kopwang-all-files.zip      # เทียบกับค่าใน REASSEMBLE.md
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = ROOT / "downloads"
PART_DIR_NAME = "parts"
DEFAULT_PART_KB = 400


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def newest_zip(directory: Path = DOWNLOAD_DIR) -> Path:
    candidates = sorted(directory.glob("kopwang-all-files*.zip"))
    if not candidates:
        raise SystemExit(
            f"ไม่พบ zip ใน {directory} — รัน python3 scripts/build_download_bundle.py ก่อน"
        )
    return max(candidates, key=lambda path: path.stat().st_mtime)


def split_payload(data: bytes, part_bytes: int) -> list[str]:
    encoded = base64.b64encode(data).decode("ascii")
    width = max(1, part_bytes // 4 * 4)
    lines = [encoded[index : index + width] for index in range(0, len(encoded), width)]
    return lines or [""]


def build_parts(zip_path: Path, part_kb: int = DEFAULT_PART_KB) -> dict[str, bytes]:
    """คืน dict ชื่อไฟล์ → เนื้อหา (ไม่เขียนดิสก์) เพื่อให้ทดสอบได้"""
    payload = zip_path.read_bytes()
    digest = sha256(payload)
    chunks = split_payload(payload, part_kb * 1024)
    total = len(chunks)
    files: dict[str, bytes] = {}
    for index, chunk in enumerate(chunks, start=1):
        header = (
            f"# Kopwang download bundle — part {index}/{total}\n"
            f"# source: {zip_path.name} ({len(payload)} bytes)\n"
            f"# sha256 (whole file): {digest}\n"
            "# รวมกลับ: cat kopwang-part-*.txt | grep -v '^#' | base64 -d > kopwang-all-files.zip\n"
        )
        files[f"kopwang-part-{index:02d}.txt"] = (header + chunk + "\n").encode("utf-8")
    files["REASSEMBLE.md"] = reassemble_notes(zip_path, digest, len(payload), total).encode("utf-8")
    return files


def reassemble_notes(zip_path: Path, digest: str, size: int, parts: int) -> str:
    return f"""# รวมไฟล์ zip กลับจากชิ้นส่วนข้อความ

ชุดนี้คือ `{zip_path.name}` ({size} bytes · {parts} ส่วน) แปลงเป็น base64 เพื่อให้ดาวน์โหลดผ่านช่องทางที่รับเฉพาะไฟล์ข้อความ

## วิธีรวมกลับ

macOS / Linux (อยู่ในโฟลเดอร์ที่มีไฟล์ `kopwang-part-*.txt`):

```bash
cat kopwang-part-*.txt | grep -v '^#' | base64 -d > kopwang-all-files.zip
shasum -a 256 kopwang-all-files.zip      # macOS
sha256sum kopwang-all-files.zip          # Linux
```

Windows (PowerShell):

```powershell
Get-Content kopwang-part-*.txt | Where-Object {{ $_ -notlike '#*' }} | Set-Content joined.b64
certutil -decode joined.b64 kopwang-all-files.zip
```

## ค่าที่ต้องตรง

- sha256 ของ zip: `{digest}`
- ขนาด: `{size}` bytes

ถ้าค่าไม่ตรง ให้ดาวน์โหลดชิ้นส่วนที่ขาดใหม่ (ดูเลข part ในบรรทัดแรกของแต่ละไฟล์)
"""


def write_parts(outdir: Path, files: dict[str, bytes]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (outdir / name).write_bytes(data)


def verify_parts(outdir: Path, digest: str | None = None) -> list[str]:
    """รวมชิ้นส่วนกลับเป็น zip แล้วเทียบแฮช — คืนรายการปัญหา (ว่าง = ผ่าน)"""
    parts = sorted(outdir.glob("kopwang-part-*.txt"))
    if not parts:
        return [f"ไม่พบไฟล์ kopwang-part-*.txt ใน {outdir}"]
    body: list[str] = []
    for path in parts:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                continue
            body.append(line.strip())
    try:
        payload = base64.b64decode("".join(body), validate=True)
    except Exception as exc:  # noqa: BLE001 — รายงานทุกกรณีที่ถอดไม่ได้
        return [f"ถอด base64 ไม่ได้: {exc}"]
    if digest and sha256(payload) != digest:
        return ["แฮชหลังรวมกลับไม่ตรงกับต้นฉบับ"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="แยก zip เป็นไฟล์ข้อความ base64 หลายส่วน")
    parser.add_argument("--zip", type=Path, help="ไฟล์ zip ต้นทาง (ค่าเริ่มต้น: zip ล่าสุดใน downloads/)")
    parser.add_argument("--part-kb", type=int, default=DEFAULT_PART_KB, help="ขนาดต่อส่วนโดยประมาณ (KB)")
    parser.add_argument("--outdir", type=Path, help="โฟลเดอร์ผลลัพธ์ (ค่าเริ่มต้น: downloads/parts)")
    args = parser.parse_args()

    zip_path = args.zip or newest_zip()
    if not zip_path.is_file():
        raise SystemExit(f"ไม่พบไฟล์ zip: {zip_path}")
    outdir = args.outdir or (DOWNLOAD_DIR / PART_DIR_NAME)

    files = build_parts(zip_path, args.part_kb)
    write_parts(outdir, files)
    payload = zip_path.read_bytes()
    digest = sha256(payload)
    problems = verify_parts(outdir, digest)
    if problems:
        for item in problems:
            print(f"❌ {item}", file=sys.stderr)
        return 1
    print(
        f"แยกแล้ว {len(files) - 1} ส่วนที่ {outdir} (จาก {zip_path.name} · {len(payload) / 1024:.0f} KB)\n"
        f"รวมกลับ: cat kopwang-part-*.txt | grep -v '^#' | base64 -d > kopwang-all-files.zip\n"
        f"sha256: {digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
