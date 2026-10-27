"""The windows of the desk, AS RENDERED: what only a real browser proves.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. Through the real hub
on an isolated HOME, the built bundle, at 393x852 with ``has_touch`` (every
press a touch tap, every swipe a CDP touch drag, the window menu a touch long
press):

* The phone desk (PHILO-13-17, C7; the owner ratified the canvas 2026-10-03):
  the frame (menu bar + Dock) <= 142 px; the front window's content >= 700
  px; the Go door is painted whole at 4.5:1; the menu bar and the Dock own
  no point of a content control's 44 px band; every body and footer control
  of the front window owns 44 x 44. The swipe lands 5 of 5 where the ring
  says (it wraps) and one swipe goes back; the long press still opens the
  window menu; Go reaches a daily window in 2 taps, and a second tap
  closes Go (Astra r1 #751).
* Escape on an open strip menu closes the menu, not the window (PHILO-13-18):
  Speak's wings fold into one strip menu at 393; a tap opens it and leaves
  focus on the Button; the first Escape closes the menu and Speak stays in
  front; a second Escape still closes the window.

* PHILO-16 the compositor core (moved whole): planes, Tile with its divider
  drag, Stage (⌘⏎), Exposé (⌘⇧E), Gather (⌘G), keys quiet in a text field,
  393 unchanged; Astra's two rounds of repros.
* PHILO-16 16b the hub owns the windows (moved whole): several browser views
  of ONE hub agree, live; the MCP arrange tiles both views.
* PHILO-17 windows open well and come back as themselves (moved whole):
  three views, drags, nothing bounces back.
* A window's title is the name of the thing in it (moved whole): at 393 the
  clock leaves the bar and the Room's name takes its width.

Cheaper successors of the rest: the ring, the switcher rows, Go at 393 and
the four flat menus at 1440 in web/src/desk/components/window/phoneRing.test.tsx
and web/src/desk/components/DeskMenuBar.test.tsx; the aftercare card's
placement in web/src/desk/chair/__tests__/aftercarePhone.philo1317.test.tsx;
clip, overlap and fit of every window in the desk sweep.

Also here (lane e2e-high-1: close means gone; the desk remembers):

Desk windows in a real browser: close means gone, and the desk remembers.

Kept by the test diet (push 2, 2026-10-12), one file for the desk's windows.
Each check needs a real browser:

* close means gone (PHILO-13-05): every opener's window closes through its
  own gadget, leaves the DOM, and `elementFromPoint` at its old centre hits
  the Desk, so the next tap reaches what is under it (hit-testing), at 1440
  and 393 (touch);
* the desk remembers (PHILO-13-07): a moved window (a drag), an iconified
  one and the unsent drafts return after a real page reload, at 1440 and 393.

Was tests/e2e/test_philo13_05_close_glass.py and
test_philo13_07_remembers_glass.py (parked whole). The remembers rig is
tests/e2e/remembers_rig.py. The other remembers legs (a closed window stays
gone; every family and draft returns; an emptied Room draft stays empty;
the Thought's words return) are web/src/desk/__tests__/deskRemembers.philo1307.test.tsx
and deskRemembers2.philo1307.test.tsx.
"""
from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from .chair_windows import chair_window, open_chair_window
from .glass_infra import (
    _api,
    _boot,
    _ensure_build,
    _normal_chair,
    _rendered_text_faults,
    _room_opened,
    _settle,
    clear_hub_windows,
    open_project_drawer,
)
from .frame_rig import ROOM, _seed, _stage
from .frame_rig import _seed as _frame_seed
from tests._evidence import evidence_dir
from .open_rig import COMMITMENT
from .remembers_rig import AGENDA
from .remembers_rig import DECISION
from .remembers_rig import PERSON
from .remembers_rig import ROOM_WORDS
from .remembers_rig import SHOTS as _h1_SHOTS
from .remembers_rig import SIZES as _h1_SIZES
from .remembers_rig import _Rig

pytestmark = [pytest.mark.e2e]

pytest.importorskip("playwright.sync_api", reason="the windows glass needs Playwright")

TOKEN = "windows-glass"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-17-shots")
SIZES = {1440: 900, 393: 852}
MEETING = "Ledger cutover sync"
FRAME_MAX, CONTENT_MIN = 142, 700
T = 30_000

# C1's ratified fence library and the C7 canvas CHROME_OWNS fence, ported
# verbatim from assets/story-11-canvas/harness/shoot.py:127 (JS_LIB) and
# assets/story-15-canvas/harness/board.py:86 (CHROME_OWNS).
JS_LIB = r"""
const shown = (e) => { if (!e || e.closest('[hidden]')) return false; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
  return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05 && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth; };
const layer = (e) => e && e.closest('[role=menu], .desk-window-shell, .desk-menubar, .desk-dock');
const vrect = (e) => { const r = e.getBoundingClientRect(); let t = r.top, l = r.left, b = r.bottom, ri = r.right;
  for (let a = e.parentElement; a; a = a.parentElement) { const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowX + cs.overflowY)) { const ar = a.getBoundingClientRect(); t = Math.max(t, ar.top); l = Math.max(l, ar.left); b = Math.min(b, ar.bottom); ri = Math.min(ri, ar.right); } }
  t = Math.max(t, 0); l = Math.max(l, 0); b = Math.min(b, innerHeight); ri = Math.min(ri, innerWidth);
  return { t, l, b, r: ri, w: ri - l, h: b - t, full: Math.abs(ri - l - r.width) < 1.5 && Math.abs(b - t - r.height) < 1.5 }; };
const nine = (x0, y0, x1, y1) => { const xs = [x0 + 2, (x0 + x1) / 2, x1 - 2], ys = [y0 + 2, (y0 + y1) / 2, y1 - 2]; return xs.flatMap((x) => ys.map((y) => [x, y])); };
const probe = (t, x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 'lost'; if (t === h || t.contains(h)) return 'own';
  const lt = layer(t), lh = layer(h); return (lh && lt && lh !== lt && !lt.contains(lh)) ? 'occluded' : 'lost'; };
"""

CHROME_OWNS = "() => {" + JS_LIB + r"""
  const out = [];
  for (const t of document.querySelectorAll('button, a[href], [role=button], [role=menuitem], [role=tab], [role=checkbox], input:not([type=hidden]), select, textarea')) {
    if (!shown(t) || !t.closest('.desk-window-shell') || t.closest('[role=menu], .desk-menubar, .desk-dock')) continue;
    if (t.parentElement && t.parentElement.closest('button, [role=button], a[href], [role=menuitem]')) continue;
    const v = vrect(t); if (!v.full) continue;
    const cx = (v.l + v.r) / 2, cy = (v.t + v.b) / 2, hw = Math.max(22, v.w / 2), hh = Math.max(22, v.h / 2);
    const w0 = (document.elementFromPoint(cx, cy) || { closest: () => null }).closest('.desk-window-shell');
    if (w0 && w0 !== t.closest('.desk-window-shell')) continue;
    const hits = nine(cx - hw, cy - hh, cx + hw, cy + hh).map(([x, y]) => document.elementFromPoint(x, y)).filter((h) => h && h.closest('.desk-menubar, .desk-dock'));
    if (hits.length) out.push({ name: (t.getAttribute('aria-label') || t.innerText || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32), chrome_points: hits.length, w: Math.round(v.w), h: Math.round(v.h) });
  }
  return out;
}"""

# Q5: every control in the FRONT window's body and footer owns 44 x 44 (C1's
# TARGETS44, scoped to the front window's body and footer).
BODY44 = "() => {" + JS_LIB + r"""
  const f = document.querySelector('.desk-window-shell.is-front'); if (!f) return null;
  const out = [];
  for (const t of f.querySelectorAll(':scope > :not(.desk-pullout-head) :is(button, a[href], [role=button])')) {
    if (!shown(t) || t.closest('[role=menu]')) continue;
    // W1-KIT (2026-10-27, the atlas fix the owner approved): the phone status
    // bar is ONE 24 px line; its verbs are dense verbs, not 44 px plates.
    if (t.closest('.kit-statusbar-verbs')) continue;
    if (t.parentElement && t.parentElement.closest('button, [role=button], a[href]')) continue;
    const v = vrect(t); if (!v.full) continue;
    const r = t.getBoundingClientRect();
    if (r.width < 43.5 || r.height < 43.5) out.push({ name: (t.getAttribute('aria-label') || t.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 32), w: Math.round(r.width), h: Math.round(r.height) });
  }
  return out;
}"""

FRAME = r"""() => {
  const h = (s) => { const e = document.querySelector(s); if (!e) return 0; const r = e.getBoundingClientRect(); return r.height > 0 ? Math.round(r.height) : 0; };
  const f = document.querySelector('.desk-window-shell.is-front');
  let content = null;
  if (f) { const r = f.getBoundingClientRect(); const head = f.querySelector(':scope > .desk-pullout-head'); const hh = head ? head.getBoundingClientRect().height : 0;
    const cs = getComputedStyle(f); const bt = parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth);
    content = Math.round(Math.min(r.bottom, innerHeight) - Math.max(r.top, 0) - hh - bt); }
  const front = [...document.querySelectorAll('.desk-window-shell.is-front')].filter((e) => e.getBoundingClientRect().width > 0).map((e) => e.getAttribute('aria-label'));
  const title = document.querySelector('[data-testid=desk-screen-title] .desk-screen-name');
  return { menubar: h('.desk-menubar'), dock: h('.desk-dock'), content, front,
           title: title ? title.textContent.trim() : null,
           fixed_card: !!document.querySelector('.ambient-aftercare-fixed'),
           card_in_capture: !!document.querySelector("[id='chair:capture'] [data-aftercare-slot] .ambient-aftercare") };
}"""

WHOLE = "(sel) => {" + JS_LIB + r"""
  const e = document.querySelector(sel); if (!e || !shown(e)) return { found: !!e, whole: false };
  const v = vrect(e); const h = document.elementFromPoint((v.l + v.r) / 2, (v.t + v.b) / 2);
  return { found: true, whole: v.full && !!h && (e === h || e.contains(h) || h.contains(e)), w: Math.round(v.w), h: Math.round(v.h) };
}"""


MARK_CONTRAST = r"""(sel) => {
  const rgb = (s) => { const m = String(s).match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const blend = (t, u) => ({r: t.r * t.a + u.r * (1 - t.a), g: t.g * t.a + u.g * (1 - t.a), b: t.b * t.a + u.b * (1 - t.a), a: 1});
  const mark = document.querySelector(sel); if (!mark) return {ratio: 0};
  const chain = []; for (let e = mark; e; e = e.parentElement) {
    const c = rgb(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { chain.push(c); if (c.a >= 1) break; } }
  let g = {r: 255, g: 255, b: 255, a: 1}; for (let i = chain.length - 1; i >= 0; i--) g = blend(chain[i], g);
  const fg = blend(rgb(getComputedStyle(mark, '::before').color) || rgb(getComputedStyle(mark).color), g);
  const x = lum(fg), y = lum(g);
  const btn = mark.closest('button');
  return {ratio: Math.round(((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)) * 100) / 100,
          fg: [fg.r, fg.g, fg.b].map(Math.round), bg: [g.r, g.g, g.b].map(Math.round),
          open: btn ? btn.getAttribute('aria-expanded') === 'true' : null};
}"""


