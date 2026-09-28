"""PHILO-10-04 canvases: the SEND well on a published update, and the
Destinations group in Settings -> Connections.

Everything is live except the stated shim: a REAL hub (scripts/graph_walk.py
serve, isolated HOME, isolated DB) seeded through its real HTTP routes, and the
PRODUCT app served twice by vite (harness/vite.config.mjs):
  - TODAY:    the product as on this branch (no swap, no shim);
  - PROPOSAL: UpdatePosture + the Connections pane swapped for the harness
              copies, plus harness/shim.ts (the unbuilt wire, stated there).

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/shoot.py

Shots: ../shots/ (Send) and ../../story-04-destinations-canvas/shots/
(Destinations), <board>-<width>.png at 1440x900 and 393x852 (device scale 2);
facts.json beside them. ONLY_WIDTH=393 limits the run to one width.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SEND = HERE.parent
DEST = SEND.parent / "story-04-destinations-canvas"
REPO = SEND.parents[5]
WEB = REPO / "web"
TOKEN = "philo10-canvas"
ALL_WIDTHS = [(1440, 900), (393, 852)]
WIDTHS = [w for w in ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
NAME = "Payments ledger cutover"


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
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        return e.code, e.read().decode()[:400]


# Rendered facts. The frame is the window that holds the anchor; proposal
# nodes carry data-p10. Portals: every visible node outside #root is scanned.
FACTS = r"""(anchorSel) => {
  const anchor = document.querySelector(anchorSel);
  const win = anchor ? anchor.closest('.desk-window') : null;
  if (!win) return {window: false};
  const GLYPH = /^[●○◆▸▾✓✗⚠—↻ℹ«»·▤›×\s]+$/;
  const roots = [win, ...[...document.body.children].filter((e) => e.id !== 'root' && e.tagName !== 'SCRIPT')];
  const small = {proposal: [], inherited: []};
  for (const root of roots) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const t = n.textContent.trim();
      if (!t || GLYPH.test(t)) continue;
      const el = n.parentElement;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none') continue;
      const fs = parseFloat(cs.fontSize);
      if (fs < 12) (el.closest('[data-p10]') ? small.proposal : small.inherited).push({text: t.slice(0, 40), fs, cls: String(el.className).slice(0, 60), portal: root !== win});
    }
  }
  const parse = (c) => { const m = c.match(/[\d.]+/g); if (!m) return [0,0,0,0]; return [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1]; };
  const lum = ([r,g,b]) => { const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }; return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(b); };
  const over = (top, under) => { const a = top[3]; return [top[0]*a + under[0]*(1-a), top[1]*a + under[1]*(1-a), top[2]*a + under[2]*(1-a), 1]; };
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    const base = layers.length && layers[layers.length-1][3] >= 1 ? layers.pop() : parse(getComputedStyle(document.body).backgroundColor);
    let acc = base[3] >= 1 ? base : over(base, [0,0,0,1]);
    for (let i = layers.length - 1; i >= 0; i--) acc = over(layers[i], acc);
    return acc;
  };
  const ratio = (a, b) => { const la = lum(a), lb = lum(b); return +(((Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)).toFixed(2)); };
  // Contrast: every text-bearing element inside the proposal (chips, tokens,
  // fields, body text, verbs) against its composited background.
  const texts = [...win.querySelectorAll('[data-p10] *')].filter((e) => {
    if (![...e.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim())) return false;
    const r = e.getBoundingClientRect(); return r.width && r.height && getComputedStyle(e).visibility !== 'hidden';
  }).map((e) => {
    const fg = parse(getComputedStyle(e).color); const bg = bgOf(e);
    const fgc = fg[3] < 1 ? over(fg, bg) : fg;
    return {text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40), ratio: ratio(fgc, bg), fs: parseFloat(getComputedStyle(e).fontSize)};
  });
  const raw = [...win.querySelectorAll('button')].filter((b) => !String(b.className).includes('btn') && b.getBoundingClientRect().width);
  const rawIn = (p) => raw.filter((b) => !!b.closest('[data-p10]') === p).map((b) => (b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 30));
  const body = win.querySelector('.desk-surface-body') || anchor;
  const text = (sel) => [...win.querySelectorAll(sel)].map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  return {
    window: true,
    destinations: text('[data-testid=destination-row], [data-testid=dest-row]'),
    prepared: text('[data-testid=prepared-row]'),
    preview_fields: text('[data-testid=send-preview-field], [data-testid=prepared-preview] [data-testid=send-preview-field]'),
    preview_has_raw: /[{}]|<\/?(p|h2|ul|li)>/.test(text('[data-testid=send-preview-body], [data-testid=prepared-preview] [data-testid=send-preview-body]').join(' ')),
    send_verbs: text('[data-testid=send-verb], [data-testid=send-retry], [data-testid=prepared-send], [data-testid=prepared-retry]'),
    outcomes: [...win.querySelectorAll('[data-testid^=send-refused], [data-testid^=send-failed], [data-testid=send-lost], [data-testid=dest-refused]')].map((e) => ({text: e.innerText.replace(/\s+/g, ' ').trim(), code: e.dataset.code || null})),
    history_head: (() => { const s = win.querySelector('[data-p10=history] .surface-section-head h3'); return s ? s.innerText.trim() : null; })(),
    history: text('[data-testid=delivery-row]'),
    list_chips: text('[data-testid=update-list-item]'),
    dest_head: (() => { const s = win.querySelector('[data-p10=destinations] .gadget-group-label'); return s ? s.innerText.trim() : null; })(),
    dest_parked: text('[data-testid=dest-parked-row]'),
    egress_chips: [...win.querySelectorAll('[data-p10] .gadget-chip-egress')].map((e) => `${e.innerText.trim()}:${e.dataset.scope || ''}`),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
    small_text: small,
    min_contrast: texts.length ? Math.min(...texts.map((t) => t.ratio)) : null,
    low_contrast: texts.filter((t) => t.ratio < 4.5),
    raw_buttons: {proposal: rawIn(true), inherited: rawIn(false)},
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
    body_overflow_x: body ? body.scrollWidth > body.clientWidth + 1 : null,
    overflow_culprits: body ? [...body.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(), b = body.getBoundingClientRect(); return r.width && r.right > b.right + 1; }).slice(0, 6).map((e) => String(e.className || e.tagName).slice(0, 40)) : [],
    words_delivered_on_email: /ACCEPTED BY SENDGRID/.test(win.innerText) && /EMAIL[^\n]*DELIVERED/.test(win.innerText),
  };
}"""

# ── The pointer pass (UX-CANON C) ──────────────────────────────────────
# EVERY Button in the window (body, head verbs, footer, menus when open) and
# every proposed ledger line (a pick is a control), NINE points each: centre,
# four edge midpoints, four corners, inset 1 px -- the painted face at 1440,
# the 44 x 44 target at 393. Each point: `elementFromPoint` AND a real
# `page.mouse.move` whose `pointermove` target is recorded.
CONTROLS = r"""(anchorSel) => {
  const anchor = document.querySelector(anchorSel);
  const win = anchor ? anchor.closest('.desk-window') : null;
  if (!win) return [];
  window.__scrollSnap = [...document.querySelectorAll('*')].filter((e) => e.scrollTop || e.scrollLeft).map((e) => [e, e.scrollTop, e.scrollLeft]);
  window.__pm = null;
  if (!window.__pmHooked) { document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, true); window.__pmHooked = true; }
  const menus = [...document.querySelectorAll('[role=menu]')];
  const btns = [...win.querySelectorAll('.btn, .btn--chrome, [data-p10] .surface-ledger-line, [data-p10] select, [data-p10] input:not([type=hidden]):not([type=checkbox]), [data-p10] label.gadget-check-token'),
    ...menus.flatMap((m) => [...m.querySelectorAll('button, [role=menuitem]')])]
    .filter((b) => b.getBoundingClientRect().width);
  return btns.map((b, i) => {
    b.dataset.probe = String(i);
    return {i, text: (b.innerText || b.getAttribute('aria-label') || b.value || '').trim().slice(0, 30),
      in_foot: !!b.closest('.desk-surface-foot, .surface-footer'), in_menu: !!b.closest('[role=menu]'),
      kind: b.matches('.surface-ledger-line') ? 'row' : b.tagName.toLowerCase(),
      touched: !!b.closest('[data-p10]')};
  });
}"""

POINTS9 = r"""([i, width]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  b.scrollIntoView({block: 'center', inline: 'nearest'});
  const r = b.getBoundingClientRect();
  const cy = r.top + r.height / 2, cx = r.left + r.width / 2;
  const w = width <= 420 ? Math.max(44, r.width) : r.width, h = width <= 420 ? Math.max(44, r.height) : r.height;
  const L = cx - w / 2 + 1, R = cx + w / 2 - 1, T = cy - h / 2 + 1, B = cy + h / 2 - 1;
  return {face: {w: +r.width.toFixed(1), h: +r.height.toFixed(1)}, target: {w: +w.toFixed(1), h: +h.toFixed(1)},
    points: [[cx, cy], [cx, T], [R, cy], [cx, B], [L, cy], [L, T], [R, T], [L, B], [R, B]]};
}"""

HIT = r"""([i, x, y]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  const el = document.elementFromPoint(x, y);
  return {efp: !!el && b.contains(el), hit: el ? String(el.className && typeof el.className === 'string' ? el.className : el.tagName).split(' ')[0] : null};
}"""
PM_OWNED = r"""([i]) => { const b = document.querySelector(`[data-probe="${i}"]`); return !!window.__pm && b.contains(window.__pm); }"""
RESTORE = r"""() => { for (const [e, t, l] of (window.__scrollSnap || []).reverse()) { e.scrollTop = t; e.scrollLeft = l; } }"""
NAMES = ["centre", "top", "right", "bottom", "left", "top-left", "top-right", "bottom-left", "bottom-right"]


def pointer_pass(page, width: int, anchor: str) -> list[dict]:
    out = []
    for c in page.evaluate(CONTROLS, anchor):
        geo = page.evaluate(POINTS9, [c["i"], width])
        pts = []
        for name, (x, y) in zip(NAMES, geo["points"]):
            hit = page.evaluate(HIT, [c["i"], x, y])
            page.mouse.move(x, y)
            pm = page.evaluate(PM_OWNED, [c["i"]])
            pts.append({"at": name, "efp": hit["efp"], "pointer": pm, "hit": hit["hit"]})
        out.append({**{k: c[k] for k in ("text", "in_foot", "in_menu", "kind", "touched")}, "face": geo["face"],
                    "target": geo["target"], "owned": all(p["efp"] and p["pointer"] for p in pts),
                    "failed_points": [p for p in pts if not (p["efp"] and p["pointer"])]})
    page.mouse.move(1, 1)
    page.evaluate(RESTORE)
    page.wait_for_timeout(100)
    return out


def main() -> None:
    home = tempfile.mkdtemp(prefix="philo10-04-canvas-")
    hub_port, today_port = free_port(), free_port()
    canvas_port = int(os.environ.get("CANVAS_PORT", "4451"))
    hub_url = f"http://127.0.0.1:{hub_port}"
    hub = subprocess.Popen(
        [str(REPO / ".venv/bin/python"), "scripts/graph_walk.py", "serve", "--port", str(hub_port), "--token", TOKEN],
        cwd=REPO, env={**os.environ, "HOME": home}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True,
    )
    vite_bin = str(WEB / "node_modules/.bin/vite")
    vites = [
        subprocess.Popen([vite_bin, "--config", str(HERE / "vite.config.mjs")], cwd=WEB,
                         env={**os.environ, "HUB": hub_url, "CANVAS_PORT": str(canvas_port), "CANVAS_MODE": "proposal"},
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
        subprocess.Popen([vite_bin, "--config", str(HERE / "vite.config.mjs")], cwd=WEB,
                         env={**os.environ, "HUB": hub_url, "CANVAS_PORT": str(today_port), "CANVAS_MODE": "today"},
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
    ]
    facts_send: dict[str, dict] = {}
    facts_dest: dict[str, dict] = {}
    errors: list[str] = []
    NET: list[str] = []
    try:
        wait_http(f"{hub_url}/api/projects", {"Authorization": f"Bearer {TOKEN}"})
        wait_http(f"http://127.0.0.1:{canvas_port}/")
        wait_http(f"http://127.0.0.1:{today_port}/")

        # ── Seed through the real routes ──
        seed: dict = {"home": home}
        st, p = hub_api(hub_url, "POST", "/api/projects", {"name": NAME})
        pid = p["project"]["id"]
        seed["project"] = [st, pid]
        for title, typ in (("Cutover rehearsal", "milestone"), ("Old ledger freeze slips", "risk")):
            hub_api(hub_url, "POST", f"/api/projects/{pid}/items", {"item_type": typ, "title": title})
        ids = []
        for _ in range(2):
            s, d = hub_api(hub_url, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})
            s2, pub = hub_api(hub_url, "POST", f"/api/updates/{d['update']['id']}/publish", {})
            ids.append({"draft": s, "publish": s2, "id": d["update"]["id"], "lifecycle": (pub or {}).get("update", {}).get("lifecycle")})
        seed["updates"] = ids
        upd_a, upd_b = ids[1]["id"], ids[0]["id"]   # A = the newer (first in the list)
        s, r = hub_api(hub_url, "POST", "/api/providers/jira/connections", {"site": "acme.atlassian.net", "email": "karol@acme.io"})
        seed["jira_account"] = [s, (r or {}).get("state") if isinstance(r, dict) else r]
        facts_send["_seed"] = facts_dest["_seed"] = seed
        print("seed", json.dumps(seed)[:400], flush=True)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            def open_page(origin: str, width: int, height: int):
                ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2)
                ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append(f"{width} pageerror: {e}"))
                page.on("response", lambda r: NET.append(f"{r.status} {r.request.method} {r.url.split('?')[0][-70:]}") if "/api/" in r.url else None)
                page.on("requestfailed", lambda r: NET.append(f"FAILED {r.url[-70:]} {r.failure}"))
                page.on("console", lambda m: errors.append(f"{width} console: {m.text[:200]}") if m.type == "error" else None)
                page.goto(f"{origin}/?token={TOKEN}", wait_until="load")
                boot(page)
                return ctx, page

            def boot(page):
                page.locator(".chair").wait_for(timeout=60_000)
                page.wait_for_timeout(800)
                if page.get_by_role("button", name="Continue later", exact=True).count():
                    page.get_by_role("button", name="Continue later", exact=True).first.click()
                    page.wait_for_timeout(800)

            def open_room(page):
                page.locator("[aria-controls=desk-tool-shelf]").first.click()
                page.locator("[aria-controls=desk-palette-listbox]").fill(NAME)
                page.get_by_text(f"Open {NAME}").first.click(timeout=20_000)
                page.locator("[data-testid=room-body]").wait_for(timeout=20_000)
                page.wait_for_timeout(1200)

            def enter_updates(page):
                page.locator("[data-testid=updates-verb]").click()
                page.locator("[data-testid=update-list]").wait_for(timeout=15_000)
                page.wait_for_timeout(700)

            def open_update(page, uid: str):
                page.locator(f"[data-testid=update-list-item]:has([data-update-id='{uid}'])").first.click()
                page.locator("[data-testid=update-editor]").wait_for(timeout=15_000)
                page.wait_for_timeout(900)

            def go_back(page):
                page.locator("[data-testid=update-verb-back]").click()
                page.locator("[data-testid=update-list]").wait_for(timeout=10_000)
                page.wait_for_timeout(500)

            def reopen(page, uid: str):
                page.reload(wait_until="load")
                boot(page)
                open_room(page)
                enter_updates(page)
                open_update(page, uid)

            def settings_front(page):
                page.evaluate("window.__p10OpenConnections()")
                page.locator("[data-testid=destinations]").wait_for(timeout=20_000)
                page.wait_for_timeout(900)

            def seat(page, sel: str):
                # Scroll the element to the top of its scroller, below the sticky head verbs.
                page.evaluate("""(sel) => { const el = document.querySelector(sel); if (!el) return;
                  el.scrollIntoView({block: 'start'});
                  let s = el.parentElement; while (s && !(s.scrollHeight > s.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) s = s.parentElement;
                  if (s) s.scrollTop = Math.max(0, s.scrollTop - 64); }""", sel)
                page.wait_for_timeout(300)

            def shoot(page, out: Path, facts: dict, board: str, width: int, anchor: str, extra: dict | None = None, focus: str | None = None):
                if focus:
                    seat(page, focus)
                page.mouse.move(1, 1)
                page.wait_for_timeout(300)
                key = f"{board}-{width}"
                page.screenshot(path=str(out / f"{key}.png"))
                f = page.evaluate(FACTS, anchor)
                f["pointer"] = pointer_pass(page, width, anchor)
                if focus:   # the pointer pass restores scroll; re-seat for the next step
                    seat(page, focus)
                if extra:
                    f.update(extra)
                facts[key] = f
                bad = [c for c in f["pointer"] if c["touched"] and not c["owned"]]
                print(key, "small", len(f["small_text"]["proposal"]), len(f["small_text"]["inherited"]), "raw", len(f["raw_buttons"]["proposal"]), len(f["raw_buttons"]["inherited"]),
                      "minC", f["min_contrast"], "ovf", f["h_overflow"], f["body_overflow_x"], "ptr-bad", len(bad), flush=True)

            UP = "[data-testid=update-posture]"
            DS = "[data-testid=destinations]"
            SS, DD = SEND / "shots", DEST / "shots"
            SS.mkdir(parents=True, exist_ok=True)
            DD.mkdir(parents=True, exist_ok=True)
            today = f"http://127.0.0.1:{today_port}"
            canvas = f"http://127.0.0.1:{canvas_port}"

            def confirm(loc, armed: str):
                # ConfirmVerb disarms after 3 s; the pointer pass outlasts that.
                if loc.inner_text().strip() != armed:
                    loc.click()
                    page_of(loc).wait_for_timeout(150)
                loc.click()

            def page_of(loc):
                return loc.page

            def pick(page, name: str):
                row = page.locator(f"[data-testid=destination-row]:has([data-destination='{name}'])").first
                row.click()
                page.locator(f"[data-testid=send-open][data-destination='{name}'] [data-testid=send-preview]").wait_for(timeout=10_000)
                page.wait_for_timeout(400)

            def send_verb(page, name: str):
                return page.locator(f"[data-testid=send-open][data-destination='{name}'] [data-testid=send-verbs] .btn").first

            def open_sel(name: str) -> str:
                return f"[data-testid=send-open][data-destination='{name}']"

            def row_sel(name: str) -> str:
                return f"[data-testid=destination-row]:has([data-destination='{name}'])"

            def dest_form_fill(page, channel: str, fields: dict[str, str], synced: bool = False):
                form = page.locator("[data-testid=dest-form]").last
                form.locator("select[aria-label=Channel]").select_option(channel)
                page.wait_for_timeout(200)
                for tid, val in fields.items():
                    form.locator(f"[data-testid={tid}]").fill(val)
                if synced:
                    form.locator("label.gadget-check-token").click()
                page.wait_for_timeout(250)

            def dest_save(page, expect_refused: bool = False):
                page.locator("[data-testid=dest-form] [data-testid=dest-save]").last.click()
                if expect_refused:
                    page.locator("[data-testid=dest-refused]").wait_for(timeout=10_000)
                else:
                    page.wait_for_function("!document.querySelector('[data-testid=dest-refused]')", timeout=10_000)
                page.wait_for_timeout(600)

            for width, height in WIDTHS:
                # ── TODAY ──
                ctx, page = open_page(today, width, height)
                open_room(page)
                enter_updates(page)
                open_update(page, upd_a)
                shoot(page, SS, facts_send, "0-today", width, UP)
                ctx.close()

                # ── PROPOSAL ──
                ctx, page = open_page(canvas, width, height)
                open_room(page)
                enter_updates(page)
                open_update(page, upd_a)
                page.locator("[data-testid=send-none]").wait_for(timeout=15_000)
                shoot(page, SS, facts_send, "1-no-destination", width, UP, focus="[data-testid=send-well]")
                page.locator("[data-testid=send-add-destination]").click()
                page.locator("[data-testid=destinations]").wait_for(timeout=20_000)
                page.wait_for_timeout(1200)
                # Canvas B: the Destinations group, reached by the Room's verb.
                shoot(page, DD, facts_dest, "1-empty-from-room", width, DS, focus="[data-testid=destinations]")
                dest_form_fill(page, "file", {"dest-folder": "/Users/karol/Reports/Payments"})
                shoot(page, DD, facts_dest, "2-add-folder", width, DS, focus="[data-testid=destinations]")
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "file", {"dest-folder": "/Users/karol/Library/CloudStorage/Dropbox/Updates"}, synced=True)
                shoot(page, DD, facts_dest, "3-add-synced-folder", width, DS, focus="[data-testid=dest-form]")
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "github", {"dest-repo": "karol/payments-ops", "dest-number": "42"})
                shoot(page, DD, facts_dest, "4-add-github", width, DS, focus="[data-testid=dest-form]")
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "jira", {"dest-key": "PAY-118, PAY-119"})
                dest_save(page, expect_refused=True)
                shoot(page, DD, facts_dest, "5-jira-one-key", width, DS, focus="[data-testid=dest-form]")
                page.locator("[data-testid=dest-form] [data-testid=dest-key]").last.fill("PAY-118")
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "confluence", {"dest-space": "98304"})
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "email", {"dest-from": "karol@acme.io", "dest-to": "lena@acme.io, tomas@acme.io"})
                form = page.locator("[data-testid=dest-form]").last
                form.locator("input[aria-label='From name']").fill("Karol")
                form.locator("input[aria-label=Cc]").fill("priya@acme.io")
                form.locator("[data-testid=dest-key-row] .btn", has_text="Replace").click()
                form.locator("[data-testid=dest-key-row] input[type=password]").fill("SG.canvas-fixture-not-a-key")
                form.locator("[data-testid=dest-key-row] input[type=password]").press("Enter")
                page.wait_for_timeout(500)
                shoot(page, DD, facts_dest, "6-add-email-key-set", width, DS, focus="[data-testid=dest-form]",
                      extra={"key_text_on_face": "canvas-fixture" in page.locator(DS).inner_text()})
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "email", {"dest-from": "updates@acme.io", "dest-to": "board@acme.io"})
                page.locator("[data-testid=dest-form]").last.locator("input[aria-label='From name']").fill("Payments updates")
                dest_save(page)
                shoot(page, DD, facts_dest, "7-list", width, DS, focus="[data-testid=destinations]")
                page.locator("[data-testid=dest-row]:has([data-destination='karol/payments-ops #42'])").click()
                page.wait_for_timeout(300)
                page.locator("[data-testid=dest-check]").click()
                page.locator("[data-testid=dest-check-result]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, DD, facts_dest, "8-row-open-checked", width, DS, focus="[data-testid=dest-open]")
                # Edit = park + new.
                page.locator("[data-testid=dest-row]:has([data-destination='Jira PAY-118'])").click()
                page.locator("[data-testid=dest-edit]").click()
                page.locator("[data-testid=dest-form] [data-testid=dest-key]").fill("PAY-121")
                page.locator("[data-testid=dest-form] [data-testid=dest-name]").fill("Jira PAY-121")
                shoot(page, DD, facts_dest, "9-edit", width, DS, focus="[data-testid=dest-form]")
                dest_save(page)
                page.locator("[data-testid=dest-parked] summary").click()
                page.wait_for_timeout(300)
                shoot(page, DD, facts_dest, "10-edited-old-parked", width, DS, focus="[data-testid=dest-parked]")
                # Remove = park.
                page.locator("[data-testid=dest-row]:has([data-destination='Email board@acme.io'])").click()
                page.locator("[data-testid=dest-remove]").click()
                page.wait_for_timeout(200)
                shoot(page, DD, facts_dest, "11-remove-armed", width, DS, focus="[data-testid=dest-open]")
                confirm(page.locator("[data-testid=dest-remove]"), "Remove?")
                page.wait_for_timeout(800)
                if not page.locator("[data-testid=dest-parked] details[open]").count():
                    page.locator("[data-testid=dest-parked] summary").click()
                page.wait_for_timeout(300)
                shoot(page, DD, facts_dest, "12-removed-parked", width, DS, focus="[data-testid=dest-parked]")

                # ── Canvas A: SEND ── (close Settings so the Send boards show the Room alone)
                closer = page.locator("[aria-label^='Close Settings']")
                if closer.count():
                    closer.first.click()
                    page.wait_for_timeout(500)
                reopen(page, upd_a)
                page.locator("[data-testid=destination-row]").first.wait_for(timeout=15_000)
                shoot(page, SS, facts_send, "2-destinations", width, UP, focus="[data-testid=send-well]")
                pick(page, "Folder Payments")
                shoot(page, SS, facts_send, "3-picked-folder", width, UP, focus=open_sel("Folder Payments"))
                send_verb(page, "Folder Payments").click()
                page.locator(f"{row_sel('Folder Payments')} .surface-state-chip[data-state=success]").first.wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "4-saved-folder", width, UP, focus="[data-p10=history]")
                pick(page, "karol/payments-ops #42")
                shoot(page, SS, facts_send, "5-picked-github", width, UP, focus=open_sel("karol/payments-ops #42"))
                n0 = page.evaluate("window.__p10Calls.length")
                page.evaluate("window.__p10Hold = true")
                send_verb(page, "karol/payments-ops #42").dblclick()
                page.wait_for_timeout(400)
                shoot(page, SS, facts_send, "6-sending", width, UP, focus=open_sel("karol/payments-ops #42"))
                page.evaluate("window.__p10Release && window.__p10Release()")
                page.wait_for_timeout(1200)
                calls = page.evaluate("window.__p10Calls")
                shoot(page, SS, facts_send, "7-posted-github", width, UP, focus="[data-p10=history]",
                      extra={"double_click_calls": calls[n0:],
                             "dispatches_after_double_click": sum(1 for c in calls[n0:] if c["dispatched"])})
                pick(page, "Jira PAY-121")
                shoot(page, SS, facts_send, "8-picked-jira", width, UP, focus=open_sel("Jira PAY-121"))
                page.evaluate("window.__p10Next = {kind: 'unknown', code: 'no_answer'}")
                send_verb(page, "Jira PAY-121").click()
                page.locator("[data-testid=send-last-unknown]").first.wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "9-unknown-jira", width, UP, focus=open_sel("Jira PAY-121"))
                pick(page, "Confluence space 98304")
                shoot(page, SS, facts_send, "10-picked-confluence", width, UP, focus=open_sel("Confluence space 98304"))
                send_verb(page, "Confluence space 98304").click()
                page.locator("[data-testid=send-refused]").first.wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "11-refused-confluence-sign-in", width, UP, focus=open_sel("Confluence space 98304"))
                pick(page, "Email lena@acme.io")
                shoot(page, SS, facts_send, "12-picked-email", width, UP, focus=open_sel("Email lena@acme.io"))
                page.evaluate("window.__p10Next = {kind: 'failed', code: 'sender_not_verified'}")
                send_verb(page, "Email lena@acme.io").click()
                page.locator("[data-testid=send-failed]").first.wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "13-failed-email-sender", width, UP, focus=open_sel("Email lena@acme.io"))
                send_verb(page, "Email lena@acme.io").click()
                page.locator(f"{row_sel('Email lena@acme.io')} .surface-state-chip[data-state=success]").nth(1).wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "14-accepted-by-sendgrid", width, UP, focus="[data-p10=history]")
                page.evaluate("window.__p10GhLogin = 'kpersonal'")
                pick(page, "karol/payments-ops #42")
                send_verb(page, "karol/payments-ops #42").click()
                page.locator("[data-testid=send-refused][data-code=github_identity_changed]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "15-refused-github-account", width, UP, focus=open_sel("karol/payments-ops #42"))
                page.evaluate("window.__p10GhLogin = 'kwork'")
                # The lost answer, bound to update A (Phase 9 r2 F1).
                pick(page, "Folder Updates")
                page.evaluate("window.__p10LoseNext = true")
                send_verb(page, "Folder Updates").click()
                page.locator("[data-testid=send-lost]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "16-lost-answer-a", width, UP, focus=open_sel("Folder Updates"))
                go_back(page)
                open_update(page, upd_b)
                b_state = page.evaluate("""() => ({lost: !!document.querySelector('[data-testid=send-lost]'),
                  retry: !!document.querySelector('[data-testid=send-retry]'), open: document.querySelectorAll('[data-testid=send-open]').length,
                  history: document.querySelectorAll('[data-testid=delivery-row]').length})""")
                shoot(page, SS, facts_send, "17-update-b-clean", width, UP, focus="[data-testid=send-well]", extra={"b_state": b_state})
                go_back(page)
                open_update(page, upd_a)
                page.wait_for_timeout(600)
                shoot(page, SS, facts_send, "18-back-on-a-retry", width, UP, focus=open_sel("Folder Updates"))
                page.locator("[data-testid=send-retry]").click()
                page.locator("[data-testid=send-lost]").wait_for(state="detached", timeout=10_000)
                page.wait_for_timeout(600)
                calls = page.evaluate("window.__p10Calls")
                lost_key = [c for c in calls if c.get("dispatched")][-1]["command_id"]
                shoot(page, SS, facts_send, "19-retried-one-dispatch", width, UP, focus="[data-p10=history]", extra={
                    "calls_with_lost_key": [c for c in calls if c["command_id"] == lost_key],
                    "dispatches_with_lost_key": sum(1 for c in calls if c["command_id"] == lost_key and c["dispatched"]),
                    "b_calls": 0})
                # A restart during dispatching.
                pick(page, "Jira PAY-121")
                page.evaluate("window.__p10CrashNext = true")
                send_verb(page, "Jira PAY-121").click()
                page.wait_for_timeout(800)
                reopen(page, upd_a)
                page.wait_for_timeout(600)
                shoot(page, SS, facts_send, "20-unknown-after-restart", width, UP, focus="[data-p10=history]",
                      extra={"rows": page.evaluate("window.__p10Dump().sends.map(s => [s.destination_name, s.state, s.reason])")})
                # PREPARED by the steward and by a connected agent.
                page.evaluate(f"""async () => {{
                  await window.__p10Prepare({{update_id: '{upd_a}', destination_name: 'karol/payments-ops #42', by_kind: 'steward', by_identity: 'steward'}});
                  await window.__p10Prepare({{update_id: '{upd_a}', destination_name: 'Folder Payments', by_kind: 'agent', by_identity: 'codex-desk'}});
                  await window.__p10Prepare({{update_id: '{upd_a}', destination_name: 'Email lena@acme.io', by_kind: 'agent', by_identity: 'codex-desk'}});
                }}""")
                reopen(page, upd_a)
                page.locator("[data-testid=prepared-row]").first.wait_for(timeout=10_000)
                shoot(page, SS, facts_send, "21-prepared", width, UP, focus="[data-testid=send-well]")
                page.locator("li.surface-ledger-row:has([data-testid=prepared-row] [data-destination='karol/payments-ops #42']) [data-testid=prepared-send]").click()
                page.wait_for_function("document.querySelectorAll('[data-testid=prepared-row]').length === 2", timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "22-prepared-sent", width, UP, focus="[data-testid=send-well]")
                page.evaluate("window.__p10Move('Folder Payments', '/Volumes/Archive/Payments')")
                page.locator("li.surface-ledger-row:has([data-testid=prepared-row] [data-destination='Folder Payments']) [data-testid=prepared-send]").click()
                page.locator("[data-testid=send-refused][data-code=destination_changed]").wait_for(timeout=10_000)
                ids_now = page.evaluate("window.__p10Dump().destinations.filter(d => d.name === 'Email lena@acme.io' && d.state === 'active').map(d => d.id)")
                page.evaluate(f"fetch('/api/channels/destinations/{ids_now[0]}/park', {{method: 'POST', body: '{{}}'}})")
                page.wait_for_timeout(300)
                page.locator("li.surface-ledger-row:has([data-testid=prepared-row] [data-destination='Email lena@acme.io']) [data-testid=prepared-send]").click()
                page.locator("[data-testid=send-refused][data-code=destination_parked]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "23-prepared-destination-changed", width, UP, focus="[data-testid=send-well]")
                page.locator("li.surface-ledger-row:has([data-testid=prepared-row] [data-destination='Folder Payments']) [data-testid=prepared-discard]").click()
                page.wait_for_timeout(200)
                shoot(page, SS, facts_send, "24-discard-armed", width, UP, focus="li.surface-ledger-row:has([data-testid=prepared-row] [data-destination='Folder Payments'])")
                confirm(page.locator("li.surface-ledger-row:has([data-testid=prepared-row] [data-destination='Folder Payments']) [data-testid=prepared-discard]"), "Discard?")
                page.wait_for_function("document.querySelectorAll('[data-testid=prepared-row]').length === 1", timeout=10_000)
                page.wait_for_timeout(400)
                shoot(page, SS, facts_send, "25-discarded", width, UP, focus="[data-testid=send-well]")
                # The manual channel, kept.
                page.locator("[data-testid=deliver-to]").fill("Priya")
                page.locator("[data-testid=deliver-verb]").click()
                page.wait_for_timeout(1200)
                shoot(page, SS, facts_send, "26-history-several", width, UP, focus="[data-p10=history]")
                go_back(page)
                page.wait_for_timeout(800)
                shoot(page, SS, facts_send, "27-list-chips", width, UP)
                page.locator("[data-testid=update-verb-draft-deterministic]").click()
                page.locator("[data-testid=update-editor][data-lifecycle=draft]").wait_for(timeout=20_000)
                page.wait_for_timeout(800)
                shoot(page, SS, facts_send, "28-draft-no-send", width, UP)
                ctx.close()
            browser.close()
    finally:
        for v in vites:
            v.terminate()
        hub.terminate()
        try:
            hub.wait(timeout=10)
        except Exception:
            hub.kill()
        # Law (2026-09-28): a run removes its own scratch HOME.
        shutil.rmtree(home, ignore_errors=True)
        # Merge with an earlier ONLY_WIDTH run's facts; this run's keys win.
        tag = "_browser_errors_" + "_".join(str(w) for w, _ in WIDTHS)
        for path, facts in ((SEND / "shots" / "facts.json", facts_send), (DEST / "shots" / "facts.json", facts_dest)):
            path.parent.mkdir(parents=True, exist_ok=True)
            prior = json.loads(path.read_text()) if path.exists() else {}
            path.write_text(json.dumps({**prior, **facts, tag: errors}, indent=1, ensure_ascii=False) + "\n")
        print("errors:", len(errors), file=sys.stderr)


if __name__ == "__main__":
    main()
