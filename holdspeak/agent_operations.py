"""Conductor K2: Hand to agent on the one declared contract (the descriptor row).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), the way ``channel_operations.py`` carries the Send. The row
names its method on the hub's ``AgentHandService``. The HTTP route and the MCP
tool reach the same declaration and the same instance.

Admission: the hand-off is the owner's press. It crosses egress (a brief from
the desk goes to a coding agent on a cloud model) and it starts a process. The
process is admitted by the kernel's own ``process.spawn`` operation, which the
launch engine submits, decides and receipts (``factory_launch.submit_process_spawn``);
its ``operation_id`` comes back in the result. The row declares that admission
and does not wrap a second kernel operation around it (``enforced=False``).
"""
from __future__ import annotations

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor

AGENT_HAND = OperationDescriptor(
    name="agent.hand",
    version=1,
    description=(
        "Hand one desk item to a coding agent. HoldSpeak writes a brief from the item, its meeting, "
        "the Project's decisions and open commitments, memory and the repository's .hs/ facts (no People "
        "data), makes a new git worktree hs-<kind>-<id> in the Project repository and starts Claude Code "
        "(profile claude-default) or Codex (codex-default) there. Only the owner hands; an agent is refused."
    ),
    args_schema={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["action", "decision", "decision_record", "project_item", "note", "meeting", "artifact", "issue"],
                "description": "The item kind. An issue is a Room issue: id <watch_id>.<entity_id>.",
            },
            "id": {"type": "string", "minLength": 1, "maxLength": 128, "description": "The item id."},
            "instruction": {"type": ["string", "null"], "maxLength": 4000,
                            "description": "Optional words for the agent."},
            "profile": {"type": ["string", "null"],
                        "description": "Agent profile id: claude-default (the default) or codex-default."},
            "project_id": {"type": ["string", "null"],
                           "description": "Optional Project id, when the item names no Project."},
        },
        "required": ["kind", "id"],
        "additionalProperties": False,
    },
    principal="derived by the transport (HTTP auth middleware; MCP auth resolver); the owner's press",
    effect="write",
    result=(
        "{status: launched or failed, resumed (true when an earlier launch of this item got its held "
        "brief again), instruction_state (pending, sent, hooks_missing or the steering refusal: the "
        "brief is typed when the agent session registers and is sent only on a delivered receipt), "
        "trust_state, launch_id, attempt_id, operation_id, state, failure, gate, session, "
        "worktree: {name, branch}, source_id, story_ref: {project, story_id}, origin_ref: {kind, id}, "
        "project_id, control_mode, brief: {bytes, refs, people_cut}}"
    ),
    refusals=_CONTRACT_REFUSALS + (
        "owner_required: only the owner hands an item to an agent",
        "item_kind_unsupported", "item_unknown", "profile_unknown", "tmux_absent", "executable_absent",
        "no_repository", "repository_not_registered: the Room watches a repository nobody registered",
        "clone_failed", "clone_timed_out", "gh_not_installed", "worktree_duplicate", "worktree_name_invalid", "brief_over_cap",
        "launch_cap_reached: 3 HoldSpeak-launched agents run now (the limit)",
        "story_ref_invalid", "process_spawn_not_gated", "kernel_unavailable",
    ),
    completion=(
        "synchronous launch; the process.spawn kernel operation (operation_id) holds the launch receipt; "
        "GET /api/delivery/attempts shows the Work attempt with its origin_ref"
    ),
    exposure=("http:POST /api/agent/hand", "mcp:agent.hand"),
    service="agent_hand_service",
    method="hand_item",
    blocking_io=True,  # git worktree add, tmux, the agent process
    owner_only=True,
    owner_press=True,
    admission=Admission(
        "admitted",
        "Starts a process and crosses egress (XI.1): admitted by the kernel's process.spawn operation, "
        "one terminal receipt per launch. The owner's press.",
        enforced=False,
    ),
)

PROJECT_REPOSITORY_REGISTER = OperationDescriptor(
    name="project.repository.register",
    version=1,
    description=(
        "Register a GitHub repository (owner/name) for a Project, so Hand to agent can work in it. Nothing is "
        "cloned now: the first hand of an item in the Project clones it from github.com into the HoldSpeak "
        "clone folder (its own receipt). Only the owner registers."
    ),
    args_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "minLength": 1, "maxLength": 128},
            "repository": {"type": "string", "minLength": 3, "maxLength": 240,
                           "description": "owner/name (a github.com URL is read as owner/name)."},
            "command_id": {"type": ["string", "null"], "maxLength": 128},
        },
        "required": ["project_id", "repository"],
        "additionalProperties": False,
    },
    principal="derived by the transport (the HTTP auth middleware); owner only",
    effect="write",
    result="{project_id, repository, registered, cloned, registered_at, cloned_at, watched, host} and the receipt",
    refusals=_CONTRACT_REFUSALS + (
        "owner_required: only the owner registers a repository",
        "repository_invalid: not owner/name", "project_unknown",
    ),
    completion="synchronous; GET /api/projects/{project_id}/repository shows it",
    exposure=("http:POST /api/projects/{project_id}/repository",),
    service="agent_hand_service",
    method="register_project_repository",
    owner_only=True,
    owner_press=True,
    admission=Admission(
        "admitted",
        "PHILO-15 16 (B38): the owner's press names the Project's repository (the Door's GitHub row, the "
        "drawer's Register). HTTP only, in no palette. The clone on the first hand is its own receipt.",
    ),
)

AGENT_OPERATIONS = (PROJECT_REPOSITORY_REGISTER, AGENT_HAND)

__all__ = ["AGENT_HAND", "AGENT_OPERATIONS", "PROJECT_REPOSITORY_REGISTER"]
