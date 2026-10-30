"""Meetings on a real hub, without a browser (the test diet, 2026-10-11).

Each test boots the real hub on an isolated HOME and DB (``glass_infra._boot``,
the same rig the browser tests used) and talks to it over HTTP, with the seeds
the browser tests used. The browser half of each old glass test is a vitest
(``web/src/desk/__tests__/decision.app.test.tsx``, ``philo1308Decide.test.tsx``).
"""
from __future__ import annotations

import json
import threading
import time
import wave
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.e2e.glass_infra import _boot

pytestmark = [pytest.mark.integration, pytest.mark.requires_meeting, pytest.mark.timeout(240)]


def _call(base: str, method: str, path: str, body: Any = None, *, token: str, ok: bool = True,
          **kwargs: Any) -> tuple[int, dict[str, Any]]:
    response = httpx.request(
        method, f"{base}{path}", json=body, headers={"authorization": f"Bearer {token}"},
        timeout=30.0, **kwargs,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if ok:
        assert response.status_code < 300, f"{method} {path}: HTTP {response.status_code}: {payload}"
    return response.status_code, payload if isinstance(payload, dict) else {}


def _api(base: str, method: str, path: str, body: Any = None, *, token: str) -> dict[str, Any]:
    return _call(base, method, path, body, token=token)[1]


def _wait(predicate: Any, *, timeout: float = 60.0, step: float = 0.2) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(step)
    return bool(predicate())


def _stop(server: Any) -> None:
    thread = server._thread
    server.stop()
    if thread is not None:
        thread.join(120)
        assert not thread.is_alive(), "the hub thread outlived its stop"


# ── import -> Run intelligence -> the drainer writes the summary ─────────────

OUTCOMES_TOKEN = "desk-meetings-outcomes"
DEC = "decision_capture"
ACT = "action_owner_enforcer"
STARTED = datetime(2026, 9, 7, 11, 0, 0)
TRANSCRIPT_SRT = """1
00:00:00,000 --> 00:02:00,000
Karol: Let's start with the cut-over sequencing for the payments platform.

2
00:18:00,000 --> 00:21:00,000
Priya: Cut-over runs on the read replica first, then we flip writes.

3
00:31:00,000 --> 00:33:00,000
Marek: I think the freeze window should move to Sunday two in the morning.

4
00:33:00,000 --> 00:35:00,000
Priya: I'll confirm the freeze window with the payments team.

5
00:40:00,000 --> 00:42:00,000
Marek: Someone needs to write the rollback runbook before we go.

6
00:44:00,000 --> 00:46:00,000
Karol: We should also check the numbers again before Friday.
"""
DECISIONS_JSON = json.dumps({
    "decisions": [
        {"decision": "Cut-over runs on the read replica first", "rationale": None, "source_timestamp": 1100.0},
        {"decision": "Freeze window moves to Sunday 02:00", "rationale": "less traffic", "source_timestamp": 1900.0},
    ],
    "open_questions": [],
})
ACTIONS_JSON = json.dumps({
    "action_items": [
        {"task": "Confirm the freeze window with the payments team", "owner": None, "due": None},
        {"task": "Draft the rollback runbook", "owner": None, "due": None},
        {"task": "Book the war room for the cut-over night", "owner": "Karol", "due": "Friday"},
    ],
})


def _scripted_engine() -> Any:
    """The one fake of the HS-200-12 rig: the model's completion text."""
    from tests.unit.test_meeting_deferred_admission import FakeIntel

    class ScriptedIntel(FakeIntel):
        def __init__(self) -> None:
            super().__init__()
            self.plugin_calls: list[str] = []

        def _chat_completion_text(self, messages: Any, *, temperature: float, max_tokens: int) -> str:
            system = str(messages[0].get("content") or "") if messages else ""
            plugin = DEC if "decisions and open questions" in system else ACT
            self.plugin_calls.append(plugin)
            return DECISIONS_JSON if plugin == DEC else ACTIONS_JSON

    return ScriptedIntel()


def test_an_imported_meeting_run_with_the_disclosed_hash_reaches_a_six_turn_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """replaces: tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_summary_ready
    and the tripwire of its two strict-xfail rows
    (test_meeting_review_proposals_stay_live_under_amendment,
    test_meeting_partial_chain_retry_stays_live_under_amendment).

    The real import route, the disclosed selection hash, the hub's own
    lifespan drainer, the real summary. Capture C4 brought the plugin ->
    proposal pipeline back (it was parked by the HS-201 analysis-only
    amendment): the job's plugins run on its disclosed route, and the review
    holds the plugins' five proposals, as
    tests/e2e/_parked/test_hs200_meeting_outcomes_glass.py asserted."""
    from holdspeak import intel_queue_conductor as conductor
    from holdspeak.db import get_database
    from holdspeak.runtime_lock import claim_database, current_lock, release_database
    from tests.unit.test_meeting_deferred_admission import _assign_deferred_queue_routes, _Route

    home = tmp_path / "home"
    (home / ".holdspeak").mkdir(parents=True, exist_ok=True)
    # The rig's subject is the owner's Run gesture, so "after every meeting" is off.
    (home / ".holdspeak" / "config.json").write_text(json.dumps({"meeting": {
        "intel_retry_base_seconds": 2, "intel_retry_max_seconds": 4, "intelligence_auto": "off",
    }}), encoding="utf-8")
    assert current_lock() is None, "this process already owns a database"
    # The drainer is the owner's scheduled work (HS-200-42): claim the DB as
    # the hub command does at boot, so the lifespan starts it.
    assert claim_database(tmp_path / "holdspeak.db").held
    server, base = _boot(tmp_path, monkeypatch, token=OUTCOMES_TOKEN)
    try:
        engine = _scripted_engine()
        _assign_deferred_queue_routes(get_database())
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
        monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript",
                            lambda **kwargs: _Route((DEC, ACT)))
        assert conductor.drainer_state() == "running", "the hub lifespan started no drainer"
        api = lambda method, path, body=None: _api(base, method, path, body, token=OUTCOMES_TOKEN)  # noqa: E731

        project_id = api("POST", "/api/projects", {
            "name": "Q4 platform", "description": "Seeded for the meetings test.",
            "command_id": "desk-meetings-proj",
        })["project"]["id"]
        status, imported = _call(
            base, "POST", "/api/meetings/import", token=OUTCOMES_TOKEN, ok=False,
            files={"file": ("architecture-review.srt", TRANSCRIPT_SRT.encode(), "text/plain")},
            data={"title": "Summary-ready meeting", "started_at_ms": str(int(STARTED.timestamp() * 1000))},
        )
        assert status == 202, imported
        meeting_id = str(imported["meeting_id"])
        assert _wait(lambda: len(api("GET", f"/api/meetings/{meeting_id}").get("segments") or []) == 6,
                     timeout=30), "the import never produced six segments"
        api("POST", f"/api/projects/{project_id}/meetings/{meeting_id}")

        planned = api("GET", f"/api/meetings/{meeting_id}")["planned_route"]
        assert planned["status"] == "ready" and planned["legs"] and planned["selection_hash"], planned
        run = api("POST", f"/api/meetings/{meeting_id}/intelligence/run",
                  {"expected_selection_hash": planned["selection_hash"]})
        assert run["state"] == "queued" and run["drainer"] == "running", run
        assert run["planned_route"]["selection_hash"] == planned["selection_hash"], run

        def ready() -> bool:
            detail = api("GET", f"/api/meetings/{meeting_id}")
            return (detail.get("intel_status") or {}).get("state") == "ready" and bool(detail.get("intel"))

        assert _wait(ready, timeout=90), api("GET", f"/api/meetings/{meeting_id}")
        detail = api("GET", f"/api/meetings/{meeting_id}")
        assert len(detail["segments"]) == 6
        assert detail["intel"]["summary"] == engine.result.summary
        review = api("GET", f"/api/meetings/{meeting_id}/outcome-review")
        assert review["job"]["status"] == "succeeded", review["job"]
        assert (review["coverage"]["turns"], review["coverage"]["read"], review["coverage"]["state"]) == (
            6, 6, "available"), review["coverage"]
        # Capture C4: the plugin chain is live again. The job's plugins run on
        # its disclosed route, and their output becomes the proposals (the
        # bridge takes decisions and actions from the plugins, never twice).
        assert sorted(engine.plugin_calls) == [ACT, DEC], engine.plugin_calls
        proposals = review["proposals"]
        assert sorted(p["kind"] for p in proposals) == ["action", "action", "action", "decision", "decision"], proposals
        assert {p["text"] for p in proposals if p["kind"] == "decision"} == {
            item["decision"] for item in json.loads(DECISIONS_JSON)["decisions"]
        }, proposals
        assert all(p["job_id"] == review["job"]["job_id"] for p in proposals), proposals
    finally:
        _stop(server)
        conductor.stop_intel_queue_conductor()
        release_database()


