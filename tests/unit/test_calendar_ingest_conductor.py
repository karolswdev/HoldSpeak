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
from holdspeak.config import CalendarConfig, Config
from holdspeak.db.core import Database, reset_database


NOW = datetime(2026, 8, 27, 9, tzinfo=timezone.utc)
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
        config_loader=lambda: Config(calendar=CalendarConfig(source["value"])),
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
        config_loader=lambda: Config(calendar=CalendarConfig("/calendar.ics")),
        tick_interval=0.01,
    )
    conductor.start()
    try:
        deadline = time.monotonic() + 1
        while calls < 2 and time.monotonic() < deadline:
            time.sleep(0.005)
        assert calls >= 2
        assert db.calendar_events.list_all() == []
        with db._connection() as conn:
            receipts = conn.execute(
                "SELECT outcome FROM kernel_receipts ORDER BY created_at"
            ).fetchall()
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
        config_loader=lambda: Config(calendar=CalendarConfig("/calendar.ics")),
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
