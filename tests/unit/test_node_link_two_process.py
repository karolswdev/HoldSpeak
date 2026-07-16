"""TWO-PROCESS node-link proof (HS-94-03).

A real ``holdspeak node serve`` subprocess (`python -m
holdspeak.commands.node_serve serve …`) links to a real uvicorn hub
on a loopback port:

1. the node goes LIVE (hello + heartbeats, token via env only);
2. SIGKILL — the hub decays live → stale → offline on its own
   monotonic clock, last-seen retained;
3. restart — the node resumes its persisted cursor and the hub's
   accepted event sequence stays contiguous: no duplicate, no gap.

Waits are bounded deadlines over observable state, never sleeps of
faith. Liveness thresholds are compressed via the state seams (the
5/15/30 ratio at 1/2 s scale); the production defaults are asserted
in test_delivery_node_routes.py.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from fastapi import FastAPI

from holdspeak.delivery.node_link import NodeLinkState, NodeTokenStore
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_node import build_delivery_node_router

REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_NAME = "proof-node"


def _wait_for(predicate, *, timeout: float, interval: float = 0.05, what: str = ""):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise AssertionError(f"timed out waiting for {what or predicate}")


@pytest.fixture
def hub_server(tmp_path):
    """A real uvicorn hub on an ephemeral loopback port, sharing its
    NodeLinkState with the test for direct observation."""
    state = NodeLinkState(
        NodeTokenStore(tmp_path / "tokens.json"),
        web_token="the-web-token",
        stale_after_seconds=1.0,
        offline_after_seconds=2.0,
    )
    app = FastAPI()
    app.include_router(
        build_delivery_node_router(WebContext(get_state=lambda: {}), link=state)
    )
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    config = uvicorn.Config(app, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [sock]}, daemon=True
    )
    thread.start()
    _wait_for(lambda: server.started, timeout=10, what="uvicorn startup")
    yield state, f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


def _spawn_node(hub_url: str, token: str, cursor_path: Path) -> subprocess.Popen:
    env = {**os.environ, "HOLDSPEAK_NODE_TOKEN": token}
    return subprocess.Popen(
        [
            sys.executable, "-m", "holdspeak.commands.node_serve", "serve",
            "--hub", hub_url,
            "--name", NODE_NAME,
            "--heartbeat-seconds", "0.15",
            "--cursor-path", str(cursor_path),
            "--capability", "delivery.source",
            "--capability", "coder.steering",
            "--backoff-base", "0.2",
            "--backoff-max", "0.5",
            "--emit-ticks",
        ],
        env=env,
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class TestTwoProcessProof:
    def test_live_kill_stale_offline_restart_resume(self, hub_server, tmp_path):
        state, hub_url = hub_server
        _, token = state.token_store.create(NODE_NAME)
        cursor_path = tmp_path / "node_cursor.json"
        timeline: list[str] = []

        def mark(step: str) -> None:
            timeline.append(f"{time.strftime('%H:%M:%S')} {step}")

        # 1. spawn the real node process; watch it go live and ship events
        proc = _spawn_node(hub_url, token, cursor_path)
        try:
            _wait_for(
                lambda: state.status_of(NODE_NAME) == "live",
                timeout=15, what="node live",
            )
            mark("node LIVE after spawn")
            _wait_for(
                lambda: len(state.events_of(NODE_NAME)) >= 3,
                timeout=15, what="3 acked events",
            )
            mark(f"events flowing (cursor {state.nodes_view()['nodes'][0]['cursor']})")

            # 2. SIGKILL — a crash, not a goodbye
            proc.kill()
            proc.wait(timeout=10)
            cursor_at_kill = state.nodes_view()["nodes"][0]["cursor"]
            events_at_kill = len(state.events_of(NODE_NAME))
            mark(f"node KILLED at cursor {cursor_at_kill}")

            _wait_for(
                lambda: state.status_of(NODE_NAME) == "stale",
                timeout=10, what="stale after kill",
            )
            mark("hub sees STALE")
            _wait_for(
                lambda: state.status_of(NODE_NAME) == "offline",
                timeout=10, what="offline after kill",
            )
            row = next(
                r for r in state.nodes_view()["nodes"] if r["name"] == NODE_NAME
            )
            assert row["last_seen"], "last-seen must survive offline"
            mark(f"hub sees OFFLINE, last_seen retained ({row['last_seen']})")

            # 3. restart — same cursor file, same pairing
            persisted = json.loads(cursor_path.read_text())["cursor"]
            assert persisted >= events_at_kill - 1  # file tracked the acks
            proc = _spawn_node(hub_url, token, cursor_path)
            _wait_for(
                lambda: state.status_of(NODE_NAME) == "live",
                timeout=15, what="node live after restart",
            )
            mark("node LIVE after restart")
            _wait_for(
                lambda: len(state.events_of(NODE_NAME)) >= events_at_kill + 2,
                timeout=15, what="post-restart events",
            )
            seqs = [e["seq"] for e in state.events_of(NODE_NAME)]
            assert seqs == list(range(1, len(seqs) + 1)), (
                f"cursor resume must be gapless and duplicate-free, got {seqs}"
            )
            mark(f"cursor RESUMED contiguously: seqs 1..{len(seqs)}")
        finally:
            proc.kill()
            proc.wait(timeout=10)
        print("\nTWO-PROCESS PROOF TIMELINE")
        for line in timeline:
            print("  " + line)
