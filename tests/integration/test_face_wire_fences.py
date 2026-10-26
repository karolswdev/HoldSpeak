"""The hub's own answers for face tests that typed their hub bodies by hand
(the test diet, 2026-10-11; lane A's list).

Each test boots the real hub (``MeetingWebServer`` through ``TestClient``) on
an isolated HOME and database, seeds it through the product, and fences the
answers the face tests read into ``web/src/test/wire/*.wire.json``
(``HOLDSPEAK_WIRE_WRITE=1`` rewrites them). The face tests check that every
field their typed bodies carry is a field the hub sends, at the same place
and of the same JSON type (``web/src/test/wireShape.ts``): no invented field
(the SCAR LAW).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402
from tests.integration import test_desk_agents_wire as wire  # noqa: E402

pytestmark = pytest.mark.timeout(240)

WIRE_DIR = REPO / "web" / "src" / "test" / "wire"
BY = "tests/integration/test_face_wire_fences.py"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database

    monkeypatch.setattr(wire, "WIRE_DIR", WIRE_DIR)
    yield seeds._boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any) -> Any:
    assert response.status_code in (200, 201), (response.request.url, response.status_code, response.text[:300])
    return response.json()


def _fence(name: str, payload: Any, tmp_path: Path, hub: Any) -> None:
    wire._fence(name, payload, tmp_path, str(hub.client.base_url), by=BY)


def test_rhythm_reads(hub: Any, tmp_path: Path) -> None:
    """The fresh Door (OneScreen) and a generated Brief (rhythm.app's Brief rows).
    The Rhythm's other reads are recorded by scripts/record_chair_rhythm_fixture.py."""
    from datetime import datetime, timedelta

    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    _fence("door.fresh", _ok(hub.client.get("/api/door")), tmp_path, hub)
    # A meeting inside the Brief's window, so its CHANGED section has a row.
    # Minutes from now, so the seed stays inside the Brief's window and this
    # week on any day (the fence compares row counts too).
    start = datetime.now() - timedelta(minutes=3)
    hub.db.meetings.save_meeting(MeetingState(
        id="m-standup", started_at=start, ended_at=start + timedelta(minutes=2), title="Standup",
        segments=[TranscriptSegment(text="We ship on Friday.", speaker="Me", start_time=1.0, end_time=3.0)]))
    # Calendar events later this week, so THIS WEEK has rows (the
    # calendar_events projection the ingest writes; tests/unit/test_desk_chair.py
    # seeds it the same way).
    import time as _time
    from datetime import timezone

    with hub.db._connection() as conn:
        for n, title in enumerate(("Sprint Planning", "Design review")):
            at = (datetime.now(timezone.utc) + timedelta(minutes=2 + n)).isoformat()
            conn.execute(
                "INSERT INTO calendar_events (id, uid, title, starts_at, ends_at, location, meeting_url, "
                "last_seen_at, subscription_revision, source_id, source_label) "
                "VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, 'rev1', 'src-work', 'WORK')",
                (f"ev-{n}", f"uid-ev-{n}", title, at, at, _time.time()),
            )
    _ok(hub.client.post("/api/brief/generate", json={}))
    _fence("brief-latest.generated", _ok(hub.client.get("/api/brief/latest")), tmp_path, hub)


def test_journal_reads(hub: Any, tmp_path: Path) -> None:
    """speak.app.test.tsx: the Journal envelope and a row, and the readiness overrides."""
    from holdspeak.plugins.dictation.journal import passthrough_run

    recorder = hub.server.dictation_journal
    # The live runtime gives the recorder the durable repository
    # (web_runtime._dictation_journal_repo); the bare test server gives none.
    recorder._repository = hub.db.dictation_journal
    from types import SimpleNamespace

    for source, text in (("dictation", "Cut the Q4 scope to the payments path"),
                         ("hotkey", "Draft the release note for the metrics change")):
        assert recorder.record(passthrough_run(text), source=source, transcript=text) is not None
    # A run a text correction fired on (the pipeline's `corrections_applied`),
    # so the row's list has a value.
    text = "Ship the Q4 platform in October"
    run = SimpleNamespace(**vars(passthrough_run(text)), corrections_applied=[7])
    assert recorder.record(run, source="dictation", transcript=text) is not None
    _fence("dictation-journal", _ok(hub.client.get("/api/dictation/journal?limit=50")), tmp_path, hub)
    # The Journal reads only the readiness answer's target overrides; the rest
    # of that answer reports this machine (agent hooks, block files).
    readiness = _ok(hub.client.get("/api/dictation/readiness"))
    _fence("dictation-readiness.target", {"target": {"overrides": readiness["target"]["overrides"]}}, tmp_path, hub)


# ── first run: the machine's facts pinned at their sources ──────────────

#: The speech backend detection's two sources (holdspeak/transcribe.py
#: `_is_darwin_arm64`, `_module_available`), pinned to an Apple-silicon Mac
#: with mlx-whisper: MLX plans 4 Whisper files, faster-whisper 6, none 2 and
#: a `speech.reason` (Astra r1 on #1107), so an unpinned recording differed by
#: machine.
_SPEECH_MODULES = {
    "mlx": {"mlx", "mlx_whisper"},
    "faster-whisper": {"faster_whisper"},
    "none": set(),
}


def _machine(monkeypatch: pytest.MonkeyPatch, backend: str) -> None:
    """Make the detection's two sources answer as a machine with ``backend``."""
    import holdspeak.transcribe as transcribe

    monkeypatch.setattr(transcribe, "_is_darwin_arm64", lambda: backend == "mlx")
    monkeypatch.setattr(transcribe, "_module_available", lambda module: module in _SPEECH_MODULES[backend])


def _pin_first_run_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    """The recorder's machine: mlx speech, llama-cpp-python 0.3.35, gh and
    acli on PATH, the Mac's Calendars granted with one calendar. Every pin is
    at the producer's boundary; the producers above it run for real."""
    import holdspeak.macos_calendar as macos_calendar
    import holdspeak.services.inference_setup_service as inference_setup
    import holdspeak.services.onboarding_service as onboarding

    _machine(monkeypatch, "mlx")
    monkeypatch.setattr(inference_setup, "_package_revision",
                        lambda dist, fallback: "0.3.35" if dist == "llama-cpp-python" else fallback)
    monkeypatch.setattr(inference_setup, "_import_llama_cpp", lambda: None)
    # EventKit's two reads (macos_calendar wraps EventKit; HOLDSPEAK_MACOS_CALENDAR=0 in the rig).
    monkeypatch.setattr(macos_calendar, "access_state", lambda: "full_access")
    monkeypatch.setattr(macos_calendar, "list_calendars", lambda: [
        {"id": "CAL-1", "title": "Work", "account": "karol@acme.com", "kind": "caldav"}])
    # PATH: gh and acli are installed (OnboardingService binds `which` at construction).
    real_init = onboarding.OnboardingService.__init__

    def init(self: Any, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("which", lambda name: f"/usr/local/bin/{name}" if name in ("gh", "acli") else None)
        # The network read of a pasted calendar link (CalendarSourceReader).
        kwargs.setdefault("calendar_reader", _FakeCalendarReader())
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(onboarding.OnboardingService, "__init__", init)


class _FakeCalendarReader:
    """The calendar link's one read: a feed with one event soon, or a redirect."""

    def read(self, url: str) -> bytes:
        from datetime import datetime, timedelta, timezone

        from holdspeak.calendar_ingest_conductor import CalendarSourceError

        if "moved" in url:
            raise CalendarSourceError("calendar_source_redirect", "https://new.example.com/a.ics")
        start = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y%m%dT%H%M%SZ")
        return (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//recorder//EN\r\nX-WR-CALNAME:Work (Outlook)\r\n"
            f"BEGIN:VEVENT\r\nUID:atlas-1\r\nDTSTAMP:{start}\r\nDTSTART:{start}\r\nDTEND:{start}\r\n"
            "SUMMARY:Atlas weekly\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
        ).encode()


_GH_HOSTS = """github.com:
    git_protocol: https
    users:
        karolswdev:
            oauth_token: gho_RECORDER_FAKE
    user: karolswdev
"""

_ACLI_PROFILES = """version: 1
current_profile: cloud-1:acct-1
profiles:
  - site: acme.atlassian.net
    cloud_id: cloud-1
    account_id: acct-1
    display_name: Karol
    email: karol@acme.com
    auth_type: oauth
"""


def _signed_in_gh(*args: Any, **kwargs: Any) -> Any:
    import subprocess

    cmd = args[0] if args else kwargs.get("args", [])
    out = "github.com\n  \u2713 Logged in to github.com account karolswdev (keyring)\n"
    return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=out, stderr="")


@pytest.fixture
def first_run_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database

    monkeypatch.setattr(wire, "WIRE_DIR", WIRE_DIR)
    _pin_first_run_machine(monkeypatch)
    hub = seeds._boot(tmp_path, monkeypatch, gh_runner=_signed_in_gh)
    (tmp_path / ".config" / "gh").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".config" / "gh" / "hosts.yml").write_text(_GH_HOSTS)
    (tmp_path / ".config" / "acli").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".config" / "acli" / "jira_config.yaml").write_text(_ACLI_PROFILES)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _local_ai(hub: Any) -> Any:
    return _ok(hub.client.get("/api/setup/local-ai"))


