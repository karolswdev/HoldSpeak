"""PROBE (b), PHILO-7-02 lifecycle beat: a reissue through the REAL settings
route keeps the principal identity, mints a new credential id, and the old
token is refused (401) while the new one works.

Real code paths: the real hub (`MeetingWebServer`) over an isolated database,
booted by the Phase 5 fence fixture (tests/unit/test_philo5_the_loop.py:116-150);
`POST /api/settings/remote/credentials` (holdspeak/web/routes/mcp_http.py:270-311);
`AgentCredentialStore.issue` (holdspeak/principals.py:136-173, `self.revoke` at :149).
Run: HOME=$(mktemp -d) uv run pytest -q -s <this file>
"""
from __future__ import annotations

from tests.unit.test_philo5_the_loop import Hub, hub  # noqa: F401  (fixture by name)
from tests.unit.test_philo5_the_loop_r2 import REMOTE_HOST, _agent_client


def _list(client) -> int:
    return client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                          "params": {"name": "meeting.list", "arguments": {}}}).status_code


def test_probe_b_reissue_keeps_identity_and_401s_the_old_token(hub: Hub) -> None:  # noqa: F811
    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    first = hub.client.post("/api/settings/remote/credentials",
                            json={"identity": "probe-desk-agent", "palette": "DESK"}).json()
    old = _agent_client(hub, first["token"], REMOTE_HOST)
    print(f"\nissue #1 -> id={first['id']} identity={first['identity']}; old token /api/mcp -> {_list(old)}")
    second = hub.client.post("/api/settings/remote/credentials",
                             json={"identity": "probe-desk-agent", "palette": "DESK"}).json()
    new = _agent_client(hub, second["token"], REMOTE_HOST)
    old_status, new_status = _list(old), _list(new)
    print(f"issue #2 (reissue) -> id={second['id']} identity={second['identity']}")
    print(f"after reissue: old token /api/mcp -> {old_status}; new token /api/mcp -> {new_status}")
    listed = hub.client.get("/api/settings/remote").json()
    rows = [(c["id"], c["identity"]) for c in listed.get("credentials", [])]
    print(f"credential ledger rows after reissue: {rows}")
    assert first["identity"] == second["identity"] == "probe-desk-agent"
    assert first["id"] != second["id"]
    assert old_status == 401 and new_status == 200
