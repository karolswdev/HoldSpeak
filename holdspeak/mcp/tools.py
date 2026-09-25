"""MCP tool schemas and transport-neutral HoldSpeak service dispatch."""
from __future__ import annotations

from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service
from holdspeak import operations

import asyncio
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from holdspeak.db import get_database, get_observer
from holdspeak.mcp.families import FAMILIES
from holdspeak.principals import Principal
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.desk_service import DeskService
from holdspeak.services.dictation_service import DictationService
from holdspeak.services.event_query_service import EventQueryService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.kernel_read_service import KernelReadService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.recipe_service import RecipeService
from holdspeak.services.scheduled_recording_service import ScheduledRecordingService
from holdspeak.services.workbench_service import WorkbenchService

PRIMITIVE_KINDS = ("notes", "decisions", "kbs", "directories", "workflows", "chains")
_KIND_ALIASES = {kind: kind[:-1] if kind.endswith("s") else kind for kind in PRIMITIVE_KINDS}
_KIND_ALIASES["kbs"] = "kb"
# PHILO-7-01: the one-letter strip made "directorie", so every desk.* zone call
# except desk.list asked PrimitiveService for ``create_directorie`` and failed.
_KIND_ALIASES["directories"] = "directory"


class ToolError(ValueError):
    """An expected tool failure which maps to an MCP ``isError`` result."""


TOOLS: list[dict[str, Any]] = [
    {
        "name": "desk.list",
        "description": "List HoldSpeak desk primitives of one kind. Find a note: kind=notes; each row has its id (read it with desk.get). List the zones: kind=directories; each row has member_ids, the objects filed in it. List the knowledge bases: kind=kbs. The desk schema advertises 18 primitive kinds; this tool operates on the 6 authorable kinds: notes, decisions, kbs, directories, workflows, and chains. The remaining 12 kinds (meeting, artifact, project, repository, recipe, coder, game, roadmap, story, workbench, layout, people) are managed through dedicated tools or are read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {"kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)}},
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.get",
        "description": "Get one HoldSpeak desk primitive by kind and id. Read a note: kind=notes and id from desk.list kind=notes. Read a zone and what is filed in it: kind=directories. The desk schema advertises 18 primitive kinds; this tool operates on the 6 authorable kinds: notes, decisions, kbs, directories, workflows, and chains. The remaining 12 kinds (meeting, artifact, project, repository, recipe, coder, game, roadmap, story, workbench, layout, people) are managed through dedicated tools or are read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string", "description": "The object's id, from desk.list with the same kind."},
            },
            "required": ["kind", "id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.create",
        "description": (
            "Create a desk primitive. Pass fields appropriate to its kind in data. "
            "Write a note: kind=notes, data title, body_markdown and tags. "
            "Make a zone: kind=directories, data name (and parent_id to put it in another zone). "
            "Make a knowledge base: kind=kbs, data name. "
            "Put a decision on my review list: kind=decisions, data title and status=proposed. "
            "Authorable kinds: notes, decisions, kbs, directories, workflows, chains."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "data": {"type": "object", "description": (
                    "Primitive fields. Each kind names its own optional id field (a new id is made when it is "
                    "absent); a field named id is refused. notes: note_id, title, body_markdown, tags. "
                    "directories: directory_id, name, parent_id (a zone id from desk.list kind=directories). "
                    "kbs: kb_id, name, member_ids (kind:id references, for example note:<id>). "
                    "decisions: title, status (proposed puts it on the review list), and the other decision fields."
                )},
            },
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.update",
        "description": (
            "Update a desk primitive. Only supplied fields in data change. "
            "Rename a zone: kind=directories, data name (the name only). "
            "Move a zone: kind=directories, data parent_id (null moves it to the desk root). "
            "Edit a note: kind=notes, data title, body_markdown or tags. "
            "Authorable kinds: notes, decisions, kbs, directories, workflows, chains."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string", "description": "The object's id, from desk.list with the same kind."},
                "data": {"type": "object", "description": "The fields to change, as for desk.create of the same kind."},
            },
            "required": ["kind", "id", "data"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.delete",
        "description": (
            "Delete one desk primitive by kind and id. Deleting a zone puts what is filed in it back on the desk. "
            "Authorable kinds: notes, decisions, kbs, directories, workflows, chains."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string", "description": "The object's id, from desk.list with the same kind."},
            },
            "required": ["kind", "id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.verb",
        "description": "Dispatch an allowlisted server-side desk verb. Local presentation verbs return ui_only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "verb_id": {"type": "string", "description": (
                    "The desk verb to run. Server verbs, one of: desk.create, desk.update, desk.delete "
                    "(arguments as for the tool with the same name), workbench.add_item, workbench.run."
                )},
                "arguments": {"type": "object", "description": "Arguments for the server-side verb."},
            },
            "required": ["verb_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "workbench.run",
        "description": "Trigger a HoldSpeak Workbench run.",
        "inputSchema": {
            "type": "object",
            "properties": {"workbench_id": {"type": "string"}},
            "required": ["workbench_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "workbench.add_item",
        "description": "Add a work item to a HoldSpeak Workbench.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workbench_id": {"type": "string"},
                "title": {"type": "string"},
                "data": {"type": "object", "description": "Optional item fields."},
            },
            "required": ["workbench_id", "title"],
            "additionalProperties": False,
        },
    },
    {
        "name": "meeting.list",
        "description": "List or search archived meetings with optional archive filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}, "from_date": {"type": "string"},
                "to_date": {"type": "string"}, "speaker": {"type": "string"},
                "tag": {"type": "string"}, "has_open_actions": {"type": "boolean"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                "cursor": {"type": ["string", "integer"]},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "meeting.get",
        "description": "Get the complete stored detail for one meeting.",
        "inputSchema": {
            "type": "object",
            "properties": {"meeting_id": {"type": "string"}, "include": {"type": "string"}},
            "required": ["meeting_id"],
            "additionalProperties": False,
        },
    },
 ]


def _workbench_tool(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"name": name, "description": description, "inputSchema": {
        "type": "object", "properties": properties, "required": required or [], "additionalProperties": False,
    }}


_RECIPE_RUN_OPTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "variables": {"type": "object"},
        "max_tokens": {"type": "integer", "minimum": 1},
        "temperature": {"type": "number", "minimum": 0, "maximum": 2},
        "source_ref": {"type": "string"},
        "source_type": {}, "grounding_refs": {}, "grounding_revisions": {},
        "source_revision": {}, "deadline_at": {}, "initiator": {},
    },
    "additionalProperties": False,
}
_RECIPE_CHAT_OPTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "history": {"type": "array"}, "grounding": {"type": "object"},
        "egress_context": {},
    },
    "additionalProperties": False,
}
_WORKBENCH_FIELDS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "recipe_id": {"type": ["string", "null"]},
        "schedule": {"type": ["string", "null"]},
        "schedule_enabled": {"type": "boolean"},
        "schedule_revision": {"type": "integer", "minimum": 1},
        "item_order": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


