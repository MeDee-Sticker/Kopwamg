# วันที่ 19 — วัดผลด้วย 4 ตัวเลขเท่านั้น

- วันที่: 2026-11-03 (อังคาร) · เฟส W3 — ระบบหลังบ้าน — แชท การปิดการขาย เก็บลีด วัดผล
- ฮุก: ดูสถิติให้ถูก 4 ตัวเลข ไม่ต้องดูทั้งหมด
- สินค้า: E-Book Kopwang : ระบบสร้างรายได้ใน 30 วัน · 390 บาท (ปกติ 890 บาท)
- ใช้พร้อมต์ตามลำดับ: (1) เขียนสคริปต์ → (2) สร้างภาพ → (3) สร้างวิดีโอ → ปักตะกร้าในแพลตฟอร์ม
- ไฟล์นี้สร้างจาก `data/content_seeds.json` + `content/plan.json` — แก้ต้นทางแล้วรัน `python3 scripts/build_prompts.py` ใหม่

---

## FACEBOOK — Facebook Page / Reels

- เวลาโพสต์ตามแผน: 12:00 · รูปแบบ: ให้ความรู้
- หัวข้อในแผน: 4 ตัวเลขที่ต้องดูทุกสัปดาห์ (และแก้ตรงไหน)

### 1) พร้อมต์เขียนสคริปต์ (คัดลอกทั้งบล็อก)

```text
บทบาท: คุณเป็นนักเขียนสคริปต์คลิปสั้นภาษาไทยให้แบรนด์ Kopwang
สินค้า: E-Book Kopwang : ระบบสร้างรายได้ใน 30 วัน ราคา 390 บาท (ปกติ 890 บาท)
กลุ่มเป้าหมาย: มนุษย์เงินเดือน ฟรีแลนซ์ แม่บ้าน พ่อค้าออนไลน์มือใหม่ อายุ 25-45
โทนเสียง: พูดตรง ไม่โอ้อวด · เปิดตัวเลขจริงของตัวเองเสมอ · สอนก่อน ขายทีหลัง (สัดส่วน 7:3) · ห้ามสัญญาผลลัพธ์เร็วเกินจริง
แพลตฟอร์ม: Facebook Page / Reels · ความยาว 15-60 วินาที · อัตราส่วน 1:1, 4:5, 16:9
ภารกิจ: เขียนสคริปต์คลิปวันที่ 19 หัวข้อ "วัดผลด้วย 4 ตัวเลขเท่านั้น"
รูปแบบคลิปที่วางไว้: ให้ความรู้

ข้อมูลที่ต้องใช้ (ห้ามคิดข้อเท็จจริงใหม่หรืออ้างตัวเลขที่ไม่มีในนี้):
- ฮุก: ดูสถิติให้ถูก 4 ตัวเลข ไม่ต้องดูทั้งหมด
- ประเด็น 1: ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ
- ประเด็น 2: ถ้าคนเห็นน้อย ให้เพิ่มความถี่ ถ้าอัตราหยุดดูต่ำ ให้แก้ 3 วิแรก
- ประเด็น 3: ถ้าอัตราสนใจสูงแต่ยอดซื้อต่ำ ปัญหาอยู่ที่ข้อเสนอหรือขั้นตอนสั่งซื้อ ไม่ใช่คอนเทนต์
- หลักฐาน/ความน่าเชื่อถือ: การดูตัวเลขเยอะเกินไปทำให้สับสนและเลิกทำ แต่การดูแค่ 4 ตัวทำให้รู้ทันทีว่าควรแก้อะไร
- CTA: กดเซฟ 4 ตัวเลขนี้ไว้ใช้เช็กทุกสัปดาห์
- รูปแบบโพสต์ Facebook: ให้ความรู้
- พาดหัวที่วางไว้: 4 ตัวเลขที่ต้องดูทุกสัปดาห์ (และแก้ตรงไหน)
- ประโยคเปิดที่วางไว้: สถิติมีเป็นสิบตัว แต่มีแค่ 4 ตัวที่บอกได้ว่าเราควรแก้อะไรต่อ

โครงเรื่องที่ต้องมีครบทุกช่วง (ปรับถ้อยคำได้ ห้ามตัดช่วงทิ้ง):
- 0-3s | ฮุกให้หยุดดู: ดูสถิติให้ถูก 4 ตัวเลข ไม่ต้องดูทั้งหมด
- 3-20s | ให้ความรู้ตามประเด็น: ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ | ถ้าคนเห็นน้อย ให้เพิ่มความถี่ ถ้าอัตราหยุดดูต่ำ ให้แก้ 3 วิแรก
- 20-35s | ขยายประเด็นที่เหลือ: ถ้าอัตราสนใจสูงแต่ยอดซื้อต่ำ ปัญหาอยู่ที่ข้อเสนอหรือขั้นตอนสั่งซื้อ ไม่ใช่คอนเทนต์
- 35-45s | สาธิตการใช้สินค้า: เปิดสารบัญให้เห็นครบทุกบท · พลิกหน้า 3-4 บทที่คนสนใจมากที่สุด · เปิดเทมเพลตคอนเทนต์ 30 วัน แล้วชี้ช่องที่ต้องกรอก · เปิดสคริปต์ตอบแชท 12 สถานการณ์ 1 หน้า · เปิดตารางติดตามผล 4 ตัวเลข แล้วกรอกตัวอย่าง 1 แถวให้เห็นภาพ
- 45-52s | หลักฐานหรือตัวเลขจริง: การดูตัวเลขเยอะเกินไปทำให้สับสนและเลิกทำ แต่การดูแค่ 4 ตัวทำให้รู้ทันทีว่าควรแก้อะไร
- 52-60s | ปักสินค้า/คอมเมนต์ + CTA: กดเซฟ 4 ตัวเลขนี้ไว้ใช้เช็กทุกสัปดาห์

ช่วงสาธิตสินค้า: ให้เห็น เปิดสารบัญให้เห็นครบทุกบท ขึ้นไปถึง เปิดตารางติดตามผล 4 ตัวเลข แล้วกรอกตัวอย่าง 1 แถวให้เห็นภาพ · วิธีถ่าย: อัดหน้าจอ (screen record) ด้วยมือถือหรือคอมพิวเตอร์ หรือถ่ายมือถือถือไฟล์จริง/สมุดงานพิมพ์
ช่วงปักตะกร้า/ลิงก์สินค้า: ติดป้ายสินค้า (Product tag) ในโพสต์หรือรีลส์จาก Facebook Shop แล้วปักหมุดคอมเมนต์ลิงก์ Line OA
  ข้อความบนจอ: กดปุ่มสินค้า หรือคอมเมนต์คำว่า 30 · คำพูด: กดปุ่มสินค้าใต้โพสต์ หรือคอมเมนต์คำว่า 30 เดี๋ยวส่งรายละเอียดให้
  ทางสำรอง: ถ้าติดป้ายสินค้าไม่ได้: ปักหมุดคอมเมนต์ลิงก์ Line @kopwang และพูดว่า "ทักไลน์ในคอมเมนต์ปักหมุด"

ข้อห้าม:
- ห้ามใช้คำเหล่านี้ทุกกรณี: รวย, รวยเร็ว, การันตีรายได้, รับประกันรายได้, รายได้แน่นอน, รายได้ guaranteed, ผลลัพธ์ 100%
- ห้ามในงานภาพ: ภาพธนบัตรหรือกองเงิน, เหรียญทองหรือทองคำแท่ง, กราฟกำไรที่อ้างผลตอบแทน, ยอดเงินในแอปธนาคารของผู้อื่น
- ถ้าคลิปมีลิงก์สินค้า/ตะกร้า ให้บอกตรง ๆ ว่าเป็นลิงก์สินค้าของร้าน และไม่สัญญาผลลัพธ์จากการซื้อ
- ข้อความรีวิวหรือภาพลูกค้าใช้ได้หลังขออนุญาตแล้วเท่านั้น และต้องปิดข้อมูลส่วนตัว

ข้อกำหนดผลลัพธ์:
- ภาษาไทยทั้งหมด อ่านออกเสียงได้จริงในเวลาที่กำหนด
- ข้อความบนจอสั้น ไม่เกิน 2 บรรทัด ใช้ฟอนต์ Noto Sans Thai
- ความยาวแคปชันไม่เกิน 2200 ตัวอักษร และมีแฮชแท็กจากแคมเปญ
- ตอบเป็น JSON เท่านั้น ตามโครงนี้:
{
  "voice_over": "สคริปต์พูดทั้งคลิปเป็นภาษาไทย",
  "onscreen_text": [
    {"time": "0-3", "text": "ข้อความสั้นบนจอ ไม่เกิน 2 บรรทัด"}
  ],
  "shot_list": [
    {"time": "0-3", "shot": "ชื่อช็อต", "detail": "สิ่งที่กล้องเห็น"}
  ],
  "caption": "แคปชันสำหรับโพสต์",
  "hashtags": ["#Kopwang"]
}
```

