"""PHILO-13 C1: summary attention is filtered before Meeting pagination."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.services.meeting_service import MeetingService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meetings.crud import build_crud_router
from scripts.philo13_needs_you_fixture import (
    A1_ID,
    A1_TASK,
    A2_TASK,
    A3_ID,
    A4_ID,
    FAILED_MEETING_ID,
    _route_client,
    seed_week,
)


def _save_job(
    db: Database,
    *,
    job_id: str,
    meeting_id: str,
    status: str,
    attempts: int,
    last_error: str | None,
    origin_job_id: str | None = None,
) -> None:
    with db._connection() as conn:
        conn.execute(
            """
            INSERT INTO intel_jobs (
                job_id, meeting_id, origin_job_id, work_descriptor_sha256,
                transcript_hash, status, attempts, last_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                meeting_id,
                origin_job_id,
                f"descriptor-{job_id}",
                f"transcript-{job_id}",
                status,
                attempts,
                last_error,
            ),
        )


def test_summary_attention_filters_before_pagination_and_excludes_parked_and_old_job_leaves(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    db_path = home / "holdspeak.db"
    seeded = seed_week(db_path, home=home)
    db = Database(db_path)
    now = datetime.fromisoformat(seeded["now"])
    try:
        db.meetings.save_meeting(
            MeetingState(
                id="old-failed",
                title="Old failed summary",
                started_at=now - timedelta(days=30),
                intel_status="failed",
            )
        )
        db.meetings.save_meeting(
            MeetingState(
                id="retrying-leaf",
                title="Retrying summary",
                started_at=now - timedelta(days=2),
                intel_status="ready",
            )
        )
        _save_job(
            db,
            job_id="retrying-leaf-job",
            meeting_id="retrying-leaf",
            status="queued",
            attempts=1,
            last_error="first attempt failed",
        )
        db.meetings.save_meeting(
            MeetingState(
                id="superseded-failure",
                title="Superseded failure",
                started_at=now - timedelta(days=3),
                intel_status="ready",
            )
        )
        _save_job(
            db,
            job_id="superseded-parent",
            meeting_id="superseded-failure",
            status="failed",
            attempts=1,
            last_error="old failure",
        )
        _save_job(
            db,
            job_id="superseded-successor",
            meeting_id="superseded-failure",
            status="succeeded",
            attempts=1,
            last_error=None,
            origin_job_id="superseded-parent",
        )
        db.meetings.save_meeting(
            MeetingState(
                id="parked-failed",
                title="Parked failed summary",
                started_at=now - timedelta(days=4),
                intel_status="failed",
                parked=True,
            )
        )
        db.meetings.delete_meeting("parked-failed")

        app = FastAPI()
        app.include_router(
            build_crud_router(
                WebContext(get_state=lambda: {}, meeting_service=MeetingService(db))
            )
        )
        with TestClient(app) as client:
            refs: list[str] = []
            for offset in range(4):
                response = client.get(
                    "/api/meetings",
                    params={"summary_attention": "true", "limit": 1, "offset": offset},
                )
                assert response.status_code == 200, response.text
                payload = response.json()
                assert payload["total"] == 3
                refs.extend(row["id"] for row in payload["meetings"])
            assert refs == [FAILED_MEETING_ID, "retrying-leaf", "old-failed"]
            assert "parked-failed" not in refs
            assert "superseded-failure" not in refs
    finally:
        db.close()


def test_cached_needs_you_route_rebuilds_after_real_action_item_status_mutation(
    tmp_path: Path, monkeypatch
) -> None:
    """A1 done settles its linked Room duplicate in a warm aggregate."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    db_path = home / "holdspeak.db"
    seeded = seed_week(db_path, home=home)
    db = Database(db_path)

    def oracle_refs(client, room_payload: dict[str, object]) -> list[str]:
        """Read the six member refs from the real producer routes.

        The cached route supplies Room rows.  Door, assignment, and meeting
        reads supply the other member classes that the Dock merges in its
        ``needsYou.ts`` hook.
        """
        door = client.get("/api/door").json()
        board = door["board"]
        door_ids = {
            str(card["id"])
            for column in ("overdue", "now", "waiting", "unassigned")
            for card in board.get(column, [])
        }
        room_items = room_payload["items"]
        unmuted_room_refs = {
            str(item["ref"])
            for item in room_items
            if not item.get("muted")
        }
        assignments = client.get("/api/inference/assignments").json()
        assignment_rows = {
            str(row["id"]): row["effective"]["status"]
            for row in assignments["task_overrides"]
        }
        meetings = client.get(
            "/api/meetings",
            params={"summary_attention": "true", "limit": 500, "offset": 0},
        ).json()
        refs = {
            ref
            for ref in (A1_ID, A3_ID, A4_ID)
            if ref in door_ids
        }
        if A2_TASK in unmuted_room_refs:
            refs.add(A2_TASK)
        if assignment_rows.get("speech.transcribe") == "no_assignment" and assignment_rows.get(
            "meeting.deferred_analysis"
        ) == "no_assignment":
            refs.add("blocker:engines")
        if any(row["id"] == FAILED_MEETING_ID for row in meetings["meetings"]):
            refs.add(FAILED_MEETING_ID)
        return [ref for ref in seeded["expectedRefs"] if ref in refs]

    try:
        with _route_client(db, datetime.fromisoformat(seeded["now"])) as client:
            before_response = client.get("/api/desk/needs-you")
            assert before_response.status_code == 200, before_response.text
            before = before_response.json()
            assert before["count"] == 2
            assert any(
                row["ref"] == A1_TASK and row["source"] == "item"
                for row in before["items"]
            )
            assert oracle_refs(client, before) == seeded["expectedRefs"]
            before_computed_at = before["computedAt"]

            mutation = client.patch(
                f"/api/all-action-items/{A1_ID}", json={"status": "done"}
            )
            assert mutation.status_code == 200, mutation.text
            assert mutation.json()["success"] is True
            assert mutation.json()["action_item"]["status"] == "done"

            after_response = client.get("/api/desk/needs-you")
            assert after_response.status_code == 200, after_response.text
            after = after_response.json()
            assert after["count"] == 1
            assert after["computedAt"] != before_computed_at
            assert not any(row["ref"] == A1_TASK for row in after["items"])
            room_item = db.projects.get_project_item(seeded["ids"]["A1Room"])
            assert room_item is not None
            assert room_item["lifecycle"] == "planned"
            assert oracle_refs(client, after) == seeded["expectedRefs"][1:]
    finally:
        db.close()
