"""The verbs of the delivery runtime (``/api/delivery``) on ``DeliveryService``, on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one verb
once: its call, its HTTP method and path, and its MCP tool schema.
``web/routes/delivery_declared.py`` produces the routes and ``mcp/families/declared.py``
the tools from these rows, both through ``OperationRegistry.invoke``.

A read is ``thread="evidence_read"`` and stays MCP and HTTP only (the seeded
thread palettes do not grow, ``services/thread_modes.py``); a write is
``thread="effect_proposal"``. A launched agent reads these reads and never
calls these writes (``services/conductor_launch.py`` derives both rules from
the rows). Imported only through ``holdspeak.operations`` (it imports this module).

The node link stays HTTP-only: the transport holds the per-node token.
Terminal live stays HTTP-only and hand-written: NDJSON frames and disconnect
cleanup. Factory, terminal commands, PR handoff/propose/decide and the desk's
actuators enter the registry. Only the owner launches, types, decides or executes.
Desk actuator proposals stay pending even in YOLO; the owner decides.

``pr_receipts`` is the internal cache collaborator behind the shared PR read
rows (including ``delivery.prs``), not a serializable operation result.
``default_launch_service``, ``actuator_proposal`` and ``execute_actuator_proposal``
are internal collaborators of the declared PR actions, never independent routes.

"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("a typed delivery refusal (its code, and the HTTP status and body in its context)",)
_ID = {"type": "string", "minLength": 1}
_TEXT = {"type": "string"}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        write: bool = False, owner_only: Optional[bool] = None, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = (), status: int = 200, tool: bool = True, held: tuple[str, ...] = (), authority: str = "work", blocking_io: bool = False, web_call: Optional[Call] = None,
        result: str = "the DeliveryService answer, as the route answered it") -> OperationDescriptor:
    """One verb of ``delivery_service``; its tool requires the path's ids and ``required``."""
    owns = write if owner_only is None else owner_only
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result=result, refusals=_REFUSALS + ("owner_required",),
        completion="synchronous; a write is one desk_changed frame on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()), service="delivery_service", method=method,
        owner_only=owns, owner_press=owns and write, announces_changes=bool(held), held=held, authority=authority, blocking_io=blocking_io, call=call, web_call=web_call, http=http, http_status=status,
        handler=handler, tool_schema=schema if tool else None, thread=("effect_proposal" if write else "evidence_read") if tool else None,
    )


def _node_request(service: Any, principal: Any, verb: str, args: dict[str, Any]) -> Any:
    from holdspeak.principals import PrincipalKind
    from holdspeak.operations import OperationOwnerRequired
    if getattr(principal, "kind", None) is PrincipalKind.AGENT:
        raise OperationOwnerRequired(f"delivery.node.{verb}")
    return service.node_request(principal, verb, args)


