#!/usr/bin/env python3
"""Kopwang — Facebook Page publisher for the 30-day content plan.

Publishes (or schedules) the Facebook rows of content/plan.json to your Page through
the Meta Graph API. TikTok rows and Shopee tasks are intentionally NOT automated:
TikTok needs an approved Content Posting API client, and Shopee work is manual.

Setup: see setup/01-facebook-page.md
Credentials live in a .env file in the repo root (never committed):

    FB_APP_ID=...
    FB_APP_SECRET=...
    FB_PAGE_ID=...
    FB_PAGE_ACCESS_TOKEN=...

Examples
--------
    # 1) swap a short-lived user token for a long-lived one + print Page tokens
    python3 scripts/fb_scheduler.py --exchange-token "EAAG..."

    # 2) confirm which Page the token can post to
    python3 scripts/fb_scheduler.py --check

    # 3) see what today's post would be (no network call, no API writes)
    python3 scripts/fb_scheduler.py --today

    # 4) publish day 5 for real
    python3 scripts/fb_scheduler.py --day 5 --live

    # 5) hand the rest of the campaign to Facebook's own scheduler
    python3 scripts/fb_scheduler.py --schedule --from-day 6 --to-day 30 --live

    # 6) create an unpublished draft in Facebook from a local draft file
    python3 scripts/fb_scheduler.py --draft --file content/drafts/fb-001-page-intro.md --live

    # 7) list the drafts we recorded, then check their live status on Facebook
    #    (scripts/daily_run.sh calls --verify-drafts every morning and logs the result)
    python3 scripts/fb_scheduler.py --list-drafts
    python3 scripts/fb_scheduler.py --verify-drafts

Every successful write is recorded in state/fb_state.json so a rerun never double-posts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "content" / "plan.json"
ENV_FILE = ROOT / ".env"
STATE_FILE = ROOT / "state" / "fb_state.json"

DEFAULT_GRAPH_VERSION = "v26.0"
BANGKOK = timezone(timedelta(hours=7))
MAX_SCHEDULE_AHEAD_DAYS = 30  # Meta rejects scheduled_publish_time beyond 30 days
MIN_SCHEDULE_AHEAD_MINUTES = 10

DRAFT_DIR = ROOT / "content" / "drafts"
MAX_DRAFT_CHARS = 2200  # เพดานเดียวกับด่านตรวจคอนเทนต์ (tests/content_draft_test.py)
BANNED_CLAIMS = ("รวย", "การันตีรายได้", "รับประกันรายได้", "รายได้แน่นอน", "รายได้ guaranteed")

DRAFT_STATUS_LABELS = {
    "draft": "ยังเป็นร่าง (unpublished)",
    "published": "เผยแพร่แล้ว",
    "missing": "ไม่พบใน Graph API",
    "error": "ตรวจไม่ได้",
}


# --------------------------------------------------------------------------- helpers


def load_env(path: Path = ENV_FILE) -> dict:
    """Minimal .env reader — no dependency, no shell sourcing."""
    values = dict(os.environ)
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val and not values.get(key):
                values[key] = val
    return values


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"published": {}, "scheduled": {}, "drafts": {}, "history": []}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def graph_url(version: str, path: str) -> str:
    return f"https://graph.facebook.com/{version}/{path.lstrip('/')}"


class GraphError(RuntimeError):
    """ข้อผิดพลาดจาก Graph API ที่ผู้เรียกจับได้ (เช่น แยกร่างที่ถูกลบออกจากร่างที่ยังอยู่)"""

    def __init__(self, status: int | None, code: int | None, message: str, *, network: bool = False):
        self.status = status
        self.code = code
        self.message = message
        self.network = network
        super().__init__(message)

    @property
    def not_found(self) -> bool:
        """Graph API ตอบว่าไม่พบ object นี้ (โพสต์ถูกลบ หรือ token ไม่มีสิทธิ์อ่าน)"""
        text = (self.message or "").lower()
        return (
            self.status == 404
            or self.code == 803
            or "does not exist" in text
            or "unsupported get request" in text
        )


def graph_call(version: str, path: str, params: dict, method: str = "GET") -> dict:
    """เรียก Graph API พร้อม backoff — โยน GraphError ให้ผู้เรียกตัดสินใจเอง"""
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    data = query.encode() if method == "POST" else None
    url = graph_url(version, path)
    if method == "GET":
        url = f"{url}?{query}"

    delay = 2.0
    last_error = None
    for attempt in range(4):
        request = urllib.request.Request(url, data=data, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                usage = response.headers.get("X-Business-Use-Case-Usage") or response.headers.get(
                    "X-App-Usage"
                )
                if usage:
                    print(f"    [rate-limit] {usage}", file=sys.stderr)
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            try:
                payload = json.loads(body)
                err = payload.get("error", {})
            except json.JSONDecodeError:
                err = {"message": body}
            code = err.get("code")
            last_error = (exc.code, code, err)
            retryable = exc.code in (429, 500, 502, 503) or code in (4, 17, 32, 613)
            if retryable and attempt < 3:
                print(
                    f"    [retry {attempt + 1}/3] HTTP {exc.code} code={code} — รอ {delay:.0f}s",
                    file=sys.stderr,
                )
                time.sleep(delay)
                delay *= 2
                continue
            raise GraphError(exc.code, code, str(err.get("message", body))) from None
        except urllib.error.URLError as exc:
            last_error = (None, None, {"message": str(exc)})
            if attempt < 3:
                print(f"    [retry {attempt + 1}/3] network: {exc} — รอ {delay:.0f}s", file=sys.stderr)
                time.sleep(delay)
                delay *= 2
                continue
            raise GraphError(None, None, f"เชื่อมต่อ Graph API ไม่ได้: {exc}", network=True) from None
    raise GraphError(None, None, f"Graph API ล้มเหลวหลังลองซ้ำ: {last_error}")


def graph_request(version: str, path: str, params: dict, method: str = "GET") -> dict:
    """Call the Graph API with backoff on throttling and transient server errors."""
    try:
        return graph_call(version, path, params, method)
    except GraphError as exc:
        if exc.status is None:
            raise SystemExit(exc.message) from None
        raise SystemExit(f"Graph API error: HTTP {exc.status} {exc.message}") from None


def require(env: dict, *keys: str) -> None:
    missing = [k for k in keys if not env.get(k)]
    if missing:
        raise SystemExit(
            "ขาดค่าตั้งต้นใน .env: " + ", ".join(missing) + "\nดูวิธีได้ที่ setup/01-facebook-page.md"
        )


def parse_slot(row: dict) -> datetime:
    """Combine a plan row's date with its post_time (Asia/Bangkok)."""
    hour, minute = (int(x) for x in row["post_time"].split(":"))
    d = date.fromisoformat(row["date"])
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=BANGKOK)