def _workbench_fields(value: Any) -> dict[str, Any]:
    fields = _data(value)
    unknown = set(fields) - set(_WORKBENCH_FIELDS_SCHEMA["properties"])
    if unknown:
        raise ToolError(f"Unsupported Workbench fields: {', '.join(sorted(unknown))}")
    return fields


TOOLS.extend([
    _workbench_tool("workbench.list", "List Workbenches.", {}),
    _workbench_tool("workbench.get", "Get a Workbench.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("workbench.create", "Create a Workbench with closed optional configuration fields.", {"name": {"type": "string", "description": "Non-empty Workbench name."}, "fields": _WORKBENCH_FIELDS_SCHEMA}, ["name"]),
    _workbench_tool("workbench.update", "Update supplied closed Workbench configuration fields.", {"workbench_id": {"type": "string"}, "fields": _WORKBENCH_FIELDS_SCHEMA}, ["workbench_id", "fields"]),
    _workbench_tool("workbench.delete", "Delete a Workbench.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("workbench.update_item", "Update supplied fields of a Workbench item.", {"workbench_id": {"type": "string"}, "item_id": {"type": "string"}, "fields": {"type": "object", "description": "Item patch fields."}}, ["workbench_id", "item_id", "fields"]),
    _workbench_tool("workbench.delete_item", "Delete a Workbench item.", {"workbench_id": {"type": "string"}, "item_id": {"type": "string"}}, ["workbench_id", "item_id"]),
    _workbench_tool("workbench.list_runs", "List Workbench runs.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("recipe.list", "List Agent recipes.", {}),
    _workbench_tool("recipe.get", "Get an Agent recipe.", {"recipe_id": {"type": "string"}}, ["recipe_id"]),
    _workbench_tool("recipe.run", "Run an Agent recipe and return its lifecycle-backed result and minted artifact reference.", {"recipe_id": {"type": "string"}, "input": {"type": "string"}, "options": _RECIPE_RUN_OPTIONS_SCHEMA}, ["recipe_id"]),
    _workbench_tool("recipe.chat", "Ask an Agent recipe a question.", {"recipe_id": {"type": "string"}, "question": {"type": "string"}, "options": _RECIPE_CHAT_OPTIONS_SCHEMA}, ["recipe_id", "question"]),
    _workbench_tool("zone.file", "File a primitive in a Zone. File a note into a zone: directory_id from desk.list kind=directories and primitive_id note:<id>. A primitive is in one zone only: filing it again moves it.", {"directory_id": {"type": "string", "description": "The zone id, from desk.list kind=directories."}, "primitive_id": {"type": "string", "description": "The object to file, as kind:id: for a note, note:<id> with the id from desk.list kind=notes."}}, ["directory_id", "primitive_id"]),
    _workbench_tool("zone.unfile", "Remove a primitive from a Zone. Take a note out of a zone: the zone id and note:<id>.", {"directory_id": {"type": "string", "description": "The zone id, from desk.list kind=directories."}, "primitive_id": {"type": "string", "description": "The filed object, as kind:id: for a note, note:<id> with the id from desk.list kind=notes."}}, ["directory_id", "primitive_id"]),
    _workbench_tool("zone.list_members", "List Zone members. List the notes in a zone: each member names its primitive_id (note:<id>).", {"directory_id": {"type": "string", "description": "The zone id, from desk.list kind=directories."}}, ["directory_id"]),
    _workbench_tool("kb.add_member", "Add a resource reference to a knowledge base. Add a note to a knowledge base: kb_id and ref note:<id>.", {"kb_id": {"type": "string", "description": "The knowledge base id, from desk.list kind=kbs."}, "ref": {"type": "string", "description": "A kind:id reference: for a note, note:<id> with the id from desk.list kind=notes."}}, ["kb_id", "ref"]),
    _workbench_tool("kb.remove_member", "Remove a resource reference from a knowledge base.", {"kb_id": {"type": "string", "description": "The knowledge base id, from desk.list kind=kbs."}, "ref": {"type": "string", "description": "The reference to remove, as kind:id: for a note, note:<id> with the id from desk.list kind=notes."}}, ["kb_id", "ref"]),
    _workbench_tool("kb.list_members", "List knowledge-base members.", {"kb_id": {"type": "string", "description": "The knowledge base id, from desk.list kind=kbs."}}, ["kb_id"]),
])


def _mcp_tool(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
            "additionalProperties": False,
        },
    }


# Kept as a distinct extension block: the workbench/recipe family above is
# owned by HS-123-09, while this is the operational meeting and desk family.
TOOLS.extend([
    _mcp_tool(
        "meeting.start_capture",
        "Start a meeting capture through the configured HoldSpeak capture controller.",
        {"config": {"type": "object", "description": "Optional capture configuration, including devices."}},
    ),
    _mcp_tool(
        "meeting.stop_capture",
        "Stop the active meeting capture, optionally identifying the meeting to stop.",
        {"meeting_id": {"type": "string", "description": "Optional meeting identifier."}},
    ),
    _mcp_tool(
        "meeting.delete",
        "Delete a stored meeting when it should no longer be retained.",
        {"meeting_id": {"type": "string", "description": "Meeting identifier to delete."}},
        ["meeting_id"],
    ),
    _mcp_tool(
        "meeting.export",
        "Export a stored meeting as Markdown or JSON for sharing or archival.",
        {
            "meeting_id": {"type": "string", "description": "Meeting identifier to export."},
            "format": {"type": "string", "enum": ["markdown", "json"], "description": "Export format."},
        },
        ["meeting_id", "format"],
    ),
    # PHILO-5-02: the MCP import intake (meeting.import). The hub opens the
    # file itself; the stdio proxy is loopback, so client and hub share the
    # machine. Completion is read through meeting.get.
    _mcp_tool(
        "meeting.import",
        "Owner only. Import one recording or transcript file into a new meeting. The hub reads the file at path, keeps its own copy and transcribes it in the background; read meeting.get until transcription finishes.",
        {
            "path": {"type": "string", "description": "Absolute path to an audio or transcript file the hub process can read."},
            "title": {"type": "string", "description": "Optional title; defaults to the file name."},
            "occurred_at": {"type": "string", "description": "Optional ISO 8601 date and time the meeting happened; defaults to now."},
        },
        ["path"],
    ),
    _mcp_tool(
        "meeting.run_intelligence",
        "Enqueue a fresh intelligence job using the disclosed summary route selection hash. Refuses when the hash is absent, stale, or the meeting has no transcript.",
        {
            "meeting_id": {"type": "string", "description": "Meeting identifier."},
            "expected_selection_hash": {"type": "string", "description": "Selection hash from the meeting planned_route read."},
        },
        ["meeting_id", "expected_selection_hash"],
    ),
    _mcp_tool(
        "meeting.proposals",
        "List follow-through proposals extracted from a meeting's intelligence run. Each proposal is a decision or action item waiting for Confirm or Drop.",
        {
            "meeting_id": {"type": "string", "description": "Meeting identifier."},
            "state": {"type": "string", "enum": ["proposed", "confirmed", "dismissed"], "description": "Optional state filter."},
        },
        ["meeting_id"],
    ),
    _mcp_tool(
        "proposal.confirm",
        "Confirm a follow-through proposal, writing the decision record or action item through the kernel. Optionally amend text, owner, or due before confirming.",
        {
            "proposal_id": {"type": "string", "description": "Proposal identifier."},
            "text": {"type": "string", "description": "Amended text (optional; original kept when omitted)."},
            "owner": {"type": "string", "description": "Accountable owner (optional)."},
            "due": {"type": "string", "description": "ISO-8601 due date (optional)."},
        },
        ["proposal_id"],
    ),
    _mcp_tool(
        "proposal.dismiss",
        "Dismiss a follow-through proposal without creating any record.",
        {"proposal_id": {"type": "string", "description": "Proposal identifier."}},
        ["proposal_id"],
    ),
    # HS-173-04: Reviewer nudge tools
    _mcp_tool(
        "steward.nudges",
        "List reviewer nudge proposals for a project, optionally filtered by state (proposed, sent, dismissed).",
        {
            "project_id": {"type": "string", "description": "Project identifier."},
            "state": {"type": "string", "enum": ["proposed", "sent", "dismissed"], "description": "Optional state filter."},
        },
        ["project_id"],
    ),
    _mcp_tool(
        "nudge.send",
        "Send a reviewer nudge: post the comment to GitHub via gh pr comment. The text is the exact comment posted.",
        {
            "step_id": {"type": "string", "description": "Nudge step identifier."},
            "text": {"type": "string", "description": "The comment text to post (required, non-empty)."},
        },
        ["step_id", "text"],
    ),
    _mcp_tool(
        "nudge.dismiss",
        "Dismiss a proposed reviewer nudge without posting. A 7-day cooldown starts.",
        {"step_id": {"type": "string", "description": "Nudge step identifier."}},
        ["step_id"],
    ),
    _mcp_tool(
        "dictation.list",
        "Read the retained dictation journal, optionally paged and filtered by source.",
        {
            "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum entries to return."},
            "cursor": {"type": "integer", "description": "Return entries older than this journal entry id."},
            "source": {"type": "string", "enum": ["dictation", "dry_run", "browser", "hotkey"], "description": "Optional dictation source filter."},
        },
    ),
    _mcp_tool(
        "dictation.get",
        "Get one retained dictation journal entry by its numeric id.",
        {"entry_id": {"type": "integer", "description": "Numeric dictation journal entry id."}},
        ["entry_id"],
    ),
    _mcp_tool("desk.snapshot", "Read one coherent snapshot of the durable HoldSpeak desk.", {}),
    _mcp_tool("desk.needs_you", "Aggregate needs-you items across all active project rooms. Returns {count, projects, items, next, coverage, complete} -- coverage names every expected source that was not observed.", {}),
    _mcp_tool("settings.hub", "Read the settings hub row facts: module state tokens for the settings truth table.", {}),
    _mcp_tool(
        "decision_record.list", "List durable decision records, newest first.",
        {"limit": {"type": "integer", "minimum": 1, "maximum": 500}, "offset": {"type": "integer", "minimum": 0}},
    ),
    _mcp_tool(
        "decision_record.get", "Get one decision record with sources, work, and revisions.",
        {"record_id": {"type": "string"}}, ["record_id"],
    ),
    _mcp_tool(
        "decision_record.create_from_meeting", "Mint a durable record from a meeting decision.",
        {"decision_id": {"type": "string"}}, ["decision_id"],
    ),
    _mcp_tool(
        "decision_record.create_from_desk", "Mint a durable record from an authored desk decision.",
        {"decision_id": {"type": "string"}}, ["decision_id"],
    ),
    _mcp_tool(
        "decision_record.search", "Search decision records and their affected-work labels.",
        {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}}, ["query"],
    ),
    _mcp_tool(
        "decision.supersede",
        "Supersede a decision when a successor decision replaces it.",
        {"decision_id": {"type": "string", "description": "Decision to supersede."}},
        ["decision_id"],
    ),
    # PHILO-7-02: the ONE new public tool -- the receipt readback (read-only).
    _mcp_tool(
        "kernel.receipt",
        "Read the receipt of a filing or decision write: operation_id from that write's result. "
        "Shows the outcome, the actor and, for an agent's write, the delegation that approved it.",
        {"operation_id": {"type": "string", "description": "The operation_id a filing or decision write returned."}},
        ["operation_id"],
    ),
    _mcp_tool(
        "pipeline.events",
        "Query observed pipeline events with optional filters.",
        {
            "service": {"type": "string"},
            "method": {"type": "string"},
            "principal_kind": {"type": "string"},
            "since": {"type": "number", "description": "Inclusive epoch timestamp."},
            "until": {"type": "number", "description": "Inclusive epoch timestamp."},
            "correlation_id": {"type": "string"},
            "errors_only": {"type": "boolean", "default": False},
            "limit": {"type": "integer", "default": 50},
        },
    ),
    _mcp_tool(
        "follow_through.board",
        "Read the Follow-Through board, optionally filtered by project, owner, or lane.",
        {
            "project_id": {"type": "string", "description": "Optional project identifier."},
            "owner": {"type": "string", "description": "Optional accountable owner."},
            "state": {"type": "string", "enum": ["now", "waiting", "unassigned", "overdue"], "description": "Optional board lane."},
        },
    ),
    _mcp_tool(
        "follow_through.complete",
        "Apply a completion verb to a Follow-Through action card.",
        {
            "card_id": {"type": "string", "description": "Action card identifier."},
            "verb": {"type": "string", "enum": ["done", "dismiss", "snooze", "delegate", "reopen", "due"], "description": "Write-through board verb (`due` sets payload.due_at, HS-200-13)."},
            "payload": {"type": "object", "description": "Verb data: until for snooze, to for delegate."},
        },
        ["card_id", "verb"],
    ),
    _mcp_tool(
        "follow_through.commit_decision",
        "Create an accountable commitment from an accepted decision.",
        {
            "decision_id": {"type": "string", "description": "Accepted decision identifier."},
            "owner": {"type": "string", "description": "Optional accountable owner."},
            "due_at": {"type": "string", "description": "Optional ISO-8601 due date."},
        },
        ["decision_id"],
    ),
    _mcp_tool(
        "monday_brief.get",
        "Read the latest persisted Monday Brief; set generate to true when no brief exists and one should be composed.",
        {"generate": {"type": "boolean", "default": False, "description": "Generate the current brief when no persisted brief exists."}},
    ),
    _mcp_tool(
        "monday_brief.generate",
        "Generate the current Monday Brief from durable sources. Repeated calls return the day's existing brief.",
        {},
    ),
    # PHILO-5-02: the brief triage shelf (brief.shelf.write / brief.shelf.read).
    _mcp_tool(
        "monday_brief.shelf",
        "Set one brief item's triage state: acknowledged or deferred. Null returns the item to untouched.",
        {
            "item_id": {"type": "string", "description": "A brief item id from monday_brief.get."},
            # PHILO-7-01 shelf-enum alignment: the brief service is the one refuser of
            # an unknown state on both transports ("Unknown shelf state: x"), so
            # this schema keeps the type and names the states in words.
            "state": {"type": ["string", "null"], "description": "acknowledged, deferred, or null to clear. Another value is refused by the brief service."},
        },
        ["item_id", "state"],
    ),
    _mcp_tool(
        "monday_brief.shelf_read",
        "Read the triage states of the latest brief's items, keyed by item id.",
        {},
    ),
    _mcp_tool(
        "scheduled_recording.list",
        "List all scheduled recordings with their current state, cron, and next-fire time.",
        {},
    ),
    _mcp_tool(
        "scheduled_recording.create",
        "Create a scheduled recording. Pass calendar_event_id to arm a calendar event (title/times/duration computed server-side, one-shot, enabled, fires 60 s before start). Without it, pass cron_expr + fields for a manual schedule.",
        {
            "title": {"type": "string", "description": "Human-readable schedule name (ignored when calendar_event_id is set)."},
            "cron_expr": {"type": "string", "description": "5-field cron expression (required without calendar_event_id)."},
            "tz": {"type": "string", "description": "IANA timezone name (default UTC; auto-detected for event-linked)."},
            "one_shot": {"type": "boolean", "description": "Disable after first fire (default false; always true for event-linked)."},
            "duration_minutes": {"type": "integer", "minimum": 1, "description": "Auto-stop minutes (default 60; computed from event for event-linked)."},
            "enabled": {"type": "boolean", "description": "Start scheduling immediately (default false; always true for event-linked)."},
            "calendar_event_id": {"type": "string", "description": "Calendar event projection id (ce_...) to arm. Server computes all fields from the event."},
        },
        [],
    ),
    _mcp_tool(
        "scheduled_recording.update",
        "Update a scheduled recording. Only supplied fields change. Re-validates cron and duration if provided.",
        {
            "schedule_id": {"type": "string", "description": "Schedule identifier."},
            "title": {"type": "string"},
            "cron_expr": {"type": "string", "description": "5-field cron expression."},
            "tz": {"type": "string"},
            "one_shot": {"type": "boolean"},
            "duration_minutes": {"type": "integer", "minimum": 1},
            "enabled": {"type": "boolean"},
        },
        ["schedule_id"],
    ),
    _mcp_tool(
        "scheduled_recording.delete",
        "Delete a scheduled recording. Refuses if the schedule is armed or recording.",
        {"schedule_id": {"type": "string", "description": "Schedule identifier."}},
        ["schedule_id"],
    ),
    _mcp_tool(
        "scheduled_recording.cancel_armed",
        "Cancel an armed (counting-down) scheduled recording before it fires.",
        {"schedule_id": {"type": "string", "description": "Schedule identifier."}},
        ["schedule_id"],
    ),
])

