"""The Conductor K1: the onboarding writes on the contract (the descriptor rows).

Carved beside ``holdspeak/operations.py`` (which imports this module into
``DESCRIPTORS``).  ``agent_hooks.install`` is the owner's one press on "Use it"
for a coding agent: a config write, admitted under Article XI, so every call
is one kernel operation with one terminal receipt (``services/project_kernel.py``)
-- succeeded, refused by name, or failed.  HTTP only, in no palette.
"""
from __future__ import annotations

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
    exposure=("http:POST /api/onboarding/agents/use", "http:POST /api/onboarding/agents/use-all"),
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

#: The Conductor K1's rows (and R7's People access, PHILO-15 04's system open), in export order.
ONBOARDING_OPERATIONS: tuple[OperationDescriptor, ...] = (AGENT_HOOKS_INSTALL, AGENT_HOOKS_REMOVE, PEOPLE_ACCESS_SET,
                                                          CALENDAR_OPEN_SETTINGS, CONNECTION_SIGN_IN)
