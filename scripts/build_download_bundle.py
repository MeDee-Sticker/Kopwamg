#!/usr/bin/env python3
"""Kopwang — รวมทุกไฟล์ในโปรเจกต์เป็นชุดเดียวสำหรับดาวน์โหลด

สร้างใน `downloads/`:

  kopwang-all-files-YYYYMMDD.zip   สำเนาทุกไฟล์ที่ใช้งานได้ของโปรเจกต์
  manifest.json                    รายชื่อไฟล์ ขนาด sha256 และแฮชของ zip
  README.md                        วิธีดาวน์โหลดและสิ่งที่ถูกตัดออก

ตัดออกเฉพาะไฟล์ที่ไม่ควรแจกหรือสร้างใหม่ได้: `.git/`, `state/` (สถานะรันจริง),
`downloads/` (ผลลัพธ์ของสคริปต์นี้), `__pycache__/`, `*.pyc` และ `.env` ทุกไฟล์
(`.env.example` ยังอยู่ เพราะเป็นตัวอย่างให้ตั้งค่าเอง)

ตัวอย่าง
--------
    python3 scripts/build_download_bundle.py
    python3 scripts/build_download_bundle.py --outdir /tmp/kopwang-downloads
    python3 scripts/build_download_bundle.py --check     # ตรวจว่า manifest ตรงกับไฟล์จริง
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTDIR = ROOT / "downloads"
BUNDLE_README = "DOWNLOAD-README.md"

EXCLUDE_DIRS = {".git", "__pycache__", "state", "downloads", "node_modules", ".venv", ".mypy_cache"}
EXCLUDE_FILES = {".env", ".DS_Store"}
EXCLUDE_SUFFIXES = (".pyc", ".pyo")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def collect_files(root: Path = ROOT) -> dict[str, bytes]:
    """ทุกไฟล์ที่ควรอยู่ในชุดดาวน์โหลด (path relative → bytes) เรียงตามชื่อ"""
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in relative.parts):
            continue
        if relative.name in EXCLUDE_FILES:
            continue
        if relative.name.startswith(".env.") and relative.name != ".env.example":
            continue
        if path.suffix in EXCLUDE_SUFFIXES:
            continue
        # ชุดดาวน์โหลดที่วางไว้รากโปรเจกต์ (เพื่อกดดาวน์โหลดง่าย) ไม่ต้องซ้อนเข้าไปในชุดใหม่
        if len(relative.parts) == 1 and relative.name.lower().endswith((".zip", ".tar.gz", ".tgz")):
            continue
        files[str(relative)] = path.read_bytes()
    return files


def bundle_readme(stamp: str, count: int) -> str:
    return f"""# Kopwang — ชุดไฟล์ทั้งหมด

สร้างเมื่อ {stamp} · {count} ไฟล์ (ไม่รวมโฟลเดอร์ `state/`, `.git/`, `__pycache__/` และไฟล์ `.env`)

## วิธีใช้

1. แตกไฟล์ zip ไว้ที่โฟลเดอร์ที่ต้องการ
2. ตั้งค่าโพสต์ Facebook: คัดลอก `.env.example` เป็น `.env` แล้วเติมค่าตาม `setup/01-facebook-page.md`
3. สร้างพร้อมต์: `python3 scripts/build_prompts.py` แล้วเปิด `prompts/generated/index.md`
4. อ่านลำดับงานทั้งหมดได้จาก `README.md`

## สิ่งที่ตัดออกจากชุดนี้

- `.env` และไฟล์ความลับทุกชนิด — ต้องตั้งค่าเองบนเครื่องปลายทาง
- `state/` — สถานะการโพสต์และ log ที่เกิดจากการรันจริง
- `.git/`, `__pycache__/`, `*.pyc` — ไฟล์ชั่วคราว/ประวัติที่สร้างใหม่ได้