# PHILO-14 A1: the Chair is the screen of objects; this spec reads its windows (tests/conftest.py).
@pytest.mark.chair_windows_open
class TestThePhoneDesk:
    """replaces: tests/e2e/test_philo13_17_phone_desk_glass.py (its touch and geometry legs)."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _frame_seed()
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the hands ────────────────────────────────────────────────────────

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(20_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        # PHILO-16 (16b): one hub is one desk; this page starts on an empty desk.
        from .glass_infra import clear_hub_windows

        clear_hub_windows(page, TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _tap(page: Any, loc: Any, width: int, wait: int = 450) -> None:
        loc.first.wait_for()
        loc.first.scroll_into_view_if_needed()
        if width < 720:
            box = loc.first.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.first.click()
        page.wait_for_timeout(wait)

    @staticmethod
    def _swipe(page: Any, direction: int) -> None:
        """A touch drag across the front window's body: start, six moves, end (CDP)."""
        y = 430
        x0, x1 = (340, 90) if direction > 0 else (60, 330)
        cdp = page.context.new_cdp_session(page)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y, "id": 1}]})
        for i in range(1, 7):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove",
                                                  "touchPoints": [{"x": x0 + (x1 - x0) * i / 6, "y": y + i, "id": 1}]})
            page.wait_for_timeout(16)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        cdp.detach()
        page.wait_for_timeout(700)
        _settle(page)

    @staticmethod
    def _long_press(page: Any, x: float, y: float) -> None:
        cdp = page.context.new_cdp_session(page)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 2}]})
        page.wait_for_timeout(800)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        cdp.detach()
        page.wait_for_timeout(400)

    @staticmethod
    def _front(page: Any) -> dict[str, Any]:
        return page.evaluate(FRAME)

    def _board(self, page: Any, width: int, name: str, facts: dict[str, Any], fails: list[str],
               *, navigator: bool = True) -> dict[str, Any]:
        """One board: the shot and every glass fence of this story."""
        _settle(page)
        f = self._front(page)
        f["chrome_owns_content"] = page.evaluate(CHROME_OWNS) if width < 720 else []
        f["body_under_44"] = page.evaluate(BODY44) if width < 720 else []
        # The Dock is left out: at 393 it is the one strip ratified to scroll
        # sideways inside itself (C1 R2; phoneDoors.test.tsx), which the reader
        # names `sideways` by design. Its own fence is the frame glass.
        faults = _rendered_text_faults(page, ".desk-window-shell.is-front, .desk-menubar, [role=menu]",
                                       on_glass=True)
        f["on_glass"] = {k: faults[k] for k in ("scopes", "clipped", "overlaps")}
        if width < 720:
            frame = f["menubar"] + f["dock"]
            f["frame_px"] = frame
            if frame > FRAME_MAX:
                fails.append(f"{name}: the frame is {frame} px (> {FRAME_MAX})")
            if f["front"] and (f["content"] or 0) < CONTENT_MIN:
                fails.append(f"{name}: the front window's content is {f['content']} px (< {CONTENT_MIN})")
            if f["chrome_owns_content"]:
                fails.append(f"{name}: chrome owns content hit points {f['chrome_owns_content']}")
            if f["body_under_44"]:
                fails.append(f"{name}: body/footer controls under 44 x 44 {f['body_under_44']}")
            if navigator:
                f["go"] = self._navigator(page)
                if not (f["go"]["whole"] and f["go"]["painted"] and f["go"]["contrast"]["ratio"] >= 4.5):
                    fails.append(f"{name}: Go is not painted whole {f['go']}")
        if faults["clipped"] or faults["overlaps"]:
            fails.append(f"{name}: on_glass clipped/overlaps {f['on_glass']}")
        if f["fixed_card"]:
            fails.append(f"{name}: a fixed aftercare card floats over work")
        if len(f["front"]) > 1:
            fails.append(f"{name}: more than one front window {f['front']}")
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))
        facts[name] = f
        return f

    @staticmethod
    def _navigator(page: Any) -> dict[str, Any]:
        """Go is painted whole, owns its centre, and has visible contrast."""
        sel = ".desk-verbbar-item[data-menu-id=go] button"
        w = page.evaluate(WHOLE, sel)
        b = page.locator(sel).first.bounding_box()
        clip = {"x": b["x"], "y": b["y"], "width": max(1, b["width"]), "height": max(1, b["height"])}
        shown = page.screenshot(clip=clip)
        page.evaluate(f"() => {{ document.querySelector('{sel}').style.visibility = 'hidden'; }}")
        hidden = page.screenshot(clip=clip)
        page.evaluate(f"() => {{ document.querySelector('{sel}').style.visibility = ''; }}")
        cut = page.evaluate("""() => { const n = document.querySelector('.desk-screen-title .desk-screen-name');
            return n ? n.scrollWidth > n.clientWidth + 1 : null; }""")
        # Keep the visibility/contrast fence on the current navigator,
        # with its menu closed and open.
        contrast = page.evaluate(MARK_CONTRAST, sel)
        return {"whole": bool(w.get("whole")), "painted": shown != hidden, "contrast": contrast,
                "box": [round(b["x"]), round(b["y"]), round(b["width"]), round(b["height"])], "title_truncated": cut}

    def _open_meeting(self, page: Any, width: int) -> None:
        """Meetings from Go's own rows, then the meeting window from the palette (the owner's doors)."""
        self._tap(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
        self._tap(page, page.locator(".desk-verbbar-menu").get_by_role("menuitem", name=re.compile(r"^Meetings")), width, 1500)
        page.locator(".desk-window-shell[aria-label='Meetings']").wait_for()
        self._tap(page, page.locator("[aria-controls=desk-tool-shelf]"), width)
        search = page.locator("[aria-controls=desk-palette-listbox]")
        search.fill(MEETING)
        page.wait_for_timeout(900)
        self._tap(page, page.locator("[id^='desk-palette-option-meeting:m-standup']"), width, 2000)
        page.locator(f".desk-window-shell[aria-label='{MEETING}']").wait_for()
        _settle(page)

    # ── the fence ────────────────────────────────────────────────────────

    def test_the_phone_desk_393(self) -> None:
        """replaces: tests/e2e/test_philo13_17_phone_desk_glass.py::TestThePhoneDesk::test_the_phone_desk_393
        (S1 the frame, S2 the swipe, the long press, S3 the switcher) and
        ::test_the_ring_keeps_order_and_name_and_the_switcher_toggles_393 (C2, the native second tap)."""
        from playwright.sync_api import sync_playwright

        width = 393
        facts: dict[str, Any] = {"width": width}
        fails: list[str] = []
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # S1 the frame on the Chair's Needs you
                f = self._board(page, width, "C7-1-the-frame", facts, fails)
                if f["front"] != ["Needs you"] or f["title"] != "Needs you":
                    fails.append(f"C7-1: Needs you is not the one front window {f['front']} {f['title']}")

                # Today from Go (Betterment D4: Today is one page; D5: Brief
                # and The week are part of it). Meetings then holds the
                # selected record in its one host; no duplicate record pane.
                self._tap(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
                self._tap(page, page.locator(".desk-verbbar-menu").get_by_role("menuitem", name="Today", exact=True), width)
                today = chair_window(page, "Brief")
                today.wait_for()
                today.get_by_test_id("today-since-toggle").wait_for()
                self._open_meeting(page, width)
                self._board(page, width, "C7-3a-meeting-window", facts, fails)
                ring = ["Needs you", "Today", MEETING]

                # Four real forward gestures still prove the wrap, followed
                # by a reverse gesture to the selected meeting's same host.
                landed: list[str | None] = []
                for _ in range(4):
                    self._swipe(page, +1)
                    fr = self._front(page)["front"]
                    landed.append(fr[0] if len(fr) == 1 else None)
                facts["swipe_forward"] = landed
                if landed != ring + ring[:1]:
                    fails.append(f"S2: 4 swipes landed {landed}, the ring says {ring + ring[:1]}")
                self._swipe(page, -1)
                back = self._front(page)["front"]
                facts["swipe_back"] = back
                if back != [MEETING]:
                    fails.append(f"S2: a swipe back landed {back}, not {MEETING}")
                self._board(page, width, "C7-3b-swipe-to-meetings", facts, fails)
                self._swipe(page, -1)
                if self._front(page)["front"] != ["Today"]:
                    fails.append(f"S2: past Meetings the swipe landed {self._front(page)['front']}")
                self._swipe(page, -1)
                if self._front(page)["front"] != ["Needs you"]:
                    fails.append(f"S2: past Today the swipe landed {self._front(page)['front']}")
                self._board(page, width, "C7-3c-swipe-to-the-chair", facts, fails)

                # the long press still opens the window menu (the swipe never eats it)
                head = page.locator(".desk-window-shell.is-front .desk-pullout-title").first.bounding_box()
                self._long_press(page, head["x"] + head["width"] / 2, head["y"] + head["height"] / 2)
                menu = page.locator(".desk-head-menu[role=menu]")
                facts["long_press_menu"] = menu.count()
                if not menu.count():
                    fails.append("long press: no window menu")
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)

                # Go is the current two-tap phone navigator. Its second
                # native tap dismisses it; a third opens it again.
                go = page.locator(".desk-verbbar-item[data-menu-id='go'] button")
                # The phone home also has a persistent Go menu. Toggle the
                # transient menu that belongs to this title Button.
                menu = page.locator('.desk-verbbar-menu[role="menu"][aria-label="Go menu"]')
                self._tap(page, go, width, 600)
                menu.wait_for()
                assert go.get_attribute("aria-expanded") == "true"
                rows = menu.locator(".desk-menu-label").all_inner_texts()
                facts["go_rows"] = rows
                # Betterment shell S1 (#1259): the phone's Go is the
                # manifest's Daily group first, as at 1440: Today, then the
                # Chair's windows (Go is their door on an empty desk).
                if rows[:3] != ["Today", "Needs you", "Capture"]:
                    fails.append(f"S3: Go lists {rows}")
                self._board(page, width, "C7-4a-go-open", facts, fails)
                self._tap(page, go, width, 600)
                if menu.count() or go.get_attribute("aria-expanded") != "false":
                    fails.append("C2 a second tap on Go did not close it")
                self._tap(page, go, width, 600)
                if not menu.is_visible() or go.get_attribute("aria-expanded") != "true":
                    fails.append("C2 a third tap did not open Go")
                self._tap(page, menu.get_by_role("menuitemcheckbox", name="Needs you", exact=True), width, 700)
                f = self._board(page, width, "C7-4b-go-picked", facts, fails)
                if f["front"] != ["Needs you"]:
                    fails.append(f"S3: two taps landed {f['front']}")

                real = [e for e in errors if "ResizeObserver" not in e]
                facts["errors"] = real
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / f"phone-desk-facts-{width}.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1, default=str))
                browser.close()
        assert not fails, fails


def test_escape_closes_the_strip_menu_not_the_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """replaces: tests/e2e/test_philo13_18_strip_escape_glass.py::test_escape_closes_the_strip_menu_not_the_window

    PHILO-17 ("A meeting opens in one window"): the window whose wings still
    fold at 393 is Speak (four wings and a door)."""
    from playwright.sync_api import sync_playwright

    token = "windows-glass-escape"
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=token)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_context(viewport={"width": 393, "height": 852}, has_touch=True).new_page()
            page.set_default_timeout(20_000)
            page.goto(f"{base}/?token={token}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=token)
            page.evaluate("sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key: 'dictate'}))")
            page.reload(wait_until="load")
            _normal_chair(page)
            window = page.locator(".desk-window-shell[aria-label='Speak']")
            window.wait_for()
            _settle(page)
            strip = window.locator(".desk-wings-menu")
            assert strip.count() == 1, "at 393 the Speak wings fold into one strip menu"
            box = strip.bounding_box()
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            strip_menu = page.get_by_role("menu", name="Window faces", exact=True)
            strip_menu.wait_for()
            assert strip.get_attribute("aria-expanded") == "true"
            page.keyboard.press("Escape")
            strip_menu.wait_for(state="detached")
            menu_open = strip_menu.count()
            assert strip.get_attribute("aria-expanded") == "false"
            still_open = window.count() and window.is_visible()
            front = page.evaluate(
                "() => { const f = [...document.querySelectorAll('.desk-window-shell.is-front')].pop();"
                " return f ? f.getAttribute('aria-label') : null; }")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            closed_after_second = window.count() == 0 or not window.is_visible()
            browser.close()
    finally:
        server.stop()

    assert menu_open == 0, "the first Escape left the strip menu open"
    assert still_open and front == "Speak", f"the first Escape closed the window (front now {front!r})"
    assert closed_after_second, "a second Escape no longer closes the window"


# ── PHILO-16 the compositor core (moved whole: Tile, Stage ⌘⏎, Exposé ⌘⇧E, Gather ⌘G, the divider drag, keys quiet in a field, 393 unchanged) ──
C_TOKEN = "philo16-compositor"
C_SHOTS = evidence_dir("docs/internal/philo/phase-16/a2-shots")

C_WINS_JS = r"""() => {
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  return [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible).map((s) => {
    const r = s.getBoundingClientRect(); const cs = getComputedStyle(s);
    return {name: s.getAttribute('aria-label'), plane: s.dataset.plane || null, layer: s.dataset.layer || null,
      front: s.classList.contains('is-front'), z: Number(cs.zIndex) || 0,
      k: s.style.getPropertyValue('--plate-k') || null, scale: cs.scale,
      layoutW: s.offsetWidth, layoutH: s.offsetHeight,
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]}; });
}"""

C_BAND_JS = r"""() => {
  const st = getComputedStyle(document.documentElement);
  const top = parseFloat(st.getPropertyValue('--desk-work-top'));
  const band = parseFloat(st.getPropertyValue('--desk-work-bottom'));
  const dock = parseFloat(st.getPropertyValue('--desk-dock-h'));
  const bottom = Number.isFinite(dock) ? Math.max(band, dock) : band;
  return {x: 10, y: top, w: innerWidth - 20, h: innerHeight - top - bottom};
}"""

C_DIVIDERS_JS = r"""() => [...document.querySelectorAll('.desk-window-divider')].map((d) => {
  const r = d.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })"""


def _c_wins(page: Any) -> list[dict[str, Any]]:
    page.wait_for_timeout(450)  # the longest moment is 360 ms
    _settle(page)
    return page.evaluate(C_WINS_JS)


def _c_by(wins: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(w for w in wins if w["name"] == name)


def _c_fronts(wins: list[dict[str, Any]]) -> list[str]:
    return [w["name"] for w in wins if w["plane"] == "front"]


def _c_inside(rect: list[int], band: dict[str, float], slack: int = 2) -> bool:
    x, y, w, h = rect
    return (x >= band["x"] - slack and y >= band["y"] - slack
            and x + w <= band["x"] + band["w"] + slack and y + h <= band["y"] + band["h"] + slack)


C_PANEL_JS = r"""() => { const d = JSON.parse(localStorage.getItem('hs.desk.workspace.v1') || 'null');
  const p = (d && d.panel) || {}; return {rects: p.rects || {}, zoom: p.zoom || {}, max: p.max || []}; }"""

# The motion moving the window itself (a lift, an arrange): script
# animations on transform / scale. A1's plane change is CSS transitions of
# colour and shadow (the ladder), which may run while the pointer is down.
C_RUNNING_JS = r"""(name) => { const el = document.querySelector(`.desk-window-shell[aria-label='${name}']`);
  if (!el) return -1;
  return el.getAnimations({subtree: false}).filter((a) => a.playState === 'running' && !(a instanceof CSSTransition))
    .filter((a) => (a.effect.getKeyframes() || []).some((k) => 'scale' in k || 'transform' in k)).length; }"""

C_ALL_RUNNING_JS = r"""(name) => { const el = document.querySelector(`.desk-window-shell[aria-label='${name}']`);
  return el ? el.getAnimations().filter((a) => a.playState === 'running')
    .map((a) => a instanceof CSSTransition ? `transition:${a.transitionProperty}` : `${a.constructor.name}:${a.animationName || ''}`) : null; }"""


def _c_drag(page: Any, selector: str, dx: float, dy: float, *, hold: Any = None) -> None:
    box = page.locator(selector).first.bounding_box()
    assert box, f"nothing to drag: {selector}"
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx / 2, y + dy / 2, steps=4)
    page.mouse.move(x + dx, y + dy, steps=4)
    if hold:
        hold()
    page.mouse.up()


def _c_window_menu(page: Any, label: str) -> None:
    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
    page.locator(".desk-verbbar-menu").wait_for()
    page.locator(".desk-verbbar-menu [role^='menuitem']").filter(has_text=label).first.click()


class TestCompositor:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=C_TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(T)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={C_TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=C_TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    def test_compositor_1440(self) -> None:
        """replaces: tests/e2e/test_philo16_compositor_glass.py::TestCompositor::test_compositor_1440 (moved whole)."""
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                band = page.evaluate(C_BAND_JS)
                # Betterment daily D5: Today (with Since yesterday open), Capture, Needs you.
                for name in ("Brief", "Capture", "Needs you"):
                    open_chair_window(page, name)
                wins = _c_wins(page)
                names = [w["name"] for w in wins]
                if not {"Today", "Capture", "Needs you"} <= set(names):
                    fails["C1 three windows open"] = names
                planes = {w["name"]: w["plane"] for w in wins}
                if sorted(planes.values()).count("front") != 1 or "near" not in planes.values() or "far" not in planes.values():
                    fails["C1 front, near, far"] = planes
                if any(w["layer"] != "window" for w in wins):
                    fails["C1 data-layer=window"] = wins
                if any(w["front"] != (w["plane"] == "front") for w in wins):
                    fails["C1 is-front is the alias of data-plane=front"] = wins
                order = sorted(wins, key=lambda w: w["z"])
                if order[-1]["plane"] != "front" or order[-2]["plane"] != "near":
                    fails["C1 z rises with the plane"] = [(w["name"], w["z"], w["plane"]) for w in order]
                page.screenshot(path=str(C_SHOTS / "1440-1-planes.png"))

                # A raise: the far window comes forward; the old front is NEAR.
                # Window ▸ Desk ▸ <name> (Today's seat sits under Needs you's).
                old_front = _c_fronts(wins)[0]
                far = next(w["name"] for w in wins if w["plane"] == "far")
                page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Desk')").click()
                page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{far}')").first.click()
                page.wait_for_timeout(300)
                wins = _c_wins(page)
                if _c_fronts(wins) != [far] or _c_by(wins, old_front)["plane"] != "near":
                    fails["C1 raise: far to front, old front to near"] = {w["name"]: w["plane"] for w in wins}

                # The depths persist: a reload keeps the stacking. The Chair's
                # own rule (PHILO-15-09 B16, ChairDesk.raiseNeedsAmongChair)
                # raises Needs you on the Chair's mount; every other window
                # keeps its place.
                # PHILO-16 (16b): the hub owns the stacking; a reload keeps its
                # order exactly (the Chair's mount no longer raises Needs you
                # over the hub's rows).
                stack = [w["name"] for w in sorted(_c_wins(page), key=lambda w: w["z"])]
                want = stack
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)
                after = [w["name"] for w in sorted(_c_wins(page), key=lambda w: w["z"])]
                if after != want:
                    fails["C1 a reload keeps the stacking"] = {"before": stack, "after": after, "want": want}

                # C2 tile.
                wins = _c_wins(page)
                free = {w["name"]: w["rect"] for w in wins}
                front = _c_fronts(wins)[0]
                near = next(w["name"] for w in wins if w["plane"] == "near")
                _c_window_menu(page, "Tile left")
                wins = _c_wins(page)
                fr, nr = _c_by(wins, front)["rect"], _c_by(wins, near)["rect"]
                half = band["w"] / 2
                if abs(fr[0] - band["x"]) > 2 or abs(fr[2] - half) > 2 or abs(nr[0] - (fr[0] + fr[2])) > 2:
                    fails["C2 tile: front left half, near right half, touching"] = {"front": fr, "near": nr, "band": band}
                if not (_c_inside(fr, band) and _c_inside(nr, band)):
                    fails["C2 the band is sacred"] = {"front": fr, "near": nr, "band": band}
                dividers = page.evaluate(C_DIVIDERS_JS)
                if len(dividers) != 1:
                    fails["C2 one steel divider on the seam"] = dividers
                page.screenshot(path=str(C_SHOTS / "1440-2-tile.png"))
                if dividers:
                    d = dividers[0]
                    cx, cy = d[0] + d[2] / 2, d[1] + d[3] / 2
                    page.mouse.move(cx, cy)
                    page.mouse.down()
                    page.mouse.move(cx + 40, cy, steps=4)
                    page.mouse.move(cx + 80, cy, steps=4)
                    page.mouse.up()
                    wins = _c_wins(page)
                    fr2, nr2 = _c_by(wins, front)["rect"], _c_by(wins, near)["rect"]
                    if abs(fr2[2] - (fr[2] + 80)) > 2 or abs(nr2[0] - (nr[0] + 80)) > 2:
                        fails["C2 the divider moves the shared edge"] = {"front": fr2, "near": nr2}
                    if fr2[0] != fr[0] or abs((nr2[0] + nr2[2]) - (nr[0] + nr[2])) > 1:
                        fails["C2 the far edges stay"] = {"front": fr2, "near": nr2}
                page.keyboard.press("Escape")
                wins = _c_wins(page)
                back = {w["name"]: w["rect"] for w in wins}
                if back != free:
                    fails["C2 Esc returns the remembered rects"] = {"free": free, "back": back}
                if page.evaluate(C_DIVIDERS_JS):
                    fails["C2 no divider after Esc (the windows no longer touch)"] = page.evaluate(C_DIVIDERS_JS)
                if len(_c_fronts(wins)) != 1:
                    fails["one front after tile"] = _c_fronts(wins)

                # C3 stage, by its key; the focus on the front window's bar.
                front = _c_fronts(wins)[0]
                page.locator(f".desk-window-shell[aria-label='{front}'] .desk-pullout-title").first.click()
                page.keyboard.press("Meta+Enter")
                wins = _c_wins(page)
                main = _c_by(wins, front)
                if abs(main["rect"][2] - round(band["w"] * 0.76)) > 2 or main["k"]:
                    fails["C3 the front takes 76 % of the band"] = {"main": main, "band": band}
                plates = [w for w in wins if w["name"] != front]
                for p in plates:
                    if not p["k"] or p["rect"][2] > 302 or p["rect"][3] > 172 or not _c_inside(p["rect"], band):
                        fails.setdefault("C3 shelf plates scaled, inside the band", []).append(p)
                    if p["rect"][0] + p["rect"][2] > main["rect"][0] + 1:
                        fails.setdefault("C3 the shelf is on the left", []).append(p)
                page.screenshot(path=str(C_SHOTS / "1440-3-stage.png"))
                swap = plates[0]["name"] if plates else None
                if swap:
                    box = page.locator(f".desk-window-shell[aria-label='{swap}']").bounding_box()
                    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    wins = _c_wins(page)
                    if _c_fronts(wins) != [swap] or _c_by(wins, swap)["k"] or abs(_c_by(wins, swap)["rect"][2] - round(band["w"] * 0.76)) > 2:
                        fails["C3 a press on a plate swaps it onto the stage"] = {w["name"]: (w["plane"], w["rect"], w["k"]) for w in wins}
                page.keyboard.press("Escape")
                wins = _c_wins(page)
                back = {w["name"]: w["rect"] for w in wins}
                if back != free:
                    fails["C3 Esc returns the remembered rects"] = {"free": free, "back": back}

                # C4 exposé.
                page.keyboard.press("Meta+Shift+E")
                page.locator(".desk-expose").wait_for()
                wins = _c_wins(page)
                for w in wins:
                    natural = free.get(w["name"])
                    scaled = w["k"] is not None and float(w["k"]) < 1
                    if natural and scaled and abs(w["layoutW"] - natural[2]) > 2:
                        fails.setdefault("C4 plates scale, never reflow", []).append(w)
                    if not _c_inside(w["rect"], band):
                        fails.setdefault("C4 plates inside the band", []).append(w)
                cells = page.locator(".desk-expose-cell").count()
                if cells != len(wins):
                    fails["C4 one pick target per plate"] = {"cells": cells, "wins": len(wins)}
                page.screenshot(path=str(C_SHOTS / "1440-4-expose.png"))
                page.keyboard.press("Escape")
                wins = _c_wins(page)
                back = {w["name"]: w["rect"] for w in wins}
                if back != free or page.locator(".desk-expose").count():
                    fails["C4 Esc returns the remembered rects"] = {"free": free, "back": back}

                # C5 gather: the project drawer and its Get Info share a Room.
                open_project_drawer(page, self.base, 'p-ledger', C_TOKEN)  # PHILO-17 U30: the parked drawer, by its key
                _normal_chair(page)
                drawer = page.locator(".drawer-window")
                drawer.wait_for(timeout=T)
                drawer.get_by_role("button", name="Get Info", exact=True).click()
                page.locator(".drawer-info-window").wait_for(timeout=T)
                page.locator(".drawer-info-window .desk-pullout-title").first.click()
                page.keyboard.press("Meta+g")
                wins = _c_wins(page)
                room = [w for w in wins if w["name"] and ("Payments ledger cutover" in w["name"])]
                if len(room) != 2:
                    fails["C5 two windows of the Room"] = [w["name"] for w in wins]
                else:
                    a, b = sorted((w["rect"] for w in room), key=lambda r: r[0])
                    if abs(a[0] - band["x"]) > 2 or abs(b[0] - (a[0] + a[2]) - 8) > 2 or abs(a[2] - b[2]) > 2:
                        fails["C5 equal columns, 8 px gutter"] = {"a": a, "b": b, "band": band}
                    if not (_c_inside(a, band) and _c_inside(b, band)):
                        fails["C5 the band is sacred"] = {"a": a, "b": b}
                if len(_c_fronts(wins)) != 1:
                    fails["one front after gather"] = _c_fronts(wins)
                page.screenshot(path=str(C_SHOTS / "1440-5-gather.png"))

                # C6 keys stay quiet inside a text field (a field in the front
                # window: the keymap's typing guard).
                page.evaluate("""() => { const w = document.querySelector('.desk-window-shell.is-front');
                  const i = document.createElement('input'); i.type = 'text'; i.id = 'c6-field';
                  w.appendChild(i); i.focus(); }""")
                rects = {w["name"]: w["rect"] for w in _c_wins(page)}
                for key in ("Meta+Enter", "Meta+Shift+E", "Meta+g", "Meta+Alt+ArrowLeft"):
                    page.keyboard.press(key)
                wins = _c_wins(page)
                if any(w["k"] for w in wins) or page.locator(".desk-expose").count() or {w["name"]: w["rect"] for w in wins} != rects:
                    fails["C6 the arrangement keys stay quiet in a field"] = wins
                page.evaluate("() => document.getElementById('c6-field')?.remove()")
                if errors:
                    fails["page errors"] = errors
            finally:
                browser.close()
        assert not fails, fails

    def test_astra_round1_1440(self) -> None:
        """replaces: tests/e2e/test_philo16_compositor_glass.py::TestCompositor::test_astra_round1_1440 (moved whole)."""
        """Astra round 1 (5fe358d78), her repros: M1 Stage keeps the saved
        arrangement (zoomed and not); M4 no lift under a resize; M2 the
        divider stops at the frame's real minimum inside the band."""
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                band = page.evaluate(C_BAND_JS)
                for name in ("Brief", "Needs you"):
                    open_chair_window(page, name)
                needs = ".desk-window-shell[aria-label='Needs you']"

                # M1 (zoomed): Zoom -> Stage -> resize the staged front -> Esc.
                page.get_by_role("button", name="Zoom Needs you").click()
                rects = {w["name"]: w["rect"] for w in _c_wins(page)}
                doc = page.evaluate(C_PANEL_JS)
                page.locator(f"{needs} .desk-pullout-title").first.click()
                page.keyboard.press("Meta+Enter")
                _c_wins(page)
                _c_drag(page, f"{needs} .desk-window-grip", -200, -100)
                if page.evaluate(C_PANEL_JS) != doc:
                    fails["M1 zoomed: a Stage resize leaves the saved arrangement"] = {"before": doc, "during": page.evaluate(C_PANEL_JS)}
                page.keyboard.press("Escape")
                back = {w["name"]: w["rect"] for w in _c_wins(page)}
                if back != rects or page.evaluate(C_PANEL_JS) != doc:
                    fails["M1 zoomed: Esc restores both rects and the zoom flag"] = {
                        "before": rects, "after": back, "doc": doc, "doc_after": page.evaluate(C_PANEL_JS)}

                # M1 (Zoom during Stage leaves Stage first).
                page.keyboard.press("Meta+Enter")
                _c_wins(page)
                page.get_by_role("button", name="Zoom Needs you").click()  # unzoom
                wins = _c_wins(page)
                if any(w["k"] for w in wins):
                    fails["M1 Zoom during Stage leaves Stage"] = wins

                # M1 (not zoomed): Stage -> resize -> Esc.
                rects = {w["name"]: w["rect"] for w in _c_wins(page)}
                doc = page.evaluate(C_PANEL_JS)
                page.locator(f"{needs} .desk-pullout-title").first.click()
                page.keyboard.press("Meta+Enter")
                _c_wins(page)
                _c_drag(page, f"{needs} .desk-window-grip", -150, -80)
                if page.evaluate(C_PANEL_JS) != doc:
                    fails["M1 a Stage resize writes no free rect"] = {"before": doc, "during": page.evaluate(C_PANEL_JS)}
                page.keyboard.press("Escape")
                back = {w["name"]: w["rect"] for w in _c_wins(page)}
                if back != rects:
                    fails["M1 Esc restores the free rects"] = {"before": rects, "after": back}

                # M4: resize Today (behind Needs you) by its grip: no lift runs
                # while the pointer is held.
                page.locator(f"{needs} .desk-pullout-title").first.click()
                _c_wins(page)
                running: list[int] = []
                _c_drag(page, ".desk-window-shell[aria-label='Today'] .desk-window-grip", -40, -30,
                      hold=lambda: (page.wait_for_timeout(60), running.append(page.evaluate(C_RUNNING_JS, "Today"))))
                if running != [0]:
                    fails["M4 no lift during a resize"] = {"lifts": running, "all": page.evaluate(C_ALL_RUNNING_JS, "Today")}

                # M2: two surface windows (min-width 420) tiled; the divider
                # dragged past both minimums.
                _stage(page, "review-meetings")
                _stage(page, "open-people")
                wins = _c_wins(page)
                front = _c_fronts(wins)[0]
                near = next(w["name"] for w in wins if w["plane"] == "near")
                _c_window_menu(page, "Tile left")
                _c_wins(page)
                for dx in (2000, -2000):
                    d = page.evaluate(C_DIVIDERS_JS)
                    if len(d) != 1:
                        fails[f"M2 one divider ({dx})"] = d
                        break
                    _c_drag(page, ".desk-window-divider", dx, 0)
                    wins = _c_wins(page)
                    for name in (front, near):
                        r = _c_by(wins, name)["rect"]
                        if not _c_inside(r, band, slack=1) or r[2] < 419:
                            fails.setdefault(f"M2 the band and the 420 minimum ({dx})", []).append({name: r, "band": band})
                    # The two windows still meet at the divider: no overlap, no gap.
                    left, right = sorted((_c_by(wins, front)["rect"], _c_by(wins, near)["rect"]), key=lambda r: r[0])
                    seam = page.evaluate(C_DIVIDERS_JS)
                    if abs(left[0] + left[2] - right[0]) > 1 or not seam or abs(seam[0][0] + 3 - right[0]) > 2:
                        fails.setdefault(f"M2 the windows meet at the divider ({dx})", []).append(
                            {"left": left, "right": right, "divider": seam})
                page.screenshot(path=str(C_SHOTS / "1440-6-divider-minimum.png"))
                page.keyboard.press("Escape")
                if errors:
                    fails["page errors"] = errors
            finally:
                browser.close()
        assert not fails, fails

    def test_astra_round2_1440(self) -> None:
        """replaces: tests/e2e/test_philo16_compositor_glass.py::TestCompositor::test_astra_round2_1440 (moved whole)."""
        """Astra round 2 (c67c80974): a fresh People window -> Stage -> Zoom ->
        unzoom returns its pre-Stage rect, and no Stage rect lands in
        panel.rects (Zoom never measures a box in flight). PHILO-17: the fresh
        window's first seat is saved (it was unarranged before)."""
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                open_chair_window(page, "Brief")
                _stage(page, "open-people")
                people = ".desk-window-shell[aria-label='People']"
                page.locator(people).wait_for()
                wins = _c_wins(page)
                if _c_fronts(wins) != ["People"]:
                    fails["People is front"] = _c_fronts(wins)
                before = _c_by(wins, "People")["rect"]
                # PHILO-17 (U28c): a window's first seat is saved, so People
                # starts ARRANGED at the rect it shows; Stage must not change it.
                doc = page.evaluate(C_PANEL_JS)
                first = doc["rects"].get("surface-people")
                if first is not None and [first["x"], first["y"], first["w"], first["h"]] != before:
                    fails["People's saved first seat is the rect it shows"] = {"saved": first, "shown": before}
                page.locator(f"{people} .desk-pullout-title").first.click()
                page.keyboard.press("Meta+Enter")
                wins = _c_wins(page)
                if not any(w["k"] for w in wins):
                    fails["Stage is on"] = wins
                page.locator(f"{people} .desk-gadget-zoom").click()  # zoom: leaves Stage
                _c_wins(page)
                page.locator(f"{people} .desk-gadget-zoom").click()  # unzoom
                wins = _c_wins(page)
                after = _c_by(wins, "People")["rect"]
                if after != before:
                    fails["unzoom returns the pre-Stage rect"] = {"before": before, "after": after}
                saved = page.evaluate(C_PANEL_JS)["rects"].get("surface-people")
                if saved is not None and [saved["x"], saved["y"], saved["w"], saved["h"]] != before:
                    fails["no Stage rect in panel.rects"] = {"saved": saved, "before": before}
                if errors:
                    fails["page errors"] = errors
            finally:
                browser.close()
        assert not fails, fails

    def test_compositor_393(self) -> None:
        """replaces: tests/e2e/test_philo16_compositor_glass.py::TestCompositor::test_compositor_393 (moved whole)."""
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                open_chair_window(page, "Needs you")
                page.wait_for_timeout(800)
                wins = _c_wins(page)
                if len(_c_fronts(wins)) != 1:
                    fails["393 one front"] = wins
                page.keyboard.press("Meta+Enter")
                page.keyboard.press("Meta+Shift+E")
                wins = _c_wins(page)
                if any(w["k"] for w in wins) or page.locator(".desk-expose").count() or page.evaluate(C_DIVIDERS_JS):
                    fails["C7 393: nothing is arranged"] = wins
                page.screenshot(path=str(C_SHOTS / "393-sheet.png"))
                if errors:
                    fails["page errors"] = errors
            finally:
                browser.close()
        assert not fails, fails


# ── PHILO-16 16b the hub owns the windows (moved whole: several browser views of ONE hub, a drag, the MCP arrange) ──
H_TOKEN = "philo16-hub-windows"
H_SHOTS = evidence_dir("docs/internal/philo/phase-16/b-shots")
SHELL_SHOTS = evidence_dir("")
# Betterment daily D5: Brief and The week retired into Today; the three are
# Capture (dragged), Meetings (seated) and Needs you (in front).
H_THREE = ("Capture", "Meetings", "Needs you")
H_IDS = {"Capture": "chair:capture", "Meetings": "surface-meetings", "Needs you": "chair:needs"}


def _h_open(page: Any, name: str) -> None:
    """Open one of H_THREE from Go (Meetings is an application window)."""
    if name != "Meetings":
        open_chair_window(page, name)
        return
    page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
    page.locator(".desk-verbbar-menu").wait_for()
    page.locator(".desk-verbbar-menu").get_by_role("menuitem", name=re.compile(r"^Meetings")).first.click()
    page.locator(".desk-window-shell[aria-label='Meetings']").wait_for()

H_WINS_JS = r"""() => {
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  return [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible).map((s) => {
    const r = s.getBoundingClientRect();
    return {name: s.getAttribute('aria-label'), plane: s.dataset.plane || null,
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]}; });
}"""

H_BAND_JS = r"""() => {
  const st = getComputedStyle(document.documentElement);
  const top = parseFloat(st.getPropertyValue('--desk-work-top'));
  const band = parseFloat(st.getPropertyValue('--desk-work-bottom'));
  const dock = parseFloat(st.getPropertyValue('--desk-dock-h'));
  const bottom = Number.isFinite(dock) ? Math.max(band, dock) : band;
  return {x: 10, y: top, w: innerWidth - 20, h: innerHeight - top - bottom};
}"""

H_CACHE_JS = r"""() => { const d = JSON.parse(localStorage.getItem('hs.desk.workspace.v1') || 'null') || {};
  const p = d.panel || {}; return {min: p.min || [], depth: p.depth || {}, closed: (d.chair || {}).closed || []}; }"""

SHELL_GEOMETRY_JS = r"""() => {
  const shown = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  return [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(shown).map((s) => {
    const r = s.getBoundingClientRect();
    const head = s.querySelector('.desk-pullout-head')?.getBoundingClientRect() || r;
    const probes = [8, Math.round(head.width / 2), Math.max(8, Math.round(head.width - 8))]
      .map((x) => document.elementFromPoint(Math.round(head.left + x), Math.round(head.top + Math.min(20, head.height / 2))))
      .filter(Boolean);
    const reachable = probes.some((point) => point?.closest('.desk-window-shell') === s);
    return {name: s.getAttribute('aria-label'), rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      head: [Math.round(head.left), Math.round(head.top), Math.round(head.width), Math.round(head.height)],
      plane: s.dataset.plane || null, z: Number(getComputedStyle(s).zIndex) || 0,
      reachable};
  });
}"""

SHELL_LABEL_CONTRAST_JS = r"""() => {
  const channel = (value, scale, normalized = false) => {
    if (value === 'none') return 0;
    if (value.endsWith('%')) return Number.parseFloat(value) * scale / 100;
    return Number.parseFloat(value) * (normalized ? scale : 1);
  };
  const alpha = (value) => value == null ? 1
    : value.endsWith('%') ? Number.parseFloat(value) / 100 : Number.parseFloat(value);
  const rgb = (value) => {
    const text = String(value).trim();
    let m = text.match(/^rgba?\(([^)]+)\)$/i);
    if (m) {
      const p = m[1].trim().split(/[,\s/]+/).filter(Boolean);
      if (p.length < 3) return null;
      return {r: channel(p[0], 255), g: channel(p[1], 255), b: channel(p[2], 255), a: alpha(p[3])};
    }
    m = text.match(/^color\(\s*srgb\s+([^\s]+)\s+([^\s]+)\s+([^\s/]+)(?:\s*\/\s*([^\s]+))?\s*\)$/i);
    if (!m) return null;
    return {r: channel(m[1], 255, true), g: channel(m[2], 255, true), b: channel(m[3], 255, true), a: alpha(m[4])};
  };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
    return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const over = (top, bottom) => ({
    r: top.r * top.a + bottom.r * (1 - top.a),
    g: top.g * top.a + bottom.g * (1 - top.a),
    b: top.b * top.a + bottom.b * (1 - top.a),
    a: 1,
  });
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  return [...document.querySelectorAll('.desk-screen .desk-icon-name')].map((e) => {
    const cs = getComputedStyle(e);
    const layers = [];
    for (let node = e; node; node = node.parentElement) {
      const color = rgb(getComputedStyle(node).backgroundColor);
      if (color && color.a > 0) {
        layers.push(color);
        if (color.a >= 1) break;
      }
    }
    let bg = {r: 255, g: 255, b: 255, a: 1};
    for (let i = layers.length - 1; i >= 0; i -= 1) bg = over(layers[i], bg);
    const parsedFg = rgb(cs.color);
    const fg = parsedFg ? over(parsedFg, bg) : null;
    return {name: e.textContent?.trim() || '', ratio: fg ? Math.round(ratio(fg, bg) * 100) / 100 : 0,
      background: cs.backgroundColor, color: cs.color};
  });
}"""


def _h_wins(page: Any) -> dict[str, dict[str, Any]]:
    _settle(page)
    return {w["name"]: w for w in page.evaluate(H_WINS_JS)}


def _h_until(probe: Callable[[], Any], ok: Callable[[Any], bool], seconds: float = 8.0) -> Any:
    deadline = time.monotonic() + seconds
    value = probe()
    while not ok(value) and time.monotonic() < deadline:
        time.sleep(0.25)
        value = probe()
    return value


def _h_drag(page: Any, selector: str, dx: float, dy: float) -> None:
    box = page.locator(selector).first.bounding_box()
    assert box, f"nothing to drag: {selector}"
    x, y = box["x"] + min(60, box["width"] / 3), box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx / 2, y + dy / 2, steps=5)
    page.mouse.move(x + dx, y + dy, steps=5)
    page.mouse.up()


