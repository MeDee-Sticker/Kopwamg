#!/usr/bin/env python3
"""สร้าง SVG ต้นฉบับ (editable masters) ของหน้าปกและแบนเนอร์ Kopwang

ไฟล์ SVG วางข้างไฟล์ PNG ที่ชื่อเดียวกันใน brand/social/cover/ และ banner/
ข้อความไทยทุกบรรทัดเป็น <text> จริง (ไม่แปลงเป็น path) จึงแก้คำพูด ขนาด หรือสีได้
ใน Illustrator / Figma / Inkscape โดยใช้เรขาคณิตเดียวกับ scripts/build_brand_assets.py
และคำพูดชุดเดียวกับ brand/social/spec.json

    python3 scripts/build_brand_assets.py   # PNG + manifest
    python3 scripts/build_brand_svg.py      # SVG + เพิ่มรายการใน manifest

ฟอนต์: SVG อ้าง brand/fonts/NotoSansThai.ttf แบบ path สัมพัทธ์ (../../fonts/)
ถ้าเปิดไฟล์ด้วยโปรแกรมที่ไม่ได้โหลดฟอนต์จาก path นี้ ให้ติดตั้งฟอนต์ในเครื่องก่อน
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_brand_assets as png  # noqa: E402

ROOT = png.ROOT
SOCIAL = png.SOCIAL
SPEC = png.SPEC
PALETTE = SPEC["palette"]
INK = PALETTE["ink"]
AMBER = PALETTE["amber"]
CREAM = PALETTE["cream"]
MINT = PALETTE["mint"]
WEIGHTS = SPEC["font"]["weights"]
FONT_REL = "../../fonts/NotoSansThai.ttf"

COPY = {
    key: (unicodedata.normalize("NFC", value) if isinstance(value, str)
          else [unicodedata.normalize("NFC", item) for item in value])
    for key, value in SPEC["copy"].items()
}

MEASURE = ImageDraw.Draw(Image.new("L", (8, 8)))
ANCHORS = {"ls": "start", "ms": "middle", "rs": "end"}


def muted(alpha: float) -> str:
    """สี Cream ผสมลงบน Ink — ค่าเดียวกับที่ตัวสร้าง PNG ใช้"""
    r, g, b = png.mix(png.CREAM, png.INK, alpha)
    return f"#{r:02X}{g:02X}{b:02X}"


def num(value: float) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return text or "0"


def measure(value: str, size: float, weight: str = "semibold", tracking: float = 0) -> float:
    return png.text_width(MEASURE, value, png.font(int(size), weight), tracking)


def fit(value: str, size: float, max_width: float, weight: str = "semibold", tracking: float = 0) -> int:
    return png.fit_text(MEASURE, value, int(size), max_width, weight, tracking)


def text(
    x: float,
    y: float,
    value: str,
    size: float,
    fill: str,
    *,
    weight: str = "semibold",
    anchor: str = "ls",
    tracking: float = 0,
    el_id: str | None = None,
) -> str:
    """<text> หนึ่งบรรทัด ใช้ baseline เดียวกับ Pillow (anchor 's')"""
    value = unicodedata.normalize("NFC", value)
    if tracking and anchor == "ms":
        x += tracking / 2  # ชดเชย letter-spacing ที่ต่อท้ายตัวสุดท้าย
    attrs = []
    if el_id:
        attrs.append(f'id="{el_id}"')
    attrs += [
        f'x="{num(x)}"',
        f'y="{num(y)}"',
        'font-family="Noto Sans Thai, sans-serif"',
        f'font-size="{num(size)}"',
        f'font-weight="{WEIGHTS[weight]}"',
        f'fill="{fill}"',
        f'text-anchor="{ANCHORS[anchor]}"',
    ]
    if tracking:
        attrs.append(f'letter-spacing="{num(tracking)}"')
    return f"<text {' '.join(attrs)}>{escape(value)}</text>"


def k_mark(cx: float, cy: float, height: float, color: str, el_id: str = "k-mark") -> str:
    """สัญลักษณ์ K-Bar จากเส้น 3 เส้น สัดส่วนเดียวกับ brand/logo/k-bar.svg"""
    scale = height / png.K_BOX
    stroke = png.K_STROKE * scale
    return (
        f'<g id="{el_id}" transform="translate({num(cx - 512 * scale)} {num(cy - 512 * scale)}) '
        f'scale({scale:.6f})" fill="none" stroke="{color}" stroke-width="{num(png.K_STROKE)}" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M328 270V754M328 512L696 270M328 512L696 754"/></g>'
    )


def day_ticks(cx: float, cy: float, inner: float, outer: float, width: float,
              color: str, accent: str) -> str:
    """วงแหวน 30 ขีด = 30 วัน ขีดสุดท้ายสี Mint (วันที่ทำสำเร็จ)"""
    lines = [f'<g id="day-ticks" stroke-width="{num(width)}" stroke-linecap="butt">']
    for day in range(30):
        angle = math.radians(-90 + day * 12)
        x1, y1 = cx + inner * math.cos(angle), cy + inner * math.sin(angle)
        x2, y2 = cx + outer * math.cos(angle), cy + outer * math.sin(angle)
        stroke = accent if day == 29 else color
        lines.append(
            f'<line x1="{num(x1)}" y1="{num(y1)}" x2="{num(x2)}" y2="{num(y2)}" stroke="{stroke}"/>'
        )
    lines.append("</g>")
    return "\n".join(lines)


def svg_document(width: int, height: int, label: str, desc: str, body: str) -> str:
    body = "\n".join(f"  {line}" if line.strip() else line for line in body.splitlines())
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}" xml:lang="th">\n'
        f"  <title>{escape(label)}</title>\n"
        f"  <desc>{escape(desc)}</desc>\n"
        "  <style>\n"
        "    @font-face {\n"
        '      font-family: "Noto Sans Thai";\n'
        "      font-style: normal;\n"
        "      font-weight: 100 900;\n"
        f'      src: url("{FONT_REL}") format("truetype");\n'
        "    }\n"
        "  </style>\n"
        f'  <rect id="background" width="{width}" height="{height}" fill="{INK}"/>\n'
        f"{body}\n"
        "</svg>\n"
    )


# ------------------------------------------------------------------ covers

def facebook_cover() -> tuple[int, int, str, str]:
    w, h, left = 851, 315, 200
    tagline_size = fit(COPY["tagline"], 24, 340)
    cta_w = measure(COPY["cta"], 15, "medium")
    grid_x, grid_y = 636, 78

    bars = []
    for i in range(30):
        col, row = i % 6, i // 6
        x = grid_x + col * 19
        y = grid_y + row * 33
        fill = AMBER if i < 12 else muted(0.34)
        bars.append(f'<rect x="{x}" y="{y}" width="8" height="22" rx="4" fill="{fill}"/>')

    body = "\n".join(
        [
            '<g id="headline">',
            "  " + text(left, 126, COPY["wordmark"], 58, CREAM, weight="bold", el_id="wordmark"),
            f'  <rect id="underline" x="{left}" y="146" width="58" height="5" rx="2.5" fill="{AMBER}"/>',
            "  " + text(left, 190, COPY["tagline"], tagline_size, CREAM, el_id="tagline"),
            "  " + text(left, 221, COPY["promise"], 15, muted(0.72), weight="regular", el_id="promise"),
            "</g>",
            '<g id="cta">',
            f'  <rect x="{left}" y="243" width="{num(cta_w + 30)}" height="38" rx="19" '
            f'fill="none" stroke="{AMBER}" stroke-width="1.5"/>',
            "  " + text(left + 15, 269, COPY["cta"], 15, AMBER, weight="medium", el_id="cta-label"),
            "</g>",
            '<g id="day-grid">',
            "  " + "\n  ".join(bars),
            "</g>",
        ]
    )
    return w, h, "Kopwang — Facebook Page cover 851×315", (
        "หน้าปกเพจ Facebook เนื้อหาอยู่ในโซนกลาง 640×312 และไม่ชนรูปโปรไฟล์มุมซ้ายล่าง"
    ), body


def shopee_cover() -> tuple[int, int, str, str]:
    w, h, left = 1200, 675, 96
    tagline_size = fit(COPY["tagline"], 34, 560)

    bullets = []
    for i, line in enumerate(COPY["shop_bullets"]):
        y = 462 + i * 44
        bullets.append(
            f'<rect x="{left}" y="{y - 7}" width="7" height="7" rx="1" fill="{AMBER}"/>'
            + text(left + 22, y, line, 20, muted(0.84), weight="regular", el_id=f"bullet-{i + 1}")
        )

    body = "\n".join(
        [
            '<g id="headline">',
            "  " + text(left, 132, COPY["shop_eyebrow"], 13, AMBER, tracking=3, el_id="eyebrow"),
            "  " + text(left, 268, COPY["wordmark"], 92, CREAM, weight="bold", el_id="wordmark"),
            f'  <rect id="underline" x="{left}" y="300" width="76" height="7" rx="3.5" fill="{AMBER}"/>',
            "  " + text(left, 356, COPY["tagline"], tagline_size, CREAM, el_id="tagline"),
            "  " + text(left, 398, COPY["shop_cover_line"], 21, muted(0.70), weight="regular", el_id="cover-line"),
            "</g>",
            '<g id="bullets">',
            "  " + "\n  ".join(bullets),
            "</g>",
            day_ticks(850, 337, 224, 256, 3.2, muted(0.32), MINT),
            k_mark(850, 337, 250, AMBER),
        ]
    )
    return w, h, "Kopwang — Shopee Shop Cover 1200×675", (
        "หน้าปกร้าน Shopee 16:9 ใช้คำพูดและสัญลักษณ์ชุดเดียวกับ Facebook Page"
    ), body


def shopee_banner() -> tuple[int, int, str, str]:
    w, h = 1200, 300
    cta_w = measure(COPY["cta"], 17, "medium")
    cta_x = 1200 - 60 - cta_w - 32

    body = "\n".join(
        [
            k_mark(140, 150, 118, AMBER),
            f'<rect id="divider" x="208" y="72" width="2" height="156" rx="1" fill="{muted(0.28)}"/>',
            '<g id="headline">',
            "  " + text(240, 136, COPY["wordmark"], 44, CREAM, weight="bold", el_id="wordmark"),
            "  " + text(240, 176, COPY["shop_banner_line"], 18, muted(0.72), weight="regular", el_id="banner-line"),
            "</g>",
            f'<rect id="offer-mark" x="560" y="143" width="7" height="7" rx="1" fill="{AMBER}"/>',
            text(584, 157, COPY["offer"], 20, muted(0.84), weight="medium", el_id="offer"),
            '<g id="cta">',
            f'  <rect x="{num(cta_x)}" y="126" width="{num(cta_w + 32)}" height="48" rx="24" '
            f'fill="none" stroke="{AMBER}" stroke-width="1.5"/>',
            "  " + text(cta_x + 16, 158, COPY["cta"], 17, AMBER, weight="medium", el_id="cta-label"),
            "</g>",
        ]
    )
    return w, h, "Kopwang — Shopee Shop Banner 1200×300", (
        "แบนเนอร์ร้าน Shopee แถบแนวนอน ใช้สัญลักษณ์ ข้อความ และปุ่มติดต่อชุดเดียวกับหน้าปก"
    ), body


def tiktok_cover() -> tuple[int, int, str, str]:
    w, h = 1080, 1920
    size1 = fit(COPY["tiktok_line_1"], 108, 760, "bold")
    size2 = fit(COPY["tiktok_line_2"], 108, 760, "bold")
    headline = min(size1, size2)

    body = "\n".join(
        [
            "  " + text(540, 336, COPY["eyebrow"], 20, AMBER, tracking=6, anchor="ms", el_id="eyebrow"),
            k_mark(540, 620, 300, AMBER),
            '<g id="headline">',
            "  " + text(540, 1060, COPY["tiktok_line_1"], headline, CREAM, weight="bold", anchor="ms", el_id="line-1"),
            "  " + text(540, 1188, COPY["tiktok_line_2"], headline, AMBER, weight="bold", anchor="ms", el_id="line-2"),
            "  " + text(540, 1274, COPY["tiktok_line"], 26, muted(0.74), weight="regular", anchor="ms", el_id="subline"),
            "</g>",
            f'<rect id="divider" x="410" y="1340" width="260" height="3" rx="1.5" fill="{muted(0.30)}"/>',
            "  " + text(540, 1398, COPY["tiktok_footer"], 22, muted(0.62), weight="medium", anchor="ms", el_id="footer"),
        ]
    )
    return w, h, "Kopwang — TikTok video cover 1080×1920", (
        "ภาพปกคลิปแนวตั้งสำหรับ TikTok เนื้อหาพ้น UI ด้านล่างและขอบซ้าย/ขวา"
    ), body


RENDERERS = {
    "cover-facebook": facebook_cover,
    "cover-shopee": shopee_cover,
    "banner-shopee": shopee_banner,
    "cover-tiktok": tiktok_cover,
}


def main() -> int:
    manifest_path = SOCIAL / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    masters = []

    for item in SPEC["assets"]:
        if item["id"] not in RENDERERS:
            continue
        width, height, label, desc, body = RENDERERS[item["id"]]()
        path = Path(item["path"]).with_suffix(".svg")
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        markup = svg_document(width, height, label, desc, body)
        target.write_text(markup, encoding="utf-8")
        raw = target.read_bytes()
        masters.append(
            {
                "id": item["id"],
                "path": str(path),
                "png": item["path"],
                "width": width,
                "height": height,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "text_nodes": markup.count("<text "),
                "font": {
                    "family": SPEC["font"]["family"],
                    "file": SPEC["font"]["file"],
                    "embedded": False,
                    "reference": FONT_REL,
                },
            }
        )

    manifest["svg_masters"] = masters
    manifest["svg_generator"] = "scripts/build_brand_svg.py"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"{'ไฟล์ SVG':52} {'ขนาด':>11}  {'KB':>6}  text")
    for item in masters:
        rel = Path(item["path"]).relative_to("brand/social")
        print(f"{str(rel):52} {item['width']:>5}×{item['height']:<5} {item['bytes'] / 1024:>6.1f}  {item['text_nodes']:>4}")
    print(f"\n{len(masters)} ไฟล์ SVG · ข้อความเป็น text จริงทั้งหมด · manifest: brand/social/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
