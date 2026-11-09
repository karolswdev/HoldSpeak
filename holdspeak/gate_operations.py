"""The gate, the principals and the kernel on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``phone_operations.py`` is. Each row states one verb once:
its call, its HTTP method and path, the EDGE RIGHT that path has
(``principals.required_right``) and, where a tool call can carry it, its MCP
tool. ``web/routes/system/gate_routes.py`` and ``kernel_routes.py`` produce the
routes from these rows; nothing about who passes the gate changes, only where
the route body lives.

The principal requirement: every row names its edge right, and its call refuses
a principal without that right (an UNAUTHENTICATED one too) with
``principal_right_required`` before the service runs. A router mounted without
the hub's edge, and an MCP call, keep the edge's rule. A right that only the
owner holds makes the row ``owner_only``. ``tests/unit/test_gate_operations.py``
holds each row to the edge.

Threads and launched agents: a read an agent may make is work
(``evidence_read``); every write and every owner-only read is ``authority``, so
no thread and no launched agent (the CONDUCTOR palette) is offered it
(``mcp/tool_authority.py``). A decide is the owner's word: ``owner_only`` and
``owner_press``.

No tool, and why:

- ``gate.full_call``: the whole held command is the owner's Raw read on his
  desk; it never goes back to an agent (PHILO-15 20, B63).
- ``principals.agent.issue``: its answer is an agent credential; a credential
  never goes through a model's context.
- ``kernel.executor.*``: the node link protocol (a node's credential); an MCP
  call never carries a node principal.

Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.principals import Principal, PrincipalKind, PrincipalRight
from holdspeak.services.errors import ServiceError, ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

#: Each verb's edge right: the same right ``principals.required_right`` names for its path.
RIGHTS: dict[str, PrincipalRight] = {}
_ID = {"type": "string", "minLength": 1}


def holders(right: PrincipalRight) -> tuple[str, ...]:
    """The principal kinds that hold *right* (``principals._RIGHTS``)."""
    return tuple(kind.value for kind in PrincipalKind if Principal(kind, "").permits(right))


def require(right: PrincipalRight, principal: Any) -> None:
    """Refuse a principal without *right*: a missing one, UNAUTHENTICATED, or a kind that lacks it."""
    permits = getattr(principal, "permits", None)
    if not callable(permits) or not permits(right):
        raise ServiceError("principal_right_required", f"This call needs the {right.value} right.", context={
            "status": 403, "principal": getattr(principal, "name", "none"), "missing_right": right.value,
        })


def _int(args: Mapping[str, Any], key: str, default: int) -> int:
    try:
        return int(args.get(key, default))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{key} must be an integer") from exc


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call,
        description: str, right: PrincipalRight, *, result: str, write: bool = False,
        tool: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (), owner_press: bool = False,
        status: int = 200, refusals: tuple[str, ...] = (), tool_name: str = "") -> OperationDescriptor:
    """One verb. ``tool``: the MCP tool's properties beside the path ids (None: no tool)."""
    RIGHTS[name] = right
    kinds = holders(right)
    owner_only = kinds == (PrincipalKind.OWNER.value,)

    def guarded(service_: Any, principal: Any, args: dict[str, Any]) -> Any:
        require(right, principal)
        return call(service_, principal, args)

    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = None if tool is None else {
        "type": "object", "properties": {**{key: _ID for key in ids}, **dict(tool)},
        "required": [*ids, *required], "additionalProperties": False,
    }
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"},
        principal=(f"edge right {right.value}: {', '.join(kinds)}. The call refuses any other principal, "
                   "an UNAUTHENTICATED one too, with principal_right_required"),
        effect="write" if write else "read", result=result,
        refusals=_CONTRACT_REFUSALS + (("owner_required",) if owner_only else ())
        + ("principal_right_required: the caller lacks the edge right",) + refusals,
        completion="synchronous; the answer is the outcome",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{tool_name or name}",) if schema is not None else ()),
        service=service, method=method, owner_only=owner_only, owner_press=owner_press,
        # Nothing new on the bus: the gate sends no desk frame; its Needs you edges
        # read the proposals on open (fix forward #2122, test_every_write_announces).
        announces_changes=False, call=guarded, http=http, http_status=status, handler=handler,
        tool_schema=schema, authority="authority" if write or owner_only else "work",
        thread=("effect_proposal" if write else "evidence_read") if schema is not None else None,
    )


