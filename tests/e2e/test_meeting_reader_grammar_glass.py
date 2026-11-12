"""Meeting object seats, failure, live work and questions on an isolated hub."""
import json
import re
import os
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
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/meetings11"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        db = get_database()
        now = datetime.now().astimezone()
        db.projects.create_project(project_id="reader-platform", name="Platform", description="", keywords=[])
        for mid, state in (("reader", "completed"), ("reader-running", "running"), ("reader-failed", "error"), ("reader-empty", "disabled")):
            db.meetings.save_meeting(MeetingState(id=mid, title={"reader":"Platform review", "reader-running":"Release review", "reader-failed":"Vendor review", "reader-empty":"Planning review"}[mid],
                started_at=now - timedelta(hours=1), ended_at=now - timedelta(minutes=30),
                segments=[TranscriptSegment(text="We move the release to Friday. Dana will write the migration plan.", speaker="Dana", start_time=1.0, end_time=4.0)] if mid != "reader-empty" else [],
                intel=IntelSnapshot(timestamp=1.0, topics=["Release"], summary="The team agreed to move the release to Friday. Dana will write the migration plan.", action_items=[]) if mid == "reader" else None,
                intel_status=state, intel_requested_at=now - timedelta(seconds=30) if state == "running" else None,
                intel_status_detail="The summary engine timed out." if state == "error" else "Reading transcript" if state == "running" else None))
        db.plugins.record_artifact(artifact_id="reader-decision", meeting_id="reader", artifact_type="decisions", title="Decisions",
            structured_json={"decisions": [{"decision": "Move the release to Friday."}]}, plugin_id="decision_capture")
        task = db.proposals.create_proposal(meeting_id="reader", project_id=None, kind="action", text="Write the migration plan", source_plugin="summary")
        decision = db.proposals.create_proposal(meeting_id="reader", project_id=None, kind="decision", text="Move the rollout to Friday", source_plugin="decision_capture")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                if width == 393:
                    task = db.proposals.create_proposal(meeting_id="reader", project_id=None, kind="action", text="Write the migration plan", source_plugin="summary")
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
                if os.environ.get("HOLDSPEAK_R3_TAPE") == "1":
                    tape = {"_source": {"rig": "test_meeting_reader_grammar_glass.py", "engine": "none"}}
                    for suffix in ("?include_parked=true", "/outcome-review", "/intel-recovery", "/sync-conflicts"):
                        path = f"/api/meetings/reader{suffix}"
                        tape[path] = _api(page, "GET", path, token=TOKEN)
                    tape["/api/meetings?limit=100"] = _api(page, "GET", "/api/meetings?limit=100", token=TOKEN)
                    target = Path(__file__).resolve().parents[2] / "web/src/desk/__tests__/fixtures/meetings-hub/reader-r3.json"
                    target.write_text(json.dumps(tape, indent=2) + "\n")
                    browser.close()
                    return

                def shot(state):
                    _settle(page)
                    assert window.evaluate("""el => { const b=el.querySelector('.desk-surface-body'); return b.scrollHeight <= b.clientHeight+1 && b.scrollWidth <= b.clientWidth+1; }"""), state
                    for form in window.locator('.surface-inspector-form[data-completion]').all():
                        assert form.evaluate("""el => {const fields=el.querySelector('.surface-inspector-fields'), rows=[...fields.querySelectorAll('.gadget-row')], verbs=el.querySelector('.surface-inspector-actions'); if(!rows.length)return true; const first=rows[0].getBoundingClientRect(),last=(el.querySelector('.surface-inspector-notice')||rows.at(-1)).getBoundingClientRect(),f=fields.getBoundingClientRect(),v=verbs.getBoundingClientRect(); return first.top>=f.top-1 && first.bottom<=f.bottom+1 && v.top-last.bottom<=20 && v.bottom<=el.getBoundingClientRect().bottom+1;}"""), state
                    page.screenshot(path=str(shots / f"meeting-reader-{state}-{'900x600' if width == 1440 else '393'}.png"))

                def verb(label):
                    button = window.get_by_role("button", name=label, exact=True)
                    if button.is_visible(): button.click()
                    else:
                        row_bar = window.get_by_role("grid").locator(".object-list-inner-toolbar")
                        anchor = row_bar.get_by_role("button", name="Actions ▾", exact=True) if label in ("Edit", "Dismiss", "Confirm", "Done", "Reopen") else window.get_by_test_id("meeting-toolbar").get_by_role("button", name="Actions ▾", exact=True)
                        anchor.click()
                        page.get_by_role("menuitem", name=label, exact=True).click()

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
                expect(window.get_by_test_id("meeting-summary-topics")).to_contain_text("Release")
                shot("summary")
                for tab in ("Transcript", "Tasks", "Decisions", "Commitments", "Results", "Facts", "Recovery"):
                    seat(tab)
                    expect(window.get_by_role("toolbar")).to_have_count(2 if window.get_by_role("grid").count() else 1)
                    expect(window.get_by_test_id("meeting-toolbar").get_by_role("button", name="Actions ▾", exact=True)).to_have_count(1)
                    if tab in ("Tasks", "Decisions", "Commitments", "Results"):
                        word = "Confirm" if tab == "Tasks" else "Read" if tab == "Results" else "Open"
                        selected_verb = window.get_by_role("button", name=word, exact=True)
                        if selected_verb.is_visible():
                            expect(selected_verb).to_be_disabled()
                            assert selected_verb.evaluate("el => getComputedStyle(el).color") != window.get_by_test_id("meeting-toolbar").get_by_role("button", name="Actions ▾", exact=True).evaluate("el => getComputedStyle(el).color")
                        else:
                            window.get_by_role("grid").get_by_role("button", name="Actions ▾", exact=True).click()
                            expect(page.get_by_role("menuitem", name=re.compile("^" + re.escape(word) + r"(?: Return)?$"))).to_be_disabled()
                            page.keyboard.press("Escape")
                    assert window.get_by_role("button", name="Delete", exact=True).count() == 0
                    if tab == "Recovery":
                        expect(window.get_by_role("tabpanel")).to_contain_text("No repair needed")
                        expect(window.get_by_test_id("meeting-status")).to_contain_text("Ready")
                    shot(tab.lower())
                recovery_reads = []
                recovery_path = "**/api/meetings/reader/intel-recovery"
                page.route(recovery_path, lambda route: recovery_reads.append(route))
                seat("Facts")
                seat("Recovery")
                expect(window.get_by_test_id("meeting-status")).to_contain_text("Reading recovery")
                shot("recovery-loading")
                for route in recovery_reads:
                    route.fulfill(status=503, json={"detail": "Hub unavailable"})
                expect(window.get_by_role("alert")).to_contain_text("Recovery not read")
                expect(window.get_by_test_id("meeting-status").get_by_role("status")).to_have_text("Failed")
                expect(window.get_by_text("Recovery not read", exact=True)).to_have_count(1)
                shot("recovery-failed")
                page.unroute(recovery_path)
                window.get_by_role("button", name="Try again", exact=True).click()
                expect(window.get_by_role("tabpanel")).to_contain_text("No repair needed")
                seat("Decisions")
                decision_row = window.get_by_test_id(f"meeting-outcome-ft-{decision.id}")
                decision_row.click()
                verb("Edit")
                window.get_by_role("textbox", name="Decision", exact=True).fill("Move the rollout to next Friday")
                assert window.get_by_role("grid", name="Decisions", exact=True).count() == 0
                shot("decision-edit")
                confirm_path = f"**/api/proposals/{decision.id}/confirm"
                page.route(confirm_path, lambda route: route.fulfill(status=503, json={"detail": "Hub unavailable"}))
                window.get_by_role("region", name="Edit decision", exact=True).get_by_role("button", name="Confirm", exact=True).click()
                expect(window.get_by_role("textbox", name="Decision", exact=True)).to_have_value("Move the rollout to next Friday")
                expect(window.get_by_test_id("meeting-status")).to_contain_text("Failed")
                expect(window.get_by_role("alert")).to_contain_text("Hub unavailable")
                shot("decision-edit-failed")
                page.unroute(confirm_path)
                window.get_by_role("button", name="Cancel", exact=True).click()
                seat("Tasks")
                row = window.get_by_test_id(f"meeting-task-{task.id}")
                row.click()
                window.get_by_test_id("meeting-toolbar").get_by_role("button", name="Actions ▾", exact=True).click()
                shot("task-actions")
                page.keyboard.press("Escape")
                expect(window.get_by_role("tabpanel")).not_to_contain_text("Could not confirm")
                assert "Could not confirm" not in window.inner_text()
                shot("task-selected")
                row.click(button="right")
                page.get_by_role("menu", name="Tasks to confirm actions", exact=True).get_by_role("menuitem", name="Edit", exact=True).click()
                window.get_by_role("textbox", name="Owner", exact=True).fill("Dana")
                shot("task-edit")
                page.route(f"**/api/proposals/{task.id}/edit", lambda route: route.fulfill(status=503, json={"detail": "Hub unavailable"}))
                window.get_by_role("button", name="Save", exact=True).click()
                expect(window.get_by_role("alert")).to_contain_text("Not saved")
                expect(window.get_by_role("textbox", name="Owner", exact=True)).to_have_value("Dana")
                expect(window.get_by_test_id("meeting-status")).to_contain_text("Failed")
                expect(window.get_by_test_id("meeting-status")).not_to_contain_text("Could not confirm")
                shot("task-edit-failed")
                window.get_by_role("button", name="Cancel", exact=True).click()
                page.unroute(f"**/api/proposals/{task.id}/edit")
                seat("Commitments")
                window.get_by_test_id(f"meeting-outcome-ft-{task.id}").click()
                verb("Edit")
                expect(window.get_by_role("textbox", name="Commitment", exact=True)).to_have_value("Write the migration plan")
                shot("commitment-edit")
                task_confirm = f"**/api/proposals/{task.id}/confirm"
                page.route(task_confirm, lambda route: route.fulfill(status=503, json={"detail":"Hub unavailable"}))
                window.get_by_role("region", name="Edit commitment", exact=True).get_by_role("button", name="Confirm", exact=True).click()
                expect(window.get_by_role("alert")).to_contain_text("Hub unavailable")
                shot("commitment-edit-failed")
                page.unroute(task_confirm)
                window.get_by_role("button", name="Cancel", exact=True).click()
                seat("Tasks")
                row.click()
                verb("Edit")
                window.get_by_role("textbox", name="Owner", exact=True).fill("Dana")
                window.get_by_role("textbox", name="Due", exact=True).fill("Friday")
                window.get_by_role("button", name="Save", exact=True).click()
                expect(row).to_contain_text("Dana")
                verb("Confirm")
                expect(row).to_have_count(0)
                seat("Commitments")
                commitment = window.get_by_role("grid", name="Commitments", exact=True).locator('[data-object-id]').filter(has_text="Write the migration plan").last
                commitment.click()
                verb("Done")
                expect(window.get_by_test_id("meeting-status")).to_contain_text("Done")
                shot("commitment-done")
                verb("Reopen")
                expect(window.get_by_test_id("meeting-status")).to_contain_text("Opened again")
                shot("commitment-reopened")
                seat("Summary")
                for label, name in (("Send to…", "send"), ("Rename", "rename"), ("Decide", "decide"), ("Add to Project", "project")):
                    verb(label)
                    if name == "rename":
                        expect(window.get_by_role("textbox", name="Name", exact=True)).to_have_value("Platform review")
                    if name == "send":
                        expect(window.locator('[data-send="face"]')).to_be_visible()
                    if name == "decide":
                        window.get_by_role("textbox", name="Decision title", exact=True).fill("Move the release to Friday")
                    if name == "project":
                        expect(page.get_by_role("menu", name="Add to Project", exact=True)).to_contain_text("Platform")
                    shot(name)
                    window.get_by_test_id("meeting-pane-back" if width == 1440 else "meeting-record-back" if name != "send" else "meeting-send-back").click()
                    expect(window.get_by_test_id("meeting-summary")).to_be_visible()
                verb("Delete")
                question = window.get_by_role("region", name="Delete Platform review?", exact=True)
                expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                shot("delete-question")
                question.get_by_role("button", name="Cancel", exact=True).click()
                assert not db.meetings.get_meeting("reader").parked
                for mid, state in (("reader-running", "running"), ("reader-failed", "failed"), ("reader-empty", "empty")):
                    window = open_record(mid)
                    if state == "failed":
                        expect(window.get_by_test_id("meeting-summary-failure")).to_contain_text("The summary engine timed out.")
                        expect(window.get_by_role("button", name="Try again", exact=True)).to_be_enabled()
                        expect(window.locator(".desk-pullout-title")).to_contain_text("Vendor review")
                    if state == "running":
                        expect(window.get_by_role("log", name="Summary work")).to_contain_text("Reading transcript")
                        expect(window.get_by_test_id("meeting-status")).to_contain_text("Summary running")
                    shot(state)
                    if state == "failed":
                        seat("Recovery")
                        expect(window.get_by_test_id("meeting-status")).to_contain_text("Repair needed")
                        expect(window.get_by_test_id("recovery-sentence")).to_have_css("text-transform", "none")
                        assert "Inter" in window.get_by_test_id("recovery-sentence").evaluate("el=>getComputedStyle(el).fontFamily")
                        shot("recovery-repair")
                held = []
                read_pattern = "**/api/meetings/reader?include_parked=true"
                read_mode = "hold"
                def read_meeting(route):
                    if read_mode == "hold":
                        held.append(route)
                    elif not page.evaluate("window.__meetingRetryPressed === true"):
                        route.fulfill(status=503, json={"detail":"Hub unavailable"})
                    else:
                        route.continue_()
                page.route(read_pattern, read_meeting)
                window = open_record("reader")
                expect(window.get_by_test_id("meeting-status")).to_contain_text("Reading meeting")
                shot("loading")
                read_mode = "fail"
                for route in held:
                    route.fulfill(status=503, json={"detail": "Hub unavailable"})
                expect(window.get_by_role("alert")).to_contain_text("Hub unavailable")
                expect(window.locator(".desk-pullout-title")).to_contain_text("Platform review")
                shot("read-failed")
                retry = window.get_by_role("button", name="Try again", exact=True)
                retry.evaluate("el => el.addEventListener('click', () => { window.__meetingRetryPressed = true; }, {capture:true, once:true})")
                retry.click()
                expect(window.get_by_test_id("meeting-summary")).to_contain_text("release to Friday")
                page.unroute(read_pattern)
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
    speech = json.loads((fixtures / "p17t.json").read_text())
    speech_ready = json.loads((fixtures / "p17t-ready.json").read_text())
    bodies = {**saved, **prepared, **ran, **speech}
    bodies["/api/meetings/m-ran?include_parked=true"] = {**bodies["/api/meetings/m-ran?include_parked=true"], "run_receipt": looked}
    shots = root / ".tmp/evidence-shots/meetings11"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        for mid in ("c5-review", "m-saved-outcomes", "m-ran", "m-off-words", "p17-audio-only"):
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
                    _settle(page)
                    page.screenshot(path=str(shots / f"meeting-reader-more-{393 if width == 393 else '900x600'}.png"))
                    page.get_by_role("menuitem", name=label, exact=True).click()
            def shot(state):
                _settle(page)
                expect(window.get_by_role("toolbar")).to_have_count(2 if window.get_by_role("grid").count() else 1)
                assert window.evaluate("el => { const b=el.querySelector('.desk-surface-body'); return b.scrollHeight<=b.clientHeight+1 && b.scrollWidth<=b.clientWidth+1; }"), state
                page.screenshot(path=str(shots / f"meeting-reader-{state}-{'900x600' if width == 1440 else '393'}.png"))
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
            expect(window.get_by_test_id("meeting-status").get_by_role("status")).to_have_text("Draft failed")
            shot("result-failed")
            window = record("m-ran")
            seat("Context")
            expect(window.get_by_role("grid", name="Meeting context")).to_contain_text("Thursday sync")
            expect(window.get_by_role("grid", name="Meeting context")).not_to_contain_text("2026-10-15")
            shot("context")
            window = record("m-saved-outcomes")
            seat("Proposals")
            grid = window.get_by_role("grid", name="Proposals", exact=True)
            grid.locator('[data-object-id]').first.click()
            assert grid.locator('[role="row"] button').count() == 0
            shot("proposals")
            bodies["/api/meetings/m-off-words?include_parked=true"] = {**saved["/api/meetings/m-off-words?include_parked=true"], "intel_status": json.loads((fixtures / "reader-r2.json").read_text())["/api/meetings/vendor"]["intel_status"]}
            page.clock.set_fixed_time(datetime.fromisoformat(saved["_now"]))
            window = record("m-off-words")
            expect(window.get_by_role("button", name="Try again", exact=True)).to_be_enabled()
            shot("failed-retry")
            for tape, name, test_id in ((speech, "audio-setup", "meeting-transcribe-speech-setup-verb"), (speech_ready, "audio-ready", "meeting-transcribe-verb")):
                bodies.update(tape)
                window = record("p17-audio-only")
                window.get_by_test_id("meeting-toolbar").get_by_role("button", name="Actions ▾", exact=True).click()
                page.get_by_role("menuitem", name="Audio and speech", exact=True).click()
                expect(window.get_by_test_id(test_id)).to_be_visible()
                expect(window.get_by_role("tabpanel")).to_contain_text("Speech ready" if name == "audio-ready" else "Speech is not set up")
                expect(window.get_by_test_id("meeting-status").get_by_role("status")).to_have_text("Ready" if name == "audio-ready" else "Setup needed")
                expect(window.get_by_role("tabpanel")).not_to_contain_text("huggingface.co")
                words = window.get_by_role("tabpanel").get_by_text("Speech ready" if name == "audio-ready" else "Speech is not set up", exact=True).bounding_box()
                verb = window.get_by_test_id(test_id).bounding_box()
                assert words and verb and abs((words["y"] + words["height"] / 2) - (verb["y"] + verb["height"] / 2)) < 1
                shot(name)
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
