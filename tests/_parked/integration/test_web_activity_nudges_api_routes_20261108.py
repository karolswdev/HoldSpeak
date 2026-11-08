"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_web_activity_nudges_api.py``: test_select_clear_drops_the_pin. Not collected.
"""
from __future__ import annotations
"""HS-53-02 — the activity pre-briefing nudges HTTP API.

`GET /api/activity/nudges` returns the computed, source-cited nudges (the engine
already drops dismissed ones); empty when activity tracking is off.
`POST /api/activity/nudges/{nudge_id}/dismiss` persists the dismissal so the
nudge does not come back. Both run on a real `TestClient` over a seeded DB.
"""


import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.db import Database, get_database, reset_database
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
    return get_database(temp_db_dir / "test.db")


@pytest.fixture
def client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


def _seed_record(db: Database, *, url: str, entity_type: str | None = None,
                 entity_id: str | None = None, minutes_ago: int = 10) -> int:
    record = db.activity.upsert_activity_record(
        source_browser="safari",
        source_profile="default",
        url=url,
        title=entity_id or url,
        entity_type=entity_type,
        entity_id=entity_id,
        last_seen_at=datetime.now() - timedelta(minutes=minutes_ago),
    )
    return record.id


# --- HS-53-07: "Dictate with this" parks a server-side selection -------------


@pytest.mark.integration
def test_select_clear_drops_the_pin(client, db: Database) -> None:
    from holdspeak import dictation_selection as ds

    record_id = _seed_record(db, url="https://example.com/x", minutes_ago=5)
    client.post("/api/activity/nudges/select", json={"record_id": record_id})
    assert ds.peek_selected_record() == record_id
    resp = client.post("/api/activity/nudges/select/clear")
    assert resp.status_code == 200
    assert resp.json() == {"cleared": True}
    assert ds.peek_selected_record() is None
