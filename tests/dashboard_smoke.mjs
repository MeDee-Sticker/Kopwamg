/**
 * ทดสอบหน้าเว็บ dashboard/index.html แบบไม่ต้องใช้เบราว์เซอร์
 * - รันสคริปต์ที่ฝังใน HTML ด้วย DOM จำลองขนาดเล็ก
 * - ตรวจว่าปฏิทินเรนเดอร์ครบ 30 วัน × 3 แพลตฟอร์ม
 * - ตรวจว่าปุ่ม "คัดลอก" ส่งข้อความตรงกับ content/plan.json จริง
 *
 * ใช้: node tests/dashboard_smoke.mjs
 */
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const htmlPath = path.join(root, "dashboard", "index.html");

/* ---------- DOM จำลอง ---------- */
let lastCopied = null;

class El {
  constructor(tag) {
    this.tagName = String(tag || "div").toUpperCase();
    this.children = [];
    this.parent = null;
    this.classes = new Set();
    this.style = {};
    this.attrs = {};
    this.listeners = new Map();
    this.value = "";
    this.checked = false;
    this.open = false;
    this._text = "";
    const self = this;
    this.classList = {
      add: (...c) => c.forEach((x) => self.classes.add(x)),
      remove: (...c) => c.forEach((x) => self.classes.delete(x)),
      contains: (c) => self.classes.has(c),
      toggle: (c) => (self.classes.has(c) ? self.classes.delete(c) : self.classes.add(c)),
    };
  }
  get className() { return [...this.classes].join(" "); }
  set className(v) { this.classes = new Set(String(v).split(/\s+/).filter(Boolean)); }
  appendChild(child) { child.parent = this; this.children.push(child); return child; }
  removeChild(child) {
    const i = this.children.indexOf(child);
    if (i >= 0) this.children.splice(i, 1);
    return child;
  }
  setAttribute(k, v) { this.attrs[k] = v; }
  getAttribute(k) { return this.attrs[k]; }
  addEventListener(type, fn) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(fn);
  }
  dispatch(type, ev = {}) {
    (this.listeners.get(type) || []).forEach((fn) => fn(ev));
    const prop = this["on" + type];
    if (typeof prop === "function") prop(ev);
  }
  showModal() { this.open = true; }
  close() { this.open = false; }
  select() {}
  setSelectionRange() {}
  focus() {}
  get textContent() {
    return this._text + this.children.map((c) => c.textContent).join("");
  }
  set textContent(v) { this._text = String(v); this.children = []; }
  set innerHTML(_v) { this._text = ""; this.children = []; }
  get innerHTML() { return ""; }
  // ค้นหาแบบง่ายพอสำหรับการทดสอบ
  getAll(pred, out = []) {
    if (pred(this)) out.push(this);
    this.children.forEach((c) => c.getAll(pred, out));
    return out;
  }
}

const registry = new Map();
function byId(id) {
  if (!registry.has(id)) registry.set(id, new El("div"));
  return registry.get(id);
}

const body = new El("body");
const document = {
  body,
  getElementById: (id) => byId(id),
  createElement: (tag) => new El(tag),
  createTextNode: (text) => { const n = new El("#text"); n.textContent = text; return n; },
  addEventListener: () => {},
  execCommand: (cmd) => {
    if (cmd === "copy") {
      const ta = body.children[body.children.length - 1];
      lastCopied = ta && typeof ta.value === "string" ? ta.value : null;
      return true;
    }
    return false;
  },
};

const store = new Map();
const localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k),
};

const window = { isSecureContext: false, print: () => {} };

