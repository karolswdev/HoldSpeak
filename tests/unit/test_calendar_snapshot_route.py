"""Route unit tests for the calendar snapshot endpoints (HS-146-07)."""
from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from holdspeak.web.routes.calendar_snapshot import (
    MAX_FILE_BYTES,
    build_calendar_snapshot_router,
)


@pytest.fixture
def client():
    from fastapi import FastAPI

    ctx = MagicMock()
    ctx._snapshot_extractor = lambda payload: json.dumps({
        "anchor_date": "2026-08-24",
        "anchor_confidence": "visible_header",
        "events": [
            {
                "title": "Standup",
                "weekday": "monday",
                "start_time": "09:00",
                "end_time": "09:30",
                "location": "Room 1",
            },
        ],
    })

    app = FastAPI()
    app.include_router(build_calendar_snapshot_router(ctx))
    return TestClient(app)


@pytest.fixture
def client_unreadable():
    from fastapi import FastAPI

    ctx = MagicMock()
    ctx._snapshot_extractor = lambda payload: json.dumps({
        "error": "unreadable_screenshot",
        "events": [],
    })

    app = FastAPI()
    app.include_router(build_calendar_snapshot_router(ctx))
    return TestClient(app)


class TestExtractEndpoint:
    def test_upload_single_image(self, client):
        png_data = _tiny_png()
        response = client.post(
            "/api/calendar/snapshot",
            files=[("files", ("calendar.png", io.BytesIO(png_data), "image/png"))],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["anchor_date"] == "2026-08-24"
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "Standup"

    def test_upload_multiple_images(self, client):
        png_data = _tiny_png()
        response = client.post(
            "/api/calendar/snapshot",
            files=[
                ("files", ("page1.png", io.BytesIO(png_data), "image/png")),
                ("files", ("page2.png", io.BytesIO(png_data), "image/png")),
            ],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_rejects_too_many_files(self, client):
        png_data = _tiny_png()
        response = client.post(
            "/api/calendar/snapshot",
            files=[
                ("files", (f"page{i}.png", io.BytesIO(png_data), "image/png"))
                for i in range(4)
            ],
        )
        assert response.status_code == 422
        assert "At most 3" in response.json()["error"]

    def test_rejects_unsupported_type(self, client):
        response = client.post(
            "/api/calendar/snapshot",
            files=[("files", ("doc.pdf", io.BytesIO(b"pdf"), "application/pdf"))],
        )
        assert response.status_code == 422
        assert "unsupported type" in response.json()["error"]

    def test_unreadable_refusal_passthrough(self, client_unreadable):
        png_data = _tiny_png()
        response = client_unreadable.post(
            "/api/calendar/snapshot",
            files=[("files", ("blurry.png", io.BytesIO(png_data), "image/png"))],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "unreadable_screenshot"


class TestConfirmEndpoint:
    def test_confirm_writes_ics(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "holdspeak.web.routes.calendar_snapshot.write_ics_atomic",
            lambda source_id, ics_bytes: tmp_path / f"{source_id}.ics",
        )
        monkeypatch.setattr(
            "holdspeak.web.routes.calendar_snapshot.trigger_calendar_refresh",
            lambda: True,
        )
        monkeypatch.setattr(
            "holdspeak.web.routes.calendar_snapshot.register_snapshot_source",
            lambda *a, **kw: {"success": True},
        )
        monkeypatch.setattr(
            "holdspeak.web.routes.calendar_snapshot.Config.load",
            lambda: MagicMock(calendar=MagicMock(sources=[])),
        )

        response = client.post(
            "/api/calendar/snapshot/confirm",
            json={
                "anchor_date": "2026-08-24",
                "events": [
                    {
                        "title": "Standup",
                        "weekday": "monday",
                        "start_time": "09:00",
                        "end_time": "09:30",
                    },
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["events_count"] == 1

    def test_confirm_rejects_missing_anchor(self, client):
        response = client.post(
            "/api/calendar/snapshot/confirm",
            json={
                "anchor_date": "",
                "events": [
                    {
                        "title": "Test",
                        "weekday": "monday",
                        "start_time": "09:00",
                        "end_time": "10:00",
                    },
                ],
            },
        )
        assert response.status_code == 422
        assert "anchor_date" in response.json()["error"]

    def test_confirm_rejects_invalid_anchor(self, client):
        response = client.post(
            "/api/calendar/snapshot/confirm",
            json={
                "anchor_date": "not-a-date",
                "events": [],
            },
        )
        assert response.status_code == 422
        assert "Invalid anchor date" in response.json()["error"]


def _tiny_png() -> bytes:
    """Minimal valid 1x1 PNG (67 bytes)."""
    import struct
    import zlib

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        raw = chunk_type + data
        return struct.pack(">I", len(data)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw_data = zlib.compress(b"\x00\x00\x00\x00")
    return sig + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", raw_data) + _chunk(b"IEND", b"")