def test_first_run_reads(first_run_hub: Any, tmp_path: Path) -> None:
    """FirstRun / OneScreen: local AI, the calendar and connection candidates,
    settings, notes, and the LAN engine's three answers (a fake OpenAI server
    on the loopback, the FakeLLM the Room tests use)."""
    from tests.integration.test_desk_project_room import FakeLLM

    hub = first_run_hub
    _fence("setup-local-ai", _local_ai(hub), tmp_path, hub)
    _fence("onboarding-calendar", _ok(hub.client.get("/api/onboarding/calendar")), tmp_path, hub)
    _fence("onboarding-calendar.use",
           _ok(hub.client.post("/api/onboarding/calendar/use", json={"id": "eventkit:CAL-1"})), tmp_path, hub)
    _fence("onboarding-calendar.access",
           _ok(hub.client.post("/api/onboarding/calendar/macos/access", json={})), tmp_path, hub)
    _fence("onboarding-calendar.check", _ok(hub.client.post("/api/onboarding/calendar/check", json={
        "url": "https://outlook.office365.com/owa/calendar/a/calendar.ics"})), tmp_path, hub)
    _fence("onboarding-calendar.check-failed", _ok(hub.client.post("/api/onboarding/calendar/check", json={
        "url": "https://cal.example.com/moved.ics"})), tmp_path, hub)
    _fence("onboarding-connections", _ok(hub.client.get("/api/onboarding/connections")), tmp_path, hub)
    _fence("onboarding-connections.use", _ok(hub.client.post(
        "/api/onboarding/connections/use", json={"id": "github:github.com:karolswdev"})), tmp_path, hub)
    # First run reads the owner and calendar blocks of /api/settings; the rest
    # reports this machine's runtime (placement, counters).
    # One calendar source, so the settings and sources answers carry a row.
    _ok(hub.client.put("/api/settings", json={"calendar": {"sources": [
        {"id": "src_work", "label": "WORK", "url": "https://cal.example.com/a.ics", "enabled": True}]}}))
    put = _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol", "aliases": []}}))
    # The PUT answers the whole settings; first run reads none of it but owner.
    _fence("settings.put", {"success": put["success"], "settings": {"owner": put["settings"]["owner"]}}, tmp_path, hub)
    settings = _ok(hub.client.get("/api/settings"))
    _fence("settings.owner", {"owner": settings["owner"], "calendar": settings["calendar"]}, tmp_path, hub)
    _fence("calendar-sources", _ok(hub.client.get("/api/calendar/sources")), tmp_path, hub)
    note = _ok(hub.client.post("/api/notes", json={"title": "First words", "body_markdown": "Send the plan."}))
    _fence("notes-create", note, tmp_path, hub)

    llm = FakeLLM()
    try:
        found = _ok(hub.client.post("/api/setup/discover-models",
                                    json={"base_url": llm.endpoint, "check_tools": True}))
        _fence("discover-models", {**found, "detail": "Found 1 model."}, tmp_path, hub)
        profile_id = f"engine-127-0-0-1-{llm.port}"
        defined = _ok(hub.client.post("/api/inference/model-library/define-endpoint", json={
            "draft": {"request_id": "first-run-1", "profile_id": profile_id, "expected_profile_revision": 0,
                      "label": f"127.0.0.1:{llm.port}", "provider_family": "openai_compatible",
                      "model": found["models"][0], "endpoint": llm.endpoint, "requires_key": False},
            "secret": None}))
        _fence("define-endpoint", defined, tmp_path, hub)
        selected = _ok(hub.client.post("/api/concierge/summary-selection", json={
            "commandId": "first-run-summary-1", "expectedAssignmentRevision": 0,
            "profileId": defined["provider"]["profile_id"],
            "profileRevision": defined["provider"]["profile_revision"], "setDefault": True}))
        _fence("summary-selection", selected, tmp_path, hub)
    finally:
        llm.stop()


