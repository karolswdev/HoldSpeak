"""Doctor coverage for the HS-124 pipeline observer."""

from __future__ import annotations

from pathlib import Path
import time

import pytest

import holdspeak.db as hsdb
from holdspeak.db.core import Database, reset_database
from holdspeak.doctor import check_observer


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def test_check_observer_healthy_on_fresh_db(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(hsdb, "get_database", lambda: db)

    result = check_observer()

    assert result.status == "PASS"
    assert "healthy" in result.detail


def test_check_observer_reports_event_count(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(hsdb, "get_database", lambda: db)
    now = time.time()
    with db._connection() as conn:
        conn.executemany(
            """
            INSERT INTO pipeline_events (
                event_id, timestamp, service, method, principal_kind
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (f"event-{index}", now, "workbench", "run_item", "owner")
                for index in range(3)
            ],
        )

    result = check_observer()

    assert result.status == "PASS"
    assert "24h events: 3" in result.detail
