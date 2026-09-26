"""PHILO-8-01 half B -- the list's in-row zone name field, the NAME TAKEN chip on
both faces, the failed save, the late refusal, and F2 on a zone row, fenced AS
RENDERED through the real hub at 1440 and 393.

The owner ratified the canvas on 2026-09-26 (AskUserQuestion): "Ratify as
drawn"; "Chip on the list and the Floor"; "Keep F2 on zone rows"
(pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-01-canvas/).

Red on main 808a9c30: the list draws no field at all (New Zone makes the zone
and nothing opens); the Floor shows an 11 px sentence, not the chip; a 422 or
a network failure reverts without a word; a refusal that lands after the field
closed is silent; F2 on a zone row does nothing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the list-rename glass needs Playwright")

TOKEN = "philo8-list-rename"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-01-shots")
WIDTHS = [1440, 393]
T = 15_000

_FIELD_JS = """() => {
  const input = document.querySelector('input.desk-zone-rename');
  if (!input) return null;
  const row = input.closest('.desk-zone-rename-row');
  const small = [];
  const walker = document.createTreeWalker(row, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || /^[✗✓●○]$/.test(t)) continue;
    const el = n.parentElement;
    if (!el.getBoundingClientRect().width) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 12) small.push({text: t, fs});
  }
  const chip = row.querySelector('[data-testid=zone-name-refused]');
  return {
    value: input.value,
    focused: document.activeElement === input,
    selStart: input.selectionStart, selEnd: input.selectionEnd,
    inListRow: !!input.closest('.desk-sortable-table-row'),
    chip: chip ? chip.innerText.replace(/\\s+/g, ' ').trim() : null,
    code: row.querySelector('[data-code]')?.dataset.code ?? null,
    small,
    sentence: !!document.querySelector('.desk-zone-rename-error'),
  };
}"""

_KIND_X_JS = """() => {
  const th = [...document.querySelectorAll('.desk-listmode th')].find(t => /^KIND/i.test((t.innerText || '').trim()));
  return th ? Math.round(th.getBoundingClientRect().left) : null;
}"""


def _palette(page: Any, query: str) -> None:
    page.locator("[aria-controls=desk-tool-shelf]").click()
    page.locator("[aria-controls=desk-palette-listbox]").fill(query)


def _ensure_view(page: Any, want: str) -> None:
    is_list = page.locator(".desk-listmode").count() > 0
    if is_list != (want == "list"):
        _palette(page, "view")
        page.locator("[id='desk-palette-option-desk.toggle-view']").click()
    if want == "list":
        page.locator(".desk-listmode").wait_for(timeout=T)
    else:
        page.locator(".desk-world").wait_for(timeout=T)


def _new_zone(page: Any) -> None:
    _palette(page, "New Zone")
    with page.expect_response(
        lambda r: r.url.split("?")[0].endswith("/api/directories") and r.request.method == "POST",
        timeout=T,
    ) as info:
        page.locator("[id='desk-palette-option-desk.new-zone']").click()
    assert info.value.status == 201


def _field(page: Any, timeout: int = 30_000) -> dict[str, Any]:
    page.locator("input.desk-zone-rename").wait_for(timeout=timeout)
    page.wait_for_timeout(200)
    return page.evaluate(_FIELD_JS)


def _names(page: Any) -> list[str]:
    return [d["name"] for d in _api(page, "GET", "/api/directories", token=TOKEN)["directories"]]


class TestListRenameGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    def _open(self, pw: Any, width: int, face: str) -> tuple[Any, Any, list[tuple[str, int]]]:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 900 if width > 720 else 852})
        puts: list[tuple[str, int]] = []
        page.on("response", lambda r: puts.append((r.url.split("?")[0].rsplit("/", 1)[-1], r.status))
                if r.request.method == "PUT" and "/api/directories/" in r.url else None)
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.locator("[data-testid=chair-floor-toggle]").click()
        _ensure_view(page, face)
        return browser, page, puts

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_list_field_opens_writes_and_keeps(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, puts = self._open(pw, width, "list")
            try:
                kind_x_before = page.evaluate(_KIND_X_JS)
                # New Zone -> the field in the new row, focused, the name selected.
                _new_zone(page)
                f = _field(page)
                assert f["inListRow"], f
                assert f["value"] == "New zone" and f["focused"], f
                assert (f["selStart"], f["selEnd"]) == (0, len("New zone")), f
                assert page.evaluate(_KIND_X_JS) == kind_x_before, "the field moved the columns"
                page.screenshot(path=str(SHOTS / f"list-field-open-{width}.png"))
                # Typing replaces; Enter writes.
                page.keyboard.type("Platform team")
                page.keyboard.press("Enter")
                page.locator("input.desk-zone-rename").wait_for(state="detached", timeout=T)
                assert puts and puts[-1][1] == 200, puts
                assert "Platform team" in _names(page)
                page.get_by_role("button", name="Platform team zone", exact=True).wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / f"list-enter-written-{width}.png"))
                # Escape keeps the default name; no PUT.
                n_puts = len(puts)
                _new_zone(page)
                _field(page)
                page.keyboard.press("End")
                page.keyboard.type(" draft")
                page.keyboard.press("Escape")
                page.locator("input.desk-zone-rename").wait_for(state="detached", timeout=T)
                page.wait_for_timeout(500)
                assert len(puts) == n_puts, puts
                # "New zone" was freed by the rename above, so this zone took it back.
                assert _names(page).count("New zone") == 1 and "Platform team" in _names(page)
                # Spaces only keeps the name; no PUT.
                _new_zone(page)
                _field(page)
                page.keyboard.type("   ")
                page.keyboard.press("Enter")
                page.locator("input.desk-zone-rename").wait_for(state="detached", timeout=T)
                page.wait_for_timeout(500)
                assert len(puts) == n_puts, puts
                assert "New zone 2" in _names(page)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_taken_name_shows_the_chip_on_the_list(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, puts = self._open(pw, width, "list")
            try:
                kind_x_before = page.evaluate(_KIND_X_JS)
                _new_zone(page)
                _field(page)
                page.keyboard.type("Inbox")
                page.keyboard.press("Enter")
                page.locator("[data-testid=zone-name-refused]").wait_for(timeout=T)
                f = page.evaluate(_FIELD_JS)
                assert puts[-1][1] == 409, puts
                assert f["chip"] == "✗ NAME TAKEN" and f["code"] == "zone_name_taken", f
                assert f["focused"] and f["value"] == "Inbox", f
                assert f["small"] == [] and not f["sentence"], f
                assert page.evaluate(_KIND_X_JS) == kind_x_before, "the chip moved the columns"
                page.screenshot(path=str(SHOTS / f"list-name-taken-{width}.png"))
                assert "New zone" in _names(page)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_taken_name_shows_the_chip_on_the_floor(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, puts = self._open(pw, width, "spatial")
            try:
                _new_zone(page)
                _field(page)
                page.keyboard.type("Inbox")  # the name opens selected: typing replaces it
                page.keyboard.press("Enter")
                page.locator("[data-testid=zone-name-refused]").wait_for(timeout=T)
                f = page.evaluate(_FIELD_JS)
                assert puts[-1][1] == 409, puts
                assert f["chip"] == "✗ NAME TAKEN" and f["code"] == "zone_name_taken", f
                assert f["focused"], f
                assert f["small"] == [] and not f["sentence"], f
                page.screenshot(path=str(SHOTS / f"floor-name-taken-{width}.png"))
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("failure", ["422", "network"])
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_failed_save_shows_in_the_chip_slot(self, width: int, failure: str) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, puts = self._open(pw, width, "list")
            try:
                _new_zone(page)
                _field(page)
                if failure == "422":
                    page.keyboard.type("x" * 65)  # the hub refuses a name over 64 characters
                else:
                    page.route("**/api/directories/*", lambda route: route.abort()
                               if route.request.method == "PUT" else route.continue_())
                    page.keyboard.type("Offline zone")
                page.keyboard.press("Enter")
                page.locator("[data-testid=zone-name-refused]").wait_for(timeout=T)
                f = page.evaluate(_FIELD_JS)
                assert f["chip"] == "✗ NOT SAVED", f
                assert f["focused"], f
                if failure == "422":
                    assert puts[-1][1] == 422, puts
                assert "New zone" in _names(page)
                page.screenshot(path=str(SHOTS / f"list-not-saved-{failure}-{width}.png"))
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_refusal_after_the_field_closed_goes_to_the_write_receipt(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, puts = self._open(pw, width, "spatial")
            try:
                _new_zone(page)
                _field(page)
                page.keyboard.type("Inbox")  # the name opens selected: typing replaces it
                # Leave the face: the blur writes, the field goes, then the hub refuses.
                page.locator("[data-testid=chair-floor-toggle]").click()
                page.locator(".chair").wait_for(timeout=T)
                receipt = page.locator(".write-receipt").filter(has_text="RENAME ZONE")
                receipt.first.wait_for(timeout=T)
                text = receipt.first.inner_text()
                assert "RENAME ZONE FAILED" in text and "NAME TAKEN" in text, text
                assert receipt.first.locator(".write-receipt-retry").count() == 1
                assert puts and puts[-1][1] == 409, puts
                assert page.locator("input.desk-zone-rename").count() == 0
                page.screenshot(path=str(SHOTS / f"late-refusal-receipt-{width}.png"))
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_f2_on_a_focused_zone_row_opens_the_field(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, puts = self._open(pw, width, "list")
            try:
                page.get_by_role("button", name="Inbox zone", exact=False).first.focus()
                page.keyboard.press("F2")
                f = _field(page, timeout=T)
                assert f["inListRow"] and f["value"] == "Inbox" and f["focused"], f
                assert (f["selStart"], f["selEnd"]) == (0, len("Inbox")), f
                page.screenshot(path=str(SHOTS / f"list-f2-{width}.png"))
                page.keyboard.press("Escape")
                page.locator("input.desk-zone-rename").wait_for(state="detached", timeout=T)
                assert puts == [], puts
            finally:
                browser.close()
