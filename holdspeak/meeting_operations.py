"""The meeting archive's web verbs on the one declared contract (2026-11-08).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``program_operations.py`` is. Each row states one
``MeetingService`` verb once: its call, its HTTP method and path, and its MCP
tool schema. ``web/routes/meetings/declared.py`` produces the routes and
``mcp/families/declared.py`` the tools from these rows, both through
``OperationRegistry.invoke``.

As in the Programs rows, the arguments schema is any object: the service
validates, as it did behind the hand-written routes. The live-meeting verbs
(``meeting.bookmark``, ``meeting.update``) keep hand-written routes: their
answer is ``{"success": true}`` and they broadcast to the live session.
Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("NotFound: unknown meeting, conflict or action item", "ValidationError", "ConflictError")
_ID = {"type": "string", "minLength": 1}
_LIMIT = {"limit": {"type": "integer", "minimum": 1, "description": "Default 200."}}


def _flag(value: Any) -> bool:
    """A query flag (``?include_completed=true``) or a JSON boolean."""
    return value.strip().lower() in {"1", "true", "yes", "on"} if isinstance(value, str) else bool(value)


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        write: bool = False, properties: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (),
        announces: bool = False) -> OperationDescriptor:
    """One verb; its tool requires the path's ids and ``required``."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result="the MeetingService answer", refusals=_REFUSALS,
        completion="synchronous; a write is one desk_changed frame on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service="meeting_service", method=method,
        announces_changes=announces, call=call, http=http, handler=handler, tool_schema=tool,
        # A read is evidence (the thread table classes every work tool); it
        # stays MCP and HTTP only (thread_modes._MCP_ONLY): a thread reaches a
        # meeting through meeting.get / meeting.list, so no palette grows.
        thread="effect_proposal" if write else "evidence_read",
    )


