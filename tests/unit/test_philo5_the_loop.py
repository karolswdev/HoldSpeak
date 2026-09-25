"""PHILO-5-02: the loop shares the contract.

Every fence here runs against the REAL hub (``MeetingWebServer``) over an
isolated database, and reaches it by BOTH transports: HTTP routes and MCP over
``/api/mcp`` (the path the stdio proxy forwards to). What each fence proves,
and what turns it red:

* **One declaration, one instance** (:class:`TestOneInstance`) -- every loop
  operation is bound once, to the hub's live service; HTTP, MCP tools and MCP
  resources all reach it through ``invoke``. Red on base ``6e707ff3``: the
  recording ``invoke`` sees nothing for the loop (the transports called their
  services by hand). Deliberate mutation: bind a fresh instance in
  ``composition.install_from_web_context`` -> the identity assertion fails.
* **Gap A** -- an MCP brief generate runs on the hub's producer clock. Red on
  base: MCP built its own clockless ``MondayBriefService`` and dated the brief
  by the wall clock.
* **Gap B + F** -- an MCP summary run puts ``runtime_queue`` on the hub bus
  (the fence names ``runtime_queue``, not ``desk_changed``). Red on base: MCP
  built an unwired ``MeetingIntelService`` with no notify.
* **Gap C** -- the HTTP summary routes use the composed instance; the hub
  carries no summary factory. Red on base: ``_svc()`` returned a fresh
  ``factory()`` object per call.
* **Gap D** -- the pilot MCP resources read through the bound contract.
  Red on base: the recording sees no resource read.
* **Gap E** -- import: the HTTP multipart upload and the MCP intake reach the
  same ``meeting.import`` on the same instance; each keeps its own custody (the
  caller's file survives an MCP import). Deliberate mutations: bypass
  ``invoke`` in the intake (recording red); hand the caller's own path to the
  worker (the survival assertion red).
* **A4's KEPT** -- ``thought.save`` is the working-copy save, with its revision
  checks, workspace cursor and ``working_note.last_modified``, through both.
* **The Phase 4 invariants through MCP** -- decision rows lead by persisted
  ``created_at``; brief-scoped breakage ids across two MCP-made briefs with the
  old triage unchanged; the MCP shelf writes are the hub's shelf.
* **The decision admission (CHARACTERIZATION ONLY)** -- a decision written
  through HTTP and through MCP leaves the same zero: no kernel operation, no
  receipt. Inherited Article XI debt, unruled (``current-phase-status.md``
  "Discovered missing admissions"); parity, not exemption.
"""
from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak import operations
from holdspeak.runtime import composition

REPO = Path(__file__).resolve().parents[2]
TOKEN = "philo5-02-token"
FIXTURE_TXT = REPO / "tests" / "fixtures" / "philo3_architect_meeting.txt"
FIXTURE_WAV = REPO / "tests" / "fixtures" / "philo3_architect_meeting.wav"

LOOP_OPERATIONS = {
    "meeting.list": "meeting_service",
    "meeting.read": "meeting_service",
    "meeting.import": "meeting_service",
    "meeting.summary.run": "meeting_intel_service",
    "brief.generate": "monday_brief_service",
    "brief.latest": "monday_brief_service",
    "brief.shelf.write": "monday_brief_service",
    "brief.shelf.read": "monday_brief_service",
    "thought.create": "refinement_service",
    "thought.save": "refinement_service",
    "thought.read": "refinement_service",
    "thought.workbench.read": "refinement_service",
    "thought.list": "refinement_service",
}


class MovableClock:
    def __init__(self, start: datetime.datetime) -> None:
        self.now = start

    def __call__(self) -> datetime.datetime:
        return self.now

    def advance(self, **delta: int) -> None:
        self.now = self.now + datetime.timedelta(**delta)


