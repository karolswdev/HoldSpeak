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

DECISION_OPERATIONS: tuple[OperationDescriptor, ...] = (DECISION_LEDGER, COMMIT_DECISION)

__all__ = ["DECISION_OPERATIONS"]