// fetch จำลองสำหรับ /api/status และ /api/post (ของจริงคือ scripts/dashboard_server.py)
const fetchCalls = [];
let statusReply = {
  api: true,
  live_allowed: true,
  credentials_ready: true,
  published: {},
  scheduled: {},
  drafts: {},
  schedule_window: {
    "1": { at: "2026-10-16T12:00:00+07:00", window: "past" },
    "2": { at: "2026-10-17T12:00:00+07:00", window: "ok" },
  },
};
let postReply = null;
let scheduleReply = null;
let draftReply = null;
const fetch = async (url, opts = {}) => {
  const call = { url, method: (opts.method || "GET"), body: opts.body ? JSON.parse(opts.body) : null };
  fetchCalls.push(call);
  if (String(url).endsWith("/api/status")) {
    return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(statusReply)) };
  }
  if (String(url).endsWith("/api/post")) {
    const reply = typeof postReply === "function" ? postReply(call.body) : postReply;
    return { ok: true, status: 200, json: async () => reply };
  }
  if (String(url).endsWith("/api/schedule")) {
    const reply = typeof scheduleReply === "function" ? scheduleReply(call.body) : scheduleReply;
    return { ok: true, status: 200, json: async () => reply };
  }
  if (String(url).endsWith("/api/draft")) {
    const reply = typeof draftReply === "function" ? draftReply(call.body) : draftReply;
    return { ok: true, status: 200, json: async () => reply };
  }
  return { ok: false, status: 404, json: async () => ({}) };
};

const sandbox = {
  document,
  window,
  navigator: {},
  localStorage,
  fetch,
  Option: function Option(text, value) { return { text, value }; },
  setTimeout: () => 0,
  clearTimeout: () => {},
  confirm: () => false,
  console,
  Date,
  Math,
  JSON,
  Object,
  String,
  Number,
  Array,
};
sandbox.globalThis = sandbox;

/* ---------- โหลด HTML และรันสคริปต์ที่ฝังอยู่ ---------- */
const html = fs.readFileSync(htmlPath, "utf8");
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) throw new Error("ไม่พบ <script> ใน dashboard/index.html");
vm.createContext(sandbox);
vm.runInContext(scriptMatch[1], sandbox, { filename: "dashboard-inline.js" });