def _propose(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    from holdspeak.agent_capabilities import Capability, require_capability

    require_capability("claude-code-hooks", Capability.TOOL_HOOKS)
    return service.propose(principal, args)


def _decide(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    from holdspeak.agent_capabilities import Capability, require_capability

    require_capability("claude-code-hooks", Capability.BLOCKING)
    body = {key: value for key, value in args.items() if key != "proposal_id"}
    return service.decide(principal, args.get("proposal_id"), body)


def _usage(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    from holdspeak.agent_capabilities import Capability, require_capability

    require_capability("claude-code-hooks", Capability.USAGE_TOKENS)
    return service.record_usage(principal, args)


def _kernel_decide(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    """The decision only: the admitted envelope never changes here."""
    body = {key: value for key, value in args.items() if key != "operation_id"}
    mutation = sorted({"payload", "arguments", "target", "placement"}.intersection(body))
    if mutation:
        raise ServiceError("admitted_envelope_immutable", "The admitted envelope does not change.",
                           context={"status": 409, "fields": mutation})
    unknown = sorted(set(body) - {"decision", "expected_revision"})
    if unknown:
        raise ServiceError("decision_field_not_allowed", "A decision carries decision and expected_revision only.",
                           context={"status": 400, "fields": unknown})
    try:
        revision = int(body.get("expected_revision"))  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ServiceError("expected_revision_required", "Give expected_revision.", context={"status": 400}) from exc
    return service.decide(principal, args.get("operation_id"), str(body.get("decision") or ""), revision)


def _kernel_receipt(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    if set(args) - {"outcome", "result_ref", "operation_id"}:
        raise ServiceError("receipt_body_invalid", "A receipt carries outcome and result_ref only.",
                           context={"status": 400})
    return service.receipt(principal, args.get("operation_id"), str(args.get("outcome") or ""),
                           str(args.get("result_ref") or ""))


_EVENT_FILTERS = ("operation_id", "event_type", "privacy_class", "stream")
_P, _G, _K = "/api/gate/proposals", "/api/principals", "/api/kernel"
_R = PrincipalRight
_STRING = {"type": "string"}
_GATE_ANSWER = "the proposal: {id, state, session_key, tool, args_sha256, args_head, cwd, expires_at, operation, ...}"

GATE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    # The principals: who may act.
    _op("principals.agent.issue", "gate_service", "issue_agent", ("POST", _G + "/agents"),
        "api_issue_agent_principal", lambda s, p, a: s.issue_agent(p, a.get("agent_identity")),
        "Issue an agent credential for one identity.", _R.DELEGATE, write=True, owner_press=True, status=201,
        result="{principal: agent, identity, credential}", refusals=("ValidationError: identity is required",)),
    _op("principals.agent.revoke", "gate_service", "revoke_agent", ("DELETE", _G + "/agents/{agent_identity}"),
        "api_revoke_agent_principal", lambda s, p, a: s.revoke_agent(p, a.get("agent_identity")),
        "Revoke an agent: its live desk and project grants first (each with its receipt), then its credential.",
        _R.DELEGATE, write=True, owner_press=True, tool={},
        result="{principal: agent, identity, revoked, grant_revoked, project_grants_revoked, ...the desk grant}",
        refusals=("a kernel refusal of a grant revoke: the credential stays",)),
    _op("principals.self.revoke", "gate_service", "revoke_self", ("DELETE", _G + "/self"), "api_revoke_self",
        lambda s, p, a: s.revoke_self(p), "Revoke the caller's own credential.", _R.SELF_REVOKE, write=True,
        tool={}, result="{principal, identity, revoked}"),
    # The gate: a held tool call and its decision.
    _op("gate.propose", "gate_service", "propose", ("POST", _P), "api_gate_propose", _propose,
        "Propose one tool call of an agent session to the gate (the coder hook's call): it is held for the "
        "owner, or decided by the control mode.", _R.AGENT_SUBMIT, write=True,
        tool={"id": _STRING, "tool": _STRING, "args_sha256": _STRING, "args_head": _STRING, "args_len": {"type": "integer"},
              "cwd": _STRING, "ttl_seconds": {"type": "number"}, "parent_operation_id": _STRING},
        result=_GATE_ANSWER, refusals=("ValidationError: id, tool and args_sha256 are required",
                                       "args_mismatch", "principal_scope_required", "proposal_not_admitted",
                                       "CapabilityUnavailableError: tool hooks")),
    _op("gate.proposal.get", "gate_service", "get_proposal", ("GET", _P + "/{proposal_id}"), "api_gate_read",
        lambda s, p, a: s.get_proposal(p, a.get("proposal_id")),
        "Read one gate proposal (an agent reads only its own session's).", _R.AGENT_READ, tool={},
        result=_GATE_ANSWER, refusals=("NotFound: unknown proposal", "principal_scope_required")),
    _op("gate.full_call", "gate_service", "full_call", ("GET", _P + "/{proposal_id}/command"), "api_gate_full_call",
        lambda s, p, a: s.full_call(p, a.get("proposal_id")),
        "Read the whole command of a held call (the owner's Raw read).", _R.DECIDE,
        result="{id, state, session_key, tool, cwd, expires_at, hold_reason, command, whole, shown_chars, "
               "declared_chars, args_cut}", refusals=("NotFound: unknown proposal", "not_held")),
    _op("gate.proposals", "gate_service", "list_proposals", ("GET", _P), "api_gate_list",
        lambda s, p, a: s.list_proposals(p, {"state": a.get("state", "held")}),
        "List the gate proposals in one state (held by default).", _R.OWNER,
        tool={"state": {"type": "string", "enum": ["held", "approved", "denied", "expired", "invalidated"]}},
        result="{proposals: [the proposal with what it shows], state}"),
    _op("gate.decide", "gate_service", "decide", ("POST", _P + "/{proposal_id}/decide"), "api_gate_decide", _decide,
        "Approve or deny a held tool call. The owner's word; an agent is refused.", _R.DECIDE, write=True,
        owner_press=True, tool={"decision": {"type": "string", "enum": ["approved", "denied"]},
                                "reason": {"type": "string", "maxLength": 200}}, required=("decision",),
        result=_GATE_ANSWER, refusals=("ValidationError: decision must be approved|denied", "NotFound: unknown proposal",
                                       "already_decided", "proposal_not_kernel_admitted",
                                       "CapabilityUnavailableError: blocking")),
    _op("gate.receipt", "gate_service", "record_receipt", ("POST", _P + "/{proposal_id}/receipt"), "api_gate_receipt",
        lambda s, p, a: s.record_receipt(p, a.get("proposal_id"), a),
        "Report how an approved call ended (the agent session that proposed it).", _R.AGENT_USAGE, write=True,
        tool={"outcome": {"type": "string", "enum": ["succeeded", "failed"]}}, status=202,
        result="the kernel receipt", refusals=("NotFound: unknown proposal", "principal_scope_required",
                                               "proposal_not_kernel_admitted", "a kernel refusal by name")),
    _op("gate.usage", "gate_service", "record_usage", ("POST", "/api/gate/usage"), "api_gate_usage", _usage,
        "Report the caller session's token use for one model.", _R.AGENT_USAGE, write=True,
        tool={"model": _STRING, **{key: {"type": "integer", "minimum": 0} for key in (
            "input_tokens", "output_tokens", "cache_read_tokens", "cache_creation_tokens")}},
        result="{success: true}", refusals=("ValidationError: figures must be integers",
                                            "CapabilityUnavailableError: usage tokens")),
    _op("gate.session_receipt", "gate_service", "get_session_receipt", ("GET", "/api/sessions/{session_key}/receipt"),
        "api_session_receipt", lambda s, p, a: s.get_session_receipt(p, a.get("session_key")),
        "Read one agent session's receipt: its calls, holds and token use.", _R.OWNER, tool={},
        result="the session receipt (session_receipts.build_receipt)"),
    _op("gate.audit", "gate_service", "audit", ("GET", "/api/gate/audit"), "api_gate_audit",
        lambda s, p, a: s.audit(p, {"limit": _int(a, "limit", 100)}),
        "Read the gate's audit lines, newest first (1 to 500).", _R.OWNER,
        tool={"limit": {"type": "integer", "minimum": 1, "maximum": 500}},
        result="{entries: [{event, proposal_id, ...}]}"),
    _op("gate.config", "gate_service", "config", ("GET", "/api/gate/config"), "api_gate_config",
        lambda s, p, a: s.config(p), "Read the gate's configuration (armed, paths).", _R.OWNER, tool={},
        result="the gate configuration (coder_gate.GateConfig.to_dict)"),
)

_KERNEL_REFUSED = ("KernelRefused: its reason by name (403 for a principal reason, else 409), with operation_id",)

KERNEL_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("kernel.read", "kernel_service", "read", ("GET", _K + "/read"), "api_kernel_read",
        lambda s, p, a: s.read(p, list(a.get("refs") or []), str(a.get("view") or "state"),
                               str(a.get("consistency") or "committed")),
        "Read kernel objects by ref (operation:<id>) in one view.", _R.AGENT_READ,
        tool={"refs": {"type": "array", "items": _STRING}, "view": _STRING, "consistency": _STRING},
        # kernel.get: a read verb (mcp.tools.READ_VERBS), so a launched agent reads it as a read.
        tool_name="kernel.get", result="{view, consistency, objects: [...]}", refusals=_KERNEL_REFUSED),
    _op("kernel.submit", "kernel_service", "submit", ("POST", _K + "/submit"), "api_kernel_submit",
        lambda s, p, a: s.submit(p, a),
        "Submit one operation envelope to the kernel; it is admitted, held for the owner, or refused with a "
        "receipt.", _R.AGENT_SUBMIT, write=True, status=202,
        tool={"request_schema": {"type": "integer"}, "request_id": _STRING, "idempotency_key": _STRING,
              "operation": {"type": "object"}, "subject_refs": {"type": "array", "items": _STRING},
              "target": {"type": "object"}, "arguments": {"type": "object"}, "placement": _STRING,
              "parent_operation_id": _STRING},
        result="{operation_id, state, revision, receipt}", refusals=_KERNEL_REFUSED),
    _op("kernel.decide", "kernel_service", "decide", ("POST", _K + "/operations/{operation_id}/decide"),
        "api_kernel_decide", _kernel_decide,
        "Approve or reject a held kernel operation. The owner's word; an agent is refused.", _R.DECIDE,
        write=True, owner_press=True,
        tool={"decision": {"type": "string", "enum": ["approve", "reject"]}, "expected_revision": {"type": "integer"}},
        required=("decision", "expected_revision"), result="{operation_id, state, revision, receipt}",
        refusals=_KERNEL_REFUSED + ("admitted_envelope_immutable", "decision_field_not_allowed",
                                    "expected_revision_required")),
    _op("kernel.events", "kernel_service", "events", ("GET", _K + "/events"), "api_kernel_events",
        lambda s, p, a: s.events(p, _int(a, "after_cursor", 0), {k: a[k] for k in _EVENT_FILTERS if a.get(k)}),
        "Read the kernel events after a cursor, filtered.", _R.AGENT_READ,
        tool={"after_cursor": {"type": "integer", "minimum": 0}, **{key: _STRING for key in _EVENT_FILTERS}},
        result="{events: [...], cursor}", refusals=_KERNEL_REFUSED),
    _op("kernel.executor.claim", "kernel_service", "claim", ("POST", _K + "/executor/claim"), "api_kernel_claim",
        lambda s, p, a: s.claim(p), "Claim approved work (a node executor).", _R.NODE_LINK, write=True,
        result="{operations: [...], refusal}", refusals=_KERNEL_REFUSED),
    _op("kernel.executor.receipt", "kernel_service", "receipt",
        ("POST", _K + "/executor/operations/{operation_id}/receipt"), "api_kernel_receipt", _kernel_receipt,
        "Record how claimed work ended (a node executor).", _R.NODE_LINK, write=True,
        result="the terminal receipt", refusals=_KERNEL_REFUSED + ("receipt_body_invalid",)),
    _op("kernel.executor.reconcile", "kernel_service", "reconcile",
        ("GET", _K + "/executor/operations/{operation_id}/reconcile"), "api_kernel_reconcile",
        lambda s, p, a: s.reconcile(p, a.get("operation_id")),
        "Read where claimed work stands (a node executor).", _R.NODE_LINK,
        result="the operation's standing", refusals=_KERNEL_REFUSED),
)


class _LiveKernelService:
    """The kernel's caller and executor calls (``kernel.runtime``) for one principal.

    The process's one broker, read at each call; a ``KernelRefused`` becomes a
    ``ServiceError`` with its reason as the code, so every transport names it.
    """

    @staticmethod
    def _run(principal: Any, verb: str, *args: Any) -> Any:
        from holdspeak import kernel
        from holdspeak.kernel.model import KernelRefused
        from holdspeak.kernel.runtime import _as_principal

        try:
            with _as_principal(principal):
                return getattr(kernel, verb)(*args)
        except KernelRefused as exc:
            raise ServiceError(exc.reason, exc.reason, context={
                "status": 403 if "principal" in exc.reason else 409, "operation_id": exc.operation_id or None,
            }) from exc

    def read(self, principal: Any, refs: list[str], view: str = "state", consistency: str = "committed") -> Any:
        return self._run(principal, "read", refs, view, consistency)

    def submit(self, principal: Any, request: Mapping[str, Any]) -> Any:
        return self._run(principal, "submit", dict(request))

    def decide(self, principal: Any, operation_id: str, decision: str, expected_revision: int) -> Any:
        return self._run(principal, "decide", operation_id, decision, expected_revision)

    def events(self, principal: Any, after_cursor: int = 0, filters: Optional[Mapping[str, Any]] = None) -> Any:
        return self._run(principal, "events", after_cursor, dict(filters or {}))

    def claim(self, principal: Any) -> Any:
        return self._run(principal, "claim")

    def receipt(self, principal: Any, operation_id: str, outcome: str, result_ref: str = "") -> Any:
        return self._run(principal, "receipt", operation_id, outcome, result_ref)

    def reconcile(self, principal: Any, operation_id: str) -> Any:
        return self._run(principal, "reconcile", operation_id)


LIVE_KERNEL_SERVICE = _LiveKernelService()

__all__ = ["GATE_OPERATIONS", "KERNEL_OPERATIONS", "LIVE_KERNEL_SERVICE", "RIGHTS", "holders", "require"]
