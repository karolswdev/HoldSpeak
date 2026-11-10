"""Calendar sources and both Snapshot steps share declared operations.

Extract keeps its multipart HTTP adapter and accepts base64 images on MCP.
Confirm writes the reviewed ICS source. Both steps are the owner's presses;
no agent or thread gets a new effect.
"""
from __future__ import annotations

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.calendar_snapshot_service import MAX_SCREENSHOTS

_ANY = "derived by the transport (HTTP auth middleware; MCP auth resolver); the edge decides who reaches it"
_OWNER = "derived by the transport (the HTTP auth middleware); owner only"
_NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}

def _extract(service, principal, args):
    import base64
    from holdspeak.services.calendar_service import CalendarRefused

    try:
        images = [(row["content_type"], base64.b64decode(row["data_base64"], validate=True))
                  for row in args.get("images", [])]
    except (KeyError, TypeError, ValueError) as exc:
        raise CalendarRefused("Each image needs its content type and base64 data") from exc
    return service.extract(principal, images)


CALENDAR_OPERATIONS: tuple[OperationDescriptor, ...] = (
    OperationDescriptor(
        name="calendar.snapshot.extract", version=1, description="Read calendar events from reviewed screenshots.",
        args_schema={"type": "object"}, principal=_OWNER, effect="write",
        result="{success, anchor_date, anchor_confidence, events, error, egress?}",
        refusals=_CONTRACT_REFUSALS + ("owner_required", "calendar_snapshot_refused"),
        completion="synchronous; review the extracted events before calendar.snapshot.confirm",
        exposure=("http:POST /api/calendar/snapshot", "mcp:calendar.snapshot.extract"),
        service="calendar_service", method="extract", owner_only=True, owner_press=True,
        blocking_io=True, authority="egress", call=_extract,
        web_call=lambda s, p, a: s.extract(p, a.get("images", [])),
        http=("POST", "/api/calendar/snapshot"), handler="extract_snapshot",
        tool_schema={"type": "object", "properties": {"images": {"type": "array", "minItems": 1,
            "maxItems": MAX_SCREENSHOTS, "items": {"type": "object", "properties": {
                "content_type": {"enum": ["image/png", "image/jpeg", "image/jpg", "image/webp"]},
                "data_base64": {"type": "string"}}, "required": ["content_type", "data_base64"],
                "additionalProperties": False}}}, "required": ["images"], "additionalProperties": False},
    ),
    OperationDescriptor(
        name="calendar.sources", version=1,
        description="See each calendar source: its type, read state, host, event count and last read; the "
                    "auto-record setting; this week's matched events; where a Snapshot upload goes. No network.",
        args_schema={"type": "object"}, principal=_ANY, effect="read",
        result="{sources: [{id, label, type, status, host, event_count, last_read_at, egress}], auto_record, "
               "auto_record_lead_minutes, matched_this_week, snapshot_egress}",
        refusals=_CONTRACT_REFUSALS, completion="synchronous; a read of the settings file and the event store",
        exposure=("http:GET /api/calendar/sources", "mcp:calendar.sources"), service="calendar_service",
        method="sources", blocking_io=True, call=lambda s, p, a: s.sources(p),
        http=("GET", "/api/calendar/sources"), handler="list_sources", tool_schema=_NO_ARGS, thread="evidence_read",
    ),
    OperationDescriptor(
        name="calendar.snapshot.confirm", version=1,
        description="Write the reviewed Snapshot events as a calendar file and add it as the snapshot source.",
        args_schema={"type": "object", "properties": {
            "anchor_date": {"type": "string", "description": "The week's Monday (YYYY-MM-DD) the events fall in."},
            "events": {"type": "array", "items": {"type": "object"}}}},
        principal=_OWNER, effect="write",
        result="{success, source_id, source_label, events_count, ics_path}",
        refusals=_CONTRACT_REFUSALS + ("owner_required", "calendar_snapshot_refused"),
        completion="synchronous; calendar.sources lists the snapshot source after the refresh",
        exposure=("http:POST /api/calendar/snapshot/confirm", "mcp:calendar.snapshot.confirm"), service="calendar_service", method="confirm",
        owner_only=True, owner_press=True, blocking_io=True,
        call=lambda s, p, a: s.confirm(p, a.get("anchor_date"), a.get("events", [])),
        http=("POST", "/api/calendar/snapshot/confirm"), handler="confirm_snapshot", authority="config",
        tool_schema={"type": "object", "properties": {
            "anchor_date": {"type": "string"}, "events": {"type": "array", "items": {"type": "object"}}},
            "required": ["anchor_date", "events"], "additionalProperties": False},
    ),
)

__all__ = ["CALENDAR_OPERATIONS"]
