"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_web_intent_timeline_api.py``: test_plugin_runs_endpoint_returns_persisted_runs, test_plugin_runs_endpoint_filters_by_window_id. Not collected.
"""
from __future__ import annotations
"""HS-2-08 / spec §9.8 — web API timeline + plugin-runs + artifacts endpoints.

Verifies the three read-side `/api/meetings/{id}/...` endpoints surface
the typed MIR data persisted by HS-2-05/HS-2-07 (windows + scores,
plugin runs, artifacts with lineage). Seeds the DB singleton, mounts
a `MeetingWebServer`, and drives requests through `TestClient`.
"""


import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.db import Database, get_database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def temp_db_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_dir):
    reset_database()
    instance = get_database(temp_db_dir / "test.db")
    return instance


@pytest.fixture
def seeded_meeting(db: Database):
    state = MeetingState(
        id="m-api",
        started_at=datetime(2026, 4, 25, 10, 0, 0),
        ended_at=datetime(2026, 4, 25, 11, 0, 0),
        title="API timeline test",
    )
    db.meetings.save_meeting(state)

    db.plugins.record_intent_window(
        meeting_id="m-api",
        window_id="m-api:w0001",
        start_seconds=0.0,
        end_seconds=90.0,
        transcript_hash="h1",
        transcript_excerpt="Architecture review opening.",
        profile="balanced",
        threshold=0.6,
        active_intents=["architecture"],
        intent_scores={"architecture": 0.83, "delivery": 0.10},
    )
    db.plugins.record_intent_window(
        meeting_id="m-api",
        window_id="m-api:w0002",
        start_seconds=30.0,
        end_seconds=120.0,
        transcript_hash="h2",
        transcript_excerpt="Delivery milestone planning.",
        profile="balanced",
        threshold=0.6,
        active_intents=["architecture", "delivery"],
        intent_scores={"architecture": 0.71, "delivery": 0.78},
    )

    db.plugins.record_plugin_run(
        meeting_id="m-api",
        window_id="m-api:w0001",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        status="success",
        idempotency_key="key-1",
        duration_ms=12.5,
        output={"summary": "Define API contract", "confidence_hint": 0.85},
    )
    db.plugins.record_plugin_run(
        meeting_id="m-api",
        window_id="m-api:w0002",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        status="deduped",
        idempotency_key="key-2",
        duration_ms=0.0,
        output={"summary": "Define API contract", "confidence_hint": 0.85},
    )

    db.plugins.record_artifact(
        artifact_id="art-001",
        meeting_id="m-api",
        artifact_type="requirements",
        title="Requirements summary",
        body_markdown="- Req 1\n- Req 2",
        structured_json={"plugin_id": "requirements_extractor"},
        confidence=0.85,
        status="draft",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        sources=[
            ("intent_window", "m-api:w0001"),
            ("intent_window", "m-api:w0002"),
            ("plugin_run", "key-1"),
            ("plugin_run", "key-2"),
        ],
    )
    return state


@pytest.fixture
def server() -> MeetingWebServer:
    return MeetingWebServer(
               WebRuntimeCallbacks(
                   on_bookmark=lambda *_args, **_kwargs: None,
                   on_stop=lambda *_args, **_kwargs: None,
                   get_state=lambda: None,
               ),
               host="127.0.0.1",
           )


@pytest.fixture
def client(server) -> TestClient:
    return TestClient(server.app)


@pytest.mark.integration
def test_plugin_runs_endpoint_returns_persisted_runs(client, seeded_meeting) -> None:
    response = client.get("/api/meetings/m-api/plugin-runs")
    assert response.status_code == 200

    body = response.json()
    assert body["meeting_id"] == "m-api"
    assert len(body["runs"]) == 2
    statuses = {r["status"] for r in body["runs"]}
    assert statuses == {"success", "deduped"}
    # Output payload is preserved.
    assert all(r["output"]["summary"] == "Define API contract" for r in body["runs"])


@pytest.mark.integration
def test_plugin_runs_endpoint_filters_by_window_id(client, seeded_meeting) -> None:
    response = client.get(
        "/api/meetings/m-api/plugin-runs",
        params={"window_id": "m-api:w0002"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["window_id"] == "m-api:w0002"
    assert len(body["runs"]) == 1
    assert body["runs"][0]["window_id"] == "m-api:w0002"


