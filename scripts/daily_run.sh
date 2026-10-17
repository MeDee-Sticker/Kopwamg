#!/usr/bin/env bash
# Kopwang — งานประจำวันของระบบโพสต์ต่อเนื่อง 30 วัน
#
#   ./scripts/daily_run.sh          ทดลองรัน (dry-run) ดูว่าจะโพสต์อะไรวันนี้
#   ./scripts/daily_run.sh --live   โพสต์จริงเข้า Facebook Page
#
# ทุกครั้งจะตรวจสถานะโพสต์ร่างกับ Facebook ก่อนโพสต์ของวันนี้ และบันทึกผลลง
# state/logs/draft-status-YYYY-MM.log (เขียนทับด้วย DAILY_LOG_DIR ได้)
# ตั้ง cron ให้รันทุกเช้าได้ (ดูตัวอย่างใน setup/01-facebook-page.md ขั้นที่ 7)
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
MODE="${1:-}"
LOG_DIR="${DAILY_LOG_DIR:-state/logs}"
DRAFT_LOG="$LOG_DIR/draft-status-$(date '+%Y-%m').log"

echo "=== $(date '+%Y-%m-%d %H:%M') Kopwang daily run ==="

if [ ! -f content/plan.json ]; then
  echo "ยังไม่มี content/plan.json — สร้างแผน 30 วันก่อน"
  "$PYTHON" scripts/generate_plan.py
fi

# ตรวจก่อนโพสต์: ถ้าร่างของวันนี้ถูกเผยแพร่แล้ว สคริปต์จะบันทึกวันนั้นใน published
# เพื่อให้ --today --live ไม่โพสต์ซ้ำ (การตรวจเป็น read-only บน Facebook)
echo "--- ตรวจสถานะโพสต์ร่าง (อัตโนมัติ) ---"
mkdir -p "$LOG_DIR"
set +e
{
  printf '\n=== %s ===\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
  "$PYTHON" scripts/fb_scheduler.py --verify-drafts 2>&1
} | tee -a "$DRAFT_LOG"
PIPE_STATUS=("${PIPESTATUS[@]}")
DRAFT_RC=${PIPE_STATUS[0]}
TEE_RC=${PIPE_STATUS[1]}
set -e
if [ "$TEE_RC" -ne 0 ]; then
  echo "⚠️ เขียน log ไม่ได้: $DRAFT_LOG"
fi
if [ "$DRAFT_RC" -ne 0 ]; then
  echo "⚠️ ตรวจสถานะร่างไม่ครบ (exit $DRAFT_RC) — ดูรายละเอียดใน $DRAFT_LOG"
  echo "   งานโพสต์ของวันนี้ยังทำงานต่อ"
fi
echo "บันทึกผลตรวจ: $DRAFT_LOG"

echo "--- โพสต์ Facebook ของวันนี้ ---"
if [ "$MODE" = "--live" ]; then
  "$PYTHON" scripts/fb_scheduler.py --today --live
else
  "$PYTHON" scripts/fb_scheduler.py --today
  echo "--- (โหมดทดลอง) เติม --live เพื่อโพสต์จริง ---"
fi

echo "--- งานที่เหลือของวันนี้ (ทำมือ) ---"
"$PYTHON" - "$(date '+%Y-%m-%d')" <<'PY'
import json
import sys
from pathlib import Path

target = sys.argv[1]
plan = json.loads(Path("content/plan.json").read_text(encoding="utf-8"))
rows = [r for r in plan["rows"] if r["date"] == target]

if not rows:
    print(f"ไม่มีรายการในแผนสำหรับ {target} (แคมเปญอาจยังไม่เริ่ม หรือจบแล้ว)")
    raise SystemExit(0)

for row in rows:
    if row["platform"] == "facebook":
        continue
    label = "TikTok" if row["platform"] == "tiktok" else "Shopee"
    print(f"[{row['post_time']}] {label}: {row['title']}")
PY
