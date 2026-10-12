"""Adversarial verification coverage for HS-124 observer queries and wiring."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.event_query_service import EventQueryService
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.sqlite_observer import SQLiteObserver


OWNER = Principal(PrincipalKind.OWNER, "verification-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _insert_event(db: Database, **overrides: object) -> None:
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "service": "TestService",
        "method": "method",
        "principal_kind": "OWNER",
        "principal_identity": "verification-owner",
        "args_summary": "{}",
        "result_summary": "{}",
        "error": None,
        "error_code": None,
        "duration_ms": 1.0,
        "correlation_id": "",
        "is_async": 0,
    }
    event.update(overrides)
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO pipeline_events "
            "(event_id, timestamp, service, method, principal_kind, "
            "principal_identity, args_summary, result_summary, error, error_code, "
            "duration_ms, correlation_id, is_async) "
            "VALUES (:event_id, :timestamp, :service, :method, :principal_kind, "
            ":principal_identity, :args_summary, :result_summary, :error, "
            ":error_code, :duration_ms, :correlation_id, :is_async)",
            event,
        )


def test_recent_zero_limit_returns_no_events(db: Database) -> None:
    _insert_event(db)

    assert EventQueryService(db).recent(OWNER, limit=0) == []


def test_stats_empty_table_has_empty_breakdowns(db: Database) -> None:
    stats = EventQueryService(db).stats(OWNER)

    assert stats == {
        "total_events": 0,
        "period": {"since": None, "until": None},
        "by_service": [],
        "by_method": [],
        "by_principal": [],
    }


def test_by_correlation_missing_chain_returns_empty_list(db: Database) -> None:
    _insert_event(db, correlation_id="other-chain")

    assert EventQueryService(db).by_correlation(OWNER, "missing-chain") == []


def test_stats_counts_non_null_errors(db: Database) -> None:
    _insert_event(db, service="Alpha", error=None)
    _insert_event(db, service="Alpha", error="failed")
    _insert_event(db, service="Beta", error="also failed")

    by_service = {
        item["service"]: item["error_count"]
        for item in EventQueryService(db).stats(OWNER)["by_service"]
    }

    assert by_service == {"Alpha": 1, "Beta": 1}


def test_recent_intersects_since_and_until_filters(db: Database) -> None:
    _insert_event(db, timestamp=1.0, method="before")
    _insert_event(db, timestamp=2.0, method="start")
    _insert_event(db, timestamp=3.0, method="middle")
    _insert_event(db, timestamp=4.0, method="end")
    _insert_event(db, timestamp=5.0, method="after")

    events = EventQueryService(db).recent(OWNER, since=2.0, until=4.0)

    assert [event["timestamp"] for event in events] == [4.0, 3.0, 2.0]


def test_primitive_service_writes_observed_event_to_database(db: Database) -> None:
    service = PrimitiveService(db, observer=SQLiteObserver(db._connection))

    assert service.list_notes(OWNER) == []

    with db._connection() as conn:
        event = conn.execute(
            "SELECT service, method, principal_kind, principal_identity, error "
            "FROM pipeline_events"
        ).fetchone()

    assert event is not None
    assert dict(event) == {
        "service": "PrimitiveService",
        "method": "list_notes",
        "principal_kind": "owner",
        "principal_identity": "verification-owner",
        "error": None,
    }
