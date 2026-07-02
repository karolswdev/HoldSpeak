"""HS-72-06 regression: the intel-process aftercare callback actually fires.

The Phase-72 split of `routes/meetings.py` surfaced a latent NameError:
`api_process_intel_jobs`'s `_on_meeting_ready` callback (HS-56-04 — the
`aftercare_ready` broadcast when deferred intel completes) referenced
`get_database` without any import in scope, so it crashed on every real
invocation and the event never fired through this path. This test drives the
callback through the real route and pins the broadcast.
"""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi.testclient")
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.intel_queue as intel_queue_module
import holdspeak.meeting_aftercare as aftercare_module
import holdspeak.db as hsdb
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meetings import build_meetings_router


def test_on_meeting_ready_broadcasts_aftercare_ready(monkeypatch, tmp_path) -> None:
    broadcasts: list[tuple[str, dict]] = []
    ctx = WebContext(get_state=lambda: {}, broadcast=lambda kind, payload: broadcasts.append((kind, payload)))

    def fake_drain(model, *, on_meeting_ready=None, **kwargs):
        assert on_meeting_ready is not None
        on_meeting_ready("m-ready")  # the moment that used to NameError
        return 1

    monkeypatch.setattr(intel_queue_module, "drain_intel_queue", fake_drain)
    monkeypatch.setattr(
        aftercare_module, "build_aftercare_ready_event",
        lambda db, meeting_id: {"meeting_id": meeting_id, "open_count": 2},
    )
    from holdspeak.db import Database, reset_database
    reset_database()
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: Database(tmp_path / "t.db"))

    app = FastAPI()
    app.include_router(build_meetings_router(ctx))
    res = TestClient(app).post("/api/intel/process", json={"max_jobs": 1})
    reset_database()

    assert res.status_code == 200, res.text
    assert ("aftercare_ready", {"meeting_id": "m-ready", "open_count": 2}) in broadcasts
