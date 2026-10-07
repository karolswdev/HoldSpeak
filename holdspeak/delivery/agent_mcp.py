"""Conductor K6: every agent HoldSpeak launches gets the HoldSpeak MCP.

Owner, 2026-10-06: "the agent we spin up here - do we inject him with our
HoldSpeak MCP? We certainly should, because it could do a lot of very
meaningful things for us with those tools at its disposal."

The launch spawn issues a launch-bound agent credential (CONDUCTOR palette,
``coder_factory.spawn``) into the tmux session's environment as
``HOLDSPEAK_AGENT_CREDENTIAL``, beside ``HOLDSPEAK_HUB_URL``. This module
turns that into the agent's MCP server ``holdspeak``:

* Claude Code: ``--mcp-config <file>``. The file names the two environment
  variables (Claude Code expands ``${VAR}`` in ``url`` and ``headers``), so no
  token is ever in the file, in argv or in a log. The file is mode 0600 and
  per launch; cleanup removes it.
* Codex: ``-c mcp_servers.holdspeak.url=...`` and
  ``-c mcp_servers.holdspeak.bearer_token_env_var=HOLDSPEAK_AGENT_CREDENTIAL``
  (Codex's streamable HTTP server reads the token from that variable).

Pre-approval follows the Control mode read at launch: in Normal and YOLO the
``holdspeak`` tools are allowed without a prompt in the agent's pane; in
Secure they are not pre-approved, so each call asks in the pane. The hub's
CONDUCTOR palette decides what the agent can call in every mode.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

SERVER_NAME = "holdspeak"
CREDENTIAL_ENV = "HOLDSPEAK_AGENT_CREDENTIAL"
HUB_URL_ENV = "HOLDSPEAK_HUB_URL"
#: Claude Code's permission rule for every tool of one MCP server.
CLAUDE_ALLOW_RULE = f"mcp__{SERVER_NAME}"
SECURE_MODE = "safe"


def mcp_config_dir() -> Path:
    """Beside the spawn settings (``coder_gate.write_spawn_settings``)."""
    return Path.home() / ".holdspeak" / "gate-spawn-settings" / "mcp"


def mcp_config_path(launch_id: str, directory: Optional[Path] = None) -> Path:
    return (directory or mcp_config_dir()) / f"{launch_id}.json"


def claude_mcp_document() -> dict[str, Any]:
    """The ``--mcp-config`` document: the two variables, never their values."""
    return {
        "mcpServers": {
            SERVER_NAME: {
                "type": "http",
                "url": "${" + HUB_URL_ENV + "}/api/mcp",
                "headers": {"Authorization": "Bearer ${" + CREDENTIAL_ENV + "}"},
            }
        }
    }


def write_mcp_config(launch_id: str, directory: Optional[Path] = None) -> Path:
    """Write the launch's ``--mcp-config`` file, mode 0600 from creation."""
    target = mcp_config_path(launch_id, directory)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(target.parent, 0o700)
    except OSError:
        pass
    data = (json.dumps(claude_mcp_document(), indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(target, 0o600)
    return target


def remove_mcp_config(launch_id: str, directory: Optional[Path] = None) -> bool:
    """Remove the launch's ``--mcp-config`` file (idempotent)."""
    clean = str(launch_id or "").strip()
    if not clean:
        return False
    try:
        mcp_config_path(clean, directory).unlink()
        return True
    except OSError:
        return False


def normalized_mode(mode: Any) -> str:
    from ..product_language import control_mode_wire

    try:
        return control_mode_wire(str(mode or "yolo"))
    except Exception:
        return "yolo"


def pre_approved(mode: Any) -> bool:
    """Normal and YOLO pre-approve the ``holdspeak`` tools; Secure does not."""
    return normalized_mode(mode) != SECURE_MODE


def claude_args(config_path: Path, mode: Any, *, allowed: tuple[str, ...] = ()) -> list[str]:
    """The Claude Code flags: the server, and one ``--allowedTools`` list.

    ``allowed`` carries tools the launch already allows (the gated path's
    ``Bash``), so the flag is given once."""
    tools = list(allowed)
    if pre_approved(mode):
        tools.append(CLAUDE_ALLOW_RULE)
    args = ["--mcp-config", str(config_path)]
    if tools:
        args += ["--allowedTools", *tools]
    return args


def codex_args(hub_url: str, mode: Any) -> list[str]:
    """The Codex flags: a streamable HTTP server with its bearer variable."""
    url = str(hub_url or "").rstrip("/") + "/api/mcp"
    key = f"mcp_servers.{SERVER_NAME}"
    args = [
        "-c", f"{key}.url={json.dumps(url)}",
        "-c", f"{key}.bearer_token_env_var={json.dumps(CREDENTIAL_ENV)}",
    ]
    if pre_approved(mode):
        args += ["-c", f'{key}.default_tools_approval_mode="approve"']
    return args


#: Claude Code's permission mode that accepts file edits in its working
#: folder (the launch's worktree) with no prompt.
CLAUDE_EDIT_MODE = "acceptEdits"


def claude_permission_args(mode: Any, argv: list[str]) -> list[str]:
    """``--permission-mode acceptEdits`` in Normal and YOLO (Conductor R1).

    Without it every Edit of a launched Claude asked in the pane, a TO
    APPROVE row for each file change, whatever the Control mode. Edits stay
    inside the worktree (Claude Code accepts edits in its working folder
    only); Bash stays with the tool gate. Secure gets nothing: each edit
    asks. A permission mode the launch already names is kept."""
    if not pre_approved(mode) or "--permission-mode" in argv:
        return []
    return ["--permission-mode", CLAUDE_EDIT_MODE]


#: Codex 0.159: run the enabled hooks of ``$CODEX_HOME/hooks.json`` with no
#: persisted hook trust, for this one process (nothing is written).
CODEX_HOOK_TRUST_FLAG = "--dangerously-bypass-hook-trust"


def codex_launch_args(worktree_path: str) -> list[str]:
    """The Codex flags that let a launch start with no screen in the way.

    * ``-c projects={"<worktree>"={trust_level="trusted"}}``: the launch's own
      worktree is trusted for this process, so Codex does not ask "Trust this
      folder?" (an inline table: Codex 0.159 does not read the dotted
      ``projects."<path>".trust_level`` form from ``-c``). Nothing is written
      to the owner's ``config.toml``.
    * :data:`CODEX_HOOK_TRUST_FLAG`: Codex runs a new or changed hook only
      after the owner reviews it in the TUI ("Hooks need review"); the K1
      install changes the hook file, so a launch would stop there and its
      rider hooks would never report. The flag holds for this process only.
    """
    path = json.dumps(os.path.realpath(str(worktree_path)))
    return ["-c", f'projects={{{path}={{trust_level="trusted"}}}}', CODEX_HOOK_TRUST_FLAG]


def config_control_mode() -> str:
    from ..config import Config

    try:
        return str(Config.load().control_mode or "yolo")
    except Exception:
        return "yolo"


__all__ = [
    "CLAUDE_ALLOW_RULE",
    "CLAUDE_EDIT_MODE",
    "CODEX_HOOK_TRUST_FLAG",
    "CREDENTIAL_ENV",
    "HUB_URL_ENV",
    "SERVER_NAME",
    "claude_args",
    "claude_mcp_document",
    "claude_permission_args",
    "codex_args",
    "codex_launch_args",
    "config_control_mode",
    "mcp_config_path",
    "pre_approved",
    "remove_mcp_config",
    "write_mcp_config",
]
