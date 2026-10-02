"""PHILO-13 H-A3 — list rows disclose the persisted summary fact.

The fence mints both rows through the real import and deferred-intelligence
producers, reads the persisted snapshot and detail route, then reaches the
same list route used by the desk for both an unfiltered and a transcript
search request.  A route/status claim is not allowed to stand in for stored
summary data.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.meeting_import import import_meeting
from holdspeak.services.meeting_service import MeetingService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meetings.crud import build_crud_router
from tests.unit.test_meeting_deferred_admission import _queue_rig
from tests.unit.test_philo3_summary_detail import OWNER, _admit


SOURCE = Path(__file__).resolve().parents[1] / "fixtures" / "philo3_architect_meeting.wav"
PRODUCED_SUMMARY = "The team reviewed the budget."


def _import_real_meeting(
    db: Database, source: Path, *, meeting_id: str, transcript: str
) -> Any:
    """Use the production import path, with only transcription input fixed."""

    class _Transcriber:
        def transcribe(self, _audio: Any, **_kwargs: Any) -> str:
            return transcript

    return import_meeting(
        source,
        db=db,
        transcriber=_Transcriber(),
        config=SimpleNamespace(
            meeting=SimpleNamespace(intel_enabled=True, intel_deferred_enabled=True)
        ),
        title=meeting_id,
        meeting_id=meeting_id,
    ).state


def _route_client(db: Database) -> TestClient:
    app = FastAPI()
    app.include_router(
        build_crud_router(
            WebContext(
                get_state=lambda: {},
                meeting_service=MeetingService(db),
            )
        )
    )
    return TestClient(app)


def _real_summary_rows(tmp_path: Path, monkeypatch: Any) -> tuple[Database, Any, Any]:
    """Mint summarized and unsummarized rows through the production paths."""
    db, _broker, _engine, _host, _requests = _queue_rig(
        tmp_path / "queue", monkeypatch
    )
    source = tmp_path / "meeting.wav"
    shutil.copyfile(SOURCE, source)
    summarized = _import_real_meeting(
        db,
        source,
        meeting_id="a3h-summarized",
        transcript="The durable atlas summary is ready for Tuesday.",
    )
    queued_without_summary = _import_real_meeting(
        db,
        source,
        meeting_id="a3h-queued-no-summary",
        transcript="The durable atlas summary is still pending for Tuesday.",
    )

    # Both rows are produced by the real admission path.  Only one reaches the
    # real queue producer and persists an IntelSnapshot.
    _admit(db, summarized.id)
    _admit(db, queued_without_summary.id)
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    stored = db.meetings.get_meeting(summarized.id)
    assert stored is not None and stored.intel is not None
    assert stored.intel.summary == PRODUCED_SUMMARY
    assert db.meetings.get_meeting(queued_without_summary.id).intel is None
    return db, summarized, queued_without_summary


def _disable_persisted_meeting_intelligence(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """Persist the app's current config with meeting intelligence disabled.

    The meetings list/detail route has no config input: it reads the database
    projection only.  SettingsService also drops these retained booleans as
    defaulted fields, so this fence uses the real Config.load/save path at an
    isolated config file rather than mutating a pretend runtime object.
    """
    import holdspeak.config as config_facade

    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config_facade, "CONFIG_FILE", config_path)
    config = Config.load()
    config.meeting.intel_enabled = False
    config.meeting.intel_deferred_enabled = False
    config.meeting.intelligence_auto = "off"
    config.save()

    persisted = Config.load()
    assert persisted.meeting.intel_enabled is False
    assert persisted.meeting.intel_deferred_enabled is False
    assert persisted.meeting.intelligence_auto == "off"


def _assert_rows(
    response: Any, summarized_id: str, unsummarized_id: str
) -> dict[str, dict[str, Any]]:
    assert response.status_code == 200, response.text
    rows = {row["id"]: row for row in response.json()["meetings"]}
    # Keep this explicit in each fence: removing has_summary must make the
    # focused test red instead of silently passing on another field.
    assert rows[summarized_id]["has_summary"] is True
    assert rows[unsummarized_id]["has_summary"] is False
    assert all("summary" not in row for row in rows.values())
    return rows


def test_summary_flag_survives_persisted_config_and_run_status_disable(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """The durable summary fact survives both current config and run status."""
    db, summarized, queued_without_summary = _real_summary_rows(
        tmp_path, monkeypatch
    )
    _disable_persisted_meeting_intelligence(tmp_path, monkeypatch)

    # The run status is independently disabled after the real snapshot exists.
    with db._connection() as conn:
        conn.execute(
            "UPDATE meetings SET intel_status = 'disabled' WHERE id = ?",
            (summarized.id,),
        )
    detail = MeetingService(db).get_meeting(OWNER, summarized.id)
    assert detail["intel"]["summary"] == PRODUCED_SUMMARY

    client = _route_client(db)
    _assert_rows(
        client.get("/api/meetings", params={"limit": 20}),
        summarized.id,
        queued_without_summary.id,
    )


def test_list_and_search_rows_do_not_leak_detail_summary_text(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """List/search expose the flag, never the exact detail summary text."""
    db, summarized, queued_without_summary = _real_summary_rows(
        tmp_path, monkeypatch
    )
    detail = MeetingService(db).get_meeting(OWNER, summarized.id)
    assert detail["intel"]["summary"] == PRODUCED_SUMMARY

    client = _route_client(db)
    rows = _assert_rows(
        client.get("/api/meetings", params={"limit": 20}),
        summarized.id,
        queued_without_summary.id,
    )
    for row in rows.values():
        assert PRODUCED_SUMMARY not in json.dumps(row, sort_keys=True)

    search_rows = _assert_rows(
        client.get(
            "/api/meetings", params={"search": "Tuesday", "limit": 20}
        ),
        summarized.id,
        queued_without_summary.id,
    )
    for row in search_rows.values():
        assert PRODUCED_SUMMARY not in json.dumps(row, sort_keys=True)
