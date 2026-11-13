"""The verbs of the coder sessions and their steering (``/api/coders``) on ``CoderService``, on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one verb
once: its call, its HTTP method and path, and its MCP tool schema.
``web/routes/system/coders.py`` produces the routes and ``mcp/families/declared.py`` the
tools from these rows, both through ``OperationRegistry.invoke``.

A read is ``thread="evidence_read"`` and stays MCP and HTTP only (the seeded
thread palettes do not grow, ``services/thread_modes.py``); a write is
``thread="effect_proposal"``. A launched agent reads these reads and never
calls these writes (``services/conductor_launch.py`` derives both rules from
the rows). Imported only through ``holdspeak.operations`` (it imports this module).

Every write is the owner's press. ``status`` keeps its runtime/device inputs
held by HTTP. ``steer`` and ``keys`` keep the hub's process-input service held.
``spawn``, ``rename`` and ``panes`` stay HTTP-only: they operate on the owner's
live tmux sessions. The relay rows are HTTP-only owner operations because the
hub forwards the configured remote credential. None widens a launch rule.

"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional
from holdspeak.held_arguments import held_arguments, hidden, text, target, prompt_facts
from holdspeak.services.held_authority import permission_facts

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + (
    "owner_required",
    "CoderRefused: a named code with its HTTP status and answer (invalid_key, unknown_session, stale_session, "
    "no_pane, wait_not_current, grounding_over_cap, a refused delivery)",
    "ValidationError",
)
_ID = {"type": "string", "minLength": 1}
_TARGET = {"agent": {"type": "string", "description": "The agent name (claude, codex)."},
           "session_id": {"type": "string", "description": "The session id of that agent."}}
_HELD = ("process_input",)


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        write: bool = False, tool: bool = True, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = (), held: tuple[str, ...] = (), authority: str = "work",
        blocking_io: bool = False, owner_only: bool = False, status: int = 200, result: str = "the CoderService answer", facts: dict[str, Any] | None = None) -> OperationDescriptor:
    """One verb of ``coder_service``; its tool (when it has one) requires the path's ids and ``required``."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {**dict(facts or {}), "type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result=result, refusals=_REFUSALS,
        completion="synchronous; a steering write is one intel_status coder frame on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()),
        service="coder_service", method=method, held=held, owner_only=owner_only or write, owner_press=write, blocking_io=blocking_io,
        call=call, http=http, http_status=status, handler=handler, tool_schema=schema if tool else None,
        authority="authority" if write and authority == "work" else authority,
        thread=("effect_proposal" if write else "evidence_read") if tool else None,
    )


def _body(args: dict[str, Any]) -> dict[str, Any]:
    """A steer's or a key press's body: the arguments without the key and the held input."""
    return {key: value for key, value in args.items() if key not in ("key", *_HELD)}