### 2) พร้อมต์สร้างภาพ

| ช็อต | ใช้ทำอะไร | อัตราส่วน | พร้อมต์ (คัดลอก) | ข้อความไทยวางทับ |
|---|---|---|---|---|
| 01-hook | ฮุกให้หยุดดู | 1:1 | `1:1 photorealistic lifestyle image for a Thai online-business brand: Thai creator in their 30s sitting at a small desk at home, talking to a phone on a tripod, warm practical light, dark charcoal room. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | ดูสถิติให้ถูก 4 ตัวเลข ไม่ต้องดูทั้งหมด |
| 02-teach-1 | ให้ความรู้ตามประเด็น | 1:1 | `1:1 photorealistic lifestyle image for a Thai online-business brand: top-down flat lay of an open notebook, pen and smartphone on a dark desk, clean checklist rows visible, generous empty space. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ | ถ้าคน |
| 03-teach-2 | ขยายประเด็นที่เหลือ | 1:1 | `1:1 photorealistic lifestyle image for a Thai online-business brand: top-down flat lay of an open notebook, pen and smartphone on a dark desk, clean checklist rows visible, generous empty space. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | ถ้าอัตราสนใจสูงแต่ยอดซื้อต่ำ ปัญหาอยู่ที่ข้อเสนอหรือขั้นตอนสั่งซื้อ ไม่ใช่คอนเทน |
| 04-demo | สาธิตการใช้สินค้า | 1:1 | `1:1 photorealistic lifestyle image for a Thai online-business brand: over-the-shoulder view of a laptop screen showing an e-book table of contents, a hand pointing at one section, warm screen glow on a dark desk. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | เปิดสารบัญให้เห็นครบทุกบท · พลิกหน้า 3-4 บทที่คนสนใจมากที่สุด · เปิดเทมเพลตคอนเท |
| 05-proof | หลักฐานหรือตัวเลขจริง | 1:1 | `1:1 photorealistic lifestyle image for a Thai online-business brand: smartphone standing on a dark desk showing a clean chat conversation bubble with all personal data blurred, amber accent light. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | การดูตัวเลขเยอะเกินไปทำให้สับสนและเลิกทำ แต่การดูแค่ 4 ตัวทำให้รู้ทันทีว่าควรแก้ |

Negative prompt รวมทุกภาพ: `banknotes, coins, gold bars, profit charts, income guarantees, readable Thai text, unreadable gibberish text, watermark, logo, extra fingers, distorted hands, oversaturated colors, cluttered background`

### 3) พร้อมต์สร้างวิดีโอ

- อัตราส่วน 1:1 · ความยาว 15-60 วินาที

```text
Short-form 1:1 social video for a Thai online-business brand, about 15-60 seconds, 6 shots. Theme: วัดผลด้วย 4 ตัวเลขเท่านั้น.
Shot list:
  1. 0-3s — Thai creator in their 30s sitting at a small desk at home, talking to a phone on a tripod, warm practical light, dark charcoal room.
  2. 3-20s — top-down flat lay of an open notebook, pen and smartphone on a dark desk, clean checklist rows visible, generous empty space.
  3. 20-35s — top-down flat lay of an open notebook, pen and smartphone on a dark desk, clean checklist rows visible, generous empty space.
  4. 35-45s — over-the-shoulder view of a laptop screen showing an e-book table of contents, a hand pointing at one section, warm screen glow on a dark desk.
  5. 45-52s — smartphone standing on a dark desk showing a clean chat conversation bubble with all personal data blurred, amber accent light.
  6. 52-60s — smartphone standing on a dark desk showing an online shop product page with a glowing shopping cart icon, amber accent light, clean negative space.
