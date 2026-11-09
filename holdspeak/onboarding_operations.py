"""The Conductor K1: the onboarding writes on the contract (the descriptor rows).

Carved beside ``holdspeak/operations.py`` (which imports this module into
``DESCRIPTORS``).  ``agent_hooks.install`` is the owner's one press on "Use it"
for a coding agent: a config write, admitted under Article XI, so every call
is one kernel operation with one terminal receipt (``services/project_kernel.py``)
-- succeeded, refused by name, or failed.  HTTP only, in no palette.
"""
from __future__ import annotations

from typing import Any

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor

AGENT_HOOKS_INSTALL = OperationDescriptor(
    name="agent_hooks.install",
    version=1,
    description="Install HoldSpeak hooks, its native MCP server and AG13 skill for one or every discovered coding agent (Claude Code or Codex). "
                "Foreign entries stay. A second install changes nothing.",
    args_schema={
        "type": "object",
        "properties": {
            "agent": {"enum": ["claude", "codex"]},
            "agents": {"type": "array", "items": {"enum": ["claude", "codex"]}, "minItems": 1,
                       "uniqueItems": True},
            "settings_path": {"type": "string", "description": "Bound by the hub before admission (the agent's "
                                                                "settings file); never sent by a client."},
            "settings_paths": {"type": "object", "additionalProperties": {"type": "string"},
                               "description": "Bound by the hub for an aggregate install; never sent by a client."},
        },
        "oneOf": [
            {"required": ["agent", "settings_path"]},
            {"required": ["agents", "settings_paths"]},
        ],
        "additionalProperties": False,
    },
    principal="derived by the transport (the HTTP auth middleware); owner only",
    effect="write",
    result="{agents, tmux, holdspeak, used: {agent, path, mcp, skill, installed_events, created_file}}, or {agents, tmux, holdspeak, state, ok, results} for an aggregate install, and the receipt",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "claude_not_installed", "codex_not_installed",
                                   "agent_settings_unreadable", "agent_settings_path_changed",
                                   "holdspeak_not_found", "mcp_name_taken", "mcp_config_unreadable",
                                   "mcp_install_failed", "mcp_binding_missing", "agents_invalid", "agent_unknown",),
    completion="synchronous; GET /api/onboarding/agents shows the complete binding(s)",
    exposure=("http:POST /api/onboarding/agents/use",),
    service="onboarding_service",
    method="agents_use",
    owner_only=True,
    blocking_io=True,
    owner_press=True,
    admission=Admission("admitted", "Config: the owner's press writes a coding agent's hooks, native MCP entry and AG13 skill "
                                    "(HTTP only, in no palette). The agent and hook file are bound at admission."),
)

AGENT_HOOKS_REMOVE = OperationDescriptor(
    name="agent_hooks.remove",
    version=1,
    description="Stop HoldSpeak use for one coding agent. Remove only HoldSpeak hooks, its native MCP entry and AG13 skill; foreign entries stay.",
    args_schema={
        "type": "object",
        "properties": {
            "agent": {"enum": ["claude", "codex"]},
            "settings_path": {"type": "string", "description": "Bound by the hub before admission."},
        },
        "required": ["agent", "settings_path"],
        "additionalProperties": False,
    },
    principal="derived by the transport (the HTTP auth middleware); owner only",
    effect="write",
    result="{agents, stopped: {agent, mcp, hooks, skill_removed}} and the receipt",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "agent_unknown", "agent_settings_path_changed",
                                   "mcp_config_unreadable", "mcp_remove_failed", "mcp_remove_incomplete"),
    completion="synchronous; GET /api/onboarding/agents shows the remaining foreign bindings",
    exposure=("http:POST /api/onboarding/agents/stop",),
    service="onboarding_service",
    method="agents_stop",
    owner_only=True,
    blocking_io=True,
    owner_press=True,
    admission=Admission("admitted", "Config: the owner's press removes HoldSpeak's agent bindings while preserving foreign entries (HTTP only, in no palette)."),
)

PEOPLE_ACCESS_SET = OperationDescriptor(
    name="people_access.set",
    version=1,
    description="Set People MCP access: off, read or write. MCP clients of the owner get it; an agent HoldSpeak "
                "launched gets read unless it is off. HOLDSPEAK_MCP_PEOPLE_ACCESS, when set, overrides it.",
    args_schema={
        "type": "object",
        "properties": {"mode": {"enum": ["off", "read", "write"]}},
        "required": ["mode"],
        "additionalProperties": False,
    },
    principal="derived by the transport; owner only",
    effect="write",
    result="{mode, source, effective, env_var, agents} and the receipt",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "people_access_mode_unknown", "people_access_env_override"),
    completion="synchronous; GET /api/settings/people-access shows the new mode",
    exposure=("http:PUT /api/settings/people-access", "mcp:people.access.set"),
    service="onboarding_service",
    method="people_access_set",
    call=lambda s, p, a: s.people_access_set(p, a.get("mode")),
    http=("PUT", "/api/settings/people-access"),
    handler="people_access_set",
    authority="config",
    owner_only=True,
    owner_press=True,
    admission=Admission("admitted", "Config (Conductor R7): the owner's press sets who reads People over MCP."),
)

