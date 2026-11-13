"""MCP tool schemas and transport-neutral HoldSpeak service dispatch."""
from __future__ import annotations


from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service
from holdspeak import operations
from holdspeak.held_arguments import held_arguments, text, hidden, named, word_count, constant, normalizer, target

from collections.abc import Callable
from dataclasses import asdict
from typing import Any, Callable

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
from holdspeak.services import meeting_transcriber

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
        "description": "List desk primitives by kind. Find a note with kind=notes. Read each result by its id with desk.get. The desk schema advertises 18 primitive kinds; this tool operates on the 6 authorable kinds: notes, decisions, kbs, directories, workflows, and chains.",
        "inputSchema": {
            "type": "object",
            "properties": {"kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)}},
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.get",
        "description": "Get one desk primitive by kind and ID. Read a note with kind=notes and the id from desk.list. Read a zone and its filed objects with kind=directories. The desk schema advertises 18 primitive kinds; this tool operates on the 6 authorable kinds: notes, decisions, kbs, directories, workflows, and chains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string", "description": "Object ID from desk.list for the same kind."},
            },
            "required": ["kind", "id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.create",
        "description": (
            "Create a desk primitive. Write a note with kind=notes and data containing a title, body_markdown and tags. "
            "Make a zone with kind=directories, a name and optional parent_id. "
            "Put a decision on my review list with kind=decisions and status=proposed. "
            "Write the reason for a decision with kind=decisions in data.context_markdown. "
            "Authorable kinds: notes, decisions, kbs, directories, workflows, chains."
        ),
        "inputSchema": {
            **held_arguments("Save an object",
                named([f"data.{_KIND_ALIASES[kind]}_id" for kind in PRIMITIVE_KINDS], "Object", "desk.get",
                      {"kind": "kind", "id": "|".join(f"data.{_KIND_ALIASES[kind]}_id" for kind in PRIMITIVE_KINDS)}, "title|name|directory.name"),
                text("kind", "Kind"),
                text("data.title", "Title"),
                text("data.name", "Name"),
                word_count("data.body_markdown", "Text"),
                word_count("data.context_markdown", "Context"),
                word_count("data.decision_markdown", "Decision"),
                word_count("data.consequences_markdown", "Result"),
                text("data.status", "State")),
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "data": {"type": "object", "description": (
                    "Fields: notes note_id,title,body_markdown,tags; directories (zones) directory_id,name,parent_id "
                    "from desk.list; kbs kb_id,name,member_ids kind:id; decisions title,status=proposed,"
                    "context_markdown(reason/facts),decision_markdown(what),consequences_markdown(result),"
                    "deciders,alternatives,tags. Kind IDs generate if absent; data.id refused."
                )},
            },
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.update",
        "description": (
            "Update a desk primitive. Rename a zone with kind=directories and name. "
            "Move a zone with kind=directories and parent_id. Set parent_id to null to move it to the desk root. "
            "Edit a note with kind=notes and title, body_markdown or tags. "
            "Change a decision with kind=decisions. Supply context_markdown, decision_markdown or consequences_markdown "
            "to replace the old text. Authorable kinds: notes, decisions, kbs, directories, workflows, chains."
        ),
        "inputSchema": {
            **held_arguments("Change an object",
                text("kind", "Kind"),
                named("id", "Object", "desk.get", {"kind": "kind", "id": "id"}, "title|name|directory.name"),
                text("data.title", "Title"),
                text("data.name", "Name"),
                word_count("data.body_markdown", "Text"),
                word_count("data.context_markdown", "Context"),
                word_count("data.decision_markdown", "Decision"),
                word_count("data.consequences_markdown", "Result"),
                text("data.status", "State")),
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string", "description": "Object ID from desk.list for the same kind."},
                "data": {"type": "object", "description": "Fields to change, as for desk.create."},
            },
            "required": ["kind", "id", "data"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.delete",
        "description": (
            "Delete one desk primitive by kind and id. Deleting a zone puts what is filed in it back on the desk. "
            "A Thought's note needs its revisions in data. "
            "Authorable kinds: notes, decisions, kbs, directories, workflows, chains."
        ),
        "inputSchema": {
            **held_arguments("Delete an object", text("kind", "Kind"), named("id", "Object", "desk.get", {"kind": "kind", "id": "id"}, "title|name|directory.name"), hidden("data", "Saved revision")),
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string", "description": "The object's id, from desk.list with the same kind."},
                # PHILO-7-02: a Thought's note delete (an admitted tombstone)
                # needs its two expected revisions; the envelope carries them.
                "data": {"type": "object", "description": (
                    "Optional. A Thought's note only: expected_aggregate_revision and "
                    "expected_lifecycle_revision from the note's last read. Any other field is refused."
                )},
            },
            "required": ["kind", "id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.verb",
        "description": "Dispatch an allowlisted server-side desk verb. Local presentation verbs return ui_only.",
        "inputSchema": {**{**normalizer('holdspeak.mcp.tools:desk_verb_arguments'), 'x-held-delegate': {'resolver': 'holdspeak.mcp.tools:held_desk_verb', 'arguments': 'arguments'}, **held_arguments('Run a Desk action',
                text('verb_id', 'Action'))}, **{
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
        }},
    },
    {
        "name": "automation.run",
        "description": "Run an automation through Programs. The result links its Program run.",
        "inputSchema": {**held_arguments('Run an automation', named('workbench_id', 'Automation', 'automation.get', {'workbench_id': 'workbench_id'}, 'automation.name|name'), constant('Action', 'Start its Program run')), **{
            "type": "object",
            "properties": {"workbench_id": {"type": "string"}},
            "required": ["workbench_id"],
            "additionalProperties": False,
        }},
    },
    {
        "name": "workbench.add_item",
        "description": "Add a work item to a HoldSpeak Workbench.",
        "inputSchema": {**{**normalizer('holdspeak.services.workbench_service:WorkbenchService.item_arguments', mode='add'), **held_arguments('Save a work item',
                named('workbench_id', 'Automation', 'automation.get', {'workbench_id': 'workbench_id'}, 'automation.name|name'),
                text('title', 'Title'),
                named('data.id', 'Item', 'automation.get', {'workbench_id': 'workbench_id'}, 'title', rows='items', match={'id': 'data.id'}),
                word_count('data.body', 'Text'),
                text('data.priority', 'Priority'),
                hidden('data.grounding', 'Sources', 'secret'),
                hidden('data.context', 'Context', 'secret'))}, **{
            "type": "object",
            "properties": {
                "workbench_id": {"type": "string"},
                "title": {"type": "string"},
                "data": {"type": "object", "description": "Optional item fields."},
            },
            "required": ["workbench_id", "title"],
            "additionalProperties": False,
        }},
    },
    {
        "name": "meeting.list",
        "description": "List or search active meetings; set parked to list retained parked meetings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}, "from_date": {"type": "string"},
                "to_date": {"type": "string"}, "speaker": {"type": "string"},
                "tag": {"type": "string"}, "has_open_actions": {"type": "boolean"},
                "parked": {"type": "boolean", "description": "List parked meetings only."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                "cursor": {"type": ["string", "integer"]},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "meeting.get",
        "description": "Get one stored meeting.",
        "inputSchema": {
            "type": "object",
            "properties": {"meeting_id": {"type": "string"}, "include": {"type": "string"}, "include_parked": {"type": "boolean", "description": "Read a retained parked meeting."}},
            "required": ["meeting_id"],
            "additionalProperties": False,
        },
    },
 ]


def _workbench_tool(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None, *, held: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "description": description, "inputSchema": {
        **(held or {}), "type": "object", "properties": properties, "required": required or [], "additionalProperties": False,
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
        "instruction": {"type": "string", "description": "The Do text. With it, each run makes one result; empty keeps the item queue."},
        "sources": {"type": "array", "items": {"type": "string"}, "description": "Refs the run reads, for example note:<id>, meeting:<id>, zone:<id> (a drawer), person:<id>, or a set: meetings:this_week, notes:this_week."},
        "output_target": {"type": "string", "description": "Where a result goes: inbox (default), needs_you, today, project_updates:<project_id>, or destination:<id> (prepared only; the owner presses Send)."},
        "do_kind": {"type": "string", "enum": ["run", "hand_to_agent", "run_program"]},
        "agent_profile": {"type": "string", "description": "Installed agent profile for hand_to_agent."},
        "review_by": {"type": "string", "enum": ["none", "codex", "claude", "pi"]},
        "program_template": {"type": "string", "enum": ["fast-cycle", "build-and-review", "race", "from-the-desk", "overnight"], "description": "Owner only. run_program: the template each run uses. Hand starts ignore templates."},
        "program_control": {"type": "string", "enum": ["secure", "normal", "yolo"], "description": "Owner only. run_program: the control level, else the template's or desk's. A hand runs no wider than the desk; this setting may narrow it."},
        "program_runs_on": {"type": "array", "items": {"type": ["string", "object"]}, "description": "run_program: the agents in order, names or {profile, engine} (engine for pi only)."},
        "program_may_call": {"type": "boolean", "description": "run_program: the engine may call the owner where the Reach rules allow it."},
        "program_may_handoff": {"type": "boolean", "description": "run_program: a step at a usage limit may continue in the next agent."},
    },
    "additionalProperties": False,
}


def _workbench_fields(value: Any) -> dict[str, Any]:
    fields = _data(value)
    unknown = set(fields) - set(_WORKBENCH_FIELDS_SCHEMA["properties"])
    if unknown:
        raise ToolError(f"Unsupported Workbench fields: {', '.join(sorted(unknown))}")
    return fields


#: Betterment M3: an automation's sentence, in the words of its window
#: (``WorkbenchService.create_automation``). ``when``, ``with`` and
#: ``spend_limit`` are the owner's: a Thread or a run stops for his press.
_SENTENCE_PROPERTIES: dict[str, Any] = {
    "do": {"type": "string", "description": "What each run does (the Do text), hand_to_agent to hand each source item once, or run_program to make and start one Program each run (fields.program_template)."},
    "about": {"type": "array", "items": {"type": "string"}, "description": "What it reads: refs as fields.sources."},
    "when": {
        "type": "object",
        "description": "One start: {schedule: {every: day|weekday|week|hour, day: friday, time: '15:00'}}, {event: <id>, repository: 'owner/repo'} or {manual: true}.",
        "properties": {
            "schedule": {"type": "object", "properties": {
                "every": {"type": "string", "enum": ["day", "weekday", "week", "hour"]},
                "day": {"type": ["string", "integer"]}, "time": {"type": "string"},
            }, "additionalProperties": False},
            "event": {"type": "string"}, "repository": {"type": "string"},
            "manual": {"type": "boolean", "enum": [True]},
        },
        "additionalProperties": False,
    },
    "with": {"type": "string", "description": "The installed agent profile for hand_to_agent; otherwise the inference profile."},
    "put_in": {"type": "string", "description": "Where results go: inbox, needs_you or destination:<id>."},
    "spend_limit": {"type": ["number", "null"], "description": "Dollars per run; null = the engine's own."},
    "review_by": {"type": "string", "enum": ["none", "codex", "claude", "pi"], "description": "Optional installed reviewer for each handed agent."},
}


def _sentence(args: dict[str, Any]) -> dict[str, Any]:
    return {word: args[word] for word in _SENTENCE_PROPERTIES if word in args}


TOOLS.extend([
    _workbench_tool("automation.list", "List Workbenches.", {}),
    _workbench_tool("automation.get", "Get a Workbench.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("automation.create", "Create an automation (a Workbench) from its sentence words and closed optional fields.", {"name": {"type": "string", "description": "Non-empty Workbench name."}, "fields": _WORKBENCH_FIELDS_SCHEMA, **_SENTENCE_PROPERTIES}, ["name"]),
    _workbench_tool("automation.update", "Update the given sentence words and closed fields of an automation.", {"workbench_id": {"type": "string"}, "fields": _WORKBENCH_FIELDS_SCHEMA, **_SENTENCE_PROPERTIES}, ["workbench_id"]),
    _workbench_tool("automation.delete", "Delete a Workbench.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("workbench.update_item", "Update supplied fields of a Workbench item.", {"workbench_id": {"type": "string"}, "item_id": {"type": "string"}, "fields": {"type": "object", "description": "Item patch fields."}}, ["workbench_id", "item_id", "fields"], held={**normalizer('holdspeak.services.workbench_service:WorkbenchService.item_arguments', mode='update'), **held_arguments('Change a work item',
                named('workbench_id', 'Automation', 'automation.get', {'workbench_id': 'workbench_id'}, 'automation.name|name'),
                named('item_id', 'Item', 'automation.get', {'workbench_id': 'workbench_id'}, 'title', rows='items', match={'id': 'item_id'}),
                text('fields.title', 'Title'),
                word_count('fields.body', 'Text'),
                text('fields.priority', 'Priority'),
                text('fields.status', 'State'))}),
    _workbench_tool("workbench.delete_item", "Park a Workbench item; its retained work stays available.", {"workbench_id": {"type": "string"}, "item_id": {"type": "string"}}, ["workbench_id", "item_id"], held=held_arguments('Park a work item',
                named('workbench_id', 'Automation', 'automation.get', {'workbench_id': 'workbench_id'}, 'automation.name|name'),
                named('item_id', 'Item', 'automation.get', {'workbench_id': 'workbench_id'}, 'title', rows='items', match={'id': 'item_id'}))),
    _workbench_tool("workbench.list_runs", "List Workbench runs.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("automation.results", "An automation's newest results: text, what it looked at, wrote and prepared, cost, failure reason.", {"workbench_id": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}}, ["workbench_id"]),
    _workbench_tool("automation.cancel", "Park an automation's running Program (the newest, or run_id). Its current agent turn can finish.", {"workbench_id": {"type": "string"}, "run_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("recipe.list", "List Agent recipes.", {}),
    _workbench_tool("recipe.get", "Get an Agent recipe.", {"recipe_id": {"type": "string"}}, ["recipe_id"]),
    _workbench_tool("recipe.run", "Run an Agent recipe and return its lifecycle-backed result and minted artifact reference.", {"recipe_id": {"type": "string"}, "input": {"type": "string"}, "options": _RECIPE_RUN_OPTIONS_SCHEMA}, ["recipe_id"]),
    _workbench_tool("zone.file", "File a primitive in a Zone. File a note into a zone by setting directory_id from desk.list kind=directories and primitive_id to note:<id>. Filing a primitive again moves it.", {"directory_id": {"type": "string", "description": "Zone ID from desk.list kind=directories."}, "primitive_id": {"type": "string", "description": "Object kind:id; for example note:<id> with its ID from desk.list kind=notes."}}, ["directory_id", "primitive_id"],
        held=held_arguments('File an object',
                named('directory_id', 'Folder', 'desk.get', {'kind': '=directories', 'id': 'directory_id'}, 'directory.name|name'),
                named('primitive_id', 'Object', 'desk.get',
                    {'kind': {'reference': 'primitive_id', 'part': 'desk_kind'}, 'id': {'reference': 'primitive_id', 'part': 'id'}},
                    'title|name|directory.name'))),
    _workbench_tool("zone.unfile", "Remove a primitive from a Zone: directory_id and kind:id primitive_id.", {"directory_id": {"type": "string", "description": "Zone ID from desk.list kind=directories."}, "primitive_id": {"type": "string", "description": "Filed object kind:id; ID from desk.list (for example note:<id> with its ID from desk.list kind=notes)."}}, ["directory_id", "primitive_id"]),
    _workbench_tool("zone.list_members", "List Zone members. List the notes in a zone. Each member has a primitive_id such as note:<id>.", {"directory_id": {"type": "string", "description": "Zone ID from desk.list kind=directories."}}, ["directory_id"]),
    _workbench_tool("kb.add_member", "Add a resource reference to a knowledge base. Add a note to a knowledge base: kb_id and ref note:<id>.", {"kb_id": {"type": "string", "description": "The knowledge base id, from desk.list kind=kbs."}, "ref": {"type": "string", "description": "A kind:id reference: for a note, note:<id> with the id from desk.list kind=notes."}}, ["kb_id", "ref"]),
    _workbench_tool("kb.remove_member", "Remove a resource reference from a knowledge base.", {"kb_id": {"type": "string", "description": "The knowledge base id, from desk.list kind=kbs."}, "ref": {"type": "string", "description": "The reference to remove, as kind:id: for a note, note:<id> with the id from desk.list kind=notes."}}, ["kb_id", "ref"]),
    _workbench_tool("kb.list_members", "List knowledge-base members.", {"kb_id": {"type": "string", "description": "The knowledge base id, from desk.list kind=kbs."}}, ["kb_id"]),
])

#: One name (2026-11-08): an automation's tools are ``automation.*``, the
#: user's word. The stored kind stays ``workbench``; the old ``workbench.*``
#: twins of these eight tools are gone.


def _mcp_tool(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None, *, held: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            **(held or {}),
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
        held=held_arguments("Start a meeting", hidden("config", "Capture settings")),
    ),
    _mcp_tool(
        "meeting.stop_capture",
        "Stop the active meeting capture, optionally identifying the meeting to stop.",
        {"meeting_id": {"type": "string", "description": "Optional meeting identifier."}},
        held={**target("meeting.read", "resolve_stop_target"), **held_arguments("Stop a meeting", named("meeting_id", "Meeting", "meeting.get", {"meeting_id": "meeting_id"}, "title"))},
    ),
    _mcp_tool(
        "meeting.delete",
        "Park a stored meeting while retaining its transcript and related work.",
        {"meeting_id": {"type": "string", "description": "Meeting identifier to park."}},
        ["meeting_id"],
        held=held_arguments("Park a meeting", named("meeting_id", "Meeting", "meeting.get", {"meeting_id": "meeting_id"}, "title")),
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
    # PHILO-17: Transcribe a meeting saved with its audio only.
    _mcp_tool(
        "meeting.transcribe",
        "Owner only. Transcribe a saved meeting that kept its audio only because speech was not set up. The transcript goes into the same meeting, in the background; read meeting.get until transcription finishes. Refused while speech is not set up.",
        {"meeting_id": {"type": "string", "description": "Meeting identifier."}},
        ["meeting_id"],
        held=held_arguments("Transcribe a meeting", named("meeting_id", "Meeting", "meeting.get", {"meeting_id": "meeting_id"}, "title")),
    ),
    _mcp_tool(
        "meeting.run_intelligence",
        "Enqueue a fresh intelligence job using the disclosed summary route selection hash. Refuses when the hash is absent, stale, or the meeting has no transcript.",
        {
            "meeting_id": {"type": "string", "description": "Meeting identifier."},
            "expected_selection_hash": {"type": "string", "description": "Selection hash from the meeting planned_route read."},
        },
        ["meeting_id", "expected_selection_hash"],
        held=held_arguments("Read a meeting", named("meeting_id", "Meeting", "meeting.get", {"meeting_id": "meeting_id"}, "title"), hidden("expected_selection_hash", "Engine revision", "token")),
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
        held=held_arguments("Send a review comment", hidden("step_id", "Review"), word_count("text", "Comment")),
    ),
    _mcp_tool(
        "nudge.dismiss",
        "Dismiss a proposed reviewer nudge without posting. A 7-day cooldown starts.",
        {"step_id": {"type": "string", "description": "Nudge step identifier."}},
        ["step_id"],

        held=held_arguments('Dismiss a review reminder',
                hidden('step_id', 'Review', 'secret'))),
    _mcp_tool("desk.snapshot", "Read one coherent snapshot of the durable HoldSpeak desk.", {}),
    _mcp_tool("desk.needs_you", "What needs me, by the one rule every face uses: Door cards, Room items, decisions to review, engine blockers, failed summaries. One count; waiting rows and muted projects are not counted. Each row has direction, person_id, person_name. Filters combine; they narrow the rows, never the count. A 1:1 commitment's text is withheld.", {
        "direction": {"type": "string", "enum": ["mine", "theirs", "decide", "setup"], "description": "theirs: owed to me"},
        "person": {"type": "string", "description": "a name (Theo) or People id"},
        "project": {"type": "string", "description": "a name, or an id from project.list"},
        "week": {"type": "boolean", "description": "due by this Sunday, late too"},
    }),
    _mcp_tool(
        "today.get",
        "Read Today as one page of data: the top of Needs you, the day, Since yesterday, and Prepared.",
        {},
    ),
    _mcp_tool(
        "decision_record.list", "List decision records.",
        # Newest first. PG16: program_id = a Program's proposed records (a
        # Skip, a merge by rule). The thread palettes may not grow
        # (test_memory_slice6_reflect MAIN_PALETTE_BYTES), so the words are
        # short and the lower bounds are the service's (it clamps limit to
        # 1..500 and offset to 0 or more).
        {"limit": {"type": "integer", "maximum": 500}, "offset": {"type": "integer"},
         "program_id": {"type": "string"}},
    ),
    _mcp_tool(
        "decision_record.get", "Get a decision record with sources, work, revisions.",
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
        "decision_record.search", "Search decision records and affected work.",
        {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}}, ["query"],
    ),
    _mcp_tool(
        "decision.supersede",
        "Supersede a decision when a successor decision replaces it.",
        {"decision_id": {"type": "string", "description": "Decision to supersede."}},
        ["decision_id"],

        held=held_arguments('Supersede a Desk decision',
                named('decision_id', 'Decision', 'desk.get', {'kind': '=decisions', 'id': 'decision_id'}, 'title'))),
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
        "Read Follow-Through cards; filter project/owner/lane.",
        {
            "project_id": {"type": "string", "description": "Optional project."},
            "owner": {"type": "string", "description": "Optional owner."},
            "state": {"type": "string", "enum": ["now", "waiting", "unassigned", "overdue"], "description": "Optional lane."},
        },
    ),
    _mcp_tool(
        "follow_through.complete",
        "Apply a completion verb to a Follow-Through card.",
        {
            "card_id": {"type": "string", "description": "Card ID."},
            "verb": {"type": "string", "enum": ["done", "dismiss", "snooze", "delegate", "reopen", "due"], "description": "Board verb; due sets payload.due_at."},
            "payload": {"type": "object", "description": "Verb data; until/snooze, to/delegate."},
        },
        ["card_id", "verb"],
        held={**normalizer('holdspeak.services.follow_through_service:FollowThroughService.effective_arguments'), **held_arguments("Change a task", named("card_id", "Task", "follow_through.board", {}, "text",
                                 rows=["now", "waiting", "unassigned", "overdue"], match={"id": "card_id"}), text("verb", "Action"),
                            text("payload.to", "Owner"), text("payload.until", "Until"),
                            text("payload.due_at", "Due"))},
    ),
    _mcp_tool(
        "monday_brief.get",
        "Read the latest persisted Monday Brief; generate=true when none exists.",
        {"generate": {"type": "boolean", "default": False, "description": "Generate if no persisted brief."}},
        held={**normalizer('holdspeak.mcp.tools:brief_arguments'), **{"x-effect": "write", **held_arguments("Read or make a Desk brief",
            text("generate", "Make if needed"), constant("Document", "Desk brief"))}},
    ),
    _mcp_tool(
        "monday_brief.generate",
        "Generate today's Brief from durable sources. A repeat on the same day remakes it (same id, new body).",
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
     held={**normalizer('holdspeak.services.scheduled_recording_service:ScheduledRecordingService.command_arguments', create=True), **held_arguments('Make a recording schedule',
                text('title', 'Title'),
                text('cron_expr', 'When'),
                text('tz', 'Time zone'),
                text('one_shot', 'One time'),
                text('duration_minutes', 'Minutes'),
                text('enabled', 'On'),
                named('calendar_event_id', 'Event', 'door.get', {}, 'title', rows='upcoming', match={'id': 'calendar_event_id'}))}),
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
     held={**normalizer('holdspeak.services.scheduled_recording_service:ScheduledRecordingService.command_arguments', create=False), **held_arguments('Change a recording schedule',
                named('schedule_id', 'Schedule', 'scheduled_recording.list', {}, 'title', rows='$', match={'id': 'schedule_id'}),
                text('title', 'Title'),
                text('cron_expr', 'When'),
                text('tz', 'Time zone'),
                text('one_shot', 'One time'),
                text('duration_minutes', 'Minutes'),
                text('enabled', 'On'))}),
    _mcp_tool(
        "scheduled_recording.delete",
        "Delete a scheduled recording. Refuses if the schedule is armed or recording.",
        {"schedule_id": {"type": "string", "description": "Schedule identifier."}},
        ["schedule_id"],
     held=held_arguments('Remove a recording schedule',
                named('schedule_id', 'Schedule', 'scheduled_recording.list', {}, 'title', rows='$', match={'id': 'schedule_id'}))),
    _mcp_tool(
        "scheduled_recording.cancel_armed",
        "Cancel an armed (counting-down) scheduled recording before it fires.",
        {"schedule_id": {"type": "string", "description": "Schedule identifier."}},
        ["schedule_id"],
     held=held_arguments('Cancel an armed recording',
                named('schedule_id', 'Schedule', 'scheduled_recording.list', {}, 'title', rows='$', match={'id': 'schedule_id'}))),
])