@pytest.mark.parametrize("backend", ["mlx", "faster-whisper", "none"])
def test_the_local_ai_answer_does_not_depend_on_the_machine(
    backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Astra r1 on #1107: whatever speech library this machine has, the
    recorder's pin makes the same answer, so the fence holds on any Mac and
    in CI. Without the pin, the three machines answer three shapes."""
    from holdspeak.db import reset_database

    monkeypatch.setattr(wire, "WIRE_DIR", WIRE_DIR)
    _pin_first_run_machine(monkeypatch)
    hub = seeds._boot(tmp_path, monkeypatch)
    try:
        _machine(monkeypatch, backend)
        unpinned = _local_ai(hub)
        expected_files = {"mlx": 4, "faster-whisper": 6, "none": 2}[backend]
        whisper = [f for f in unpinned["files"] if f["key"] == "whisper"]
        assert len(unpinned["files"]) == expected_files and ("reason" in unpinned["speech"]) == (backend == "none"), \
            (backend, len(unpinned["files"]), unpinned["speech"], len(whisper))
        _pin_first_run_machine(monkeypatch)
        _fence("setup-local-ai", _local_ai(hub), tmp_path, hub)
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


def test_parked_reads(hub: Any, tmp_path: Path) -> None:
    """parkedDrawer.test.tsx: the parked list and each kind's restore answer."""
    from test_philo15_desk_parked import _seed

    _seed(hub.db)
    _fence("desk-parked", _ok(hub.client.get("/api/desk/parked")), tmp_path, hub)
    _fence("restore.project", _ok(hub.client.post("/api/projects/p-old/restore", json={})), tmp_path, hub)
    _fence("restore.workbench-item",
           _ok(hub.client.post("/api/workbenches/wb-1/items/wbi-park/restore", json={})), tmp_path, hub)
    _fence("restore.meeting", _ok(hub.client.post("/api/meetings/m-park/restore", json={})), tmp_path, hub)


def test_start_here_note(hub: Any, tmp_path: Path) -> None:
    """materialDoors.test.tsx: the fresh desk's Start here note, as the hub serves it."""
    from holdspeak.db.seed import apply_seed

    apply_seed(hub.db)  # what setup_service does for a fresh desk
    note = _ok(hub.client.get("/api/notes/hs-seed-start-here"))
    _fence("note.start-here", note, tmp_path, hub)
    assert "(door:record-live)" in str(note)


def test_shade_finished_remote_receipt(hub: Any, tmp_path: Path) -> None:
    """bell.app.test.tsx: the shade's Finished rows read /api/desk/projections
    (desk/projections.ts refresh). One remote pipeline event (a sweep a LAN agent
    ran from 192.168.1.43) and one local one, seeded as
    tests/e2e/_parked/test_hs174_receipts_glass.py::_seed_pipeline_event seeds them."""
    import time as _time
    import uuid as _uuid

    with hub.db._connection() as conn:
        for n, (service, method, origin, caller, summary) in enumerate((
            ("HeartbeatService", "run_sweep", "remote", "192.168.1.43", '{"watches":4,"rooms":2,"held":false}'),
            ("StewardService", "project_run_steward", "local", "", "{}"),
        )):
            conn.execute(
                """INSERT INTO pipeline_events
                   (event_id, timestamp, service, method,
                    principal_kind, principal_identity, args_summary,
                    result_summary, error, error_code, duration_ms,
                    correlation_id, is_async, origin, caller, caller_identity)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f"ev-shade-{n}", _time.time() - n, service, method, "agent", "sweep-runner", "{}",
                 summary, None, None, 42.0, str(_uuid.uuid4()), 0, origin, caller,
                 "sweep-runner" if origin == "remote" else ""),
            )
    answer = _ok(hub.client.get("/api/desk/projections?offset=0&limit=50"))
    remote = [row for row in answer["projections"] if row.get("origin") == "remote"]
    assert remote and remote[0]["caller"] == "192.168.1.43", answer["projections"]
    _fence("desk-projections.remote-receipt", answer, tmp_path, hub)


def test_schedule_create_reads(hub: Any, tmp_path: Path) -> None:
    """chair.app.test.tsx (the capture bar's Schedule window): the create
    answer and the list after it.

    replaces: tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
    (the hub half: Cancel saved nothing; Create saved one row with its title)."""
    assert _ok(hub.client.get("/api/scheduled-recordings"))["schedules"] == []
    created = _ok(hub.client.post("/api/scheduled-recordings", json={
        "title": "Rail form recording", "cron_expr": "0 9 1 1 *", "tz": "UTC",
        "one_shot": True, "duration_minutes": 60, "enabled": True,
    }))
    assert created["schedule"]["title"] == "Rail form recording"
    _fence("scheduled-recordings.create", created, tmp_path, hub)
    listed = _ok(hub.client.get("/api/scheduled-recordings"))
    assert [row["title"] for row in listed["schedules"]] == ["Rail form recording"]
    _fence("scheduled-recordings.list", listed, tmp_path, hub)


def test_honest_faces_and_arrival_reads(hub: Any, tmp_path: Path) -> None:
    """The honest faces' seed (tests/unit/test_desk_needs_you.py::_seed_honest_faces):
    the Follow-through board (FollowThroughView.test.tsx), every decision
    (DecisionsView.test.tsx), the ⌘K search hit and its decision read
    (paletteMemory.test.tsx). The arrival's unfinished thoughts before and after
    one typed thought (chair.app.test.tsx, the THOUGHTS section).

    replaces: tests/e2e/test_honest_faces_glass.py::test_intelligence_lane_names_and_decision_rows (the hub's answers)
    replaces: tests/e2e/test_honest_faces_glass.py::test_a_decision_search_hit_opens_the_decision_and_adds_no_floor_icon (the hub's answers)
    replaces: tests/e2e/test_hs170_arrival_glass.py::TestArrivalGlass (the THOUGHTS section's hub answers)
    """
    import uuid

    seeds._seed_honest_faces(hub)
    _fence("follow-through-board.honest-faces", _ok(hub.client.get("/api/follow-through/board")), tmp_path, hub)
    _fence("decisions.honest-faces",
           _ok(hub.client.get("/api/decisions?scope=all&limit=100&offset=0")), tmp_path, hub)
    # ⌘K: the search hit, and the decision read its opener makes (paletteMemory.test.tsx).
    _fence("memory-search.honest-faces",
           _ok(hub.client.get("/api/memory/search", params={"query": "Freeze the old ledger"})), tmp_path, hub)
    lifecycle = hub.db.decisions.list(meeting_id="m-standup")[0]
    _fence("decision.honest-faces", _ok(hub.client.get(f"/api/decisions/{lifecycle.id}")), tmp_path, hub)

    from holdspeak.db.seed import apply_seed

    apply_seed(hub.db)  # a fresh desk's Inbox, where a new thought's note lands
    unfinished = "/api/thoughts?state=unfinished&limit=3"
    none = _ok(hub.client.get(unfinished))
    assert none["items"] == [], none
    _fence("thoughts-unfinished.none", none, tmp_path, hub)
    _ok(hub.client.post("/api/thoughts", json={
        "request_id": str(uuid.uuid4()),
        "raw_text": "Plan to migrate authentication.",
        "source": {"kind": "typed"},
        "initial_note": {"title": "Migrate the auth service",
                         "body_markdown": "Plan to migrate authentication.", "tags": []},
    }))
    one = _ok(hub.client.get(unfinished))
    assert [t["title"] for t in one["items"]] == ["Migrate the auth service"], one
    _fence("thoughts-unfinished.one", one, tmp_path, hub)


def test_new_decision_reads(hub: Any, tmp_path: Path) -> None:
    """newDecision.app.test.tsx (the owner, 2026-10-25): New Decision's window
    creates through the store's own POST (dataSlice createNow: the from-desk
    producer with the Project in front), then the Decisions window reads the
    record and its list."""
    project = _ok(hub.client.post("/api/projects", json={"name": "Payments ledger cutover"}))["project"]
    created = _ok(hub.client.post("/api/decision-records/from-desk", json={
        "status": "accepted", "context_markdown": "", "decision_markdown": "",
        "consequences_markdown": "", "alternatives": [], "decision_text": "",
        "title": "Keep the ledger on SQLite",
        "why": "One writer, one file. Postgres waits until we need a second host.",
        "project_id": project["id"], "project_name": project["name"],
    }))
    record = created["record"]
    assert record["decision_text"] == "Keep the ledger on SQLite", record
    _fence("decision-records.from-desk", created, tmp_path, hub)
    read = _ok(hub.client.get(f"/api/decision-records/{record['id']}"))
    assert "Why: One writer" in str(read.get("rationale")), read
    _fence("decision-record.new", read, tmp_path, hub)
    _fence("decision-records.list-new",
           _ok(hub.client.get("/api/decision-records?limit=100&offset=0")), tmp_path, hub)


def test_decisions_window_scope_reads(hub: Any, tmp_path: Path) -> None:
    """newDecision.app.test.tsx (the owner, 2026-10-25): the two doors that
    still opened the Decisions page in Today. (a) A meeting's decision with no
    record yet: its read, the empty records-from-it answer, and the one-row
    ledger read the Decisions window makes by its id. (b) WHY with two
    governing records: the records for that work item, and each record."""
    from datetime import datetime, timedelta

    from holdspeak.db.decisions import backfill_decisions
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.decision_record_service import DecisionRecordService

    db = hub.db
    start = (datetime.now() - timedelta(hours=2)).replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id="m-sync", started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger cutover sync",
        segments=[TranscriptSegment(text="We freeze the old ledger.", speaker="Me", start_time=1.0, end_time=3.0)]))
    db.plugins.record_artifact(
        artifact_id="m-sync-decisions", meeting_id="m-sync", artifact_type="decisions",
        title="Meeting decisions", plugin_id="scope-reads",
        structured_json={"decisions": [{"decision": "Freeze the old ledger on Nov 5",
                                        "rationale": "Dual-write is stable."}]},
    )
    with db._connection() as conn:
        backfill_decisions(conn)
    lifecycle = db.decisions.list(meeting_id="m-sync")[0]
    one = _ok(hub.client.get(f"/api/decisions/{lifecycle.id}"))
    assert one["decision"]["source_meeting_id"] == "m-sync", one
    _fence("decision.no-record", one, tmp_path, hub)
    none = _ok(hub.client.get(f"/api/decision-records/source/meeting/{lifecycle.id}"))
    assert none == [], none
    row = _ok(hub.client.get(f"/api/decisions?scope=all&decision_id={lifecycle.id}&limit=1"))
    assert [r["text"] for r in row["decisions"]] == ["Freeze the old ledger on Nov 5"], row
    assert not row["decisions"][0].get("record_id"), row
    _fence("decisions.no-record", row, tmp_path, hub)

    owner = Principal(PrincipalKind.OWNER, "karol")
    service = DecisionRecordService(db)
    ids = []
    for title, why in (("Keep the ledger on SQLite", "One writer, one file."),
                       ("Ship the cutover on Nov 5", "Dual-write is stable.")):
        created = _ok(hub.client.post("/api/decision-records/from-desk", json={
            "status": "accepted", "context_markdown": "", "decision_markdown": "",
            "consequences_markdown": "", "alternatives": [], "decision_text": "",
            "title": title, "why": why,
        }))
        ids.append(created["record"]["id"])
        service.link_work(owner, created["record"]["id"], "item", "w-2")
    governing = _ok(hub.client.get("/api/decision-records/work/item/w-2"))
    assert sorted(r["id"] for r in governing) == sorted(ids), governing
    assert all(r["lifecycle"] == "active" for r in governing), governing
    _fence("decision-records.work-two", governing, tmp_path, hub)
    for name, record_id in zip(("decision-record.governing-a", "decision-record.governing-b"), ids):
        _fence(name, _ok(hub.client.get(f"/api/decision-records/{record_id}")), tmp_path, hub)