Product demo: show E-Book Kopwang : ระบบสร้างรายได้ใน 30 วัน on screen (อัดหน้าจอ (screen record) ด้วยมือถือหรือคอมพิวเตอร์ หรือถ่ายมือถือถือไฟล์จริง/สมุดงานพิมพ์).
Cart pin: ติดป้ายสินค้า (Product tag) ในโพสต์หรือรีลส์จาก Facebook Shop แล้วปักหมุดคอมเมนต์ลิงก์ Line OA — appears ติดป้ายตั้งแต่ตอนโพสต์ และปักหมุดคอมเมนต์ทันทีหลังโพสต์; on-screen cue 'กดปุ่มสินค้า หรือคอมเมนต์คำว่า 30' is added in editing, not rendered by the model.
Camera: handheld phone with a subtle push-in on the demo shot and quick cuts on the beat. Lighting: warm practical light, dark charcoal background, amber accent. Audio: clear Thai voice-over, subtle neutral background bed, no copyrighted music.
Leave clean space for Thai text overlays (added later with the brand font) and do not render readable text, currency symbols, banknotes or profit charts.
```

### 4) ปักตะกร้า / ลิงก์สินค้า

- กลไก: ติดป้ายสินค้า (Product tag) ในโพสต์หรือรีลส์จาก Facebook Shop แล้วปักหมุดคอมเมนต์ลิงก์ Line OA
- ตำแหน่ง: ป้ายสินค้าบนโพสต์/มุมล่างของรีลส์ และคอมเมนต์ปักหมุดอันดับแรก
- จังหวะ: ติดป้ายตั้งแต่ตอนโพสต์ และปักหมุดคอมเมนต์ทันทีหลังโพสต์
- ข้อความบนจอ: กดปุ่มสินค้า หรือคอมเมนต์คำว่า 30
- คำพูด: กดปุ่มสินค้าใต้โพสต์ หรือคอมเมนต์คำว่า 30 เดี๋ยวส่งรายละเอียดให้
- ถ้าทำไม่ได้: ถ้าติดป้ายสินค้าไม่ได้: ปักหมุดคอมเมนต์ลิงก์ Line @kopwang และพูดว่า "ทักไลน์ในคอมเมนต์ปักหมุด"

### 5) แคปชันที่ใช้อยู่ (คัดลอกได้)

```text
4 ตัวเลขที่ต้องดูทุกสัปดาห์ (และแก้ตรงไหน)

สถิติมีเป็นสิบตัว แต่มีแค่ 4 ตัวที่บอกได้ว่าเราควรแก้อะไรต่อ

1. ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ
2. ถ้าคนเห็นน้อย ให้เพิ่มความถี่ ถ้าอัตราหยุดดูต่ำ ให้แก้ 3 วิแรก
3. ถ้าอัตราสนใจสูงแต่ยอดซื้อต่ำ ปัญหาอยู่ที่ข้อเสนอหรือขั้นตอนสั่งซื้อ ไม่ใช่คอนเทนต์

💡 การดูตัวเลขเยอะเกินไปทำให้สับสนและเลิกทำ แต่การดูแค่ 4 ตัวทำให้รู้ทันทีว่าควรแก้อะไร

👉 กดเซฟ 4 ตัวเลขนี้ไว้ใช้เช็กทุกสัปดาห์

#Kopwang #ระบบสร้างรายได้ใน30วัน #รายได้เสริม #ทำเงินออนไลน์ #คอนเทนต์ขายของ #ปิดการขาย #ตอบแชทลูกค้า #DAY19