def _h_window_menu(page: Any, label: str) -> None:
    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
    page.locator(".desk-verbbar-menu").wait_for()
    page.locator(".desk-verbbar-menu [role^='menuitem']").filter(has_text=label).first.click()


def _h_to_front(page: Any, name: str) -> None:
    """Window ▸ Chair ▸ name: picking an open Chair window brings it in front."""
    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
    page.locator(".desk-verbbar-menu").wait_for()
    sub = page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Desk')")
    sub.scroll_into_view_if_needed()
    sub.click()
    page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')").click()
    page.wait_for_timeout(300)


def _h_side_by_side(pw_browser: Any, left: Path, right: Path, out: Path) -> None:
    """One shot of two: the two contexts' shots drawn side by side."""
    def uri(path: Path) -> str:
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()

    page = pw_browser.new_page(viewport={"width": 2900, "height": 960}, device_scale_factor=0.5)
    page.set_content(
        "<body style='margin:0;background:#222;display:flex;gap:20px;padding:20px;font:14px sans-serif;color:#ddd'>"
        f"<figure style='margin:0'><figcaption>context A</figcaption><img src='{uri(left)}' width=1440></figure>"
        f"<figure style='margin:0'><figcaption>context B (fresh load)</figcaption><img src='{uri(right)}' width=1440></figure>"
        "</body>")
    page.wait_for_timeout(300)
    page.screenshot(path=str(out), full_page=True)
    page.close()


