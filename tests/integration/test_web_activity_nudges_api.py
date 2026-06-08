"""HS-53-02 — the activity pre-briefing nudges HTTP API.

`GET /api/activity/nudges` returns the computed, source-cited nudges (the engine
already drops dismissed ones); empty when activity tracking is off.
`POST /api/activity/nudges/{nudge_id}/dismiss` persists the dismissal so the
nudge does not come back. Both run on a real `TestClient` over a seeded DB.
"""

from __future__ import annotations

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


@pytest.mark.integration
def test_get_nudges_returns_source_cited_records(client, db: Database) -> None:
    _seed_record(
        db,
        url="https://github.com/karol/holdspeak/issues/53",
        entity_type="github_issue",
        entity_id="karol/holdspeak#53",
        minutes_ago=15,
    )
    response = client.get("/api/activity/nudges")
    assert response.status_code == 200
    body = response.json()
    assert body["activity_enabled"] is True
    assert body["nudges"], "expected at least one nudge"
    citations = body["nudges"][0]["citations"]
    assert citations
    assert citations[0]["source_browser"] == "safari"
    assert citations[0]["record_id"]


@pytest.mark.integration
def test_get_nudges_is_empty_when_activity_off(client, db: Database) -> None:
    db.activity.update_activity_privacy_settings(enabled=False)
    _seed_record(
        db,
        url="https://example.com/page",
        minutes_ago=5,
    )
    body = client.get("/api/activity/nudges").json()
    assert body["activity_enabled"] is False
    assert body["nudges"] == []


@pytest.mark.integration
def test_dismiss_removes_nudge_from_subsequent_get(client, db: Database) -> None:
    record_id = _seed_record(
        db,
        url="https://github.com/karol/holdspeak/issues/53",
        entity_type="github_issue",
        entity_id="karol/holdspeak#53",
        minutes_ago=20,
    )
    nudge_key = f"record:{record_id}"

    first = client.get("/api/activity/nudges").json()
    assert nudge_key in {n["key"] for n in first["nudges"]}

    dismiss = client.post(f"/api/activity/nudges/{nudge_key}/dismiss")
    assert dismiss.status_code == 200
    assert dismiss.json() == {"dismissed": nudge_key}

    second = client.get("/api/activity/nudges").json()
    assert nudge_key not in {n["key"] for n in second["nudges"]}


@pytest.mark.integration
def test_dismiss_blank_key_returns_400(client, db: Database) -> None:
    # FastAPI will route an empty path segment as a 404, so test the whitespace
    # case (a real blank key would not match the route). A whitespace-only key
    # exercises the engine's own validation through the route.
    response = client.post("/api/activity/nudges/%20%20/dismiss")
    assert response.status_code == 400


@pytest.mark.integration
def test_get_nudges_respects_limit_query(client, db: Database) -> None:
    for i in range(6):
        _seed_record(
            db,
            url=f"https://github.com/k/h/issues/{i}",
            entity_type="github_issue",
            entity_id=f"k/h#{i}",
            minutes_ago=10 + i,
        )
    body = client.get("/api/activity/nudges?limit=2").json()
    assert len(body["nudges"]) == 2