ไฟล์ภาพขนาดใหญ่ (ภาพแบรนด์ทุกแพลตฟอร์ม) และพร้อมต์ทั้ง 30 วันอยู่ในชุดนี้ครบ
"""


def zip_entry(name: str, stamp: str) -> zipfile.ZipInfo:
    """สร้าง ZipInfo ที่เวลาไฟล์คงที่ เพื่อให้ zip เดียวกันได้ไบต์เดิมทุกครั้งที่สร้าง"""
    digits = stamp.replace("-", "")
    year, month, day = int(digits[:4]), int(digits[4:6]), int(digits[6:8])
    info = zipfile.ZipInfo(name, date_time=(year, month, day, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def build_bundle(outdir: Path = DEFAULT_OUTDIR, stamp: str | None = None) -> dict[str, bytes]:
    """คืน dict ของไฟล์ผลลัพธ์ (ไม่เขียนดิสก์) เพื่อให้ทดสอบได้"""
    today = stamp or date.today().strftime("%Y%m%d")
    label = stamp or date.today().isoformat()
    sources = collect_files()
    zip_name = f"kopwang-all-files-{today}.zip"

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in sources.items():
            archive.writestr(zip_entry(name, today), data)
        archive.writestr(zip_entry(BUNDLE_README, today), bundle_readme(label, len(sources)))
    payload = buffer.getvalue()

    manifest = {
        "version": 1,
        "generated_at": label,
        "zip": zip_name,
        "zip_sha256": sha256(payload),
        "zip_bytes": len(payload),
        "file_count": len(sources),
        "files": {name: {"sha256": sha256(data), "bytes": len(data)} for name, data in sources.items()},
        "excluded": sorted(EXCLUDE_DIRS) + sorted(EXCLUDE_FILES) + list(EXCLUDE_SUFFIXES),
    }

    return {
        zip_name: payload,
        "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n",
        "README.md": bundle_readme(label, len(sources)).encode("utf-8"),
    }


def write_bundle(outdir: Path, files: dict[str, bytes]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (outdir / name).write_bytes(data)
    for old in outdir.glob("kopwang-all-files-*.zip"):
        if old.name not in files:
            old.unlink()


def verify_manifest(outdir: Path = DEFAULT_OUTDIR) -> list[str]:
    """เทียบ manifest.json กับไฟล์จริงในโปรเจกต์ (ละเว้น generated_at และไฟล์ของชุดดาวน์โหลดเอง)"""
    manifest_path = outdir / "manifest.json"
    if not manifest_path.exists():
        return [f"ยังไม่มี {display(manifest_path)} — รัน python3 scripts/build_download_bundle.py ก่อน"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = collect_files()
    problems: list[str] = []
    listed = manifest.get("files", {})
    for name in sorted(set(listed) - set(actual)):
        problems.append(f"manifest อ้างไฟล์ที่หายไป: {name}")
    for name in sorted(set(actual) - set(listed)):
        problems.append(f"มีไฟล์ใหม่ที่ยังไม่อยู่ใน manifest: {name}")
    for name in sorted(set(actual) & set(listed)):
        if sha256(actual[name]) != listed[name]["sha256"]:
            problems.append(f"เนื้อหาเปลี่ยน: {name}")
    zip_path = outdir / manifest.get("zip", "")
    if not zip_path.exists():
        problems.append(f"ไม่พบไฟล์ zip: {manifest.get('zip')}")
    elif sha256(zip_path.read_bytes()) != manifest.get("zip_sha256"):
        problems.append("แฮชของ zip ไม่ตรง — สร้างชุดดาวน์โหลดใหม่")
    if manifest.get("file_count") != len(actual):
        problems.append(f"จำนวนไฟล์ใน manifest ({manifest.get('file_count')}) ไม่ตรงกับจริง ({len(actual)})")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="รวมทุกไฟล์โปรเจกต์เป็น zip เดียวสำหรับดาวน์โหลด")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--stamp", help="วันที่ที่ใช้ตั้งชื่อ zip (YYYYMMDD) สำหรับทดสอบ")
    parser.add_argument("--check", action="store_true", help="ตรวจว่า manifest ตรงกับไฟล์จริง")
    args = parser.parse_args()

    if args.check:
        problems = verify_manifest(args.outdir)
        if problems:
            print(f"manifest ไม่ตรงกับไฟล์จริง {len(problems)} รายการ:")
            for item in problems[:20]:
                print(f"  - {item}")
            return 1
        print(f"manifest ตรงกับไฟล์จริงทั้งหมด ({display(args.outdir)})")
        return 0

    files = build_bundle(args.outdir, stamp=args.stamp)
    write_bundle(args.outdir, files)
    manifest = json.loads(files["manifest.json"].decode("utf-8"))
    print(
        f"สร้างชุดดาวน์โหลดที่ {display(args.outdir)}: {manifest['zip']} "
        f"({manifest['file_count']} ไฟล์ · {manifest['zip_bytes'] / 1024 / 1024:.1f} MB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