# Aggregate tools from per-family modules.
for _family in FAMILIES:
    TOOLS.extend(_family.TOOLS)

# The UI owns local surface state. These IDs deliberately never mutate the
# database when sent by an external MCP client.
_UI_ONLY_VERBS = {
    "desk.open", "object.open", "object.info", "object.edit", "object.rename",
    "object.ask-about", "desk.toggle-view", "desk.overview",
    "desk.arrange", "desk.reset-layout", "desk.reset-to-seed", "system.search",
    "system.sheet", "window.close", "window.minimize", "window.cycle",
    "window.cycle-reverse", "window.snap-left", "window.snap-right", "window.maximize",
    "window.depth",
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
        InferenceAssignmentService.require_owner(principal)


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
        registry = ops()
        return _receipted(*_invoke(ops, principal, operation, registry.update_args(
            principal, data, item_id, operation=operation, id_field=operations.DESK_ID_ARGUMENT[kind])))
    return getattr(service, f"update_{kind}")(principal, item_id, **data)


def _primitive_delete(ops: Callable[[], operations.OperationRegistry], service: PrimitiveService, principal: Principal, kind: str, item_id: str, data: dict[str, Any] | None = None) -> Any:
    kernel = None
    data = dict(data or {})
    if (operation := _desk_operation(kind, "delete")) is not None:
        # The contract refuses any field its descriptor does not name (no silent drop).
        registry = ops()
        deleted, kernel = _invoke(ops, principal, operation, registry.update_args(
            principal, data, item_id, operation=operation, id_field=operations.DESK_ID_ARGUMENT[kind]))
    else:
        if data:
            raise ToolError(f"desk.delete kind={kind}s takes no data")
        deleted = getattr(service, f"delete_{kind}")(principal, item_id)
    return _receipted({"deleted": deleted, "id": item_id}, kernel)


# ── PHILO-7-02: refusal receipts before ``invoke`` (R2 class 4) ─────────
#
# An authenticated call that names an ADMITTED operation (or a conditionally
# admitted one whose payload carries its admission argument) and is refused
# before the registry -- the schema refusal, non-object arguments, the palette
# refusal -- keeps its named error and leaves a kernel refusal receipt. A call
# that names no identifiable consequential operation leaves none.

#: MCP tools that name one operation directly, and how their arguments map.
_TOOL_OPERATIONS: dict[str, str] = {
    "zone.file": "zone.file", "zone.unfile": "zone.unfile",
    "kb.add_member": "kb.member.add", "kb.remove_member": "kb.member.remove",
    "decision.supersede": "decision.supersede",
}
_TOOL_VERBS = {"desk.create": "create", "desk.update": "update", "desk.delete": "delete"}
_PALETTE_REFUSED = "mcp_palette_refused"


def _tool_operation(name: str, args: Any) -> tuple[str | None, Any]:
    """The operation an MCP call names, and its raw operation payload, when identifiable."""
    from holdspeak.mcp.families.channel import TOOL_OPERATIONS as _CHANNEL_TOOL_OPERATIONS
    from holdspeak.mcp.families.project import TOOL_OPERATIONS as _ROOM_TOOL_OPERATIONS

    if name in _CHANNEL_TOOL_OPERATIONS:
        # PHILO-10-01: the Send's tools name their declared operation.
        return _CHANNEL_TOOL_OPERATIONS[name], (dict(args) if isinstance(args, dict) else None)
    if name in _ROOM_TOOL_OPERATIONS:
        # PHILO-9-02: the Room's tools name their declared operation too (a
        # palette refusal of an ADMITTED one leaves its refusal receipt).
        return _ROOM_TOOL_OPERATIONS[name], (dict(args) if isinstance(args, dict) else None)
    if name in _TOOL_OPERATIONS:
        if not isinstance(args, dict):
            return _TOOL_OPERATIONS[name], None
        raw = {("resource_ref" if key == "ref" else key): value for key, value in args.items()}
        return _TOOL_OPERATIONS[name], raw
    if name == "desk.verb":
        if not isinstance(args, dict) or args.get("verb_id") not in _TOOL_VERBS:
            return None, None
        name, args = str(args["verb_id"]), args.get("arguments")
    verb = _TOOL_VERBS.get(name)
    if verb is None or not isinstance(args, dict):
        return None, None
    kind = _KIND_ALIASES.get(str(args.get("kind") or ""))
    operation = operations.DESK_OPERATIONS.get((kind, verb)) if kind else None
    if operation is None:
        return None, None
    id_field = operations.DESK_ID_ARGUMENT[kind]
    data = args.get("data") if args.get("data") is not None or verb != "delete" else {}
    if not isinstance(data, dict):
        return operation, None
    raw = dict(data)
    if verb != "create" and args.get("id") is not None:
        raw.setdefault(id_field, args.get("id"))
    return operation, raw


def _bare_project_service(db: Any, obs: Any) -> Any:
    from holdspeak.services.project_service import ProjectService

    return ProjectService(db, observer=obs)


def _registry() -> operations.OperationRegistry:
    db = db_or(get_database)
    return operations.for_runtime(lambda: runtime_service(
        "primitive_service", lambda: PrimitiveService(db, observer=observer_or(get_observer))))


def refuse_before_invoke(name: str, args: Any, principal: Principal, code: str) -> dict[str, Any] | None:
    """Class 4: the refusal receipt for a consequential MCP attempt refused before ``invoke``."""
    operation, raw = _tool_operation(name, args)
    if operation is None:
        return None
    try:
        return _registry().refuse(principal, operation, code, raw)
    except Exception:  # pragma: no cover - a receipt never replaces the named refusal
        return None


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

    overlay = compose_person_overlay(brief_window, people_svc, follow_through, db, principal, shared_only=True)

    if overlay.get("state") == "ready":
        # F6: filter sections to shared_intent-only via _mcp_readable pattern.
        # Person overlay sections are manager-computed summaries (counts + dates),
        # not encrypted records, so they pass through.  The underlying encrypted
        # data was already filtered by the people_service layer.
        result["person_sections"] = overlay.get("sections", [])
    elif overlay.get("state") == "unavailable":
        result["person_sections_state"] = "unavailable"

    return result


# The one helper every family shares (holdspeak/mcp/aio.py).
from holdspeak.mcp.aio import run_async as _run  # noqa: E402


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
            "transcriber_factory": meeting_transcriber.default_transcriber_factory,
        })
    except Exception:
        held_path.unlink(missing_ok=True)
        raise
    return {"meeting_id": result["meeting_id"], "transcription_status": result["status"]}


