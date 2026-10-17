#!/usr/bin/env python3
"""ทดสอบโหมด --draft ของ scripts/fb_scheduler.py (สร้างโพสต์ unpublished จากไฟล์ในเครื่อง)

ครอบคลุม: การดึงแคปชันจากไฟล์ร่าง, ด่านกันคำสัญญารายได้/แคปชันยาว, dry-run ที่ไม่แตะ API,
การยิง POST จริงไปยัง Graph API จำลอง (ตรวจพารามิเตอร์ published=false + DRAFT),
การอ่านกลับมาตรวจ is_published, การกันสร้างร่างซ้ำ, --force, และการเลือกวันจากแผน

    python3 tests/fb_draft_test.py

ไม่มีการเชื่อมต่อ Facebook จริง: ใช้เซิร์ฟเวอร์ HTTP ในเครื่องแทน graph.facebook.com
"""

from __future__ import annotations

import argparse
import contextlib
import http.server
import importlib.util
import io
import json
import sys
import tempfile
import threading
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fb_scheduler as fb  # noqa: E402

DRAFT = ROOT / "content" / "drafts" / "fb-001-page-intro.md"
PLAN = ROOT / "content" / "plan.json"
SCHEDULER = ROOT / "scripts" / "fb_scheduler.py"

failures: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {extra}" if extra else ""))
    if not ok:
        failures.append(name)


def capture(func, *args, **kwargs) -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        func(*args, **kwargs)
    return buffer.getvalue()


