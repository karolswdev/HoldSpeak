"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/unit/test_delivery_node_routes.py``: TestCommandsLeg. Not collected.
"""
from __future__ import annotations
"""Delivery node-link routes (HS-94-03) — the HTTP surface.

The router is assembled onto a local FastAPI app in-test (the
delivery-route precedent); production registration is wired
elsewhere. Proven here: node-token auth (missing/wrong/revoked/
browser-token all refuse, typed), hello-before-heartbeat ordering,
the command envelope and its capability gate, the smuggling refusal
over the wire, and the browser-facing nodes projection with typed
liveness, last-seen, and zero secret material.
"""


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


