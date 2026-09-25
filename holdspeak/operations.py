"""The application-operation contract (PHILO-5-01).

One small, explicit descriptor module. Each :class:`OperationDescriptor` names
one application operation: its arguments (a closed JSON schema; an empty object
is lawful), its result and refusal shapes, how its completion is read back, and
which transport entry points expose it. :func:`bind` resolves every descriptor
to a method on a LIVE service instance, once, when the hub composes itself
(``runtime/composition.install_from_web_context``). HTTP routes and MCP dispatch
then call :meth:`OperationRegistry.invoke` instead of calling the service by
hand, so both transports reach the same declaration and the same instance.

What this module is not:

* not a decorator or plugin framework — the descriptor list below is the whole
  catalogue, and it grows story by story;
* not the model-tool projection (``services/tool_capability_service.py``) and
  not the kernel's ``OperationSpec`` (``kernel/model.py``) — those keep their
  narrower jobs;
* not an authorizer beyond one flag. The principal comes from the transport
  (the HTTP auth middleware, the MCP auth resolver); arguments can never carry
  authority, and :meth:`OperationRegistry.invoke` refuses an argument that
  tries. A descriptor marked ``owner_only`` refuses every non-owner principal
  by name (``owner_required``) before anything else runs.

Service errors (``NotFound``, ``ValueError``) pass through unchanged, so every
transport keeps its existing response mapping. Contract refusals raise
:class:`OperationRefused`, a ``ValueError``: HTTP routes already answer a
``ValueError`` with 400, and MCP already answers it with an ``isError`` result.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from holdspeak.principals import PrincipalKind
from holdspeak.services.errors import ServiceError

#: Argument names that would let a caller claim authority. The principal is a
#: transport fact; no operation accepts it as data.
AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {"principal", "principal_kind", "principal_identity", "actor", "owner",
     "identity", "authority", "as_principal", "on_behalf_of"}
)


#: PHILO-7-02: the kernel outcome of the last ``invoke`` in this context
#: (``{operation_id, receipt}`` for an admitted call, else ``None``).
_LAST_KERNEL: ContextVar[Optional[dict[str, Any]]] = ContextVar("operations_last_kernel", default=None)


class OperationRefused(ValueError):
    """A named refusal from the contract itself (never from the service)."""

    def __init__(self, code: str, operation: str, detail: str) -> None:
        self.code = code
        self.operation = operation
        self.detail = detail
        super().__init__(detail)


class OperationOwnerRequired(ServiceError):
    """``owner_required``: an owner-only operation called by any other principal.

    The same idiom as the owner-only services (``ModelLibraryApplicationService
    .require_owner``): a ``ServiceError`` with the code and a 403 status, so MCP
    answers ``{error, code: owner_required}`` and HTTP answers 403.
    """

    def __init__(self, operation: str) -> None:
        self.operation = operation
        super().__init__(
            "owner_required",
            f"{operation} requires the owner. An agent or node credential cannot call it.",
            context={"status": 403, "operation": operation},
        )


@dataclass(frozen=True)
class Admission:
    """Article XI admission, as the owner ruled it (PHILO-7 phase status, "The admission table").

    DECLARED by the descriptor; PHILO-7-02 enforces it (kernel admission and a
    receipt). ``rule`` is one of:

    * ``exempt`` -- no admission (a plain edit, a rename, a read);
    * ``admitted`` -- every call is admitted;
    * ``admitted_if`` -- admitted when ``condition`` holds. ``arguments`` names
      the arguments the condition reads, decided from the validated arguments
      BEFORE the service acts; an empty tuple means the condition reads stored
      state (the Thought-owned note).
    """

    rule: str
    condition: str
    arguments: tuple[str, ...] = ()
    #: For an argument condition: the condition itself, over the validated
    #: arguments (PHILO-7-01 round two, Astra finding 2 -- the words alone let
    #: a mapping ``member_ids`` read as exempt). ``None`` for a stored-state
    #: condition, which the arguments cannot decide.
    holds: Optional[Callable[[Mapping[str, Any]], bool]] = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if self.rule not in {"exempt", "admitted", "admitted_if"}:
            raise ValueError(f"unknown admission rule: {self.rule}")
        if self.rule == "admitted_if" and bool(self.arguments) != (self.holds is not None):
            raise ValueError("an argument condition needs its predicate; a stored-state one has none")

    def admits(self, args: Mapping[str, Any]) -> Optional[bool]:
        """Whether these validated arguments are admitted; ``None``: stored state decides."""
        if self.rule == "exempt":
            return False
        if self.rule == "admitted":
            return True
        return None if self.holds is None else bool(self.holds(args))

    def export(self) -> dict[str, Any]:
        return {"rule": self.rule, "condition": self.condition, "arguments": list(self.arguments)}


@dataclass(frozen=True)
class OperationDescriptor:
    """One application operation, stated once."""

    name: str
    version: int
    description: str
    #: Closed JSON schema for the arguments. ``{"type": "object",
    #: "properties": {}, "additionalProperties": False}`` is the empty object.
    args_schema: Mapping[str, Any]
    #: Where the principal comes from, and what the service does with it.
    principal: str
    #: ``read`` or ``write``.
    effect: str
    #: The result's shape, in words a client can act on.
    result: str
    #: Named refusals: the contract's own codes, then the service's errors.
    refusals: tuple[str, ...]
    #: How a caller knows the operation finished and reads its outcome back.
    completion: str
    #: The transport entry points that reach this operation.
    exposure: tuple[str, ...]
    #: The RuntimeServices field and method the hub binds this to.
    service: str
    method: str
    #: Inputs the TRANSPORT holds and passes beside the arguments -- a file the
    #: hub took custody of, a loaded configuration, a factory. No client can
    #: send them; they are never arguments and never validated as data.
    held: tuple[str, ...] = ()
    #: Only an OWNER principal may call it (PHILO-5-02 r2, Astra's check on
    #: built finding 1). :meth:`OperationRegistry.authorize` refuses every other
    #: principal with ``owner_required``, before any argument or held input is
    #: read. A transport that touches the filesystem for the operation calls
    #: ``authorize`` first.
    owner_only: bool = False
    #: Article XI admission (PHILO-7-01 declares it for the desk slice; story
    #: 02 enforces it). ``None``: not yet declared for this operation.
    admission: Optional[Admission] = None

    def __post_init__(self) -> None:
        Draft202012Validator.check_schema(dict(self.args_schema))
        if self.args_schema.get("type") != "object":
            raise ValueError(f"{self.name}: args_schema must describe an object")
        if self.effect not in {"read", "write"}:
            raise ValueError(f"{self.name}: effect must be read or write")
        object.__setattr__(self, "args_schema", MappingProxyType(dict(self.args_schema)))

    def export(self) -> dict[str, Any]:
        """The public, transport-neutral view (``docs/generated/operations.json``)."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "args_schema": _plain(self.args_schema),
            "principal": self.principal,
            "effect": self.effect,
            "result": self.result,
            "refusals": list(self.refusals),
            "completion": self.completion,
            "exposure": list(self.exposure),
            "held": list(self.held),
            "owner_only": self.owner_only,
            "admission": self.admission.export() if self.admission is not None else None,
        }


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


# ── the catalogue ─────────────────────────────────────────────────────────

_CONTRACT_REFUSALS = ("unknown_operation", "invalid_arguments", "authority_in_arguments")
_TRANSPORT_PRINCIPAL = (
    "derived by the transport (HTTP auth middleware; MCP auth resolver); "
    "the desk decision service performs no principal check of its own"
)

