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
        origin="meeting" if mid else "run",
    )


def _empty_primitive_repo():
    # The Primitive Framework desk repos default to empty for the meeting/artifact
    # focused tests in this module (their own coverage lives in
    # test_web_routes_sync_primitives.py).
    return types.SimpleNamespace(
        list=lambda include_deleted=False, limit=500: [],
        get=lambda rid, include_deleted=False: None,
        upsert=lambda **kw: None,
    )


def _fake_db(tmp_path, *, meetings=(), artifacts=None):
    artifacts = artifacts or {}
    summaries = [types.SimpleNamespace(id=m, started_at=datetime(2026, 1, 1)) for m in meetings]
    states = {m: _meeting_state(m) for m in meetings}
    # Equilibrium 23-04: the push route now live-merges meetings/artifacts, so the
    # fake repos record the merge calls (LWW reads return None → the push wins).
    saved_meetings: list = []
    recorded_artifacts: list = []
    return types.SimpleNamespace(
        db_path=tmp_path / "hs.db",
        saved_meetings=saved_meetings,
        recorded_artifacts=recorded_artifacts,
        meetings=types.SimpleNamespace(
            list_meetings=lambda limit=50: summaries[:limit],
            get_meeting=lambda mid: states.get(mid),
            save_meeting=lambda state: saved_meetings.append(state),
            delete_meeting=lambda mid: True,
        ),
        plugins=types.SimpleNamespace(
            list_artifacts=lambda mid: artifacts.get(mid, []),
            list_run_artifacts=lambda limit=200: [],
            get_artifact=lambda aid: None,
            delete_artifact=lambda aid: True,
            record_artifact=lambda **kw: recorded_artifacts.append(kw),
        ),
        notes=_empty_primitive_repo(),
        kbs=_empty_primitive_repo(),
        recipes=_empty_primitive_repo(),
        profiles=_empty_primitive_repo(),
        chains=_empty_primitive_repo(),
        workflows=_empty_primitive_repo(),
        directories=_empty_primitive_repo(),
        directory_memberships=_empty_primitive_repo(),
        model_manifests=_empty_primitive_repo(),
    )


def test_pull_serializes_meetings_and_artifacts(monkeypatch, tmp_path):
    fake = _fake_db(tmp_path, meetings=["m1"], artifacts={"m1": [_artifact("a1", "m1")]})
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: fake)

    resp = _client().get("/api/sync/pull")
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["meetings"]) == 1
    m = body["meetings"][0]
    # Strict wire ISO-8601 (`Z`, no fraction): Foundation's `.iso8601` on the iPad
    # rejects timezone-less stamps, and ONE bad stamp fails the whole pull decode.
    assert m["meta"] == {"id": "m1", "kind": "meeting",
                         "last_modified": "2026-01-01T00:00:00Z", "deleted": False}
    assert m["value"]["id"] == "m1"

    assert len(body["artifacts"]) == 1
    a = body["artifacts"][0]
    assert a["meta"]["kind"] == "artifact" and a["meta"]["id"] == "a1"
    assert a["value"]["artifact_type"] == "decisions"
    assert a["value"]["meeting_id"] == "m1"


def test_push_live_merges_meeting_and_keeps_audit_inbox(monkeypatch, tmp_path):
    # Equilibrium 23-04: a pushed meeting live-merges into the real table (a
    # `save_meeting` call) AND a copy lands in the durable JSON audit inbox.
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
    body = resp.json()
    assert body["success"] is True
    assert body["received"]["meetings"] == 1
    assert body["received"]["artifacts"] == 0

    # Live-merged into the meetings table (not just inboxed).
    assert len(fake.saved_meetings) == 1
    assert fake.saved_meetings[0].id == "m1"

    # And a replayable audit copy still lands in the inbox.
    inbox = tmp_path / "sync_inbox"
    files = list(inbox.glob("inbox-*.json"))
    assert len(files) == 1
    stored = json.loads(files[0].read_text())
    assert stored["meetings"][0]["meta"]["id"] == "m1"


def test_push_rejects_non_changeset(monkeypatch, tmp_path):
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: _fake_db(tmp_path))
    resp = _client().post("/api/sync/push", json={"nope": 1})
    assert resp.status_code == 422


def test_push_rejects_malformed_record(monkeypatch, tmp_path):
    # HSM-10-03 both-ends validation: a record without a well-formed meta is rejected
    # and never reaches the inbox.
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: _fake_db(tmp_path))
    bad = {"meetings": [{"value": {"id": "m1"}}], "artifacts": []}  # no meta
    resp = _client().post("/api/sync/push", json=bad)
    assert resp.status_code == 422
    assert not (tmp_path / "sync_inbox").exists()


# ---------------------------------------------------------------------------
# HS-93-06 — the exactly-once matrix on a REAL database: an identical replayed
# envelope is idempotent, a changed payload at an equal clock is refused into a
# retained conflict (never merged by guessing), and tombstones delete once and
# replay harmlessly.
# ---------------------------------------------------------------------------


