"""Lifecycle and cadence coverage for the Calendar ingest conductor."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from holdspeak.calendar_ingest_conductor import (
    CalendarIngestConductor,
    CalendarSourceError,
)
from holdspeak.config import CalendarConfig, CalendarSource, Config
from holdspeak.db.core import Database, reset_database


NOW = datetime(2026, 8, 27, 9, tzinfo=timezone.utc)


def _cal(url: str) -> CalendarConfig:
    return CalendarConfig(sources=[
        CalendarSource(id="test-src", label="", url=url, enabled=True)
    ])
BASIC = (
    b"BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:cadence-event\r\n"
    b"DTSTART:20260827T100000Z\r\nDTEND:20260827T110000Z\r\n"
    b"SUMMARY:Cadence event\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "calendar-conductor.db")
    yield database
    reset_database()


def test_boot_refreshes_once_and_periodic_tick_rereads_current_subscription(db: Database) -> None:
    calls: list[str] = []
    booted = threading.Event()
    source = {"value": "/first.ics"}

    def reader(subscription: str) -> bytes:
        calls.append(subscription)
        if len(calls) >= 2:
            booted.set()
        return BASIC

    conductor = CalendarIngestConductor(
        clock=lambda: NOW.timestamp(),
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: Config(calendar=_cal(source["value"])),
        tick_interval=0.01,
    )
    conductor.start()
    try:
        deadline = time.monotonic() + 1
        while len(calls) < 1 and time.monotonic() < deadline:
            time.sleep(0.005)
        assert calls == ["/first.ics"]
        source["value"] = "/second.ics"
        assert booted.wait(timeout=1)
        assert calls[-1] == "/second.ics"
        assert db.calendar_events.list_all()[0].subscription_revision
    finally:
        conductor.stop()


def test_boot_and_tick_contain_fetch_and_parse_failures(db: Database) -> None:
    calls = 0

    def reader(_subscription: str) -> bytes:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise CalendarSourceError("calendar_source_network_error")
        return b"invalid\xff"

    conductor = CalendarIngestConductor(
        clock=lambda: NOW.timestamp(),
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: Config(calendar=_cal("/calendar.ics")),
        tick_interval=0.01,
    )
    conductor.start()
    try:
        # HS-145 triage of the cross-arc xdist watch item: waiting on reader
        # ENTRY raced the second receipt write (entry precedes the tick's
        # failure receipt). Wait on the receipts themselves — the observable
        # this test asserts.
        def _receipts() -> list:
            with db._connection() as conn:
                return conn.execute(
                    "SELECT outcome FROM kernel_receipts ORDER BY created_at"
                ).fetchall()

        deadline = time.monotonic() + 5
        receipts = _receipts()
        while len(receipts) < 2 and time.monotonic() < deadline:
            time.sleep(0.005)
            receipts = _receipts()
        assert calls >= 2
        assert db.calendar_events.list_all() == []
        assert [tuple(receipt) for receipt in receipts] == [
            ("calendar_refresh_failed",),
            ("calendar_refresh_failed",),
        ]
    finally:
        conductor.stop()


def test_stop_joins_the_calendar_thread_and_prevents_later_refresh(db: Database) -> None:
    calls = 0
    first = threading.Event()

    def reader(_subscription: str) -> bytes:
        nonlocal calls
        calls += 1
        first.set()
        return BASIC

    conductor = CalendarIngestConductor(
        clock=lambda: NOW.timestamp(),
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: Config(calendar=_cal("/calendar.ics")),
        tick_interval=0.01,
    )
    conductor.start()
    assert first.wait(timeout=1)
    conductor.stop()
    stopped_calls = calls
    time.sleep(0.05)
    assert conductor._thread is not None
    assert conductor._thread.is_alive() is False
    assert calls == stopped_calls


def test_multi_source_iteration_refreshes_all_enabled(db: Database) -> None:
    fetched: list[str] = []

    def reader(url: str) -> bytes:
        fetched.append(url)
        return BASIC

    config = Config(calendar=CalendarConfig(sources=[
        CalendarSource(id="src-a", label="Work", url="/work.ics", enabled=True),
        CalendarSource(id="src-b", label="Personal", url="/personal.ics", enabled=True),
        CalendarSource(id="src-c", label="Disabled", url="/disabled.ics", enabled=False),
    ]))
    conductor = CalendarIngestConductor(
        clock=lambda: NOW.timestamp(),
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: config,
    )
    assert conductor.refresh() is True
    assert sorted(fetched) == ["/personal.ics", "/work.ics"]
    rows = db.calendar_events.list_all()
    source_ids = {r.source_id for r in rows}
    assert source_ids == {"src-a", "src-b"}


def test_per_source_failure_isolation(db: Database) -> None:
    call_count = {"work": 0, "personal": 0}

    def reader(url: str) -> bytes:
        if "work" in url:
            call_count["work"] += 1
            raise CalendarSourceError("calendar_source_network_error")
        call_count["personal"] += 1
        return BASIC

    config = Config(calendar=CalendarConfig(sources=[
        CalendarSource(id="src-work", label="Work", url="/work.ics", enabled=True),
        CalendarSource(id="src-personal", label="Personal", url="/personal.ics", enabled=True),
    ]))
    conductor = CalendarIngestConductor(
        clock=lambda: NOW.timestamp(),
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: config,
    )
    conductor.refresh()

    rows = db.calendar_events.list_all()
    assert len(rows) == 1
    assert rows[0].source_id == "src-personal"
    assert call_count["work"] == 1
    assert call_count["personal"] == 1


def test_empty_sources_list_no_fetch(db: Database) -> None:
    fetched: list[str] = []

    def reader(url: str) -> bytes:
        fetched.append(url)
        return BASIC

    config = Config(calendar=CalendarConfig(sources=[]))
    conductor = CalendarIngestConductor(
        clock=lambda: NOW.timestamp(),
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: config,
    )
    assert conductor.refresh() is False
    assert fetched == []


def test_orphan_cleanup_after_source_removal(db: Database) -> None:
    def reader(url: str) -> bytes:
        return BASIC

    full_config = Config(calendar=CalendarConfig(sources=[
        CalendarSource(id="src-a", label="A", url="/a.ics", enabled=True),
        CalendarSource(id="src-b", label="B", url="/b.ics", enabled=True),
    ]))
    conductor = CalendarIngestConductor(
        clock=lambda: NOW.timestamp(),
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: full_config,
    )
    conductor.refresh()
    assert len(db.calendar_events.list_all()) == 2

    reduced_config = Config(calendar=CalendarConfig(sources=[
        CalendarSource(id="src-a", label="A", url="/a.ics", enabled=True),
    ]))
    conductor2 = CalendarIngestConductor(
        clock=lambda: NOW.timestamp(),
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: reduced_config,
    )
    conductor2.refresh()
    rows = db.calendar_events.list_all()
    assert len(rows) == 1
    assert rows[0].source_id == "src-a"