def runtime_registry(primitives: Any = None, meetings: Any = None) -> operations.OperationRegistry:
    """The hub's bound contract, the object its HTTP routes reach (PHILO-5-01/02): the one MCP path to it.

    In the hub no builder below runs (the brief's producer clock, the summary's
    runtime_queue notify and the Programs engine are the hub's); in a bare
    composition it binds over plain (db, observer) services.
    """
    from holdspeak.mcp.families import people as people_family
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
    from holdspeak.services.desk_window_service import DeskWindowService
    from holdspeak.services.today_service import TodayService
    from holdspeak.services.channel_service import ChannelService

    db, obs = db_or(get_database), observer_or(get_observer)
    from holdspeak.services.meeting_aftercare_service import MeetingAftercareService

    from holdspeak.mcp.families import ask as ask_family
    plain = {"channel_service": lambda: ChannelService(db), "ask_service": lambda: _Lazy(ask_family._service), "meeting_intel_service": lambda: MeetingIntelService(db, observer=obs),
             "meeting_aftercare_service": lambda: MeetingAftercareService(db, observer=obs),
             "monday_brief_service": lambda: MondayBriefService(db, observer=obs),
             "kernel_read_service": lambda: KernelReadService(db), "today_service": lambda: TodayService(db),
             "project_service": lambda: _bare_project_service(db, obs),
             "primitive_service": lambda: primitives or PrimitiveService(db, observer=obs),
             "meeting_service": lambda: meetings or MeetingService(db, observer=obs),
             "desk_window_service": lambda: DeskWindowService(db),
             "people_service": lambda: people_family.build_people_service(),
             # The Automations verbs (automation_operations.py): the hub's one composed instance.
             "workbench_service": lambda: WorkbenchService(db, observer=obs),
             # The Decisions verbs (decision_operations.py): the ledger and Commit.
             "decision_lifecycle_service": lambda: DecisionLifecycleService(db, observer=obs),
             "follow_through_service": lambda: FollowThroughService(db, observer=obs),
             # The Settings credential verbs bind here; they have no tool (HTTP only).
             "credential_service": lambda: _credential_service(db, obs),
             # The dictation verbs (dictation_operations.py): the hub's journal and correction store.
             "dictation_service": lambda: DictationService(db, observer=obs),
             # The device sync (device_operations.py).
             "sync_service": lambda: _sync_service(db, obs),
             # The Settings family (settings_operations.py, setup_operations.py): off the hub too.
             **_settings_family(db, obs),
             # 2026-11-09 (ops/programs-work): recipe writes, the note window, memory.
             **_work_services(db, obs),
             # 2026-11-09 (ops/connections): the Engines window, the providers, the calendar, UI feedback.
             **_connections_services(db)}
    return operations.for_runtime(program_service=lambda: operations.LIVE_PROGRAM_SERVICE,
                                  phone_service=lambda: operations.LIVE_PHONE_SERVICE,
                                  calls_service=lambda: operations.LIVE_CALLS_SERVICE,
                                  recordings_service=lambda: operations.LIVE_RECORDINGS_SERVICE,
                                  tts_service=_tts_service, **{
        name: (lambda name=name, build=build: runtime_service(name, build)) for name, build in plain.items()})


