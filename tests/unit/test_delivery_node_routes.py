"""Delivery node-link routes (HS-94-03) — the HTTP surface.

The router is assembled onto a local FastAPI app in-test (the
delivery-route precedent); production registration is wired
elsewhere. Proven here: node-token auth (missing/wrong/revoked/
browser-token all refuse, typed), hello-before-heartbeat ordering,
the command envelope and its capability gate, the smuggling refusal
over the wire, and the browser-facing nodes projection with typed
liveness, last-seen, and zero secret material.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.delivery.node_link import (
    NODE_PROTOCOL,
    NodeLinkState,
    NodeTokenStore,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_node import build_delivery_node_router

WEB_TOKEN = "the-browser-token"
FULL_CAPS = ["delivery.source", "coder.steering"]


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def state(tmp_path, clock) -> NodeLinkState:
    return NodeLinkState(
        NodeTokenStore(tmp_path / "tokens.json"), web_token=WEB_TOKEN, clock=clock
    )


@pytest.fixture
def legacy_env() -> dict:
    return {
        "HOLDSPEAK_STEER_NODES": json.dumps(
            {"old-box": {"base_url": "http://192.168.1.99:8765", "token": "LEGACY-SECRET"}}
        )
    }


@pytest.fixture
def client(state, legacy_env) -> TestClient:
    app = FastAPI()
    app.include_router(
        build_delivery_node_router(
            WebContext(get_state=lambda: {}), link=state, legacy_env=legacy_env
        )
    )
    return TestClient(app)


def _pair(state, name="studio-mac"):
    _, token = state.token_store.create(name)
    return token


def _hello(client, token, name="studio-mac", caps=None, protocol=NODE_PROTOCOL):
    return client.post(
        "/api/delivery/node/hello",
        json={
            "node_protocol": protocol,
            "name": name,
            "instance_id": "inst-http",
            "capabilities": caps if caps is not None else FULL_CAPS,
            "resume_cursor": 0,
        },
        headers={"X-HoldSpeak-Node-Token": token},
    )


class TestNodeAuth:
    def test_hello_without_token_refuses(self, client, state):
        _pair(state)
        response = client.post(
            "/api/delivery/node/hello",
            json={"node_protocol": 1, "name": "studio-mac"},
        )
        assert response.status_code == 401
        assert response.json()["error"] == "token_rejected"

    def test_wrong_token_refuses(self, client, state):
        _pair(state)
        response = _hello(client, "not-the-token")
        assert response.status_code == 401
        assert response.json()["error"] == "token_rejected"

    def test_browser_token_refuses_by_name(self, client, state):
        _pair(state)
        response = _hello(client, WEB_TOKEN)
        assert response.status_code == 401
        assert response.json()["error"] == "node_token_required"

    def test_revoked_node_refused_by_name_on_hello_and_heartbeat(self, client, state):
        token = _pair(state)
        assert _hello(client, token).status_code == 200
        state.token_store.revoke("studio-mac")
        refused = _hello(client, token)
        assert refused.status_code == 401
        assert refused.json()["error"] == "node_revoked"
        beat = client.post(
            "/api/delivery/node/heartbeat",
            json={"name": "studio-mac"},
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert beat.status_code == 401
        assert beat.json()["error"] == "node_revoked"

    def test_rotation_takes_effect_without_repo_edits(self, client, state):
        token = _pair(state)
        assert _hello(client, token).status_code == 200
        rotated = state.token_store.rotate("studio-mac")
        assert _hello(client, token).status_code == 401
        assert _hello(client, rotated).status_code == 200

    def test_refusal_bodies_carry_no_token_material(self, client, state):
        token = _pair(state)
        response = _hello(client, "wrong-token")
        assert token not in response.text
        assert WEB_TOKEN not in response.text


class TestLinkOrdering:
    def test_heartbeat_before_hello_refuses(self, client, state):
        token = _pair(state)
        response = client.post(
            "/api/delivery/node/heartbeat",
            json={"name": "studio-mac"},
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert response.status_code == 409
        assert response.json()["error"] == "hello_required"

    def test_hello_envelope(self, client, state):
        token = _pair(state)
        body = _hello(client, token).json()
        assert body["ok"] is True
        assert body["node_protocol"] == NODE_PROTOCOL
        assert body["node_id"].startswith("node_")
        assert body["cursor"] == 0
        assert body["commands_enabled"] is True
        assert body["heartbeat_seconds"] == 5.0
        assert body["stale_after_seconds"] == 15.0
        assert body["offline_after_seconds"] == 30.0


class TestCommandsLeg:
    def test_empty_envelope_for_a_compatible_node(self, client, state):
        token = _pair(state)
        _hello(client, token)
        response = client.get(
            "/api/delivery/node/commands",
            params={"name": "studio-mac"},
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["commands_schema"] == 1
        assert body["commands"] == []

    def test_capability_mismatch_disables_commands_only(self, client, state):
        token = _pair(state)
        _hello(client, token, caps=["delivery.source"])
        refused = client.get(
            "/api/delivery/node/commands",
            params={"name": "studio-mac"},
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert refused.status_code == 409
        assert refused.json()["error"] == "commands_disabled"
        # Observation unaffected: the heartbeat leg still answers.
        beat = client.post(
            "/api/delivery/node/heartbeat",
            json={"name": "studio-mac", "events": [{"seq": 1, "kind": "rail.cursor"}]},
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert beat.status_code == 200
        assert beat.json()["cursor"] == 1


class TestEventWire:
    def test_smuggled_field_refused_over_http(self, client, state):
        token = _pair(state)
        _hello(client, token)
        smuggle = client.post(
            "/api/delivery/node/heartbeat",
            json={
                "name": "studio-mac",
                "events": [{"seq": 1, "kind": "rail.cursor", "prompt": "smuggled body"}],
            },
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert smuggle.status_code == 400
        assert smuggle.json()["error"] == "event_field_not_allowed"
        # Cursor integrity survives the refusal.
        clean = client.post(
            "/api/delivery/node/heartbeat",
            json={"name": "studio-mac", "events": [{"seq": 1, "kind": "rail.cursor"}]},
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert clean.status_code == 200
        assert clean.json() == {
            "ok": True, "cursor": 1, "accepted": 1,
            "resync": False, "commands_enabled": True,
        }


class TestNodesProjection:
    def test_liveness_projection_with_last_seen_and_legacy(
        self, client, state, clock
    ):
        token = _pair(state)
        _hello(client, token)
        clock.advance(16)
        view = client.get("/api/delivery/nodes").json()
        assert view["nodes_schema"] == 1
        linked = next(r for r in view["nodes"] if r["name"] == "studio-mac")
        assert linked["status"] == "stale"
        assert linked["last_seen"]
        legacy = next(r for r in view["nodes"] if r["name"] == "old-box")
        assert legacy["kind"] == "legacy-direct"
        assert legacy["status"] == "unknown"

    def test_projection_carries_no_secrets_or_urls(self, client, state):
        token = _pair(state)
        _hello(client, token)
        text = client.get("/api/delivery/nodes").text
        assert token not in text
        assert WEB_TOKEN not in text
        assert "LEGACY-SECRET" not in text
        assert "192.168.1.99" not in text

    def test_explicit_disconnect_projects_offline(self, client, state):
        token = _pair(state)
        _hello(client, token)
        gone = client.post(
            "/api/delivery/node/disconnect",
            json={"name": "studio-mac"},
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert gone.status_code == 200
        view = client.get("/api/delivery/nodes").json()
        row = next(r for r in view["nodes"] if r["name"] == "studio-mac")
        assert row["status"] == "offline"
        assert row["last_seen"]
