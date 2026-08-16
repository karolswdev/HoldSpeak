"""Adversarial verification for HS-124 observer MCP and doctor paths."""

from __future__ import annotations

from pathlib import Path
import time

import pytest

import holdspeak.db as hsdb
import holdspeak.mcp.tools as mcp_tools
from holdspeak.db.core import Database, reset_database
from holdspeak.doctor import check_observer
from holdspeak.principals import Principal, PrincipalKind


OWNER = Principal(PrincipalKind.OWNER, "verify-round3")


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _insert_event(db: Database, event_id: str = "verify-event") -> None:
    with db._connection() as conn:
        conn.execute(
            """
            INSERT INTO pipeline_events (
                event_id, timestamp, service, method, principal_kind,
                correlation_id, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, time.time(), "verify-service", "verify-method", "owner", "verify-chain", "boom"),
        )


def test_pipeline_events_without_filters_returns_recent_events(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    _insert_event(db)
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)

    events = mcp_tools.dispatch("pipeline.events", {}, OWNER)

    assert [event["event_id"] for event in events] == ["verify-event"]


def test_pipeline_events_passes_every_filter(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    _insert_event(db)
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    now = time.time()

    events = mcp_tools.dispatch(
        "pipeline.events",
        {
            "service": "verify-service",
            "method": "verify-method",
            "principal_kind": "owner",
            "since": now - 60,
            "until": now + 60,
            "correlation_id": "verify-chain",
            "errors_only": True,
            "limit": 1,
        },
        OWNER,
    )

    assert [event["event_id"] for event in events] == ["verify-event"]


def test_check_observer_reports_probe_insert_failure(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(hsdb, "get_database", lambda: db)
    with db._connection() as conn:
        conn.execute(
            """
            CREATE TRIGGER reject_doctor_observer_probe
            BEFORE INSERT ON pipeline_events
            WHEN NEW.service = 'doctor'
            BEGIN
                SELECT RAISE(ABORT, 'probe writes rejected');
            END
            """
        )

    result = check_observer()

    assert result.status == "FAIL"
    assert "probe writes rejected" in result.detail
    assert "24h events: unavailable" in result.detail