# Every field is type-permissive (PHILO-5-01 r2, Astra's check on built): both
# transports passed any value straight to the service before this contract, and
# the service and repository coerce it (``title=123`` is stored as "123";
# ``decided_at=20260924`` as "20260924"; a non-list ``tags`` as []). The
# contract preserves every input the service accepted; it refuses only what was
# Exception (ratified, Astra r2 2026-09-24): authority fields inside update data are REFUSED — on main eight of them were accepted-and-ignored and `principal` already failed (positional collision); arguments cannot supply authority.
# already refused (an unknown field on create, once a Python ``TypeError``).
_DECISION_FIELDS: dict[str, Any] = {
    "title": {"description": "Text; defaults to 'New decision'."},
    "status": {"description": "proposed, accepted, superseded or deprecated."},
    "deciders": {"description": "A list of names."},
    "decided_at": {"description": "A date, as text."},
    "context_markdown": {"description": "Markdown text."},
    "decision_markdown": {"description": "Markdown text."},
    "alternatives": {"description": "Objects with name and reason."},
    "consequences_markdown": {"description": "Markdown text."},
    "tags": {"description": "A list of tags."},
}

DECISION_CREATE = OperationDescriptor(
    name="decision.create",
    version=1,
    description="Record one desk decision. Every field is optional; the title defaults to 'New decision' and the status to 'proposed'.",
    args_schema={
        "type": "object",
        "properties": {"decision_id": {"description": "Optional; a new id is made when absent."}, **_DECISION_FIELDS},
        "additionalProperties": False,
    },
    principal=_TRANSPORT_PRINCIPAL,
    effect="write",
    result="the decision record (id, title, status, deciders, decided_at, the three markdown fields, alternatives, superseded_by, tags, created_at, updated_at, deleted)",
    refusals=_CONTRACT_REFUSALS + ("ValueError: invalid decision status",),
    completion="synchronous; the returned id reads back through decision.read; one desk_changed frame (kind decision, op create) on the hub bus",
    exposure=("http:POST /api/decisions", "mcp:desk.create[kind=decisions]", "mcp:desk.verb[verb_id=desk.create,kind=decisions]"),
    service="primitive_service",
    method="create_decision",
    admission=Admission("admitted", "A decision made (D3)."),
)

DECISION_UPDATE = OperationDescriptor(
    name="decision.update",
    version=1,
    description="Change fields of one desk decision. Only the supplied fields change; null leaves a field as it is; unknown fields are ignored.",
    args_schema={
        "type": "object",
        "properties": {
            "decision_id": {"type": "string"},
            **_DECISION_FIELDS,
            "superseded_by": {"description": "The id of the decision that replaces this one."},
        },
        "required": ["decision_id"],
        # Preserved on purpose: both transports passed any field through and
        # the repository ignores the ones it does not know (the desk's rename
        # sends ``name`` for a decision today).
        "additionalProperties": True,
    },
    principal=_TRANSPORT_PRINCIPAL,
    effect="write",
    result="the updated decision record",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown decision", "ValueError: invalid decision status"),
    completion="synchronous; decision.read returns the new state; one desk_changed frame (kind decision, op update) on the hub bus",
    exposure=("http:PUT /api/decisions/{decision_id}", "mcp:desk.update[kind=decisions]", "mcp:desk.verb[verb_id=desk.update,kind=decisions]"),
    service="primitive_service",
    method="update_decision",
    admission=Admission("admitted", "A decision changed (D3)."),
)

DECISION_READ = OperationDescriptor(
    name="decision.read",
    version=1,
    description="Read one desk decision by id.",
    args_schema={
        "type": "object",
        "properties": {"decision_id": {"type": "string"}},
        "required": ["decision_id"],
        "additionalProperties": False,
    },
    principal=_TRANSPORT_PRINCIPAL,
    effect="read",
    result="the decision record",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown decision",),
    completion="synchronous",
    exposure=("http:GET /api/decisions/{decision_id}", "mcp:desk.get[kind=decisions]", "mcp-resource:holdspeak://primitives/decisions/{id}"),
    service="primitive_service",
    method="get_decision",
    admission=Admission("exempt", "A read: computation without effect (Article XI.5)."),
)

DECISION_LIST = OperationDescriptor(
    name="decision.list",
    version=1,
    description="List the desk decisions that are not deleted, most recently updated first. The empty object lists up to 500; limit asks for 1 to 2000.",
    args_schema={
        "type": "object",
        # PHILO-5-01 r2: HTTP's ``?limit=`` passes through (it was a slice of
        # an already-limited result, so a limit above 500 lost rows).
        "properties": {"limit": {"type": "integer", "description": "Clamped to 1..2000; default 500."}},
        "additionalProperties": False,
    },
    principal=_TRANSPORT_PRINCIPAL,
    effect="read",
    result="a list of decision records",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/decisions", "mcp:desk.list[kind=decisions]"),
    service="primitive_service",
    method="list_decisions",
    admission=Admission("exempt", "A read: computation without effect (Article XI.5)."),
)

# ── PHILO-5-02: the rest of the loop ──────────────────────────────────────
#
# The same rule as the decision fields: a field is only as strict as BOTH
# transports already were. Each transport keeps its own published schema
# (FastAPI parameters, the MCP inputSchema, the closed-body checks of the
# Thought routes); the service keeps its own named refusals. The descriptor
# closes the argument NAMES and states the shapes the transports guarantee.

_OWNER_PRINCIPAL = (
    "derived by the transport (HTTP auth middleware; MCP auth resolver) and "
    "passed to the service unchanged"
)
_NULLABLE_STRING = {"type": ["string", "null"]}

MEETING_LIST = OperationDescriptor(
    name="meeting.list",
    version=1,
    description="List or search the archived meetings, newest first, with optional filters. The empty object lists the first 50.",
    args_schema={
        "type": "object",
        "properties": {
            "query": {**_NULLABLE_STRING, "description": "Full-text search."},
            "from_date": _NULLABLE_STRING,
            "to_date": _NULLABLE_STRING,
            "speaker": _NULLABLE_STRING,
            "tag": _NULLABLE_STRING,
            "has_open_actions": {"type": ["boolean", "null"]},
            "limit": {"type": "integer", "description": "Clamped to 1..500; default 50."},
            "cursor": {"type": ["string", "integer", "null"], "description": "An offset or the previous page's next_cursor."},
        },
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="read",
    result="{meetings: [meeting summaries], total, next_cursor} (HTTP drops next_cursor; its offset is the cursor)",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/meetings", "mcp:meeting.list"),
    service="meeting_service",
    method="list_meetings",
)

MEETING_READ = OperationDescriptor(
    name="meeting.read",
    version=1,
    description="Read one meeting: transcript, summary, intelligence job state, the planned route with its selection hash, and the run receipt. This is also how a summary run and an import are read back.",
    args_schema={
        "type": "object",
        "properties": {
            "meeting_id": {"type": "string"},
            "include": {**_NULLABLE_STRING, "description": "Optional detail selector (MCP)."},
        },
        "required": ["meeting_id"],
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="read",
    result="the meeting detail (planned_route.selection_hash, intel, intel_status, run_receipt, segments ...)",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown meeting", "ValidationError: meeting id is required"),
    completion="synchronous",
    exposure=("http:GET /api/meetings/{meeting_id}", "mcp:meeting.get", "mcp-resource:holdspeak://meetings/{meeting_id}"),
    service="meeting_service",
    method="get_meeting",
)

MEETING_IMPORT = OperationDescriptor(
    name="meeting.import",
    version=1,
    description="Import one recording or transcript file the hub already holds. Makes the visible importing meeting now and transcribes in the background.",
    args_schema={
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "The original file name; its extension picks audio or transcript."},
            "title": {**_NULLABLE_STRING, "description": "Defaults to the file name without its extension."},
            "speaker": _NULLABLE_STRING,
            "tags": {"type": "array", "items": {"type": "string"}},
            "occurred_at": {**_NULLABLE_STRING, "description": "ISO 8601 date and time the meeting happened; defaults to now."},
        },
        "required": ["filename"],
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL + "; the background transcription runs under that same principal",
    effect="write",
    result="{meeting_id, status: importing}",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "ValidationError: occurred_at is not an ISO 8601 date and time",),
    completion="asynchronous; read meeting.read until intel_status leaves importing (import_failed carries the reason); one desk_changed frame (kind meeting, op update) when the worker ends",
    exposure=("http:POST /api/meetings/import", "mcp:meeting.import"),
    service="meeting_service",
    method="import_held_file",
    # Gap E: custody, configuration and the transcriber stay transport work.
    held=("tmp_path", "config", "transcriber_factory"),
    # r2 (Astra finding 1): the MCP intake opens a caller-named hub path; only
    # the owner may make the hub read its own filesystem.
    owner_only=True,
)

