#!/usr/bin/env python3
"""สัญญาของชุดภาพแบรนด์ Kopwang (brand/social/)

ตรวจไฟล์จริงกับสเปกใน brand/social/spec.json และ manifest.json: ขนาด, น้ำหนักไฟล์,
แฮช, ความสม่ำเสมอของอวตารทั้ง 3 ช่องทาง, โซนปลอดภัย, สีที่อนุญาต, คอนทราสต์,
คำต้องห้าม และไฟล์ตัวอย่างสำหรับตรวจงาน

    python3 tests/brand_assets_test.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOCIAL = ROOT / "brand" / "social"
SPEC = json.loads((SOCIAL / "spec.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((SOCIAL / "manifest.json").read_text(encoding="utf-8"))
ASSETS = {item["id"]: item for item in MANIFEST["assets"]}
BY_ID = {item["id"]: item for item in SPEC["assets"]}

PALETTE = {
    "ink": (20, 22, 28),
    "amber": (255, 176, 32),
    "cream": (245, 239, 226),
    "mint": (37, 194, 129),
}

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))


def record(name: str, ok: bool, detail: str = "") -> None:
    check(name, ok, detail)


def path_of(asset_id: str) -> Path:
    return ROOT / ASSETS[asset_id]["path"]


def pixels(asset_id: str) -> np.ndarray:
    return np.asarray(Image.open(path_of(asset_id)).convert("RGB"), dtype=np.int16)


def bbox_of_content(img: np.ndarray, tolerance: int = 14) -> tuple[int, int, int, int] | None:
    """กรอบพิกเซลที่ต่างจากพื้น Ink เกิน tolerance (ผลบวกค่าต่างสามช่อง)"""
    distance = np.abs(img - np.array(PALETTE["ink"], dtype=np.int16)).sum(axis=2)
    ys, xs = np.where(distance > tolerance)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def close_share(img: np.ndarray, color: tuple[int, int, int], tolerance: float = 40) -> float:
    return float((np.linalg.norm(img - np.array(color, dtype=np.float32), axis=2) <= tolerance).mean())


def luminance(color: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    lighter, darker = sorted((luminance(a), luminance(b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


# 1. ไฟล์ตรงกับสเปกและ manifest ------------------------------------------------

for asset_id, item in BY_ID.items():
    path = ROOT / item["path"]
    if not path.exists():
        record(f"{asset_id}: มีไฟล์ {item['path']}", False)
        continue
    raw = path.read_bytes()
    record(f"{asset_id}: เป็น PNG จริง", raw[:8] == b"\x89PNG\r\n\x1a\n", raw[:8].hex())
    with Image.open(path) as im:
        width, height = im.size
        mode = im.mode
    record(f"{asset_id}: ขนาด {item['width']}×{item['height']}", (width, height) == (item["width"], item["height"]),
           f"{width}×{height}")
    record(f"{asset_id}: manifest ตรงกับไฟล์", ASSETS[asset_id]["bytes"] == len(raw)
           and ASSETS[asset_id]["sha256"] == hashlib.sha256(raw).hexdigest(),
           f"{len(raw)} bytes")
    record(f"{asset_id}: ไม่เกินลิมิตแพลตฟอร์ม", len(raw) <= item["max_bytes"],
           f"{len(raw) / 1024:.1f} KB ≤ {item['max_bytes'] / 1024:.0f} KB")
    record(f"{asset_id}: บันทึกเป็น RGB", mode == "RGB", mode)

# 2. ครบทั้ง 3 ช่องทาง ------------------------------------------------------

for channel in ("facebook", "tiktok", "shopee"):
    for role in ("profile", "cover"):
        record(f"{channel}: มีไฟล์ {role}",
               any(a["channel"] == channel and a["role"] == role for a in SPEC["assets"]))
record("shopee: มีแบนเนอร์ร้าน", any(a["role"] == "banner" for a in SPEC["assets"]))
record("มีไฟล์ตรวจงาน (preview) ครบ", len([a for a in SPEC["assets"] if a["role"] == "preview"]) >= 3)

# 3. อวตารทั้ง 3 ช่องทางมาจากภาพเดียวกันและไม่หลุดวงกลม ----------------------

master = pixels("profile-master")
record("profile-master: เป็นสี่เหลี่ยมจัตุรัส", master.shape[0] == master.shape[1],
       f"{master.shape[1]}×{master.shape[0]}")

master_img = Image.open(path_of("profile-master")).convert("RGB")
for asset_id, size in (("profile-facebook", 1024), ("profile-tiktok", 200), ("profile-shopee", 500)):
    expected = np.asarray(master_img.resize((size, size), Image.LANCZOS), dtype=np.int16)
    diff = float(np.abs(pixels(asset_id) - expected).mean())
    record(f"{asset_id}: ตรงกับ master หลังย่อ", diff <= 1.0, f"ผลต่างเฉลี่ย {diff:.3f}")

for asset_id in ("profile-master", "profile-facebook", "profile-tiktok", "profile-shopee"):
    img = pixels(asset_id)
    h, w = img.shape[:2]
    distance = np.abs(img - np.array(PALETTE["ink"], dtype=np.int16)).sum(axis=2)
    ys, xs = np.where(distance > 14)
    radii = np.sqrt((xs - (w - 1) / 2) ** 2 + (ys - (h - 1) / 2) ** 2)
    limit = 0.42 * min(w, h) + 2
    record(f"{asset_id}: สัญลักษณ์อยู่ในวงกลม Ø 84%", float(radii.max()) <= limit,
           f"รัศมีไกลสุด {radii.max():.1f} ≤ {limit:.1f}")

    cream = float(((img[:, :, 0] > 150) & (img[:, :, 1] > 140) & (img[:, :, 2] > 120)).mean())
    record(f"{asset_id}: ไม่มีตัวอักษรสีครีมในอวตาร", cream == 0, f"{cream:.4%} ของพื้นที่")

# 4. โซนปลอดภัยของหน้าปกและแบนเนอร์ ----------------------------------------

zone = SPEC["safe_zones"]

fb = pixels("cover-facebook")
fb_bbox = bbox_of_content(fb)
fb_safe_x = (fb.shape[1] - zone["facebook_cover_mobile_width"]) / 2
fb_safe_y = (fb.shape[0] - zone["facebook_cover_mobile_height"]) / 2
record("facebook cover: เนื้อหาอยู่ในโซนปลอดภัย 640×312",
       fb_bbox is not None and fb_bbox[0] >= fb_safe_x - 1 and fb_bbox[2] <= fb_safe_x + zone["facebook_cover_mobile_width"] + 1
       and fb_bbox[1] >= fb_safe_y - 1 and fb_bbox[3] <= fb_safe_y + zone["facebook_cover_mobile_height"] + 1,
       str(fb_bbox))
overlap = zone["facebook_cover_profile_overlap"]
record("facebook cover: ไม่มีเนื้อหามุมซ้ายล่างที่รูปโปรไฟล์ทับ",
       fb_bbox is not None and not (fb_bbox[0] < overlap["x"] + overlap["width"] and fb_bbox[3] > overlap["y"]),
       str(fb_bbox))
record("facebook cover: ไฟล์เล็กกว่า 100 KB ตามคำแนะนำของ Facebook",
       ASSETS["cover-facebook"]["bytes"] < 100_000, f"{ASSETS['cover-facebook']['bytes'] / 1024:.1f} KB")

for asset_id, margin_key in (("cover-shopee", "shopee_margin"), ("banner-shopee", "shopee_banner_margin")):
    img = pixels(asset_id)
    bbox = bbox_of_content(img)
    margin = zone[margin_key]
    record(f"{asset_id}: เนื้อหาอยู่ในขอบ {margin}px",
           bbox is not None and bbox[0] >= margin and bbox[1] >= margin
           and bbox[2] <= img.shape[1] - margin and bbox[3] <= img.shape[0] - margin,
           str(bbox))

tt = pixels("cover-tiktok")
tt_bbox = bbox_of_content(tt)
record("tiktok cover: ไม่ชนขอบซ้าย/ขวา",
       tt_bbox is not None and tt_bbox[0] >= zone["tiktok_cover_side_padding"]
       and tt_bbox[2] <= tt.shape[1] - zone["tiktok_cover_side_padding"], str(tt_bbox))
record("tiktok cover: พ้นขอบบน",
       tt_bbox is not None and tt_bbox[1] >= zone["tiktok_cover_top_padding"], str(tt_bbox))
record("tiktok cover: พ้นพื้นที่ UI ด้านล่าง",
       tt_bbox is not None and tt_bbox[3] <= tt.shape[0] - zone["tiktok_cover_bottom_padding"], str(tt_bbox))

# 5. สี มินต์ และคอนทราสต์ --------------------------------------------------

for asset_id in ("cover-facebook", "cover-shopee", "cover-tiktok", "banner-shopee"):
    share = close_share(pixels(asset_id), PALETTE["mint"], tolerance=50)
    record(f"{asset_id}: Mint ≤ 10% ของพื้นที่", share <= 0.10, f"{share:.3%}")

for name, color in (("Amber", PALETTE["amber"]), ("Cream", PALETTE["cream"]), ("Mint", PALETTE["mint"])):
    ratio = contrast(color, PALETTE["ink"])
    record(f"คอนทราสต์ {name} บน Ink ≥ 4.5:1", ratio >= 4.5, f"{ratio:.1f}:1")

# 6. คำพูดต้องไม่สัญญารายได้ ------------------------------------------------

def strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for item in value for s in strings(item)]
    if isinstance(value, dict):
        return [s for item in value.values() for s in strings(item)]
    return []


copy_text = strings(SPEC["copy"])
banned_hits = [word for word in SPEC["rules"]["banned_words"] for text in copy_text if word in text]
record("คำที่ใช้ในภาพไม่มีคำต้องห้าม", not banned_hits, ", ".join(sorted(set(banned_hits))))

# 7. ฟอนต์และลิขสิทธิ์ ------------------------------------------------------

font_file = ROOT / SPEC["font"]["file"]
license_file = ROOT / SPEC["font"]["license"]
record("มีไฟล์ฟอนต์ไทย", font_file.exists(), SPEC["font"]["file"])
record("ฟอนต์ตรงกับ manifest",
       font_file.exists() and hashlib.sha256(font_file.read_bytes()).hexdigest() == MANIFEST["font"]["sha256"])
record("มีไฟล์ลิขสิทธิ์ฟอนต์ (OFL)",
       license_file.exists() and "SIL Open Font License" in license_file.read_text(encoding="utf-8"))


# 8. ไฟล์ตรวจงาน ------------------------------------------------------------

record("contact sheet มีภาพรวมทุกชิ้น", ASSETS["contact-sheet"]["width"] == 1600
       and ASSETS["contact-sheet"]["height"] == 1300, "1600×1300")
record("ภาพตรวจการครอปวงกลมมีจริง", path_of("preview-profile-crops").exists())
record("ภาพตรวจโซนปลอดภัย Facebook มีจริง", path_of("preview-facebook-safe").exists())
fb_manifest_bbox = ASSETS["cover-facebook"]["content_bbox"]
record("manifest บันทึกกรอบเนื้อหาตรงกับภาพจริง",
       fb_manifest_bbox is not None and tuple(fb_manifest_bbox) == bbox_of_content(fb),
       f"manifest {fb_manifest_bbox} · ภาพจริง {bbox_of_content(fb)}")

# 9. สรุป -------------------------------------------------------------------

print("ชุดภาพแบรนด์ Kopwang — brand/social/")
for name, ok, detail in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
failures = sum(1 for _, ok, _ in results if not ok)
print(f"\n{len(results) - failures}/{len(results)} ผ่าน")
if failures:
    print(f"{failures} รายการไม่ผ่าน")
raise SystemExit(1 if failures else 0)