class _Lazy:
    """A bare service built at its first use, never when the registry binds:
    some constructors reach the kernel broker (``RecipeService``), and a bare
    MCP registry binds every builder at once."""

    def __init__(self, build: Callable[[], Any]) -> None:
        self._build, self._target = build, None

    def __getattr__(self, name: str) -> Any:
        if self._target is None:
            self._target = self._build()
        return getattr(self._target, name)


def _work_services(db: Any, obs: Any) -> dict[str, Any]:
    """The bare builds of the recipe, note-window, memory and desk-state rows' services (lazy)."""
    from holdspeak.mcp.families.thought import _service as refinement
    from holdspeak.runtime import composition_declared as bare
    from holdspeak.services.memory_service import MemoryService

    builds: dict[str, Callable[[], Any]] = {
        "recipe_service": lambda: bare._bare_recipes(db, obs),
        "desk_service": lambda: bare._bare_desk(db, obs),
        "projection_service": lambda: bare._bare_projections(db, obs),
        "constitutional_context_service": bare._constitutional,
        "watch_service": lambda: _watch_service(db, obs),
        "refinement_thought_service": lambda: bare._bare_thoughts(db),
        "recall_service": lambda: bare._bare_recall(db),
        "refinement_service": refinement,
        "memory_service": lambda: MemoryService(db=db, observer=obs),
    }
    return {name: (lambda build=build: _Lazy(build)) for name, build in builds.items()}


