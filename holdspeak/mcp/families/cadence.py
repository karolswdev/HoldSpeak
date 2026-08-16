"""Cadence family — MCP tools for the CadenceService surface."""
from __future__ import annotations

import asyncio
from typing import Any

from holdspeak.config import Config
from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal
from holdspeak.services.cadence_service import CadenceService

_VALID_STATUSES = {"open", "closed", "killed"}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "cadence.status",
        "description": "Read Cadence engine status: enabled, pressure, loop counts, policy count.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.loops",
        "description": "List cadence loops. Omit include_terminal to exclude killed/closed loops.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_terminal": {
                    "type": "boolean",
                    "description": "Include killed/closed loops (default false).",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.get_loop",
        "description": "Get one cadence loop with its next action. MAY INVOKE MODEL when cadence intelligence is enabled; rides the admitted inference path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "loop_id": {"type": "string"},
            },
            "required": ["loop_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.brief",
        "description": "Read the deterministic Cadence morning brief.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.closeout",
        "description": "Read the current Cadence closeout recommendations.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.history",
        "description": "Read the Cadence nudge history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum nudges to return (default 50).",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.audit",
        "description": "Export the full Cadence audit trail.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.snooze",
        "description": "Snooze a cadence loop until a given time or for a number of hours.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "loop_id": {"type": "string"},
                "until": {
                    "type": "string",
                    "description": "ISO-8601 snooze-until timestamp.",
                },
                "hours": {
                    "type": "number",
                    "minimum": 0.1,
                    "description": "Hours to snooze (default 24, used when until is omitted).",
                },
            },
            "required": ["loop_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.set_status",
        "description": "Set the status of a cadence loop. The reply verb is intentionally absent from the sidecar: it requires the live agent-context pane delivery path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "loop_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["open", "closed", "killed"],
                    "description": "New loop status.",
                },
            },
            "required": ["loop_id", "status"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.run_now",
        "description": "Run a Cadence engine tick immediately. Local-only: projects loops, computes due nudges, returns them. May surface nudges ahead of schedule.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "cadence.apply_closeout",
        "description": "Apply closeout decisions to cadence loops. Each decision names a loop_id and an action; returns applied/skipped counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "decisions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "loop_id": {"type": "string"},
                            "action": {"type": "string"},
                        },
                        "required": ["loop_id", "action"],
                        "additionalProperties": False,
                    },
                    "maxItems": 100,
                    "description": "Closeout decisions to apply.",
                },
            },
            "required": ["decisions"],
            "additionalProperties": False,
        },
    },
]


def _run(coro: Any) -> Any:
    """Run an async coroutine synchronously; mirrors tools.py:411-416."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise ValueError("async MCP tools cannot execute inside an active event loop")


def _service() -> CadenceService:
    """Construct CadenceService per spec: db + config.cadence + kernel=None + observer."""
    return CadenceService(
        db=get_database(),
        config=Config.load().cadence,
        kernel=None,
        observer=get_observer(),
    )


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name == "cadence.status":
        return _service().status(principal)

    if name == "cadence.loops":
        include_terminal = arguments.get("include_terminal", False)
        return _service().list_loops(principal, include_terminal=bool(include_terminal))

    if name == "cadence.get_loop":
        loop_id = arguments.get("loop_id")
        if not isinstance(loop_id, str) or not loop_id.strip():
            raise ValueError("loop_id is required")
        return _run(_service().get_loop(principal, loop_id))

    if name == "cadence.brief":
        return _service().brief(principal)

    if name == "cadence.closeout":
        return _service().closeout(principal)

    if name == "cadence.history":
        kwargs: dict[str, Any] = {}
        if "limit" in arguments:
            kwargs["limit"] = int(arguments["limit"])
        return _service().history(principal, **kwargs)

    if name == "cadence.audit":
        return _service().audit(principal)

    if name == "cadence.snooze":
        loop_id = arguments.get("loop_id")
        if not isinstance(loop_id, str) or not loop_id.strip():
            raise ValueError("loop_id is required")
        payload: dict[str, Any] = {}
        if "until" in arguments:
            payload["until"] = arguments["until"]
        if "hours" in arguments:
            payload["hours"] = arguments["hours"]
        return _service().snooze(principal, loop_id, payload)

    if name == "cadence.set_status":
        loop_id = arguments.get("loop_id")
        if not isinstance(loop_id, str) or not loop_id.strip():
            raise ValueError("loop_id is required")
        status = arguments.get("status")
        if not isinstance(status, str) or status not in _VALID_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}")
        return _service().set_status(principal, loop_id, status)

    if name == "cadence.run_now":
        return _service().run_now(principal)

    if name == "cadence.apply_closeout":
        decisions = arguments.get("decisions")
        if not isinstance(decisions, list):
            raise ValueError("decisions is required and must be an array")
        return _service().apply_closeout(principal, {"decisions": decisions})

    raise LookupError(name)
