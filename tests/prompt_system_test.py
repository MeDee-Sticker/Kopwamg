#!/usr/bin/env python3
"""ทดสอบระบบสร้างพร้อมต์ (prompts/system.json + scripts/build_prompts.py)

ตรวจว่า
  - สเปกครบ: สินค้า สาธิตสินค้า สไตล์ ข้อห้าม และกลไกปักตะกร้าของทั้ง 3 แพลตฟอร์ม
  - ตัวสร้างทำงานซ้ำได้ผลเท่าเดิม และไฟล์ที่ commit ตรงกับข้อมูลต้นทาง (seeds + plan)
  - ทุกวันมีพร้อมต์ครบ 3 ขั้น (สคริปต์ → ภาพ → วิดีโอ) และทุกรอบมีช่วงสาธิตสินค้า + ปักตะกร้า
  - ไม่มีคำสัญญารายได้หลุดออกไปนอกบรรทัด "ห้าม" และไม่มีข้อมูลลับ

    python3 tests/prompt_system_test.py
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_prompts as bp  # noqa: E402

THAI = re.compile(r"[\u0e00-\u0e7f]")
SECRETS = ("access_token", "FB_PAGE_ACCESS_TOKEN", "EAA", "refresh_token")
SCRIPT_MARKER = '"voice_over"'

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


def banned_offending_lines(text: str, banned: list[str]) -> list[str]:
    """คืนบรรทัดที่มีคำต้องห้ามแต่ไม่มีบริบท 'ห้าม' กำกับ"""
    offenders: list[str] = []
    for line in text.splitlines():
        if "ห้าม" in line:
            continue
        for word in banned:
            if word in line:
                offenders.append(line.strip()[:120])
                break
    return offenders


def phase_spec() -> dict:
    print("== สเปก prompt system ==")
    config = bp.load_json(bp.SYSTEM_FILE)
    check("มีชื่อและวัตถุประสงค์", bool(config.get("name")) and bool(config.get("purpose")))
    steps = [s["step"] for s in config.get("workflow", [])]
    check("ลำดับงานคือ สคริปต์ → ภาพ → วิดีโอ", steps == ["script", "image", "video"], str(steps))
    check(
        "ทุกขั้นบอกอินพุต/เอาต์พุต/ขั้นถัดไป",
        all(s.get("input") and s.get("output") and s.get("then") for s in config["workflow"]),
    )
    models = config.get("models", {})
    check(
        "ระบุโมเดลเป้าหมายครบ 3 ขั้น",
        all(models.get(k, {}).get("suggested") for k in ("script", "image", "video")),
    )
    check(
        "โมเดลภาพ/วิดีโอใช้พร้อมต์ภาษาอังกฤษ",
        models["image"]["language"] == "en" and models["video"]["language"] == "en",
    )
    check("โมเดลสคริปต์ใช้ภาษาไทย", models["script"]["language"] == "th")

    demo = config["product"]["demo"]
    check("สเปกสาธิตสินค้ามีรายการให้โชว์ ≥ 4 อย่าง", len(demo["show"]) >= 4, str(len(demo["show"])))
    check("บอกวิธีถ่ายสาธิตและสิ่งที่ห้ามโชว์", bool(demo["how"]) and len(demo["avoid"]) >= 2)
    check("โชว์สารบัญและตารางติดตามผล", any("สารบัญ" in s for s in demo["show"]) and any("ตาราง" in s for s in demo["show"]))

    style = config["style"]
    check("มีครบ 4 สีแบรนด์", set(style["palette"]) == {"ink", "amber", "cream", "mint"})
    check("ระบุฟอนต์ไทย", "Noto Sans Thai" in style["font"])
    check("มีกติกาภาพและห้ามภาพการเงิน", any("ธนบัตร" in r for r in style["visual_rules"]))

    safety = config["safety"]
    check("มีรายการคำต้องห้าม ≥ 5 คำ", len(safety["banned_claims"]) >= 5, str(len(safety["banned_claims"])))
    check("ห้ามภาพการเงินครบ", len(safety["banned_visuals"]) >= 3)
    check("มีข้อกำหนดเปิดเผยลิงก์สินค้าและขออนุญาตรีวิว", bool(safety["disclosure"]) and bool(safety["consent"]))

    platforms = config["platforms"]
    check("มีครบ 3 แพลตฟอร์ม", set(platforms) == {"facebook", "tiktok", "shopee"}, str(sorted(platforms)))
    for name, view in platforms.items():
        pin = view.get("cart_pin", {})
        check(
            f"{name}: กลไกปักตะกร้าครบ (กลไก/ตำแหน่ง/จังหวะ/ข้อความ/คำพูด/ทางสำรอง)",
            all(pin.get(k) for k in ("mechanic", "where", "when", "onscreen_text", "voice_cta", "requirements", "fallback")),
        )
        check(f"{name}: มีอัตราส่วนภาพและเพดานแคปชัน", bool(view["aspect_ratios"]) and view["caption_limit"] > 0)
    check("TikTok ระบุตะกร้า TikTok Shop", "TikTok Shop" in platforms["tiktok"]["cart_pin"]["mechanic"])
    check("Facebook ระบุ Product tag + คอมเมนต์ปักหมุด", "Product tag" in platforms["facebook"]["cart_pin"]["mechanic"] and "ปักหมุด" in platforms["facebook"]["cart_pin"]["when"])
    check("Shopee ระบุ Shopee Video และข้อกำหนดนโยบาย", "Shopee Video" in platforms["shopee"]["cart_pin"]["mechanic"] and "setup/03-shopee.md" in platforms["shopee"]["cart_pin"]["policy_note"])
    return config


def phase_generation(config: dict) -> dict[str, bytes]:
    print("\n== การสร้างและจำนวนพร้อมต์ ==")
    first = bp.generate(config=config)
    second = bp.generate(config=config)
    check("สร้างซ้ำได้ผลเหมือนเดิมทุกไบต์", first == second, f"{len(first)} ไฟล์")

    manifest = json.loads(first["manifest.json"].decode("utf-8"))
    counts = manifest["counts"]
    check("มี 30 วัน", counts["days"] == 30, str(counts["days"]))
    check("มี 3 แพลตฟอร์ม × 30 วัน = 90 ชุดสคริปต์", counts["script_prompts"] == 90, str(counts["script_prompts"]))
    check("มี 90 พร้อมต์วิดีโอ", counts["video_prompts"] == 90, str(counts["video_prompts"]))
    check("มีพร้อมต์ภาพ ≥ 3 ต่อแพลตฟอร์มต่อวัน", counts["image_prompts"] >= 270, str(counts["image_prompts"]))
    check("มี 90 ชุดปักตะกร้า", counts["cart_pin_sets"] == 90, str(counts["cart_pin_sets"]))
    expected = {f"day-{d:02d}.md" for d in range(1, 31)} | {f"day-{d:02d}.json" for d in range(1, 31)} | {
        "index.md",
        "prompts.json",
        "manifest.json",
    }
    check("ชุดไฟล์ครบ 63 ไฟล์", set(first) == expected, str(sorted(set(expected) - set(first))))

    sources_ok = all(
        bp.sha256(Path(ROOT / path).read_bytes()) == digest
        for path, digest in manifest["sources"].items()
    )
    check("manifest แฮชข้อมูลต้นทาง (seeds/plan/system) ถูกต้อง", sources_ok)
    hashes_ok = all(
        bp.sha256(data) == manifest["files"][name]["sha256"] for name, data in first.items() if name != "manifest.json"
    )
    check("manifest แฮชไฟล์พร้อมต์ตรงกับเนื้อหาจริง", hashes_ok)
    return first


def phase_content(files: dict[str, bytes], config: dict) -> None:
    print("\n== เนื้อหาพร้อมต์แต่ละวัน ==")
    banned = config["safety"]["banned_claims"]
    platforms = config["platforms"]
    checked_platform_headings = 0
    checked_images = 0
    checked_captions = 0
    offenders: list[str] = []
    secret_hits: list[str] = []

    for day in range(1, 31):
        md = files[f"day-{day:02d}.md"].decode("utf-8")
        data = json.loads(files[f"day-{day:02d}.json"].decode("utf-8"))
        checked_platform_headings += sum(1 for p in platforms if f"## {p.upper()} —" in md)
        check(f"วัน {day:02d}: มีพร้อมต์สคริปต์ ภาพ วิดีโอ ครบในไฟล์ md", all(
            marker in md
            for marker in ("### 1) พร้อมต์เขียนสคริปต์", "### 2) พร้อมต์สร้างภาพ", "### 3) พร้อมต์สร้างวิดีโอ", "### 4) ปักตะกร้า / ลิงก์สินค้า")
        ))
        check(f"วัน {day:02d}: ข้อความไทยในพร้อมต์", bool(THAI.search(md)) and bool(THAI.search(json.dumps(data, ensure_ascii=False))))
        check(f"วัน {day:02d}: สคริปต์ต้องมีช่วงสาธิตสินค้าและปักตะกร้า", all(
            phrase in data["platforms"][p]["script_prompt"]
            for p in platforms
            for phrase in ("ช่วงสาธิตสินค้า", "ช่วงปักตะกร้า/ลิงก์สินค้า", SCRIPT_MARKER)
        ))

        for name, block in data["platforms"].items():
            view = platforms[name]
            check(f"วัน {day:02d} {name}: มีพร้อมต์ภาพ ≥ 3 และอัตราส่วนถูกต้อง", len(block["image_prompts"]) >= 3 and all(
                img["aspect"] == view["aspect_ratios"][0] and img["negative"] for img in block["image_prompts"]
            ))
            checked_images += len(block["image_prompts"])
            check(f"วัน {day:02d} {name}: พร้อมต์วิดีโอมีช็อต จังหวะ และปักตะกร้า", all(
                phrase in block["video"]["prompt"]
                for phrase in ("Shot list:", "Cart pin:", "clean space for Thai text overlays")
            ))
            check(
                f"วัน {day:02d} {name}: ปักตะกร้าตรงกลไกของแพลตฟอร์ม",
                block["video"]["cart_pin"]["mechanic"] == view["cart_pin"]["mechanic"]
                and any(req in block["video"]["cart_pin"]["requirements"] for req in view["cart_pin"]["requirements"]),
            )
            check(
                f"วัน {day:02d} {name}: ทุกช็อตมีเวลาและคำอธิบาย",
                all(s["time"] and s["label"] and s["content"] for s in block["shot_list"]),
            )

        captions = [b["caption"] for b in data["platforms"].values() if b["caption"]]
        checked_captions += len(captions)
        for text in (md,):
            offenders += banned_offending_lines(text, banned)
            secret_hits += [s for s in SECRETS if s in text]

    check("มีหัวข้อครบ 90 บล็อกแพลตฟอร์มในไฟล์ md", checked_platform_headings == 90, str(checked_platform_headings))
    check("นับพร้อมต์ภาพครบทุกไฟล์", checked_images >= 270, str(checked_images))
    check("ดึงแคปชันจากแผนมาไว้ในไฟล์พร้อมต์", checked_captions >= 60, str(checked_captions))
    check("ไม่มีคำสัญญารายได้หลุดนอกบรรทัดห้าม", not offenders, "; ".join(offenders[:3]))
    check("ไม่มีข้อมูลลับในไฟล์พร้อมต์", not secret_hits, ", ".join(secret_hits[:3]))

    index = files["index.md"].decode("utf-8")
    check("index.md ลิงก์ครบ 30 วัน", all(f"day-{d:02d}.md" in index for d in range(1, 31)))


def phase_files(config: dict) -> None:
    print("\n== ไฟล์ที่ commit และคำสั่ง --check ==")
    outdir = bp.DEFAULT_OUTDIR
    generated = bp.generate(config=config)
    on_disk_ok = all((outdir / name).read_bytes() == data for name, data in generated.items())
    check("ไฟล์ใน prompts/generated ตรงกับข้อมูลต้นทางทุกไฟล์", on_disk_ok)
    rc, output = capture(bp.check, outdir)
    check("bp.check() คืนค่า 0 เมื่อไฟล์ตรง", rc == 0, output.strip())
    cli_ok = callable(bp.main)

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        bp.write_files(tmp, generated)
        check("เขียนไฟล์ครบตามที่สร้าง", len(list(tmp.iterdir())) == len(generated))
        rc, _ = capture(bp.check, tmp)
        check("--check ผ่านกับสำเนาที่ถูกต้อง", rc == 0)
        target = tmp / "day-01.md"
        target.write_text(target.read_text(encoding="utf-8") + "\nแก้ไขเพิ่ม\n", encoding="utf-8")
        rc, output = capture(bp.check, tmp)
        check("--check จับไฟล์ที่ถูกแก้", rc == 1 and "day-01.md" in output, output.strip().splitlines()[:1])
    check("โมดูลหลักมี CLI ให้รันได้", cli_ok)


def main() -> int:
    config = phase_spec()
    files = phase_generation(config)
    phase_content(files, config)
    phase_files(config)
    print()
    if failures:
        print(f"{len(failures)} รายการไม่ผ่าน")
        return 1
    print("ผ่านทั้งหมด")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