def _watch_service(db: Any, obs: Any) -> Any:
    from holdspeak.services.watch_service import WatchService

    return WatchService(db, observer=obs)


def _connections_services(db: Any) -> dict[str, Any]:
    """The bare builds of the concierge, provider, connections, calendar and feedback rows' services (lazy:
    the connections service composes the assignment authority, built only when a call needs it)."""
    from holdspeak.provider_operations import bare_provider_service
    from holdspeak.services.calendar_service import CalendarService
    from holdspeak.services.concierge_service import ConciergeService
    from holdspeak.services.ui_feedback import FeedbackService

    from holdspeak.mcp.families import project as project_family

    builds = {"concierge_service": lambda: ConciergeService(db=db), "provider_service": bare_provider_service,
              "connections_service": project_family._connections_service,
              "calendar_service": lambda: CalendarService(db=db), "feedback_service": FeedbackService}
    return {name: (lambda build=build: _Lazy(build)) for name, build in builds.items()}


def _tts_service() -> Any:
    from holdspeak.services.tts_service import TtsService

    return TtsService()


def _sync_service(db: Any, obs: Any) -> Any:
    from holdspeak.services.sync_service import SyncService

    return SyncService(db, observer=obs)
def _settings_family(db: Any, obs: Any) -> dict[str, Any]:
    from holdspeak.settings_operations import bare_builders

    return bare_builders(db, obs)


