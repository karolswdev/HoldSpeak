"""HS-106-02: credential-derived owner, agent, and node principals."""
from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import holdspeak.db as hsdb
from holdspeak import coder_factory, coder_steering
from holdspeak.db import Database, reset_database
from holdspeak.delivery.node_link import NodeTokenStore
from holdspeak.principals import AgentCredentialStore, agent_credentials
from holdspeak.web_auth import websocket_auth_protocol
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


def _server(tmp_path: Path, monkeypatch) -> tuple[MeetingWebServer, TestClient, Database]:
    reset_database()
    db = Database(tmp_path / "principals.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    callbacks = WebRuntimeCallbacks(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={"id": "principal-test"}),
    )
    server = MeetingWebServer(callbacks, host="127.0.0.1", auth_token="owner-secret")
    return server, TestClient(server.app), db


def test_agent_identity_is_derived_and_owner_only_rights_refuse_by_name(
    tmp_path: Path, monkeypatch
) -> None:
    server, owner, db = _server(tmp_path, monkeypatch)
    issued = owner.post(
        "/api/principals/agents", json={"identity": "claude:real-session"}
    )
    assert issued.status_code == 201
    token = issued.json()["credential"]
    agent = TestClient(server.app)
    agent.headers.pop("x-holdspeak-token", None)
    agent.headers["Authorization"] = f"Bearer {token}"

    proposal = agent.post(
        "/api/gate/proposals",
        json={
            "id": "principal-proposal",
            "session_key": "caller-claims-owner",
            "agent": "owner",
            "tool": "Bash",
            "args_sha256": "a" * 64,
            "cwd": str(tmp_path),
            "ttl_seconds": 60,
        },
    )
    assert proposal.status_code == 200
    row = db.gate.get("principal-proposal")
    assert row is not None
    assert row.session_key == "claude:real-session"
    assert row.agent == "agent"
    assert agent.get("/api/gate/proposals/principal-proposal").status_code == 200

    refused = agent.post(
        "/api/gate/proposals/principal-proposal/decide",
        json={"decision": "approved", "actor": "owner"},
    )
    assert refused.status_code == 403
    assert refused.json() == {
        "success": False,
        "error": "principal_right_required",
        "principal": "agent",
        "principal_identity": "claude:real-session",
        "missing_right": "decide",
    }
    posture = agent.put(
        "/api/authority/control-mode", json={"control_mode": "yolo"}
    )
    assert posture.status_code == 403
    assert posture.json()["principal"] == "agent"
    assert posture.json()["missing_right"] == "posture"

    decided = owner.post(
        "/api/gate/proposals/principal-proposal/decide",
        json={"decision": "denied", "actor": "caller-claims-agent"},
    )
    assert decided.status_code == 200
    assert db.gate.get("principal-proposal").decided_by == "owner-session"

    ended = agent.delete("/api/principals/self")
    assert ended.status_code == 200
    assert ended.json()["revoked"] is True
    stale = agent.get("/api/gate/proposals/principal-proposal")
    assert stale.status_code == 401
    assert stale.json()["principal"] == "none"
    replacement = owner.post(
        "/api/principals/agents", json={"identity": "claude:real-session"}
    ).json()["credential"]
    assert replacement != token
    agent_credentials.revoke("claude:real-session")


def test_http_and_websocket_share_agent_principal(tmp_path: Path, monkeypatch) -> None:
    server, owner, _db = _server(tmp_path, monkeypatch)
    token = owner.post(
        "/api/principals/agents", json={"identity": "claude:ws-session"}
    ).json()["credential"]
    anonymous = TestClient(server.app)
    anonymous.headers.pop("x-holdspeak-token", None)

    with pytest.raises(WebSocketDisconnect) as refused:
        with anonymous.websocket_connect(
            "/ws",
            subprotocols=["holdspeak.v1", websocket_auth_protocol(token)],
        ):
            pass
    assert refused.value.reason == "principal=agent missing_right=owner"


