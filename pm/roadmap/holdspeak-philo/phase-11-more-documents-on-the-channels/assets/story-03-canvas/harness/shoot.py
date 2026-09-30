"""PHILO-11-03 canvases A-E and T1-T3: the SEND well on every document.

Everything is live except the stated shim: a REAL hub (scripts/graph_walk.py
serve) on an isolated HOME (tempfile.mkdtemp, removed when the run ends),
seeded through its real HTTP routes and, for the records no route makes (a
recorded meeting with its stored intelligence, its decision records),
through the product's DB layer (seed_db.py); and the PRODUCT app served twice
by vite (harness/vite.config.mjs):
  - TODAY:    the product as on this branch (no seat, no shim);
  - PROPOSAL: the seats (P11Hosts.tsx at named anchors), the species
              (DocSendWell.tsx), Slack in Destinations, the removals, and
              harness/shim.ts (the unbuilt wire, stated there).
Nothing leaves the machine: the shim's dispatch is a stand-in; the Slack
webhook in config.json (for the TODAY boards) is never called.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    <python with playwright> pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-03-canvas/harness/shoot.py

Shots: ../shots/<board>-<width>.png at 1440x900 and 393x852 (device scale 2);
facts.json beside them. Each width runs on its own hub and HOME.
ONLY_WIDTH=393 limits the run to one width. Exit 2 on a named element off
screen, a failed assertion, or two identical shots in one width.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
SHOTS = CANVAS / "shots"
REPO = CANVAS.parents[5]
WEB = REPO / "web"
PY = os.environ.get("CANVAS_PYTHON") or str(REPO / ".venv/bin/python")
TOKEN = "philo11-canvas"
ALL_WIDTHS = [(1440, 900), (393, 852)]
WIDTHS = [w for w in ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
PROJECT = "Payments ledger cutover"
FAKE_WEBHOOK = "https://hooks.slack.com/services/T0CANVAS/B0CANVAS/never-called"
STALE = ["OLD VERSION", "STALE", "OUTDATED", "PREVIOUS VERSION", "NEWER VERSION", "CHANGED SINCE"]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, headers: dict[str, str] | None = None, timeout: float = 120) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=2) as r:
                if r.status < 500:
                    return
        except Exception:
            time.sleep(0.4)
    raise RuntimeError(f"not up: {url}")


def hub_api(base: str, method: str, path: str, body=None):
    req = urllib.request.Request(
        f"{base}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


# ── rendered facts over the frame (a desk window, or the Chair) ──────────
FACTS = r"""(anchorSel) => {
  const anchor = document.querySelector(anchorSel);
  const win = anchor ? (anchor.closest('.desk-window') || anchor.closest('.chair') || document.body) : null;
  if (!win) return {window: false};
  const GLYPH = /^[●○◆▸▾✓✗⚠—↻ℹ«»·▤›×\s]+$/;
  const small = {proposal: [], inherited: []};
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || GLYPH.test(t)) continue;
    const el = n.parentElement; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none') continue;
    // The section head species (SurfaceSection, surface.css) draws its head at 10 px in a pullout, on the
    // host's own heads too (DECISION CONTEXT): recorded as the species' size, not the proposal's.
    if (parseFloat(cs.fontSize) < 12) (el.closest('[data-p11]') && !el.closest('.surface-section-head') ? small.proposal : small.inherited).push({text: t.slice(0, 40), fs: parseFloat(cs.fontSize), head: !!el.closest('.surface-section-head')});
  }
  const raw = [...win.querySelectorAll('button')].filter((b) => !String(b.className).includes('btn') && b.getBoundingClientRect().width);
  const rawIn = (p) => raw.filter((b) => !!b.closest('[data-p11]') === p).map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30));
  const wells = [...win.querySelectorAll('[data-p11=well]')];
  const text = (sel) => [...win.querySelectorAll(sel)].map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  const wellText = wells.map((w) => w.innerText).join('\n') + '\n' + text('[data-p11=history]').join('\n');
  const body = win.querySelector('.desk-surface-body') || win;
  const winRect = win.getBoundingClientRect();
  return {
    window: true,
    window_width: Math.round(winRect.width),
    wells: wells.map((w) => w.dataset.doc),
    destinations: text('[data-p11=well] [data-testid=destination-row]'),
    prepared: text('[data-p11=well] [data-testid=prepared-row], [data-p11=well] [data-testid=prepared-result]'),
    preview_fields: text('[data-p11=well] [data-testid=send-preview-field]'),
    preview_body: text('[data-p11=well] [data-testid=send-preview-body]').join('\n').slice(0, 4000),
    outcomes: [...win.querySelectorAll('[data-p11=well] [data-testid=send-refused], [data-p11=well] [data-testid=preview-refused], [data-p11=well] [data-testid=preview-failed], [data-p11=well] [data-testid=send-sent]')].map((e) => ({tid: e.dataset.testid, text: e.innerText.replace(/\s+/g, ' ').trim(), code: e.dataset.code || null})),
    history_head: (() => { const s = win.querySelector('[data-p11=history] .surface-section-head, [data-p11=history] h3'); return s ? s.innerText.trim() : null; })(),
    history: text('[data-p11=history] [data-testid=history-row]'),
    egress_chips: [...win.querySelectorAll('[data-p11] .gadget-chip-egress')].map((e) => e.innerText.trim()),
    proof_links_on_slack: [...win.querySelectorAll('[data-p11] [data-testid=proof][data-href]')].filter((e) => /hooks\.slack|slack\.com/.test(e.dataset.href)).length,
    mark_delivered_in_new_kind: [...wells].filter((w) => !String(w.dataset.doc).startsWith('project_update:')).some((w) => /Mark delivered/.test(w.closest('[data-p11=wells]')?.innerText || '')),
    stale_words: %STALE%.filter((wd) => wellText.toUpperCase().includes(wd)),
    no_answer_shown: /NO ANSWER/.test(wellText),
    transcript_sentinel: /TRANSCRIPT-SENTINEL-7Q/.test(wellText),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
    small_text: small,
    raw_buttons: {proposal: rawIn(true), inherited: rawIn(false)},
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
    body_overflow_x: body ? body.scrollWidth > body.clientWidth + 1 : null,
  };
}""".replace("%STALE%", json.dumps(STALE))

# The on-screen law (Phase 9/10): each board's NAMED elements are in the
# viewport, inside every clipping ancestor, and on top at their centre and two
# inner corners.
VISIBLE = r"""(sels) => sels.map((sel) => {
  const els = [...document.querySelectorAll(sel)].filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.height; });
  if (!els.length) return {sel, ok: false, why: 'absent'};
  const e = els[0]; const r = e.getBoundingClientRect();
  let top = 0, left = 0, bottom = innerHeight, right = innerWidth;
  for (let a = e.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowY + ' ' + cs.overflowX)) {
      const ar = a.getBoundingClientRect();
      top = Math.max(top, ar.top); bottom = Math.min(bottom, ar.bottom); left = Math.max(left, ar.left); right = Math.min(right, ar.right);
    }
  }
  // A block taller than its scroller (a preview body, a history) counts by its START: its first
  // 40 px on screen, whole width; anything shorter must be whole.
  const band = Math.min(r.height, 40);
  const inside = r.top >= top - 1 && r.top + band <= bottom + 1 && r.left >= left - 1 && r.right <= right + 1
    && (r.height <= 40 || r.bottom <= bottom + 1 || r.height > bottom - top);
  const yb = r.top + band / 2;
  const pts = [[r.left + r.width / 2, yb], [r.left + 2, r.top + 2], [r.right - 2, r.top + band - 2]];
  const hit = pts.every(([x, y]) => { const h = document.elementFromPoint(x, y); return !!h && (e.contains(h) || h.contains(e)); });
  return {sel, ok: inside && hit, why: inside ? (hit ? '' : 'covered') : 'clipped', tall: r.height > bottom - top, text: (e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, 60)};
})"""

# The pointer pass (UX-CANON C): every proposal control (Button, ledger line,
# select, input), nine points each -- the painted face at 1440, the 44 x 44
# target at 393 -- by elementFromPoint AND a real pointer move.
CONTROLS = r"""(anchorSel) => {
  const anchor = document.querySelector(anchorSel);
  const win = anchor ? (anchor.closest('.desk-window') || anchor.closest('.chair') || document.body) : null;
  if (!win) return [];
  document.querySelectorAll('[data-probe]').forEach((e) => e.removeAttribute('data-probe'));
  window.__scrollSnap = [...document.querySelectorAll('*')].filter((e) => e.scrollTop || e.scrollLeft).map((e) => [e, e.scrollTop, e.scrollLeft]);
  window.__pm = null;
  if (!window.__pmHooked) { document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, true); window.__pmHooked = true; }
  const btns = [...win.querySelectorAll('[data-p11] .btn, [data-p11] .surface-ledger-line, [data-p11] select, [data-p11] input:not([type=hidden]):not([type=checkbox])')]
    .filter((b) => { const r = b.getBoundingClientRect(); return r.width && r.bottom > 0 && r.top < innerHeight; });
  return btns.map((b, i) => { b.dataset.probe = String(i); return {i, text: (b.innerText || b.getAttribute('aria-label') || b.value || '').trim().slice(0, 30),
    html: b.outerHTML.slice(0, 140), opacity: getComputedStyle(b).opacity}; });
}"""
POINTS9 = r"""([i, width]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  const r = b.getBoundingClientRect();
  const cy = r.top + r.height / 2, cx = r.left + r.width / 2;
  const w = width <= 420 ? Math.max(44, r.width) : r.width, h = width <= 420 ? Math.max(44, r.height) : r.height;
  const L = cx - w / 2 + 1, R = cx + w / 2 - 1, T = cy - h / 2 + 1, B = cy + h / 2 - 1;
  let top = 0, left = 0, bottom = innerHeight, right = innerWidth;
  for (let a = b.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowY + ' ' + cs.overflowX)) {
      const ar = a.getBoundingClientRect();
      top = Math.max(top, ar.top); bottom = Math.min(bottom, ar.bottom); left = Math.max(left, ar.left); right = Math.min(right, ar.right);
    }
  }
  // Only a control the shot shows whole is measured (a control cut by its scroller is off this board).
  const inview = r.top >= top - 1 && r.bottom <= bottom + 1 && r.left >= left - 1 && r.right <= right + 1;
  return {points: [[cx, cy], [cx, T], [R, cy], [cx, B], [L, cy], [L, T], [R, T], [L, B], [R, B]], inview};
}"""
HIT = r"""([i, x, y]) => { const b = document.querySelector(`[data-probe="${i}"]`); const el = document.elementFromPoint(x, y);
  let bar = false;
  for (let a = el; a && !bar; a = a.parentElement) { const p = getComputedStyle(a).position; if ((p === 'sticky' || p === 'fixed') && !a.closest('[data-p11]')) bar = true; }
  return {own: !!el && b.contains(el), bar: !!el && !b.contains(el) && bar}; }"""
PM_OWNED = r"""([i]) => { const b = document.querySelector(`[data-probe="${i}"]`); return !!window.__pm && b.contains(window.__pm); }"""
RESTORE = r"""() => { for (const [e, t, l] of (window.__scrollSnap || []).reverse()) { e.scrollTop = t; e.scrollLeft = l; } }"""


def pointer_pass(page, width: int, anchor: str) -> dict:
    owned, missed, behind = 0, [], []
    for c in page.evaluate(CONTROLS, anchor):
        geo = page.evaluate(POINTS9, [c["i"], width])
        if not geo["inview"]:
            continue   # only what the shot shows
        bad, where, under = 0, [], 0
        for x, y in geo["points"]:
            if not (0 <= x < page.viewport_size["width"] and 0 <= y < page.viewport_size["height"]):
                bad += 1
                continue
            h = page.evaluate(HIT, [c["i"], x, y])
            efp = h["own"]
            under += 1 if h["bar"] else 0
            page.mouse.move(x, y)
            pm = page.evaluate(PM_OWNED, [c["i"]])
            if not (efp and pm):
                bad += 1
                where.append([round(x), round(y), page.evaluate("([x, y]) => { const e = document.elementFromPoint(x, y); return e ? String(e.className || e.tagName).slice(0, 50) : null; }", [x, y])])
        if bad and under == bad:
            # Scrolled under the HOST's own sticky bar (the Chair's capture bar, the Room's ask
            # well): not on this board. Recorded, not counted as a miss.
            behind.append({"text": c["text"], "points_under_host_bar": under})
        elif bad:
            missed.append({"text": c["text"], "missed_points": bad, "where": where, "html": c["html"], "opacity": c["opacity"]})
        else:
            owned += 1
    page.mouse.move(1, 1)
    page.evaluate(RESTORE)
    page.wait_for_timeout(100)
    return {"owned": owned, "missed": missed, "under_host_bar": behind}


def seed_hub(hub_url: str, home: str) -> dict:
    seed: dict = {}
    s, p = hub_api(hub_url, "POST", "/api/projects", {"name": PROJECT})
    pid = p["project"]["id"]
    seed["project"] = [s, pid]
    seed["link_meeting"] = hub_api(hub_url, "POST", f"/api/projects/{pid}/meetings/m-sync", {})[0]
    hub_api(hub_url, "POST", f"/api/projects/{pid}/items", {"item_type": "milestone", "title": "Cutover rehearsal"})
    s1, d = hub_api(hub_url, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})
    s2, _ = hub_api(hub_url, "POST", f"/api/updates/{d['update']['id']}/publish", {})
    seed["update"] = [s1, s2, d["update"]["id"]]
    s, dec = hub_api(hub_url, "POST", "/api/decisions", {
        "title": "Freeze the old ledger on Nov 3", "status": "accepted", "deciders": ["Karol", "Priya"],
        "context_markdown": "The cutover rehearsal showed two write paths into the old ledger.",
        "decision_markdown": "Freeze the old ledger on Nov 3. All writes go to the new ledger after that day.",
        "consequences_markdown": "- Finance runs one extra reconciliation.\n- Rollback window closes Nov 10."})
    seed["desk_decision"] = [s, dec["decision"]["id"]]
    seed["people_setup"] = hub_api(hub_url, "POST", "/api/people/setup", {})[0]
    s, r = hub_api(hub_url, "POST", "/api/people/relationships", {"display_name": "Priya Nair"})
    rid = r["relationship"]["id"]
    seed["person"] = [s, hub_api(hub_url, "POST", f"/api/people/relationships/{rid}/owner-aliases", {"alias": "Priya"})[0], rid]
    s, b = hub_api(hub_url, "POST", "/api/brief/generate", {})
    seed["brief"] = [s, b.get("id") if isinstance(b, dict) else b]
    folder = Path(home) / "Reports" / "Team"
    folder.mkdir(parents=True)
    folder = Path(os.environ["P11_FOLDER"])
    s, fd = hub_api(hub_url, "POST", "/api/channels/destinations", {"name": "Team folder", "channel": "file", "folder": str(folder)})
    seed["file_destination"] = [s, (fd or {}).get("destination", {}).get("id") if isinstance(fd, dict) else fd]
    return seed


def run(width: int, height: int) -> tuple[list[str], dict]:
    home = tempfile.mkdtemp(prefix="philo11-03-canvas-")
    # The folder destination: a short real path the run removes (the send is a stand-in; nothing is written).
    outdir = tempfile.mkdtemp(prefix="p11-", dir="/tmp")
    os.environ["P11_FOLDER"] = f"{outdir}/Reports"
    Path(os.environ["P11_FOLDER"]).mkdir()
    hub_port, today_port, canvas_port = free_port(), free_port(), free_port()
    hub_url = f"http://127.0.0.1:{hub_port}"
    env = {**os.environ, "HOME": home, "PYTHONPATH": str(REPO), "HOLDSPEAK_PEOPLE_KEYSTORE_FILE": f"{home}/people.key"}
    facts: dict[str, dict] = {}
    errors: list[str] = []
    fails: list[str] = []
    procs: list[subprocess.Popen] = []
    try:
        # TODAY's aftercare rows and Credentials row show only with a webhook set (never called).
        cfg = Path(home) / ".config" / "holdspeak"
        cfg.mkdir(parents=True)
        (cfg / "config.json").write_text(json.dumps({"meeting": {"slack_webhook_url": FAKE_WEBHOOK}}))
        seeded = subprocess.run([PY, str(HERE / "seed_db.py")], cwd=REPO, env=env, capture_output=True, text=True, timeout=180)
        if seeded.returncode:
            raise RuntimeError(f"seed_db failed: {seeded.stderr[-2000:]}")
        db_seed = json.loads(seeded.stdout.strip().splitlines()[-1])
        procs.append(subprocess.Popen([PY, "scripts/graph_walk.py", "serve", "--port", str(hub_port), "--token", TOKEN],
                                      cwd=REPO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        vite = str(WEB / "node_modules/.bin/vite")
        for port, mode in ((canvas_port, "proposal"), (today_port, "today")):
            procs.append(subprocess.Popen([vite, "--config", str(HERE / "vite.config.mjs")], cwd=WEB,
                                          env={**os.environ, "HUB": hub_url, "CANVAS_PORT": str(port), "CANVAS_MODE": mode},
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        wait_http(f"{hub_url}/api/projects", {"Authorization": f"Bearer {TOKEN}"})
        wait_http(f"http://127.0.0.1:{canvas_port}/")
        wait_http(f"http://127.0.0.1:{today_port}/")
        seed = seed_hub(hub_url, home)
        seed["db"] = db_seed
        facts["_seed"] = seed
        print("seed", json.dumps(seed)[:700], flush=True)
        rec, rec_mtg = db_seed["record"], db_seed["record_mtg"]
        desk_dec = seed["desk_decision"][1]
        brief_id = seed["brief"][1]
        upd = seed["update"][2]
        SHOTS.mkdir(parents=True, exist_ok=True)

        try:
          with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            def open_page(origin: str):
                ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2)
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append(f"{width} pageerror: {e}"))
                page.on("console", lambda m: errors.append(f"{width} console: {m.text[:200]}")
                        if m.type == "error" and "Failed to fetch" not in m.text and "status of 4" not in m.text else None)
                page.goto(f"{origin}/?token={TOKEN}", wait_until="load")
                boot(page)
                return ctx, page

            def boot(page):
                page.locator(".chair").wait_for(timeout=60_000)
                page.wait_for_timeout(1500)
                for _ in range(20):
                    cl = page.get_by_role("button", name="Continue later", exact=True)
                    if cl.count():
                        cl.first.click(force=True)
                        page.wait_for_timeout(1200)
                        break
                    page.wait_for_timeout(300)

            def nav(page, what: str, *args: str, wait: str | None = None):
                page.evaluate("([w, a]) => window.__p11Open[w](...a)", [what, list(args)])
                if wait:
                    page.locator(wait).first.wait_for(timeout=20_000)
                page.wait_for_timeout(900)

            def close_windows(page):
                # A clean desk for the next board: every window closed through the store (what each
                # window's close does); the desk remembers open windows across a reload.
                page.evaluate("window.__p11Open.closeAll()")
                page.wait_for_timeout(900)

            def open_room(page):
                page.locator("[aria-controls=desk-tool-shelf]").first.click()
                page.locator("[aria-controls=desk-palette-listbox]").fill(PROJECT)
                page.get_by_text(f"Open {PROJECT}").first.click(timeout=20_000)
                page.locator("[data-testid=room-body]").wait_for(timeout=20_000)
                page.wait_for_timeout(1200)

            def mark(page, text: str, name: str, within: str = "body", contains: bool = False) -> str:
                """Name the smallest element whose text is (or contains) `text`, any case: a CSS handle for the on-screen law."""
                page.evaluate("""([t, n, w, c]) => { const root = document.querySelector(w) || document.body; const T = t.toUpperCase();
                  const ok = (e) => { const x = (e.innerText || '').trim().toUpperCase(); return c ? x.includes(T) : x === T; };
                  const all = [...root.querySelectorAll('*')].filter((e) => ok(e) && e.getBoundingClientRect().width);
                  const el = all.find((e) => ![...e.children].some(ok)) || all[0];
                  if (el) el.dataset.mark = n; }""", [text, name, within, contains])
                return f"[data-mark='{name}']"

            def mark_last_window(page) -> str:
                page.evaluate("() => { const w = [...document.querySelectorAll('.desk-window')].pop(); if (w) w.dataset.mark = 'lastwin'; }")
                return "[data-mark='lastwin']"

            def scroll_to_text(page, sel: str, text: str) -> bool:
                """Scroll the text's own line to the middle of its scroller; True when that line is on screen."""
                return page.evaluate("""([sel, t]) => { const b = document.querySelector(sel); if (!b) return false;
                  const w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
                  for (let n = w.nextNode(); n; n = w.nextNode()) { const i = n.textContent.indexOf(t); if (i < 0) continue;
                    const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + t.length);
                    // Every scroller from the inner one out (the preview well scrolls inside its window).
                    for (let s = n.parentElement; s; s = s.parentElement) {
                      if (!(s.scrollHeight > s.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) continue;
                      const rr = r.getBoundingClientRect(), sr = s.getBoundingClientRect();
                      s.scrollTop += rr.top - (sr.top + Math.min(sr.height / 3, 120));
                    }
                    const q = r.getBoundingClientRect(); const h = document.elementFromPoint(q.left + 2, q.top + q.height / 2);
                    return q.top >= 0 && q.bottom <= innerHeight && !!h && b.contains(h); }
                  return false; }""", [sel, text])

            def seat(page, sel: str, block: str = "start"):
                page.evaluate("""([sel, block]) => { const el = document.querySelector(sel); if (!el) return;
                  el.scrollIntoView({block});
                  if (block !== 'start') return;
                  let s = el.parentElement; while (s && !(s.scrollHeight > s.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) s = s.parentElement;
                  if (s) s.scrollTop = Math.max(0, s.scrollTop - 48); else window.scrollBy(0, -48); }""", [sel, block])
                page.wait_for_timeout(300)

            def shoot(page, board: str, anchor: str, named: list[str], seat_on: str | None = "FIRST", block: str = "start",
                      extra: dict | None = None, checks: dict | None = None):
                target = named[0] if seat_on == "FIRST" else seat_on
                if target:
                    seat(page, target, block)
                page.mouse.move(1, 1)
                page.wait_for_timeout(300)
                key = f"{board}-{width}"
                vis = page.evaluate(VISIBLE, named)
                page.screenshot(path=str(SHOTS / f"{key}.png"))
                masked = hashlib.sha256(page.screenshot(mask=[page.locator(".desk-clock")], mask_color="#000000")).hexdigest()
                f = page.evaluate(FACTS, anchor)
                f["named"] = vis
                f["masked_sha"] = masked
                f["pointer"] = pointer_pass(page, width, anchor)
                if target:
                    seat(page, target, block)
                if extra:
                    f.update(extra)
                facts[key] = f
                hidden = [v for v in vis if not v["ok"]]
                if hidden:
                    fails.append(f"{key}: off screen {hidden}")
                for name, ok in (checks or {}).items():
                    if not ok:
                        fails.append(f"{key}: check failed: {name}")
                law = {"stale words": not f.get("stale_words"), "no Mark delivered on a new kind": not f.get("mark_delivered_in_new_kind"),
                       "no link on a Slack post": not f.get("proof_links_on_slack"), "no modal": not f.get("modal"),
                       "no transcript": not f.get("transcript_sentinel"), "no raw button in the proposal": not f.get("raw_buttons", {}).get("proposal"),
                       "no text under 12px in the proposal": not f.get("small_text", {}).get("proposal")}
                for name, ok in law.items():
                    if not ok and f.get("window"):
                        fails.append(f"{key}: law: {name}")
                print(key, "w", f.get("window_width"), "wells", f.get("wells"), "ptr", f["pointer"]["owned"], len(f["pointer"]["missed"]),
                      "hidden", [(v["sel"][-50:], v["why"]) for v in hidden], "ovf", f.get("h_overflow"), f.get("body_overflow_x"), flush=True)

            # scoped selectors
            CH = ".chair [data-seat=brief]"                     # the Chair's brief seat
            IB = ".desk-window [data-seat=brief]"               # Intelligence BRIEF view
            DD = ".desk-window [data-seat=desk-decision]"
            DR = ".desk-window [data-seat=decision-record]"
            MR = ".desk-window [data-seat=meeting]"

            def row(scope: str, name: str) -> str:
                return f"{scope} [data-testid=destination-row]:has([data-destination='{name}'])"

            def opened(scope: str, name: str) -> str:
                return f"{scope} [data-testid=send-open][data-destination='{name}']"

            def pick(page, scope: str, name: str):
                if not page.locator(opened(scope, name)).count():
                    page.locator(row(scope, name)).first.click()
                page.locator(f"{opened(scope, name)} [data-testid=send-preview], {opened(scope, name)} [data-testid=preview-refused], "
                             f"{opened(scope, name)} [data-testid=preview-failed]").first.wait_for(timeout=15_000)
                page.wait_for_timeout(400)

            def unpick(page, scope: str, name: str):
                if page.locator(opened(scope, name)).count():
                    page.locator(row(scope, name)).first.click()
                    page.wait_for_timeout(300)

            def press(page, scope: str, name: str, expect: str = "[data-testid=send-sent]"):
                page.locator(f"{opened(scope, name)} [data-testid=send-verb]").first.click()
                page.locator(f"{opened(scope, name)} {expect}").first.wait_for(timeout=15_000)
                page.wait_for_timeout(600)

            today = f"http://127.0.0.1:{today_port}"
            canvas = f"http://127.0.0.1:{canvas_port}"

            # ── TODAY: what R7 removes, and the unknown of design 6a ──────────
            ctx, page = open_page(today)
            nav(page, "meetings", "m-sync", wait=".desk-window .meeting-summary-slab, .desk-window [data-testid=meeting-summary-text], .desk-window .summary-text")
            page.wait_for_timeout(800)
            m1, m2 = mark(page, "DIGEST → SLACK", "dig"), mark(page, "FOLLOW-UP → SLACK", "fol")
            shoot(page, "0a-today-aftercare-slack-rows", ".desk-window", [m1, m2], seat_on=m1, block="center")
            close_windows(page)
            nav(page, "settings", wait="[data-testid=destinations]")
            m = mark(page, "Slack webhook", "slackcred", ".desk-window", contains=True)
            facts["_today_settings_text"] = page.locator(".desk-window").last.inner_text()[-1500:]
            shoot(page, "0b-today-credentials-slack-row", ".desk-window", [m], seat_on=m, block="center")
            close_windows(page)
            # design 6a unknown: the Room's decision row Open, on today's product.
            open_room(page)
            page.locator("[data-testid=decision-row]").first.wait_for(timeout=15_000)
            lifecycle_text = "Cut over by space, not by region"
            room_text = page.locator("[data-testid=room-body]").inner_text()
            before = page.locator(".desk-window").count()
            warns: list[str] = []
            page.on("console", lambda m: warns.append(m.text[:200]) if "openPullout" in m.text or "unknown" in m.text.lower() else None)
            page.locator("[data-testid=decision-row] .btn", has_text="Open").first.click()
            page.wait_for_timeout(1800)
            after = page.locator(".desk-window").count()
            open_win = f"windows before {before}, after {after}; console: {warns}"
            lw = mark_last_window(page)
            shoot(page, "0c-today-room-record-open", lw, [lw], seat_on=None,
                  extra={"room_row_open_window_text": open_win[:600], "lifecycle_row_text_in_room": lifecycle_text in room_text})
            ctx.close()

            # ── PROPOSAL ─────────────────────────────────────────────────────
            ctx, page = open_page(canvas)
            # Canvas A, board A1: no destination saved yet (the real file destination is parked first).
            hub_api(hub_url, "DELETE", f"/api/channels/destinations/{seed['file_destination'][1]}", {"command_id": "canvas-park-1"})
            page.reload(wait_until="load"); boot(page)
            page.locator(f"{CH} [data-testid=send-none]").wait_for(timeout=20_000)
            shoot(page, "A1-brief-chair-no-destination", CH, [f"{CH} [data-testid=send-none]", f"{CH} [data-testid=send-add-destination]"],
                  seat_on=f"{CH} [data-testid=send-none]", block="center")

            # Canvas D: Destinations with Slack (Settings -> Connections, under Tools).
            page.locator(f"{CH} [data-testid=send-add-destination]").click()
            page.locator("[data-testid=destinations] [data-testid=dest-form]").wait_for(timeout=20_000)
            page.wait_for_timeout(900)
            form = page.locator("[data-testid=dest-form]").last
            form.locator("select[aria-label=Channel]").select_option("slack")
            page.wait_for_timeout(300)
            form.locator("[data-testid=dest-slack-label]").fill("#leads")
            page.wait_for_timeout(300)
            shoot(page, "D1-slack-form", "[data-testid=destinations]",
                  ["[data-testid=dest-form][data-channel=slack] [data-testid=dest-key-row]", "[data-testid=dest-slack-label]",
                   "[data-testid=dest-form] [data-testid=dest-save]"], seat_on="[data-testid=dest-form][data-channel=slack]")
            # D2b: a URL that is not a Slack webhook: refused, not kept.
            form.locator("[data-testid=dest-key-row] .btn", has_text="Replace").click()
            form.locator("[data-testid=dest-key-row] input[type=password]").fill("https://example.com/hooks/abc")
            form.locator("[data-testid=dest-key-row] input[type=password]").press("Enter")
            page.locator("[data-testid=dest-key-refused]").wait_for(timeout=10_000)
            shoot(page, "D2b-webhook-refused", "[data-testid=destinations]", ["[data-testid=dest-key-refused]"],
                  seat_on="[data-testid=dest-form][data-channel=slack]")
            form.locator("[data-testid=dest-key-row] .btn", has_text="Replace").click()
            form.locator("[data-testid=dest-key-row] input[type=password]").fill(FAKE_WEBHOOK)
            form.locator("[data-testid=dest-key-row] input[type=password]").press("Enter")
            page.wait_for_function("!document.querySelector('[data-testid=dest-key-refused]')", timeout=10_000)
            page.wait_for_timeout(500)
            key_text = form.locator("[data-testid=dest-key-row]").inner_text()
            shoot(page, "D2a-webhook-saved", "[data-testid=destinations]", ["[data-testid=dest-form][data-channel=slack] [data-testid=dest-key-row]"],
                  seat_on="[data-testid=dest-form][data-channel=slack]",
                  extra={"key_row_text": key_text}, checks={"the URL is never shown": "hooks.slack.com/services" not in key_text})
            form.locator("[data-testid=dest-save]").click()
            page.locator("[data-testid=dest-row]:has([data-destination='Slack #leads'])").wait_for(timeout=10_000)
            page.wait_for_timeout(600)
            # A second destination: a folder, through the real Phase 10 route (the face's own add path is Phase 10's).
            s, fd2 = hub_api(hub_url, "POST", "/api/channels/destinations", {"name": "Team folder", "channel": "file", "folder": os.environ["P11_FOLDER"]})
            page.evaluate("window.dispatchEvent(new Event('holdspeak:destinations-changed'))")
            close_windows(page)
            nav(page, "settings", wait="[data-testid=destinations]")
            page.locator("[data-testid=dest-row]:has([data-destination='Slack #leads'])").click()
            page.locator("[data-testid=dest-open] [data-testid=dest-check]").click()
            page.locator("[data-testid=dest-check-result]").wait_for(timeout=10_000)
            shoot(page, "D3-slack-row-checked", "[data-testid=destinations]",
                  ["[data-testid=dest-row]:has([data-destination='Slack #leads'])", "[data-testid=dest-check-result]"])
            page.locator("[data-testid=dest-row]:has([data-destination='Slack #leads'])").click()
            page.wait_for_timeout(300)
            mc = mark(page, "Credentials", "creds", ".desk-window")
            creds = page.locator(".desk-window").last.inner_text()
            shoot(page, "D4-credentials-no-slack-row", "[data-testid=destinations]", [mc], seat_on=mc,
                  extra={"credentials_slack_row": "Slack webhook" in creds}, checks={"no Slack webhook row": "Slack webhook" not in creds})
            close_windows(page)

            # Canvas A: the brief. A2 on the Intelligence BRIEF view (the document form).
            nav(page, "brief", wait=f"{IB} [data-testid=destination-row]")
            pick(page, IB, "Team folder")
            shoot(page, "A2-brief-picked-folder", IB, [row(IB, "Team folder"), f"{opened(IB, 'Team folder')} [data-testid=send-verb]",
                                                       f"{opened(IB, 'Team folder')} [data-testid=send-preview-body] > * > :first-child"])
            press(page, IB, "Team folder")
            unpick(page, IB, "Team folder")
            shoot(page, "A3-brief-saved-history", IB, [f"{row(IB, 'Team folder')} [data-testid=send-last-sent]", f"{IB} [data-testid=send-history] .surface-section-head"],
                  seat_on=row(IB, "Team folder"))
            unpick(page, IB, "Team folder")
            # A6: the person sections in the preview (R1): Slack, scrolled to PEOPLE.
            pick(page, IB, "Slack #leads")
            body = page.locator(f"{opened(IB, 'Slack #leads')} [data-testid=send-preview-body]").inner_text()
            people_on_screen = scroll_to_text(page, f"{opened(IB, 'Slack #leads')} [data-testid=send-preview-body]", "*People*")
            shoot(page, "A6-brief-slack-person-sections", IB, [], seat_on=None,
                  extra={"preview_has_people": "*People*" in body and "Priya Nair" in body, "preview_has_ack_marks": "ACKNOWLEDGED" in body.upper(),
                         "people_line_on_screen": people_on_screen},
                  checks={"person sections in the preview": "*People*" in body and "Priya Nair" in body, "People line on screen": people_on_screen})
            unpick(page, IB, "Slack #leads")
            # A5: the brief changes after the send (a new person signal, the same brief id): the new preview, Send again (R9).
            rel = facts["_seed"]["person"][2]
            hub_api(hub_url, "POST", f"/api/people/relationships/{rel}/requests", {"body": "Review the rollback plan with me"})
            s, r2 = hub_api(hub_url, "POST", "/api/people/relationships", {"display_name": "Marek Wolny"})
            hub_api(hub_url, "POST", f"/api/people/relationships/{r2['relationship']['id']}/owner-aliases", {"alias": "Marek"})
            s, again = hub_api(hub_url, "POST", "/api/brief/generate", {})
            same_id = isinstance(again, dict) and again.get("id") == brief_id
            pick(page, IB, "Team folder")
            body2 = page.locator(f"{opened(IB, 'Team folder')} [data-testid=send-preview-body]").inner_text()
            verb = page.locator(f"{opened(IB, 'Team folder')} [data-testid=send-verb]").inner_text().strip()
            marek_on_screen = scroll_to_text(page, f"{opened(IB, 'Team folder')} [data-testid=send-preview-body]", "Marek Wolny")
            shoot(page, "A5-brief-changed-send-again", IB, [], seat_on=None,
                  extra={"same_brief_id_after_generate": same_id, "new_text_in_preview": "Marek Wolny" in body2, "verb": verb, "new_line_on_screen": marek_on_screen},
                  checks={"same id": same_id, "new words in the preview": "Marek Wolny" in body2, "Send again": verb == "Send again",
                          "the new line on screen": marek_on_screen})
            seat(page, f"{opened(IB, 'Team folder')} [data-testid=send-verb]", "center")
            shoot(page, "A5b-brief-changed-verb", IB, [f"{opened(IB, 'Team folder')} [data-testid=send-verb]", f"{row(IB, 'Team folder')} [data-testid=send-last-sent]"],
                  seat_on=row(IB, "Team folder"), block="start")
            unpick(page, IB, "Team folder")
            close_windows(page)
            # A4: the steward prepared a send of the brief: the Chair's BRIEF head chip and the PREPARED row.
            page.evaluate("(r) => window.__p11Prepare({document_ref: r, destination_name: 'Slack #leads', by_kind: 'steward', by_identity: 'steward'})",
                          f"monday_brief:{brief_id}")
            page.reload(wait_until="load"); boot(page)
            page.locator(".chair [data-testid=doc-prepared-chip]").wait_for(timeout=20_000)
            shoot(page, "A4-brief-prepared-chair", CH, [".chair [data-testid=doc-prepared-chip]"], seat_on=".chair [data-testid=doc-prepared-chip]", block="center")
            seat(page, f"{CH} [data-testid=prepared-list]", "center")
            shoot(page, "A4b-brief-prepared-row", CH, [f"{CH} [data-testid=prepared-row]", f"{CH} [data-testid=prepared-send]"],
                  seat_on=f"{CH} [data-testid=prepared-row]")
            page.locator(f"{CH} [data-testid=prepared-send]").click()
            page.locator(f"{CH} [data-testid=prepared-result]").wait_for(timeout=15_000)
            page.wait_for_timeout(600)
            shoot(page, "A4c-brief-prepared-posted", CH, [f"{CH} [data-testid=prepared-result]", f"{CH} [data-testid=send-history]"],
                  seat_on=f"{CH} [data-testid=prepared-result]")
            # T3: the last brief item acknowledged: the Chair changes branch; the well stays.
            _, latest = hub_api(hub_url, "GET", "/api/brief/latest")
            items = [it for sec in latest["sections"].values() for it in sec]
            keep = next((it for it in items if str(it.get("text", "")).startswith("Review decision: Freeze")), items[0])
            for it in [x for x in items if x["id"] != keep["id"]]:
                hub_api(hub_url, "POST", f"/api/brief/items/{it['id']}/shelf", {"state": "acknowledged"})
            page.reload(wait_until="load"); boot(page)
            page.locator(".chair [data-testid=arrival-brief] .btn", has_text="Ack").first.wait_for(timeout=20_000)
            ack = mark(page, "Ack", "ack", ".chair [data-testid=arrival-brief]")
            shoot(page, "T3a-chair-last-item", CH, [ack, f"{CH} [data-testid=send-well]"],
                  seat_on=".chair [data-testid=arrival-brief]")
            page.locator(".chair [data-testid=arrival-brief] .btn", has_text="Ack").first.click()
            page.locator(".chair [data-testid=arrival-brief-headline], .chair [data-testid=arrival-brief-handled]").first.wait_for(timeout=15_000)
            page.wait_for_timeout(900)
            branch = page.locator(".chair [data-testid=arrival-brief]").inner_text()
            shoot(page, "T3b-chair-after-last-ack", CH, [".chair [data-testid=arrival-brief] .surface-section-head", f"{CH} [data-testid=send-well]"],
                  seat_on=".chair [data-testid=arrival-brief]",
                  extra={"branch_text": branch[:400]}, checks={"the well stays after the branch change": page.locator(f"{CH} [data-testid=send-well]").count() == 1})

            # Canvas B: a decision. B0: design 6a on glass -- no face renders a lifecycle row.
            # B1: the desk decision window (about 400 px at 1440).
            nav(page, "decision", desk_dec, wait=f"{DD} [data-testid=destination-row]")
            pick(page, DD, "Slack #leads")
            shoot(page, "B1-decision-window-picked", DD, [row(DD, "Slack #leads"), f"{opened(DD, 'Slack #leads')} [data-testid=send-verb]"],
                  seat_on=row(DD, "Slack #leads"))
            press(page, DD, "Slack #leads")
            shoot(page, "B2-decision-posted-slack", DD, [f"{opened(DD, 'Slack #leads')} [data-testid=send-sent]", f"{row(DD, 'Slack #leads')} [data-testid=send-last-sent]"],
                  seat_on=row(DD, "Slack #leads"))
            unpick(page, DD, "Slack #leads")
            shoot(page, "B2b-decision-history", DD, [f"{DD} [data-testid=send-history] .surface-section-head", f"{DD} [data-testid=history-row]"],
                  seat_on=f"{DD} [data-testid=send-history]")
            unpick(page, DD, "Slack #leads")
            # B3: Edit after a send (on glass: Edit, type, Done): the preview shows the new text; Send again (R9).
            win = page.locator(".desk-window").last
            win.locator(".btn", has_text="Edit").last.click()
            page.wait_for_timeout(500)
            pad = win.locator("textarea").nth(1)
            pad.fill("Freeze the old ledger on Nov 5. All writes go to the new ledger after that day.")
            win.locator(".btn", has_text="Done").last.click()
            page.locator(f"{DD} [data-testid=destination-row]").first.wait_for(timeout=15_000)
            page.wait_for_timeout(800)
            pick(page, DD, "Slack #leads")
            b3 = page.locator(f"{opened(DD, 'Slack #leads')} [data-testid=send-preview-body]").inner_text()
            b3verb = page.locator(f"{opened(DD, 'Slack #leads')} [data-testid=send-verb]").inner_text().strip()
            nov5 = scroll_to_text(page, f"{opened(DD, 'Slack #leads')} [data-testid=send-preview-body]", "Nov 5")
            shoot(page, "B3-decision-edited-send-again", DD, [],
                  seat_on=None, extra={"new_text": "Nov 5" in b3, "verb": b3verb, "new_text_on_screen": nov5},
                  checks={"the preview has the edit": "Nov 5" in b3, "Send again": b3verb == "Send again", "the edit on screen": nov5})
            # T2: the decision changes in another place after he read the preview: PREVIEW CHANGED, a fresh preview, another press.
            hub_api(hub_url, "PUT", f"/api/decisions/{desk_dec}", {"decision_markdown": "Freeze the old ledger on Nov 6. All writes go to the new ledger after that day."})
            page.locator(f"{opened(DD, 'Slack #leads')} [data-testid=send-verb]").click()
            page.locator(f"{opened(DD, 'Slack #leads')} [data-testid=send-refused][data-code=preview_changed]").wait_for(timeout=15_000)
            page.wait_for_function("(sel) => (document.querySelector(sel)?.innerText || '').includes('Nov 6')",
                                   arg=f"{opened(DD, 'Slack #leads')} [data-testid=send-preview-body]", timeout=15_000)
            page.wait_for_timeout(500)
            shoot(page, "T2a-preview-changed-fresh-preview", DD, [f"{opened(DD, 'Slack #leads')} [data-testid=send-refused]",
                                                                  f"{opened(DD, 'Slack #leads')} [data-testid=send-verb]"],
                  seat_on=row(DD, "Slack #leads"))
            page.locator(f"{opened(DD, 'Slack #leads')} [data-testid=send-verb]").click()
            page.locator(f"{opened(DD, 'Slack #leads')} [data-testid=send-sent]").wait_for(timeout=15_000)
            page.wait_for_timeout(600)
            dump = page.evaluate("window.__p11Dump()")
            last = [s for s in dump["sends"] if s["document_ref"] == f"desk_decision:{desk_dec}" and s["state"] == "sent"][-1]
            shoot(page, "T2b-preview-changed-sent", DD, [f"{opened(DD, 'Slack #leads')} [data-testid=send-sent]"], seat_on=row(DD, "Slack #leads"),
                  extra={"sent_text_has_nov6": "Nov 6" in last["preview"]["text"]}, checks={"the new text went": "Nov 6" in last["preview"]["text"]})
            close_windows(page)
            # B5: the decision RECORD in Intelligence -> DECISIONS.
            nav(page, "record", rec, wait=f"{DR} [data-testid=destination-row]")
            pick(page, DR, "Team folder")
            shoot(page, "B5-record-intelligence-picked", DR, [row(DR, "Team folder"), f"{opened(DR, 'Team folder')} [data-testid=send-verb]"],
                  seat_on=row(DR, "Team folder"))
            close_windows(page)
            # B4: an agent prepared a send of the Room's MTG record; the Room row carries PREPARED ×1 and opens in place.
            page.evaluate("(r) => window.__p11Prepare({document_ref: r, destination_name: 'Team folder', by_kind: 'agent', by_identity: 'codex'})",
                          f"decision_record:{rec_mtg}")
            open_room(page)
            page.locator("[data-testid=decision-row] [data-testid=doc-prepared-chip]").wait_for(timeout=20_000)
            room_now = page.locator("[data-testid=room-body]").inner_text()
            shoot(page, "B4-room-row-prepared-chip", "[data-testid=room-body]", ["[data-testid=decision-row]:has([data-testid=doc-prepared-chip])"],
                  seat_on="[data-testid=decision-row]:has([data-testid=doc-prepared-chip])",
                  extra={"lifecycle_row_text_in_room": "Cut over by space, not by region" in room_now})
            page.locator("[data-testid=decision-row]:has([data-testid=doc-prepared-chip])").first.click()
            RR = "li.surface-ledger-row:has(> [data-testid=decision-row]) [data-seat=decision-record]"
            page.locator(f"{RR} [data-testid=prepared-row]").wait_for(timeout=15_000)
            shoot(page, "B4b-room-row-open-prepared", "[data-testid=room-body]", [f"{RR} [data-testid=prepared-send]", f"{RR} [data-testid=prepared-label]"],
                  seat_on=f"{RR} [data-testid=prepared-send]", block="center")
            close_windows(page)

            # Canvas C: a meeting summary. C1 the Meetings record (about 640 px at 1440): SUMMARY, then SEND.
            nav(page, "meetings", "m-sync", wait=f"{MR} [data-testid=destination-row]")
            shoot(page, "C1-meetings-record-send", MR, [f"{MR} [data-testid=doc-forms]", f"{MR} [data-testid=destination-row]"],
                  seat_on=f"{MR} [data-testid=send-well]", block="center")
            pick(page, MR, "Slack #leads")
            c2 = page.locator(f"{opened(MR, 'Slack #leads')} [data-testid=send-preview-body]").inner_text()
            shoot(page, "C2-summary-slack-picked", MR, [row(MR, "Slack #leads"), f"{opened(MR, 'Slack #leads')} [data-testid=send-verb]"],
                  seat_on=row(MR, "Slack #leads"), checks={"summary text": "freeze the old ledger" in c2.lower()})
            press(page, MR, "Slack #leads")
            shoot(page, "C3-summary-posted-slack", MR, [f"{opened(MR, 'Slack #leads')} [data-testid=send-sent]", f"{row(MR, 'Slack #leads')} [data-testid=send-last-sent]"],
                  seat_on=row(MR, "Slack #leads"))
            unpick(page, MR, "Slack #leads")
            shoot(page, "C3b-summary-history", MR, [f"{MR} [data-testid=send-history] .surface-section-head", f"{MR} [data-testid=history-row]"],
                  seat_on=f"{MR} [data-testid=send-history]")
            unpick(page, MR, "Slack #leads")
            # C5: the digest, a form in the same well; the aftercare Slack rows are gone (compare 0a).
            page.locator(f"{MR} [data-testid=doc-forms] select").select_option("meeting_digest")
            page.locator(f"{MR} [data-testid=destination-row]").first.wait_for(timeout=15_000)
            pick(page, MR, "Slack #leads")
            c5 = page.locator(f"{opened(MR, 'Slack #leads')} [data-testid=send-preview-body]").inner_text()
            win_text = page.locator(".desk-window:has([data-seat=meeting])").inner_text()
            shoot(page, "C5-digest-form-slack", MR, [f"{MR} [data-testid=doc-forms]", f"{opened(MR, 'Slack #leads')} [data-testid=send-verb]"],
                  seat_on=f"{MR} [data-testid=doc-forms]",
                  extra={"aftercare_rows_on_face": "DIGEST → SLACK" in win_text},
                  checks={"no aftercare Slack rows": "DIGEST → SLACK" not in win_text and "FOLLOW-UP → SLACK" not in win_text,
                          "digest text": "What we decided" in c5})
            unpick(page, MR, "Slack #leads")
            page.locator(f"{MR} [data-testid=doc-forms] select").select_option("meeting_followup")
            page.locator(f"{MR} [data-testid=destination-row]").first.wait_for(timeout=15_000)
            pick(page, MR, "Team folder")
            shoot(page, "C5b-followup-form-folder", MR, [f"{MR} [data-testid=doc-forms]", f"{opened(MR, 'Team folder')} [data-testid=send-verb]"],
                  seat_on=f"{MR} [data-testid=doc-forms]")
            unpick(page, MR, "Team folder")
            page.locator(f"{MR} [data-testid=doc-forms] select").select_option("meeting_summary")
            close_windows(page)
            # C4: a meeting with no summary: no SEND well.
            nav(page, "meetings", "m-bare", wait=".desk-window [data-testid=room-body], .desk-window")
            page.wait_for_timeout(1500)
            wells = page.locator(".desk-window [data-p11=well]").count()
            lw = ".desk-window[aria-label='Meetings']"
            wells = page.locator(f"{lw} [data-p11=well]").count()
            shoot(page, "C4-no-summary-no-well", lw, [lw], seat_on=None,
                  extra={"send_wells": wells}, checks={"no SEND well without a summary": wells == 0})
            close_windows(page)
            # T1: a summary over the Slack limit: REFUSED by name with the size; never NO ANSWER.
            nav(page, "meetings", "m-offsite", wait=f"{MR} [data-testid=destination-row]")
            pick(page, MR, "Slack #leads")
            ref = page.locator(f"{opened(MR, 'Slack #leads')} [data-testid=preview-refused]")
            t1 = ref.inner_text() if ref.count() else ""
            shoot(page, "T1-over-slack-limit-refused", MR, [f"{opened(MR, 'Slack #leads')} [data-testid=preview-refused]"], seat_on=row(MR, "Slack #leads"),
                  extra={"refusal_text": t1}, checks={"named refusal": "TOO LARGE FOR SLACK" in t1, "never NO ANSWER": "NO ANSWER" not in t1})
            close_windows(page)
            # C6: the meeting window and the Chair's MEETINGS row carry the same well.
            nav(page, "meeting", "m-sync", wait=f"{MR} [data-testid=destination-row]")
            shoot(page, "C6-meeting-window-well", MR, [f"{MR} [data-testid=doc-forms]", f"{MR} [data-testid=destination-row]"],
                  seat_on=f"{MR} [data-testid=doc-forms]")
            close_windows(page)
            shoot(page, "C6b-chair-meetings-row-well", ".chair [data-seat=meeting]", [".chair [data-seat=meeting] [data-testid=doc-forms]"],
                  seat_on=".chair [data-seat=meeting] [data-testid=doc-forms]", block="center")

            # Canvas E: the one species on the four faces (plus the update's own history and manual row).
            open_room(page)
            page.locator("[data-testid=updates-verb]").click()
            page.locator("[data-testid=update-list]").wait_for(timeout=15_000)
            page.locator(f"[data-testid=update-list-item]:has([data-update-id='{upd}'])").first.click()
            page.locator("[data-seat=update] [data-testid=destination-row]").first.wait_for(timeout=15_000)
            page.wait_for_timeout(800)
            shoot(page, "E1a-update-well", "[data-seat=update]", ["[data-seat=update] [data-testid=destination-row]", "[data-testid=deliver-line]"],
                  seat_on="[data-seat=update] [data-testid=send-well]")
            sig = page.evaluate("""() => [...document.querySelectorAll('[data-p11=well]')].map((w) => ({doc: w.dataset.doc,
                rows: [...w.querySelectorAll('[data-testid=destination-row]')].map((r) => [...r.querySelectorAll('.surface-token, .gadget-chip-egress, .state-chip')].length)}))""")
            facts[f"E1a-update-well-{width}"]["well_signature"] = sig
            close_windows(page)
            for board, what, args, sel in (("E1b-brief-well", "brief", [], IB), ("E1c-decision-well", "decision", [desk_dec], DD),
                                           ("E1d-meeting-well", "meeting", ["m-sync"], MR)):
                nav(page, what, *args, wait=f"{sel} [data-testid=destination-row]")
                page.wait_for_timeout(2500)   # the window has finished opening (the row layout is not a transient)
                rows_stacked = page.evaluate("""(sel) => { const r = document.querySelector(sel + ' [data-testid=destination-row]');
                  if (!r) return null; const lead = r.querySelector('.surface-ledger-lead'), prim = r.querySelector('.surface-ledger-primary');
                  return !!lead && !!prim && Math.abs(lead.getBoundingClientRect().top - prim.getBoundingClientRect().top) > 8; }""", sel)
                facts.setdefault(f"_row_layout_{width}", {})[f"{board}-{width}"] = rows_stacked
                shoot(page, board, sel, [f"{sel} [data-testid=destination-row]"], seat_on=f"{sel} [data-testid=send-well]")
                close_windows(page)
            ctx.close()
            browser.close()
        except Exception as exc:   # a crash is a named failure; the facts so far are kept
            import traceback
            traceback.print_exc()
            fails.append(f"CRASH at width {width}: {str(exc).splitlines()[0][:300]}")
    finally:
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except Exception:
                p.kill()
        shutil.rmtree(outdir, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)   # law: a run removes its own scratch HOME
        facts[f"_browser_errors_{width}"] = errors  # type: ignore[assignment]
    return fails, facts


def main() -> None:
    import signal
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    all_fails: list[str] = []
    path = SHOTS / "facts.json"
    for w, h in WIDTHS:
        fails, facts = run(w, h)
        all_fails += fails
        prior = json.loads(path.read_text()) if path.exists() else {}
        SHOTS.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**prior, **facts, f"_fails_{w}": fails}, indent=1, ensure_ascii=False) + "\n")
    facts = json.loads(path.read_text())
    for w, _ in WIDTHS:
        seen: dict[str, str] = {}
        for key, f in sorted(facts.items()):
            if key.startswith("_") or not key.endswith(f"-{w}"):
                continue
            if f["masked_sha"] in seen:
                all_fails.append(f"IDENTICAL SHOTS (clock masked): {seen[f['masked_sha']]} == {key}")
            seen[f["masked_sha"]] = key
    if all_fails:
        print("FENCE FAILURES:", *all_fails, sep="\n  ", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