class TestHubWindows:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=H_TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, browser: Any, width: int, *, onboard: bool = False) -> tuple[Any, Any, list[str]]:
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(T)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        # Every window write this view sends to the hub, in order (evidence).
        sent: list[str] = []
        page.on("request", lambda r: sent.append(
            f"{r.url.split('/api/desk/windows', 1)[1] or '/'} {r.post_data or ''}")
            if "/api/desk/windows" in r.url and r.method == "POST" else None)
        page.hub_writes = sent  # type: ignore[attr-defined]
        page.goto(f"{self.base}/?token={H_TOKEN}", wait_until="load")
        if onboard:
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=H_TOKEN)
            page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return ctx, page, errors

    def _rows(self, page: Any) -> dict[str, dict[str, Any]]:
        listed = _api(page, "GET", "/api/desk/windows", token=H_TOKEN)
        return {w["id"]: w for w in listed["windows"]}

    def test_shell_s678_real_hub_geometry_and_faces(self) -> None:
        """S6/S7/S8: the settled shell survives the real Hub and two widths."""
        from playwright.sync_api import sync_playwright

        # The manifest door is labelled Ask AI; the hosted window's identity
        # is the shorter settled title "Ask" (AskPanel owns that title).
        apps = ("Today", "Meetings", "People", "Agents", "Speak", "Ask")
        # The registry's ⌘I primary modifier accepts Control on this Linux
        # Chromium runner; the live key remains ⌘I in the rendered menu.
        keys = ("Control+1", "Control+2", "Control+3", "Control+4", "Control+5", "Control+KeyI")

        def windows(page: Any) -> dict[str, dict[str, Any]]:
            return {row["name"]: row for row in page.evaluate(SHELL_GEOMETRY_JS)}

        def head_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
            lx, ly, lw, lh = left["head"]
            rx, ry, rw, rh = right["head"]
            return lx < rx + rw and rx < lx + lw and ly < ry + rh and ry < ly + lh

        def open_settings(page: Any) -> None:
            page.locator(".desk-mark").click()
            # The desktop row's accessible name includes its keycap.
            page.get_by_role("menu", name="HoldSpeak").get_by_role("menuitem", name=re.compile(r"^Settings(?:\s|$)")).click()
            page.locator(".desk-window-shell[aria-label^='Settings']").wait_for(timeout=T)

        def focus_window(page: Any, name: str) -> None:
            page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
            menu = page.get_by_role("menu", name="Window")
            menu.wait_for()
            menu.locator("[role='menuitemcheckbox']").filter(has_text=name).first.click()
            page.wait_for_timeout(350)

        def resize(page: Any, name: str, dx: float, dy: float) -> None:
            grip = page.locator(f".desk-window-shell[aria-label='{name}'] .desk-window-grip")
            box = grip.bounding_box()
            assert box, f"no resize grip for {name}"
            x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            page.mouse.move(x, y)
            page.mouse.down()
            page.mouse.move(x + dx / 2, y + dy / 2, steps=5)
            page.mouse.move(x + dx, y + dy, steps=5)
            page.mouse.up()
            page.wait_for_timeout(500)

        def reachable(page: Any, rows: dict[str, dict[str, Any]], *, check_icon_column: bool = True) -> list[str]:
            band = page.evaluate(H_BAND_JS)
            icon_right = page.evaluate(W_ICONS_JS)
            bad: list[str] = []
            for name, row in rows.items():
                x, y, w, h = row["rect"]
                hx, hy, hw, hh = row["head"]
                if x < band["x"] or y < band["y"] or x + w > band["x"] + band["w"] + 2 or y + h > band["y"] + band["h"] + 2:
                    bad.append(f"{name}: outside work band {row['rect']} / {band}")
                if (check_icon_column and hx < icon_right - 1) or not row["reachable"] or hw <= 0 or hh <= 0:
                    bad.append(f"{name}: head unreachable or in icon column {row} / icon-right={icon_right}")
            return bad

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx_a = ctx_c = None
            a = c = None
            errors_a: list[str] = []
            errors_c: list[str] = []
            try:
                ctx_a, a, errors_a = self._page(browser, 1440, onboard=True)
                # The case starts at the real Hub's seeded desk, then crosses
                # the same clear boundary as the other Hub proof. The next
                # load has no local second ledger to mask server placement.
                clear_hub_windows(a, H_TOKEN)
                a.reload(wait_until="load")
                _normal_chair(a)
                _settle(a)

                for key, name in zip(keys, apps):
                    # Press against the document body. Speak may leave its
                    # editor focused, but the shell keymap remains global.
                    a.locator("body").press(key)
                    a.locator(f".desk-window-shell[aria-label='{name}']").wait_for(timeout=T)
                    a.wait_for_timeout(350)
                rows = windows(a)
                assert set(apps) <= set(rows), {"open": sorted(rows), "wanted": apps}
                assert rows["Meetings"]["rect"][2] >= 640
                assert rows["Speak"]["rect"][2] >= 560
                assert rows["Today"]["rect"][2] > 0 and rows["Ask"]["rect"][3] > 0

                # S8's live menu is read from the rendered rows. Its first
                # eight rows are the settled plain order, followed by the
                # separator and open-window list.
                a.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                menu = a.get_by_role("menu", name="Window")
                menu.wait_for()
                menu_labels = menu.locator(":scope > [role^='menuitem'] .desk-menu-label").all_text_contents()
                assert menu_labels[:8] == ["Minimize", "Zoom", "Tile left", "Tile right", "Arrange all", "Overview", "Next window", "Close"], menu_labels
                assert all(old not in menu_labels for old in ("Iconify", "Cycle windows", "Cascade", "Reset layout")), menu_labels
                assert all(name in menu_labels for name in apps), {"labels": menu_labels, "apps": apps}
                a.screenshot(path=str(SHELL_SHOTS / "shell-window-menu-1440.png"))
                a.keyboard.press("Escape")
                _h_window_menu(a, "Arrange all")
                _settle(a)
                rows = _h_until(lambda: windows(a), lambda value: set(apps) <= set(value))
                bad = reachable(a, {name: rows[name] for name in apps}, check_icon_column=False)
                assert not bad, {"bad": bad, "rows": rows}
                a.screenshot(path=str(SHELL_SHOTS / "shell-windows-1440.png"))

                # Persist a deliberately colliding People rect. A reload
                # clears the per-session owner set; the head-only placement
                # rule must then reseat it while retaining its size.
                people_before = windows(a)["People"]
                meetings_before = windows(a)["Meetings"]
                # Move the target away from the top snap zone first. The
                # second real drag then creates a head collision without a
                # snap gesture consuming the release.
                focus_window(a, "Meetings")
                _h_drag(a, ".desk-window-shell[aria-label='Meetings'] .desk-pullout-title", 300, 250)
                meetings_collision = windows(a)["Meetings"]
                focus_window(a, "People")
                _h_drag(a, ".desk-window-shell[aria-label='People'] .desk-pullout-title",
                        meetings_collision["rect"][0] + 10 - people_before["rect"][0],
                        meetings_collision["rect"][1] + 10 - people_before["rect"][1])
                a.wait_for_timeout(500)
                collided = windows(a)
                assert head_overlap(collided["People"], collided["Meetings"]), collided
                a.locator(".desk-window-shell[aria-label='People'] [aria-label='Close People']").click()
                a.locator(".desk-window-shell[aria-label='People']").wait_for(state="detached", timeout=T)
                a.reload(wait_until="load")
                _normal_chair(a)
                a.keyboard.press("Control+3")
                a.locator(".desk-window-shell[aria-label='People']").wait_for(timeout=T)
                reseated = _h_until(lambda: windows(a), lambda value: "People" in value and "Meetings" in value)
                assert not head_overlap(reseated["People"], reseated["Meetings"]), reseated
                assert reseated["People"]["rect"][2:] == collided["People"]["rect"][2:], {"before": collided["People"], "after": reseated["People"]}
                assert reachable(a, {"People": reseated["People"], "Meetings": reseated["Meetings"]}) == []
                a.screenshot(path=str(SHELL_SHOTS / "shell-remembered-1440.png"))

                # A resize is an owner decision for this session. Move
                # Meetings over the resized People head, close and reopen
                # People, and prove that the deliberate rect remains exact.
                # Arrange through the real Hub first so both windows have
                # room for the collision; the lower work-band clamp must
                # not consume the test's drag. This does not mark a local
                # pointer resize in the new browser session.
                band = a.evaluate(H_BAND_JS)
                before_resize = windows(a)["People"]["rect"]
                _api(a, "POST", "/api/desk/windows/arrange", {"rects": {
                    "surface-people": {
                        "x": f"-1/2 + {before_resize[0] - band['x']}",
                        "y": "-1/2 + 80", "w": before_resize[2], "h": before_resize[3],
                    },
                }}, token=H_TOKEN)
                _h_until(lambda: windows(a), lambda value: value["People"]["rect"][1] == round(band["y"] + 80))
                focus_window(a, "People")
                before_resize = windows(a)["People"]["rect"]
                resize(a, "People", 110, 70)
                owner_rect = windows(a)["People"]["rect"]
                assert owner_rect[3] >= before_resize[3] + 20, {"before": before_resize, "resized": owner_rect}
                owner_hub_row = self._rows(a)["surface-people"]
                current_meetings = windows(a)["Meetings"]["rect"]
                focus_window(a, "Meetings")
                _h_drag(a, ".desk-window-shell[aria-label='Meetings'] .desk-pullout-title",
                        owner_rect[0] + 10 - current_meetings[0], owner_rect[1] + 20 - current_meetings[1])
                a.wait_for_timeout(400)
                assert head_overlap(windows(a)["People"], windows(a)["Meetings"])
                focus_window(a, "People")
                a.locator(".desk-window-shell[aria-label='People'] [aria-label='Close People']").click()
                a.locator(".desk-window-shell[aria-label='People']").wait_for(state="detached", timeout=T)
                a.keyboard.press("Control+3")
                a.locator(".desk-window-shell[aria-label='People']").wait_for(timeout=T)
                _settle(a)
                owner_reopened = _h_until(lambda: windows(a), lambda value: "People" in value and "Meetings" in value)
                (SHELL_SHOTS / "shell-owner-reopen-observation.json").write_text(json.dumps({
                    "before_resize": before_resize, "owner_rect": owner_rect,
                    "owner_hub_row": owner_hub_row, "reopened": owner_reopened["People"],
                    "reopened_hub_row": self._rows(a)["surface-people"],
                    "saved_rects": a.evaluate("JSON.parse(localStorage.getItem('hs.desk.workspace.v1')).panel.rects"),
                }, indent=2) + "\n")
                assert owner_reopened["People"]["rect"] == owner_rect, {"owner": owner_rect, "reopened": owner_reopened["People"]}

                # Arrange all uses the live order and keeps the owner's sizes.
                open_project_drawer(a, self.base, "p-ledger", H_TOKEN)
                _normal_chair(a)
                a.locator(".drawer-window").first.wait_for(timeout=T)
                # The real project title loads after its window shell. Read
                # order only after that identity settles, so Arrange all is
                # compared with the same named windows on both sides.
                a.locator(".desk-window-shell[aria-label='Payments ledger cutover']").wait_for(timeout=T)
                before_arrange = windows(a)
                before_order = [row["name"] for row in sorted(before_arrange.values(), key=lambda row: row["z"])]
                _h_window_menu(a, "Arrange all")
                _settle(a)
                after_arrange = _h_until(lambda: windows(a), lambda value: all(name in value for name in before_arrange))
                (SHELL_SHOTS / "shell-arrange-observation.json").write_text(json.dumps({
                    "before": before_arrange, "after": after_arrange, "order": before_order,
                    "band": a.evaluate(H_BAND_JS),
                }, indent=2) + "\n")
                assert not reachable(a, after_arrange, check_icon_column=False), reachable(a, after_arrange, check_icon_column=False)
                assert [row["name"] for row in sorted(after_arrange.values(), key=lambda row: row["z"])] == before_order
                for name, before in before_arrange.items():
                    assert after_arrange[name]["rect"][2:] == before["rect"][2:], {"name": name, "before": before, "after": after_arrange[name]}
                a.screenshot(path=str(SHELL_SHOTS / "shell-needs-1440.png"))

                # The Needs window is still clear and its title bar remains
                # out of the left drawer/icon column after the cascade.
                _h_open(a, "Needs you")
                a.wait_for_timeout(300)
                needs = windows(a)
                assert "Needs you" in needs, sorted(needs)
                assert reachable(a, {"Needs you": needs["Needs you"]}) == []
                needs_answer = _api(a, "GET", "/api/desk/needs-you?fresh=1", token=H_TOKEN)
                headline = a.locator(".desk-window-shell[aria-label='Needs you'] [data-testid='arrival-display']")
                headline.wait_for(timeout=T)
                count = int(needs_answer["count"])
                expected_heads = [f"{count} {'needs' if count == 1 else 'need'} you"] if count else ["Nothing needs you", "Coverage incomplete"]
                _h_until(headline.inner_text, lambda value: value in expected_heads)
                assert headline.inner_text() in expected_heads, {"head": headline.inner_text(), "needs": needs_answer}

                # S6: the one Wallpaper home opens Settings at Desk, then
                # selects Jupiter. The floor labels are measured in the live
                # scene so the 4.5:1 claim is not a token-only assertion.
                open_settings(a)
                a.get_by_test_id("settings-index-desk").click()
                a.locator("[data-atmosphere-choice='jupiter-orbit']").wait_for(timeout=T)
                a.locator("[data-atmosphere-choice='jupiter-orbit']").click()
                a.locator("[data-atmosphere-choice='jupiter-orbit'][aria-checked='true']").wait_for(timeout=T)
                assert a.get_by_text("In Jupiter's orbit", exact=True).count() >= 1
                contrast = a.evaluate(SHELL_LABEL_CONTRAST_JS)
                assert contrast and min(float(row["ratio"]) for row in contrast) >= 4.5, contrast
                a.screenshot(path=str(SHELL_SHOTS / "shell-jupiter-1440.png"))

                ctx_c, c, errors_c = self._page(browser, 393)
                open_settings(c)
                settings_index = c.get_by_role("navigation", name="Settings sections")
                index_labels = settings_index.locator(".btn").all_text_contents()
                assert "Wallpaper" not in index_labels, index_labels
                c.screenshot(path=str(SHELL_SHOTS / "shell-settings-393.png"))
                (SHELL_SHOTS / "shell-window-proof.json").write_text(json.dumps({
                    "apps_1440": {name: rows[name] for name in apps},
                    "remembered": {"collided": collided["People"], "reseated": reseated["People"]},
                    "owner_resize": {"owner": owner_rect, "reopened": owner_reopened["People"]},
                    "arrange_all_order": before_order,
                    "wallpaper_contrast": contrast,
                    "settings_index_393": index_labels,
                }, indent=2) + "\n")
                assert errors_a == [], errors_a
                assert errors_c == [], errors_c
            finally:
                if ctx_c is not None:
                    ctx_c.close()
                if ctx_a is not None:
                    ctx_a.close()
                browser.close()

    def test_one_desk_two_views(self) -> None:
        """replaces: tests/e2e/test_philo16_hub_windows_glass.py::TestHubWindows::test_one_desk_two_views (moved whole)."""
        from playwright.sync_api import sync_playwright

        from holdspeak.mcp import tools as mcp_tools
        from holdspeak.principals import Principal, PrincipalKind

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                # ── B1: context A opens three, drags one, seats one ─────────
                ctx_a, a, errors_a = self._page(browser, 1440, onboard=True)
                # Capture first (dragged), then Needs you, then Meetings in
                # front, which he iconifies.
                _h_open(a, "Capture")
                a.wait_for_timeout(500)
                _h_drag(a, ".desk-window-shell[aria-label='Capture'] .desk-pullout-title", -160, 70)
                a.wait_for_timeout(400)
                _h_open(a, "Needs you")
                _h_open(a, "Meetings")
                a.wait_for_timeout(300)
                _h_window_menu(a, "Minimize")
                rows = _h_until(lambda: self._rows(a), lambda r: (
                    set(H_IDS.values()) <= set(r) and r["surface-meetings"]["minimized"] and r["chair:capture"]["arranged"]))
                if not set(H_IDS.values()) <= set(rows):
                    fails["B1 the hub holds the three windows"] = sorted(rows)
                else:
                    if not rows["surface-meetings"]["minimized"]:
                        fails["B1 Meetings is seated on the hub"] = rows["surface-meetings"]
                    capture = rows["chair:capture"]
                    if not capture["arranged"] or not all(isinstance(capture[k], str) and "%" in capture[k] for k in "xywh"):
                        fails["B1 Capture's rect is share+px on the hub"] = capture
                (H_SHOTS / "hub-rows.json").write_text(json.dumps(
                    _api(a, "GET", "/api/desk/windows", token=H_TOKEN), indent=2) + "\n")
                wins_a = _h_wins(a)
                a.screenshot(path=str(H_SHOTS / "1440-A.png"))

                # ── B2: context B, a fresh load, shows the same desk ────────
                ctx_b, b, errors_b = self._page(browser, 1440)
                wins_b = _h_until(lambda: _h_wins(b), lambda w: {"Capture", "Needs you"} <= set(w))
                if not {"Capture", "Needs you"} <= set(wins_b):
                    fails["B2 B shows the open windows"] = sorted(wins_b)
                if "Meetings" in wins_b:
                    fails["B2 Meetings is seated in B (not on the glass)"] = wins_b["Meetings"]
                if "Capture" in wins_a and "Capture" in wins_b and wins_a["Capture"]["rect"] != wins_b["Capture"]["rect"]:
                    fails["B2 Capture at the same rect in A and B"] = {"A": wins_a["Capture"]["rect"], "B": wins_b["Capture"]["rect"]}
                fronts = {label: [n for n, w in wins.items() if w["plane"] == "front"]
                          for label, wins in (("A", wins_a), ("B", wins_b))}
                if fronts["A"] != fronts["B"] or len(fronts["A"]) != 1:
                    fails["B2 one front, the same in A and B"] = fronts
                cache_b = b.evaluate(H_CACHE_JS)
                if "surface-meetings" not in cache_b["min"] or any(H_IDS[n] in cache_b["closed"] for n in H_THREE):
                    fails["B2 B's cache is the hub's rows"] = cache_b
                b.screenshot(path=str(H_SHOTS / "1440-B.png"))
                _h_side_by_side(browser, H_SHOTS / "1440-A.png", H_SHOTS / "1440-B.png", H_SHOTS / "1440-A-and-B.png")

                # ── B3: B raises A's near window; A follows ─────────────────
                planes_a = {n: w["plane"] for n, w in _h_wins(a).items()}
                near = next((n for n, p in planes_a.items() if p == "near"), None)
                if near is None:
                    fails["B3 A has a near window"] = planes_a
                else:
                    _h_to_front(b, near)
                    followed = _h_until(lambda: _h_wins(a), lambda w: w.get(near, {}).get("plane") == "front")
                    if followed.get(near, {}).get("plane") != "front":
                        fails["B3 A follows B's raise without a reload"] = {
                            n: w["plane"] for n, w in followed.items()}
                    a.screenshot(path=str(H_SHOTS / "1440-A-follows-B.png"))

                # ── B4: an agent tiles two through MCP; both views follow ───
                owner = Principal(PrincipalKind.OWNER, "philo16-owner")
                a_before, b_before = len(a.hub_writes), len(b.hub_writes)
                mcp_tools.dispatch("desk_window.arrange", {"rects": {
                    "chair:capture": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"},
                    "chair:needs": {"x": "0%", "y": "-1/2", "w": "1/2", "h": "100%"},
                }}, owner)
                band = a.evaluate(H_BAND_JS)
                half = band["w"] / 2

                def tiled(w: dict[str, Any]) -> bool:
                    if "Capture" not in w or "Needs you" not in w:
                        return False
                    bx, _, bw, _ = w["Capture"]["rect"]
                    nx, _, nw, _ = w["Needs you"]["rect"]
                    return abs(bx - band["x"]) <= 2 and abs(bw - half) <= 3 and abs(nx - (band["x"] + half)) <= 3

                for label, page in (("A", a), ("B", b)):
                    seen = _h_until(lambda: _h_wins(page), tiled)
                    if not tiled(seen):
                        fails[f"B4 {label} shows the agent's tile"] = {
                            n: w["rect"] for n, w in seen.items()} | {"band": band}
                a.wait_for_timeout(800)  # a follow settles (SETTLE_MS) and must send nothing
                echoes = a.hub_writes[a_before:] + b.hub_writes[b_before:]
                if echoes:
                    fails["B4 following the agent's tile writes nothing back"] = echoes
                a.screenshot(path=str(H_SHOTS / "1440-A-tile.png"))
                b.screenshot(path=str(H_SHOTS / "1440-B-tile.png"))
                _h_side_by_side(browser, H_SHOTS / "1440-A-tile.png", H_SHOTS / "1440-B-tile.png",
                              H_SHOTS / "1440-A-and-B-tile.png")

                # ── B5: 393, a fresh load: the same set, the same seat ──────
                ctx_c, c, errors_c = self._page(browser, 393)
                cache_c = _h_until(lambda: c.evaluate(H_CACHE_JS), lambda v: "surface-meetings" in v["min"])
                if "surface-meetings" not in cache_c["min"] or any(H_IDS[n] in cache_c["closed"] for n in H_THREE):
                    fails["B5 393 holds the hub's set and seat"] = cache_c
                c.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                c.locator(".desk-verbbar-menu").wait_for()
                checked = {}
                for name in ("Capture", "Needs you"):
                    row = c.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')").first
                    checked[name] = row.get_attribute("aria-checked") if row.count() else None
                if any(value != "true" for value in checked.values()):
                    fails["B5 393 Go lists the open Chair windows"] = checked
                # Betterment daily D5: Brief and The week are part of Today;
                # Go offers neither, and Today is its own row.
                go_menu = c.locator(".desk-verbbar-menu")
                retired = [n for n in ("Brief", "The week") if go_menu.locator(".desk-menu-label", has_text=re.compile(rf"^{n}$")).count()]
                if retired or not go_menu.get_by_role("menuitem", name="Today", exact=True).count():
                    fails["B5 393 Go offers Today, not Brief or The week"] = retired
                c.screenshot(path=str(H_SHOTS / "393-C-go-chair.png"))
                c.keyboard.press("Escape")

                # ── B6 (Astra r1 M4): a Project drawer follows into a fresh view ──
                open_project_drawer(a, self.base, 'p-ledger', H_TOKEN)  # PHILO-17 U30: the parked drawer, by its key
                _normal_chair(a)
                a.locator(".drawer-window").first.wait_for(timeout=T)
                drawer_row = _h_until(lambda: self._rows(a), lambda r: "drawer:project:p-ledger" in r)
                if drawer_row.get("drawer:project:p-ledger", {}).get("object_ref") != "project:p-ledger":
                    fails["B6 the hub holds A's Project drawer"] = sorted(drawer_row)
                ctx_d, d, errors_d = self._page(browser, 1440)
                try:
                    d.locator(".drawer-window").first.wait_for(timeout=10_000)
                except Exception:
                    fails["B6 a fresh view shows A's Project drawer"] = sorted(_h_wins(d))
                d.wait_for_timeout(800)
                if d.hub_writes:
                    fails["B6 a fresh load writes nothing to the hub"] = d.hub_writes
                d.screenshot(path=str(H_SHOTS / "1440-D-drawer.png"))
                if errors_d:
                    fails["page errors D"] = errors_d
                ctx_d.close()

                # ── B7 (Astra r2 M3): the agent lane follows on its launch ──
                # The lane is opened on the hub (as an agent or another view
                # would): A, live, follows the frame; a fresh view E shows it.
                # The owner's own open sending launch:<id> is fenced in vitest.
                _api(a, "POST", "/api/desk/windows/lane/open", {"object_ref": "launch:L-glass"}, token=H_TOKEN)
                lane_sel = ".desk-window-shell.is-lane"
                try:
                    a.locator(lane_sel).first.wait_for(timeout=10_000)
                except Exception:
                    fails["B7 A follows the lane opened on the hub"] = sorted(_h_wins(a))
                lane_row = self._rows(a).get("lane", {})
                if lane_row.get("object_ref") != "launch:L-glass":
                    fails["B7 the lane's row names its launch"] = lane_row
                ctx_e, e, errors_e = self._page(browser, 1440)
                try:
                    e.locator(lane_sel).first.wait_for(timeout=10_000)
                except Exception:
                    fails["B7 a fresh view shows the lane"] = sorted(_h_wins(e))
                e.screenshot(path=str(H_SHOTS / "1440-E-lane.png"))
                e.wait_for_timeout(800)
                lane_writes_e = list(e.hub_writes)
                if lane_writes_e:
                    fails["B7 a fresh load writes nothing to the hub"] = lane_writes_e
                ctx_e.close()

                (H_SHOTS / "hub-writes.json").write_text(json.dumps(
                    {"A": a.hub_writes, "B": b.hub_writes, "C": c.hub_writes, "E": lane_writes_e}, indent=2) + "\n")
                if c.hub_writes:
                    fails["B5 a 393 load writes nothing to the hub"] = c.hub_writes
                rows_end = self._rows(a)
                (H_SHOTS / "hub-rows-end.json").write_text(json.dumps(rows_end, indent=2) + "\n")
                for label, errors in (("A", errors_a), ("B", errors_b), ("C", errors_c)):
                    if errors:
                        fails[f"page errors {label}"] = errors
                for ctx in (ctx_a, ctx_b, ctx_c):
                    ctx.close()
            finally:
                browser.close()
        assert not fails, json.dumps(fails, indent=2, default=str)


