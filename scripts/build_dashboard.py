#!/usr/bin/env python3
"""Kopwang — สร้างหน้าเว็บปฏิทิน 30 วัน จากไฟล์แผน content/plan.json

หน้าเว็บที่ได้เป็นไฟล์ HTML ไฟล์เดียว (ฝังข้อมูลไว้ในตัว) จึงเปิดด้วยการดับเบิลคลิก
ก็ได้ หรือจะเสิร์ฟผ่านเซิร์ฟเวอร์ในเครื่องก็ได้ ไม่ต้องต่ออินเทอร์เน็ต

    python3 scripts/build_dashboard.py                 # สร้าง content/plan.json ให้ก่อนถ้ายังไม่มี
    python3 scripts/build_dashboard.py --no-generate   # ใช้ plan.json เดิม
    python3 scripts/build_dashboard.py --open          # เปิดในเบราว์เซอร์ให้เลย

จากนั้นเปิดดูได้ 2 วิธี

    เปิดไฟล์ตรง ๆ:  dashboard/index.html
    เสิร์ฟในเครื่อง: python3 -m http.server 3000 --directory dashboard
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "content" / "plan.json"
OUT_PATH = ROOT / "dashboard" / "index.html"

PLATFORMS = ["facebook", "tiktok", "shopee"]

PLATFORM_LABEL = {
    "facebook": "Facebook",
    "tiktok": "TikTok",
    "shopee": "Shopee",
}

PLATFORM_SHORT = {
    "facebook": "FB",
    "tiktok": "TT",
    "shopee": "SP",
}


def load_plan(plan_path: Path) -> dict:
    """อ่าน plan.json และแปลงเป็นโครงที่หน้าเว็บใช้ง่าย: รวมโพสต์ของแต่ละวันไว้ด้วยกัน"""
    if not plan_path.exists():
        raise SystemExit(
            f"ไม่พบไฟล์ {plan_path.relative_to(ROOT)}\n"
            "รันคำสั่งนี้ก่อน: python3 scripts/generate_plan.py --start-date YYYY-MM-DD\n"
            "(หรือไม่ต้องใส่ --no-generate)"
        )

    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    rows = raw.get("rows") or []
    if not rows:
        raise SystemExit(f"ไฟล์ {plan_path} ไม่มีข้อมูลแถวโพสต์ (คีย์ 'rows' ว่าง)")

    days: dict[int, dict] = {}
    posts_seen = 0

    for row in rows:
        day = int(row["day"])
        platform = str(row.get("platform", "")).strip().lower()
        if platform not in PLATFORMS:
            continue

        entry = days.setdefault(
            day,
            {
                "day": day,
                "date": row.get("date", ""),
                "weekday": row.get("weekday", ""),
                "phase": row.get("phase", ""),
                "phase_goal": row.get("phase_goal", ""),
                "theme": row.get("theme", ""),
                "hook": row.get("hook", ""),
                "posts": {},
            },
        )
        entry["posts"][platform] = {
            "platform": platform,
            "post_time": row.get("post_time", ""),
            "format": row.get("format", ""),
            "title": row.get("title", ""),
            "caption": row.get("caption", ""),
            "script": row.get("notes", ""),
            "hook": row.get("hook", ""),
        }
        posts_seen += 1

    day_list = [days[k] for k in sorted(days)]

    return {
        "brand": raw.get("brand", {}),
        "plan_generated_at": raw.get("generated_at", ""),
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "plan_file": str(PLAN_PATH.relative_to(ROOT)),
        "platforms": PLATFORMS,
        "days": day_list,
        "total_posts": posts_seen,
    }


HTML_TEMPLATE = r"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kopwang · ปฏิทิน 30 วัน</title>
<style>
  :root{
    --bg:#0f1115; --panel:#171a21; --panel2:#1e222b; --line:#2a2f3a;
    --text:#e8ebf0; --muted:#9aa4b2; --accent:#ffb020;
    --fb:#1877f2; --tt:#fe2c55; --sp:#ee4d2d; --ok:#25c281;
    --radius:14px;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    background:var(--bg); color:var(--text);
    font-family:"Noto Sans Thai","Sarabun","IBM Plex Sans Thai",system-ui,-apple-system,"Segoe UI",sans-serif;
    line-height:1.55; -webkit-text-size-adjust:100%;
  }
  a{color:var(--accent)}
  header.top{
    padding:22px 20px 16px; border-bottom:1px solid var(--line);
    background:linear-gradient(180deg,#1b1f28,var(--bg));
  }
  .wrap{max-width:1180px;margin:0 auto}
  h1{margin:0 0 4px;font-size:1.5rem}
  .sub{color:var(--muted);font-size:.9rem}
  .brandline{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:10px;font-size:.88rem;color:var(--muted)}
  .brandline b{color:var(--text);font-weight:600}
  .progress{margin-top:14px;display:flex;align-items:center;gap:12px;font-size:.85rem;color:var(--muted)}
  .bar{flex:1;height:8px;background:#22262f;border-radius:99px;overflow:hidden;min-width:120px}
  .bar > i{display:block;height:100%;width:0;background:linear-gradient(90deg,#ffb020,#25c281);transition:width .25s}

  .toolbar{
    position:sticky;top:0;z-index:20;background:rgba(15,17,21,.94);
    backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
    padding:10px 20px;
  }
  .toolbar .row{max-width:1180px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
  select,input[type=search],button{
    font:inherit;font-size:.86rem;color:var(--text);background:var(--panel2);
    border:1px solid var(--line);border-radius:10px;padding:7px 11px;
  }
  input[type=search]{min-width:190px;flex:1}
  button{cursor:pointer}
  button:hover{border-color:#3b414d;background:#242935}
  button.primary{background:var(--accent);border-color:var(--accent);color:#191307;font-weight:600}
  button.ghost{background:transparent}
  main{padding:20px;max-width:1180px;margin:0 auto}

  section.week{margin:0 0 26px}
  .weekhead{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline;margin:0 0 12px}
  .weekhead .tag{
    font-size:.75rem;font-weight:700;letter-spacing:.06em;padding:3px 9px;border-radius:99px;
    background:#2b2113;color:var(--accent);border:1px solid #4a3a17
  }
  .weekhead .goal{color:var(--muted);font-size:.88rem}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:12px}

  article.day{
    background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
    padding:12px 12px 10px;cursor:pointer;transition:border-color .15s,transform .15s;
    display:flex;flex-direction:column;gap:8px;
  }
  article.day:hover{border-color:#3d4453;transform:translateY(-1px)}
  article.day.today{border-color:var(--accent);box-shadow:0 0 0 1px rgba(255,176,32,.35)}
  article.day.all-done{border-color:var(--ok)}
  .daytop{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
  .daynum{font-weight:700;font-size:1.02rem}
  .daydate{color:var(--muted);font-size:.78rem;text-align:right}
  .theme{font-size:.88rem;min-height:2.4em}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:auto}
  .chip{
    font-size:.74rem;padding:2px 7px;border-radius:99px;border:1px solid var(--line);
    color:var(--muted);display:inline-flex;align-items:center;gap:4px;background:#1b1f27
  }
  .chip.facebook{color:#cfe2ff;border-color:#28405f;background:#16223a}
  .chip.tiktok{color:#ffd5de;border-color:#5c2436;background:#2a1620}
  .chip.shopee{color:#ffdcd2;border-color:#5f2b1e;background:#2a1a15}
  .chip.done{border-color:var(--ok);color:#bdf4dc}
  .empty-note{color:var(--muted);font-size:.85rem;padding:8px 0}

  dialog{
    border:1px solid var(--line);background:var(--panel);color:var(--text);
    border-radius:16px;padding:0;max-width:760px;width:min(94vw,760px);
  }
  dialog::backdrop{background:rgba(6,8,11,.72)}
  .modal-head{padding:16px 18px 12px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:flex-start}
  .modal-head h2{margin:0;font-size:1.08rem}
  .modal-head .meta{color:var(--muted);font-size:.83rem;margin-top:2px}
  .modal-head .close{margin-left:auto;background:transparent;border:1px solid var(--line);border-radius:9px;padding:4px 10px}
  .tabs{display:flex;gap:6px;padding:12px 18px 0;flex-wrap:wrap}
  .tab{border:1px solid var(--line);background:#1b1f27;border-radius:99px;padding:5px 13px;font-size:.84rem;color:var(--muted)}
  .tab.active{color:var(--text);border-color:#4a5261;background:#242a35}
  .tab.facebook.active{border-color:var(--fb)}
  .tab.tiktok.active{border-color:var(--tt)}
  .tab.shopee.active{border-color:var(--sp)}
  .modal-body{padding:14px 18px 18px;max-height:64vh;overflow:auto}
  .field{margin:0 0 12px}
  .field .k{font-size:.76rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin-bottom:3px}
  .txt{
    background:#12151b;border:1px solid var(--line);border-radius:11px;padding:11px 12px;
    white-space:pre-wrap;word-wrap:break-word;font-size:.88rem;margin:0;
  }
  .blockhead{display:flex;align-items:center;gap:10px;margin:0 0 6px}
  .blockhead .k{font-size:.76rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
  .blockhead button{margin-left:auto;padding:4px 11px;font-size:.8rem}
  .modal-foot{padding:12px 18px 16px;border-top:1px solid var(--line);display:flex;flex-wrap:wrap;gap:8px;align-items:center}
  .done-toggle{display:flex;align-items:center;gap:7px;font-size:.86rem;color:var(--muted);cursor:pointer}
  .done-toggle input{width:16px;height:16px;accent-color:var(--ok)}

  .postbox{
    border-top:1px solid var(--line);padding:12px 18px;background:#151922;
    display:flex;flex-direction:column;gap:8px;
  }
  .postrow{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
  .poststatus{font-size:.82rem;color:var(--muted)}
  .poststatus.warn{color:#ffcf7a}
  button.postlive{background:var(--fb);border-color:var(--fb);color:#fff;font-weight:600}
  button.postlive:hover{background:#1668d6}
  button.postlive[disabled],button.postlive[disabled]:hover{opacity:.45;cursor:not-allowed;background:var(--fb)}
  #m-post-out{max-height:190px;overflow:auto;margin:0;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.8rem}
  .published-badge{
    color:var(--ok);border:1px solid #1f5b45;background:#12261f;border-radius:99px;
    padding:1px 7px;font-size:.72rem;white-space:nowrap;
  }
  .scheduled-badge{
    color:#ffcf7a;border:1px solid #4a3a17;background:#2b2113;border-radius:99px;
    padding:1px 7px;font-size:.72rem;white-space:nowrap;
  }
  .schedrow,.draftrow{border-top:1px dashed var(--line);margin-top:2px;padding-top:9px}

  #toast{
    position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(20px);
    background:#242a35;border:1px solid #3d4453;color:var(--text);padding:9px 16px;border-radius:99px;
    font-size:.86rem;opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;z-index:60;max-width:90vw
  }
  #toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
  footer{padding:8px 20px 40px;max-width:1180px;margin:0 auto;color:var(--muted);font-size:.8rem}

  @media print{
    :root{--bg:#fff;--panel:#fff;--panel2:#fff;--text:#111;--muted:#555;--line:#ccc}
    body{background:#fff;color:#111}
    .toolbar,.modal-foot,#toast,footer{display:none !important}
    header.top{background:#fff}
    .grid{grid-template-columns:repeat(3,1fr)}
    article.day{break-inside:avoid}
  }
</style>
</head>
<body>
<header class="top">
  <div class="wrap">
    <h1 id="h-title">Kopwang · ปฏิทิน 30 วัน</h1>
    <div class="sub" id="h-sub"></div>
    <div class="brandline" id="h-brand"></div>
    <div class="progress">
      <span id="h-progress">ทำแล้ว 0 / 0</span>
      <span class="bar"><i id="h-bar"></i></span>
      <button class="ghost" id="btn-reset" title="ล้างเครื่องหมายทำแล้วทั้งหมด">ล้างเครื่องหมาย</button>
    </div>
  </div>
</header>

<div class="toolbar">
  <div class="row">
    <label>แพลตฟอร์ม
      <select id="f-platform">
        <option value="all">ทั้งหมด</option>
        <option value="facebook">Facebook</option>
        <option value="tiktok">TikTok</option>
        <option value="shopee">Shopee</option>
      </select>
    </label>
    <label>สัปดาห์
      <select id="f-week">
        <option value="all">ทั้งหมด</option>
      </select>
    </label>
    <select id="f-status">
      <option value="all">ทุกสถานะ</option>
      <option value="todo">ยังไม่ทำ</option>
      <option value="done">ทำแล้ว</option>
    </select>
    <input type="search" id="f-search" placeholder="ค้นหา: หัวข้อ, hook, แคปชัน, งาน…">
    <button id="btn-today">ไปวันที่วันนี้</button>
    <button class="ghost" id="btn-print">พิมพ์ / PDF</button>
  </div>
</div>

<main id="main"></main>

<footer id="foot"></footer>

<dialog id="modal">
  <div class="modal-head">
    <div>
      <h2 id="m-title"></h2>
      <div class="meta" id="m-meta"></div>
    </div>
    <button class="close" id="m-close">ปิด ✕</button>
  </div>
  <div class="tabs" id="m-tabs"></div>
  <div class="modal-body" id="m-body"></div>
  <div class="postbox" id="m-postbox" hidden>
    <div class="postrow">
      <span class="poststatus" id="m-post-status"></span>
      <span style="flex:1"></span>
      <button id="m-post-dry">ทดลองโพสต์ (ไม่ยิง API)</button>
      <button class="postlive" id="m-post-live">โพสต์ขึ้นเพจทันที</button>
    </div>
    <div class="postrow schedrow">
      <span class="poststatus" id="m-sched-status"></span>
      <span style="flex:1"></span>
      <button id="m-sched-dry">ทดลองตั้งเวลา</button>
      <button class="postlive" id="m-sched-live">ตั้งเวลาโพสต์ล่วงหน้า</button>
    </div>
    <div class="postrow draftrow">
      <span class="poststatus" id="m-draft-status"></span>
      <span style="flex:1"></span>
      <button id="m-draft-dry">ทดลองสร้างร่าง</button>
      <button class="postlive" id="m-draft-live">สร้างโพสต์ร่าง (unpublished)</button>
    </div>
    <pre class="txt" id="m-post-out" hidden></pre>
  </div>
  <div class="modal-foot">
    <label class="done-toggle"><input type="checkbox" id="m-done"> ทำโพสต์นี้แล้ว</label>
    <button id="m-copy-all">คัดลอกโพสต์นี้ทั้งหมด</button>
    <button class="ghost" id="m-copy-plan">คัดลอกทุกแพลตฟอร์มของวันนี้</button>
  </div>
</dialog>

<div id="toast"></div>

<script>
const DATA = __PLAN_DATA__;
const PLATFORMS = DATA.platforms;
const SHORT = {facebook:"FB", tiktok:"TT", shopee:"SP"};
const LABEL = {facebook:"Facebook", tiktok:"TikTok", shopee:"Shopee"};
const STORE_KEY = "kopwang.done.v1";

let done = loadDone();
let activeDay = null;
let activeTab = "facebook";

/* สถานะจากเซิร์ฟเวอร์ในเครื่อง (scripts/dashboard_server.py) — ถ้าเปิดไฟล์ตรง ๆ จะไม่พร้อมใช้ */
let API = {api:false, live_allowed:false, credentials_ready:false, published:{}, scheduled:{}, drafts:{}, schedule_window:{}};
let postOutput = null; // {day, text} เก็บผลลัพธ์ล่าสุดไว้แสดงในกล่องข้อความ

function publishedOf(day){ return API.published[String(day)] || null; }
function scheduledOf(day){ return API.scheduled[String(day)] || null; }
function draftsOf(day){ return (API.drafts || {})[String(day)] || null; }
function scheduleWindowOf(day){ return (API.schedule_window || {})[String(day)] || null; }

/* "2026-10-18T12:00+07:00" → "2026-10-18 12:00" (เวลาไทยตามที่อยู่ในแผน) */
function slotText(at){
  return at ? String(at).slice(0, 16).replace("T", " ") : "";
}

async function loadStatus(){
  if(typeof fetch !== "function") return;
  try{
    const res = await fetch("/api/status", {headers:{"Accept":"application/json"}});
    if(!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    API = Object.assign({}, API, data, {api:true});
  }catch(err){
    API = Object.assign({}, API, {api:false});
    return;
  }
  // วันที่โพสต์ขึ้นเพจจริงแล้ว = ทำแล้ว
  let changed = false;
  Object.keys(API.published || {}).forEach(function(day){
    if(!done[keyOf(day, "facebook")]){ done[keyOf(day, "facebook")] = 1; changed = true; }
  });
  if(changed) saveDone();
  render();
  refreshProgress();
  if(activeDay && document.getElementById("modal").open) renderModal();
}

async function callServer(path, day, live, pending, liveMsg, dryMsg){
  const out = document.getElementById("m-post-out");
  out.hidden = false;
  out.textContent = pending;
  let text;
  try{
    const res = await fetch(path, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({day:day, live:live})
    });
    const data = await res.json().catch(function(){ return {}; });
    text = data.output || data.error || ("HTTP " + res.status);
    if(data.ok){
      if(data.mode === "live" && path === "/api/post") setDone(day, "facebook", true);
      toast(data.mode === "live" ? liveMsg : dryMsg);
      if(data.status) API = Object.assign({}, API, data.status, {api:true});
    } else {
      toast("ไม่สำเร็จ — อ่านข้อความในกล่องด้านล่าง");
      if(data.status) API = Object.assign({}, API, data.status, {api:true});
    }
  }catch(err){
    text = "เรียกเซิร์ฟเวอร์ไม่ได้: " + err.message +
      "\n\nต้องเปิดหน้านี้ผ่านเซิร์ฟเวอร์ในเครื่อง:\n" +
      "    python3 scripts/dashboard_server.py\n" +
      "(ถ้าเปิดไฟล์ตรง ๆ หรือเสิร์ฟด้วย http.server ปุ่มนี้จะใช้ไม่ได้)";
  }
  postOutput = {day: day, text: text};
  render();
  if(document.getElementById("modal").open) renderModal();
}

function postDay(day, live){
  return callServer("/api/post", day, live,
    live ? "กำลังโพสต์ขึ้นเพจ…" : "กำลังทดลองโพสต์…",
    "โพสต์ขึ้นเพจแล้ว", "ทดลองเสร็จ — ยังไม่ยิงเข้า API จริง");
}

function scheduleDay(day, live){
  return callServer("/api/schedule", day, live,
    live ? "กำลังตั้งเวลาโพสต์…" : "กำลังทดลองตั้งเวลา…",
    "ตั้งเวลาโพสต์ไว้แล้ว", "ทดลองตั้งเวลาเสร็จ — ยังไม่ยิงเข้า API จริง");
}

function draftDay(day, live){
  return callServer("/api/draft", day, live,
    live ? "กำลังสร้างโพสต์ร่าง…" : "กำลังทดลองสร้างร่าง…",
    "สร้างโพสต์ร่างแล้ว (ยังไม่ขึ้นเพจ)", "ทดลองสร้างร่างเสร็จ — ยังไม่ยิงเข้า API จริง");
}


function loadDone(){
  try { return JSON.parse(localStorage.getItem(STORE_KEY) || "{}") || {}; }
  catch(e){ return {}; }
}
function saveDone(){
  try { localStorage.setItem(STORE_KEY, JSON.stringify(done)); } catch(e){}
}
function keyOf(day, platform){ return day + ":" + platform; }
function isDone(day, platform){ return !!done[keyOf(day, platform)]; }
function setDone(day, platform, value){
  if(value) done[keyOf(day, platform)] = 1; else delete done[keyOf(day, platform)];
  saveDone(); render(); refreshProgress();
}
function postOf(day, platform){ return (day.posts && day.posts[platform]) || null; }
function doneCount(){
  let n = 0;
  DATA.days.forEach(function(d){
    PLATFORMS.forEach(function(p){ if(postOf(d,p) && isDone(d.day,p)) n++; });
  });
  return n;
}
function refreshProgress(){
  const total = DATA.total_posts;
  const n = doneCount();
  document.getElementById("h-progress").textContent = "ทำแล้ว " + n + " / " + total + " โพสต์";
  document.getElementById("h-bar").style.width = total ? Math.round(n/total*100) + "%" : "0%";
}

function toast(msg){
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(function(){ el.classList.remove("show"); }, 1900);
}

function fallbackCopy(text){
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.top = "-1000px";
  document.body.appendChild(ta);
  ta.select();
  ta.setSelectionRange(0, ta.value.length);
  let ok = false;
  try { ok = document.execCommand("copy"); } catch(e){ ok = false; }
  document.body.removeChild(ta);
  return ok;
}
async function copyText(text, label){
  if(!text || !text.trim()){ toast("ไม่มีข้อความให้คัดลอก"); return; }
  let ok = false;
  if(navigator.clipboard && window.isSecureContext){
    try { await navigator.clipboard.writeText(text); ok = true; } catch(e){ ok = false; }
  }
  if(!ok) ok = fallbackCopy(text);
  toast(ok ? ("คัดลอก " + label + " แล้ว") : "เบราว์เซอร์บล็อกการคัดลอก — เลือกข้อความแล้วกด Ctrl+C");
}

function el(tag, cls, text){
  const n = document.createElement(tag);
  if(cls) n.className = cls;
  if(text !== undefined && text !== null) n.textContent = text;
  return n;
}

/* ---------- ตัวกรอง ---------- */
const state = {platform:"all", week:"all", status:"all", q:""};

function matchSearch(day, q){
  if(!q) return true;
  const hay = [day.theme, day.hook, day.phase_goal, "วันที่ " + day.day].join(" ");
  const parts = [hay];
  PLATFORMS.forEach(function(p){
    const post = postOf(day, p);
    if(post) parts.push([post.title, post.caption, post.script, post.format, post.post_time].join(" "));
  });
  return parts.join(" ").toLowerCase().indexOf(q) !== -1;
}
function matchPlatform(day){
  if(state.platform === "all") return true;
  return !!postOf(day, state.platform);
}
function matchStatus(day){
  if(state.status === "all") return true;
  const list = PLATFORMS.filter(function(p){ return postOf(day, p); });
  if(!list.length) return false;
  const allDone = list.every(function(p){ return isDone(day.day, p); });
  const anyDone = list.some(function(p){ return isDone(day.day, p); });
  return state.status === "done" ? anyDone : !allDone;
}
function visibleDays(){
  const q = state.q.trim().toLowerCase();
  return DATA.days.filter(function(d){
    if(state.week !== "all" && d.phase !== state.week) return false;
    if(!matchPlatform(d) || !matchStatus(d) || !matchSearch(d, q)) return false;
    return true;
  });
}

/* ---------- เรนเดอร์ ---------- */
function todayISO(){
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return d.getFullYear() + "-" + m + "-" + day;
}

function render(){
  const main = document.getElementById("main");
  main.innerHTML = "";
  const days = visibleDays();
  if(!days.length){
    main.appendChild(el("p", "empty-note", "ไม่พบวันที่ตรงกับตัวกรอง — ลองล้างตัวกรองหรือคำค้นหา"));
    return;
  }
  const weeks = [];
  days.forEach(function(d){
    let w = weeks[weeks.length - 1];
    if(!w || w.phase !== d.phase) { w = {phase:d.phase, goal:d.phase_goal, days:[]}; weeks.push(w); }
    w.days.push(d);
  });
  const today = todayISO();
  weeks.forEach(function(w){
    const sec = el("section", "week");
    const head = el("div", "weekhead");
    head.appendChild(el("span", "tag", w.phase));
    head.appendChild(el("span", "goal", w.goal || ""));
    sec.appendChild(head);
    const grid = el("div", "grid");
    w.days.forEach(function(d){ grid.appendChild(dayCard(d, today)); });
    sec.appendChild(grid);
    main.appendChild(sec);
  });
}

function dayCard(d, today){
  const card = el("article", "day");
  if(d.date === today) card.classList.add("today");
  const list = PLATFORMS.filter(function(p){ return postOf(d, p); });
  if(list.length && list.every(function(p){ return isDone(d.day, p); })) card.classList.add("all-done");

  const top = el("div", "daytop");
  const left = el("div", "");
  left.appendChild(el("span", "daynum", "วันที่ " + d.day));
  const pub = publishedOf(d.day);
  const sched = scheduledOf(d.day);
  if(pub && pub.post_id) left.appendChild(el("span", "published-badge", " FB โพสต์แล้ว"));
  else if(sched && sched.post_id) left.appendChild(el("span", "scheduled-badge", " FB ตั้งเวลาไว้"));
  top.appendChild(left);
  top.appendChild(el("span", "daydate", (d.weekday ? d.weekday + " " : "") + d.date));
  card.appendChild(top);

  card.appendChild(el("div", "theme", d.theme || ""));

  const chips = el("div", "chips");
  list.forEach(function(p){
    const post = postOf(d, p);
    const chip = el("span", "chip " + p, SHORT[p] + " " + (post.post_time || ""));
    if(isDone(d.day, p)){ chip.classList.add("done"); chip.textContent += " ✓"; }
    chips.appendChild(chip);
  });
  card.appendChild(chips);

  card.addEventListener("click", function(){ openDay(d.day, state.platform === "all" ? (list[0] || "facebook") : state.platform); });
  return card;
}

/* ---------- ป๊อปอัป ---------- */
function copyBlocksFor(day, platform){
  const post = postOf(day, platform);
  if(!post) return [];
  const blocks = [];
  if(post.caption) blocks.push({k:"แคปชัน", v:post.caption});
  if(post.script) blocks.push({k:(platform === "tiktok" ? "สคริปต์วิดีโอ (ลำดับภาพ/คำพูด)" : (platform === "shopee" ? "งานที่ต้องทำ" : "โน้ตกำกับ")), v:post.script});
  return blocks;
}

function plainTextFor(day, platform){
  const post = postOf(day, platform);
  if(!post) return "";
  const lines = [];
  lines.push("[" + LABEL[platform] + "] วันที่ " + day.day + " · " + (post.post_time || "") + " · " + (post.format || ""));
  lines.push("หัวข้อ: " + (post.title || ""));
  if(post.hook) lines.push("Hook: " + post.hook);
  copyBlocksFor(day, platform).forEach(function(b){
    lines.push("");
    lines.push("— " + b.k + " —");
    lines.push(b.v);
  });
  return lines.join("\n");
}

function textBlock(label, value){
  const wrap = el("div", "field");
  const head = el("div", "blockhead");
  head.appendChild(el("span", "k", label));
  const btn = el("button", "", "คัดลอก");
  btn.addEventListener("click", function(){ copyText(value, label); });
  head.appendChild(btn);
  wrap.appendChild(head);
  wrap.appendChild(el("pre", "txt", value));
  return wrap;
}

function openDay(dayNumber, platform){
  const day = DATA.days.find(function(d){ return d.day === dayNumber; });
  if(!day) return;
  activeDay = day;
  activeTab = (platform && postOf(day, platform)) ? platform : (PLATFORMS.filter(function(p){ return postOf(day, p); })[0] || "facebook");

  document.getElementById("m-title").textContent = "วันที่ " + day.day + " · " + (day.theme || "");
  document.getElementById("m-meta").textContent = [day.weekday, day.date, day.phase, day.phase_goal].filter(Boolean).join(" · ");
  renderModal();
  const dlg = document.getElementById("modal");
  if(!dlg.open) dlg.showModal();
}

function renderModal(){
  const day = activeDay;
  const tabs = document.getElementById("m-tabs");
  const body = document.getElementById("m-body");
  tabs.innerHTML = "";
  body.innerHTML = "";

  PLATFORMS.forEach(function(p){
    if(!postOf(day, p)) return;
    const b = el("button", "tab " + p + (p === activeTab ? " active" : ""), LABEL[p] + " " + (postOf(day,p).post_time || ""));
    b.addEventListener("click", function(){ activeTab = p; renderModal(); });
    tabs.appendChild(b);
  });

  const post = postOf(day, activeTab);
  if(!post){
    body.appendChild(el("p", "empty-note", "วันนี้ไม่มีโพสต์ของแพลตฟอร์มนี้"));
    renderPostBox();
    return;
  }
  if(post.hook) body.appendChild(textBlock("Hook / ประโยคเปิด", post.hook));
  const facts = el("div", "field");
  facts.appendChild(el("div", "k", "ข้อมูลโพสต์"));
  facts.appendChild(el("div", "txt", "เวลาโพสต์: " + (post.post_time || "-") + "\nรูปแบบ: " + (post.format || "-") + "\nหัวข้อ: " + (post.title || "-")));
  body.appendChild(facts);
  copyBlocksFor(day, activeTab).forEach(function(b){ body.appendChild(textBlock(b.k, b.v)); });
  if(!copyBlocksFor(day, activeTab).length){
    body.appendChild(el("p", "empty-note", "ยังไม่มีข้อความสำหรับโพสต์นี้"));
  }

  const cb = document.getElementById("m-done");
  cb.checked = isDone(day.day, activeTab);
  cb.onchange = function(){ setDone(day.day, activeTab, cb.checked); };
  document.getElementById("m-copy-all").onclick = function(){ copyText(plainTextFor(day, activeTab), LABEL[activeTab] + " วันที่ " + day.day); };
  document.getElementById("m-copy-plan").onclick = function(){
    const txt = PLATFORMS.filter(function(p){ return postOf(day, p); })
      .map(function(p){ return plainTextFor(day, p); }).join("\n\n==========\n\n");
    copyText(txt, "แผนวันที่ " + day.day);
  };
  renderPostBox();
}

/* ---------- กล่องโพสต์ Facebook (ต้องเปิดผ่าน scripts/dashboard_server.py) ---------- */
function renderPostBox(){
  const box = document.getElementById("m-postbox");
  if(!activeDay || activeTab !== "facebook" || !postOf(activeDay, "facebook")){ box.hidden = true; return; }
  box.hidden = false;

  const day = activeDay.day;
  const status = document.getElementById("m-post-status");
  const dryBtn = document.getElementById("m-post-dry");
  const liveBtn = document.getElementById("m-post-live");
  const schedStatus = document.getElementById("m-sched-status");
  const schedDry = document.getElementById("m-sched-dry");
  const schedLive = document.getElementById("m-sched-live");
  const draftStatus = document.getElementById("m-draft-status");
  const draftDry = document.getElementById("m-draft-dry");
  const draftLive = document.getElementById("m-draft-live");
  const out = document.getElementById("m-post-out");
  const pub = publishedOf(day);
  const sched = scheduledOf(day);
  const draft = draftsOf(day);
  const win = scheduleWindowOf(day);

  const notes = [];
  if(pub && pub.post_id){
    notes.push("โพสต์แล้ว " + (pub.at || "") + " (id " + pub.post_id + ")");
  } else if(sched && sched.post_id){
    notes.push("ยังไม่โพสต์ — ตั้งเวลาไว้ " + slotText(sched.scheduled_for));
  } else {
    notes.push("ยังไม่โพสต์");
  }
  if(!API.api){
    notes.push("ยังไม่เชื่อมเซิร์ฟเวอร์ในเครื่อง — เปิดด้วย python3 scripts/dashboard_server.py (ปุ่มโพสต์จะใช้ไม่ได้)");
  } else {
    notes.push("โทเคน: " + (API.credentials_ready ? "พร้อม" : "ยังไม่ตั้งค่าใน .env"));
    notes.push("เซิร์ฟเวอร์: " + (API.live_allowed ? "เปิดโพสต์จริง" : "ทดลองเท่านั้น (เปิดใหม่ด้วย --live)"));
  }
  status.textContent = notes.join(" · ");
  if(!API.api || !API.credentials_ready) status.classList.add("warn"); else status.classList.remove("warn");

  dryBtn.disabled = !API.api;
  liveBtn.disabled = !API.api || !API.live_allowed || !API.credentials_ready;
  liveBtn.title = !API.api
    ? "ต้องเปิดหน้าผ่าน scripts/dashboard_server.py"
    : (!API.live_allowed
        ? "เซิร์ฟเวอร์ยังไม่ได้เปิดด้วย --live"
        : (!API.credentials_ready ? "ยังไม่มี FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN ใน .env" : ""));

  if(postOutput && postOutput.day === day){
    out.hidden = false;
    out.textContent = postOutput.text;
  } else {
    out.hidden = true;
    out.textContent = "";
  }

  dryBtn.onclick = function(){ postDay(day, false); };
  liveBtn.onclick = function(){
    if(!confirm("โพสต์ข้อความของวันที่ " + day + " ขึ้นเพจ Facebook จริงหรือไม่?")) return;
    postDay(day, true);
  };

  /* ---------- ตั้งเวลาโพสต์ล่วงหน้า ---------- */
  const schedNotes = [];
  if(pub && pub.post_id){
    schedNotes.push("โพสต์ขึ้นเพจแล้ว — ไม่ต้องตั้งเวลา");
  } else if(sched && sched.post_id){
    schedNotes.push("ตั้งเวลาไว้ " + slotText(sched.scheduled_for) + " (id " + sched.post_id + ")");
  } else if(!API.api){
    schedNotes.push("ยังไม่เชื่อมเซิร์ฟเวอร์ในเครื่อง — ตั้งเวลาไม่ได้");
  } else if(!win){
    schedNotes.push("ไม่พบกำหนดโพสต์ของวันนี้ใน plan.json");
  } else if(win.window === "past"){
    schedNotes.push("เลยเวลาตั้งเวลาแล้ว (กำหนด " + slotText(win.at) + ") — ใช้ปุ่มโพสต์ขึ้นเพจทันทีแทน");
  } else if(win.window === "too_far"){
    schedNotes.push("กำหนด " + slotText(win.at) + " เกิน 30 วันล่วงหน้า Meta ไม่รับตั้งเวลา");
  } else {
    schedNotes.push("จะตั้งเวลาไว้ " + slotText(win.at) + " ตามเวลาในแผน");
  }
  schedStatus.textContent = schedNotes.join(" · ");
  if(!API.api || (win && win.window !== "ok")) schedStatus.classList.add("warn"); else schedStatus.classList.remove("warn");

  schedDry.disabled = !API.api;
  function schedBlockedReason(){
    if(!API.api) return "ต้องเปิดหน้าผ่าน scripts/dashboard_server.py";
    if(!API.live_allowed) return "เซิร์ฟเวอร์ยังไม่ได้เปิดด้วย --live";
    if(!API.credentials_ready) return "ยังไม่มี FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN ใน .env";
    if(pub && pub.post_id) return "โพสต์ขึ้นเพจแล้ว";
    if(sched && sched.post_id) return "ตั้งเวลาไว้แล้ว";
    if(!win) return "ไม่พบกำหนดโพสต์ของวันนี้ใน plan.json";
    if(win.window === "past") return "เลยเวลาตั้งเวลาแล้ว — ใช้ปุ่มโพสต์ขึ้นเพจทันที";
    if(win.window === "too_far") return "เกิน 30 วันล่วงหน้า Meta ไม่รับ";
    return "";
  }
  schedLive.disabled = !!schedBlockedReason();
  schedLive.title = schedBlockedReason();

  schedDry.onclick = function(){ scheduleDay(day, false); };
  schedLive.onclick = function(){
    if(!confirm("ตั้งเวลาโพสต์ของวันที่ " + day + " ไว้ที่ " + slotText(win && win.at) + " หรือไม่?")) return;
    scheduleDay(day, true);
  };

  /* ---------- สร้างโพสต์ร่าง (unpublished) ---------- */
  const draftNotes = [];
  if(draft && draft.post_id){
    draftNotes.push("มีร่าง unpublished แล้ว (id " + draft.post_id + ") — ตรวจใน Meta Business Suite → Content → Drafts");
  } else if(!API.api){
    draftNotes.push("ยังไม่เชื่อมเซิร์ฟเวอร์ในเครื่อง — สร้างร่างไม่ได้");
  } else if(!API.credentials_ready){
    draftNotes.push("ยังไม่มี FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN ใน .env — สร้างร่างไม่ได้");
  } else {
    draftNotes.push("จะสร้างร่าง unpublished จากแคปชันนี้ — ไม่ขึ้นเพจจนกว่าจะกดเผยแพร่เอง");
  }
  draftStatus.textContent = draftNotes.join(" · ");
  if(!API.api || (!API.credentials_ready && !(draft && draft.post_id))) draftStatus.classList.add("warn");
  else draftStatus.classList.remove("warn");

  draftDry.disabled = !API.api;
  function draftBlockedReason(){
    if(!API.api) return "ต้องเปิดหน้าผ่าน scripts/dashboard_server.py";
    if(!API.live_allowed) return "เซิร์ฟเวอร์ยังไม่ได้เปิดด้วย --live";
    if(!API.credentials_ready) return "ยังไม่มี FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN ใน .env";
    if(draft && draft.post_id) return "มีร่าง unpublished อยู่แล้ว";
    return "";
  }
  draftLive.disabled = !!draftBlockedReason();
  draftLive.title = draftBlockedReason();

  draftDry.onclick = function(){ draftDay(day, false); };
  draftLive.onclick = function(){
    if(!confirm("สร้างโพสต์ร่าง (unpublished) ของวันที่ " + day + " ใน Facebook หรือไม่?\nร่างจะยังไม่ขึ้นเพจ จนกว่าคุณจะกดเผยแพร่เอง")) return;
    draftDay(day, true);
  };
}

/* ---------- เหตุการณ์ ---------- */
function bind(){
  const selPlatform = document.getElementById("f-platform");
  const selWeek = document.getElementById("f-week");
  const selStatus = document.getElementById("f-status");
  const search = document.getElementById("f-search");

  const phases = [];
  DATA.days.forEach(function(d){ if(d.phase && phases.indexOf(d.phase) === -1) phases.push(d.phase); });
  phases.forEach(function(p){ selWeek.appendChild(new Option(p, p)); });

  selPlatform.addEventListener("change", function(){ state.platform = selPlatform.value; render(); });
  selWeek.addEventListener("change", function(){ state.week = selWeek.value; render(); });
  selStatus.addEventListener("change", function(){ state.status = selStatus.value; render(); });
  search.addEventListener("input", function(){ state.q = search.value; render(); });

  document.getElementById("btn-today").addEventListener("click", function(){
    const iso = todayISO();
    const day = DATA.days.find(function(d){ return d.date === iso; });
    if(day){ openDay(day.day, "all"); }
    else { toast("วันนี้ (" + iso + ") ไม่มีในแผน — แผนเริ่ม " + (DATA.days[0] ? DATA.days[0].date : "-")); }
  });

  document.getElementById("btn-print").addEventListener("click", function(){ window.print(); });

  document.getElementById("btn-reset").addEventListener("click", function(){
    if(!Object.keys(done).length){ toast("ยังไม่มีเครื่องหมายให้ล้าง"); return; }
    if(confirm("ล้างเครื่องหมาย 'ทำแล้ว' ทั้งหมด?")){ done = {}; saveDone(); render(); refreshProgress(); toast("ล้างเครื่องหมายแล้ว"); }
  });

  const dlg = document.getElementById("modal");
  document.getElementById("m-close").addEventListener("click", function(){ dlg.close(); });
  dlg.addEventListener("click", function(e){ if(e.target === dlg) dlg.close(); });
  document.addEventListener("keydown", function(e){ if(e.key === "Escape" && dlg.open) dlg.close(); });
}

function boot(){
  const brand = DATA.brand || {};
  document.getElementById("h-sub").textContent = (brand.campaign || "") + (brand.price ? " · ราคา " + brand.price : "");
  const bl = document.getElementById("h-brand");
  [["สินค้า", brand.product], ["คำสัญญา", brand.promise], ["กลุ่มเป้าหมาย", brand.audience], ["ช่องทางปิดการขาย", brand.primary_checkout]].forEach(function(pair){
    if(!pair[1]) return;
    const s = el("span");
    s.appendChild(el("b", "", pair[0] + ": "));
    s.appendChild(document.createTextNode(pair[1]));
    bl.appendChild(s);
  });
  document.getElementById("foot").textContent =
    "สร้างจาก " + DATA.plan_file + " เมื่อ " + DATA.built_at + " · แผน " + DATA.days.length + " วัน / " + DATA.total_posts +
    " โพสต์ · เครื่องหมาย 'ทำแล้ว' เก็บไว้ในเบราว์เซอร์นี้เท่านั้น (localStorage)";
  bind();
  render();
  refreshProgress();
  loadStatus();
}

boot();
</script>
</body>
</html>
"""