def _credential_service(db: Any, obs: Any) -> Any:
    from holdspeak.services.credential_service import CredentialService

    return CredentialService(db, observer=obs)


def dispatch(name: str, arguments: dict[str, Any] | None, principal: Principal) -> Any:
    """Call one day-one MCP tool and return JSON-serializable data.

    Every tool call that writes announces itself: ONE ``desk_changed`` frame
    when the call returns and changed a row (2026-10-05). A tool that goes
    through ``OperationRegistry.invoke``, or whose service announces, adds
    to the same frame; a tool outside both is named here, so no MCP write is
    silent and no read sends a frame.
    """
    from holdspeak.db.connection import watch_writes
    from holdspeak.runtime.announce_scope import announce_scope

    # Conductor K6: a launched agent's call meets its launch rule here, the
    # one dispatcher every MCP transport reaches (services/conductor_launch).
    from holdspeak.services import conductor_launch

    arguments = conductor_launch.gate_call(name, arguments, principal)
    # S9: capture the existing hub window rows before a model write so the
    # existing run trace can describe a revision-safe Undo.  The capture is a
    # read only context value consumed by run_trace.record_call after this
    # dispatcher returns.
    if name.startswith("desk_window.") and name.rsplit(".", 1)[-1] != "list":
        from holdspeak.services import run_trace

        run_trace.capture_window_before(name, arguments)
    with announce_scope() as announce, watch_writes() as wrote:
        result = _dispatch(name, arguments, principal)
        conductor_launch.after_call(name, arguments, result, principal)
        if wrote() and not is_read_tool(name):
            announce(*operations.changed_for(name, arguments, result))
    return result


