"""The Calendar app (test diet, 2026-10-11): the screenshot snapshot, end to end on the hub.

The real hub app (``MeetingWebServer``) over an isolated HOME, config and DB,
driven through ``TestClient``. The one stand-in is the vision model:
``extract_via_router`` answers the same two events the browser walk's fake
answered. Upload -> extract -> confirm -> the real ingest conductor -> the
Door's upcoming rail.
"""
from __future__ import annotations

import io
import json
import struct
import sys
import zlib
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

EVENTS = [
    {"title": "Glass Standup", "weekday": "monday", "start_time": "09:00", "end_time": "09:30", "location": "Room 1"},
    {"title": "Glass Review", "weekday": "friday", "start_time": "14:00", "end_time": "15:00", "location": None},
]


def _tiny_png() -> bytes:
    def _chunk(kind: bytes, data: bytes) -> bytes:
        raw = kind + data
        return struct.pack(">I", len(data)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00")) + _chunk(b"IEND", b"")


def _next_monday() -> date:
    today = date.today()
    return today + timedelta(days=7 - today.weekday())


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.config as config_module
    from holdspeak.db import reset_database

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    extraction = json.dumps({"anchor_date": _next_monday().isoformat(), "anchor_confidence": "visible_header",
                             "events": EVENTS})
    monkeypatch.setattr(
        "holdspeak.services.calendar_snapshot_service.extract_via_router",
        lambda principal, payload: {"output": extraction,
                                    "egress": {"scope": "private_network", "host": "192.168.1.50"}},
    )
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_a_confirmed_snapshot_puts_its_events_on_the_door_rail(hub: Hub) -> None:
    """replaces: tests/e2e/test_hs146_calendar_snapshot_glass.py::test_hs146_snapshot_upload_confirm_shows_rail"""
    extracted = hub.client.post(
        "/api/calendar/snapshot",
        files=[("files", ("calendar.png", io.BytesIO(_tiny_png()), "image/png"))],
    )
    assert extracted.status_code == 200, extracted.text
    body = extracted.json()
    assert body["success"] is True, body
    assert len(body["events"]) == 2, body

    confirmed = hub.client.post("/api/calendar/snapshot/confirm",
                                json={"anchor_date": _next_monday().isoformat(), "events": EVENTS})
    assert confirmed.status_code == 200, confirmed.text
    result = confirmed.json()
    assert result["success"] is True
    assert result["source_label"] == "O365 SNAPSHOT"
    assert result["events_count"] == 2

    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    assert CalendarIngestConductor().refresh(), "the conductor did not apply the snapshot .ics"

    door = hub.client.get("/api/door")
    assert door.status_code == 200, door.text
    rail: list[dict[str, Any]] = [
        item for item in door.json().get("upcoming", [])
        if item.get("source") == "calendar_event" and "Glass" in item.get("title", "")
    ]
    assert sorted(item["title"] for item in rail) == ["Glass Review", "Glass Standup"], door.json().get("upcoming")
    assert {item.get("source_label", "") for item in rail} == {"O365 SNAPSHOT"}