# Aggregate tools from per-family modules.
for _family in FAMILIES:
    TOOLS.extend(_family.TOOLS)

# The UI owns local surface state. These IDs deliberately never mutate the
# database when sent by an external MCP client.
_UI_ONLY_VERBS = {
    "desk.open", "object.open", "object.info", "object.edit", "object.rename",
    "object.ask", "object.ask-project", "desk.toggle-view", "desk.overview",
    "desk.arrange", "desk.reset-layout", "desk.reset-to-seed", "system.search",
    "system.sheet", "window.close", "window.minimize", "window.cycle",
    "window.cycle-reverse", "window.snap-left", "window.snap-right", "window.maximize",
}


def _kind(kind: Any) -> str:
    raw = str(kind or "")
    if raw not in _KIND_ALIASES:
        raise ToolError(f"Unsupported primitive kind: {raw}")
    return _KIND_ALIASES[raw]


def _data(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ToolError("data must be an object")
    return dict(value)


def _tool_schema(name: str) -> dict[str, Any] | None:
    for tool in TOOLS:
        if tool["name"] == name:
            return tool["inputSchema"]
    # Families are the dispatch authority.  The fallback keeps an in-process
    # family extension closed even before a caller refreshes the public list.
    for family in FAMILIES:
        for tool in family.TOOLS:
            if tool["name"] == name:
                return tool["inputSchema"]
    return None


def _validate_tool_arguments(name: str, arguments: dict[str, Any]) -> None:
    schema = _tool_schema(name)
    if schema is None:
        raise ToolError(f"Unknown tool: {name}")
    try:
        Draft202012Validator(schema).validate(arguments)
    except JsonSchemaValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path)
        detail = f"{location}: {exc.message}" if location else exc.message
        raise ToolError(f"Invalid arguments for {name}: {detail}") from exc