CALENDAR_OPEN_SETTINGS = OperationDescriptor(
    name="calendar.open_settings",
    version=1,
    description="Open System Settings at Privacy & Security > Calendars on this Mac, so the owner can allow "
                "calendar access after he denied it. It changes no setting.",
    args_schema={"type": "object", "properties": {}, "additionalProperties": False},
    principal="derived by the transport (the HTTP auth middleware); owner only",
    effect="write",
    result="{opened, pane} and the receipt",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "system_settings_not_opened"),
    completion="synchronous; GET /api/onboarding/calendar shows the access state after he changes it",
    exposure=("http:POST /api/onboarding/calendar/macos/settings",),
    service="onboarding_service",
    method="calendar_open_settings",
    call=lambda s, p, a: s.calendar_open_settings(p),
    http=("POST", "/api/onboarding/calendar/macos/settings"),
    handler="onboarding_calendar_settings",
    owner_only=True,
    owner_press=True,
    admission=Admission("admitted", "A system open (PHILO-15 04): the owner's press opens the macOS Calendars "
                                    "privacy pane on this device (HTTP only, in no palette)."),
)

CONNECTION_SIGN_IN = OperationDescriptor(
    name="connection.signin",
    version=1,
    description="Start the provider's native browser sign-in in the Accounts terminal pane.",
    args_schema={
        "type": "object",
        "properties": {
            "provider_id": {"enum": ["github", "jira", "confluence"]},
            "site": {"type": "string"},
            "email": {"type": ["string", "null"]},
        },
        "required": ["provider_id", "site"],
        "additionalProperties": False,
    },
    principal="derived by the transport; owner only",
    effect="write",
    result="{status, run_id, target} and the receipt",
    refusals=_CONTRACT_REFUSALS + (
        "owner_required", "provider_unsupported", "site_invalid", "email_invalid",
        "cli_unavailable", "cli_help_failed", "browser_flow_unsupported",
        "terminal_unavailable", "terminal_target_failed", "spawn_failed",
    ),
    completion="the returned terminal target streams the native CLI; connection.recheck runs after its exit",
    exposure=("http:POST /api/connections/{provider}/signin",),
    service="connection_signin_service",
    method="start_sign_in",
    owner_only=True,
    blocking_io=True,
    owner_press=True,
    admission=Admission("admitted", "The owner's press starts a provider-owned sign-in process in the shared terminal pane."),
)

def _signin_status(service: Any, principal: Any, run_id: Any) -> Any:
    """The sign-in poll; a refusal is a named ServiceError (``run_unknown`` 404, ``owner_required`` 403)."""
    from holdspeak.services.connection_signin_service import SignInRefused
    from holdspeak.services.errors import ServiceError

    try:
        return service.status(principal, run_id)
    except SignInRefused as exc:
        status = 403 if exc.reason == "owner_required" else 404 if exc.reason == "run_unknown" else 409
        raise ServiceError(exc.reason, str(exc), context={"status": status}) from exc


CONNECTION_SIGN_IN_STATUS = OperationDescriptor(
    name="connection.signin.status",
    version=1,
    description="Read one provider sign-in started in the Accounts terminal pane: running, signed in or failed.",
    args_schema={"type": "object", "properties": {"run_id": {"type": "string", "minLength": 1}},
                 "required": ["run_id"], "additionalProperties": False},
    principal="derived by the transport; owner only",
    effect="read",
    result="{run_id, provider_id, state, target, exit_code}",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "run_unknown"),
    completion="synchronous; poll until the state is final",
    exposure=("http:GET /api/connections/signin/{run_id}", "mcp:connection.signin.status"),
    service="connection_signin_service",
    method="status",
    owner_only=True,
    call=lambda s, p, a: _signin_status(s, p, a.get("run_id")),
    http=("GET", "/api/connections/signin/{run_id}"),
    handler="connection_signin_status",
    tool_schema={"type": "object", "properties": {"run_id": {"type": "string", "minLength": 1}},
                 "required": ["run_id"], "additionalProperties": False},
    thread="evidence_read",
)

# ── every other onboarding route (2026-11-09): one row each ──────────────
# The detections read files, PATH and the macOS calendar store (no prompt, no
# network): anyone's evidence, so each read has an MCP tool. The presses act
# for the owner (owner_only, config or egress, so no thread offers them): the
# macOS prompt is a system dialog on his screen; a calendar check reads one ICS
# URL and a connection's Use probes its provider (egress, his press).

