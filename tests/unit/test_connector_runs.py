"""HS-13-05 — connector_runs table + helpers."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from holdspeak.db import Database, reset_database


@pytest.fixture
def db(tmp_path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def test_record_and_list_run_round_trip(db):
    started = datetime(2026, 5, 1, 12, 0, 0)
    finished = started + timedelta(milliseconds=320)

    run = db.activity.record_connector_run(
        connector_id="gh",
        started_at=started,
        finished_at=finished,
        succeeded=True,
        output_bytes=2048,
        annotation_count=3,
        command_count=3,
    )

    assert run.id > 0
    assert run.duration_ms() == 320

    runs = db.activity.list_connector_runs(connector_id="gh")
    assert len(runs) == 1
    assert runs[0].connector_id == "gh"
    assert runs[0].succeeded is True
    assert runs[0].annotation_count == 3
    assert runs[0].error is None


def test_failed_run_records_error_text(db):
    started = datetime(2026, 5, 1, 12, 0, 0)
    finished = started + timedelta(milliseconds=15)
    db.activity.record_connector_run(
        connector_id="jira",
        started_at=started,
        finished_at=finished,
        succeeded=False,
        error="2 jira command(s) failed",
        output_bytes=512,
        command_count=2,
    )

    [run] = db.activity.list_connector_runs(connector_id="jira")
    assert run.succeeded is False
    assert run.error == "2 jira command(s) failed"


def test_list_returns_runs_in_descending_time_order(db):
    base = datetime(2026, 5, 1, 12, 0, 0)
    for offset in (0, 5, 10):
        db.activity.record_connector_run(
            connector_id="gh",
            started_at=base + timedelta(seconds=offset),
            finished_at=base + timedelta(seconds=offset, milliseconds=10),
            succeeded=True,
        )

    runs = db.activity.list_connector_runs(connector_id="gh", limit=5)
    starts = [r.started_at for r in runs]
    assert starts == sorted(starts, reverse=True)


def test_list_is_scoped_to_connector(db):
    base = datetime(2026, 5, 1, 12, 0, 0)
    db.activity.record_connector_run(
        connector_id="gh",
        started_at=base,
        finished_at=base + timedelta(milliseconds=1),
        succeeded=True,
    )
    db.activity.record_connector_run(
        connector_id="jira",
        started_at=base,
        finished_at=base + timedelta(milliseconds=1),
        succeeded=True,
    )

    assert len(db.activity.list_connector_runs(connector_id="gh")) == 1
    assert len(db.activity.list_connector_runs(connector_id="jira")) == 1
    assert len(db.activity.list_connector_runs(connector_id="calendar_activity")) == 0


def test_delete_connector_runs_is_pack_scoped(db):
    base = datetime(2026, 5, 1, 12, 0, 0)
    for cid in ("gh", "gh", "jira"):
        db.activity.record_connector_run(
            connector_id=cid,
            started_at=base,
            finished_at=base + timedelta(milliseconds=1),
            succeeded=True,
        )
    deleted = db.activity.delete_connector_runs(connector_id="gh")
    assert deleted == 2
    assert db.activity.list_connector_runs(connector_id="gh") == []
    assert len(db.activity.list_connector_runs(connector_id="jira")) == 1


def test_run_payload_round_trip(db):
    started = datetime(2026, 5, 1, 12, 0, 0)
    finished = started + timedelta(milliseconds=42)
    run = db.activity.record_connector_run(
        connector_id="gh",
        started_at=started,
        finished_at=finished,
        succeeded=True,
        output_bytes=64,
        annotation_count=1,
        command_count=1,
    )
    payload = run.to_payload()
    assert payload["connector_id"] == "gh"
    assert payload["succeeded"] is True
    assert payload["duration_ms"] == 42
    assert payload["output_bytes"] == 64
    # ISO-8601 strings round-trip cleanly.
    assert datetime.fromisoformat(payload["started_at"]) == started


def test_record_connector_run_requires_connector_id(db):
    with pytest.raises(ValueError):
        db.activity.record_connector_run(
            connector_id="",
            started_at=datetime.now(),
            finished_at=datetime.now(),
            succeeded=True,
        )
