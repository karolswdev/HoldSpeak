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
from scripts.philo13_needs_you_fixture import FAILED_MEETING_ID, seed_week


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