MEETING_SUMMARY_RUN = OperationDescriptor(
    name="meeting.summary.run",
    version=1,
    description="Queue a fresh summary (meeting intelligence) run with the selection hash read from meeting.read. Refused when the hash is absent or stale, or the meeting has no transcript.",
    args_schema={
        "type": "object",
        "properties": {
            "meeting_id": {"type": "string"},
            "expected_selection_hash": {"description": "planned_route.selection_hash from meeting.read."},
        },
        "required": ["meeting_id"],
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="write",
    result="{jobId, state: queued, host, drainer, expectedWithinSeconds, planned_route, run_receipt}",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown meeting", "ConflictError: empty | stale selection hash | reserved | running | ready (with planned_route, run_receipt, last_refusal)"),
    completion="asynchronous; one runtime_queue frame on the hub bus when queued; read meeting.read for the job state, the summary and the run receipt",
    exposure=("http:POST /api/meetings/{meeting_id}/intelligence/run", "mcp:meeting.run_intelligence"),
    service="meeting_intel_service",
    method="run_intelligence",
)

_EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}

BRIEF_GENERATE = OperationDescriptor(
    name="brief.generate",
    version=1,
    description="Make today's brief from durable sources on the producer's clock. A second call on the same producer day returns that day's brief.",
    args_schema=_EMPTY,
    principal=_OWNER_PRINCIPAL,
    effect="write",
    result="the brief (id, generated_at, period_start, period_end, sections with brief-scoped item ids, shelf)",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous; brief.latest returns it",
    exposure=("http:POST /api/brief/generate", "mcp:monday_brief.generate", "mcp:monday_brief.get[generate=true]"),
    service="monday_brief_service",
    method="generate",
)

BRIEF_LATEST = OperationDescriptor(
    name="brief.latest",
    version=1,
    description="Read the most recently made brief, or nothing when none exists.",
    args_schema=_EMPTY,
    principal=_OWNER_PRINCIPAL,
    effect="read",
    result="the brief, or null",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/brief/latest", "mcp:monday_brief.get", "mcp-resource:holdspeak://briefs/latest"),
    service="monday_brief_service",
    method="get_latest",
)

