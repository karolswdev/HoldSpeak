"""HS-57-03 — POST /api/meetings/import with a transcript file.

A transcript upload rides the exact recording lifecycle (202 → visible row →
resolved meeting / honest `import_failed`) but NEVER constructs a transcriber
— the factory is monkeypatched to explode, so any model construction fails
the test. The audio behavior itself is locked by the untouched Phase-55
route tests.
"""
from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.db import get_database, reset_database
from holdspeak.web.routes import meeting_import as import_route
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

VTT = (
    "WEBVTT\n"
    "\n"
    "00:00:01.000 --> 00:00:04.000\n"
    "<v Priya>Morning, let's start with the rollout.</v>\n"
    "\n"
    "00:00:04.500 --> 00:00:09.000\n"
    "<v Sam>The fix is merged and the tests are green.\n"
)


@pytest.fixture
def temp_db_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_dir):
    reset_database()
    return get_database(temp_db_dir / "test.db")


@pytest.fixture
def client(db):
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


@pytest.fixture
def no_transcriber(monkeypatch):
    """Any transcriber construction fails the test — transcripts never need one."""

    def _boom(_cfg):
        raise AssertionError("a transcript import must not build a transcriber")

    monkeypatch.setattr(import_route, "_transcriber_factory", _boom)


def _intel_state(payload) -> str:
    status = payload.get("intel_status") or {}
    return status.get("state") if isinstance(status, dict) else status


def _wait_for_status(client, meeting_id, statuses, timeout=10.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        detail = client.get(f"/api/meetings/{meeting_id}")
        if detail.status_code == 200:
            last = detail.json()
            if _intel_state(last) in statuses:
                return last
        time.sleep(0.05)
    raise AssertionError(
        f"meeting never reached {statuses}; last={last and _intel_state(last)}"
    )


def test_vtt_upload_becomes_a_real_meeting_without_a_transcriber(client, db, no_transcriber):
    response = client.post(
        "/api/meetings/import",
        files={"file": ("weekly sync.vtt", VTT.encode(), "text/vtt")},
        data={"tags": "imported,transcript"},
    )
    assert response.status_code == 202
    meeting_id = response.json()["meeting_id"]

    final = _wait_for_status(client, meeting_id, {"queued", "disabled"})
    # The file's own speakers and real cue timestamps.
    assert [s["speaker"] for s in final["segments"]] == ["Priya", "Sam"]
    assert [s["start_time"] for s in final["segments"]] == [1.0, 4.5]
    assert final["title"] == "weekly sync"
    assert "transcript" in final.get("tags", [])


def test_txt_upload_uses_the_transcript_fallback_speaker(client, db, no_transcriber):
    response = client.post(
        "/api/meetings/import",
        files={"file": ("notes.txt", b"we agreed to ship friday\n", "text/plain")},
    )
    assert response.status_code == 202
    final = _wait_for_status(client, response.json()["meeting_id"], {"queued", "disabled"})
    assert [s["speaker"] for s in final["segments"]] == ["Transcript"]


def test_garbage_transcript_marks_the_row_honestly_and_is_removable(client, db, no_transcriber):
    garbage = bytes(range(256)) * 8
    response = client.post(
        "/api/meetings/import",
        files={"file": ("mystery.txt", garbage, "text/plain")},
    )
    assert response.status_code == 202
    meeting_id = response.json()["meeting_id"]

    failed = _wait_for_status(client, meeting_id, {"import_failed"})
    detail = ((failed.get("intel_status") or {}).get("detail") or "")
    assert "does not look like a text transcript" in detail
    deleted = client.delete(f"/api/meetings/{meeting_id}")
    assert deleted.status_code in (200, 204)


def test_header_only_vtt_fails_with_the_parser_message(client, db, no_transcriber):
    response = client.post(
        "/api/meetings/import",
        files={"file": ("empty.vtt", b"WEBVTT\n\nNOTE nothing\n", "text/vtt")},
    )
    assert response.status_code == 202
    failed = _wait_for_status(client, response.json()["meeting_id"], {"import_failed"})
    assert "no readable cue blocks" in ((failed.get("intel_status") or {}).get("detail") or "")
