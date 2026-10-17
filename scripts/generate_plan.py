#!/usr/bin/env python3
"""Kopwang 30-day content engine.

Reads data/content_seeds.json (the human-written knowledge base) and expands it into
ready-to-publish artifacts for Facebook, TikTok and Shopee.

Outputs (all under content/):
  30-day-plan.csv         flat calendar, one row per post (Google Sheets / Excel ready)
  facebook-30days.md      copy-paste captions for the Facebook Page
  tiktok-30days.md        full video scripts (hook + beats + caption + hashtags)
  shopee-30days.md        daily shop action list
  plan.json               machine readable plan consumed by scripts/fb_scheduler.py

Usage:
  python3 scripts/generate_plan.py
  python3 scripts/generate_plan.py --start-date 2026-11-01
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "data" / "content_seeds.json"
OUT_DIR = ROOT / "content"

WEEKDAYS_TH = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

# Platform posting slots (HH:MM). Used both for the CSV and for FB scheduling.
FB_SLOTS = ["12:00"]
TIKTOK_SLOTS = ["19:30"]
SHOPEE_SLOTS = ["09:30"]


def load_seeds() -> dict:
    with SEEDS.open(encoding="utf-8") as fh:
        data = json.load(fh)
    days = data.get("days", [])
    if len(days) != 30:
        raise SystemExit(f"expected 30 days in {SEEDS.name}, found {len(days)}")
    numbers = [d["day"] for d in days]
    if numbers != list(range(1, 31)):
        raise SystemExit("day numbers must run 1..30 in order")
    return data


def hashtags_for(seed: dict, brand: dict) -> str:
    tags = list(brand["hashtags_base"])
    tags += brand.get("phase_hashtags", {}).get(seed["phase"], [])
    tags.append(f"#DAY{seed['day']}")
    # แฮชแท็กของบางช่วงสัปดาห์ซ้ำกับชุดหลัก — ตัดตัวซ้ำออกโดยคงลำดับเดิม
    return " ".join(dict.fromkeys(tags))


def fb_caption(seed: dict, brand: dict) -> str:
    fb = seed["fb"]
    points = "\n".join(f"{i}. {p}" for i, p in enumerate(seed["points"], start=1))
    return (
        f"{fb['headline']}\n\n"
        f"{fb['lead']}\n\n"
        f"{points}\n\n"
        f"💡 {seed['proof']}\n\n"
        f"👉 {seed['cta']}\n\n"
        f"{hashtags_for(seed, brand)}\n\n"
        f"— {brand['name']} | {brand['campaign']}"
    )


def tiktok_caption(seed: dict, brand: dict) -> str:
    tk = seed["tiktok"]
    return (
        f"{seed['hook']}\n\n"
        f"{seed['points'][0]}\n\n"
        f"{seed['cta']}\n\n"
        f"{hashtags_for(seed, brand)}"
    )


def build_rows(data: dict, start: date) -> list[dict]:
    brand = data["brand"]
    rows: list[dict] = []

    for seed in data["days"]:
        current = start + timedelta(days=seed["day"] - 1)
        common = {
            "day": seed["day"],
            "date": current.isoformat(),
            "weekday": WEEKDAYS_TH[current.weekday()],
            "phase": seed["phase"],
            "phase_goal": brand["weekly_phases"][seed["phase"]],
            "theme": seed["theme"],
            "hook": seed["hook"],
        }

        for slot in FB_SLOTS:
            rows.append(
                {
                    **common,
                    "platform": "facebook",
                    "post_time": slot,
                    "format": seed["fb"]["kind"],
                    "title": seed["fb"]["headline"],
                    "caption": fb_caption(seed, brand),
                    "notes": f"โพสต์ตามเวลาที่คนในเพจออนไลน์จริง · เป้าหมาย: {brand['weekly_phases'][seed['phase']]}",
                }
            )

        for slot in TIKTOK_SLOTS:
            rows.append(
                {
                    **common,
                    "platform": "tiktok",
                    "post_time": slot,
                    "format": seed["tiktok"]["format"],
                    "title": seed["tiktok"]["hook_line"],
                    "caption": tiktok_caption(seed, brand),
                    "notes": " | ".join(seed["tiktok"]["beats"]),
                }
            )

        for slot in SHOPEE_SLOTS:
            rows.append(
                {
                    **common,
                    "platform": "shopee",
                    "post_time": slot,
                    "format": "shop action",
                    "title": seed["shopee"],
                    "caption": "",
                    "notes": "งานประจำวันของร้าน Shopee (ทำมือ ไม่ใช้ API)",
                }
            )

    rows.sort(key=lambda r: (r["date"], r["post_time"], r["platform"]))
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    fields = [
        "day",
        "date",
        "weekday",
        "post_time",
        "platform",
        "phase",
        "phase_goal",
        "theme",
        "format",
        "title",
        "hook",
        "caption",
        "notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_facebook_md(data: dict, path: Path) -> None:
    brand = data["brand"]
    out = [
        f"# Facebook Page — ปฏิทินโพสต์ 30 วัน",
        "",
        f"**เพจ:** {brand['name']} — {brand['campaign']}  ",
        f"**เวลาที่ควรโพสต์:** {brand['best_times']['facebook']}  ",
        f"**สัดส่วนคอนเทนต์:** 7 คลิป/โพสต์ให้ความรู้ ต่อ 3 โพสต์ขายตรง  ",
        f"**CTA หลัก:** {data['cta_ladder']['lead']}",
        "",
        "> คัดลอกข้อความใต้แต่ละวันไปวางในเพจได้เลย แก้เฉพาะตัวเลขและรายละเอียดที่เป็นของคุณ",
        "",
        "---",
        "",
    ]
    for seed in data["days"]:
        out += [
            f"## วันที่ {seed['day']} — {seed['theme']}",
            f"*รูปแบบ: {seed['fb']['kind']} · เป้าหมายสัปดาห์: {brand['weekly_phases'][seed['phase']]}*",
            "",
            "```text",
            fb_caption(seed, brand),
            "```",
            "",
        ]
    path.write_text("\n".join(out), encoding="utf-8")


def write_tiktok_md(data: dict, path: Path) -> None:
    brand = data["brand"]
    out = [
        "# TikTok — สคริปต์วิดีโอ 30 วัน",
        "",
        f"**เวลาที่ควรโพสต์:** {brand['best_times']['tiktok']}  ",
        f"**ความยาวเป้าหมาย:** 25-40 วินาที · **ความถี่:** วันละ 1 คลิป ห้ามขาด  ",
        "**กฎ 3 วิแรก:** ห้ามทักทาย ห้ามเกริ่น ให้เข้าเรื่องทันที  ",
        "**การโพสต์:** อัปโหลดด้วยมือผ่านแอป TikTok (การโพสต์อัตโนมัติต้องผ่านการอนุมัติ Content Posting API ของ TikTok ก่อน)",
        "",
        "---",
        "",
    ]
    for seed in data["days"]:
        tk = seed["tiktok"]
        out += [
            f"## วันที่ {seed['day']} — {seed['theme']}",
            "",
            f"- **รูปแบบคลิป:** {tk['format']}",
            f"- **Hook ที่พูด (0-3 วิ):** {tk['hook_line']}",
            "- **ลำดับภาพและคำพูด:**",
        ]
        out += [f"    - {beat}" for beat in tk["beats"]]
        out += [
            "",
            "- **แคปชัน:**",
            "",
            "```text",
            tiktok_caption(seed, brand),
            "```",
            "",
            f"- **CTA ประจำวัน:** {seed['cta']}",
            "",
            "---",
            "",
        ]
    path.write_text("\n".join(out), encoding="utf-8")


def write_shopee_md(data: dict, path: Path) -> None:
    brand = data["brand"]
    out = [
        "# Shopee — งานร้านประจำวัน 30 วัน",
        "",
        f"**เวลาทำงานร้าน:** {brand['best_times']['shopee']}",
        "",
        "> อีบุ๊กเป็นไฟล์ดิจิทัล ซึ่งหลายแพลตฟอร์มมีข้อจำกัดด้านนโยบายสินค้า ",
        "> ให้ใช้ร้านเป็นหน้าต่างสร้างความเชื่อถือ และดึงคนมาที่ช่องทางของเราเอง (Line OA) เพื่อรับไฟล์",
        "> อ่านรายละเอียดข้อกำหนดได้ที่ setup/03-shopee.md ก่อนตั้งลิสต์ทุกครั้ง",
        "",
        "---",
        "",
    ]
    for seed in data["days"]:
        out.append(f"- **วันที่ {seed['day']} — {seed['theme']}:** {seed['shopee']}")
    path.write_text("\n".join(out), encoding="utf-8")


def write_plan_json(data: dict, rows: list[dict], path: Path) -> None:
    brand = data["brand"]
    payload = {
        "brand": brand,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rows": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Kopwang 30-day content plan.")
    parser.add_argument(
        "--start-date",
        default=date.today().isoformat(),
        help="วันแรกของแคมเปญ (YYYY-MM-DD), ค่าเริ่มต้นคือวันนี้",
    )
    args = parser.parse_args()
    try:
        start = date.fromisoformat(args.start_date)
    except ValueError:
        raise SystemExit(f"--start-date ต้องอยู่ในรูปแบบ YYYY-MM-DD (ได้รับ {args.start_date!r})")

    data = load_seeds()
    OUT_DIR.mkdir(exist_ok=True)
    rows = build_rows(data, start)

    write_csv(rows, OUT_DIR / "30-day-plan.csv")
    write_facebook_md(data, OUT_DIR / "facebook-30days.md")
    write_tiktok_md(data, OUT_DIR / "tiktok-30days.md")
    write_shopee_md(data, OUT_DIR / "shopee-30days.md")
    write_plan_json(data, rows, OUT_DIR / "plan.json")

    end = start + timedelta(days=29)
    print(f"สร้างแผน 30 วันสำเร็จ: {start.isoformat()} → {end.isoformat()}")
    print(f"  จำนวนโพสต์ทั้งหมด : {len(rows)}")
    print(f"  facebook          : {sum(r['platform'] == 'facebook' for r in rows)}")
    print(f"  tiktok            : {sum(r['platform'] == 'tiktok' for r in rows)}")
    print(f"  shopee            : {sum(r['platform'] == 'shopee' for r in rows)}")
    print(f"  ไฟล์ผลลัพธ์        : {OUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
