"""The calendar's source facts and the Snapshot confirm on the one declared contract
(2026-11-09, ops/connections).

Carved beside ``holdspeak/operations.py`` (which imports it into ``DESCRIPTORS``);
``services/calendar_service.CalendarService`` serves every row.

* ``calendar.sources`` reads the configured sources and the stored events
  (no network): evidence, with an MCP tool.
* ``calendar.snapshot.confirm`` writes an ICS file and adds the snapshot
  source to his settings: config, owner only, his press, HTTP only (the face's
  second step after its screenshot upload). The upload itself
  (``POST /api/calendar/snapshot``) stays hand-written: a produced route takes
  no file. It calls ``CalendarService.extract``.
* The UI feedback verbs (``services/ui_feedback.FeedbackService``) are owner
  only: each write is a file in his feedback folder. The switch's read has a
  tool; the save and the transcription are the Desk's presses, HTTP only.
"""
from __future__ import annotations

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

_ANY = "derived by the transport (HTTP auth middleware; MCP auth resolver); the edge decides who reaches it"
_OWNER = "derived by the transport (the HTTP auth middleware); owner only"
_NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}

CALENDAR_OPERATIONS: tuple[OperationDescriptor, ...] = (
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
        exposure=("http:POST /api/calendar/snapshot/confirm",), service="calendar_service", method="confirm",
        owner_only=True, owner_press=True, blocking_io=True,
        call=lambda s, p, a: s.confirm(p, a.get("anchor_date"), a.get("events", [])),
        http=("POST", "/api/calendar/snapshot/confirm"), handler="confirm_snapshot", authority="config",
    ),
)

__all__ = ["CALENDAR_OPERATIONS"]