def schedule_window(row: dict, now: datetime | None = None) -> str:
    """บอกว่าตั้งเวลาโพสต์ของแถวนี้ได้หรือไม่: "ok" | "past" | "too_far"

    ใช้ร่วมกับหน้าเว็บ เพื่อไม่ให้กด "ตั้งเวลา" แล้วกลายเป็นการโพสต์ทันที
    โดยไม่ตั้งใจ (พฤติกรรมเดิมของ _schedule เมื่อเลยกำหนดไปแล้ว)
    """
    when = parse_slot(row)
    now = now or datetime.now(BANGKOK)
    if when >= now + timedelta(days=MAX_SCHEDULE_AHEAD_DAYS):
        return "too_far"
    if when < now + timedelta(minutes=MIN_SCHEDULE_AHEAD_MINUTES):
        return "past"
    return "ok"


def facebook_rows(plan: dict) -> list[dict]:
    rows = [r for r in plan["rows"] if r["platform"] == "facebook"]
    if not rows:
        raise SystemExit("ไม่พบโพสต์ facebook ใน content/plan.json — รัน generate_plan.py ก่อน")
    return rows


def _display_path(path: Path) -> str:
    """เส้นทางแบบสั้นสำหรับพิมพ์ให้คนอ่าน (relative กับรากโปรเจกต์ถ้าอยู่ในโปรเจกต์)"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def draft_caption(path: Path) -> str:
    """ดึงแคปชันจากหัวข้อ '## แคปชัน ...' ของไฟล์ร่างในเครื่อง"""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^## แคปชัน[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        raise SystemExit(
            f"ไม่พบหัวข้อ '## แคปชัน' ใน {_display_path(path)}\n"
            "ไฟล์ร่างต้องมีหัวข้อ '## แคปชัน (คัดลอกวางได้เลย)' แล้วตามด้วยข้อความโพสต์"
        )
    return match.group(1).strip()


def validate_caption(caption: str, source: str) -> str:
    """ด่านสุดท้ายก่อนสร้างร่าง — กันแคปชันว่าง ยาวเกิน หรือสัญญารายได้"""
    if not caption.strip():
        raise SystemExit(f"แคปชันว่าง — ตรวจหัวข้อ '## แคปชัน' ใน {source}")
    if len(caption) > MAX_DRAFT_CHARS:
        raise SystemExit(
            f"แคปชันยาว {len(caption)} ตัวอักษร เกินเพดาน {MAX_DRAFT_CHARS} ของโปรเจกต์ — ตัดให้สั้นลงใน {source}"
        )
    banned = [word for word in BANNED_CLAIMS if word in caption]
    if banned:
        raise SystemExit(
            "พบคำที่ผิดนโยบายโฆษณา: " + ", ".join(banned) + f" — แก้ {source} ก่อนสร้างร่าง"
        )
    return caption


def resolve_draft_file(raw: str) -> Path:
    """หาไฟล์ร่างจาก path ที่ผู้ใช้พิมพ์ (รองรับชื่อไฟล์เดี่ยวใน content/drafts/)"""
    candidate = Path(raw).expanduser()
    options = (
        [candidate]
        if candidate.is_absolute()
        else [Path.cwd() / candidate, ROOT / candidate, DRAFT_DIR / candidate]
    )
    for option in options:
        if option.is_file():
            return option.resolve()
    available = sorted(DRAFT_DIR.glob("*.md")) if DRAFT_DIR.exists() else []
    listing = "\n".join(f"  - {_display_path(p)}" for p in available) or "  (ยังไม่มีไฟล์ร่าง)"
    raise SystemExit(f"ไม่พบไฟล์ร่าง {raw}\nไฟล์ที่มี:\n{listing}")


def _print_draft_usage() -> None:
    print("ต้องเลือกว่าจะสร้างร่างจากไฟล์ในเครื่องหรือจากวันไหนในแผน", file=sys.stderr)
    print(
        "  python3 scripts/fb_scheduler.py --draft --file content/drafts/<ชื่อไฟล์>.md --live",
        file=sys.stderr,
    )
    print("  python3 scripts/fb_scheduler.py --draft --day 5 --live", file=sys.stderr)
    available = sorted(DRAFT_DIR.glob("*.md")) if DRAFT_DIR.exists() else []
    if available:
        print("\nไฟล์ร่างในเครื่อง:", file=sys.stderr)
        for path in available:
            print(f"  - {_display_path(path)}", file=sys.stderr)
    else:
        print(f"\nยังไม่มีไฟล์ร่างใน {_display_path(DRAFT_DIR)}", file=sys.stderr)


# --------------------------------------------------------------------------- commands


def cmd_exchange(env: dict, args) -> None:
    require(env, "FB_APP_ID", "FB_APP_SECRET")
    version = env.get("FB_GRAPH_VERSION", DEFAULT_GRAPH_VERSION)
    print("1) แลก short-lived token เป็น long-lived user token (~60 วัน)")
    result = graph_request(
        version,
        "oauth/access_token",
        {
            "grant_type": "fb_exchange_token",
            "client_id": env["FB_APP_ID"],
            "client_secret": env["FB_APP_SECRET"],
            "fb_exchange_token": args.exchange_token,
        },
    )
    long_token = result.get("access_token")
    if not long_token:
        raise SystemExit(f"ไม่ได้ access_token กลับมา: {result}")

    print("2) ดึงรายการเพจและ Page access token ที่โทเคนนี้เข้าถึง")
    accounts = graph_request(
        version,
        "me/accounts",
        {"fields": "id,name,access_token,tasks", "access_token": long_token},
    ).get("data", [])
    if not accounts:
        raise SystemExit(
            "ไม่พบเพจที่โทเคนนี้จัดการได้\n"
            "- ตรวจว่าบัญชีที่ล็อกอินเป็นแอดมินเพจ\n"
            "- ตรวจว่าได้ติ๊กสิทธิ์ pages_show_list และ pages_manage_posts ตอนอนุญาตแอป"
        )

    print("\nเขียนค่าต่อไปนี้ลงไฟล์ .env (ห้ามคอมมิตไฟล์นี้):\n")
    print(f"FB_PAGE_ACCESS_TOKEN={long_token}")
    print("# --- เลือกเพจด้านล่างนี้ แล้วคัดลอก id กับ access_token ลง .env ---")
    for page in accounts:
        tasks = ", ".join(page.get("tasks", [])) or "-"
        print(f"\n# เพจ: {page.get('name')}  (tasks: {tasks})")
        print(f"FB_PAGE_ID={page.get('id')}")
        print(f"FB_PAGE_ACCESS_TOKEN={page.get('access_token')}")
    print("\nหมายเหตุ: ถ้าไม่มี tasks ที่มี CREATE_CONTENT/MANAGE ให้ขอสิทธิ์จากแอดมินเพจก่อน")


def cmd_check(env: dict, args) -> None:
    require(env, "FB_PAGE_ID", "FB_PAGE_ACCESS_TOKEN")
    version = env.get("FB_GRAPH_VERSION", DEFAULT_GRAPH_VERSION)
    page_id = env["FB_PAGE_ID"]
    token = env["FB_PAGE_ACCESS_TOKEN"]

    info = graph_request(
        version,
        page_id,
        {"fields": "id,name,category,link,fan_count", "access_token": token},
    )
    print("เพจที่เชื่อมต่อสำเร็จ:")
    for key in ("id", "name", "category", "link", "fan_count"):
        if info.get(key) is not None:
            print(f"  {key:10}: {info[key]}")

    plan_path = PLAN
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        rows = facebook_rows(plan)
        state = load_state()
        done = len(state["published"])
        print(f"\nแผนที่สร้างไว้: {len(rows)} โพสต์ Facebook")
        print(f"โพสต์แล้ว {done} ยังไม่โพสต์ {len(rows) - done}")
        drafts = state.get("drafts", {})
        if drafts:
            print(f"สร้างร่าง (unpublished) ไว้ {len(drafts)} รายการ — ยังไม่ขึ้นเพจ")
            print("ตรวจสถานะร่างกับ Facebook: python3 scripts/fb_scheduler.py --verify-drafts")


def _select_rows(rows: list[dict], args) -> list[dict]:
    if args.day is not None:
        selected = [r for r in rows if r["day"] == args.day]
        if not selected:
            raise SystemExit(f"ไม่พบวันที่ {args.day} ในแผน")
        return selected
    if args.today:
        today = date.today().isoformat()
        selected = [r for r in rows if r["date"] == today]
        if not selected:
            print(f"วันนี้ ({today}) ไม่มีโพสต์ในแผน — อาจยังไม่เริ่มแคมเปญ หรือเลยกำหนดแล้ว")
        return selected
    lo = args.from_day or 1
    hi = args.to_day or 30
    return [r for r in rows if lo <= r["day"] <= hi]


def _render(row: dict) -> None:
    when = parse_slot(row)
    print(f"\n--- วันที่ {row['day']} · {row['date']} ({row['weekday']}) {row['post_time']} · {row['format']} ---")
    print(f"หัวข้อ: {row['title']}")
    print(f"กำหนดโพสต์: {when.isoformat()}")
    print("ข้อความโพสต์:")
    print(row["caption"])


def _publish(env: dict, version: str, row: dict, state: dict) -> None:
    page_id = env["FB_PAGE_ID"]
    token = env["FB_PAGE_ACCESS_TOKEN"]
    result = graph_request(
        version,
        f"{page_id}/feed",
        {"message": row["caption"], "access_token": token},
        method="POST",
    )
    post_id = result.get("id", "")
    state["published"][str(row["day"])] = {
        "post_id": post_id,
        "at": datetime.now(BANGKOK).isoformat(timespec="seconds"),
        "date": row["date"],
    }
    state["history"].append({"action": "publish", "day": row["day"], "post_id": post_id})
    save_state(state)
    print(f"    ✅ โพสต์แล้ว: https://facebook.com/{post_id}")


def _schedule(env: dict, version: str, row: dict, state: dict) -> None:
    page_id = env["FB_PAGE_ID"]
    token = env["FB_PAGE_ACCESS_TOKEN"]
    when = parse_slot(row)
    window = schedule_window(row)
    if window == "too_far":
        print(f"    ⏭  ข้ามวันที่ {row['day']}: เกิน 30 วันล่วงหน้า ซึ่ง Meta ไม่รับ")
        return
    if window == "past":
        print(f"    ⚠️  วันที่ {row['day']} เลยเวลาแล้ว — เปลี่ยนเป็นโพสต์ทันที")
        _publish(env, version, row, state)
        return

    result = graph_request(
        version,
        f"{page_id}/feed",
        {
            "message": row["caption"],
            "published": "false",
            "scheduled_publish_time": int(when.timestamp()),
            "access_token": token,
        },
        method="POST",
    )
    post_id = result.get("id", "")
    state["scheduled"][str(row["day"])] = {
        "post_id": post_id,
        "scheduled_for": when.isoformat(timespec="seconds"),
    }
    state["history"].append({"action": "schedule", "day": row["day"], "post_id": post_id})
    save_state(state)
    print(f"    🗓  ตั้งเวลาไว้ {when.strftime('%Y-%m-%d %H:%M')} (โพสต์ id {post_id})")


def _render_draft(target: dict) -> None:
    caption = target["caption"]
    print(f"\n--- โพสต์ร่างจาก {target['source']} ---")
    row = target.get("row")
    if row:
        print(f"วันที่ {row['day']} · {row['date']} ({row['weekday']}) {row['post_time']} · {row['format']}")
    print(f"ความยาวแคปชัน: {len(caption)} ตัวอักษร")
    print("โหมด: unpublished — published=false + unpublished_content_type=DRAFT (ไม่ขึ้นเพจ)")
    print("ข้อความร่าง:")
    print(caption)


def _create_draft(env: dict, version: str, target: dict, state: dict) -> bool:
    """สร้างโพสต์ unpublished (ร่าง) จากแคปชัน แล้วอ่านกลับมาตรวจว่าไม่ขึ้นเพจจริง

    คืนค่า True เมื่อ Facebook สร้างโพสต์ให้จริง (มี post id กลับมา)
    """
    page_id = env["FB_PAGE_ID"]
    token = env["FB_PAGE_ACCESS_TOKEN"]
    caption = target["caption"]
    result = graph_request(
        version,
        f"{page_id}/feed",
        {
            "message": caption,
            "published": "false",
            "unpublished_content_type": "DRAFT",
            "access_token": token,
        },
        method="POST",
    )
    post_id = result.get("id", "")
    if not post_id:
        print(f"    ⚠️  Facebook ไม่ได้คืน post id: {result}")
        return False

    entry = {
        "post_id": post_id,
        "source": target["source"],
        "chars": len(caption),
        "created_at": datetime.now(BANGKOK).isoformat(timespec="seconds"),
        "is_published": None,
    }
    if target.get("row"):
        entry["date"] = target["row"]["date"]
    if target.get("day") is not None:
        entry["day"] = target["day"]
    state.setdefault("drafts", {})[target["key"]] = entry
    state["history"].append({"action": "draft", "key": target["key"], "post_id": post_id})
    save_state(state)  # บันทึกก่อนอ่านกลับ — ร่างที่สร้างสำเร็จแล้วต้องไม่หลุดจากการนับ
    print(f"    📝 สร้างโพสต์ร่างแล้ว: id {post_id}")

    try:
        check = graph_request(
            version,
            post_id,
            {"fields": "is_published,created_time", "access_token": token},
        )
    except SystemExit:
        print("    ⚠️  อ่านกลับมาตรวจ is_published ไม่ได้ — เปิดตรวจใน Meta Business Suite อีกครั้ง")
    else:
        entry["is_published"] = check.get("is_published")
        save_state(state)
        if entry["is_published"] is True:
            print(
                "    ❗ is_published=true — ร่างนี้ขึ้นเพจจริงแล้ว!\n"
                "       ลบหรือซ่อนโพสต์นี้ใน Facebook ก่อน แล้วตรวจสิทธิ์ของโทเคนและค่าที่ส่งไป"
            )
        else:
            print("    ✅ ตรวจแล้ว: is_published=false — ยังไม่ขึ้นเพจ")

    print("    ตรวจใน Facebook: Meta Business Suite → Content → Drafts")
    print("       https://business.facebook.com/latest/posts/drafts")
    if entry["is_published"] is not True:
        print("    ระบบจะไม่กดเผยแพร่ให้ — คุณกดเองใน Facebook หลังตรวจแล้ว")
    return True


def cmd_draft(env: dict, args) -> None:
    """โหมด --draft: สร้างโพสต์ unpublished จากไฟล์ร่างในเครื่องหรือแคปชันในแผน"""
    state = load_state()
    drafts = state.setdefault("drafts", {})
    version = env.get("FB_GRAPH_VERSION", DEFAULT_GRAPH_VERSION)

    if args.file:
        targets = []
        for raw in args.file:
            path = resolve_draft_file(raw)
            caption = validate_caption(draft_caption(path), _display_path(path))
            targets.append(
                {
                    "key": f"file:{path.stem}",
                    "caption": caption,
                    "source": _display_path(path),
                }
            )
    else:
        if not (args.day or args.today or args.from_day or args.to_day):
            _print_draft_usage()
            raise SystemExit(2)
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        rows = _select_rows(facebook_rows(plan), args)
        if not rows:
            return
        targets = [
            {
                "key": f"day:{row['day']}",
                "caption": validate_caption(row["caption"], f"content/plan.json วันที่ {row['day']}"),
                "source": f"content/plan.json วันที่ {row['day']}",
                "day": row["day"],
                "row": row,
            }
            for row in rows
        ]

    live = args.live
    if live:
        require(env, "FB_PAGE_ID", "FB_PAGE_ACCESS_TOKEN")
    else:
        print("โหมดทดลอง (dry-run) — เติม --live เพื่อสร้างโพสต์ร่างใน Facebook (จะไม่ขึ้นเพจ)")

    created = skipped = 0
    for target in targets:
        saved = drafts.get(target["key"])
        if saved and not args.force:
            print(
                f"\n⏭  ข้าม {target['key']}: สร้างร่างไว้แล้ว (id {saved.get('post_id')}) "
                "— ใช้ --force ถ้าต้องการสร้างใหม่"
            )
            skipped += 1
            continue
        _render_draft(target)
        if not live:
            continue
        if _create_draft(env, version, target, state):
            created += 1
        time.sleep(1)  # be gentle with Page rate limits

    if live:
        print(f"\nสร้างโพสต์ร่าง {created} รายการ · ข้าม {skipped} รายการ")


def _sorted_drafts(drafts: dict) -> list[tuple[str, dict]]:
    return sorted(drafts.items(), key=lambda item: (str(item[1].get("created_at") or ""), item[0]))


def cmd_list_drafts(env: dict, args) -> None:
    """แสดงโพสต์ร่างที่บันทึกไว้ใน state (อ่านจากไฟล์เท่านั้น ไม่ยิง API)"""
    drafts = load_state().get("drafts") or {}
    if not drafts:
        print("ยังไม่มีโพสต์ร่างที่บันทึกไว้ — สร้างด้วย --draft --file ... --live ก่อน")
        return

    print(f"โพสต์ร่างที่บันทึกไว้ {len(drafts)} รายการ (จาก state/fb_state.json)")
    for key, entry in _sorted_drafts(drafts):
        print(f"\n  {key}")
        print(f"    post id   : {entry.get('post_id') or '-'}")
        if entry.get("source"):
            print(f"    ที่มา      : {entry['source']}")
        if entry.get("created_at"):
            print(f"    สร้างเมื่อ : {entry['created_at']}")
        if entry.get("checked_at"):
            label = DRAFT_STATUS_LABELS.get(str(entry.get("status")), "ไม่ทราบสถานะ")
            print(f"    ตรวจล่าสุด : {entry['checked_at']} → {label}")
        else:
            print("    ตรวจล่าสุด : ยังไม่เคยตรวจ — ใช้ --verify-drafts")
        if entry.get("chars") is not None:
            print(f"    ความยาว  : {entry['chars']} ตัวอักษร")

    print("\nตรวจสถานะกับ Facebook: python3 scripts/fb_scheduler.py --verify-drafts")


def cmd_verify_drafts(env: dict, args) -> int:
    """ตรวจสถานะร่างทุกรายการกับ Graph API: ยังเป็นร่าง / เผยแพร่แล้ว / ไม่พบ

    เป็นการอ่านอย่างเดียวบน Facebook แต่จะอัปเดต state ในเครื่อง (status, checked_at,
    status_changed_at) และถ้าร่างที่ผูกกับวันถูกเผยแพร่แล้ว จะบันทึกใน published
    เพื่อกันโพสต์ซ้ำ สถานะที่เปลี่ยนจากครั้งก่อนจะถูกเตือนและสรุปเป็น 'ร่างที่ต้องตรวจสอบ'
    (daily_run.sh เรียกคำสั่งนี้ทุกวันและเก็บผลลง state/logs/)
    คืนค่า 1 ถ้ามีรายการที่ตรวจไม่ได้ (ข้อผิดพลาดจริง) — 'ไม่พบ' ถือว่าตรวจได้
    """
    state = load_state()
    drafts = state.setdefault("drafts", {})
    if not drafts:
        print("ยังไม่มีโพสต์ร่างที่บันทึกไว้ — ไม่มีอะไรต้องตรวจ")
        return 0
    require(env, "FB_PAGE_ID", "FB_PAGE_ACCESS_TOKEN")

    version = env.get("FB_GRAPH_VERSION", DEFAULT_GRAPH_VERSION)
    token = env["FB_PAGE_ACCESS_TOKEN"]
    counts = {"draft": 0, "published": 0, "missing": 0, "error": 0}
    changes: list[tuple[str, str, str]] = []
    alerts: list[tuple[str, str]] = []
    print(f"ตรวจสถานะร่าง {len(drafts)} รายการกับ Graph API (อ่านอย่างเดียวบน Facebook)\n")

    for key, entry in _sorted_drafts(drafts):
        post_id = entry.get("post_id")
        previous = entry.get("status")
        label = f"{key} (id {post_id})" if post_id else key
        if not post_id:
            status = "error"
            print(f"  ❌ {label}: ไม่มี post id ใน state — ตรวจไม่ได้")
        else:
            try:
                data = graph_call(
                    version,
                    str(post_id),
                    {"fields": "is_published,created_time", "access_token": token},
                )
            except GraphError as exc:
                if exc.not_found:
                    status = "missing"
                    print(f"  ⚠️  {label}: ไม่พบใน Graph API — อาจถูกลบ หรือโทเคนไม่มีสิทธิ์อ่าน")
                else:
                    status = "error"
                    hint = "โทเคนใช้ไม่ได้/หมดอายุ" if exc.code == 190 else "ตรวจไม่ได้"
                    print(f"  ❌ {label}: {hint} — {exc.message}")
            else:
                is_published = data.get("is_published")
                if is_published is True:
                    status = "published"
                    print(f"  ✅ {label}: เผยแพร่แล้ว (is_published=true)")
                elif is_published is False:
                    status = "draft"
                    print(f"  ✅ {label}: ยังเป็นร่าง (unpublished)")
                else:
                    status = "error"
                    print(f"  ❌ {label}: Graph API ไม่ได้คืนค่า is_published")

        entry["status"] = status
        entry["checked_at"] = datetime.now(BANGKOK).isoformat(timespec="seconds")
        if previous and previous != status:
            entry["status_changed_at"] = entry["checked_at"]
            changes.append((key, previous, status))
            print(
                f"    🔔 เปลี่ยนสถานะ: {DRAFT_STATUS_LABELS.get(previous, previous)} "
                f"→ {DRAFT_STATUS_LABELS.get(status, status)}"
            )
        if status in ("published", "missing") and previous != status:
            alerts.append((key, status))
        if status in ("draft", "published"):
            entry["is_published"] = status == "published"

        if status == "published" and entry.get("day") is not None:
            day_key = str(entry["day"])
            if day_key not in state.setdefault("published", {}):
                state["published"][day_key] = {
                    "post_id": post_id,
                    "at": entry["checked_at"],
                    "date": entry.get("date", ""),
                    "source": "verify-drafts",
                }
                print(f"    📌 บันทึกว่าวันที่ {day_key} ขึ้นเพจแล้ว เพื่อกันโพสต์ซ้ำ")
        counts[status] += 1

    save_state(state)
    print(
        f"\nสรุป: ยังเป็นร่าง {counts['draft']} · เผยแพร่แล้ว {counts['published']} · "
        f"ไม่พบ {counts['missing']} · ตรวจไม่ได้ {counts['error']}"
    )
    if changes:
        print(f"เปลี่ยนสถานะจากการตรวจครั้งก่อน {len(changes)} รายการ")
    if alerts:
        print("\n🔔 ร่างที่ต้องตรวจสอบ:")
        for key, status in alerts:
            print(f"  - {key}: {DRAFT_STATUS_LABELS[status]}")
    if counts["missing"]:
        print("หมายเหตุ: 'ไม่พบ' อาจหมายถึงถูกลบไปแล้ว หรือโทเคนไม่มีสิทธิ์อ่านโพสต์ unpublished")
    return 1 if counts["error"] else 0


def cmd_run(env: dict, args) -> None:
    if args.draft:
        cmd_draft(env, args)
        return
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    rows = _select_rows(facebook_rows(plan), args)
    state = load_state()
    version = env.get("FB_GRAPH_VERSION", DEFAULT_GRAPH_VERSION)

    if not rows:
        return
    # ตั้งเวลาซ้ำวันเดิมจะสร้างโพสต์ซ้ำอีกใบในเพจ จึงนับวันที่ตั้งเวลาไว้แล้วว่าทำแล้วด้วย
    already = set(state["published"])
    if args.schedule:
        already |= set(state["scheduled"])
    todo = [r for r in rows if str(r["day"]) not in already]
    skipped = len(rows) - len(todo)
    label = "โพสต์หรือตั้งเวลาแล้ว" if args.schedule else "ทำแล้ว"
    print(f"เลือกไว้ {len(rows)} วัน · ต้องทำ {len(todo)} · ข้ามเพราะ{label} {skipped}")

    live = args.live
    if live:
        require(env, "FB_PAGE_ID", "FB_PAGE_ACCESS_TOKEN")
    else:
        print("โหมดทดลอง (dry-run) — เติม --live เพื่อยิงเข้า Graph API จริง")

    for row in todo:
        _render(row)
        if not live:
            continue
        if args.schedule:
            _schedule(env, version, row, state)
        else:
            _publish(env, version, row, state)
        time.sleep(1)  # be gentle with Page rate limits


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "โพสต์/ตั้งเวลาโพสต์ Facebook Page จาก content/plan.json "
            "หรือสร้างโพสต์ร่าง unpublished จาก content/drafts/"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--check", action="store_true", help="ตรวจเพจและโทเคนที่เชื่อมต่ออยู่")
    parser.add_argument("--exchange-token", metavar="SHORT_TOKEN", help="แลกเป็น long-lived token + ดู Page token")
    parser.add_argument("--day", type=int, help="ทำเฉพาะวันที่กำหนด (1-30)")
    parser.add_argument("--today", action="store_true", help="ทำเฉพาะโพสต์ของวันนี้")
    parser.add_argument("--from-day", type=int, help="เริ่มตั้งแต่วันที่")
    parser.add_argument("--to-day", type=int, help="ถึงวันที่")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--schedule", action="store_true", help="ตั้งเวลาโพสต์แทนการโพสต์ทันที")
    mode.add_argument(
        "--draft",
        action="store_true",
        help="สร้างโพสต์ unpublished (ร่าง) จากไฟล์ในเครื่องหรือแคปชันในแผน — ไม่ขึ้นเพจ",
    )
    parser.add_argument(
        "--file",
        action="append",
        metavar="PATH",
        help="ไฟล์ร่าง .md ที่มีหัวข้อ '## แคปชัน' (ใช้กับ --draft, ระบุซ้ำได้)",
    )
    parser.add_argument("--force", action="store_true", help="สร้างร่างซ้ำได้ แม้ state จะบันทึกไว้แล้ว")
    parser.add_argument("--list-drafts", action="store_true", help="แสดงโพสต์ร่างที่บันทึกไว้ (ไม่ยิง API)")
    parser.add_argument(
        "--verify-drafts",
        action="store_true",
        help="ตรวจสถานะร่างกับ Graph API: ยังเป็นร่าง / เผยแพร่แล้ว / ถูกลบ",
    )
    parser.add_argument("--live", action="store_true", help="ยิงเข้า Graph API จริง (ไม่มี = dry-run)")
    args = parser.parse_args()

    if args.file and not args.draft:
        parser.error("--file ใช้ร่วมกับ --draft เท่านั้น")
    if args.force and not args.draft:
        parser.error("--force ใช้ร่วมกับ --draft เท่านั้น")
    if args.draft and args.file and (args.day or args.today or args.from_day or args.to_day):
        parser.error("--file ใช้ร่วมกับ --day/--today/--from-day/--to-day ไม่ได้ (เลือกอย่างใดอย่างหนึ่ง)")

    env = load_env()

    if args.exchange_token:
        cmd_exchange(env, args)
        return
    if args.check:
        cmd_check(env, args)
        return
    if args.list_drafts:
        cmd_list_drafts(env, args)
        return
    if args.verify_drafts:
        raise SystemExit(cmd_verify_drafts(env, args))

    # --draft --file อ่านจากไฟล์ในเครื่องล้วน ๆ จึงไม่ต้องมี content/plan.json
    if args.draft and args.file:
        cmd_draft(env, args)
        return

    if not PLAN.exists():
        raise SystemExit("ยังไม่มี content/plan.json — รัน: python3 scripts/generate_plan.py")
    cmd_run(env, args)


if __name__ == "__main__":
    main()
