"""Room lists and inspector seats at 900 by 600 and 393, on an isolated hub."""
from __future__ import annotations

from tests.room_bindings import http_binding

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .room_seed_rig import _seed_populated_project, _seed_meeting_with_proposals, TOKEN
from .test_desk_sweep import CLIPPED_JS, LIST_GRAMMAR_JS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".tmp/evidence-shots/room11"


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
                _api(page, "POST", f"/api/proposals/{proposal}/confirm", {**({} or {}), "binding": http_binding(f"/api/proposals/{proposal}/confirm")}, token=TOKEN)
            draft = _api(page, "POST", f"/api/projects/{project_id}/updates/draft", {"generator": "deterministic"}, token=TOKEN)["update"]
            # Real stored records; only the page-writing engine is scripted.
            from tests.unit.test_memory_slice5_pages import Pages, _filed_note, _learn, write_page, spec_for
            db = get_database()
            _filed_note(db, "room11-page-source", "Cutover status is ready. Rollback status is tested.", project_id)
            _learn(db)
            write_page(db, Pages(recall=False), ("project", project_id), spec_for("project", "what-changed-this-week"))
            brief = _api(page, "POST", f"/api/projects/{project_id}/briefs/prepare", {"purpose": "Read the cutover plan", "generator": "deterministic"}, token=TOKEN)["brief"]
            _api(page, "POST", f"/api/briefs/{brief['id']}/keep", {}, token=TOKEN)
            db.project_observations.insert_review(review_id="room11-review", project_id=project_id, status="open", opened_at="2026-11-11T12:00:00+00:00")
            db.project_observations.insert_proposal(proposal_id="room11-proposal", project_id=project_id, review_window_key="room11-review", proposal_kind="review_flag", title="Read the saved cutover plan", target_ref=f"project:{project_id}", rationale="The cutover window needs review", patch_json=json.dumps({"text": "Keep the tested rollback plan", "state": "open"}))


            def open_room(pid: str) -> Any:
                clear_hub_windows_http(base, TOKEN)
                _api(page, "POST", "/api/desk/windows/surface-project-memory/open", {"object_ref": f"project:{pid}"}, token=TOKEN)
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-project-memory/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                win = page.locator("#surface-project-memory")
                expect(win.get_by_role("grid", name="Open", exact=True)).to_be_attached()
                _settle(page)
                return win

            def shot(win: Any, name: str) -> None:
                _settle(page)
                suffix = "900x600" if width == 1440 else "393"
                dest = OUT / f"{name}-{suffix}-after"
                page.screenshot(path=str(dest.with_suffix(".png")))
                facts = win.evaluate("""el => ({box:el.getBoundingClientRect().toJSON(),
                    scroll: [...el.querySelectorAll('.object-list-rows,.surface-list-pane-preview')].map(e=>({kind:e.className,height:e.clientHeight,scroll:e.scrollHeight})),
                    headers:[...el.querySelectorAll('h1,.surface-mast:not(.surface-mast--framed),summary')].map(e=>e.textContent),
                    rowVerbs:[...el.querySelectorAll('.object-list-row button,.object-list-row a')].map(e=>e.textContent),
                    status:[...el.querySelectorAll('.kit-statusbar')].map(e=>e.textContent)})""")
                facts["engine_mode"] = "replayed" if name in ("ask-answer", "pages-filled-reader", "posture-pages") else "none"
                dest.with_suffix(".json").write_text(json.dumps(facts, indent=2))
                assert not win.locator(".desk-wings-menu").count()
                assert win.locator(".desk-window-title").inner_text().strip()
                assert not facts["headers"], facts
                assert not facts["rowVerbs"], facts
                assert not page.evaluate(LIST_GRAMMAR_JS, "#" + win.get_attribute("id"))
                assert not page.evaluate(CLIPPED_JS, "#" + win.get_attribute("id"))
                for strong in win.locator(".surface-object-reading .reading-document strong").all():
                    assert strong.evaluate("e => getComputedStyle(e).display === 'inline'")
                for well in win.locator(".surface-object-reading").all():
                    assert well.evaluate("e => e.clientHeight >= Math.min(80, e.scrollHeight)"), well.evaluate("e=>({height:e.clientHeight,scroll:e.scrollHeight})")
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
            expect(win.locator(".surface-object-reader[aria-label=Update]")).to_be_visible()
            expect(win.locator(".surface-object-reading")).not_to_contain_text("at_risk")
            expect(win.locator(".surface-object-reading")).not_to_contain_text("-- open")
            expect(win.locator(".surface-object-reading strong").first).to_be_visible()
            shot(win, "update-reader")
            _verb(page, win, "Edit")
            expect(win.get_by_role("textbox", name="Update body", exact=True)).to_be_visible()
            shot(win, "update")
            _verb(page, win, "Cancel")
            for seat in ("claims", "sources"):
                win.get_by_role("combobox", name="View", exact=True).select_option(seat)
                first = win.locator(".object-list-row").first
                if first.count(): first.click()
                shot(win, "update-" + seat)
            win.get_by_role("combobox", name="View", exact=True).select_option("updates")
            win.get_by_role("tab", name="Open", exact=True).click()
            for posture in ("Prepare", "Review", "Steward", "People", "Files", "History", "Pages", "Brief", "Cadence", "Recall"):
                _view(page, win, posture)
                if posture == "Prepare":
                    expect(win.get_by_role("textbox", name="Purpose", exact=True)).to_be_visible()
                if posture == "History":
                    expect(win.get_by_role("columnheader", name="State", exact=True)).to_have_count(0)
                if posture == "Brief":
                    expect(win.locator(".surface-object-reading")).to_contain_text("Progress")
                    expect(win.locator(".object-list-row")).to_have_count(0)
                if posture == "Pages":
                    row = win.locator(".object-list-row").first
                    expect(row).to_be_visible()
                    row.click()
                    expect(win.locator(".surface-object-reading")).to_contain_text("Cutover status is ready")
                    expect(win.get_by_role("button", name="Open", exact=True)).to_be_disabled()
                    shot(win, "pages-filled-reader")
                    _verb(page, win, "Open source")
                    source_note = page.locator('[id="pullout:note:room11-page-source"]')
                    expect(source_note.locator(".thought-note-body .cm-content")).to_contain_text("Cutover status is ready")
                    source_note.locator(".desk-gadget-close").click()
                    expect(win.locator(".desk-window-title")).to_have_attribute("aria-label", "Payments Platform Rewrite")
                    expect(win.locator(".surface-object-reading")).to_contain_text("Cutover status is ready")
                if posture == "Prepare":
                    shot(win, "prepare-purpose")
                    win.get_by_role("combobox", name="View", exact=True).select_option("kept")
                    kept = win.locator(".object-list-row").first
                    expect(kept).to_be_visible()
                    shot(win, "prepare-kept-list")
                    kept.dblclick()
                    expect(win.locator(".surface-object-reader[aria-label=Brief]")).to_contain_text("Kept")
                    expect(win.locator(".object-list-row")).to_have_count(0)
                    shot(win, "prepare-kept-reader")
                    # Visit every records seat of a saved brief after the fit change.
                    for seat in ("sources", "claims", "carried"):
                        win.get_by_role("combobox", name="View", exact=True).select_option(seat)
                        shot(win, "prepare-" + seat)
                    win.get_by_role("combobox", name="View", exact=True).select_option("brief")
                if posture == "Review":
                    expect(win.get_by_role("button", name="Open", exact=True)).to_be_disabled()
                    expect(win.locator(".object-list-row")).not_to_have_count(0)
                    shot(win, "review-populated")
                    _verb(page, win, "Edit and accept")
                    expect(win.get_by_role("textbox", name="text", exact=True)).to_be_visible()
                    shot(win, "review-edit")
                    _verb(page, win, "Cancel")
                    _verb(page, win, "Defer")
                    expect(win.get_by_role("textbox", name="Until", exact=True)).to_be_visible()
                    shot(win, "review-defer")
                    _verb(page, win, "Cancel")
                    _verb(page, win, "Dismiss")
                    expect(win.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                    shot(win, "review-dismiss-question")
                    _verb(page, win, "Cancel")
                shot(win, "posture-" + posture.lower())
            _view(page, win, "Now")
            page.route(f"**/api/updates/{draft['id']}", lambda route: route.fulfill(status=503, json={"detail": "Read unavailable"}))
            _view(page, win, "Brief")
            expect(win.get_by_text("Could not read the brief · Nothing changed", exact=True)).to_be_visible()
            shot(win, "brief-failed-read")
            page.unroute(f"**/api/updates/{draft['id']}")
            _verb(page, win, "Try again")
            expect(win.locator(".surface-object-reading")).to_contain_text("Progress")
            shot(win, "brief-recovered")
            _view(page, win, "Now")
            _verb(page, win, "Add source")
            expect(win.get_by_role("grid", name="Add sources", exact=True)).to_be_visible()
            shot(win, "posture-add-source")
            win.get_by_role("combobox", name="View", exact=True).select_option("source")
            win.locator(".object-list-row").first.click()
            shot(win, "add-source-selected")
            win.get_by_role("combobox", name="View", exact=True).select_option("found")
            shot(win, "add-source-found")
            _verb(page, win, "Cancel")
            ask_wire = json.loads((ROOT / "web/src/test/wire/ask.thread.wire.json").read_text())["first"]
            page.route("**/api/ask", lambda route: route.fulfill(json=ask_wire))
            question = win.get_by_role("textbox", name="Ask this project", exact=True)
            question.fill("What changed?")
            question.press("Enter")
            expect(win.get_by_text(ask_wire["output"], exact=True)).to_be_visible()
            done = win.get_by_role("button", name="Done", exact=True)
            assert done.evaluate("e => {const r=e.getBoundingClientRect(),w=e.closest('[data-layer=window]').getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return r.bottom<=w.bottom && (hit===e||e.contains(hit));}")
            shot(win, "ask-answer")
            clear_hub_windows_http(base, TOKEN)
            _api(page, "POST", "/api/desk/windows/surface-project-setup/open", {}, token=TOKEN)
            if width == 1440:
                _api(page, "POST", "/api/desk/windows/surface-project-setup/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            door = page.locator("#surface-project-setup")
            expect(door.get_by_role("grid", name="New project", exact=True)).to_be_visible()
            shot(door, "posture-door")
            win = open_room(empty_id)
            expect(win.get_by_text("Nothing open", exact=True)).to_be_visible()
            shot(win, "empty-project")
            for empty_view in ("Brief", "History", "Pages", "Review"):
                _view(page, win, empty_view)
                shot(win, "empty-" + empty_view.lower())
            page.route(f"**/api/projects/{empty_id}/room", lambda route: route.fulfill(status=503, json={"detail": "Read unavailable"}))
            page.reload(wait_until="load")
            win = page.locator("#surface-project-memory")
            expect(win.get_by_text("Could not load the Project", exact=False)).to_be_visible()
            shot(win, "failed-read")
            browser.close()
    finally:
        server.stop()