def _mark_ready_read(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    result = service.mark_ready_read(principal, args.get("meeting_id"))
    if result["ready_at"] is not None:
        # The Dock reads this kind (web/src/desk/components/window/Dock.tsx).
        from holdspeak.runtime.composition import notify_desk_changed

        notify_desk_changed("meeting_ready_read", result["meeting_id"], "read")
    return result


def _rename(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    if "title" not in args:
        raise ValidationError("expected a title")
    return {"meeting": service.rename_meeting(principal, args.get("meeting_id"), args.get("title"))}


def _resolve(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    payload = {key: value for key, value in args.items() if key not in {"meeting_id", "conflict_id"}}
    return service.resolve_sync_conflict(principal, args.get("meeting_id"), args.get("conflict_id"), payload)


_M = "/api/meetings/{meeting_id}"
MEETING_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("meeting.ready_list", "list_ready", ("GET", "/api/meetings/ready"), "api_list_unread_ready_meetings",
        lambda s, p, a: s.list_ready(p), "List the meetings that became ready and are not opened yet."),
    _op("meeting.ready_read", "mark_ready_read", ("POST", _M + "/ready/read"), "api_mark_meeting_ready_read",
        _mark_ready_read, "Mark a ready meeting as opened.", write=True, announces=True),
    _op("meeting.facets", "facets", ("GET", "/api/meetings/facets"), "api_meeting_facets",
        lambda s, p, a: s.facets(p), "List the speakers and tags of the meeting archive (the filter values)."),
    _op("meeting.rename", "rename_meeting", ("PUT", _M), "api_rename_meeting", _rename,
        "Rename one archived meeting.", write=True, properties={"title": _ID}, required=("title",)),
    _op("meeting.restore", "restore_meeting", ("POST", _M + "/restore"), "api_restore_meeting",
        lambda s, p, a: s.restore_meeting(p, a.get("meeting_id")), "Restore a parked meeting with all its work.",
        write=True),
    _op("meeting.recover_capture", "recover_capture", ("POST", _M + "/capture/recover"),
        "api_recover_meeting_capture", lambda s, p, a: s.recover_capture(p, a.get("meeting_id")),
        "Keep the last saved checkpoint of a stopped capture as a partial meeting.", write=True),
    _op("meeting.sync_conflicts", "list_sync_conflicts", ("GET", _M + "/sync-conflicts"),
        "api_meeting_sync_conflicts", lambda s, p, a: s.list_sync_conflicts(p, a.get("meeting_id")),
        "List the open sync conflicts of one meeting (two versions of it)."),
    _op("meeting.resolve_sync_conflict", "resolve_sync_conflict", ("POST", _M + "/sync-conflicts/{conflict_id}/resolve"),
        "api_resolve_meeting_sync_conflict", _resolve,
        "Resolve one sync conflict: keep the current version or use the incoming one.", write=True,
        properties={"resolution": {"enum": ["keep_current", "use_incoming"]}}, required=("resolution",)),
    _op("meeting.intent_timeline", "get_intent_timeline", ("GET", _M + "/intent-timeline"),
        "api_get_meeting_intent_timeline",
        lambda s, p, a: s.get_intent_timeline(p, a.get("meeting_id"), int(a.get("limit", 200))),
        "Read the intent timeline of one meeting.", properties=_LIMIT),
    _op("meeting.artifacts", "list_artifacts", ("GET", _M + "/artifacts"), "api_get_meeting_artifacts",
        lambda s, p, a: s.list_artifacts(p, a.get("meeting_id"), int(a.get("limit", 200))),
        "List the plugin artifacts of one meeting.", properties=_LIMIT),
    _op("meeting.prepared", "prepared_results", ("GET", _M + "/prepared"), "api_get_meeting_prepared",
        lambda s, p, a: s.prepared_results(p, a.get("meeting_id")),
        "List the Results this meeting prepared and the ones it can prepare."),
    _op("speaker.list", "list_speakers", ("GET", "/api/speakers"), "api_list_speakers",
        lambda s, p, a: s.list_speakers(p), "List the saved speaker profiles with their meeting counts."),
    _op("action_item.list", "list_all_action_items", ("GET", "/api/all-action-items"), "api_list_all_action_items",
        lambda s, p, a: s.list_all_action_items(p, {"include_completed": _flag(a.get("include_completed")),
                                                    "owner": a.get("owner"), "meeting_id": a.get("meeting_id")}),
        "List the action items of every meeting. Open items only, unless include_completed.",
        properties={"include_completed": {"type": "boolean"}, "owner": {"type": "string"}, "meeting_id": _ID}),
    _op("action_item.update", "update_action_item", ("PATCH", "/api/all-action-items/{item_id}"),
        "api_update_global_action_item",
        lambda s, p, a: s.update_action_item(p, a.get("item_id"), {"status": a.get("status")}),
        "Set the status of one action item (live meeting first, then the archive).", write=True,
        properties={"status": {"enum": ["done", "pending", "dismissed"]}}, required=("status",)),
    _op("action_item.review", "review_action_item", ("PATCH", "/api/all-action-items/{item_id}/review"),
        "api_review_global_action_item",
        lambda s, p, a: s.review_action_item(p, a.get("item_id"), {"review_state": a.get("review_state")}),
        "Accept an action item, or set it back to pending.", write=True,
        properties={"review_state": {"enum": ["pending", "accepted"]}}, required=("review_state",)),
    _op("meeting.bookmark", "bookmark", ("POST", "/api/bookmark"), "api_bookmark",
        lambda s, p, a: s.bookmark(p, label=a.get("label") or ""),
        "Bookmark the current moment of the live meeting.", write=True, properties={"label": {"type": "string"}}),
    _op("meeting.update", "update_meeting", ("PATCH", "/api/meeting"), "api_update_meeting",
        lambda s, p, a: s.update_meeting(p, a.get("meeting_id") or "", title=a.get("title"), tags=a.get("tags")),
        "Change the title or tags of the live meeting (else of the meeting named by meeting_id).", write=True,
        properties={"meeting_id": _ID, "title": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}),
)

__all__ = ["MEETING_OPERATIONS"]
