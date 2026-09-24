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
* not an authorizer. The principal comes from the transport (the HTTP auth
  middleware, the MCP auth resolver); arguments can never carry authority, and
  :meth:`OperationRegistry.invoke` refuses an argument that tries.

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

#: The whole catalogue, in export order.
DESCRIPTORS: tuple[OperationDescriptor, ...] = (
    DECISION_CREATE, DECISION_UPDATE, DECISION_READ, DECISION_LIST,
)


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

    def invoke(self, principal: Any, name: str, args: Optional[Mapping[str, Any]] = None) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result."""
        bound = self._bound(name)
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
        return bound.call(principal, **dict(payload))


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


def for_context(ctx: Any) -> OperationRegistry:
    """The registry a route reaches through its ``WebContext``.

    In the hub this is ``ctx.operations``, bound at composition. A partially
    wired context — a route test that builds a ``WebContext`` with only the
    fields it exercises — gets a registry bound over its own (or a bare)
    primitive service: lawful case 3 of ``composition.service``.
    """
    registry = getattr(ctx, "operations", None)
    if registry is not None:
        return registry
    primitives = getattr(ctx, "primitive_service", None)
    if primitives is None:
        from holdspeak.db import get_database, get_observer
        from holdspeak.services.primitive_service import PrimitiveService

        primitives = PrimitiveService(get_database(), observer=get_observer())
    return bind({"primitive_service": primitives})


def for_runtime(build_primitives: Callable[[], Any]) -> OperationRegistry:
    """The registry the installed composition root holds, else one bound over *build_primitives*.

    MCP dispatch reads this. In the hub it is the same object the HTTP routes
    reach; in a bare composition (a unit test) it binds over the caller's own
    service, exactly as the caller's previous hand-wired path did.
    """
    from holdspeak.runtime.composition import service

    return service("operations", lambda: bind({"primitive_service": build_primitives()}))
