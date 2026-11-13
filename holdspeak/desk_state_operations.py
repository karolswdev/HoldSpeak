"""The Desk's own state on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``automation_operations.py`` is. Each row states one verb
once: its call, its HTTP method and path, and its MCP tool schema. The routes
are produced in ``web/routes/projections.py``, ``today.py``, ``desk_seed.py``
and ``core.py``; ``mcp/families/declared.py`` makes the tools. Both go
through ``OperationRegistry.invoke``.

- the projections: the desk's attention and receipts, and one projection's
  presentation (acknowledge, dismiss, restore);
- Today's Since this morning;
- the hub's health;
- seed and reset: the owner's alone (reset is the desk's first destructive
  act), so an agent is refused and no thread offers them;
- the owner's constitutional context (the always-on context every agent run
  receives): anyone reads it; only he changes it (authority).

Imported only through ``holdspeak.operations``.
"""
from __future__ import annotations

from holdspeak.held_arguments import held_arguments, text, named, constant

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("ValidationError", "NotFound: unknown projection")
_ID = {"type": "string", "minLength": 1}
_TRUE = {"1", "true", "yes", "on"}


def _int(args: Mapping[str, Any], key: str, default: int) -> int:
    try:
        return int(args.get(key, default))
    except (TypeError, ValueError):
        raise ValidationError(f"{key} must be an integer") from None


def _projections(service: Any, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
    dismissed = args.get("include_dismissed")
    filters = {
        "q": str(args.get("q") or ""), "kind": args.get("kind"), "attention_state": args.get("attention_state"),
        "subject_ref": args.get("subject_ref"),
        "include_dismissed": dismissed is True or str(dismissed or "").strip().lower() in _TRUE,
        "offset": _int(args, "offset", 0), "limit": _int(args, "limit", 50),
    }
    return {"version": 1, **service.list(principal, filters)}


def _presentation(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    projection_id = str(args.get("projection_id"))
    state = {key: value for key, value in args.items() if key != "projection_id"}
    return service.set_presentation(principal, projection_id, state)


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str,
        *, properties: Optional[Mapping[str, Any]] = None, write: bool = False,
        owner: bool = False, facts: dict[str, Any] | None = None) -> OperationDescriptor:
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {**dict(facts or {}), "type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids, "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result="the service answer, in the route's envelope",
        refusals=_REFUSALS + (("owner_required",) if owner else ()),
        completion="synchronous" + ("; one desk_changed frame" if write else ""),
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service=service, method=method, call=call,
        http=http, handler=handler, tool_schema=tool, owner_only=owner,
        authority="authority" if owner else "work",
        thread=None if owner else "effect_proposal" if write else "evidence_read",
    )


DESK_STATE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("desk.projection.list", "projection_service", "list", ("GET", "/api/desk/projections"),
        "api_list_projections", _projections,
        "List the desk's projections: what needs attention and the receipts of finished work, newest first. "
        "attention_state needs_attention narrows to what needs him.",
        properties={"q": {"type": "string"}, "kind": {"type": ["string", "null"]},
                    "attention_state": {"type": ["string", "null"]}, "subject_ref": {"type": ["string", "null"]},
                    "include_dismissed": {"type": "boolean"},
                    "offset": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200}}),
    _op("desk.projection.present", "projection_service", "set_presentation",
        ("PUT", "/api/desk/projections/{projection_id}/presentation"), "api_set_projection_presentation",
        _presentation, "Change how one projection shows: acknowledge, dismiss or restore it (action).",
        write=True, properties={"action": {"type": "string", "enum": ["acknowledge", "dismiss", "restore"]}}, facts=held_arguments('Change a notice',
                named('projection_id', 'Notice', 'desk.projection.list', {}, 'summary.title|title', rows='projections|items', match={'projection_id': 'projection_id'}),
                text('action', 'Action'))),
    _op("today.since_morning", "today_service", "since_morning", ("GET", "/api/today/since-morning"),
        "since_morning", lambda s, p, a: s.since_morning(p),
        "Read what got done today: tasks ticked, decisions recorded, notes filed, sends sent, meetings held, "
        "and the Programs block, newest first."),
    _op("desk.health", "desk_service", "health", ("GET", "/health"), "health", lambda s, p, a: s.health(),
        "Read the hub's health: ok, or unhealthy with the projection faults."),
    _op("desk.seed", "desk_service", "seed", ("POST", "/api/desk/seed"), "api_desk_seed",
        lambda s, p, a: s.seed(p), "Seed the desk with its starting objects. Owner only.", write=True, owner=True, facts=held_arguments('Add the starting objects',
                constant('Scope', "Owner's Desk"),
                constant('Action', 'Add starting objects'))),
    _op("desk.reset", "desk_service", "reset", ("POST", "/api/desk/reset"), "api_desk_reset",
        lambda s, p, a: s.reset(p), "Reset the desk: its objects are tombstoned and the seed is put back. Owner only.",
        write=True, owner=True, facts=held_arguments('Reset the Desk',
                constant('Scope', "Owner's Desk"),
                constant('Action', 'Park Desk objects and add starting objects'))),
    _op("constitutional_context.read", "constitutional_context_service", "get", ("GET", "/api/constitutional-context"),
        "api_get_context", lambda s, p, a: {"context": s.get(p)},
        "Read the owner's constitutional context: the always-on text every agent run receives, its revision "
        "and its character limit."),
    _op("constitutional_context.update", "constitutional_context_service", "update",
        ("PUT", "/api/constitutional-context"), "api_update_context",
        lambda s, p, a: {"context": s.update(p, a.get("content"))},
        "Replace the owner's constitutional context. Owner only.", write=True, owner=True,
        properties={"content": {"type": "string", "maxLength": 32768}}),
    _op("constitutional_context.history", "constitutional_context_service", "history",
        ("GET", "/api/constitutional-context/history"), "api_context_history",
        lambda s, p, a: {"revisions": s.history(p)},
        "Read the last ten revisions of the owner's constitutional context, newest first."),
)

__all__ = ["DESK_STATE_OPERATIONS"]
