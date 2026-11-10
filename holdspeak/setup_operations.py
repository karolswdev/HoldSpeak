"""The Setup rows on the application-operation contract (ST3-ST5; every Setup route 2026-11-09).

The Setup window, CLI and MCP all reach these descriptors so they cannot grow
second inventory or adoption paths. ``web/routes/setup.py`` produces every
``/api/setup`` route (but the model check, ``discover-models``, below) and
``mcp/families/declared.py`` every tool from these rows, through
``OperationRegistry.invoke``.

Reads are anyone's evidence (the transport's edge decides who reaches a
route); every write acts for the owner (``owner_only``). The local-AI
download and the LAN look are egress and his press (``owner_press``).
Every owner-only write is config: no thread offers it and no launched agent
is handed it; the owner's own MCP client reaches each one.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor
from holdspeak.services.errors import ServiceError, ValidationError


_PRINCIPAL = "derived by the transport; owner only"
_SETUP_REFUSALS = _CONTRACT_REFUSALS + (
    "owner_required",
    "setup_unavailable",
    "people_unavailable",
)
_SETUP_STATUS_REFUSALS = _CONTRACT_REFUSALS + (
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
    call=lambda s, p, a: s.found(p),
    http=("GET", "/api/setup/found"),
    handler="api_setup_found",
)


SETUP_STATUS = OperationDescriptor(
    name="setup.status",
    version=1,
    description="Read the local Setup inventory: the same rows HoldSpeak shows in Setup.",
    args_schema={"type": "object", "properties": {}, "additionalProperties": False},
    principal="derived by the transport; owner or agent",
    effect="read",
    result="{rows, owner_name, people, suggestions, first_run}; rows carry the shared Setup fields id, kind, label, detail, state, reason, egress_host, verb, action and payload",
    refusals=_SETUP_STATUS_REFUSALS,
    completion="synchronous; reads the existing local Setup producers",
    exposure=("mcp:setup.status",),
    service="setup_service",
    method="found",
    owner_only=False,
    admission=Admission("exempt", "A local Setup read; it changes no state and performs no network scan."),
    call=lambda s, p, a: s.found(p),
    tool_schema={"type": "object", "properties": {}, "additionalProperties": False},
    thread="evidence_read",
)


SETUP_USE = OperationDescriptor(
    name="setup.use",
    version=1,
    description="Use one found Setup row, or all actionable rows in the current Setup order. Each outcome remains visible.",
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
    result="{state, success, count, results} when id is all; otherwise the selected producer result",
    refusals=_SETUP_REFUSALS + ("NotFound: unknown Setup row",),
    completion="synchronous or producer-pending; the Setup read reports the durable result",
    exposure=("http:POST /api/setup/use", "mcp:setup.use"),
    service="setup_service",
    method="use_row",
    owner_only=True,
    blocking_io=True,
    owner_press=True,
    admission=Admission("admitted", "Config: the owner's press uses one found Setup item."),
    call=lambda s, p, a: s.use_row(p, a.get("id"), a.get("payload")),
    # The Setup window reads ``{success, result}``; the MCP tool the bare result.
    web_call=lambda s, p, a: {"success": True, "result": s.use_row(p, a.get("id"), a.get("payload"))},
    http=("POST", "/api/setup/use"),
    handler="api_setup_use",
    tool_schema={"type": "object", "properties": {"id": {"type": "string", "minLength": 1},
                                                   "payload": {"type": "object", "additionalProperties": True}},
                 "required": ["id"], "additionalProperties": False},
    authority="config",
    thread="effect_proposal",
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
    exposure=("http:POST /api/setup/people", "mcp:setup.people.add"),
    service="setup_service",
    method="add_people",
    owner_only=True,
    owner_press=True,
    admission=Admission("admitted", "Config: the owner's press writes the People store."),
    call=lambda s, p, a: s.add_people(p, a.get("names")),
    web_call=lambda s, p, a: {"success": True, **s.add_people(p, a.get("names"))},
    http=("POST", "/api/setup/people"),
    http_status=201,
    handler="api_setup_people",
    authority="config",
    tool_schema={"type": "object", "properties": {"names": {"anyOf": [
        {"type": "string", "minLength": 1},
        {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1}]}},
        "required": ["names"], "additionalProperties": False},
    thread="effect_proposal",
)


SETUP_LAN_SCAN = OperationDescriptor(
    name="setup.lan.scan",
    version=1,
    description="Look once on the owner's private network for a responding engine. This is a read; it adds no engine.",
    args_schema={"type": "object", "properties": {}, "additionalProperties": False},
    principal=_PRINCIPAL,
    effect="read",
    result="{rows: [{id, name, host, baseUrl, found}], checkedAt}; scanner facts include partial, unavailable, reason and hostsChecked; disabled=true when scanning is off",
    refusals=_SETUP_REFUSALS + ("setup_lan_refused",),
    completion="synchronous; the answering servers are returned as Setup found rows",
    exposure=("http:POST /api/setup/lan", "mcp:setup.lan.scan"),
    service="setup_service",
    method="scan_lan",
    owner_only=True,
    blocking_io=True,
    owner_press=True,
    admission=Admission("admitted", "Network egress: the approved Setup-open look reaches answering private-network engines."),
    call=lambda s, p, a: s.scan_lan(p),
    http=("POST", "/api/setup/lan"),
    handler="api_setup_lan",
    tool_schema={"type": "object", "properties": {}, "additionalProperties": False},
    authority="egress",
)


Call = Callable[[Any, Any, dict[str, Any]], Any]
_ANY = "derived by the transport (HTTP auth middleware; MCP auth resolver); the edge decides who reaches it"
_ID = {"type": "string", "minLength": 1}
_OBJECT = {"type": "object"}


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        result: str, write: bool = False, owner_only: bool = False, owner_press: bool = False,
        blocking_io: bool = False, status: int = 200, tool: bool = True, authority: str = "work",
        properties: Optional[Mapping[str, Any]] = None, refusals: tuple[str, ...] = ()) -> OperationDescriptor:
    """One Setup verb: its route, and its tool when it has one (the path's ids required)."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids, "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"},
        principal=_PRINCIPAL if owner_only else _ANY, effect="write" if write else "read", result=result,
        refusals=_CONTRACT_REFUSALS + (("owner_required",) if owner_only else ()) + refusals,
        completion="synchronous; GET /api/setup/status and GET /api/setup/found read the state back",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()), service=service,
        method=method, owner_only=owner_only, owner_press=owner_press, blocking_io=blocking_io, call=call,
        http=http, http_status=status, handler=handler, tool_schema=schema if tool else None,
        # An owner-only write changes his Setup: config, in no thread palette and never offered to a launched agent.
        authority="config" if write and owner_only and authority == "work" else authority,
        thread=("effect_proposal" if write else "evidence_read") if tool else None,
    )


