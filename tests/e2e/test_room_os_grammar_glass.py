"""Room lists and inspector seats at 900 by 600 and 393, on an isolated hub."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .room_seed_rig import _seed_populated_project, _seed_meeting_with_proposals, TOKEN
from .test_desk_sweep import CLIPPED_JS, LIST_GRAMMAR_JS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".tmp/evidence-shots/room10"


def _verb(page: Any, win: Any, word: str) -> None:
    button = win.get_by_role("button", name=word, exact=True)
    if button.count() and button.first.is_visible():
        button.first.click()
    else:
        win.get_by_role("button", name="Actions ▾", exact=True).first.click()
        page.get_by_role("menu").last.get_by_role("menuitem", name=word, exact=True).click()


def _view(page: Any, win: Any, word: str) -> None:
    button = win.get_by_role("button", name="Project view", exact=True)
    if button.count() and button.first.is_visible():
        button.first.click()
    else:
        win.get_by_role("button", name="Actions ▾", exact=True).first.click()
        page.get_by_role("menu").last.get_by_role("menuitem", name="Project view", exact=True).click()
    page.get_by_role("menu").last.get_by_role("menuitem", name=word, exact=True).click()


@pytest.mark.parametrize("width", [1440, 393])
def test_room_lists_inspectors_and_postures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect
    from holdspeak.db import get_database
    from ._hs173_seed import seed_health_room

    _ensure_build()
    OUT.mkdir(parents=True, exist_ok=True)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(15000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            project_id = _seed_populated_project(page)
            seed_health_room(get_database(), project_id=project_id)
            empty_id = _api(page, "POST", "/api/projects", {"name": "Empty project"}, token=TOKEN)["project"]["id"]
            _api(page, "POST", "/api/programs", {"title": "Read the cutover plan", "project_id": project_id, "steps": [{"title": "Read the plan", "brief": "Read the current cutover plan.", "kind": "prompt"}]}, token=TOKEN)
            proposals = _seed_meeting_with_proposals(project_id, [("You", "Approve the cutover window"), ("Dana", "Load test rerun"), ("You", "Use idempotency keys on retries")])
            with get_database()._connection() as conn:
                conn.execute("UPDATE follow_through_proposals SET kind='decision' WHERE id=?", (proposals[2],))
            for proposal in proposals[1:]:
                _api(page, "POST", f"/api/proposals/{proposal}/confirm", {}, token=TOKEN)
            draft = _api(page, "POST", f"/api/projects/{project_id}/updates/draft", {"generator": "deterministic"}, token=TOKEN)["update"]

            def open_room(pid: str) -> Any:
                clear_hub_windows_http(base, TOKEN)
                _api(page, "POST", "/api/desk/windows/surface-project-memory/open", {"object_ref": f"project:{pid}"}, token=TOKEN)
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-project-memory/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                win = page.locator("#surface-project-memory")
                expect(win.get_by_role("grid", name="Open", exact=True)).to_be_visible()
                return win

            def shot(win: Any, name: str) -> None:
                _settle(page)
                suffix = "900x600" if width == 1440 else "393"
                dest = OUT / f"{name}-{suffix}-after"
                page.screenshot(path=str(dest.with_suffix(".png")))
                facts = win.evaluate("""el => ({box:el.getBoundingClientRect().toJSON(),
                    scroll: [...el.querySelectorAll('.object-list-rows,.surface-list-pane-preview')].map(e=>({kind:e.className,height:e.clientHeight,scroll:e.scrollHeight})),
                    headers:[...el.querySelectorAll('h1,.surface-mast,summary')].map(e=>e.textContent),
                    rowVerbs:[...el.querySelectorAll('.object-list-row button,.object-list-row a')].map(e=>e.textContent),
                    status:[...el.querySelectorAll('.kit-statusbar')].map(e=>e.textContent)})""")
                facts["engine_mode"] = "none"
                dest.with_suffix(".json").write_text(json.dumps(facts, indent=2))
                assert not facts["headers"], facts
                assert not facts["rowVerbs"], facts
                assert not page.evaluate(LIST_GRAMMAR_JS, "#surface-project-memory")
                assert not page.evaluate(CLIPPED_JS, "#surface-project-memory")
                assert not errors, errors

            win = open_room(project_id)
            shot(win, "open")
            for kind in ("Risk", "Plan item", "Program", "Question", "Task", "Decision"):
                rows = win.locator(".object-list-row").filter(has=page.locator(f'[data-col="kind"]', has_text=kind))
                expect(rows.first).to_be_visible()
                rows.first.click()
                expect(rows.first).to_have_attribute("aria-selected", "true")
                shot(win, "selection-" + kind.lower().replace(" ", "-"))
            for tab in ("Plan", "Sources", "Updates"):
                win.get_by_role("tab", name=tab, exact=True).click()
                expect(win.get_by_role("grid", name=tab, exact=True)).to_be_visible()
                shot(win, tab.lower())
            update_row = win.locator(".object-list-row").first
            update_row.click()
            expect(win.get_by_role("textbox", name="Update body", exact=True)).to_be_visible()
            shot(win, "update")
            win.get_by_role("tab", name="Open", exact=True).click()
            for posture in ("Prepare", "Review", "Steward", "People", "Files", "History", "Pages", "Brief", "Cadence", "Recall"):
                _view(page, win, posture)
                if posture == "Prepare":
                    expect(win.get_by_role("textbox", name="Purpose", exact=True)).to_be_visible()
                shot(win, "posture-" + posture.lower())
            _view(page, win, "Now")
            ask_wire = json.loads((ROOT / "web/src/test/wire/ask.thread.wire.json").read_text())["first"]
            page.route("**/api/ask", lambda route: route.fulfill(json=ask_wire))
            question = win.get_by_role("textbox", name="Ask this project", exact=True)
            question.fill("What changed?")
            question.press("Enter")
            expect(win.get_by_text(ask_wire["output"], exact=True)).to_be_visible()
            shot(win, "ask-answer")
            win = open_room(empty_id)
            expect(win.get_by_text("Nothing open", exact=True)).to_be_visible()
            shot(win, "empty-project")
            page.route(f"**/api/projects/{empty_id}/room", lambda route: route.fulfill(status=503, json={"detail": "Read unavailable"}))
            page.reload(wait_until="load")
            win = page.locator("#surface-project-memory")
            expect(win.get_by_text("Could not load the Project", exact=False)).to_be_visible()
            shot(win, "failed-read")
            browser.close()
    finally:
        server.stop()
