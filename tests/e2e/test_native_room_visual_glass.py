"""Room Files keeps the real Note return door on the list grammar."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _ensure_build
from .test_native_project_source_return_glass import (
    TOKEN, PROJECT_A, PROJECT_A_NAME, NOTE_REF, NOTE_TITLE,
    _boot_isolated, _seed, _start, _open_project, _files,
    _open_filed_note, _return_project, _focused_filed_row,
)
from .test_desk_sweep import CLIPPED_JS, LIST_GRAMMAR_JS
from .test_room_os_grammar_glass import _view

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".tmp/evidence-shots/room10"


@pytest.mark.parametrize("width", [1440, 393])
def test_room_files_selection_and_real_note_return(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    server, base = _boot_isolated(tmp_path, monkeypatch)
    _seed()
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(15000)
            _start(page, base)
            room = _open_project(page, PROJECT_A, PROJECT_A_NAME)
            if width == 1440:
                _api(page, "POST", "/api/desk/windows/surface-project-memory/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
            files = _files(room)
            row = files.locator(f"[data-object-id='{NOTE_REF}']")
            expect(row).to_contain_text(NOTE_TITLE)
            row.click()
            expect(row).to_have_attribute("aria-selected", "true")
            assert not row.locator("button,a").count()
            note = _open_filed_note(page, room)
            room = _return_project(page, note, PROJECT_A_NAME, width)
            expect(room.get_by_test_id("room-files-return")).to_have_text("Filed here")
            _focused_filed_row(room)
            assert not page.evaluate(LIST_GRAMMAR_JS, "#surface-project-memory")
            assert not page.evaluate(CLIPPED_JS, "#surface-project-memory")
            suffix = "900x600" if width == 1440 else "393"
            page.screenshot(path=str(OUT / f"file-return-{suffix}-after.png"))
            browser.close()
    finally:
        server.stop()


@pytest.mark.parametrize("width", [1440, 393])
def test_room_source_sign_in_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """The producer's expired-source answer is replayed; no provider is read."""
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    server, base = _boot_isolated(tmp_path, monkeypatch)
    _seed()
    tape = json.loads((ROOT / "web/src/features/project-room/__tests__/room-wires/recall10.json").read_text())["room"]
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(15000)
            page.route(f"**/api/projects/{PROJECT_A}/room", lambda route: route.fulfill(json=tape))
            _start(page, base)
            _api(page, "POST", "/api/desk/windows/surface-project-memory/open", {"object_ref": f"project:{PROJECT_A}"}, token=TOKEN)
            page.reload(wait_until="load")
            room = page.locator("#surface-project-memory")
            expect(room.get_by_test_id("room-body")).to_be_visible()
            if width == 1440:
                _api(page, "POST", "/api/desk/windows/surface-project-memory/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
            room.get_by_role("tab", name="Sources", exact=True).click()
            source = room.locator(".object-list-row").filter(has=page.get_by_text("Sign in again", exact=True)).first
            expect(source).to_be_visible()
            source.click()
            assert not source.locator("button,a").count()
            assert not page.evaluate(CLIPPED_JS, "#surface-project-memory")
            suffix = "900x600" if width == 1440 else "393"
            page.screenshot(path=str(OUT / f"source-needs-sign-in-{suffix}-after.png"))
            browser.close()
    finally:
        server.stop()
