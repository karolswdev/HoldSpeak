"""The Dock app, AS RENDERED: current daily doors, seats and touch ownership.

The historical paging test names stay as recovery-queue identities. Their
current proofs cover all four essential phone doors, exact tap destinations,
Capture's return seat and five project seat journeys. No pager is assumed.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. Through the real hub
on an isolated HOME:

* 393 (touch): the daily seats come first, whole, left of More AppIcons; a
  touch tap on More AppIcons moves the shelf one page.
* The hub stops and his "Refresh from hub" runs (the palette, at both widths):
  the outage receipt's Retry and OK each own the point at their centre, and
  the screen bar stays one line with the receipt in it.

The Dock's words have cheaper successors: READY, SENT, REC and OFFLINE in
web/src/desk/components/window/Dock.test.tsx, the outage receipt's words in
web/src/desk/__tests__/dock.app.test.tsx, the producers in
tests/unit/test_philo13_c3_dock.py and tests/unit/test_philo13_c3_ready.py.
Clip, overlap and fit of the Dock at 1440 and 393 are the desk sweep's
(tests/e2e/test_desk_sweep.py, the bare desk case and the pager waiver).

Also kept here by lane e2e-high-1:

The Dock in a real browser: touch and the shelf's exact geometry.

Kept by the test diet (push 2, 2026-10-12), one file for the Dock app:

* a tap on the 393 Dock presses the icon under the finger, after the shelf
  pages the three ways a person pages it (More, a native swipe, the browser
  bringing the icon into view) -- PHILO-13-01 (B0): the sticky More gadget
  carried ``scroll-snap-align: start`` and every tap re-snapped the shelf a
  page on (was tests/e2e/test_philo13_01_dock_tap_glass.py);
* every page of the 393 shelf starts and ends on a whole AppIcon: no strip
  of the icon before a page in the left gutter, none of the next one beside
  More ("a 5 px strip"; was the Dock leg of
  tests/e2e/test_finish_face_polish_glass.py).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

from .finish_rig import SHOTS as FINISH_SHOTS, FinishRig

pytest.importorskip("playwright.sync_api", reason="the Dock glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "dock-glass"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-13-shots")
SIZES = {1440: 900, 393: 852}
T = 20_000
DOCK = ".desk-dock"
PHONE_DOORS = {
    "today": ("intelligence:desk", '[id="pullout:intelligence:desk"]', '[data-testid="today-day"]'),
    "capture": ("chair:capture", '[aria-label="Capture"].desk-window-shell', '[data-testid="arrival-capture-bar"]'),
    "meetings": ("surface-meetings", '#surface-meetings', '[data-testid="meetings-headline"]'),
    "people": ("surface-people", '#surface-people', '.desk-surface-body'),
}


def _whole_dock_target(target: Any) -> dict[str, Any]:
    probe = target.evaluate("""el => {
      const r=el.getBoundingClientRect(), d=el.closest('.desk-dock').getBoundingClientRect();
      const points=[.1,.5,.9].flatMap(x=>[.1,.5,.9].map(y=>{
        const hit=document.elementFromPoint(r.left+r.width*x,r.top+r.height*y);
        return !!hit && (hit===el || el.contains(hit));
      }));
      return {name:el.getAttribute('aria-label'),width:r.width,height:r.height,
        whole:r.left>=Math.max(0,d.left)-.5 && r.right<=Math.min(innerWidth,d.right)+.5 && r.top>=0 && r.bottom<=innerHeight,
        points};
    }""")
    assert probe["whole"] and probe["width"] >= 44 and probe["height"] >= 44, probe
    assert all(probe["points"]), probe
    return probe


def _tap_dock(page: Any, target: Any) -> None:
    _whole_dock_target(target)
    box = target.bounding_box()
    page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def _swipe_shelf(page: Any, *, right: bool = False) -> None:
    box = page.locator(DOCK).bounding_box()
    assert box
    cdp = page.context.new_cdp_session(page)
    try:
        cdp.send("Input.synthesizeScrollGesture", {
            "x": box["x"] + box["width"] / 2, "y": box["y"] + box["height"] / 2,
            "xDistance": 340 if right else -340, "yDistance": 0,
            "gestureSourceType": "touch", "speed": 800})
    finally:
        cdp.detach()
    page.wait_for_timeout(700)

OWNS_ITS_CENTRE = """(el) => { const r = el.getBoundingClientRect();
    const x = r.left + r.width / 2, y = r.top + r.height / 2;
    const hit = document.elementFromPoint(x, y);
    return { owned: !!hit && (hit === el || el.contains(hit)),
             hit: hit ? (hit.className || hit.tagName) + '' : null,
             in_viewport: x >= 0 && y >= 0 && x <= innerWidth && y <= innerHeight }; }"""

BAR_SPILL = """() => {
    const bar = document.querySelector('.desk-menubar').getBoundingClientRect();
    return [...document.querySelectorAll('.desk-menubar .desk-chrome-tr > *')]
      .map((e) => ({el: (e.getAttribute('aria-label') || e.textContent || e.className).trim().slice(0, 40),
                    r: e.getBoundingClientRect()}))
      .filter((x) => x.r.width > 0 && x.r.height > 0 && (x.r.top < bar.top - 0.5 || x.r.bottom > bar.bottom + 0.5))
      .map((x) => ({el: x.el, top: Math.round(x.r.top), bottom: Math.round(x.r.bottom), bar: Math.round(bar.bottom)}));
}"""


class TestDockGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        self.stopped = False
        try:
            yield
        finally:
            if not self.stopped:
                server.stop()

    def _page(self, pw: Any, width: int, *, builder_tools: bool = False) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720,
                                  reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        if builder_tools:
            # Betterment shell S1 (#1259): Refresh from hub is a builder tool;
            # Search lists it only with Settings ▸ System ▸ Builder tools on.
            page.evaluate("() => localStorage.setItem('hs.desk.builderTools', 'on')")
        page.reload(wait_until="load")
        _normal_chair(page)
        page.locator(DOCK).wait_for()
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    def test_the_phone_shelf_seats_and_pages_by_touch(self) -> None:
        """replaces: tests/e2e/test_philo13_13_dock_glass.py::TestLiveDock::test_the_dock_shows_his_day_live_and_stays_through_an_outage
        (the 393 leg: the daily seats on the first page, More AppIcons pages the shelf)."""
        from playwright.sync_api import sync_playwright

        width = 393
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                doors = page.locator(".desk-dock-app[data-app]")
                assert set(doors.evaluate_all("bs => bs.map(b=>b.dataset.app)")) == {door[0] for door in PHONE_DOORS.values()}
                for target in doors.all():
                    _whole_dock_target(target)
                capture = page.locator('.desk-dock [data-app="chair:capture"]')
                _tap_dock(page, capture)
                page.locator('[aria-label="Capture"].desk-window-shell [data-testid=arrival-capture-bar]').wait_for()
                _tap_dock(page, page.locator('.desk-dock [data-app="intelligence:desk"]'))
                page.locator('[id="pullout:intelligence:desk"] [data-testid=today-day]').wait_for()
                _whole_dock_target(capture)
                capture_window = page.locator('[aria-label="Capture"].desk-window-shell')
                assert capture_window.count() == 1, "Capture must remain open while Today is front"
                _tap_dock(page, capture)
                capture_window.wait_for(state="visible")
                page.wait_for_function("el => el.classList.contains('is-front')", arg=capture_window.element_handle())
                capture_window.locator('[data-testid=arrival-capture-bar]').wait_for()
                page.screenshot(path=str(SHOTS / f"dock-02-capture-return-{width}.png"))
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_outage_receipt_owns_its_verbs_and_the_bar_stays_one_line(self, width: int) -> None:
        """replaces: tests/e2e/test_philo13_13_dock_glass.py::TestLiveDock::test_the_dock_shows_his_day_live_and_stays_through_an_outage
        (the outage legs that are geometry: Retry and OK own their centres;
        PHILO-13-11 close, design §4: the screen bar does not wrap under the receipt)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width, builder_tools=True)
            try:
                self.server.stop()
                self.stopped = True
                page.get_by_test_id("desk-dock-offline").wait_for(timeout=T)
                # An actual failed Desk refresh: his "Refresh from hub", from the palette.
                field = page.locator("[aria-controls=desk-palette-listbox]")
                if not field.is_visible():
                    self._press(page, page.locator("[aria-controls=desk-tool-shelf]"), width)
                field.fill("Refresh from hub")
                self._press(page, page.locator("[id='desk-palette-option-desk.refresh']"), width)
                receipt = page.locator(".write-receipt", has_text="READ MEETINGS FAILED · HUB UNREACHABLE").first
                receipt.wait_for(timeout=T)
                _settle(page)  # the phone window yields to the receipt row in a layout pass; measure after it
                for name in ("Retry", "OK"):
                    button = receipt.get_by_role("button", name=name, exact=True)
                    assert button.count() == 1, f"{name} is missing from the outage receipt"
                    owned = page.evaluate(OWNS_ITS_CENTRE, button.element_handle())
                    assert owned["in_viewport"] and owned["owned"], f"{name}: {owned}"
                spill = page.evaluate(BAR_SPILL)
                assert not spill, f"the screen bar wraps under the outage receipt: {spill}"
                page.screenshot(path=str(SHOTS / f"dock-08b-outage-receipt-{width}.png"))
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()


