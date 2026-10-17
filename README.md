# Kopwang — ระบบสร้างรายได้ใน 30 วัน

ระบบคอนเทนต์และโพสต์ต่อเนื่อง **30 วัน** สำหรับเพจ Facebook, บัญชี TikTok และร้าน Shopee ของแบรนด์
**Kopwang** พร้อมสินค้า **E-Book Kopwang : ระบบสร้างรายได้ใน 30 วัน**

แผน 30 วันเขียนไว้ล่วงหน้าทั้งหมดแล้ว (หัวข้อ, hook, สคริปต์วิดีโอ, แคปชัน, แฮชแท็ก, งานร้าน)
แล้วใช้สคริปต์สร้างปฏิทินจริง + โพสต์ Facebook อัตโนมัติได้

---

## ไฟล์สำคัญ

| ไฟล์ | คืออะไร |
|---|---|
| `data/content_seeds.json` | **ต้นทางของทุกอย่าง** — หัวข้อ 30 วัน พร้อม hook, จุดสำคัญ, CTA, สคริปต์ TikTok และงาน Shopee |
| `content/30-day-plan.csv` | ปฏิทินจริง 90 รายการ (30 วัน × 3 แพลตฟอร์ม) เปิดใน Google Sheets ได้ทันที |
| `content/facebook-30days.md` | ข้อความโพสต์ Facebook ทั้ง 30 วัน คัดลอกวางได้เลย |
| `content/tiktok-30days.md` | สคริปต์วิดีโอ TikTok ทั้ง 30 วัน (hook + ลำดับภาพ/คำพูด + แคปชัน + แฮชแท็ก) |
| `content/shopee-30days.md` | งานร้าน Shopee วันละ 1 อย่าง |
| `content/plan.json` | แผนฉบับเครื่องอ่าน ใช้โดยสคริปต์โพสต์ Facebook |
| `content/drafts/` | ฉบับร่างโพสต์ที่ **ยังไม่โพสต์** พร้อมเช็กลิสต์ตรวจก่อนกดโพสต์ |
| `brand/brand-kit.md` | ชื่อเพจ คำโปรย ข้อเสนอ เส้นทางลูกค้า และตัวเลขที่ต้องวัด |
| `brand/logo/brief.md` | ไอเดียโลโก้ 3 แบบ + ไฟล์ SVG/PNG + สเปกขนาดทุกแพลตฟอร์ม |
| `brand/social/` | **ชุดภาพโปรไฟล์ หน้าปก และแบนเนอร์ร้าน** ที่ใช้ร่วมกันทั้ง 3 ช่องทาง + วิธีอัปโหลด |
| `scripts/build_brand_assets.py` | สร้างชุดภาพแบรนด์ใหม่จาก `brand/social/spec.json` (ต้องมี Pillow) |
| `tests/brand_assets_test.py` | ตรวจขนาด โซนปลอดภัย สี คำต้องห้าม และความสม่ำเสมอของอวตาร |
| `docs/ebook-outline.md` | โครงสร้าง E-Book ที่จะขาย พร้อมกำหนดส่งรายบท |
| `setup/01-facebook-page.md` | สร้างเพจ + แอป Meta + โทเคน + ตั้ง cron |
| `setup/02-tiktok.md` | สมัครบัญชี โปรไฟล์ และวินัยโพสต์ 30 วัน |
| `setup/03-shopee.md` | เปิดร้าน Shopee + **ข้อจำกัดนโยบายการขายอีบุ๊ก (อ่านก่อนตั้งลิสต์)** |
| `dashboard/index.html` | **หน้าเว็บปฏิทิน 30 วัน** — เห็นทุกวัน พร้อมปุ่มคัดลอกแคปชัน Facebook และสคริปต์ TikTok (ไฟล์เดียว เปิดได้เลย) |
| `scripts/generate_plan.py` | สร้างแผนและไฟล์ทั้งหมดจาก `content_seeds.json` |
| `scripts/dashboard_server.py` | เสิร์ฟหน้าเว็บ + เปิดปุ่มสั่งโพสต์/ตั้งเวลา/สร้างร่าง Facebook บนหน้าเว็บ |
| `scripts/build_dashboard.py` | สร้าง `dashboard/index.html` จาก `content/plan.json` |
| `tests/dashboard_smoke.mjs` | ทดสอบหน้าเว็บโดยไม่ต้องเปิดเบราว์เซอร์ (ต้องมี Node) |
| `tests/dashboard_api_test.py` | ทดสอบ API ของเซิร์ฟเวอร์หน้าเว็บแบบ end-to-end |
| `tests/content_draft_test.py` | ด่านตรวจฉบับร่างโพสต์ (ความยาว คำต้องห้าม ลายเซ็น CTA เช็กลิสต์) |
| `tests/fb_draft_test.py` | ทดสอบโหมด `--draft` (สร้างโพสต์ unpublished จากไฟล์ในเครื่อง) ด้วย Graph API จำลอง |
| `tests/daily_run_test.py` | ทดสอบว่างานประจำวันตรวจสถานะร่างอัตโนมัติและต่อท้าย log (ไม่ยิง Facebook จริง) |
| `scripts/fb_scheduler.py` | โพสต์ / ตั้งเวลา / สร้างโพสต์ร่าง unpublished ของ Facebook Page ผ่าน Graph API |
| `scripts/daily_run.sh` | งานประจำวัน: ตรวจสถานะร่างอัตโนมัติ + โพสต์ Facebook + แสดงงานมือที่เหลือ |
| `prompts/system.json` | กติกาพร้อมต์: สินค้า สาธิตการใช้สินค้า สไตล์ภาพ ข้อห้าม และกลไกปักตะกร้า 3 แพลตฟอร์ม |
| `prompts/generated/` | พร้อมต์พร้อมใช้ 30 วัน (สคริปต์ → ภาพ → วิดีโอ + ปักตะกร้า) สร้างจาก `build_prompts.py` |
| `scripts/build_prompts.py` | สร้างพร้อมต์ทั้งหมดจาก seeds + แผน + `prompts/system.json` |
| `scripts/gemini_prompt_runner.py` | รันพร้อมต์สคริปต์กับ Google Gemini จริง + ด่านตรวจคำต้องห้าม ก่อนเก็บผลลง `content/ai-drafts/` |
| `content/ai-drafts/` | ร่างที่โมเดลสร้างให้ (ต้องตรวจก่อนใช้) — แยกจาก `content/drafts/` ที่ผ่านด่านแล้ว |
| `tests/gemini_runner_test.py` | ทดสอบตัวรัน Gemini ด้วยเซิร์ฟเวอร์จำลอง (ไม่ยิง Google จริง) |
| `tests/prompt_system_test.py` | ตรวจสเปก จำนวน เนื้อหา และการปักตะกร้าของพร้อมต์ทุกวัน |
| `scripts/build_download_bundle.py` | รวมทุกไฟล์เป็น zip เดียวสำหรับดาวน์โหลด + manifest แฮช |
| `scripts/split_bundle_for_download.py` | แยก zip เป็นไฟล์ข้อความ base64 หลายส่วน สำหรับช่องทางที่โหลดไฟล์ไบนารีไม่ได้ |
| `downloads/` | ผลลัพธ์ชุดดาวน์โหลด (`kopwang-all-files-YYYYMMDD.zip` + manifest) |
| `tests/download_bundle_test.py` | ตรวจว่า zip ครบ ถูกลบเฉพาะไฟล์ที่ควร และ manifest ตรงกับไฟล์จริง |
| `tests/split_bundle_test.py` | ตรวจว่าชิ้นส่วน base64 รวมกลับได้ไฟล์เดิมและตรวจเจอเมื่อชิ้นส่วนหาย/ถูกแก้ |