#: The last name segment of a tool that only reads. A read may still write a
#: row of its own (a kernel read receipt, a cache), so a changed row alone does
#: not make a call a write. Any other tool that changed a row announces; a new
#: tool is a write until its verb is named here (a spare frame costs one
#: re-read; a silent write leaves a window stale).
READ_VERBS: frozenset[str] = frozenset({
    "list", "get", "status", "preview", "search", "history", "events",
    "list_members", "list_runs", "list_updates", "list_context", "loops",
    "get_loop", "get_delta", "get_room", "get_steward_run", "get_default_context",
    "destinations", "check_destination", "sends", "snapshot", "board",
    "needs_you", "observations", "page", "readiness", "suggested_sources",
    "evaluate", "inspect", "presets", "hub", "nudges", "shelf", "shelf_read",
    "resolve_grounding", "preview_use_default", "export", "proposals",
    "summary", "audit", "editor", "receipt", "detect", "probe", "results",
    # Betterment AG7: coder.explain reads why an agent has its state.
    "explain", "held",
    "confluence_connections", "confluence_discover", "confluence_validate_space",
    "github_connection", "github_discover", "github_validate_repo", "github_pr_get",
    "jira_connection", "jira_connections", "jira_discover", "jira_search",
    "jira_validate_scope",
})


def is_read_tool(name: str) -> bool:
    """True when the tool *name* only reads (its last segment is a read verb)."""
    return name.rsplit(".", 1)[-1] in READ_VERBS


def brief_arguments(args: dict[str, Any]) -> dict[str, Any]:
    _validate_tool_arguments("monday_brief.get", args)
    return args


def _dispatch(name: str, arguments: dict[str, Any] | None, principal: Principal) -> Any:
    """:func:`dispatch` without the announcement."""
    args = arguments or {}
    if not isinstance(args, dict):
        error = ToolError("arguments must be an object")
        error.kernel = refuse_before_invoke(name, arguments, principal, "invalid_arguments")  # type: ignore[attr-defined]
        raise error
    if _tool_schema(name) is None:
        raise ToolError(f"Unknown tool: {name}")
    retired_family_fields = {
        "ask.run": {"inference_target_id"},
    }
    if retired := (retired_family_fields.get(name, set()) & set(args)):
        raise ToolError(f"Invalid arguments for {name}: retired field(s): {', '.join(sorted(retired))}")
    _require_owner_before_schema(name, principal)
    from holdspeak.held_arguments import normalize_arguments
    args = normalize_arguments(_tool_schema(name), args)

    # Families preserve their established transport-specific validation and
    # refusal codes. S4's retired selector families reject those names before
    # composing a service; the owner twins above already deny before body read.
    # Main-catalogue tools have no family dispatcher, so their schemas are the
    # dispatch-time closure fence.
    for family in FAMILIES:
        if any(tool["name"] == name for tool in family.TOOLS):
            return family.dispatch(name, args, principal)

    try:
        _validate_tool_arguments(name, args)
    except ToolError as error:
        # The refusal receipt rides the error to the response (readback).
        error.kernel = refuse_before_invoke(name, args, principal, "invalid_arguments")  # type: ignore[attr-defined]
        raise
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
    follow_through = runtime_service("follow_through_service", lambda: FollowThroughService(db, observer=obs))
    recipes = RecipeService(db, observer=obs)
    events = EventQueryService(db)
    desk = DeskService(db, observer=obs)
    records = DecisionRecordService(db, observer=obs)
    def ops() -> operations.OperationRegistry:
        return runtime_registry(primitives, meetings)

    if name == "desk.list":
        return _primitive_list(ops, primitives, principal, _kind(args.get("kind")))
    if name == "desk.get":
        return _primitive_get(ops, primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""))
    if name == "desk.create":
        return _primitive_create(ops, primitives, principal, _kind(args.get("kind")), _data(args.get("data")))
    if name == "desk.update":
        return _primitive_update(ops, primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""), _data(args.get("data")))
    if name == "desk.delete":
        return _primitive_delete(ops, primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""), _data(args.get("data")))
    if name == "desk.verb":
        return _dispatch_verb(args, principal, primitives, workbenches, ops)
    if name == "automation.run":
        return _run(workbenches.run(principal, str(args.get("workbench_id") or "")))
    if name == "workbench.add_item":
        return workbenches.add_item(principal, str(args.get("workbench_id") or ""), title=str(args.get("title") or ""), **_data(args.get("data")))
    if name == "automation.list":
        return workbenches.list_workbenches(principal)
    if name == "automation.get":
        return workbenches.get_workbench(principal, str(args.get("workbench_id") or ""))
    if name == "automation.create":
        fields = _workbench_fields(args.get("fields"))
        if "name" in fields:
            raise ToolError("Workbench name belongs at the top level")
        if sentence := _sentence(args):
            return workbenches.create_automation(principal, name=str(args.get("name") or ""), sentence=sentence, **fields)
        return workbenches.create_workbench(principal, name=str(args.get("name") or ""), **fields)
    if name == "automation.update":
        fields = _workbench_fields(args.get("fields"))
        if sentence := _sentence(args):
            return workbenches.update_automation(principal, str(args.get("workbench_id") or ""), sentence=sentence, **fields)
        if "fields" not in args:
            raise ToolError("Give fields or at least one sentence word")
        return workbenches.update_workbench(principal, str(args.get("workbench_id") or ""), **fields)
    if name == "automation.delete":
        workbenches.delete_workbench(principal, str(args.get("workbench_id") or ""))
        return {"deleted": True, "id": str(args.get("workbench_id") or "")}
    if name == "workbench.update_item":
        return workbenches.update_item(principal, str(args.get("workbench_id") or ""), str(args.get("item_id") or ""), **_data(args.get("fields")))
    if name == "workbench.delete_item":
        item_id = str(args.get("item_id") or "")
        workbenches.delete_item(principal, str(args.get("workbench_id") or ""), item_id)
        return {"parked": True, "id": item_id}
    if name == "workbench.list_runs":
        return workbenches.list_runs(principal, str(args.get("workbench_id") or ""))
    if name == "automation.results":
        return workbenches.results(principal, str(args.get("workbench_id") or ""), limit=int(args.get("limit") or 1))
    if name == "automation.cancel":
        return workbenches.cancel_latest_run(principal, str(args.get("workbench_id") or ""), str(args.get("run_id") or ""))
    if name == "recipe.list":
        return recipes.list_recipes(principal)
    if name == "recipe.get":
        return recipes.get_recipe(principal, str(args.get("recipe_id") or ""))
    if name == "recipe.run":
        allowed = ("variables", "max_tokens", "temperature", "source_ref", "source_type", "grounding_refs", "grounding_revisions", "source_revision", "deadline_at", "initiator")
        options = _data(args.get("options"))
        return _run(recipes.run(principal, str(args.get("recipe_id") or ""), input=str(args.get("input") or ""), **{key: options[key] for key in allowed if key in options}))
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
        allowed = ("query", "from_date", "to_date", "limit", "cursor", "speaker", "tag", "has_open_actions", "parked")
        return ops().invoke(principal, "meeting.list", {key: args[key] for key in allowed if key in args})
    if name == "meeting.get":
        return ops().invoke(principal, "meeting.read", {"meeting_id": str(args.get("meeting_id") or ""), "include": args.get("include"), "include_parked": args.get("include_parked")})
    if name == "meeting.import":
        return _meeting_import(ops(), meetings, principal, args)
    if name == "meeting.transcribe":
        from holdspeak.config import Config
        return ops().invoke(principal, "meeting.transcribe", {"meeting_id": str(args.get("meeting_id") or "")}, held={
            "config": Config.load(),
            "transcriber_factory": meeting_transcriber.frozen_transcriber_factory,
        })
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
        return {"parked": True, "id": meeting_id}
    if name == "meeting.export":
        return meetings.export_meeting(principal, str(args.get("meeting_id") or ""), str(args.get("format") or ""))
    if name == "desk.snapshot":
        return desk.snapshot(principal)
    if name == "desk.needs_you":
        # PHILO-9-01 (F13): the declared operation, the same one the HTTP
        # route reaches: one aggregate, the heartbeat's muted projects applied,
        # one count. The hub's calendar read (the Door's upcoming meetings) is
        # held by the transport, as the route holds it.
        door = runtime_service("door_service", lambda: None)
        # The one rule, the one count. People commitments are members and are
        # counted; their text never leaves the People custody boundary: the
        # operation itself withholds it (its result is observed), before any
        # transport sees it.
        filters = {key: args[key] for key in ("direction", "person", "project", "week")
                   if args.get(key) not in (None, "")}
        return ops().invoke(
            principal, "desk.needs_you", filters,
            held={"door_upcoming": getattr(door, "upcoming", None) if door else None})
    if name == "today.get":
        result = ops().invoke(principal, "today.get", {})
        if result.get("since_yesterday") is not None:
            result["since_yesterday"] = _compose_brief_overlay_mcp(result["since_yesterday"], db, principal)
        return result
    if name == "meeting.run_intelligence":
        return ops().invoke(principal, "meeting.summary.run", {
            "meeting_id": str(args.get("meeting_id") or ""),
            "expected_selection_hash": str(args.get("expected_selection_hash") or ""),
        })
    if name == "meeting.proposals":
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS
        pbs = _PBS(db)
        return {"proposals": pbs.list_meeting_proposals(str(args.get("meeting_id") or ""), state=args.get("state"))}
    # HS-173-04: reviewer nudge MCP twins. PHILO-9-02 (F9): the declared
    # steward.nudges / nudge.send / nudge.dismiss, bound to the HUB's steward
    # service with its real collaborators (they built one over MagicMock
    # collaborators here); nudge.send is admitted (egress) with its receipt.
    if name in {"steward.nudges", "nudge.send", "nudge.dismiss"}:
        from holdspeak.mcp.families.project import _room_tool

        return _room_tool(name, args, principal)
    if name == "decision_record.list":
        program_id = str(args.get("program_id") or "").strip()
        if program_id:  # PG16: the records a Program proposed
            rows = [row for row in records.records_for_work(principal, "program", program_id) if not row.get("deleted")]
            offset = max(0, int(args.get("offset") or 0))
            return rows[offset:offset + max(1, min(int(args.get("limit") or 50), 500))]
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
            args = ScheduledRecordingService.command_arguments(args, create=True)
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
            args = ScheduledRecordingService.command_arguments(args, create=False)
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