# ── the summary and its receipt survive a hub restart ────────────────────────

LANE_A_TOKEN = "desk-meetings-restart"


def test_the_summary_and_its_receipt_survive_a_hub_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """replaces: tests/e2e/test_hs201_lane_a_glass.py::test_summary_and_receipt_survive_real_hub_restart_on_both_glasses

    The lane A seed: a saved meeting, a stub engine, the summary selection.
    The run receipt and the summary read the same after the hub stops and
    starts again, and from a new connection to the same DB file."""
    from holdspeak.db import Database, get_database
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    from tests.unit.test_meeting_deferred_admission import FakeHost, FakeIntel, _Route
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    server, base = _boot(tmp_path, monkeypatch, token=LANE_A_TOKEN)
    try:
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
        api = lambda method, path, body=None: _api(base, method, path, body, token=LANE_A_TOKEN)  # noqa: E731
        api("POST", "/api/desk/seed")
        api("PUT", "/api/setup/onboarding", {"disposition": "completed"})
        selected = api("POST", "/api/concierge/summary-selection", {
            "commandId": "lane-a-selection", "expectedAssignmentRevision": 0,
            "profileId": "lane-a-summary", "profileRevision": 1,
        })
        assert selected["status"] == "succeeded", selected
        planned = api("GET", f"/api/meetings/{meeting.id}")["planned_route"]
        assert planned["status"] == "ready" and len(planned["legs"]) == 1, planned
        queued = api("POST", f"/api/meetings/{meeting.id}/intelligence/run",
                     {"expected_selection_hash": planned["selection_hash"]})
        assert queued["state"] == "queued", queued
        for _ in range(100):
            if db.meetings.get_meeting(meeting.id).intel is not None:
                break
            process_next_intel_job()
            time.sleep(0.05)
        assert db.meetings.get_meeting(meeting.id).intel.summary == engine.result.summary
        receipt = api("GET", f"/api/meetings/{meeting.id}/intel-recovery")["run_receipt"]
        assert receipt["outcome"] == "succeeded"
        assert receipt["selection_hash"] == planned["selection_hash"]
        assert receipt["attempts"] and receipt["attempts"][0]["host"] == planned["legs"][0]["host"]

        _stop(server)
        base = server.start()
        api = lambda method, path, body=None: _api(base, method, path, body, token=LANE_A_TOKEN)  # noqa: E731
        assert api("GET", f"/api/meetings/{meeting.id}/intel-recovery")["run_receipt"] == receipt
        assert api("GET", f"/api/meetings/{meeting.id}")["intel"]["summary"] == engine.result.summary
        reopened = Database(Path(db.db_path))
        assert reopened.intel.get_run_receipt(meeting.id) == receipt
        assert reopened.meetings.get_meeting(meeting.id).intel.summary == engine.result.summary
    finally:
        _stop(server)