---

## เริ่มใช้งาน 5 นาที

```bash
# 1) สร้างปฏิทิน 30 วัน (กำหนดวันเริ่มเองได้)
python3 scripts/generate_plan.py --start-date 2026-11-01

# 2) ดูว่าโพสต์ของวันนี้คืออะไร (ไม่ยิง API — dry-run เป็นค่าเริ่มต้น)
python3 scripts/fb_scheduler.py --today
```

สคริปต์โพสต์และสร้างแผนใช้ Python 3 มาตรฐาน ไม่ต้องติดตั้งไลบรารีเพิ่ม
(ชุดภาพแบรนด์ต้องใช้ Pillow — ดูหัวข้อ "ชุดภาพแบรนด์ 3 ช่องทาง" ด้านล่าง)

```bash
# 3) ตั้งค่า Facebook (ทำครั้งเดียว) — ดู setup/01-facebook-page.md
cp .env.example .env      # แล้วเติมค่าจากขั้นตอนใน setup/01
python3 scripts/fb_scheduler.py --exchange-token "SHORT_LIVED_TOKEN"
python3 scripts/fb_scheduler.py --check

# 4) โพสต์จริง
python3 scripts/fb_scheduler.py --today --live
# หรือมอบหมายให้ Facebook ตั้งเวลาโพสต์ที่เหลือทั้งหมด
python3 scripts/fb_scheduler.py --schedule --from-day 2 --to-day 30 --live

# 5) สร้างโพสต์ร่าง (unpublished) จากไฟล์ในเครื่อง เพื่อไปตรวจใน Facebook ก่อน
python3 scripts/fb_scheduler.py --draft --file content/drafts/fb-001-page-intro.md --live
```

---

## หน้าเว็บปฏิทิน 30 วัน

