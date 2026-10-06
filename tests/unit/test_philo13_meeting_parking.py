"""PHILO-13-02 H-A1: meeting parking preserves the retained row and work."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.cadence.collector import LoopCollector
from holdspeak.db.calendar_events import CalendarEvent
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
from holdspeak.mcp import tools as mcp_tools
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.people_service import PeopleService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.projection_service import ProjectionService
from holdspeak.services.proposal_bridge_service import ProposalBridgeService
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.recall_service import RecallService
from holdspeak.services.room_people_service import _read_room_commitments
from holdspeak.services.watch_sources import MeetingWatchSource
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meeting_import import build_meeting_import_router
from holdspeak.web.routes.meetings.crud import build_crud_router
from holdspeak.web.routes.projections import build_projections_router
from holdspeak.web.routes.proposals import _status, build_proposal_router


OWNER = Principal(PrincipalKind.OWNER, "philo13-test-owner")


def _meeting(meeting_id: str = "meeting-a1") -> MeetingState:
    return MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 10, 1, 10, 0, 0),
        ended_at=datetime(2026, 10, 1, 10, 1, 0),
        title="A1 retained meeting",
        tags=["phase-13"],
        segments=[
            TranscriptSegment(
                text="The retained transcript must survive parking.",
                speaker="Me",
                start_time=0.0,
                end_time=3.0,
            ),
            TranscriptSegment(
                text="Restore must return the same meeting.",
                speaker="Remote",
                start_time=4.0,
                end_time=8.0,
            ),
        ],
        intel=IntelSnapshot(
            timestamp=8.0,
            topics=["retention"],
            action_items=[{"id": "a1-action", "task": "Verify restore", "owner": "Me"}],
            summary="The meeting carries retained work.",
        ),
    )


def _client(db: Database, service: MeetingService) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, meeting_service=service)
    app.include_router(build_meeting_import_router(ctx))
    app.include_router(build_crud_router(ctx))
    return TestClient(app)


def _proposal_client(db: Database) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {})
    ctx.proposal_bridge_service = ProposalBridgeService(db)
    app.include_router(build_proposal_router(ctx))
    return TestClient(app)


class _RecordingBoundBinder:
    """A real queue binder that records the producer's claimed Meeting id."""

    def __init__(self, db: Database, *, park_in_prepare: bool = False) -> None:
        self.db = db
        self.park_in_prepare = park_in_prepare
        self.prepared: list[str] = []
        self.bound: list[tuple[str, dict[str, str]]] = []
        self.discarded: list[str] = []

    def prepare(self, job, command_ids) -> None:
        self.prepared.append(str(job.meeting_id))
        if self.park_in_prepare:
            assert self.db.meetings.delete_meeting(str(job.meeting_id)) is True

    def discard(self, job_id: str) -> None:
        self.discarded.append(str(job_id))

    def __call__(self, _conn, job, command_ids):
        self.bound.append((str(job.meeting_id), dict(command_ids)))
        return {
            "parent_operation_id": "parent:recording-fence",
            "bundle_id": "bundle:recording-fence",
            "bundle_sha256": "sha256:recording-fence",
        }


def _decision_commitment_chain(db: Database, meeting_id: str) -> tuple[str, str, str]:
    """Mint a decisions artifact, accepted decision, promoted record and commitment."""
    db.plugins.record_artifact(
        artifact_id=f"decisions-{meeting_id}",
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Decision extraction",
        structured_json={
            "decisions": [{
                "decision": "Parked meeting dependency must disappear",
                "rationale": "A parked source is not active work.",
                "source_timestamp": 1.0,
            }],
        },
        confidence=1.0,
        status="accepted",
        plugin_id="decision_capture",
        plugin_version="test",
    )
    decision = db.decisions.list(meeting_id=meeting_id)[0]
    db.decisions.accept(decision.id, actor=OWNER.identity)
    record = DecisionRecordService(db).create_from_meeting(OWNER, decision.id)
    db.decisions.promote(decision.id, "note", actor=OWNER.identity)
    commitment = FollowThroughService(db).commit_decision(
        OWNER, decision.id, owner="Me", due_at="2099-01-01"
    )
    return decision.id, str(record["id"]), str(commitment["id"])