— Kopwang | ระบบสร้างรายได้ใน 30 วัน
```
---

## TIKTOK — TikTok

- เวลาโพสต์ตามแผน: 19:30 · รูปแบบ: Screen Record
- หัวข้อในแผน: "เช็กแค่ 4 ตัวเลขนี้พอ"

### 1) พร้อมต์เขียนสคริปต์ (คัดลอกทั้งบล็อก)

```text
บทบาท: คุณเป็นนักเขียนสคริปต์คลิปสั้นภาษาไทยให้แบรนด์ Kopwang
สินค้า: E-Book Kopwang : ระบบสร้างรายได้ใน 30 วัน ราคา 390 บาท (ปกติ 890 บาท)
กลุ่มเป้าหมาย: มนุษย์เงินเดือน ฟรีแลนซ์ แม่บ้าน พ่อค้าออนไลน์มือใหม่ อายุ 25-45
โทนเสียง: พูดตรง ไม่โอ้อวด · เปิดตัวเลขจริงของตัวเองเสมอ · สอนก่อน ขายทีหลัง (สัดส่วน 7:3) · ห้ามสัญญาผลลัพธ์เร็วเกินจริง
แพลตฟอร์ม: TikTok · ความยาว 21-45 วินาที · อัตราส่วน 9:16
ภารกิจ: เขียนสคริปต์คลิปวันที่ 19 หัวข้อ "วัดผลด้วย 4 ตัวเลขเท่านั้น"
รูปแบบคลิปที่วางไว้: Screen Record

ข้อมูลที่ต้องใช้ (ห้ามคิดข้อเท็จจริงใหม่หรืออ้างตัวเลขที่ไม่มีในนี้):
- ฮุก: ดูสถิติให้ถูก 4 ตัวเลข ไม่ต้องดูทั้งหมด
- ประเด็น 1: ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ
- ประเด็น 2: ถ้าคนเห็นน้อย ให้เพิ่มความถี่ ถ้าอัตราหยุดดูต่ำ ให้แก้ 3 วิแรก
- ประเด็น 3: ถ้าอัตราสนใจสูงแต่ยอดซื้อต่ำ ปัญหาอยู่ที่ข้อเสนอหรือขั้นตอนสั่งซื้อ ไม่ใช่คอนเทนต์
- หลักฐาน/ความน่าเชื่อถือ: การดูตัวเลขเยอะเกินไปทำให้สับสนและเลิกทำ แต่การดูแค่ 4 ตัวทำให้รู้ทันทีว่าควรแก้อะไร
- CTA: กดเซฟ 4 ตัวเลขนี้ไว้ใช้เช็กทุกสัปดาห์

บีตที่ผู้เขียนแผนให้มา (ต้องพูดให้ครบหรือเทียบเท่า):
- 0-3s: โชว์แดชบอร์ดแล้วซูม 4 ตัวเลข
- 3-15s: อธิบายแต่ละตัวบอกอะไร
- 15-22s: ถ้าตัวเลขไหนต่ำ ให้แก้ตรงไหน
- 22-28s: สรุปเป็นเช็กลิสต์สั้น ๆ
- 28-30s: CTA กดเซฟ

โครงเรื่องที่ต้องมีครบทุกช่วง (ปรับถ้อยคำได้ ห้ามตัดช่วงทิ้ง):
- 0-3s | ฮุก 3 วินาทีแรก: "เช็กแค่ 4 ตัวเลขนี้พอ"
- 3-10s | ประเด็นหลักข้อ 1: ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ
- 10-18s | ประเด็นหลักข้อ 2-3: ถ้าคนเห็นน้อย ให้เพิ่มความถี่ ถ้าอัตราหยุดดูต่ำ ให้แก้ 3 วิแรก | ถ้าอัตราสนใจสูงแต่ยอดซื้อต่ำ ปัญหาอยู่ที่ข้อเสนอหรือขั้นตอนสั่งซื้อ ไม่ใช่คอนเทนต์
- 18-28s | สาธิตการใช้สินค้า: เปิดสารบัญให้เห็นครบทุกบท · พลิกหน้า 3-4 บทที่คนสนใจมากที่สุด · เปิดเทมเพลตคอนเทนต์ 30 วัน แล้วชี้ช่องที่ต้องกรอก · เปิดสคริปต์ตอบแชท 12 สถานการณ์ 1 หน้า · เปิดตารางติดตามผล 4 ตัวเลข แล้วกรอกตัวอย่าง 1 แถวให้เห็นภาพ
- 28-36s | หลักฐานและความน่าเชื่อถือ: การดูตัวเลขเยอะเกินไปทำให้สับสนและเลิกทำ แต่การดูแค่ 4 ตัวทำให้รู้ทันทีว่าควรแก้อะไร
- 36-45s | ปักตะกร้า + CTA: กดเซฟ 4 ตัวเลขนี้ไว้ใช้เช็กทุกสัปดาห์

ช่วงสาธิตสินค้า: ให้เห็น เปิดสารบัญให้เห็นครบทุกบท ขึ้นไปถึง เปิดตารางติดตามผล 4 ตัวเลข แล้วกรอกตัวอย่าง 1 แถวให้เห็นภาพ · วิธีถ่าย: อัดหน้าจอ (screen record) ด้วยมือถือหรือคอมพิวเตอร์ หรือถ่ายมือถือถือไฟล์จริง/สมุดงานพิมพ์
ช่วงปักตะกร้า/ลิงก์สินค้า: แนบสินค้า TikTok Shop (Product link) ให้ติดกับคลิป
  ข้อความบนจอ: กดตะกร้าเหลือง ดูรายละเอียด · คำพูด: กดตะกร้าเหลืองตรงมุมล่างซ้ายได้เลย
  ทางสำรอง: ถ้ายังปักตะกร้าไม่ได้: ปักหมุดคอมเมนต์ลิงก์ Line @kopwang แล้วพูดว่า "ทักไลน์ในคอมเมนต์ปักหมุด"