หน้าเว็บนี้เป็นไฟล์ HTML ไฟล์เดียวที่ฝังข้อมูลแผนไว้ในตัว ใช้เป็นคู่มือทำงานประจำวัน:
ดูทั้ง 30 วันแบบการ์ด, กรองตามแพลตฟอร์ม/สัปดาห์, ค้นหา, กดคัดลอกแคปชัน Facebook
หรือสคริปต์ TikTok ไปวางได้ทันที และกดเครื่องหมาย "ทำแล้ว" เพื่อดูความคืบหน้า (เก็บในเบราว์เซอร์ของคุณ)

```bash
# สร้าง/อัปเดตหน้าเว็บจากแผนล่าสุด (ถ้า plan.json ยังไม่มี จะสร้างแผนให้ก่อน)
python3 scripts/build_dashboard.py

# เปิดดู
open dashboard/index.html                                  # macOS
xdg-open dashboard/index.html                              # Linux

# หรือเสิร์ฟในเครื่องแล้วเปิด http://localhost:3000
python3 -m http.server 3000 --directory dashboard
```

ทุกครั้งที่แก้ `data/content_seeds.json` แล้วสร้างแผนใหม่ ให้รัน `build_dashboard.py` ซ้ำเพื่อให้หน้าเว็บตรงกับแผน

### ปุ่มสั่งโพสต์ Facebook จากหน้าเว็บ

หน้าเว็บเป็นไฟล์ static จึงเรียกสคริปต์โพสต์เองไม่ได้ ต้องเปิดผ่านเซิร์ฟเวอร์ในเครื่อง:

```bash
# โหมดปลอดภัย — ปุ่มจะทำได้แค่ "ทดลองโพสต์" (ไม่ยิงเข้า Graph API)
python3 scripts/dashboard_server.py

# เปิดให้ปุ่มโพสต์ขึ้นเพจจริง (ต้องตั้งค่า .env ตาม setup/01-facebook-page.md แล้ว)
python3 scripts/dashboard_server.py --live
```

แล้วเปิด `http://localhost:3000` → คลิกการ์ดวัน → แท็บ Facebook → จะเห็นกล่องโพสต์ด้านล่าง
ปุ่ม "ทดลองโพสต์" จะพิมพ์ข้อความโพสต์ให้ดูก่อน (ไม่ยิง API) ส่วนปุ่ม "โพสต์ขึ้นเพจทันที"
จะถามยืนยันหนึ่งครั้งแล้วโพสต์จริง — วันที่โพสต์แล้วจะขึ้นป้าย on การ์ดและถูกทำเครื่องหมายว่าทำแล้ว

### ปุ่มตั้งเวลาโพสต์ล่วงหน้าจากหน้าเว็บ

ในกล่องเดียวกันมีแถว "ตั้งเวลา" ใช้มอบหมายให้ Facebook โพสต์เองตามวันและเวลาในแผน
(เวลาโพสต์ของแต่ละวันมาจาก `content/plan.json` ไม่ต้องกรอกเอง) — ใช้ความสามารถเดิมของ
`scripts/fb_scheduler.py --schedule` ทุกประการ

- "ทดลองตั้งเวลา" = พิมพ์กำหนดเวลาและข้อความให้ดูก่อน ไม่ยิง API
- "ตั้งเวลาโพสต์ล่วงหน้า" = ตั้งเวลาจริง ถามยืนยันหนึ่งครั้ง แล้วขึ้นป้าย **FB ตั้งเวลาไว้** บนการ์ด
  (ไม่ถูกทำเครื่องหมายว่า "ทำแล้ว" จนกว่าโพสต์จะขึ้นเพจจริง)
- ปุ่มจะกดไม่ได้พร้อมบอกเหตุผล เมื่อ: ยังไม่เปิดเซิร์ฟเวอร์ด้วย `--live`, โทเคนใน `.env` ไม่ครบ,
  วันที่นั้นโพสต์ขึ้นเพจหรือตั้งเวลาไปแล้ว, เลยกำหนดเวลาแล้ว (Meta ต้องล่วงหน้าอย่างน้อย 10 นาที
  — ใช้ปุ่ม "โพสต์ขึ้นเพจทันที" แทน), หรือกำหนดเวลาเกิน 30 วันล่วงหน้า
- ตั้งซ้ำไม่ได้: `state/fb_state.json` กันทั้งการโพสต์และการตั้งเวลาซ้ำวันเดิม

### ปุ่มสร้างโพสต์ร่าง (unpublished) จากหน้าเว็บ

ในกล่องเดียวกันมีแถว "ร่าง" สำหรับสร้างโพสต์ unpublished จากแคปชันของวันนั้น เพื่อเปิดตรวจใน
Meta Business Suite → Content → Drafts ก่อนกดเผยแพร่เอง (ใช้ `--day N --draft` ตัวเดียวกับ CLI)