def _require_owner_before_schema(name: str, principal: Principal | None) -> None:
    """Preserve owner-before-body semantics for the twelve owner MCP twins.

    The shared validator closes every public schema, but these endpoints must
    return their owner denial without inspecting even a malformed body. Their
    service guards are static, so this check neither composes a service nor
    discovers a database before authorization.
    """
    if name.startswith("model_library."):
        ModelLibraryApplicationService.require_owner(principal)
    elif name.startswith("inference_assignment."):
        InferenceAssignmentService._require_owner(principal)


# PHILO-5-01 / PHILO-7-01 / PHILO-7-02: for decisions, notes, zones
# (directories) and knowledge bases, each (kind, verb) is ONE declared operation
# (``operations.DESK_OPERATIONS``), bound to the hub's live PrimitiveService and
# reached through the registry's ``invoke``. The generic getattr path below
# serves only the kinds with no row: workflows and chains (their owning slice).


def _desk_operation(kind: str, verb: str) -> str | None:
    return operations.DESK_OPERATIONS.get((kind, verb))


def _receipted(value: Any, kernel: dict[str, Any] | None) -> Any:
    """PHILO-7-02: an ADMITTED write's result carries ``operation_id`` and its receipt."""
    if kernel and isinstance(value, dict):
        return {**value, **kernel}
    return value


def _invoke(ops: Callable[[], operations.OperationRegistry], principal: Principal, name: str, args: dict[str, Any]) -> tuple[Any, dict[str, Any] | None]:
    return ops().invoke_receipted(principal, name, args)


def _primitive_list(ops: Callable[[], operations.OperationRegistry], service: PrimitiveService, principal: Principal, kind: str) -> Any:
    if (operation := _desk_operation(kind, "list")) is not None:
        return ops().invoke(principal, operation, {})
    return getattr(service, f"list_{kind}s")(principal)


def _primitive_get(ops: Callable[[], operations.OperationRegistry], service: PrimitiveService, principal: Principal, kind: str, item_id: str) -> Any:
    if (operation := _desk_operation(kind, "get")) is not None:
        return ops().invoke(principal, operation, {operations.DESK_ID_ARGUMENT[kind]: item_id})
    return getattr(service, f"get_{kind}")(principal, item_id)


def _primitive_create(ops: Callable[[], operations.OperationRegistry], service: PrimitiveService, principal: Principal, kind: str, data: dict[str, Any]) -> Any:
    if (operation := _desk_operation(kind, "create")) is not None:
        return _receipted(*_invoke(ops, principal, operation, data))
    return getattr(service, f"create_{kind}")(principal, **data)