# ── a meeting saved with its audio only is transcribed in place ──────────────

TRANSCRIBE_TOKEN = "desk-meetings-transcribe"
AUDIO_MEETING = "p17-audio-only"
LINE = "we ship the speech fix on friday"
FIXTURE_WAV = Path(__file__).parents[1] / "fixtures" / "core_path_smoke_16k.wav"


class _ReplayTranscriber:
    def transcribe(self, _audio: Any, **_kwargs: Any) -> str:
        return LINE


def _seed_audio_only(db: Any) -> None:
    """The PHILO-17 transcribe glass seed: saved record-only, audio in the real journal."""
    import numpy as np

    from holdspeak.meeting_capture_journal import MeetingCaptureJournal
    from holdspeak.meeting_session import MeetingState

    now = datetime.now()
    meeting = MeetingState(id=AUDIO_MEETING, title="Standup with audio only",
                           started_at=now - timedelta(minutes=2), ended_at=now, segments=[])
    meeting.capture_status = "finalized"
    meeting.intel_status = "disabled"
    meeting.transcription_status = "record_only"
    meeting.transcription_status_detail = {
        "family": "speech-recognition-route-assignments",
        "reason_code": "speech_not_set_up",
        "repair": "set_up_speech",
    }
    db.meetings.save_meeting(meeting)
    with wave.open(str(FIXTURE_WAV), "rb") as wav:
        audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    journal = MeetingCaptureJournal(AUDIO_MEETING)
    journal.append("mic", audio)
    journal.finalize()


def test_an_audio_only_meeting_is_refused_without_speech_and_transcribed_in_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """replaces: tests/e2e/test_philo17_transcribe_glass.py::test_an_audio_only_meeting_is_transcribed_in_place (T1 half)

    The service fact is also fenced by tests/unit/test_philo17_transcribe_saved.py::
    test_transcribe_turns_kept_audio_into_the_same_meetings_transcript; this
    one goes through the hub's HTTP route, as the face does."""
    from holdspeak.db import get_database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.web.routes import meeting_import as import_route

    server, base = _boot(tmp_path, monkeypatch, token=TRANSCRIBE_TOKEN)
    try:
        db = get_database()
        _configure(db)
        monkeypatch.setattr(import_route, "_frozen_transcriber_factory", lambda _construct: _ReplayTranscriber())
        _seed_audio_only(db)
        api = lambda method, path, body=None: _api(base, method, path, body, token=TRANSCRIBE_TOKEN)  # noqa: E731

        # 1. Speech not set up (this HOME has no model): the route refuses.
        assert api("GET", "/api/setup/local-ai")["speech"]["ready"] is False
        status, refused = _call(base, "POST", f"/api/meetings/{AUDIO_MEETING}/transcribe",
                                token=TRANSCRIBE_TOKEN, ok=False)
        assert status == 409 and refused.get("code") == "speech_not_set_up", (status, refused)
        assert db.meetings.get_meeting(AUDIO_MEETING).segments == []

        # 2. Speech set up (a readiness double): the meeting says so; Transcribe
        # writes the transcript into the SAME meeting.
        monkeypatch.setattr(
            "holdspeak.whisper_models.speech_readiness",
            lambda name, backend, *, home=None: {
                "model": name or "base", "backend": "mlx", "state": "on_device", "ready": True, "bytes": 0,
            },
        )
        assert api("GET", f"/api/meetings/{AUDIO_MEETING}")["transcribe_speech"]["ready"] is True
        status, started = _call(base, "POST", f"/api/meetings/{AUDIO_MEETING}/transcribe",
                                token=TRANSCRIBE_TOKEN, ok=False)
        assert status < 300 and started.get("meeting_id") == AUDIO_MEETING, (status, started)
        for thread in threading.enumerate():
            if thread.name == f"meeting-transcribe-{AUDIO_MEETING}":
                thread.join(timeout=60)
        assert _wait(lambda: db.meetings.get_meeting(AUDIO_MEETING).transcription_status == "complete", timeout=30)
        saved = db.meetings.get_meeting(AUDIO_MEETING)
        assert [seg.text for seg in saved.segments] == [LINE]
        detail = api("GET", f"/api/meetings/{AUDIO_MEETING}")
        assert [seg["text"] for seg in detail["segments"]] == [LINE]
    finally:
        _stop(server)