# ── PHILO-17 windows open well and come back as themselves (moved whole: three views, drags, no bounce) ──
W_TOKEN = "philo17-windows"
W_SHOTS = evidence_dir("docs/internal/philo/phase-17/windows-shots")

# Every window shell (shown or not: at 393 only the front sheet shows).
W_ALL_JS = r"""() => [...document.querySelectorAll('.desk-window-shell:not([data-departing])')]
  .map((s) => s.getAttribute('aria-label'))"""

W_WINS_JS = r"""() => {
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  return [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible).map((s) => {
    const r = s.getBoundingClientRect();
    return {name: s.getAttribute('aria-label'),
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]}; });
}"""

# The right edge of the desk's left icon columns (icons outside windows and
# the Dock), or 0 when the desk shows none: the icons at the left edge, then
# each placed icon that starts right beside them (a second drawer column).
W_ICONS_JS = r"""() => {
  const icons = [...document.querySelectorAll('.desk-icon')]
    .filter((e) => !e.closest('.desk-window, .desk-dock'))
    .map((e) => ({r: e.getBoundingClientRect(), placed: !!e.closest('.desk-screen-placed')}))
    .filter(({r}) => r.width > 0);
  let right = 0, edge = 60;
  for (let col = 0; ; col++) {
    const next = Math.max(right, ...icons.filter(({r, placed}) => r.left <= edge && (col === 0 || placed)).map(({r}) => r.right));
    if (next <= right) return right;
    right = next; edge = right + 24;
  }
}"""

