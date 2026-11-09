"""The Automations face's verbs on the one declared contract (2026-11-08).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one
``WorkbenchService`` verb once: its call, its HTTP method and path, and its MCP
tool schema. ``web/routes/primitives/workbenches.py`` produces the routes and
``mcp/families/declared.py`` the tools from these rows, both through
``OperationRegistry.invoke``.

Each call answers the shape the hand-written route answered (the face reads
it unchanged), and names a missing object in the route's words ("Unknown
automation: <id>"). A write the service announces (``on_changed``) sends its
frame; the registry names the rest ``workbench`` (the kind the desk refreshes
on), so no write is silent. When and With keep the schedule-delegation rule
(``mcp/tool_authority.py``): When is authority, With is config; the service
refuses any principal but the owner. Imported only through
``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import NotFound, ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

WORK, AUTHORITY, CONFIG = "work", "authority", "config"  # mcp/tool_authority.py classes

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + (
    "NotFound: unknown automation, result, template or lesson", "ValidationError", "ConflictError",
    "ServiceError: owner_principal_required (When and With are the owner's)",
)
_ID = {"type": "string", "minLength": 1}
_WB = "/api/workbenches/{workbench_id}"


def _named(kind: str, key: str, call: Call) -> Call:
    """The route's words for a missing object: ``Unknown <kind>: <the path id>``."""

    def run(service: Any, principal: Any, args: dict[str, Any]) -> Any:
        try:
            return call(service, principal, args)
        except NotFound:
            raise NotFound(kind, str(args.get(key))) from None

    return run