ข้อห้าม:
- ห้ามใช้คำเหล่านี้ทุกกรณี: รวย, รวยเร็ว, การันตีรายได้, รับประกันรายได้, รายได้แน่นอน, รายได้ guaranteed, ผลลัพธ์ 100%
- ห้ามในงานภาพ: ภาพธนบัตรหรือกองเงิน, เหรียญทองหรือทองคำแท่ง, กราฟกำไรที่อ้างผลตอบแทน, ยอดเงินในแอปธนาคารของผู้อื่น
- ถ้าคลิปมีลิงก์สินค้า/ตะกร้า ให้บอกตรง ๆ ว่าเป็นลิงก์สินค้าของร้าน และไม่สัญญาผลลัพธ์จากการซื้อ
- ข้อความรีวิวหรือภาพลูกค้าใช้ได้หลังขออนุญาตแล้วเท่านั้น และต้องปิดข้อมูลส่วนตัว

ข้อกำหนดผลลัพธ์:
- ภาษาไทยทั้งหมด อ่านออกเสียงได้จริงในเวลาที่กำหนด
- ข้อความบนจอสั้น ไม่เกิน 2 บรรทัด ใช้ฟอนต์ Noto Sans Thai
- ความยาวแคปชันไม่เกิน 2200 ตัวอักษร และมีแฮชแท็กจากแคมเปญ
- ตอบเป็น JSON เท่านั้น ตามโครงนี้:
{
  "voice_over": "สคริปต์พูดทั้งคลิปเป็นภาษาไทย",
  "onscreen_text": [
    {"time": "0-3", "text": "ข้อความสั้นบนจอ ไม่เกิน 2 บรรทัด"}
  ],
  "shot_list": [
    {"time": "0-3", "shot": "ชื่อช็อต", "detail": "สิ่งที่กล้องเห็น"}
  ],
  "caption": "แคปชันสำหรับโพสต์",
  "hashtags": ["#Kopwang"]
}
```

### 2) พร้อมต์สร้างภาพ

| ช็อต | ใช้ทำอะไร | อัตราส่วน | พร้อมต์ (คัดลอก) | ข้อความไทยวางทับ |
|---|---|---|---|---|
| 01-hook | ฮุก 3 วินาทีแรก | 9:16 | `9:16 photorealistic lifestyle image for a Thai online-business brand: Thai creator in their 30s sitting at a small desk at home, talking to a phone on a tripod, warm practical light, dark charcoal room. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | "เช็กแค่ 4 ตัวเลขนี้พอ" |
| 02-teach-1 | ประเด็นหลักข้อ 1 | 9:16 | `9:16 photorealistic lifestyle image for a Thai online-business brand: top-down flat lay of an open notebook, pen and smartphone on a dark desk, clean checklist rows visible, generous empty space. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ |
| 03-teach-2 | ประเด็นหลักข้อ 2-3 | 9:16 | `9:16 photorealistic lifestyle image for a Thai online-business brand: top-down flat lay of an open notebook, pen and smartphone on a dark desk, clean checklist rows visible, generous empty space. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | ถ้าคนเห็นน้อย ให้เพิ่มความถี่ ถ้าอัตราหยุดดูต่ำ ให้แก้ 3 วิแรก | ถ้าอัตราสนใจสูง |
| 04-demo | สาธิตการใช้สินค้า | 9:16 | `9:16 photorealistic lifestyle image for a Thai online-business brand: over-the-shoulder view of a laptop screen showing an e-book table of contents, a hand pointing at one section, warm screen glow on a dark desk. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | เปิดสารบัญให้เห็นครบทุกบท · พลิกหน้า 3-4 บทที่คนสนใจมากที่สุด · เปิดเทมเพลตคอนเท |
| 05-proof | หลักฐานและความน่าเชื่อถือ | 9:16 | `9:16 photorealistic lifestyle image for a Thai online-business brand: smartphone standing on a dark desk showing a clean chat conversation bubble with all personal data blurred, amber accent light. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | การดูตัวเลขเยอะเกินไปทำให้สับสนและเลิกทำ แต่การดูแค่ 4 ตัวทำให้รู้ทันทีว่าควรแก้ |

Negative prompt รวมทุกภาพ: `banknotes, coins, gold bars, profit charts, income guarantees, readable Thai text, unreadable gibberish text, watermark, logo, extra fingers, distorted hands, oversaturated colors, cluttered background`

### 3) พร้อมต์สร้างวิดีโอ

- อัตราส่วน 9:16 · ความยาว 21-45 วินาที