/* ---------- ตรวจผล ---------- */
const plan = JSON.parse(fs.readFileSync(path.join(root, "content", "plan.json"), "utf8"));
const failures = [];
const check = (name, ok, extra = "") => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${extra ? " — " + extra : ""}`);
  if (!ok) failures.push(name);
};

const flush = () => new Promise((resolve) => setImmediate(resolve));
await flush(); // ให้ loadStatus() จาก boot() ทำงานจนจบ

const main = byId("main");
const dayCards = main.getAll((n) => n.classes.has("day"));
const chips = main.getAll((n) => n.classes.has("chip"));
const weekSections = main.getAll((n) => n.classes.has("week"));

check("เรนเดอร์ 4 สัปดาห์", weekSections.length === 4, `ได้ ${weekSections.length}`);
check("เรนเดอร์ 30 การ์ดวัน", dayCards.length === 30, `ได้ ${dayCards.length}`);
check("เรนเดอร์ 90 ชิปแพลตฟอร์ม", chips.length === 90, `ได้ ${chips.length}`);
check(
  "การ์ดวันแรกมีเลขวันและหัวข้อ",
  dayCards[0].textContent.includes("วันที่ 1") &&
    dayCards[0].textContent.includes(plan.rows[0].theme),
  dayCards[0].textContent.slice(0, 60),
);
check(
  "แถบความคืบหน้าเริ่มที่ 0/90",
  byId("h-progress").textContent.includes("0 / 90"),
  byId("h-progress").textContent,
);

// เปิดการ์ดวันแรก แล้วตรวจว่าเนื้อหาตรงกับแผน และปุ่ม "คัดลอก" ได้ข้อความจริง
dayCards[0].dispatch("click");
check("คลิกการ์ดแล้วป๊อปอัปเปิด", byId("modal").open === true);

const day1 = plan.rows.filter((r) => r.day === 1);
const fb = day1.find((r) => r.platform === "facebook");
const modalBody = byId("m-body");
const copyButtons = modalBody.getAll((n) => n.tagName === "BUTTON" && n.textContent === "คัดลอก");
check("มีปุ่มคัดลอกในป๊อปอัป", copyButtons.length >= 2, `ได้ ${copyButtons.length}`);
check(
  "เนื้อหาในป๊อปอัปตรงกับแคปชัน Facebook ใน plan.json",
  modalBody.textContent.includes(fb.caption.split("\n")[0]),
);

// หาปุ่มคัดลอกของบล็อก "แคปชัน" โดยตรง (ไม่ใช่ปุ่มของ Hook)
function copyButtonFor(label) {
  const head = byId("m-body").getAll(
    (n) => n.classes.has("blockhead") && n.textContent.includes(label),
  )[0];
  return head && head.children.find((c) => c.tagName === "BUTTON");
}
const captionBtn = copyButtonFor("แคปชัน");
check("พบบล็อกแคปชันพร้อมปุ่มคัดลอก", !!captionBtn);
captionBtn.dispatch("click");
check(
  "กดปุ่มคัดลอกแล้วได้แคปชัน Facebook ตรงกับ plan.json",
  lastCopied === fb.caption,
  lastCopied ? `ได้ ${lastCopied.slice(0, 40)}…` : "ไม่ได้ข้อความ",
);

// TikTok: สลับแท็บแล้วตรวจว่าคัดลอกสคริปต์วิดีโอได้ตรงกับแผน
const tiktokTab = byId("m-tabs").getAll((n) => n.classes.has("tab") && n.classes.has("tiktok"))[0];
check("มีแท็บ TikTok ในป๊อปอัป", !!tiktokTab);
tiktokTab.dispatch("click");
const tt = day1.find((r) => r.platform === "tiktok");
const scriptBtn = copyButtonFor("สคริปต์วิดีโอ");
check("พบบล็อกสคริปต์วิดีโอพร้อมปุ่มคัดลอก", !!scriptBtn);
scriptBtn.dispatch("click");
check("กดคัดลอกสคริปต์ TikTok แล้วได้ข้อความตรงกับ plan.json", lastCopied === tt.notes);

// ปุ่ม "คัดลอกโพสต์นี้ทั้งหมด" ต้องได้แคปชัน + สคริปต์ของแท็บที่เปิดอยู่ (ตอนนี้คือ TikTok)
byId("m-copy-all").dispatch("click");
const tabTxt = lastCopied || "";
check(
  "คัดลอกโพสต์นี้ทั้งหมด ได้แคปชันและสคริปต์ของแท็บที่เปิด",
  tabTxt.includes(tt.caption) && tabTxt.includes(tt.notes),
);

// ปุ่ม "คัดลอกทุกแพลตฟอร์มของวันนี้" ต้องมีครบ 3 ช่องทาง
const shopee = day1.find((r) => r.platform === "shopee");
byId("m-copy-plan").dispatch("click");
const dayTxt = lastCopied || "";
check(
  "คัดลอกทุกแพลตฟอร์มของวันนี้ครบ 3 ช่องทาง",
  dayTxt.includes("[Facebook]") && dayTxt.includes("[TikTok]") && dayTxt.includes("[Shopee]"),
);
check(
  "ข้อความที่คัดลอกมีแคปชัน Facebook และงาน Shopee จริง",
  dayTxt.includes(fb.caption) && dayTxt.includes(shopee.title),
);

// ทำเครื่องหมาย "ทำแล้ว" แล้วความคืบหน้าต้องขยับ และบันทึกลง localStorage
byId("m-done").checked = true;
byId("m-done").dispatch("change");
check("ทำเครื่องหมายแล้วความคืบหน้าเป็น 1 / 90", byId("h-progress").textContent.includes("1 / 90"), byId("h-progress").textContent);
const saved = JSON.parse(localStorage.getItem("kopwang.done.v1") || "{}");
check("บันทึกสถานะทำแล้วลง localStorage", saved["1:tiktok"] === 1, JSON.stringify(saved));

// ตัวกรอง: เลือก TikTok อย่างเดียว ต้องเหลือ 30 การ์ด
const sel = byId("f-platform");
sel.value = "tiktok";
sel.dispatch("change");
check(
  "กรองเฉพาะ TikTok เหลือ 30 การ์ด",
  byId("main").getAll((n) => n.classes.has("day")).length === 30,
);
sel.value = "all";
sel.dispatch("change");

// ค้นหา: คำที่อยู่ในแคปชันของวันอื่น ต้องเจอเพียงบางวัน
const search = byId("f-search");
search.value = "30 วัน";
search.dispatch("input");
const found = byId("main").getAll((n) => n.classes.has("day")).length;
check("ค้นหาแล้วได้ผลลัพธ์แบบจำกัดวง (≤30 วัน)", found > 0 && found <= 30, `ได้ ${found} วัน`);
search.value = "";
search.dispatch("input");

/* ---------- ปุ่มสั่งโพสต์ Facebook ---------- */
check("boot() เรียก /api/status หนึ่งครั้ง", fetchCalls.filter((c) => c.url.endsWith("/api/status")).length === 1);
check("กล่องโพสต์แสดงโทเคนพร้อมใช้", byId("m-post-status").textContent.includes("โทเคน: พร้อม"), byId("m-post-status").textContent);
check("ปุ่มโพสต์จริงกดได้เมื่อเซิร์ฟเวอร์เปิด --live และ .env พร้อม", byId("m-post-live").disabled === false);

// สลับกลับแท็บ Facebook ของวันที่ 1 แล้วทดลองโพสต์ (dry-run)
const day1Card = byId("main").getAll((n) => n.classes.has("day"))[0];
day1Card.dispatch("click");
byId("m-tabs").getAll((n) => n.classes.has("tab") && n.classes.has("facebook"))[0].dispatch("click");
check("เปิดแท็บ Facebook แล้วกล่องโพสต์โผล่", byId("m-postbox").hidden === false);

postReply = { ok: true, exit_code: 0, mode: "dry-run", action: "ทดลอง (ไม่ยิง API)", day: 1, output: "โหมดทดลอง (dry-run) — เติม --live เพื่อยิงเข้า Graph API จริง" };
byId("m-post-dry").dispatch("click");
await flush();
const dryCall = fetchCalls.filter((c) => c.url.endsWith("/api/post")).pop();
check("ปุ่มทดลองโพสต์ยิง POST /api/post ของวันที่ 1 แบบ live=false", !!dryCall && dryCall.method === "POST" && dryCall.body.day === 1 && dryCall.body.live === false, JSON.stringify(dryCall));
check("แสดงผลลัพธ์จากสคริปต์ในกล่องข้อความ", byId("m-post-out").textContent.includes("โหมดทดลอง"), byId("m-post-out").textContent.slice(0, 60));

// โพสต์จริง (จำลอง) ต้องผ่านด่าน confirm และบันทึกว่าโพสต์แล้ว
sandbox.confirm = () => true;
postReply = (body) => ({
  ok: true,
  exit_code: 0,
  mode: body.live ? "live" : "dry-run",
  action: body.live ? "โพสต์จริง" : "ทดลอง (ไม่ยิง API)",
  day: body.day,
  output: body.live ? "    ✅ โพสต์แล้ว: https://facebook.com/123_456" : "โหมดทดลอง",
  status: {
    api: true,
    live_allowed: true,
    credentials_ready: true,
    published: body.live ? { [String(body.day)]: { post_id: "123_456", at: "2026-10-16T12:00:00+07:00" } } : {},
    scheduled: {},
  },
});
byId("m-post-live").dispatch("click");
await flush();
const liveCall = fetchCalls.filter((c) => c.url.endsWith("/api/post")).pop();
check("ปุ่มโพสต์จริงยิง POST ของวันที่ 1 แบบ live=true", !!liveCall && liveCall.body.day === 1 && liveCall.body.live === true, JSON.stringify(liveCall));
check("โพสต์สำเร็จแล้วทำเครื่องหมายว่าทำแล้ว", JSON.parse(localStorage.getItem("kopwang.done.v1"))["1:facebook"] === 1);
check("สถานะหลังโพสต์บอกว่าโพสต์แล้ว", byId("m-post-status").textContent.includes("โพสต์แล้ว"), byId("m-post-status").textContent);
check(
  "การ์ดวันที่ 1 มีป้ายว่าโพสต์แล้ว",
  byId("main").getAll((n) => n.classes.has("day"))[0].getAll((n) => n.classes.has("published-badge")).length === 1,
);

/* ---------- ปุ่มตั้งเวลาโพสต์ล่วงหน้า ---------- */
const day2Card = byId("main").getAll((n) => n.classes.has("day"))[1];
day2Card.dispatch("click");
byId("m-tabs").getAll((n) => n.classes.has("tab") && n.classes.has("facebook"))[0].dispatch("click");
check("เปิดวันที่ 2 แล้วกล่องตั้งเวลาแสดงกำหนดเวลาจากแผน", byId("m-sched-status").textContent.includes("2026-10-17 12:00"), byId("m-sched-status").textContent);
check("ปุ่มตั้งเวลาจริงกดได้เมื่อกำหนดเวลายังอยู่ในช่วงที่ Meta รับ", byId("m-sched-live").disabled === false, byId("m-sched-live").title);

const scheduleCalls = () => fetchCalls.filter((c) => c.url.endsWith("/api/schedule"));
scheduleReply = { ok: true, exit_code: 0, mode: "dry-run", action: "ทดลองตั้งเวลา (ไม่ยิง API)", day: 2, output: "--- วันที่ 2 · ... กำหนดโพสต์: 2026-10-17T12:00:00+07:00 ---" };
byId("m-sched-dry").dispatch("click");
await flush();
const drySchedule = scheduleCalls().pop();
check(
  "ปุ่มทดลองตั้งเวลายิง POST /api/schedule ของวันที่ 2 แบบ live=false",
  !!drySchedule && drySchedule.method === "POST" && drySchedule.body.day === 2 && drySchedule.body.live === false,
  JSON.stringify(drySchedule),
);
check("แสดงผลลัพธ์การทดลองตั้งเวลาในกล่องข้อความ", byId("m-post-out").textContent.includes("กำหนดโพสต์"), byId("m-post-out").textContent.slice(0, 60));

// ตั้งเวลาจริง (จำลอง) → ต้องถามยืนยัน, ไม่ทำเครื่องหมายว่าทำแล้ว, และขึ้นป้าย "ตั้งเวลาไว้"
scheduleReply = (body) => ({
  ok: true,
  exit_code: 0,
  mode: body.live ? "live" : "dry-run",
  action: body.live ? "ตั้งเวลาโพสต์" : "ทดลองตั้งเวลา (ไม่ยิง API)",
  day: body.day,
  output: body.live ? "    🗓  ตั้งเวลาไว้ 2026-10-17 12:00 (โพสต์ id 789_012)" : "โหมดทดลอง",
  status: {
    api: true,
    live_allowed: true,
    credentials_ready: true,
    published: {},
    scheduled: body.live ? { [String(body.day)]: { post_id: "789_012", scheduled_for: "2026-10-17T12:00:00+07:00" } } : {},
    schedule_window: statusReply.schedule_window,
  },
});
byId("m-sched-live").dispatch("click");
await flush();
const liveSchedule = scheduleCalls().pop();
check("ปุ่มตั้งเวลาจริงยิง POST /api/schedule ของวันที่ 2 แบบ live=true", !!liveSchedule && liveSchedule.body.day === 2 && liveSchedule.body.live === true, JSON.stringify(liveSchedule));
check("ตั้งเวลาแล้วไม่ทำเครื่องหมายว่าทำแล้ว", !JSON.parse(localStorage.getItem("kopwang.done.v1") || "{}")["2:facebook"]);
check("กล่องสถานะบอกว่าตั้งเวลาไว้แล้ว", byId("m-sched-status").textContent.includes("ตั้งเวลาไว้ 2026-10-17 12:00"), byId("m-sched-status").textContent);
check("ปุ่มตั้งเวลาถูกล็อกหลังตั้งเวลาแล้ว", byId("m-sched-live").disabled === true && byId("m-sched-live").title.includes("ตั้งเวลาไว้แล้ว"), byId("m-sched-live").title);
check(
  "การ์ดวันที่ 2 ขึ้นป้าย \"FB ตั้งเวลาไว้\" ไม่ใช่ \"โพสต์แล้ว\"",
  byId("main").getAll((n) => n.classes.has("day"))[1].getAll((n) => n.classes.has("scheduled-badge"))[0].textContent.includes("ตั้งเวลาไว้"),
);

/* ---------- ปุ่มสร้างโพสต์ร่าง (unpublished) ---------- */
const draftCalls = () => fetchCalls.filter((c) => c.url.endsWith("/api/draft"));
check(
  "กล่องสร้างร่างบอกว่าจะไม่ขึ้นเพจจนกว่าจะกดเผยแพร่เอง",
  byId("m-draft-status").textContent.includes("ไม่ขึ้นเพจ"),
  byId("m-draft-status").textContent,
);
check(
  "ปุ่มสร้างร่างกดได้เมื่อเซิร์ฟเวอร์เปิด --live และ .env พร้อม",
  byId("m-draft-live").disabled === false,
  byId("m-draft-live").title,
);

draftReply = {
  ok: true, exit_code: 0, mode: "dry-run", action: "ทดลองสร้างร่าง (ไม่ยิง API)", day: 2,
  output: "โหมด: unpublished — published=false + unpublished_content_type=DRAFT (ไม่ขึ้นเพจ)",
};
byId("m-draft-dry").dispatch("click");
await flush();
const dryDraft = draftCalls().pop();
check(
  "ปุ่มทดลองสร้างร่างยิง POST /api/draft ของวันที่ 2 แบบ live=false",
  !!dryDraft && dryDraft.method === "POST" && dryDraft.body.day === 2 && dryDraft.body.live === false,
  JSON.stringify(dryDraft),
);
check(
  "แสดงผลลัพธ์โหมด unpublished ในกล่องข้อความ",
  byId("m-post-out").textContent.includes("unpublished_content_type=DRAFT"),
  byId("m-post-out").textContent.slice(0, 60),
);

// ต้องถามยืนยันก่อนสร้าง — ถ้ายกเลิก ต้องไม่ยิงคำขอ
sandbox.confirm = () => false;
byId("m-draft-live").dispatch("click");
await flush();
check("ยกเลิกในกล่องยืนยันแล้วไม่ยิงคำขอสร้างร่าง", draftCalls().length === 1, `ได้ ${draftCalls().length} คำขอ`);

// ยืนยันแล้วสร้างร่างจริง (จำลอง) → ไม่ทำเครื่องหมายว่าทำแล้ว และขึ้นสถานะมีร่าง
sandbox.confirm = () => true;
draftReply = (body) => ({
  ok: true,
  exit_code: 0,
  mode: body.live ? "live" : "dry-run",
  action: body.live ? "สร้างโพสต์ร่าง" : "ทดลองสร้างร่าง (ไม่ยิง API)",
  day: body.day,
  output: body.live ? "    ✅ ตรวจแล้ว: is_published=false — ยังไม่ขึ้นเพจ" : "โหมดทดลอง",
  status: {
    api: true, live_allowed: true, credentials_ready: true,
    published: {}, scheduled: {},
    drafts: body.live ? { [String(body.day)]: { post_id: "456_789", is_published: false } } : {},
    schedule_window: statusReply.schedule_window,
  },
});
byId("m-draft-live").dispatch("click");
await flush();
const liveDraft = draftCalls().pop();
check(
  "ปุ่มสร้างร่างจริงยิง POST /api/draft ของวันที่ 2 แบบ live=true",
  !!liveDraft && liveDraft.body.day === 2 && liveDraft.body.live === true,
  JSON.stringify(liveDraft),
);
check("สร้างร่างแล้วไม่ทำเครื่องหมายว่าทำแล้ว", !JSON.parse(localStorage.getItem("kopwang.done.v1") || "{}")["2:facebook"]);
check(
  "กล่องสถานะบอกร่าง unpublished พร้อม post id",
  byId("m-draft-status").textContent.includes("มีร่าง unpublished") && byId("m-draft-status").textContent.includes("456_789"),
  byId("m-draft-status").textContent,
);
check(
  "ปุ่มสร้างร่างถูกล็อกหลังมีร่างแล้ว (กันสร้างซ้ำ)",
  byId("m-draft-live").disabled === true && byId("m-draft-live").title.includes("มีร่าง"),
  byId("m-draft-live").title,
);

// วันที่เลยกำหนดแล้ว ต้องตั้งเวลาไม่ได้ และชี้ไปที่ปุ่มโพสต์ทันที
statusReply = {
  api: true, live_allowed: true, credentials_ready: true, published: {}, scheduled: {}, drafts: {},
  schedule_window: { "2": { at: "2026-10-01T12:00:00+07:00", window: "past" } },
};
sandbox.loadStatus();
await flush();
check("กำหนดเวลาเลยแล้ว → ปุ่มตั้งเวลาถูกล็อกและชี้ไปที่ปุ่มโพสต์ทันที", byId("m-sched-live").disabled === true && byId("m-sched-live").title.includes("ใช้ปุ่มโพสต์ขึ้นเพจทันที"), byId("m-sched-live").title);
check("สถานะตั้งเวลาบอกว่าเลยเวลาแล้ว", byId("m-sched-status").textContent.includes("เลยเวลา"), byId("m-sched-status").textContent);

// ถ้าเซิร์ฟเวอร์ไม่ได้เปิด --live ปุ่มโพสต์จริงต้องกดไม่ได้
statusReply = {
  api: true, live_allowed: false, credentials_ready: true, published: {}, scheduled: {}, drafts: {},
  schedule_window: { "2": { at: "2026-10-17T12:00:00+07:00", window: "ok" } },
};
sandbox.loadStatus();
await flush();
check("เซิร์ฟเวอร์ไม่เปิด --live → ปุ่มโพสต์จริงถูกล็อกพร้อมคำอธิบาย", byId("m-post-live").disabled === true && byId("m-post-live").title.includes("--live"), byId("m-post-live").title);
check("กล่องโพสต์บอกว่าเป็นโหมดทดลองเท่านั้น", byId("m-post-status").textContent.includes("ทดลองเท่านั้น"));
check("เซิร์ฟเวอร์ไม่เปิด --live → ปุ่มตั้งเวลาก็ถูกล็อก", byId("m-sched-live").disabled === true && byId("m-sched-live").title.includes("--live"), byId("m-sched-live").title);
check("เซิร์ฟเวอร์ไม่เปิด --live → ปุ่มสร้างร่างก็ถูกล็อก", byId("m-draft-live").disabled === true && byId("m-draft-live").title.includes("--live"), byId("m-draft-live").title);

// ถ้าไม่มีโทเคนใน .env ปุ่มโพสต์จริงก็ต้องถูกล็อก
statusReply = {
  api: true, live_allowed: true, credentials_ready: false, published: {}, scheduled: {}, drafts: {},
  schedule_window: { "2": { at: "2026-10-17T12:00:00+07:00", window: "ok" } },
};
sandbox.loadStatus();
await flush();
check("ไม่มีโทเคนใน .env → ปุ่มโพสต์จริงถูกล็อก", byId("m-post-live").disabled === true && byId("m-post-live").title.includes(".env"), byId("m-post-live").title);
check("ไม่มีโทเคนใน .env → ปุ่มตั้งเวลาก็ถูกล็อก", byId("m-sched-live").disabled === true && byId("m-sched-live").title.includes(".env"), byId("m-sched-live").title);
check("ไม่มีโทเคนใน .env → ปุ่มสร้างร่างก็ถูกล็อก", byId("m-draft-live").disabled === true && byId("m-draft-live").title.includes(".env"), byId("m-draft-live").title);

console.log(failures.length ? `\n${failures.length} รายการไม่ผ่าน` : "\nผ่านทั้งหมด");
process.exit(failures.length ? 1 : 0);
