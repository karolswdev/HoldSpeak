"""Producer-backed native Terminals inventory and route contract."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.principals import PrincipalRight, required_right
from holdspeak.services.delivery_service import DeliveryService
from holdspeak.services.terminal_workspace import TerminalWorkspaceService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_terminal import build_delivery_terminal_router


class IdentityTmux:
    def __init__(self) -> None:
        self.pane = {
            "pane_id": "%5",
            "pane_pid": "501",
            "pane_tty": "/dev/ttys001",
            "current_path": "/work/one",
            "session_id": "$1",
            "window_id": "@1",
            "window_index": "0",
            "pane_index": "0",
            "command": "bash",
            "title": "one",
            "active": "1",
            "pane_start_command": "bash --norc",
            "socket_path": "/tmp/tmux-501/default",
            "server_pid": "500",
        }

    def __call__(self, argv, cwd=None):
        if argv[1] != "display-message":
            raise AssertionError(f"unexpected tmux call: {argv}")
        pane = self.pane
        fields = (
            pane["pane_id"],
            pane["pane_pid"],
            pane["pane_tty"],
            pane["current_path"],
            pane["session_id"],
            pane["window_id"],
            pane["window_index"],
            pane["pane_index"],
            pane["command"],
            pane["title"],
            pane["active"],
            pane["pane_start_command"],
            pane["socket_path"],
            pane["server_pid"],
        )
        return SimpleNamespace(returncode=0, stdout="\t".join(fields) + "\n", stderr="")


def _pane(tmux: IdentityTmux) -> dict[str, str | bool]:
    return {
        "pane_id": tmux.pane["pane_id"],
        "session": "main",
        "window": "0",
        "pane_index": tmux.pane["pane_index"],
        "command": tmux.pane["command"],
        "title": tmux.pane["title"],
        "active": True,
        "pane_pid": tmux.pane["pane_pid"],
        "pane_tty": tmux.pane["pane_tty"],
        "current_path": tmux.pane["current_path"],
        "session_id": tmux.pane["session_id"],
        "window_id": tmux.pane["window_id"],
        "pane_start_command": tmux.pane["pane_start_command"],
        "socket_path": tmux.pane["socket_path"],
        "server_pid": tmux.pane["server_pid"],
        "fingerprint": "sha256:first",
    }


def test_inventory_correlates_hook_state_and_keeps_unknown_shell_live() -> None:
    tmux = IdentityTmux()
    pane = _pane(tmux)
    pane["pane_index"] = 0
    hooks = [
        SimpleNamespace(
            agent="codex",
            session_id="session-one",
            tmux_pane="%5",
            tmux_session="main",
            tmux_window="0",
            tmux_pane_index=0,
            project_name="Architecture",
            lifecycle="waiting",
            cwd="/work/one",
            tmux_pane_current_path="/work/one",
        )
    ]
    targets = TerminalTargetRegistry(runner=tmux)
    service = TerminalWorkspaceService(
        targets,
        pane_loader=lambda: {"status": "ok", "panes": [pane]},
        session_loader=lambda: hooks,
    )
    result = service.discover()
    assert result["status"] == "ok"
    row = result["sessions"][0]
    assert row["key"] == "codex:session-one"
    assert row["agent"] == "codex"
    assert row["state"] == "waiting"
    assert row["label"] == "codex · Architecture · main:0.0"
    assert row["current_path"] == "/work/one"
    assert row["target"]["node_id"] == "local"

    # A pane with no hook is still discoverable, but is never called an agent.
    hooks.clear()
    pane["title"] = "shell"
    result = service.discover()
    row = result["sessions"][0]
    assert row["key"] == "pane:%5"
    assert row["agent"] == "pane"
    assert row["state"] == "live"
    assert row["label"] == "main:0.0"


def test_inventory_rejects_conflicting_or_ended_hook_for_live_pane() -> None:
    tmux = IdentityTmux()
    pane = _pane(tmux)
    targets = TerminalTargetRegistry(runner=tmux)
    service = TerminalWorkspaceService(
        targets,
        pane_loader=lambda: {"status": "ok", "panes": [pane]},
        session_loader=lambda: [
            SimpleNamespace(
                agent="codex",
                session_id="conflicting",
                tmux_pane="%5",
                tmux_session="other",
                tmux_window="9",
                tmux_pane_index="4",
                lifecycle="waiting",
                updated_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            ),
            SimpleNamespace(
                agent="claude",
                session_id="ended",
                tmux_pane="%5",
                tmux_session="main",
                tmux_window="0",
                tmux_pane_index="0",
                lifecycle="ended",
                updated_at="2026-10-30T13:00:00Z",
            ),
        ],
    )
    row = service.discover()["sessions"][0]
    assert row["key"] == "pane:%5"
    assert row["agent"] == "pane"
    assert row["state"] == "live"


def test_inventory_rejects_an_effectively_dead_agent_record_for_live_pane() -> None:
    from holdspeak.agent_context import AgentSession

    tmux = IdentityTmux()
    pane = _pane(tmux)
    old = AgentSession(
        agent="codex",
        session_id="old",
        cwd="/work/one",
        updated_at=(datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
        hook_event_name="Stop",
        tmux_pane="%5",
        tmux_session="main",
        tmux_window="0",
        tmux_pane_index="0",
        lifecycle="waiting",
    )
    service = TerminalWorkspaceService(
        TerminalTargetRegistry(runner=tmux),
        pane_loader=lambda: {"status": "ok", "panes": [pane]},
        session_loader=lambda: [old],
    )
    row = service.discover()["sessions"][0]
    assert row["key"] == "pane:%5"
    assert row["agent"] == "pane"
    assert row["state"] == "live"


def test_inventory_id_ignores_mutable_labels_but_changes_for_process_identity() -> None:
    tmux = IdentityTmux()
    pane = _pane(tmux)
    targets = TerminalTargetRegistry(runner=tmux)
    service = TerminalWorkspaceService(
        targets,
        pane_loader=lambda: {"status": "ok", "panes": [pane]},
        session_loader=lambda: [],
    )
    first = service.discover()["sessions"][0]

    pane["current_path"] = "/work/two"
    pane["command"] = "zsh"
    pane["title"] = "renamed"
    tmux.pane["current_path"] = "/work/two"
    tmux.pane["command"] = "zsh"
    tmux.pane["title"] = "renamed"
    second = service.discover()["sessions"][0]
    assert second["id"] == first["id"]
    assert second["current_path"] == "/work/two"

    old_generation = first["target"]["target_generation"]
    pane["pane_pid"] = "777"
    tmux.pane["pane_pid"] = "777"
    pane["fingerprint"] = "sha256:second"
    changed = service.discover()["sessions"][0]
    assert changed["id"] != first["id"]
    assert changed["target"]["target_generation"] != old_generation
    refused = targets.verify(
        first["target"]["target_id"], old_generation
    )
    assert refused["status"] == "generation_mismatch"


def test_sessions_route_uses_injected_workspace_service() -> None:
    tmux = IdentityTmux()
    pane = _pane(tmux)
    targets = TerminalTargetRegistry(runner=tmux)
    workspace = TerminalWorkspaceService(
        targets,
        pane_loader=lambda: {"status": "ok", "panes": [pane]},
        session_loader=lambda: [],
    )
    app = FastAPI()
    app.include_router(
        build_delivery_terminal_router(
            WebContext(get_state=lambda: {}),
            targets=targets,
            workspace=workspace,
        )
    )
    response = TestClient(app).get("/api/delivery/terminal/sessions")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["sessions"][0]["pane_id"] == "%5"
    assert required_right("GET", "/api/delivery/terminal/sessions") is PrincipalRight.OWNER


def test_delivery_service_composes_workspace_with_shared_targets() -> None:
    targets = object()
    service = DeliveryService(None)
    workspace = service.terminal_workspace_service(targets=targets, local_node_id="node-a")
    assert workspace.targets is targets
    assert workspace.local_node_id == "node-a"


def test_sessions_route_delegates_workspace_composition_and_shared_targets() -> None:
    tmux = IdentityTmux()
    targets = TerminalTargetRegistry(runner=tmux)
    seen: dict[str, object] = {}

    class ComposedDelivery:
        def terminal_workspace_service(self, *, targets, local_node_id):
            seen.update({"targets": targets, "local_node_id": local_node_id})
            return TerminalWorkspaceService(
                targets,
                local_node_id=local_node_id,
                pane_loader=lambda: {"status": "ok", "panes": [_pane(tmux)]},
                session_loader=lambda: [],
            )

    app = FastAPI()
    app.include_router(
        build_delivery_terminal_router(
            WebContext(get_state=lambda: {}, delivery_service=ComposedDelivery()),
            targets=targets,
            local_node_id="node-a",
        )
    )
    response = TestClient(app).get("/api/delivery/terminal/sessions")
    assert response.status_code == 200
    assert response.json()["sessions"][0]["target"]["node_id"] == "node-a"
    assert seen == {"targets": targets, "local_node_id": "node-a"}


def test_missing_tmux_is_typed_and_empty() -> None:
    targets = TerminalTargetRegistry(resolver=lambda _ref, runner=None: {"status": "tmux_absent"})
    service = TerminalWorkspaceService(
        targets, pane_loader=lambda: {"status": "tmux_absent", "panes": []}
    )
    assert service.discover() == {"status": "tmux_absent", "sessions": []}
