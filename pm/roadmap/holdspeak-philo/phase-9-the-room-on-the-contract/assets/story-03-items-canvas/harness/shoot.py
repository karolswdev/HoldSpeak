"""PHILO-9-03 canvases: the Room's ITEMS section and the copy-and-confirm moment.

Everything is live except the stated shim: a REAL hub (scripts/graph_walk.py
serve, isolated HOME, isolated DB) seeded through its real HTTP routes, and the
PRODUCT app served twice by vite (harness/vite.config.mjs):
  - TODAY:    the product as on this branch (no swap, no shim);
  - PROPOSAL: ProjectRoomCore swapped for harness/ProposedProjectRoomCore.tsx,
              plus harness/shim.ts (the unbuilt wire, stated in that file).

Usage (from the repo root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/shoot.py

Shots: ../shots/ (items) and ../../story-03-delivery-canvas/shots/ (delivery),
<n>-<board>-<width>.png at 1440x900 and 393x852; facts.json beside them.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ITEMS = HERE.parent
DELIVERY = ITEMS.parent / "story-03-delivery-canvas"
REPO = ITEMS.parents[5]
WEB = REPO / "web"
TOKEN = "philo9-canvas"
WIDTHS = [(1440, 900), (393, 852)]
NAME = "Payments ledger cutover"
EMPTY = "Vendor review"
TODAY = dt.date.today()


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, headers: dict[str, str] | None = None, timeout: float = 90) -> None:
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


# Rendered facts. The Room window is the frame; proposal nodes carry data-p9.
FACTS = r"""() => {
  const anchor = document.querySelector('[data-testid=room-body], [data-testid=update-posture]');
  const win = anchor ? anchor.closest('.desk-window') : null;
  if (!win) return {window: false};
  const GLYPH = /^[●○✓✗⚠—↻ℹ«»·▤›×\s]+$/;
  const small = {proposal: [], inherited: []};
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || GLYPH.test(t)) continue;
    const el = n.parentElement;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none') continue;
    const fs = parseFloat(cs.fontSize);
    if (fs < 12) (el.closest('[data-p9]') ? small.proposal : small.inherited).push({text: t.slice(0, 40), fs, cls: String(el.className).slice(0, 60)});
  }
  // WCAG contrast of every chip / token: its text colour against the
  // background composited up the tree (to the page).
  const parse = (c) => { const m = c.match(/[\d.]+/g); if (!m) return [0,0,0,0]; return [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1]; };
  const lum = ([r,g,b]) => { const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }; return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(b); };
  const over = (top, under) => { const a = top[3]; return [top[0]*a + under[0]*(1-a), top[1]*a + under[1]*(1-a), top[2]*a + under[2]*(1-a), 1]; };
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    let acc = [0,0,0,1];
    const base = layers.length && layers[layers.length-1][3] >= 1 ? layers.pop() : parse(getComputedStyle(document.body).backgroundColor);
    acc = base[3] >= 1 ? base : over(base, [0,0,0,1]);
    for (let i = layers.length - 1; i >= 0; i--) acc = over(layers[i], acc);
    return acc;
  };
  const ratio = (a, b) => { const la = lum(a), lb = lum(b); return +(((Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)).toFixed(2)); };
  const chips = [...win.querySelectorAll('.surface-state-chip, .surface-token, .gadget-chip, .surface-provenance-chip, .provenance-chip, .egress-chip')]
    .filter((c) => { const r = c.getBoundingClientRect(); return r.width && r.height && (c.innerText || '').trim(); })
    .map((c) => {
      const fg = parse(getComputedStyle(c).color); const bg = bgOf(c);
      const fgc = fg[3] < 1 ? over(fg, bg) : fg;
      return {text: c.innerText.replace(/\s+/g, ' ').trim().slice(0, 48), proposal: !!c.closest('[data-p9]'), ratio: ratio(fgc, bg), fs: parseFloat(getComputedStyle(c).fontSize)};
    });
  const raw = [...win.querySelectorAll('button')].filter((b) => !String(b.className).includes('btn') && b.getBoundingClientRect().width);
  const body = win.querySelector('.desk-surface-body') || anchor;
  const text = (sel) => [...win.querySelectorAll(sel)].map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  return {
    window: true,
    headline: text('[data-testid=room-headline]')[0] ?? null,
    head_chips: text('[data-testid=room-head-chips] .surface-state-chip, [data-testid=room-head-chips] .surface-token'),
    needs_you: text('[data-testid=needs-you-row], [data-testid=needs-you-empty]'),
    items_head: (() => { const s = win.querySelector('[data-p9=items] .surface-section-head, [data-p9=items] h3'); return s ? s.innerText.trim() : null; })(),
    items_section_present: !!win.querySelector('[data-p9=items] section, [data-p9=items] .surface-section'),
    item_rows: text('[data-testid=item-row]'),
    add_controls_in_items: [...win.querySelectorAll('[data-p9=items] button, [data-p9=items] input')].length,
    update_list_head: text('.update-list .surface-ledger-count')[0] ?? null,
    update_rows: text('[data-testid=update-list-item]'),
    delivered_chips: text('[data-testid=update-delivered-chip]'),
    deliver_verb: text('[data-testid=deliver-verb]')[0] ?? null,
    deliver_verb_busy: (() => { const b = win.querySelector('[data-testid=deliver-verb]'); return b ? (b.disabled || b.getAttribute('aria-busy') === 'true' || String(b.className).includes('loading')) : null; })(),
    deliver_to: (() => { const i = win.querySelector('[data-testid=deliver-to]'); return i ? {value: i.value, disabled: i.disabled} : null; })(),
    delivery_rows: text('[data-testid=delivery-row]'),
    delivery_head: (() => { const s = win.querySelector('[data-p9=delivery] .surface-section-head, [data-p9=delivery] h3'); return s ? s.innerText.trim() : null; })(),
    copy_verb: text('[data-testid=update-verb-copy]')[0] ?? null,
    lifecycle_band: text('[data-testid=update-editor-band]')[0] ?? null,
    footer: text('.desk-surface-foot, .surface-footer')[0] ?? null,
    words_send: /\bsend\b|\bsent\b/i.test(win.innerText),
    egress_badges: [...win.querySelectorAll('.egress-chip, [data-testid*=egress]')].map((e) => e.innerText.trim()),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
    small_text: small,
    chips,
    raw_buttons: raw.map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30)),
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
    body_overflow_x: body ? body.scrollWidth > body.clientWidth + 1 : null,
    footer_in_scan: !!win.querySelector('.desk-surface-foot, .surface-footer'),
    overflow_culprits: body ? [...body.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(), b = body.getBoundingClientRect(); return r.width && r.right > b.right + 1; }).slice(0, 6).map((e) => String(e.className || e.tagName).slice(0, 40)) : [],
    // F10: a visible verb or section head whose centre is under the Ask well.
    under_ask_well: [...win.querySelectorAll('.btn, .btn--chrome, .surface-section-head, h3')].filter((e) => {
      if (e.closest('.room-ask-container')) return false;
      const r = e.getBoundingClientRect();
      if (!r.width || r.bottom < 0 || r.top > window.innerHeight) return false;
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return !!hit && !!hit.closest('.room-ask-container');
    }).map((e) => e.innerText.trim().slice(0, 30)),
    ask_well_position: (() => { const c = win.querySelector('.room-ask-container'); return c ? getComputedStyle(c).position : null; })(),
  };
}"""

# ── The pointer pass (UX-CANON C; Astra r2 F3) ─────────────────────────────
# EVERY Button in the Room window (body, head verbs and footer; menus when
# open), NINE points each: the centre, the four edge midpoints and the four
# corners, inset 1 px, of the painted face at 1440 and of the 44 x 44 target at
# 393. Each point: `elementFromPoint` AND a real `page.mouse.move`, recording
# the `pointermove` target (the grant canvas's method). Each control is
# scrolled into view to probe; every scroll position is restored after.
CONTROLS = r"""() => {
  const anchor = document.querySelector('[data-testid=room-body], [data-testid=update-posture]');
  const win = anchor ? anchor.closest('.desk-window') : null;
  if (!win) return [];
  window.__scrollSnap = [...document.querySelectorAll('*')].filter((e) => e.scrollTop || e.scrollLeft).map((e) => [e, e.scrollTop, e.scrollLeft]);
  window.__pm = null;
  if (!window.__pmHooked) { document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, true); window.__pmHooked = true; }
  const menus = [...document.querySelectorAll('[role=menu]')];
  const btns = [...win.querySelectorAll('.btn, .btn--chrome'), ...menus.flatMap((m) => [...m.querySelectorAll('button, [role=menuitem]')])]
    .filter((b) => b.getBoundingClientRect().width);
  return btns.map((b, i) => {
    b.dataset.probe = String(i);
    return {i, text: (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30),
      in_foot: !!b.closest('.desk-surface-foot, .surface-footer'), in_menu: !!b.closest('[role=menu]'),
      proposal: !!b.closest('[data-p9]'),
      touched: !!(b.closest('[data-p9]') || b.closest('.desk-editor-toolbar') || b.closest('.update-body-editor-mic')
        || b.matches('[data-testid=update-claim-ref], [data-testid=update-verb-back]'))};
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

# The open update's delivery face, read back (Astra r2 F1).
DELIVERY_STATE = r"""() => {
  const i = document.querySelector('[data-testid=deliver-to]');
  return {
    field: i ? {value: i.value, disabled: i.disabled} : null,
    retry: !!document.querySelector('[data-testid=deliver-retry]'),
    mark: !!document.querySelector('[data-testid=deliver-verb]'),
    unknown: !!document.querySelector('[data-testid=deliver-uncertain]'),
    rows: [...document.querySelectorAll('[data-testid=delivery-row]')].map((r) => r.innerText.replace(/\s+/g, ' ').trim()),
  };
}"""


def pointer_pass(page, width: int) -> list[dict]:
    out = []
    for c in page.evaluate(CONTROLS):
        geo = page.evaluate(POINTS9, [c["i"], width])
        pts = []
        for name, (x, y) in zip(NAMES, geo["points"]):
            hit = page.evaluate(HIT, [c["i"], x, y])
            page.mouse.move(x, y)
            pm = page.evaluate(PM_OWNED, [c["i"]])
            pts.append({"at": name, "x": round(x, 1), "y": round(y, 1), "efp": hit["efp"], "pointer": pm, "hit": hit["hit"]})
        out.append({**{k: c[k] for k in ("text", "in_foot", "in_menu", "proposal", "touched")}, "face": geo["face"],
                    "target": geo["target"], "owned": all(p["efp"] and p["pointer"] for p in pts), "points": pts})
    page.mouse.move(1, 1)
    page.evaluate(RESTORE)
    page.wait_for_timeout(100)
    return out


def main() -> None:
    home = tempfile.mkdtemp(prefix="philo9-03-canvas-")
    hub_port, today_port = free_port(), free_port()
    canvas_port = int(os.environ.get("CANVAS_PORT", "4441"))
    hub_url = f"http://127.0.0.1:{hub_port}"
    hub = subprocess.Popen(
        ["uv", "run", "--extra", "test", "python", "scripts/graph_walk.py", "serve", "--port", str(hub_port), "--token", TOKEN],
        cwd=REPO, env={**os.environ, "HOME": home}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
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
    facts_items: dict[str, dict] = {"_seed": {}}
    facts_delivery: dict[str, dict] = {"_seed": {}}
    errors: list[str] = []
    try:
        wait_http(f"{hub_url}/api/projects", {"Authorization": f"Bearer {TOKEN}"})
        wait_http(f"http://127.0.0.1:{canvas_port}/")
        wait_http(f"http://127.0.0.1:{today_port}/")

        # ── Seed through the real routes ──
        seed: dict = {"home": home, "today": TODAY.isoformat()}
        st, p = hub_api(hub_url, "POST", "/api/projects", {"name": NAME})
        pid = p["project"]["id"]
        st2, p2 = hub_api(hub_url, "POST", "/api/projects", {"name": EMPTY})
        seed["projects"] = {NAME: [st, pid], EMPTY: [st2, p2["project"]["id"]]}
        late_due = (TODAY - dt.timedelta(days=7)).isoformat()
        items = [
            {"item_type": "milestone", "title": "Cutover rehearsal", "due_at": late_due},
            {"item_type": "risk", "title": "Old ledger freeze slips", "severity": "high",
             "details": {"likelihood": "high", "impact": "high"}},
            {"item_type": "milestone", "title": "Ledger go-live", "due_at": (TODAY + dt.timedelta(days=14)).isoformat()},
        ]
        seed["items"] = []
        for it in items:
            s, r = hub_api(hub_url, "POST", f"/api/projects/{pid}/items", it)
            seed["items"].append({"status": s, "id": (r or {}).get("item", {}).get("id") if isinstance(r, dict) else r,
                                  "title": it["title"], "due_at": it.get("due_at")})
        rehearsal_id = seed["items"][0]["id"]
        # Astra r1 F7: a missed and a dropped milestone, by the real transition route.
        for title, due, verb in (("Parallel run", TODAY - dt.timedelta(days=10), "missed"),
                                 ("Vendor shadow run", TODAY + dt.timedelta(days=5), "dropped")):
            s, r = hub_api(hub_url, "POST", f"/api/projects/{pid}/items",
                           {"item_type": "milestone", "title": title, "due_at": due.isoformat()})
            iid = (r or {}).get("item", {}).get("id") if isinstance(r, dict) else None
            s2, r2 = hub_api(hub_url, "POST", f"/api/projects/{pid}/items/{iid}/transition", {"verb": verb})
            seed["items"].append({"status": s, "id": iid, "title": title, "due_at": due.isoformat(),
                                  "transition": [s2, (r2 or {}).get("item", {}).get("lifecycle") if isinstance(r2, dict) else r2]})
        s, d = hub_api(hub_url, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})
        upd = d["update"]["id"]
        s2, pub = hub_api(hub_url, "POST", f"/api/updates/{upd}/publish", {})
        seed["update"] = {"draft": s, "publish": s2, "id": upd, "lifecycle": (pub or {}).get("update", {}).get("lifecycle")}
        # Astra r2 F1: a second published update (B), to prove a held
        # confirmation stays with A.
        s3, d3 = hub_api(hub_url, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})
        upd_b = d3["update"]["id"]
        s4, pub_b = hub_api(hub_url, "POST", f"/api/updates/{upd_b}/publish", {})
        seed["update_b"] = {"draft": s3, "publish": s4, "id": upd_b,
                            "lifecycle": (pub_b or {}).get("update", {}).get("lifecycle")}
        facts_items["_seed"] = facts_delivery["_seed"] = seed
        print("seed", json.dumps(seed)[:400])

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            pages: dict[int, object] = {}

            def open_page(origin: str, width: int, height: int, query: str = ""):
                ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2)
                ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append(f"{width} pageerror: {e}"))
                page.on("console", lambda m: errors.append(f"{width} console: {m.text[:200]}") if m.type == "error" else None)
                page.goto(f"{origin}/?token={TOKEN}{query}", wait_until="load")
                boot(page)
                return ctx, page

            def boot(page):
                chair = page.locator(".chair")
                chair.wait_for(timeout=45_000)
                page.wait_for_timeout(800)
                if page.get_by_role("button", name="Continue later", exact=True).count():
                    page.get_by_role("button", name="Continue later", exact=True).first.click()
                    page.wait_for_timeout(800)

            def open_room(page, name: str):
                page.locator("[aria-controls=desk-tool-shelf]").first.click()
                page.locator("[aria-controls=desk-palette-listbox]").fill(name)
                try:
                    page.get_by_text(f"Open {name}").first.click(timeout=20_000)
                except Exception:
                    page.screenshot(path=os.environ.get("DEBUG_SHOT", "/tmp/philo9-open-room-fail.png"))
                    raise
                page.locator("[data-testid=room-body]").wait_for(timeout=20_000)
                page.wait_for_timeout(1500)

            def close_windows(page):
                for _ in range(4):
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(150)

            def enter_updates(page):
                page.locator("[data-testid=updates-verb]").click()
                page.locator("[data-testid=update-list]").wait_for(timeout=15_000)
                page.wait_for_timeout(500)

            def open_update(page, lifecycle: str, uid: str | None = None):
                sel = f"[data-update-id='{uid}']" if uid else f"[data-lifecycle={lifecycle}]"
                page.locator(f"[data-testid=update-list-item]:has({sel})").first.click()
                page.locator("[data-testid=update-editor]").wait_for(timeout=15_000)
                page.wait_for_timeout(600)

            def go_back(page):
                page.locator("[data-testid=update-verb-back]").click()
                page.locator("[data-testid=update-list]").wait_for(timeout=10_000)
                page.wait_for_timeout(400)

            def shoot(page, out: Path, facts: dict, board: str, width: int, extra: dict | None = None):
                page.mouse.move(1, 1)
                page.wait_for_timeout(250)
                key = f"{board}-{width}"
                page.screenshot(path=str(out / f"{key}.png"))
                f = page.evaluate(FACTS)
                f["pointer"] = pointer_pass(page, width)
                if extra:
                    f.update(extra)
                facts[key] = f
                print(key, f.get("headline"), f.get("item_rows", [])[:3], f.get("delivery_rows"), f.get("delivered_chips"))

            def scroll_to(page, sel: str):
                page.evaluate(f"document.querySelector({json.dumps(sel)})?.scrollIntoView({{block: 'start'}})")
                page.wait_for_timeout(300)

            today_origin = f"http://127.0.0.1:{today_port}"
            canvas_origin = f"http://127.0.0.1:{canvas_port}"
            IS, DS = ITEMS / "shots", DELIVERY / "shots"
            IS.mkdir(parents=True, exist_ok=True)
            DS.mkdir(parents=True, exist_ok=True)

            # ── Canvas 1: ITEMS ──
            for width, height in WIDTHS:
                ctx, page = open_page(today_origin, width, height)
                open_room(page, NAME)
                shoot(page, IS, facts_items, "0-today", width)
                ctx.close()
                ctx, page = open_page(canvas_origin, width, height)
                open_room(page, NAME)
                page.locator("[data-testid=item-row]").first.wait_for(timeout=15_000)
                shoot(page, IS, facts_items, "1a-late-first-view", width)
                scroll_to(page, "[data-p9=items]")
                shoot(page, IS, facts_items, "1b-late-items", width)
                # F10: SOURCES and its Steward verb in view; the Ask well covers nothing.
                page.evaluate("[...document.querySelectorAll('.btn')].find(b => b.innerText.trim() === 'Steward')?.scrollIntoView({block: 'center'})")
                page.wait_for_timeout(300)
                shoot(page, IS, facts_items, "1c-sources-in-view", width)
                close_windows(page)
                open_room(page, EMPTY)
                shoot(page, IS, facts_items, "3-empty-omitted", width)
                ctx.close()
                # Astra r1 F7: the face's items read fails -> UNAVAILABLE, not empty.
                ctx, page = open_page(canvas_origin, width, height, "&items_fail=1")
                open_room(page, NAME)
                page.locator("[data-testid=items-unavailable]").wait_for(timeout=15_000)
                scroll_to(page, "[data-p9=items]")
                shoot(page, IS, facts_items, "4-items-unavailable", width)
                ctx.close()
            # Board 2: the rehearsal reached (a real transition) -> health back.
            s, r = hub_api(hub_url, "POST", f"/api/projects/{pid}/items/{rehearsal_id}/transition", {"verb": "reached"})
            facts_items["_seed"]["transition"] = {"status": s, "lifecycle": (r or {}).get("item", {}).get("lifecycle") if isinstance(r, dict) else r}
            for width, height in WIDTHS:
                ctx, page = open_page(canvas_origin, width, height)
                open_room(page, NAME)
                page.locator("[data-testid=item-row]").first.wait_for(timeout=15_000)
                shoot(page, IS, facts_items, "2a-reached-first-view", width)
                scroll_to(page, "[data-p9=items]")
                shoot(page, IS, facts_items, "2b-reached-items", width)
                ctx.close()

            # ── Canvas 2: COPY AND CONFIRM ──
            for width, height in WIDTHS:
                ctx, page = open_page(today_origin, width, height)
                open_room(page, NAME)
                enter_updates(page)
                shoot(page, DS, facts_delivery, "0a-today-list", width)
                open_update(page, "published")
                shoot(page, DS, facts_delivery, "0b-today-published", width)
                ctx.close()

                ctx, page = open_page(canvas_origin, width, height)
                open_room(page, NAME)
                enter_updates(page)
                open_update(page, "published", upd)
                page.locator("[data-testid=update-verb-copy]").click()
                page.wait_for_timeout(400)
                clip = page.evaluate("navigator.clipboard.readText().catch(e => 'ERR ' + e)")
                shoot(page, DS, facts_delivery, "1-after-copy", width, {"clipboard_head": str(clip)[:80]})
                # He leaves and returns: a full reload, the Room reopened. No clipboard state.
                page.reload(wait_until="load")
                boot(page)
                open_room(page, NAME)
                enter_updates(page)
                open_update(page, "published", upd)
                shoot(page, DS, facts_delivery, "2-returned", width)
                # To "Priya" (the mistaken one), then the press held: the pending face.
                page.locator("[data-testid=deliver-to]").fill("Priya")
                shoot(page, DS, facts_delivery, "3-to-typed", width)
                page.evaluate("window.__philoHold = true")
                page.locator("[data-testid=deliver-verb]").dblclick()
                page.wait_for_timeout(300)
                shoot(page, DS, facts_delivery, "4-pending", width)
                page.evaluate("window.__philoRelease && window.__philoRelease()")
                page.locator("[data-testid=delivery-row]").first.wait_for(timeout=10_000)
                page.wait_for_timeout(500)
                calls = page.evaluate("window.__philoDeliveryCalls")
                shoot(page, DS, facts_delivery, "5-delivered-once", width, {"calls_after_double_click": calls})
                # The correct one: To "Tomas". The wrong row stays.
                page.locator("[data-testid=deliver-to]").fill("Tomas")
                page.locator("[data-testid=deliver-verb]").click()
                page.wait_for_function("document.querySelectorAll('[data-testid=delivery-row]').length >= 2", timeout=10_000)
                page.wait_for_timeout(400)
                shoot(page, DS, facts_delivery, "6-mistake-kept", width, {"calls": page.evaluate("window.__philoDeliveryCalls")})
                # Astra r1 F4: a named refusal (fixture code from the hub's set).
                page.locator("[data-testid=deliver-to]").fill("Priya")
                page.evaluate("window.__philoRefuseNext = 'update_not_published'")
                page.locator("[data-testid=deliver-verb]").click()
                page.locator("[data-testid=deliver-refused]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, DS, facts_delivery, "6b-refused", width, {
                    "refused_code": page.locator("[data-testid=deliver-refused]").get_attribute("data-code")})
                # Astra r1 F4: the answer is lost after the row committed -> result unknown.
                page.locator("[data-testid=deliver-to]").fill("Lena")
                page.evaluate("window.__philoLoseNext = true")
                page.locator("[data-testid=deliver-verb]").click()
                page.locator("[data-testid=deliver-uncertain]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                # The field is locked to this confirmation's payload.
                locked_try = page.evaluate("""() => { const i = document.querySelector('[data-testid=deliver-to]');
                  return {disabled: i.disabled, value: i.value}; }""")
                shoot(page, DS, facts_delivery, "6c-result-unknown", width, {"to_field_during_unknown": locked_try,
                      "calls": page.evaluate("window.__philoDeliveryCalls")})
                # Astra r2 F1: the unresolved confirmation stays with update A.
                # Back -> open B: B is clean (free field, no Retry, no unknown).
                go_back(page)
                open_update(page, "published", upd_b)
                b_state = page.evaluate(DELIVERY_STATE)
                shoot(page, DS, facts_delivery, "6d-other-update-clean", width, {"b_state": b_state})
                # Back -> open A: A still holds its unknown result and its Retry.
                go_back(page)
                open_update(page, "published", upd)
                a_state = page.evaluate(DELIVERY_STATE)
                shoot(page, DS, facts_delivery, "6e-back-on-a-still-unknown", width, {"a_state": a_state})
                page.locator("[data-testid=deliver-retry]").click()
                page.locator("[data-testid=deliver-uncertain]").wait_for(state="detached", timeout=10_000)
                page.wait_for_timeout(400)
                calls = page.evaluate("window.__philoDeliveryCalls")
                lost, retry = calls[-2], calls[-1]
                a_rows = page.evaluate("[...document.querySelectorAll('[data-testid=delivery-row]')].map(r => r.innerText.replace(/\\s+/g, ' ').trim())")
                shoot(page, DS, facts_delivery, "6f-retried-one-row", width, {"calls": calls,
                      "retry_same_update": retry["update_id"] == lost["update_id"] == upd,
                      "retry_same_key": retry["command_id"] == lost["command_id"],
                      "retry_same_to": retry["delivered_to"] == lost["delivered_to"],
                      "lena_rows_on_a": sum("Lena" in r for r in a_rows)})
                # B still has no delivery.
                go_back(page)
                open_update(page, "published", upd_b)
                facts_delivery[f"6f-retried-one-row-{width}"]["b_rows_after"] = page.evaluate(
                    "document.querySelectorAll('[data-testid=delivery-row]').length")
                facts_delivery[f"6f-retried-one-row-{width}"]["b_calls"] = sum(1 for c in calls if c["update_id"] == upd_b)
                # Back to the list (the 393 defect of round one: diagnosed here).
                back = page.locator("[data-testid=update-verb-back]")
                back.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                diag = page.evaluate("""() => { const b = document.querySelector('[data-testid=update-verb-back]');
                  const r = b.getBoundingClientRect(); const el = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
                  window.__backClicks = 0; b.addEventListener('click', () => { window.__backClicks++; });
                  window.__evlog = [];
                  for (const t of ['pointerdown', 'pointerup', 'click', 'focusin', 'scroll']) document.addEventListener(t, (e) => {
                    const bb = document.querySelector('[data-testid=update-verb-back]')?.getBoundingClientRect();
                    window.__evlog.push([t, String(e.target && (e.target.className || e.target.tagName)).slice(0, 50), bb ? Math.round(bb.top) : null]); }, true);
                  return {rect: [r.left, r.top, r.width, r.height], hit: el ? String(el.className || el.tagName) : null, owned: !!el && b.contains(el)}; }""")
                back.click()
                back_ok = True
                try:
                    page.locator("[data-testid=update-list]").wait_for(timeout=10_000)
                except Exception:
                    back_ok = False
                    page.screenshot(path=os.environ.get("DEBUG_SHOT", "/tmp/philo9-back-fail.png"))
                    diag["after"] = page.evaluate("""() => ({clicks: window.__backClicks, evlog: window.__evlog.slice(0, 30),
                      phase: document.querySelector('[data-testid=update-posture]')?.dataset.phase ?? null,
                      editor: !!document.querySelector('[data-testid=update-editor]')})""")
                    errors.append(f"{width}: Back did not return to the list; Escape used; {diag}")
                    page.locator("[data-testid=update-editor]").press("Escape")
                    page.locator("[data-testid=update-list]").wait_for(timeout=10_000)
                diag["clicks"] = page.evaluate("window.__backClicks")
                page.wait_for_timeout(500)
                facts_delivery.setdefault("_back", {})[str(width)] = {"worked": back_ok, **diag}
                shoot(page, DS, facts_delivery, "7a-list-chip-count", width)
                # The other chip form (same stored rows: sessionStorage survives the reload).
                page.goto(f"{canvas_origin}/?chip=latest", wait_until="load")
                boot(page)
                open_room(page, NAME)
                enter_updates(page)
                shoot(page, DS, facts_delivery, "7b-list-chip-latest", width)
                # A draft offers no Mark delivered.
                if page.locator("[data-testid=update-list-item]:has([data-lifecycle=draft])").count():
                    open_update(page, "draft")
                else:
                    page.locator("[data-testid=update-verb-draft-deterministic]").click()
                    page.locator("[data-testid=update-editor][data-lifecycle=draft]").wait_for(timeout=20_000)
                    page.wait_for_timeout(800)
                shoot(page, DS, facts_delivery, "8-draft-no-mark", width)
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
    (ITEMS / "shots" / "facts.json").write_text(json.dumps({**facts_items, "_browser_errors": errors}, indent=2, ensure_ascii=False) + "\n")
    (DELIVERY / "shots" / "facts.json").write_text(json.dumps({**facts_delivery, "_browser_errors": errors}, indent=2, ensure_ascii=False) + "\n")
    print("errors:", len(errors))


if __name__ == "__main__":
    main()
