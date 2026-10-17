#!/usr/bin/env python3
"""ทดสอบชุดดาวน์โหลดทุกไฟล์ (scripts/build_download_bundle.py)

ตรวจว่า
  - เก็บไฟล์ครบตามที่ควรแจก และตัด `.env` / `state/` / `.git/` / `__pycache__` ออกจริง
  - zip เปิดได้ ทุกไฟล์ใน manifest อยู่จริงและแฮชตรง
  - สร้างซ้ำด้วยวันที่เดียวกันได้ผลเท่าเดิม และ manifest ที่ commit ตรงกับไฟล์จริง
  - ตรวจเจอเมื่อ manifest ไม่ตรงกับไฟล์ (กันส่งชุดเก่าออกไป)

    python3 tests/download_bundle_test.py
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_download_bundle as bundle  # noqa: E402

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


def phase_collect() -> None:
    print("== การเลือกไฟล์ ==")
    files = bundle.collect_files()
    names = set(files)
    check("เก็บไฟล์หลักของโปรเจกต์ครบ", all(
        name in names
        for name in (
            "README.md",
            ".env.example",
            "scripts/build_prompts.py",
            "prompts/system.json",
            "prompts/generated/index.md",
            "prompts/generated/manifest.json",
            "content/plan.json",
            "data/content_seeds.json",
            "brand/brand-kit.md",
            "tests/prompt_system_test.py",
        )
    ))
    check("ไม่เก็บไฟล์ .env จริง", not any(n == ".env" or (n.startswith(".env.") and n != ".env.example") for n in names))
    check("ไม่เก็บ state/ และ log", not any(n.startswith("state/") for n in names))
    check("ไม่เก็บ .git/ และ __pycache__", not any(n.startswith(".git/") or "__pycache__" in n for n in names))
    check("ไม่เก็บไฟล์ .pyc", not any(n.endswith(".pyc") for n in names))
    check("ไม่มีไฟล์ของชุดดาวน์โหลดปนเข้าไป", not any(n.startswith("downloads/") for n in names))


def phase_root_archives() -> None:
    print("== ไฟล์ zip ที่วางไว้รากโปรเจกต์ ==")
    with tempfile.TemporaryDirectory() as tmp_name:
        root = Path(tmp_name)
        (root / "sub").mkdir()
        (root / "kopwang-all-files.zip").write_bytes(b"zip")
        (root / "kopwang-all-files.tar.gz").write_bytes(b"gz")
        (root / "keep.txt").write_text("x", encoding="utf-8")
        (root / "sub" / "keep.zip").write_bytes(b"zip")
        files = bundle.collect_files(root)
        check("ไม่เก็บ zip รากโปรเจกต์ซ้อนเข้าไปในชุดใหม่", "kopwang-all-files.zip" not in files and "kopwang-all-files.tar.gz" not in files)
        check("ยังเก็บไฟล์อื่นที่รากและ zip ในโฟลเดอร์ย่อย", set(files) == {"keep.txt", "sub/keep.zip"}, str(sorted(files)))


def phase_build() -> dict[str, bytes]:
    print("\n== สร้างและตรวจ zip ==")
    first = bundle.build_bundle(stamp="20260101")
    second = bundle.build_bundle(stamp="20260101")
    check("สร้างซ้ำด้วยวันที่เดียวกันได้ผลเท่าเดิม", first == second)
    check("มี zip, manifest.json และ README.md", set(first) == {"kopwang-all-files-20260101.zip", "manifest.json", "README.md"})

    manifest = json.loads(first["manifest.json"].decode("utf-8"))
    sources = bundle.collect_files()
    check("manifest นับจำนวนไฟล์ตรงกับไฟล์จริง", manifest["file_count"] == len(sources), f"{manifest['file_count']} vs {len(sources)}")
    check("manifest แฮช zip ตรงกับไฟล์ zip", bundle.sha256(first[manifest["zip"]]) == manifest["zip_sha256"])

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        bundle.write_bundle(tmp, first)
        check("เขียนไฟล์ครบ 3 ไฟล์", len(list(tmp.iterdir())) == 3)
        zip_path = tmp / manifest["zip"]
        with zipfile.ZipFile(zip_path) as archive:
            bad = archive.testzip()
            names = set(archive.namelist())
            contents = {name: archive.read(name) for name in names}
        check("zip เปิดได้และไม่มีความเสียหาย", bad is None, str(bad))
        check("zip มีไฟล์ทุกไฟล์ใน manifest", set(manifest["files"]).issubset(names), str(sorted(set(manifest["files"]) - names)[:3]))
        check("zip มี README สำหรับผู้รับ", "DOWNLOAD-README.md" in names)
        check("zip ไม่มี .env/state/.git", not any(
            n == ".env" or n.startswith(("state/", ".git/")) or "__pycache__" in n for n in names
        ))
        mismatched = [n for n in manifest["files"] if bundle.sha256(contents[n]) != manifest["files"][n]["sha256"]]
        check("แฮชไฟล์ใน zip ตรงกับ manifest", not mismatched, ", ".join(mismatched[:3]))

        problems = bundle.verify_manifest(tmp)
        check("verify_manifest ผ่านกับชุดที่เพิ่งสร้าง (วันที่ย้อนหลัง)", not problems, "; ".join(problems[:2]))

        # ทำ manifest ให้อ้างไฟล์ที่ไม่มีอยู่ → ต้องตรวจเจอ
        tampered = json.loads((tmp / "manifest.json").read_text(encoding="utf-8"))
        tampered["files"]["ghost-file.md"] = {"sha256": "0" * 64, "bytes": 1}
        tampered["file_count"] += 1
        (tmp / "manifest.json").write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
        problems = bundle.verify_manifest(tmp)
        check("จับ manifest ที่อ้างไฟล์เกิน", any("ghost-file.md" in p for p in problems), "; ".join(problems[:2]))
    return first


def phase_repo() -> None:
    print("\n== ชุดที่อยู่ในโปรเจกต์ ==")
    problems = bundle.verify_manifest(bundle.DEFAULT_OUTDIR)
    check("downloads/ ในโปรเจกต์ตรงกับไฟล์จริงทุกไฟล์", not problems, "; ".join(problems[:3]))
    manifest_path = bundle.DEFAULT_OUTDIR / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        check("manifest บอกจำนวนไฟล์และวันที่สร้าง", manifest.get("file_count", 0) > 100 and bool(manifest.get("generated_at")), str(manifest.get("generated_at")))
        check("zip ในโปรเจกต์เปิดได้", zipfile.ZipFile(bundle.DEFAULT_OUTDIR / manifest["zip"]).testzip() is None)
    else:
        check("มี manifest ของชุดดาวน์โหลดในโปรเจกต์", False, "รัน scripts/build_download_bundle.py ก่อน")

    original_argv = sys.argv
    sys.argv = ["build_download_bundle.py", "--check"]
    try:
        rc, output = capture(bundle.main)
    finally:
        sys.argv = original_argv
    check("CLI --check ผ่าน", rc == 0, output.strip())


def main() -> int:
    phase_collect()
    phase_root_archives()
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
