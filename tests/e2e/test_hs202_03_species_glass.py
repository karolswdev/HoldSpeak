"""HS-202-03 — the shared controls are library species, on real glass.

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
     moves the selected wing; one rail stop computes a non-zero outline.
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

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    REPO,
    _api,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="HS-202 glass needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-03-shots"
TOKEN = "hs202-species"
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
    page.screenshot(path=str(SHOTS / name))
    page.emulate_media(reduced_motion="no-preference")


def _arrive(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)
    page.locator(".desk-dock").wait_for(timeout=10_000)
    _settle(page)


class TestSharedControlsAreSpecies:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed_meeting()
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
    def test_menus_dock_and_wings(self, width: int, height: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        tag = str(width)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            # ── the dock: every chip is the species ────────────────────
            _library_species(page, ".desk-dock button", subject="the dock")
            _shot(page, f"dock-{tag}.png")

            # ── the dock tab-walks in DOM order, every stop with a ring ─
            order = page.evaluate(
                """() => Array.from(
                     document.querySelectorAll('.desk-dock > button')
                   ).map(el => (el.getAttribute('aria-label') || '').trim())"""
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
            menu = page.get_by_role("menu", name=f"{name} menu", exact=True)
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
            page.get_by_role("menu", name=f"{name} menu", exact=True).wait_for(
                state="detached"
            )
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
            page.evaluate(
                """([key]) => sessionStorage.setItem(
                     "hs.desk.staged-surface-open", JSON.stringify({key}))""",
                ["review-meetings"],
            )
            page.reload(wait_until="load")
            _normal_chair(page)
            tabs = page.locator(".desk-wings-tabs [role=tab]")
            tabs.first.wait_for(timeout=15_000)
            _settle(page)
            if tabs.count() >= 2:
                _library_species(
                    page, ".desk-wings button", subject="the wing bar",
                    chrome_only=True,
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
                    "the Meetings window drew fewer than two wings; "
                    "the wing keyboard grammar was NOT ASSESSED"
                )

            # ── the Meetings row body: a real Button that draws as a div ─
            # It WAS `<div role="button" tabIndex={0}>` (the last raw control
            # on the Meetings stream, `CatalogRail.tsx:211` in the census).
            # A <button> arrives wearing the UA plate — buttonface fill, an
            # outset border, 1px 6px of padding — so `.meetings-stream-row-body`
            # now erases all three. Read it back off the glass: the row draws
            # what the div drew.
            plate = page.evaluate(
                """() => {
                     const el = document.querySelector('.meetings-stream-row-body');
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
            assert plate["paddingTop"] == "0px", plate
            assert plate["paddingLeft"] == "0px", plate
            assert plate["textAlign"] == "left", plate
            assert plate["display"] == "flex", plate

            real_errors = [e for e in errors if "ResizeObserver" not in e]
            assert not real_errors, real_errors
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
    def test_the_editor_rail(self, width: int, height: int) -> None:
        """The note editor's formatting rail: eleven verbs, one species."""
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        tag = str(width)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)
            # An ORDINARY note: the rail rides the note editor
            # (`NoteEditor.tsx:143`). The thought workspace deliberately
            # hides it (`ThoughtDocumentPane.tsx:57 showToolbar={false}`),
            # so the thought door is the wrong door for this subject.
            _api(
                page, "POST", "/api/notes",
                {"title": NOTE_TITLE, "body": "The rail is the library."},
                token=TOKEN,
            )
            notes = _api(page, "GET", "/api/notes", token=TOKEN)["notes"]
            note_id = str(
                next(n for n in notes if n.get("title") == NOTE_TITLE)["id"]
            )

            # The product's own door to a saved note: ⌘K, then Enter.
            page.locator(".desk-tools-launch").click()
            shelf = page.get_by_role("region", name="Tools and Desk search", exact=True)
            field = shelf.get_by_role(
                "combobox", name="Search tools and Desk items", exact=True
            )
            field.fill(NOTE_TITLE)
            target = shelf.locator(f'[id="desk-palette-option-note:{note_id}"]')
            target.wait_for(timeout=10_000)
            field.press("Enter")
            note = page.get_by_role("region", name=NOTE_TITLE, exact=True)
            note.wait_for(timeout=15_000)
            # The note opens READ-first; its own verb opens the editor
            # (`NotePullout.tsx:434 onAction={() => openEditor(o.id)}`).
            note.get_by_role("button", name="Start writing", exact=True).click()
            rail = page.locator(".desk-editor-toolbar")
            rail.first.wait_for(timeout=20_000)
            _settle(page)

            rows = _library_species(
                page, ".desk-editor-toolbar button", subject="the editor's rail",
                chrome_only=True,
            )
            assert len(rows) >= 11, f"the rail lost verbs: {len(rows)}"
            _shot(page, f"editor-rail-{tag}.png")

            # The rail is a toolbar of real buttons: each one focuses and
            # draws a ring (the raw markup did too; nothing moved).
            ring = _tab_into(
                page, ".desk-editor-toolbar", start=".desk-light-close", limit=20,
            )
            assert ring["outlineWidth"] > 0, f"no focus ring on the rail: {ring}"
            assert ring["inRail"], ring

            real_errors = [e for e in errors if "ResizeObserver" not in e]
            assert not real_errors, real_errors
            browser.close()