```text
Short-form 9:16 social video for a Thai online-business brand, about 21-45 seconds, 6 shots. Theme: วัดผลด้วย 4 ตัวเลขเท่านั้น.
Shot list:
  1. 0-3s — Thai creator in their 30s sitting at a small desk at home, talking to a phone on a tripod, warm practical light, dark charcoal room.
  2. 3-10s — top-down flat lay of an open notebook, pen and smartphone on a dark desk, clean checklist rows visible, generous empty space.
  3. 10-18s — top-down flat lay of an open notebook, pen and smartphone on a dark desk, clean checklist rows visible, generous empty space.
  4. 18-28s — over-the-shoulder view of a laptop screen showing an e-book table of contents, a hand pointing at one section, warm screen glow on a dark desk.
  5. 28-36s — smartphone standing on a dark desk showing a clean chat conversation bubble with all personal data blurred, amber accent light.
  6. 36-45s — smartphone standing on a dark desk showing an online shop product page with a glowing shopping cart icon, amber accent light, clean negative space.
Product demo: show E-Book Kopwang : ระบบสร้างรายได้ใน 30 วัน on screen (อัดหน้าจอ (screen record) ด้วยมือถือหรือคอมพิวเตอร์ หรือถ่ายมือถือถือไฟล์จริง/สมุดงานพิมพ์).
Cart pin: แนบสินค้า TikTok Shop (Product link) ให้ติดกับคลิป — appears ให้ตะกร้าปรากฏตั้งแต่ช่วงสาธิตสินค้า (ประมาณวินาทีที่ 8-12) และคงอยู่จนจบคลิป; on-screen cue 'กดตะกร้าเหลือง ดูรายละเอียด' is added in editing, not rendered by the model.
Camera: handheld phone with a subtle push-in on the demo shot and quick cuts on the beat. Lighting: warm practical light, dark charcoal background, amber accent. Audio: clear Thai voice-over, subtle neutral background bed, no copyrighted music.
Leave clean space for Thai text overlays (added later with the brand font) and do not render readable text, currency symbols, banknotes or profit charts.
```

### 4) ปักตะกร้า / ลิงก์สินค้า

- กลไก: แนบสินค้า TikTok Shop (Product link) ให้ติดกับคลิป
- ตำแหน่ง: ไอคอนตะกร้าเหลืองมุมล่างซ้ายของวิดีโอ
- จังหวะ: ให้ตะกร้าปรากฏตั้งแต่ช่วงสาธิตสินค้า (ประมาณวินาทีที่ 8-12) และคงอยู่จนจบคลิป
- ข้อความบนจอ: กดตะกร้าเหลือง ดูรายละเอียด
- คำพูด: กดตะกร้าเหลืองตรงมุมล่างซ้ายได้เลย
- ถ้าทำไม่ได้: ถ้ายังปักตะกร้าไม่ได้: ปักหมุดคอมเมนต์ลิงก์ Line @kopwang แล้วพูดว่า "ทักไลน์ในคอมเมนต์ปักหมุด"

### 5) แคปชันที่ใช้อยู่ (คัดลอกได้)

```text
ดูสถิติให้ถูก 4 ตัวเลข ไม่ต้องดูทั้งหมด

ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ

กดเซฟ 4 ตัวเลขนี้ไว้ใช้เช็กทุกสัปดาห์

#Kopwang #ระบบสร้างรายได้ใน30วัน #รายได้เสริม #ทำเงินออนไลน์ #คอนเทนต์ขายของ #ปิดการขาย #ตอบแชทลูกค้า #DAY19
```
---

## SHOPEE — Shopee Shop / Shopee Video

- เวลาโพสต์ตามแผน: 09:30 · รูปแบบ: shop action
- หัวข้อในแผน: เช็กอัตราการเข้าชมเทียบการสั่งซื้อของสินค้าแต่ละตัว แล้วคัดตัวที่ควรปรับก่อน

### 1) พร้อมต์เขียนสคริปต์ (คัดลอกทั้งบล็อก)

