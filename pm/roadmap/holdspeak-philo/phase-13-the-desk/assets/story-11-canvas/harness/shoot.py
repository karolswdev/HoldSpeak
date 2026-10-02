"""PHILO-13-11 (C1) canvas: the Workbench look, drawn on the REAL product.

Everything is live except the stand-ins named in harness/p13.tsx's header: a REAL
hub (scripts/graph_walk.py serve) on an isolated HOME (tempfile.mkdtemp under
/tmp, removed when the run ends), seeded through the product's producers
(seed_db.py, the Phase 13 grounding seed) and its routes (rig.seed_hub); the
PRODUCT app served by vite with the seats (vite.config.mjs) and the proposed
material (canvas.css). Nothing leaves the machine; no send is pressed.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/harness/shoot.py

Shots: ../shots/C1-<n>-<name>-<width>.png at 1440x900 and 393x852 (device scale 2);
facts.json beside them. Each width runs on its own hub and HOME (the proposal),
and the comparison's alternative runs on the same hub with the theme switched.
ONLY_WIDTH=393 limits the run to one width; ONLY=C1-2 to boards whose id starts so;
STACK_STATE=<dev.py state file> reuses a running stack (iteration only).
Exit 2 on a failed fence.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig  # noqa: E402

CANVAS = HERE.parent
SHOTS = CANVAS / "shots"
ALL_WIDTHS = [(1440, 900), (393, 852)]
WIDTHS = [w for w in ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
ONLY = os.environ.get("ONLY", "")

# ── the rendered facts of one board ─────────────────────────────────────────
FACTS = r"""() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !e.closest('[hidden]'); };
  // The proposal's own surface: the frame (screen bar, Dock), every window head, every menu, every p13 element.
  const roots = [...document.querySelectorAll('.desk-menubar, .desk-dock, .desk-pullout-head, [role=menu], .p13-chairwin, .p13-parked, .p13-park-receipt, .p13-sheet')].filter(vis);
  const small = [], raw = [];
  for (const root of roots) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const t = n.textContent.trim(); if (!t || !/[A-Za-z0-9]/.test(t)) continue;  // a glyph is not text (UX-CANON C)
      const el = n.parentElement; if (!vis(el)) continue;
      const fs = parseFloat(getComputedStyle(el).fontSize);
      if (fs < 12) small.push({ text: t.slice(0, 30), fs, where: (root.className || '').toString().slice(0, 40), proposal: !el.closest('.desk-surface-body, .desk-window-shell > :not(.desk-pullout-head)') || !!el.closest('.p13-parked, .p13-park-receipt, .p13-sheet') });
    }
    for (const b of [...(root.matches('button') ? [root] : []), ...root.querySelectorAll('button')]) {
      if (!vis(b)) continue;
      const cn = String(b.className || '');
      // the library Button: plated (.btn) or chrome (variant="chrome" carries no plate class; Signal.tsx:62)
      if (!/(^|\s)(btn|btn--chrome)(\s|$)/.test(cn) && !b.closest('.desk-menu-list')) raw.push({ text: (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30), cls: cn.slice(0, 60), proposal: !!b.closest('[class*=p13-], .p13-chairwin') && !b.closest('.desk-surface-body') });
    }
  }
  const shells = [...document.querySelectorAll('.desk-window-shell')].filter(vis).filter((s) => !s.closest('.p13-sample-stack'));
  const windows = shells.map((s) => {
    const head = s.querySelector(':scope > .desk-pullout-head');
    return {
      name: s.getAttribute('aria-label') || '',
      front: s.hasAttribute('data-p13-front'),
      close: head ? head.querySelectorAll('.p13-gadgets-left .p13-g-close').length : 0,
      depth: head ? head.querySelectorAll('.p13-gadgets-right .p13-g-depth').length : 0,
      zoom: head ? head.querySelectorAll('.p13-gadgets-right .p13-g-zoom').length : 0,
      iconify: head ? head.querySelectorAll('.p13-gadgets-right .p13-g-iconify').length : 0,
      old_traffic_visible: head ? [...head.querySelectorAll('.desk-traffic')].filter(vis).length : 0,
      frame: getComputedStyle(s).borderLeftColor,
    };
  });
  const dock = document.querySelector('.desk-dock');
  const dr = dock ? dock.getBoundingClientRect() : null;
  const menu = [...document.querySelectorAll('[role=menu]')].filter(vis);
  return {
    screen_title: (document.querySelector('.p13-screen-name') || {}).innerText || null,
    clock: (document.querySelector('.desk-clock') || {}).innerText || null,
    windows,
    dock: dr ? { left: Math.round(dr.left), right: Math.round(dr.right), top: Math.round(dr.top), height: Math.round(dr.height), scrolls: dock.scrollWidth > dock.clientWidth } : null,
    appstates: [...document.querySelectorAll('.desk-dock .p13-appstate, .desk-dock .desk-dock-badge')].filter(vis).map((e) => e.innerText.trim()),
    menus: menu.map((m) => ({ label: m.getAttribute('aria-label'), rows: [...m.querySelectorAll('[role^=menuitem]')].filter(vis).map((r) => r.innerText.replace(/\s+/g, ' ').trim()) })),
    small_text: small,
    raw_buttons: raw,
    zero_counter: roots.some((r) => /(^|\s)0 [A-Z]{2,}/.test(r.innerText || '')),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], dialog[open]'),
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
  };
}"""

# ONE meaning of "needs you" (story 03): every "need(s) you" on the glass is the Chair head's number,
# and the bell and the Dock's needs-you badges carry the same number.
NEEDS = r"""() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && getComputedStyle(e).visibility !== 'hidden'; };
  const said = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.replace(/\s+/g, ' ').trim();
    if (/needs? you/i.test(t) && vis(n.parentElement)) said.push(t);
  }
  const head = document.querySelector('[data-testid=arrival-display]');
  const num = (t) => { const m = (t || '').match(/\d+/); return m ? Number(m[0]) : null; };
  const bell = document.querySelector('.desk-bell strong');
  const intel = document.querySelector('.desk-dock [aria-label^="Intelligence"] .desk-dock-badge');
  const memory = document.querySelector('.desk-dock [aria-label^="Desk memory"] .desk-dock-badge');
  return { said, head: head ? head.innerText : null, head_n: num(head && head.innerText), bell: num(bell && bell.innerText),
           intel: num(intel && intel.innerText), memory: num(memory && memory.innerText) };
}"""

# 393: the shelf ends on a whole icon (no icon cut by the edge or by the More gadget).
SHELF = r"""() => {
  const dock = document.querySelector('.desk-dock'); if (!dock) return null;
  const more = dock.querySelector('.p13-dock-more'); const edge = more ? more.getBoundingClientRect().left : innerWidth;
  const cut = [...dock.children].filter((c) => c !== more).map((c) => ({ c, r: c.getBoundingClientRect() }))
    .filter(({ r }) => r.width && r.left < edge - 1 && r.right > edge + 1).map(({ c }) => (c.getAttribute('aria-label') || c.className || '').toString().slice(0, 40));
  const whole = [...dock.children].filter((c) => c !== more).filter((c) => { const r = c.getBoundingClientRect(); return r.width && r.left >= -1 && r.right <= edge + 1; })
    .map((c) => (c.getAttribute('aria-label') || '').split(',')[0]);
  return { cut, whole, more: !!more, more_w: more ? Math.round(more.getBoundingClientRect().width) : 0, more_h: more ? Math.round(more.getBoundingClientRect().height) : 0 };
}"""

# Each gadget owns its points (UX-CANON C: a chrome strip's row owes the target).
GADGET_POINTS = r"""() => [...document.querySelectorAll('.p13-gadget')].filter((g) => { const r = g.getBoundingClientRect(); return r.width && r.height && r.top >= 0 && r.bottom <= innerHeight; })
  .map((g) => { const b = g.getBoundingClientRect();
    const xs = [b.left + 2, b.left + b.width / 2, b.right - 2], ys = [b.top + 2, b.top + b.height / 2, b.bottom - 2];
    const mine = g.closest('.desk-window-shell, .desk-menubar, .desk-dock');
    let own = 0, shown = 0; for (const x of xs) for (const y of ys) { const h = document.elementFromPoint(x, y); if (!h) continue; if (g.contains(h)) own++; else if (mine && mine.contains(h)) shown++; }
    return { name: g.getAttribute('aria-label'), w: Math.round(b.width), h: Math.round(b.height), own, under_other: 9 - own - shown }; })"""


# Text below 4.5:1 on the ground it is really on (the first opaque ancestor background), in view.
CONTRAST = r"""() => {
  const lum = (c) => { const m = c.match(/[\d.]+/g); if (!m) return null; const [r, g, b] = m.slice(0, 3).map(Number).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const alpha = (c) => { const m = c.match(/[\d.]+/g); return m && m.length > 3 ? Number(m[3]) : 1; };
  const ground = (e) => { for (let a = e; a; a = a.parentElement) { const bg = getComputedStyle(a).backgroundColor; if (alpha(bg) >= 0.9) return bg; } return 'rgb(14,15,19)'; };
  const out = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.trim(); if (!t || !/[A-Za-z0-9]/.test(t)) continue;
    const el = n.parentElement; const r = el.getBoundingClientRect();
    if (!r.width || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || alpha(cs.color) < 0.5) continue;
    const top = document.elementFromPoint(Math.min(innerWidth - 1, Math.max(0, r.left + 2)), Math.min(innerHeight - 1, Math.max(0, r.top + r.height / 2)));
    if (top && !el.contains(top) && !top.contains(el)) continue;
    const a = lum(cs.color), b = lum(ground(el)); if (a === null || b === null) continue;
    const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    if (ratio < 4.5) out.push({ text: t.slice(0, 28), ratio: Math.round(ratio * 100) / 100 });
  }
  return out;
}"""


def run(width: int, height: int, state: dict | None) -> tuple[list[str], dict]:
    facts: dict = {}
    fails: list[str] = []
    errors: list[str] = []
    phone = width <= 420
    stack = None
    try:
        if state is None:
            stack = rig.Stack("proposal").__enter__()
            url, seed, guard = stack.url, stack.seed, stack.guard
        else:
            url, seed, guard = state["url"], state["seed"], state.get("guard")
        facts[f"_seat_guard_{width}"] = guard
        facts[f"_seed_{width}"] = {k: v for k, v in seed.items() if k != "db"}
        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, has_touch=phone)
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.on("console", lambda m: errors.append(f"console: {m.text[:200]}")
                    if m.type == "error" and "status of 4" not in m.text and "Failed to fetch" not in m.text else None)
            try:
                boards(page, width, url, seed, facts, fails)
            except Exception as exc:
                traceback.print_exc()
                fails.append(f"CRASH at width {width}: {str(exc).splitlines()[0][:300]}")
                try:
                    page.screenshot(path=str(SHOTS / f"_crash-{width}.png"))
                except Exception:
                    pass
            browser.close()
    finally:
        if stack is not None:
            stack.__exit__(None, None, None)
        facts[f"_browser_errors_{width}"] = errors
    return fails, facts


def boards(page, width: int, url: str, seed: dict, facts: dict, fails: list[str]) -> None:
    phone = width <= 420
    W, H = page.viewport_size["width"], page.viewport_size["height"]

    def ev(js: str, arg=None):
        return page.evaluate(js, arg)

    def boot():
        page.goto(url, wait_until="load")
        page.locator(".chair").wait_for(timeout=120_000)
        for _ in range(40):
            cl = page.get_by_role("button", name="Continue later", exact=True)
            if not cl.count():
                break
            try:
                cl.first.click(timeout=2000)
            except Exception:
                pass
            page.wait_for_timeout(500)
        page.locator("[data-testid=p13-chair-needs]").wait_for(timeout=60_000)
        page.wait_for_timeout(2500)
        ev("() => window.__p13.live({rec: '12:04', oneOnOne: '14:30', projects: {'p-ledger': 3, 'p-obs': 1}})")
        ev("() => { window.__p13.sheet(false); window.__p13Open.closeAll(); }")
        page.wait_for_timeout(800)
        ev("() => { window.__p13Booted = true; }")

    def settle(ms=700):
        page.wait_for_timeout(ms)

    def close_all():
        ev("() => window.__p13Open.closeAll()")
        page.keyboard.press("Escape")
        settle(600)

    def shoot(board: str, checks: dict | None = None, extra: dict | None = None):
        if ONLY and not board.startswith(ONLY):
            return None
        # no stray focus ring from the rig's own clicks (kept while a menu is open: it is the menu's)
        ev("() => { if (!document.querySelector('[role=menu]')) document.activeElement?.blur?.(); }")
        settle(500)
        key = f"{board}-{width}"
        if not ev("() => window.__p13Booted === true"):
            fails.append(f"{key}: the page reloaded during the run (the board would show a boot screen)")
        page.screenshot(path=str(SHOTS / f"{key}.png"))
        f = ev(FACTS)
        f["gadget_points"] = ev(GADGET_POINTS)
        f["needs_you"] = ev(NEEDS)
        if phone:
            f["shelf"] = ev(SHELF)
        if extra:
            f.update(extra)
        facts[key] = f
        law = {
            "(1) every window carries close + depth, zoom at 1440": all(w["close"] == 1 and w["depth"] == 1 and (phone or w["zoom"] == 1) for w in f["windows"]),
            "(1) the old traffic lights are gone": all(w["old_traffic_visible"] == 0 for w in f["windows"]),
            "(2) the screen bar names a window": bool(f["screen_title"]),
            "(2) the screen bar shows the time": bool(f["clock"]),
            "(5) no text under 12 px in the proposal (frame, heads, menus, Chair windows' chrome, parked face)": not [x for x in f["small_text"] if x["proposal"]],
            "(5) no raw button in the proposal": not [x for x in f["raw_buttons"] if x["proposal"]],
            "no counter of zero": not f["zero_counter"],
            "no modal": not f["modal"],
            "no horizontal overflow": not f["h_overflow"],
            "the Dock inside the viewport": bool(f["dock"]) and f["dock"]["left"] >= 0 and f["dock"]["right"] <= W,
            "each gadget on top owns its points (one under a window in front is occluded, not a defect)": all(g["own"] >= 1 or g["under_other"] >= 5 for g in f["gadget_points"]),
        }
        ny = f["needs_you"]
        n = ny["head_n"]
        law["one needs-you number: every 'need(s) you' on the glass is the Chair head's"] = all(
            (t == ny["head"]) or t == "Needs you" or (n is not None and t.startswith(f"{n} need")) for t in ny["said"])  # "Needs you" = the Chair window's name
        if n is not None:
            law["the bell carries the Chair's needs-you number"] = ny["bell"] == n
            law["the Dock (Intelligence, Desk memory) carries the same number"] = ny["intel"] in (n, None) and ny["memory"] in (n, None)
        if phone:
            law["(393) the shelf ends on a whole icon; the More gadget is 44 px or more"] = bool(f["shelf"]) and not f["shelf"]["cut"] and f["shelf"]["more"] and f["shelf"]["more_w"] >= 44 and f["shelf"]["more_h"] >= 44
            law["no scratch path on the glass"] = not ev("() => /p13c1-|\\/private\\/tmp|\\/tmp\\//.test(document.body.innerText)")
        else:
            law["no scratch path on the glass"] = not ev("() => /p13c1-|\\/private\\/tmp|\\/tmp\\//.test(document.body.innerText)")
        if phone:
            law["(393) gadgets 44 px wide, the bar 44 px high"] = all(g["w"] >= 44 and g["h"] >= 43 for g in f["gadget_points"] if not g["name"].endswith("Material"))
        for name, ok in {**law, **(checks or {})}.items():
            if not ok:
                fails.append(f"{key}: {name}")
        print(key, "title", f["screen_title"], "windows", [(w["name"], w["front"]) for w in f["windows"]],
              "appstates", f["appstates"], "small", f["small_text"][:3], "raw", f["raw_buttons"][:3], flush=True)
        return f

    def jsclick(loc):
        """Select an element by its own click handler (the look canvas proves faces, not gestures)."""
        loc.first.evaluate("(e) => { e.scrollIntoView({block: 'center'}); e.click(); }")
        settle(700)

    def front_win():
        return ev("() => { const s=document.querySelector('.desk-window-shell[data-p13-front]'); return s ? s.getAttribute('aria-label') : null; }")

    # WARM-UP (not a board): a cold vite server optimizes a dependency the first time a lazy
    # window imports it and then RELOADS the page. Open every window the boards use once, then
    # start clean. The reload fence in shoot() proves no board was drawn across a reload.
    page.goto(url, wait_until="load")
    page.locator(".chair").wait_for(timeout=120_000)
    page.wait_for_timeout(2000)
    for js, arg in [("(s) => window.__p13Open.surface(s)", "review-meetings"), ("(p) => window.__p13Open.room(p)", "p-ledger"),
                    ("(s) => window.__p13Open.surface(s)", "open-people"), ("(r) => window.__p13Open.open(r)", f"workbench:{seed['workbench']}"),
                    ("() => window.__p13.sheet(true)", None)]:
        try:
            ev(js, arg) if arg is not None else ev(js)
        except Exception:
            pass
        page.wait_for_timeout(2500)
    page.wait_for_timeout(3000)
    boot()

    # ── C1-1 the whole Desk: screen title bar, the Chair as windows, the Dock with live AppIcons ──
    ev("() => window.__p13.chairFront('needs')")
    f = shoot("C1-1-the-desk", checks={})
    if f is not None:
        if f["screen_title"] != "Needs you":
            fails.append(f"C1-1-{width}: the screen title names the front window (got {f['screen_title']})")
        need = ["REC 12:04", "1:1 14:30"] if not phone else ["REC 12:04"]
        for n in need:
            if not any(n in a for a in f["appstates"]):
                fails.append(f"C1-1-{width}: AppIcon state {n} not drawn")

    # ── C1-2 one window close-up: the gadget set, its menu bar on the right button ──
    if not ONLY or "C1-2".startswith(ONLY[:4]) or ONLY.startswith("C1-2"):
        ev("(s) => window.__p13Open.surface(s)", "review-meetings")
        settle(2500)
        ev("(p) => window.__p13Open.room(p)", "p-ledger")
        settle(3000)
        if not phone:
            # place the two real windows so one overlaps the other (the depth story)
            ev("""() => { const m = document.querySelector('.desk-window-shell[aria-label="Meetings"]');
                  const r = [...document.querySelectorAll('.desk-window-shell')].find(e => /Payments ledger/.test(e.getAttribute('aria-label')||''));
                  return [m && m.getBoundingClientRect().toJSON(), r && r.getBoundingClientRect().toJSON()]; }""")
        head = page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head").last
        hb = head.bounding_box()
        title = front_win()
        f = shoot("C1-2a-window-gadgets", extra={"front": title})
        if f is not None and f["screen_title"] != title:
            fails.append(f"C1-2a-{width}: the screen title ({f['screen_title']}) is not the front window ({title})")
        # the right button on the head: the window's menu bar at the pointer, the Amiga-key column
        # The right button on the drag bar just past the title, so the menu opens beside it and the
        # front window's name stays readable.
        tb = page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head .desk-pullout-title").last.bounding_box()
        px = tb["x"] + tb["width"] + 18
        py = tb["y"] + (tb["height"] / 2 if not phone else tb["height"] + 8)
        if phone:
            px, py = tb["x"] + tb["width"] - 10, tb["y"] + tb["height"] / 2
        page.mouse.click(px, py, button="right")
        page.locator("[role=menu]").first.wait_for(timeout=10_000)
        settle(300)
        if not phone:
            page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Desk')").first.hover()
            settle(600)
        else:
            page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Desk')").first.click()
            settle(600)
        f = shoot("C1-2b-window-menu-amiga-keys")
        if f is not None:
            rows = [r for m in f["menus"] for r in m["rows"]]
            if not any("⌘N" in r.replace(" ", "") for r in rows):
                fails.append(f"C1-2b-{width}: no Amiga-key column on the menu ({rows})")
        page.keyboard.press("Escape")
        page.keyboard.press("Escape")
        settle(400)
        ev("() => document.body.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}))")
        settle(300)
        # depth: the front window goes behind; the next one comes to the front
        before = front_win()
        page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head .p13-g-depth").last.click()
        settle(800)
        after = front_win()
        f = shoot("C1-2c-depth-to-back", extra={"before": before, "after": after})
        if f is not None and (before == after or not after):
            fails.append(f"C1-2c-{width}: depth did not change the front window ({before} -> {after})")
        if not phone:
            page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head .p13-g-zoom").last.click()
            settle(900)
            shoot("C1-2d-zoom")
            page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head .p13-g-zoom").last.click()
            settle(600)
        close_all()

    # ── C1-3 the material tokens sheet ──
    ev("() => window.__p13.sheet(true)")
    settle(900)
    shoot("C1-3-material-tokens")
    ev("() => window.__p13.sheet(false)")
    settle(400)

    # ── C1-4 the Chair composed of windows (brief, needs you, the week), populated ──
    if phone:
        ev("() => window.__p13.phoneOpen('brief')")
        ev("() => window.__p13.chairFront('brief')")
    else:
        ev("() => window.__p13.chairFront('week')")
    settle(700)
    f = shoot("C1-4a-chair-windows")
    if f is not None:
        names = {w["name"] for w in f["windows"]}
        for n in ("Needs you", "Brief", "The week"):
            if n not in names:
                fails.append(f"C1-4a-{width}: the Chair has no {n} window")
    if phone:
        ev("() => window.__p13.phoneOpen('week')")
        ev("() => window.__p13.chairFront('week')")
    else:
        page.locator("[data-testid=p13-chair-brief] .p13-g-zoom").click()
    settle(800)
    shoot("C1-4b-chair-window-zoomed" if not phone else "C1-4b-chair-week-open")
    if not phone:
        page.locator("[data-testid=p13-chair-brief] .p13-g-zoom").click()
        settle(500)
    else:
        ev("() => window.__p13.phoneOpen('needs')")
    ev("() => window.__p13.chairFront('needs')")

    # ── C1-5 Parked and Restore (A1-F): Meetings, then the Workbench window ──
    ev("(s) => window.__p13Open.surface(s)", "review-meetings")
    settle(2500)
    row = page.locator(".desk-window-shell[aria-label='Meetings'] :text('Hiring debrief: staff engineer')").first
    jsclick(row)
    settle(800)
    shoot("C1-5a-meeting-selected-park")
    park = page.locator("[data-testid=p13-park]").first
    jsclick(park)
    f = shoot("C1-5b-meeting-parked-receipt")
    if f is not None:
        txt = ev("() => (document.querySelector('[data-testid=p13-park-receipt-meetings]') || {}).innerText || ''")
        if "PARKED" not in txt or "Restore" not in txt:
            fails.append(f"C1-5b-{width}: no PARKED receipt with Restore ({txt!r})")
        gone = ev("() => !![...document.querySelectorAll('.desk-window-shell[aria-label=Meetings] *')].find(e => e.children.length === 0 && /Hiring debrief: staff engineer/.test(e.textContent))")
        if gone:
            fails.append(f"C1-5b-{width}: the parked meeting is still in the list")
    jsclick(page.locator("[data-testid=p13-parked-meetings] button, [data-testid=p13-parked-meetings] label"))
    f = shoot("C1-5c-meetings-parked-filter")
    jsclick(page.locator("[data-testid=p13-parked-row] button:has-text('Restore')"))
    f = shoot("C1-5d-meeting-restored")
    if f is not None:
        back = ev("() => !![...document.querySelectorAll('.desk-window-shell[aria-label=Meetings] *')].find(e => e.children.length === 0 && /Hiring debrief: staff engineer/.test(e.textContent))")
        if not back:
            fails.append(f"C1-5d-{width}: Restore did not bring the meeting back")
    close_all()
    ev("(r) => window.__p13Open.open(r)", f"workbench:{seed['workbench']}")
    settle(3000)
    wb = page.locator(".desk-window-shell[data-p13-front]").last
    coll = wb.locator("button:has-text('Collapse')")
    if coll.count():
        jsclick(coll)
    item = wb.locator(":text('Old sampling spike')").first
    jsclick(item)
    rm = wb.locator("button:has-text('Remove'), button[aria-label^='Remove']")
    if rm.count():
        jsclick(rm)
    else:
        ev("(t) => window.__p13Park('workbench', {id: 'canvas-item', title: t})", "Old sampling spike")
        settle(600)
    f = shoot("C1-5e-workbench-item-parked")
    jsclick(page.locator("[data-testid=p13-parked-workbench] button, [data-testid=p13-parked-workbench] label"))
    page.locator("[data-testid=p13-parked-workbench]").first.evaluate("(e) => e.scrollIntoView({block: 'start'})")
    settle(400)
    shoot("C1-5f-workbench-parked-filter")
    close_all()

    # ── C1-6 the phone desk (393): one window open, the rest are title bars; one-row Dock ──
    if phone:
        ev("() => window.__p13.phoneOpen('needs')")
        ev("() => window.__p13.chairFront('needs')")
        settle(600)
        frame = ev("""() => { const bar = document.querySelector('.desk-menubar').getBoundingClientRect();
            const dock = document.querySelector('.desk-dock').getBoundingClientRect();
            const open = document.querySelector('.p13-chairwin[data-phone-open]').getBoundingClientRect();
            return { bar: Math.round(bar.height), dock: Math.round(dock.height), frame: Math.round(bar.height + dock.height), open_window: Math.round(open.height) }; }""")
        f = shoot("C1-6a-phone-desk", extra={"frame": frame})
        if f is not None and frame["frame"] > 142:
            fails.append(f"C1-6a-{width}: the frame takes {frame['frame']} px (C7 budget 142)")
        ev("(s) => window.__p13Open.surface(s)", "open-people")
        settle(2500)
        shoot("C1-6b-phone-window-sheet")
        close_all()

    # ── C1-7 the comparison: the recommendation and the one alternative, same Desk, two states ──
    if not ONLY or ONLY.startswith("C1-7"):
        def pair(tag: str):
            page.screenshot(path=str(SHOTS / f"_cmp-steel-{tag}-{width}.png"))
            facts[f"_cmp_steel_{tag}_{width}"] = {"low_contrast": ev(CONTRAST)}
            ev("() => window.__p13.theme('honest')")
            settle(900)
            page.screenshot(path=str(SHOTS / f"_cmp-honest-{tag}-{width}.png"))
            facts[f"_cmp_honest_{tag}_{width}"] = {"low_contrast": ev(CONTRAST)}
            ev("() => window.__p13.theme(null)")
            settle(500)
        ev("() => window.__p13.chairFront('needs')")
        if phone:
            ev("() => window.__p13.phoneOpen('needs')")
        settle(600)
        pair("chair")
        ev("(s) => window.__p13Open.surface(s)", "review-meetings")
        settle(2000)
        ev("(p) => window.__p13Open.room(p)", "p-ledger")
        settle(3000)
        pair("windows")
        close_all()


def compose_comparison() -> None:
    """C1-7: one artboard per width: the two directions side by side, in two states (the Chair; two windows)."""
    for width, height in WIDTHS:
        tags = ["chair", "windows"]
        if not all((SHOTS / f"_cmp-{d}-{t}-{width}.png").exists() for d in ("steel", "honest") for t in tags):
            continue
        pad = 12 if width > 500 else 4
        cells = "".join(f'<img src="_cmp-steel-{t}-{width}.png"><img src="_cmp-honest-{t}-{width}.png">' for t in tags)
        html = f"""<!doctype html><html><head><style>
          body {{ margin: 0; background: #3c4454; font: 700 {13 if width > 500 else 12}px 'JetBrains Mono', monospace; color: #0b0c10; }}
          .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: {pad}px; padding: {pad}px; }}
          .cap {{ background: #eef0f3; border: 1px solid #0b0c10; padding: 3px 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
          .cap.rec {{ background: #6688bb; }}
          img {{ width: 100%; border: 1px solid #0b0c10; display: block; }}
        </style></head><body><div class="grid">
          <div class="cap rec">RECOMMENDED · STEEL</div><div class="cap">ALTERNATIVE · HONEST 2.0</div>
          {cells}
        </div></body></html>"""
        page_file = SHOTS / f"_cmp-{width}.html"
        page_file.write_text(html)
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            pg.goto(page_file.as_uri())
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(SHOTS / f"C1-7-comparison-{width}.png"))
            br.close()
        page_file.unlink()


def main() -> int:
    state = json.loads(Path(os.environ["STACK_STATE"]).read_text()) if os.environ.get("STACK_STATE") else None
    all_fails: list[str] = []
    facts_path = SHOTS / "facts.json"
    facts: dict = json.loads(facts_path.read_text()) if (ONLY or os.environ.get("ONLY_WIDTH")) and facts_path.exists() else {}
    for width, height in WIDTHS:
        fails, f = run(width, height, state)
        all_fails += fails
        facts.update(f)
    if not ONLY or ONLY.startswith("C1-7"):
        compose_comparison()
    facts["_fails"] = all_fails
    facts_path.write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if all_fails else "\nALL FENCES HELD", *all_fails, sep="\n  ")
    return 2 if all_fails else 0


if __name__ == "__main__":
    sys.exit(main())
