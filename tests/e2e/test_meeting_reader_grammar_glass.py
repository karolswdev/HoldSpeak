"""Meeting object seats, failure, live work and questions on an isolated hub."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

TOKEN = "meeting-reader-grammar"


@pytest.mark.e2e
@pytest.mark.timeout(240)
def test_meeting_reader_seats_and_shots(tmp_path, monkeypatch):
    from playwright.sync_api import expect, sync_playwright
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/meetings10"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        db = get_database()
        now = datetime.now().astimezone()
        for mid, state in (("reader", "completed"), ("reader-running", "running"), ("reader-failed", "error"), ("reader-empty", "disabled")):
            db.meetings.save_meeting(MeetingState(id=mid, title="Platform review" if mid == "reader" else mid.replace("reader-", "Summary "),
                started_at=now - timedelta(hours=1), ended_at=now - timedelta(minutes=30),
                segments=[TranscriptSegment(text="We move the release to Friday. Dana will write the migration plan.", speaker="Dana", start_time=1.0, end_time=4.0)] if mid != "reader-empty" else [],
                intel=IntelSnapshot(timestamp=1.0, topics=[], summary="The team agreed to move the release to Friday. Dana will write the migration plan.", action_items=[]) if mid == "reader" else None,
                intel_status=state, intel_requested_at=now - timedelta(seconds=30) if state == "running" else None,
                intel_status_detail="The summary engine timed out." if state == "error" else "Reading transcript" if state == "running" else None))
        db.plugins.record_artifact(artifact_id="reader-decision", meeting_id="reader", artifact_type="decisions", title="Decisions",
            structured_json={"decisions": [{"decision": "Move the release to Friday."}]}, plugin_id="decision_capture")
        task = db.proposals.create_proposal(meeting_id="reader", project_id=None, kind="action", text="Write the migration plan", source_plugin="summary")
        decision = db.proposals.create_proposal(meeting_id="reader", project_id=None, kind="decision", text="Move the rollout to Friday", source_plugin="decision_capture")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)

                def open_record(mid):
                    _api(page, "POST", "/api/desk/windows/surface-meetings/open", {"object_ref": f"meeting:{mid}"}, token=TOKEN)
                    page.reload(wait_until="load")
                    _normal_chair(page)
                    window = page.locator("#surface-meetings")
                    window.get_by_test_id("meeting-toolbar").wait_for()
                    if width == 1440:
                        _api(page, "POST", "/api/desk/windows/surface-meetings/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                    return window

                window = open_record("reader")

                def shot(state):
                    _settle(page)
                    assert window.evaluate("""el => { const b=el.querySelector('.desk-surface-body'); return b.scrollHeight <= b.clientHeight+1 && b.scrollWidth <= b.clientWidth+1; }"""), state
                    page.screenshot(path=str(shots / f"meeting-reader-{state}-{'900x600' if width == 1440 else '393'}-after.png"))

                def seat(label):
                    tab = window.get_by_role("tab", name=label, exact=True)
                    if tab.is_visible():
                        tab.click()
                    else:
                        window.get_by_role("button", name="Meeting contents more", exact=True).click()
                        page.get_by_role("menuitem", name=label, exact=True).click()

                expect(window.locator('.desk-pullout-title')).to_contain_text("Platform review")
                expect(window.get_by_test_id("meeting-summary")).to_contain_text("release to Friday")
                assert window.locator('[role="tablist"]').count() == 1
                assert window.locator('.meeting-mast, .meeting-plate, .meeting-spine').count() == 0
                shot("summary")
                for tab in ("Transcript", "Tasks", "Decisions", "Commitments", "Results", "Facts", "Recovery"):
                    seat(tab)
                    shot(tab.lower())
                seat("Decisions")
                decision_row = window.get_by_test_id(f"meeting-outcome-ft-{decision.id}")
                decision_row.click()
                window.get_by_role("button", name="Edit", exact=True).click()
                window.get_by_role("textbox", name="Task", exact=True).fill("Move the rollout to next Friday")
                assert window.get_by_role("grid", name="Decisions", exact=True).count() == 0
                shot("decision-edit")
                confirm_path = f"**/api/proposals/{decision.id}/confirm"
                page.route(confirm_path, lambda route: route.fulfill(status=503, json={"detail": "Hub unavailable"}))
                window.get_by_role("region", name="Edit proposal", exact=True).get_by_role("button", name="Confirm", exact=True).click()
                expect(window.get_by_role("textbox", name="Task", exact=True)).to_have_value("Move the rollout to next Friday")
                expect(window.get_by_test_id("meeting-status")).to_contain_text("Could not confirm")
                shot("decision-edit-failed")
                page.unroute(confirm_path)
                window.get_by_role("button", name="Cancel", exact=True).click()
                seat("Tasks")
                row = window.get_by_test_id(f"meeting-task-{task.id}")
                row.click()
                shot("task-selected")
                row.click(button="right")
                page.get_by_role("menu", name="Tasks to confirm actions", exact=True).get_by_role("menuitem", name="Edit", exact=True).click()
                window.get_by_role("textbox", name="Owner", exact=True).fill("Dana")
                shot("task-edit")
                page.route(f"**/api/proposals/{task.id}/edit", lambda route: route.fulfill(status=503, json={"detail": "Hub unavailable"}))
                window.get_by_role("button", name="Save", exact=True).click()
                expect(window.get_by_role("alert")).to_contain_text("Not saved")
                expect(window.get_by_role("textbox", name="Owner", exact=True)).to_have_value("Dana")
                shot("task-edit-failed")
                window.get_by_role("button", name="Cancel", exact=True).click()
                seat("Summary")
                window.get_by_test_id("meeting-delete").click()
                question = window.get_by_role("region", name="Delete meeting?", exact=True)
                expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                shot("delete-question")
                question.get_by_role("button", name="Cancel", exact=True).click()
                assert not db.meetings.get_meeting("reader").parked
                for mid, state in (("reader-running", "running"), ("reader-failed", "failed"), ("reader-empty", "empty")):
                    window = open_record(mid)
                    if state == "failed":
                        expect(window.get_by_test_id("meeting-summary-failure")).to_contain_text("The summary engine timed out.")
                        expect(window.get_by_role("button", name="Try again", exact=True)).to_be_visible()
                    if state == "running":
                        expect(window.get_by_role("log", name="Summary work")).to_contain_text("Reading transcript")
                        expect(window.get_by_test_id("meeting-status")).to_contain_text("Summary running")
                    shot(state)
                held = []
                read_pattern = "**/api/meetings/reader?include_parked=true"
                page.route(read_pattern, lambda route: held.append(route))
                window = open_record("reader")
                expect(window.get_by_test_id("meeting-status")).to_contain_text("Reading meeting")
                shot("loading")
                for route in held:
                    route.fulfill(status=503, json={"detail": "Hub unavailable"})
                expect(window.get_by_role("alert")).to_contain_text("Hub unavailable")
                shot("read-failed")
                page.unroute(read_pattern)
                window.get_by_role("button", name="Try again", exact=True).click()
                expect(window.get_by_test_id("meeting-summary")).to_contain_text("release to Friday")
                page.close()
                assert not errors, errors
            browser.close()
    finally:
        server.stop()

@pytest.mark.e2e
@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(180)
def test_reader_recorded_result_and_context_seats(tmp_path, monkeypatch, width):
    """Replay real producer tapes for optional seats; no engine or send runs."""
    import json
    from urllib.parse import urlsplit
    from playwright.sync_api import expect, sync_playwright
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    root = Path(__file__).resolve().parents[2]
    fixtures = root / "web/src/desk/__tests__/fixtures/meetings-hub"
    prepared = json.loads((fixtures / "prepared.json").read_text())
    failed = json.loads((fixtures / "prepared-failed.json").read_text())["prepared"]
    saved = json.loads((fixtures / "hs170.json").read_text())
    ran = json.loads((fixtures / "hs172.json").read_text())
    looked = json.loads((fixtures / "looked-at.json").read_text())["run_receipt"]
    bodies = {**saved, **prepared, **ran}
    bodies["/api/meetings/m-ran?include_parked=true"] = {**bodies["/api/meetings/m-ran?include_parked=true"], "run_receipt": looked}
    shots = root / ".tmp/evidence-shots/meetings10"
    try:
        for mid in ("c5-review", "m-saved-outcomes", "m-ran"):
            title = bodies[f"/api/meetings/{mid}?include_parked=true"]["title"]
            get_database().meetings.save_meeting(MeetingState(id=mid, title=title, started_at=datetime.now().astimezone()))
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            def replay(route):
                url = urlsplit(route.request.url)
                key = url.path + (f"?{url.query}" if url.query else "")
                if route.request.method == "GET" and (key in bodies or key + "?include_parked=true" in bodies):
                    route.fulfill(json=bodies.get(key, bodies.get(key + "?include_parked=true")))
                else:
                    route.continue_()
            page.clock.set_fixed_time(datetime.fromisoformat(prepared["_now"]))
            page.route("**/api/**", replay)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            def record(mid):
                _api(page, "POST", "/api/desk/windows/surface-meetings/open", {"object_ref": f"meeting:{mid}"}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                window = page.locator("#surface-meetings")
                window.get_by_test_id("meeting-toolbar").wait_for()
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-meetings/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                return window
            def seat(label):
                tab = window.get_by_role("tab", name=label, exact=True)
                if tab.is_visible(): tab.click()
                else:
                    window.get_by_role("button", name="Meeting contents more", exact=True).click()
                    page.get_by_role("menuitem", name=label, exact=True).click()
            def shot(state):
                _settle(page)
                assert window.evaluate("el => { const b=el.querySelector('.desk-surface-body'); return b.scrollHeight<=b.clientHeight+1 && b.scrollWidth<=b.clientWidth+1; }"), state
                page.screenshot(path=str(shots / f"meeting-reader-{state}-{'900x600' if width == 1440 else '393'}-after.png"))
            window = record("c5-review")
            seat("Results")
            window.get_by_test_id("meeting-prepared-adr").click()
            expect(window.get_by_test_id("meeting-prepared-draft")).to_contain_text("idempotency")
            shot("result-ready")
            bodies["/api/meetings/c5-review/prepared"] = prepared["/api/meetings/c5-review/prepared#writing"]
            window = record("c5-review")
            seat("Results")
            window.get_by_test_id("meeting-prepared-adr").click()
            expect(window.get_by_role("log", name="Prepared draft")).to_contain_text("Writing draft")
            shot("result-writing")
            bodies["/api/meetings/c5-review/prepared"] = failed
            window = record("c5-review")
            seat("Results")
            window.get_by_test_id("meeting-prepared-adr").click()
            expect(window.get_by_role("alert")).to_contain_text("engine did not finish")
            shot("result-failed")
            window = record("m-ran")
            seat("Context")
            expect(window.get_by_role("grid", name="Meeting context")).to_contain_text("Thursday sync")
            shot("context")
            window = record("m-saved-outcomes")
            seat("Proposals")
            grid = window.get_by_role("grid", name="Proposals", exact=True)
            grid.locator('[data-object-id]').first.click()
            assert grid.locator('[role="row"] button').count() == 0
            shot("proposals")
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
