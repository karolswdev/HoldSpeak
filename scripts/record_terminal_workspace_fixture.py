#!/usr/bin/env python3
"""Record the native Terminals inventory through its real service boundary.

This producer uses injected tmux/session seams; it never contacts the owner's
tmux server, HOME, database, agent, or provider. The resulting JSON is for UI
fixture tests only and is not a hand-authored API answer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.services.terminal_workspace import TerminalWorkspaceService


class FixtureTmux:
    def __init__(self) -> None:
        self.panes = [
            {
                "pane_id": "%5", "session": "review", "window": "0",
                "pane_index": "0", "pane_pid": "501", "pane_tty": "/dev/ttys001",
                "current_path": "/work/review", "session_id": "$1", "window_id": "@1",
                "command": "bash", "title": "review", "active": "1",
                "pane_start_command": "bash --norc", "socket_path": "/tmp/hs-fixture/default",
                "server_pid": "500", "fingerprint": "sha256:fixture-review",
            },
            {
                "pane_id": "%8", "session": "scratch", "window": "0",
                "pane_index": "0", "pane_pid": "801", "pane_tty": "/dev/ttys002",
                "current_path": "/work/scratch", "session_id": "$2", "window_id": "@2",
                "command": "zsh", "title": "scratch", "active": "0",
                "pane_start_command": "zsh", "socket_path": "/tmp/hs-fixture/default",
                "server_pid": "500", "fingerprint": "sha256:fixture-scratch",
            },
        ]

    def identity(self, pane_id: str) -> dict[str, str]:
        return next(pane for pane in self.panes if pane["pane_id"] == pane_id)

    def __call__(self, argv, cwd=None):
        target = argv[argv.index("-t") + 1]
        pane_id = target if target.startswith("%") else target.split(":", 1)[-1]
        pane = self.identity(pane_id)
        fields = (
            pane["pane_id"], pane["pane_pid"], pane["pane_tty"], pane["current_path"],
            pane["session_id"], pane["window_id"], pane["window"], pane["pane_index"],
            pane["command"], pane["title"], pane["active"], pane["pane_start_command"],
            pane["socket_path"], pane["server_pid"],
        )
        return SimpleNamespace(returncode=0, stdout="\t".join(fields) + "\n", stderr="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("web/src/desk/terminals/__tests__/fixtures/sessions.recorded.json"),
    )
    args = parser.parse_args()
    tmux = FixtureTmux()

    def panes():
        return {"status": "ok", "panes": [dict(pane) for pane in tmux.panes]}

    hooks = [
        SimpleNamespace(
            agent="codex", session_id="fixture-agent", tmux_pane="%5",
            tmux_session="review", tmux_window="0", tmux_pane_index="0",
            project_name="Review", lifecycle="working", cwd="/work/review",
            tmux_pane_current_path="/work/review",
        )
    ]
    targets = TerminalTargetRegistry(runner=tmux)
    payload = TerminalWorkspaceService(
        targets, pane_loader=panes, session_loader=lambda: hooks
    ).discover()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
