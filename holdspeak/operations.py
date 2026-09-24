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
    exposure=("http:GET /api/decisions/{decision_id}", "mcp:desk.get[kind=decisions]"),
    service="primitive_service",
    method="get_decision",
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

#: The whole catalogue, in export order.
DESCRIPTORS: tuple[OperationDescriptor, ...] = (
    DECISION_CREATE, DECISION_UPDATE, DECISION_READ, DECISION_LIST,
    MEETING_LIST, MEETING_READ, MEETING_IMPORT, MEETING_SUMMARY_RUN,
    BRIEF_GENERATE, BRIEF_LATEST, BRIEF_SHELF_WRITE, BRIEF_SHELF_READ,
    THOUGHT_CREATE, THOUGHT_SAVE, THOUGHT_READ, THOUGHT_WORKBENCH_READ, THOUGHT_LIST,
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
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
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
        return bound.call(principal, **dict(payload), **given_held)


def update_args(data: Mapping[str, Any], decision_id: str) -> dict[str, Any]:
    """``decision.update`` arguments from a transport's body and its path/tool id.

    The id comes from the path (HTTP) or the tool's ``id`` (MCP). A body that
    also carries ``decision_id`` was refused before this contract (a Python
    ``TypeError``: "multiple values for argument 'decision_id'"); it stays
    refused, now by name.
    """
    if "decision_id" in data:
        raise OperationRefused(
            "invalid_arguments", "decision.update",
            "Invalid arguments for decision.update: decision_id comes from the path or the tool id, not the data",
        )
    return {**data, "decision_id": decision_id}


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
