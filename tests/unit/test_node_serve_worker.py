"""`holdspeak node serve` — the node-side link worker (HS-94-03).

Against an in-process hub app (the mesh-serve test discipline) the
worker says hello, adopts the hub's acked cursor, heartbeats with
metadata events, and persists its cursor after every ack; a
kill/restart (a fresh worker on the same cursor file) resumes with
no duplicate and no gap; an unreachable hub backs off exponentially
with jitter, bounded; the token rides the constructor/env — never
argv — and capabilities load from declarative local config.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.commands.node_serve import (
    DEFAULT_CAPABILITIES,
    NodeLinkWorker,
    load_node_capabilities,
    run_node_serve_command,
)
from holdspeak.delivery.node_link import NodeLinkState, NodeTokenStore
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_node import build_delivery_node_router

FULL_CAPS = ["delivery.source", "coder.steering"]


@pytest.fixture
def state(tmp_path) -> NodeLinkState:
    return NodeLinkState(
        NodeTokenStore(tmp_path / "tokens.json"), web_token="the-web-token"
    )


@pytest.fixture
def hub(state) -> TestClient:
    app = FastAPI()
    app.include_router(
        build_delivery_node_router(WebContext(get_state=lambda: {}), link=state)
    )
    return TestClient(app)


def _http_via(client: TestClient):
    """Adapt the worker's http_post seam onto the in-process hub."""

    def post(url: str, payload: dict[str, Any], *, token: str, timeout: float):
        path = url.split("http://test-hub", 1)[1]
        response = client.post(
            path, json=payload, headers={"X-HoldSpeak-Node-Token": token}
        )
        if response.status_code >= 400:
            raise ValueError(f"{response.status_code}: {response.json().get('error')}")
        return response.json()

    return post


def _worker(hub, state, tmp_path, name="edge", **kwargs) -> NodeLinkWorker:
    _, token = state.token_store.ensure(name)
    return NodeLinkWorker(
        hub_url="http://test-hub",
        name=name,
        token=kwargs.pop("token", token),
        capabilities=kwargs.pop("capabilities", FULL_CAPS),
        cursor_path=tmp_path / f"cursor_{name}.json",
        heartbeat_seconds=0.1,
        http_post=kwargs.pop("http_post", _http_via(hub)),
        sleep=kwargs.pop("sleep", lambda _s: None),
        **kwargs,
    )


class TestLinkLoop:
    def test_hello_then_heartbeat_goes_live(self, hub, state, tmp_path):
        worker = _worker(hub, state, tmp_path)
        assert worker.run_once() == 0
        assert state.status_of("edge") == "live"
        assert worker.node_id and worker.node_id.startswith("node_")

    def test_events_flow_and_cursor_persists(self, hub, state, tmp_path):
        worker = _worker(hub, state, tmp_path)
        worker.hello()
        worker.emit({"kind": "rail.cursor", "detail": {"tick": 1}})
        worker.emit({"kind": "session.lifecycle", "detail": {"state": "waiting"}})
        worker.heartbeat()
        assert worker.cursor == 2
        assert [e["seq"] for e in state.events_of("edge")] == [1, 2]
        persisted = json.loads((tmp_path / "cursor_edge.json").read_text())
        assert persisted == {"cursor": 2}

    def test_kill_restart_resumes_without_duplicate_or_gap(self, hub, state, tmp_path):
        first = _worker(hub, state, tmp_path)
        first.hello()
        for n in (1, 2, 3):
            first.emit({"kind": "rail.cursor", "detail": {"tick": n}})
        first.heartbeat()
        # "Kill": drop the worker object entirely; only the cursor
        # file survives, exactly like a process death after an ack.
        second = _worker(hub, state, tmp_path)
        assert second.cursor == 3  # loaded from the persisted file
        second.hello()
        second.emit({"kind": "rail.cursor", "detail": {"tick": 4}})
        second.heartbeat()
        seqs = [e["seq"] for e in state.events_of("edge")]
        assert seqs == [1, 2, 3, 4]  # no duplicate, no gap

    def test_restart_after_lost_ack_dedups_via_hub_cursor(self, hub, state, tmp_path):
        first = _worker(hub, state, tmp_path)
        first.hello()
        first.emit({"kind": "rail.cursor", "detail": {"tick": 1}})
        first.heartbeat()
        # Simulate dying BEFORE the cursor file caught up with the ack.
        (tmp_path / "cursor_edge.json").write_text('{"cursor": 0}\n')
        second = _worker(hub, state, tmp_path)
        assert second.cursor == 0
        response = second.hello()
        # The hub record is authoritative: resume adopts its cursor,
        # so the already-acked event is never re-emitted as seq 1.
        assert response["cursor"] == 1
        assert second.cursor == 1
        second.emit({"kind": "rail.cursor", "detail": {"tick": 2}})
        second.heartbeat()
        assert [e["seq"] for e in state.events_of("edge")] == [1, 2]


