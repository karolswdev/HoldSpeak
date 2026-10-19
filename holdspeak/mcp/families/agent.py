"""Agent family: Hand to agent over MCP (docs/internal/CONDUCTOR.md, step 2).

``agent.hand`` is the declared operation of the same name
(``holdspeak/agent_operations.py``), an egress row in the authority census
(``mcp/tool_authority.py``): it starts a coding agent that runs on a cloud
model and sends it a brief built from the owner's desk. A thread never
offers it; the owner's own MCP client calls it as a press.
"""
from __future__ import annotations

from typing import Any

from holdspeak.principals import Principal


def _tool() -> dict[str, Any]:
    """``agent.hand`` IS its declared operation: one schema, one set of words."""
    import copy

    from holdspeak.agent_operations import AGENT_HAND as descriptor

    schema = copy.deepcopy(dict(descriptor.args_schema))
    schema["$id"] = f"holdspeak://mcp/agent.hand@{descriptor.version}"
    return {"name": "agent.hand", "description": descriptor.description, "inputSchema": schema}


_LAUNCH_ID = {"type": "string", "description": "The helper's launch id (from agent.start_helper)."}


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


#: Betterment AG11: agents that work together (a launched agent and its one
#: helper; services/agent_helpers.py has herdr's rules).
HELPER_TOOLS: list[dict[str, Any]] = [
    {"name": "agent.start_helper",
     "description": "Start your one helper agent (a reviewer, a test runner) on your item, in its own worktree "
                    "on a branch from yours. Secure mode asks the owner for one Allow press.",
     "inputSchema": _schema({
         "instruction": {"type": "string", "description": "What the helper should do."},
         "profile": {"type": "string", "description": "claude-default, codex-default or pi-default."},
     }, ["instruction"])},
    {"name": "agent.prompt",
     "description": "Send text to your helper; with wait, also wait until it is done, asks or is quiet, in one "
                    "request. Refuses a helper that waits for an answer (agent_blocked); says "
                    "agent_prompt_stalled when nothing moves in 5 s.",
     "inputSchema": _schema({
         "launch_id": _LAUNCH_ID, "text": {"type": "string"},
         "wait": {"type": "boolean"}, "timeout_s": {"type": "number", "minimum": 1, "maximum": 600},
     }, ["launch_id", "text"])},
    {"name": "agent.wait",
     "description": "Wait until your helper is done, asks or is quiet (pinned to its session).",
     "inputSchema": _schema({"launch_id": _LAUNCH_ID, "timeout_s": {"type": "number", "minimum": 1, "maximum": 600}},
                            ["launch_id"])},
    {"name": "agent.read",
     "description": "Read your helper: its state, its last words and the last lines of its screen.",
     "inputSchema": _schema({"launch_id": _LAUNCH_ID, "lines": {"type": "integer", "minimum": 1, "maximum": 200}},
                            ["launch_id"])},
    {"name": "agent.answer",
     "description": "Answer a question your helper asks (text or a choice number). Never an approval prompt.",
     "inputSchema": _schema({"launch_id": _LAUNCH_ID, "text": {"type": "string"}}, ["launch_id", "text"])},
]

TOOLS: list[dict[str, Any]] = [_tool(), *HELPER_TOOLS]
HELPER_NAMES = frozenset(t["name"] for t in HELPER_TOOLS)


def _helpers(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or, service as runtime_service
    from holdspeak.services import agent_helpers
    from holdspeak.services.agent_hand_service import _config_control_mode, default_agent_hand_service
    from holdspeak.services.conductor_launch import launch_id_of

    caller = launch_id_of(principal)
    if caller is None:
        raise agent_helpers.HelperRefused("launch_only", "only a launched agent has helpers", 403)
    db = db_or(get_database)
    args = dict(arguments or {})
    if name == "agent.start_helper":
        service = runtime_service("agent_hand_service", lambda: default_agent_hand_service(db))
        return agent_helpers.start_helper(
            caller, instruction=str(args.get("instruction") or ""), profile=args.get("profile"),
            hand_service=service, control_mode=_config_control_mode,
        )
    launch_id = str(args.get("launch_id") or "")
    if name == "agent.prompt":
        return agent_helpers.prompt(db, caller, launch_id, str(args.get("text") or ""),
                                    wait=bool(args.get("wait")), timeout_s=float(args.get("timeout_s") or 300))
    if name == "agent.wait":
        return agent_helpers.wait_for(db, caller, launch_id, timeout_s=float(args.get("timeout_s") or 300))
    if name == "agent.read":
        return agent_helpers.read(db, caller, launch_id, lines=int(args.get("lines") or 40))
    return agent_helpers.answer(db, caller, launch_id, str(args.get("text") or ""))


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    if name in HELPER_NAMES:
        return _helpers(name, arguments, principal)
    if name != "agent.hand":
        raise LookupError(name)
    from holdspeak import operations
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or, service as runtime_service
    from holdspeak.services.agent_hand_service import default_agent_hand_service

    ops = operations.for_runtime(
        agent_hand_service=lambda: runtime_service(
            "agent_hand_service", lambda: default_agent_hand_service(db_or(get_database))
        ),
    )
    return ops.invoke(principal, "agent.hand", dict(arguments or {}))


__all__ = ["TOOLS", "dispatch"]
