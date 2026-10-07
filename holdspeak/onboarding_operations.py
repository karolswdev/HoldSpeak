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
    description="Install the HoldSpeak hooks for one coding agent (Claude Code or Codex) in the settings file "
                "that agent reads. Foreign hooks stay. A second install changes nothing.",
    args_schema={
        "type": "object",
        "properties": {
            "agent": {"enum": ["claude", "codex"]},
            "settings_path": {"type": "string", "description": "Bound by the hub before admission (the agent's "
                                                                "settings file); never sent by a client."},
        },
        "required": ["agent", "settings_path"],
        "additionalProperties": False,
    },
    principal="derived by the transport (the HTTP auth middleware); owner only",
    effect="write",
    result="{agents, tmux, holdspeak, used: {agent, path, installed_events, created_file}} and the receipt",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "claude_not_installed", "codex_not_installed",
                                   "agent_settings_unreadable", "agent_settings_path_changed",
                                   "holdspeak_not_found"),
    completion="synchronous; GET /api/onboarding/agents shows hooks installed",
    exposure=("http:POST /api/onboarding/agents/use",),
    service="onboarding_service",
    method="agents_use",
    owner_only=True,
    owner_press=True,
    admission=Admission("admitted", "Config: the owner's press writes a coding agent's hook settings file "
                                    "(HTTP only, in no palette). The agent and the file are bound at admission."),
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
    result="{mode, source, effective, agents} and the receipt",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "people_access_mode_unknown"),
    completion="synchronous; GET /api/settings/people-access shows the new mode",
    exposure=("http:PUT /api/settings/people-access", "mcp:people.access.set"),
    service="onboarding_service",
    method="people_access_set",
    owner_only=True,
    owner_press=True,
    admission=Admission("admitted", "Config (Conductor R7): the owner's press sets who reads People over MCP."),
)

#: The Conductor K1's rows (and R7's People access), in export order.
ONBOARDING_OPERATIONS: tuple[OperationDescriptor, ...] = (AGENT_HOOKS_INSTALL, PEOPLE_ACCESS_SET)