BRIEF_SHELF_WRITE = OperationDescriptor(
    name="brief.shelf.write",
    version=1,
    description="Set one brief item's triage state: acknowledged, deferred, or null to return it to untouched.",
    args_schema={
        "type": "object",
        "properties": {
            "item_id": {"type": "string"},
            # The service names an unknown state ("Unknown shelf state: x");
            # the contract does not pre-empt that refusal.
            "state": {**_NULLABLE_STRING, "description": "acknowledged, deferred or null."},
        },
        "required": ["item_id", "state"],
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="write",
    result="{item_id, state}",
    refusals=_CONTRACT_REFUSALS + ("LookupError: unknown brief item", "ValueError: unknown shelf state"),
    completion="synchronous; brief.shelf.read returns the new state",
    exposure=("http:POST /api/brief/items/{item_id}/shelf", "mcp:monday_brief.shelf"),
    service="monday_brief_service",
    method="shelve",
)

BRIEF_SHELF_READ = OperationDescriptor(
    name="brief.shelf.read",
    version=1,
    description="Read the triage states of the latest brief's items.",
    args_schema=_EMPTY,
    principal=_OWNER_PRINCIPAL,
    effect="read",
    result="{item_id: state} for the latest brief; {} when there is none",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/brief/shelf", "mcp:monday_brief.shelf_read"),
    service="monday_brief_service",
    method="shelf",
)

# The Thought fields stay type-permissive for the same reason as the decision
# fields: the service names every bad value with its own code
# (``thought_create_request_invalid``, ``revision_conflict`` ...), and a JSON
# schema type error would replace that named refusal with a generic one.
_ANY = {}

THOUGHT_CREATE = OperationDescriptor(
    name="thought.create",
    version=1,
    description="Make one durable Thought from raw text, with the hub's default AI context applied.",
    args_schema={
        "type": "object",
        "properties": {"request_id": _ANY, "raw_text": _ANY, "source": _ANY, "initial_note": _ANY},
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="write",
    result="{thought, default_context_receipt}",
    refusals=_CONTRACT_REFUSALS + ("ValidationError / ConflictError with the Thought service's own codes",),
    completion="synchronous; thought.read returns it",
    exposure=("http:POST /api/thoughts", "mcp:thought.create"),
    service="refinement_service",
    method="create_thought",
)

THOUGHT_SAVE = OperationDescriptor(
    name="thought.save",
    version=1,
    description="Save the working copy of one Thought under its revision checks (KEPT). Never invokes a model and never completes the Thought.",
    args_schema={
        "type": "object",
        "properties": {
            "thought_id": {"type": "string"},
            "expected_aggregate_revision": _ANY,
            "expected_working_revision": _ANY,
            "title": _ANY,
            "body_markdown": _ANY,
            "tags": _ANY,
            "workspace_cursor": _ANY,
        },
        "required": ["thought_id"],
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="write",
    result="{thought (working_note.last_modified moves), workbench}",
    refusals=_CONTRACT_REFUSALS + ("ConflictError: revision_conflict | workspace_cursor_conflict (with the workbench)", "NotFound: unknown thought"),
    completion="synchronous; thought.read and thought.workbench.read return the saved state",
    exposure=("http:PATCH /api/thoughts/{thought_id}/working", "mcp:thought.update_working"),
    service="refinement_service",
    method="update_working",
)

THOUGHT_READ = OperationDescriptor(
    name="thought.read",
    version=1,
    description="Read one Thought: its working note, revisions and lifecycle.",
    args_schema={
        "type": "object",
        "properties": {"thought_id": {"type": "string"}},
        "required": ["thought_id"],
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="read",
    result="the Thought",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown thought",),
    completion="synchronous",
    exposure=("http:GET /api/thoughts/{thought_id}", "mcp-resource:holdspeak://thoughts/{thought_id}"),
    service="refinement_service",
    method="get_thought",
)

THOUGHT_WORKBENCH_READ = OperationDescriptor(
    name="thought.workbench.read",
    version=1,
    description="Read one Thought's workbench: the Thought, its context, its review state and the workspace cursor.",
    args_schema={
        "type": "object",
        "properties": {"thought_id": {"type": "string"}},
        "required": ["thought_id"],
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="read",
    result="the workbench",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown thought",),
    completion="synchronous",
    exposure=("http:GET /api/thoughts/{thought_id}/workbench", "mcp-resource:holdspeak://thoughts/{thought_id}/workbench"),
    service="refinement_service",
    method="get_workbench",
)

THOUGHT_LIST = OperationDescriptor(
    name="thought.list",
    version=1,
    description="List the unfinished Thoughts, one page at a time.",
    args_schema={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "Default 20."},
            "cursor": _NULLABLE_STRING,
        },
        "additionalProperties": False,
    },
    principal=_OWNER_PRINCIPAL,
    effect="read",
    result="{items, next_cursor}",
    refusals=_CONTRACT_REFUSALS + ("ValidationError with the Thought service's own codes",),
    completion="synchronous",
    exposure=("http:GET /api/thoughts?state=unfinished", "mcp-resource:holdspeak://thoughts/unfinished"),
    service="refinement_service",
    method="list_unfinished",
)

# ── PHILO-7-01: notes, zones (directories) and knowledge bases ────────────
#
# One explicit row per (kind, verb): the Phase 7 slice table. Each row names
# the real PrimitiveService callable; no row resolves a callable from a kind
# string. The fields are type-permissive for the reason the decision fields
# are: both transports passed any value straight to the service before this
# contract, and the service or repository coerces it (``title=123`` is stored
# as "123"). Argument NAMES are closed: an unknown name was a Python
# ``TypeError`` before (the service takes closed keyword arguments); it is now
# refused by name. Each row declares its Article XI admission (story 02
# enforces it).

_DESK_PRINCIPAL = (
    "derived by the transport (HTTP auth middleware; MCP auth resolver); "
    "the desk primitive service performs no principal check of its own "
    "(a Thought's note: the Thought service's own owner check applies)"
)
_EXEMPT_READ = Admission("exempt", "A read: computation without effect (Article XI.5).")
_NOTE_RECORD = "the note record (id, title, body_markdown, tags, created_at, updated_at, last_modified, deleted)"
_THOUGHT_NOTE = (
    "; for a Thought's note, the working note plus its retry cursors "
    "(state, aggregate_revision, lifecycle_revision, working_revision, attachment_revision)"
)
_THOUGHT_REFUSALS = (
    "ConflictError thought_expected_revision_required: the note belongs to a Thought and the expected revisions are absent",
    "ConflictError / ValidationError with the Thought service's own codes (revision_conflict ...)",
)
_ZONE_RECORD = "the zone record (id, name, name_normalized, parent_id, created_at, last_modified, deleted)"
_KB_RECORD = "the knowledge base record (id, name, member_ids, created_at, last_modified, deleted)"
_ZONE_NAME_REFUSALS = (
    "ValidationError: zone name is required | zone name must be 64 characters or fewer",
    "ConflictError zone_name_taken (existing_name): another live zone has this name, ignoring case",
)

NOTE_CREATE = OperationDescriptor(
    name="note.create",
    version=1,
    description="Make one desk note. Every field is optional; a new id is made when note_id is absent.",
    args_schema={
        "type": "object",
        "properties": {
            "note_id": {"description": "Optional. A new id is made when absent. The id of a Thought's note is refused."},
            "title": {"description": "Text; defaults to empty."},
            "body_markdown": {"description": "Markdown text; defaults to empty."},
            "tags": {"description": "A list of tags."},
        },
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result=_NOTE_RECORD,
    refusals=_CONTRACT_REFUSALS + _THOUGHT_REFUSALS[:1],
    completion="synchronous; note.read returns it; one desk_changed frame (kind note, op create) on the hub bus",
    exposure=("http:POST /api/notes", "mcp:desk.create[kind=notes]", "mcp:desk.verb[verb_id=desk.create,kind=notes]"),
    service="primitive_service",
    method="create_note",
    admission=Admission("exempt", "A plain edit: no placement field (D3)."),
)

NOTE_READ = OperationDescriptor(
    name="note.read",
    version=1,
    description="Read one desk note by id.",
    args_schema={
        "type": "object",
        "properties": {"note_id": {"type": "string"}},
        "required": ["note_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="read",
    result=_NOTE_RECORD,
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown note",),
    completion="synchronous",
    exposure=("http:GET /api/notes/{note_id}", "mcp:desk.get[kind=notes]", "mcp-resource:holdspeak://primitives/notes/{id}"),
    service="primitive_service",
    method="get_note",
    admission=_EXEMPT_READ,
)

NOTE_UPDATE = OperationDescriptor(
    name="note.update",
    version=1,
    description=(
        "Change fields of one desk note. Only the supplied fields change; null leaves a field as it is. "
        "A Thought's note is saved through the Thought service and needs both expected revisions."
    ),
    args_schema={
        "type": "object",
        "properties": {
            "note_id": {"type": "string"},
            "title": {"description": "Text."},
            "body_markdown": {"description": "Markdown text."},
            "tags": {"description": "A list of tags."},
            "expected_aggregate_revision": {"description": "A Thought's note only: aggregate_revision from the last read."},
            "expected_working_revision": {"description": "A Thought's note only: working_revision from the last read."},
        },
        "required": ["note_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result=_NOTE_RECORD + _THOUGHT_NOTE,
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown note",) + _THOUGHT_REFUSALS,
    completion="synchronous; note.read returns the new state; one desk_changed frame (kind note, op update) for a plain note",
    exposure=("http:PUT /api/notes/{note_id}", "mcp:desk.update[kind=notes]", "mcp:desk.verb[verb_id=desk.update,kind=notes]"),
    service="primitive_service",
    method="update_note",
    admission=Admission("exempt", "A plain edit (title, body, tags) or a Thought save (D3)."),
)

NOTE_DELETE = OperationDescriptor(
    name="note.delete",
    version=1,
    description=(
        "Delete one desk note (a tombstone). A Thought's note is tombstoned through the Thought service "
        "and needs both expected revisions."
    ),
    args_schema={
        "type": "object",
        "properties": {
            "note_id": {"type": "string"},
            "expected_aggregate_revision": {"description": "A Thought's note only: aggregate_revision from the last read."},
            "expected_lifecycle_revision": {"description": "A Thought's note only: lifecycle_revision from the last read."},
        },
        "required": ["note_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result="true for a plain note" + _THOUGHT_NOTE + " (the tombstoned note)",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown note",) + _THOUGHT_REFUSALS,
    completion="synchronous; note.read then refuses the id (NotFound); one desk_changed frame (kind note, op delete) for a plain note",
    exposure=("http:DELETE /api/notes/{note_id}", "mcp:desk.delete[kind=notes]", "mcp:desk.verb[verb_id=desk.delete,kind=notes]"),
    service="primitive_service",
    method="delete_note",
    admission=Admission(
        "admitted_if",
        "The note belongs to a Thought: its tombstone unfiles the note from its zone "
        "(db/refinement_thoughts.py:236). A plain note's delete is exempt: its zone membership row stays.",
    ),
)

NOTE_LIST = OperationDescriptor(
    name="note.list",
    version=1,
    description="List the desk notes that are not deleted (up to 500). With tag, only the notes that carry it.",
    args_schema={
        "type": "object",
        "properties": {"tag": {**_NULLABLE_STRING, "description": "Optional. One tag."}},
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="read",
    result="a list of note records",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/notes", "mcp:desk.list[kind=notes]"),
    service="primitive_service",
    method="list_notes",
    admission=_EXEMPT_READ,
)

ZONE_CREATE = OperationDescriptor(
    name="zone.create",
    version=1,
    description="Make one zone (a desk directory), at the desk root or inside another zone.",
    args_schema={
        "type": "object",
        "properties": {
            "directory_id": {"description": "Optional. A new id is made when absent. The id of an existing zone sets that zone's parent_id (it can move it)."},
            "name": {"description": "1 to 64 characters after trimming; unique among the live zones, ignoring case."},
            "parent_id": {"description": "Optional. The id of the zone to put this zone in; absent or null: the desk root."},
        },
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result=_ZONE_RECORD,
    refusals=_CONTRACT_REFUSALS + _ZONE_NAME_REFUSALS,
    completion="synchronous; zone.read returns it; one desk_changed frame (kind directory, op create) on the hub bus",
    exposure=("http:POST /api/directories", "mcp:desk.create[kind=directories]", "mcp:desk.verb[verb_id=desk.create,kind=directories]"),
    service="primitive_service",
    method="create_directory",
    admission=Admission(
        "admitted_if",
        "directory_id is given and not empty: over an existing zone the create sets its parent_id "
        "(to parent_id or null), so it can move that zone with its contents. Without directory_id: exempt.",
        ("directory_id",),
        holds=lambda args: bool(args.get("directory_id")),
    ),
)

ZONE_READ = OperationDescriptor(
    name="zone.read",
    version=1,
    description="Read one zone and what is filed in it.",
    args_schema={
        "type": "object",
        "properties": {"directory_id": {"type": "string"}},
        "required": ["directory_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="read",
    result="{directory: the zone record, member_ids: the filed primitive refs, members: the membership records}",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown directory",),
    completion="synchronous",
    exposure=("http:GET /api/directories/{directory_id}", "mcp:desk.get[kind=directories]", "mcp-resource:holdspeak://primitives/directories/{id}"),
    service="primitive_service",
    method="get_directory",
    admission=_EXEMPT_READ,
)

ZONE_UPDATE = OperationDescriptor(
    name="zone.update",
    version=1,
    description=(
        "Rename a zone or move it. A rename (no parent_id) writes the name only. "
        "parent_id moves the zone with its contents: absent leaves it where it is; null moves it to the desk root."
    ),
    args_schema={
        "type": "object",
        "properties": {
            "directory_id": {"type": "string"},
            "name": {"description": "The new name; null or absent keeps the name."},
            "parent_id": {"description": "Optional. The id of the new parent zone, or null for the desk root. Absent: the zone does not move."},
        },
        "required": ["directory_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result=_ZONE_RECORD,
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown directory",) + _ZONE_NAME_REFUSALS,
    completion="synchronous; zone.read returns the new state; one desk_changed frame (kind directory, op update) on the hub bus",
    exposure=("http:PUT /api/directories/{directory_id}", "mcp:desk.update[kind=directories]", "mcp:desk.verb[verb_id=desk.update,kind=directories]"),
    service="primitive_service",
    method="update_directory",
    admission=Admission(
        "admitted_if",
        "parent_id is present (null included): the zone moves with its contents. "
        "A rename alone (no parent_id) is exempt and writes the name only (PHILO-7-01 rename repair).",
        ("parent_id",),
        holds=lambda args: "parent_id" in args,
    ),
)

ZONE_DELETE = OperationDescriptor(
    name="zone.delete",
    version=1,
    description="Delete one zone. What is filed in it goes back to the desk root; its child zones move to the root.",
    args_schema={
        "type": "object",
        "properties": {"directory_id": {"type": "string"}},
        "required": ["directory_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result="true",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown directory",),
    completion="synchronous; zone.read then refuses the id (NotFound); one desk_changed frame (kind directory, op delete) on the hub bus",
    exposure=("http:DELETE /api/directories/{directory_id}", "mcp:desk.delete[kind=directories]", "mcp:desk.verb[verb_id=desk.delete,kind=directories]"),
    service="primitive_service",
    method="delete_directory",
    admission=Admission(
        "admitted",
        "Every member unfiled and every child zone moved to the root, in the same transaction (db/primitives.py:1182-1204).",
    ),
)

ZONE_LIST = OperationDescriptor(
    name="zone.list",
    version=1,
    description="List the zones that are not deleted, by name. Each row carries member_ids: what is filed in it.",
    args_schema=_EMPTY,
    principal=_DESK_PRINCIPAL,
    effect="read",
    result="a list of zone records, each with member_ids",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/directories", "mcp:desk.list[kind=directories]"),
    service="primitive_service",
    method="list_directories",
    admission=_EXEMPT_READ,
)

KB_CREATE = OperationDescriptor(
    name="kb.create",
    version=1,
    description="Make one knowledge base: a named set of references to desk objects.",
    args_schema={
        "type": "object",
        "properties": {
            "kb_id": {"description": "Optional. A new id is made when absent. The id of an existing knowledge base REPLACES its members with member_ids."},
            "name": {"description": "Required text (not empty)."},
            "member_ids": {"description": "Optional. A list of kind:id references, for example note:<id> (a mapping is also accepted: its keys are the references)."},
        },
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result=_KB_RECORD,
    refusals=_CONTRACT_REFUSALS + ("ValidationError: kb name is required",),
    completion="synchronous; kb.read returns it; one desk_changed frame (kind kb, op create) on the hub bus",
    exposure=("http:POST /api/kbs", "mcp:desk.create[kind=kbs]", "mcp:desk.verb[verb_id=desk.create,kind=kbs]"),
    service="primitive_service",
    method="create_kb",
    admission=Admission(
        "admitted_if",
        "member_ids is given and not empty, in any accepted form (a list; a mapping, whose keys the "
        "repository files as references; any other non-empty value), or kb_id is given and not empty: "
        "knowledge memberships can be written (over an existing kb_id the membership set is REPLACED). "
        "Otherwise exempt.",
        ("member_ids", "kb_id"),
        holds=lambda args: bool(args.get("member_ids")) or bool(args.get("kb_id")),
    ),
)

KB_READ = OperationDescriptor(
    name="kb.read",
    version=1,
    description="Read one knowledge base by id.",
    args_schema={
        "type": "object",
        "properties": {"kb_id": {"type": "string"}},
        "required": ["kb_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="read",
    result=_KB_RECORD,
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown kb",),
    completion="synchronous",
    exposure=("http:GET /api/kbs/{kb_id}", "mcp:desk.get[kind=kbs]", "mcp-resource:holdspeak://primitives/kbs/{id}"),
    service="primitive_service",
    method="get_kb",
    admission=_EXEMPT_READ,
)

KB_UPDATE = OperationDescriptor(
    name="kb.update",
    version=1,
    description=(
        "Rename a knowledge base or set its members. A rename (no member_ids) writes the name only. "
        "member_ids makes the member set exactly that list."
    ),
    args_schema={
        "type": "object",
        "properties": {
            "kb_id": {"type": "string"},
            "name": {"description": "The new name; null or absent keeps the name."},
            "member_ids": {"description": "Optional. The complete new list of kind:id references. Absent or null: the members do not change."},
        },
        "required": ["kb_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result=_KB_RECORD,
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown kb",),
    completion="synchronous; kb.read returns the new state; one desk_changed frame (kind kb, op update) on the hub bus",
    exposure=("http:PUT /api/kbs/{kb_id}", "mcp:desk.update[kind=kbs]", "mcp:desk.verb[verb_id=desk.update,kind=kbs]"),
    service="primitive_service",
    method="update_kb",
    admission=Admission(
        "admitted_if",
        "member_ids is present and not null, in any accepted form (a list; a mapping, whose keys the "
        "repository files as references; an empty value removes every member): knowledge memberships are "
        "added and removed to match it. A rename alone is exempt and writes the name only (PHILO-7-01 rename repair).",
        ("member_ids",),
        holds=lambda args: args.get("member_ids") is not None,
    ),
)

KB_DELETE = OperationDescriptor(
    name="kb.delete",
    version=1,
    description="Delete one knowledge base (a tombstone). Its membership rows are not changed.",
    args_schema={
        "type": "object",
        "properties": {"kb_id": {"type": "string"}},
        "required": ["kb_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result="true",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown kb",),
    completion="synchronous; kb.read then refuses the id (NotFound); one desk_changed frame (kind kb, op delete) on the hub bus",
    exposure=("http:DELETE /api/kbs/{kb_id}", "mcp:desk.delete[kind=kbs]", "mcp:desk.verb[verb_id=desk.delete,kind=kbs]"),
    service="primitive_service",
    method="delete_kb",
    admission=Admission("exempt", "The knowledge base row is tombstoned; its membership rows are not touched (R4)."),
)

KB_LIST = OperationDescriptor(
    name="kb.list",
    version=1,
    description="List the knowledge bases that are not deleted, by name.",
    args_schema=_EMPTY,
    principal=_DESK_PRINCIPAL,
    effect="read",
    result="a list of knowledge base records",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/kbs", "mcp:desk.list[kind=kbs]"),
    service="primitive_service",
    method="list_kbs",
    admission=_EXEMPT_READ,
)

# ── PHILO-7-02: membership and the remaining decision operations ─────────
#
# The same rules as the rows above: argument NAMES closed, values as permissive
# as both transports already were; each row names its real PrimitiveService
# method and its Article XI admission (phase status, "The admission table";
# the owner's D3 and R4). Story 02 ENFORCES every admission: an admitted call
# runs the complete kernel path (``holdspeak/services/desk_kernel.py``).

_MEMBERSHIP_RECORD = "the membership record (primitive_id as kind:id, directory_id, created_at, last_modified, deleted)"
_KB_MEMBER_RECORD = "the knowledge membership record (knowledge_id, resource_ref, created_at, last_modified, deleted)"
_DECISION_ID = {"type": "string", "description": "The decision id, from desk.list kind=decisions."}

ZONE_FILE = OperationDescriptor(
    name="zone.file",
    version=1,
    description="File one desk object into a zone. An object is in one zone only: filing it again moves it.",
    args_schema={
        "type": "object",
        "properties": {
            "directory_id": {"type": "string", "description": "The zone id, from zone.list."},
            "primitive_id": {"type": "string", "description": "The object, as kind:id (for a note, note:<id>); a bare id is read as that id's kind."},
        },
        "required": ["directory_id", "primitive_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result=_MEMBERSHIP_RECORD,
    refusals=_CONTRACT_REFUSALS + (
        "NotFound: unknown directory",
        "ConflictError thought_tombstoned: the note belongs to a tombstoned Thought",
    ),
    completion="synchronous; zone.members lists it; one desk_changed frame (kind directory, op update) on the hub bus",
    exposure=("http:PUT /api/directories/{directory_id}/members/{primitive_id}", "mcp:zone.file"),
    service="primitive_service",
    method="file_member",
    admission=Admission("admitted", "A primitive filed; a re-file moves it (D3)."),
)

ZONE_UNFILE = OperationDescriptor(
    name="zone.unfile",
    version=1,
    description="Take one desk object out of the zone it is filed in.",
    args_schema={
        "type": "object",
        "properties": {
            "directory_id": {"type": "string", "description": "The zone id, from zone.list."},
            "primitive_id": {"type": "string", "description": "The filed object, as kind:id."},
        },
        "required": ["directory_id", "primitive_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result="true",
    refusals=_CONTRACT_REFUSALS + (
        "NotFound: the object is not filed in that zone",
        "ConflictError thought_tombstoned: the note belongs to a tombstoned Thought",
    ),
    completion="synchronous; zone.members no longer lists it; one desk_changed frame (kind directory, op update) on the hub bus",
    exposure=("http:DELETE /api/directories/{directory_id}/members/{primitive_id}", "mcp:zone.unfile"),
    service="primitive_service",
    method="unfile_member",
    admission=Admission("admitted", "The filing relationship removed (R4)."),
)

ZONE_MEMBERS = OperationDescriptor(
    name="zone.members",
    version=1,
    description="List what is filed in one zone.",
    args_schema={
        "type": "object",
        "properties": {"directory_id": {"type": "string", "description": "The zone id, from zone.list."}},
        "required": ["directory_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="read",
    result="a list of " + _MEMBERSHIP_RECORD.replace("the membership record", "membership records"),
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown directory",),
    completion="synchronous",
    exposure=("http:GET /api/directories/{directory_id}/members", "mcp:zone.list_members", "mcp-resource:holdspeak://zones/{id}/members"),
    service="primitive_service",
    method="list_directory_members",
    admission=_EXEMPT_READ,
)

KB_MEMBER_ADD = OperationDescriptor(
    name="kb.member.add",
    version=1,
    description="Add one reference (kind:id) to a knowledge base.",
    args_schema={
        "type": "object",
        "properties": {
            "kb_id": {"type": "string", "description": "The knowledge base id, from kb.list."},
            "resource_ref": {"type": "string", "description": "A kind:id reference, for example note:<id>."},
        },
        "required": ["kb_id", "resource_ref"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result=_KB_MEMBER_RECORD,
    refusals=_CONTRACT_REFUSALS + ("ValueError: resource_ref must be qualified as kind:id | unknown resource kind | Unknown Knowledge",),
    completion="synchronous; kb.members lists it; one desk_changed frame (kind kb, op update) on the hub bus",
    exposure=("http:PUT /api/kbs/{kb_id}/members/{resource_ref}", "mcp:kb.add_member"),
    service="primitive_service",
    method="add_kb_member",
    admission=Admission("admitted", "A durable reference filed into a knowledge base (R4)."),
)

KB_MEMBER_REMOVE = OperationDescriptor(
    name="kb.member.remove",
    version=1,
    description="Remove one reference from a knowledge base.",
    args_schema={
        "type": "object",
        "properties": {
            "kb_id": {"type": "string", "description": "The knowledge base id, from kb.list."},
            "resource_ref": {"type": "string", "description": "The reference to remove, as kind:id."},
        },
        "required": ["kb_id", "resource_ref"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="write",
    result="true when a live reference was removed, false when there was none",
    refusals=_CONTRACT_REFUSALS + ("ValueError: resource_ref must be qualified as kind:id | unknown resource kind",),
    completion="synchronous; kb.members no longer lists it; one desk_changed frame (kind kb, op update) when one was removed",
    exposure=("http:DELETE /api/kbs/{kb_id}/members/{resource_ref}", "mcp:kb.remove_member"),
    service="primitive_service",
    method="remove_kb_member",
    admission=Admission("admitted", "A durable reference removed from a knowledge base (R4)."),
)

KB_MEMBERS = OperationDescriptor(
    name="kb.members",
    version=1,
    description="List the references in one knowledge base.",
    args_schema={
        "type": "object",
        "properties": {"kb_id": {"type": "string", "description": "The knowledge base id, from kb.list."}},
        "required": ["kb_id"],
        "additionalProperties": False,
    },
    principal=_DESK_PRINCIPAL,
    effect="read",
    result="a list of knowledge membership records",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown kb",),
    completion="synchronous",
    exposure=("http:GET /api/kbs/{kb_id}/members", "mcp:kb.list_members"),
    service="primitive_service",
    method="list_kb_members",
    admission=_EXEMPT_READ,
)

DECISION_DELETE = OperationDescriptor(
    name="decision.delete",
    version=1,
    description="Withdraw one desk decision (a tombstone).",
    args_schema={
        "type": "object",
        "properties": {"decision_id": _DECISION_ID},
        "required": ["decision_id"],
        "additionalProperties": False,
    },
    principal=_TRANSPORT_PRINCIPAL,
    effect="write",
    result="true",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown decision",),
    completion="synchronous; decision.read then refuses the id (NotFound); one desk_changed frame (kind decision, op delete) on the hub bus",
    exposure=("http:DELETE /api/decisions/{decision_id}", "mcp:desk.delete[kind=decisions]", "mcp:desk.verb[verb_id=desk.delete,kind=decisions]"),
    service="primitive_service",
    method="delete_decision",
    admission=Admission("admitted", "A decision withdrawn: a lifecycle change (R4; in the delegation grant by R5)."),
)

DECISION_STATUS = OperationDescriptor(
    name="decision.status",
    version=1,
    description=(
        "Set one desk decision's status: proposed (it goes on the review list), accepted, superseded or "
        "deprecated. Over MCP the same change is desk.update kind=decisions with data status."
    ),
    args_schema={
        "type": "object",
        "properties": {
            "decision_id": _DECISION_ID,
            "status": {"description": "proposed, accepted, superseded or deprecated."},
        },
        "required": ["decision_id"],
        "additionalProperties": False,
    },
    principal=_TRANSPORT_PRINCIPAL,
    effect="write",
    result="the updated decision record",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown decision", "ValueError: invalid decision status"),
    completion="synchronous; decision.read returns the new status; one desk_changed frame (kind decision, op update) on the hub bus",
    # PHILO-7-02 decides (phase status, "Decisions deferred"): no separately
    # named MCP tool. MCP reaches the same status mutation as decision.update
    # (desk.update kind=decisions {status}), which is admitted the same way.
    exposure=("http:PUT /api/decisions/{decision_id}/status",),
    service="primitive_service",
    method="update_decision_status",
    admission=Admission("admitted", "The same status mutation as the admitted decision.update (R4)."),
)

DECISION_SUPERSEDE = OperationDescriptor(
    name="decision.supersede",
    version=1,
    description="Replace one desk decision with a new successor: the old one becomes superseded and names the successor.",
    args_schema={
        "type": "object",
        "properties": {
            "decision_id": _DECISION_ID,
            "successor_id": {"type": "string", "description": "Optional. The successor's id; minted before admission when absent."},
        },
        "required": ["decision_id"],
        "additionalProperties": False,
    },
    principal=_TRANSPORT_PRINCIPAL,
    effect="write",
    result="the successor decision record",
    refusals=_CONTRACT_REFUSALS + ("NotFound: unknown decision",),
    completion="synchronous; decision.read returns both rows; two desk_changed frames (the old decision updated, the successor created)",
    exposure=("http:POST /api/decisions/{decision_id}/supersede", "mcp:decision.supersede"),
    service="primitive_service",
    method="supersede_decision",
    admission=Admission("admitted", "A decision replaced: two rows, ONE admission (D3); the successor id is minted before submission."),
)

# ── PHILO-7-02: the receipt readback (read-only, XI.5) ────────────────────

KERNEL_RECEIPT_READ = OperationDescriptor(
    name="kernel.receipt.read",
    version=1,
    description=(
        "Read the kernel receipt of one operation: the operation_id a filing or decision write returned. "
        "An agent reads only its own operations."
    ),
    args_schema={
        "type": "object",
        "properties": {"operation_id": {"type": "string", "description": "The operation_id a write returned."}},
        "required": ["operation_id"],
        "additionalProperties": False,
    },
    principal="derived by the transport; the kernel's read scope applies (an agent reads only its own operations)",
    effect="read",
    result="{view: receipt, consistency: committed, objects: [{ref, operation, receipt, native_receipts}]} (the same answer as GET /api/kernel/read?refs=operation:<id>&view=receipt)",
    refusals=_CONTRACT_REFUSALS + ("KernelRefused principal_read_scope_required: another principal's operation", "KernelRefused principal_authentication_required"),
    completion="synchronous; no kernel operation is made",
    exposure=("mcp:kernel.receipt",),
    service="kernel_read_service",
    method="read_receipt",
    admission=_EXEMPT_READ,
)

#: The Phase 7 slice table: (desk kind, verb) -> operation. The MCP ``desk.*``
#: tools, the ``desk.verb`` aliases and the primitive resource read it; every
#: row names a descriptor above. Workflows and chains are not in it (their
#: owning slice).
DESK_OPERATIONS: Mapping[tuple[str, str], str] = MappingProxyType({
    ("decision", "list"): "decision.list",
    ("decision", "get"): "decision.read",
    ("decision", "create"): "decision.create",
    ("decision", "update"): "decision.update",
    ("decision", "delete"): "decision.delete",
    ("note", "list"): "note.list",
    ("note", "get"): "note.read",
    ("note", "create"): "note.create",
    ("note", "update"): "note.update",
    ("note", "delete"): "note.delete",
    ("directory", "list"): "zone.list",
    ("directory", "get"): "zone.read",
    ("directory", "create"): "zone.create",
    ("directory", "update"): "zone.update",
    ("directory", "delete"): "zone.delete",
    ("kb", "list"): "kb.list",
    ("kb", "get"): "kb.read",
    ("kb", "create"): "kb.create",
    ("kb", "update"): "kb.update",
    ("kb", "delete"): "kb.delete",
})

#: The id argument of each kind's operations (the path or tool id supplies it).
DESK_ID_ARGUMENT: Mapping[str, str] = MappingProxyType({
    "decision": "decision_id", "note": "note_id", "directory": "directory_id", "kb": "kb_id",
})

#: The whole catalogue, in export order.
DESCRIPTORS: tuple[OperationDescriptor, ...] = (
    DECISION_CREATE, DECISION_UPDATE, DECISION_READ, DECISION_LIST,
    MEETING_LIST, MEETING_READ, MEETING_IMPORT, MEETING_SUMMARY_RUN,
    BRIEF_GENERATE, BRIEF_LATEST, BRIEF_SHELF_WRITE, BRIEF_SHELF_READ,
    THOUGHT_CREATE, THOUGHT_SAVE, THOUGHT_READ, THOUGHT_WORKBENCH_READ, THOUGHT_LIST,
    NOTE_CREATE, NOTE_READ, NOTE_UPDATE, NOTE_DELETE, NOTE_LIST,
    ZONE_CREATE, ZONE_READ, ZONE_UPDATE, ZONE_DELETE, ZONE_LIST,
    KB_CREATE, KB_READ, KB_UPDATE, KB_DELETE, KB_LIST,
    ZONE_FILE, ZONE_UNFILE, ZONE_MEMBERS, KB_MEMBER_ADD, KB_MEMBER_REMOVE, KB_MEMBERS,
    DECISION_DELETE, DECISION_STATUS, DECISION_SUPERSEDE,
    KERNEL_RECEIPT_READ,
)

#: The RuntimeServices / WebContext fields the catalogue binds to.
BOUND_SERVICES: tuple[str, ...] = tuple(dict.fromkeys(d.service for d in DESCRIPTORS))


# ── binding and invocation ────────────────────────────────────────────────


@dataclass(frozen=True)
class BoundOperation:
    descriptor: OperationDescriptor
    call: Callable[..., Any]
    target: Any


@dataclass
class OperationRegistry:
    """The descriptors, each bound to a method on one live service instance."""

    operations: dict[str, BoundOperation] = field(default_factory=dict)

    def descriptor(self, name: str) -> OperationDescriptor:
        return self._bound(name).descriptor

    def target(self, name: str) -> Any:
        """The service instance *name* is bound to (the identity fences read it)."""
        return self._bound(name).target

    def _bound(self, name: str) -> BoundOperation:
        bound = self.operations.get(name)
        if bound is None:
            raise OperationRefused("unknown_operation", name, f"Unknown operation: {name}")
        return bound

    def authorize(self, principal: Any, name: str) -> None:
        """Refuse a non-owner principal for an ``owner_only`` operation.

        :meth:`invoke` calls it first. A transport calls it itself before any
        work it does ahead of ``invoke`` (the MCP import intake, before it opens
        the caller's path; the HTTP upload, before it stores the body).
        """
        if not self._bound(name).descriptor.owner_only:
            return
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise OperationOwnerRequired(name)

    def invoke_receipted(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> tuple[Any, Optional[dict[str, Any]]]:
        """:meth:`invoke`, plus ``{operation_id, receipt}`` when the call was ADMITTED.

        PHILO-7-02: an admitted call runs the complete kernel path around the
        service call (``holdspeak/services/desk_kernel.py``); the second value
        is its terminal receipt, ``None`` for an exempt call. It calls
        :meth:`invoke` itself, so every transport still passes through the one
        ``invoke`` (the recording fences read it).
        """
        # ``held`` only when given: a recording fence may wrap ``invoke`` with
        # the three-argument signature every transport uses.
        result = (self.invoke(principal, name, args) if held is None
                  else self.invoke(principal, name, args, held=held))
        return result, _LAST_KERNEL.get()

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.

        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
                Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))
            except JsonSchemaValidationError as exc:
                location = ".".join(str(part) for part in exc.absolute_path)
                detail = f"{location}: {exc.message}" if location else exc.message
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: {detail}") from exc
        except OperationRefused as exc:
            # R2 class 3: a contract refusal of an identifiable consequential
            # attempt keeps its named error AND leaves a refusal receipt.
            self._refusal_receipt(exc, principal, name, payload)
            raise
        if self._admits(bound, payload):
            # PHILO-7-02: Article XI -- the complete kernel path around the call.
            from holdspeak.services import desk_kernel

            if not isinstance(getattr(principal, "kind", None), PrincipalKind) or principal.kind is PrincipalKind.NONE:
                # No transport hands an admitted write a missing principal (the
                # hub's edge refuses the unauthenticated first); a caller that
                # does is refused by name, never written without a receipt.
                raise OperationRefused(
                    "principal_required", name,
                    f"{name} is admitted under Article XI and needs the transport's authenticated principal",
                )

            result, kernel = desk_kernel.run(
                _database_of(bound.target), principal, name, payload,
                lambda minted: bound.call(principal, **minted, **given_held),
            )
            _LAST_KERNEL.set(kernel)
            return result
        return bound.call(principal, **dict(payload), **given_held)

    @staticmethod
    def _admits(bound: BoundOperation, payload: Mapping[str, Any]) -> bool:
        """The descriptor's admission over the validated arguments (stored state where it says so)."""
        admission = bound.descriptor.admission
        if admission is None:
            return False
        admits = admission.admits(payload)
        if admits is None:
            # A stored-state condition: a Thought's note (note.delete).
            owns = getattr(bound.target, "thought_owns_note", None)
            return bool(owns(payload.get("note_id"))) if callable(owns) else False
        return admits

    def consequential(self, name: str, raw: Any) -> bool:
        """R2: an identifiable operation the admission table ADMITS, from a malformed raw payload.

        ``admitted``: always. ``admitted_if`` with an argument condition: when
        the raw payload is an object that carries an admission argument and the
        condition holds over it. A non-object payload for a conditional
        operation, a stored-state condition and every exempt operation: no
        (the protocol-refusal boundary; no effect is invented to journal).
        """
        bound = self.operations.get(name)
        admission = None if bound is None else bound.descriptor.admission
        if admission is None or admission.rule == "exempt":
            return False
        if admission.rule == "admitted":
            return True
        if admission.holds is None or not isinstance(raw, Mapping):
            return False
        if not set(admission.arguments) & set(raw):
            return False
        try:
            return bool(admission.holds(raw))
        except Exception:
            return False

    def refuse(self, principal: Any, name: str, code: str, raw: Any) -> Optional[dict[str, Any]]:
        """Class 3 and 4: a refusal receipt for a consequential attempt refused before the service.

        ``None`` (and nothing written) when the attempt is not identifiable as
        consequential. The caller keeps raising its own named error.
        """
        if not self.consequential(name, raw):
            return None
        from holdspeak.services import desk_kernel

        return desk_kernel.refuse(_database_of(self.operations[name].target), principal, name, code, raw)

    def _refusal_receipt(self, exc: OperationRefused, principal: Any, name: str, raw: Any) -> None:
        kernel = self.refuse(principal, name, exc.code, raw)
        if kernel is not None:
            exc.kernel = kernel  # type: ignore[attr-defined]

    def update_args(
        self, principal: Any, data: Mapping[str, Any], item_id: str, *,
        operation: str = "decision.update", id_field: str = "decision_id",
    ) -> dict[str, Any]:
        """:func:`update_args` with the class-4 refusal receipt (a duplicate id in the data)."""
        try:
            return update_args(data, item_id, operation=operation, id_field=id_field)
        except OperationRefused as exc:
            self._refusal_receipt(exc, principal, operation, data)
            raise


def _database_of(target: Any) -> Any:
    """The database the bound service writes through (the kernel journal lives beside it)."""
    database = getattr(target, "_db", None)
    if database is None:
        from holdspeak.db import get_database

        database = get_database()
    return database


def update_args(
    data: Mapping[str, Any],
    item_id: str,
    *,
    operation: str = "decision.update",
    id_field: str = "decision_id",
) -> dict[str, Any]:
    """An update operation's arguments from a transport's body and its path/tool id.

    The id comes from the path (HTTP) or the tool's ``id`` (MCP). A body that
    also carries the id argument was refused before this contract (a Python
    ``TypeError``: "multiple values for argument ..."); it stays refused, now
    by name. PHILO-7-01: the same rule for ``note.update``, ``zone.update`` and
    ``kb.update`` (``operation`` and ``id_field``).
    """
    if id_field in data:
        raise OperationRefused(
            "invalid_arguments", operation,
            f"Invalid arguments for {operation}: {id_field} comes from the path or the tool id, not the data",
        )
    return {**data, id_field: item_id}


def bind(services: Mapping[str, Any], descriptors: tuple[OperationDescriptor, ...] = DESCRIPTORS) -> OperationRegistry:
    """Bind every descriptor to ``services[descriptor.service].<method>`` now.

    *services* maps a RuntimeServices field name to the live instance. A
    missing service or method is a composition error, raised here at hub start,
    never on the first call.
    """
    registry = OperationRegistry()
    for descriptor in descriptors:
        target = services.get(descriptor.service)
        if target is None:
            raise RuntimeError(f"{descriptor.name}: no {descriptor.service} to bind to")
        call = getattr(target, descriptor.method, None)
        if not callable(call):
            raise RuntimeError(f"{descriptor.name}: {type(target).__name__} has no {descriptor.method}")
        if descriptor.name in registry.operations:
            raise RuntimeError(f"{descriptor.name} is declared twice")
        registry.operations[descriptor.name] = BoundOperation(descriptor, call, target)
    return registry


def bind_available(services: Mapping[str, Any]) -> OperationRegistry:
    """Bind the descriptors whose service *services* holds (a partial composition).

    For the two lawful partial cases only: a route test's partially wired
    ``WebContext`` and a bare (non-hub) MCP composition. The hub binds the
    whole catalogue through :func:`bind`, which fails on a missing service.
    """
    present = {name: target for name, target in services.items() if target is not None}
    return bind(present, tuple(d for d in DESCRIPTORS if d.service in present))


def _bare_primitives(ctx: Any) -> Any:
    from holdspeak.db import get_database, get_observer
    from holdspeak.services.primitive_service import PrimitiveService

    return PrimitiveService(get_database(), observer=get_observer())


#: The bare builds a partially wired context may fall back to, by field name.
#: Only services whose bare build is behaviourally identical off-hub (no
#: callbacks, no runners) are here.
_BARE: dict[str, Callable[[Any], Any]] = {
    "primitive_service": _bare_primitives,
}


def for_context(ctx: Any, *bare: str, **fallbacks: Callable[[], Any]) -> OperationRegistry:
    """The registry a route reaches through its ``WebContext``.

    In the hub this is ``ctx.operations``, bound at composition, and nothing
    is built. A partially wired context -- a route test that builds a
    ``WebContext`` with only the fields it exercises -- gets a registry bound
    over the services it carries, else the route's own *fallbacks* (field name
    -> builder), else the bare builds it names in *bare*: lawful case 3 of
    ``composition.service``.
    """
    registry = getattr(ctx, "operations", None)
    if registry is not None:
        return registry
    services: dict[str, Any] = {}
    for name in BOUND_SERVICES:
        target = getattr(ctx, name, None)
        if target is None and name in fallbacks:
            target = fallbacks[name]()
        if target is None and name in bare:
            target = _BARE[name](ctx)
        services[name] = target
    return bind_available(services)


def for_runtime(
    build_primitives: Optional[Callable[[], Any]] = None,
    **builders: Callable[[], Any],
) -> OperationRegistry:
    """The registry the installed composition root holds, else one bound over the caller's builders.

    MCP dispatch and the MCP resources read this. In the hub it is the same
    object the HTTP routes reach and no builder runs; in a bare composition (a
    unit test, the proxy-less diagnosis path) it binds over the caller's own
    services, exactly as the caller's previous hand-wired path did.
    """
    from holdspeak.runtime.composition import service

    if build_primitives is not None:
        builders["primitive_service"] = build_primitives
    return service(
        "operations",
        lambda: bind_available({name: build() for name, build in builders.items()}),
    )
