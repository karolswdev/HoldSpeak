"""HS-109-01 archive backfill, synthesis reconciliation, and route authority."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.plugins.synthesis import synthesize_and_persist
from holdspeak.principals import agent_credentials
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


def _meeting(db: Database, meeting_id: str, started_at: str) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id,started_at,title) VALUES (?,?,?)",
            (meeting_id, started_at, meeting_id),
        )


def _artifact(db: Database, artifact_id: str, meeting_id: str, text: str) -> None:
    db.plugins.record_artifact(
        artifact_id=artifact_id,
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Decisions",
        structured_json={"decisions": [{"decision": text}]},
        plugin_id="decision_capture",
    )


def test_v30_migration_backfills_multi_meeting_archive_and_reruns_cleanly(
    tmp_path: Path,
) -> None:
    path = tmp_path / "archive.db"
    seeded = Database(path)
    _meeting(seeded, "meeting-1", "2026-06-01T10:00:00")
    _meeting(seeded, "meeting-2", "2026-06-02T10:00:00")
    _artifact(seeded, "artifact-1", "meeting-1", "Keep local-first")
    _artifact(seeded, "artifact-2", "meeting-2", "Keep local-first")
    with seeded._connection() as conn:
        conn.execute("DROP TABLE decisions")
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version(version) VALUES (29)")

    migrated = Database(path)
    rows = migrated.decisions.list()
    assert len(rows) == 2
    assert len({row.id for row in rows}) == 2
    assert {row.source_meeting_id for row in rows} == {"meeting-1", "meeting-2"}
    assert migrated.decisions.backfill() == {
        "artifacts": 2,
        "decisions": 2,
        "inserted": 0,
        "updated": 0,
        "unchanged": 2,
        "skipped": 0,
    }


def test_synthesis_persistence_reconciles_decisions_without_plugin_changes(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "synthesis.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    drafts, _lineage = synthesize_and_persist(
        db,
        "meeting-1",
        plugin_runs=[
            {
                "id": "run-1",
                "meeting_id": "meeting-1",
                "window_id": "window-1",
                "plugin_id": "decision_capture",
                "plugin_version": "1",
                "status": "success",
                "created_at": "2026-07-01T10:05:00",
                "output": {
                    "summary": "One decision",
                    "decisions": [
                        {"decision": "Use the persisted record", "rationale": "Queryable"}
                    ],
                },
            }
        ],
    )

    assert [draft.artifact_type for draft in drafts] == ["decisions"]
    assert [row.text for row in db.decisions.list()] == ["Use the persisted record"]
    before = db.decisions.list()[0].id
    synthesize_and_persist(db, "meeting-1", plugin_runs=[{
        "id": "run-1", "meeting_id": "meeting-1", "window_id": "window-1",
        "plugin_id": "decision_capture", "plugin_version": "1", "status": "success",
        "created_at": "2026-07-01T10:05:00",
        "output": {"summary": "One decision", "decisions": [
            {"decision": "Use the persisted record", "rationale": "Queryable"}
        ]},
    }])
    assert [row.id for row in db.decisions.list()] == [before]


def test_decision_routes_require_read_authority_and_owner_lifecycle_principal(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "routes.db")
    _meeting(db, "meeting-1", "2026-07-01T10:00:00")
    _artifact(db, "artifact-1", "meeting-1", "Keep the source memory")
    db.decisions.reconcile_artifact("artifact-1")
    decision_id = db.decisions.list()[0].id
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    callbacks = WebRuntimeCallbacks(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={"id": "decision-routes"}),
    )
    server = MeetingWebServer(
        callbacks, host="127.0.0.1", auth_token="owner-secret"
    )
    owner = TestClient(server.app)

    anonymous = TestClient(server.app)
    anonymous.headers.pop("x-holdspeak-token", None)
    denied_read = anonymous.get("/api/decisions")
    assert denied_read.status_code == 401
    assert denied_read.json()["principal"] == "none"
    assert denied_read.json()["missing_right"] == "read"

    issued = owner.post(
        "/api/principals/agents", json={"identity": "claude:decision-reader"}
    ).json()
    agent = TestClient(server.app)
    agent.headers.pop("x-holdspeak-token", None)
    agent.headers["Authorization"] = f"Bearer {issued['credential']}"
    denied_agent_read = agent.get("/api/decisions")
    assert denied_agent_read.status_code == 403
    assert denied_agent_read.json()["principal"] == "agent"
    assert denied_agent_read.json()["missing_right"] == "read"
    denied_write = agent.post(f"/api/decisions/{decision_id}/accept")
    assert denied_write.status_code == 403
    assert denied_write.json()["principal"] == "agent"
    assert denied_write.json()["missing_right"] == "owner"

    listed = owner.get("/api/decisions", params={"meeting_id": "meeting-1"})
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()["decisions"]] == [decision_id]
    accepted = owner.post(f"/api/decisions/{decision_id}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["receipt"]["actor"] == "owner-session"
    assert accepted.json()["receipt"]["operation"] == "decision.accept"
    illegal = owner.post(f"/api/decisions/{decision_id}/reject")
    assert illegal.status_code == 409
    assert illegal.json()["error"] == "illegal_decision_lifecycle_transition"
    agent_credentials.revoke("claude:decision-reader")