def _rest(args: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    return {key: value for key, value in args.items() if key not in keys}


def _new_results(service: Any, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
    rows = service.new_results(principal)
    return {"automations": rows, "new_count": sum(row["new_count"] for row in rows)}


def _forget(service: Any, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
    try:
        index = int(args.get("index"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise NotFound("lesson", str(args.get("index"))) from None
    service.forget_memory(principal, args.get("workbench_id"), index, str(args.get("at") or ""))
    return {"success": True}


def _event_start_view(watch: Mapping[str, Any]) -> dict[str, Any]:
    """An automation's event start (a watch, the watch fold of 2026-11-08) as the face's row."""
    connector = str(watch.get("connector_id") or "custom")
    adapter_status = "ready" if connector in ("gh", "jira") else "unavailable"
    enabled = watch.get("state") in {"active", "tested"}
    status = ("attention" if watch.get("last_error") else "unavailable" if adapter_status == "unavailable"
              else "active" if enabled else "paused")
    query = watch.get("query") if isinstance(watch.get("query"), dict) else {}
    return {
        "id": watch.get("id"), "name": watch.get("name") or "Event automation",
        "provider": "github" if connector == "gh" else connector, "event_kind": watch.get("event_pattern") or "",
        "enabled": enabled, "status": status, "adapter_status": adapter_status,
        "last_error": watch.get("last_error"), "last_good_at": watch.get("last_success_at"),
        "created_at": watch.get("created_at"), "repository": query.get("repository"),
    }


def _set_event_start(service: Any, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
    """On or off for one event start of an automation (Enabling sets a silent baseline)."""
    from holdspeak.services.watch_service import AUTOMATION_INTENT_PREFIX, _automation_event_pattern

    workbench_id, watch_id = str(args.get("workbench_id")), str(args.get("automation_id"))
    if not isinstance(args.get("enabled"), bool):
        raise ValidationError("enabled must be true or false")
    db = service._db
    watch = db.automations.get_watch(watch_id)
    if not watch or watch.get("intent") != AUTOMATION_INTENT_PREFIX + workbench_id:
        raise NotFound("automation event", watch_id)
    value = service.set_automation_event_enabled(principal, workbench_id=workbench_id, watch_id=watch_id,
                                                 enabled=args["enabled"])
    pattern = _automation_event_pattern(db.automations.list_rules(str(value.get("id") or "")))
    return {"automation": _event_start_view({**value, "event_pattern": pattern})}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        write: bool = False, properties: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (),
        status: int = 200, authority: str = WORK, service: str = "workbench_service") -> OperationDescriptor:
    """One verb; its tool requires the path's ids and ``required``."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result="the WorkbenchService answer, in the route's envelope",
        refusals=_REFUSALS, completion="synchronous; a write is one desk_changed frame (kind workbench)",
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service=service, method=method,
        call=call, http=http, http_status=status, handler=handler, tool_schema=tool,
        authority=authority,
        # A read is evidence and MCP only (thread_modes._MCP_ONLY): a thread
        # reads an automation through automation.get. When and With are never
        # a thread's (authority, config).
        thread=None if authority != WORK else "effect_proposal" if write else "evidence_read",
    )


_WHEN = {
    "kind": {"enum": ["schedule", "event", "manual"]},
    "every": {"type": "string", "enum": ["day", "weekday", "week", "hour"]},
    "time": {"type": "string", "description": "HH:MM, for a schedule."},
    "day": {"type": ["string", "integer"], "description": "The weekday, for a weekly schedule."},
    "event_id": {"type": "string", "description": "One of the events the hub can deliver, for an event."},
    "repository": {"type": "string", "description": "owner/repo, for a repository event."},
}

AUTOMATION_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("automation.set_when", "set_when", ("PUT", _WB + "/when"), "api_set_workbench_when",
        _named("automation", "workbench_id",
               lambda s, p, a: {"workbench": s.set_when(p, a.get("workbench_id"), _rest(a, "workbench_id"))}),
        "Set when an automation runs: one schedule, one event or manual. The other starts stop.",
        write=True, properties=_WHEN, required=("kind",), authority=AUTHORITY),
    _op("automation.set_engine", "set_engine", ("PUT", _WB + "/engine"), "api_set_workbench_engine",
        _named("automation", "workbench_id",
               lambda s, p, a: {"workbench": s.set_engine(p, a.get("workbench_id"), **_rest(a, "workbench_id"))}),
        "Set the engine of an automation's runs (With) and its spend limit per run.", write=True,
        properties={"profile_id": {"type": "string"}, "spend_limit_usd": {"type": ["number", "null"]}},
        authority=CONFIG),
    _op("automation.make_one", "make_one_automation", ("POST", _WB + "/make-one"), "api_make_one_automation",
        _named("workbench", "workbench_id",
               lambda s, p, a: {"workbench": s.make_one_automation(p, a.get("workbench_id"))}),
        "Make an old queue automation one automation: its agent's prompt becomes its Do text.", write=True),
    _op("automation.template.list", "list_templates", ("GET", "/api/workbench-templates"), "api_list_templates",
        lambda s, p, a: {"templates": s.list_templates(p)},
        "List the starters New automation offers, each with its schedule."),
    _op("automation.template.instantiate", "instantiate_template",
        ("POST", "/api/workbench-templates/{template_id}/instantiate"), "api_instantiate_template",
        _named("template", "template_id",
               lambda s, p, a: s.instantiate_template(p, a.get("template_id"), a.get("profile_id") or None)),
        "Make an automation from one starter (its schedule stays off).", write=True,
        properties={"profile_id": {"type": "string"}}, status=201),
    _op("automation.result.open", "open_result", ("POST", _WB + "/results/{artifact_id}/open"), "api_open_result",
        _named("result", "artifact_id",
               lambda s, p, a: {"result": s.open_result(p, a.get("workbench_id"), a.get("artifact_id"))}),
        "Open one result of an automation: a new result becomes read.", write=True),
    _op("automation.new.list", "new_results", ("GET", "/api/automations/new"), "api_new_results", _new_results,
        "List the automations that hold a new result, with their count."),
    _op("automation.lesson.list", "list_memory", ("GET", _WB + "/memory"), "api_list_memory",
        lambda s, p, a: {"entries": s.list_memory(p, a.get("workbench_id"))},
        "List the lessons an automation keeps between runs."),
    _op("automation.lesson.forget", "forget_memory", ("DELETE", _WB + "/memory/{index}"), "api_forget_memory",
        _forget, "Forget one lesson of an automation; at is its timestamp.", write=True,
        properties={"index": {"type": ["integer", "string"]}, "at": {"type": "string"}}),
    # 2026-11-09 (ops/programs-work): Today's Prepared block and an item's Restore.
    _op("automation.prepared.read", "prepared_for_today", ("GET", "/api/automations/prepared"),
        "api_prepared_for_today", lambda s, p, a: s.prepared_for_today(p),
        "Read what is prepared for today: the newest result of an automation that puts it in Today, and the "
        "automation Prepare now runs. Each is null when there is none."),
    _op("automation.item.restore", "restore_item", ("POST", _WB + "/items/{item_id}/restore"), "api_restore_item",
        _named("item", "item_id",
               lambda s, p, a: {"item": s.restore_item(p, a.get("workbench_id"), a.get("item_id"))}),
        "Restore one parked item of an automation (workbench.delete_item parks it).", write=True),
    _op("automation.event_start.set_enabled", "set_automation_event_enabled",
        ("PATCH", _WB + "/automations/{automation_id}"), "set_workbench_automation_enabled", _set_event_start,
        "Turn one event start of an automation on or off. Turning it on sets a silent baseline first.",
        write=True, properties={"enabled": {"type": "boolean"}}, required=("enabled",), service="watch_service"),
)

__all__ = ["AUTOMATION_OPERATIONS"]
