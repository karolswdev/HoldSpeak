"""The ``holdspeak setup`` terminal surface.

The command is a client of the running local hub. It uses the same owner
credential and owner-lock discovery as the MCP sidecar, so it never opens or
starts a second database.
"""
from __future__ import annotations

import json
from typing import Any

from .doctor import _setup_row_line


class SetupCommandError(RuntimeError):
    """A terminal setup request could not be completed by the local hub."""


def _tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call one Setup MCP tool through the existing local hub proxy."""
    from ..mcp.server import discover_hub, forward_to_hub, no_hub_message

    hub = discover_hub()
    if hub is None:
        raise SetupCommandError(no_hub_message())
    response = forward_to_hub(
        {
            "jsonrpc": "2.0",
            "id": f"holdspeak-setup-{name}",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        hub,
    )
    if not isinstance(response, dict):
        raise SetupCommandError("The HoldSpeak hub returned no Setup answer.")
    if isinstance(response.get("error"), dict):
        error = response["error"]
        raise SetupCommandError(str(error.get("message") or "The Setup request failed."))
    result = response.get("result")
    if not isinstance(result, dict):
        raise SetupCommandError("The HoldSpeak hub returned an invalid Setup answer.")
    content = result.get("content")
    if isinstance(content, list) and content and isinstance(content[0], dict):
        text = content[0].get("text")
        if isinstance(text, str):
            try:
                value = json.loads(text)
            except (TypeError, ValueError) as exc:
                raise SetupCommandError("The HoldSpeak hub returned invalid Setup data.") from exc
            if isinstance(value, dict):
                if result.get("isError"):
                    raise SetupCommandError(str(value.get("message") or value.get("error") or "The Setup request failed."))
                return value
    raise SetupCommandError("The HoldSpeak hub returned an invalid Setup answer.")


def _print_inventory(inventory: dict[str, Any]) -> None:
    print("HoldSpeak Setup")
    print("===============")
    rows = inventory.get("rows")
    if isinstance(rows, list) and rows:
        for row in rows:
            if isinstance(row, dict):
                print(f"- {_setup_row_line(row)}")
    else:
        print("- Setup inventory: Not found")


def _print_outcomes(answer: dict[str, Any]) -> None:
    results = answer.get("results")
    if not isinstance(results, list):
        return
    print()
    print("Use everything found")
    print("====================")
    for item in results:
        if isinstance(item, dict):
            print(f"- {_setup_row_line(item)}")


def run_setup_command(args: object) -> int:
    """Print the shared inventory, optionally pressing all actionable rows."""
    try:
        inventory = _tool_call("setup.status", {})
        _print_inventory(inventory)
        if bool(getattr(args, "yes", False)):
            answer = _tool_call("setup.use", {"id": "all"})
            _print_outcomes(answer)
            if str(answer.get("state") or "").lower() == "does_not_work":
                return 1
    except SetupCommandError as exc:
        print(f"Setup: Does not work · {exc}")
        return 1
    return 0


__all__ = ["run_setup_command"]
