"""Lane A: real HTTP, durable summary/receipt, and unchanged face inspection.

The engine is a controlled stub. These shots are backend integration evidence;
lane B owns disclosure controls and summary presentation on the face.
"""
from datetime import datetime, timedelta
from pathlib import Path
import time

from holdspeak.intel_queue import process_next_intel_job
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from tests.unit.test_meeting_deferred_admission import FakeHost, FakeIntel, _Route
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle


SHOTS = Path(__file__).resolve().parents[2] / (
    "pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a"
)
TOKEN = "hs201-lane-a-fixture"


def test_summary_and_receipt_survive_real_hub_restart_on_both_glasses(tmp_path, monkeypatch):
    from holdspeak.db import get_database
    from playwright.sync_api import sync_playwright

    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json"))
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _configure(db)
    engine = FakeIntel()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(()))
    monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(()))
    _profile(db, "lane-a-summary", claims=("language", _result_claim("meeting.deferred_analysis")))
    now = datetime.now()
    meeting = MeetingState(
        id="lane-a-fixture", title="Lane A fixture meeting",
        started_at=now - timedelta(minutes=1), ended_at=now,
        capture_status="finalized", transcription_status="final",
        segments=[TranscriptSegment("We agreed to send the budget report.", "Me", 0.0, 2.0)],
    )
    db.meetings.save_meeting(meeting)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            selected = _api(page, "POST", "/api/concierge/summary-selection", {
                "commandId": "lane-a-glass-selection", "expectedAssignmentRevision": 0,
                "profileId": "lane-a-summary", "profileRevision": 1,
            }, token=TOKEN)
            assert selected["status"] == "succeeded"
            before = _api(page, "GET", f"/api/meetings/{meeting.id}", token=TOKEN)
            planned = before["planned_route"]
            assert planned["status"] == "ready" and len(planned["legs"]) == 1
            queued = _api(page, "POST", f"/api/meetings/{meeting.id}/intelligence/run", {
                "expected_selection_hash": planned["selection_hash"],
            }, token=TOKEN)
            assert queued["state"] == "queued", queued
            for _ in range(100):
                if db.meetings.get_meeting(meeting.id).intel is not None:
                    break
                process_next_intel_job()
                time.sleep(0.05)
            saved = db.meetings.get_meeting(meeting.id)
            assert saved is not None and saved.intel is not None
            assert saved.intel.summary == engine.result.summary
            after = _api(page, "GET", f"/api/meetings/{meeting.id}/intel-recovery", token=TOKEN)
            receipt = after["run_receipt"]
            assert receipt["outcome"] == "succeeded"
            assert receipt["selection_hash"] == planned["selection_hash"]
            assert receipt["attempts"] and receipt["attempts"][0]["host"] == planned["legs"][0]["host"]

            server.stop()
            url = server.start()
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            reopened = _api(page, "GET", f"/api/meetings/{meeting.id}/intel-recovery", token=TOKEN)
            assert reopened["run_receipt"] == receipt
            assert db.meetings.get_meeting(meeting.id).intel.summary == engine.result.summary
            print(f"SUMMARY meeting={meeting.id} text={engine.result.summary!r}")
            print(f"RECEIPT after hub restart={receipt!r}")

            for width in (1440, 393):
                page.set_viewport_size({"width": width, "height": 900 if width == 1440 else 852})
                _normal_chair(page)
                page.evaluate("""() => {
                    localStorage.removeItem('hs.desk.workspace.v1');
                    sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key:'review-meetings'}));
                }""")
                page.reload(wait_until="load")
                _normal_chair(page)
                row = page.get_by_test_id(f"meeting-row-{meeting.id}")
                row.locator(".meetings-stream-row-body").click()
                page.get_by_text("We agreed to send the budget report.", exact=True).wait_for()
                _settle(page)
                _assert_clean(page, errors)
                shot = SHOTS / f"meeting-after-restart-{width}.png"
                page.screenshot(path=str(shot))
                assert shot.stat().st_size > 2000
                print(f"SHOT {shot}")
            browser.close()
    finally:
        server.stop()