- "ทดลองสร้างร่าง" = พิมพ์ว่าจะส่งอะไรไป (published=false) โดยไม่ยิง API
- "สร้างโพสต์ร่าง (unpublished)" = ถามยืนยันหนึ่งครั้ง แล้วสร้างร่างจริง — **ไม่ขึ้นเพจ** และไม่ทำเครื่องหมายว่าทำแล้ว
- เมื่อมีร่างของวันนั้นแล้ว ปุ่มจะถูกล็อกพร้อมบอก post id; สร้างซ้ำต้องใช้ `--force` ผ่าน CLI
- คำสั่งนี้เป็น POST ที่ต้องมาจาก origin เดียวกัน (กัน CSRF) และกดได้เฉพาะเมื่อเซิร์ฟเวอร์เปิดด้วย `--live`
- ร่างจากไฟล์ใน `content/drafts/` ยังสร้างด้วย `--draft --file ...` (ไม่มีปุ่มบนหน้าเว็บ เพราะไฟล์ไม่ได้ผูกกับวันในแผน)

**ข้อควรระวัง**

- ค่าเริ่มต้นผูกกับ `127.0.0.1` เท่านั้น — เครื่องอื่นเข้าไม่ถึง **อย่าใช้ `--host 0.0.0.0` ร่วมกับ `--live`** บนเครือข่ายที่คนอื่นเข้าถึงได้
- คำขอที่มาจากคนละ origin ถูกปฏิเสธ (กันเว็บอื่นแอบยิงคำสั่งเข้ามาที่เครื่องคุณ)
- เซิร์ฟเวอร์ไม่เคยส่งโทเคนออกไป มีแค่สถานะ "พร้อม/ยังไม่ตั้งค่า"
- โพสต์ซ้ำไม่ได้: สถานะใน `state/fb_state.json` กันไว้อยู่แล้ว และสคริปต์จะแจ้งว่า "ข้ามเพราะทำแล้ว"

```bash
# ทดสอบหน้าเว็บ (ตรวจ 30 วัน × 3 แพลตฟอร์ม และข้อความที่ปุ่มคัดลอกส่งออกมา)
node tests/dashboard_smoke.mjs

# ทดสอบ API ของเซิร์ฟเวอร์ (รวมการกันโพสต์จริง/กัน CSRF) — รันได้โดยไม่ต้องมีโทเคน
python3 tests/dashboard_api_test.py

# ทดสอบโหมด --draft กับ Graph API จำลอง (ไม่ต่อ Facebook จริง)
python3 tests/fb_draft_test.py
```

### ฉบับร่างโพสต์ + ด่านตรวจก่อนโพสต์

โพสต์ที่ยังไม่ควรขึ้นเพจให้เก็บเป็นไฟล์ใน `content/drafts/` โดยระบุสถานะ "ยังไม่โพสต์"
และปิดท้ายด้วยเช็กลิสต์ที่คนตรวจต้องติ๊กก่อนกดโพสต์

```bash
# ตรวจร่างทุกไฟล์: ความยาวแคปชัน, ประโยคเปิด, ลายเซ็น/แฮชแท็ก/CTA,
# คำสัญญารายได้ต้องห้าม, การหลุดโทเคน และจำนวนข้อในเช็กลิสต์
python3 tests/content_draft_test.py
```

### ส่งร่างขึ้น Facebook แบบ unpublished

โหมด `--draft` อ่านแคปชันจากหัวข้อ `## แคปชัน` ในไฟล์ร่าง แล้วสร้างเป็น **โพสต์ unpublished**
(`published=false` + `unpublished_content_type=DRAFT`) เพื่อเปิดตรวจใน Meta Business Suite → Content → Drafts
ก่อนกดเผยแพร่เอง:

```bash
# ดูตัวอย่างก่อน (dry-run — ไม่ยิง API)
python3 scripts/fb_scheduler.py --draft --file content/drafts/fb-001-page-intro.md

# สร้างร่างจริง
python3 scripts/fb_scheduler.py --draft --file content/drafts/fb-001-page-intro.md --live

# ใช้แคปชันจากแผนแทนไฟล์ร่าง
python3 scripts/fb_scheduler.py --draft --day 5 --live
```

- สคริปต์อ่านกลับมาตรวจ `is_published` ว่าเป็น `false` และเตือนถ้าร่างขึ้นเพจจริง
- ไม่กดเผยแพร่และไม่ตั้งเวลาให้ — คุณกดเองหลังตรวจ
- ร่างที่สร้างแล้วถูกบันทึกใน `state/fb_state.json` (`drafts`) รันซ้ำจะข้ามให้ ใช้ `--force` เมื่อต้องสร้างใหม่
- แคปชันที่ยาวเกิน 2,200 ตัวอักษรหรือมีคำสัญญารายได้จะถูกปฏิเสธก่อนยิง API

### ดูและตรวจสถานะร่างที่สร้างไว้

```bash
# ดูรายการร่างจาก state ในเครื่อง (ไม่ยิง API)
python3 scripts/fb_scheduler.py --list-drafts

# ตรวจกับ Facebook ว่ายังเป็นร่าง / เผยแพร่แล้ว / ถูกลบ
python3 scripts/fb_scheduler.py --verify-drafts
```