# ── Decide: the decision is saved with its meeting and its project ───────────

DECIDE_TOKEN = "desk-meetings-decide"
MEETING = "p13-checkout"
MEETING_TITLE = "Checkout latency review"
MEETING_B = "p13-hiring"


def _seed_meetings(db: Any) -> None:
    """The PHILO-13-08 decide glass seeds (meeting A with a summary, meeting B)."""
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db.meetings.save_meeting(MeetingState(
        id=MEETING, started_at=datetime(2026, 10, 1, 9, 0, 0), ended_at=datetime(2026, 10, 1, 9, 30, 0),
        title=MEETING_TITLE,
        segments=[
            TranscriptSegment(text="p99 doubled after the cache change.", speaker="Avery", start_time=0.0, end_time=3.0),
            TranscriptSegment(text="We roll it back today.", speaker="Priya", start_time=4.0, end_time=8.0),
        ],
        intel=IntelSnapshot(timestamp=8.0, topics=["Latency"], summary="p99 doubled after the cache change.",
                            action_items=[{"id": "p13-08-a1", "task": "Roll back the cache", "owner": "Priya"}])))
    db.meetings.save_meeting(MeetingState(
        id=MEETING_B, started_at=datetime(2026, 9, 30, 14, 0, 0), ended_at=datetime(2026, 9, 30, 14, 20, 0),
        title="Hiring debrief",
        segments=[TranscriptSegment(text="We hire for the platform team.", speaker="Sam", start_time=0.0, end_time=3.0)],
        intel=IntelSnapshot(timestamp=3.0, topics=["Hiring"], summary="Run a second ops interview.",
                            action_items=[])))


def _decision_rows(db: Any) -> list[dict[str, Any]]:
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT id, title, context_markdown, tags_json FROM desk_decisions ORDER BY created_at"
        ).fetchall()
    return [{"id": r[0], "title": r[1], "context": r[2], "tags": json.loads(r[3] or "[]")} for r in rows]


def _project_edges(db: Any, decision_id: str) -> list[str]:
    """A desk decision's Project edges, under its one ref name (#770)."""
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT project_id, resource_ref FROM project_resources WHERE resource_ref IN (?, ?) AND deleted = 0",
            (f"desk_decision:{decision_id}", f"decision:{decision_id}"),
        ).fetchall()
    assert all(r[1] == f"desk_decision:{decision_id}" for r in rows), [tuple(r) for r in rows]
    return [r[0] for r in rows]


def _decide(api: Any, meeting_id: str, title: str, context: str) -> dict[str, Any]:
    """What web/src/desk/decide.ts decideFromMeeting sends, call for call."""
    projects = api("GET", f"/api/meetings/{meeting_id}/projects").get("projects") or []
    project = next((p for p in projects if str(p.get("project_id") or "").strip()), None)
    tags = [f"meeting:{meeting_id}", *([f"project:{project['project_id']}"] if project else [])]
    decision = api("POST", "/api/decisions", {
        "title": title, "status": "accepted", "context_markdown": context, "tags": tags,
    })["decision"]
    if project:
        api("PUT", f"/api/projects/{project['project_id']}/resources/desk_decision:{decision['id']}",
            {"relationship": "member"})
    return decision


