"""The ST3-ST5 Setup rows on the application-operation contract.

These operations are HTTP-only until ST9.  The descriptors still live on the
shared contract now so the Setup window and the later CLI/MCP transport cannot
grow a second write path.
"""
from __future__ import annotations

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor


_PRINCIPAL = "derived by the transport (the HTTP auth middleware); owner only"
_SETUP_REFUSALS = _CONTRACT_REFUSALS + (
    "owner_required",
    "setup_unavailable",
    "people_unavailable",
)


SETUP_FOUND = OperationDescriptor(
    name="setup.found",
    version=1,
    description="Read the local Setup inventory: what HoldSpeak found and the one action for each row.",
    args_schema={"type": "object", "properties": {}, "additionalProperties": False},
    principal=_PRINCIPAL,
    effect="read",
    result="{rows: [{id, kind, label, detail, state, reason, egress_host, verb, action, payload}], owner_name, people, suggestions, first_run}",
    refusals=_SETUP_REFUSALS,
    completion="synchronous; the same read is used when Setup opens again",
    exposure=("http:GET /api/setup/found",),
    service="setup_service",
    method="found",
    owner_only=True,
    admission=Admission("exempt", "A local Setup read; it changes no state and performs no network scan."),
)


SETUP_USE = OperationDescriptor(
    name="setup.use",
    version=1,
    description="Use one found Setup row. The row's producer reports Works, Working or a named failure.",
    args_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "payload": {"type": "object", "additionalProperties": True},
        },
        "required": ["id"],
        "additionalProperties": False,
    },
    principal=_PRINCIPAL,
    effect="write",
    result="the producer's result for the row",
    refusals=_SETUP_REFUSALS + ("NotFound: unknown Setup row",),
    completion="synchronous or producer-pending; the Setup read reports the durable result",
    exposure=("http:POST /api/setup/use",),
    service="setup_service",
    method="use_row",
    owner_only=True,
    blocking_io=True,
    owner_press=True,
    admission=Admission("admitted", "Config: the owner's press uses one found Setup item."),
)


SETUP_PEOPLE_ADD = OperationDescriptor(
    name="setup.people.add",
    version=1,
    description="Add comma-separated direct reports in Setup. The People store is initialized on this press when needed.",
    args_schema={
        "type": "object",
        "properties": {
            "names": {
                "anyOf": [
                    {"type": "string", "minLength": 1},
                    {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1},
                ],
            },
        },
        "required": ["names"],
        "additionalProperties": False,
    },
    principal=_PRINCIPAL,
    effect="write",
    result="{relationships: [{id, display_name, relationship_kind}]} and the receipt",
    refusals=_SETUP_REFUSALS + ("ValidationError: Add a name",),
    completion="synchronous; People lists the new relationships",
    exposure=("http:POST /api/setup/people",),
    service="setup_service",
    method="add_people",
    owner_only=True,
    owner_press=True,
    admission=Admission("admitted", "Config: the owner's press writes the People store."),
)


SETUP_LAN_SCAN = OperationDescriptor(
    name="setup.lan.scan",
    version=1,
    description="Look once on the owner's private network for a responding engine. This is a read; it adds no engine.",
    args_schema={"type": "object", "properties": {}, "additionalProperties": False},
    principal=_PRINCIPAL,
    effect="read",
    result="{rows: [{id, name, model, host, base_url}], checkedAt, disabled?}",
    refusals=_SETUP_REFUSALS,
    completion="synchronous; the answering servers are returned as Setup found rows",
    exposure=("http:POST /api/setup/lan",),
    service="setup_service",
    method="scan_lan",
    owner_only=True,
    blocking_io=True,
    owner_press=True,
    admission=Admission("admitted", "Network egress: the approved Setup-open look reaches answering private-network engines."),
)


SETUP_OPERATIONS: tuple[OperationDescriptor, ...] = (
    SETUP_FOUND,
    SETUP_USE,
    SETUP_PEOPLE_ADD,
    SETUP_LAN_SCAN,
)


__all__ = ["SETUP_OPERATIONS"]