```text
บทบาท: คุณเป็นนักเขียนสคริปต์คลิปสั้นภาษาไทยให้แบรนด์ Kopwang
สินค้า: E-Book Kopwang : ระบบสร้างรายได้ใน 30 วัน ราคา 390 บาท (ปกติ 890 บาท)
กลุ่มเป้าหมาย: มนุษย์เงินเดือน ฟรีแลนซ์ แม่บ้าน พ่อค้าออนไลน์มือใหม่ อายุ 25-45
โทนเสียง: พูดตรง ไม่โอ้อวด · เปิดตัวเลขจริงของตัวเองเสมอ · สอนก่อน ขายทีหลัง (สัดส่วน 7:3) · ห้ามสัญญาผลลัพธ์เร็วเกินจริง
แพลตฟอร์ม: Shopee Shop / Shopee Video · ความยาว 15-40 วินาที · อัตราส่วน 1:1, 9:16
ภารกิจ: เขียนสคริปต์คลิปวันที่ 19 หัวข้อ "วัดผลด้วย 4 ตัวเลขเท่านั้น"
รูปแบบคลิปที่วางไว้: shop action

ข้อมูลที่ต้องใช้ (ห้ามคิดข้อเท็จจริงใหม่หรืออ้างตัวเลขที่ไม่มีในนี้):
- ฮุก: ดูสถิติให้ถูก 4 ตัวเลข ไม่ต้องดูทั้งหมด
- ประเด็น 1: ตัวเลข 4 ตัว: คนเห็นโพสต์ อัตราหยุดดู อัตราสนใจ (คอมเมนต์+แชท) อัตราซื้อ
- ประเด็น 2: ถ้าคนเห็นน้อย ให้เพิ่มความถี่ ถ้าอัตราหยุดดูต่ำ ให้แก้ 3 วิแรก
- ประเด็น 3: ถ้าอัตราสนใจสูงแต่ยอดซื้อต่ำ ปัญหาอยู่ที่ข้อเสนอหรือขั้นตอนสั่งซื้อ ไม่ใช่คอนเทนต์
- หลักฐาน/ความน่าเชื่อถือ: การดูตัวเลขเยอะเกินไปทำให้สับสนและเลิกทำ แต่การดูแค่ 4 ตัวทำให้รู้ทันทีว่าควรแก้อะไร
- CTA: กดเซฟ 4 ตัวเลขนี้ไว้ใช้เช็กทุกสัปดาห์

- งานร้าน Shopee ของวันนี้: เช็กอัตราการเข้าชมเทียบการสั่งซื้อของสินค้าแต่ละตัว แล้วคัดตัวที่ควรปรับก่อน

โครงเรื่องที่ต้องมีครบทุกช่วง (ปรับถ้อยคำได้ ห้ามตัดช่วงทิ้ง):
- 0-5s | อัปเดตหน้าร้าน: เช็กอัตราการเข้าชมเทียบการสั่งซื้อของสินค้าแต่ละตัว แล้วคัดตัวที่ควรปรับก่อน
- 5-15s | ภาพสินค้าที่ Shopee อนุมัติ: เช็กอัตราการเข้าชมเทียบการสั่งซื้อของสินค้าแต่ละตัว แล้วคัดตัวที่ควรปรับก่อน
- 15-28s | สาธิตสินค้า/ของจริงในมือ: เปิดสารบัญให้เห็นครบทุกบท · พลิกหน้า 3-4 บทที่คนสนใจมากที่สุด · เปิดเทมเพลตคอนเทนต์ 30 วัน แล้วชี้ช่องที่ต้องกรอก · เปิดสคริปต์ตอบแชท 12 สถานการณ์ 1 หน้า · เปิดตารางติดตามผล 4 ตัวเลข แล้วกรอกตัวอย่าง 1 แถวให้เห็นภาพ
- 28-40s | ปักตะกร้า Shopee Video + CTA: กดเซฟ 4 ตัวเลขนี้ไว้ใช้เช็กทุกสัปดาห์

ช่วงสาธิตสินค้า: ให้เห็น เปิดสารบัญให้เห็นครบทุกบท ขึ้นไปถึง เปิดตารางติดตามผล 4 ตัวเลข แล้วกรอกตัวอย่าง 1 แถวให้เห็นภาพ · วิธีถ่าย: อัดหน้าจอ (screen record) ด้วยมือถือหรือคอมพิวเตอร์ หรือถ่ายมือถือถือไฟล์จริง/สมุดงานพิมพ์
ช่วงปักตะกร้า/ลิงก์สินค้า: แนบสินค้าใน Shopee Video หรือปักตะกร้าใน Shopee Live เฉพาะลิสต์ที่ Shopee อนุมัติแล้ว
  ข้อความบนจอ: กดตะกร้าใน Shopee Video · คำพูด: กดตะกร้าใน Shopee Video ได้เลย หรือทักแชทร้านถ้ายังไม่เห็นสินค้า
  ทางสำรอง: ถ้ายังไม่มีลิสต์ที่อนุมัติ: ใช้แชทร้านและโปรไฟล์ชี้ไปที่ Line @kopwang โดยไม่วางไฟล์ในลิสต์
  ข้อกำหนดที่ต้องรู้: อ้างอิง setup/03-shopee.md — Shopee ยังไม่ยืนยันว่าขายไฟล์อีบุ๊กได้ ต้องได้คำยืนยันเป็นลายลักษณ์อักษรก่อนตั้งลิสต์

ข้อห้าม:
- ห้ามใช้คำเหล่านี้ทุกกรณี: รวย, รวยเร็ว, การันตีรายได้, รับประกันรายได้, รายได้แน่นอน, รายได้ guaranteed, ผลลัพธ์ 100%
- ห้ามในงานภาพ: ภาพธนบัตรหรือกองเงิน, เหรียญทองหรือทองคำแท่ง, กราฟกำไรที่อ้างผลตอบแทน, ยอดเงินในแอปธนาคารของผู้อื่น
- ถ้าคลิปมีลิงก์สินค้า/ตะกร้า ให้บอกตรง ๆ ว่าเป็นลิงก์สินค้าของร้าน และไม่สัญญาผลลัพธ์จากการซื้อ
- ข้อความรีวิวหรือภาพลูกค้าใช้ได้หลังขออนุญาตแล้วเท่านั้น และต้องปิดข้อมูลส่วนตัว

ข้อกำหนดผลลัพธ์:
- ภาษาไทยทั้งหมด อ่านออกเสียงได้จริงในเวลาที่กำหนด
- ข้อความบนจอสั้น ไม่เกิน 2 บรรทัด ใช้ฟอนต์ Noto Sans Thai
- ความยาวแคปชันไม่เกิน 1000 ตัวอักษร และมีแฮชแท็กจากแคมเปญ
- ตอบเป็น JSON เท่านั้น ตามโครงนี้:
{
  "voice_over": "สคริปต์พูดทั้งคลิปเป็นภาษาไทย",
  "onscreen_text": [
    {"time": "0-3", "text": "ข้อความสั้นบนจอ ไม่เกิน 2 บรรทัด"}
  ],
  "shot_list": [
    {"time": "0-3", "shot": "ชื่อช็อต", "detail": "สิ่งที่กล้องเห็น"}
  ],
  "caption": "แคปชันสำหรับโพสต์",
  "hashtags": ["#Kopwang"]
}
```

### 2) พร้อมต์สร้างภาพ

