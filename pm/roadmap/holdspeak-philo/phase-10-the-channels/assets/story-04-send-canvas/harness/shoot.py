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
facts.json beside them. Each width runs on its own hub and HOME; ONLY_WIDTH=393 limits the run to one width.
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
  // Unrounded (Codex Astra r1 F7): compare before rounding; record the element.
  const ratio = (a, b) => { const la = lum(a), lb = lum(b); return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); };
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
    history_outcomes: [...win.querySelectorAll('[data-testid=delivery-row] [data-outcome]')].map((e) => e.dataset.outcome),
    prepared_results: text('[data-testid=prepared-result]'),
    list_chips: text('[data-testid=update-list-item]'),
    dest_head: (() => { const s = win.querySelector('[data-p10=destinations] .gadget-group-label'); return s ? s.innerText.trim() : null; })(),
    dest_parked: text('[data-testid=dest-parked-row]'),
    egress_chips: [...win.querySelectorAll('[data-p10] .gadget-chip-egress')].map((e) => `${e.innerText.trim()}:${e.dataset.scope || ''}`),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
    small_text: small,
    min_contrast: texts.length ? Math.min(...texts.map((t) => t.ratio)) : null,
    min_contrast_el: texts.length ? texts.reduce((m, t) => (t.ratio < m.ratio ? t : m)) : null,
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
# The on-screen law (Phase 9; Codex Astra r1 F3): each board's NAMED elements
# are in the viewport, inside every clipping ancestor, and on top at their
# centre and two inner corners. Offscreen DOM text does not count.
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
  const inside = r.top >= top - 1 && r.bottom <= bottom + 1 && r.left >= left - 1 && r.right <= right + 1;
  const pts = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 2, r.top + 2], [r.right - 2, r.bottom - 2]];
  const hit = pts.every(([x, y]) => { const h = document.elementFromPoint(x, y); return !!h && (e.contains(h) || h.contains(e)); });
  return {sel, ok: inside && hit, why: inside ? (hit ? '' : 'covered') : 'clipped', rect: [Math.round(r.top), Math.round(r.bottom)], text: (e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, 60)};
})"""

PM_OWNED = r"""([i]) => { const b = document.querySelector(`[data-probe="${i}"]`); return !!window.__pm && b.contains(window.__pm); }"""
RESTORE = r"""() => { for (const [e, t, l] of (window.__scrollSnap || []).reverse()) { e.scrollTop = t; e.scrollLeft = l; } }"""
NAMES = ["centre", "top", "right", "bottom", "left", "top-left", "top-right", "bottom-left", "bottom-right"]


def pointer_pass(page, width: int, anchor: str) -> list[dict]:
    out = []
    def probe(i: int):
        geo = page.evaluate(POINTS9, [i, width])
        pts = []
        for name, (x, y) in zip(NAMES, geo["points"]):
            hit = page.evaluate(HIT, [i, x, y])
            page.mouse.move(x, y)
            pm = page.evaluate(PM_OWNED, [i])
            pts.append({"at": name, "efp": hit["efp"], "pointer": pm, "hit": hit["hit"]})
        return geo, pts

    for c in page.evaluate(CONTROLS, anchor):
        geo, pts = probe(c["i"])
        retried = None
        if not all(p["efp"] and p["pointer"] for p in pts):
            # A control can change size under the probe (ConfirmVerb disarms after
            # 3 s: "Remove?" -> "Remove"). Measure it again and probe once more at
            # its current size; both results are recorded.
            retried = {"face_before": geo["face"], "failed_before": [p for p in pts if not (p["efp"] and p["pointer"])]}
            geo, pts = probe(c["i"])
        out.append({**{k: c[k] for k in ("text", "in_foot", "in_menu", "kind", "touched")}, "face": geo["face"],
                    "target": geo["target"], "owned": all(p["efp"] and p["pointer"] for p in pts),
                    "failed_points": [p for p in pts if not (p["efp"] and p["pointer"])], "retried": retried})
    page.mouse.move(1, 1)
    page.evaluate(RESTORE)
    page.wait_for_timeout(100)
    return out


def long_folder(root: Path) -> Path:
    """Story 01's UNKNOWN recipe: a folder whose path leaves no room for the file's name (ENAMETOOLONG)."""
    limit = os.pathconf("/", "PC_PATH_MAX")
    folder = root.resolve()
    while len(str(folder)) < limit - 25:
        folder = folder / ("a" * min(100, limit - 25 - len(str(folder)) - 1 or 1))
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def run(widths: list[tuple[int, int]]) -> list[str]:
    """One width, its own hub, HOME and fixtures (Codex Astra r3 F4: a shared hub
    carried the desktop run's history into the phone run)."""
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
    invisible: list[str] = []
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
        for _ in range(3):
            s, d = hub_api(hub_url, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})
            s2, pub = hub_api(hub_url, "POST", f"/api/updates/{d['update']['id']}/publish", {})
            ids.append({"draft": s, "publish": s2, "id": d["update"]["id"], "lifecycle": (pub or {}).get("update", {}).get("lifecycle")})
        seed["updates"] = ids
        upd_c, upd_b, upd_a = ids[0]["id"], ids[1]["id"], ids[2]["id"]   # A = the newest (first in the list)
        # Update C carries story 01's REAL records for board 0: a real file send
        # (SENT), a real UNKNOWN (story 01's ENAMETOOLONG recipe) and a real manual row.
        real = {}
        out = Path(home) / "Reports" / "Team"
        out.mkdir(parents=True)
        for name, folder in (("Team folder", out), ("Long path folder", long_folder(Path(home) / "deep"))):
            s1, dst = hub_api(hub_url, "POST", "/api/channels/destinations", {"name": name, "channel": "file", "folder": str(folder)})
            s2, prep = hub_api(hub_url, "POST", "/api/channels/sends", {"update_id": upd_c, "destination_id": dst["destination"]["id"]})
            s3, sent = hub_api(hub_url, "POST", "/api/channels/send", {"send_id": prep["send"]["id"]})
            real[name] = [s1, s2, s3, (sent or {}).get("send", {}).get("state") if isinstance(sent, dict) else sent]
        real["manual"] = hub_api(hub_url, "POST", f"/api/updates/{upd_c}/delivered", {"delivered_to": "Priya", "command_id": "seed-manual-1"})[0]
        _, ups = hub_api(hub_url, "GET", f"/api/projects/{pid}/updates")
        real["history"] = [(d.get("delivered_to"), d.get("channel"), d.get("outcome")) for u in ups["updates"] if u["id"] == upd_c for d in u["deliveries"]]
        seed["story01_real_on_c"] = real
        s, r = hub_api(hub_url, "POST", "/api/providers/jira/connections", {"site": "acme.atlassian.net", "email": "karol@acme.io"})
        seed["jira_account"] = [s, (r or {}).get("state") if isinstance(r, dict) else r]
        facts_send["_seed"] = facts_dest["_seed"] = seed
        print("seed", json.dumps(seed)[:600], flush=True)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            def open_page(origin: str, width: int, height: int):
                ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2)
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append(f"{width} pageerror: {e}"))
                page.on("console", lambda m: errors.append(f"{width} console: {m.text[:200]}")
                        if m.type == "error" and "Failed to fetch" not in m.text else None)
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
                # A reload: a restart of the page (board 25), or opening the Room later (board 26).
                page.reload(wait_until="load")
                boot(page)
                open_room(page)
                enter_updates(page)
                open_update(page, uid)

            def open_settings(page):
                # The Dock's Settings, as the Door opens it (harness navigation, stated in shim.ts).
                page.evaluate("window.__p10OpenConnections()")
                page.locator("[data-testid=destinations]").wait_for(timeout=20_000)
                page.wait_for_timeout(900)

            def close_settings(page):
                page.locator("[aria-label^='Close Settings']").first.click()
                page.wait_for_timeout(600)

            def seat(page, sel: str):
                # Scroll the element to the top of its scroller, below the sticky head verbs;
                # "CENTER:<sel>" centres it instead.
                if sel.startswith("CENTER:"):
                    page.evaluate("(sel) => { const el = document.querySelector(sel); if (el) el.scrollIntoView({block: 'center'}); }", sel[7:])
                    page.wait_for_timeout(300)
                    return
                page.evaluate("""(sel) => { const el = document.querySelector(sel); if (!el) return;
                  el.scrollIntoView({block: 'start'});
                  let s = el.parentElement; while (s && !(s.scrollHeight > s.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) s = s.parentElement;
                  if (s) s.scrollTop = Math.max(0, s.scrollTop - 64); }""", sel)
                page.wait_for_timeout(300)

            def shoot(page, out: Path, facts: dict, board: str, width: int, anchor: str, named: list[str],
                      seat_on: str | None = "FIRST", extra: dict | None = None):
                """seat_on: "FIRST" seats the first named element; None = no scroll at all (the
                arrival and the return prove their own position)."""
                target = named[0] if seat_on == "FIRST" else seat_on
                if target:
                    seat(page, target)
                page.mouse.move(1, 1)
                page.wait_for_timeout(300)
                key = f"{board}-{width}"
                vis = page.evaluate(VISIBLE, named)
                page.screenshot(path=str(out / f"{key}.png"))
                masked = masked_sha(page)
                f = page.evaluate(FACTS, anchor)
                f["named"] = vis
                f["masked_sha"] = masked
                f["pointer"] = pointer_pass(page, width, anchor)
                if target:   # the pointer pass restores scroll; re-seat for the next step
                    seat(page, target)
                if extra:
                    f.update(extra)
                facts[key] = f
                bad = [c for c in f["pointer"] if c["touched"] and not c["owned"]]
                hidden = [v for v in vis if not v["ok"]]
                if hidden:
                    invisible.append(f"{key}: {hidden}")
                print(key, "small", len(f["small_text"]["proposal"]), len(f["small_text"]["inherited"]), "raw", len(f["raw_buttons"]["proposal"]), len(f["raw_buttons"]["inherited"]),
                      "minC", f["min_contrast"] and round(f["min_contrast"], 4), "ovf", f["h_overflow"], f["body_overflow_x"], "ptr-bad", len(bad),
                      "hidden", [(v["sel"][-40:], v["why"]) for v in hidden], flush=True)

            UP = "[data-testid=update-posture]"
            DS = "[data-testid=destinations]"
            SS, DD = SEND / "shots", DEST / "shots"
            SS.mkdir(parents=True, exist_ok=True)
            DD.mkdir(parents=True, exist_ok=True)
            today = f"http://127.0.0.1:{today_port}"
            canvas = f"http://127.0.0.1:{canvas_port}"

            def masked_sha(page) -> str:
                # The byte fence compares shots with the changing chrome masked: the
                # menu-bar clock (DeskChrome.tsx:104, `.desk-clock`). Codex Astra r2 F3.
                import hashlib
                return hashlib.sha256(page.screenshot(mask=[page.locator(".desk-clock")], mask_color="#000000")).hexdigest()

            def confirm(loc, armed: str):
                # ConfirmVerb disarms after 3 s; the pointer pass outlasts that.
                if loc.inner_text().strip() != armed:
                    loc.click()
                    loc.page.wait_for_timeout(150)
                loc.click()

            def row_sel(name: str) -> str:
                return f"[data-testid=destination-row]:has([data-destination='{name}'])"

            def open_sel(name: str) -> str:
                return f"[data-testid=send-open][data-destination='{name}']"

            def idle(page, name: str):
                # The press has ended: the verb is no longer busy (a busy row ignores a toggle).
                page.wait_for_function("""(sel) => { const b = document.querySelector(sel); return !b || b.getAttribute('aria-busy') !== 'true'; }""",
                                       arg=f"{open_sel(name)} [data-testid=send-verbs] .btn", timeout=10_000)

            def close(page, name: str):
                idle(page, name)
                if page.locator(open_sel(name)).count():
                    page.locator(row_sel(name)).first.click()
                    page.locator(open_sel(name)).wait_for(state="detached", timeout=10_000)

            def pick(page, name: str):
                if not page.locator(open_sel(name)).count():
                    page.locator(row_sel(name)).first.click()
                page.locator(f"{open_sel(name)} [data-testid=send-preview], {open_sel(name)} [data-testid=preview-failed]").first.wait_for(timeout=10_000)
                page.wait_for_timeout(400)

            def send_verb(page, name: str):
                return page.locator(f"{open_sel(name)} [data-testid=send-verbs] .btn").first

            def prep_li(name: str, state: str = "prepared") -> str:
                tid = "prepared-row" if state == "prepared" else "prepared-sending" if state == "dispatching" else "prepared-result"
                return f"li.surface-ledger-row:has([data-testid={tid}] [data-destination='{name}'])"

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

            def dest_open(page, name: str):
                page.locator(f"[data-testid=dest-row]:has([data-destination='{name}'])").click()
                page.wait_for_timeout(300)

            def type_key(page, value: str):
                form = page.locator("[data-testid=dest-form]").last
                form.locator("[data-testid=dest-key-row] .btn", has_text="Replace").click()
                form.locator("[data-testid=dest-key-row] input[type=password]").fill(value)
                form.locator("[data-testid=dest-key-row] input[type=password]").press("Enter")
                page.wait_for_timeout(500)

            for width, height in widths:
                # ── TODAY: story 01's face on its real records (update C) ──
                ctx, page = open_page(today, width, height)
                open_room(page)
                enter_updates(page)
                shoot(page, SS, facts_send, "0a-today-list", width, UP,
                      [f"[data-testid=update-list-item]:has([data-update-id='{upd_c}']) [data-testid=update-unknown-chip]",
                       f"[data-testid=update-list-item]:has([data-update-id='{upd_c}']) [data-testid=update-delivered-chip]"])
                open_update(page, upd_c)
                shoot(page, SS, facts_send, "0b-today-history", width, UP,
                      ["[data-testid=delivery-row]:has([data-outcome=unknown])", "[data-testid=delivery-row]:has([data-outcome=sent])"],
                      seat_on="CENTER:[data-testid=delivery-row]:has([data-outcome=sent])")
                ctx.close()

                # ── PROPOSAL ──
                ctx, page = open_page(canvas, width, height)
                open_room(page)
                enter_updates(page)
                open_update(page, upd_a)
                page.locator("[data-testid=send-none]").wait_for(timeout=15_000)
                shoot(page, SS, facts_send, "1-no-destination", width, UP, ["[data-testid=send-none]", "[data-testid=send-add-destination]"],
                      seat_on="[data-testid=send-well]")

                # The first setup loop, with no harness scroll and no reload (F2).
                page.locator("[data-testid=send-add-destination]").click()
                page.locator("[data-testid=destinations] [data-testid=dest-form]").wait_for(timeout=20_000)
                page.wait_for_timeout(1200)
                shoot(page, DD, facts_dest, "1-arrive-from-room", width, DS,
                      ["[data-testid=destinations] .gadget-group-label", "[data-testid=dest-form] select[aria-label=Channel]"], seat_on=None)
                dest_form_fill(page, "file", {"dest-folder": "/Users/karol/Reports/Payments"})
                shoot(page, DD, facts_dest, "2-add-folder", width, DS,
                      ["[data-testid=dest-folder]", "[data-testid=dest-name]", "[data-testid=dest-save]"])
                dest_save(page)
                close_settings(page)
                page.locator(row_sel("Folder Payments")).wait_for(timeout=10_000)   # the Room read again: no reload
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "2-back-in-the-room", width, UP, [row_sel("Folder Payments")], seat_on=None)

                # ── Canvas B: the rest of the Destinations group ──
                open_settings(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "file", {"dest-folder": "/Users/karol/Library/CloudStorage/Dropbox/Updates"}, synced=True)
                shoot(page, DD, facts_dest, "3-add-synced-folder", width, DS,
                      ["[data-testid=dest-form] label.gadget-check-token", "[data-testid=dest-form-verbs] .gadget-chip-egress"],
                      seat_on="[data-testid=dest-form]")
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "github", {"dest-repo": "karol/payments-ops", "dest-number": "42"})
                shoot(page, DD, facts_dest, "4-add-github", width, DS,
                      ["[data-testid=dest-repo]", "[data-testid=dest-number]", "[data-testid=dest-save]"], seat_on="[data-testid=dest-repo]")
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "jira", {"dest-key": "PAY-118, PAY-119"})
                dest_save(page, expect_refused=True)
                shoot(page, DD, facts_dest, "5-jira-one-key", width, DS,
                      ["[data-testid=dest-key]", "[data-testid=dest-refused]"], seat_on="[data-testid=dest-form]")
                page.locator("[data-testid=dest-form] [data-testid=dest-key]").last.fill("PAY-118")
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "confluence", {"dest-space": "98304"})
                shoot(page, DD, facts_dest, "6-add-confluence", width, DS,
                      ["[data-testid=dest-form] select[aria-label='Confluence account']", "[data-testid=dest-space]", "[data-testid=dest-save]"],
                      seat_on="[data-testid=dest-form]")
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "email", {"dest-from": "karol@acme.io", "dest-to": "lena@acme.io, tomas@acme.io"})
                form = page.locator("[data-testid=dest-form]").last
                form.locator("input[aria-label='From name']").fill("Karol")
                form.locator("input[aria-label=Cc]").fill("priya@acme.io")
                page.evaluate("window.__p10KeyFail = 'email_key_store_not_native'")
                type_key(page, "SG.canvas-fixture-not-a-key")
                page.locator("[data-testid=dest-key-refused]").wait_for(timeout=10_000)
                shoot(page, DD, facts_dest, "7-key-not-saved", width, DS,
                      ["[data-testid=dest-key-row]", "[data-testid=dest-key-refused]"], seat_on="[data-testid=dest-key-row]",
                      extra={"key_text_on_face": "canvas-fixture" in page.locator(DS).inner_text()})
                type_key(page, "SG.canvas-fixture-not-a-key")
                shoot(page, DD, facts_dest, "8-add-email-key-set", width, DS,
                      ["[data-testid=dest-from]", "[data-testid=dest-key-row]", "[data-testid=dest-to]"], seat_on="[data-testid=dest-from]",
                      extra={"key_text_on_face": "canvas-fixture" in page.locator(DS).inner_text()})
                dest_save(page)
                page.locator("[data-testid=dest-add]").click()
                dest_form_fill(page, "email", {"dest-from": "updates@acme.io", "dest-to": "board@acme.io"})
                page.locator("[data-testid=dest-form]").last.locator("input[aria-label='From name']").fill("Payments updates")
                dest_save(page)
                shoot(page, DD, facts_dest, "9-list", width, DS,
                      ["[data-testid=destinations] .gadget-group-label", "[data-testid=dest-row]:has([data-destination='Folder Payments'])",
                       "[data-testid=dest-row]:has([data-destination='karol/payments-ops #42'])"])
                dest_open(page, "karol/payments-ops #42")
                page.locator("[data-testid=dest-check]").click()
                page.locator("[data-testid=dest-check-result]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, DD, facts_dest, "10-row-open-checked", width, DS,
                      ["[data-testid=dest-row]:has([data-destination='karol/payments-ops #42'])", "[data-testid=dest-check-result]"])
                dest_open(page, "Email lena@acme.io")
                page.locator("[data-testid=dest-check]").click()
                page.locator("[data-testid=dest-check-result][data-code=sender_not_verified]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, DD, facts_dest, "11-email-check-not-verified", width, DS,
                      ["[data-testid=dest-row]:has([data-destination='Email lena@acme.io'])", "[data-testid=dest-check-result]"])
                dest_open(page, "Jira PAY-118")
                page.locator("[data-testid=dest-edit]").click()
                page.locator("[data-testid=dest-form] [data-testid=dest-key]").fill("PAY-121")
                page.locator("[data-testid=dest-form] [data-testid=dest-name]").fill("Jira PAY-121")
                shoot(page, DD, facts_dest, "12-edit", width, DS,
                      ["[data-testid=dest-form] [data-testid=dest-key]", "[data-testid=dest-form] [data-testid=dest-save]"],
                      seat_on="[data-testid=dest-form]")
                dest_save(page)
                page.locator("[data-testid=dest-parked] summary").click()
                page.wait_for_timeout(300)
                shoot(page, DD, facts_dest, "13-edited-old-parked", width, DS,
                      ["[data-testid=dest-parked-row]", "[data-testid=dest-row]:has([data-destination='Jira PAY-121'])"],
                      seat_on="[data-testid=dest-row]:has([data-destination='Jira PAY-121'])")
                dest_open(page, "Email board@acme.io")
                page.locator("[data-testid=dest-remove]").click()
                page.wait_for_timeout(200)
                shoot(page, DD, facts_dest, "14-remove-armed", width, DS,
                      ["[data-testid=dest-row]:has([data-destination='Email board@acme.io'])", "[data-testid=dest-remove]"])
                confirm(page.locator("[data-testid=dest-remove]"), "Remove?")
                page.wait_for_timeout(800)
                if not page.locator("[data-testid=dest-parked] details[open]").count():
                    page.locator("[data-testid=dest-parked] summary").click()
                page.wait_for_timeout(300)
                shoot(page, DD, facts_dest, "15-removed-parked", width, DS,
                      ["[data-testid=dest-parked-row]:has([data-destination='Email board@acme.io'])"], seat_on="[data-testid=dest-parked]")
                # A read that gets no answer: named, never the empty form (F5).
                close_settings(page)
                page.evaluate("window.__p10ReadFail = ['destinations']")
                page.evaluate("window.__p10OpenConnections()")
                page.locator("[data-testid=dest-unreadable]").wait_for(timeout=20_000)
                page.wait_for_timeout(500)
                shoot(page, DD, facts_dest, "16-destinations-unreadable", width, DS, ["[data-testid=dest-unreadable]"])
                page.evaluate("window.__p10ReadFail = []")
                page.locator("[data-testid=dest-unreadable-retry]").click()
                page.locator("[data-testid=dest-list]").wait_for(timeout=10_000)
                close_settings(page)

                # ── Canvas A: SEND (the Room read again on return; no reload) ──
                page.locator(row_sel("Confluence space 98304")).wait_for(timeout=10_000)
                page.wait_for_timeout(400)
                shoot(page, SS, facts_send, "3-destinations", width, UP,
                      [row_sel("Folder Payments"), row_sel("Folder Updates"), row_sel("karol/payments-ops #42")], seat_on="[data-testid=send-well]")
                pick(page, "Folder Payments")
                shoot(page, SS, facts_send, "4-picked-folder", width, UP,
                      [row_sel("Folder Payments"), f"{open_sel('Folder Payments')} .p10-preview-fields", f"{open_sel('Folder Payments')} [data-testid=send-verb]"],
                      seat_on=row_sel("Folder Payments"))
                send_verb(page, "Folder Payments").click()
                page.locator(f"{open_sel('Folder Payments')} [data-testid=send-sent]").wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "5-saved-folder", width, UP,
                      [f"{row_sel('Folder Payments')} [data-testid=send-last-sent]", f"{open_sel('Folder Payments')} [data-testid=send-sent]"],
                      seat_on=row_sel("Folder Payments"))
                shoot(page, SS, facts_send, "6-saved-folder-history", width, UP,
                      ["[data-testid=delivery-row]:has([data-to='Folder Payments']) [data-testid=proof]"])
                pick(page, "karol/payments-ops #42")
                shoot(page, SS, facts_send, "7-picked-github", width, UP,
                      [row_sel("karol/payments-ops #42"), f"{open_sel('karol/payments-ops #42')} .p10-preview-fields",
                       f"{open_sel('karol/payments-ops #42')} [data-testid=send-verb]"], seat_on=row_sel("karol/payments-ops #42"))
                n0 = page.evaluate("window.__p10Calls.length")
                page.evaluate("window.__p10Hold = true")
                send_verb(page, "karol/payments-ops #42").dblclick()
                page.wait_for_timeout(400)
                shoot(page, SS, facts_send, "8-sending", width, UP,
                      [row_sel("karol/payments-ops #42"), f"{open_sel('karol/payments-ops #42')} [data-testid=send-verb][aria-busy=true], {open_sel('karol/payments-ops #42')} [data-testid=send-verb]"],
                      seat_on=row_sel("karol/payments-ops #42"))
                page.evaluate("window.__p10Release && window.__p10Release()")
                page.locator(f"{open_sel('karol/payments-ops #42')} [data-testid=send-sent]").wait_for(timeout=10_000)
                page.wait_for_timeout(600)
                calls = page.evaluate("window.__p10Calls")
                shoot(page, SS, facts_send, "9-posted-github", width, UP,
                      [row_sel("karol/payments-ops #42"), f"{open_sel('karol/payments-ops #42')} [data-testid=send-sent]"],
                      seat_on=row_sel("karol/payments-ops #42"),
                      extra={"double_click_calls": calls[n0:], "dispatches_after_double_click": sum(1 for c in calls[n0:] if c["dispatched"])})
                pick(page, "Jira PAY-121")
                shoot(page, SS, facts_send, "10-picked-jira", width, UP,
                      [row_sel("Jira PAY-121"), f"{open_sel('Jira PAY-121')} .p10-preview-fields", f"{open_sel('Jira PAY-121')} [data-testid=send-verb]"],
                      seat_on=row_sel("Jira PAY-121"))
                page.evaluate("window.__p10Next = {kind: 'unknown', code: 'no_answer'}")
                send_verb(page, "Jira PAY-121").click()
                page.locator(f"{open_sel('Jira PAY-121')} [data-testid=send-unknown]").wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "11-unknown-jira", width, UP,
                      [row_sel("Jira PAY-121"), f"{open_sel('Jira PAY-121')} [data-testid=send-unknown]", f"{open_sel('Jira PAY-121')} [data-testid=send-check]"],
                      seat_on=row_sel("Jira PAY-121"))
                send_verb(page, "Jira PAY-121").click()
                page.locator(f"{open_sel('Jira PAY-121')} [data-testid=send-sent]").wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "12-commented-jira", width, UP,
                      [row_sel("Jira PAY-121"), f"{open_sel('Jira PAY-121')} [data-testid=send-sent]"], seat_on=row_sel("Jira PAY-121"))
                pick(page, "Confluence space 98304")
                shoot(page, SS, facts_send, "13-picked-confluence", width, UP,
                      [row_sel("Confluence space 98304"), f"{open_sel('Confluence space 98304')} .p10-preview-fields",
                       f"{open_sel('Confluence space 98304')} [data-testid=send-verb]"], seat_on=row_sel("Confluence space 98304"))
                send_verb(page, "Confluence space 98304").click()
                page.locator(f"{open_sel('Confluence space 98304')} [data-testid=send-refused]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "14-refused-confluence-sign-in", width, UP,
                      [row_sel("Confluence space 98304"), f"{open_sel('Confluence space 98304')} [data-testid=send-refused]"],
                      seat_on=row_sel("Confluence space 98304"))
                # He signs in to the Atlassian account again and comes back to the Room.
                page.evaluate("window.__p10SignIn('confluence'); window.dispatchEvent(new Event('focus'))")
                page.wait_for_timeout(800)
                send_verb(page, "Confluence space 98304").click()
                page.locator(f"{open_sel('Confluence space 98304')} [data-testid=send-sent]").wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "15-blog-posted-confluence", width, UP,
                      [row_sel("Confluence space 98304"), f"{open_sel('Confluence space 98304')} [data-testid=send-sent]"],
                      seat_on=row_sel("Confluence space 98304"))
                pick(page, "Email lena@acme.io")
                shoot(page, SS, facts_send, "16-picked-email", width, UP,
                      [row_sel("Email lena@acme.io"), f"{open_sel('Email lena@acme.io')} .p10-preview-fields",
                       f"{open_sel('Email lena@acme.io')} [data-testid=send-verb]"], seat_on=row_sel("Email lena@acme.io"))
                send_verb(page, "Email lena@acme.io").click()   # the sender is not verified in SendGrid
                page.locator(f"{open_sel('Email lena@acme.io')} [data-testid=send-failed]").wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "17-failed-email-sender", width, UP,
                      [f"{row_sel('Email lena@acme.io')} [data-testid=send-last-failed]", f"{open_sel('Email lena@acme.io')} [data-testid=send-failed]"],
                      seat_on=row_sel("Email lena@acme.io"))
                # He verifies the sender in SendGrid, then sends again.
                page.evaluate("window.__p10VerifySender('karol@acme.io')")
                send_verb(page, "Email lena@acme.io").click()
                page.locator(f"{open_sel('Email lena@acme.io')} [data-testid=send-sent]").wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "18-accepted-by-sendgrid", width, UP,
                      [row_sel("Email lena@acme.io"), f"{open_sel('Email lena@acme.io')} [data-testid=send-sent]"], seat_on=row_sel("Email lena@acme.io"))
                shoot(page, SS, facts_send, "19-accepted-history", width, UP,
                      ["[data-testid=delivery-row]:has([data-to='Email lena@acme.io'])"])
                page.evaluate("window.__p10GhLogin = 'kpersonal'")
                pick(page, "karol/payments-ops #42")
                send_verb(page, "karol/payments-ops #42").click()
                page.locator(f"{open_sel('karol/payments-ops #42')} [data-testid=send-refused][data-code=github_identity_changed]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "20-refused-github-account", width, UP,
                      [row_sel("karol/payments-ops #42"), f"{open_sel('karol/payments-ops #42')} [data-testid=send-refused]"],
                      seat_on=row_sel("karol/payments-ops #42"))
                page.evaluate("window.__p10GhLogin = 'kwork'")
                # The lost answer, bound to update A (Phase 9 r2 F1).
                pick(page, "Folder Updates")
                page.evaluate("window.__p10LoseNext = true")
                send_verb(page, "Folder Updates").click()
                page.locator("[data-testid=send-lost]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "21-lost-answer-a", width, UP,
                      [row_sel("Folder Updates"), f"{open_sel('Folder Updates')} [data-testid=send-lost]", f"{open_sel('Folder Updates')} [data-testid=send-retry]"],
                      seat_on=row_sel("Folder Updates"))
                go_back(page)
                open_update(page, upd_b)
                b_state = page.evaluate("""() => ({lost: !!document.querySelector('[data-testid=send-lost]'),
                  retry: !!document.querySelector('[data-testid=send-retry]'), open: document.querySelectorAll('[data-testid=send-open]').length,
                  history: document.querySelectorAll('[data-testid=delivery-row]').length})""")
                # Update B stays clean: a fact, not a board (Codex Astra r2 F3; its screen is
                # board 3's list with the clock changed).
                seat(page, "[data-testid=send-well]")
                b_state["named"] = page.evaluate(VISIBLE, [row_sel("Folder Updates")])
                go_back(page)
                open_update(page, upd_a)
                page.wait_for_timeout(600)
                # Back on A: the same screen as board 21, pixel for pixel. That identity IS the
                # proof (nothing moved while he was on B), so it is a fact, not a second board.
                import hashlib
                seat(page, row_sel("Folder Updates"))
                page.mouse.move(1, 1)
                page.wait_for_timeout(300)
                back_on_a = {
                    "named": page.evaluate(VISIBLE, [row_sel("Folder Updates"), f"{open_sel('Folder Updates')} [data-testid=send-lost]",
                                                     f"{open_sel('Folder Updates')} [data-testid=send-retry]"]),
                    "same_pixels_as_board_21_clock_masked": masked_sha(page) == facts_send[f"21-lost-answer-a-{width}"]["masked_sha"],
                }
                if not all(v["ok"] for v in back_on_a["named"]):
                    invisible.append(f"back-on-a-{width}: {back_on_a['named']}")
                page.locator("[data-testid=send-retry]").click()
                page.locator("[data-testid=send-lost]").wait_for(state="detached", timeout=10_000)
                page.wait_for_timeout(600)
                calls = page.evaluate("window.__p10Calls")
                lost_key = [c for c in calls if c.get("dispatched")][-1]["command_id"]
                shoot(page, SS, facts_send, "24-retried-one-dispatch", width, UP,
                      [row_sel("Folder Updates"), f"{open_sel('Folder Updates')} [data-testid=send-sent]"], seat_on=row_sel("Folder Updates"), extra={
                    "calls_with_lost_key": [c for c in calls if c["command_id"] == lost_key],
                    "dispatches_with_lost_key": sum(1 for c in calls if c["command_id"] == lost_key and c["dispatched"]),
                    "back_on_a_before_retry": back_on_a, "update_b_clean": b_state})
                # A restart during dispatching.
                pick(page, "Jira PAY-121")
                page.evaluate("window.__p10CrashNext = true")
                send_verb(page, "Jira PAY-121").click()
                page.wait_for_timeout(800)
                reopen(page, upd_a)
                page.wait_for_timeout(600)
                shoot(page, SS, facts_send, "25-unknown-after-restart", width, UP,
                      ["[data-testid=delivery-row]:has([data-code=interrupted])"],
                      extra={"rows": page.evaluate("window.__p10Dump().sends.map(s => [s.destination_name, s.state, s.reason])")})
                # PREPARED by the steward and by a connected agent.
                page.evaluate(f"""async () => {{
                  await window.__p10Prepare({{update_id: '{upd_a}', destination_name: 'karol/payments-ops #42', by_kind: 'steward', by_identity: 'steward'}});
                  await window.__p10Prepare({{update_id: '{upd_a}', destination_name: 'Folder Payments', by_kind: 'agent', by_identity: 'codex-desk'}});
                  await window.__p10Prepare({{update_id: '{upd_a}', destination_name: 'Email lena@acme.io', by_kind: 'agent', by_identity: 'codex-desk'}});
                  await window.__p10Prepare({{update_id: '{upd_a}', destination_name: 'Folder Updates', by_kind: 'agent', by_identity: 'codex-desk'}});
                  await window.__p10Prepare({{update_id: '{upd_a}', destination_name: 'Jira PAY-121', by_kind: 'agent', by_identity: 'codex-desk'}});
                }}""")
                reopen(page, upd_a)
                page.locator("[data-testid=prepared-row]").first.wait_for(timeout=10_000)
                gh = prep_li("karol/payments-ops #42")
                shoot(page, SS, facts_send, "26-prepared", width, UP,
                      [f"{gh} [data-testid=prepared-row]", f"{gh} [data-testid=prepared-send]", f"{gh} [data-testid=prepared-discard]"], seat_on="[data-testid=prepared-list]")
                # A prepared send that is RUNNING stays on the face through Back -> return,
                # and its destination offers no second Send while it runs (Codex Astra r2 F2).
                page.evaluate("window.__p10Hold = true")
                page.locator(f"{gh} [data-testid=prepared-send]").click()
                page.locator(prep_li("karol/payments-ops #42", "dispatching")).wait_for(timeout=10_000)
                go_back(page)
                open_update(page, upd_a)
                page.locator(prep_li("karol/payments-ops #42", "dispatching")).wait_for(timeout=10_000)
                page.wait_for_timeout(400)
                shoot(page, SS, facts_send, "26b-prepared-running-after-return", width, UP,
                      [f"{prep_li('karol/payments-ops #42', 'dispatching')} [data-testid=prepared-running]"], seat_on="[data-testid=prepared-list]",
                      extra={"stored_state": page.evaluate("window.__p10Dump().sends.filter(s => s.prepared_by_kind === 'steward').map(s => s.state)")})
                pick(page, "karol/payments-ops #42")
                ghv = f"{open_sel('karol/payments-ops #42')} [data-testid=send-verbs] .btn >> nth=0"
                shoot(page, SS, facts_send, "26c-destination-running", width, UP,
                      [f"{row_sel('karol/payments-ops #42')} [data-testid=send-last-running]", f"{open_sel('karol/payments-ops #42')} [data-testid=send-verbs] .btn"],
                      seat_on=row_sel("karol/payments-ops #42"),
                      extra={"send_enabled_while_running": page.locator(ghv).is_enabled()})
                page.locator(row_sel("karol/payments-ops #42")).first.click()   # close the pick (no press is running on it)
                page.locator(open_sel("karol/payments-ops #42")).wait_for(state="detached", timeout=10_000)
                page.evaluate("window.__p10Release && window.__p10Release()")
                page.locator(prep_li("karol/payments-ops #42", "sent")).wait_for(timeout=10_000)   # settles on the face, no reload
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "27-prepared-sent", width, UP,
                      [f"{prep_li('karol/payments-ops #42', 'sent')} [data-testid=prepared-result-word]"], seat_on="[data-testid=prepared-list]")
                # The latest result follows SEND order (Codex Astra r2 F1): lena's send was
                # prepared at board 26; an inline send to lena goes first and is accepted;
                # then the older preparation is sent and fails. The destination shows FAILED.
                pick(page, "Email lena@acme.io")
                send_verb(page, "Email lena@acme.io").click()
                page.locator(f"{open_sel('Email lena@acme.io')} [data-testid=send-sent]").wait_for(timeout=10_000)
                close(page, "Email lena@acme.io")
                em = prep_li("Email lena@acme.io")
                page.locator(f"{em} [data-testid=prepared-row]").click()
                page.locator(f"{em} [data-testid=prepared-send]").wait_for(timeout=10_000)
                page.evaluate("window.__p10Next = {kind: 'failed', code: 'api_key_invalid'}")
                page.locator(f"{em} [data-testid=prepared-send]").click()
                page.locator(prep_li("Email lena@acme.io", "failed")).wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, SS, facts_send, "28-prepared-failed", width, UP,
                      [f"{prep_li('Email lena@acme.io', 'failed')} [data-testid=prepared-result-word]"], seat_on="[data-testid=prepared-list]")
                order = page.evaluate("""() => window.__p10Dump().sends.filter(s => s.destination_name === 'Email lena@acme.io' && s.dispatch_started_at)
                  .map(s => ({state: s.state, by: s.prepared_by_kind, created_at: s.created_at, dispatch_started_at: s.dispatch_started_at}))""")
                shoot(page, SS, facts_send, "28b-destination-latest-failed", width, UP,
                      [f"{row_sel('Email lena@acme.io')} [data-testid=send-last-failed]"], seat_on=row_sel("Email lena@acme.io"),
                      extra={"lena_sends": order,
                             "latest_by_dispatch": max(order, key=lambda r: r["dispatch_started_at"])["state"],
                             "latest_by_preparation": max(order, key=lambda r: r["created_at"])["state"]})
                # Round four (Codex Astra r3 F1): reopen the destination. The expanded
                # receipt says what the header says: the latest send FAILED; the earlier
                # acceptance is not shown as the current result.
                pick(page, "Email lena@acme.io")
                reopened = page.evaluate("""(sel) => { const o = document.querySelector(sel); return {
                  receipts: o ? [...o.querySelectorAll('[data-receipt=latest]')].map((e) => e.dataset.state) : null,
                  success_shown: o ? !!o.querySelector('[data-testid=send-sent]') : null,
                  header: (document.querySelector("[data-testid=destination-row]:has([data-destination='Email lena@acme.io']) [data-testid^=send-last-]") || {}).dataset?.testid || null}; }""",
                  open_sel("Email lena@acme.io"))
                if reopened["receipts"] != ["failed"] or reopened["success_shown"] or reopened["header"] != "send-last-failed":
                    invisible.append(f"28c-{width}: the reopened receipt disagrees with the header: {reopened}")
                shoot(page, SS, facts_send, "28c-destination-reopened", width, UP,
                      [f"{row_sel('Email lena@acme.io')} [data-testid=send-last-failed]", f"{open_sel('Email lena@acme.io')} [data-testid=send-failed][data-receipt=latest]",
                       f"{open_sel('Email lena@acme.io')} [data-testid=send-verb]"],
                      seat_on=row_sel("Email lena@acme.io"), extra={"reopened": reopened})
                close(page, "Email lena@acme.io")
                # A prepared file send: its preview names the file; the receipt names the SAME file (F6).
                fu = prep_li("Folder Updates")
                page.locator(f"{fu} [data-testid=prepared-row]").click()
                page.locator(f"{fu} [data-testid=prepared-send]").wait_for(timeout=10_000)
                file_named = page.locator(f"{fu} [data-testid=send-preview-field]").all_inner_texts()
                page.locator(f"{fu} [data-testid=prepared-send]").click()
                page.locator(prep_li("Folder Updates", "sent")).wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                proof_path = page.locator(f"{prep_li('Folder Updates', 'sent')} [data-testid=proof]").inner_text()
                shoot(page, SS, facts_send, "29-prepared-file-sent", width, UP,
                      [f"{prep_li('Folder Updates', 'sent')} [data-testid=prepared-result-word]"], seat_on=prep_li("Folder Updates", "sent"),
                      extra={"prepared_file_preview_fields": file_named, "prepared_file_proof": proof_path,
                             "same_file": any(proof_path.endswith("/" + f.split(None, 1)[-1].strip()) for f in file_named if f.upper().startswith("FILE"))})
                fp = prep_li("Folder Payments")
                page.evaluate("window.__p10Move('Folder Payments', '/Volumes/Archive/Payments')")
                page.locator(f"{fp} [data-testid=prepared-row]").click()
                page.locator(f"{fp} [data-testid=prepared-send]").click()
                page.locator(f"{fp} [data-testid=prepared-refused-chip][data-code=destination_changed]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "30-prepared-destination-changed", width, UP,
                      [f"{fp} [data-testid=prepared-refused-chip]", f"{fp} [data-testid=prepared-discard]"], seat_on=fp)
                jr = prep_li("Jira PAY-121")
                ids_now = page.evaluate("window.__p10Dump().destinations.filter(d => d.name === 'Jira PAY-121' && d.state === 'active').map(d => d.id)")
                page.evaluate(f"fetch('/api/channels/destinations/{ids_now[0]}', {{method: 'DELETE'}})")   # he removed it in Settings
                page.wait_for_timeout(300)
                page.locator(f"{jr} [data-testid=prepared-row]").click()
                page.locator(f"{jr} [data-testid=prepared-send]").click()
                page.locator(f"{jr} [data-testid=prepared-refused-chip][data-code=destination_parked]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "31-prepared-destination-parked", width, UP,
                      [f"{jr} [data-testid=prepared-refused-chip]", f"{jr} [data-testid=prepared-discard]"], seat_on=jr)
                page.locator(f"{fp} [data-testid=prepared-row]").click()
                page.locator(f"{fp} [data-testid=prepared-discard]").click()
                page.wait_for_timeout(200)
                shoot(page, SS, facts_send, "32-discard-armed", width, UP,
                      [f"{fp} [data-testid=prepared-refused-chip]", f"{fp} [data-testid=prepared-discard]"], seat_on=fp)
                confirm(page.locator(f"{fp} [data-testid=prepared-discard]"), "Discard?")
                page.locator(prep_li("Folder Payments", "discarded")).wait_for(timeout=10_000)
                page.wait_for_timeout(400)
                dump = page.evaluate("window.__p10Dump().sends.filter(s => s.prepared_by_kind !== 'owner').map(s => [s.destination_name, s.state, s.reason, s.file_name || null, s.proof && s.proof.path || null])")
                shoot(page, SS, facts_send, "33-discarded", width, UP,
                      [f"{prep_li('Folder Payments', 'discarded')} [data-testid=prepared-result-word]"], seat_on=prep_li("Folder Payments", "discarded"),
                      extra={"prepared_rows": dump})
                # The manual channel, kept.
                page.locator("[data-testid=deliver-to]").fill("Priya")
                page.locator("[data-testid=deliver-verb]").click()
                page.locator("[data-testid=delivery-row]:has([data-to='Priya'])").wait_for(timeout=10_000)
                page.wait_for_timeout(800)
                shoot(page, SS, facts_send, "34-history-several", width, UP,
                      ["[data-p10=history] .surface-section-head", "[data-testid=deliver-line]", "[data-testid=delivery-row]"])
                shoot(page, SS, facts_send, "34b-history-manual", width, UP,
                      ["[data-testid=delivery-row]:has([data-to='Priya'])"],
                      seat_on="CENTER:[data-testid=delivery-row]:has([data-to='Priya'])")
                go_back(page)
                page.wait_for_timeout(800)
                li = f"[data-testid=update-list-item]:has([data-update-id='{upd_a}'])"
                shoot(page, SS, facts_send, "35-list-chips", width, UP,
                      [f"{li} [data-testid=update-prepared-chip]", f"{li} [data-testid=update-unknown-chip]", f"{li} [data-testid=update-delivered-chip]"], seat_on=None)
                page.locator("[data-testid=update-verb-draft-deterministic]").click()
                page.locator("[data-testid=update-editor][data-lifecycle=draft]").wait_for(timeout=20_000)
                page.wait_for_timeout(800)
                shoot(page, SS, facts_send, "36-draft-no-send", width, UP, ["[data-testid=update-editor][data-lifecycle=draft] [data-testid=update-editor-band]"], seat_on=None,
                      extra={"send_well_on_draft": page.locator("[data-testid=send-well]").count()})
                # Reads that get no answer: named, never empty (F5).
                go_back(page)
                open_update(page, upd_a)
                page.evaluate("window.__p10ReadFail = ['destinations']; window.dispatchEvent(new Event('focus'))")
                page.locator("[data-testid=destinations-unreadable]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "37-destinations-unreadable", width, UP, ["[data-testid=destinations-unreadable]"])
                page.evaluate("window.__p10ReadFail = []")
                page.locator("[data-testid=destinations-unreadable-retry]").click()
                page.locator(row_sel("Folder Payments")).wait_for(timeout=10_000)
                page.evaluate("window.__p10ReadFail = ['sends']")
                page.locator(row_sel("Folder Payments")).click()   # any press reads the sends again
                page.locator("[data-testid=sends-unreadable]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "38-sends-unreadable", width, UP, ["[data-testid=sends-unreadable]"])
                page.evaluate("window.__p10ReadFail = []")
                page.locator("[data-testid=sends-unreadable-retry]").click()
                page.locator("[data-testid=prepared-list]").wait_for(timeout=10_000)
                page.evaluate("window.__p10ReadFail = ['history']")
                page.locator(row_sel("Folder Payments")).click()   # a press reads the history again
                page.locator("[data-testid=history-unreadable]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "39-history-unreadable", width, UP, ["[data-testid=history-unreadable]"])
                page.evaluate("window.__p10ReadFail = []")
                page.locator("[data-testid=history-unreadable-retry]").click()
                page.wait_for_timeout(500)
                if page.locator(open_sel("Folder Payments")).count():
                    page.locator(row_sel("Folder Payments")).click()
                    page.wait_for_timeout(300)
                page.evaluate("window.__p10PreviewFail = true")
                page.locator(row_sel("karol/payments-ops #42")).click()
                page.locator("[data-testid=preview-failed]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, SS, facts_send, "40-preview-failed", width, UP,
                      [row_sel("karol/payments-ops #42"), "[data-testid=preview-failed]"], seat_on=row_sel("karol/payments-ops #42"))
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
        for v in vites:
            try:
                v.wait(timeout=10)
            except Exception:
                v.kill()
        # Law (2026-09-28): a run removes its own scratch HOME.
        shutil.rmtree(home, ignore_errors=True)
        # Merge with an earlier ONLY_WIDTH run's facts; this run's keys win.
        tag = "_browser_errors_" + "_".join(str(w) for w, _ in widths)
        for path, facts in ((SEND / "shots" / "facts.json", facts_send), (DEST / "shots" / "facts.json", facts_dest)):
            path.parent.mkdir(parents=True, exist_ok=True)
            prior = json.loads(path.read_text()) if path.exists() else {}
            path.write_text(json.dumps({**prior, **facts, tag: errors}, indent=1, ensure_ascii=False) + "\n")
        print("errors:", len(errors), file=sys.stderr)

    return invisible


def main() -> None:
    # A TERM or an interrupt still runs each run's `finally`: servers down, HOME removed.
    import signal
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    invisible: list[str] = []
    for w in WIDTHS:
        invisible += run([w])
    # ── The fences (Codex Astra r1 F3, r2 F3, r3 F1) ──
    failed = False
    if invisible:
        failed = True
        print("FENCE FAILURES (named elements off screen, or a failed assertion):", *invisible, sep="\n  ", file=sys.stderr)
    # Two boards of one width may not share bytes once the clock is masked.
    for folder in (SEND / "shots", DEST / "shots"):
        facts = json.loads((folder / "facts.json").read_text())
        for w, _ in WIDTHS:
            seen: dict[str, str] = {}
            for key, f in sorted(facts.items()):
                if key.startswith("_") or not key.endswith(f"-{w}"):
                    continue
                h = f["masked_sha"]
                if h in seen:
                    failed = True
                    print(f"IDENTICAL SHOTS (clock masked): {seen[h]} == {key}", file=sys.stderr)
                seen[h] = key
    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
