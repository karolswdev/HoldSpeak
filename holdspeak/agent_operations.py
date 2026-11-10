"""Conductor K2: Hand to an agent session on the one declared contract (the descriptor row).

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
        "Hand one desk item to a coder (a coding session: Claude Code, Codex or pi). HoldSpeak writes a brief from the item, its meeting, "
        "the Project's decisions and open commitments, memory and the repository's .hs/ facts (no People "
        "data), makes a new git worktree hs-<kind>-<id> in the Project repository and starts Claude Code "
        "(profile claude-default), Codex (codex-default) or pi (pi-default, on the hub's engine for coding "
        "work) there. Only the owner hands; an agent is refused."
    ),
    args_schema={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["action", "decision", "decision_record", "project_item", "note", "meeting", "artifact", "issue",
                         "program_step"],
                "description": "The item kind. An issue is a Room issue: id <watch_id>.<entity_id>. A program_step is one step of a Program (the Programs engine hands it).",
            },
            "id": {"type": "string", "minLength": 1, "maxLength": 128, "description": "The item id."},
            "instruction": {"type": ["string", "null"], "maxLength": 4000,
                            "description": "Optional words for the agent."},
            "profile": {"type": ["string", "null"],
                        "description": "Agent profile id: claude-default (the default), codex-default or pi-default."},
            "project_id": {"type": ["string", "null"],
                           "description": "Optional Project id, when the item names no Project."},
            "queue": {"type": ["boolean", "null"],
                      "description": "At the working-at-once limit, wait for a free agent and start then "
                                     "(status queued) instead of the launch_cap_reached refusal."},
        },
        "required": ["kind", "id"],
        "additionalProperties": False,
    },
    principal="derived by the transport (HTTP auth middleware; MCP auth resolver); the owner's press",
    effect="write",
    result=(
        "{status: launched or failed (or queued: at the working-at-once limit with queue, the hand waits "
        "for a free agent and the answer carries queue_id and queued_at), resumed (true when an earlier launch of this item got its held "
        "brief again), instruction_state (pending, sent, hooks_missing or the steering refusal: the "
        "brief is typed when the agent session registers and is sent only on a delivered receipt), "
        "trust_state, launch_id, attempt_id, operation_id, state, failure, gate, session, "
        "worktree: {name, branch}, source_id, story_ref: {project, story_id}, origin_ref: {kind, id}, "
        "project_id, control_mode, brief: {bytes, refs, people_cut}}"
    ),
    refusals=_CONTRACT_REFUSALS + (
        "owner_required",
        "item_kind_unsupported", "item_unknown", "profile_unknown", "tmux_absent", "executable_absent",
        "no_repository", "repository_not_registered: the Room watches a repository nobody registered",
        "clone_failed", "clone_timed_out", "gh_not_installed", "worktree_duplicate", "worktree_name_invalid", "brief_over_cap",
        "launch_cap_reached: as many agents work now as the setting agents.working_at_once allows (default 6)",
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
        "Register a GitHub repository (owner/name) for a Project, so Hand to an agent session can work in it. Nothing is "
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
        "owner_required",
        "repository_invalid: not owner/name", "project_unknown",
    ),
    completion="synchronous; GET /api/projects/{project_id}/repository shows it",
    exposure=("http:POST /api/projects/{project_id}/repository", "mcp:project.repository.register"),
    service="agent_hand_service",
    method="register_project_repository",
    tool_schema={"type": "object", "properties": {"project_id": {"type": "string", "minLength": 1},
        "repository": {"type": "string", "minLength": 3}, "command_id": {"type": "string"}},
        "required": ["project_id", "repository"], "additionalProperties": False},
    authority="authority",
    owner_only=True,
    owner_press=True,
    admission=Admission(
        "admitted",
        "PHILO-15 16 (B38): the owner's press names the Project's repository (the Door's GitHub row, the "
        "drawer's Register). Owner only, in no agent palette. The clone on the first hand is its own receipt.",
    ),
)

# ── The launch verbs (2026-11-08; MCP tools 2026-11-09) ──
#
# One row per verb the Agents window, the lane and the Hand sheet call on a
# launch: its call on the hub's ``AgentHandService``, its HTTP method and
# path, and its MCP tool. ``web/routes/agent_hand.py`` produces the routes
# and ``mcp/families/declared.py`` the tools from these rows, both through
# ``OperationRegistry.invoke``. As in the meeting rows, the arguments schema is
# any object (a GET's query arrives as strings); the service validates. The
# tool schema is closed and requires the path's ids. A read is evidence, MCP
# and HTTP only (``thread_modes._family_reads``); a launched agent reads the
# reads and never calls the writes (``conductor_launch._family_rules``).

_LAUNCH_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver); the owner's desk"
_LAUNCH_REFUSALS = _CONTRACT_REFUSALS + ("launch_unknown",)
_ANY = {"type": "object"}
_ID = {"type": "string", "minLength": 1, "maxLength": 128}
_TEXT = {"type": "string", "maxLength": 4000}
_L = "/api/agent/launches/{launch_id}"
_EXEMPT = Admission("exempt", "The owner's view of, and press on, his own agent: the launch ledger is its record.")


def _launch_op(name: str, method: str, http: tuple[str, str], handler: str, call, description: str, *,
               write: bool = False, result: str = "the AgentHandService answer", status: int = 200,
               refusals: tuple[str, ...] = (), owner_only: bool = False, blocking_io: bool = False,
               properties: dict | None = None, required: tuple[str, ...] = ()) -> OperationDescriptor:
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema=_ANY, principal=_LAUNCH_PRINCIPAL,
        effect="write" if write else "read", result=result, refusals=_LAUNCH_REFUSALS + refusals,
        completion="synchronous; a write is one desk_changed frame (the Agents window reads its flights again)",
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service="agent_hand_service", method=method,
        owner_only=owner_only, owner_press=owner_only and write,
        authority="authority" if owner_only else "work", blocking_io=blocking_io, admission=_EXEMPT,
        call=call, http=http, http_status=status, handler=handler, tool_schema=tool,
        thread="effect_proposal" if write else "evidence_read",
    )


_HAND_ITEM = {
    "kind": {"type": "string", "description": "The item kind (as agent.hand)."},
    "id": {"type": "string", "minLength": 1, "maxLength": 128, "description": "The item id."},
    "instruction": {"type": ["string", "null"], "maxLength": 4000},
    "profile": {"type": ["string", "null"], "description": "claude-default, codex-default or pi-default."},
    "project_id": {"type": ["string", "null"]},
    "review_by": {"type": ["string", "null"], "description": "The agent profile that reviews the work."},
}

LAUNCH_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _launch_op("agent.launch.lane", "launch_lane", ("GET", _L + "/lane"), "api_agent_launch_lane",
               lambda s, p, a: s.launch_lane(p, a.get("launch_id"), after=a.get("after", 0), limit=a.get("limit", 200)),
               "Read one launch: its brief, follow-through and PR checks, the wait with its draft, the session's "
               "events (paged: after, limit), the gated calls, the answers typed, the worktree and the usage.",
               properties={"after": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 1000}},
               result="the lane: launch, session, follow_through, wait, events, events_next_after, gated, answers, "
                      "attempt_events, worktree, usage, control, used, last_words"),
    _launch_op("agent.launch.explain", "launch_explain", ("GET", _L + "/explain"), "api_agent_launch_explain",
               lambda s, p, a: s.launch_explain(p, a.get("launch_id")),
               "Why the agent has its state: the hook or the screen rule that decided it, the rule's file, the "
               "lines it matched and the age of the read.", result="the source that decided the state, its rule, the hook or screen read"),
    _launch_op("agent.launch.answer", "launch_answer", ("POST", _L + "/answer"), "api_agent_launch_answer",
               lambda s, p, a: s.launch_answer(p, a.get("launch_id"), since=a.get("since"), keys=a.get("keys"),
                                               text=a.get("text")),
               "Answer an agent whose hooks are off, after a fresh read of its prompt: keys (Enter, Escape, 1..9) "
               "or text; since names the prompt he saw.", write=True, owner_only=True, blocking_io=True,
               refusals=("owner_required", "wait_not_current", "pane_gone", "transport_error"),
               properties={"since": {"type": "string"}, "keys": {"type": "array", "items": {"type": "string"}},
                           "text": _TEXT}),
    _launch_op("agent.launch.seen", "launch_seen", ("POST", _L + "/seen"), "api_agent_launch_seen",
               lambda s, p, a: s.launch_seen(p, a.get("launch_id"), wait_id=a.get("wait_id")),
               "He opened the agent: its done turn and the desk's answer are seen (New goes).", write=True,
               result="launch_id, seen (the turn) and answer_seen", properties={"wait_id": {"type": "string"}}),
    _launch_op("agent.launch.done", "launch_done", ("POST", _L + "/done"), "api_agent_launch_done",
               lambda s, p, a: s.launch_done(p, a.get("launch_id")),
               "Done: he checked the work of a launch whose turn ended done; it leaves the running agents.",
               write=True, owner_only=True, refusals=("owner_required", "not_done", "unknown")),
    _launch_op("agent.launch.remove", "launch_remove", ("POST", _L + "/remove"), "api_agent_launch_remove",
               lambda s, p, a: s.launch_remove(p, a.get("launch_id")),
               "Remove an ended launch from the Agents list (the record stays).", write=True, owner_only=True,
               refusals=("owner_required", "in_flight", "unknown")),
    _launch_op("agent.launch.resume", "launch_resume", ("POST", _L + "/resume"), "api_agent_resume",
               lambda s, p, a: s.launch_resume(p, a.get("launch_id")),
               "Resume an agent a restart stopped: a new terminal in its worktree runs the agent's own resume.",
               write=True, owner_only=True, status=202, blocking_io=True, refusals=("owner_required", "launch_not_stopped")),
    _launch_op("agent.hand.cancel_queued", "cancel_queued_hand", ("DELETE", "/api/agent/hand/queue/{queue_id}"),
               "api_agent_hand_queue_cancel", lambda s, p, a: s.cancel_queued_hand(p, a.get("queue_id")),
               "Cancel a hand that waits for a free agent: it leaves the queue and never starts.", write=True,
               result="queue_id and cancelled", refusals=("queue_unknown",)),
    _launch_op("agent.helper.allow", "allow_helper", ("POST", _L + "/helper/allow"), "api_agent_helper_allow",
               lambda s, p, a: s.allow_helper(p, a.get("launch_id"), request_id=a.get("request_id")),
               "Allow the one helper an agent asked for under Secure (the worktree and process.spawn checks "
               "still decide).", write=True, owner_only=True, status=202, blocking_io=True, refusals=("owner_required", "request_id_required"),
               properties={"request_id": _ID}, required=("request_id",)),
    # 2026-11-09: the Hand sheet's preview and receipt, the lane's Re-brief and
    # Take back, and Deliver (the held brief of an existing launch).
    _launch_op("agent.hand.preview", "preview", ("POST", "/api/agent/hand/preview"), "api_agent_hand_preview",
               lambda s, p, a: s.preview(p, a.get("kind"), a.get("id"), instruction=a.get("instruction"),
                                         profile=a.get("profile"), project_id=a.get("project_id"),
                                         review_by=a.get("review_by")),
               "Preview Hand to an agent session with no side effect: the brief, the repository, the branch, the "
               "worktree and the agent it would use. Only the owner previews.", owner_only=True,
               refusals=("owner_required", "item_required", "item_unknown", "profile_unknown"),
               properties=_HAND_ITEM, required=("kind", "id"),
               result="{text, refs, bytes, people_cut, sources, acceptance, repo, repo_label, branch, worktree, "
                      "project_id, control_mode, kind, id, requested_profile, profile, resume, refused, engine}"),
    _launch_op("agent.launch.get", "launch_record", ("GET", _L), "api_agent_launch",
               lambda s, p, a: s.launch_record(p, a.get("launch_id")),
               "Read one launch's delivery from the launch ledger: the brief is pending, held, sent or refused.",
               result="{launch_id, state, instruction_state, trust_state, failure, profile_id, profile}"),
    _launch_op("agent.launch.rebrief", "rebrief", ("POST", _L + "/rebrief"), "api_agent_rebrief",
               lambda s, p, a: s.rebrief(p, a.get("launch_id"), text=a.get("text")),
               "Re-brief a launched agent: the words are typed into its own terminal now when it is idle or "
               "asks (delivered), else at the end of its turn (queued).", write=True, owner_only=True,
               blocking_io=True, properties={"text": _TEXT}, required=("text",),
               refusals=("owner_required", "no_session", "launch_ended", "wait_not_current"),
               result="{status: delivered or queued, command_id, ...}"),
    _launch_op("agent.launch.take_back", "take_back", ("POST", _L + "/rebrief/{press_id}/take-back"),
               "api_agent_rebrief_take_back", lambda s, p, a: s.take_back(p, a.get("launch_id"), a.get("press_id")),
               "Take back one queued Re-brief before the agent's turn ends; its receipt is TAKEN BACK.",
               write=True, owner_only=True, refusals=("owner_required", "not_queued"),
               result="{status: taken_back, ...}"),
    _launch_op("agent.launch.deliver", "resume", ("POST", _L + "/deliver"), "api_agent_deliver",
               lambda s, p, a: s.resume(p, a.get("launch_id")),
               "Deliver the held brief of an existing launch (after a restart, a hook install or a refused "
               "send). The launch is not started again.", write=True, owner_only=True, status=202, blocking_io=True,
               refusals=("owner_required",), result="{launch_id, state, instruction_state, trust_state}"),
)

AGENT_OPERATIONS = (PROJECT_REPOSITORY_REGISTER, AGENT_HAND) + LAUNCH_OPERATIONS

__all__ = ["AGENT_HAND", "AGENT_OPERATIONS", "LAUNCH_OPERATIONS", "PROJECT_REPOSITORY_REGISTER"]