# A point on the title bar of window `name` that hits the bar itself (not a
# tab, a gadget or the title): the empty part of the bar.
W_EMPTY_BAR_JS = r"""(name) => {
  const shell = [...document.querySelectorAll('.desk-window-shell')].find((s) => s.getAttribute('aria-label') === name);
  const head = shell && shell.querySelector('.desk-window-handle');
  if (!head) return null;
  // The middle of the longest stretch of bare bar (not the gap beside a gadget).
  const b = head.getBoundingClientRect();
  const y = b.top + b.height / 2;
  let best = null, run = null;
  for (let x = b.left + 2; x < b.right - 2; x += 2) {
    if (document.elementFromPoint(x, y) === head) {
      run = run || {from: x, to: x}; run.to = x;
      if (!best || run.to - run.from > best.to - best.from) best = {...run};
    } else run = null;
  }
  if (!best || best.to - best.from < 12) return null;
  return {x: (best.from + best.to) / 2, y, width: best.to - best.from, tabs: head.querySelectorAll('[role=tab]').length};
}"""


def _w_until(probe: Callable[[], Any], ok: Callable[[Any], bool], seconds: float = 8.0) -> Any:
    deadline = time.monotonic() + seconds
    value = probe()
    while not ok(value) and time.monotonic() < deadline:
        time.sleep(0.25)
        value = probe()
    return value


def _w_wins(page: Any) -> dict[str, list[int]]:
    _settle(page)
    return {w["name"]: w["rect"] for w in page.evaluate(W_WINS_JS)}


def _w_near(a: list[int], b: list[int], px: int = 2) -> bool:
    return all(abs(x - y) <= px for x, y in zip(a, b))


class TestWindowsOpenWell:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=W_TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, browser: Any, width: int, *, onboard: bool = False) -> tuple[Any, Any, list[str]]:
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(T)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        # Every window write this view sends to the hub (a follower sends none).
        sent: list[str] = []
        page.on("request", lambda r: sent.append(r.url.split("/api/desk/windows", 1)[1])
                if "/api/desk/windows" in r.url and r.method == "POST" else None)
        page.hub_writes = sent  # type: ignore[attr-defined]
        page.goto(f"{self.base}/?token={W_TOKEN}", wait_until="load")
        if onboard:
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=W_TOKEN)
            page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return ctx, page, errors

    def test_windows_open_clear_and_come_back(self) -> None:
        """replaces: tests/e2e/test_philo17_windows_glass.py::TestWindowsOpenWell::test_windows_open_clear_and_come_back (moved whole)."""
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                # ── W1: two apps from their doors ───────────────────────────
                # PHILO-17 (doors): Meetings from the Dock, People from its
                # desk drawer.
                ctx_a, a, errors_a = self._page(browser, 1440, onboard=True)
                a.locator(".desk-dock button").filter(has_text="Meetings").first.click()
                a.wait_for_timeout(900)
                a.locator(".desk-dock [data-app='surface-people']").click()
                a.wait_for_timeout(900)
                wins = _w_until(lambda: _w_wins(a), lambda w: {"Meetings", "People"} <= set(w))
                icons = a.evaluate(W_ICONS_JS)
                if not {"Meetings", "People"} <= set(wins):
                    fails["W1 Meetings and People open"] = sorted(wins)
                else:
                    meetings, people = wins["Meetings"], wins["People"]
                    if meetings[:2] == people[:2]:
                        fails["W1 the two do not sit on each other"] = wins
                    for name in ("Meetings", "People"):
                        if icons and wins[name][0] < icons:
                            fails[f"W1 {name} clear of the icon column"] = {"rect": wins[name], "icons_right": icons}
                    # S7 keeps its declared width and fits the two records
                    # below the preferred height, without trapping a row.
                    body = a.locator("#surface-meetings .desk-surface-body")
                    fits = body.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
                    if meetings[2] != 720 or not 220 <= meetings[3] < 600 or not fits:
                        fails["W1 Meetings fits its two records at the declared width"] = {"rect": meetings, "fits": fits}
                a.screenshot(path=str(W_SHOTS / "1440-two-apps.png"))

                # ── W2: drag a tabbed app by the empty part of its bar ─────
                # Meetings is brought to the front first (a press on its
                # title). A drag that starts on a window BEHIND another moved
                # nothing in 2 of 5 runs here: reported, not fenced yet.
                a.locator(".desk-window-shell[aria-label='Meetings'] .desk-pullout-title").first.click()
                a.wait_for_timeout(400)
                spot = a.evaluate(W_EMPTY_BAR_JS, "Meetings")
                if not spot:
                    fails["W2 Meetings' bar has an empty part"] = None
                else:
                    before = _w_wins(a).get("Meetings")
                    a.mouse.move(spot["x"], spot["y"])
                    a.mouse.down()
                    a.mouse.move(spot["x"] + 30, spot["y"] + 40, steps=8)
                    a.mouse.up()
                    a.wait_for_timeout(500)
                    after = _w_wins(a).get("Meetings")
                    if not before or not after or after[:2] == before[:2]:
                        fails["W2 the empty bar drags (U28b)"] = {"before": before, "after": after, "tabs": spot["tabs"],
                                                                  "spot": spot, "wins": _w_wins(a)}

                # ── W3: the Room of one project ────────────────────────────
                # PHILO-17 U30 (#1068): opening a Project opens its Room.
                a.get_by_role("button", name=f"{ROOM}, PROJECT").first.dblclick()
                _room_opened(a)
                wins_a = _w_until(lambda: _w_wins(a), lambda w: ROOM in w)
                if ROOM not in wins_a or "Desk memory" in wins_a:
                    fails["W3 the Room is named by its project"] = sorted(wins_a)
                # These are now owner-arranged rectangles. A fresh view must
                # follow them exactly, including a content-sized reader.
                _c_window_menu(a, "Arrange all")
                _settle(a)
                a.wait_for_timeout(1200)  # the writes reach the hub (keepalive)
                wins_a = _w_wins(a)
                a.screenshot(path=str(W_SHOTS / "1440-A.png"))

                # ── W4: a reload keeps the windows and their places ─────────
                a.reload(wait_until="load")
                _normal_chair(a)
                reloaded = _w_until(lambda: _w_wins(a), lambda w: set(w) == set(wins_a))
                if set(reloaded) != set(wins_a):
                    fails["W4 the same windows after a reload"] = {"before": sorted(wins_a), "after": sorted(reloaded)}
                moved = {n: [wins_a[n], r] for n, r in reloaded.items() if n in wins_a and not _w_near(wins_a[n], r)}
                if moved:
                    fails["W4 the same places after a reload"] = moved
                a.screenshot(path=str(W_SHOTS / "1440-A-reloaded.png"))

                # ── W5: another view, a fresh load ──────────────────────────
                ctx_b, b, errors_b = self._page(browser, 1440)
                wins_b = _w_until(lambda: _w_wins(b), lambda w: set(w) == set(wins_a))
                if set(wins_b) != set(wins_a) or "Desk memory" in wins_b:
                    fails["W5 B shows the same windows (the Room as the Room)"] = {"A": sorted(wins_a), "B": sorted(wins_b)}
                moved = {n: [wins_a[n], r] for n, r in wins_b.items() if n in wins_a and not _w_near(wins_a[n], r)}
                if moved:
                    fails["W5 B shows them at the same places"] = moved
                b.screenshot(path=str(W_SHOTS / "1440-B-fresh.png"))

                # ── W5b: both views open; A moves the Room, B follows live ──
                # (Astra r1 on #1070): no reload; B writes nothing; nothing
                # bounces back in either view. The Room is A's front window.
                b_writes = len(b.hub_writes)
                start = _w_wins(a).get(ROOM)
                spot = a.evaluate(W_EMPTY_BAR_JS, ROOM)
                if not start or not spot:
                    fails["W5b the Room's bar is on A's glass"] = {"wins": sorted(_w_wins(a)), "spot": spot}
                else:
                    a.mouse.move(spot["x"], spot["y"])
                    a.mouse.down()
                    a.mouse.move(spot["x"] + 60, spot["y"] + 50, steps=10)
                    a.mouse.up()
                    moved_a = _w_until(lambda: _w_wins(a).get(ROOM), lambda r: bool(r) and r[:2] != start[:2])
                    seen_b = _w_until(lambda: _w_wins(b).get(ROOM), lambda r: bool(r) and bool(moved_a) and _w_near(r, moved_a))
                    if not moved_a or moved_a[:2] == start[:2]:
                        fails["W5b A moved the Room"] = {"start": start, "after": moved_a}
                    elif not seen_b or not _w_near(seen_b, moved_a):
                        fails["W5b B shows the Room where A put it"] = {"A": moved_a, "B": seen_b}
                    a.wait_for_timeout(1500)
                    later_a, later_b = _w_wins(a).get(ROOM), _w_wins(b).get(ROOM)
                    if moved_a and (not later_a or not _w_near(later_a, moved_a) or not later_b or not _w_near(later_b, moved_a)):
                        fails["W5b nothing bounces back"] = {"moved": moved_a, "A later": later_a, "B later": later_b}
                    if len(b.hub_writes) != b_writes:
                        fails["W5b B (a follower) writes nothing"] = b.hub_writes[b_writes:]
                b.screenshot(path=str(W_SHOTS / "1440-B-follows-A.png"))

                # ── W6: the phone, a fresh load ─────────────────────────────
                ctx_c, c, errors_c = self._page(browser, 393)
                names_c = _w_until(lambda: set(c.evaluate(W_ALL_JS)), lambda n: set(wins_a) <= n)
                if not set(wins_a) <= names_c or "Desk memory" in names_c:
                    fails["W6 the phone holds the same windows"] = {"A": sorted(wins_a), "C": sorted(names_c)}
                c.screenshot(path=str(W_SHOTS / "393-C-fresh.png"))

                errors = errors_a + errors_b + errors_c
                if errors:
                    fails["no page errors"] = errors[:5]
                for ctx in (ctx_a, ctx_b, ctx_c):
                    ctx.close()
            finally:
                browser.close()
        assert not fails, fails