`--verify-drafts` อ่านโพสต์ทีละใบด้วย Page token แล้วรายงาน 4 สถานะ

| สถานะ | ความหมาย |
| --- | --- |
| ยังเป็นร่าง (unpublished) | `is_published=false` — ยังไม่ขึ้นเพจ |
| เผยแพร่แล้ว | `is_published=true` — มีการกดเผยแพร่แล้ว (หรือถูกโพสต์จากที่อื่น) |
| ไม่พบใน Graph API | โพสต์ถูกลบ หรือ token ไม่มีสิทธิ์อ่านโพสต์ unpublished (Meta ใช้ข้อความเดียวกัน จึงแยกไม่ได้) |
| ตรวจไม่ได้ | token หมดอายุ/สิทธิ์ไม่พอ/เครือข่ายขัดข้อง — ดูข้อความ error ที่พิมพ์ออกมา |

- ผลตรวจถูกบันทึกลง `state/fb_state.json` (`status`, `checked_at`) ให้ `--list-drafts` แสดงได้ทันทีโดยไม่ต้องยิง API
- ถ้าร่างที่ผูกกับวันในแผนถูกเผยแพร่แล้ว สคริปต์จะบันทึกวันนั้นใน `published` เพื่อกัน `--day N --live` โพสต์ซ้ำ
- exit code: `0` เมื่อตรวจได้ครบทุกรายการ (รวม "ไม่พบ") · `1` เมื่อมีรายการที่ตรวจไม่ได้
- เป็นการอ่านอย่างเดียวบน Facebook — ไม่แก้/ลบโพสต์ และไม่ต้องใช้ `--live`

### ตรวจสถานะร่างอัตโนมัติทุกวัน

`scripts/daily_run.sh` เรียก `--verify-drafts` ให้เอง **ก่อนโพสต์ของวันนี้ทุกครั้ง** (รวม dry-run)
แล้วต่อท้ายผลลง `state/logs/draft-status-YYYY-MM.log` พร้อม timestamp ของรอบนั้น
จึงไม่ต้องสั่ง `--verify-drafts` เองเพื่อจับร่างที่ถูกเผยแพร่หรือหลุด

- ถ้าสถานะเปลี่ยนจากครั้งก่อน สคริปต์จะพิมพ์ `🔔 เปลี่ยนสถานะ` และสรุป `🔔 ร่างที่ต้องตรวจสอบ`
  พร้อมชื่อร่าง — เน้น `draft → published` (เผยแพร่แล้ว) และ `draft → missing` (หลุด/ถูกลบ)
  และบันทึก `status_changed_at` ไว้ใน state เพื่อดูย้อนหลัง
- การตรวจก่อนโพสต์ทำให้ร่างของวันนี้ที่ถูกเผยแพร่แล้วถูกบันทึกเป็น `published` — `--today --live`
  จึงไม่โพสต์ซ้ำ (อย่าสลับลำดับนี้)
- ถ้าตรวจไม่ได้ (ไม่มีโทเคน / โทเคนหมดอายุ / เครือข่ายขัดข้อง) งานโพสต์ของวันนั้นยังทำงานต่อ
  แต่ผลและเหตุผลอยู่ใน log พร้อมบรรทัดเตือนในเทอร์มินัล
- กำหนดโฟลเดอร์ log เองได้ด้วย `DAILY_LOG_DIR=...` เมื่อต้องแยกไฟล์ต่อสภาพแวดล้อม

---

## ชุดภาพแบรนด์ 3 ช่องทาง

ภาพโปรไฟล์ หน้าปก และแบนเนอร์ร้านที่ใช้ร่วมกันทั้ง Facebook, TikTok และ Shopee อยู่ใน `brand/social/`
สร้างจากเรขาคณิตเดียวกับโลโก้ K-Bar และสีจาก `brand/brand-kit.md` — รายละเอียดการอัปโหลดและโซนปลอดภัย
ของแต่ละแพลตฟอร์มอยู่ใน `brand/social/README.md`

| ไฟล์ | ขนาด | ใช้ที่ |
|---|---|---|
| `profile/facebook-profile-1024.png` | 1024×1024 | รูปโปรไฟล์ Facebook Page |
| `profile/tiktok-profile-200.png` | 200×200 | รูปโปรไฟล์ TikTok |
| `profile/shopee-shop-logo-500.png` | 500×500 | โลโก้ร้าน Shopee |
| `cover/facebook-cover-851x315.png` | 851×315 | หน้าปกเพจ Facebook |
| `cover/shopee-cover-1200x675.png` | 1200×675 | Shop Cover |
| `banner/shopee-shop-banner-1200x300.png` | 1200×300 | Shop Banner |
| `cover/tiktok-video-cover-1080x1920.png` | 1080×1920 | ปกคลิป TikTok (TikTok ไม่มีหน้าปกโปรไฟล์) |

