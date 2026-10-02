"""PHILO-13-02 H-A1: meeting parking preserves the retained row and work."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
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
            legacy_displaced_work=True,
        )
        assert job_id
        read = db.intel.claim_next_intel_job
        expected_after_park = None
        expected_after_restore = job_id

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
        assert restored_value is not None and restored_value.job_id == expected_after_restore
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

    assert [item.id for item in db.meetings.list_action_items()] == [
        "standalone-owner-read", "a1-action"
    ]
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
    assert [item.id for item in db.meetings.list_action_items()] == [
        "standalone-owner-read", "a1-action"
    ]
    assert [item["id"] for item in project_service.list_action_items(OWNER, "owner-read-project")] == [
        "a1-action"
    ]
    assert db.meetings.get_speaker_segments("speaker-fence")
    assert db.meetings.get_speaker_stats("speaker-fence")["total_segments"] == 1
    assert people.one_on_one_brief(OWNER, relationship["id"], db=db)["linked_meetings"]
