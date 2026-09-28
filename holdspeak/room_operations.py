"""PHILO-9-02: the steward and the connectors on the contract (the descriptor rows).

One explicit row per operation (the Phase 7 settled method), carved beside
``holdspeak/operations.py`` (which imports this module into ``DESCRIPTORS``):
the twenty MCP identities of the charter's enumeration (the steward 5, the
nudges 3, the watches 7, the suggested sources 3, the connections 2), the
three HTTP-only rows the charter names (the Door's count, a watch's update and
its baseline), and the new ``project.mark_update_delivered``. Each row names
the real method on the hub's service and its Article XI admission BY EFFECT
(the owner's Q1; the phase status's admission table). Enforced: an ADMITTED
row is one kernel operation with one terminal receipt
(``services/project_kernel.py``); an agent is refused
``project_delegation_required`` with a receipt until story 07's grant names it.

The words name the owner's jobs and where every id comes from. The product
sends no update: nudge.send is a GitHub comment the owner reviews and sends.
"""
from __future__ import annotations

from typing import Any, Mapping

from holdspeak.operations import (
    _COMMAND_ID,
    _CONTRACT_REFUSALS,
    _PROJECT_ID,
    _ROOM_PRINCIPAL,
    _ROOM_READ,
    _UPDATE_ID,
    Admission,
    OperationDescriptor,
)

#: The policy fields whose presence makes project.configure_steward a WRITE.
STEWARD_POLICY_FIELDS: tuple[str, ...] = (
    "enabled", "unattended_enabled", "eligible_effect_kinds", "max_retries",
    "max_actions_per_run", "cooldown_seconds", "bounds", "evaluation_cadence_minutes",
)
#: connection.recheck probes these providers (egress); calendar and models read local state.
REMOTE_PROVIDERS: frozenset[str] = frozenset({"github", "jira", "confluence"})


def _policy_write(args: Mapping[str, Any]) -> bool:
    return any(args.get(field) is not None for field in STEWARD_POLICY_FIELDS)


def _remote(args: Mapping[str, Any]) -> bool:
    return str(args.get("provider_id") or "") in REMOTE_PROVIDERS


_RUN_ID = {"type": "string", "description": "The steward run id: run_id from project.run_steward, or "
                                            "steward.latest_run.id from project.get_room."}
_WATCH_ID = {"type": "string", "description": "The watch id: sources.items[].watchIds[] from project.get_room."}
_STEP_ID = {"type": "string", "description": "The nudge id: nudges[].step_id from steward.nudges."}
_REFERENCE = {"type": "string", "description": "The suggested source: suggestions[].reference from "
                                               "project.suggested_sources (owner/repo or PROJ-123)."}
_GRADUATED = "the MCP tool reaches graduated watches only (legacy rows: legacy_watch_boundary)"
_WATCH_REFUSALS = _CONTRACT_REFUSALS + ("NotFound not_found: unknown watch",
                                        "ServiceError owner_principal_required", "ServiceError legacy_watch_boundary")

# ── the steward ─────────────────────────────────────────────────────────