def _primitive_update(ops: Callable[[], operations.OperationRegistry], service: PrimitiveService, principal: Principal, kind: str, item_id: str, data: dict[str, Any]) -> Any:
    if (operation := _desk_operation(kind, "update")) is not None:
        return _receipted(*_invoke(ops, principal, operation, operations.update_args(
            data, item_id, operation=operation, id_field=operations.DESK_ID_ARGUMENT[kind])))
    return getattr(service, f"update_{kind}")(principal, item_id, **data)


def _primitive_delete(ops: Callable[[], operations.OperationRegistry], service: PrimitiveService, principal: Principal, kind: str, item_id: str) -> Any:
    kernel = None
    if (operation := _desk_operation(kind, "delete")) is not None:
        deleted, kernel = _invoke(ops, principal, operation, {operations.DESK_ID_ARGUMENT[kind]: item_id})
    else:
        deleted = getattr(service, f"delete_{kind}")(principal, item_id)
    return _receipted({"deleted": deleted, "id": item_id}, kernel)


def _card_dict(card: Any) -> dict[str, Any]:
    """Serialize a follow-through card, including its provenance, for MCP."""
    return asdict(card)


def _compose_brief_overlay_mcp(result: dict[str, Any], db: Any, principal: Principal) -> dict[str, Any]:
    """HS-150-03: person_sections at the MCP adapter, gated by People access."""
    from holdspeak.mcp.families.people import access_mode, build_people_service, _mcp_readable
    from holdspeak.services.follow_through_service import FollowThroughService as _FT
    from holdspeak.services.person_overlay import compose_person_overlay

    # Gate: absent when People access is off.
    try:
        mode = access_mode()
    except Exception:
        mode = "off"
    if mode == "off":
        return result

    people_svc = build_people_service()
    follow_through = _FT(db)
    brief_window = (result.get("period_start", ""), result.get("period_end", ""))

    overlay = compose_person_overlay(brief_window, people_svc, follow_through, db, principal)

    if overlay.get("state") == "ready":
        # F6: filter sections to shared_intent-only via _mcp_readable pattern.
        # Person overlay sections are manager-computed summaries (counts + dates),
        # not encrypted records, so they pass through.  The underlying encrypted
        # data was already filtered by the people_service layer.
        result["person_sections"] = overlay.get("sections", [])
    elif overlay.get("state") == "unavailable":
        result["person_sections_state"] = "unavailable"

    return result