หน้าปกและแบนเนอร์ทุกไฟล์มี **SVG ต้นฉบับชื่อเดียวกันวางข้าง PNG** — ข้อความเป็น `<text>` จริง
แก้คำพูด/สีได้ใน Illustrator, Figma หรือ Inkscape โดยไม่ต้องสร้างภาพใหม่ (สัญลักษณ์ K เป็นเวกเตอร์)
SVG เป็นไฟล์สำหรับแก้ต่อ ไม่ใช่ไฟล์อัปโหลด — อัปโหลดเฉพาะ PNG

```bash
# ต้องมี Pillow + numpy สำหรับสร้าง/ตรวจภาพ (ไม่กระทบสคริปต์โพสต์ Facebook)
python3 -m pip install pillow numpy

# สร้างใหม่หลังแก้คำพูด/ขนาดใน brand/social/spec.json
python3 scripts/build_brand_assets.py

# สร้าง/อัปเดต SVG ต้นฉบับ (ต่อจาก PNG)
python3 scripts/build_brand_svg.py

# ตรวจขนาดจริง โซนปลอดภัย คอนทราสต์ คำต้องห้าม และอวตารทั้ง 3 ช่องทางว่าเป็นภาพเดียวกัน
python3 tests/brand_assets_test.py

# ตรวจ SVG ว่าเป็นข้อความจริงและตำแหน่งตรงกับ PNG (ต้องมี resvg ใน PATH สำหรับการเทียบภาพ)
python3 tests/brand_svg_test.py
```

ภาพตัวอย่างสำหรับตรวจด้วยตา: `brand/social/preview/contact-sheet.png` (ทุกชิ้นในภาพเดียว),
`preview/profile-circle-crops.png` (อวตารเมื่อถูกครอปเป็นวงกลม) และ `preview/facebook-cover-safe-zone.png`

## ระบบสร้าง Prompt (สคริปต์ → รูป → วิดีโอ + ปักตะกร้า)

พร้อมต์สำหรับคอนเทนต์ทั้ง 30 วัน ครบ 3 แพลตฟอร์ม สร้างจากข้อมูลจริงใน `data/content_seeds.json`
และ `content/plan.json` — ทุกวันมีพร้อมต์ 3 ขั้นที่ส่งต่อกันได้ และมีช่วงสาธิตการใช้สินค้า
กับจังหวะปักตะกร้า/แนบสินค้าของ Facebook, TikTok และ Shopee ระบุชัดเจนในทุกวัน

```bash
python3 scripts/build_prompts.py            # สร้าง/อัปเดต prompts/generated/
python3 scripts/build_prompts.py --check    # ตรวจว่าพร้อมต์ที่ commit ตรงกับข้อมูลต้นทาง
python3 tests/prompt_system_test.py         # ทดสอบระบบพร้อมต์
```

| สิ่งที่ได้ | ที่ไหน | ใช้กับ |
|---|---|---|
| พร้อมต์เขียนสคริปต์ (ไทย) | `prompts/generated/day-NN.md` | ChatGPT / Claude / Gemini |
| พร้อมต์สร้างภาพ + negative prompt | `prompts/generated/day-NN.md` | Midjourney / FLUX / SDXL / DALL·E |
| พร้อมต์สร้างวิดีโอต่อช็อต | `prompts/generated/day-NN.md` | Veo / Sora / Runway / Kling / Luma |
| ชุดข้อมูลเครื่องอ่าน | `prompts/generated/day-NN.json`, `prompts.json` | ส่งต่อเข้าทูลสร้างภาพ/วิดีโออัตโนมัติ |
| สารบัญ 30 วัน | `prompts/generated/index.md` | เปิดเลือกวัน |
| กติกาแบรนด์/สาธิตสินค้า/ปักตะกร้า | `prompts/system.json` | แก้แล้วรัน `build_prompts.py` ใหม่ |

**ปักตะกร้า:** Facebook ใช้ Product tag + ปักหมุดคอมเมนต์ · TikTok ใช้ TikTok Shop product link
(ตะกร้าเหลือง) · Shopee ใช้ Shopee Video/Live เฉพาะลิสต์ที่อนุมัติ — ทุกแพลตฟอร์มมีทางสำรองเป็น Line OA
รายละเอียดทั้งหมดและข้อจำกัดด้านนโยบายอยู่ที่ `prompts/README.md`

### รันพร้อมต์กับ Gemini จริง (ขั้นสคริปต์)

`scripts/gemini_prompt_runner.py` ส่งพร้อมต์สคริปต์ของวันนั้นเข้า Google Gemini (`generateContent`)
ขอผลเป็น JSON ตรวจด่านคำต้องห้าม/ฟิลด์ครบ/ความยาวแคปชัน แล้วเก็บผลไว้ที่ `content/ai-drafts/`