def _related_rows(db: Database, meeting_id: str) -> dict[str, list[tuple]]:
    with db._connection() as conn:
        return {
            "segments": [
                tuple(row)
                for row in conn.execute(
                    "SELECT text, speaker, start_time, end_time FROM segments "
                    "WHERE meeting_id = ? ORDER BY start_time",
                    (meeting_id,),
                )
            ],
            "intel": [
                tuple(row)
                for row in conn.execute(
                    "SELECT timestamp, summary FROM intel_snapshots "
                    "WHERE meeting_id = ? ORDER BY timestamp",
                    (meeting_id,),
                )
            ],
            "actions": [
                tuple(row)
                for row in conn.execute(
                    "SELECT id, task, owner FROM action_items "
                    "WHERE meeting_id = ? ORDER BY id",
                    (meeting_id,),
                )
            ],
            "artifacts": [
                tuple(row)
                for row in conn.execute(
                    "SELECT id, title, body_markdown FROM artifacts "
                    "WHERE meeting_id = ? ORDER BY id",
                    (meeting_id,),
                )
            ],
            "project_links": [
                tuple(row)
                for row in conn.execute(
                    "SELECT meeting_id, project_id, source, confidence "
                    "FROM meeting_projects WHERE meeting_id = ? ORDER BY project_id",
                    (meeting_id,),
                )
            ],
        }


def test_repository_parks_and_restores_without_deleting_retained_work(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking.db")
    state = _meeting()
    db.meetings.save_meeting(state)
    db.plugins.record_artifact(
        artifact_id="a1-artifact",
        meeting_id=state.id,
        artifact_type="handoff",
        title="Retained handoff",
        body_markdown="The body remains while parked.",
    )
    db.projects.create_project(project_id="a1-project", name="A1 project")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="a1-project", source="test", confidence=0.9
    )
    before = _related_rows(db, state.id)
    assert len(before["segments"]) == 2
    assert len(before["intel"]) == 1
    assert len(before["actions"]) == 1
    assert len(before["artifacts"]) == 1
    assert len(before["project_links"]) == 1

    assert db.meetings.delete_meeting(state.id) is True
    with db._connection() as conn:
        retained_row = conn.execute(
            "SELECT parked FROM meetings WHERE id = ?", (state.id,)
        ).fetchone()
    assert retained_row is not None
    assert retained_row[0] == 1
    assert db.meetings.get_meeting(state.id) is None
    assert db.meetings.get_meeting(state.id, include_parked=True).id == state.id
    assert _related_rows(db, state.id) == before
    assert db.meetings.list_meetings() == []
    assert [item.id for item in db.meetings.list_meetings(parked=True)] == [state.id]

    db.close()
    reopened = Database(tmp_path / "meeting-parking.db")
    assert reopened.meetings.get_meeting(state.id) is None
    assert reopened.meetings.get_meeting(state.id, include_parked=True).parked is True
    assert _related_rows(reopened, state.id) == before

    assert reopened.meetings.restore_meeting(state.id) is True
    assert reopened.meetings.get_meeting(state.id).to_dict()["id"] == state.id
    assert _related_rows(reopened, state.id) == before
    with reopened._connection() as conn:
        assert conn.execute("SELECT parked FROM meetings WHERE id = ?", (state.id,)).fetchone()[0] == 0