def capture_result(func, *args, **kwargs):
    """เหมือน capture แต่คืนค่าที่ฟังก์ชันส่งกลับมาด้วย"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        value = func(*args, **kwargs)
    return value, buffer.getvalue()


def expect_exit(func, *args) -> str:
    """เรียกฟังก์ชันที่ต้องล้ม แล้วคืนข้อความ error (SystemExit)"""
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            func(*args)
    except SystemExit as exc:
        return str(exc)
    return ""


def make_args(**kwargs) -> argparse.Namespace:
    values = {
        "file": None,
        "day": None,
        "today": False,
        "from_day": None,
        "to_day": None,
        "live": False,
        "force": False,
    }
    values.update(kwargs)
    return argparse.Namespace(**values)


def run_cli(*argv: str) -> tuple[int, str, str]:
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(SCHEDULER), *argv],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode, proc.stdout, proc.stderr


class FakeGraph(http.server.BaseHTTPRequestHandler):
    """Graph API จำลอง — เก็บคำขอที่ได้รับแล้วตอบกลับแบบเดียวกับ Meta

    objects: post id → payload ที่จะตอบเมื่อ GET (ค่าเริ่มต้นคือ is_published=false)
    errors:  post id → (HTTP status, payload error) สำหรับจำลองโพสต์ที่ถูกลบ/โทเคนเสีย
    """

    posts: list[tuple[str, dict]] = []
    gets: list[str] = []
    objects: dict[str, dict] = {}
    errors: dict[str, tuple[int, dict]] = {}

    def do_POST(self) -> None:  # noqa: N802 (ชื่อที่ BaseHTTPRequestHandler กำหนด)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8")
        type(self).posts.append((self.path, urllib.parse.parse_qs(body)))
        self._json({"id": "777_888"})

    def do_GET(self) -> None:  # noqa: N802
        type(self).gets.append(self.path)
        post_id = self.path.split("?", 1)[0].strip("/").split("/")[-1]
        if post_id in type(self).errors:
            code, payload = type(self).errors[post_id]
            self._json(payload, code)
            return
        payload = type(self).objects.get(post_id)
        if payload is None:
            payload = {"id": post_id, "is_published": False, "created_time": "2026-10-17T12:00:00+0000"}
        self._json(payload)

    def _json(self, payload: dict, code: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args) -> None:  # ปิด log ของเซิร์ฟเวอร์ทดสอบ
        pass


def phase_caption() -> None:
    """การดึงแคปชันจากไฟล์ร่าง + ด่านตรวจ"""
    caption = fb.draft_caption(DRAFT)
    check("ดึงแคปชันจากหัวข้อ '## แคปชัน' ได้", bool(caption), f"{len(caption)} ตัวอักษร")
    check("แคปชันขึ้นต้นด้วยประโยคเปิดของไฟล์ร่าง", caption.startswith("ถ้าคุณเคยเริ่มขายของออนไลน์"))
    check("ไม่ติดหัวข้อถัดไปมาในแคปชัน", "## คอมเมนต์แรก" not in caption and "- [ ]" not in caption)
    check("ไม่ติดตาราง metadata มาในแคปชัน", "| หัวข้อ |" not in caption and "เพจเป้าหมาย" not in caption)
    check("แคปชันลงท้ายด้วยลายเซ็นแบรนด์", caption.rstrip().endswith("Kopwang | ระบบสร้างรายได้ใน 30 วัน"))

    check(
        "คำต้องห้ามชุดเดียวกับด่านตรวจคอนเทนต์",
        set(_content_contract().BANNED) <= set(fb.BANNED_CLAIMS),
        f"{sorted(set(_content_contract().BANNED) - set(fb.BANNED_CLAIMS))}",
    )

    tmp = Path(tempfile.mkdtemp()) / "no-heading.md"
    tmp.write_text("# ร่างที่ไม่มีหัวข้อแคปชัน\n\nข้อความอะไรก็ได้\n", encoding="utf-8")
    message = expect_exit(fb.draft_caption, tmp)
    check("ไฟล์ที่ไม่มีหัวข้อแคปชันถูกปฏิเสธพร้อมบอกสาเหตุ", "ไม่พบหัวข้อ '## แคปชัน'" in message, message[:70])

    check(
        "ปฏิเสธแคปชันที่มีคำสัญญารายได้",
        "ผิดนโยบาย" in expect_exit(fb.validate_caption, "ลงทุนน้อย รวยเร็วแน่นอน", "test"),
    )
    check(
        "ปฏิเสธแคปชันว่าง",
        "แคปชันว่าง" in expect_exit(fb.validate_caption, "   ", "test"),
    )
    check(
        f"ปฏิเสธแคปชันยาวเกิน {fb.MAX_DRAFT_CHARS} ตัวอักษร",
        "เกินเพดาน" in expect_exit(fb.validate_caption, "ก" * (fb.MAX_DRAFT_CHARS + 1), "test"),
    )
    check("ปล่อยแคปชันปกติผ่านด่าน", fb.validate_caption(caption, "test") == caption)

    check("หาไฟล์ร่างจากชื่อไฟล์เดี่ยวได้", fb.resolve_draft_file(DRAFT.name) == DRAFT.resolve())
    check(
        "ไฟล์ที่ไม่มีอยู่จริงถูกปฏิเสธพร้อมรายการไฟล์ที่มี",
        "ไม่พบไฟล์ร่าง" in expect_exit(fb.resolve_draft_file, "ไม่มีไฟล์นี้.md"),
    )


def _content_contract():
    spec = importlib.util.spec_from_file_location("content_draft_test", ROOT / "tests" / "content_draft_test.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def phase_http(server_url: str, original_graph_url) -> None:
    """ยิงผ่าน graph_request จริงไปยัง Graph API จำลอง แล้วตรวจพารามิเตอร์และ state"""
    fb.graph_url = lambda version, path: f"{server_url}/{path.lstrip('/')}"
    original_state = fb.STATE_FILE
    fb.STATE_FILE = Path(tempfile.mkdtemp()) / "fb_state.json"
    env = {"FB_PAGE_ID": "PAGE", "FB_PAGE_ACCESS_TOKEN": "TOKEN", "FB_GRAPH_VERSION": "v26.0"}
    caption = fb.draft_caption(DRAFT)
    try:
        FakeGraph.posts.clear()
        FakeGraph.gets.clear()
        out = capture(fb.cmd_draft, env, make_args(file=[str(DRAFT)], live=True))

        check("โหมด --live สร้างร่าง 1 รายการ", "สร้างโพสต์ร่าง 1 รายการ" in out, out.strip().splitlines()[-1])
        check("ยิง POST ไปที่ /PAGE/feed", len(FakeGraph.posts) == 1 and FakeGraph.posts[0][0].endswith("/PAGE/feed"),
              FakeGraph.posts[0][0] if FakeGraph.posts else "ไม่มีการยิง POST")
        params = FakeGraph.posts[0][1] if FakeGraph.posts else {}
        check("ส่ง published=false", params.get("published") == ["false"], str(params.get("published")))
        check("ส่ง unpublished_content_type=DRAFT", params.get("unpublished_content_type") == ["DRAFT"],
              str(params.get("unpublished_content_type")))
        check("ส่งข้อความร่างครบทุกตัวอักษร", params.get("message") == [caption], f"{len(params.get('message', [''])[0])} ตัวอักษร")
        check("ใช้ Page access token จาก .env", params.get("access_token") == ["TOKEN"])
        check(
            "ไม่มีการส่ง scheduled_publish_time (ร่างไม่ได้ถูกตั้งเวลา)",
            "scheduled_publish_time" not in params,
        )

        check("อ่านกลับมาตรวจ is_published", len(FakeGraph.gets) == 1 and "is_published" in FakeGraph.gets[0],
              FakeGraph.gets[0] if FakeGraph.gets else "ไม่มีการยิง GET")
        check("รายงานว่ายังไม่ขึ้นเพจ", "is_published=false" in out and "ยังไม่ขึ้นเพจ" in out)
        check("บอกที่ตรวจร่างใน Facebook", "business.facebook.com/latest/posts/drafts" in out)
        check("ยืนยันว่าไม่กดเผยแพร่ให้", "ไม่กดเผยแพร่ให้" in out)

        state = fb.load_state()
        entry = state.get("drafts", {}).get("file:fb-001-page-intro", {})
        check("บันทึก post id ใน state", entry.get("post_id") == "777_888", str(entry.get("post_id")))
        check("บันทึก is_published=false ลง state", entry.get("is_published") is False, repr(entry.get("is_published")))
        check("บันทึกประวัติว่าเป็น action=draft", state["history"][-1].get("action") == "draft",
              str(state["history"][-1]))
        check("ไม่ได้บันทึกว่าโพสต์ขึ้นเพจแล้ว", state.get("published") == {}, str(state.get("published")))

        # รันซ้ำ: ต้องไม่สร้างร่างซ้ำ
        FakeGraph.posts.clear()
        FakeGraph.gets.clear()
        out = capture(fb.cmd_draft, env, make_args(file=[str(DRAFT)], live=True))
        check("รันซ้ำไม่ยิง POST ใหม่", FakeGraph.posts == [], f"{len(FakeGraph.posts)} คำขอ")
        check("แจ้งว่าข้ามเพราะสร้างร่างไว้แล้ว", "ข้าม" in out and "777_888" in out, out.strip()[:80])
        check("state ยังมีร่างรายการเดียว", len(fb.load_state()["drafts"]) == 1)

        # --force: สร้างใหม่ได้
        FakeGraph.posts.clear()
        capture(fb.cmd_draft, env, make_args(file=[str(DRAFT)], live=True, force=True))
        check("--force สร้างร่างใหม่ได้", len(FakeGraph.posts) == 1, f"{len(FakeGraph.posts)} คำขอ")
        check("ประวัติมี action=draft สองครั้ง", len(fb.load_state()["history"]) == 2)

        # เลือกวันจากแผน
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        day1 = next(r for r in plan["rows"] if r["platform"] == "facebook" and r["day"] == 1)
        FakeGraph.posts.clear()
        out = capture(fb.cmd_draft, env, make_args(day=1, live=True))
        check(
            "สร้างร่างจากแคปชันในแผนได้ (--day 1)",
            len(FakeGraph.posts) == 1
            and FakeGraph.posts[0][1].get("message") == [day1["caption"]],
            out.strip().splitlines()[-1],
        )
        check(
            "บันทึกด้วย key day:1",
            fb.load_state().get("drafts", {}).get("day:1", {}).get("post_id") == "777_888",
            str(list(fb.load_state().get("drafts", {}))),
        )
    finally:
        fb.graph_url = original_graph_url
        fb.STATE_FILE = original_state


def phase_unexpected_publish(server_url: str, original_graph_url) -> None:
    """ถ้า Facebook ตอบ is_published=true ต้องเตือนดัง ๆ ไม่ใช่ปล่อยผ่าน"""
    fb.graph_url = lambda version, path: f"{server_url}/{path.lstrip('/')}"
    original_state = fb.STATE_FILE
    fb.STATE_FILE = Path(tempfile.mkdtemp()) / "fb_state.json"
    env = {"FB_PAGE_ID": "PAGE", "FB_PAGE_ACCESS_TOKEN": "TOKEN", "FB_GRAPH_VERSION": "v26.0"}
    original_do_get = FakeGraph.do_GET

    def published_get(self) -> None:
        type(self).gets.append(self.path)
        self._json({"id": "777_888", "is_published": True})

    FakeGraph.do_GET = published_get
    try:
        out = capture(fb.cmd_draft, env, make_args(file=[str(DRAFT)], live=True))
        check("เตือนเมื่อร่างกลายเป็นโพสต์ที่ขึ้นเพจจริง", "is_published=true" in out and "ลบหรือซ่อน" in out)
        check("state บันทึก is_published=true ตามที่ Facebook ตอบ", fb.load_state()["drafts"]["file:fb-001-page-intro"]["is_published"] is True)
    finally:
        FakeGraph.do_GET = original_do_get
        fb.graph_url = original_graph_url
        fb.STATE_FILE = original_state


def phase_list_and_verify(server_url: str, original_graph_url) -> None:
    """--list-drafts และ --verify-drafts: แยกร่างที่ยังอยู่ / เผยแพร่แล้ว / ถูกลบ / ตรวจไม่ได้"""
    fb.graph_url = lambda version, path: f"{server_url}/{path.lstrip('/')}"
    original_state = fb.STATE_FILE
    fb.STATE_FILE = Path(tempfile.mkdtemp()) / "fb_state.json"
    env = {"FB_PAGE_ID": "PAGE", "FB_PAGE_ACCESS_TOKEN": "TOKEN", "FB_GRAPH_VERSION": "v26.0"}
    FakeGraph.objects = {
        "111_222": {"id": "111_222", "is_published": False, "created_time": "2026-10-18T09:00:00+0000"},
        "333_444": {"id": "333_444", "is_published": True},
        "999_000": {"id": "999_000", "is_published": True},
    }
    FakeGraph.errors = {
        "555_666": (
            400,
            {
                "error": {
                    "message": (
                        "Unsupported get request. Object with ID '555_666' does not exist, "
                        "cannot be loaded due to missing permissions, or does not support this operation."
                    ),
                    "code": 100,
                }
            },
        )
    }
    fb.save_state(
        {
            "published": {},
            "scheduled": {},
            "drafts": {
                "day:5": {
                    "post_id": "111_222",
                    "source": "content/plan.json วันที่ 5",
                    "chars": 600,
                    "created_at": "2026-10-17T12:00:00+07:00",
                    "is_published": None,
                    "status": "draft",
                    "day": 5,
                    "date": "2026-10-20",
                },
                "file:fb-001-page-intro": {
                    "post_id": "333_444",
                    "source": "content/drafts/fb-001-page-intro.md",
                    "chars": 791,
                    "created_at": "2026-10-17T13:00:00+07:00",
                    "is_published": False,
                    "status": "draft",
                },
                "day:7": {
                    "post_id": "555_666",
                    "source": "content/plan.json วันที่ 7",
                    "chars": 500,
                    "created_at": "2026-10-17T14:00:00+07:00",
                    "is_published": False,
                    "status": "draft",
                    "day": 7,
                    "date": "2026-10-22",
                },
                "day:9": {
                    "post_id": "999_000",
                    "source": "content/plan.json วันที่ 9",
                    "chars": 500,
                    "created_at": "2026-10-17T15:00:00+07:00",
                    "is_published": False,
                    "status": "draft",
                    "day": 9,
                    "date": "2026-10-24",
                },
            },
            "history": [],
        }
    )
    try:
        out = capture(fb.cmd_list_drafts, env, make_args())
        check(
            "--list-drafts แสดงร่างครบทุกใบจาก state",
            "4 รายการ" in out
            and all(k in out for k in ("day:5", "file:fb-001-page-intro", "day:7", "day:9")),
            out.strip().splitlines()[0],
        )
        check("--list-drafts บอกว่ายังไม่เคยตรวจ", "ยังไม่เคยตรวจ" in out)
        check(
            "--list-drafts แสดง post id, ที่มา และความยาว",
            "111_222" in out and "content/plan.json วันที่ 5" in out and "600 ตัวอักษร" in out,
        )

        rc, out = capture_result(fb.cmd_verify_drafts, env, make_args())
        check("ตรวจได้ครบทุกใบ (ไม่มี error) → คืนค่า 0", rc == 0, f"rc={rc}")
        check("day:5 ยังเป็นร่าง (unpublished)", "day:5 (id 111_222): ยังเป็นร่าง" in out)
        check("ร่างจากไฟล์ที่ถูกเผยแพร่แล้ว", "file:fb-001-page-intro (id 333_444): เผยแพร่แล้ว" in out)
        check("โพสต์ที่ถูกลบ/อ่านไม่ได้ → ไม่พบ", "day:7 (id 555_666): ไม่พบใน Graph API" in out)
        check(
            "สรุปจำนวนถูกต้อง",
            "ยังเป็นร่าง 1" in out and "เผยแพร่แล้ว 2" in out and "ไม่พบ 1" in out and "ตรวจไม่ได้ 0" in out,
            out.strip().splitlines()[-1],
        )
        check(
            "ยิง GET ไปที่ post id ของทุกร่าง",
            all(any(pid in path for path in FakeGraph.gets) for pid in ("111_222", "333_444", "555_666", "999_000")),
            str(FakeGraph.gets),
        )

        state = fb.load_state()
        check(
            "บันทึก status ของแต่ละร่างลง state",
            state["drafts"]["day:5"]["status"] == "draft"
            and state["drafts"]["file:fb-001-page-intro"]["status"] == "published"
            and state["drafts"]["day:7"]["status"] == "missing",
            str({k: v.get("status") for k, v in state["drafts"].items()}),
        )
        check("บันทึก checked_at ทุกรายการ", all(e.get("checked_at") for e in state["drafts"].values()))
        check(
            "ร่าง day:9 ที่เผยแพร่แล้วถูกบันทึกใน published (กันโพสต์ซ้ำ)",
            state["published"].get("9", {}).get("post_id") == "999_000",
            str(state["published"].get("9")),
        )
        check("ร่าง day:5 ที่ยังเป็นร่างไม่ถูกบันทึกว่าโพสต์แล้ว", "5" not in state["published"])
        check("บอกว่าร่างของวันไหนถูกบันทึกกันโพสต์ซ้ำ", "บันทึกว่าวันที่ 9 ขึ้นเพจแล้ว" in out)
        check(
            "เตือนเมื่อร่างถูกเผยแพร่ (draft → published)",
            "🔔 เปลี่ยนสถานะ: ยังเป็นร่าง (unpublished) → เผยแพร่แล้ว" in out,
        )
        check(
            "เตือนเมื่อร่างหลุดหรือถูกลบ (draft → missing)",
            "🔔 เปลี่ยนสถานะ: ยังเป็นร่าง (unpublished) → ไม่พบใน Graph API" in out,
        )
        check(
            "สรุปจำนวนที่เปลี่ยนสถานะ",
            "เปลี่ยนสถานะจากการตรวจครั้งก่อน 3 รายการ" in out,
            [line for line in out.splitlines() if "เปลี่ยนสถานะจาก" in line],
        )
        check(
            "สรุปรายการที่ต้องตรวจสอบพร้อมชื่อร่าง",
            "ร่างที่ต้องตรวจสอบ" in out
            and "file:fb-001-page-intro: เผยแพร่แล้ว" in out
            and "day:7: ไม่พบใน Graph API" in out,
        )
        check(
            "บันทึกเวลาที่เปลี่ยนสถานะ",
            bool(fb.load_state()["drafts"]["file:fb-001-page-intro"].get("status_changed_at")),
            str(fb.load_state()["drafts"]["file:fb-001-page-intro"]),
        )

        out = capture(fb.cmd_list_drafts, env, make_args())
        check(
            "--list-drafts แสดงสถานะล่าสุดหลังตรวจ",
            "ยังเป็นร่าง (unpublished)" in out and "เผยแพร่แล้ว" in out and "ไม่พบใน Graph API" in out,
        )

        # โทเคนเสีย → ตรวจไม่ได้และคืนค่า 1
        FakeGraph.errors["888_777"] = (
            400,
            {"error": {"message": "Error validating access token: Session has expired", "code": 190}},
        )
        state = fb.load_state()
        state["drafts"]["day:11"] = {
            "post_id": "888_777",
            "source": "content/plan.json วันที่ 11",
            "chars": 520,
            "created_at": "2026-10-17T16:00:00+07:00",
            "is_published": False,
            "day": 11,
            "date": "2026-10-26",
        }
        fb.save_state(state)
        rc, out = capture_result(fb.cmd_verify_drafts, env, make_args())
        check("รายการที่ตรวจไม่ได้ทำให้คืนค่า 1", rc == 1, f"rc={rc}")
        check("แยกข้อความโทเคนใช้ไม่ได้/หมดอายุ", "โทเคนใช้ไม่ได้/หมดอายุ" in out)
        check(
            "ไม่ลบ is_published เดิมทิ้งเมื่อตรวจไม่ได้",
            fb.load_state()["drafts"]["day:11"].get("is_published") is False,
            str(fb.load_state()["drafts"]["day:11"]),
        )
        check(
            "ตรวจซ้ำโดยสถานะไม่เปลี่ยน → ไม่เตือนซ้ำ",
            "🔔 เปลี่ยนสถานะ" not in out and "ร่างที่ต้องตรวจสอบ" not in out,
            [line for line in out.splitlines() if "🔔" in line],
        )
    finally:
        FakeGraph.objects = {}
        FakeGraph.errors = {}
        fb.graph_url = original_graph_url
        fb.STATE_FILE = original_state


def phase_cli() -> None:
    """พฤติกรรมของ CLI: dry-run, การเลือกไฟล์/วัน, การกันใช้ flag ผิด"""
    state_path = fb.STATE_FILE
    existed = state_path.exists()

    code, out, err = run_cli("--draft", "--file", str(DRAFT), "--force")
    check("dry-run --draft --file สำเร็จโดยไม่ต้องมีโทเคน", code == 0, f"exit {code}")
    check("dry-run บอกว่าจะสร้างแบบ unpublished", "published=false" in out and "unpublished_content_type=DRAFT" in out)
    check("dry-run พิมพ์แคปชันให้ตรวจ", "791 ตัวอักษร" in out and "ถ้าคุณเคยเริ่มขายของออนไลน์" in out)
    check("dry-run บอกวิธีสร้างจริง", "--live" in out or "โหมดทดลอง" in out)

    code, out, err = run_cli("--draft", "--day", "1", "--force")
    check("dry-run --draft --day 1 อ่านแคปชันจากแผน", code == 0 and "content/plan.json วันที่ 1" in out, f"exit {code}")

    code, out, err = run_cli("--draft")
    check("--draft เปล่า ๆ ไม่สร้างอะไรและบอกวิธีใช้", code == 2, f"exit {code}")
    check("บอกให้เลือกไฟล์หรือวัน", "ต้องเลือก" in err and "--file" in err, err.strip().splitlines()[:1])
    check("แสดงรายการไฟล์ร่างในเครื่อง", "content/drafts/fb-001-page-intro.md" in err)

    code, out, err = run_cli("--draft", "--schedule")
    check("ใช้ --draft คู่กับ --schedule ไม่ได้", code == 2, f"exit {code}")

    code, out, err = run_cli("--file", str(DRAFT))
    check("ใช้ --file โดยไม่มี --draft ไม่ได้", code == 2 and "--draft" in err, f"exit {code}")

    code, out, err = run_cli("--draft", "--file", str(DRAFT), "--day", "1")
    check("ใช้ --file คู่กับ --day ไม่ได้", code == 2, f"exit {code}")

    code, out, err = run_cli("--draft", "--file", "ไม่มีไฟล์นี้.md")
    check("ไฟล์ที่ไม่มีจริงแจ้ง error ชัดเจน", code != 0 and "ไม่พบไฟล์ร่าง" in (out + err), f"exit {code}")

    code, out, err = run_cli("--list-drafts")
    check("--list-drafts รันได้โดยไม่ต้องมีโทเคน", code == 0, f"exit {code}")
    check(
        "--list-drafts แสดงรายการหรือบอกว่าไม่มีร่าง",
        "โพสต์ร่างที่บันทึกไว้" in out or "ยังไม่มีโพสต์ร่าง" in out,
        out.strip()[:70],
    )
    if not existed:
        code, out, err = run_cli("--verify-drafts")
        check("--verify-drafts ไม่มีร่าง → จบ 0 แม้ไม่มีโทเคน", code == 0, f"exit {code}")

    if not existed:
        check("dry-run ไม่สร้าง state/fb_state.json", not state_path.exists(), str(state_path))


def main() -> int:
    print("== ฉบับร่างในเครื่อง ==")
    phase_caption()

    original_graph_url = fb.graph_url
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeGraph)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        print("\n== Graph API จำลอง (POST published=false) ==")
        phase_http(server_url, original_graph_url)
        print("\n== กรณี Facebook ตอบว่าร่างขึ้นเพจจริง ==")
        phase_unexpected_publish(server_url, original_graph_url)
        print("\n== ดูและตรวจสถานะร่าง ==")
        phase_list_and_verify(server_url, original_graph_url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    print("\n== CLI ==")
    phase_cli()

    print("\nผ่านทั้งหมด" if not failures else f"\n{len(failures)} รายการไม่ผ่าน")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
