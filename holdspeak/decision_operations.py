"""The Decisions app's web verbs on the one declared contract (2026-11-08).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. The ``decision.*`` core
rows (create, read, update, status, supersede, delete) are in
``operations.py``; these are the two the native Decisions face needed that a
route still made by hand: the desk's ledger of decisions (one page, the
total, a search) and Commit (a decided record becomes a commitment).
``web/routes/decisions.py`` produces the routes and
``mcp/families/declared.py`` the tools from these rows, both through
``OperationRegistry.invoke``.

Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_ID = {"type": "string", "minLength": 1}


def _flag(value: Any) -> bool:
    """A query flag (``?current=true``) or a JSON boolean."""
    return value.strip().lower() in {"1", "true", "yes", "on"} if isinstance(value, str) else bool(value)


def _ledger(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return service.list_decisions(
        principal, scope="all", meeting_id=args.get("meeting_id") or None,
        decision_id=args.get("decision_id") or None, q=args.get("q") or None,
        current=_flag(args.get("current")), limit=int(args.get("limit") or 200),
        offset=int(args.get("offset") or 0),
    )


def _commit(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return service.commit_decision(
        principal, str(args.get("decision_id") or ""), owner=args.get("who") or None,
        due_at=args.get("due_at") or None,
    )


DECISION_LEDGER = OperationDescriptor(
    name="decision.ledger", version=1,
    description=("List every decision on the desk, newest first: a meeting's decisions with the meeting's "
                 "title, and the Desk decisions with their status. Each row names its record and the person "
                 "it is committed to, when there is one. One page and the total; q searches the words."),
    args_schema={"type": "object"}, principal=_PRINCIPAL, effect="read",
    result=("one page of decisions, each with its source, id, text, rationale, decided_at, lifecycle, status, "
            "meeting_id, meeting_title, record_id, committed_to and committed; and the page's offset, limit, count "
            "and total"),
    refusals=_CONTRACT_REFUSALS + ("PermissionDenied: the READ right",),
    completion="synchronous; nothing changes",
    exposure=("http:GET /api/decisions/ledger", "mcp:decision.ledger"),
    service="decision_lifecycle_service", method="list_decisions", call=_ledger,
    http=("GET", "/api/decisions/ledger"), handler="api_decision_ledger",
    tool_schema={"type": "object", "properties": {
        "q": {"type": "string", "description": "Words the decision, its reason or its meeting's title holds."},
        "current": {"type": "boolean", "description": "Only the decisions that stand now."},
        "meeting_id": _ID, "decision_id": _ID,
        "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Default 200."},
        "offset": {"type": "integer", "minimum": 0},
    }, "required": [], "additionalProperties": False},
    # A read is evidence; it stays MCP and HTTP only (thread_modes._MCP_ONLY).
    thread="evidence_read",
)

COMMIT_DECISION = OperationDescriptor(
    name="follow_through.commit_decision", version=1,
    # ``who``, not ``owner``: the contract refuses an authority word as an
    # argument (AUTHORITY_FIELDS); the hand-written tool took ``owner``.
    description="Create an accountable commitment from an accepted decision.",
    args_schema={"type": "object"}, principal=_PRINCIPAL, effect="write",
    result="the commitment {id, decision_id, action_item_id, owner, due_at, status, replayed}",
    refusals=_CONTRACT_REFUSALS + ("ValueError: decision not found", "ValueError: only accepted decisions can be committed"),
    completion="synchronous; a second call answers the first commitment (replayed) and writes nothing",
    exposure=("http:POST /api/decision-records/{decision_id}/commit", "mcp:follow_through.commit_decision"),
    service="follow_through_service", method="commit_decision", call=_commit,
    http=("POST", "/api/decision-records/{decision_id}/commit"), handler="api_commit_decision_record",
    tool_schema={"type": "object", "properties": {
        "decision_id": {"type": "string", "description": "Accepted decision ID."},
        "who": {"type": "string", "description": "Optional person."},
        "due_at": {"type": "string", "description": "Optional ISO-8601 date."},
    }, "required": ["decision_id"], "additionalProperties": False},
    thread="effect_proposal",
)

# ── 2026-11-09 (ops/projects): the meeting decision's lifecycle verbs and the
# record ledger's reads, the routes ``decisions.py`` and ``decision_records.py``
# answered by hand. A meeting decision lives in ``decisions``; a Desk decision in
# ``desk_decisions`` (``decision.read`` / ``decision.supersede`` in operations.py).


def _complete(coroutine: Any) -> Any:
    """Run a service coroutine to its end from a synchronous call (an engine draft).

    The registry calls off the event loop (a produced route's threadpool);
    a caller that holds a running loop gets a thread of its own."""
    import asyncio

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coroutine).result()


def _rest(args: dict[str, Any], *ids: str) -> dict[str, Any]:
    return {key: value for key, value in args.items() if key not in ids}


def _op(name: str, method: str, description: str, call: Any, *, service: str = "decision_lifecycle_service",
        http: Any = None, handler: Any = None, write: bool = False, properties: Any = None,
        required: tuple[str, ...] = (), owner_only: bool = False, result: str = "the service's answer") -> OperationDescriptor:
    ids = [part[1:-1] for part in (http[1] if http else "").split("/") if part.startswith("{")]
    props = {**{key: _ID for key in ids}, **dict(properties or {})}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result=result,
        refusals=_CONTRACT_REFUSALS + ("NotFound: unknown decision or record", "ValidationError", "ConflictError",
                                       "PermissionDenied: the READ, DECIDE or OWNER right"),
        completion="synchronous; a write is one desk_changed frame on the hub bus",
        exposure=((f"http:{http[0]} {http[1]}",) if http else ()) + (f"mcp:{name}",),
        service=service, method=method, call=call, http=http, handler=handler, owner_only=owner_only,
        tool_schema={"type": "object", "properties": props, "required": [*ids, *required],
                     "additionalProperties": False},
        # A read is evidence; it stays MCP and HTTP only (thread_modes._MCP_ONLY).
        thread="effect_proposal" if write else "evidence_read",
    )


_D = "/api/decisions/{decision_id}"
_ARTIFACT = {"artifact_type": {"type": "string", "minLength": 1,
                               "description": "The artifact to promote the decision to (adr, story, ...)."}}
LIFECYCLE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    # The decision's own read: GET /api/decisions/{id} keeps its hand-written
    # handler (it probes which store owns the id, then invokes this or
    # decision.read), so this row has no route of its own.
    _op("decision.lineage", "get_decision",
        "Read one meeting decision with its lineage (what it superseded and what superseded it).",
        lambda s, p, a: s.get_decision(p, str(a.get("decision_id") or "")),
        properties={"decision_id": _ID}, required=("decision_id",)),
    _op("decision.moment", "get_moment", "Read the meeting moment one decision was made in (its transcript span).",
        lambda s, p, a: s.get_moment(p, str(a.get("decision_id") or "")),
        http=("GET", _D + "/moment"), handler="get_decision_moment"),
    _op("decision.accept", "transition", "Accept one proposed meeting decision.",
        lambda s, p, a: s.transition(p, str(a.get("decision_id") or ""), "accept", {}),
        http=("POST", _D + "/accept"), handler="accept_decision", write=True),
    # POST /api/decisions/{id}/supersede keeps its hand-written handler: a Desk
    # decision is the admitted decision.supersede (operations.py), a meeting
    # decision this row.
    _op("decision.meeting_supersede", "supersede",
        "Supersede one meeting decision by another (superseded_by names the successor decision).",
        lambda s, p, a: s.supersede(p, str(a.get("decision_id") or ""), _rest(a, "decision_id")), write=True,
        properties={"decision_id": _ID, "superseded_by": _ID}, required=("decision_id", "superseded_by")),
    _op("decision.promote", "promote", "Promote an accepted meeting decision to an artifact (an ADR, a story).",
        lambda s, p, a: s.promote(p, str(a.get("decision_id") or ""), str(a.get("artifact_type") or ""), {}),
        http=("POST", _D + "/promote/{artifact_type}"), handler="promote_decision", write=True),
    _op("decision.promote_draft", "draft_promoted_with_model",
        "Draft the promoted artifact of an accepted decision with the engine its assignment names.",
        lambda s, p, a: _complete(s.draft_promoted_with_model(
            p, str(a.get("decision_id") or ""), str(a.get("artifact_type") or ""),
            _rest(a, "decision_id", "artifact_type"))),
        http=("POST", _D + "/promote/{artifact_type}/draft-with-model"), handler="draft_promoted_decision_with_model",
        write=True, owner_only=True),
)

_R = "decision_record_service"
RECORD_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("decision_record.due_for_review", "due_for_review", "List the decision records due for review now.",
        lambda s, p, a: s.due_for_review(p), service=_R,
        http=("GET", "/api/decision-records/review"), handler="records_due_for_review"),
    _op("decision_record.for_source", "records_for_source",
        "List the decision records minted from one source (source_type: meeting, desk, ...; source_id).",
        lambda s, p, a: s.records_for_source(p, str(a.get("source_type") or ""), str(a.get("source_id") or "")),
        service=_R, http=("GET", "/api/decision-records/source/{source_type}/{source_id}"),
        handler="records_for_source"),
    _op("decision_record.carry", "carry", "Carry a current decision record into its project's next brief.",
        lambda s, p, a: s.carry(p, str(a.get("record_id") or ""), project_id=a.get("project_id") or None),
        service=_R, http=("POST", "/api/decision-records/{record_id}/carry"), handler="carry_record", write=True,
        properties={"project_id": _ID}),
)

DECISION_OPERATIONS: tuple[OperationDescriptor, ...] = (DECISION_LEDGER, COMMIT_DECISION) + LIFECYCLE_OPERATIONS \
    + RECORD_OPERATIONS

__all__ = ["DECISION_OPERATIONS"]