class TestBackoff:
    def test_bounded_exponential_backoff_with_jitter(self, state, tmp_path):
        waits: list[float] = []

        def down(*_a, **_k):
            raise OSError("connection refused")

        worker = NodeLinkWorker(
            hub_url="http://test-hub",
            name="edge",
            token="tok",
            capabilities=FULL_CAPS,
            cursor_path=tmp_path / "cursor.json",
            http_post=down,
            sleep=waits.append,
            rng=lambda: 1.0,  # jitter factor pinned to its ceiling
            backoff_base_seconds=1.0,
            backoff_max_seconds=8.0,
        )
        for _ in range(6):
            assert worker.step() is False
        assert waits == [1.0, 2.0, 4.0, 8.0, 8.0, 8.0]  # doubles, then bounded

    def test_jitter_stays_within_the_half_open_band(self, state, tmp_path):
        waits: list[float] = []

        def down(*_a, **_k):
            raise OSError("down")

        worker = NodeLinkWorker(
            hub_url="http://test-hub",
            name="edge",
            token="tok",
            cursor_path=tmp_path / "cursor.json",
            capabilities=FULL_CAPS,
            http_post=down,
            sleep=waits.append,
            rng=lambda: 0.0,  # jitter floor
            backoff_base_seconds=2.0,
            backoff_max_seconds=8.0,
        )
        worker.step()
        assert waits == [1.0]  # 2.0 * (0.5 + 0.5*0.0)

    def test_recovery_resets_the_backoff(self, hub, state, tmp_path):
        calls = {"n": 0}
        good = _http_via(hub)

        def flaky(url, payload, *, token, timeout):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise OSError("still down")
            return good(url, payload, token=token, timeout=timeout)

        worker = _worker(hub, state, tmp_path, http_post=flaky, rng=lambda: 1.0)
        assert worker.step() is False
        assert worker.step() is False
        assert worker.step() is True  # hello lands
        assert worker._failures == 0  # backoff reset on success


class TestConfigCustody:
    def test_capabilities_load_from_declarative_config(self, tmp_path):
        config = tmp_path / "node_link_edge.json"
        config.write_text(json.dumps({"capabilities": ["delivery.source"]}))
        assert load_node_capabilities("edge", config) == ["delivery.source"]
        assert load_node_capabilities("edge", tmp_path / "absent.json") == list(
            DEFAULT_CAPABILITIES
        )

    def test_serve_refuses_without_a_token_in_the_environment(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.delenv("HOLDSPEAK_NODE_TOKEN", raising=False)
        from types import SimpleNamespace

        args = SimpleNamespace(
            hub="http://test-hub", name="edge", token_env="HOLDSPEAK_NODE_TOKEN"
        )
        assert run_node_serve_command(args) == 2

    def test_token_never_appears_in_the_argument_surface(self):
        from holdspeak.commands.node_serve import build_parser

        parser = build_parser()
        args = parser.parse_args(["serve", "--name", "edge", "--hub", "http://h"])
        assert not hasattr(args, "token")  # token rides env, never argv
