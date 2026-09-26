"""PHILO-8-01 half A -- the free zone name, the Chair without New Zone, and no
stale rename field, fenced AS RENDERED through the real hub at 1440 and 393.

Red on main 267f692a:
- the second New Zone posts ``{"name": "New zone"}`` again and the hub answers
  ``409 zone_name_taken`` (``web/src/desk/store/dataSlice.ts:322``; FINDING S1);
- a zone the owner named "new  ZONE 2" is not skipped: the next New Zone 409s;
- the Chair's palette and menus offer New Zone, a Floor-only verb
  (``web/src/desk/verbRegistry.ts:203-212``; the owner's Q2 (c));
- a New Zone on the list, then Spatial view, shows a stale rename field
  (FINDING Finding 1, "Floor list -> Spatial view").
The leg "floor-chair-floor" is a guard, GREEN on main: leaving the Floor blurs
the open field, and the blur commits and closes it. It stays to hold the face
change rule (DeskApp.tsx) once the list field exists.
"""
from __future__ import annotations

import unicodedata
import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the zone-name glass needs Playwright")

TOKEN = "philo8-zone-name"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-01-shots")
WIDTHS = [1440, 393]


def _norm(raw: str) -> str:
    """The hub's rule (holdspeak/db/primitives.py:60-68), for the assertions."""
    s = re.sub(r"\s+", " ", str(raw or "").strip())
    return unicodedata.normalize("NFC", s).casefold()


def _palette(page: Any, query: str) -> None:
    page.locator("[aria-controls=desk-tool-shelf]").click()
    page.locator("[aria-controls=desk-palette-listbox]").fill(query)


def _close_palette(page: Any) -> None:
    # The deck's Escape ladder: the query first, then the panel.
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    page.wait_for_function(
        "() => document.querySelector('[aria-controls=desk-tool-shelf]')?.getAttribute('aria-expanded') !== 'true'",
        timeout=15_000,
    )


def _view(page: Any) -> str:
    return "list" if page.locator(".desk-listmode").count() else "spatial"


def _ensure_view(page: Any, want: str) -> None:
    if _view(page) != want:
        _palette(page, "view")
        page.locator("[id='desk-palette-option-desk.toggle-view']").click()
    if want == "list":
        page.locator(".desk-listmode").wait_for(timeout=15_000)
    else:
        page.locator(".desk-listmode").wait_for(state="detached", timeout=15_000)


def _new_zone(page: Any) -> int:
    """Press New Zone from the palette; return the hub's status for the create."""
    _palette(page, "New Zone")
    with page.expect_response(
        lambda r: r.url.split("?")[0].endswith("/api/directories") and r.request.method == "POST",
        timeout=15_000,
    ) as info:
        page.locator("[id='desk-palette-option-desk.new-zone']").click()
    return info.value.status


def _zone_names(page: Any) -> list[str]:
    return [d["name"] for d in _api(page, "GET", "/api/directories", token=TOKEN)["directories"]]


class TestZoneNameGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[int], list[str]]:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 900 if width > 720 else 852})
        statuses: list[int] = []
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on(
            "response",
            lambda r: statuses.append(r.status)
            if r.url.split("?")[0].endswith("/api/directories") and r.request.method == "POST"
            else None,
        )
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        return browser, page, statuses, errors

    @pytest.mark.e2e
    @pytest.mark.parametrize("face", ["spatial", "list"])
    @pytest.mark.parametrize("width", WIDTHS)
    def test_two_new_zone_presses_make_two_zones(self, width: int, face: str) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, statuses, errors = self._open(pw, width)
            try:
                page.locator("[data-testid=chair-floor-toggle]").click()
                _ensure_view(page, face)
                first = _new_zone(page)
                second = _new_zone(page)
                page.screenshot(path=str(SHOTS / f"two-zones-{face}-{width}.png"))
                names = _zone_names(page)
                assert statuses.count(409) == 0, f"409s in the network log: {statuses}"
                assert (first, second) == (201, 201), (first, second, statuses)
                # The fresh hub seeds its own zones (Inbox, Decisions, …); only the made ones count.
                made = sorted(_norm(n) for n in names if _norm(n).startswith("new zone"))
                assert made == ["new zone", "new zone 2"], names
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_name_the_owner_chose_is_skipped_not_renamed(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, statuses, errors = self._open(pw, width)
            try:
                _api(page, "POST", "/api/directories", {"name": "New zone"}, token=TOKEN)
                own = _api(page, "POST", "/api/directories", {"name": "new  ZONE 2"}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=chair-floor-toggle]").click()
                _ensure_view(page, "list")
                assert _new_zone(page) == 201, statuses
                names = _zone_names(page)
                assert statuses.count(409) == 0, statuses
                assert "New zone 3" in names, names
                owned = [d for d in _api(page, "GET", "/api/directories", token=TOKEN)["directories"]
                         if d["id"] == own["directory"]["id"]]
                assert owned and owned[0]["name"] == "new  ZONE 2", owned
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_chair_does_not_offer_new_zone(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, statuses, errors = self._open(pw, width)
            try:
                # The Chair's palette.
                _palette(page, "")
                page.locator("[id='desk-palette-option-desk.new-note']").wait_for(timeout=15_000)
                assert page.locator("[id='desk-palette-option-desk.new-zone']").count() == 0
                page.locator("[aria-controls=desk-palette-listbox]").fill("New Zone")
                page.wait_for_timeout(300)
                assert page.locator("[id='desk-palette-option-desk.new-zone']").count() == 0
                page.screenshot(path=str(SHOTS / f"chair-palette-{width}.png"))
                _close_palette(page)
                # The Chair's menu bar (1440: the Desk menu; 393: the one phone door).
                menu = "desk" if width > 720 else "go"
                page.locator(f".desk-verbbar-item[data-menu-id={menu}] button").first.click()
                page.get_by_role("menuitem", name=re.compile("New Note")).first.wait_for(timeout=15_000)
                assert page.get_by_role("menuitem", name=re.compile("New Zone")).count() == 0
                page.screenshot(path=str(SHOTS / f"chair-menu-{width}.png"))
                page.keyboard.press("Escape")
                # The Floor still offers it.
                page.locator("[data-testid=chair-floor-toggle]").click()
                _palette(page, "New Zone")
                page.locator("[id='desk-palette-option-desk.new-zone']").wait_for(timeout=15_000)
                page.keyboard.press("Escape")
                assert statuses == [], statuses
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("leg", ["list-to-spatial", "floor-chair-floor"])
    @pytest.mark.parametrize("width", WIDTHS)
    def test_no_stale_rename_field_after_a_face_change(self, width: int, leg: str) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, statuses, errors = self._open(pw, width)
            try:
                page.locator("[data-testid=chair-floor-toggle]").click()
                if leg == "list-to-spatial":
                    # FINDING Finding 1: the list, then Spatial view.
                    _ensure_view(page, "list")
                    assert _new_zone(page) == 201
                    # C1 (Astra-role check r1): wait for the create to LAND before the
                    # face change. The new zone's row appears only after the post-create
                    # refresh, and createPrimitive starts the rename in the same turn
                    # (dataSlice.ts createPrimitive), so on main the stale state is set
                    # by now and the Floor draws it at mount. A fixed sleep let a slow
                    # refresh hide the defect (green on main under load).
                    # Main: the row's name button; half B: the row's name field.
                    page.get_by_role("button", name="New zone zone", exact=True).or_(
                        page.locator(".desk-listmode input.desk-zone-rename")
                    ).first.wait_for(timeout=30_000)
                    _ensure_view(page, "spatial")
                    page.locator(".desk-world").wait_for(timeout=15_000)
                else:
                    _ensure_view(page, "spatial")
                    assert _new_zone(page) == 201
                    # The field waits for the post-create refresh (~4.7 s on this rig at 1440).
                    page.locator("input.desk-zone-rename").wait_for(timeout=20_000)
                    page.locator("[data-testid=chair-floor-toggle]").click()
                    page.locator(".chair").wait_for(timeout=15_000)
                    page.locator("[data-testid=chair-floor-toggle]").click()
                    page.locator(".chair").wait_for(state="detached", timeout=15_000)
                # The Floor is mounted and the create has landed: a stale field would
                # already be drawn. Give it a render beat, then it must be absent.
                page.wait_for_timeout(1_000)
                assert page.locator("input.desk-zone-rename").count() == 0, f"stale rename field: {leg}"
                page.screenshot(path=str(SHOTS / f"no-stale-{leg}-{width}.png"))
                assert statuses.count(409) == 0, statuses
            finally:
                browser.close()