_C = "/api/coders"
_K = _C + "/{key}"
CODER_OPERATIONS: tuple[OperationDescriptor, ...] = (
    *(_op(f"coder.relay.{verb}", "relay", ("GET" if verb == "peek" else "POST", f"/api/coders/relay/{{node}}/{verb}"),
          f"api_relay_{verb}", lambda s, p, a, verb=verb: s.relay(p, verb, a),
          "Relay a steering request to a configured node. HTTP only: the hub holds the node credential.",
          write=verb != "peek", tool=False, owner_only=True, authority="authority", blocking_io=True)
      for verb in ("peek", "arm", "disarm", "steer", "keys")),
    # The coder board: which live session receives a spoken answer.
    _op("coder.status", "companion_status", ("GET", _C + "/status"), "api_companion_status",
        lambda s, p, a: s.companion_status(p, runtime=a["runtime"], runtime_error=a["runtime_error"],
                                           devices=a["devices"]),
        "Read the AI PI companion state: the waiting sessions, the reply target, the devices and the blockers.",
        tool=False, held=("runtime", "runtime_error", "devices")),
    _op("coder.list", "board", ("GET", _C + "/sessions"), "api_coders_sessions",
        lambda s, p, a: s.board(p, agent=a.get("agent"), include_ended=a.get("include_ended")),
        "List the live coder sessions, newest first, with the items handed to agents (flights), the launch "
        "history and the launch count.",
        properties={"agent": {"type": "string", "description": "Filter by agent name."},
                    "include_ended": {"type": "boolean", "description": "Include ended sessions (default true)."}},
        result="{sessions, count, flights, history, launches}"),
    _op("coder.own_agents", "own_agents", ("GET", _C + "/own-agents"), "api_coders_own_agents",
        lambda s, p, a: s.own_agents(p),
        "List the Claude Code and Codex processes the owner started by hand (read only).",
        blocking_io=True, result="{agents, count}"),
    _op("coder.own_agents.answer", "answer_own_agent", ("POST", _C + "/own-agents/answer"),
        "api_coders_own_agent_answer",
        lambda s, p, a: s.answer_own_agent(p, a.get("pane_id"), a.get("since"), a.get("keys"), a.get("text"), **({"expected_authority": a["expected_authority"]} if "expected_authority" in a else {})),
        "Answer the prompt of one agent the owner started by hand, after a new read of its screen.",
        write=True, authority="authority", blocking_io=True,
        properties={"pane_id": _ID, "since": _ID, "keys": {"type": "array", "items": {"type": "string"}},
                    "text": {"type": "string"}, "expected_authority": {"type": "object"}}, required=("pane_id", "since"),
        facts={**target("coder.own_agents.answer", "resolve_own_answer_authority"), "x-held-authority": "prompt",
            **held_arguments("Answer this agent prompt", *prompt_facts(), hidden("pane_id", "Pane"), hidden("since", "Read", "token"),
                hidden("keys", "Keys"), hidden("text", "Answer", "secret"))}),
    _op("coder.select", "select", ("POST", _C + "/select"), "api_companion_select",
        lambda s, p, a: s.select(p, a.get("agent"), a.get("session_id")),
        "Make one waiting session the active reply target.", write=True, properties=_TARGET,
        required=("agent", "session_id"), result="{success, session}"),
    _op("coder.dismiss", "dismiss", ("POST", _C + "/dismiss"), "api_companion_dismiss",
        lambda s, p, a: s.dismiss(p, a.get("agent"), a.get("session_id")),
        "Clear the captured question of a waiting session. The session stays.", write=True, properties=_TARGET,
        required=("agent", "session_id"), result="{success, session}"),
    _op("coder.pin", "pin", ("POST", _C + "/pin"), "api_companion_pin",
        lambda s, p, a: s.pin(p, a.get("agent"), a.get("session_id"), a.get("pinned", True)),
        "Pin or unpin a waiting session as the sticky reply target.", write=True,
        properties={**_TARGET, "pinned": {"type": "boolean", "description": "Default true."}},
        required=("agent", "session_id"), result="{success, session}"),
    # The factory: a tmux session on this Mac.
    _op("coder.spawn", "spawn", ("POST", _C + "/factory/spawn"), "api_factory_spawn",
        lambda s, p, a: s.spawn(p, a.get("name"), a.get("command"), a.get("cwd")),
        "Start a detached tmux session with a name, a command and a folder (audited).",
        write=True, tool=False, blocking_io=True),
    _op("coder.rename", "rename", ("POST", _C + "/factory/rename"), "api_factory_rename",
        lambda s, p, a: s.rename(p, a.get("target"), a.get("name")),
        "Rename a tmux session (audited).", write=True, tool=False, blocking_io=True),
    # Steering (HS-87): watch, arm, steer, end, keep.
    _op("coder.peek", "peek", ("GET", _K + "/peek"), "api_coder_peek",
        lambda s, p, a: s.peek(p, a.get("key"), a.get("lines"), a.get("last_hash"), a.get("raw")),
        "Read the screen of a session's tmux pane, with its grant and its steering policy. The key is "
        "agent:session_id or pane:%N.",
        blocking_io=True,
        properties={"lines": {"type": "integer", "minimum": 1, "description": "Default 200."},
                    "last_hash": {"type": "string"},
                    "raw": {"type": "integer", "enum": [0, 1], "description": "1 keeps the terminal colours."}}),
    _op("coder.arm", "arm", ("POST", _K + "/arm"), "api_coder_arm",
        lambda s, p, a: s.arm(p, a.get("key"), a.get("ttl_seconds"), **({"expected_authority": a["expected_authority"]} if "expected_authority" in a else {})),
        "Arm a session for steering: a grant on its pane for a time.", write=True, authority="authority",
        blocking_io=True, properties={"ttl_seconds": {"type": "integer", "minimum": 1}, "expected_authority": {"type": "object"}},
        facts={**target("coder.arm", "resolve_arm_authority"), "x-held-authority": "steering",
            **held_arguments("Arm this agent pane", *permission_facts(), hidden("key", "Session"), text("ttl_seconds", "Requested seconds"))}),
    _op("coder.disarm", "disarm", ("POST", _K + "/disarm"), "api_coder_disarm",
        lambda s, p, a: s.disarm(p, a.get("key"), **({"expected_authority": a["expected_authority"]} if "expected_authority" in a else {})), "Disarm a session at once. A second disarm does nothing.",
        write=True, properties={"expected_authority": {"type": "object"}},
        facts={**target("coder.disarm", "resolve_disarm_authority"), "x-held-authority": "steering-revoke",
            **held_arguments("Disarm this agent pane", *permission_facts(), hidden("key", "Session"))}),
    _op("coder.grants", "grants", ("GET", _C + "/steering/grants"), "api_coder_grants",
        lambda s, p, a: s.grants(p), "List the live steering grants.", result="{grants}"),
    _op("coder.nodes", "nodes", ("GET", _C + "/steering/nodes"), "api_coder_nodes",
        lambda s, p, a: s.nodes(p), "List the names of the configured steering nodes (never an address or a token).",
        result="{nodes}"),
    _op("coder.panes", "panes", ("GET", _C + "/steering/panes"), "api_coder_panes",
        lambda s, p, a: s.panes(p), "List every tmux pane on this Mac.", tool=False, blocking_io=True),
    _op("coder.steer", "steer", ("POST", _K + "/steer"), "api_coder_steer",
        lambda s, p, a: s.steer(p, a.get("key"), _body(a), process_input=a["process_input"]),
        "Type one steer into a session's pane, with its grounding (audited). preview: true sends nothing.",
        write=True, tool=False, held=_HELD, blocking_io=True),
    _op("coder.keys", "send_keys", ("POST", _K + "/keys"), "api_coder_keys",
        lambda s, p, a: s.send_keys(p, a.get("key"), _body(a), process_input=a["process_input"]),
        "Send allowed keys to a session's pane (audited).", write=True, tool=False, held=_HELD, blocking_io=True),
    _op("coder.kill", "kill", ("POST", _K + "/kill"), "api_coder_kill",
        lambda s, p, a: s.kill(p, a.get("key"), a.get("scope")),
        "End the armed pane, or its tmux session (audited).", write=True, authority="authority", blocking_io=True,
        properties={"scope": {"enum": ["pane", "session"], "description": "Default pane."}}),
    _op("coder.audit", "list_steering_audit", ("GET", _C + "/steering/audit"), "api_coder_steering_audit",
        lambda s, p, a: {"audit": s.list_steering_audit(p, a.get("session_key"), a.get("limit", 50))},
        "Read the steering audit trail, newest first: who, when, the session, the pane and the outcome. "
        "Only the head and a hash of each text are kept.",
        properties={"session_key": {"type": "string", "description": "Filter by session key."},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 500,
                              "description": "Maximum entries (default 50)."}},
        result="{audit}"),
    _op("coder.keep_note", "keep_session_note", ("POST", _K + "/keep-note"), "api_coder_keep_note",
        lambda s, p, a: s.keep_session_note(p, a.get("key"), a.get("title"), a.get("body")),
        "Keep the session's current ask as a desk note, with a line that names the session.", write=True,
        status=201, properties={"title": {"type": "string"}, "body": {"type": "string"}}, result="{note}"),
)

CODER_OPERATIONS += (OperationDescriptor(
    name="coder.explain", version=1, description="Why an agent has its state: hook or screen rule, evidence and age.",
    args_schema={"type": "object", "properties": {"target": _ID}, "required": ["target"], "additionalProperties": False},
    principal=_PRINCIPAL, effect="read", result="the source and evidence behind the agent state",
    refusals=_REFUSALS, completion="synchronous", exposure=("mcp:coder.explain",),
    service="coder_service", method="explain", call=lambda s, p, a: s.explain(p, a["target"]), thread="evidence_read", blocking_io=True,
    tool_schema={"type": "object", "properties": {"target": _ID}, "required": ["target"], "additionalProperties": False},
),)

__all__ = ["CODER_OPERATIONS"]