def build(plan: dict, out_path: Path) -> int:
    data_json = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
    # กันข้อมูลที่มี "</script>" ไปปิดสคริปต์ก่อนกำหนด
    data_json = data_json.replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__PLAN_DATA__", data_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return len(html.encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="สร้างหน้าเว็บปฏิทิน 30 วัน (Thai) จาก content/plan.json",
    )
    parser.add_argument("--plan", default=str(PLAN_PATH), help="พาธไฟล์ plan.json (ค่าเริ่มต้น content/plan.json)")
    parser.add_argument("--out", default=str(OUT_PATH), help="พาธไฟล์ HTML ที่จะสร้าง (ค่าเริ่มต้น dashboard/index.html)")
    parser.add_argument("--no-generate", action="store_true", help="ไม่ต้องสร้างแผนใหม่ก่อน ถ้ามี plan.json อยู่แล้ว")
    parser.add_argument("--open", action="store_true", help="เปิดไฟล์ HTML ในเบราว์เซอร์หลังสร้างเสร็จ")
    args = parser.parse_args(argv)

    plan_path = Path(args.plan)
    out_path = Path(args.out)

    if not args.no_generate:
        generator = ROOT / "scripts" / "generate_plan.py"
        if generator.exists():
            result = subprocess.run([sys.executable, str(generator)], cwd=str(ROOT))
            if result.returncode != 0:
                print(f"คำเตือน: generate_plan.py จบด้วยรหัส {result.returncode} — จะใช้ plan.json ที่มีอยู่ต่อ", file=sys.stderr)

    plan = load_plan(plan_path)
    size = build(plan, out_path)

    first = plan["days"][0] if plan["days"] else {}
    print(f"สร้างหน้าเว็บแล้ว: {out_path.relative_to(ROOT)}  ({size:,} ไบต์)")
    print(f"ข้อมูล: {len(plan['days'])} วัน · {plan['total_posts']} โพสต์ · เริ่มวันที่ {first.get('date','-')}")
    print("เปิดดูได้ 3 วิธี:")
    print(f"  1) เปิดไฟล์ตรง ๆ:  {out_path.relative_to(ROOT)}  (อ่าน/คัดลอกได้ แต่ปุ่มโพสต์ใช้ไม่ได้)")
    print("  2) เปิดด้วยเซิร์ฟเวอร์ที่มีปุ่มโพสต์: python3 scripts/dashboard_server.py")
    print(f"  3) เสิร์ฟแบบอ่านอย่างเดียว: python3 -m http.server 3000 --directory {out_path.parent.relative_to(ROOT)}")

    if args.open:
        webbrowser.open(out_path.resolve().as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