_D = "/api/delivery"
_PR = _D + "/prs/{source_id}/{number}"
DELIVERY_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("delivery.pr_send_agent", "send_pr_agent", ("POST", _PR + "/send-agent"), "api_delivery_pr_send_agent",
        lambda s, p, a: s.send_pr_agent(p, a["source_id"], a["number"], a),
        "Hand one PR and its bounded diff to a coding agent. Only the owner starts it.",
        write=True, authority="egress", blocking_io=True, properties={"instruction": _TEXT, "agent_profile_id": _ID},
        status=202),
    _op("delivery.pr_propose", "propose_pr", ("POST", _PR + "/propose"), "api_delivery_pr_propose",
        lambda s, p, a: s.propose_pr(p, a["source_id"], a["number"], a),
        "Propose a PR comment or commit status. The owner decides before it is sent.",
        write=True, authority="egress", blocking_io=True,
        properties={"kind": _TEXT, "body": _TEXT, "description": _TEXT, "state": _TEXT, "context": _TEXT}, status=202),
    _op("delivery.pr_decide", "decide_pr", ("POST", _D + "/prs/proposals/{proposal_id}/decide"), "api_delivery_pr_decide",
        lambda s, p, a: s.decide_pr(p, a["proposal_id"], a.get("decision")),
        "Decide a PR proposal and execute its approved action. Only the owner decides.",
        write=True, authority="egress", blocking_io=True, properties={"decision": {"enum": ["approve", "reject"]}}),
    _op("delivery.factory_launch", "factory_launch", ("POST", _D + "/factory/launch"), "api_factory_launch",
        lambda s, p, a: s.factory_launch(p, a), "Launch one agent from a registered profile and worktree. Only the owner launches.",
        write=True, authority="authority", blocking_io=True,
        properties={"agent_profile_id": _ID, "source_id": _ID, "worktree": {"type": "object"},
            "story_ref": {"type": "object"}, "session_label": _TEXT, "options": {"type": "object"}}),
    _op("delivery.terminal_command", "terminal_command", ("POST", _D + "/terminal/commands"), "api_terminal_command",
        lambda s, p, a: s.terminal_command(p, a), "Submit one owner terminal command with the hub's authority checks.",
        write=True, authority="authority", blocking_io=True,
        properties={"command_id": _ID, "target_id": _ID, "target_generation": _ID,
            "operation": {"type": "object"}, "payload": {"type": "object"},
            "expected_sequence": {"type": "integer"}, "issued_at": _TEXT, "expires_at": _TEXT}),
    *(_op(f"delivery.node.{verb}", "node_call", ("POST", f"{_D}/node/{verb}"), f"api_node_{verb}",
        lambda s, p, a, verb=verb: _node_request(s, p, verb, a),
        "Node protocol traffic. HTTP only: authenticate the held per-node token on every call.",
        write=True, owner_only=False, tool=False, held=("node_token",), authority="authority", blocking_io=True)
      for verb in ("hello", "heartbeat")),
    _op("delivery.terminal_live", "terminal_subscribe", ("POST", _D + "/terminal/live"), "api_terminal_live",
        lambda s, p, a: s.terminal_subscribe(a["target_id"], a["target_generation"],
            stream_id=a.get("stream_id"), resume_sequence=a.get("resume_sequence")),
        "Read a terminal as an NDJSON stream. HTTP only: streaming response and disconnect cleanup.",
        owner_only=True, tool=False, blocking_io=True),
    _op("delivery.snapshot", "snapshot", ("GET", _D + "/snapshot"), "api_delivery_snapshot",
        lambda s, p, a: s.snapshot(p),
        "Read the delivery snapshot: every registered source with its freshness. The snapshot is cached; "
        "a read does not run dw or gh.", blocking_io=True),
    _op("delivery.sources", "sources", ("GET", _D + "/sources"), "api_delivery_sources",
        lambda s, p, a: s.sources(p), "List the registered delivery sources with their labels and status."),
    _op("delivery.source_register", "register_source", ("POST", _D + "/sources"), "api_delivery_register_source",
        lambda s, p, a: s.register_source(p, a.get("path"), a.get("label")),
        "Register a delivery source by its path. The hub resolves and validates the path.", write=True,
        properties={"path": _ID, "label": _TEXT}, required=("path",), blocking_io=True),
    _op("delivery.attempts", "list_attempts", ("GET", _D + "/attempts"), "api_delivery_list_attempts",
        lambda s, p, a: s.list_attempts(p, a.get("source_id", ""), a.get("project", ""), a.get("story_id", ""),
                                        a.get("session_id", ""), a.get("active_only", False)),
        "List the work attempts with their state and origin. Filter by source, project, story or session.",
        properties={"source_id": _TEXT, "project": _TEXT, "story_id": _TEXT, "session_id": _TEXT,
                    "active_only": {"type": "boolean"}}, blocking_io=True),
    _op("delivery.attempt_create", "create_attempt", ("POST", _D + "/attempts"), "api_delivery_create_attempt",
        lambda s, p, a: s.create_attempt(p, a.get("source_id"), a.get("worktree_id"), a.get("project"),
                                         a.get("story_id"), a.get("session_id"), a.get("node_id"),
                                         a.get("target_id")),
        "Attach a work attempt to a story by hand. A session that has a live attempt is refused.", write=True,
        properties={"source_id": _ID, "worktree_id": _ID, "project": _ID, "story_id": _ID, "session_id": _TEXT,
                    "node_id": _TEXT, "target_id": _TEXT},
        required=("source_id", "worktree_id", "project", "story_id")),
    _op("delivery.story_dossier", "story_dossier", ("GET", _D + "/stories/{project}/{story}/dossier"),
        "api_story_dossier", lambda s, p, a: s.story_dossier(p, a.get("project"), a.get("story"), a.get("source", "")),
        "Read the evidence dossier of one story. Give source to read one source only.",
        properties={"source": _TEXT}, blocking_io=True),
    _op("delivery.phase_dossier", "phase_dossier", ("GET", _D + "/phases/{project}/{phase}/dossier"),
        "api_phase_dossier", lambda s, p, a: s.phase_dossier(p, a.get("project"), a.get("phase"), a.get("source", "")),
        "Read the evidence dossier of one phase: its story dossiers and the final summary. Metadata only.",
        properties={"source": _TEXT}, blocking_io=True),
    _op("delivery.evidence_asset", "evidence_asset", ("GET", _D + "/evidence/{bundle_id}/{asset_id}"),
        "api_evidence_asset",
        lambda s, p, a: s.evidence_asset_wire(p, a.get("bundle_id"), a.get("asset_id")),
        "Read one evidence file that the bundle manifest names, as base64 with its media type.",
        web_call=lambda s, p, a: s.evidence_asset(p, a.get("bundle_id"), a.get("asset_id")), blocking_io=True,
        result="the asset bytes and its manifest member (HTTP: the file; MCP: base64)"),
    _op("delivery.prs", "pr_rows", ("GET", _D + "/prs"), "api_delivery_prs", lambda s, p, a: s.pr_rows(p),
        "List the cached pull requests of the registered sources, with their freshness."),
    _op("delivery.prs_refresh", "refresh_prs", ("POST", _D + "/prs/refresh"), "api_delivery_prs_refresh",
        lambda s, p, a: s.refresh_prs(p, a.get("source_id")),
        "Read the pull requests from GitHub again, for one source or for all sources.", write=True,
        properties={"source_id": _TEXT}, blocking_io=True),
    _op("delivery.pr_diff", "pr_diff", ("GET", _PR + "/diff"), "api_delivery_pr_diff",
        lambda s, p, a: s.pr_diff(p, a.get("source_id"), a.get("number")),
        "Read the local diff of one pull request. If it is not local, the answer says so.", blocking_io=True),
    _op("delivery.pr_fetch", "fetch_pr", ("POST", _PR + "/fetch"), "api_delivery_pr_fetch",
        lambda s, p, a: s.fetch_pr(p, a.get("source_id"), a.get("number")),
        "Fetch the head of one pull request from GitHub, so that its diff is local.", write=True,
        blocking_io=True),
    _op("delivery.nodes", "nodes", ("GET", _D + "/nodes"), "api_delivery_nodes", lambda s, p, a: s.nodes(p),
        "List the delivery nodes with their liveness and the time each was last seen."),
    # The terminal reads are owner-only, as the HTTP edge holds them: they
    # show what the owner's terminals show.
    _op("delivery.terminal_sessions", "terminal_sessions", ("GET", _D + "/terminal/sessions"),
        "api_terminal_sessions", lambda s, p, a: s.terminal_sessions(p),
        "List the local terminal sessions from the live tmux panes.", owner_only=True, blocking_io=True),
    _op("delivery.terminal_read", "terminal_read", ("POST", _D + "/terminal/subscriptions"),
        "api_terminal_subscribe",
        lambda s, p, a: s.terminal_read(p, a.get("target_id"), a.get("target_generation"),
                                        a.get("resume_sequence"), a.get("last_hash")),
        "Read the output of one terminal target: a snapshot, the new output after resume_sequence, "
        "or a typed absence.", owner_only=True,
        properties={"target_id": _ID, "target_generation": _ID, "resume_sequence": {"type": "integer"},
                    "last_hash": _TEXT}, required=("target_id", "target_generation"), blocking_io=True),
    _op("delivery.factory_profiles", "factory_profiles", ("GET", _D + "/factory/profiles"),
        "api_factory_profiles", lambda s, p, a: s.factory_profiles(p),
        "List the agent profiles that this node can launch."),
    _op("delivery.factory_discover", "factory_discover", ("GET", _D + "/factory/discover"),
        "api_factory_discover", lambda s, p, a: s.factory_discover(p),
        "List the agent panes and sessions as targets. The read first binds new story claims.",
        blocking_io=True),
)

