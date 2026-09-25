"""PHILO-7-02 canvas: capture the REAL `GET /api/settings/remote` wire.

The credential half of every board comes from the real producer
(holdspeak/web/routes/mcp_http.py:198-245) on the real hub over an isolated
database, booted by the Phase 5 fence fixture
(tests/unit/test_philo5_the_loop.py:116-150). Two credentials are issued
through the real route; the first is used once from a non-loopback host so
`last_used_at` is a real value.

The grant half does NOT exist on main (story 02 builds it). The canvas adds it
from the lifecycle beat's decided shape (design/grant-lifecycle-beat.md:155):
`delegations: [{identity, state, grant_id, expires_at}]`.

Not collected by the suite (testpaths = tests). Run:
HOME=$(mktemp -d) uv run pytest -q -s -p no:cacheprovider <this file>
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from tests.unit.test_philo5_the_loop import Hub, hub  # noqa: F401  (fixture by name)
from tests.unit.test_philo5_the_loop_r2 import REMOTE_HOST, _agent_client

OUT = Path(__file__).parent / "fixtures" / "remote-wire.json"


def test_capture_remote_wire(hub: Hub) -> None:  # noqa: F811
    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    first = hub.client.post(
        "/api/settings/remote/credentials",
        json={"identity": "desk-agent", "palette": "DESK", "ttl_seconds": 43200},
    ).json()
    hub.client.post(
        "/api/settings/remote/credentials",
        json={"identity": "sweep-runner", "palette": "PROJECT", "ttl_seconds": 86400},
    )
    # A third credential with a 1 s TTL, read after it lapses and before any
    # authentication attempt: the real store keeps the row with active=false
    # (principals.py:244-250; the beat's matrix row 3, :147).
    hub.client.post(
        "/api/settings/remote/credentials",
        json={"identity": "review-agent", "palette": "PROJECT", "ttl_seconds": 1},
    )
    time.sleep(1.5)
    agent = _agent_client(hub, first["token"], REMOTE_HOST)
    used = agent.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                        "params": {"name": "meeting.list", "arguments": {}}})
    assert used.status_code == 200, used.text
    wire = hub.client.get("/api/settings/remote").json()
    assert [c["identity"] for c in wire["credentials"]] == ["desk-agent", "sweep-runner", "review-agent"]
    assert [c["active"] for c in wire["credentials"]] == [True, True, False]
    assert "delegations" not in wire  # the grant half is unbuilt on this tree
    OUT.write_text(json.dumps(wire, indent=2, sort_keys=True) + "\n")
    print(json.dumps(wire, indent=2, sort_keys=True))
