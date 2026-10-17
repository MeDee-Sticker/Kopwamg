#!/usr/bin/env python3
"""สร้างชุดภาพแบรนด์ Kopwang สำหรับ Facebook Page, TikTok และ Shopee

อ่านสเปกจาก brand/social/spec.json (ขนาด, คำที่ใช้, โซนปลอดภัย) แล้ววาดภาพใหม่
ทั้งหมดจากเรขาคณิตเดียวกับโลโก้ K-Bar — ไม่มีภาพสต็อก ไม่มีไล่เฉด และไม่ต้องพึ่ง
เครื่องมือออกแบบภายนอก

    python3 scripts/build_brand_assets.py

ผลลัพธ์: brand/social/{profile,cover,banner,preview}/*.png + manifest.json
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SOCIAL = ROOT / "brand" / "social"
SPEC_PATH = SOCIAL / "spec.json"

# เรขาคณิตของ K-Bar ในกรอบ 1024 (ต้นฉบับ: brand/logo/k-bar.svg)
K_BOX = 484          # ความสูงจริงรวมหัวเส้นกลม
K_STROKE = 116
K_LEFT, K_RIGHT = 328, 696
K_TOP, K_BOTTOM = 270, 754

THAI_LAYOUT = getattr(ImageFont.Layout, "RAQM", ImageFont.Layout.BASIC)
SS = 2               # วาดใหญ่กว่าขนาดจริง 2 เท่าแล้วย่อ -> ขอบเนียน


# ---------------------------------------------------------------- utilities

def rgb(hex_value: str) -> tuple[int, int, int]:
    value = hex_value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


INK = rgb("#14161C")
AMBER = rgb("#FFB020")
CREAM = rgb("#F5EFE2")
MINT = rgb("#25C281")


def mix(fg: tuple[int, int, int], bg: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
    """สีทึบที่ได้จากการวาง fg ทับ bg ด้วย alpha (ใช้แทน RGBA เพื่อคุมคอนทราสต์)"""
    return tuple(round(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


SPEC = load_spec()
COPY = SPEC["copy"]
FONT_PATH = ROOT / SPEC["font"]["file"]
WEIGHTS = SPEC["font"]["weights"]

_font_cache: dict[tuple[int, int], ImageFont.FreeTypeFont] = {}


def font(size: int, weight: str = "semibold") -> ImageFont.FreeTypeFont:
    key = (round(size), WEIGHTS[weight])
    if key not in _font_cache:
        f = ImageFont.truetype(str(FONT_PATH), size=key[0], layout_engine=THAI_LAYOUT)
        f.set_variation_by_axes([WEIGHTS[weight], 100])
        _font_cache[key] = f
    return _font_cache[key]


def text_width(draw: ImageDraw.ImageDraw, value: str, f: ImageFont.FreeTypeFont, tracking: float = 0) -> float:
    if not tracking:
        return draw.textlength(value, font=f)
    return sum(draw.textlength(ch, font=f) for ch in value) + tracking * (len(value) - 1)


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    value: str,
    size: int,
    color: tuple[int, int, int],
    *,
    weight: str = "semibold",
    anchor: str = "ls",
    tracking: float = 0,
) -> float:
    """วาดข้อความ (รองรับ Thai shaping ผ่าน raqm) คืนความกว้างที่วาดจริง"""
    f = font(size, weight)
    if not tracking:
        draw.text(xy, value, font=f, fill=color, anchor=anchor)
        return draw.textlength(value, font=f)

    total = text_width(draw, value, f, tracking)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    for ch in value:
        draw.text((x, y), ch, font=f, fill=color, anchor="l" + anchor[1:])
        x += draw.textlength(ch, font=f) + tracking
    return total


def fit_text(
    draw: ImageDraw.ImageDraw,
    value: str,
    size: int,
    max_width: float,
    weight: str = "semibold",
    tracking: float = 0,
) -> int:
    """ลดขนาดฟอนต์ลงทีละ 1px จนกว่าจะพอดีความกว้างที่กำหนด"""
    while size > 8 and text_width(draw, value, font(size, weight), tracking) > max_width:
        size -= 1
    return size


def k_mark(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    height: float,
    color: tuple[int, int, int],
    stroke_ratio: float = K_STROKE / K_BOX,
) -> None:
    """วาดสัญลักษณ์ K-Bar โดยคงสัดส่วนเดียวกับ brand/logo/k-bar.svg"""
    s = height / K_BOX
    stroke = K_STROKE * s
    lx, rx = K_LEFT * s, K_RIGHT * s
    top, bottom = K_TOP * s, K_BOTTOM * s
    ox, oy = cx - 512 * s, cy - 512 * s
    width = max(1, round(stroke))
    for a, b in (
        ((lx, top), (lx, bottom)),
        ((lx, 512 * s), (rx, top)),
        ((lx, 512 * s), (rx, bottom)),
    ):
        draw.line([(ox + a[0], oy + a[1]), (ox + b[0], oy + b[1])], fill=color, width=width)
    for px, py in ((lx, top), (lx, bottom), (rx, top), (rx, bottom), (lx, 512 * s)):
        r = stroke / 2
        draw.ellipse((ox + px - r, oy + py - r, ox + px + r, oy + py + r), fill=color)


def rounded_bar(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float], color, radius: float) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=color)


def dashed_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    color: tuple[int, int, int],
    width: int = 2,
    dash: int = 14,
    gap: int = 10,
) -> None:
    x0, y0, x1, y1 = box
    for start, end, horizontal in (
        ((x0, y0), (x1, y0), True),
        ((x0, y1), (x1, y1), True),
        ((x0, y0), (x0, y1), False),
        ((x1, y0), (x1, y1), False),
    ):
        length = (end[0] - start[0]) if horizontal else (end[1] - start[1])
        pos = 0.0
        while pos < length:
            seg = min(dash, length - pos)
            if horizontal:
                draw.line([(start[0] + pos, start[1]), (start[0] + pos + seg, start[1])], fill=color, width=width)
            else:
                draw.line([(start[0], start[1] + pos), (start[0], start[1] + pos + seg)], fill=color, width=width)
            pos += dash + gap


def day_ticks(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    radius_inner: float,
    radius_outer: float,
    color: tuple[int, int, int],
    accent: tuple[int, int, int],
    width: int,
) -> None:
    """วงแหวน 30 ขีด = 30 วัน (ขีดสุดท้ายเป็นสี Mint = วันที่ทำสำเร็จ)"""
    for day in range(30):
        angle = math.radians(-90 + day * 12)
        inner = (cx + radius_inner * math.cos(angle), cy + radius_inner * math.sin(angle))
        outer = (cx + radius_outer * math.cos(angle), cy + radius_outer * math.sin(angle))
        draw.line([inner, outer], fill=accent if day == 29 else color, width=width)


def aa_ring(img: Image.Image, box: tuple[int, int, int, int], color: tuple[int, int, int], width: int = 2) -> None:
    """วงแหวนบางแบบ anti-alias (วาด 4 เท่าแล้วย่อ) สำหรับภาพตัวอย่างบนพื้นเข้ม"""
    scale = 4
    mask = Image.new("L", (img.width * scale, img.height * scale), 0)
    ImageDraw.Draw(mask).ellipse([c * scale for c in box], outline=255, width=width * scale)
    img.paste(Image.new("RGB", img.size, color), (0, 0), mask.resize(img.size, Image.LANCZOS))


def save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path, format="PNG", optimize=True)


def content_bbox(img: Image.Image, background: tuple[int, int, int] = INK, tolerance: int = 14) -> list[int] | None:
    """กรอบของพิกเซลที่ไม่ใช่สีพื้น — ใช้ตรวจว่าเนื้อหาไม่ล้ำโซนปลอดภัย"""
    diff = Image.new("L", img.size, 0)
    src = img.convert("RGB")
    px, out = src.load(), diff.load()
    width, height = img.size
    for y in range(height):
        for x in range(width):
            r, g, b = px[x, y]
            if abs(r - background[0]) + abs(g - background[1]) + abs(b - background[2]) > tolerance:
                out[x, y] = 255
    return list(diff.getbbox()) if diff.getbbox() else None


# ------------------------------------------------------------------ artwork

def render_profile(size: int) -> Image.Image:
    """อวตาร = สัญลักษณ์ล้วนบนพื้น Ink (ห้ามมีตัวอักษร ตาม brand-kit)"""
    canvas = size * SS
    img = Image.new("RGB", (canvas, canvas), INK)
    draw = ImageDraw.Draw(img)
    k_mark(draw, canvas / 2, canvas / 2, canvas * 0.55, AMBER)
    return img.resize((size, size), Image.LANCZOS)


def render_facebook_cover() -> Image.Image:
    w, h = 851, 315
    img = Image.new("RGB", (w * SS, h * SS), INK)
    d = ImageDraw.Draw(img)
    s = SS

    left = 200
    draw_text(d, (left * s, 126 * s), COPY["wordmark"], 58 * s, CREAM, weight="bold")
    d.rounded_rectangle((left * s, 146 * s, (left + 58) * s, 151 * s), radius=2.5 * s, fill=AMBER)
    tagline_size = fit_text(d, COPY["tagline"], 24 * s, 340 * s, "semibold")
    draw_text(d, (left * s, 190 * s), COPY["tagline"], tagline_size, CREAM, weight="semibold")
    draw_text(d, (left * s, 221 * s), COPY["promise"], 15 * s, mix(CREAM, INK, 0.72), weight="regular")

    cta_font = 15 * s
    cta_w = text_width(d, COPY["cta"], font(cta_font, "medium"))
    d.rounded_rectangle(
        (left * s, 243 * s, left * s + cta_w + 30 * s, 281 * s),
        radius=19 * s,
        outline=AMBER,
        width=max(1, round(1.5 * s)),
    )
    draw_text(d, (left * s + 15 * s, 269 * s), COPY["cta"], cta_font, AMBER, weight="medium")

    # 30 วัน = ขีด 30 อัน 6×5 (อ่านเป็นปฏิทิน ไม่ใช่กราฟกำไร)
    tick_w, tick_h, gap = 8 * s, 22 * s, 11 * s
    grid_w = 6 * tick_w + 5 * gap
    grid_x, grid_y = 739 * s - grid_w, 78 * s
    for i in range(30):
        col, row = i % 6, i // 6
        x = grid_x + col * (tick_w + gap)
        y = grid_y + row * (tick_h + gap)
        color = AMBER if i < 12 else mix(CREAM, INK, 0.34)
        rounded_bar(d, (x, y, x + tick_w, y + tick_h), color, radius=tick_w / 2)

    return img.resize((w, h), Image.LANCZOS)


def render_shopee_cover() -> Image.Image:
    w, h = 1200, 675
    img = Image.new("RGB", (w * SS, h * SS), INK)
    d = ImageDraw.Draw(img)
    s = SS

    left = 96
    draw_text(d, (left * s, 132 * s), COPY["shop_eyebrow"], 13 * s, AMBER, weight="semibold", tracking=3 * s)
    draw_text(d, (left * s, 268 * s), COPY["wordmark"], 92 * s, CREAM, weight="bold")
    d.rounded_rectangle((left * s, 300 * s, (left + 76) * s, 307 * s), radius=3.5 * s, fill=AMBER)
    tagline_size = fit_text(d, COPY["tagline"], 34 * s, 560 * s, "semibold")
    draw_text(d, (left * s, 356 * s), COPY["tagline"], tagline_size, CREAM, weight="semibold")
    draw_text(d, (left * s, 398 * s), COPY["shop_cover_line"], 21 * s, mix(CREAM, INK, 0.7), weight="regular")

    for i, line in enumerate(COPY["shop_bullets"]):
        y = (462 + i * 44) * s
        d.rounded_rectangle((left * s, (y / s - 7) * s, (left + 7) * s, (y / s) * s), radius=1 * s, fill=AMBER)
        draw_text(d, ((left + 22) * s, y), line, 20 * s, mix(CREAM, INK, 0.84), weight="regular")

    cx, cy = 850 * s, 337 * s
    day_ticks(d, cx, cy, 224 * s, 256 * s, mix(CREAM, INK, 0.32), MINT, max(1, round(3.2 * s)))
    k_mark(d, cx, cy, 250 * s, AMBER)

    return img.resize((w, h), Image.LANCZOS)


def render_shopee_banner() -> Image.Image:
    w, h = 1200, 300
    img = Image.new("RGB", (w * SS, h * SS), INK)
    d = ImageDraw.Draw(img)
    s = SS

    k_mark(d, 140 * s, 150 * s, 118 * s, AMBER)
    d.rounded_rectangle((208 * s, 72 * s, 210 * s, 228 * s), radius=1 * s, fill=mix(CREAM, INK, 0.28))

    draw_text(d, (240 * s, 136 * s), COPY["wordmark"], 44 * s, CREAM, weight="bold")
    draw_text(d, (240 * s, 176 * s), COPY["shop_banner_line"], 18 * s, mix(CREAM, INK, 0.72), weight="regular")

    d.rounded_rectangle((560 * s, 143 * s, 567 * s, 150 * s), radius=1 * s, fill=AMBER)
    draw_text(d, (584 * s, 157 * s), COPY["offer"], 20 * s, mix(CREAM, INK, 0.84), weight="medium")

    cta_font = 17 * s
    cta_w = text_width(d, COPY["cta"], font(cta_font, "medium"))
    box = ((1200 - 60) * s - cta_w - 32 * s, 126 * s, (1200 - 60) * s, 174 * s)
    d.rounded_rectangle(box, radius=24 * s, outline=AMBER, width=max(1, round(1.5 * s)))
    draw_text(d, (box[0] + 16 * s, 158 * s), COPY["cta"], cta_font, AMBER, weight="medium")

    return img.resize((w, h), Image.LANCZOS)


def render_tiktok_cover() -> Image.Image:
    """TikTok ไม่มีภาพหน้าปกโปรไฟล์ — ใช้เป็นภาพปกคลิปแนวตั้งแทน"""
    w, h = 1080, 1920
    img = Image.new("RGB", (w * SS, h * SS), INK)
    d = ImageDraw.Draw(img)
    s = SS

    draw_text(d, (540 * s, 336 * s), COPY["eyebrow"], 20 * s, AMBER, weight="semibold", anchor="ms", tracking=6 * s)
    k_mark(d, 540 * s, 620 * s, 300 * s, AMBER)

    line1 = COPY["tiktok_line_1"]
    line2 = COPY["tiktok_line_2"]
    size1 = fit_text(d, line1, 108 * s, 760 * s, "bold")
    size2 = fit_text(d, line2, 108 * s, 760 * s, "bold")
    draw_text(d, (540 * s, 1060 * s), line1, min(size1, size2), CREAM, weight="bold", anchor="ms")
    draw_text(d, (540 * s, 1188 * s), line2, min(size1, size2), AMBER, weight="bold", anchor="ms")
    draw_text(d, (540 * s, 1274 * s), COPY["tiktok_line"], 26 * s, mix(CREAM, INK, 0.74), weight="regular", anchor="ms")

    d.rounded_rectangle((410 * s, 1340 * s, 670 * s, 1343 * s), radius=1.5 * s, fill=mix(CREAM, INK, 0.3))
    draw_text(d, (540 * s, 1398 * s), COPY["tiktok_footer"], 22 * s, mix(CREAM, INK, 0.62), weight="medium", anchor="ms")

    return img.resize((w, h), Image.LANCZOS)


# ------------------------------------------------------------------ previews

def render_facebook_safe_preview(cover: Image.Image) -> Image.Image:
    """ภาพตรวจงาน: กรอบโซนปลอดภัย + พื้นที่ที่รูปโปรไฟล์จะทับ"""
    img = cover.copy()
    d = ImageDraw.Draw(img, "RGBA")
    zone = SPEC["safe_zones"]
    x0 = (851 - zone["facebook_cover_mobile_width"]) / 2
    y0 = (315 - zone["facebook_cover_mobile_height"]) / 2
    dashed_rect(d, (x0, y0, x0 + zone["facebook_cover_mobile_width"], y0 + zone["facebook_cover_mobile_height"]),
                MINT, width=2)
    overlap = zone["facebook_cover_profile_overlap"]
    d.rectangle((overlap["x"], overlap["y"], overlap["x"] + overlap["width"], overlap["y"] + overlap["height"]),
                fill=(255, 176, 32, 36), outline=AMBER, width=2)
    label = "โซนปลอดภัย 640×312"
    d.rectangle((x0 + 8, y0 + 8, x0 + 8 + 176, y0 + 34), fill=(20, 22, 28, 220))
    draw_text(d, (x0 + 16, y0 + 27), label, 13, MINT, weight="medium")
    d.rectangle((overlap["x"] + 6, overlap["y"] + 8, overlap["x"] + 150, overlap["y"] + 32), fill=(20, 22, 28, 220))
    draw_text(d, (overlap["x"] + 12, overlap["y"] + 26), "รูปโปรไฟล์ทับ", 12, AMBER, weight="medium")
    return img


def render_profile_crops(master: Image.Image) -> Image.Image:
    """ภาพตรวจงาน: อวตารเมื่อถูกครอปเป็นวงกลมบนพื้นอ่อนและพื้นเข้ม"""
    w, h = 1600, 760
    img = Image.new("RGB", (w, h), CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 380, w, 760), fill=INK)

    sizes = [(200, "200 px · TikTok"), (120, "120 px"), (64, "64 px · favicon")]
    for row, bg, label_color in ((0, CREAM, INK), (1, INK, CREAM)):
        cy = 170 if row == 0 else 550
        x = 250
        for size, label in sizes:
            mask_ss = Image.new("L", (size * 4, size * 4), 0)
            ImageDraw.Draw(mask_ss).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
            circle = mask_ss.resize((size, size), Image.LANCZOS)
            thumb = master.resize((size, size), Image.LANCZOS)
            offset = (x - size // 2, cy - size // 2)
            img.paste(thumb, offset, circle)
            if row == 1:
                aa_ring(img, (offset[0], offset[1], offset[0] + size - 1, offset[1] + size - 1),
                        mix(CREAM, INK, 0.2), width=2)
            draw_text(d, (x, cy + 130), label, 16, mix(label_color, bg, 0.7), weight="regular", anchor="ms")
            x += 290

    draw_text(d, (1080, 120), "ทดสอบการครอปวงกลม", 26, INK, weight="bold")
    draw_text(d, (1080, 156), "อวตารใช้สัญลักษณ์ล้วน", 17, mix(INK, CREAM, 0.72), weight="regular")
    draw_text(d, (1080, 186), "ไม่มีตัวอักษรหรือคำว่า 30 วัน", 17, mix(INK, CREAM, 0.72), weight="regular")
    draw_text(d, (1080, 500), "บนพื้นเข้ม", 26, CREAM, weight="bold")
    draw_text(d, (1080, 536), "ขอบสัญลักษณ์ยังอยู่ในวงกลม Ø 84%", 17, mix(CREAM, INK, 0.72), weight="regular")
    draw_text(d, (1080, 566), "ไม่ถูกตัดแขน K แม้ย่อเหลือ 64 px", 17, mix(CREAM, INK, 0.72), weight="regular")
    return img


def render_contact_sheet(assets: dict[str, Image.Image]) -> Image.Image:
    w, h = 1600, 1300
    img = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(img)
    muted = mix(CREAM, INK, 0.6)

    draw_text(d, (80, 96), "Kopwang — ชุดภาพ 3 ช่องทาง", 34, CREAM, weight="bold")
    draw_text(d, (80, 132), "Facebook Page · TikTok · Shopee  |  ไฟล์จริงใน brand/social/", 16, muted, weight="regular")

    def thumb(key: str, box, label: str, note: str) -> None:
        source = assets[key]
        target_w, target_h = box[2] - box[0], box[3] - box[1]
        scale = min(target_w / source.width, target_h / source.height)
        size = (max(1, round(source.width * scale)), max(1, round(source.height * scale)))
        img.paste(source.resize(size, Image.LANCZOS), (box[0], box[1]))
        d.rectangle(box, outline=mix(CREAM, INK, 0.22), width=1)
        draw_text(d, (box[0], box[3] + 26), label, 15, CREAM, weight="semibold")
        draw_text(d, (box[0], box[3] + 48), note, 13, muted, weight="regular")

    thumb("profile-facebook", (80, 180, 260, 360), "Profile", "1024 × 1024 · สัญลักษณ์ล้วน")
    thumb("cover-facebook", (320, 180, 920, 402), "Facebook cover", "851 × 315 · เนื้อหาอยู่ใน 640 × 312")

    thumb("cover-shopee", (80, 500, 600, 793), "Shopee shop cover", "1200 × 675 · Shop Cover")
    thumb("banner-shopee", (660, 500, 1220, 640), "Shopee shop banner", "1200 × 300")
    thumb("profile-shopee", (660, 700, 800, 840), "Shopee logo", "500 × 500")

    thumb("cover-tiktok", (80, 900, 260, 1220), "TikTok video cover", "1080 × 1920 · ไม่มีหน้าปกโปรไฟล์")

    draw_text(d, (980, 200), "ไฟล์ชุดเดียวกันทุกช่องทาง", 20, CREAM, weight="bold")
    for i, line in enumerate(("อวตารเดียวกัน 3 ขนาด", "หน้าปกปรับตามสัดส่วนของแพลตฟอร์ม", "โทนสี คำพูด และระยะขอบชุดเดียว")):
        draw_text(d, (980, 242 + i * 32), "— " + line, 15, muted, weight="regular")

    rules = [
        "ใช้สี Ink / Amber / Cream / Mint จาก brand-kit เท่านั้น",
        "อวตารทุกช่องทางใช้สัญลักษณ์ล้วน — ไม่มีคำว่า Kopwang หรือ 30 วัน",
        "Mint ≤ 10% ของพื้นที่ ใช้เฉพาะจุด “ทำแล้ว”",
        "ไม่มีธนบัตร เหรียญ กราฟกำไร หรือคำสัญญารายได้",
        "Facebook cover: หลีกเลี่ยงมุมซ้ายล่าง (รูปโปรไฟล์ทับ)",
    ]
    draw_text(d, (340, 940), "กฎที่ใช้ร่วมกันทั้ง 3 ช่องทาง", 20, CREAM, weight="bold")
    for i, line in enumerate(rules):
        draw_text(d, (340, 982 + i * 32), "— " + line, 15, muted, weight="regular")

    draw_text(d, (340, 1160), "หมายเหตุ", 18, CREAM, weight="bold")
    draw_text(d, (340, 1196), "TikTok ไม่มีภาพหน้าปกโปรไฟล์ — ไฟล์ 1080 × 1920 ใช้เป็นปกคลิป", 14, muted, weight="regular")
    draw_text(d, (340, 1224), "ไฟล์ใน preview/ เป็นภาพตรวจงาน ไม่ต้องอัปโหลด", 14, muted, weight="regular")
    return img


# --------------------------------------------------------------------- main

def main() -> int:
    SOCIAL.mkdir(parents=True, exist_ok=True)
    master = render_profile(2048)

    rendered = {
        "profile-master": master,
        "profile-facebook": master.resize((1024, 1024), Image.LANCZOS),
        "profile-tiktok": master.resize((200, 200), Image.LANCZOS),
        "profile-shopee": master.resize((500, 500), Image.LANCZOS),
        "cover-facebook": render_facebook_cover(),
        "cover-shopee": render_shopee_cover(),
        "banner-shopee": render_shopee_banner(),
        "cover-tiktok": render_tiktok_cover(),
    }
    rendered["preview-facebook-safe"] = render_facebook_safe_preview(rendered["cover-facebook"])
    rendered["preview-profile-crops"] = render_profile_crops(master)
    rendered["contact-sheet"] = render_contact_sheet(rendered)

    manifest_assets = []
    for item in SPEC["assets"]:
        image = rendered[item["id"]]
        path = ROOT / item["path"]
        save_png(image, path)
        data = path.read_bytes()
        if item["role"] != "preview":
            actual_bbox = content_bbox(image)
        else:
            actual_bbox = None
        manifest_assets.append(
            {
                **item,
                "actual_width": image.width,
                "actual_height": image.height,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "content_bbox": actual_bbox,
            }
        )

    manifest = {
        "brand": SPEC["brand"],
        "version": SPEC["version"],
        "generator": "scripts/build_brand_assets.py",
        "font": {
            "family": SPEC["font"]["family"],
            "sha256": hashlib.sha256(FONT_PATH.read_bytes()).hexdigest(),
            "license": SPEC["font"]["license"],
        },
        "palette": SPEC["palette"],
        "safe_zones": SPEC["safe_zones"],
        "assets": manifest_assets,
    }
    (SOCIAL / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"{'ไฟล์':44} {'ขนาด':>11}  {'KB':>7}")
    for item in manifest_assets:
        rel = Path(item["path"]).relative_to("brand/social")
        print(f"{str(rel):44} {item['actual_width']:>5}×{item['actual_height']:<5} {item['bytes'] / 1024:>7.1f}")
    total = sum(i["bytes"] for i in manifest_assets)
    print(f"\n{len(manifest_assets)} ไฟล์ · รวม {total / 1024:.1f} KB · manifest: brand/social/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
