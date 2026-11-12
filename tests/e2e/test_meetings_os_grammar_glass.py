"""Records selection, menus, bounded wells and shots over an isolated real hub."""
from __future__ import annotations

import json
import os

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

TOKEN = "meetings-os-grammar"


@pytest.mark.e2e
@pytest.mark.timeout(240)
def test_records_selection_and_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import expect, sync_playwright
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/meetings11"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        db = get_database()
        for i, (mid, title, status, summary) in enumerate((
            ("platform", "Platform review", "completed", "The team agreed to move the release to Friday."),
            ("dana", "1:1 with Dana", "completed", "Dana wants the on-call rota changed before December. You agreed to raise it with the leads on Friday."),
            ("guild", "Architecture guild", "completed", "The guild reviewed the migration plan."),
            ("vendor", "Vendor call, Woodward", "error", ""),
            ("sprint", "Sprint planning", "disabled", ""),
            ("incident", "Incident review", "queued", ""),
            ("hiring", "Hiring sync", "completed", "The hiring panel will meet on Monday."),
        )):
            start = datetime.now().astimezone() - timedelta(hours=i + 1)
            db.meetings.save_meeting(MeetingState(id=mid, title=title, started_at=start, ended_at=start + timedelta(minutes=27 + i),
                segments=[TranscriptSegment(text="We move the release to Friday.", speaker="Me", start_time=1.0, end_time=4.0)],
                intel=IntelSnapshot(timestamp=1.0, topics=[], summary=summary, action_items=[]) if summary else None,
                intel_status=status, intel_status_detail="The summary engine timed out." if status == "error" else None))
        db.plugins.record_artifact(artifact_id="dana-decision", meeting_id="dana", artifact_type="decisions", title="Decisions",
            structured_json={"decisions": [{"decision": "Raise the rota change with the leads on Friday."}]}, plugin_id="decision_capture")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            tape: dict = {"_source": {"rig": "tests/e2e/test_meetings_os_grammar_glass.py", "engine": "none"}}
            for width in (1440, 393):
                # A fresh set at each width, made through the proposal producer.
                for proposal in db.proposals.list_proposals(meeting_id="guild", state="proposed"):
                    db.proposals.dismiss_proposal(proposal.id)
                task_ids = [db.proposals.create_proposal(meeting_id="guild", project_id=None, kind="action", text=task, source_plugin="summary").id
                            for task in ("Write the migration plan", "Review the rollback plan", "Confirm the release date")]
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.evaluate("sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key: 'review-meetings'}))")
                page.reload(wait_until="load")
                _normal_chair(page)
                window = page.locator("#surface-meetings")
                window.get_by_test_id("meeting-row-platform").wait_for()
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-meetings/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                _settle(page)
                if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
                    fixture = Path(__file__).resolve().parents[2] / "web/src/desk/__tests__/fixtures/meetings-hub/reader-r2.json"
                    body = {"_source": {"rig": "test_meetings_os_grammar_glass.py", "engine": "none"},
                        "/api/meetings/vendor": _api(page, "GET", "/api/meetings/vendor", token=TOKEN)}
                    fixture.write_text(json.dumps(body, indent=2) + "\n")

                def shot(state: str) -> None:
                    _settle(page)
                    assert window.evaluate("""el => {
                      const body = el.querySelector('.desk-surface-body');
                      return body.scrollHeight <= body.clientHeight + 1 && body.scrollWidth <= body.clientWidth + 1;
                    }"""), state
                    assert window.get_by_test_id("meetings-list").evaluate("""el => { const well=el.querySelector('.object-list-rows'); if(!well)return true; const box=well.getBoundingClientRect(),top=box.top+well.clientTop,bottom=top+well.clientHeight; return [...well.querySelectorAll('[data-object-id]')].every(row=>{const r=row.getBoundingClientRect(); return r.bottom<=top+1 || r.top>=bottom-1 || (r.top>=top-1 && r.bottom<=bottom+1);}); }"""), f"No partial collection row: {state}"
                    if state == "summary":
                        facts = window.get_by_test_id("meeting-list-preview").locator('.surface-inspector-facts')
                        assert facts.evaluate("el => [...el.querySelectorAll('.gadget-row')].every(row => row.getBoundingClientRect().bottom <= el.getBoundingClientRect().bottom+1)"), "Every preview fact must fit whole"
                    if state in ("find-empty", "find-error"):
                        expect(window).not_to_contain_text("Restored at")
                    if state in ("deleted", "deleted-list"):
                        expect(window).not_to_contain_text("Parked at")
                    page.screenshot(path=str(shots / f"meetings-{state}-{'900x600' if width == 1440 else '393'}.png"))

                def face(name: str) -> None:
                    window.locator(".desk-wings").wait_for(state="visible")
                    tab = window.get_by_role("tab", name=name, exact=True)
                    if tab.is_visible():
                        tab.click()
                    else:
                        window.get_by_test_id("surface-strip-menu").click()
                        page.get_by_role("menuitemcheckbox", name=name, exact=True).click()

                def open_app_menu():
                    switcher = page.get_by_test_id("desk-screen-switcher")
                    if switcher.is_visible():
                        switcher.click()
                        page.get_by_role("menuitem", name="Meetings", exact=True).click()
                        app_menu = page.get_by_role("menu").last
                    else:
                        page.get_by_test_id("desk-screen-title").get_by_role("button", name="Meetings", exact=True).click()
                        app_menu = page.get_by_role("menu", name="Meetings menu", exact=True)
                    return app_menu

                assert window.locator('[role="row"] button').count() == 0
                assert window.locator('.surface-spine, .mt-rail, .mt-plate').count() == 0
                rows = window.locator('[role="row"][data-object-id]')
                assert all(abs(row.bounding_box()["height"] - (26 if width == 1440 else 44)) < 1 for row in rows.all())
                expect(window.get_by_test_id("meeting-row-platform").locator('[data-col="state"]')).to_have_text("")
                shot("records")
                for mid, state in (("dana", "summary"), ("guild", "confirm"), ("vendor", "failed"), ("sprint", "no-summary"), ("incident", "queued")):
                    row = window.get_by_test_id(f"meeting-row-{mid}")
                    row.click()
                    expect(row).to_have_attribute("aria-selected", "true")
                    expect(window.get_by_test_id("meeting-list-preview")).to_be_visible()
                    expect(window.get_by_test_id("meeting-list-preview")).not_to_contain_text("Reading summary…")
                    assert window.get_by_test_id("meeting-mast").count() == 0
                    if mid == "dana":
                        expect(window.get_by_test_id("meeting-list-preview")).to_contain_text("Raise the rota change with the leads on Friday.")
                    if mid == "vendor":
                        expect(window.get_by_test_id("meeting-list-preview")).to_contain_text("The summary engine timed out.")
                    shot(state)
                    if mid == "vendor":
                        retry_path = "**/api/meetings/vendor/intelligence/run"
                        page.route(retry_path, lambda route: route.abort("failed"))
                        preview = window.get_by_test_id("meeting-list-preview")
                        preview.get_by_role("button", name="Try again", exact=True).click()
                        retry_failure = preview.get_by_test_id("meeting-summary-retry-failure")
                        expect(retry_failure.get_by_role("alert")).not_to_be_empty()
                        expect(preview).not_to_contain_text("The summary engine timed out.")
                        expect(retry_failure.get_by_role("button", name="Try again", exact=True)).to_be_enabled()
                        shot("summary-retry-failed")
                        page.unroute(retry_path)
                    if mid == "guild":
                        tasks = window.get_by_role("grid", name="Tasks to confirm", exact=True)
                        expect(tasks).to_be_visible()
                        task = window.get_by_test_id(f"meeting-task-{task_ids[0]}")
                        expect(task).to_contain_text("Write the migration plan")
                        expect(window.get_by_test_id("meetings-status")).to_contain_text("3 tasks to confirm")
                        task.click()
                        task_app_menu = open_app_menu()
                        for verb in ("Confirm", "Edit", "Dismiss"):
                            expect(task_app_menu.get_by_role("menuitem", name=verb, exact=True)).to_be_visible()
                        shot("task-app-menu")
                        page.keyboard.press("Escape")
                        task.click(button="right")
                        task_menu = page.get_by_role("menu", name="Tasks to confirm actions", exact=True)
                        expect(task_menu.get_by_role("menuitem", name="Confirm", exact=True)).to_be_visible()
                        expect(task_menu.get_by_role("menuitem", name="Dismiss", exact=True)).to_be_visible()
                        shot("task-menu")
                        task_menu.get_by_role("menuitem", name="Edit", exact=True).click()
                        window.get_by_role("textbox", name="Owner", exact=True).fill("Dana")
                        window.get_by_role("textbox", name="Due", exact=True).fill("Friday")
                        save = window.get_by_role("button", name="Save", exact=True)
                        assert save.evaluate("""el => {
                            const r = el.getBoundingClientRect();
                            const xs = innerWidth === 393 ? [r.left+r.width/2-20, r.left+r.width/2, r.left+r.width/2+20] : [r.left+2, r.left+r.width/2, r.right-2];
                            const ys = innerWidth === 393 ? [r.top+r.height/2-20, r.top+r.height/2, r.top+r.height/2+20] : [r.top+2, r.top+r.height/2, r.bottom-2];
                            return xs.every(x => ys.every(y => document.elementFromPoint(x,y)?.closest('button') === el));
                        }"""), "Save must stay reachable in the task inspector"
                        shot("task-edit")
                        edit_path = f"**/api/proposals/{task_ids[0]}/edit"
                        page.route(edit_path, lambda route: route.fulfill(status=503, json={"detail": "Hub unavailable"}))
                        save.click()
                        expect(window.get_by_role("alert")).to_contain_text("Not saved")
                        expect(window.get_by_role("textbox", name="Owner", exact=True)).to_have_value("Dana")
                        expect(window.get_by_test_id("meetings-status")).to_contain_text("Failed")
                        shot("task-edit-failed")
                        page.unroute(edit_path)
                        save.click()
                        expect(task).to_contain_text("Dana")
                        assert db.proposals.get_proposal(task_ids[0]).owner == "Dana"
                        actions = window.get_by_role("toolbar", name="Tasks to confirm actions", exact=True)
                        assert actions.evaluate("el => {const list=el.closest('.object-list');const head=list.querySelector('.object-list-head');const verbs=el.querySelector('.object-list-toolbar-strip');return el.getBoundingClientRect().bottom <= head.getBoundingClientRect().top+1 && Math.abs(verbs.getBoundingClientRect().left-list.getBoundingClientRect().left)<=1}")
                        actions.get_by_role("button", name="Confirm", exact=True).click()
                        expect(task).to_have_count(0)
                        assert db.proposals.get_proposal(task_ids[0]).state == "confirmed"
                        expect(window.get_by_test_id("meetings-status")).to_contain_text("Confirmed")
                        expect(window.get_by_test_id("meetings-status")).to_contain_text("2 tasks to confirm")
                        shot("task-confirmed")
                        window.get_by_test_id(f"meeting-task-{task_ids[1]}").click()
                        actions.get_by_role("button", name="Dismiss", exact=True).click()
                        expect(window.get_by_test_id(f"meeting-task-{task_ids[1]}")).to_have_count(0)
                        assert db.proposals.get_proposal(task_ids[1]).state == "dismissed"
                        expect(window.get_by_test_id("meetings-status")).to_contain_text("1 task to confirm")
                        shot("task-dismissed")
                        # A failed review read is distinct from an empty pending list.
                        review_paths = ("**/api/meetings/guild/outcome-review", "**/api/meetings/guild/follow-through-proposals")
                        for path in review_paths:
                            page.route(path, lambda route: route.fulfill(status=503, json={"detail": "Hub unavailable"}))
                        window.get_by_test_id("meeting-row-dana").click()
                        window.get_by_test_id("meeting-row-guild").click()
                        expect(window.get_by_role("alert")).to_contain_text("Tasks not read")
                        shot("tasks-read-failed")
                        for path in review_paths:
                            page.unroute(path)
                        window.get_by_role("button", name="Try again", exact=True).click()
                        last_task = window.get_by_test_id(f"meeting-task-{task_ids[2]}")
                        expect(last_task).to_be_visible()
                        shot("tasks-read-retry")
                        last_task.click()
                        actions.get_by_role("button", name="Dismiss", exact=True).click()
                        expect(last_task).to_have_count(0)
                        expect(window.get_by_test_id("meetings-status")).not_to_contain_text("to confirm")
                        expect(row.locator('[data-col="state"]')).to_have_text("")
                        shot("tasks-done")
                # Keyboard moves the selection, and Home/End keep the list in its well.
                window.get_by_test_id("meeting-row-incident").focus()
                page.keyboard.press("Home")
                expect(window.get_by_test_id("meeting-row-platform")).to_have_attribute("aria-selected", "true")
                page.keyboard.press("ArrowDown")
                expect(window.get_by_test_id("meeting-row-dana")).to_have_attribute("aria-selected", "true")
                row = window.get_by_test_id("meeting-row-dana")
                row.click(button="right")
                menu = page.get_by_role("menu", name="Meetings actions", exact=True)
                expect(menu.get_by_role("menuitem", name="Open", exact=False)).to_be_visible()
                expect(menu.get_by_role("menuitem", name="Delete", exact=False)).to_be_visible()
                expect(menu.get_by_role("menuitem", name="Send to…", exact=True)).to_be_visible()
                shot("context-menu")
                page.keyboard.press("Escape")
                # The app menu uses the same selection declaration.
                app_menu = open_app_menu()
                expect(app_menu.get_by_role("menuitem", name="Delete", exact=False)).to_be_visible()
                expect(app_menu.get_by_role("menuitem", name="Send to…", exact=True)).to_be_visible()
                shot("app-menu")
                page.keyboard.press("Escape")
                tape["/api/meetings?limit=100"] = _api(page, "GET", "/api/meetings?limit=100", token=TOKEN)
                tape["/api/meetings/dana"] = _api(page, "GET", "/api/meetings/dana", token=TOKEN)
                # Backspace is reversible; the list stays in the window.
                row.focus()
                page.keyboard.press("Backspace")
                expect(window.get_by_test_id("meeting-row-dana")).to_have_count(0)
                expect(window.get_by_test_id("meetings-park-receipt")).to_be_visible()
                if width == 393:
                    restore = window.get_by_test_id("meetings-park-receipt").get_by_role("button", name="Restore", exact=True)
                    assert restore.evaluate("""el => {
                      const r = el.getBoundingClientRect(); const x = (r.left+r.right)/2; const y = (r.top+r.bottom)/2;
                      return [-20,0,20].every(dx => [-20,0,20].every(dy => document.elementFromPoint(x+dx,y+dy)?.closest('button') === el));
                    }"""), "Restore must own its 44px hit area in the status bar"
                shot("deleted")
                window.get_by_test_id("meetings-park-receipt").get_by_role("button", name="Restore", exact=True).click()
                expect(window.get_by_test_id("meeting-row-dana")).to_be_visible()
                # Deleted records use the same selection list and restore action.
                window.get_by_test_id("meeting-row-dana").focus()
                page.keyboard.press("Delete")
                expect(window.get_by_test_id("meeting-row-dana")).to_have_count(0)
                # Restore clears the old Records Find without clearing its own acknowledgement.
                window.get_by_role("searchbox", name="Find a meeting", exact=True).fill("zzzzzz")
                expect(rows).to_have_count(0)
                face("Deleted")
                window.get_by_test_id("meeting-row-dana").click()
                shot("deleted-list")
                tape["/api/meetings?parked=true"] = _api(page, "GET", "/api/meetings?parked=true", token=TOKEN)
                tape["GET active while deleted"] = _api(page, "GET", "/api/meetings?limit=100", token=TOKEN)
                with page.expect_response(lambda response: response.url.endswith("/api/meetings/dana/restore")) as restored:
                    window.get_by_role("toolbar", name="Meetings", exact=True).get_by_role("button", name="Restore", exact=True).click()
                tape["POST /api/meetings/dana/restore"] = restored.value.json()
                if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1" and width == 1440:
                    fixture = Path(__file__).resolve().parents[2] / "web/src/desk/__tests__/fixtures/meetings-hub/list-app.json"
                    fixture.write_text(json.dumps(tape, indent=2) + "\n")
                expect(window.get_by_test_id("meeting-row-dana")).to_have_attribute("aria-selected", "true")
                expect(window.get_by_test_id("meeting-row-platform")).to_be_visible()
                expect(window.get_by_test_id("meeting-row-dana")).to_be_visible()
                expect(window.get_by_test_id("meetings-park-receipt")).to_contain_text("Restored at")
                shot("restored")
                find = window.get_by_role("searchbox", name="Find a meeting", exact=True)
                find.fill("zzzzzz")
                expect(rows).to_have_count(0)
                shot("find-empty")
                find.fill("no-match-for-this-meeting")
                expect(rows).to_have_count(0)
                assert window.get_by_role("alert").count() == 0
                # Literal search now accepts hyphens (#2187). Inject a failed
                # read to test the error and recovery path independently.
                page.route("**/api/meetings?*", lambda route: route.fulfill(status=503, json={"detail": "Meetings not read"}))
                find.fill("unavailable")
                expect(window.get_by_role("alert")).to_contain_text("Meetings not read")
                shot("find-error")
                page.unroute("**/api/meetings?*")
                find.fill("")
                expect(window.get_by_test_id("meeting-row-dana")).to_be_visible()
                # Deleted read failures stay visible and recover in their collection.
                page.route("**/api/meetings?parked=true", lambda route: route.fulfill(status=503, json={"detail": "Deleted meetings not read"}))
                page.reload(wait_until="load")
                _normal_chair(page)
                face("Deleted")
                expect(window.get_by_role("alert")).to_contain_text("Deleted meetings not read")
                shot("deleted-failed")
                page.unroute("**/api/meetings?parked=true")
                window.get_by_role("button", name="Try again", exact=True).click()
                expect(window.get_by_text("No deleted meetings", exact=True)).to_be_visible()
                shot("deleted-empty")
                face("Records")
                expect(window.get_by_test_id("meeting-row-dana")).to_be_visible()
                empty = _api(page, "GET", "/api/meetings?limit=100&search=unique-missing-record", token=TOKEN)
                page.route("**/api/meetings?limit=100", lambda route: route.fulfill(json=empty))
                page.reload(wait_until="load")
                _normal_chair(page)
                expect(window.get_by_text("Record or import a meeting", exact=True)).to_be_visible()
                shot("empty")
                page.unroute("**/api/meetings?limit=100")
                page.add_init_script("""(() => {
                    const read = window.fetch.bind(window);
                    const gate = new Promise(resolve => { window.__releaseMeetingsRead = resolve; });
                    window.__meetingsReadHeld = 0;
                    window.fetch = (input, init) => {
                        const url = typeof input === 'string' ? input : input.url;
                        if (url.includes('/api/meetings?limit=100')) {
                            window.__meetingsReadHeld += 1;
                            return gate.then(() => read(input, init));
                        }
                        return read(input, init);
                    };
                })()""")
                page.reload(wait_until="load")
                _normal_chair(page)
                expect(window.get_by_test_id("meetings-collection")).to_be_visible()
                page.wait_for_function("() => window.__meetingsReadHeld > 0")
                expect(window.locator('.surface-state[data-kind="loading"]')).to_be_visible()
                expect(window.get_by_test_id("meetings-toolbar")).to_be_visible()
                expect(window.get_by_test_id("meetings-status")).to_be_visible()
                shot("loading")
                page.evaluate("window.__releaseMeetingsRead()")
                expect(window.get_by_test_id("meeting-row-dana")).to_be_visible()
                window.get_by_test_id("meeting-row-dana").focus()
                page.keyboard.press("Enter")
                expect(window.get_by_test_id("meeting-toolbar")).to_be_visible()
                assert errors == [], errors
                page.close()
            if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
                fixture = Path(__file__).resolve().parents[2] / "web/src/desk/__tests__/fixtures/meetings-hub/list-app.json"
                fixture.write_text(json.dumps(tape, indent=2) + "\n")
            browser.close()
    finally:
        server.stop()
