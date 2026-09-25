"""PHILO-6-01 — the honest import badge: the producer link of the fence.

The fence runs producer -> wire adaptation -> rendered badge. This file is
the producer link: an empty VTT goes through the REAL import route and the
REAL background worker (``MeetingService._run_import_job``), which records
``intel_status = import_failed`` (``holdspeak/services/meeting_service.py``).

The wire JSON the Arrival reads (the list row from ``GET /api/meetings`` and
the detail from ``GET /api/meetings/{id}``) is compared with the fixture the
vitest link adapts and renders
(``web/src/desk/chair/__tests__/fixtures/philo6/import-failed-meeting.json``).
The fixture is never hand-written: set ``PHILO6_WRITE_FIXTURE=1`` to write it
from this run; otherwise a drift between the producer and the fixture fails
here, so the rendered link cannot pass on a wire the producer does not make.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

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

REPO = Path(__file__).resolve().parents[2]
EMPTY_VTT = REPO / "tests/fixtures/philo5_empty.vtt"
FIXTURE = (
    REPO / "web/src/desk/chair/__tests__/fixtures/philo6/import-failed-meeting.json"
)
TITLE = "Architecture boundary review — empty transcript"
STABLE_ID = "philo6-import-failed"
# Fields that change per run; the fixture stores stable stand-ins.
VOLATILE = {
    "id", "started_at", "ended_at", "created_at", "updated_at", "requested_at",
    "sync_modified_at",
}
TMP_NAME = re.compile(r"tmp\w+\.vtt")


@pytest.fixture
def client():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    get_database(temp_dir / "test.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    try:
        yield TestClient(server.app)
    finally:
        reset_database()
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def no_transcriber(monkeypatch):
    def _boom(_cfg):
        raise AssertionError("a transcript import must not build a transcriber")

    monkeypatch.setattr(import_route, "_transcriber_factory", _boom)


def _state(payload: dict[str, Any]) -> Any:
    status = payload.get("intel_status")
    return status.get("state") if isinstance(status, dict) else status


def _normalise(value: Any, meeting_id: str) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                0.0
                if key == "duration" and isinstance(item, (int, float))
                else STABLE_ID
                if key == "id" and item == meeting_id
                else "2026-09-24T09:00:00"
                if key in VOLATILE and isinstance(item, str) and key != "id"
                else _normalise(item, meeting_id)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalise(item, meeting_id) for item in value]
    if isinstance(value, str):
        return TMP_NAME.sub("upload.vtt", value.replace(meeting_id, STABLE_ID))
    return value


def _mint_failed_import(client: TestClient) -> tuple[str, dict[str, Any], dict[str, Any]]:
    response = client.post(
        "/api/meetings/import",
        files={"file": ("empty.vtt", EMPTY_VTT.read_bytes(), "text/vtt")},
        data={"title": TITLE},
    )
    assert response.status_code == 202, response.text
    meeting_id = response.json()["meeting_id"]
    deadline = time.time() + 15
    detail: dict[str, Any] = {}
    while time.time() < deadline:
        read = client.get(f"/api/meetings/{meeting_id}")
        if read.status_code == 200:
            detail = read.json()
            if _state(detail) != "importing":
                break
        time.sleep(0.05)
    listing = client.get("/api/meetings?limit=24")
    assert listing.status_code == 200
    rows = [row for row in listing.json()["meetings"] if row.get("id") == meeting_id]
    assert rows, "the failed import is not in the list the Arrival reads"
    return meeting_id, rows[0], detail


def test_empty_vtt_import_leaves_import_failed_on_the_wire(client, no_transcriber):
    """Characterisation (may pass pre-fix): the producer says import_failed."""
    meeting_id, row, detail = _mint_failed_import(client)
    assert _state(detail) == "import_failed", detail.get("intel_status")
    assert detail.get("segments") == []
    assert _state(row) == "import_failed", row.get("intel_status")

    wire = {
        "list_row": _normalise(row, meeting_id),
        "detail": _normalise(detail, meeting_id),
    }
    if os.environ.get("PHILO6_WRITE_FIXTURE") == "1":
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(wire, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    recorded = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert recorded == wire, (
        "the vitest fixture drifted from the real producer; "
        "re-run with PHILO6_WRITE_FIXTURE=1"
    )


def test_the_import_cause_is_short_and_names_no_temp_file(client, no_transcriber):
    """PHILO-6-01 round 3 (UX-CANON A.3; Astra's round-two check, finding 3).

    The worker's stored detail is what the Arrival shows as
    ``LAST ERROR · <cause>``. Round two showed a paragraph naming the worker's
    temp file (``TMPLYES_VQF.VTT``), a file the owner never selected. The
    cause is the short class: no file name, no path, no sentence, <= 60.
    """
    meeting_id, row, detail = _mint_failed_import(client)
    cause = (detail.get("intel_status") or {}).get("detail")
    assert row.get("intel_status_detail", cause) == cause
    assert cause == "NO TRANSCRIPT LINES", cause
    assert len(f"LAST ERROR · {cause}") <= 60, cause
    assert not re.search(r"tmp|\.(?:vtt|srt|txt|wav)|[/\\]|\.\s|\.$", cause, re.I), cause
