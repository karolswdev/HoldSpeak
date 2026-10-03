"""Title bar canvas (owner 2026-10-03: "the title bar looks terrible"): three directions and the
control, drawn on the REAL product.

A REAL hub (scripts/graph_walk.py serve) on an isolated HOME (tempfile.mkdtemp under /tmp, removed
when the run ends), seeded by the C1 canvas seed (seed_db.py + rig.seed_hub, copied from
../../story-11-canvas/harness/); the PRODUCT app as on main, served by vite (vite.config.mjs, no
seat, no shim). Each proposal is one CSS file (proposals/*.css) injected after the app's CSS;
the control injects nothing. Nothing leaves the machine; no send is pressed.

The fences are C1's (../../story-11-canvas/harness/shoot.py, imported, not copied): CONTRAST_ALL
(every text in place, >= 4.5:1, 3:1 large), TARGETS44 (393: every target owns 44 x 44), CLIP (no
sideways strip, no clipped text) and OVERLAP (no rendered overlap, the three narrowed waivers).
OWN is C1's ownership fence over the BUILT gadget classes (C1 drew .p13-gadget; the build ships
.desk-gadget). SMALL is C1's 12 px floor over the whole board. TITLES measures each window's
title in place (contrast on its ground, size, weight, family) and the bar's height.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/titlebar-canvas/harness/shoot.py
STACK_STATE=<dev.py state file> reuses a running stack (iteration only). ONLY=A limits the run to
one direction. Exit 2 on a failed fence.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig  # noqa: E402

_spec = importlib.util.spec_from_file_location("c1shoot", HERE.parents[1] / "story-11-canvas/harness/shoot.py")
C1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C1)

CANVAS = HERE.parent
SHOTS = CANVAS / "shots"
DIRECTIONS = [
    ("control", None),
    ("A", HERE / "proposals/A-quiet.css"),
    ("B", HERE / "proposals/B-refined.css"),
    ("C", HERE / "proposals/C-modern.css"),
]
ONLY = os.environ.get("ONLY", "")

# C1's ownership fence (shoot.py OWN) over the built frame controls.
OWN = "() => {" + C1.JS_LIB.replace(".desk-window-shell:not(.p13-sample-win)", ".desk-window-shell") + r"""
  const sel = '.desk-gadget, .desk-menubar button, .desk-dock > button, .desk-pullout-head .desk-wings button, .desk-pullout-head .desk-window-actions button';
  const out = [];
  for (const t of document.querySelectorAll(sel)) {
    if (!shown(t)) continue;
    const v = vrect(t); if (!v.full) continue;
    const res = nine(v.l, v.t, v.r, v.b).map(([x, y]) => probe(t, x, y));
    const own = res.filter((r) => r === 'own').length, occ = res.filter((r) => r === 'occluded').length;
    out.push({ name: (t.getAttribute('aria-label') || t.innerText || '').trim().slice(0, 32), own, occ, lost: 9 - own - occ, w: Math.round(v.w), h: Math.round(v.h) });
  }
  return out;
}"""

# C1's 12 px floor (shoot.py FACTS small_text) over the whole board.
SMALL = r"""() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !e.closest('[hidden]'); };
  const small = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.trim(); if (!t || !/[A-Za-z0-9]/.test(t)) continue;
    const el = n.parentElement; if (!vis(el)) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs > 0 && fs < 12) small.push({ text: t.slice(0, 30), fs });
  }
  return small;
}"""

# Each window's title, measured in place: its ink on the ground under it (the chain of backgrounds,
# alpha blended), its size, weight and family; the bar's height; which window is in front; and the
# front bar's ground against an inactive bar's ground (the at-a-glance cue, luminance ratio).
TITLES = r"""() => {
  const rgb = (s) => { const m = String(s).match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return Math.round(((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)) * 100) / 100; };
  const blend = (t, u) => ({r: t.r * t.a + u.r * (1 - t.a), g: t.g * t.a + u.g * (1 - t.a), b: t.b * t.a + u.b * (1 - t.a), a: 1});
  const groundOf = (el) => { const chain = []; for (let e = el; e; e = e.parentElement) {
      const c = rgb(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { chain.push(c); if (c.a >= 1) break; } }
    let g = {r: 0, g: 0, b: 0, a: 1}; for (let i = chain.length - 1; i >= 0; i--) g = blend(chain[i], g); return g; };
  const hex = (c) => '#' + [c.r, c.g, c.b].map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
  const shells = [...document.querySelectorAll('.desk-window-shell')].filter((s) => { const r = s.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const out = [];
  for (const s of shells) {
    const head = s.querySelector(':scope > .desk-pullout-head'); if (!head) continue;
    const title = head.querySelector('.desk-pullout-title');
    const hr = head.getBoundingClientRect();
    const row = { name: s.getAttribute('aria-label'), front: s.classList.contains('is-front'), bar_h: Math.round(hr.height * 10) / 10,
                  bar_ground: hex(groundOf(head)), bar_image: getComputedStyle(head).backgroundImage !== 'none' };
    if (title && title.getBoundingClientRect().width > 0 && getComputedStyle(title).display !== 'none') {
      const cs = getComputedStyle(title); const fg = rgb(cs.color); const g = groundOf(title);
      Object.assign(row, { title: title.textContent.trim().slice(0, 30), ink: hex(fg), ground: hex(g), contrast: ratio(fg.a < 1 ? blend(fg, g) : fg, g),
        px: parseFloat(cs.fontSize), weight: Number(cs.fontWeight), family: cs.fontFamily.split(',')[0].replace(/"/g, ''),
        title_plate: rgb(cs.backgroundColor) && rgb(cs.backgroundColor).a > 0 });
    } else { row.title = null; }
    const gad = [...head.querySelectorAll('.desk-gadget')].filter((g) => g.getBoundingClientRect().width > 0);
    row.gadgets = gad.map((g) => { const r = g.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; });
    row.gadget_classes_ok = gad.every((g) => g.classList.contains('btn--chrome') && g.tagName === 'BUTTON');
    out.push(row);
  }
  const front = out.filter((r) => r.front);
  const rest = out.filter((r) => !r.front);
  const toRgb = (h) => ({r: parseInt(h.slice(1, 3), 16), g: parseInt(h.slice(3, 5), 16), b: parseInt(h.slice(5, 7), 16), a: 1});
  return { windows: out, front_count: front.length,
           front_vs_inactive_bar: front.length && rest.length ? ratio(toRgb(front[0].bar_ground), toRgb(rest[0].bar_ground)) : null };
}"""

# C1's rendered-overlap fence with its three narrowed waivers; waiver (c) names the built More
# gadget (.desk-dock-more; C1 drew .p13-dock-more), the relationship unchanged.
OVERLAP = C1.OVERLAP.replace(".p13-dock-more", ".desk-dock-more")
assert OVERLAP.count(".desk-dock-more") == 1

CONTENT = r"""() => {
  const f = document.querySelector('.desk-window-shell.is-front'); if (!f) return null;
  const r = f.getBoundingClientRect(); const head = f.querySelector(':scope > .desk-pullout-head'); const hh = head ? head.getBoundingClientRect().height : 0;
  const cs = getComputedStyle(f); const bt = parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth);
  return Math.round(Math.min(r.bottom, innerHeight) - Math.max(r.top, 0) - hh - bt);
}"""

MENU = r"""() => { const m = [...document.querySelectorAll('[role=menu]')].filter((e) => e.getBoundingClientRect().width > 0);
  return m.map((e) => { const r = e.getBoundingClientRect(); return { label: e.getAttribute('aria-label'), l: Math.round(r.left), t: Math.round(r.top), r: Math.round(r.right), b: Math.round(r.bottom),
    inside: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
    rows: [...e.querySelectorAll('[role^=menuitem]')].filter((x) => x.getBoundingClientRect().width > 0).map((x) => x.innerText.replace(/\s+/g, ' ').trim()) }; }); }"""


def run(state: dict | None) -> tuple[list[str], dict]:
    facts: dict = {}
    fails: list[str] = []
    stack = None
    try:
        if state is None:
            stack = rig.Stack("today").__enter__()
            url, hub = stack.url, stack.hub
        else:
            url, hub = state["url"], state["hub"]
        st, _ = rig.hub_api(hub, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
        facts["_onboarding_put"] = st
        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            # a warm-up pass: vite optimizes lazily imported windows once (a late optimize reloads the page)
            warm = browser.new_context(viewport={"width": 1440, "height": 900})
            wp = warm.new_page()
            wp.goto(url, wait_until="load")
            wp.wait_for_timeout(4000)
            for key in ("open-people", "review-meetings"):
                wp.evaluate("(k) => window.__p13Open.surface(k)", key)
                wp.wait_for_timeout(3000)
            warm.close()
            for d, css in DIRECTIONS:
                if ONLY and d != ONLY:
                    continue
                for width, height in ((1440, 900), (393, 852)):
                    try:
                        boards(browser, url, d, css, width, height, facts, fails)
                    except Exception as exc:  # noqa: BLE001
                        traceback.print_exc()
                        fails.append(f"CRASH {d} {width}: {str(exc).splitlines()[0][:300]}")
            browser.close()
    finally:
        if stack is not None:
            stack.__exit__(None, None, None)
    return fails, facts


def boards(browser, url: str, d: str, css: Path | None, width: int, height: int, facts: dict, fails: list[str]) -> None:
    phone = width <= 720
    ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, has_touch=phone)
    page = ctx.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    ev = page.evaluate
    page.goto(url, wait_until="load")
    page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=60_000)
    page.wait_for_timeout(2500)
    if css is not None:
        page.add_style_tag(content=css.read_text())
    ev("() => { window.__tbBooted = true; }")
    page.wait_for_timeout(300)

    def tap(loc):
        box = loc.bounding_box()
        page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    def press(loc):
        tap(loc) if phone else loc.click()

    # the document window in front: People on Priya
    ev("() => window.__p13Open.surface('open-people')")
    people = page.locator(".desk-window-shell[aria-label='People']")
    people.wait_for(timeout=30_000)
    page.wait_for_timeout(1200)
    press(people.get_by_text("Priya Nair", exact=True).first)
    page.wait_for_timeout(1200)
    if not phone:
        # drag People by its title bar so the front bar sits among the inactive ones
        t = people.locator(":scope > .desk-pullout-head .desk-pullout-title").bounding_box()
        sx, sy = t["x"] + 10, t["y"] + t["height"] / 2
        page.mouse.move(sx, sy)
        page.mouse.down()
        for i in range(1, 11):
            page.mouse.move(sx + 356 * i / 10, sy + 78 * i / 10)
            page.wait_for_timeout(16)
        page.mouse.up()
        page.wait_for_timeout(600)
    page.mouse.move(2, height - 2) if not phone else None

    def shoot(board: str, clip: dict | None = None, hover=None):
        key = f"TB-{d}-{board}"
        page.wait_for_timeout(500)
        if not ev("() => window.__tbBooted === true"):
            fails.append(f"{key}: the page reloaded during the run")
        f = {"titles": ev(TITLES), "small_text": ev(SMALL), "own": ev(OWN), "low_contrast": ev(C1.CONTRAST_ALL),
             "clip": ev(C1.CLIP), "menus": ev(MENU)}
        ov = ev(OVERLAP)
        f["overlap"], f["overlap_waived"] = ov["hits"], ov["waived"]
        if phone:
            f["targets_under_44"] = ev(C1.TARGETS44)
            f["content_px"] = ev(CONTENT)
        if hover is not None:
            hover()
            page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / f"{key}.png"), clip=clip)
        f["h_overflow"] = ev("() => document.documentElement.scrollWidth > innerWidth")
        facts[key] = f
        T = f["titles"]
        law = {
            "one window in front": T["front_count"] == 1,
            "every gadget is the library Button (btn--chrome)": all(w["gadget_classes_ok"] for w in T["windows"]),
            "every title >= 4.5:1 in place": all(w.get("contrast") is None or w["contrast"] >= 4.5 for w in T["windows"]),
            "12 px floor (the whole board)": not f["small_text"],
            "ownership: no lost point on a frame control": all(o["lost"] == 0 for o in f["own"]),
            "in-place contrast (the whole board)": not f["low_contrast"],
            "no sideways strip": not f["clip"]["strips"],
            "no clipped text": not f["clip"]["clipped"],
            "no rendered overlap": not f["overlap"],
            "no horizontal page overflow": not f["h_overflow"],
            "every menu inside the viewport": all(m["inside"] for m in f["menus"]),
        }
        if phone:
            law["393: no target under 44 x 44"] = not f["targets_under_44"]
            law["393: the front window's content >= 700 px"] = (f["content_px"] or 0) >= 700
        for name, ok in law.items():
            if not ok:
                fails.append(f"{key}: {name}")
        fw = [w for w in T["windows"] if w["front"]]
        print(key, "front", [(w["name"], w["bar_h"], w.get("contrast")) for w in fw],
              "inactive", sorted({(w["bar_h"], w.get("contrast")) for w in T["windows"] if not w["front"]}),
              "fails", [n for n, ok in law.items() if not ok], flush=True)

    if not phone:
        shoot("1-desk-1440")
        front_head = people.locator(":scope > .desk-pullout-head")
        hb = front_head.bounding_box()
        clip = {"x": 8, "y": 34, "width": int(hb["x"] + hb["width"] + 8 - 8), "height": int(hb["y"] + hb["height"] + 10 - 34)}
        shoot("2-closeup-1440", clip=clip, hover=lambda: page.locator(".desk-window-shell[aria-label='Needs you'] .desk-gadget-iconify").hover())
        page.mouse.move(2, height - 2)
        title = people.locator(":scope > .desk-pullout-head .desk-pullout-title")
        title.click(button="right")
        page.locator(".desk-head-menu, [role=menu]").first.wait_for(timeout=10_000)
        shoot("4-window-menu-1440")
        page.keyboard.press("Escape")
    else:
        shoot("3-phone-393")
        head = page.locator(".desk-window-shell.is-front > .desk-pullout-head")
        tb = head.locator(".desk-pullout-title")
        target = tb if tb.count() and tb.first.is_visible() else head
        b = target.first.bounding_box()
        x, y = b["x"] + min(40, b["width"] / 2), b["y"] + b["height"] / 2
        cdp = ctx.new_cdp_session(page)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
        page.wait_for_timeout(800)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.locator("[role=menu]").first.wait_for(timeout=10_000)
        shoot("5-window-menu-393")
    facts[f"_errors_{d}_{width}"] = errors
    if errors:
        fails.append(f"{d} {width}: browser errors {errors[:3]}")
    ctx.close()


if __name__ == "__main__":
    state = json.loads(Path(os.environ["STACK_STATE"]).read_text()) if os.environ.get("STACK_STATE") else None
    fails, facts = run(state)
    out = SHOTS / "facts.json"
    if ONLY and out.exists():
        merged = json.loads(out.read_text())
        merged.update(facts)
        facts = merged
    out.write_text(json.dumps(facts, indent=1) + "\n")
    verdict = "ALL FENCES HELD; EXIT 0" if not fails else f"{len(fails)} FENCE FAILURE(S); EXIT 2"
    print("\n".join(fails))
    print(verdict)
    sys.exit(0 if not fails else 2)
