"""HSM-10-02 (PR-B) — the desktop sync receiver routes.

Fake-DB unit tests: no real DB seeding. The handlers do `from ...db import
get_database` at call time, so we patch `holdspeak.db.get_database`.
"""

from __future__ import annotations

import json
import types
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_sync_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(build_sync_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


def _meeting_state(mid: str):
    return types.SimpleNamespace(
        id=mid,
        to_dict=lambda: {
            "id": mid, "started_at": "2026-01-01T00:00:00Z", "ended_at": None,
            "duration": 0.0, "formatted_duration": "0:00", "title": "T", "tags": [],
            "segments": [], "bookmarks": [], "intel": None,
            "intel_status": {"state": "none", "detail": None,
                             "requested_at": None, "completed_at": None},
            "mic_label": "m", "remote_label": "r", "web_url": None, "devices": [],
        },
    )


def _artifact(aid: str, mid: str):
    return types.SimpleNamespace(
        id=aid, meeting_id=mid, artifact_type="decisions", title="t",
        body_markdown="b", structured_json={}, confidence=0.8, status="draft",
        plugin_id="p", plugin_version="1", sources=[], updated_at=datetime(2026, 1, 2),
    )


def _fake_db(tmp_path, *, meetings=(), artifacts=None):
    artifacts = artifacts or {}
    summaries = [types.SimpleNamespace(id=m, started_at=datetime(2026, 1, 1)) for m in meetings]
    states = {m: _meeting_state(m) for m in meetings}
    return types.SimpleNamespace(
        db_path=tmp_path / "hs.db",
        meetings=types.SimpleNamespace(
            list_meetings=lambda limit=50: summaries[:limit],
            get_meeting=lambda mid: states.get(mid),
        ),
        plugins=types.SimpleNamespace(
            list_artifacts=lambda mid: artifacts.get(mid, []),
        ),
    )


def test_pull_serializes_meetings_and_artifacts(monkeypatch, tmp_path):
    fake = _fake_db(tmp_path, meetings=["m1"], artifacts={"m1": [_artifact("a1", "m1")]})
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: fake)

    resp = _client().get("/api/sync/pull")
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["meetings"]) == 1
    m = body["meetings"][0]
    assert m["meta"] == {"id": "m1", "kind": "meeting",
                         "last_modified": "2026-01-01T00:00:00", "deleted": False}
    assert m["value"]["id"] == "m1"

    assert len(body["artifacts"]) == 1
    a = body["artifacts"][0]
    assert a["meta"]["kind"] == "artifact" and a["meta"]["id"] == "a1"
    assert a["value"]["artifact_type"] == "decisions"
    assert a["value"]["meeting_id"] == "m1"


def test_push_writes_changeset_to_inbox(monkeypatch, tmp_path):
    fake = _fake_db(tmp_path)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: fake)

    changeset = {
        "meetings": [{"meta": {"id": "m1", "kind": "meeting",
                               "last_modified": "2026-01-01T00:00:00Z", "deleted": False},
                      "value": {"id": "m1"}}],
        "artifacts": [],
    }
    resp = _client().post("/api/sync/push", json=changeset)
    assert resp.status_code == 200
    assert resp.json() == {"success": True, "received": {"meetings": 1, "artifacts": 0}}

    inbox = tmp_path / "sync_inbox"
    files = list(inbox.glob("inbox-*.json"))
    assert len(files) == 1
    stored = json.loads(files[0].read_text())
    assert stored["meetings"][0]["meta"]["id"] == "m1"


def test_push_rejects_non_changeset(monkeypatch, tmp_path):
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: _fake_db(tmp_path))
    resp = _client().post("/api/sync/push", json={"nope": 1})
    assert resp.status_code == 422