def test_a_decision_from_a_meeting_is_saved_with_the_meeting_and_its_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """replaces: tests/e2e/test_philo13_08_decide_glass.py::TestDecideGlass::test_decide_in_the_meetings_record (T1 half)
    replaces: tests/e2e/test_philo13_08_decide_glass.py::TestDecideGlass::test_decide_in_the_meeting_window_and_abandoned_tries (T1 half)
    replaces: tests/e2e/test_philo13_08_decide_glass.py::TestDecideGlass::test_a_draft_never_moves_to_another_meeting (T1 half)

    The hub half of Decide: the meeting's project is the one the face reads;
    the decision keeps its meeting and project tags, the project edge is under
    `desk_decision:<id>`, and the decision's relationships list the project.
    A meeting with no project files under its meeting only. No `New decision`
    row is ever written (the face's abandoned tries post nothing:
    web/src/desk/__tests__/philo1308Decide.test.tsx)."""
    from holdspeak.db import get_database

    server, base = _boot(tmp_path, monkeypatch, token=DECIDE_TOKEN)
    try:
        db = get_database()
        _seed_meetings(db)
        api = lambda method, path, body=None: _api(base, method, path, body, token=DECIDE_TOKEN)  # noqa: E731
        project_id = api("POST", "/api/projects", {
            "name": "Checkout", "description": "The checkout path.", "command_id": "p13-08-project",
        })["project"]["id"]
        api("POST", f"/api/projects/{project_id}/meetings/{MEETING}", {})
        assert _decision_rows(db) == []

        title = "Roll back the cache change"
        made = _decide(api, MEETING, title, f"Meeting: {MEETING_TITLE} · 2026-10-01\n\np99 doubled after the cache change.")
        rows = _decision_rows(db)
        assert [r["title"] for r in rows] == [title], rows
        assert rows[0]["id"] == made["id"]
        assert rows[0]["tags"] == [f"meeting:{MEETING}", f"project:{project_id}"], rows
        assert rows[0]["context"].startswith(f"Meeting: {MEETING_TITLE} · 2026-10-01"), rows
        assert _project_edges(db, made["id"]) == [project_id]
        hub = api("GET", f"/api/decisions/{made['id']}")["decision"]
        assert hub["title"] == title and hub["status"] == "accepted"
        assert f"meeting:{MEETING}" in hub["tags"], hub
        related = api("GET", f"/api/desk/relationships/decision:{made['id']}")
        assert project_id in [str(p.get("project_id") or p.get("id") or "") for p in related.get("projects", [])], related
        assert made["id"] in {d["id"] for d in api("GET", "/api/decisions")["decisions"]}

        # Meeting B has no project: its decision files under B only.
        made_b = _decide(api, MEETING_B, "Typed under B", "Meeting: Hiring debrief · 2026-09-30")
        rows = {r["title"]: r["tags"] for r in _decision_rows(db)}
        assert rows == {title: [f"meeting:{MEETING}", f"project:{project_id}"], "Typed under B": [f"meeting:{MEETING_B}"]}
        assert _project_edges(db, made_b["id"]) == []
        assert "New decision" not in rows
    finally:
        _stop(server)


# ── a summary reads only earlier, dated sources (betterment/capture C2) ──────

EARLIER_TOKEN = "desk-meetings-earlier"


def test_a_summary_reads_only_earlier_dated_sources_and_its_receipt_lists_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three meetings on one project: Wednesday, Thursday, Friday. Thursday is
    summarised last. The memory block sent to the engine names Wednesday and
    not Friday, each line leads with its date, and the run receipt lists what
    was read. Friday's summary then lists the Thursday sync, dated 2026-10-15."""
    from holdspeak.db import get_database
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from tests.unit.test_meeting_deferred_admission import FakeHost, FakeIntel, _Route
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    class RecordingIntel(FakeIntel):
        def __init__(self) -> None:
            super().__init__()
            self.memory: list[str] = []

        def analyze(self, transcript: str, *, stream: bool = False, memory_context: str = "") -> Any:
            self.memory.append(memory_context)
            return super().analyze(transcript, stream=stream, memory_context=memory_context)

    server, base = _boot(tmp_path, monkeypatch, token=EARLIER_TOKEN)
    try:
        db = get_database()
        _configure(db)
        engine = RecordingIntel()
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
        monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda: db)
        monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(()))
        monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(()))
        _profile(db, "earlier-summary", claims=("language", _result_claim("meeting.deferred_analysis")))
        api = lambda method, path, body=None: _api(base, method, path, body, token=EARLIER_TOKEN)  # noqa: E731
        api("POST", "/api/desk/seed")
        api("PUT", "/api/setup/onboarding", {"disposition": "completed"})
        selected = api("POST", "/api/concierge/summary-selection", {
            "commandId": "earlier-selection", "expectedAssignmentRevision": 0,
            "profileId": "earlier-summary", "profileRevision": 1,
        })
        assert selected["status"] == "succeeded", selected
        project_id = api("POST", "/api/projects", {"name": "Payments cut-over"})["project"]["id"]

        days = {"wed": ("Wednesday planning", 14), "thu": ("Thursday sync", 15), "fri": ("Friday review", 16)}
        for key, (title, day) in days.items():
            started = datetime(2026, 10, day, 10, 0, 0)
            db.meetings.save_meeting(MeetingState(
                id=f"c2-{key}", title=title, started_at=started, ended_at=started + timedelta(minutes=30),
                capture_status="finalized", transcription_status="final",
                segments=[TranscriptSegment(f"{title}: the payments cut-over freeze window.", "Priya", 0.0, 2.0)],
                intel=None if key == "thu" else IntelSnapshot(
                    timestamp=1.0, topics=["Cut-over"], summary=f"{title} on the cut-over freeze window.",
                    action_items=[],
                ),
            ))
            db.projects.associate_meeting_project(
                meeting_id=f"c2-{key}", project_id=project_id, source="manual", confidence=1.0,
            )

        def summarise(meeting_id: str) -> dict[str, Any]:
            before = len(engine.memory)
            planned = api("GET", f"/api/meetings/{meeting_id}")["planned_route"]
            assert planned["status"] == "ready", planned
            queued = api("POST", f"/api/meetings/{meeting_id}/intelligence/run",
                         {"expected_selection_hash": planned["selection_hash"]})
            assert queued["state"] == "queued", queued
            for _ in range(100):
                if len(engine.memory) > before and db.intel.get_run_receipt(meeting_id):
                    break
                process_next_intel_job()
                time.sleep(0.05)
            assert len(engine.memory) == before + 1, engine.memory
            return api("GET", f"/api/meetings/{meeting_id}")["run_receipt"]

        thursday = summarise("c2-thu")
        block = engine.memory[-1]
        assert "meeting:c2-wed" in block, block
        assert "c2-fri" not in block and "Friday" not in block, block
        assert "2026-10-14 meeting:c2-wed" in block, block
        assert [item["ref"] for item in thursday.get("looked_at", [])] == ["meeting:c2-wed"], thursday
        assert thursday["looked_at"][0]["at"] == "2026-10-14", thursday

        friday = summarise("c2-fri")
        looked = {item["ref"]: item for item in friday.get("looked_at", [])}
        assert "meeting:c2-thu" in looked, friday
        assert looked["meeting:c2-thu"]["at"] == "2026-10-15"
        assert looked["meeting:c2-thu"]["title"] == "Thursday sync"
        _recorded_looked_at(friday)
    finally:
        _stop(server)


