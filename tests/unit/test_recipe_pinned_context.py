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
    db.recipes.upsert(recipe_id="a1", name="Owl",
                     manual_context="Always consider the Q3 launch.",
                     use_zone_context=True)
    got = db.recipes.get("a1")
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
        "recipes": [{
            "meta": {"id": "a-ipad", "kind": "recipe",
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
    assert resp.json()["received"]["recipes"] == 1

    pull = client.get("/api/sync/pull?limit=50").json()
    agents = [r for r in pull["recipes"] if r["meta"]["id"] == "a-ipad"]
    assert len(agents) == 1
    value = agents[0]["value"]
    assert value["manual_context"] == "Pin: the mesh charter."
    assert value["use_zone_context"] is True


def test_rest_routes_carry_and_preserve(rig) -> None:
    client, _db = rig
    created = client.post("/api/recipes", json={
        "name": "Owl", "manual_context": "pinned", "use_zone_context": True,
    }).json()["recipe"]
    assert created["manual_context"] == "pinned"
    assert created["use_zone_context"] is True
    # A partial PUT that never mentions the fields must NOT wipe them.
    updated = client.put(f"/api/recipes/{created['id']}", json={"role": "terse"}).json()["recipe"]
    assert updated["role"] == "terse"
    assert updated["manual_context"] == "pinned"
    assert updated["use_zone_context"] is True


