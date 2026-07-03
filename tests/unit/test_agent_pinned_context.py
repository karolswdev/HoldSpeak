"""HS-77-01 — the agent's pinned context survives the hub (schema v7).

The iPad authors `manual_context`/`use_zone_context`; Phase 72 documented
them as LOSSY through hub sync. v7 ends it: the hub stores them, the wire
carries them both ways, and a pushed agent pulls back byte-faithful.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="route tests drive the real app")

from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture()
def rig(monkeypatch):
    reset_database()
    database = Database(Path(tempfile.mkdtemp()) / "pinned.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: database)
    server = MeetingWebServer(WebRuntimeCallbacks(
        on_bookmark=lambda *a, **k: None, on_stop=lambda *a, **k: None,
        get_state=lambda: {"activity": {"state": "idle"}},
    ), host="127.0.0.1")
    yield TestClient(server.app), database
    reset_database()


def test_store_round_trips_the_pinned_context(rig) -> None:
    _client, db = rig
    db.agents.upsert(agent_id="a1", name="Owl",
                     manual_context="Always consider the Q3 launch.",
                     use_zone_context=True)
    got = db.agents.get("a1")
    assert got.manual_context == "Always consider the Q3 launch."
    assert got.use_zone_context is True
    # And to_dict carries the wire keys.
    d = got.to_dict()
    assert d["manual_context"] == "Always consider the Q3 launch."
    assert d["use_zone_context"] is True


def test_pushed_agent_pulls_back_byte_faithful(rig) -> None:
    """The full sync round trip — the exact loss Phase 72 documented."""
    client, _db = rig
    push = {
        "agents": [{
            "meta": {"id": "a-ipad", "kind": "agent",
                     "last_modified": "2026-07-02T12:00:00", "deleted": False},
            "value": {
                "id": "a-ipad", "name": "Scribe", "avatar": "📜",
                "system_prompt": "summarize",
                "manual_context": "Pin: the mesh charter.",
                "use_zone_context": True,
            },
        }],
    }
    resp = client.post("/api/sync/push", json=push)
    assert resp.status_code == 200, resp.text
    assert resp.json()["received"]["agents"] == 1

    pull = client.get("/api/sync/pull?limit=50").json()
    agents = [r for r in pull["agents"] if r["meta"]["id"] == "a-ipad"]
    assert len(agents) == 1
    value = agents[0]["value"]
    assert value["manual_context"] == "Pin: the mesh charter."
    assert value["use_zone_context"] is True


def test_rest_routes_carry_and_preserve(rig) -> None:
    client, _db = rig
    created = client.post("/api/agents", json={
        "name": "Owl", "manual_context": "pinned", "use_zone_context": True,
    }).json()["agent"]
    assert created["manual_context"] == "pinned"
    assert created["use_zone_context"] is True
    # A partial PUT that never mentions the fields must NOT wipe them.
    updated = client.put(f"/api/agents/{created['id']}", json={"role": "terse"}).json()["agent"]
    assert updated["role"] == "terse"
    assert updated["manual_context"] == "pinned"
    assert updated["use_zone_context"] is True


def test_v6_facsimile_upgrade_adds_the_columns(tmp_path) -> None:
    import sqlite3

    db_path = tmp_path / "v6.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE schema_version (version INTEGER NOT NULL);
        INSERT INTO schema_version (version) VALUES (6);
        CREATE TABLE agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            avatar TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT '',
            system_prompt TEXT NOT NULL DEFAULT '',
            user_template TEXT NOT NULL DEFAULT '',
            tools_json TEXT NOT NULL DEFAULT '[]',
            kb_id TEXT,
            profile_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_modified TEXT NOT NULL DEFAULT (datetime('now')),
            deleted INTEGER NOT NULL DEFAULT 0
        );
        INSERT INTO agents (id, name) VALUES ('old-agent', 'Kept');
        """
    )
    conn.commit()
    conn.close()

    reset_database()
    upgraded = Database(db_path)
    got = upgraded.agents.get("old-agent")
    assert got is not None and got.name == "Kept"
    assert got.manual_context == "" and got.use_zone_context is False
    upgraded.agents.upsert(agent_id="old-agent", name="Kept",
                           manual_context="now pinned", use_zone_context=True)
    again = upgraded.agents.get("old-agent")
    assert again.manual_context == "now pinned" and again.use_zone_context is True
    backups = list(db_path.parent.glob(f"{db_path.name}.*.bak"))
    assert backups, "no backup before the schema migration"
    reset_database()
