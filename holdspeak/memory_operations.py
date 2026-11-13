"""Memory's desk reads and its meaning-search switch on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``automation_operations.py`` is. Each row states one verb
once: its call (``web_call`` where the desk's shape differs: Search draws plain
snippets), its HTTP method and path, and its MCP tool schema.
``web/routes/memory.py`` produces the routes and ``mcp/families/declared.py``
the tools from these rows, both through ``OperationRegistry.invoke``.
``memory.search`` was a hand-written tool of ``mcp/families/memory.py``; it is
this row now, with the same name and schema. ``memory.page`` and
``memory.observations`` stay their own rows in ``operations.py``.

No row calls a model: a search may wait a bounded time for the question's
embedding (``blocking_io``), and Turn on is the one press that may start the
meaning model's download (the owner's, config). Imported only through
``holdspeak.operations``.
"""
from __future__ import annotations

from holdspeak.held_arguments import held_arguments, constant

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ServiceError, ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver); the memory service needs the READ right"
_REFUSALS = _CONTRACT_REFUSALS + ("ServiceError read_forbidden", "ValidationError: a bad query, kind, scope or limit")
_TRUE = {"1", "true", "yes", "on"}


def _int(args: Mapping[str, Any], key: str, default: int) -> int:
    value = args.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{key} must be an integer") from None


def _search_args(args: Mapping[str, Any]) -> dict[str, Any]:
    keys = ("kind", "project_id", "time_from", "time_to")
    return {**{key: args[key] for key in keys if args.get(key) is not None},
            "limit": _int(args, "limit", 50), "offset": _int(args, "offset", 0)}


def _meaning(service: Any) -> Any:
    meaning = getattr(service, "meaning", None)
    if meaning is None:
        raise ServiceError("meaning_search_unavailable", "Meaning search is not available on this hub.",
                           context={"status": 503})
    return meaning


def _recall(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    newest = str(args.get("recent") or "").strip().lower() in _TRUE or args.get("recent") is True
    return service.recall(principal, str(args.get("query") or ""), filter=args.get("filter") or "all",
                          limit=_int(args, "limit", 50), recent=newest)


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str,
        *, properties: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (),
        web: Optional[Call] = None, write: bool = False, owner: bool = False,
        blocking: bool = False, facts: dict[str, Any] | None = None) -> OperationDescriptor:
    tool = {**dict(facts or {}), "type": "object", "properties": dict(properties or {}), "required": list(required),
            "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result="the service answer, in the route's envelope",
        refusals=_REFUSALS + (("owner_required",) if owner else ()),
        completion="synchronous; no model call", exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"),
        service=service, method=method, call=call, web_call=web, http=http, handler=handler, tool_schema=tool,
        owner_only=owner, blocking_io=blocking,
        # Turn on and off are his (config): no thread offers them.
        authority="config" if owner else "work", thread=None if owner else "evidence_read",
    )


_SEARCH = {
    "query": {"type": "string", "description": "Search query."},
    "kind": {"type": "string", "description": "Kinds: decision, decision_record, desk_decision, artifact, meeting, "
                                              "note, thread, action, project_item, workbench_item, cadence, send, "
                                              "project_update, prep_brief, calendar_event."},
    "project_id": {"type": "string", "description": "Project ID."},
    "time_from": {"type": "string", "description": "ISO-8601 start."},
    "time_to": {"type": "string", "description": "ISO-8601 end."},
    "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum; default 50."},
    "offset": {"type": "integer", "minimum": 0, "description": "Pagination offset."},
}

MEMORY_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("memory.search", "memory_service", "search", ("GET", "/api/memory/search"), "search_memory",
        lambda s, p, a: s.search(p, str(a.get("query") or ""), **_search_args(a)),
        "Search memory: decisions, meetings (transcript, summary), notes, threads, actions, project "
        "milestones/risks, sends, published updates, prep briefs, calendar events. Returns records; use "
        "project.list for projects; read permission applies.",
        properties=_SEARCH, required=("query",), blocking=True,
        web=lambda s, p, a: s.search_for_desk(p, str(a.get("query") or ""), **_search_args(a))),
    _op("memory.pages", "memory_service", "standing_pages", ("GET", "/api/memory/pages"), "memory_pages",
        lambda s, p, a: s.standing_pages(p, scope=a.get("scope"), project_id=a.get("project_id")),
        "Read the standing memory pages of one scope (a project's, or the desk's): each a standing answer "
        "with its sources. No model call.",
        properties={"scope": {"type": ["string", "null"], "enum": ["desk", "project", None]},
                    "project_id": {"type": ["string", "null"]}}),
    _op("memory.recall", "recall_service", "recall", ("GET", "/api/memory/recall"), "recall_memory", _recall,
        "Recall over one query: what is current, superseded, disputed and owed. recent true with no query "
        "reads the desk's newest memory.",
        properties={"query": {"type": "string"},
                    "filter": {"type": "string", "enum": ["all", "current", "superseded", "disputed", "owed"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                    "recent": {"type": ["boolean", "string"]}}),
    _op("memory.meaning.status", "memory_service", "meaning", ("GET", "/api/memory/meaning-search"),
        "meaning_search_status", lambda s, p, a: _meaning(s).status(p),
        "Read meaning search's state: off, downloading, indexing or on."),
    _op("memory.meaning.turn_on", "memory_service", "meaning", ("POST", "/api/memory/meaning-search/turn-on"),
        "meaning_search_turn_on", lambda s, p, a: _meaning(s).turn_on(p),
        "Turn meaning search on: the one press that may start the meaning model's download. Owner only.",
        write=True, owner=True, blocking=True, facts=held_arguments('Turn on meaning search',
                constant('Feature', 'Meaning search'),
                constant('On', 'True'))),
    _op("memory.meaning.turn_off", "memory_service", "meaning", ("POST", "/api/memory/meaning-search/turn-off"),
        "meaning_search_turn_off", lambda s, p, a: _meaning(s).turn_off(p),
        "Turn meaning search off. Owner only.", write=True, owner=True, facts=held_arguments('Turn off meaning search',
                constant('Feature', 'Meaning search'),
                constant('On', 'False'))),
)

__all__ = ["MEMORY_OPERATIONS"]
