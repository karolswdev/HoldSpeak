"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_web_activity_api.py``: test_project_briefings_endpoint_returns_timeline_newest_first, test_project_briefings_endpoint_unknown_project_returns_404, test_project_briefings_endpoint_empty_when_no_runs. Not collected.
"""
from __future__ import annotations
"""Integration tests for local activity intelligence web APIs."""


from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# DEFAULT_DB_PATH now lives in holdspeak.db.core (Phase 31 split); patch it there
# so Database.__init__ / get_database see the override.
from holdspeak.db import core as db_module
from holdspeak.db import Database, reset_database
from holdspeak.principals import PrincipalKind
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

pytestmark = [pytest.mark.requires_meeting]


@pytest.fixture
def activity_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    # HS-200-03: order matters, and owning the singleton matters.
    #
    # This used to reset FIRST and repoint `DEFAULT_DB_PATH` second, then build
    # a Database it never published. Between the reset and the repoint the
    # singleton was None while the default path was still the real one, so any
    # thread calling `get_database()` in that window published a foreign
    # database to the very routes under test — and the routes then read a
    # different file from the one this fixture wrote to. That is the three
    # CI-only failures on Actions run 34007939416 (`assert 0 == 1`,
    # `assert 404 == 200`, `assert None is not None`).
    #
    # Repoint first, then reset, then INSTALL this database as the singleton,
    # so there is no moment at which the default path and the singleton
    # disagree with what this test is asserting about.
    db_path = tmp_path / "holdspeak.db"
    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_path)
    reset_database()
    database = Database(db_path)
    monkeypatch.setattr(db_module, "_db", database, raising=False)
    yield database
    reset_database()


def test_project_briefings_endpoint_returns_timeline_newest_first(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    """HS-13-09: GET /api/projects/{id}/briefings walks
    meeting_context annotations matching `value.project_id`,
    newest first."""
    activity_db.projects.create_project(
        project_id="holdspeak", name="HoldSpeak", keywords=["holdspeak"]
    )
    activity_db.projects.create_project(
        project_id="other", name="Other", keywords=["other"]
    )
    # Two snapshots for holdspeak (different content), one for
    # the other project. The endpoint scopes by project_id.
    activity_db.activity.create_activity_annotation(
        source_connector_id="meeting_context",
        annotation_type="meeting_context_briefing",
        title="HoldSpeak — meeting context",
        value={"project_id": "holdspeak", "markdown": "# v1"},
    )
    activity_db.activity.create_activity_annotation(
        source_connector_id="meeting_context",
        annotation_type="meeting_context_briefing",
        title="HoldSpeak — meeting context",
        value={"project_id": "holdspeak", "markdown": "# v2"},
    )
    activity_db.activity.create_activity_annotation(
        source_connector_id="meeting_context",
        annotation_type="meeting_context_briefing",
        title="Other — meeting context",
        value={"project_id": "other", "markdown": "# o"},
    )

    response = test_client.get("/api/projects/holdspeak/briefings")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "holdspeak"
    assert len(body["briefings"]) == 2
    assert body["briefings"][0]["value"]["markdown"] == "# v2"
    assert body["briefings"][1]["value"]["markdown"] == "# v1"


def test_project_briefings_endpoint_unknown_project_returns_404(
    test_client: TestClient,
) -> None:
    response = test_client.get("/api/projects/no_such_project/briefings")
    assert response.status_code == 404


def test_project_briefings_endpoint_empty_when_no_runs(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    activity_db.projects.create_project(
        project_id="quiet", name="Quiet project", keywords=["quiet"]
    )
    response = test_client.get("/api/projects/quiet/briefings")
    assert response.status_code == 200
    assert response.json() == {"project_id": "quiet", "briefings": []}