# ── A window's title is the name of the thing in it (moved whole: at 393 the name takes the clock's width) ──
N_TOKEN = "window-names-glass"
N_SHOTS = evidence_dir("tests/e2e/shots/window-names")
N_PROJECT = "Payments ledger cutover"

# How much of the name the screen title paints: the characters that fit its
# box in its own font (the rest is the ellipsis).
N_NAME_FACTS = """() => {
  const e = document.querySelector('.desk-screen-name'); if (!e) return null;
  const cs = getComputedStyle(e); const text = e.textContent.trim();
  const c = document.createElement('canvas').getContext('2d'); c.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
  const box = e.clientWidth; let shown = text.length;
  if (c.measureText(text).width > box + 0.5) { shown = 0;
    for (let n = text.length - 1; n > 0; n--) if (c.measureText(text.slice(0, n) + '…').width <= box + 0.5) { shown = n; break; } }
  const clock = document.querySelector('.desk-clock');
  const go = document.querySelector(".desk-verbbar-item[data-menu-id=go] button");
  const bar = document.querySelector('.desk-menubar').getBoundingClientRect();
  const r = e.getBoundingClientRect(); const g = go ? go.getBoundingClientRect() : null;
  const hit = g ? document.elementFromPoint(g.x + g.width / 2, g.y + g.height / 2) : null;
  return { text, box, shown, one_line: r.height < parseFloat(cs.fontSize) * 1.8, ellipsis: cs.textOverflow,
    clock: !!clock && clock.getBoundingClientRect().width > 0,
    go_whole: g ? (g.width >= 44 && g.height >= 44 && g.left >= bar.left && g.right <= bar.right + 0.5 && !!hit && go.contains(hit)) : false,
    bar_overflow: document.documentElement.scrollWidth > innerWidth,
    front: [...document.querySelectorAll('.desk-window-shell.is-front')].map((w) => w.getAttribute('aria-label')) };
}"""


class TestWindowNamesOnGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=N_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @pytest.mark.parametrize("width", [393, 1440])
    def test_the_project_room_is_named_by_its_project_and_393_shows_the_name(self, width: int) -> None:
        """replaces: tests/e2e/test_window_names_glass.py::TestWindowNamesOnGlass::test_the_project_room_is_named_by_its_project_and_393_shows_the_name (moved whole)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={N_TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=N_TOKEN)
                _api(page, "POST", "/api/projects", {"name": N_PROJECT}, token=N_TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(2500)
                _settle(page)

                # The Room, from the palette: `Open <project>`.
                self._press(page, page.locator("button[aria-controls=desk-tool-shelf]"), width)
                page.locator("input[aria-controls=desk-palette-listbox]").fill("Payments")
                row = page.get_by_role("option", name=f"Open {N_PROJECT}").first
                row.wait_for()
                self._press(page, row, width)
                _room_opened(page)
                room = page.locator("[id='surface-project-memory']")
                room.wait_for()
                page.wait_for_timeout(1200)
                _settle(page)

                # One name: the frame, and the screen title.
                assert room.get_attribute("aria-label") == N_PROJECT, room.get_attribute("aria-label")
                facts = page.evaluate(N_NAME_FACTS)
                N_SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(N_SHOTS / f"project-room-{width}.png"))
                (N_SHOTS / f"project-room-{width}.txt").write_text(f"{facts}\n")
                assert facts["text"] == N_PROJECT, facts
                assert N_PROJECT in facts["front"], facts
                assert facts["one_line"] and facts["ellipsis"] == "ellipsis", facts
                assert not facts["bar_overflow"], facts
                if width < 720:
                    # The ruling: the clock is gone while a window is in front,
                    # and the name shows more than `Pay…` (it showed 3 letters).
                    assert not facts["clock"], facts
                    assert facts["shown"] >= 10, facts
                    assert facts["box"] >= 100, facts
                    assert facts["go_whole"], facts  # the current navigator owns its touch target
                else:
                    assert facts["clock"], facts
                    assert facts["shown"] == len(N_PROJECT), facts
                assert errors == [], errors
            finally:
                browser.close()


# ══ lane e2e-high-1: close means gone; the desk remembers ════════════════════════════════════════

CLOSE_TOKEN = "philo13-05-close"

CLOSE_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-05-shots")

CLOSE_SIZES = {1440: 900, 393: 852}

def _close_control(page: Any, width: int, label: str, *, host: Any = None) -> Any:
    """The shared frame calls its compact gadget Back; unscoped Back closes."""
    return (host if host is not None else page).get_by_role(
        "button", name=f"Back from {label}" if width < 720 else f"Close {label}", exact=True)


def _on_the_desk(hit: dict[str, Any] | None) -> bool:
    """The old centre lands on the Desk. PHILO-13-11 (slice two): the Chair
    screen is now four windows (`chair:*`), so a hit on a Chair window is the
    Desk under the closed window; any other window is not."""
    return hit is not None and hit["desk"] and (
        hit["window"] is None or str(hit["window"]).startswith("chair:"))

CLOSE_DECISION = "Freeze the old ledger on Nov 5"

NOTE = "Arch review prep"

HIT_JS = """([x, y]) => {
  const e = document.elementFromPoint(x, y);
  if (!e) return null;
  const w = e.closest('.desk-window, .desk-pullout');
  const t = e.closest('[data-testid]');
  return {tag: e.tagName.toLowerCase(), cls: String(e.className || '').slice(0, 80),
          testid: t ? t.dataset.testid : null, window: w ? (w.id || String(w.className).slice(0, 60)) : null,
          desk: Boolean(e.closest('.desk-next'))};
}"""

OPEN_WINDOWS_JS = """() => [...document.querySelectorAll('.desk-window, .desk-pullout')]
  .filter(w => w.getBoundingClientRect().width > 0 && getComputedStyle(w).display !== 'none')
  .map(w => { const r = w.getBoundingClientRect(); const cs = getComputedStyle(w);
    return {id: w.id, label: w.getAttribute('aria-label'), op: cs.opacity, pe: cs.pointerEvents,
            rect: [r.x, r.y, r.width, r.height]}; })"""

@pytest.mark.chair_windows_open
class TestCloseMeansGone:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=CLOSE_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": CLOSE_SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={CLOSE_TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=CLOSE_TOKEN)
        created = _api(page, "POST", "/api/decisions", {"title": CLOSE_DECISION, "status": "proposed",
                                                        "decision_markdown": "Freeze writes on Nov 5."}, token=CLOSE_TOKEN)
        decision_id = created["decision"]["id"]
        kept = _api(page, "PUT", f"/api/directories/hs-seed-desk/members/decision:{decision_id}", {}, token=CLOSE_TOKEN)
        assert kept["membership"], kept
        _api(page, "POST", "/api/notes", {"title": NOTE, "body_markdown": "- Ledger cutover risks\n"}, token=CLOSE_TOKEN)
        _api(page, "POST", "/api/brief/generate", {}, token=CLOSE_TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        """A click at 1440; a real touch tap at the element's centre at 393."""
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _open(page: Any) -> list[dict[str, Any]]:
        return page.evaluate(OPEN_WINDOWS_JS)

    def _close_and_prove(self, page: Any, width: int, label: str, name: str) -> dict[str, Any]:
        """Close the one open window ``label`` by its Close gadget; prove it is gone."""
        page.wait_for_timeout(600)
        _settle(page)
        wins = [w for w in self._open(page) if w["label"] == label]
        assert len(wins) == 1, (label, self._open(page))
        win = wins[0]
        x, y, w, h = win["rect"]
        cx, cy = x + w / 2, y + h / 2
        assert page.evaluate(HIT_JS, [cx, cy])["window"] == win["id"], "the open window is not on top"
        page.screenshot(path=str(CLOSE_SHOTS / f"{name}-before-{width}.png"))
        self._press(page, _close_control(page, width, label, host=page.locator(f"[id='{win['id']}']")), width)
        page.wait_for_timeout(900)
        _settle(page)
        hit = page.evaluate(HIT_JS, [cx, cy])
        left = [o for o in self._open(page) if o["id"] == win["id"]]
        page.screenshot(path=str(CLOSE_SHOTS / f"{name}-after-{width}.png"))
        proof = {"window": win["id"], "centre": [round(cx), round(cy)], "hit": hit, "left_in_dom": left}
        (CLOSE_SHOTS / f"{name}-{width}.txt").write_text(f"{proof}\n")
        assert not left, f"the closed window stays in the DOM: {left}"
        assert _on_the_desk(hit), f"the old centre hits {hit}"
        return proof

    # ── the fences ───────────────────────────────────────────────────────

    @pytest.mark.parametrize("width", list(CLOSE_SIZES))
    def test_every_opener_closes_to_the_desk(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # 1. the palette: `decision:<id>` (DeskToolShelf → qualifiedRef).
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").fill("freeze")
                option = page.locator("[id^='desk-palette-option-decision:']").first
                option.wait_for()
                self._press(page, option, width)
                _close_control(page, width, CLOSE_DECISION).wait_for()
                self._close_and_prove(page, width, CLOSE_DECISION, "palette-decision")

                # 2. the Dock: `intelligence:desk`.
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Today']"), width)
                _close_control(page, width, "Today").wait_for()
                self._close_and_prove(page, width, "Today", "dock-intelligence")

                # 3. New note: Go raises Capture even when it is already
                # visible behind another window. The generic helper is a
                # no-op for a shown window, so it cannot do this preparation.
                page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                page.locator(".desk-verbbar-menu [role^='menuitem']").filter(
                    has=page.locator(".desk-menu-label", has_text=re.compile(r"^Capture$"))).click()
                self._press(page, page.get_by_test_id("arrival-develop-thought"), width)
                # Betterment C8: the press unfolds an empty note under the
                # verbs; the first character makes the record and opens its
                # window, and the keys after it follow into the note.
                page.get_by_test_id("arrival-new-note").locator("textarea").press("P")
                page.keyboard.type("lan")
                page.locator("[id^='pullout:note:']").first.wait_for()
                page.wait_for_timeout(1200)
                _settle(page)
                # The note's first words name its window, else `New note`
                # (windowName.ts, Betterment Q8).
                label = next(w["label"] for w in self._open(page) if str(w["id"]).startswith("pullout:note:"))
                self._close_and_prove(page, width, label, "write-a-thought")

                if width < 720:
                    # The phone home is Go. Find opens exact existing
                    # records; the grid and its keyboard icon menu are
                    # desktop doors. Keep the Note and bare-id Object Open
                    # journeys through their current touch doors.
                    self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                    page.locator("[aria-controls=desk-palette-listbox]").fill(NOTE)
                    note_option = page.locator("[id^='desk-palette-option-note:']").first
                    note_option.wait_for()
                    page.wait_for_timeout(900)
                    _settle(page)
                    self._press(page, note_option, width)
                    _close_control(page, width, NOTE).wait_for()
                    self._close_and_prove(page, width, NOTE, "find-note")

                    self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                    page.locator("[aria-controls=desk-palette-listbox]").fill("freeze")
                    option.wait_for()
                    page.wait_for_timeout(900)
                    _settle(page)
                    self._press(page, option, width)
                    decision = page.locator(f".desk-window-shell[aria-label='{CLOSE_DECISION}']")
                    head = decision.locator(".desk-pullout-title").bounding_box()
                    assert head
                    TestThePhoneDesk._long_press(page, head["x"] + head["width"] / 2, head["y"] + head["height"] / 2)
                    window_menu = page.get_by_role("menu", name=f"{CLOSE_DECISION} window menu", exact=True)
                    object_menu = page.get_by_role("menu", name="Object submenu", exact=True)
                    # Betterment daily D5: the phone's window menu is shorter
                    # (no Brief, no The week in the ring), so the finger that
                    # held the head can lift on the Object row and open it.
                    if not object_menu.count():
                        self._press(page, window_menu.get_by_role("menuitem", name="Object", exact=True), width)
                    self._press(page, object_menu.get_by_role("menuitem", name="Open", exact=True), width)
                    _close_control(page, width, CLOSE_DECISION).wait_for()
                    assert decision.count() == 1, "Object Open duplicated the existing decision"
                    self._close_and_prove(page, width, CLOSE_DECISION, "window-menu-bare-decision")
                else:
                    # 4. the one desk (PHILO-17): a Screen icon, Enter -> `note:<id>` (qualified).
                    icon = page.locator(f"[data-testid=desk-screen] .desk-icon[aria-label^='{NOTE}']").first
                    icon.wait_for(state="attached")
                    # 393: one window fills the work area; close the Chair windows
                    # shown over the desk until its icons are on the glass.
                    for _ in range(6):
                        if icon.is_visible():
                            break
                        shown = page.locator(".desk-window-shell.chair-window:visible .desk-gadget-close").first
                        if not shown.count():
                            break
                        self._press(page, shown, width)
                        page.wait_for_timeout(500)
                    icon.wait_for()
                    icon.focus()
                    page.keyboard.press("Enter")
                    _close_control(page, width, NOTE).wait_for()
                    self._close_and_prove(page, width, NOTE, "screen-icon-note")
                    # 5. a bare id: the icon's menu -> Open (object.open -> openPullout(o.id)).
                    icon = page.locator(f"[data-testid=desk-screen] .desk-icon[aria-label^='{CLOSE_DECISION}']").first
                    icon.focus()
                    page.keyboard.press("Shift+F10")
                    item = page.get_by_role("menuitem", name="Open", exact=True)
                    item.wait_for()
                    self._press(page, item, width)
                    _close_control(page, width, CLOSE_DECISION).wait_for()
                    self._close_and_prove(page, width, CLOSE_DECISION, "icon-menu-bare-decision")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(CLOSE_SIZES))
    def test_the_closed_intelligence_window_does_not_swallow_retry(self, width: int) -> None:
        """J1's recovery leg: close leaves no stale pane swallowing the next
        action, and the visible Brief retry reads successfully with no reload."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.route("**/api/brief/latest*", lambda r: r.fulfill(
                    status=500, body='{"detail":"injected"}', content_type="application/json"))
                page.reload(wait_until="load")
                _normal_chair(page)
                # Betterment D4: the brief is Today's Since-yesterday fold; a
                # failed read is its one line and Retry. D5: at both widths
                # (the Brief window retired into Today).
                open_chair_window(page, "Brief")
                brief = chair_window(page, "Brief").get_by_test_id("today-since-failed").filter(visible=True)
                retry = brief.get_by_role("button", name="Retry", exact=True)
                retry.wait_for()
                proof = self._close_and_prove(page, width, "Today", "j1-retry")
                # Closing leaves no stale pane over the next owner's action.
                # Go reopens Today; its visible Retry performs the successful
                # read in that exact canonical host.
                open_chair_window(page, "Brief")
                retry.wait_for()
                page.unroute("**/api/brief/latest*")
                with page.expect_response(lambda response: "/api/brief/latest" in response.url and response.status == 200):
                    self._press(page, retry, width)
                retry.wait_for(state="detached", timeout=10_000)
                since = chair_window(page, "Brief").get_by_test_id("today-since").filter(visible=True)
                since.wait_for()
                result = since.inner_text()[:200]
                _settle(page)
                page.screenshot(path=str(CLOSE_SHOTS / f"j1-retry-reached-{width}.png"))
                (CLOSE_SHOTS / f"j1-retry-{width}.txt").write_text(f"{proof}\nafter Retry: {result!r}\n")
                assert not [e for e in errors if "injected" not in e], errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(CLOSE_SIZES))
    def test_a_meeting_resolved_as_deleted_closes_its_card(self, width: int) -> None:
        """Round three (Astra counsel r2): the meeting card's own close caller,
        through the REAL producer. A tombstone conflict is recorded through the
        meeting repository; the selected record opens in canonical Meetings;
        Use incoming deletes the DB row and returns to the list. The shared
        host then closes and its old centre hits the Desk."""
        from playwright.sync_api import sync_playwright
        from datetime import datetime, timedelta

        from holdspeak.db import get_database
        from holdspeak.meeting_session import MeetingState, TranscriptSegment

        db = get_database()
        started = datetime.now() - timedelta(hours=2)
        title = "Tombstone sync review"
        local = MeetingState(
            id="p13-tombstone", started_at=started, ended_at=started + timedelta(minutes=12),
            title=title, tags=["delivery"],
            segments=[TranscriptSegment(text="Retained until the owner decides.", speaker="Karol",
                                        start_time=4.0, end_time=9.0)],
        )
        db.meetings.save_meeting(local)
        db.meetings.record_sync_conflict(local.id, local_value=local.to_dict(),
                                         incoming_value={"deleted": True})

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").fill("Tombstone")
                option = page.locator("[id='desk-palette-option-meeting:p13-tombstone']")
                option.wait_for()
                self._press(page, option, width)
                card = page.locator("#surface-meetings")
                card.wait_for()
                page.wait_for_function("title => document.querySelector('#surface-meetings')?.getAttribute('aria-label') === title", arg=title)
                incoming = card.get_by_role("button", name="Use incoming")
                incoming.wait_for()
                page.wait_for_timeout(600)
                _settle(page)
                box = card.bounding_box()
                assert box
                cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                win_id = card.get_attribute("id")
                page.screenshot(path=str(CLOSE_SHOTS / f"meeting-tombstone-before-{width}.png"))
                answers: list[dict] = []
                page.on("response", lambda r: answers.append({"status": r.status, "url": r.url})
                        if "/sync-conflicts/" in r.url and r.url.endswith("/resolve") else None)
                self._press(page, incoming, width)
                page.wait_for_timeout(1500)
                _settle(page)
                hit = page.evaluate(HIT_JS, [cx, cy])
                card.get_by_test_id("meetings-toolbar").wait_for()
                page.wait_for_function("() => document.querySelector('#surface-meetings')?.getAttribute('aria-label') === 'Meetings'")
                left = [o for o in self._open(page) if o["id"] == win_id and o["label"] == title]
                page.screenshot(path=str(CLOSE_SHOTS / f"meeting-tombstone-after-{width}.png"))
                proof = {"window": win_id, "centre": [round(cx), round(cy)], "resolve": answers,
                         "hit": hit, "left_in_dom": left}
                (CLOSE_SHOTS / f"meeting-tombstone-{width}.txt").write_text(f"{proof}\n")
                assert answers and answers[0]["status"] == 200, answers
                assert db.meetings.get_meeting(local.id) is None
                assert not left, f"the deleted meeting's detail stays on glass: {left}"
                assert incoming.count() == 0, "the deleted record's recovery controls stayed mounted"
                assert hit and hit["window"] == "surface-meetings", hit
                # Deletion returns to the list in the same host. Its own
                # unscoped Back/Close then proves the Desk is reachable.
                self._close_and_prove(page, width, "Meetings", "meeting-tombstone-host")
                assert not errors, errors
            finally:
                browser.close()

@pytest.mark.chair_windows_open
class TestTheDeskRemembers(_Rig):
    @pytest.mark.parametrize("width", list(_h1_SIZES))
    def test_windows_places_and_drafts_return_after_a_reload(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            puts: list[str] = []
            page.on("request", lambda r: puts.append(f"{r.method} {r.url}")
                    if r.method in ("PUT", "POST") and ("/api/updates/" in r.url or "/agenda" in r.url) else None)
            try:
                # 3. People on Priya, the Prep (Betterment D7: the prep is the page;
                #    Context, History and Info are folds under it, not tabs), an
                #    agenda item typed, not added
                self._chair_window(page, width, "Needs you")
                # PHILO-14 A5: the Needs-you drawer row's body opens it (`needs-row`).
                commitment = page.locator(".desk-window-shell[aria-label='Needs you'] [data-testid='needs-row']",
                                          has_text=COMMITMENT).first.locator(".needs-row-name")
                self._press(page, commitment, width)
                people = page.locator(PERSON).first
                people.get_by_test_id("people-add-agenda").wait_for()
                self._press(page, people.get_by_test_id("people-add-agenda"), width)
                pad = people.get_by_role("textbox", name="Add to the agenda")
                pad.wait_for()
                self._press(page, pad, width)
                page.keyboard.type(AGENDA)
                page.wait_for_timeout(400)

                # 4. Intelligence: opened, then closed (close means gone)
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Today']"), width)
                close = _close_control(page, width, "Today")
                close.wait_for()
                page.wait_for_timeout(500)
                self._press(page, close, width)
                close.wait_for(state="detached")

                # 1. the decision window
                self._palette(page, "freeze", "decision:d-freeze", width)
                page.locator(f".desk-pullout[aria-label='{DECISION}']").wait_for()
                _settle(page)

                # 2. the Room: Updates -> Draft -> typed words, not saved
                self._palette(page, "Payments", "project.open.p-ledger", width)
                _room_opened(page)
                room = page.locator("#surface-project-memory")
                # The Room's reads land after it opens and move its rows; a
                # touch tap aimed before they land hits a meeting row (its own
                # window then covers the Room at 393).
                page.wait_for_timeout(900)
                _settle(page)
                self._press(page, room.get_by_test_id("updates-verb"), width)
                # The Room's Draft update now creates the draft directly,
                # rather than entering a list with a second generator verb.
                room.locator('[data-testid="update-posture"][data-phase="editor"]').wait_for()
                # Betterment P1 (#1283): a draft is plain text, edited in place
                # (a TextArea), no longer the contenteditable DeskEditor.
                editor = room.get_by_test_id("update-plain-text")
                editor.wait_for()
                self._press(page, editor, width)
                page.keyboard.press("Control+End")
                page.keyboard.type(" " + ROOM_WORDS)
                assert ROOM_WORDS in editor.input_value()
                page.wait_for_timeout(400)
                if width >= 720:
                    head = room.locator(".desk-window-head, .desk-window-title").first
                    box = head.bounding_box()
                    assert box
                    page.mouse.move(box["x"] + 40, box["y"] + box["height"] / 2)
                    page.mouse.down()
                    page.mouse.move(box["x"] + 160, box["y"] + box["height"] / 2 + 60, steps=8)
                    page.mouse.up()
                    page.wait_for_timeout(500)
                room_rect = next(w["rect"] for w in self._windows(page) if w["id"] == "surface-project-memory")

                # 5. at 1440 the decision is iconified (393 has no Iconify gadget)
                if width >= 720:
                    # The moved Room can cover the decision's header. Raise
                    # that same record through Find before its real Iconify
                    # press; the Room's unsent words and measured seat stay.
                    self._palette(page, "freeze", "decision:d-freeze", width)
                    deck = page.locator(f".desk-pullout[aria-label='{DECISION}']")
                    self._press(page, deck.locator(f"[aria-label='Iconify {DECISION}']"), width)
                    page.wait_for_timeout(900)
                _settle(page)
                page.screenshot(path=str(_h1_SHOTS / f"B2-01-before-reload-{width}.png"))
                before = {"windows": self._windows(page), "workspace": self._workspace(page),
                          "room_rect": room_rect, "writes": list(puts)}

                # ── the reload ──
                page.reload(wait_until="load")
                _normal_chair(page)
                room = page.locator("#surface-project-memory")
                editor = room.get_by_test_id("update-plain-text")
                editor.wait_for(timeout=20_000)
                page.wait_for_function(
                    "(w) => [...document.querySelectorAll('#surface-project-memory [data-testid=update-plain-text]')].some(e => e.value.includes(w))",
                    arg=ROOM_WORDS, timeout=15_000)
                people = page.locator(PERSON).first
                if width < 720:
                    # An exact palette record pick raises the restored person
                    # without changing the retained Prep lens or unsent draft.
                    people.wait_for(state="attached", timeout=20_000)
                    self._palette(page, "Priya", f"people:{self.ids['priya']}", width)
                people.get_by_role("textbox", name="Add to the agenda").wait_for(timeout=20_000)
                page.wait_for_timeout(1200)
                _settle(page)
                after_windows = self._windows(page)
                page.screenshot(path=str(_h1_SHOTS / f"B2-02-after-reload-{width}.png"))
                # The lens is the open fold under the prep; none open reads Prep.
                open_folds = people.locator(
                    "[data-testid='people-folds'] button[aria-expanded='true'] .surface-disclosure-label")
                tab = open_folds.first.inner_text().strip() if open_folds.count() else "Prep"
                agenda = people.get_by_role("textbox", name="Add to the agenda").input_value()
                person = people.locator(".people-detail-head .people-name").inner_text().strip()
                room_after = next((w["rect"] for w in after_windows if w["id"] == "surface-project-memory"), None)
                titles = [w["title"] for w in after_windows]
                decision_drawn = any(DECISION in t for t in titles)
                # PHILO-16 (A1) §5: the window chips are parked; a seated window
                # with no application tile (a decision pullout) has its own seat tile.
                chips = page.evaluate("() => [...document.querySelectorAll('.desk-dock .desk-dock-seat-tile')].map(b => (b.getAttribute('aria-label') || b.textContent || '').trim())")
                proof = {"width": width, "before": before, "after_windows": after_windows,
                         "people": {"person": person, "tab": tab, "agenda": agenda},
                         "room_rect_after": room_after, "dock_seats": chips,
                         "writes_after_reload": [p for p in puts if p not in before["writes"]]}
                (_h1_SHOTS / f"B2-proof-{width}.json").write_text(json.dumps(proof, indent=1) + "\n")

                assert person == "Priya Nair", proof
                assert tab.lower() == "prep", proof
                assert agenda == AGENDA, proof
                assert not proof["writes_after_reload"], "restore sent a write"
                assert not before["writes"], "nothing was saved or sent before the reload"
                assert not any("Today" in t for t in titles), "the closed Intelligence window came back"
                if width >= 720:
                    # PHILO-14 A1 (#939, Astra's P2): saved positions are restored.
                    # The moved Room comes back exactly. PHILO-17 (U28c): a
                    # window's first seat is saved too, so the untouched People
                    # window comes back at the place it opened (before, it was
                    # placed again and could land elsewhere); it is whole in the
                    # band and hides no other window's title bar.
                    assert room_after == room_rect, (room_rect, room_after)
                    people_id = next(w["id"] for w in after_windows if w["title"] == "Priya Nair")
                    people_before = next(w["rect"] for w in before["windows"] if w["id"] == people_id)
                    pr = next(w["rect"] for w in after_windows if w["id"] == people_id)
                    assert pr == people_before, (people_before, pr)
                    assert pr[0] >= 0 and pr[1] >= 0 and pr[0] + pr[2] <= 1440 and pr[1] + pr[3] <= 900, pr
                    for other in after_windows:
                        if other["id"] == people_id:
                            continue
                        x, y, w, h = other["rect"]
                        hides = pr[0] <= x and pr[0] + pr[2] >= x + w and pr[1] <= y and pr[1] + pr[3] >= y + 44
                        assert not hides, (people_id, pr, other)
                    assert not decision_drawn, "the iconified decision came back drawn"
                    assert "pullout:decision:d-freeze" in self._workspace(page)["panel"]["min"]
                    assert any(DECISION in c for c in chips), chips
                else:
                    assert "decision:d-freeze" in self._workspace(page)["windows"]["pullouts"]
                assert not errors, errors
            finally:
                browser.close()

