"""Source-boundary and projection coverage for Calendar ingest."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from holdspeak.calendar_ingest import MAX_FEED_BYTES
from holdspeak.calendar_ingest_conductor import (
    CalendarIngestConductor,
    CalendarSourceError,
    CalendarSourceReader,
)
from holdspeak.config import CalendarConfig, Config, calendar_subscription_revision
from holdspeak.db.core import Database, reset_database


NOW = datetime(2026, 8, 27, 9, tzinfo=timezone.utc)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "calendar-ingest.db")
    yield database
    reset_database()


@pytest.fixture
def subscription_file(tmp_path: Path) -> Path:
    fixture = Path(__file__).parents[1] / "fixtures" / "calendar" / "basic.ics"
    path = tmp_path / "calendar.ics"
    path.write_bytes(fixture.read_bytes())
    return path


class _FetchHandler(BaseHTTPRequestHandler):
    seen_headers: list[dict[str, str]] = []

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        type(self).seen_headers.append(dict(self.headers.items()))
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://calendar-final.example.test/final.ics")
            self.end_headers()
            return
        if self.path == "/oversize":
            self.send_response(200)
            self.send_header("Content-Length", str(MAX_FEED_BYTES + 1))
            self.end_headers()
            return
        if self.path == "/slow":
            time.sleep(10.2)
        body = (
            b"BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:basic-1\r\n"
            b"DTSTART:20260827T100000Z\r\nDTEND:20260827T110000Z\r\n"
            b"SUMMARY:Team standup\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def local_http_server() -> str:
    _FetchHandler.seen_headers = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FetchHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def _conductor(
    db: Database,
    source: str,
    reader: Any,
    *,
    clock: float = NOW.timestamp(),
) -> CalendarIngestConductor:
    return CalendarIngestConductor(
        clock=lambda: clock,
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: Config(calendar=CalendarConfig(source)),
    )


def test_file_subscription_projects_then_honestly_removes_vanished_events(
    db: Database, subscription_file: Path
) -> None:
    conductor = _conductor(db, str(subscription_file), CalendarSourceReader())

    assert conductor.refresh() is True
    first = db.calendar_events.list_all()
    assert [(event.uid, event.title) for event in first] == [("basic-1", "Team standup")]

    subscription_file.write_bytes(b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n")

    assert conductor.refresh() is True
    assert db.calendar_events.list_all() == []

    subscription_file.write_bytes(b"x" * (MAX_FEED_BYTES + 1))
    with pytest.raises(CalendarSourceError, match="calendar_source_too_large"):
        CalendarSourceReader().read(str(subscription_file))


def test_https_subscription_projects_the_same_contract_without_auth_headers(
    db: Database, local_http_server: str
) -> None:
    # ``read`` rejects http before any I/O. Calling the HTTPS transport seam
    # directly against a local HTTP server is the lawful external-wire fake;
    # it proves redirects/headers/caps without inventing a TLS fixture.
    reader = CalendarSourceReader()
    with pytest.raises(CalendarSourceError, match="calendar_source_invalid"):
        reader.read(f"{local_http_server}/basic")
    conductor = _conductor(
        db,
        "https://calendar.example.test/source.ics",
        lambda _subscription: reader._read_https(f"{local_http_server}/basic"),
    )

    assert conductor.refresh() is True
    assert db.calendar_events.list_all()[0].uid == "basic-1"
    headers = {key.lower(): value for key, value in _FetchHandler.seen_headers[-1].items()}
    assert "authorization" not in headers
    assert "cookie" not in headers


def test_reader_rejects_redirect_timeout_and_oversize_before_projection(
    db: Database, local_http_server: str
) -> None:
    reader = CalendarSourceReader()
    # This is the production 10-second socket timeout against a live delayed
    # local socket, not a mocked transport timeout.
    assert reader.timeout_seconds == 10.0

    with pytest.raises(CalendarSourceError) as redirect:
        reader._read_https(f"{local_http_server}/redirect")
    assert redirect.value.error_class == "calendar_source_redirect"
    assert redirect.value.redirect_target == "https://calendar-final.example.test/final.ics"

    with pytest.raises(CalendarSourceError, match="calendar_source_timeout"):
        reader._read_https(f"{local_http_server}/slow")

    with pytest.raises(CalendarSourceError, match="calendar_source_too_large"):
        reader._read_https(f"{local_http_server}/oversize")

    conductor = _conductor(
        db,
        "https://calendar.example.test/source.ics",
        lambda _subscription: (_ for _ in ()).throw(redirect.value),
    )
    assert conductor.refresh() is False
    with db._connection() as conn:
        receipt = conn.execute(
            "SELECT state, outcome, result_ref FROM kernel_receipts"
        ).fetchone()
    assert tuple(receipt) == (
        "refused",
        "calendar_refresh_failed",
        "calendar-source:"
        f"{calendar_subscription_revision('https://calendar.example.test/source.ics')[:16]}:"
        "https://calendar-final.example.test/final.ics",
    )


def test_bad_event_is_skipped_with_deduplicated_kernel_receipt(db: Database) -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "calendar" / "mixed-bad-event.ics"
    conductor = _conductor(db, "/calendar.ics", lambda _source: fixture.read_bytes())

    assert conductor.refresh() is True
    assert conductor.refresh() is True
    assert [event.uid for event in db.calendar_events.list_all()] == ["good-sibling"]
    with db._connection() as conn:
        receipts = conn.execute(
            "SELECT state, outcome, result_ref FROM kernel_receipts ORDER BY created_at"
        ).fetchall()
    assert len(receipts) == 1
    assert receipts[0][0:2] == ("refused", "calendar_event_skipped")
    assert receipts[0][2].startswith("calendar-event:")


def test_feed_failure_retains_last_known_good_projection_and_receipts_once(
    db: Database, subscription_file: Path
) -> None:
    conductor = _conductor(db, str(subscription_file), CalendarSourceReader())
    assert conductor.refresh() is True
    original = db.calendar_events.list_all()
    subscription_file.write_bytes(b"not calendar\xff")

    assert conductor.refresh() is False
    assert conductor.refresh() is False
    assert db.calendar_events.list_all() == original
    with db._connection() as conn:
        receipts = conn.execute(
            "SELECT state, outcome FROM kernel_receipts ORDER BY created_at"
        ).fetchall()
    assert [tuple(receipt) for receipt in receipts] == [
        ("failed", "calendar_refresh_failed")
    ]
