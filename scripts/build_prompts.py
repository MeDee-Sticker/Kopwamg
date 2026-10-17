#!/usr/bin/env python3
"""Kopwang prompt system — สร้างพร้อมต์เป็นชุดสำหรับ สคริปต์ → ภาพ → วิดีโอ

อ่านข้อมูลจริงของแคมเปญแล้วประกอบเป็นพร้อมต์ที่พร้อมคัดลอกไปใช้:

  data/content_seeds.json      หัวข้อ ฮุก ประเด็น หลักฐาน CTA และบีตคลิปของทั้ง 30 วัน
  content/plan.json            วันที่ แพลตฟอร์ม รูปแบบ และแคปชันที่โพสต์จริง
  prompts/system.json          กติกาแบรนด์ สินค้า สไตล์ภาพ ข้อห้าม และกลไกปักตะกร้าต่อแพลตฟอร์ม

ผลลัพธ์ (ค่าเริ่มต้นที่ prompts/generated/):

  day-01.md … day-30.md        พร้อมต์ครบ 3 ขั้นของวันนั้น พร้อมวิธีใช้ + ตารางปักตะกร้า
  day-01.json … day-30.json    โครงเดียวกันแบบเครื่องอ่าน สำหรับส่งต่อเข้าทูลสร้างภาพ/วิดีโอ
  prompts.json                 รวมทุกวันในไฟล์เดียว
  index.md                     สารบัญลิงก์ทุกวัน
  manifest.json                sha256 ของทุกไฟล์ + จำนวนพร้อมต์ แยกตามขั้นและแพลตฟอร์ม

ตัวอย่าง
--------
    python3 scripts/build_prompts.py               # สร้าง/อัปเดตพร้อมต์ทั้งหมด
    python3 scripts/build_prompts.py --outdir /tmp/prompts
    python3 scripts/build_prompts.py --check       # ตรวจว่าไฟล์ที่ commit ตรงกับข้อมูลจริง
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYSTEM_FILE = ROOT / "prompts" / "system.json"
SEEDS_FILE = ROOT / "data" / "content_seeds.json"
PLAN_FILE = ROOT / "content" / "plan.json"
DEFAULT_OUTDIR = ROOT / "prompts" / "generated"

PLATFORM_ORDER = ("facebook", "tiktok", "shopee")

SCRIPT_JSON_EXAMPLE = """{
  "voice_over": "สคริปต์พูดทั้งคลิปเป็นภาษาไทย",
  "onscreen_text": [
    {"time": "0-3", "text": "ข้อความสั้นบนจอ ไม่เกิน 2 บรรทัด"}
  ],
  "shot_list": [
    {"time": "0-3", "shot": "ชื่อช็อต", "detail": "สิ่งที่กล้องเห็น"}
  ],
  "caption": "แคปชันสำหรับโพสต์",
  "hashtags": ["#Kopwang"]
}"""

VISUALS = {
    "hook": (
        "Thai creator in their 30s sitting at a small desk at home, talking to a phone on a tripod, "
        "warm practical light, dark charcoal room"
    ),
    "teach": (
        "top-down flat lay of an open notebook, pen and smartphone on a dark desk, "
        "clean checklist rows visible, generous empty space"
    ),
    "demo": (
        "over-the-shoulder view of a laptop screen showing an e-book table of contents, "
        "a hand pointing at one section, warm screen glow on a dark desk"
    ),
    "proof": (
        "smartphone standing on a dark desk showing a clean chat conversation bubble with "
        "all personal data blurred, amber accent light"
    ),
    "cart": (
        "smartphone standing on a dark desk showing an online shop product page with a glowing "
        "shopping cart icon, amber accent light, clean negative space"
    ),
    "shop": (
        "e-commerce pack shot of a printed workbook and a notebook on a cream surface, "
        "soft shadow, minimal props, product photography"
    ),
    "cta": (
        "Thai creator smiling at the camera giving a thumbs up beside a phone showing a shop page, "
        "warm light, dark background"
    ),
}

NEGATIVE_PROMPT = (
    "banknotes, coins, gold bars, profit charts, income guarantees, "
    "readable Thai text, unreadable gibberish text, watermark, logo, extra fingers, "
    "distorted hands, oversaturated colors, cluttered background"
)


# --------------------------------------------------------------------------- helpers


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def encode(text: str) -> bytes:
    return text.encode("utf-8")


def _aspect(config: dict, platform: str) -> str:
    return config["platforms"][platform]["aspect_ratios"][0]


def _seconds(config: dict, platform: str) -> str:
    return config["platforms"][platform]["video_seconds"]


# --------------------------------------------------------------------------- shots


def shot_plan(seed: dict, row: dict, platform: str, config: dict) -> list[dict]:
    """โครงช็อตมาตรฐานของแต่ละแพลตฟอร์ม — ทุกแพลตฟอร์มมีช็อตสาธิตสินค้าและช็อตปักตะกร้าเสมอ"""
    points = [p for p in (seed.get("points") or []) if p]
    demo = " · ".join(config["product"]["demo"]["show"])
    hook = seed.get("hook", "")

    if platform == "tiktok":
        raw = [
            ("hook", "0-3", "ฮุก 3 วินาทีแรก", seed.get("tiktok", {}).get("hook_line") or hook),
            ("teach-1", "3-10", "ประเด็นหลักข้อ 1", points[0] if points else seed.get("theme", "")),
            ("teach-2", "10-18", "ประเด็นหลักข้อ 2-3", " | ".join(points[1:3]) or seed.get("theme", "")),
            ("demo", "18-28", "สาธิตการใช้สินค้า", demo),
            ("proof", "28-36", "หลักฐานและความน่าเชื่อถือ", seed.get("proof", "")),
            ("cart", "36-45", "ปักตะกร้า + CTA", seed.get("cta", "")),
        ]
    elif platform == "facebook":
        raw = [
            ("hook", "0-3", "ฮุกให้หยุดดู", hook),
            ("teach-1", "3-20", "ให้ความรู้ตามประเด็น", " | ".join(points[:2]) or seed.get("theme", "")),
            ("teach-2", "20-35", "ขยายประเด็นที่เหลือ", " | ".join(points[2:]) or seed.get("theme", "")),
            ("demo", "35-45", "สาธิตการใช้สินค้า", demo),
            ("proof", "45-52", "หลักฐานหรือตัวเลขจริง", seed.get("proof", "")),
            ("cart", "52-60", "ปักสินค้า/คอมเมนต์ + CTA", seed.get("cta", "")),
        ]
    else:  # shopee
        raw = [
            ("shop", "0-5", "อัปเดตหน้าร้าน", seed.get("shopee", "")),
            ("shop", "5-15", "ภาพสินค้าที่ Shopee อนุมัติ", row.get("title") or seed.get("theme", "")),
            ("demo", "15-28", "สาธิตสินค้า/ของจริงในมือ", demo),
            ("cart", "28-40", "ปักตะกร้า Shopee Video + CTA", seed.get("cta", "")),
        ]

    shots: list[dict] = []
    for index, (kind, seconds, label, content) in enumerate(raw, start=1):
        shots.append(
            {
                "id": f"{index:02d}-{kind}",
                "kind": kind,
                "seconds": seconds,
                "label": label,
                "content": content,
                "visual_en": VISUALS.get(kind, VISUALS["teach"]),
            }
        )
    return shots


def image_prompt(shot: dict, platform: str, config: dict) -> dict:
    aspect = _aspect(config, platform)
    prompt = (
        f"{aspect} photorealistic lifestyle image for a Thai online-business brand: {shot['visual_en']}. "
        "Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) "
        "with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, "
        "mobile-first composition with clean empty space at the top for a Thai caption overlay, "
        "high detail, no text, no logos, no currency"
    )
    return {
        "shot": shot["id"],
        "purpose": shot["label"],
        "aspect": aspect,
        "prompt": prompt,
        "negative": NEGATIVE_PROMPT,
        "th_overlay": shot["content"][:80],
    }


def video_prompt(seed: dict, row: dict, platform: str, config: dict, shots: list[dict]) -> dict:
    aspect = _aspect(config, platform)
    seconds = _seconds(config, platform)
    cart = config["platforms"][platform]["cart_pin"]
    lines = [
        f"Short-form {aspect} social video for a Thai online-business brand, about {seconds} seconds, "
        f"{len(shots)} shots. Theme: {seed.get('theme', '')}.",
        "Shot list:",
    ]
    for index, shot in enumerate(shots, start=1):
        lines.append(f"  {index}. {shot['seconds']}s — {shot['visual_en']}.")
    lines.append(
        f"Product demo: show {config['product']['name']} on screen "
        f"({config['product']['demo']['how']})."
    )
    lines.append(
        f"Cart pin: {cart['mechanic']} — appears {cart['when']}; "
        f"on-screen cue '{cart['onscreen_text']}' is added in editing, not rendered by the model."
    )
    lines.append(
        "Camera: handheld phone with a subtle push-in on the demo shot and quick cuts on the beat. "
        "Lighting: warm practical light, dark charcoal background, amber accent. "
        "Audio: clear Thai voice-over, subtle neutral background bed, no copyrighted music."
    )
    lines.append(
        "Leave clean space for Thai text overlays (added later with the brand font) and do not render "
        "readable text, currency symbols, banknotes or profit charts."
    )
    return {
        "aspect": aspect,
        "seconds": seconds,
        "prompt": "\n".join(lines),
        "negative": NEGATIVE_PROMPT,
        "shot_list": [
            {
                "time": shot["seconds"],
                "shot": shot["id"],
                "detail": shot["label"],
                "content": shot["content"],
            }
            for shot in shots
        ],
        "cart_pin": cart,
    }


# --------------------------------------------------------------------------- script prompt


def safety_lines(config: dict) -> list[str]:
    safety = config["safety"]
    lines = [f"- ห้ามใช้คำเหล่านี้ทุกกรณี: {', '.join(safety['banned_claims'])}"]
    lines.append(f"- ห้ามในงานภาพ: {', '.join(safety['banned_visuals'])}")
    lines.append(f"- {safety['disclosure']}")
    lines.append(f"- {safety['consent']}")
    return lines


def script_prompt(seed: dict, row: dict, platform: str, config: dict, shots: list[dict]) -> str:
    brand_block = config.get("brand", {})
    view = config["platforms"][platform]
    cart = view["cart_pin"]
    product = config["product"]
    style = config["style"]
    tone = " · ".join(style["tone"])
    points = seed.get("points") or []

    lines: list[str] = [
        "บทบาท: คุณเป็นนักเขียนสคริปต์คลิปสั้นภาษาไทยให้แบรนด์ Kopwang",
        f"สินค้า: {product['name']} ราคา {product['price']}",
        f"กลุ่มเป้าหมาย: {brand_block.get('audience', 'คนไทยที่อยากเริ่มขายของออนไลน์')}",
        f"โทนเสียง: {tone}",
        f"แพลตฟอร์ม: {view['label']} · ความยาว {view['video_seconds']} วินาที · อัตราส่วน {', '.join(view['aspect_ratios'])}",
        f"ภารกิจ: เขียนสคริปต์คลิปวันที่ {seed['day']} หัวข้อ \"{seed.get('theme', '')}\"",
        f"รูปแบบคลิปที่วางไว้: {row.get('format') or seed.get('tiktok', {}).get('format', '')}",
        "",
        "ข้อมูลที่ต้องใช้ (ห้ามคิดข้อเท็จจริงใหม่หรืออ้างตัวเลขที่ไม่มีในนี้):",
        f"- ฮุก: {seed.get('hook', '')}",
        *[f"- ประเด็น {i}: {p}" for i, p in enumerate(points, start=1)],
        f"- หลักฐาน/ความน่าเชื่อถือ: {seed.get('proof', '')}",
        f"- CTA: {seed.get('cta', '')}",
    ]

    if platform == "facebook":
        fb = seed.get("fb", {})
        lines += [
            f"- รูปแบบโพสต์ Facebook: {fb.get('kind', '')}",
            f"- พาดหัวที่วางไว้: {fb.get('headline', '')}",
            f"- ประโยคเปิดที่วางไว้: {fb.get('lead', '')}",
        ]
    if platform == "tiktok":
        beats = seed.get("tiktok", {}).get("beats") or []
        lines += ["", "บีตที่ผู้เขียนแผนให้มา (ต้องพูดให้ครบหรือเทียบเท่า):"]
        lines += [f"- {b}" for b in beats]
    if platform == "shopee":
        lines += ["", f"- งานร้าน Shopee ของวันนี้: {seed.get('shopee', '')}"]

    lines += [
        "",
        "โครงเรื่องที่ต้องมีครบทุกช่วง (ปรับถ้อยคำได้ ห้ามตัดช่วงทิ้ง):",
        *[f"- {s['seconds']}s | {s['label']}: {s['content']}" for s in shots],
        "",
        f"ช่วงสาธิตสินค้า: ให้เห็น {product['demo']['show'][0]} ขึ้นไปถึง "
        f"{product['demo']['show'][-1]} · วิธีถ่าย: {product['demo']['how']}",
        f"ช่วงปักตะกร้า/ลิงก์สินค้า: {cart['mechanic']}",
        f"  ข้อความบนจอ: {cart['onscreen_text']} · คำพูด: {cart['voice_cta']}",
        f"  ทางสำรอง: {cart['fallback']}",
    ]
    if platform == "shopee" and cart.get("policy_note"):
        lines.append(f"  ข้อกำหนดที่ต้องรู้: {cart['policy_note']}")

    lines += [
        "",
        "ข้อห้าม:",
        *safety_lines(config),
        "",
        "ข้อกำหนดผลลัพธ์:",
        f"- ภาษาไทยทั้งหมด อ่านออกเสียงได้จริงในเวลาที่กำหนด",
        f"- ข้อความบนจอสั้น ไม่เกิน 2 บรรทัด ใช้ฟอนต์ {style['font']}",
        f"- ความยาวแคปชันไม่เกิน {view['caption_limit']} ตัวอักษร และมีแฮชแท็กจากแคมเปญ",
        "- ตอบเป็น JSON เท่านั้น ตามโครงนี้:",
        SCRIPT_JSON_EXAMPLE,
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- day assembly


def build_day(seed: dict, rows: dict, config: dict) -> dict:
    platforms: dict[str, dict] = {}
    for platform in PLATFORM_ORDER:
        row = rows.get(platform, {})
        shots = shot_plan(seed, row, platform, config)
        platforms[platform] = {
            "label": config["platforms"][platform]["label"],
            "plan_title": row.get("title", ""),
            "format": row.get("format", ""),
            "post_time": row.get("post_time", ""),
            "caption": (row.get("caption") or "").strip(),
            "script_prompt": script_prompt(seed, row, platform, config, shots),
            "image_prompts": [image_prompt(shot, platform, config) for shot in shots if shot["kind"] != "cart"],
            "video": video_prompt(seed, row, platform, config, shots),
            "shot_list": [
                {
                    "time": s["seconds"],
                    "id": s["id"],
                    "label": s["label"],
                    "content": s["content"],
                }
                for s in shots
            ],
        }
    return {
        "day": seed["day"],
        "date": rows.get("facebook", {}).get("date", ""),
        "weekday": rows.get("facebook", {}).get("weekday", ""),
        "phase": seed.get("phase", ""),
        "phase_goal": rows.get("facebook", {}).get("phase_goal", ""),
        "theme": seed.get("theme", ""),
        "hook": seed.get("hook", ""),
        "cta": seed.get("cta", ""),
        "platforms": platforms,
    }


def render_markdown(day: dict, config: dict) -> str:
    product = config["product"]
    out: list[str] = [
        f"# วันที่ {day['day']:02d} — {day['theme']}",
        "",
        f"- วันที่: {day['date']} ({day['weekday']}) · เฟส {day['phase']} — {day['phase_goal']}",
        f"- ฮุก: {day['hook']}",
        f"- สินค้า: {product['name']} · {product['price']}",
        "- ใช้พร้อมต์ตามลำดับ: (1) เขียนสคริปต์ → (2) สร้างภาพ → (3) สร้างวิดีโอ → ปักตะกร้าในแพลตฟอร์ม",
        "- ไฟล์นี้สร้างจาก `data/content_seeds.json` + `content/plan.json` — แก้ต้นทางแล้วรัน "
        "`python3 scripts/build_prompts.py` ใหม่",
        "",
    ]
    for platform in PLATFORM_ORDER:
        block = day["platforms"][platform]
        out += [
            "---",
            "",
            f"## {platform.upper()} — {block['label']}",
            "",
            f"- เวลาโพสต์ตามแผน: {block['post_time']} · รูปแบบ: {block['format']}",
            f"- หัวข้อในแผน: {block['plan_title'] or '-'}",
            "",
            "### 1) พร้อมต์เขียนสคริปต์ (คัดลอกทั้งบล็อก)",
            "",
            "```text",
            block["script_prompt"],
            "```",
            "",
            "### 2) พร้อมต์สร้างภาพ",
            "",
            "| ช็อต | ใช้ทำอะไร | อัตราส่วน | พร้อมต์ (คัดลอก) | ข้อความไทยวางทับ |",
            "|---|---|---|---|---|",
        ]
        for img in block["image_prompts"]:
            out.append(
                f"| {img['shot']} | {img['purpose']} | {img['aspect']} | `{img['prompt']}` | {img['th_overlay']} |"
            )
        out += [
            "",
            f"Negative prompt รวมทุกภาพ: `{NEGATIVE_PROMPT}`",
            "",
            "### 3) พร้อมต์สร้างวิดีโอ",
            "",
            f"- อัตราส่วน {block['video']['aspect']} · ความยาว {block['video']['seconds']} วินาที",
            "",
            "```text",
            block["video"]["prompt"],
            "```",
            "",
            "### 4) ปักตะกร้า / ลิงก์สินค้า",
            "",
            f"- กลไก: {block['video']['cart_pin']['mechanic']}",
            f"- ตำแหน่ง: {block['video']['cart_pin']['where']}",
            f"- จังหวะ: {block['video']['cart_pin']['when']}",
            f"- ข้อความบนจอ: {block['video']['cart_pin']['onscreen_text']}",
            f"- คำพูด: {block['video']['cart_pin']['voice_cta']}",
            f"- ถ้าทำไม่ได้: {block['video']['cart_pin']['fallback']}",
        ]
        if block["video"]["cart_pin"].get("policy_note"):
            out.append(f"- ข้อกำหนดนโยบาย: {block['video']['cart_pin']['policy_note']}")
        if block["caption"]:
            out += ["", "### 5) แคปชันที่ใช้อยู่ (คัดลอกได้)", "", "```text", block["caption"], "```"]
    out += [
        "",
        "---",
        "",
        "## ข้อห้ามก่อนส่งงาน",
        "",
        "```text",
        *safety_lines(config),
        "```",
        "",
    ]
    return "\n".join(out)


def render_index(days: list[dict], config: dict) -> str:
    out = [
        "# Kopwang Prompt System — สารบัญ 30 วัน",
        "",
        f"พร้อมต์สำหรับ {len(days)} วัน × 3 แพลตฟอร์ม: สคริปต์ → ภาพ → วิดีโอ → ปักตะกร้า",
        "",
        "| วัน | วันที่ | เฟส | หัวข้อ | ไฟล์ |",
        "|---|---|---|---|---|",
    ]
    for day in days:
        out.append(
            f"| {day['day']:02d} | {day['date']} | {day['phase']} | {day['theme']} | "
            f"[md](day-{day['day']:02d}.md) · [json](day-{day['day']:02d}.json) |"
        )
    out += [
        "",
        "โครงพร้อมต์และกติกาทั้งหมดอยู่ที่ `prompts/system.json` — วิธีใช้แบบละเอียดอยู่ที่ `prompts/README.md`",
        "",
    ]
    return "\n".join(out)


def count_prompts(days: list[dict]) -> dict:
    return {
        "days": len(days),
        "platforms": len(PLATFORM_ORDER),
        "script_prompts": sum(len(d["platforms"]) for d in days),
        "image_prompts": sum(len(b["image_prompts"]) for d in days for b in d["platforms"].values()),
        "video_prompts": sum(len(d["platforms"]) for d in days),
        "cart_pin_sets": sum(len(d["platforms"]) for d in days),
    }


def generate(outdir: Path | None = None, config: dict | None = None) -> dict[str, bytes]:
    """สร้างผลลัพธ์ทั้งหมดเป็น bytes (ไม่แตะดิสก์) เพื่อทดสอบ/ตรวจความถูกต้องได้"""
    config = config or load_json(SYSTEM_FILE)
    config = {**config, "brand": load_json(SEEDS_FILE).get("brand", {})}
    seeds = load_json(SEEDS_FILE)["days"]
    plan = load_json(PLAN_FILE)["rows"]
    rows_by_day: dict[int, dict] = {}
    for row in plan:
        rows_by_day.setdefault(row["day"], {})[row["platform"]] = row

    days = [build_day(seed, rows_by_day.get(seed["day"], {}), config) for seed in seeds]

    files: dict[str, bytes] = {}
    for day in days:
        name = f"day-{day['day']:02d}"
        files[f"{name}.md"] = encode(render_markdown(day, config))
        files[f"{name}.json"] = encode(json.dumps(day, ensure_ascii=False, indent=2) + "\n")
    files["index.md"] = encode(render_index(days, config))
    files["prompts.json"] = encode(
        json.dumps({"version": 1, "days": days}, ensure_ascii=False, separators=(",", ":"))
    )

    manifest = {
        "version": 1,
        "system": display(SYSTEM_FILE),
        "sources": {
            display(path): sha256(path.read_bytes())
            for path in (SYSTEM_FILE, SEEDS_FILE, PLAN_FILE)
        },
        "counts": count_prompts(days),
        "files": {
            name: {"sha256": sha256(data), "bytes": len(data)}
            for name, data in sorted(files.items())
        },
    }
    files["manifest.json"] = encode(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return files


def write_files(outdir: Path, files: dict[str, bytes]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (outdir / name).write_bytes(data)


def check(outdir: Path) -> int:
    generated = generate()
    manifest_path = outdir / "manifest.json"
    if not manifest_path.exists():
        print(f"ยังไม่มี {display(manifest_path)} — รัน python3 scripts/build_prompts.py ก่อน")
        return 1
    problems: list[str] = []
    for name, data in generated.items():
        target = outdir / name
        if not target.exists():
            problems.append(f"ขาดไฟล์ {name}")
        elif target.read_bytes() != data:
            problems.append(f"เนื้อหาไม่ตรงกับข้อมูลต้นทาง {name}")
    return report(problems, outdir)


def report(problems: list[str], outdir: Path) -> int:
    if problems:
        print(f"พร้อมต์ไม่ตรงกับต้นทาง {len(problems)} รายการ:")
        for item in problems[:20]:
            print(f"  - {item}")
        return 1
    print(f"พร้อมต์ตรงกับข้อมูลต้นทางทั้งหมด ({display(outdir)})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="สร้างพร้อมต์ สคริปต์ → ภาพ → วิดีโอ ของแคมเปญ Kopwang")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR, help="โฟลเดอร์ผลลัพธ์")
    parser.add_argument("--check", action="store_true", help="ตรวจว่าไฟล์ที่มีอยู่ตรงกับข้อมูลต้นทาง")
    args = parser.parse_args()

    if args.check:
        return check(args.outdir)

    files = generate()
    write_files(args.outdir, files)
    manifest = json.loads(files["manifest.json"].decode("utf-8"))
    counts = manifest["counts"]
    print(
        f"สร้างพร้อมต์แล้วที่ {display(args.outdir)}: "
        f"{counts['script_prompts']} สคริปต์ · {counts['image_prompts']} ภาพ · {counts['video_prompts']} วิดีโอ "
        f"· {counts['cart_pin_sets']} ชุดปักตะกร้า ({counts['days']} วัน × {counts['platforms']} แพลตฟอร์ม)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