class Hub:
    def __init__(self, server: Any, root: Any, client: Any, frames: list[tuple[str, Any]]) -> None:
        self.server, self.root, self.client, self.frames = server, root, client, frames

    @property
    def db(self) -> Any:
        from holdspeak.db import get_database

        return get_database()

    def mcp(self, name: str, arguments: dict[str, Any]) -> tuple[bool, Any]:
        resp = self.client.post("/api/mcp", json={
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        assert resp.status_code == 200, resp.text
        result = resp.json()["result"]
        return result["isError"], json.loads(result["content"][0]["text"])

    def resource(self, uri: str) -> Any:
        resp = self.client.post("/api/mcp", json={
            "jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": uri},
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "result" in body, body
        return json.loads(body["result"]["contents"][0]["text"])


def _boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, clock: Any = None) -> Hub:
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "hub.db")
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
        brief_clock=clock,
    )
    frames: list[tuple[str, Any]] = []
    # The hub's notify thunks resolve ``self.broadcast`` at call time.
    server.broadcast = lambda message_type, data: frames.append((message_type, data))
    root = composition.installed()
    assert root is not None and root.bare_root is False, "the hub installed no root"
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    hub = Hub(server, root, client, frames)
    assert Path(str(hub.db.db_path)).parent == tmp_path, "the hub is not on the isolated database"
    hub.db.directories.upsert(directory_id="hs-seed-inbox", name="Inbox")
    return hub


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.fixture
def recorded(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every name the hub's ONE registry is asked to invoke, in order."""
    registry = hub.root.operations
    seen: list[str] = []
    real_invoke = registry.invoke

    def recording_invoke(principal: Any, name: str, args: Any = None, **kwargs: Any) -> Any:
        seen.append(name)
        return real_invoke(principal, name, args, **kwargs)

    monkeypatch.setattr(registry, "invoke", recording_invoke)
    return seen


def _wait_imported(hub: Hub, meeting_id: str, timeout: float = 20.0) -> dict[str, Any]:
    deadline = time.time() + timeout
    last: Any = None
    while time.time() < deadline:
        is_error, last = hub.mcp("meeting.get", {"meeting_id": meeting_id})
        assert is_error is False, last
        status = last.get("intel_status")
        state = status.get("state") if isinstance(status, dict) else status
        if state not in {"importing", None}:
            return last
        time.sleep(0.05)
    raise AssertionError(f"import of {meeting_id} never finished; last={last and last.get('intel_status')}")


def _thought(hub: Hub, request_id: str, text: str = "raw thought") -> dict[str, Any]:
    made = hub.client.post("/api/thoughts", json={"request_id": request_id, "raw_text": text, "source": {"kind": "typed"}})
    assert made.status_code == 201, made.text
    return made.json()["thought"]


# ── one declaration, one instance ────────────────────────────────────────


class TestOneInstance:
    def test_every_loop_operation_is_bound_once_to_the_hubs_instance(self, hub: Hub) -> None:
        root, ctx = hub.root, hub.root.web_context
        assert ctx.operations is root.operations
        for name, field in LOOP_OPERATIONS.items():
            target = root.operations.target(name)
            assert target is getattr(root, field), name
            assert target is getattr(ctx, field), name
        # MCP dispatch and resources resolve the SAME registry, building nothing.
        fail = lambda: pytest.fail("built a fresh service in the hub")  # noqa: E731
        assert operations.for_runtime(fail, meeting_service=fail, meeting_intel_service=fail,
                                      monday_brief_service=fail, refinement_service=fail) is root.operations

    def test_gap_c_the_hub_has_one_summary_instance_and_no_factory(self, hub: Hub) -> None:
        from holdspeak.web.routes.meetings.intel import _svc

        ctx = hub.root.web_context
        assert ctx.meeting_intel_service_factory is None
        assert _svc(ctx) is hub.root.meeting_intel_service
        assert _svc(ctx) is _svc(ctx), "the HTTP summary routes build a new instance per call"
        assert hub.root.operations.target("meeting.summary.run") is _svc(ctx)

    def test_gap_a_the_hubs_brief_service_carries_the_hub_clock(self, tmp_path, monkeypatch) -> None:
        from holdspeak.db import reset_database

        clock = MovableClock(datetime.datetime(2026, 10, 13, 9, 0))
        try:
            hub = _boot(tmp_path, monkeypatch, clock=clock)
            assert hub.root.monday_brief_service._clock is clock
        finally:
            reset_database()
            composition.install(composition.bare(label="pytest"))

    def test_http_mcp_and_resources_all_go_through_invoke(self, hub: Hub, recorded: list[str]) -> None:
        # meetings
        assert hub.client.get("/api/meetings").status_code == 200
        is_error, _ = hub.mcp("meeting.list", {})
        assert is_error is False
        from holdspeak.meeting_session import MeetingState, TranscriptSegment

        hub.db.meetings.save_meeting(MeetingState(
            id="m-identity", started_at=datetime.datetime(2026, 9, 1, 9), title="Identity",
            segments=[TranscriptSegment(text="hello", speaker="Me", start_time=0.0, end_time=1.0)],
        ))
        assert hub.client.get("/api/meetings/m-identity").status_code == 200
        is_error, _ = hub.mcp("meeting.get", {"meeting_id": "m-identity"})
        assert is_error is False
        hub.resource("holdspeak://meetings/m-identity")
        assert recorded == ["meeting.list", "meeting.list", "meeting.read", "meeting.read", "meeting.read"]

        # the brief
        recorded.clear()
        assert hub.client.post("/api/brief/generate").status_code == 200
        assert hub.client.get("/api/brief/latest").status_code == 200
        assert hub.client.get("/api/brief/shelf").status_code == 200
        hub.mcp("monday_brief.generate", {})
        hub.mcp("monday_brief.get", {})
        hub.mcp("monday_brief.get", {"generate": True})
        hub.mcp("monday_brief.shelf_read", {})
        hub.resource("holdspeak://briefs/latest")
        assert recorded == ["brief.generate", "brief.latest", "brief.shelf.read",
                            "brief.generate", "brief.latest", "brief.generate",
                            "brief.shelf.read", "brief.latest"]

        # the Thought
        recorded.clear()
        thought = _thought(hub, "identity-http")
        tid = thought["id"]
        saved = hub.client.patch(f"/api/thoughts/{tid}/working", json={
            "expected_aggregate_revision": thought["aggregate_revision"],
            "expected_working_revision": thought["working_revision"], "title": "HTTP save"})
        assert saved.status_code == 200, saved.text
        assert hub.client.get(f"/api/thoughts/{tid}").status_code == 200
        assert hub.client.get(f"/api/thoughts/{tid}/workbench").status_code == 200
        assert hub.client.get("/api/thoughts?state=unfinished").status_code == 200
        is_error, made = hub.mcp("thought.create", {"request_id": "identity-mcp", "raw_text": "via mcp"})
        assert is_error is False, made
        mt = made["thought"]
        is_error, out = hub.mcp("thought.update_working", {
            "thought_id": mt["id"], "expected_aggregate_revision": mt["aggregate_revision"],
            "expected_working_revision": mt["working_revision"], "title": "MCP save"})
        assert is_error is False, out
        hub.resource(f"holdspeak://thoughts/{tid}")
        hub.resource(f"holdspeak://thoughts/{tid}/workbench")
        hub.resource("holdspeak://thoughts/unfinished")
        assert recorded == ["thought.create", "thought.save", "thought.read", "thought.workbench.read",
                            "thought.list", "thought.create", "thought.save", "thought.read",
                            "thought.workbench.read", "thought.list"]


def test_durable_loop_state_survives_a_new_hub_over_the_same_database(tmp_path, monkeypatch) -> None:
    """Across a restart the objects differ; the meeting, brief and Thought do not."""
    from holdspeak.db import reset_database

    try:
        first = _boot(tmp_path, monkeypatch)
        is_error, brief = first.mcp("monday_brief.generate", {})
        assert is_error is False, brief
        is_error, made = first.mcp("thought.create", {"request_id": "restart-1", "raw_text": "before restart"})
        assert is_error is False, made
        second = _boot(tmp_path, monkeypatch)
        assert second.root.operations is not first.root.operations
        assert second.root.monday_brief_service is not first.root.monday_brief_service
        is_error, again = second.mcp("monday_brief.get", {})
        assert is_error is False and again["id"] == brief["id"]
        assert second.client.get("/api/brief/latest").json()["id"] == brief["id"]
        read = second.resource(f"holdspeak://thoughts/{made['thought']['id']}")
        assert read["thought"]["working_note"]["body_markdown"] == "before restart"
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── gap A: the brief's producer clock through MCP ────────────────────────


def test_gap_a_an_mcp_brief_generate_uses_the_hubs_producer_clock(tmp_path, monkeypatch) -> None:
    from holdspeak.db import reset_database

    clock = MovableClock(datetime.datetime(2026, 10, 13, 9, 0))  # a Tuesday, never "today"
    try:
        hub = _boot(tmp_path, monkeypatch, clock=clock)
        is_error, day_one = hub.mcp("monday_brief.generate", {})
        assert is_error is False, day_one
        assert day_one["period_end"].startswith("2026-10-13"), day_one["period_end"]
        # Same producer day as HTTP: one brief, one id.
        http = hub.client.post("/api/brief/generate").json()
        assert http["id"] == day_one["id"]

        clock.advance(days=1)
        is_error, day_two = hub.mcp("monday_brief.generate", {})
        assert is_error is False, day_two
        assert day_two["period_end"].startswith("2026-10-14"), day_two["period_end"]
        assert day_two["id"] != day_one["id"]
        # monday_brief.get keeps its default read and its generate=true.
        is_error, latest = hub.mcp("monday_brief.get", {})
        assert is_error is False and latest["id"] == day_two["id"]
        is_error, same = hub.mcp("monday_brief.get", {"generate": True})
        assert is_error is False and same["id"] == day_two["id"]
        # And HTTP's own read agrees on the dated brief.
        assert hub.client.get("/api/brief/latest").json()["id"] == day_two["id"]
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── gaps B + F: the summary's runtime_queue through MCP ──────────────────


def _summary_ready_meeting(hub: Hub, monkeypatch: pytest.MonkeyPatch, meeting_id: str) -> str:
    """A meeting with a transcript and an assigned summary route; its selection hash."""
    from tests.unit.test_meeting_deferred_admission import _Route, _assign_deferred_queue_routes
    from tests.unit.test_philo3_summary_queue import _meeting

    _assign_deferred_queue_routes(hub.db)
    monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript", lambda **kwargs: _Route(()))
    _meeting(hub.db, meeting_id)
    is_error, detail = hub.mcp("meeting.get", {"meeting_id": meeting_id})
    assert is_error is False, detail
    selection_hash = detail["planned_route"]["selection_hash"]
    assert selection_hash, detail["planned_route"]
    return selection_hash


def test_gap_b_an_mcp_summary_run_fires_runtime_queue(hub: Hub, monkeypatch) -> None:
    selection_hash = _summary_ready_meeting(hub, monkeypatch, "m-gap-b")
    hub.frames.clear()
    is_error, queued = hub.mcp("meeting.run_intelligence", {"meeting_id": "m-gap-b", "expected_selection_hash": selection_hash})
    assert is_error is False, queued
    assert queued["state"] == "queued"
    kinds = [kind for kind, _ in hub.frames]
    # Gap F: the summary's event is runtime_queue -- NOT desk_changed.
    assert "runtime_queue" in kinds, kinds
    # Completion is read back through meeting.read (the same meeting detail).
    is_error, detail = hub.mcp("meeting.get", {"meeting_id": "m-gap-b"})
    assert is_error is False, detail
    status = detail["intel_status"]
    assert (status.get("state") if isinstance(status, dict) else status) == "queued", status


def test_gap_b_http_and_mcp_summary_runs_reach_the_one_instance(hub: Hub, recorded: list[str], monkeypatch) -> None:
    selection_hash = _summary_ready_meeting(hub, monkeypatch, "m-gap-c")
    run = hub.client.post("/api/meetings/m-gap-c/intelligence/run", json={"expected_selection_hash": selection_hash})
    assert run.status_code == 200, run.text
    assert "runtime_queue" in [kind for kind, _ in hub.frames]
    # A repeat over each transport has the same outcome (a fresh queued job).
    again = hub.client.post("/api/meetings/m-gap-c/intelligence/run", json={"expected_selection_hash": selection_hash})
    is_error, repeat = hub.mcp("meeting.run_intelligence", {"meeting_id": "m-gap-c", "expected_selection_hash": selection_hash})
    assert again.status_code == 200 and is_error is False, (again.text, repeat)
    assert again.json()["state"] == repeat["state"] == "queued"
    assert set(again.json()) == set(repeat)
    # A stale hash is refused by name through both, with the same code.
    stale = hub.client.post("/api/meetings/m-gap-c/intelligence/run", json={"expected_selection_hash": "sha256:stale"})
    is_error, refused = hub.mcp("meeting.run_intelligence", {"meeting_id": "m-gap-c", "expected_selection_hash": "sha256:stale"})
    assert stale.status_code == 409 and is_error is True
    assert stale.json()["code"] == refused["code"]
    assert recorded[1:] == ["meeting.summary.run"] * 5


# ── gap E: import through both transports ────────────────────────────────


def test_gap_e_http_and_mcp_imports_reach_one_operation_and_equal_meetings(hub: Hub, recorded: list[str], tmp_path) -> None:
    caller_file = tmp_path / "architect meeting.txt"
    caller_file.write_bytes(FIXTURE_TXT.read_bytes())

    upload = hub.client.post(
        "/api/meetings/import",
        files={"file": ("architect meeting.txt", FIXTURE_TXT.read_bytes(), "text/plain")},
        data={"title": "Architect sync"},
    )
    assert upload.status_code == 202, upload.text
    http_id = upload.json()["meeting_id"]
    is_error, intake = hub.mcp("meeting.import", {"path": str(caller_file), "title": "Architect sync",
                                                  "occurred_at": "2026-09-23T10:00:00"})
    assert is_error is False, intake
    assert set(intake) == {"meeting_id", "transcription_status"}
    assert intake["transcription_status"] == "importing"
    assert recorded[:1] == ["meeting.import"] and recorded.count("meeting.import") == 2

    via_http = _wait_imported(hub, http_id)
    via_mcp = _wait_imported(hub, intake["meeting_id"])
    assert [s["text"] for s in via_mcp["segments"]] == [s["text"] for s in via_http["segments"]]
    assert via_mcp["segments"], "the transcript produced no segments"
    assert via_mcp["title"] == via_http["title"] == "Architect sync"
    assert via_mcp["started_at"].startswith("2026-09-23T10:00:00")
    # Custody: the hub imported its OWN copy; the caller's file is untouched.
    assert caller_file.read_bytes() == FIXTURE_TXT.read_bytes()


def test_gap_e_an_mcp_audio_import_transcribes_with_the_shared_transcriber(hub: Hub, monkeypatch, tmp_path) -> None:
    from holdspeak.web.routes import meeting_import as import_route

    class StubTranscriber:
        def transcribe(self, audio: Any, **_admission: Any) -> str:
            return "stub words"

    monkeypatch.setattr(import_route, "_transcriber_factory", lambda cfg: StubTranscriber())
    caller_file = tmp_path / "architect.wav"
    caller_file.write_bytes(FIXTURE_WAV.read_bytes())
    is_error, intake = hub.mcp("meeting.import", {"path": str(caller_file)})
    assert is_error is False, intake
    done = _wait_imported(hub, intake["meeting_id"], timeout=60.0)
    assert done["segments"] and all(s["text"] == "stub words" for s in done["segments"])
    assert done["title"] == "architect"
    assert caller_file.exists() and caller_file.stat().st_size == FIXTURE_WAV.stat().st_size


@pytest.mark.parametrize(("make_path", "code"), [
    (lambda tmp: "relative/meeting.txt", "path_not_absolute"),
    (lambda tmp: str(tmp / "missing.txt"), "path_not_readable"),
    (lambda tmp: str(tmp), "path_not_readable"),
    (lambda tmp: _write(tmp / "slides.pdf", b"%PDF fake"), "unsupported_type"),
    (lambda tmp: _write(tmp / "empty.txt", b""), "file_empty"),
], ids=["relative", "missing", "directory", "unsupported", "empty"])
def test_gap_e_the_mcp_intake_refuses_by_name_and_makes_no_meeting(hub: Hub, tmp_path, make_path, code) -> None:
    is_error, refused = hub.mcp("meeting.import", {"path": make_path(tmp_path)})
    assert is_error is True, refused
    assert refused["code"] == code, refused
    is_error, listing = hub.mcp("meeting.list", {})
    assert is_error is False and listing["meetings"] == []


def _write(path: Path, data: bytes) -> str:
    path.write_bytes(data)
    return str(path)


# ── A4's KEPT: the working-copy save through both transports ─────────────


def test_a4_kept_is_the_working_copy_save_with_revisions_cursor_and_last_modified(hub: Hub) -> None:
    thought = _thought(hub, "kept-1", "first body")
    tid = thought["id"]
    before = thought["working_note"]["last_modified"]
    cursor = hub.client.get(f"/api/thoughts/{tid}/workbench").json()["workspace_cursor"]
    time.sleep(1.1)  # last_modified has second precision on some writers

    # HTTP save with the cursor: the working copy moves, the Thought stays open.
    saved = hub.client.patch(f"/api/thoughts/{tid}/working", json={
        "expected_aggregate_revision": thought["aggregate_revision"],
        "expected_working_revision": thought["working_revision"],
        "body_markdown": "kept over HTTP", "workspace_cursor": cursor})
    assert saved.status_code == 200, saved.text
    after_http = saved.json()["thought"]
    assert after_http["working_note"]["body_markdown"] == "kept over HTTP"
    assert after_http["working_revision"] == thought["working_revision"] + 1
    assert after_http["working_note"]["last_modified"] != before
    assert after_http["state"] == thought["state"], "a save must not complete the Thought"
    assert saved.json()["workbench"]["workspace_cursor"]

    # MCP save of the SAME Thought on the next revision.
    time.sleep(1.1)
    is_error, out = hub.mcp("thought.update_working", {
        "thought_id": tid, "expected_aggregate_revision": after_http["aggregate_revision"],
        "expected_working_revision": after_http["working_revision"], "body_markdown": "kept over MCP"})
    assert is_error is False, out
    assert out["thought"]["working_note"]["body_markdown"] == "kept over MCP"
    assert out["thought"]["working_note"]["last_modified"] != after_http["working_note"]["last_modified"]
    assert out["thought"]["state"] == thought["state"]

    # The revision check refuses a stale save the same way on both transports.
    stale = {"expected_aggregate_revision": thought["aggregate_revision"],
             "expected_working_revision": thought["working_revision"], "body_markdown": "stale"}
    http_stale = hub.client.patch(f"/api/thoughts/{tid}/working", json=stale)
    is_error, mcp_stale = hub.mcp("thought.update_working", {"thought_id": tid, **stale})
    assert http_stale.status_code == 409 and is_error is True
    assert http_stale.json()["error"] == mcp_stale["code"]
    # A stale workspace cursor is a workspace_cursor_conflict with the fresh workbench.
    current = out["thought"]
    is_error, cursor_conflict = hub.mcp("thought.update_working", {
        "thought_id": tid, "expected_aggregate_revision": current["aggregate_revision"],
        "expected_working_revision": current["working_revision"], "body_markdown": "x",
        "workspace_cursor": cursor})
    assert is_error is True and cursor_conflict["code"] == "workspace_cursor_conflict"
    assert cursor_conflict["workbench"]["workspace_cursor"]["aggregate_revision"] == current["aggregate_revision"]
    # The durable body is the last KEPT one.
    assert hub.client.get(f"/api/thoughts/{tid}").json()["thought"]["working_note"]["body_markdown"] == "kept over MCP"


# ── the Phase 4 invariants, through MCP ──────────────────────────────────


def test_phase4_decision_rows_lead_by_persisted_created_at_via_mcp(hub: Hub) -> None:
    ids = []
    for title in ("First decision", "Second decision", "Third decision", "Fourth decision"):
        is_error, made = hub.mcp("desk.create", {"kind": "decisions", "data": {"title": title}})
        assert is_error is False, made
        ids.append(made["id"])
        time.sleep(1.05)  # distinct persisted created_at
    is_error, brief = hub.mcp("monday_brief.generate", {})
    assert is_error is False, brief
    rows = brief["sections"]["decisions"]
    created = [row["created_at"] for row in rows]
    assert created == sorted(created, reverse=True), created
    assert rows[0]["text"].endswith("Fourth decision")
    # Survives the reload, through both transports.
    is_error, reloaded = hub.mcp("monday_brief.get", {})
    assert [r["id"] for r in reloaded["sections"]["decisions"]] == [r["id"] for r in rows]
    http = hub.client.get("/api/brief/latest").json()
    assert [r["id"] for r in http["sections"]["decisions"]] == [r["id"] for r in rows]


def test_phase4_breakage_ids_are_brief_scoped_across_two_mcp_briefs(tmp_path, monkeypatch) -> None:
    import holdspeak.services.observer as observer_module
    from types import SimpleNamespace

    from holdspeak.db import reset_database

    day_one_at = datetime.datetime(2026, 9, 23, 18, 30)  # a Wednesday evening
    failed_at = datetime.datetime(2026, 9, 23, 18, 0)
    clock = MovableClock(day_one_at)
    try:
        hub = _boot(tmp_path, monkeypatch, clock=clock)
        # The REAL producer, now through MCP: an observed shelf write on an
        # unknown item fails and the hub's observer records it.
        monkeypatch.setattr(observer_module, "time", SimpleNamespace(time=lambda: failed_at.timestamp()))
        is_error, refused = hub.mcp("monday_brief.shelf", {"item_id": "brief-item-missing", "state": "acknowledged"})
        assert is_error is True and "Unknown brief item" in refused["error"]
        with hub.db._connection() as conn:
            events = conn.execute(
                "SELECT event_id, service, method FROM pipeline_events WHERE error IS NOT NULL"
            ).fetchall()
        assert [(e["service"], e["method"]) for e in events] == [("MondayBriefService", "shelve")]
        source_ref = f"pipeline-event:{events[0]['event_id']}"

        is_error, day_one = hub.mcp("monday_brief.generate", {})
        assert is_error is False, day_one
        first = [i for i in day_one["sections"]["broke"] if i["source_ref"] == source_ref]
        assert len(first) == 1, day_one["sections"]["broke"]
        is_error, acked = hub.mcp("monday_brief.shelf", {"item_id": first[0]["id"], "state": "acknowledged"})
        assert is_error is False and acked == {"item_id": first[0]["id"], "state": "acknowledged"}
        is_error, again = hub.mcp("monday_brief.generate", {})
        assert again["id"] == day_one["id"]

        clock.advance(days=1)
        is_error, day_two = hub.mcp("monday_brief.generate", {})
        assert is_error is False, day_two
        assert day_two["id"] != day_one["id"]
        second = [i for i in day_two["sections"]["broke"] if i["source_ref"] == source_ref]
        assert len(second) == 1 and second[0]["id"] != first[0]["id"]
        assert day_one["id"] in first[0]["id"] and day_two["id"] in second[0]["id"]
        brief_service = hub.root.monday_brief_service
        assert brief_service.shelf(None, day_one["id"]) == {first[0]["id"]: "acknowledged"}
        is_error, latest_shelf = hub.mcp("monday_brief.shelf_read", {})
        assert is_error is False and latest_shelf == {}
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


def test_phase4_mcp_shelf_writes_are_the_hubs_shelf(hub: Hub) -> None:
    """The handled line reads the hub's shelf; MCP Ack/Defer write that shelf."""
    for title in ("One", "Two"):
        hub.mcp("desk.create", {"kind": "decisions", "data": {"title": title}})
    is_error, brief = hub.mcp("monday_brief.generate", {})
    assert is_error is False, brief
    items = [row["id"] for row in brief["sections"]["decisions"]]
    assert len(items) == 2
    assert hub.mcp("monday_brief.shelf", {"item_id": items[0], "state": "acknowledged"})[0] is False
    assert hub.mcp("monday_brief.shelf", {"item_id": items[1], "state": "deferred"})[0] is False
    expected = {items[0]: "acknowledged", items[1]: "deferred"}
    assert hub.client.get("/api/brief/shelf").json() == expected
    assert hub.client.get("/api/brief/latest").json()["shelf"] == expected
    assert hub.mcp("monday_brief.shelf_read", {}) == (False, expected)
    # null returns an item to untouched, as the face's toggle does.
    assert hub.mcp("monday_brief.shelf", {"item_id": items[1], "state": None}) == (False, {"item_id": items[1], "state": None})
    assert hub.client.get("/api/brief/shelf").json() == {items[0]: "acknowledged"}
    # Refusals: an unknown state and an unknown item, both by the brief service
    # (PHILO-7-01 shelf-enum alignment: the MCP schema no longer pre-empts it).
    is_error, bad_state = hub.mcp("monday_brief.shelf", {"item_id": items[0], "state": "filed"})
    assert is_error is True and bad_state["error"] == "Unknown shelf state: filed"
    is_error, bad_item = hub.mcp("monday_brief.shelf", {"item_id": "nope", "state": "deferred"})
    assert is_error is True and "Unknown brief item" in bad_item["error"]
    assert hub.client.post("/api/brief/items/nope/shelf", json={"state": "deferred"}).status_code == 404


# ── the decision admission: the same documented absence ──────────────────


def _kernel_counts(db: Any) -> tuple[int, int, int]:
    with db._connection() as conn:
        return tuple(  # type: ignore[return-value]
            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("kernel_operations", "kernel_receipts", "kernel_journal")
        )


def test_decision_writes_leave_the_same_documented_absence_on_both_transports(hub: Hub) -> None:
    """CHARACTERIZATION ONLY -- not an exemption, not a certification.

    It pins what IS: ``decision.create``/``decision.update`` leave no kernel
    operation and no receipt through EITHER transport, the same zero on both.
    That is INHERITED DEBT under Article XI (``current-phase-status.md``
    "Discovered missing admissions"): whether a desk decision write "acts under
    Article V" (filing) is UNRULED, and the debt is assigned to the owner's
    ruling (``pm/roadmap/holdspeak/BACKLOG.md``, PHILO-5-02 follow-ups). Equal
    absence proves parity between the transports, not that the absence is
    lawful. When the debt is paid, this test goes red on BOTH transports at
    once and is replaced by an admission fence.
    """
    start = _kernel_counts(hub.db)
    made = hub.client.post("/api/decisions", json={"title": "Over HTTP"})
    assert made.status_code == 201
    assert hub.client.put(f"/api/decisions/{made.json()['decision']['id']}", json={"status": "accepted"}).status_code == 200
    after_http = _kernel_counts(hub.db)
    is_error, mcp_made = hub.mcp("desk.create", {"kind": "decisions", "data": {"title": "Over MCP"}})
    assert is_error is False
    is_error, _ = hub.mcp("desk.update", {"kind": "decisions", "id": mcp_made["id"], "data": {"status": "accepted"}})
    assert is_error is False
    after_mcp = _kernel_counts(hub.db)
    assert after_http == start, "HTTP decision writes began admitting; pay the Article XI debt record and MCP together"
    assert after_mcp == after_http, "MCP decision writes began admitting; pay the Article XI debt record and HTTP together"


# ── compatibility of the new tools' surface ──────────────────────────────


def test_new_tools_are_classified_and_outside_the_chat_palette() -> None:
    from holdspeak.mcp.tools import TOOLS
    from holdspeak.services.thread_tools import CHAT_PALETTE, tool_class

    names = {t["name"] for t in TOOLS}
    assert {"meeting.import", "monday_brief.shelf", "monday_brief.shelf_read"} <= names
    assert tool_class("meeting.import") == "effect_proposal"
    assert tool_class("monday_brief.shelf") == "effect_proposal"
    assert tool_class("monday_brief.shelf_read") == "evidence_read"
    # As monday_brief.generate: classified, not offered to a chat turn.
    assert not ({"meeting.import", "monday_brief.shelf", "monday_brief.shelf_read", "monday_brief.generate"} & CHAT_PALETTE)
    assert "monday_brief.get" in CHAT_PALETTE


def test_palette_refusal_through_dispatch_for_the_new_tools() -> None:
    from holdspeak.mcp.server import handle_message_for_principal
    from holdspeak.principals import Principal, PrincipalKind

    owner = Principal(PrincipalKind.OWNER, "owner")
    for name, arguments in (("meeting.import", {"path": "/tmp/x.txt"}),
                            ("monday_brief.shelf", {"item_id": "i", "state": "deferred"}),
                            ("monday_brief.shelf_read", {})):
        response = handle_message_for_principal({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }, owner, palette=frozenset({"monday_brief.get"}))
        assert response["error"]["data"] == {"code": "MCP-005", "tool": name}


def test_the_intake_holds_custody_and_passes_exactly_the_held_inputs(tmp_path) -> None:
    from holdspeak.db import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.meeting_service import MeetingService

    # r2: meeting.import is owner_only, so these checks run as the owner (a
    # non-owner is refused before them: test_philo5_the_loop_r2.py).
    owner = Principal(PrincipalKind.OWNER, "owner-session")
    registry = operations.bind_available({"meeting_service": MeetingService(Database(tmp_path / "h.db"))})
    with pytest.raises(RuntimeError, match="must hold exactly"):
        registry.invoke(owner, "meeting.import", {"filename": "a.txt"})
    with pytest.raises(operations.OperationRefused) as exc:
        registry.invoke(owner, "meeting.import", {"filename": "a.txt", "tmp_path": "/etc/passwd"},
                        held={"tmp_path": Path("x"), "config": None, "transcriber_factory": None})
    assert exc.value.code == "invalid_arguments"
    assert list(operations.MEETING_IMPORT.held) == ["tmp_path", "config", "transcriber_factory"]
