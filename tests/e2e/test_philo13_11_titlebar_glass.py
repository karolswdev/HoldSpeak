"""PHILO-13-11 -- TITLE BAR B ("Workbench refined"), fenced AS RENDERED.

The owner picked B on 2026-10-03 ("B"; the boards are
pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/titlebar-canvas/). The
product renders it on its own (no canvas CSS). Through the real hub on an
isolated HOME at 1440x900 (mouse) and 393x852 (touch), on the canvas week
(the Chair as windows; People on Priya Nair in front, as on the boards).

The fences (each records its findings in ``titlebar-facts-<width>.json``):

  T1 one front window; ONLY its bar carries stripes (a background image);
     every inactive bar is flat (no background image).
  T2 every title in place >= 4.5:1 on its own ground, front and inactive,
     measured (the chain of backgrounds, alpha blended).
  T3 every gadget is the library Button (btn--chrome) and owns its centre
     (elementFromPoint), unless a window in front covers that point.
  T4 nothing in a title bar under 12 px; the bar is 26 px at 1440, 44 px at
     393, and every gadget at 393 is 44 x 44.
  T5 the window menu (right button at 1440, long press at 393) opens from
     the title bar and sits inside the viewport.

Shots go to pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/titlebar-build/
under HOLDSPEAK_EVIDENCE_WRITE=1 (``.tmp/evidence-shots/`` otherwise).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_11_chair_glass import _seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the title bar glass needs Playwright")

TOKEN = "philo13-11-titlebar"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/titlebar-build")
SIZES = {1440: 900, 393: 852}

TITLEBAR_JS = r"""(width) => {
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
  const shown = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const shells = [...document.querySelectorAll('.desk-window-shell')].filter(shown);
  const out = {width, windows: [], small_text: [], gadgets_not_owned: [], gadgets_not_library: [], gadgets_small: []};
  for (const s of shells) {
    const head = s.querySelector(':scope > .desk-pullout-head'); if (!head) continue;
    const hcs = getComputedStyle(head); const hr = head.getBoundingClientRect();
    const row = {name: s.getAttribute('aria-label'), front: s.classList.contains('is-front'), bar_h: Math.round(hr.height * 10) / 10,
                 bar_color: hex(rgb(hcs.backgroundColor)), striped: hcs.backgroundImage !== 'none'};
    const title = head.querySelector('.desk-pullout-title');
    if (title && shown(title)) {
      const cs = getComputedStyle(title); const fg = rgb(cs.color); const g = groundOf(title);
      Object.assign(row, {title: title.textContent.trim(), ink: hex(fg), ground: hex(g), contrast: ratio(fg.a < 1 ? blend(fg, g) : fg, g),
                          px: parseFloat(cs.fontSize), title_image: cs.backgroundImage !== 'none'});
    }
    out.windows.push(row);
    const w = document.createTreeWalker(head, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const t = n.textContent.trim(); if (!t || !/[A-Za-z0-9]/.test(t) || !shown(n.parentElement)) continue;
      const px = parseFloat(getComputedStyle(n.parentElement).fontSize);
      if (px < 12 - 0.01) out.small_text.push({text: t.slice(0, 30), px});
    }
    for (const gd of head.querySelectorAll('.desk-gadget')) {
      if (!shown(gd)) continue;
      const r = gd.getBoundingClientRect(); const label = gd.getAttribute('aria-label');
      if (gd.tagName !== 'BUTTON' || !gd.classList.contains('btn--chrome')) out.gadgets_not_library.push(label);
      if (width <= 720 && (r.width < 43.5 || r.height < 43.5)) out.gadgets_small.push({label, w: r.width, h: r.height});
      const x = r.left + r.width / 2, y = r.top + r.height / 2;
      if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) continue;
      const hit = document.elementFromPoint(x, y);
      if (hit && (gd === hit || gd.contains(hit))) continue;
      const over = hit && hit.closest('.desk-window-shell, [role=menu]');
      if (over && over !== s) continue;   // a window or menu in front covers the point
      out.gadgets_not_owned.push({label, hit: hit ? String(hit.className).slice(0, 40) : null});
    }
  }
  const menus = [...document.querySelectorAll('[role=menu]')].filter(shown);
  out.menus = menus.map((m) => { const r = m.getBoundingClientRect(); return {label: m.getAttribute('aria-label'),
    inside: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight}; });
  return out;
}"""


def _fails(m: dict[str, Any], width: int) -> dict[str, Any]:
    fails: dict[str, Any] = {}
    front = [w for w in m["windows"] if w["front"]]
    rest = [w for w in m["windows"] if not w["front"]]
    if len(front) != 1 or not front[0]["striped"]:
        fails["T1 one front window and its bar is striped"] = front
    if any(w["striped"] for w in rest):
        fails["T1 inactive bars are flat"] = [w["name"] for w in rest if w["striped"]]
    low = [w for w in m["windows"] if w.get("contrast") is not None and w["contrast"] < 4.5]
    if low:
        fails["T2 every title >= 4.5:1"] = low
    if m["gadgets_not_library"] or m["gadgets_not_owned"]:
        fails["T3 gadgets are library Buttons and own their centres"] = {
            "not_library": m["gadgets_not_library"], "not_owned": m["gadgets_not_owned"]}
    want_h = 44 if width <= 720 else 26
    bad_h = [w for w in m["windows"] if abs(w["bar_h"] - want_h) > 0.5]
    if m["small_text"] or bad_h or m["gadgets_small"]:
        fails["T4 12 px floor, bar height, 44 px gadgets at 393"] = {
            "small": m["small_text"], "bar_h": bad_h, "gadgets": m["gadgets_small"]}
    if any(not x["inside"] for x in m["menus"]):
        fails["T5 the window menu sits inside the viewport"] = m["menus"]
    return fails


class TestTitleBarB:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.home = tmp_path / "home"
        _seed(self.home)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_title_bar_b(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        phone = width <= 720
        facts: dict[str, Any] = {}
        failures: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=2, has_touch=phone, is_mobile=False)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                page.evaluate(
                    """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                        headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                        body: JSON.stringify({disposition: 'completed'})})""",
                    TOKEN,
                )
                _api(page, "POST", "/api/channels/destinations",
                     {"name": "Team updates", "channel": "file",
                      "folder": str(self.home / "Documents" / "HoldSpeak" / "Team updates")}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator(".desk-window-shell[aria-label='Needs you']").wait_for()
                page.wait_for_timeout(1200)

                def press(loc: Any) -> None:
                    if phone:
                        box = loc.bounding_box()
                        page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    else:
                        loc.click()

                def measure(board: str) -> dict[str, Any]:
                    page.wait_for_timeout(400)
                    _settle(page)
                    m = page.evaluate(TITLEBAR_JS, width)
                    facts[board] = m
                    failures[board] = _fails(m, width)
                    return m

                # People on Priya in front (the boards' document window)
                press(page.locator(".desk-dock [aria-label^='People']").first)
                people = page.locator(".desk-window-shell[aria-label='People']")
                people.wait_for()
                page.wait_for_timeout(800)
                press(people.get_by_text("Priya Nair", exact=True).first)
                page.wait_for_timeout(800)
                if not phone:
                    t = people.locator(":scope > .desk-pullout-head .desk-pullout-title").bounding_box()
                    sx, sy = t["x"] + 10, t["y"] + t["height"] / 2
                    page.mouse.move(sx, sy)
                    page.mouse.down()
                    for i in range(1, 11):
                        page.mouse.move(sx + 356 * i / 10, sy + 78 * i / 10)
                        page.wait_for_timeout(16)
                    page.mouse.up()
                    page.mouse.move(2, SIZES[width] - 2)
                    measure("desk")
                    page.screenshot(path=str(SHOTS / "build-TB-1-desk-1440.png"))
                    hb = people.locator(":scope > .desk-pullout-head").bounding_box()
                    page.screenshot(path=str(SHOTS / "build-TB-2-closeup-1440.png"),
                                    clip={"x": 8, "y": 34, "width": hb["x"] + hb["width"], "height": hb["y"] + hb["height"] + 10 - 34})
                    people.locator(":scope > .desk-pullout-head .desk-pullout-title").click(button="right")
                    page.locator("[role=menu]").first.wait_for()
                    m = measure("window-menu")
                    if not m["menus"]:
                        failures["window-menu"]["T5 the window menu opens from the title bar"] = True
                    page.screenshot(path=str(SHOTS / "build-TB-4-window-menu-1440.png"))
                    page.keyboard.press("Escape")
                else:
                    measure("phone")
                    page.screenshot(path=str(SHOTS / "build-TB-3-phone-393.png"))
                    head = page.locator(".desk-window-shell.is-front > .desk-pullout-head")
                    tb = head.locator(".desk-pullout-title")
                    b = (tb if tb.count() and tb.first.is_visible() else head).first.bounding_box()
                    x, y = b["x"] + min(40, b["width"] / 2), b["y"] + b["height"] / 2
                    cdp = ctx.new_cdp_session(page)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
                    page.wait_for_timeout(800)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                    page.locator("[role=menu]").first.wait_for()
                    m = measure("window-menu")
                    if not m["menus"]:
                        failures["window-menu"]["T5 the window menu opens from the title bar"] = True
                    page.screenshot(path=str(SHOTS / "build-TB-5-window-menu-393.png"))
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                failures = {k: v for k, v in failures.items() if v}
                facts["failures"] = failures
                (SHOTS / f"titlebar-facts-{width}.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not failures, json.dumps(failures, indent=2)
            finally:
                browser.close()