def _run(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise ToolError("async MCP tools cannot execute inside an active event loop")


def _require_live_capture(tool: str, meetings: Any) -> None:
    """Refuse a live-capture verb honestly when no capture controller exists.

    HS-200-45 R6. Before this, the bare ``MeetingService`` MCP composed had no
    lifecycle callbacks, so every call reached
    ``MeetingService.start_capture``'s ``ValidationError("Meeting start control
    not supported")`` -- an error whose wire ``code`` is ``validation_error``,
    i.e. "your input was wrong". The truth is the opposite: the input was fine
    and there is no capture controller in this process. Now that dispatch reads
    the hub's composition root, the hub path has the callbacks and this refusal
    only fires where it is true.
    """
    if getattr(meetings, "_on_start", None) is not None:
        return
    raise ToolError(
        f"{tool} needs the hub's live capture controller, which only "
        "`holdspeak web` owns: the microphone, the pipeline and the lifecycle "
        "callbacks live in that process. Start the hub (the stdio sidecar then "
        "forwards this call to it) and retry; there is nothing to configure "
        "here."
    )


def _meeting_import(registry: operations.OperationRegistry, meetings: Any, principal: Principal, args: dict[str, Any]) -> dict[str, Any]:
    """The MCP import intake (PHILO-5-02): custody first, then ``meeting.import``.

    The hub opens the caller's file and copies it into its own temporary file;
    the import worker consumes (and deletes) that copy, never the caller's
    file. The configuration and the transcriber are the same ones the HTTP
    upload route passes (``web/routes/meeting_import.py``), read at call time.
    """
    import os
    import shutil
    import tempfile
    from pathlib import Path

    from holdspeak.config import Config
    from holdspeak.services.errors import ValidationError
    from holdspeak.web.routes import meeting_import as import_route

    # r2 (Astra's check on built, finding 1): the owner boundary comes FIRST.
    # A non-owner principal (a remote DESK credential, any agent or node) is
    # refused with owner_required before the path is looked at, opened or copied.
    registry.authorize(principal, "meeting.import")
    path = Path(str(args.get("path") or ""))
    if not path.is_absolute():
        raise ValidationError(
            f"meeting.import needs an absolute path; got {str(path)!r}", code="path_not_absolute"
        )
    if not path.is_file() or not os.access(path, os.R_OK):
        raise ValidationError(
            f"The hub cannot read a file at {path}", code="path_not_readable"
        )
    try:
        meetings.validate_import(principal, path.name)
    except ValidationError as exc:
        raise ValidationError(exc.detail, code="unsupported_type") from exc
    with tempfile.NamedTemporaryFile(suffix=path.suffix.lower() or ".wav", delete=False) as held, path.open("rb") as source:
        shutil.copyfileobj(source, held)
    held_path = Path(held.name)
    if held_path.stat().st_size == 0:
        held_path.unlink(missing_ok=True)
        raise ValidationError(f"The file at {path} is empty", code="file_empty")
    arguments: dict[str, Any] = {"filename": path.name}
    for key in ("title", "occurred_at"):
        if args.get(key) is not None:
            arguments[key] = args[key]
    try:
        result = registry.invoke(principal, "meeting.import", arguments, held={
            "tmp_path": held_path,
            "config": Config.load(),
            "transcriber_factory": import_route._transcriber_factory,
        })
    except Exception:
        held_path.unlink(missing_ok=True)
        raise
    return {"meeting_id": result["meeting_id"], "transcription_status": result["status"]}


def dispatch(name: str, arguments: dict[str, Any] | None, principal: Principal) -> Any:
    """Call one day-one MCP tool and return JSON-serializable data."""
    args = arguments or {}
    if not isinstance(args, dict):
        raise ToolError("arguments must be an object")
    if _tool_schema(name) is None:
        raise ToolError(f"Unknown tool: {name}")
    retired_family_fields = {
        "ask.run": {"inference_target_id"},
        "sequence.run": {"inference_target_id"},
        "workflow.run": {"inference_target_id"},
    }
    if retired := (retired_family_fields.get(name, set()) & set(args)):
        raise ToolError(f"Invalid arguments for {name}: retired field(s): {', '.join(sorted(retired))}")
    _require_owner_before_schema(name, principal)

    # Families preserve their established transport-specific validation and
    # refusal codes. S4's retired selector families reject those names before
    # composing a service; the owner twins above already deny before body read.
    # Main-catalogue tools have no family dispatcher, so their schemas are the
    # dispatch-time closure fence.
    for family in FAMILIES:
        if any(tool["name"] == name for tool in family.TOOLS):
            return family.dispatch(name, args, principal)

    _validate_tool_arguments(name, args)
    db = db_or(get_database)
    obs = observer_or(get_observer)
    # HS-200-45 R1: the FIVE services the hub composes with wiring a bare
    # constructor cannot reproduce come from the one composition root.
    # ``primitives``/``workbenches`` carry ``on_changed`` -> the /ws bus (R4),
    # ``meetings`` carries ``bind_lifecycle`` (so meeting.start_capture can
    # actually start a capture, R6), ``follow_through`` the hub's People
    # projection, ``dictation`` the hub's journal repository. The rest are
    # plain (db, observer) services the hub's own routes also build per
    # request, so a fresh instance over the same Database is identical.
    primitives = runtime_service("primitive_service", lambda: PrimitiveService(db, observer=obs))
    workbenches = runtime_service("workbench_service", lambda: WorkbenchService(db, observer=obs))
    meetings = runtime_service("meeting_service", lambda: MeetingService(db, observer=obs))
    dictation = runtime_service("dictation_service", lambda: DictationService(db, observer=obs))
    follow_through = runtime_service("follow_through_service", lambda: FollowThroughService(db, observer=obs))
    recipes = RecipeService(db, observer=obs)
    events = EventQueryService(db)
    desk = DeskService(db, observer=obs)
    records = DecisionRecordService(db, observer=obs)
    # PHILO-5-01/02: the hub's bound contract (the object its HTTP routes
    # reach). In the hub no builder below runs: meeting.* , the summary run,
    # the brief (with the hub's producer clock, gap A) and the summary's
    # runtime_queue notify (gap B) all come from the hub's one instances. In a
    # bare composition it binds over the same services this dispatcher built
    # before. Resolved only when a contract operation is called.
    def ops() -> operations.OperationRegistry:
        return operations.for_runtime(
            lambda: primitives,
            meeting_service=lambda: meetings,
            meeting_intel_service=lambda: runtime_service(
                "meeting_intel_service", lambda: MeetingIntelService(db, observer=obs)
            ),
            monday_brief_service=lambda: runtime_service(
                "monday_brief_service", lambda: MondayBriefService(db, observer=obs)
            ),
            kernel_read_service=lambda: runtime_service(
                "kernel_read_service", lambda: KernelReadService(db)
            ),
        )

    if name == "desk.list":
        return _primitive_list(ops, primitives, principal, _kind(args.get("kind")))
    if name == "desk.get":
        return _primitive_get(ops, primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""))
    if name == "desk.create":
        return _primitive_create(ops, primitives, principal, _kind(args.get("kind")), _data(args.get("data")))
    if name == "desk.update":
        return _primitive_update(ops, primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""), _data(args.get("data")))
    if name == "desk.delete":
        return _primitive_delete(ops, primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""))
    if name == "desk.verb":
        return _dispatch_verb(args, principal, primitives, workbenches, ops)
    if name == "workbench.run":
        return _run(workbenches.run(principal, str(args.get("workbench_id") or "")))
    if name == "workbench.add_item":
        return workbenches.add_item(principal, str(args.get("workbench_id") or ""), title=str(args.get("title") or ""), **_data(args.get("data")))
    if name == "workbench.list":
        return workbenches.list_workbenches(principal)
    if name == "workbench.get":
        return workbenches.get_workbench(principal, str(args.get("workbench_id") or ""))
    if name == "workbench.create":
        fields = _workbench_fields(args.get("fields"))
        if "name" in fields:
            raise ToolError("Workbench name belongs at the top level")
        return workbenches.create_workbench(principal, name=str(args.get("name") or ""), **fields)
    if name == "workbench.update":
        return workbenches.update_workbench(
            principal, str(args.get("workbench_id") or ""), **_workbench_fields(args.get("fields"))
        )
    if name == "workbench.delete":
        workbenches.delete_workbench(principal, str(args.get("workbench_id") or ""))
        return {"deleted": True, "id": str(args.get("workbench_id") or "")}
    if name == "workbench.update_item":
        return workbenches.update_item(principal, str(args.get("workbench_id") or ""), str(args.get("item_id") or ""), **_data(args.get("fields")))
    if name == "workbench.delete_item":
        item_id = str(args.get("item_id") or "")
        workbenches.delete_item(principal, str(args.get("workbench_id") or ""), item_id)
        return {"deleted": True, "id": item_id}
    if name == "workbench.list_runs":
        return workbenches.list_runs(principal, str(args.get("workbench_id") or ""))
    if name == "recipe.list":
        return recipes.list_recipes(principal)
    if name == "recipe.get":
        return recipes.get_recipe(principal, str(args.get("recipe_id") or ""))
    if name == "recipe.run":
        allowed = ("variables", "max_tokens", "temperature", "source_ref", "source_type", "grounding_refs", "grounding_revisions", "source_revision", "deadline_at", "initiator")
        options = _data(args.get("options"))
        return _run(recipes.run(principal, str(args.get("recipe_id") or ""), input=str(args.get("input") or ""), **{key: options[key] for key in allowed if key in options}))
    if name == "recipe.chat":
        # HS-151-02: recipe.chat RETIRED. The tool definition stays so tool
        # counts documented elsewhere remain stable.
        # HS-200-45 R6: it RAISES now. Returning the refusal made the sidecar
        # answer `isError: false`, so a caller read a permanent retirement as a
        # successful chat turn.
        raise ToolError(
            "recipe.chat is retired (HS-151-02) and will never run: threads "
            "replaced it. Post the turn to /api/threads/{id}/turns instead, or "
            "call thought.* for the refinement loop."
        )
    # PHILO-7-02: the membership tools are the declared zone.file/unfile/members
    # and kb.member.add/remove/kb.members operations, through the one registry.
    if name == "zone.file":
        return _receipted(*_invoke(ops, principal, "zone.file", {
            "directory_id": str(args.get("directory_id") or ""), "primitive_id": str(args.get("primitive_id") or "")}))
    if name == "zone.unfile":
        primitive_id = str(args.get("primitive_id") or "")
        _unfiled, kernel = _invoke(ops, principal, "zone.unfile", {
            "directory_id": str(args.get("directory_id") or ""), "primitive_id": primitive_id})
        return _receipted({"deleted": True, "id": primitive_id}, kernel)
    if name == "zone.list_members":
        return ops().invoke(principal, "zone.members", {"directory_id": str(args.get("directory_id") or "")})
    if name == "kb.add_member":
        return _receipted(*_invoke(ops, principal, "kb.member.add", {
            "kb_id": str(args.get("kb_id") or ""), "resource_ref": str(args.get("ref") or "")}))
    if name == "kb.remove_member":
        ref = str(args.get("ref") or "")
        _removed, kernel = _invoke(ops, principal, "kb.member.remove", {"kb_id": str(args.get("kb_id") or ""), "resource_ref": ref})
        return _receipted({"deleted": True, "id": ref}, kernel)
    if name == "kb.list_members":
        return ops().invoke(principal, "kb.members", {"kb_id": str(args.get("kb_id") or "")})
    if name == "kernel.receipt":
        return ops().invoke(principal, "kernel.receipt.read", {"operation_id": str(args.get("operation_id") or "")})
    if name == "meeting.list":
        allowed = ("query", "from_date", "to_date", "limit", "cursor", "speaker", "tag", "has_open_actions")
        return ops().invoke(principal, "meeting.list", {key: args[key] for key in allowed if key in args})
    if name == "meeting.get":
        return ops().invoke(principal, "meeting.read", {"meeting_id": str(args.get("meeting_id") or ""), "include": args.get("include")})
    if name == "meeting.import":
        return _meeting_import(ops(), meetings, principal, args)
    if name == "meeting.start_capture":
        config = args.get("config")
        if config is not None and not isinstance(config, dict):
            raise ToolError("config must be an object")
        _require_live_capture("meeting.start_capture", meetings)
        return meetings.start_capture(principal, config=config)
    if name == "meeting.stop_capture":
        meeting_id = args.get("meeting_id")
        _require_live_capture("meeting.stop_capture", meetings)
        return meetings.stop_capture(principal, meeting_id=str(meeting_id) if meeting_id is not None else None)
    if name == "meeting.delete":
        meeting_id = str(args.get("meeting_id") or "")
        meetings.delete_meeting(principal, meeting_id)
        return {"deleted": True, "id": meeting_id}
    if name == "meeting.export":
        return meetings.export_meeting(principal, str(args.get("meeting_id") or ""), str(args.get("format") or ""))
    if name == "dictation.list":
        allowed = ("limit", "cursor", "source")
        return dictation.list_journal(principal, **{key: args[key] for key in allowed if key in args})
    if name == "dictation.get":
        try:
            entry_id = int(args.get("entry_id"))
        except (TypeError, ValueError) as exc:
            raise ToolError("entry_id must be an integer") from exc
        return dictation.get_entry(principal, entry_id)
    if name == "desk.snapshot":
        return desk.snapshot(principal)
    if name == "desk.needs_you":
        # HS-200-07 (C4): ONE owner of the aggregate shape.  The inline
        # copy that lived here skipped a failed Room silently, so an
        # unobserved source read as an all-clear on this surface.
        from holdspeak.services.needs_you_aggregate import build_aggregate, shared_last_known
        from holdspeak.services.project_service import ProjectService
        project_service = ProjectService(db, observer=obs)
        return build_aggregate(
            list_projects=project_service.list_projects,
            room=project_service.room,
            principal=principal,
            # HS-200-13 (counsel P1-4): ONE last-known store with the hub.
            last_known=shared_last_known(lambda: db),
        )
    if name == "settings.hub":
        from holdspeak.config import Config, CONFIG_FILE
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        config = Config.load()
        engines = 0; groups_set = 0; default_set = False
        try:
            from holdspeak.services.model_library_service import ModelLibraryApplicationService
            from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
            setup = InferenceSetupApplicationService(db)
            lib = ModelLibraryApplicationService(db, setup_service=setup)
            lib_data = lib.get_library(principal)
            engines = lib_data.get("summary", {}).get("ready_count", 0)
        except Exception:
            pass
        try:
            from holdspeak.kernel.runtime import _configure
            broker = _configure(db)
            asn_svc = InferenceAssignmentService(db, registry=broker.inference_capability_registry)
            asn = asn_svc.assignment_summary(principal)
            for row in asn.get("rows", []):
                if row.get("id") == "global":
                    default_set = row.get("status") == "assigned"
                elif row.get("status") == "assigned":
                    groups_set += 1
        except Exception:
            pass
        connected = 0
        try:
            connected = len(db.automations.list_provider_connections())
        except Exception:
            pass
        loops = 0
        try:
            loops = len(db.cadence.list_loops())
        except Exception:
            pass
        import os
        written_at = None
        try:
            if CONFIG_FILE.exists():
                written_at = os.path.getmtime(CONFIG_FILE)
        except Exception:
            pass
        # HS-171-02: heartbeat rhythm mirror.
        heartbeat_rhythm: dict = {"loops": loops}
        try:
            from holdspeak.services.heartbeat_service import HeartbeatService
            hb = HeartbeatService(db)
            heartbeat_rhythm = hb.hub_rhythm()
        except Exception:
            heartbeat_rhythm["sweepEveryMinutes"] = 15
            heartbeat_rhythm["nextSweepAt"] = None
            heartbeat_rhythm["lastSweepAt"] = None
            heartbeat_rhythm["quiet"] = {"start": 22, "end": 8, "held": False}
        meetings_host = None
        try:
            if config.meeting.intel_profile_id:
                from holdspeak.intel.providers import resolve_meeting_placement as _rmp, endpoint_host as _eh
                _pl = _rmp(config.meeting)
                if _pl.profile_id:
                    if _pl.node:
                        meetings_host = str(_pl.node)
                    else:
                        _h = _eh(_pl.base_url)
                        meetings_host = _h if _h else (_pl.boundary or "local")
        except Exception:
            pass
        return {"models": {"engines": engines, "groupsSet": groups_set, "defaultSet": default_set}, "connections": {"connected": connected}, "voice": {"live": config.dictation.pipeline.enabled, "target": config.dictation.pipeline.target_profile_override or "auto"}, "meetings": {"intelligence": config.meeting.intel_enabled, "auto": config.meeting.intelligence_auto, "host": meetings_host}, "rhythm": heartbeat_rhythm, "sounds": {"on": config.ui.desk_sounds}, "system": {"host": "THIS DEVICE", "mesh": bool(getattr(config.mesh, "device_name", ""))}, "posture": config.control_mode, "writtenAt": written_at}
    if name == "meeting.run_intelligence":
        return ops().invoke(principal, "meeting.summary.run", {
            "meeting_id": str(args.get("meeting_id") or ""),
            "expected_selection_hash": str(args.get("expected_selection_hash") or ""),
        })
    if name == "meeting.proposals":
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS
        pbs = _PBS(db)
        return {"proposals": pbs.list_meeting_proposals(str(args.get("meeting_id") or ""), state=args.get("state"))}
    if name == "proposal.confirm":
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS2
        pbs = _PBS2(db)
        return pbs.confirm_proposal(principal, str(args.get("proposal_id") or ""), text=args.get("text"), owner=args.get("owner"), due=args.get("due"))
    if name == "proposal.dismiss":
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS3
        pbs = _PBS3(db)
        return pbs.dismiss_proposal(principal, str(args.get("proposal_id") or ""))
    # HS-173-04: reviewer nudge MCP twins
    if name == "steward.nudges":
        from holdspeak.services.project_steward_service import ProjectStewardService as _PSS
        from unittest.mock import MagicMock
        svc = _PSS(db, MagicMock(), MagicMock())
        return {"nudges": svc.list_nudges(str(args.get("project_id") or ""), state=args.get("state"))}
    if name == "nudge.send":
        from holdspeak.services.project_steward_service import ProjectStewardService as _PSS2
        from unittest.mock import MagicMock
        svc = _PSS2(db, MagicMock(), MagicMock())
        return svc.send_nudge(principal, str(args.get("step_id") or ""), str(args.get("text") or ""))
    if name == "nudge.dismiss":
        from holdspeak.services.project_steward_service import ProjectStewardService as _PSS3
        from unittest.mock import MagicMock
        svc = _PSS3(db, MagicMock(), MagicMock())
        return svc.dismiss_nudge(principal, str(args.get("step_id") or ""))
    if name == "decision_record.list":
        allowed = ("limit", "offset")
        return records.list_records(principal, **{key: args[key] for key in allowed if key in args})
    if name == "decision_record.get":
        return records.get(principal, str(args.get("record_id") or ""))
    if name == "decision_record.create_from_meeting":
        return records.create_from_meeting(principal, str(args.get("decision_id") or ""))
    if name == "decision_record.create_from_desk":
        return records.create_from_desk(principal, str(args.get("decision_id") or ""))
    if name == "decision_record.search":
        return records.search(
            principal, str(args.get("query") or ""),
            **({"limit": args["limit"]} if "limit" in args else {}),
        )
    if name == "decision.supersede":
        return _receipted(*_invoke(ops, principal, "decision.supersede", {"decision_id": str(args.get("decision_id") or "")}))
    if name == "pipeline.events":
        allowed = ("service", "method", "principal_kind", "since", "until", "correlation_id", "errors_only", "limit")
        filters = {key: args[key] for key in allowed if key in args}
        return events.recent(principal, **filters)
    if name == "follow_through.board":
        filters = {}
        if args.get("project_id"):
            filters["project_id"] = args["project_id"]
        if args.get("owner"):
            filters["owner"] = args["owner"]
        if args.get("state"):
            filters["state"] = args["state"]
        board = follow_through.board(principal, **filters)
        return {
            "now": [_card_dict(card) for card in board.now],
            "waiting": [_card_dict(card) for card in board.waiting],
            "unassigned": [_card_dict(card) for card in board.unassigned],
            "overdue": [_card_dict(card) for card in board.overdue],
        }
    if name == "follow_through.complete":
        return follow_through.complete(
            principal,
            str(args.get("card_id") or ""),
            str(args.get("verb") or ""),
            args.get("payload"),
        )
    if name == "follow_through.commit_decision":
        return follow_through.commit_decision(
            principal,
            str(args.get("decision_id") or ""),
            owner=args.get("owner"),
            due_at=args.get("due_at"),
        )
    if name == "monday_brief.get":
        brief = ops().invoke(principal, "brief.generate" if args.get("generate") else "brief.latest", {})
        if brief is None:
            return None
        result = asdict(brief)
        return _compose_brief_overlay_mcp(result, db, principal)
    if name == "monday_brief.generate":
        result = asdict(ops().invoke(principal, "brief.generate", {}))
        return _compose_brief_overlay_mcp(result, db, principal)
    if name == "monday_brief.shelf":
        return ops().invoke(principal, "brief.shelf.write", {"item_id": str(args.get("item_id") or ""), "state": args.get("state")})
    if name == "monday_brief.shelf_read":
        return ops().invoke(principal, "brief.shelf.read", {})

    # HS-136-02: scheduled recording CRUD + cancel-armed
    if name.startswith("scheduled_recording."):
        sr_service = ScheduledRecordingService(db)
        if name == "scheduled_recording.list":
            return sr_service.list_schedules(principal)
        if name == "scheduled_recording.create":
            kwargs: dict[str, Any] = {}
            # HS-147-01: calendar_event_id triggers event-linked arm;
            # service computes everything from the event.
            if "calendar_event_id" in args:
                kwargs["calendar_event_id"] = str(args["calendar_event_id"])
            else:
                kwargs["cron_expr"] = str(args.get("cron_expr") or "")
            if "title" in args:
                kwargs["title"] = str(args["title"])
            if "tz" in args:
                kwargs["tz"] = str(args["tz"])
            if "one_shot" in args:
                kwargs["one_shot"] = bool(args["one_shot"])
            if "duration_minutes" in args:
                kwargs["duration_minutes"] = int(args["duration_minutes"])
            if "enabled" in args:
                kwargs["enabled"] = bool(args["enabled"])
            return sr_service.create_schedule(principal, **kwargs)
        if name == "scheduled_recording.update":
            schedule_id = str(args.get("schedule_id") or "")
            kwargs = {}
            if "title" in args:
                kwargs["title"] = str(args["title"])
            if "cron_expr" in args:
                kwargs["cron_expr"] = str(args["cron_expr"])
            if "tz" in args:
                kwargs["tz"] = str(args["tz"])
            if "one_shot" in args:
                kwargs["one_shot"] = bool(args["one_shot"])
            if "duration_minutes" in args:
                kwargs["duration_minutes"] = int(args["duration_minutes"])
            if "enabled" in args:
                kwargs["enabled"] = bool(args["enabled"])
            return sr_service.update_schedule(principal, schedule_id, **kwargs)
        if name == "scheduled_recording.delete":
            return sr_service.delete_schedule(principal, str(args.get("schedule_id") or ""))
        if name == "scheduled_recording.cancel_armed":
            return sr_service.cancel_armed(principal, str(args.get("schedule_id") or ""))
    raise ToolError(f"Unknown tool: {name}")