def _real_db(tmp_path, monkeypatch):
    from holdspeak.db import Database

    db = Database(tmp_path / "hs.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    return db


def _meeting_value(mid: str) -> dict:
    return {
        "id": mid,
        "title": "Native capture",
        "tags": ["sync"],
        "started_at": "2026-07-10T09:00:00Z",
        "ended_at": "2026-07-10T09:30:00Z",
        "segments": [
            {"text": "the first durable words", "speaker": "Me",
             "start_time": 1.0, "end_time": 4.0},
        ],
        "capture_status": "finalized",
        "provenance": "native",
    }


def _push(client, record) -> dict:
    resp = client.post(
        "/api/sync/push", json={"meetings": [record], "artifacts": []}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _record(mid: str, lm: str, value=None, *, deleted: bool = False) -> dict:
    return {
        "meta": {"id": mid, "kind": "meeting", "last_modified": lm,
                 "deleted": deleted},
        "value": value,
    }


LM = "2026-07-10T09:30:00Z"
LM_NEWER = "2026-07-10T09:31:00Z"
LM_OLDER = "2026-07-10T09:29:00Z"


def test_replayed_identical_envelope_is_exactly_once(monkeypatch, tmp_path):
    db = _real_db(tmp_path, monkeypatch)
    client = _client()

    _push(client, _record("m-once", LM, _meeting_value("m-once")))
    stored = db.meetings.get_meeting("m-once")
    assert stored is not None

    # Replay the exact wire shape the hub itself would emit for this meeting.
    _push(client, _record("m-once", LM, stored.to_dict()))

    assert [m.id for m in db.meetings.list_meetings()] == ["m-once"]
    replayed = db.meetings.get_meeting("m-once")
    assert replayed.title == "Native capture"
    assert [s.text for s in replayed.segments] == ["the first durable words"]
    assert db.meetings.list_sync_conflicts("m-once") == []


def test_changed_payload_at_equal_clock_is_refused_into_one_conflict(
    monkeypatch, tmp_path
):
    db = _real_db(tmp_path, monkeypatch)
    client = _client()

    _push(client, _record("m-clash", LM, _meeting_value("m-clash")))
    divergent = db.meetings.get_meeting("m-clash").to_dict()
    divergent["title"] = "Divergent native title"

    _push(client, _record("m-clash", LM, divergent))
    # Local remains authoritative; the losing value is retained exactly once.
    assert db.meetings.get_meeting("m-clash").title == "Native capture"
    conflicts = db.meetings.list_sync_conflicts("m-clash")
    assert len(conflicts) == 1
    assert conflicts[0]["incoming"]["title"] == "Divergent native title"

    # Replaying the same divergent push does not stack a second conflict.
    _push(client, _record("m-clash", LM, divergent))
    assert len(db.meetings.list_sync_conflicts("m-clash")) == 1
    assert [m.id for m in db.meetings.list_meetings()] == ["m-clash"]


def test_stale_clock_push_is_skipped_without_conflict(monkeypatch, tmp_path):
    db = _real_db(tmp_path, monkeypatch)
    client = _client()

    _push(client, _record("m-stale", LM, _meeting_value("m-stale")))
    stale = db.meetings.get_meeting("m-stale").to_dict()
    stale["title"] = "An older device speaks"

    _push(client, _record("m-stale", LM_OLDER, stale))
    assert db.meetings.get_meeting("m-stale").title == "Native capture"
    assert db.meetings.list_sync_conflicts("m-stale") == []


def test_newer_clock_updates_same_identity_without_duplicate(monkeypatch, tmp_path):
    db = _real_db(tmp_path, monkeypatch)
    client = _client()

    _push(client, _record("m-lww", LM, _meeting_value("m-lww")))
    newer = db.meetings.get_meeting("m-lww").to_dict()
    newer["title"] = "Corrected after the meeting"

    _push(client, _record("m-lww", LM_NEWER, newer))
    assert [m.id for m in db.meetings.list_meetings()] == ["m-lww"]
    assert db.meetings.get_meeting("m-lww").title == "Corrected after the meeting"
    assert db.meetings.list_sync_conflicts("m-lww") == []


def test_tombstone_deletes_once_and_replays_harmlessly(monkeypatch, tmp_path):
    db = _real_db(tmp_path, monkeypatch)
    client = _client()

    _push(client, _record("m-tomb", LM, _meeting_value("m-tomb")))
    assert db.meetings.get_meeting("m-tomb") is not None

    _push(client, _record("m-tomb", LM_NEWER, deleted=True))
    assert db.meetings.get_meeting("m-tomb") is None

    # The replayed tombstone neither errors nor resurrects the meeting.
    _push(client, _record("m-tomb", LM_NEWER, deleted=True))
    assert db.meetings.get_meeting("m-tomb") is None
    assert db.meetings.list_meetings() == []


def test_tombstone_at_equal_clock_keeps_meeting_and_retains_conflict(
    monkeypatch, tmp_path
):
    db = _real_db(tmp_path, monkeypatch)
    client = _client()

    _push(client, _record("m-tomb-eq", LM, _meeting_value("m-tomb-eq")))
    _push(client, _record("m-tomb-eq", LM, deleted=True))

    # An equal-clock delete is a conflict decision for the owner, not a merge.
    assert db.meetings.get_meeting("m-tomb-eq") is not None
    conflicts = db.meetings.list_sync_conflicts("m-tomb-eq")
    assert len(conflicts) == 1
    assert conflicts[0]["incoming"]["deleted"] is True


def test_iso_emits_strict_wire_timestamps():
    """Every `_iso` shape lands as strict `Z` seconds — the iPad's `.iso8601`
    decoder rejects fractional seconds and timezone-less strings, and one bad
    stamp fails the WHOLE pull decode (the 2026-07-05 remote-pairing autopsy)."""
    from datetime import timezone
    from holdspeak.web.routes.sync import _iso

    assert _iso(None) is None
    assert _iso(datetime(2026, 7, 4, 9, 12, 48, 721541)) == "2026-07-04T09:12:48Z"
    assert _iso(datetime(2026, 7, 4, 9, 12, 48)) == "2026-07-04T09:12:48Z"
    assert _iso(datetime(2026, 7, 4, 9, 12, 48, 5, tzinfo=timezone.utc)) == "2026-07-04T09:12:48Z"
    assert _iso("2026-07-04T09:12:48Z") == "2026-07-04T09:12:48Z"
