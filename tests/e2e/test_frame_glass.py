"""The window frame in a real browser: its gadgets, its title bar and its
measures, at 1440 (mouse) and 393 (touch).

Kept by the test diet (push 2, 2026-10-12), one file for the window frame
(DeskWindowFrame and its gadgets). Every check here needs a real browser:
drag, hover, keys, touch, elementFromPoint ownership, and exact geometry
(a zoom that returns the exact rect, a window lifted above the Dock).

Was tests/e2e/test_philo13_11_frame_glass.py (the frame fences F1-F5),
test_philo13_11_titlebar_glass.py (title bar B) and
test_philo13_12_gadgets_glass.py (the gadgets), parked whole. The shared
seeds and measures are tests/e2e/frame_rig.py and chair_rig.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .chair_rig import _seed as _chair_seed
from .chair_windows import open_chair_window
from .frame_rig import FRAME_JS, ROOM, _seed, _stage
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="this glass needs Playwright")



# ══ was tests/e2e/test_philo13_11_frame_glass.py ══════════════════

FRAME_TOKEN = "philo13-11-frame"

FRAME_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-build")

FRAME_SIZES = {1440: 900, 393: 852}
# The floating dock (#1497): 10 px of air between the work band and the plate.
DOCK_AIR = 10

class TestTheFrame:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=FRAME_TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": FRAME_SIZES[width]},
                                  device_scale_factor=2, has_touch=width < 720, is_mobile=False)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={FRAME_TOKEN}", wait_until="load")
        page.evaluate(
            """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                body: JSON.stringify({disposition: 'completed'})})""",
            FRAME_TOKEN,
        )
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _measure(page: Any, width: int, board: str, facts: dict[str, Any]) -> dict[str, Any]:
        page.wait_for_timeout(400)
        _settle(page)
        m = page.evaluate(FRAME_JS, width)
        facts[board] = m
        return m

    @staticmethod
    def _fails(m: dict[str, Any], width: int, expect_window: bool) -> dict[str, Any]:
        fails: dict[str, Any] = {}
        if expect_window:
            if len(m["blue"]) != 1 or m["front"] != m["blue"] or m["screen"] != m["blue"][0]:
                fails["F1 one blue front window"] = {"blue": m["blue"], "front": m["front"], "screen": m["screen"]}
        if m["layout"] or m["ownership"]:
            fails["F2 gadget layout and ownership"] = {"layout": m["layout"], "ownership": m["ownership"]}
        if m["clipped"] or m["sideways"]:
            fails["F3 nothing clips, nothing scrolls sideways"] = {"clipped": m["clipped"], "sideways": m["sideways"]}
        if width <= 720:
            # The floating dock (#1494/#1497) reserves 80 px on the phone (the
            # 64 px plate, its 8 px inset, 8 px of air): 852 - 44 bar - 80 -
            # 44 title bar - 2 border = 682 px of content; the floor is 680.
            if (expect_window and (m["content"] is None or m["content"] < 680)) or m["small_targets"]:
                fails["F4 393 content and targets"] = {"content": m["content"], "small": m["small_targets"]}
        if m["small_text"] or m["low_contrast"]:
            fails["F5 frame text in place"] = {"small": m["small_text"], "low": m["low_contrast"]}
        return fails

    @pytest.mark.parametrize("width", list(FRAME_SIZES))
    def test_the_frame(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        failures: dict[str, Any] = {}
        tag = f"{width}"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                if width > 720:
                    # The Desk with two windows (C1-1 / C1-2a): the Room, then Meetings.
                    _stage(page, "open-project-memory", "project:p-ledger")
                    self._press(page, page.locator(".desk-dock [aria-label^='Meetings']").first, width)
                    page.locator(".desk-window-shell[aria-label='Meetings']").wait_for()
                    m = self._measure(page, width, "two-windows-meetings-front", facts)
                    failures["two-windows-meetings-front"] = self._fails(m, width, True)
                    # the Room comes to the front by a press on its title bar
                    room = page.locator(f".desk-window-shell[aria-label='{ROOM}']")
                    room.locator(".desk-pullout-title").click()
                    m = self._measure(page, width, "two-windows-room-front", facts)
                    failures["two-windows-room-front"] = self._fails(m, width, True)
                    page.screenshot(path=str(FRAME_SHOTS / f"build-C1-1-the-desk-{tag}.png"))
                    room.screenshot(path=str(FRAME_SHOTS / f"build-C1-2a-window-gadgets-{tag}.png"))
                    # an open menu on the screen bar (paper, ink, the blue row)
                    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                    page.locator(".desk-verbbar-menu").wait_for()
                    m = self._measure(page, width, "window-menu-open", facts)
                    failures["window-menu-open"] = self._fails(m, width, True)
                    page.screenshot(path=str(FRAME_SHOTS / f"build-C1-2b-window-menu-{tag}.png"))
                    page.keyboard.press("Escape")
                else:
                    # The Chair at 393 (C1-1): the screen bar with no window.
                    m = self._measure(page, width, "chair", facts)
                    failures["chair"] = self._fails(m, width, False)
                    page.screenshot(path=str(FRAME_SHOTS / f"build-C1-1-the-desk-{tag}.png"))
                    # A window with wings that do not fit: the strip menu (C1-2e).
                    # PHILO-17: the Meetings window is the list (two wings that
                    # fit); Speak keeps four wings and a door, which fold.
                    _stage(page, "dictate")
                    meeting_window = page.locator(".desk-window-shell[aria-label='Speak']")
                    meeting_window.wait_for()
                    m = self._measure(page, width, "meetings", facts)
                    failures["meetings"] = self._fails(m, width, True)
                    page.screenshot(path=str(FRAME_SHOTS / f"build-C1-2a-window-gadgets-{tag}.png"))
                    strip = meeting_window.locator(".surface-strip-menu")
                    if strip.count() != 1:
                        # §3a: four wings and a gear door do not fit one 393 row
                        failures["meetings"]["F3 the wings fold into the strip menu"] = {"strip_menus": strip.count()}
                    else:
                        self._press(page, strip, width)
                        wing_menu = page.get_by_role("menu", name="Window faces", exact=True)
                        wing_menu.wait_for()
                        m = self._measure(page, width, "strip-menu-open", facts)
                        failures["strip-menu-open"] = self._fails(m, width, True)
                        checked = wing_menu.locator("[aria-checked='true']").all_inner_texts()
                        facts["strip-menu-checked"] = checked
                        mark = page.evaluate("""() => { const g = document.querySelector(
                            '[role=menu][aria-label="Window faces"] [aria-checked="true"] .desk-menu-glyph svg, [role=menu][aria-label="Window faces"] [aria-checked="true"] .desk-menu-glyph');
                          if (!g) return 0; const r = g.getBoundingClientRect(); return r.width * r.height; }""")
                        facts["strip-menu-check-mark-area"] = mark
                        if len(checked) != 1 or not mark:
                            failures["strip-menu-open"]["F3 the current choice is checked, and the check shows"] = {
                                "checked": checked, "mark_area": mark}
                        page.screenshot(path=str(FRAME_SHOTS / f"build-C1-2e-strip-menu-open-{tag}.png"))
                        page.keyboard.press("Escape")
                    # A window that fills the work area (C1-6b): People.
                    _stage(page, "open-people")
                    page.locator(".desk-window-shell[aria-label='People']").wait_for()
                    m = self._measure(page, width, "people", facts)
                    failures["people"] = self._fails(m, width, True)
                    page.screenshot(path=str(FRAME_SHOTS / f"build-C1-6b-phone-window-{tag}.png"))
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                failures = {k: v for k, v in failures.items() if v}
                facts["failures"] = failures
                (FRAME_SHOTS / f"frame-facts-{tag}.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not failures, json.dumps(failures, indent=2)
            finally:
                browser.close()


# ══ was tests/e2e/test_philo13_11_titlebar_glass.py ═══════════════

TITLEBAR_TOKEN = "philo13-11-titlebar"

TITLEBAR_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/titlebar-build")

TITLEBAR_SIZES = {1440: 900, 393: 852}

TITLEBAR_TITLEBAR_JS = r"""(width) => {
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
  const shells = [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(shown);
  const paint = document.createElement('span'); paint.style.backgroundColor='var(--wb-bar-front)';
  document.body.appendChild(paint); const activeColor=hex(rgb(getComputedStyle(paint).backgroundColor)); paint.remove();
  const out = {width, activeColor, windows: [], small_text: [], gadgets_not_owned: [], gadgets_not_library: [], gadgets_small: []};
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

def _titlebar_fails(m: dict[str, Any], width: int) -> dict[str, Any]:
    fails: dict[str, Any] = {}
    front = [w for w in m["windows"] if w["front"]]
    rest = [w for w in m["windows"] if not w["front"]]
    if len(front) != 1 or front[0]["bar_color"] != m["activeColor"] or front[0]["striped"]:
        fails["T1 one front window with the shared flat active head"] = front
    if any(w["striped"] for w in rest):
        fails["T1 inactive bars are flat"] = [w["name"] for w in rest if w["striped"]]
    low = [w for w in m["windows"] if w.get("contrast") is not None and w["contrast"] < 4.5]
    if low:
        fails["T2 every title >= 4.5:1"] = low
    if m["gadgets_not_library"] or m["gadgets_not_owned"]:
        fails["T3 gadgets are library Buttons and own their centres"] = {
            "not_library": m["gadgets_not_library"], "not_owned": m["gadgets_not_owned"]}
    want_h = 44 if width <= 720 else 30  # window grammar 2026-10-24: a 28-32 px desktop bar
    bad_h = [w for w in m["windows"] if abs(w["bar_h"] - want_h) > 0.5]
    if m["small_text"] or bad_h or m["gadgets_small"]:
        fails["T4 12 px floor, bar height, 44 px gadgets at 393"] = {
            "small": m["small_text"], "bar_h": bad_h, "gadgets": m["gadgets_small"]}
    if any(not x["inside"] for x in m["menus"]):
        fails["T5 the window menu sits inside the viewport"] = m["menus"]
    return fails

@pytest.mark.chair_windows_open
class TestTitleBarB:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TITLEBAR_TOKEN)
        self.home = tmp_path / "home"
        _chair_seed(self.home)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(TITLEBAR_SIZES))
    def test_title_bar_b(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        phone = width <= 720
        facts: dict[str, Any] = {}
        failures: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": TITLEBAR_SIZES[width]},
                                      device_scale_factor=2, has_touch=phone, is_mobile=False)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TITLEBAR_TOKEN}", wait_until="load")
                page.evaluate(
                    """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                        headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                        body: JSON.stringify({disposition: 'completed'})})""",
                    TITLEBAR_TOKEN,
                )
                _api(page, "POST", "/api/channels/destinations",
                     {"name": "Team updates", "channel": "file",
                      "folder": str(self.home / "Documents" / "HoldSpeak" / "Team updates")}, token=TITLEBAR_TOKEN)
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
                    m = page.evaluate(TITLEBAR_TITLEBAR_JS, width)
                    facts[board] = m
                    failures[board] = _titlebar_fails(m, width)
                    return m

                # People on Priya in front (the boards' document window).
                # PHILO-17 (doors): People opens from Go (and its desk drawer).
                press(page.locator(".desk-verbbar-item[data-menu-id='go'] button"))
                press(page.locator("[role^=menuitem]").filter(has=page.locator(".desk-menu-label", has_text=re.compile(r"^People$"))).last)
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
                    page.mouse.move(2, TITLEBAR_SIZES[width] - 2)
                    measure("desk")
                    page.screenshot(path=str(TITLEBAR_SHOTS / "build-TB-1-desk-1440.png"))
                    hb = people.locator(":scope > .desk-pullout-head").bounding_box()
                    page.screenshot(path=str(TITLEBAR_SHOTS / "build-TB-2-closeup-1440.png"),
                                    clip={"x": 8, "y": 34, "width": hb["x"] + hb["width"], "height": hb["y"] + hb["height"] + 10 - 34})
                    people.locator(":scope > .desk-pullout-head .desk-pullout-title").click(button="right")
                    page.locator(".desk-head-menu[role=menu]").wait_for()
                    m = measure("window-menu")
                    if not m["menus"]:
                        failures["window-menu"]["T5 the window menu opens from the title bar"] = True
                    page.screenshot(path=str(TITLEBAR_SHOTS / "build-TB-4-window-menu-1440.png"))
                    page.keyboard.press("Escape")
                    # T6 (Astra on #759): a held front gadget draws the pressed
                    # fill, not the hover fill. Press, read, release off it.
                    zoom = people.locator(":scope > .desk-pullout-head .desk-gadget[aria-label^='Zoom']").first
                    zb = zoom.bounding_box()
                    page.mouse.move(zb["x"] + zb["width"] / 2, zb["y"] + zb["height"] / 2)
                    page.mouse.down()
                    held = zoom.evaluate("""el => {
                      const probe = document.createElement('i');
                      probe.style.background = 'var(--wb-press)';
                      el.parentElement.appendChild(probe);
                      const want = getComputedStyle(probe).backgroundColor; probe.remove();
                      return {got: getComputedStyle(el).backgroundColor, want};
                    }""")
                    page.mouse.move(2, TITLEBAR_SIZES[width] - 2)
                    page.mouse.up()
                    facts["held_zoom"] = held
                    if held["got"] != held["want"]:
                        failures["window-menu"]["T6 a held front gadget draws --wb-press"] = held
                else:
                    measure("phone")
                    page.screenshot(path=str(TITLEBAR_SHOTS / "build-TB-3-phone-393.png"))
                    head = page.locator(".desk-window-shell.is-front > .desk-pullout-head")
                    tb = head.locator(".desk-pullout-title")
                    b = (tb if tb.count() and tb.first.is_visible() else head).first.bounding_box()
                    x, y = b["x"] + min(40, b["width"] / 2), b["y"] + b["height"] / 2
                    cdp = ctx.new_cdp_session(page)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
                    page.wait_for_timeout(800)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                    page.locator(".desk-head-menu[role=menu]").wait_for()
                    m = measure("window-menu")
                    if not m["menus"]:
                        failures["window-menu"]["T5 the window menu opens from the title bar"] = True
                    page.screenshot(path=str(TITLEBAR_SHOTS / "build-TB-5-window-menu-393.png"))
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                failures = {k: v for k, v in failures.items() if v}
                facts["failures"] = failures
                (TITLEBAR_SHOTS / f"titlebar-facts-{width}.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not failures, json.dumps(failures, indent=2)
            finally:
                browser.close()


# ══ was tests/e2e/test_philo13_12_gadgets_glass.py ════════════════

GADGETS_TOKEN = "philo13-12-gadgets"

GADGETS_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-12-build")

GADGETS_SIZES = {1440: 900, 393: 852}

# The stacking facts as rendered: every visible window, its z, its blue head,
# and the screen title.
STACK_JS = r"""() => {
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  const paint=document.createElement('span'); paint.style.backgroundColor='var(--wb-bar-front)';
  document.body.appendChild(paint); const active=getComputedStyle(paint).backgroundColor; paint.remove();
  const blue = (h) => getComputedStyle(h).backgroundColor === active;
  const wins = [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible).map((s) => {
    const h = s.querySelector(':scope > .desk-pullout-head'); const r = s.getBoundingClientRect();
    return {name: s.getAttribute('aria-label'), z: Number(getComputedStyle(s).zIndex) || 0,
      front: s.classList.contains('is-front'), blue: Boolean(h && blue(h)),
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]}; });
  const st = document.querySelector('[data-testid="desk-screen-title"]');
  return {wins, screen: st ? st.textContent.trim() : null};
}"""

MENU_JS = r"""() => {
  const menus = [...document.querySelectorAll('.desk-head-menu')];
  return menus.map((m) => ({label: m.getAttribute('aria-label'),
    rows: [...m.querySelectorAll('[role^="menuitem"]')].map((r) => {
      const b = r.getBoundingClientRect();
      return {label: (r.querySelector('.desk-menu-label') || r).textContent.trim(),
        keycap: (r.querySelector('.desk-menu-keycaps') || {getAttribute: () => null}).getAttribute('aria-label'),
        ghost: r.classList.contains('is-ghost') || r.getAttribute('aria-disabled') === 'true',
        w: Math.round(b.width), h: Math.round(b.height)}; })}));
}"""

DOC_JS = r"""() => JSON.parse(localStorage.getItem('hs.desk.workspace.v1') || 'null')"""

def _one_blue(stack: dict[str, Any], name: str) -> list[str]:
    """The faults when `name` is not the one blue front window the screen names."""
    faults = []
    blue = [w["name"] for w in stack["wins"] if w["blue"]]
    front = [w["name"] for w in stack["wins"] if w["front"]]
    if blue != [name]:
        faults.append(f"blue={blue}, want [{name}]")
    if front != [name]:
        faults.append(f"front={front}, want [{name}]")
    if stack["screen"] != name:
        faults.append(f"screen title={stack['screen']!r}, want {name!r}")
    return faults

def _behind(stack: dict[str, Any], sent: str) -> list[str]:
    """The faults when `sent` is not behind every other window, or the front
    is not ONE blue window (another one) that the screen title names."""
    faults = []
    others = [w for w in stack["wins"] if w["name"] != sent]
    if others and _z(stack, sent) >= min(w["z"] for w in others):
        faults.append(f"{sent} is not behind every other window")
    front = [w["name"] for w in stack["wins"] if w["front"]]
    if len(front) != 1 or front[0] == sent:
        faults.append(f"front={front}")
    else:
        faults += _one_blue(stack, front[0])
    return faults

def _z(stack: dict[str, Any], name: str) -> int:
    return next(w["z"] for w in stack["wins"] if w["name"] == name)

def _rect(stack: dict[str, Any], name: str) -> list[int]:
    return next(w["rect"] for w in stack["wins"] if w["name"] == name)

class TestTheGadgets:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=GADGETS_TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": GADGETS_SIZES[width]},
                                  device_scale_factor=2, has_touch=width < 720, is_mobile=False)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={GADGETS_TOKEN}", wait_until="load")
        page.evaluate(
            """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                body: JSON.stringify({disposition: 'completed'})})""",
            GADGETS_TOKEN,
        )
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _tap(page: Any, loc: Any) -> None:
        box = loc.bounding_box()
        assert box, "nothing to tap"
        page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    @staticmethod
    def _long_press(page: Any, x: float, y: float) -> None:
        cdp = page.context.new_cdp_session(page)
        point = [{"x": x, "y": y, "radiusX": 4, "radiusY": 4, "force": 1, "id": 1}]
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": point})
        page.wait_for_timeout(800)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        cdp.detach()

    @staticmethod
    def _stack(page: Any) -> dict[str, Any]:
        page.wait_for_timeout(300)
        _settle(page)
        return page.evaluate(STACK_JS)

    def _check_menu(self, page: Any, name: str, width: int, facts: dict[str, Any], fails: dict[str, Any]) -> None:
        menus = page.evaluate(MENU_JS)
        facts[f"menu-{name}"] = menus
        menu = next((m for m in menus if m["label"] == f"{name} window menu"), None)
        if not menu:
            fails["G3 the window menu opens"] = menus
            return
        got = [(r["label"].split(" · ")[0], r["keycap"]) for r in menu["rows"]]
        # PHILO-16 §5: Zoom ⌘⇧Z, To back ⌘⇧`. PHILO-17 windows (#1070, U27):
        # the menus show ⌃M and ⌃W (a browser tab keeps the ⌘ keys).
        want = [("Minimize", "⌃M"), ("Zoom", "⌘⇧Z"), ("To back", "⌘⇧`"), ("Close", "⌃W"),
                ("Desk", None), ("Go", None)]
        if width < 720:
            # PHILO-15 11 (B21): a phone has no ⌘ key, so no row at 393 draws
            # a keycap (DeskMenu.tsx `entry.keycap && !NARROW()`).
            # Betterment shell S0 (#1257, UX-CANON A.11 "withhold, never
            # ghost"): a window fills the phone screen, so Zoom cannot run
            # there and is not drawn.
            want = [(label, None) for label, _ in want if label != "Zoom"]
        if got != want:
            fails["G3 the menu bar with its key caps"] = got
        if any(r.get("ghost") for r in menu["rows"]):
            fails["G3 no ghosted row (withheld, never ghosted)"] = [r for r in menu["rows"] if r.get("ghost")]
        if width < 720:
            small = [r for r in menu["rows"] if r["h"] < 44]
            if small:
                fails["G3 393: every menu row owns 44 px"] = small

    def test_gadgets_1440(self) -> None:
        from playwright.sync_api import sync_playwright

        width = 1440
        facts: dict[str, Any] = {}
        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # G1 on the Chair: Needs you to back, another Chair window is front.
                # PHILO-14 A1 (#939): the Chair's windows start closed; he opens
                # the Brief, then Needs you, from Window > Chair.
                open_chair_window(page, "Brief")
                open_chair_window(page, "Needs you")
                needs = page.get_by_role("button", name="To back Needs you")
                needs.click()
                st = self._stack(page)
                facts["chair-after-depth"] = st
                if _behind(st, "Needs you"):
                    fails["G1 Chair: depth"] = _behind(st, "Needs you")

                # Two desk windows: the Room, then Meetings in front.
                _stage(page, "open-project-memory", "project:p-ledger")
                page.locator(".desk-dock [aria-label^='Meetings']").first.click()
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                st = self._stack(page)
                if _one_blue(st, "Meetings"):
                    fails["G1 setup: Meetings front"] = st
                page.screenshot(path=str(GADGETS_SHOTS / "build-C1-2c-before-depth-1440.png"))

                # G1 the depth gadget.
                meetings.get_by_role("button", name="To back Meetings").click()
                st = self._stack(page)
                facts["after-depth-gadget"] = st
                faults = _one_blue(st, ROOM) + _behind(st, "Meetings")
                if faults:
                    fails["G1 depth gadget"] = faults
                page.screenshot(path=str(GADGETS_SHOTS / "build-C1-2c-depth-to-back-1440.png"))

                # G4 ⌃B: the front window (the Room) goes to the back.
                page.keyboard.press("Control+b")
                st = self._stack(page)
                facts["after-ctrl-b"] = st
                # Behind every window (the Chair's windows are windows too).
                faults = _behind(st, ROOM)
                if faults:
                    fails["G4 ⌃B runs To back"] = faults

                # G2 zoom: the two remembered rects. Meetings comes forward
                # from its Dock AppIcon.
                page.locator(".desk-dock [aria-label^='Meetings']").first.click()
                page.wait_for_timeout(300)
                # The owner arranges Meetings first (a drag of its title bar):
                # the normal rect is his, and the workspace keeps it.
                title = meetings.locator(".desk-pullout-title").bounding_box()
                assert title
                tx, ty = title["x"] + title["width"] / 2, title["y"] + title["height"] / 2
                page.mouse.move(tx, ty)
                page.mouse.down()
                page.mouse.move(tx + 40, ty + 30, steps=8)
                page.mouse.up()
                prior = _rect(self._stack(page), "Meetings")
                zoom = meetings.get_by_role("button", name="Zoom Meetings")
                zoom.click()
                st = self._stack(page)
                zoomed = _rect(st, "Meetings")
                if zoom.get_attribute("aria-pressed") != "true" or zoomed == prior:
                    fails["G2 zoom fills the work band"] = {"prior": prior, "zoomed": zoomed}
                # PHILO-13-11 close (board C1-2d): the zoomed window fills the
                # screen between the screen bar and the shelf -- its head flush
                # under the bar (no window behind peeks above it) and its foot
                # and sizing gadget clear of the Dock (the 76 px shelf of C3-W).
                band = page.evaluate("""() => {
                    const bar = document.querySelector('.desk-menubar').getBoundingClientRect();
                    const dock = document.querySelector('.desk-dock').getBoundingClientRect();
                    const win = document.querySelector(".desk-window-shell[aria-label='Meetings']").getBoundingClientRect();
                    const grip = document.querySelector(".desk-window-shell[aria-label='Meetings'] .desk-window-grip");
                    const g = grip.getBoundingClientRect();
                    const hit = document.elementFromPoint(g.left + g.width / 2, g.top + g.height / 2);
                    return {bar_bottom: Math.round(bar.bottom), dock_top: Math.round(dock.top),
                            top: Math.round(win.top), bottom: Math.round(win.bottom), grip_owned: grip.contains(hit)};
                }""")
                facts["zoom-band"] = band
                if abs(band["top"] - band["bar_bottom"]) > 2 or band["bottom"] > band["dock_top"] + 1 or not band["grip_owned"]:
                    fails["G2 zoom fills the screen between the bar and the shelf"] = band
                page.screenshot(path=str(GADGETS_SHOTS / "build-C1-2d-zoom-1440.png"))
                # The user sizes the zoomed window: the sizing gadget, dragged.
                grip = meetings.locator(".desk-window-grip").bounding_box()
                assert grip, "the zoomed window has no sizing gadget"
                gx, gy = grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2
                page.mouse.move(gx, gy)
                page.mouse.down()
                page.mouse.move(gx - 240, gy - 160, steps=12)
                page.mouse.up()
                sized = _rect(self._stack(page), "Meetings")
                if sized == zoomed:
                    fails["G2 the zoomed state resizes"] = {"zoomed": zoomed, "sized": sized}
                zoom.click()
                back = _rect(self._stack(page), "Meetings")
                if back != prior:
                    fails["G2 zoom back restores the exact prior rect"] = {"prior": prior, "back": back}
                zoom.click()
                again = _rect(self._stack(page), "Meetings")
                if again != sized:
                    fails["G2 zoom again restores the remembered zoomed rect"] = {"sized": sized, "again": again}
                doc = page.evaluate(DOC_JS) or {}
                panel = doc.get("panel", {})
                mid = next((k for k in (panel.get("zoom") or {}) if "meeting" in k.lower()), None)
                facts["workspace-panel"] = panel
                if not mid or mid not in panel.get("rects", {}) or mid not in panel.get("max", []):
                    fails["G2 both rects in the workspace document"] = panel
                # Each survives a reload: Meetings comes back zoomed at the
                # remembered zoomed rect, and zooms back to the prior rect.
                page.reload(wait_until="load")
                _normal_chair(page)
                meetings.wait_for()
                page.wait_for_timeout(800)
                reloaded = _rect(self._stack(page), "Meetings")
                if reloaded != sized or zoom.get_attribute("aria-pressed") != "true":
                    fails["G2 the zoomed rect survives a reload"] = {"sized": sized, "reloaded": reloaded}
                # G4 ⌘⇧Z: zoom back by key (PHILO-17 #1070: ⌃M is Iconify now).
                page.keyboard.press("Meta+Shift+z")
                page.wait_for_timeout(300)
                if zoom.get_attribute("aria-pressed") != "false" or _rect(self._stack(page), "Meetings") != prior:
                    fails["G4 ⌘⇧Z runs Zoom"] = _rect(self._stack(page), "Meetings")

                # G3 the right button in the BODY of Meetings (the front window).
                box = meetings.bounding_box()
                assert box
                page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.55, button="right")
                page.locator(".desk-head-menu").first.wait_for()
                self._check_menu(page, "Meetings", width, facts, fails)
                page.locator(".desk-head-menu [role^='menuitem']", has_text="Desk").first.hover()
                page.wait_for_timeout(400)
                page.screenshot(path=str(GADGETS_SHOTS / "build-C1-2b-window-menu-amiga-keys-1440.png"))
                # The submenu sits beside its panel, never over it.
                over = page.evaluate("""() => { const [p, sb] = [...document.querySelectorAll('.desk-menu-list')].map((m) => m.getBoundingClientRect());
                  return sb ? (sb.left < p.right - 1 && sb.right > p.left + 1) : null; }""")
                if over is not False:
                    fails["G3 Desk ▸ opens beside the menu, not over it"] = over
                sub = page.locator(".desk-work-submenu [role^='menuitem']").all_inner_texts()
                facts["desk-submenu"] = sub
                if not any("New Note" in s for s in sub):
                    fails["G3 Desk ▸ carries the registry verbs"] = sub
                page.keyboard.press("Escape")
                page.keyboard.press("Escape")

                # G4 the other shortcuts, each by its verb's effect.
                page.keyboard.press("Meta+k")
                # PHILO-17 (palette-rank, #1097): the deck opens at once and its
                # list draws when its ranking reads resolve (at most 600 ms).
                try:
                    page.locator("#desk-palette-listbox").wait_for(state="visible", timeout=3_000)
                    ok_k = True
                except Exception:  # noqa: BLE001 - recorded as the G4 fault below
                    ok_k = False
                page.keyboard.press("Escape")
                page.keyboard.press("Meta+/")
                page.wait_for_timeout(300)
                ok_sheet = page.locator(".desk-shortcut-sheet").is_visible()
                page.keyboard.press("Escape")
                page.keyboard.press("Control+ArrowUp")
                page.wait_for_timeout(400)
                ok_expose = page.locator(".desk-expose").count() > 0
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                facts["keys"] = {"⌘K": ok_k, "⌘/": ok_sheet, "⌃↑": ok_expose}
                for k, ok in facts["keys"].items():
                    if not ok:
                        fails[f"G4 {k} runs its verb"] = False
                # ⌘M iconifies the front window; its Dock chip brings it back.
                front = next(w["name"] for w in self._stack(page)["wins"] if w["front"])
                page.keyboard.press("Meta+m")
                page.wait_for_timeout(600)
                if any(w["name"] == front for w in self._stack(page)["wins"]):
                    fails["G4 ⌘M runs Iconify"] = front
                # ⌘W closes the front window.
                st = self._stack(page)
                front = next((w["name"] for w in st["wins"] if w["front"]), None)
                page.keyboard.press("Meta+w")
                page.wait_for_timeout(600)
                if front and any(w["name"] == front for w in self._stack(page)["wins"]):
                    fails["G4 ⌘W runs Close window"] = front
                # ⌘N makes a note (the one create path).
                before = len(self._notes(page))
                page.keyboard.press("Meta+n")
                page.wait_for_timeout(1200)
                if len(self._notes(page)) != before + 1:
                    fails["G4 ⌘N runs New Note"] = {"before": before, "after": len(self._notes(page))}

                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                facts["failures"] = fails
                (GADGETS_SHOTS / "gadget-facts-1440.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not fails, json.dumps(fails, indent=2, ensure_ascii=False)
            finally:
                browser.close()

    def test_zoom_survives_reload_unarranged_1440(self) -> None:
        """Astra on PR #731: open, Zoom, reload, Zoom -> the exact original
        rect, with NO drag first (a window the owner never arranged)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                _stage(page, "review-meetings")
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                page.wait_for_timeout(600)
                original = _rect(self._stack(page), "Meetings")
                zoom = meetings.get_by_role("button", name="Zoom Meetings")
                zoom.click()
                zoomed = _rect(self._stack(page), "Meetings")
                cached_zoom = page.evaluate(DOC_JS)["panel"]
                page.reload(wait_until="load")
                _normal_chair(page)
                meetings.wait_for()
                page.wait_for_timeout(800)
                after_reload = _rect(self._stack(page), "Meetings")
                cached_reload = page.evaluate(DOC_JS)["panel"]
                zoom.click()
                back = _rect(self._stack(page), "Meetings")
                cached_back = page.evaluate(DOC_JS)["panel"]
                facts = {"original": original, "zoomed": zoomed, "after_reload": after_reload, "back": back,
                         "auto_rect_at_zoom": cached_zoom.get("autoRects", {}).get("surface-meetings"),
                         "auto_rect_after_reload": cached_reload.get("autoRects", {}).get("surface-meetings"),
                         "errors": [e for e in errors if "ResizeObserver" not in e]}
                (GADGETS_SHOTS / "gadget-facts-zoom-reload-1440.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert zoomed != original, facts
                assert after_reload == zoomed, facts
                assert back == original, facts
                for cached in (cached_zoom, cached_reload):
                    assert "surface-meetings" not in cached["rects"], facts
                    auto = cached.get("autoRects", {}).get("surface-meetings")
                    assert auto and all(abs(auto[key] - value) <= 1 for key, value in
                                        zip(("x", "y", "w", "h"), original)), facts
                assert "surface-meetings" not in cached_back["rects"], facts
                assert "surface-meetings" not in cached_back.get("autoRects", {}), facts
                assert not facts["errors"], facts["errors"]
            finally:
                browser.close()

    def _notes(self, page: Any) -> list[Any]:
        return page.evaluate(
            """async (token) => { const r = await fetch('/api/notes', {headers: {authorization: `Bearer ${token}`}});
               const j = await r.json(); return Array.isArray(j) ? j : (j.items || j.notes || []); }""",
            GADGETS_TOKEN,
        )

    def test_gadgets_393(self) -> None:
        from playwright.sync_api import sync_playwright

        width = 393
        facts: dict[str, Any] = {}
        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # G1 on the Chair: one window at a time; depth gives the work
                # area to the next Chair window. PHILO-14 A1 (#939): the
                # Chair's windows start closed; he opens the Brief, then Needs
                # you, from Go. Brief now belongs to the Today window.
                brief = open_chair_window(page, "Brief")
                brief_name = brief.get_attribute("aria-label")
                open_chair_window(page, "Needs you")
                self._tap(page, page.get_by_role("button", name="To back Needs you"))
                st = self._stack(page)
                facts["chair-after-depth"] = st
                shown = [w["name"] for w in st["wins"]]
                # Canonical Today keeps the Chair pane mounted behind it.
                # Prove the one blue front and its whole hit area instead of
                # requiring every obscured window to leave the DOM.
                hits = brief.evaluate("""el => { const r = el.getBoundingClientRect();
                  // Probe the painted corners of the owner's rounded shell,
                  // rather than the transparent pixels outside its curve.
                  const inset=Math.max(2, parseFloat(getComputedStyle(el).borderTopLeftRadius)||0);
                  return [[r.left + inset, r.top + inset], [r.right - inset, r.top + inset],
                    [r.left + inset, r.bottom - inset], [r.right - inset, r.bottom - inset],
                    [r.left + r.width / 2, r.top + r.height / 2]].map(([x, y]) =>
                      document.elementFromPoint(x, y)?.closest('.desk-window-shell')?.getAttribute('aria-label') ?? null);
                }""")
                st["hit_windows"] = hits
                if (brief_name not in shown or _one_blue(st, brief_name)
                        or _z(st, "Needs you") >= _z(st, brief_name)
                        or hits != [brief_name] * 5):
                    fails["G1 393 Chair: depth"] = st

                # Two desk windows, People in front.
                _stage(page, "review-meetings")
                page.locator(".desk-window-shell[aria-label='Meetings']").wait_for()
                _stage(page, "open-people")
                people = page.locator(".desk-window-shell[aria-label='People']")
                people.wait_for()
                st = self._stack(page)
                facts["two-windows"] = st
                if _one_blue(st, "People"):
                    fails["G1 393 setup: People front"] = st
                head = people.locator(":scope > .desk-pullout-head")
                labels = [b.get_attribute("aria-label") for b in head.locator("button").all() if b.is_visible()]
                facts["people-head"] = labels
                if not labels or labels[0] != "Back from People" or labels[-1] != "To back People":
                    fails["G1 393 head: Back ... depth"] = labels
                # Depth closes the row on the right edge (design §3, board C1-2c).
                edge = page.evaluate("""() => { const s = [...document.querySelectorAll('.desk-window-shell')].find((e) => e.getAttribute('aria-label') === 'People');
                  const h = s.querySelector(':scope > .desk-pullout-head').getBoundingClientRect();
                  const d = s.querySelector('.desk-gadget-depth').getBoundingClientRect(); return Math.round(h.right - d.right); }""")
                if edge > 2:
                    fails["G1 393 depth flush right"] = edge
                depth = people.get_by_role("button", name="To back People")
                db = depth.bounding_box() or {"width": 0, "height": 0}
                if db["width"] < 43.5 or db["height"] < 43.5:
                    fails["G1 393 depth owns 44 x 44"] = db
                page.screenshot(path=str(GADGETS_SHOTS / "build-C1-2c-before-depth-393.png"))
                self._tap(page, depth)
                st = self._stack(page)
                facts["after-depth"] = st
                faults = _one_blue(st, "Meetings")
                if _z(st, "People") >= _z(st, "Meetings"):
                    faults.append("People is not behind Meetings")
                if faults:
                    fails["G1 393 depth by touch"] = faults
                page.screenshot(path=str(GADGETS_SHOTS / "build-C1-2c-depth-to-back-393.png"))

                # G3 a long press in the body opens the window menu.
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                box = meetings.bounding_box()
                assert box
                self._long_press(page, box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.6)
                page.locator(".desk-head-menu").first.wait_for()
                _settle(page)
                self._check_menu(page, "Meetings", width, facts, fails)
                page.screenshot(path=str(GADGETS_SHOTS / "build-C1-2b-window-menu-amiga-keys-393.png"))
                # To back from the menu, by touch.
                self._tap(page, page.locator(".desk-head-menu [role^='menuitem']", has_text="To back").first)
                st = self._stack(page)
                facts["after-menu-depth"] = st
                if _behind(st, "Meetings"):
                    fails["G1 393 To back from the menu"] = _behind(st, "Meetings")

                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                facts["failures"] = fails
                (GADGETS_SHOTS / "gadget-facts-393.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not fails, json.dumps(fails, indent=2, ensure_ascii=False)
            finally:
                browser.close()

    def test_a_restored_window_is_lifted_above_the_dock_1440(self) -> None:
        """Astra on PR #805: a window saved at 1440x924 and reopened at
        1440x900 kept its foot at 848 px, under the Dock (824 px). The
        window's layout effect runs before the Dock publishes its height;
        the publish must lift the window. The sizing gadget must own its own
        centre after the reload, and after the viewport gets smaller.
        """
        from playwright.sync_api import sync_playwright

        owns = r"""() => {
          const shell = document.querySelector(".desk-window-shell[aria-label='Meetings']");
          const grip = shell.querySelector('.desk-gadget-size');
          const g = grip.getBoundingClientRect(), s = shell.getBoundingClientRect();
          const dock = document.querySelector('.desk-dock').getBoundingClientRect();
          const hit = document.elementFromPoint(g.left + g.width / 2, g.top + g.height / 2);
          return {owns: Boolean(hit && grip.contains(hit)), hit: hit ? String(hit.className).slice(0, 60) : null,
            foot: Math.round(s.bottom), dockTop: Math.round(dock.top), vh: innerHeight};
        }"""
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                page.set_viewport_size({"width": 1440, "height": 924})
                page.wait_for_timeout(400)
                _stage(page, "review-meetings")
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                page.wait_for_timeout(600)
                # Snap Meetings to the left half: its foot is the band's foot.
                title = meetings.locator(".desk-pullout-title").bounding_box()
                assert title
                tx, ty = title["x"] + title["width"] / 2, title["y"] + title["height"] / 2
                page.mouse.move(tx, ty)
                page.mouse.down()
                page.mouse.move(1, 460, steps=12)
                page.mouse.up()
                page.wait_for_timeout(400)
                saved = page.evaluate(owns)
                # The floating dock (#1494/#1497): the band ends 10 px of air
                # above the plate (reserve 84 = plate 64 + inset 10 + air 10).
                assert saved["owns"] and saved["foot"] == saved["dockTop"] - DOCK_AIR, saved
                assert saved["foot"] > 900 - 84, saved  # under the band at 900 unless lifted

                # The reload at a smaller height: a new page of the same
                # context (the same saved workspace), never a resize.
                ctx = page.context
                page.close()
                page = ctx.new_page()
                page.set_viewport_size({"width": 1440, "height": 900})
                page.goto(f"{self.base}/?token={GADGETS_TOKEN}", wait_until="load")
                _normal_chair(page)
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                page.wait_for_timeout(800)
                reloaded = page.evaluate(owns)
                assert reloaded["owns"] and reloaded["foot"] <= reloaded["dockTop"] - DOCK_AIR, reloaded

                # The viewport gets smaller: the window is clamped again.
                page.set_viewport_size({"width": 1440, "height": 860})
                page.wait_for_timeout(700)
                smaller = page.evaluate(owns)
                assert smaller["owns"] and smaller["foot"] <= smaller["dockTop"] - DOCK_AIR, smaller
                assert not errors, errors
            finally:
                browser.close()


@pytest.mark.e2e
@pytest.mark.parametrize("width", [1440, 393])
def test_firefox_modern_shell_keeps_frame_and_control_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Actual shared frame on Ask and Settings, including narrow hit ownership."""
    from playwright.sync_api import expect, sync_playwright

    token = "modern-shell-glass"
    _ensure_build()
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    server, base = _boot(tmp_path, monkeypatch, token=token)
    shots = evidence_dir("modern-shell")
    try:
        with sync_playwright() as pw:
            browser = pw.firefox.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852},
                                    reduced_motion="reduce")
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            try:
                page.goto(f"{base}/?token={token}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=token)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.keyboard.press("Control+KeyI")
                ask = page.locator("#ask[data-layer=window]")
                editor = ask.get_by_role("textbox", name="Ask about your work", exact=True)
                editor.fill("A retained draft in the modern shell")
                _settle(page)
                for frame, name in [(ask, "ask")]:
                    facts = frame.evaluate("""el => {
                      const s=getComputedStyle(el), h=getComputedStyle(el.querySelector('.desk-pullout-head'));
                      return {sheet:el.classList.contains('is-sheet'),border:s.borderLeftWidth,radius:s.borderTopLeftRadius,shadow:s.boxShadow,
                        titleFont:h.fontFamily,headImage:h.backgroundImage,headHeight:el.querySelector('.desk-pullout-head').getBoundingClientRect().height};
                    }""")
                    assert facts["border"] == ("0px" if facts["sheet"] else "1px"), facts
                    assert float(facts["radius"].replace('px','')) >= 6, facts
                    assert facts["headImage"] == "none", facts
                    assert facts["headHeight"] >= (44 if width == 393 else 30), facts
                    assert frame.evaluate("el=>{const r=el.getBoundingClientRect();return r.left>=-1&&r.right<=innerWidth+1}")
                    controls = frame.locator(".desk-pullout-head button")
                    for control in controls.all():
                        if not control.is_visible(): continue
                        assert control.evaluate("""el => {
                          const r=el.getBoundingClientRect();
                          return [.15,.5,.85].every(x=>[.15,.5,.85].every(y=>{
                            const hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);
                            return hit===el || el.contains(hit);
                          }));
                        }"""), control.get_attribute("aria-label")
                    page.screenshot(path=str(shots / f"{name}-{width}.png"))
                    (shots / f"frame-{width}.json").write_text(json.dumps(facts, indent=2))
                expect(editor).to_have_value("A retained draft in the modern shell")
                _api(page, "POST", "/api/desk/windows/surface-settings/open", {}, token=token)
                settings = page.locator("#surface-settings[data-layer=window]")
                settings.get_by_test_id("settings-index-speak").click()
                expect(settings.get_by_test_id("settings-index-speak")).to_have_attribute("aria-current", "location")
                _settle(page)
                assert settings.evaluate("el=>{const r=el.getBoundingClientRect();return r.left>=-1&&r.right<=innerWidth+1}")
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                page.screenshot(path=str(shots / f"settings-{width}.png"))
                if width == 393:
                    # The narrow Settings window opens its pane over the rail
                    # (#1458); the frame's own Back returns to the rail.
                    settings.get_by_test_id("settings-back").click()
                settings.get_by_test_id("settings-index-you").click()
                expect(settings.get_by_test_id("settings-index-you")).to_have_attribute("aria-current", "location")
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.stop()