```bash
# 1) ตั้งค่า key ครั้งเดียว (ห้ามคอมมิต) — ขอ key: https://aistudio.google.com/apikey
cp .env.example .env      # แล้วเติม GEMINI_API_KEY=...

# 2) ดูโมเดลที่บัญชีนี้ใช้ generateContent ได้
python3 scripts/gemini_prompt_runner.py --list-models

# 3) ดู payload + คำสั่ง curl ก่อน โดยไม่ยิง API
python3 scripts/gemini_prompt_runner.py --day 1 --platform tiktok --dry-run

# 4) รันจริง 1 งาน → content/ai-drafts/day-01-tiktok.{md,json}
python3 scripts/gemini_prompt_runner.py --day 1 --platform tiktok

# ทดสอบด้วยเซิร์ฟเวอร์จำลอง ไม่ยิง Google จริง
python3 tests/gemini_runner_test.py
```

- รองรับขั้น **สคริปต์** เท่านั้น — พร้อมต์ภาพ/วิดีโอในไฟล์เดียวกันเป็นของโมเดลสร้างภาพ/วิดีโอ (Midjourney, Veo)
- ผลที่ได้ยังไม่ใช่ฉบับร่างพร้อมโพสต์: ต้องตรวจคำ ใส่เสียงแบรนด์ แล้วค่อยย้ายไป `content/drafts/`
- ทุกครั้งที่รันจะบันทึกประวัติที่ `state/gemini-runs.jsonl` (ไม่ถูกคอมมิต) พร้อมจำนวนโทเคน
- โมเดลเริ่มต้น `gemini-3.8-flash` เปลี่ยนได้ด้วย `--model` หรือ `GEMINI_MODEL` ใน `.env`

> ลำดับการสร้างใหม่หลังแก้เนื้อหา: `generate_plan.py` → `build_prompts.py` → `build_download_bundle.py`

## รวมทุกไฟล์เป็นชุดดาวน์โหลด

```bash
python3 scripts/build_download_bundle.py          # สร้าง downloads/kopwang-all-files-YYYYMMDD.zip
python3 scripts/build_download_bundle.py --check  # ตรวจว่า manifest ตรงกับไฟล์จริง
python3 tests/download_bundle_test.py
```

ชุด zip มีทุกไฟล์ที่ใช้งานได้ของโปรเจกต์ (พร้อมต์ 30 วัน ภาพแบรนด์ เอกสาร และเทสต์)
โดยตัดเฉพาะ `.env`, `state/`, `.git/` และไฟล์แคชออก เปิด `downloads/README.md` เพื่ออ่านวิธีใช้บนเครื่องปลายทาง
ดาวน์โหลดไฟล์ได้จากแผง Files ด้านขวาของ Freebuff — คลาวด์เขียนลงโฟลเดอร์ `Downloads` ของเครื่องคุณโดยตรงไม่ได้
ถ้าต้องการเก็บไว้ที่ `~/Downloads` จริง ๆ ให้สั่งย้ายแชตนี้ไปรันบนเครื่อง

มีสำเนาชื่อสั้นไว้ที่รากโปรเจกต์ด้วย (`kopwang-all-files.zip`) เผื่อแผงไฟล์โหลดจากโฟลเดอร์ซ้อนไม่สะดวก

> **ถ้ากดดาวน์โหลด .zip ไม่ได้** (บางหน้าจอ/แชตรับเฉพาะไฟล์ข้อความ) ให้แยกเป็นชิ้นส่วนข้อความก่อน:
>
> ```bash
> python3 scripts/split_bundle_for_download.py        # → downloads/parts/kopwang-part-NN.txt (ส่วนละ ~400 KB)
> ```
>
> แล้วดาวน์โหลดไฟล์ `.txt` ทั้งหมด + `downloads/parts/REASSEMBLE.md` ไปรวมกลับบนเครื่องปลายทาง:
>
> ```bash
> cat kopwang-part-*.txt | grep -v '^#' | base64 -d > kopwang-all-files.zip
> sha256sum kopwang-all-files.zip     # เทียบกับค่าใน REASSEMBLE.md
> ```

`downloads/` และ `kopwang-all-files.zip` **ไม่ถูกคอมมิต** (สร้างใหม่ได้เสมอด้วย `build_download_bundle.py`)
ถ้าโคลนจาก GitHub ให้กด **Code → Download ZIP** ของ repo แทนได้เลย — ได้ไฟล์ชุดเดียวกันโดยไม่ต้องใช้ชุด zip ที่สร้างไว้

## จังหวะงานประจำวัน