_ANY = "derived by the transport (HTTP auth middleware; MCP auth resolver); the edge decides who reaches it"
_OWNER = "derived by the transport (the HTTP auth middleware); owner only"
_NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}


def _detect(name: str, method: str, path: str, handler: str, description: str, result: str, *,
            tool: str = "", blocking: bool = True) -> OperationDescriptor:
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_ANY,
        effect="read", result=result, refusals=_CONTRACT_REFUSALS + ("onboarding_unavailable",),
        completion="synchronous; a read of local state", exposure=(f"http:GET {path}", f"mcp:{tool or name}"),
        service="onboarding_service", method=method, blocking_io=blocking, call=lambda s, p, a: getattr(s, method)(p),
        http=("GET", path), handler=handler, tool_schema=_NO_ARGS, thread="evidence_read",
    )


def _press(name: str, method: str, path: str, handler: str, call: Any, description: str, result: str, *,
           authority: str, egress: bool = False, refusals: tuple[str, ...] = (),
           properties: dict[str, Any] | None = None) -> OperationDescriptor:
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_OWNER,
        effect="write", result=result, refusals=_CONTRACT_REFUSALS + ("owner_required", "onboarding_unavailable") + refusals,
        completion="synchronous; the matching GET detection reads the new state",
        exposure=(f"http:POST {path}", f"mcp:{name}"), service="onboarding_service", method=method, owner_only=True,
        owner_press=egress, blocking_io=True, call=call, http=("POST", path), handler=handler, authority=authority,
        tool_schema={"type": "object", "properties": dict(properties or {}), "additionalProperties": False},
        thread="effect_proposal",
    )


ONBOARDING_ROUTE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _detect("onboarding.calendar.detect", "calendar_detect", "/api/onboarding/calendar", "onboarding_calendar",
            "Read the calendars on this Mac HoldSpeak can use, and the macOS Calendars permission. No prompt, no network.",
            "{macos: {state, can_request}, candidates, sources}"),
    _press("onboarding.calendar.request_access", "calendar_request_access", "/api/onboarding/calendar/macos/access",
           "onboarding_calendar_access", lambda s, p, a: s.calendar_request_access(p),
           "Show the macOS Calendars permission prompt on this Mac, then read the calendars again.",
           "the calendar detection with macos.requested", authority="config"),
    _press("onboarding.calendar.check", "calendar_check", "/api/onboarding/calendar/check", "onboarding_calendar_check",
           lambda s, p, a: s.calendar_check(p, a.get("url")),
           "Check one calendar address (ICS): validate it and read it once.",
           "{ok, events, host, detail}", authority="egress", egress=True,
           refusals=("calendar_url_invalid", "calendar_unreachable"),
           properties={"url": {"type": "string", "description": "An https or webcal ICS address."}}),
    _press("onboarding.calendar.use", "calendar_use", "/api/onboarding/calendar/use", "onboarding_calendar_use",
           lambda s, p, a: s.calendar_use(p, dict(a)),
           "Use one found calendar: add it as a calendar source.", "{source, sources}", authority="config",
           properties={"id": {"type": "string"}, "label": {"type": "string"}, "url": {"type": "string"}}),
    _detect("onboarding.connections.detect", "connections_detect", "/api/onboarding/connections",
            "onboarding_connections",
            "Read the gh and acli accounts this Mac is signed in to (files only), and which are in use.",
            "{candidates, connected}"),
    _press("onboarding.connections.use", "connections_use", "/api/onboarding/connections/use",
           "onboarding_connections_use", lambda s, p, a: s.connections_use(p, dict(a)),
           "Use one signed-in account: add the connection and check it with its provider once.",
           "{connection, status}", authority="egress", egress=True,
           properties={"id": {"type": "string", "description": "The account id from onboarding.connections.detect."}}),
    _detect("onboarding.agents.detect", "agents_detect", "/api/onboarding/agents", "onboarding_agents",
            "Read the coding agents on this Mac (Claude Code, Codex), tmux, and whether HoldSpeak is bound to each.",
            "{agents, tmux, holdspeak}"),
    _detect("people_access.get", "people_access", "/api/settings/people-access", "people_access",
            "Read who reads People over MCP: off, read or write; the effective mode and where it comes from.",
            "{mode, source, effective, env_var, agents}", tool="people.access.get", blocking=False),
)

#: The Conductor K1's rows (and R7's People access, PHILO-15 04's system open), in export order.
ONBOARDING_OPERATIONS: tuple[OperationDescriptor, ...] = (AGENT_HOOKS_INSTALL, AGENT_HOOKS_REMOVE, PEOPLE_ACCESS_SET,
                                                          CALENDAR_OPEN_SETTINGS, CONNECTION_SIGN_IN) \
    + (CONNECTION_SIGN_IN_STATUS,) + ONBOARDING_ROUTE_OPERATIONS