def _dispatch_verb(args: dict[str, Any], principal: Principal, primitives: PrimitiveService, workbenches: WorkbenchService, ops: Callable[[], operations.OperationRegistry]) -> Any:
    verb_id = str(args.get("verb_id") or "")
    verb_args = _data(args.get("arguments"))
    if verb_id in _UI_ONLY_VERBS or verb_id.startswith(("go.", "window.", "system.")):
        return {"status": "ui_only", "verb_id": verb_id, "reason": "Opens a local surface"}
    server_verbs: dict[str, Callable[[dict[str, Any]], Any]] = {
        "desk.create": lambda value: _primitive_create(ops, primitives, principal, _kind(value.get("kind")), _data(value.get("data"))),
        "desk.update": lambda value: _primitive_update(ops, primitives, principal, _kind(value.get("kind")), str(value.get("id") or ""), _data(value.get("data"))),
        "desk.delete": lambda value: _primitive_delete(ops, primitives, principal, _kind(value.get("kind")), str(value.get("id") or "")),
        "workbench.add_item": lambda value: workbenches.add_item(principal, str(value.get("workbench_id") or ""), title=str(value.get("title") or ""), **_data(value.get("data"))),
        "workbench.run": lambda value: _run(workbenches.run(principal, str(value.get("workbench_id") or ""))),
    }
    handler = server_verbs.get(verb_id)
    if handler is None:
        raise ToolError(f"Verb is not allowlisted for MCP: {verb_id}")
    return handler(verb_args)


# ── MCP-007: Palette scoping ────────────────────────────────────────
# The same species as thread_modes.palette_for (allow-list intersected
# with a registry), applied at the MCP layer.  A palette is a
# frozenset[str] of tool names.  tools_for_palette filters the
# catalogue; dispatch_for_palette rejects names outside the palette.


def tools_for_palette(palette: frozenset[str]) -> list[dict[str, Any]]:
    """Return only the tools whose names are in *palette*."""
    return [t for t in TOOLS if t["name"] in palette]


def dispatch_for_palette(
    name: str,
    arguments: dict[str, Any] | None,
    principal: Principal,
    palette: frozenset[str],
) -> Any:
    """Dispatch scoped by *palette* -- typed refusal for tools outside it."""
    if name not in palette:
        raise ToolError(
            f"Tool {name!r} is not in the configured palette"
        )
    return dispatch(name, arguments, principal)