def test_node_credential_derives_node_not_owner(tmp_path: Path, monkeypatch) -> None:
    server, _owner, _db = _server(tmp_path, monkeypatch)
    store = NodeTokenStore(tmp_path / "nodes.json")
    node_id, token = store.create("workstation")
    server.app.state.node_token_store = store
    node = TestClient(server.app)
    node.headers.pop("x-holdspeak-token", None)
    refused = node.get(
        "/api/state", headers={"X-HoldSpeak-Node-Token": token}
    )
    assert refused.status_code == 403
    assert refused.json()["principal"] == "node"
    assert refused.json()["principal_identity"] == node_id
    assert refused.json()["missing_right"] == "owner"


def test_agent_credential_expires() -> None:
    now = [10.0]
    store = AgentCredentialStore(clock=lambda: now[0])
    credential = store.issue("claude:expiring", ttl_seconds=5)
    assert store.derive(credential.token).identity == "claude:expiring"
    now[0] = 15.0
    assert store.derive(credential.token) is None


def test_spawn_kill_respawn_invalidates_old_credential(monkeypatch) -> None:
    calls: list[list[str]] = []

    def runner(argv: list[str]):
        calls.append(argv)
        if argv[1] == "list-panes":
            return type("Done", (), {"returncode": 0, "stdout": "%principal", "stderr": ""})()
        return type("Done", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    first = coder_factory.spawn("principal-life", runner=runner, audit=lambda **_: 1)
    assert first["status"] == "spawned"
    first_argv = calls[0]
    old_token = next(
        value.split("=", 1)[1]
        for value in first_argv
        if value.startswith("HOLDSPEAK_AGENT_CREDENTIAL=")
    )
    assert agent_credentials.derive(old_token).identity == "agent:tmux:principal-life"

    monkeypatch.setattr(
        coder_steering,
        "require_grant",
        lambda *args, **kwargs: {"status": "ok", "pane_id": "%principal"},
    )
    monkeypatch.setattr(coder_steering, "disarm", lambda _key: True)
    killed = coder_factory.kill(
        "claude:ignored-body-identity",
        current_target="session:principal-life",
        runner=runner,
        audit=lambda **_: 2,
    )
    assert killed["status"] == "killed"
    assert agent_credentials.derive(old_token) is None

    calls.clear()
    second = coder_factory.spawn("principal-life", runner=runner, audit=lambda **_: 3)
    assert second["status"] == "spawned"
    new_token = next(
        value.split("=", 1)[1]
        for value in calls[0]
        if value.startswith("HOLDSPEAK_AGENT_CREDENTIAL=")
    )
    assert new_token != old_token
    assert agent_credentials.derive(new_token).identity == "agent:tmux:principal-life"
    agent_credentials.revoke("agent:tmux:principal-life")


def test_loopback_classifier_has_no_request_authority_callers() -> None:
    root = Path(__file__).parents[2] / "holdspeak"
    found: set[tuple[str, str]] = set()

    for source_path in root.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        stack: list[str] = []

        class Visitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Call(self, node: ast.Call) -> None:
                name = node.func.attr if isinstance(node.func, ast.Attribute) else (
                    node.func.id if isinstance(node.func, ast.Name) else ""
                )
                if name == "is_loopback_host":
                    found.add((str(source_path.relative_to(root)), stack[-1] if stack else ""))
                self.generic_visit(node)

        Visitor().visit(tree)

    assert found == {
        ("web_auth.py", "nonloopback_bind_blocked"),
        ("mesh.py", "should_advertise"),
        ("web/routes/mcp_http.py", "mcp_http_endpoint"),  # HS-174 C5: the per-route guard refusing OWNER off-loopback (XI:4); classifies, never grants
        ("web_server.py", "__init__"),
        ("web_server.py", "start"),
        ("web_server.py", "_start_mesh_advertising"),
        ("web_server.py", "_create_app"),
    }