_DESK_SERVER_VERBS: dict[str, Callable[..., Any]] = {
        "desk.create": lambda value, principal, primitives, workbenches, ops: _primitive_create(ops, primitives, principal, _kind(value.get("kind")), _data(value.get("data"))),
        "desk.update": lambda value, principal, primitives, workbenches, ops: _primitive_update(ops, primitives, principal, _kind(value.get("kind")), str(value.get("id") or ""), _data(value.get("data"))),
        "desk.delete": lambda value, principal, primitives, workbenches, ops: _primitive_delete(ops, primitives, principal, _kind(value.get("kind")), str(value.get("id") or ""), _data(value.get("data"))),
        "workbench.add_item": lambda value, principal, primitives, workbenches, ops: workbenches.add_item(principal, str(value.get("workbench_id") or ""), title=str(value.get("title") or ""), **_data(value.get("data"))),
        "workbench.run": lambda value, principal, primitives, workbenches, ops: _run(workbenches.run(principal, str(value.get("workbench_id") or ""))),
    }


def desk_verb_arguments(args: dict[str, Any]) -> dict[str, Any]:
    verb_id = str(args.get("verb_id") or "")
    payload = _data(args.get("arguments"))
    ui_only = verb_id in _UI_ONLY_VERBS or verb_id.startswith(("go.", "window.", "system."))
    if not ui_only and verb_id not in _DESK_SERVER_VERBS:
        raise ToolError(f"Verb is not allowlisted for MCP: {verb_id}")
    return {**args, "verb_id": verb_id, "arguments": payload}


def held_desk_verb(args: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    """The same existing handler table selects the inner declaration."""
    prepared = desk_verb_arguments(args)
    verb = prepared["verb_id"]
    if verb not in _DESK_SERVER_VERBS:
        return None, prepared["arguments"]
    return ("automation.run" if verb == "workbench.run" else verb), prepared["arguments"]


def _dispatch_verb(args: dict[str, Any], principal: Principal, primitives: PrimitiveService, workbenches: WorkbenchService, ops: Callable[[], operations.OperationRegistry]) -> Any:
    prepared = desk_verb_arguments(args)
    verb_id = prepared["verb_id"]
    if verb_id not in _DESK_SERVER_VERBS:
        return {"status": "ui_only", "verb_id": verb_id, "reason": "Opens a local surface"}
    return _DESK_SERVER_VERBS[verb_id](prepared["arguments"], principal, primitives, workbenches, ops)


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
    *,
    call_gate: Any = None,
) -> Any:
    """Dispatch scoped by *palette* -- typed refusal for tools outside it.

    ``call_gate(name, arguments) -> bool`` (Conductor K6) refuses one call of a
    palette tool on its arguments, the same way (a mixed tool that would
    schedule or delegate)."""
    outside = name not in palette
    if not outside and call_gate is not None and not call_gate(name, arguments):
        outside = True
    if outside:
        # PHILO-7-02: the palette refusal of a tool that names an ADMITTED
        # operation leaves a refusal receipt (a read or exempt tool: none).
        error = ToolError(f"Tool {name!r} is not in the configured palette")
        error.kernel = refuse_before_invoke(name, arguments, principal, _PALETTE_REFUSED)  # type: ignore[attr-defined]
        raise error
    return dispatch(name, arguments, principal)