# ══ lane e2e-high-1 (the finish-polish and Dock-tap fences) ═══════════

TAP_TOKEN = "philo13-01-dock-tap"


# ── a tap on a paged Dock (PHILO-13-01) ──────────────────────────────────

# The first dock icon wholly past the first page (its left edge at 393 px or more).
PAST_JS = """() => { const all = [...document.querySelectorAll('.desk-dock .desk-dock-launch')];
  const i = all.findIndex((b) => { const r = b.getBoundingClientRect();
    return r.width > 0 && r.x >= 393 && !/hide/i.test(b.getAttribute('aria-label') || ''); });
  if (i < 0) return null; all[i].setAttribute('data-fence-target', '1');
  return all[i].getAttribute('aria-label') || all[i].textContent.trim(); }"""
PRESSES_JS = """() => { window.__presses = [];
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('button');
    window.__presses.push(b ? (b.getAttribute('aria-label') || b.textContent.trim()) : null);
  }, true); }"""


class TestDockTap393:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TAP_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("app", list(PHONE_DOORS))
    def test_a_tap_on_a_paged_dock_presses_that_icon_393(self, app: str) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 393, "height": 852},
                                      device_scale_factor=1, has_touch=True)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            try:
                page.goto(f"{self.base}/?token={TAP_TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TAP_TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                _settle(page)
                page.locator(".desk-dock .desk-dock-launch").first.wait_for(state="attached")
                app_id, window_selector, content = PHONE_DOORS[app]
                door = page.locator(f'.desk-dock [data-app="{app_id}"]')
                label = door.get_attribute("aria-label")
                page.evaluate(PRESSES_JS)
                _tap_dock(page, door)
                window = page.locator(window_selector)
                window.wait_for(state="visible")
                window.locator(content).wait_for()
                assert "is-front" in (window.get_attribute("class") or ""), app
                presses = page.evaluate("() => window.__presses")
                settled = page.evaluate(
                    "() => document.querySelector('.desk-next').getAttribute('data-settled')")
                assert presses == [label], (app, presses)
                assert settled != "true", (app, "the tap hid the menus")
                assert page.locator(".desk-tools-launch").first.is_visible(), (
                    app, "Search is hidden after the tap")
            finally:
                browser.close()


# ── the shelf pages on whole icons (the finish polish) ──────────────────

# Every launcher and strip item that crosses the shelf's left gutter or the
# More gadget's left edge on the page in view.
SHELF_PAGE = """() => {
  const d = document.querySelector('.desk-dock');
  const more = d.querySelector('.desk-dock-more').getBoundingClientRect();
  const gutter = d.getBoundingClientRect().left + 4;
  const atEnd = d.scrollLeft >= d.scrollWidth - d.clientWidth - 1;
  const out = {scrollLeft: d.scrollLeft, atEnd, left: [], right: []};
  for (const k of d.children) {
    if (k.classList.contains('desk-dock-more') || getComputedStyle(k).display === 'none') continue;
    const b = k.getBoundingClientRect();
    const name = k.getAttribute('aria-label') || k.className;
    if (b.left < gutter - 0.5 && b.right > gutter + 0.5) out.left.push([name, Math.round(b.right - gutter)]);
    if (k.classList.contains('desk-dock-launch') && b.left < more.left - 0.5 && b.right > more.left + 0.5)
      out.right.push([name, Math.round(more.left - b.left)]);
  }
  return out;
}"""


class TestDockPagesOnWholeIcons(FinishRig):
    @pytest.mark.e2e
    def test_the_phone_dock_pages_on_whole_icons(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                probes = [_whole_dock_target(target) for target in page.locator('.desk-dock-app[data-app]').all()]
                page.screenshot(path=str(FINISH_SHOTS / "dock-home-393.png"))
                # Five actual project journeys exercise window seats on the
                # current shelf; projects are reached from Go, not Dock pages.
                projects = _api(page,"GET","/api/projects",token="finish-polish-glass")["projects"]
                assert len(projects) >= 5
                for n, project in enumerate(projects):
                    page.locator(".desk-verbbar-item[data-menu-id='go'] button").tap()
                    menu = page.locator(".desk-verbbar-menu")
                    # Betterment shell S1 (#1259): projects sit under Go ▸ Projects
                    # (at 393 the submenu replaces the panel).
                    menu.get_by_role("menuitem",name="Projects",exact=True).tap()
                    menu.get_by_role("menuitem",name=project["name"],exact=True).tap()
                    room = page.locator('#surface-project-memory')
                    room.wait_for(state="visible")
                    assert room.get_attribute("aria-label") == project["name"]
                    page.locator(".desk-verbbar-item[data-menu-id='go'] button").tap()
                    page.locator(".desk-verbbar-menu [role^=menuitem]").filter(
                        has=page.locator(".desk-menu-label",has_text="Needs you")).tap()
                    page.locator('.desk-window-shell[aria-label="Needs you"]').wait_for(state="visible")
                    seat = page.locator('.desk-dock [data-seat="surface-project-memory"]')
                    seat.wait_for(state="attached")
                    for _ in range(6):
                        if seat.evaluate("el => { const r=el.getBoundingClientRect(); return r.left>=0 && r.right<=innerWidth; }"):
                            break
                        _swipe_shelf(page)
                    probes.append(_whole_dock_target(seat))
                    _tap_dock(page,seat)
                    room.wait_for(state="visible")
                    assert room.get_attribute("aria-label") == project["name"]
                    seat.wait_for(state="detached")
                    page.screenshot(path=str(FINISH_SHOTS / f"dock-seat{n}-393.png"))
                assert len(probes) >= 9, probes
                assert not errors, errors
            finally:
                browser.close()


def test_a_late_people_fact_keeps_the_desktop_dock_targets_in_place(tmp_path, monkeypatch):
    """Hold the real People read; its actual reply must not move a live door."""
    import json
    from datetime import datetime
    from . import open_rig
    from playwright.sync_api import sync_playwright

    _ensure_build()
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        week = open_rig._seed(tmp_path / "home", base)
        brief = open_rig._http(base, "GET", f"/api/people/relationships/{week['priya']}/brief")["brief"]
        starts = brief["next_one_on_one"]["starts_at"]
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
                # Keep the actual seeded meeting on the browser's current day,
                # including a run just before midnight. Timers still advance.
                page.clock.set_fixed_time(datetime.fromisoformat(starts.replace("Z", "+00:00")))
                held = []
                released = False

                def hold_read(route):
                    if released:
                        route.continue_()
                    else:
                        held.append(route)

                page.route("**/api/people/readiness", hold_read)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                page.locator(".desk-dock-app").first.wait_for()
                assert held, "the real People readiness read was not held"
                tiles = page.locator(".desk-dock-app")
                read = "els => els.map(el => { const r=el.getBoundingClientRect(); return {app:el.dataset.app,x:r.x,y:r.y,w:r.width,h:r.height}; })"
                before = tiles.evaluate_all(read)
                assert page.get_by_test_id("desk-dock-people-state").count() == 0
                released = True
                for route in held:
                    route.continue_()
                page.get_by_test_id("desk-dock-people-state").wait_for()
                after = tiles.evaluate_all(read)
                assert [row["app"] for row in before] == [row["app"] for row in after]
                for old, new in zip(before, after):
                    for field in ("x", "y", "w", "h"):
                        assert abs(old[field] - new[field]) <= .5, (field, old, new)
                out = evidence_dir("s3-dock-arrival")
                out.mkdir(parents=True, exist_ok=True)
                (out / "late-people-1440.json").write_text(json.dumps({"before": before, "after": after}, indent=2))
                page.screenshot(path=str(out / "late-people-1440.png"))
            finally:
                browser.close()
    finally:
        server.stop()