LOOKED_AT_FIXTURE = (
    Path(__file__).parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "meetings-hub" / "looked-at.json"
)


def _recorded_looked_at(receipt: dict[str, Any]) -> None:
    """The face test's recorded answer (meetings.app.test.tsx): Friday's run
    receipt as the hub served it. HOLDSPEAK_WIRE_WRITE=1 rewrites the file;
    otherwise the stored `looked_at` must equal the live one."""
    import os

    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        LOOKED_AT_FIXTURE.write_text(json.dumps({
            "_source": "Recorded from a real hub by tests/integration/test_desk_meetings.py::"
                       "test_a_summary_reads_only_earlier_dated_sources_and_its_receipt_lists_them "
                       "(GET /api/meetings/c2-fri run_receipt). HOLDSPEAK_WIRE_WRITE=1 rewrites this "
                       "file; never hand-edit a field a test reads.",
            "run_receipt": receipt,
        }, indent=2, sort_keys=True) + "\n")
    stored = json.loads(LOOKED_AT_FIXTURE.read_text())["run_receipt"]
    assert stored["looked_at"] == receipt["looked_at"], "re-record with HOLDSPEAK_WIRE_WRITE=1"
    assert set(stored) == set(receipt), "re-record with HOLDSPEAK_WIRE_WRITE=1"


# ── Capture C3: Import asks when it was ──────────────────────────────────────

WHEN_TOKEN = "desk-meetings-when"
THEO_TXT = Path(__file__).parents[1] / "fixtures" / "capture_one_on_one_theo.txt"


