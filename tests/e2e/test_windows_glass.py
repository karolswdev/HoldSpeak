"""The windows of the desk, AS RENDERED: what only a real browser proves.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. Through the real hub
on an isolated HOME, the built bundle, at 393x852 with ``has_touch`` (every
press a touch tap, every swipe a CDP touch drag, the window menu a touch long
press):

* The phone desk (PHILO-13-17, C7; the owner ratified the canvas 2026-10-03):
  the frame (menu bar + Dock) <= 142 px; the front window's content >= 700
  px; the switcher's ▾ is painted whole at 3:1; the menu bar and the Dock own
  no point of a content control's 44 px band; every body and footer control
  of the front window owns 44 x 44. The swipe lands 5 of 5 where the ring
  says (it wraps) and one swipe goes back; the long press still opens the
  window menu; the switcher reaches any window in 2 taps, and a second tap
  closes it (Astra r1 #751).
* Escape on an open strip menu closes the menu, not the window (PHILO-13-18):
  Speak's wings fold into one strip menu at 393; a tap opens it and leaves
  focus on the Button; the first Escape closes the menu and Speak stays in
  front; a second Escape still closes the window.

Cheaper successors of the rest: the ring, the switcher rows, Go at 393 and
the four flat menus at 1440 in web/src/desk/components/window/phoneRing.test.tsx
and web/src/desk/components/DeskMenuBar.test.tsx; the aftercare card's
placement in web/src/desk/chair/__tests__/aftercarePhone.philo1317.test.tsx;
clip, overlap and fit of every window in the desk sweep.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle
from .test_philo13_11_frame_glass import _seed as _frame_seed
from tests._evidence import evidence_dir

pytestmark = [pytest.mark.e2e]

pytest.importorskip("playwright.sync_api", reason="the windows glass needs Playwright")

TOKEN = "windows-glass"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-17-shots")
SIZES = {1440: 900, 393: 852}
MEETING = "Ledger cutover sync"
FRAME_MAX, CONTENT_MIN = 142, 700

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
  const btn = mark.closest('.desk-screen-switcher');
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
               *, chevron: bool = True) -> dict[str, Any]:
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
            if chevron:
                f["chevron"] = self._chevron(page)
                if not (f["chevron"]["whole"] and f["chevron"]["painted"] and f["chevron"]["contrast"]["ratio"] >= 3):
                    fails.append(f"{name}: the switcher ▾ is not painted whole {f['chevron']}")
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
    def _chevron(page: Any) -> dict[str, Any]:
        """The ▾ is PAINTED: whole, on top at its centre, and its box's pixels change when it alone is hidden."""
        sel = "[data-testid=desk-screen-switcher-mark]"
        w = page.evaluate(WHOLE, sel)
        b = page.locator(sel).first.bounding_box()
        clip = {"x": b["x"], "y": b["y"], "width": max(1, b["width"]), "height": max(1, b["height"])}
        shown = page.screenshot(clip=clip)
        page.evaluate(f"() => {{ document.querySelector('{sel}').style.visibility = 'hidden'; }}")
        hidden = page.screenshot(clip=clip)
        page.evaluate(f"() => {{ document.querySelector('{sel}').style.visibility = ''; }}")
        cut = page.evaluate("""() => { const n = document.querySelector('.desk-screen-switcher .desk-screen-name');
            return n ? n.scrollWidth > n.clientWidth + 1 : null; }""")
        # Astra r1 #751, condition 3: pixels that change at 1:1 are not "painted"
        # for a reader. The mark's computed colour against the button's own
        # (opaque, composited) background reads >= 3:1 (a non-text mark), in
        # the closed and in the open state.
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

                # two desk windows: Meetings, then the meeting (the ring is now 5)
                self._open_meeting(page, width)
                self._board(page, width, "C7-3a-meeting-window", facts, fails)
                ring = ["Needs you", "Brief", "The week", "Meetings", MEETING]

                # S2 the swipe: 5 of 5 forward (it wraps), then one back
                landed: list[str | None] = []
                for _ in range(5):
                    self._swipe(page, +1)
                    fr = self._front(page)["front"]
                    landed.append(fr[0] if len(fr) == 1 else None)
                facts["swipe_forward"] = landed
                if landed != ring:
                    fails.append(f"S2: 5 swipes landed {landed}, the ring says {ring}")
                self._swipe(page, -1)
                back = self._front(page)["front"]
                facts["swipe_back"] = back
                if back != ["Meetings"]:
                    fails.append(f"S2: a swipe back landed {back}, not Meetings")
                self._board(page, width, "C7-3b-swipe-to-meetings", facts, fails)
                # past the first desk window, the Chair's window returns
                self._swipe(page, -1)
                if self._front(page)["front"] != ["The week"]:
                    fails.append(f"S2: past Meetings the swipe landed {self._front(page)['front']}")
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

                # S3 the switcher: 2 taps to Needs you
                switcher = ".desk-screen-switcher-menu"
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 600)
                rows = page.locator(f"{switcher} [role=menuitemcheckbox]").all_inner_texts()
                facts["switcher_rows"] = rows
                if [r.replace("✓", "").strip() for r in rows] != ring:
                    fails.append(f"S3: the switcher lists {rows}")
                self._board(page, width, "C7-4a-switcher-open", facts, fails)
                # C2: the second native tap on the open switcher closes it; a third opens it again
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 600)
                if page.locator(switcher).count():
                    fails.append("C2 a second tap on the switcher did not close it")
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 600)
                if not page.locator(switcher).count():
                    fails.append("C2 a third tap did not open the switcher")
                self._tap(page, page.locator(f"{switcher} [role=menuitemcheckbox]", has_text="Needs you"), width, 700)
                f = self._board(page, width, "C7-4b-switcher-picked", facts, fails)
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
            page.locator(".desk-menu-list").first.wait_for()
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            menu_open = page.locator(".desk-menu-list").count()
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