def _event(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    body = {key: value for key, value in args.items() if key != "attempt_id"}
    if set(body) - {"event_id", "kind"}:
        raise ValidationError("First-value events accept only event_id and kind.")
    return service.record_event(principal, args.get("attempt_id"), body)


class Unavailable:
    """A partial composition's stand-in for a service the hub composes (local AI, model downloads):
    every call through it is refused as unavailable, as the hand-written routes refused a missing one."""


def _local_ai(service: Any) -> Any:
    if service is None or isinstance(service, Unavailable):
        raise ServiceError("local_ai_unavailable", "Set up local AI is not available on this hub.", context={"status": 503})
    return service


def _local_ai_start(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    only = args.get("only")
    if only is not None and not isinstance(only, list):
        raise ServiceError("local_ai_invalid", "only must be a list.", context={"status": 400})
    return _local_ai(service).start(principal, only=only)


def _acquisition(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    if service is None or isinstance(service, Unavailable):
        raise ServiceError("inference_acquisition_unavailable", "Model downloads are unavailable on this hub.",
                           context={"status": 503})
    return service.get_acquisition(principal, args.get("job_id"))


_FIRST_VALUE = "/api/setup/first-value"
SETUP_ROUTE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("setup.readiness", "setup_service", "status", ("GET", "/api/setup/status"), "api_setup_status",
        lambda s, p, a: s.status(p),
        "Read whether HoldSpeak is ready on this Mac: every doctor check, what can leave the machine, "
        "presence, the first-run state and the one next step. No network call.",
        result="{sections, trust, presence, first_run, primary_action, verdict}", blocking_io=True),
    _op("setup.runtime.probe", "setup_service", "test_runtime", ("POST", "/api/setup/runtime-test"),
        "api_setup_runtime_test", lambda s, p, a: s.test_runtime(p),
        "Test the dictation runtime once: is the speech model and its backend usable. A remote "
        "(OpenAI-compatible) runtime is reached once with its stored key (GET /models): egress, the owner's press.",
        result="the runtime probe: {ok, backend, model, detail}", blocking_io=True,
        owner_only=True, owner_press=True, authority="egress"),
    _op("setup.onboarding.set", "setup_service", "set_onboarding_disposition", ("PUT", "/api/setup/onboarding"),
        "api_onboarding_disposition", lambda s, p, a: s.set_onboarding_disposition(p, a),
        "Record how the owner left Setup (finished, skipped) and seed the Desk.",
        result="{success, onboarding}", write=True, owner_only=True, tool=True,
        properties={"disposition": {"type": "string", "description": "How he left Setup: finished or skipped."}}),
    _op("setup.first_value.start", "setup_service", "start_first_value", ("POST", _FIRST_VALUE + "/start"),
        "api_first_value_start", lambda s, p, a: s.start_first_value(p, a),
        "Start the first-value receipt: the owner's first dictation attempt on this Mac.",
        result="{success, attempt}", write=True, owner_only=True, tool=True, status=201,
        properties={"destination": {"type": "string"}}),
    _op("setup.first_value.finish", "setup_service", "finish_first_value",
        ("POST", _FIRST_VALUE + "/{attempt_id}/finish"), "api_first_value_finish",
        lambda s, p, a: s.finish_first_value(p, a.get("attempt_id"), {k: v for k, v in a.items() if k != "attempt_id"}),
        "Finish the first-value receipt with its outcome and steps (no words of the dictation).",
        result="{success, attempt}", write=True, owner_only=True, tool=True,
        properties={"outcome": {"type": "string"}, "steps": {}, "decisions": {}, "destination": {"type": "string"},
                    "failure_category": {}},
        refusals=("NotFound: unknown first-value attempt",)),
    _op("setup.first_value.event", "setup_service", "record_event", ("POST", _FIRST_VALUE + "/{attempt_id}/event"),
        "api_first_value_event", _event,
        "Record one first-value step (event_id and kind only).",
        result="{success, event}", write=True, owner_only=True, tool=True, status=201,
        properties={"event_id": {"type": "string"}, "kind": {"type": "string"}},
        refusals=("NotFound: unknown first-value attempt",)),
    _op("setup.local_ai.status", "local_ai_setup_service", "status", ("GET", "/api/setup/local-ai"),
        "api_local_ai_status", lambda s, p, a: _local_ai(s).status(p),
        "Read what Set up local AI downloads, what is on this Mac already, and the download progress.",
        result="{state, models, speech, progress}", owner_only=True,
        refusals=("local_ai_unavailable",)),
    _op("setup.local_ai.start", "local_ai_setup_service", "start", ("POST", "/api/setup/local-ai"),
        "api_local_ai_start", _local_ai_start,
        "Set up local AI: check the runtime, download the models (one egress receipt), set them up. "
        "only: [\"whisper\"] downloads the speech model alone.",
        result="the download state", write=True, owner_only=True, owner_press=True, blocking_io=True, status=202,
        authority="config", properties={"only": {"type": "array", "items": {"type": "string"}}},
        refusals=("local_ai_unavailable", "local_ai_invalid")),
    _op("setup.local_ai.cancel", "local_ai_setup_service", "cancel", ("POST", "/api/setup/local-ai/cancel"),
        "api_local_ai_cancel", lambda s, p, a: _local_ai(s).cancel(p),
        "Stop the local AI download.", result="the download state", write=True, owner_only=True, authority="config",
        refusals=("local_ai_unavailable",)),
    _op("inference.acquisition.get", "inference_acquisition_service", "get_acquisition",
        ("GET", "/api/inference/acquisitions/{job_id}"), "api_inference_acquisition", _acquisition,
        "Read one model download: its state, bytes and the step it is on.",
        result="{job_id, state, bytes, total, step}", owner_only=True,
        refusals=("NotFound: unknown download", "inference_acquisition_unavailable")),
    _op("inference.targets.list", "profile_service", "list_inference_targets", ("GET", "/api/inference-targets"),
        "api_list_inference_targets", lambda s, p, a: s.list_inference_targets(p),
        "List the inference targets HoldSpeak can run work on (this Mac, LAN engines, hosted models).",
        result="{version, targets}", owner_only=True),
)


SETUP_OPERATIONS: tuple[OperationDescriptor, ...] = (
    SETUP_FOUND,
    SETUP_STATUS,
    SETUP_USE,
    SETUP_PEOPLE_ADD,
    SETUP_LAN_SCAN,
) + SETUP_ROUTE_OPERATIONS


__all__ = ["SETUP_OPERATIONS", "Unavailable"]