def test_an_import_with_a_stated_start_is_listed_on_that_day(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The face sends "When was this?" as ``started_at_ms``. The hub stores
    that start: the Thursday 1:1 (imported on a Saturday) lists under
    Thursday 15 October 10:00, not under the import moment."""
    thursday = datetime(2026, 10, 15, 10, 0, 0)
    server, base = _boot(tmp_path, monkeypatch, token=WHEN_TOKEN)
    try:
        api = lambda method, path, body=None: _api(base, method, path, body, token=WHEN_TOKEN)  # noqa: E731
        status, imported = _call(
            base, "POST", "/api/meetings/import", token=WHEN_TOKEN, ok=False,
            files={"file": ("one-on-one-theo.txt", THEO_TXT.read_bytes(), "text/plain")},
            data={"title": "1:1 with Theo", "started_at_ms": str(int(thursday.timestamp() * 1000))},
        )
        assert status == 202, imported
        meeting_id = str(imported["meeting_id"])
        assert _wait(lambda: bool(api("GET", f"/api/meetings/{meeting_id}").get("segments")), timeout=30), (
            "the import never produced its segments")
        detail = api("GET", f"/api/meetings/{meeting_id}")
        started = datetime.fromisoformat(str(detail["started_at"]).replace("Z", "+00:00"))
        assert started.astimezone().replace(tzinfo=None) == thursday, detail["started_at"]
        listed = [row for row in api("GET", "/api/meetings?limit=100")["meetings"] if row["id"] == meeting_id]
        assert listed, "the imported meeting is not in the list"
        row_start = datetime.fromisoformat(str(listed[0]["started_at"]).replace("Z", "+00:00"))
        assert row_start.astimezone().date() == thursday.date(), listed[0]
        assert row_start.astimezone().strftime("%A") == "Thursday"
    finally:
        _stop(server)


# ── Capture C6: Since last time ──────────────────────────────────────────────

SINCE_TOKEN = "desk-meetings-since"
SYNC_TXT = Path(__file__).parents[1] / "fixtures" / "capture_payments_platform_sync.txt"
REVIEW_TXT = Path(__file__).parents[1] / "fixtures" / "capture_architecture_review.txt"
SINCE_FIXTURE = (
    Path(__file__).parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "meetings-hub" / "since-last.json"
)
# The promises the LAN engine wrote for the sync and the review in the
# capture walk (docs/internal/betterment/capture/RECON.md §3).
SYNC_ACTIONS = [
    ("c6-sync-a1", "Write the two idempotent-retry options on one page", "Jun", "Thursday evening"),
    ("c6-sync-a2", "Profile the reconciliation job", "Theo", "Thursday"),
    ("c6-sync-a3", "Draft the rollback runbook for the cutover", "Mira", "Tuesday"),
]
REVIEW_ACTIONS = [
    ("c6-rev-a1", "Write the ADR for idempotent retries", "Jun", "Wednesday"),
    ("c6-rev-a2", "Update the reconciliation job to read the dedupe key", "Theo", None),
]


def test_since_last_time_names_the_last_meeting_of_the_same_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The capture week, imported with its dates: the Thursday sync, a 1:1
    with Theo later that Thursday, Friday's architecture review. Friday's
    aftercare names the sync (the same people), not the later 1:1; what
    closed, what is still open and what is new are each listed. The sync and
    the 1:1 have no last time."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot

    week = {
        "sync": (SYNC_TXT, "Payments platform sync", datetime(2026, 10, 15, 10, 0, 0)),
        "theo": (THEO_TXT, "1:1 with Theo", datetime(2026, 10, 15, 14, 0, 0)),
        "review": (REVIEW_TXT, "Architecture review: idempotent retries", datetime(2026, 10, 16, 11, 0, 0)),
    }
    server, base = _boot(tmp_path, monkeypatch, token=SINCE_TOKEN)
    try:
        api = lambda method, path, body=None: _api(base, method, path, body, token=SINCE_TOKEN)  # noqa: E731
        ids: dict[str, str] = {}
        for key, (path, title, started) in week.items():
            status, imported = _call(
                base, "POST", "/api/meetings/import", token=SINCE_TOKEN, ok=False,
                files={"file": (path.name, path.read_bytes(), "text/plain")},
                data={"title": title, "started_at_ms": str(int(started.timestamp() * 1000))},
            )
            assert status == 202, imported
            ids[key] = str(imported["meeting_id"])
            assert _wait(lambda: bool(api("GET", f"/api/meetings/{ids[key]}").get("segments")), timeout=30)

        # The promises each summary wrote (no engine in the rig).
        db = get_database()
        for key, actions in (("sync", SYNC_ACTIONS), ("review", REVIEW_ACTIONS)):
            state = db.meetings.get_meeting(ids[key])
            state.intel = IntelSnapshot(timestamp=1.0, summary="", action_items=[
                {"id": item_id, "task": task, "owner": owner, "due": due, "status": "pending",
                 "review_state": "pending", "source_timestamp": None,
                 "created_at": week[key][2].isoformat()}
                for item_id, task, owner, due in actions
            ])
            db.meetings.save_meeting(state)
        # Jun wrote the options page before the review.
        api("PATCH", "/api/all-action-items/c6-sync-a1", {"status": "done"})

        review = api("GET", f"/api/meetings/{ids['review']}/aftercare")
        since = review["since_last_meeting"]
        assert since is not None, review
        assert since["previous_meeting"]["id"] == ids["sync"], since
        assert since["previous_meeting"]["title"] == "Payments platform sync"
        assert since["previous_meeting"]["date"].startswith("2026-10-15"), since
        assert [a["task"] for a in since["closed_actions"]] == [SYNC_ACTIONS[0][1]]
        assert [a["task"] for a in since["still_open_actions"]] == [SYNC_ACTIONS[1][1], SYNC_ACTIONS[2][1]]
        assert [a["task"] for a in since["new_actions"]] == [task for _, task, _, _ in REVIEW_ACTIONS]

        for key in ("sync", "theo"):
            assert api("GET", f"/api/meetings/{ids[key]}/aftercare")["since_last_meeting"] is None, key
        _recorded_since(review)
    finally:
        _stop(server)


def _recorded_since(review: dict[str, Any]) -> None:
    """The face test's recorded answer (meetings.app.test.tsx): Friday's
    aftercare as the hub served it. HOLDSPEAK_WIRE_WRITE=1 rewrites the file;
    otherwise the stored diff must equal the live one (ids aside: an import
    makes a new meeting id each run)."""
    import os

    def shape(body: dict[str, Any]) -> Any:
        since = body["since_last_meeting"]
        return {
            "title": since["previous_meeting"]["title"],
            "date": since["previous_meeting"]["date"][:10],
            **{k: [a["task"] for a in since[k]] for k in ("closed_actions", "still_open_actions", "new_actions")},
        }

    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        SINCE_FIXTURE.write_text(json.dumps({
            "_source": "Recorded from a real hub by tests/integration/test_desk_meetings.py::"
                       "test_since_last_time_names_the_last_meeting_of_the_same_kind "
                       "(GET /api/meetings/<review>/aftercare). HOLDSPEAK_WIRE_WRITE=1 rewrites this "
                       "file; never hand-edit a field a test reads.",
            "aftercare": review,
        }, indent=2, sort_keys=True) + "\n")
    stored = json.loads(SINCE_FIXTURE.read_text())["aftercare"]
    assert shape(stored) == shape(review), "re-record with HOLDSPEAK_WIRE_WRITE=1"
    assert set(stored["since_last_meeting"]) == set(review["since_last_meeting"]), "re-record"


# ── Capture C7: a scheduled fire on the hub as composed ──────────────────────

FIRE_TOKEN = "desk-meetings-fire"


class _CaptureDouble:
    """The start boundary the real fire uses: the runtime's bound ``on_start``
    (``WebRuntimeCallbacks.on_start`` → ``web_runtime._start_meeting``), with
    the pending-title seam ``MeetingWebServer._conductor_start_meeting`` sets
    on its owner. It records the start, or raises what the real start raises."""

    def __init__(self, raises: BaseException | None = None) -> None:
        self.pending_title: str | None = None
        self.pending_calendar_event_id: str | None = None
        self.starts: list[tuple[Any, str | None]] = []
        self.raises = raises

    def start_meeting(self, principal: Any = None) -> dict[str, Any]:
        if self.raises is not None:
            raise self.raises
        self.starts.append((principal, self.pending_title))
        return {"id": "m-scheduled"}


def _fire_now(base: str, title: str) -> dict[str, Any]:
    """Arm a one-shot due now on the hub's OWN conductor (its composed
    voice floor and start seam) and run one tick."""
    from holdspeak import scheduled_recording_conductor as src
    from holdspeak.db import get_database

    conductor = src._conductor
    assert conductor is not None, "the hub did not start the scheduled-recording conductor"
    conductor._countdown_seconds = 0.0
    db = get_database()
    sched = db.scheduled_recordings.create(
        title=title, cron_expr="0 9 * * *", one_shot=True, duration_minutes=1,
        enabled=True, next_fire_at=time.time() - 1,
    )
    conductor._tick()
    # Wait for the fire itself, not its first write: the countdown thread
    # writes `recording`, then calls the start, then writes `refused` if the
    # start raised. A read between those writes is a half-done fire (the
    # 2026-10-29/30 FAST reds). The thread ends when the fire is decided.
    fire = [t for t in threading.enumerate() if t.name == f"sr-countdown-{sched.id}"]
    for thread in fire:
        thread.join(timeout=10)
        assert not thread.is_alive(), "the scheduled fire did not finish"
    assert db.scheduled_recordings.get(sched.id).state not in ("idle", "arming")
    rows = _api(base, "GET", "/api/scheduled-recordings", token=FIRE_TOKEN)["schedules"]
    return next(r for r in rows if r["id"] == sched.id)


def test_a_scheduled_fire_on_a_hub_with_no_voice_session_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RECON.md §6: the glass hub has no voice session, and the fire died on
    `None.active_owner` (web_server.py's floor lambda) with no receipt. A hub
    with no audio arbiter has no floor holder: the fire reaches the start."""
    double = _CaptureDouble()
    server, base = _boot(tmp_path, monkeypatch, token=FIRE_TOKEN, on_start=double.start_meeting)
    try:
        assert server.voice_session is None  # the rig's composition, as in the walk
        row = _fire_now(base, "Platform design follow-up")
        assert row["state"] == "recording", row
        assert row["last_outcome"] == "recording_started", row
        assert row["did_not_record"] is None, row
        assert len(double.starts) == 1 and double.starts[0][1] == "Platform design follow-up"
    finally:
        _stop(server)


@pytest.mark.parametrize("raised, words", [
    ("floor", "Another recording is running"),
    ("mic", "No microphone"),
])
def test_a_scheduled_fire_that_cannot_start_says_why_in_plain_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raised: str, words: str,
) -> None:
    """The real start's refusals (meeting_glue's held floor, the recorder with
    no input device) end the fire in `refused` with the plain words; the
    exception text is never in the row."""
    from holdspeak.meeting_recorder import MeetingRecorderError

    exc = (RuntimeError("Cannot start meeting: audio floor held by 'hotkey'") if raised == "floor"
           else MeetingRecorderError("Failed to start mic recording: Error querying device -1"))
    double = _CaptureDouble(raises=exc)
    server, base = _boot(tmp_path, monkeypatch, token=FIRE_TOKEN, on_start=double.start_meeting)
    try:
        row = _fire_now(base, "1:1 with Mira")
        assert row["state"] == "refused" and row["last_outcome"] == "start_failed", row
        assert row["did_not_record"]["reason"] == words, row
        assert str(exc) not in json.dumps(row)
    finally:
        _stop(server)