| ช็อต | ใช้ทำอะไร | อัตราส่วน | พร้อมต์ (คัดลอก) | ข้อความไทยวางทับ |
|---|---|---|---|---|
| 01-shop | อัปเดตหน้าร้าน | 1:1 | `1:1 photorealistic lifestyle image for a Thai online-business brand: e-commerce pack shot of a printed workbook and a notebook on a cream surface, soft shadow, minimal props, product photography. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | เช็กอัตราการเข้าชมเทียบการสั่งซื้อของสินค้าแต่ละตัว แล้วคัดตัวที่ควรปรับก่อน |
| 02-shop | ภาพสินค้าที่ Shopee อนุมัติ | 1:1 | `1:1 photorealistic lifestyle image for a Thai online-business brand: e-commerce pack shot of a printed workbook and a notebook on a cream surface, soft shadow, minimal props, product photography. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | เช็กอัตราการเข้าชมเทียบการสั่งซื้อของสินค้าแต่ละตัว แล้วคัดตัวที่ควรปรับก่อน |
| 03-demo | สาธิตสินค้า/ของจริงในมือ | 1:1 | `1:1 photorealistic lifestyle image for a Thai online-business brand: over-the-shoulder view of a laptop screen showing an e-book table of contents, a hand pointing at one section, warm screen glow on a dark desk. Shot on 50mm lens, f/2.0, soft diffused window light, dark charcoal background (#14161C) with amber (#FFB020) accents and cream (#F5EFE2) surfaces, minimal props, mobile-first composition with clean empty space at the top for a Thai caption overlay, high detail, no text, no logos, no currency` | เปิดสารบัญให้เห็นครบทุกบท · พลิกหน้า 3-4 บทที่คนสนใจมากที่สุด · เปิดเทมเพลตคอนเท |

Negative prompt รวมทุกภาพ: `banknotes, coins, gold bars, profit charts, income guarantees, readable Thai text, unreadable gibberish text, watermark, logo, extra fingers, distorted hands, oversaturated colors, cluttered background`

### 3) พร้อมต์สร้างวิดีโอ

- อัตราส่วน 1:1 · ความยาว 15-40 วินาที

```text
Short-form 1:1 social video for a Thai online-business brand, about 15-40 seconds, 4 shots. Theme: วัดผลด้วย 4 ตัวเลขเท่านั้น.
Shot list:
  1. 0-5s — e-commerce pack shot of a printed workbook and a notebook on a cream surface, soft shadow, minimal props, product photography.
  2. 5-15s — e-commerce pack shot of a printed workbook and a notebook on a cream surface, soft shadow, minimal props, product photography.
  3. 15-28s — over-the-shoulder view of a laptop screen showing an e-book table of contents, a hand pointing at one section, warm screen glow on a dark desk.
  4. 28-40s — smartphone standing on a dark desk showing an online shop product page with a glowing shopping cart icon, amber accent light, clean negative space.
Product demo: show E-Book Kopwang : ระบบสร้างรายได้ใน 30 วัน on screen (อัดหน้าจอ (screen record) ด้วยมือถือหรือคอมพิวเตอร์ หรือถ่ายมือถือถือไฟล์จริง/สมุดงานพิมพ์).
Cart pin: แนบสินค้าใน Shopee Video หรือปักตะกร้าใน Shopee Live เฉพาะลิสต์ที่ Shopee อนุมัติแล้ว — appears แนบตะกร้าตั้งแต่เปิดคลิป และพูดถึงอีกครั้งในช่วง 5 วินาทีสุดท้าย; on-screen cue 'กดตะกร้าใน Shopee Video' is added in editing, not rendered by the model.
Camera: handheld phone with a subtle push-in on the demo shot and quick cuts on the beat. Lighting: warm practical light, dark charcoal background, amber accent. Audio: clear Thai voice-over, subtle neutral background bed, no copyrighted music.
Leave clean space for Thai text overlays (added later with the brand font) and do not render readable text, currency symbols, banknotes or profit charts.
```

### 4) ปักตะกร้า / ลิงก์สินค้า

- กลไก: แนบสินค้าใน Shopee Video หรือปักตะกร้าใน Shopee Live เฉพาะลิสต์ที่ Shopee อนุมัติแล้ว
- ตำแหน่ง: ไอคอนตะกร้า/สินค้าใน Shopee Video และในไลฟ์
- จังหวะ: แนบตะกร้าตั้งแต่เปิดคลิป และพูดถึงอีกครั้งในช่วง 5 วินาทีสุดท้าย
- ข้อความบนจอ: กดตะกร้าใน Shopee Video
- คำพูด: กดตะกร้าใน Shopee Video ได้เลย หรือทักแชทร้านถ้ายังไม่เห็นสินค้า
- ถ้าทำไม่ได้: ถ้ายังไม่มีลิสต์ที่อนุมัติ: ใช้แชทร้านและโปรไฟล์ชี้ไปที่ Line @kopwang โดยไม่วางไฟล์ในลิสต์
- ข้อกำหนดนโยบาย: อ้างอิง setup/03-shopee.md — Shopee ยังไม่ยืนยันว่าขายไฟล์อีบุ๊กได้ ต้องได้คำยืนยันเป็นลายลักษณ์อักษรก่อนตั้งลิสต์

---

## ข้อห้ามก่อนส่งงาน

```text
- ห้ามใช้คำเหล่านี้ทุกกรณี: รวย, รวยเร็ว, การันตีรายได้, รับประกันรายได้, รายได้แน่นอน, รายได้ guaranteed, ผลลัพธ์ 100%
- ห้ามในงานภาพ: ภาพธนบัตรหรือกองเงิน, เหรียญทองหรือทองคำแท่ง, กราฟกำไรที่อ้างผลตอบแทน, ยอดเงินในแอปธนาคารของผู้อื่น
- ถ้าคลิปมีลิงก์สินค้า/ตะกร้า ให้บอกตรง ๆ ว่าเป็นลิงก์สินค้าของร้าน และไม่สัญญาผลลัพธ์จากการซื้อ
- ข้อความรีวิวหรือภาพลูกค้าใช้ได้หลังขออนุญาตแล้วเท่านั้น และต้องปิดข้อมูลส่วนตัว
```
