#!/usr/bin/env python3
"""สัญญาของ SVG ต้นฉบับ (editable masters) ใน brand/social/

ตรวจว่าไฟล์ SVG หน้าปก/แบนเนอร์:
  - ขนาดและ manifest ตรงกับ PNG ที่ชื่อเดียวกัน
  - ข้อความทุกบรรทัดเป็น <text> จริง ไม่ถูกแปลงเป็น path
  - ใช้คำพูดชุดเดียวกับ spec.json, ฟอนต์ไทยตัวเดียว และไม่มีคำต้องห้าม
  - เรนเดอร์แล้วตำแหน่งเนื้อหาตรงกับ PNG (ต้องมี resvg ใน PATH — ถ้าไม่มีจะรายงาน SKIP)

    python3 tests/brand_svg_test.py
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOCIAL = ROOT / "brand" / "social"
SPEC = json.loads((SOCIAL / "spec.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((SOCIAL / "manifest.json").read_text(encoding="utf-8"))
COPY = SPEC["copy"]
SVG_NS = "{http://www.w3.org/2000/svg}"

TEXT_COUNTS = {
    "cover-facebook": 4,
    "cover-shopee": 7,
    "banner-shopee": 4,
    "cover-tiktok": 5,
}
REQUIRED_TEXT = {
    "cover-facebook": ["wordmark", "tagline", "promise", "cta"],
    "cover-shopee": ["shop_eyebrow", "wordmark", "tagline", "shop_cover_line", "shop_bullets"],
    "banner-shopee": ["wordmark", "shop_banner_line", "offer", "cta"],
    "cover-tiktok": ["eyebrow", "tiktok_line_1", "tiktok_line_2", "tiktok_line", "tiktok_footer"],
}
INK = (20, 22, 28)
THAI = re.compile(r"[\u0E00-\u0E7F]")

results: list[tuple[str, bool | None, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))


def skip(name: str, detail: str) -> None:
    results.append((name, None, detail))


def asset_by_png_suffix(suffix: str) -> dict:
    return next(item for item in SPEC["assets"] if item["path"].endswith(suffix))


def copy_strings(keys: list[str]) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = COPY[key]
        if isinstance(value, list):
            values.extend(value)
        else:
            values.append(value)
    return values


def bbox_of(path: Path) -> tuple[int, int, int, int] | None:
    img = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    ys, xs = np.where(np.abs(img - np.array(INK, dtype=np.int16)).sum(axis=2) > 14)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def text_nodes(root: ET.Element) -> list[ET.Element]:
    return [el for el in root.iter(f"{SVG_NS}text")]


masters = MANIFEST.get("svg_masters", [])
check("manifest มีรายการ SVG masters", len(masters) == 4, f"{len(masters)} รายการ")

renderer = shutil.which("resvg")

for master in masters:
    asset_id = master["id"]
    svg_path = ROOT / master["path"]
    png = asset_by_png_suffix(Path(master["png"]).name)
    name = Path(master["path"]).name

    if not svg_path.exists():
        check(f"{asset_id}: มีไฟล์ SVG", False, master["path"])
        continue

    raw = svg_path.read_bytes()
    check(f"{asset_id}: เป็น SVG (XML)", raw.lstrip().startswith(b"<?xml") or raw.lstrip().startswith(b"<svg"), name)
    check(f"{asset_id}: manifest ตรงกับไฟล์",
          master["bytes"] == len(raw) and master["sha256"] == hashlib.sha256(raw).hexdigest(),
          f"{len(raw)} bytes")
    check(f"{asset_id}: ไฟล์เล็กพอแก้มือ", len(raw) < 50_000, f"{len(raw) / 1024:.1f} KB")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        check(f"{asset_id}: XML อ่านได้", False, str(exc))
        continue

    check(f"{asset_id}: ขนาดกรอบ {png['width']}×{png['height']}",
          root.get("width") == str(png["width"]) and root.get("height") == str(png["height"])
          and root.get("viewBox") == f"0 0 {png['width']} {png['height']}",
          f"{root.get('width')}×{root.get('height')} viewBox={root.get('viewBox')}")
    xml_lang = root.get("{http://www.w3.org/XML/1998/namespace}lang")
    check(f"{asset_id}: ประกาศภาษาไทย", xml_lang == "th", str(xml_lang))
    check(f"{asset_id}: ไม่มีภาพฝัง (เป็นเวกเตอร์/ข้อความล้วน)",
          not list(root.iter(f"{SVG_NS}image")) and not list(root.iter(f"{SVG_NS}foreignObject")))

    texts = text_nodes(root)
    contents = ["".join(el.itertext()).strip() for el in texts]
    check(f"{asset_id}: จำนวน text ตรงกับเลย์เอาต์", len(texts) == TEXT_COUNTS[asset_id],
          f"{len(texts)} บรรทัด (คาด {TEXT_COUNTS[asset_id]})")
    check(f"{asset_id}: ข้อความทุกบรรทัดไม่ว่าง", all(contents), str(contents))

    required = copy_strings(REQUIRED_TEXT[asset_id])
    missing = [value for value in required if value not in contents]
    check(f"{asset_id}: คำพูดครบตาม spec และเป็น text จริง", not missing, ", ".join(missing))

    banned = [word for word in SPEC["rules"]["banned_words"] for value in contents if word in value]
    check(f"{asset_id}: ไม่มีคำต้องห้ามในข้อความ", not banned, ", ".join(sorted(set(banned))))

    bad_font = [el.get("font-family", "") for el in texts if "Noto Sans Thai" not in el.get("font-family", "")]
    check(f"{asset_id}: ทุกข้อความใช้ฟอนต์แบรนด์", not bad_font, ", ".join(bad_font))
    bad_weight = [el.get("font-weight") for el in texts
                  if el.get("font-weight") not in {"400", "500", "600", "700"}]
    check(f"{asset_id}: น้ำหนักฟอนต์อยู่ในชุดที่กำหนด", not bad_weight, ", ".join(map(str, bad_weight)))
    bad_fill = [el.get("fill") for el in texts if not re.fullmatch(r"#[0-9A-F]{6}", el.get("fill", ""))]
    check(f"{asset_id}: ข้อความมีสี hex ชัดเจน", not bad_fill, ", ".join(map(str, bad_fill)))
    check(f"{asset_id}: ไม่ใช้ textLength (ไทยจะถูกบีบ)",
          all("textLength" not in el.attrib for el in texts))
    spaced_thai = [value for el, value in zip(texts, contents)
                   if el.get("letter-spacing") and THAI.search(value)]
    check(f"{asset_id}: ไม่ใส่ letter-spacing กับข้อความไทย", not spaced_thai, ", ".join(spaced_thai))

    style = "".join("".join(el.itertext()) for el in root.iter(f"{SVG_NS}style"))
    check(f"{asset_id}: มี @font-face ของฟอนต์ไทย", "@font-face" in style and "Noto Sans Thai" in style)
    refs = re.findall(r'url\("([^"]+)"\)', style)
    resolved = [(svg_path.parent / ref).resolve() for ref in refs]
    check(f"{asset_id}: path ฟอนต์ชี้ไฟล์ที่มีจริง", bool(resolved) and all(p.exists() for p in resolved),
          ", ".join(str(p.relative_to(ROOT)) for p in resolved))

    png_path = ROOT / png["path"]
    png_bbox = bbox_of(png_path)
    check(f"{asset_id}: มี PNG คู่กันไว้เทียบ", png_path.exists() and png_bbox is not None, str(png_bbox))

    if renderer is None:
        skip(f"{asset_id}: เรนเดอร์ SVG แล้วเทียบตำแหน่งกับ PNG", "ไม่พบ resvg ใน PATH")
        continue

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "render.png"
        proc = subprocess.run(
            [renderer, "--use-font-file", str(ROOT / SPEC["font"]["file"]), "--skip-system-fonts",
             str(svg_path), str(out)],
            capture_output=True, text=True, timeout=60,
        )
        check(f"{asset_id}: เรนเดอร์ SVG ได้", proc.returncode == 0 and out.exists(),
              "ok" if proc.returncode == 0 else (proc.stderr.strip().splitlines() or [""])[-1][:120])
        if proc.returncode == 0 and out.exists():
            with Image.open(out) as im:
                size = im.size
            check(f"{asset_id}: เรนเดอร์ได้ขนาดจริง", size == (png["width"], png["height"]), str(size))
            svg_bbox = bbox_of(out)
            check(f"{asset_id}: ตำแหน่งเนื้อหาตรง PNG ±3px",
                  svg_bbox is not None and png_bbox is not None
                  and all(abs(a - b) <= 3 for a, b in zip(svg_bbox, png_bbox)),
                  f"SVG {svg_bbox} · PNG {png_bbox}")

# ไฟล์โปรไฟล์ไม่ต้องมี SVG — ใช้ brand/logo/k-bar.svg เป็นต้นฉบับเวกเตอร์อยู่แล้ว
check("โปรไฟล์ใช้ brand/logo/k-bar.svg เป็นเวกเตอร์ต้นฉบับ",
      (ROOT / "brand" / "logo" / "k-bar.svg").exists())

failed = sum(1 for _, ok, _ in results if ok is False)
skipped = sum(1 for _, ok, _ in results if ok is None)
print("SVG ต้นฉบับ Kopwang — brand/social/{cover,banner}/")
for name, ok, detail in results:
    mark = "PASS" if ok else ("SKIP" if ok is None else "FAIL")
    print(f"  {mark}  {name}" + (f" — {detail}" if detail else ""))
print(f"\n{len(results) - failed - skipped}/{len(results) - skipped} ผ่าน"
      + (f" · {skipped} ข้าม (ไม่มี resvg)" if skipped else ""))
if failed:
    print(f"{failed} รายการไม่ผ่าน")
raise SystemExit(1 if failed else 0)
