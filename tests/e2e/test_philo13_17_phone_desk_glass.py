"""PHILO-13-17 (C7) -- the phone desk, fenced AS RENDERED.

The owner ratified the canvas on 2026-10-03 ("Ratify, build it"; all six
defaults stand; story-17 acceptance line 1). Through the real hub on an
isolated HOME, the built bundle, at 393x852 with ``has_touch`` (every press a
touch tap, every swipe a CDP touch drag, the window menu a touch long press)
and the 1440x900 control (mouse):

  S1 the frame (menu bar + Dock) <= 142 px; the front window's content
     >= 700 px; the switcher's ▾ is painted whole (its box changes when the
     mark alone is hidden); the menu bar and the Dock own no point of a
     content control's 44 px band (the canvas CHROME_OWNS fence); every body
     and footer control of the front window owns 44 x 44; the on_glass reader
     finds zero clipping and zero overlap.
  S2 the swipe: 5 of 5 land where the ring says (Needs you, Brief, The week,
     Meetings, Ledger cutover sync; it wraps), and one swipe back.
  S3 the switcher: any open window in 2 taps.
  S4 Go grouped: Chair ▸ Desk ▸ Object ▸ Window ▸ first; Object opens as a menu.
  S6 (Muad'Dib's ruling 2026-10-03): the meeting's own record in front in
     Meetings, which hosts the card's slot: the card lands there; Capture does
     not open; Meetings stays in front.
  S5 aftercare (the owner's ruling, decision 5): arrive over a window with no
     slot (Capture opens; that window iconifies) -> swipe away -> the switcher
     lists Capture -> return; never a fixed card.
  1440: the four menus stay flat; the screen title is a label (no switcher);
     a card lands in Capture, which is already open; nothing moves.

The aftercare frame is the hub's own: ``build_aftercare_ready_event`` over a
seeded meeting with open items, sent through ``MeetingWebServer.broadcast``
(the frame a finished meeting sends; the canvas limit, README "Limits").
Shots go to assets/story-17-shots/ under HOLDSPEAK_EVIDENCE_WRITE=1.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle
from .test_philo13_11_frame_glass import _seed as _frame_seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the phone desk glass needs Playwright")

TOKEN = "philo13-17-phone"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-17-shots")
SIZES = {1440: 900, 393: 852}
MEETING = "Ledger cutover sync"
CARD_MEETING = "m-c7-vendor"
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


def _seed_card_meeting() -> None:
    """A finished meeting with open items, so the hub's own aftercare event is not quiet."""
    from holdspeak.db import get_database
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    start = (datetime.now() - timedelta(minutes=40)).replace(microsecond=0)
    get_database().meetings.save_meeting(MeetingState(
        id=CARD_MEETING, started_at=start, ended_at=start + timedelta(minutes=30), title="Vendor call",
        segments=[TranscriptSegment(text="Avery sends the contract draft.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["vendor"], summary="Contract draft by Friday.",
                            action_items=[ActionItem(task="Send the contract draft", owner="Avery Chen"),
                                          ActionItem(task="Book the legal review", owner="Me")]),
        intel_status="completed"))


class TestThePhoneDesk:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _frame_seed()
        _seed_card_meeting()
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

    def _send_card(self) -> dict[str, Any]:
        from holdspeak.db import get_database
        from holdspeak.meeting_aftercare import build_aftercare_ready_event

        event = build_aftercare_ready_event(get_database(), CARD_MEETING)
        assert event, "the seeded meeting has no aftercare (the event is quiet)"
        self.server.broadcast("aftercare_ready", event)
        return event

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
                hits = sum(1 for a, b in zip(landed, ring) if a == b)
                facts["swipe_score"] = f"{hits} of 5"
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
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 600)
                rows = page.locator(".desk-screen-switcher-menu [role=menuitemcheckbox]").all_inner_texts()
                facts["switcher_rows"] = rows
                if [r.replace("✓", "").strip() for r in rows] != ring:
                    fails.append(f"S3: the switcher lists {rows}")
                self._board(page, width, "C7-4a-switcher-open", facts, fails)
                self._tap(page, page.locator(".desk-screen-switcher-menu [role=menuitemcheckbox]", has_text="Needs you"), width, 700)
                f = self._board(page, width, "C7-4b-switcher-picked", facts, fails)
                facts["switcher_taps"] = 2
                if f["front"] != ["Needs you"]:
                    fails.append(f"S3: two taps landed {f['front']}")

                # S4 Go grouped
                self._tap(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width, 600)
                heads = page.locator(".desk-verbbar-menu [role=menuitem][aria-haspopup=menu] .desk-menu-label").all_inner_texts()
                facts["go_heads"] = heads
                first = page.locator(".desk-verbbar-menu [role=menuitem] .desk-menu-label").all_inner_texts()[:4]
                if first != ["Chair", "Desk", "Object", "Window"]:
                    fails.append(f"S4: Go leads with {first}")
                self._board(page, width, "C7-5a-go-grouped", facts, fails)
                self._tap(page, page.locator(".desk-verbbar-menu [role=menuitem][aria-haspopup=menu]", has_text="Object"), width, 500)
                back_row = page.locator(".desk-verbbar-menu .desk-menu-back").inner_text().strip()
                facts["go_object_back_row"] = back_row
                if "Object" not in back_row:
                    fails.append(f"S4: Object did not open as a menu ({back_row})")
                self._board(page, width, "C7-5b-go-object", facts, fails)
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)

                # S6 (Muad'Dib's ruling 2026-10-03): the meeting's own record is in front in
                # Meetings, which hosts the card's slot: the card lands there, Capture
                # does not open, and Meetings stays in front.
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 500)
                self._tap(page, page.locator(".desk-screen-switcher-menu [role=menuitemcheckbox]", has_text="Meetings"), width, 900)
                self._tap(page, page.get_by_test_id(f"meeting-row-{CARD_MEETING}").locator(".meetings-stream-row-body"), width, 1500)
                if self._front(page)["front"] != ["Meetings"]:
                    fails.append(f"S6: Meetings is not in front before the card {self._front(page)['front']}")
                record = page.locator(".desk-window-shell[aria-label='Meetings'] [data-testid=meeting-summary-text]",
                                      has_text="Contract draft by Friday.")
                try:
                    record.first.wait_for(state="attached", timeout=8000)
                    facts["own_record_open"] = True
                except Exception:  # noqa: BLE001 -- the fence below names it
                    facts["own_record_open"] = False
                    fails.append("S6: the card meeting's own record is not open in Meetings")
                facts["aftercare_event"] = self._send_card()
                page.wait_for_timeout(1800)
                f = self._board(page, width, "C7-6e-aftercare-own-record-in-front", facts, fails)
                in_meetings = page.evaluate("""() => !!document.querySelector(
                    ".desk-window-shell[aria-label='Meetings'] [data-aftercare-window-slot] .ambient-aftercare")""")
                facts["own_record_card_in_meetings"] = in_meetings
                if f["front"] != ["Meetings"] or not in_meetings or f["card_in_capture"]:
                    fails.append(f"S6: front {f['front']}, card in Meetings {in_meetings}, in Capture {f['card_in_capture']}")
                if facts["own_record_open"]:
                    record.first.scroll_into_view_if_needed()
                    page.wait_for_timeout(300)
                    page.screenshot(path=str(SHOTS / f"C7-6f-aftercare-own-record-still-open-{width}.png"))
                    if self._front(page)["front"] != ["Meetings"]:
                        fails.append("S6: the record left the front after the card")
                self._tap(page, page.locator(".ambient-aftercare").get_by_role("button", name="Dismiss"), width, 800)
                if page.locator(".ambient-aftercare").count():
                    fails.append("S6: Dismiss did not clear the card")

                # S5 aftercare (decision 5): a desk window with no slot in front (the meeting
                # window) -> the card opens Capture and that window iconifies -> swipe away ->
                # the switcher lists Capture -> return
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 500)
                self._tap(page, page.locator(".desk-screen-switcher-menu [role=menuitemcheckbox]", has_text=MEETING), width, 900)
                if self._front(page)["front"] != [MEETING]:
                    fails.append(f"S5: {MEETING} is not in front before the card {self._front(page)['front']}")
                self._send_card()
                page.wait_for_timeout(1800)
                f = self._board(page, width, "C7-6a-aftercare-arrives", facts, fails)
                iconified = page.evaluate("""(name) => { const s = document.querySelector(`.desk-window-shell[aria-label='${name}']`);
                    return s ? getComputedStyle(s).display : 'closed'; }""", MEETING)
                facts["meeting_window_after_card"] = iconified
                if f["front"] != ["Capture"] or not f["card_in_capture"]:
                    fails.append(f"S5 arrive: front {f['front']}, card in Capture {f['card_in_capture']}")
                # iconified: off the glass (unmounted while minimized, or display none)
                if iconified not in ("none", "closed"):
                    fails.append(f"S5 arrive: {MEETING} is still on the glass (display {iconified})")
                self._swipe(page, +1)
                f = self._board(page, width, "C7-6b-aftercare-swipe-away", facts, fails)
                if f["front"] == ["Capture"]:
                    fails.append("S5: the swipe did not leave Capture")
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 600)
                rows = [r.replace("✓", "").strip() for r in
                        page.locator(".desk-screen-switcher-menu [role=menuitemcheckbox]").all_inner_texts()]
                facts["switcher_after_card"] = rows
                if "Capture" not in rows:
                    fails.append(f"S5: the switcher does not list Capture {rows}")
                # ... and never closed: the meeting window is still an open window in the ring
                if MEETING not in rows:
                    fails.append(f"S5: {MEETING} was closed by the card, not iconified {rows}")
                self._board(page, width, "C7-6c-aftercare-switcher-lists-capture", facts, fails)
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                self._swipe(page, -1)
                f = self._board(page, width, "C7-6d-aftercare-return", facts, fails)
                if f["front"] != ["Capture"] or not f["card_in_capture"]:
                    fails.append(f"S5 return: front {f['front']}, card in Capture {f['card_in_capture']}")

                # Q6: the eyebrow reads on --accent-text
                facts["eyebrow_color"] = page.evaluate("""() => { const e = document.querySelector('.ambient-aftercare .signal-eyebrow');
                    return e ? getComputedStyle(e).color : null; }""")

                real = [e for e in errors if "ResizeObserver" not in e]
                facts["errors"] = real
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / f"phone-desk-facts-{width}.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1, default=str))
                browser.close()
        assert not fails, fails

    def test_the_ring_keeps_order_and_name_and_the_switcher_toggles_393(self) -> None:
        """Astra r1 #751, conditions 1 and 2, with native touch taps.

        Open the Room (a core that publishes its own title), then Meetings, then
        a meeting, then swipe to Needs you (the desk windows iconify): the ring
        keeps the opening order and the Room keeps its name. A second tap on the
        switcher closes its menu."""
        from playwright.sync_api import sync_playwright
        from .test_philo13_11_frame_glass import ROOM, _stage

        width = 393
        facts: dict[str, Any] = {"width": width}
        fails: list[str] = []
        want = ["Needs you", "Brief", "The week", ROOM, "Meetings", MEETING]
        switcher = ".desk-screen-switcher-menu"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                _stage(page, "open-project-memory", "project:p-ledger")
                page.locator(f".desk-window-shell[aria-label='{ROOM}']").wait_for()
                self._open_meeting(page, width)
                self._swipe(page, +1)  # wraps to Needs you: every desk window iconifies
                facts["front_after_swipe"] = self._front(page)["front"]
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 600)
                rows = [r.replace("✓", "").strip() for r in page.locator(f"{switcher} [role=menuitemcheckbox]").all_inner_texts()]
                facts["ring_after_iconify"] = rows
                if rows != want:
                    fails.append(f"C1 the ring lost order or name: {rows}, want {want}")
                page.screenshot(path=str(SHOTS / f"C7-11-ring-order-and-name-{width}.png"))
                # C2: the second native tap on the open switcher closes it
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 600)
                still = page.locator(switcher).count()
                facts["menu_after_second_tap"] = still
                if still:
                    fails.append("C2 a second tap on the switcher did not close it")
                # ... and a third opens it again (the toggle, not a dead title)
                self._tap(page, page.get_by_test_id("desk-screen-switcher"), width, 600)
                facts["menu_after_third_tap"] = page.locator(switcher).count()
                if not facts["menu_after_third_tap"]:
                    fails.append("C2 a third tap did not open the switcher")
                # the Room comes back by its name (the menu the third tap opened)
                self._tap(page, page.locator(f"{switcher} [role=menuitemcheckbox]", has_text=ROOM), width, 1500)
                f = self._front(page)
                facts["room_restored"] = f
                if f["front"] != [ROOM] or f["title"] != ROOM:
                    fails.append(f"C1 the Room restored as {f['front']} titled {f['title']}")
                real = [e for e in errors if "ResizeObserver" not in e]
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / f"ring-facts-{width}.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1, default=str))
                browser.close()
        assert not fails, fails

    def test_the_1440_control(self) -> None:
        from playwright.sync_api import sync_playwright

        width = 1440
        facts: dict[str, Any] = {"width": width}
        fails: list[str] = []
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                ids = page.evaluate("() => [...document.querySelectorAll('[data-menu-id]')].map((e) => e.dataset.menuId)")
                facts["menus"] = ids
                if ids != ["desk", "object", "go", "window"]:
                    fails.append(f"1440: the menus are {ids}")
                if page.get_by_test_id("desk-screen-switcher").count():
                    fails.append("1440: the screen title became a switcher")
                page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                page.wait_for_timeout(400)
                subs = page.locator(".desk-verbbar-menu [role=menuitem][aria-haspopup=menu]").count()
                facts["go_submenus"] = subs
                if subs:
                    fails.append(f"1440: Go carries {subs} submenus")
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                self._board(page, width, "C7-1-the-frame", facts, fails, chevron=False)
                self._send_card()
                page.wait_for_timeout(1800)
                f = self._board(page, width, "C7-6a-aftercare-arrives", facts, fails, chevron=False)
                if not f["card_in_capture"]:
                    fails.append("1440: the card is not in Capture")
                fronts = page.evaluate("() => [...document.querySelectorAll('.chair-window')].map((e) => e.getAttribute('aria-label'))")
                facts["chair_windows"] = fronts
                if sorted(fronts) != sorted(["Needs you", "Brief", "The week", "Capture"]):
                    fails.append(f"1440: the Chair windows moved {fronts}")
                self._open_meeting(page, width)
                self._board(page, width, "C7-9-control-two-windows", facts, fails, chevron=False)
                real = [e for e in errors if "ResizeObserver" not in e]
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / f"phone-desk-facts-{width}.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1, default=str))
                browser.close()
        assert not fails, fails
