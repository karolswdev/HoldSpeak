"""The menus and doors of the desk, AS RENDERED: what only a real browser proves.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. Through ONE real hub
on an isolated HOME and the built bundle, with three projects:

* 393 (touch): the whole Go menu is on one phone screen (no scroll to its
  end) (PHILO-15 11, B21).
* D6: a Room opens from Go, falls to its own Dock tile (Iconify at 1440; a
  Chair window taking the work area at 393), the tile names it, and a press
  on the tile brings it back. (T2 owed: it needs the whole desk rendered over
  recorded answers; until then it stays here.)
* D7 (393, Astra r2): Go ▸ Ask AI, Go ▸ Capture, Go ▸ Ask AI shows Ask again.
  (T2 owed, as D6.)

The rest of PHILO-17 doors and PHILO-15 11 have cheaper successors: the Go,
Tools and HoldSpeak menu rows in web/src/desk/components/DeskMenuBar.test.tsx
and web/src/desk/__tests__/menus.app.test.tsx; the phone Go and New in
web/src/desk/components/window/phoneRing.test.tsx:191-206; no keycap on a
phone in web/src/desk/__tests__/phoneKeycaps.philo1511.test.tsx; the Dock's
seats in web/src/desk/components/window/Dock.test.tsx:130; the next 1:1 on the
People drawer in web/src/desk/screen/__tests__/nextOneOnOne.test.tsx; every
application drawn loaded, and fit, in the desk sweep.

Also here (lane e2e-high-1):

The shared chrome strips in a real browser: the keys on the menus, the
Dock, the wing strips and the current note footer.

Kept by the test diet (push 2, 2026-10-12), one file for the menus and the
strips they share. Was tests/e2e/test_hs202_03_species_glass.py (whole: each
check presses keys, measures a focus ring or measures a 44 px row; the
"every verb is the library Button" half is also the desk sweep's `library`
fence).

HS-202-03 — the shared controls are library species, on real glass.

The surface inventory of 2026-09-20 (§3.3, F-U1) found raw buttons
outnumbering library Buttons more than two to one, and the worst sites were
the shared species themselves: every menu item (`DeskMenu.tsx:155`), every
wing tab (`wings.tsx:88`), the dock (7), the editor's rail (11). Story 03
makes them the library `Button` through the new `chrome` variant — the
species without the plate, because their material is drawn by the strip they
ride.

WHAT THIS RIG PROVES, exactly (counsel #598, finding 2 — the earlier
docstring claimed "the keyboard is UNCHANGED" and "returns focus on
Escape", and both were overclaims):

  1. Every verb on the shared strips is now the library species: a real
     `<button>` carrying a library mark — `btn--chrome` on the strips whose
     material is their own, the `.btn` plate elsewhere. A control wearing
     neither was drawn by a raw `<button>`.
  2. The SPECIFIC keyboard interactions it presses still behave: the dock's
     Tab order equals its DOM order and each of those stops computes a
     non-zero outline; ArrowDown/ArrowUp rove the open menu and Escape
     closes it; the wing strip holds exactly one Tab stop and ArrowRight
     moves the selected wing; one note-footer stop computes a non-zero outline.
     At 393 it also measures the two strips 03 owns: every row of the dock
     and of the wing bar has a bounding height of at least 44px, and no two
     rows overlap (story 05's ruling — a plated Button owns 44px through a
     halo, a chrome Button is a strip row and the STRIP owes it the height).
  3. The Meetings row body computes the same box the `div` computed
     (background, border, padding, text-align, display).

WHAT IT DOES NOT PROVE. Not complete keyboard equivalence: only the keys
listed above are pressed, on these four strips, on a cold seeded desk. Not
pixel identity: nothing here compares images, and the ink argument rests on
the separate fact that no stylesheet defines `.btn--chrome`
(`web/src/desk/__tests__/hs202ChromeSpecies.test.tsx`). Where focus LANDS
after Escape is deliberately not asserted — `DeskMenuBar.tsx:134-144` has
never passed `returnFocus` to `WorkMenu`, at the base commit as well, so
focus falls to the body; that gap is ledgered, not fixed here.

Both widths, 1440 and 393. Shots into this story's assets.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from tests._evidence import evidence_dir
from datetime import datetime
from datetime import timedelta

pytest.importorskip("playwright.sync_api", reason="the menus glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "menus-glass"
SHOTS = evidence_dir("docs/internal/philo/phase-17/doors-shots")
SIZES = {1440: 900, 393: 852}
T = 30_000
PROJECTS = ["Ledger cutover", "Platform observability", "Hiring loop"]

# Is this Dock control fully on the shelf's visible page (left of More)?
ON_SHELF_JS = r"""(el) => {
  const d = el.closest('.desk-dock'); const more = d.querySelector('.desk-dock-more');
  const r = el.getBoundingClientRect(), b = d.getBoundingClientRect();
  const edge = more && getComputedStyle(more).display !== 'none' ? more.getBoundingClientRect().left : b.right;
  return r.width > 0 && r.left >= b.left - 0.5 && r.right <= edge + 0.5;
}"""


def _press(page: Any, target: Any) -> None:
    """A real gesture: a finger tap on a phone page, a mouse click on a desk."""
    if (page.viewport_size or {}).get("width", 1440) < 720:
        target.tap()
    else:
        target.click()


def _press_dock(page: Any, selector: str) -> None:
    """Swipe the current phone shelf until its named tile can be tapped."""
    target = page.locator(selector)
    target.wait_for(state="attached")
    for _ in range(6):
        if target.evaluate(ON_SHELF_JS):
            _press(page, target)
            return
        box = page.locator(".desk-dock").bounding_box()
        assert box, "the Dock has no touch surface"
        y = box["y"] + box["height"] / 2
        start, end = box["x"] + box["width"] - 20, box["x"] + 20
        cdp = page.context.new_cdp_session(page)
        try:
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": start, "y": y}]})
            for step in range(1, 9):
                cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": start + (end - start) * step / 8, "y": y}]})
                page.wait_for_timeout(16)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        finally:
            cdp.detach()
        page.wait_for_timeout(450)
    raise AssertionError(f"{selector} never came onto the Dock's visible page")


def _row(page: Any, label: str) -> Any:
    """The menu row whose label is `label` (its name also carries a keycap)."""
    return page.locator(".desk-verbbar-menu [role^=menuitem]").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(f"^{re.escape(label)}$")))


class _MenusRig:
    names: list[str] = PROJECTS

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        from holdspeak.db import get_database

        for i, name in enumerate(self.names):
            get_database().projects.create_project(project_id=f"p-door-{i}", name=name, description="", keywords=[])
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(T)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        self._fresh(page)
        return browser, page, errors

    @staticmethod
    def _fresh(page: Any) -> None:
        clear_hub_windows(page, TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        _settle(page)

    def _go_row(self, page: Any, *path: str) -> Callable[[], None]:
        def run() -> None:
            _press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"))
            page.locator(".desk-verbbar-menu").wait_for()
            for label in path:
                _press(page, _row(page, label))
        return run

class TestGoFitsAPhone(_MenusRig):
    # PHILO-15 11 measured Go with one project.
    names = PROJECTS[:1]

    def test_go_fits_a_phone_393(self) -> None:
        """replaces: tests/e2e/test_philo15_11_phone_menus_glass.py::TestThePhoneMenus::test_go_and_new_fit_a_phone_393
        (the fit leg; the rows are vitest's)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                _press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"))
                page.locator(".desk-verbbar-menu").first.wait_for()
                page.wait_for_timeout(500)
                fits = page.evaluate("""() => { const m = document.querySelector('.desk-verbbar-menu');
                  return !!m && m.scrollHeight <= m.clientHeight + 1; }""")
                page.screenshot(path=str(SHOTS / "393-go-fits.png"))
                assert fits, "Go does not fit the phone screen"
                assert errors == [], errors
            finally:
                browser.close()


class TestDoors(_MenusRig):
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_room_falls_to_its_dock_tile_and_comes_back(self, width: int) -> None:
        """replaces: tests/e2e/test_philo17_doors_glass.py::TestDoors::test_one_door_per_application (D6)."""
        from playwright.sync_api import sync_playwright

        room = PROJECTS[0]
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                phone = width < 720
                # Betterment shell S1 (#1259): Go draws the manifest's groups
                # at both widths, so the phone's projects sit in Projects ▸ too.
                self._go_row(page, "Projects", room)()
                page.locator(f".desk-window-shell[aria-label='{room}']").wait_for(timeout=T)
                if phone:
                    # The phone's own way: a Chair window takes the work area and
                    # the window in front falls to its Dock tile (393 has no
                    # Iconify gadget).
                    self._go_row(page, "Needs you")()
                    page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=T)
                else:
                    _press(page, page.locator(f"[aria-label='Iconify {room}']").first)
                seat = page.locator(".desk-dock [data-seat='surface-project-memory']")
                seat.wait_for(timeout=T)
                assert (seat.get_attribute("aria-label") or "").startswith(room), seat.get_attribute("aria-label")
                page.screenshot(path=str(SHOTS / f"{width}-room-seated.png"))
                _press_dock(page, ".desk-dock [data-seat='surface-project-memory']")
                page.locator("#surface-project-memory").wait_for(state="visible", timeout=T)
                page.locator(".desk-dock [data-seat='surface-project-memory']").wait_for(state="detached", timeout=T)
                assert errors == [], errors
            finally:
                browser.close()

    def test_ask_ai_comes_back_after_capture_393(self) -> None:
        """replaces: tests/e2e/test_philo17_doors_glass.py::TestDoors::test_one_door_per_application (D7, Astra r2)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                ask = page.locator(".desk-ask")
                self._go_row(page, "Ask AI")()
                ask.wait_for(state="visible", timeout=T)
                self._go_row(page, "Capture")()
                page.locator(".desk-window-shell[aria-label='Capture']").wait_for(state="visible", timeout=T)
                ask.wait_for(state="hidden", timeout=T)
                self._go_row(page, "Ask AI")()
                ask.wait_for(state="visible", timeout=T)
                page.locator(".desk-ask textarea, .desk-ask [role=textbox]").first.wait_for(state="visible", timeout=T)
                page.screenshot(path=str(SHOTS / "393-ask-back.png"))
                assert errors == [], errors
            finally:
                browser.close()


# ══ lane e2e-high-1 ════════════════════════════════════════

H1_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-03-shots")

H1_TOKEN = "hs202-species"

NOTE_TITLE = "Species rail note"

#: The species marker the library stamps for `variant="chrome"`
#: (`web/src/components/signal/Signal.tsx`).
CHROME = "btn--chrome"

#: What a raw `<button>` would look like: an element with neither the plate
#: nor the chrome marker. Read off the class list in the browser.
_SPECIES_JS = """(selector) => {
  return Array.from(document.querySelectorAll(selector)).map((el) => ({
    tag: el.tagName,
    classes: Array.from(el.classList),
    label: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40),
  }));
}"""

#: A focus ring is a real outline on the FOCUSED element. Chromium resolves
#: :focus-visible in getComputedStyle, but ONLY when focus arrived by the
#: keyboard -- a programmatic `.focus()` does not match it, so every ring
#: assertion below is reached by pressing Tab, never by calling focus().
#:
#: The rings are measured with the browser in its DEFAULT motion state.
#: Under `prefers-reduced-motion: reduce` the desk-chrome controls report
#: `outline-width: 0px` while the plated `.btn` verbs still report 2px. A
#: PAIRED reproduction against the base commit 73758ef3 (same page, same
#: controls, same emulation, three rounds) measured 18/26 ringless stops on
#: the base and 17-18/26 here, with ZERO controls ringless only on this
#: branch: INHERITED, ledgered with an owner, not introduced. Reduced motion
#: is emulated only for the shots.
_RING_JS = """() => {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  const style = getComputedStyle(el);
  return {
    label: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40),
    classes: Array.from(el.classList),
    outlineWidth: parseFloat(style.outlineWidth) || 0,
    outlineStyle: style.outlineStyle,
    boxShadow: style.boxShadow,
    background: style.backgroundColor,
    focusVisible: el.matches(':focus-visible'),
    inDock: Boolean(el.closest('.desk-dock')),
    inWings: Boolean(el.closest('.desk-wings')),
    inRail: Boolean(el.closest('.desk-editor-toolbar')),
  };
}"""

def _tab_into(
    page: Any, selector: str, *, limit: int = 60, start: str | None = None,
) -> dict:
    """Press Tab until focus lands inside `selector`, and return the stop.

    Keyboard, never `.focus()` on the MEASURED element: only a real Tab
    makes Chromium match :focus-visible, and the focus ring is the thing
    under test. `start` seeds the walk programmatically somewhere earlier in
    tab order — used where a Tab from the page head would be swallowed on
    the way (CodeMirror binds Tab to indent, `DeskEditor.tsx:264`).
    """
    if start:
        page.evaluate("(sel) => document.querySelector(sel)?.focus()", start)
    for _ in range(limit):
        page.keyboard.press("Tab")
        landed = page.evaluate(
            """(sel) => {
                 const el = document.activeElement;
                 return Boolean(el && el !== document.body && el.closest(sel));
               }""",
            selector,
        )
        if landed:
            ring = page.evaluate(_RING_JS)
            assert ring is not None
            return ring
    raise AssertionError(f"Tab never reached {selector!r} in {limit} stops")

def _library_species(
    page: Any, selector: str, *, subject: str, chrome_only: bool = False,
) -> list[dict]:
    """Every control matching `selector` is the library Button, not raw HTML.

    A library verb wears one of two marks: the plate (`btn btn--primary` and
    its kin) or the chrome marker (`btn--chrome`, the plate withheld because
    the strip draws its own material). A control wearing NEITHER was drawn by
    a raw `<button>` — UX-CANON A.1's bounce.

    `chrome_only` is for the strips whose whole species is chrome (the menu
    rows, the wing tabs, the editor's rail): there a plate class would
    repaint the strip, so it is the defect, not the proof.
    """
    rows = page.evaluate(_SPECIES_JS, selector)
    assert rows, f"{subject}: nothing matched {selector!r} — the rig is looking at the wrong face"
    raw = [
        row for row in rows
        if row["tag"] != "BUTTON"
        or not ({"btn", CHROME} & set(row["classes"]))
    ]
    assert not raw, f"{subject}: raw controls, not library species: {raw}"
    if chrome_only:
        plated = [row for row in rows if "btn" in row["classes"]]
        assert not plated, (
            f"{subject}: the .btn plate is stamped on a strip that draws its "
            f"own material (28px min-height, a bevel, a centred label): {plated}"
        )
    return rows

#: Story 05's ruling, measured on the live screens: a PLATED Button owns its
#: 44px through a halo, and a CHROME Button is a strip ROW -- so the strip
#: owes it >= 44px at the phone width. This rig fences the strips 03 owns.
TOUCH = 44.0

def _strip_targets(page: Any, selector: str, *, subject: str, pager: str | None = None) -> list[dict]:
    """Every row of a strip is a 44px target, and no two rows overlap.

    Measured at 393 only. Bounding boxes, not CSS: a `min-height` that a
    flex parent squashes is not a target, and only the box on the glass
    says so.

    `pager` names a gadget that is pinned over a paged shelf (the Dock's
    More AppIcons, `dock.css` `.desk-dock > .desk-dock-more`, sticky at the
    right edge: PHILO-13-17 C7). The next page's rows are under it on
    purpose, so it is a 44px target but is not held to the overlap rule.
    """
    rows = page.evaluate(
        """([sel, pager]) => Array.from(document.querySelectorAll(sel)).map(el => {
             const r = el.getBoundingClientRect();
             return {
               label: (el.getAttribute('aria-label') || el.textContent || '')
                        .trim().slice(0, 26),
               classes: Array.from(el.classList).join(' '),
               pager: !!pager && el.matches(pager),
               chrome: el.classList.contains('btn--chrome'),
               h: Math.round(r.height * 10) / 10,
               w: Math.round(r.width * 10) / 10,
               top: r.top, bottom: r.bottom, left: r.left, right: r.right,
             };
           })""",
        [selector, pager],
    )
    assert rows, f"{subject}: nothing matched {selector!r}"
    short = [r for r in rows if r["h"] < TOUCH]
    assert not short, (
        f"{subject}: rows under {TOUCH:.0f}px at 393 — the strip owns its row "
        f"height, and a chrome verb has no plate to own it instead: "
        + ", ".join(f"{r['label']!r} {r['h']}px" for r in short)
    )
    assert any(r["chrome"] for r in rows), (
        f"{subject}: no chrome row here — the rig is measuring the wrong strip"
    )
    # Adjacent rows must not overlap. One pixel is allowed on purpose: the
    # wing segments butt with a shared hairline (`pullout.css`,
    # `.desk-wing + .desk-wing { margin-left: -1px }`).
    overlaps = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a["pager"] or b["pager"]:
                continue
            dx = min(a["right"], b["right"]) - max(a["left"], b["left"])
            dy = min(a["bottom"], b["bottom"]) - max(a["top"], b["top"])
            if dx > 1 and dy > 1:
                overlaps.append(
                    f"{a['label']!r} x {b['label']!r} ({dx:.1f}x{dy:.1f}px)"
                )
    assert not overlaps, (
        f"{subject}: rows overlap after the 44px growth — a taller target that "
        f"eats its neighbour is not a target: " + ", ".join(overlaps)
    )
    return rows

def _seed_meeting() -> None:
    """One finalized meeting, so the Meetings stream draws a real row.

    The row BODY is the control this story converted from a
    `div role="button"` to the library Button; an empty stream would leave
    that conversion NOT ASSESSED.
    """
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'error', 'finalized', 'desktop')",
            (
                "m-species",
                (now - timedelta(hours=2)).isoformat(),
                (now - timedelta(hours=1, minutes=30)).isoformat(),
                "Species stream meeting",
                1800.0,
            ),
        )
        conn.commit()

def _shot(page: Any, name: str) -> None:
    """Shoot with motion stilled, then hand the page back as it was."""
    page.emulate_media(reduced_motion="reduce")
    _settle(page)
    page.screenshot(path=str(H1_SHOTS / name))
    page.emulate_media(reduced_motion="no-preference")

def _arrive(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={H1_TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=H1_TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=H1_TOKEN)
    _normal_chair(page)
    page.locator(".desk-dock").wait_for(timeout=10_000)
    _settle(page)

class TestSharedControlsAreSpecies:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=H1_TOKEN)
        _seed_meeting()
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
    def test_menus_dock_and_wings(self, width: int, height: int) -> None:
        from playwright.sync_api import sync_playwright

        H1_SHOTS.mkdir(parents=True, exist_ok=True)
        tag = str(width)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            # ── the dock: every chip is the species ────────────────────
            _library_species(page, ".desk-dock button", subject="the dock")
            if width <= 720:
                _strip_targets(page, ".desk-dock button", subject="the dock",
                               pager=".desk-dock-more")
            _shot(page, f"dock-{tag}.png")

            # ── the dock tab-walks in DOM order, every stop with a ring ─
            order = page.evaluate(
                # Every Tab stop of the dock in DOM order: the AppIcons, the
                # nested gadgets, and at 393 the More AppIcons gadget (last in
                # the DOM; `display: none` at 1440, dock.css). Only the stops
                # on the glass: a button that is not drawn takes no Tab.
                """() => Array.from(
                     document.querySelectorAll('.desk-dock button')
                   ).filter(el => el.checkVisibility() && !el.disabled && el.tabIndex >= 0)
                    .map(el => (el.getAttribute('aria-label') || el.textContent || '')
                                 .trim().slice(0, 40))"""
            )
            assert len(order) >= 3, order
            _tab_into(page, ".desk-dock")
            walked = []
            rings = []
            for _ in range(len(order)):
                ring = page.evaluate(_RING_JS)
                assert ring is not None, "focus fell off the dock"
                if not ring["inDock"]:
                    break
                walked.append(ring["label"])
                rings.append(ring)
                page.keyboard.press("Tab")
            assert walked == order, (
                f"the dock's Tab order left DOM order: {walked} != {order}"
            )
            # Measured in the browser's DEFAULT motion state. Under
            # `prefers-reduced-motion: reduce` these same controls compute a
            # zero outline — on the base commit 73758ef3 identically (paired
            # reproduction in the story's assets), so it is inherited and
            # ledgered, not this story's to assert here.
            ringless = [
                r for r in rings
                if r["outlineWidth"] <= 0 or r["outlineStyle"] == "none"
            ]
            assert not ringless, f"dock stops with no focus ring: {ringless}"

            # ── the menu: library rows, arrows rove, Escape closes ─────
            # At phone width the bar folds to ONE title and every verb rides
            # the Go menu (`DeskMenuBar.tsx:103`, HS-202-02), so the rig
            # opens the door the width actually has.
            name = "Desk" if width > 720 else "Go"
            title = page.locator(".desk-verbbar-title", has_text=name)
            title.wait_for(timeout=10_000)
            title.click()
            menu = page.locator(f'.desk-verbbar-menu[aria-label="{name} menu"]')
            menu.wait_for(timeout=10_000)
            _library_species(
                page,
                ".desk-work-menu [role=menuitem], .desk-work-menu [role=menuitemcheckbox],"
                " .desk-work-menu [role=menuitemradio]",
                subject=f"the {name} menu",
                chrome_only=True,
            )
            _shot(page, f"menu-open-{tag}.png")

            first = page.evaluate(_RING_JS)
            assert first is not None, "the menu did not take focus when it opened"
            page.keyboard.press("ArrowDown")
            second = page.evaluate(_RING_JS)
            assert second is not None and second["label"] != first["label"], (
                f"ArrowDown did not rove the {name} menu: {first} -> {second}"
            )
            page.keyboard.press("ArrowUp")
            back = page.evaluate(_RING_JS)
            assert back is not None and back["label"] == first["label"], (
                f"ArrowUp did not walk back: {back} != {first}"
            )
            page.keyboard.press("Escape")
            menu.wait_for(state="detached")
            # Escape closes the whole panel. Where focus LANDS afterwards is
            # NOT ASSESSED here: `DeskMenuBar.tsx:134-144` renders `WorkMenu`
            # without `returnFocus` (`DeskMenu.tsx:455` accepts it), at the
            # base commit 73758ef3 as well, so focus falls to the body — a
            # pre-existing gap this story did not cause and does not fix. It
            # is ledgered in the phase status with an owner.
            assert page.evaluate(
                "() => !document.querySelector('.desk-verbbar-menu')"
            ), f"the {name} menu survived Escape"

            # ── the wings: one roving Tab stop, arrows walk, species ────
            # PHILO-17 ("A meeting opens in one window"): the Meetings window
            # is the list (two wings that fit at 393); Speak keeps four wings
            # and a door, the strip that folds.
            page.evaluate(
                """([key]) => sessionStorage.setItem(
                     "hs.desk.staged-surface-open", JSON.stringify({key}))""",
                ["dictate"],
            )
            page.reload(wait_until="load")
            _normal_chair(page)
            # PHILO-13-11 (C1, §3a; owner-ratified 2026-10-02): at 393 a wing
            # strip that does not fit the head's one 44 px row is ONE strip
            # menu Button (the current face + ▾). The species, the 44 px
            # target and the keyboard grammar are fenced on that Button and
            # its menu; the dock checks with a window open stay as they were.
            if width <= 720:
                strip = page.locator(".desk-wings .surface-strip-menu")
                strip.wait_for(timeout=15_000)
                _settle(page)
                assert strip.count() == 1, "the wings did not fold into ONE strip menu at 393"
                _library_species(page, ".desk-wings button", subject="the wing strip menu", chrome_only=True)
                _strip_targets(page, ".desk-wings button", subject="the wing strip menu")
                reset = page.locator(".desk-dock-reset")
                assert reset.count() == 0, (
                    "the retired overview/reset keys returned to the Dock"
                )
                _strip_targets(page, ".desk-dock button", subject="the dock, with a window open",
                               pager=".desk-dock-more")
                _shot(page, f"wings-{tag}.png")
                before = strip.text_content().strip()
                ring = _tab_into(page, ".desk-wings")
                assert ring["outlineWidth"] > 0, f"the strip menu has no focus ring: {ring}"
                page.keyboard.press("Enter")
                wing_menu = page.get_by_role("menu", name="Window faces", exact=True)
                wing_menu.wait_for(timeout=5_000)
                checked = wing_menu.locator("[aria-checked=true]").all_inner_texts()
                assert len(checked) == 1, f"the strip menu must check ONE current face: {checked}"
                # the CHOICES own the target, not only the trigger (Astra counsel
                # on #730): every row of the open menu, checkable rows included
                choices = wing_menu.locator("[role^=menuitem]")
                assert choices.count() >= 5, f"the strip menu drew {choices.count()} choices"
                assert wing_menu.get_by_role("menuitemcheckbox").count() >= 4
                _strip_targets(page, '[role=menu][aria-label="Window faces"] [role^=menuitem]', subject="the strip menu's choices")
                # a keyboard open puts focus on a row (DeskMenu autoFocus)
                page.wait_for_function(
                    "() => Boolean(document.activeElement?.closest('[role=menu][aria-label=\"Window faces\"]'))",
                    timeout=5_000,
                )
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
                page.wait_for_timeout(400)
                after = page.locator(".desk-wings .surface-strip-menu").text_content().strip()
                assert after and after != before, f"the keyboard did not walk the faces: {before} -> {after}"
                tabs = page.locator(".desk-wings-tabs [role=tab]")
            else:
                tabs = page.locator(".desk-wings-tabs [role=tab]")
                tabs.first.wait_for(timeout=15_000)
                _settle(page)
            if width <= 720:
                pass
            elif tabs.count() >= 2:
                _library_species(
                    page, ".desk-wings button", subject="the wing bar",
                    chrome_only=True,
                )
                if width <= 720:
                    _strip_targets(
                        page, ".desk-wings button", subject="the wing bar",
                    )
                    # The dock again, WITH a window open: `Overview` and
                    # `Reset layout` (`.desk-dock-reset`, measured 22px) and
                    # the window chip only exist once something is open, so
                    # the arrival pass above cannot see them.
                    reset = page.locator(".desk-dock-reset")
                    assert reset.count() == 0, (
                        "the retired overview/reset keys returned to the Dock"
                    )
                    _strip_targets(
                        page, ".desk-dock button",
                        subject="the dock, with a window open",
                        pager=".desk-dock-more",
                    )
                _shot(page, f"wings-{tag}.png")
                stops = page.evaluate(
                    """() => Array.from(
                         document.querySelectorAll('.desk-wings-tabs [role=tab]')
                       ).map(el => el.tabIndex)"""
                )
                assert stops.count(0) == 1, (
                    f"the wing strip must hold ONE Tab stop, not {stops}"
                )
                selected = page.evaluate(
                    """() => document.querySelector(
                         '.desk-wings-tabs [role=tab][aria-selected=true]'
                       )?.textContent?.trim() || null"""
                )
                ring = _tab_into(page, ".desk-wings-tabs")
                assert ring["outlineWidth"] > 0, (
                    f"the active wing has no focus ring: {ring}"
                )
                page.keyboard.press("ArrowRight")
                moved = page.evaluate(
                    """() => document.querySelector(
                         '.desk-wings-tabs [role=tab][aria-selected=true]'
                       )?.textContent?.trim() || null"""
                )
                assert moved and moved != selected, (
                    f"ArrowRight did not walk the wings: {selected} -> {moved}"
                )
            else:
                pytest.fail(
                    "the Speak window drew fewer than two wings; "
                    "the wing keyboard grammar was NOT ASSESSED"
                )

            # The Meetings list holds the rows (PHILO-17).
            page.evaluate(
                """() => sessionStorage.setItem(
                     "hs.desk.staged-surface-open", JSON.stringify({key: 'review-meetings'}))""")
            page.reload(wait_until="load")
            _normal_chair(page)
            page.locator("#surface-meetings .object-list-open").first.wait_for(timeout=15_000)
            # ── the Meetings row body: a real Button that draws as a div ─
            # It WAS `<div role="button" tabIndex={0}>` (the last raw control
            # on the Meetings stream, `CatalogRail.tsx:211` in the census).
            # A <button> arrives wearing the UA plate — buttonface fill, an
            # outset border, 1px 6px of padding — so `.meetings-stream-row-body`
            # now erases all three. Read it back off the glass: the row draws
            # what the div drew.
            plate = page.evaluate(
                """() => {
                     const el = document.querySelector('#surface-meetings .object-list-open');
                     if (!el) return null;
                     const s = getComputedStyle(el);
                     return {
                       tag: el.tagName,
                       background: s.backgroundColor,
                       borderTopWidth: s.borderTopWidth,
                       paddingTop: s.paddingTop,
                       paddingLeft: s.paddingLeft,
                       textAlign: s.textAlign,
                       display: s.display,
                       font: s.font,
                     };
                   }"""
            )
            assert plate is not None, (
                "the Meetings stream drew no row: the row-body conversion "
                "was NOT ASSESSED"
            )
            assert plate["tag"] == "BUTTON", plate
            assert plate["background"] in ("rgba(0, 0, 0, 0)", "transparent"), plate
            assert plate["borderTopWidth"] == "0px", plate
            # Window grammar: the dense list row's own inset, not the UA's 1px 6px.
            assert plate["paddingTop"] == "4px", plate
            assert plate["paddingLeft"] == "10px", plate
            assert plate["textAlign"] == "left", plate
            assert plate["display"] == "flex", plate

            real_errors = [e for e in errors if "ResizeObserver" not in e]
            assert not real_errors, real_errors
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
    def test_the_note_editor_and_footer_use_the_library(self, width: int, height: int) -> None:
        """The one note window has its direct editor and library footer verbs."""
        from playwright.sync_api import sync_playwright

        H1_SHOTS.mkdir(parents=True, exist_ok=True)
        tag = str(width)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)
            # Q8 adopts ordinary notes into the one note window. Seed the
            # real body field so the current editor must preserve its words.
            _api(
                page, "POST", "/api/notes",
                {"title": NOTE_TITLE, "body_markdown": "The note uses the library."},
                token=H1_TOKEN,
            )
            notes = _api(page, "GET", "/api/notes", token=H1_TOKEN)["notes"]
            note_id = str(
                next(n for n in notes if n.get("title") == NOTE_TITLE)["id"]
            )

            # The product's own door to a saved note: ⌘K, then Enter.
            page.locator(".desk-tools-launch").click()
            shelf = page.get_by_role("region", name="Search", exact=True)
            field = shelf.get_by_role(
                "combobox", name="Find, open or ask", exact=True
            )
            field.fill(NOTE_TITLE)
            target = shelf.locator(f'[id="desk-palette-option-note:{note_id}"]')
            target.wait_for(timeout=10_000)
            field.press("Enter")
            note = page.get_by_role("region", name=NOTE_TITLE, exact=True)
            note.wait_for(timeout=15_000)
            editor = note.locator(".cm-content[contenteditable=true]")
            editor.wait_for(state="visible", timeout=15000)
            assert editor.inner_text().strip() == "The note uses the library."
            assert note.locator(".desk-editor-toolbar").count() == 0
            # Window grammar (2026-10-24): the note's verbs are its toolbar.
            rows = _library_species(
                page, ".thought-workspace-window .thought-note-toolbar .kit-toolbar-verbs button",
                subject="the note toolbar",
            )
            expected = {"Ask about this", "Find the tasks", "Send…"}
            if width > 720:
                expected.add("Done")
            assert {row["label"] for row in rows} == expected, rows
            assert note.get_by_role("button", name="Done", exact=True).count() == 1
            _shot(page, f"note-editor-{tag}.png")
            ring = _tab_into(
                page, ".thought-workspace-window .thought-note-toolbar .kit-toolbar-verbs",
                start=".thought-workspace-window .desk-pullout-head button", limit=12,
            )
            assert ring["outlineWidth"] > 0, f"no keyboard focus ring on the toolbar: {ring}"
            assert page.evaluate("() => Boolean(document.activeElement?.closest('.thought-note-toolbar .kit-toolbar-verbs'))")

            real_errors = [e for e in errors if "ResizeObserver" not in e]
            assert not real_errors, real_errors
            browser.close()