def test_repository_park_and_restore_are_idempotent_and_unknown_stays_missing(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-idempotent.db")
    db.meetings.save_meeting(_meeting("idempotent"))
    assert db.meetings.delete_meeting("idempotent") is True
    assert db.meetings.delete_meeting("idempotent") is True
    assert db.meetings.restore_meeting("idempotent") is True
    assert db.meetings.restore_meeting("idempotent") is True
    assert db.meetings.delete_meeting("unknown") is False
    assert db.meetings.restore_meeting("unknown") is False


def test_save_does_not_accidentally_unpark_a_retained_meeting(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-save.db")
    db.meetings.save_meeting(_meeting("save-retained"))
    assert db.meetings.delete_meeting("save-retained") is True
    db.meetings.save_meeting(MeetingState(id="save-retained", started_at=datetime.now()))
    assert db.meetings.get_meeting("save-retained") is None
    assert db.meetings.get_meeting("save-retained", include_parked=True).parked is True


def test_service_parked_search_reads_only_the_retained_meeting(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-search.db")
    service = MeetingService(db)
    db.meetings.save_meeting(_meeting("search-retained"))
    service.delete_meeting(OWNER, "search-retained")

    assert service.list_meetings(OWNER, query="retained", parked=False)["meetings"] == []
    parked = service.list_meetings(OWNER, query="retained", parked=True)
    assert [row["id"] for row in parked["meetings"]] == ["search-retained"]


def test_parked_meeting_proposal_refusal_tells_owner_to_restore(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-proposal.db")
    db.meetings.save_meeting(_meeting("proposal-retained"))
    proposal = db.proposals.create_proposal(
        meeting_id="proposal-retained",
        project_id=None,
        kind="decision",
        text="Keep the retained record",
        source_plugin="test",
    )
    assert proposal is not None
    db.meetings.delete_meeting("proposal-retained")

    result = ProposalBridgeService(db).confirm_proposal(OWNER, proposal.id)
    assert result["code"] == "meeting_parked"
    assert "restore" in result["error"].lower()
    assert _status(result) == 409

    response = _proposal_client(db).post(f"/api/proposals/{proposal.id}/confirm", json={})
    assert response.status_code == 409
    assert response.json()["success"] is False
    assert response.json()["code"] == "meeting_parked"
    assert "restore" in response.json()["error"].lower()


def test_mcp_delete_verbs_return_parked_receipts_and_retain_rows(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "meeting-parking-mcp.db")
    db.meetings.save_meeting(_meeting("mcp-meeting"))
    workbench = db.workbenches.upsert(workbench_id="mcp-workbench", name="MCP parking")
    item = WorkbenchService(db).add_item(OWNER, workbench.id, title="Retained item")

    # Dispatch through the same operation composition used by MCP, with this
    # isolated producer database as the root.  No fabricated parked field is
    # supplied to either operation.
    monkeypatch.setattr(composition, "_installed", composition.bare(db=db, label="a1-mcp"))
    meeting_receipt = mcp_tools.dispatch(
        "meeting.delete", {"meeting_id": "mcp-meeting"}, OWNER
    )
    item_receipt = mcp_tools.dispatch(
        "workbench.delete_item",
        {"workbench_id": workbench.id, "item_id": item["id"]},
        OWNER,
    )

    assert meeting_receipt == {"parked": True, "id": "mcp-meeting"}
    assert item_receipt == {"parked": True, "id": item["id"]}
    assert db.meetings.get_meeting("mcp-meeting") is None
    assert db.meetings.get_meeting("mcp-meeting", include_parked=True).parked is True
    assert db.workbench_items.get(item["id"]) is None
    assert db.workbench_items.get(item["id"], include_parked=True).parked is True


def test_real_import_route_parks_reads_retained_detail_and_restores(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-route.db")
    service = MeetingService(db)
    client = _client(db, service)

    response = client.post(
        "/api/meetings/import",
        files={"file": ("a1.txt", b"Me: first imported line\nRemote: second imported line\n", "text/plain")},
        data={"title": "Imported A1"},
    )
    assert response.status_code == 202, response.text
    meeting_id = response.json()["meeting_id"]

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        imported = db.meetings.get_meeting(meeting_id, include_parked=True)
        if imported is not None and imported.intel_status != "importing":
            break
        time.sleep(0.02)
    imported = db.meetings.get_meeting(meeting_id, include_parked=True)
    assert imported is not None
    assert len(imported.segments) == 2
    before = _related_rows(db, meeting_id)

    parked = client.delete(f"/api/meetings/{meeting_id}")
    assert parked.status_code == 200
    assert parked.json() == {"parked": meeting_id}
    assert client.get(f"/api/meetings/{meeting_id}").status_code == 404
    assert client.get("/api/meetings").json()["meetings"] == []
    parked_list = client.get("/api/meetings?parked=true")
    assert parked_list.status_code == 200
    assert [row["id"] for row in parked_list.json()["meetings"]] == [meeting_id]
    retained = client.get(f"/api/meetings/{meeting_id}?include_parked=true")
    assert retained.status_code == 200
    assert retained.json()["parked"] is True
    assert [segment["text"] for segment in retained.json()["segments"]] == [
        "first imported line",
        "second imported line",
    ]
    assert _related_rows(db, meeting_id) == before

    restored = client.post(f"/api/meetings/{meeting_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["meeting"]["id"] == meeting_id
    assert restored.json()["meeting"]["parked"] is False
    assert client.get(f"/api/meetings/{meeting_id}").status_code == 200
    assert client.get("/api/meetings?parked=true").json()["meetings"] == []
    assert _related_rows(db, meeting_id) == before


def test_schema_reconciles_parked_columns_additively(tmp_path: Path) -> None:
    path = tmp_path / "old-shape.db"
    db = Database(path)
    with db._connection() as conn:
        conn.execute("ALTER TABLE meetings RENAME TO meetings_old")
        conn.execute(
            "CREATE TABLE meetings (id TEXT PRIMARY KEY, started_at TEXT NOT NULL, "
            "ended_at TEXT, title TEXT)"
        )
        conn.execute(
            "INSERT INTO meetings(id, started_at, ended_at, title) "
            "SELECT id, started_at, ended_at, title FROM meetings_old"
        )
        conn.execute("DROP TABLE meetings_old")
        conn.commit()
    db.close()
    reopened = Database(path)
    with reopened._connection() as conn:
        meeting_columns = {row[1] for row in conn.execute("PRAGMA table_info(meetings)")}
        workbench_columns = {row[1] for row in conn.execute("PRAGMA table_info(workbench_items)")}
    assert "parked" in meeting_columns
    assert "parked" in workbench_columns


@pytest.mark.parametrize(
    "read_family",
    ["brief", "calendar", "recall", "proposal", "intel_claim"],
)
def test_parked_meeting_is_absent_from_its_real_read_family(
    tmp_path: Path, read_family: str,
) -> None:
    db = Database(tmp_path / f"meeting-parking-{read_family}.db")
    state = _meeting(f"read-family-{read_family}")
    if read_family in {"brief", "calendar"}:
        state.calendar_event_id = f"calendar-{read_family}"
    db.meetings.save_meeting(state)

    if read_family in {"brief", "calendar"}:
        from holdspeak.services.monday_brief_service import MondayBriefService

        brief = MondayBriefService(db)
        window_start = "2026-10-01T00:00:00"
        window_end = "2026-10-02T00:00:00"
        read = (
            (lambda: brief._collect_meetings(window_start, window_end))
            if read_family == "brief"
            else (lambda: brief._recorded_calendar_event_ids(window_start, window_end))
        )
        expected_after_park = [] if read_family == "brief" else set()
        expected_after_restore = (
            {f"calendar-{read_family}"} if read_family == "calendar" else None
        )
    elif read_family == "recall":
        read = lambda: db.memory.search("retained transcript", kinds=["meeting"]).hits
        expected_after_park = []
        expected_after_restore = f"meeting:{state.id}"
    elif read_family == "proposal":
        proposal = db.proposals.create_proposal(
            meeting_id=state.id,
            project_id=None,
            kind="action",
            text="Keep the producer fence",
            source_plugin="test",
        )
        assert proposal is not None
        read = lambda: db.proposals.list_proposals(meeting_id=state.id)
        expected_after_park = []
        expected_after_restore = proposal.id
    else:
        job_id = db.intel.enqueue_intel_job(
            state.id,
            transcript_hash=state.transcript_hash(),
            reason="producer fence",
        )
        assert job_id
        binder = _RecordingBoundBinder(db)
        read = lambda: db.intel.claim_next_intel_job_bound(binder)
        expected_after_park = None

    assert db.meetings.delete_meeting(state.id) is True
    parked_value = read()
    assert parked_value == expected_after_park

    assert db.meetings.restore_meeting(state.id) is True
    restored_value = read()
    if read_family == "brief":
        assert restored_value
    elif read_family == "recall":
        assert [hit.source_ref for hit in restored_value] == [expected_after_restore]
    elif read_family == "proposal":
        assert [row.id for row in restored_value] == [expected_after_restore]
    elif read_family == "intel_claim":
        assert restored_value is not None and restored_value.meeting_id == state.id
        assert binder.bound and binder.bound[-1][0] == state.id
    else:
        assert restored_value == expected_after_restore


def test_projection_route_hides_meeting_actuator_job_and_conflict_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-projections.db")
    state = _meeting("projection-fences")
    db.meetings.save_meeting(state)
    db.actuators.record_proposal(
        meeting_id=state.id,
        window_id="projection-window",
        plugin_id="projection-test",
        plugin_version="1",
        idempotency_key="projection-fence-actuator",
        target="webhook",
        action="post",
        preview="projection fence",
    )
    db.plugins.record_artifact(
        artifact_id="projection-fence-artifact",
        meeting_id=state.id,
        artifact_type="handoff",
        title="Projection fence artifact",
        body_markdown="Hidden with its parked Meeting",
    )
    db.intel.enqueue_intel_job(
        state.id,
        transcript_hash=state.transcript_hash(),
        reason="projection fence",
        legacy_displaced_work=True,
    )
    conflict_id = db.meetings.record_sync_conflict(
        state.id,
        local_value=state.to_dict(),
        incoming_value={**state.to_dict(), "title": "incoming"},
    )
    assert conflict_id

    app = FastAPI()
    app.include_router(build_projections_router(WebContext(
        get_state=lambda: {},
        projection_service=ProjectionService(db),
    )))
    client = TestClient(app)

    before_response = client.get("/api/desk/projections", params={"limit": 200}).json()
    before = before_response["projections"]
    meeting_ref = f"meeting:{state.id}"
    related_rows = [
        row for row in before
        if row["subject_ref"] == meeting_ref or row["correlation_id"] == meeting_ref
    ]
    assert {row["source_kind"] for row in related_rows} >= {
        "actuator_proposal", "artifact", "intel_job", "meeting_sync_conflict"
    }

    db.meetings.delete_meeting(state.id)
    parked_response = client.get("/api/desk/projections", params={"limit": 200}).json()
    parked = parked_response["projections"]
    assert all(
        row["subject_ref"] != meeting_ref and row["correlation_id"] != meeting_ref
        for row in parked
    )
    assert parked_response["page"]["total"] == before_response["page"]["total"] - len(related_rows)

    db.meetings.restore_meeting(state.id)
    restored_response = client.get("/api/desk/projections", params={"limit": 200}).json()
    restored = restored_response["projections"]
    restored_related = [
        row for row in restored
        if row["subject_ref"] == meeting_ref or row["correlation_id"] == meeting_ref
    ]
    assert {row["source_kind"] for row in restored_related} >= {
        "actuator_proposal", "artifact", "intel_job", "meeting_sync_conflict"
    }
    assert restored_response["page"]["total"] == before_response["page"]["total"]


def test_sync_conflict_tombstone_parks_and_restores_retained_children(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-conflict.db")
    state = _meeting("conflict-tombstone")
    db.meetings.save_meeting(state)
    db.plugins.record_artifact(
        artifact_id="conflict-artifact",
        meeting_id=state.id,
        artifact_type="handoff",
        title="Conflict artifact",
        body_markdown="Retained while parked",
    )
    before = _related_rows(db, state.id)
    conflict_id = db.meetings.record_sync_conflict(
        state.id,
        local_value=state.to_dict(),
        incoming_value={"id": state.id, "deleted": True},
    )

    assert db.meetings.resolve_sync_conflict(
        state.id, conflict_id, resolution="use_incoming"
    ) == "deleted"
    assert db.meetings.get_meeting(state.id) is None
    retained = db.meetings.get_meeting(state.id, include_parked=True)
    assert retained is not None and retained.parked is True
    assert _related_rows(db, state.id) == before
    assert db.meetings.list_sync_conflicts(state.id) == []

    assert db.meetings.restore_meeting(state.id) is True
    assert db.meetings.get_meeting(state.id) is not None
    assert _related_rows(db, state.id) == before


def test_parked_meeting_actions_and_speakers_disappear_from_all_owner_reads(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-owner-reads.db")
    state = _meeting("owner-read-fences")
    state.segments[0].speaker_id = "speaker-fence"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO speakers (id, name, embedding) VALUES (?, ?, ?)",
            ("speaker-fence", "Fence speaker", b"speaker-embedding"),
        )
        conn.commit()
    db.meetings.save_meeting(state)
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, status) "
            "VALUES (?, NULL, ?, ?, 'pending')",
            ("standalone-owner-read", "Standalone action", "Me"),
        )
        conn.commit()
    db.projects.create_project(project_id="owner-read-project", name="Owner read project")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="owner-read-project", source="test", confidence=1.0
    )

    assert {item.id for item in db.meetings.list_action_items()} == {
        "standalone-owner-read", "a1-action"
    }
    project_service = ProjectService(db)
    assert [item["id"] for item in project_service.list_action_items(OWNER, "owner-read-project")] == [
        "a1-action"
    ]

    before_segments = db.meetings.get_speaker_segments("speaker-fence")
    assert len(before_segments) == 1 and len(before_segments[0]["segments"]) == 1
    assert db.meetings.get_speaker_stats("speaker-fence")["total_segments"] == 1

    people_store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    people_store.initialize()
    people = PeopleService(people_store)
    relationship = people.create_relationship(OWNER, {"display_name": "Owner read person"})
    people.link_calendar_series(
        OWNER, relationship["id"], "uid-owner-read", "source-owner-read", "Owner read"
    )
    db.calendar_events.replace_projection(
        "owner-read-revision",
        [CalendarEvent(
            id="event-owner-read", uid="uid-owner-read", title="Owner read",
            starts_at="2026-10-01T10:00:00", ends_at="2026-10-01T11:00:00",
            location=None, meeting_url=None, last_seen_at=1.0,
            subscription_revision="owner-read-revision", source_id="source-owner-read",
        )],
        seen_at=1.0,
        source_id="source-owner-read",
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE meetings SET calendar_event_id=? WHERE id=?",
            ("event-owner-read", state.id),
        )
        conn.commit()
    assert people.one_on_one_brief(OWNER, relationship["id"], db=db)["linked_meetings"]

    db.meetings.delete_meeting(state.id)
    after_park = {
        "global_actions": [item.id for item in db.meetings.list_action_items()],
        "project_actions": [
            item["id"] for item in project_service.list_action_items(OWNER, "owner-read-project")
        ],
        "speaker_meetings": [
            group["meeting_id"] for group in db.meetings.get_speaker_segments("speaker-fence")
        ],
        "speaker_total_segments": db.meetings.get_speaker_stats("speaker-fence")["total_segments"],
        "people_meetings": [
            row["meeting_id"]
            for row in people.one_on_one_brief(OWNER, relationship["id"], db=db)["linked_meetings"]
        ],
    }
    assert after_park == {
        "global_actions": ["standalone-owner-read"],
        "project_actions": [],
        "speaker_meetings": [],
        "speaker_total_segments": 0,
        "people_meetings": [],
    }

    db.meetings.restore_meeting(state.id)
    assert {item.id for item in db.meetings.list_action_items()} == {
        "standalone-owner-read", "a1-action"
    }
    assert [item["id"] for item in project_service.list_action_items(OWNER, "owner-read-project")] == [
        "a1-action"
    ]
    assert db.meetings.get_speaker_segments("speaker-fence")
    assert db.meetings.get_speaker_stats("speaker-fence")["total_segments"] == 1
    assert people.one_on_one_brief(OWNER, relationship["id"], db=db)["linked_meetings"]


def test_bound_intel_claim_initial_fence_reads_real_parked_meeting(tmp_path: Path) -> None:
    db = Database(tmp_path / "bound-intel-initial.db")
    state = _meeting("bound-intel-initial")
    db.meetings.save_meeting(state)
    job_id = db.intel.enqueue_intel_job(
        state.id, transcript_hash=state.transcript_hash(), reason="bound fence"
    )
    assert db.meetings.delete_meeting(state.id) is True

    binder = _RecordingBoundBinder(db)
    assert db.intel.claim_next_intel_job_bound(binder) is None
    assert binder.bound == []
    with db._connection() as conn:
        row = conn.execute(
            "SELECT status FROM intel_jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
    assert row["status"] == "queued"

    assert db.meetings.restore_meeting(state.id) is True
    claimed = db.intel.claim_next_intel_job_bound(binder)
    assert claimed is not None
    assert binder.bound and binder.bound[-1][0] == state.id


def test_bound_intel_claim_recheck_fence_rejects_meeting_parked_during_prepare(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "bound-intel-recheck.db")
    state = _meeting("bound-intel-recheck")
    db.meetings.save_meeting(state)
    db.intel.enqueue_intel_job(
        state.id, transcript_hash=state.transcript_hash(), reason="bound recheck fence"
    )

    binder = _RecordingBoundBinder(db, park_in_prepare=True)
    assert db.intel.claim_next_intel_job_bound(binder) is None
    assert binder.prepared == [state.id]
    assert binder.bound == []
    # The bound path may replace the legacy queue leaf before prepare freezes
    # it; the binder must discard that exact prepared leaf after the recheck.
    assert len(binder.discarded) == 1
    with db._connection() as conn:
        row = conn.execute(
            "SELECT status FROM intel_jobs WHERE job_id = ?", (binder.discarded[0],)
        ).fetchone()
    assert row["status"] == "queued"


def test_follow_through_action_read_hides_parked_meeting_and_restores_it(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "follow-through-parked.db")
    state = _meeting("follow-through-parked")
    db.meetings.save_meeting(state)
    service = FollowThroughService(db)

    def card_ids() -> set[str]:
        board = service.board(OWNER)
        return {card.id for lane in (board.now, board.waiting, board.unassigned, board.overdue) for card in lane}

    assert "a1-action" in card_ids()
    assert db.meetings.delete_meeting(state.id) is True
    assert "a1-action" not in card_ids()
    assert db.meetings.restore_meeting(state.id) is True
    assert "a1-action" in card_ids()


def test_follow_through_decision_commitment_hides_parked_source_and_restores_it(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "follow-through-decision-parked.db")
    state = _meeting("follow-through-decision-parked")
    db.meetings.save_meeting(state)
    decision_id, _, _ = _decision_commitment_chain(db, state.id)
    with db._connection() as conn:
        action_item_id = str(conn.execute(
            "SELECT action_item_id FROM decision_commitments WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()[0])
    # The real collector produces the meeting-decision and source-meeting
    # action cadence cards. The board must hide both loops and the open
    # commitment when the source meeting is parked, without a refresh.
    loops = LoopCollector(db).collect()
    decision_loop = next(
        loop for loop in loops
        if loop.source_type == "meeting_decision" and loop.source_id == decision_id
    )
    decision_loop_id = str(decision_loop.id)
    with db._connection() as conn:
        action_rows = conn.execute(
            "SELECT id FROM action_items WHERE meeting_id = ?", (state.id,)
        ).fetchall()
        action_item_ids = {str(row["id"]) for row in action_rows}
        action_loop_rows = conn.execute(
            """SELECT c.id, c.source_id
               FROM cadence_loops c
               JOIN action_items a ON a.id = c.source_id
               WHERE c.source_type = 'meeting_action' AND a.meeting_id = ?""",
            (state.id,),
        ).fetchall()
    action_loop_ids = {str(row["id"]) for row in action_loop_rows}
    assert action_loop_ids
    assert action_item_id in action_item_ids
    assert {str(row["source_id"]) for row in action_loop_rows} <= action_item_ids
    service = FollowThroughService(db)

    def decision_cards() -> list[object]:
        board = service.board(OWNER)
        return [
            card
            for lane in (board.now, board.waiting, board.unassigned, board.overdue)
            for card in lane
            if card.decision_id == decision_id
            or card.id in action_item_ids | action_loop_ids | {decision_loop_id}
        ]

    before = decision_cards()
    before_ids = {card.id for card in before}
    assert action_item_ids <= before_ids
    assert decision_loop_id in before_ids
    assert db.meetings.delete_meeting(state.id) is True
    parked_ids = {card.id for card in decision_cards()}
    assert parked_ids.isdisjoint(action_item_ids | action_loop_ids | {decision_loop_id})
    assert db.meetings.restore_meeting(state.id) is True
    restored_ids = {card.id for card in decision_cards()}
    assert action_item_ids | {decision_loop_id} <= restored_ids
    with db._connection() as conn:
        restored_loop_ids = {
            str(row["id"])
            for row in conn.execute(
                "SELECT id FROM cadence_loops WHERE id IN ({})".format(
                    ",".join("?" for _ in action_loop_ids)
                ),
                tuple(action_loop_ids),
            ).fetchall()
        }
    assert restored_loop_ids == action_loop_ids


def test_project_stats_hide_parked_meeting_actions_and_artifacts(tmp_path: Path) -> None:
    db = Database(tmp_path / "project-stats-parked.db")
    state = _meeting("project-stats-parked")
    db.meetings.save_meeting(state)
    db.projects.create_project(project_id="project-stats", name="Project stats")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="project-stats", source="test", confidence=1.0
    )
    db.plugins.record_artifact(
        artifact_id="project-stats-artifact", meeting_id=state.id,
        artifact_type="handoff", title="Stats artifact", body_markdown="retained",
    )
    service = ProjectService(db)
    assert service.summary(OWNER, "project-stats") == {
        "meeting_count": 1,
        # Stored as the aware UTC instant of 10:00 local (the aware-time census).
        "first_meeting": datetime(2026, 10, 1, 10, 0, 0).astimezone(timezone.utc).isoformat(),
        "last_meeting": datetime(2026, 10, 1, 10, 0, 0).astimezone(timezone.utc).isoformat(),
        "action_items_by_status": {"pending": 1},
        "artifact_count": 1,
    }

    assert db.meetings.delete_meeting(state.id) is True
    assert service.summary(OWNER, "project-stats") == {
        "meeting_count": 0,
        "first_meeting": None,
        "last_meeting": None,
        "action_items_by_status": {},
        "artifact_count": 0,
    }
    assert db.meetings.restore_meeting(state.id) is True
    assert service.summary(OWNER, "project-stats")["artifact_count"] == 1
    assert service.summary(OWNER, "project-stats")["action_items_by_status"] == {"pending": 1}


def test_meeting_watch_source_hides_parked_meeting_and_restores_it(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-watch-parked.db")
    state = _meeting("meeting-watch-parked")
    db.meetings.save_meeting(state)
    db.projects.create_project(project_id="watch-project", name="Watch project")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="watch-project", source="test", confidence=1.0
    )
    source = MeetingWatchSource(db=db)
    query = {"project_id": "watch-project"}
    assert [row["id"] for row in source.snapshot(OWNER, query_kind="meetings", query=query)] == [state.id]

    assert db.meetings.delete_meeting(state.id) is True
    assert source.snapshot(OWNER, query_kind="meetings", query=query) == []
    assert db.meetings.restore_meeting(state.id) is True
    assert [row["id"] for row in source.snapshot(OWNER, query_kind="meetings", query=query)] == [state.id]


def test_intel_job_list_hides_parked_meeting_and_restores_it(tmp_path: Path) -> None:
    db = Database(tmp_path / "intel-list-parked.db")
    state = _meeting("intel-list-parked")
    db.meetings.save_meeting(state)
    job_id = db.intel.enqueue_intel_job(
        state.id, transcript_hash=state.transcript_hash(), reason="list fence"
    )
    assert [job.job_id for job in db.intel.list_intel_jobs()] == [job_id]

    assert db.meetings.delete_meeting(state.id) is True
    assert db.intel.list_intel_jobs() == []
    assert db.meetings.restore_meeting(state.id) is True
    assert [job.job_id for job in db.intel.list_intel_jobs()] == [job_id]


def test_loop_collector_hides_parked_meeting_decision_and_restores_it(tmp_path: Path) -> None:
    db = Database(tmp_path / "collector-parked.db")
    state = _meeting("collector-parked")
    db.meetings.save_meeting(state)
    decision_id, _, _ = _decision_commitment_chain(db, state.id)
    collector = LoopCollector(db)

    assert any(loop.source_id == decision_id for loop in collector.collect())
    assert db.meetings.delete_meeting(state.id) is True
    assert collector._collect_meeting_decisions(datetime.now()) == []
    parked_loop = db.cadence.get_loop_by_source("meeting_decision", decision_id)
    assert parked_loop is not None and parked_loop.status == "closed"
    assert db.meetings.restore_meeting(state.id) is True
    assert any(loop.source_id == decision_id for loop in collector.collect())


def test_room_commitment_read_hides_parked_source_and_restores_it(tmp_path: Path) -> None:
    db = Database(tmp_path / "room-commitment-parked.db")
    state = _meeting("room-commitment-parked")
    db.meetings.save_meeting(state)
    db.projects.create_project(project_id="room-project", name="Room project")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="room-project", source="test", confidence=1.0
    )
    _, _, commitment_id = _decision_commitment_chain(db, state.id)
    project_service = ProjectService(db)
    assert [row["id"] for row in _read_room_commitments(project_service, "room-project")] == [commitment_id]

    assert db.meetings.delete_meeting(state.id) is True
    assert _read_room_commitments(project_service, "room-project") == []
    assert db.meetings.restore_meeting(state.id) is True
    assert [row["id"] for row in _read_room_commitments(project_service, "room-project")] == [commitment_id]


def test_recall_hides_parked_commitment_but_keeps_promoted_decision_record(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "recall-parked.db")
    state = _meeting("recall-parked")
    db.meetings.save_meeting(state)
    _, record_id, commitment_id = _decision_commitment_chain(db, state.id)
    service = RecallService(db)

    before_decisions = service.recall(OWNER, "Parked meeting dependency", filter="decisions")
    before_commitments = service.recall(OWNER, "Parked meeting dependency", filter="commitments")
    assert [card["id"] for card in before_decisions["current"]] == [record_id]
    assert [row["id"] for row in before_commitments["owed"]] == [commitment_id]
    assert before_decisions["current"][0]["source"]["meeting_id"] == state.id

    assert db.meetings.delete_meeting(state.id) is True
    parked_decisions = service.recall(OWNER, "Parked meeting dependency", filter="decisions")
    parked_commitments = service.recall(OWNER, "Parked meeting dependency", filter="commitments")
    assert [card["id"] for card in parked_decisions["current"]] == [record_id]
    assert parked_decisions["current"][0]["source"] is None
    assert parked_commitments["owed"] == []

    assert db.meetings.restore_meeting(state.id) is True
    restored = service.recall(OWNER, "Parked meeting dependency", filter="commitments")
    assert [row["id"] for row in restored["owed"]] == [commitment_id]