STEWARD_CONFIGURE = OperationDescriptor(
    name="project.configure_steward",
    version=1,
    description="Read or set the steward's policy for a project: what it may do (eligible_effect_kinds), its "
                "bounds, and whether it may run on its own (unattended_enabled). Give only project_id to read it.",
    args_schema={
        "type": "object",
        "properties": {
            "project_id": _PROJECT_ID,
            "enabled": {"type": ["boolean", "null"], "description": "Optional. Turn the steward on or off."},
            "unattended_enabled": {"type": ["boolean", "null"],
                                   "description": "Optional. Let the steward run on a schedule without you."},
            "eligible_effect_kinds": {"type": ["array", "null"], "items": {"type": "string"},
                                      "description": "Optional. What the steward may do: refresh_sources, "
                                                     "create_proposals, apply_proposal_effects, draft_update, "
                                                     "create_door_item, github_comment."},
            "max_retries": {"type": ["integer", "null"], "description": "Optional, 0 to 100."},
            "max_actions_per_run": {"type": ["integer", "null"], "description": "Optional, 0 to 1000."},
            "cooldown_seconds": {"type": ["integer", "null"], "description": "Optional, 0 to 86400."},
            "bounds": {"type": ["object", "null"], "description": "Optional bounds object."},
            "evaluation_cadence_minutes": {"type": ["integer", "null"],
                                           "description": "Optional, 1 to 10080: how often the project's watches read."},
            "command_id": _COMMAND_ID,
        },
        "required": ["project_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{policy} for a read (null when none is set); {success: true, policy} for a write",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown project",
                                   "ValidationError validation_error: a value outside its range or an unknown effect kind"),
    completion="synchronous; a read returns the stored policy",
    exposure=("http:GET /api/projects/{project_id}/steward/policy", "http:PUT /api/projects/{project_id}/steward/policy",
              "mcp:project.configure_steward"),
    service="project_steward_service",
    method="configure_policy",
    admission=Admission(
        "admitted_if",
        "Any policy field given: it sets what the steward may do and whether it runs on its own (a delegation; "
        "changes authority, Q1). Only project_id: a read.",
        STEWARD_POLICY_FIELDS,
        holds=_policy_write,
    ),
)

STEWARD_RUN = OperationDescriptor(
    name="project.run_steward",
    version=1,
    description="Let the steward run on a project now: it reads the sources, opens a review, and does what its "
                "policy allows. Returns run_id and operation_id at once; the run works in the background. Read it "
                "with project.get_steward_run.",
    args_schema={
        "type": "object",
        "properties": {
            "project_id": _PROJECT_ID,
            "watermark": {"type": ["string", "null"], "description": "Optional text to find this run again."},
            "command_id": _COMMAND_ID,
        },
        "required": ["project_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{success: true, run_id, operation_id, state, receipt} (receipt null while the run works)",
    refusals=_CONTRACT_REFUSALS + ("not_found: unknown project", "active_run_exists", "steward_disabled",
                                   "cooldown_active", "project_delegation_required",
                                   "project_delegation_expired", "project_delegation_revoked"),
    completion="asynchronous; project.get_steward_run returns the run's state, its steps and its one terminal receipt",
    exposure=("http:POST /api/projects/{project_id}/steward/runs", "mcp:project.run_steward"),
    service="project_steward_service",
    method="start_run",
    admission=Admission("admitted", "A run acts under the policy; each executed effect is a child operation "
                                    "(XI.2); github_comment crosses egress (Q1)."),
)

STEWARD_STOP = OperationDescriptor(
    name="project.stop_steward",
    version=1,
    description="Stop a steward run. The run stops at its next safe point and ends with its own receipt.",
    args_schema={
        "type": "object",
        "properties": {"run_id": _RUN_ID, "command_id": _COMMAND_ID},
        "required": ["run_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{success: true, run_id, operation_id, receipt}: the stop request is recorded (not: the run has stopped)",
    refusals=_CONTRACT_REFUSALS + ("not_found: unknown run", "steward_run_already_terminal",
                                   "steward_run_owner_required", "project_delegation_required",
                                   "project_delegation_expired", "project_delegation_revoked"),
    completion="synchronous for the request; project.get_steward_run shows the run end interrupted",
    exposure=("http:POST /api/steward/runs/{run_id}/stop", "mcp:project.stop_steward"),
    service="project_steward_service",
    method="stop_run",
    admission=Admission("admitted", "A durable stop on a run: controls a process (Q1)."),
)

STEWARD_READ_RUN = OperationDescriptor(
    name="project.get_steward_run",
    version=1,
    description="Read a steward run: its state, phase, steps, its operation_id and its terminal receipt.",
    args_schema={"type": "object", "properties": {"run_id": _RUN_ID}, "required": ["run_id"],
                 "additionalProperties": False},
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{run, steps, operation_id, receipt} (receipt null while the run works)",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown run",),
    completion="synchronous",
    exposure=("http:GET /api/steward/runs/{run_id}", "mcp:project.get_steward_run"),
    service="project_steward_service",
    method="read_run",
    admission=_ROOM_READ,
)

STEWARD_TRIGGER = OperationDescriptor(
    name="project.steward.trigger",
    version=1,
    description="Do the scheduled work now: read the watches that are due and start the steward runs they ask "
                "for. Returns operation_id at once; project.get_steward_run reads each run.",
    args_schema={"type": "object", "properties": {"command_id": _COMMAND_ID}, "additionalProperties": False},
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{success: true, operation_id, state, receipt} (receipt null until its runs end); the terminal "
           "receipt's result names the watch and run outcomes",
    refusals=_CONTRACT_REFUSALS + ("scheduler_not_wired", "project_delegation_required"),
    completion="asynchronous; kernel.receipt reads the trigger's receipt when its runs end",
    exposure=("http:POST /api/steward/trigger", "mcp:project.steward.trigger"),
    service="project_steward_service",
    method="trigger",
    admission=Admission("admitted", "Evaluates due watches and starts due steward work: controls a process; its "
                                    "runs are children (Q1)."),
)

# ── the nudges ──────────────────────────────────────────────────────────

NUDGE_LIST = OperationDescriptor(
    name="steward.nudges",
    version=1,
    description="List the steward's reviewer nudges for a project (proposed, sent or dismissed).",
    args_schema={
        "type": "object",
        "properties": {"project_id": _PROJECT_ID,
                       "state": {"type": ["string", "null"], "enum": ["proposed", "sent", "dismissed", None],
                                 "description": "Optional filter."}},
        "required": ["project_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="a list of nudges (step_id, state, repo, pr_number, reviewer_login, days, comment_text, host, receipt ...)",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/projects/{project_id}/nudges", "mcp:steward.nudges"),
    service="project_steward_service",
    method="nudges",
    admission=_ROOM_READ,
)

NUDGE_SEND = OperationDescriptor(
    name="nudge.send",
    version=1,
    description="Send a reviewer nudge you reviewed: it posts your text as a comment on the GitHub pull request.",
    args_schema={
        "type": "object",
        "properties": {"step_id": _STEP_ID,
                       "text": {"type": "string", "description": "The comment text (not empty); it is posted as you write it."}},
        "required": ["step_id", "text"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{step_id, state: sent, receipt ...} and the kernel operation_id and receipt",
    refusals=_CONTRACT_REFUSALS + ("nudge_not_found", "nudge_not_proposed", "empty_text", "the policy or gh refusals",
                                   "project_delegation_required"),
    completion="synchronous; steward.nudges shows it sent",
    exposure=("http:POST /api/nudges/{step_id}/send", "mcp:nudge.send"),
    service="project_steward_service",
    method="send_nudge_command",
    admission=Admission("admitted", "A GitHub comment: egress (Q1)."),
)

NUDGE_DISMISS = OperationDescriptor(
    name="nudge.dismiss",
    version=1,
    description="Dismiss a reviewer nudge without posting it. It does not come back for 7 days.",
    args_schema={"type": "object", "properties": {"step_id": _STEP_ID}, "required": ["step_id"],
                 "additionalProperties": False},
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{step_id, state: dismissed ...}, or {error} (nudge_not_found, nudge_not_proposed)",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous; steward.nudges shows it dismissed",
    exposure=("http:POST /api/nudges/{step_id}/dismiss", "mcp:nudge.dismiss"),
    service="project_steward_service",
    method="dismiss_nudge",
    admission=Admission("exempt", "The nudge's own state only (Q1)."),
)

# ── the watches ─────────────────────────────────────────────────────────


def _watch_row(name: str, description: str, method: str, exposure: tuple[str, ...], admission: Admission, *,
               result: str = "the watch with its rules", extra: Mapping[str, Any] | None = None,
               required: tuple[str, ...] = ("watch_id",), effect: str = "write",
               held: tuple[str, ...] = ("graduated_only",)) -> OperationDescriptor:
    return OperationDescriptor(
        name=name,
        version=1,
        description=description,
        args_schema={"type": "object", "properties": {"watch_id": _WATCH_ID, **dict(extra or {})},
                     "required": list(required), "additionalProperties": False},
        principal=_ROOM_PRINCIPAL + "; " + _GRADUATED,
        effect=effect,
        result=result,
        refusals=_WATCH_REFUSALS,
        completion="synchronous; project.watch.inspect returns the new state",
        exposure=exposure,
        service="watch_service",
        method=method,
        held=held,
        admission=admission,
    )


WATCH_INSPECT = _watch_row(
    "project.watch.inspect", "Read one watch of a project: its query, rules, state and last reads.",
    "get_watch", ("http:GET /api/watches/{watch_id}", "mcp:project.watch.inspect"), _ROOM_READ, effect="read",
)
WATCH_TEST = _watch_row(
    "project.watch.test", "Test a watch: one bounded read of its source (GitHub, Jira or Confluence) that changes nothing.",
    "test_watch", ("http:POST /api/watches/{watch_id}/test", "mcp:project.watch.test"),
    Admission("admitted", "Fetches the source (egress) and stores the test result (Q1)."),
    result="the test result (test_state, entities ...)",
)
WATCH_EVALUATE = _watch_row(
    "project.watch.evaluate", "Read a watch's source now and record what changed since its last read.",
    "evaluate_once", ("http:POST /api/watches/{watch_id}/evaluate", "mcp:project.watch.evaluate"),
    Admission("admitted", "Snapshot, diff, transitions; records effects the steward can act on: egress (Q1)."),
    result="{success: true, ...the evaluation}",
)
WATCH_SET_RULES = _watch_row(
    "project.watch.set_rules", "Set what a watch does when its source changes (its rules), and optionally how often it reads.",
    "set_rules", ("http:PUT /api/watches/{watch_id}/rules", "mcp:project.watch.set_rules"),
    Admission("admitted", "What the watch does and how often: changes what may act (Q1)."),
    extra={"rules": {"type": "array", "items": {"type": "object"}, "description": "The rule list (condition and actions)."},
           "evaluation_cadence_minutes": {"type": ["integer", "null"], "description": "Optional, 1 to 10080."}},
    required=("watch_id", "rules"),
)
WATCH_PAUSE = _watch_row(
    "project.watch.pause", "Pause a watch: it stops reading its source.",
    "pause_watch", ("http:POST /api/watches/{watch_id}/pause", "mcp:project.watch.pause"),
    Admission("admitted", "Stops scheduled source reads: controls a process (Q1)."),
)
WATCH_RESUME = _watch_row(
    "project.watch.resume", "Resume a paused watch: it reads its source on its schedule again.",
    "resume_watch", ("http:POST /api/watches/{watch_id}/resume", "mcp:project.watch.resume"),
    Admission("admitted", "Starts scheduled source reads: controls a process (Q1)."),
)
WATCH_RETIRE = _watch_row(
    "project.watch.retire", "Retire a watch: it stops for good and keeps its history.",
    "retire_watch", ("http:POST /api/watches/{watch_id}/retire", "mcp:project.watch.retire"),
    Admission("admitted", "Stops scheduled source reads for good: controls a process (Q1)."),
)
WATCH_UPDATE = _watch_row(
    "project.watch.update", "Change a watch's name, intent, query or trigger. A change to what it reads makes its "
                            "test and baseline stale.",
    "update_watch", ("http:PATCH /api/watches/{watch_id}",),
    Admission("admitted", "Changes what the watch reads and when: changes what may act (the charter's HTTP "
                          "capability exceptions)."),
    extra={"name": {"type": ["string", "null"]}, "intent": {"type": ["string", "null"]},
           "subject_kind": {"type": ["string", "null"]}, "query": {"type": ["object", "null"]},
           "trigger_kind": {"type": ["string", "null"]}, "trigger": {"type": ["object", "null"]}},
    held=(),
)
WATCH_BASELINE = _watch_row(
    "project.watch.baseline", "Take a watch's baseline: one read of its source that later changes compare to.",
    "baseline_watch", ("http:POST /api/watches/{watch_id}/baseline",),
    Admission("admitted", "A baseline read of the source: egress (the charter's HTTP capability exceptions)."),
    result="the baseline result", held=(),
)

# ── the suggested sources ───────────────────────────────────────────────

SUGGESTED_LIST = OperationDescriptor(
    name="project.suggested_sources",
    version=1,
    description="List the sources a project's meetings mention that the Room does not watch yet "
                "(GitHub owner/repo, Jira PROJ-123).",
    args_schema={"type": "object", "properties": {"project_id": _PROJECT_ID}, "required": ["project_id"],
                 "additionalProperties": False},
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="a list of pending suggestions (id, provider, reference, meeting_id, status, created_at)",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown project",),
    completion="synchronous",
    exposure=("http:GET /api/projects/{project_id}/suggested-sources", "mcp:project.suggested_sources"),
    service="suggested_source_service",
    method="pending",
    admission=_ROOM_READ,
)

SUGGESTED_ADD = OperationDescriptor(
    name="project.add_suggested_source",
    version=1,
    description="Watch a suggested source in the Room: it files the source in the Room and arms a watch that reads "
                "it on a schedule. When it cannot, it says why and the suggestion stays pending.",
    args_schema={
        "type": "object",
        "properties": {"project_id": _PROJECT_ID, "reference": _REFERENCE, "command_id": _COMMAND_ID},
        "required": ["project_id", "reference"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{suggestion (status accepted), resource (the filed source), watch (the armed watch)}",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown project, or no pending suggestion",
                                   "ServiceError jira_connection_required: no connected Jira account",
                                   "ServiceError source_unsupported", "project_delegation_required"),
    completion="synchronous; project.resource.list and project.get_room (sources) read it back",
    exposure=("http:POST /api/projects/{project_id}/suggested-sources/{ref}/add", "mcp:project.add_suggested_source"),
    service="suggested_source_service",
    method="add",
    admission=Admission("admitted", "Files the source in the Room and arms a watch that reads the provider "
                                    "(filing; arms egress, Q1)."),
)

SUGGESTED_DISMISS = OperationDescriptor(
    name="project.dismiss_suggested_source",
    version=1,
    description="Dismiss a suggested source: the Room does not suggest it again.",
    args_schema={
        "type": "object",
        "properties": {"project_id": _PROJECT_ID, "reference": _REFERENCE},
        "required": ["project_id", "reference"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{suggestion (status dismissed)}",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown project, or no pending suggestion",),
    completion="synchronous; project.suggested_sources no longer lists it",
    exposure=("http:POST /api/projects/{project_id}/suggested-sources/{ref}/dismiss", "mcp:project.dismiss_suggested_source"),
    service="suggested_source_service",
    method="dismiss",
    admission=Admission("exempt", "The suggestion never shows again (Q1)."),
)

# ── the connections ─────────────────────────────────────────────────────

CONNECTION_LIST = OperationDescriptor(
    name="connection.list",
    version=1,
    description="See your connections: GitHub, Jira and Confluence as last checked (each with its own check time, "
                "or never_checked), and Calendar and Models as they are now. It checks nothing.",
    args_schema={"type": "object", "properties": {}, "additionalProperties": False},
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{tools: [{provider_id, state, account, next_action, last_checked_at, checked_age_seconds, connections ...}]}",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous; a cached read (B1): no provider call",
    exposure=("http:GET /api/connections", "mcp:connection.list"),
    service="connections_service",
    method="list_tools",
    admission=_ROOM_READ,
)

CONNECTION_RECHECK = OperationDescriptor(
    name="connection.recheck",
    version=1,
    description="Check a connection again now: github, jira or confluence asks the provider and stores what it "
                "says; calendar and models read local state.",
    args_schema={
        "type": "object",
        "properties": {
            "provider_id": {"type": "string", "description": "github, jira, confluence, calendar or models: "
                                                             "tools[].provider_id from connection.list."},
            "ref": {"type": ["string", "null"], "description": "Optional, Jira or Confluence: one connection "
                                                               "(site|email): connections[].connection_ref from connection.list."},
        },
        "required": ["provider_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="the provider's tool entry, as connection.list gives it",
    refusals=_CONTRACT_REFUSALS + ("project_delegation_required",),
    completion="synchronous; connection.list shows the new check time",
    exposure=("http:POST /api/connections/{provider}/recheck", "mcp:connection.recheck"),
    service="connections_service",
    method="recheck",
    admission=Admission(
        "admitted_if",
        "github, jira, confluence: asks the provider and stores its state (egress, Q1; B1). calendar, models: "
        "local readiness, no egress.",
        ("provider_id",),
        holds=_remote,
    ),
)

# ── the Door's count (HTTP only) ────────────────────────────────────────

DOOR_COUNT = OperationDescriptor(
    name="project.door.count",
    version=1,
    description="Count what a GitHub or Jira source has now, for the Door's source rows: it reads the provider.",
    args_schema={
        "type": "object",
        "properties": {
            "provider": {"type": "string", "description": "github or jira."},
            "scope": {"description": "owner/repo for GitHub; {connection_ref, projects} for Jira."},
            "watches": {"type": ["array", "null"], "description": "Optional watch keys to count."},
            "adjust": {"type": ["object", "null"], "description": "Optional adjustments."},
        },
        "required": ["provider", "scope"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="the counts per watch key (count, label, host, counted_at)",
    refusals=_CONTRACT_REFUSALS + ("ValidationError validation", "project_delegation_required"),
    completion="synchronous",
    exposure=("http:POST /api/projects/door/count",),
    service="project_door_service",
    method="count",
    admission=Admission("admitted", "Fetches GitHub/Jira snapshots to count: egress (Q1; F21)."),
)

# ── delivery by copy and confirm (the Q0 ruling; R4-2) ──────────────────

UPDATE_MARK_DELIVERED = OperationDescriptor(
    name="project.mark_update_delivered",
    version=1,
    description="Mark it delivered: record that you delivered a published update yourself (to your boss, then to "
                "a peer ...). Each mark is its own record with its time and optional To. HoldSpeak delivers "
                "nothing. A mark without command_id is a new record every time; repeat a command_id to retry one mark.",
    args_schema={
        "type": "object",
        "properties": {
            "update_id": _UPDATE_ID,
            "delivered_to": {"type": ["string", "null"], "maxLength": 200,
                             "description": "Optional: who you delivered it to, in your words (200 characters at most)."},
            "command_id": _COMMAND_ID,
        },
        "required": ["update_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{success: true, delivery: {id, update_id, project_id, delivered_at, delivered_to, operation_id}} and the receipt",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown update", "ValidationError update_not_published",
                                   "idempotency_conflict", "project_delegation_required"),
    completion="synchronous; project.list_updates lists the delivery (deliveries, oldest first)",
    exposure=("http:POST /api/updates/{update_id}/delivered", "mcp:project.mark_update_delivered"),
    service="project_update_service",
    method="mark_update_delivered",
    owner_only=False,
    admission=Admission("admitted", "Each mark is final: its receipt proves he recorded that confirmation, not "
                                    "that anyone received anything. Owner-only: never in the grant (Q0; R4-2)."),
)

#: PHILO-9-02's rows, in export order.
STEWARD_CONNECTOR_OPERATIONS: tuple[OperationDescriptor, ...] = (
    STEWARD_CONFIGURE, STEWARD_RUN, STEWARD_STOP, STEWARD_READ_RUN, STEWARD_TRIGGER,
    NUDGE_LIST, NUDGE_SEND, NUDGE_DISMISS,
    WATCH_INSPECT, WATCH_TEST, WATCH_EVALUATE, WATCH_SET_RULES, WATCH_PAUSE, WATCH_RESUME, WATCH_RETIRE,
    WATCH_UPDATE, WATCH_BASELINE,
    SUGGESTED_LIST, SUGGESTED_ADD, SUGGESTED_DISMISS,
    CONNECTION_LIST, CONNECTION_RECHECK,
    DOOR_COUNT, UPDATE_MARK_DELIVERED,
)