def _actuator(name: str, target: str, *, decide: bool) -> OperationDescriptor:
    from holdspeak.web_requests import _CompanionSlackRequest, _ProposalDecisionRequest

    model = _ProposalDecisionRequest if decide else _CompanionSlackRequest
    method = f"{'decide' if decide else 'propose'}_{target}"
    path = f"/api/desk/actuators/{target}/" + ("{proposal_id}/decision" if decide else "propose")
    schema = model.model_json_schema()
    if decide:
        schema["properties"].pop("decided_by", None)  # actor comes from authentication
        schema["properties"]["proposal_id"] = _ID
        schema["required"] = [*schema.get("required", []), "proposal_id"]
    schema["additionalProperties"] = False
    def call(service, principal, args):
        data = {k: v for k, v in args.items() if k != "proposal_id"}
        from pydantic import ValidationError as PayloadInvalid
        from holdspeak.services.errors import ValidationError
        try:
            payload = model.model_validate(data)
        except PayloadInvalid as exc:
            raise ValidationError("The proposal fields are invalid.") from exc
        if decide:
            return getattr(service, method)(principal, args["proposal_id"], payload)
        return getattr(service, method)(principal, payload)
    return OperationDescriptor(name=name, version=1,
        description=("Decide and execute one actuator proposal. Only the owner decides." if decide else
            "Propose one external action. The proposal stays pending for the owner."),
        args_schema={"type": "object"}, principal=_PRINCIPAL, effect="write", result="{success, proposal}",
        refusals=_REFUSALS + ("owner_required", "ValidationError", "NotFound"), completion="synchronous; actuator lifecycle frames",
        exposure=(f"http:POST {path}", f"mcp:{name}"), service="actuator_service", method=method,
        call=call, http=("POST", path), handler=method, tool_schema=schema,
        owner_only=decide, owner_press=decide, authority="egress" if decide else "work",
        thread=None if decide else "effect_proposal", blocking_io=True, announces_changes=True)


DELIVERY_OPERATIONS += tuple(_actuator(f"delivery.actuator.{target}.{verb}", target, decide=verb == "decide")
    for target in ("slack", "webhook", "github") for verb in ("propose", "decide"))

__all__ = ["DELIVERY_OPERATIONS"]