| เวลา | งาน | ทำอย่างไร |
|---|---|---|
| 09:30 | อัปเดตร้าน Shopee | ตาม `content/shopee-30days.md` |
| 09:00 (cron) | ตรวจสถานะร่าง + โพสต์ Facebook | `./scripts/daily_run.sh --live` |
| 12:00-13:00 | ช่วงเวลาที่คนดู Facebook มาก | เช็กคอมเมนต์และตอบ |
| 19:30 | อัปโหลดคลิป TikTok | ใช้สคริปต์ใน `content/tiktok-30days.md` |
| 21:00 | ตอบแชทและสรุปตัวเลขรายวัน | บันทึก 4 ตัวเลขตาม `brand/brand-kit.md` |

เอกสารทั้ง 30 วันเรียงตาม 4 สัปดาห์นี้:

1. **สัปดาห์ 1 (วันที่ 1-7)** วางฐาน: หาเวลา เลือกสินค้า หาทำเลในตลาด ตั้งโปรไฟล์
2. **สัปดาห์ 2 (วันที่ 8-14)** คอนเทนต์ที่คนหยุดดู: hook, โครงคลิป, รีวิว, ตอบคอมเมนต์
3. **สัปดาห์ 3 (วันที่ 15-21)** ระบบหลังบ้าน: แชท ปิดการขาย เก็บลีด วัดผล ทำซ้ำ
4. **สัปดาห์ 4 (วันที่ 22-30)** เปิดขาย E-Book, โบนัส, ตอบข้อโต้แย้ง, สเกลและรอบที่ 2

---

## สถานะการทำงานอัตโนมัติของแต่ละแพลตฟอร์ม

| แพลตฟอร์ม | โพสต์อัตโนมัติ | เหตุผล |
|---|---|---|
| Facebook Page | ✅ ได้ (สคริปต์นี้) | Meta Graph API รองรับ `POST /{page-id}/feed` และตั้งเวลาโพสต์ล่วงหน้า 10 นาที-30 วัน ด้วยสิทธิ์ `pages_manage_posts` |
| TikTok | ❌ ยังไม่ทำ | Content Posting API ต้องผ่านการตรวจสอบไคลเอนต์ก่อน ถ้ายังไม่ผ่านจะโพสต์ได้แบบส่วนตัวเท่านั้น (`SELF_ONLY`) และจำกัด 5 ผู้ใช้/24 ชม. — ดู `setup/02-tiktok.md` |
| Shopee | ❌ ยังไม่ทำ | เป็นงานร้านที่ทำมือ ส่วนการเชื่อมต่อ Open Platform ต้องมีบัญชีนักพัฒนาและการอนุญาตสิทธิ์ร้าน — ดู `setup/03-shopee.md` |

**หมายเหตุด้านนโยบาย:** การสร้างเพจ Facebook ทำผ่านหน้าเว็บเท่านั้น (Meta ไม่มี API สร้างเพจใหม่)
และ TikTok Shop ประเทศไทยจัด **อีบุ๊กแบบดาวน์โหลดเป็นสินค้าที่ไม่รองรับ** ส่วน Shopee ยังไม่ได้ระบุชัดว่าอีบุ๊กดาวน์โหลดเข้าข่าย
— จึงให้ Shopee ทำหน้าที่เป็นช่องทางสร้างความเชื่อถือ และส่งมอบไฟล์จริงผ่าน Line OA ของแบรนด์

---

## ข้อกำหนดของสคริปต์

- Python 3.9+ (ใช้ `zoneinfo`-free fixed offset และ `datetime.timezone` เท่านั้น — รันได้บน 3.9 ขึ้นไป)
- สคริปต์โพสต์/สร้างแผนไม่ต้องใช้ไลบรารีภายนอก
- การสร้างชุดภาพและเทสต์ภาพต้องใช้ `pillow` + `numpy` (และ Pillow ที่มี libraqm เพื่อวางสระ/วรรณยุกต์ไทยให้ถูก)
- ค่าลับทั้งหมดอยู่ใน `.env` ซึ่งถูกกันด้วย `.gitignore` แล้ว — **ห้ามคอมมิตไฟล์นี้**
- ทุกการโพสต์สำเร็จถูกบันทึกใน `state/fb_state.json` เพื่อกันการโพสต์ซ้ำเมื่อรันซ้ำ (รวมโพสต์ร่างจาก `--draft`)

```bash
# ตรวจไฟล์แผนก่อนโพสต์จริง
python3 scripts/fb_scheduler.py --from-day 1 --to-day 30 --schedule   # dry-run ทุกวัน
```

## ขั้นถัดไปที่แนะนำ

- เขียนเนื้อหา E-Book ตาม `docs/ebook-outline.md` ให้เสร็จก่อนวันที่ 22 ของแคมเปญ
- เตรียมฉบับตัวอย่าง 5-8 หน้าไว้ให้ลูกค้าดูก่อนซื้อ
- ถ้าต้องการหน้าขาย + ส่งไฟล์อัตโนมัติ (รับชำระเงิน → ส่งลิงก์ทางอีเมล) บอกได้เลยว่าจะทำเว็บร้านให้ในรอบถัดไป
