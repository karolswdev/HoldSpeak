"""MCP resources for read-oriented HoldSpeak desk context."""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from holdspeak.db import get_database
from holdspeak.mcp.families import people as people_family
from holdspeak.mcp.families import thought as thought_family
from holdspeak.principals import Principal
from holdspeak.config import Config
from holdspeak.services.cadence_service import CadenceService
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.desk_service import DeskService
from holdspeak.services.dictation_service import DictationService
from holdspeak.services.event_query_service import EventQueryService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.recipe_service import RecipeService
from holdspeak.services.refinement_application_service import RefinementApplicationService
from holdspeak.services.refinement_thought_service import RefinementThoughtService
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.services.inference_capability_service import InferenceCapabilityApplicationService
from holdspeak.inference_capabilities import process_inference_capability_registry
from holdspeak.services.errors import ServiceError
from holdspeak.principals import PrincipalKind

_JSON_MIME = "application/json"
_TEXT_MIME = "text/markdown"
_REPO_ROOT = Path(__file__).resolve().parents[2]

# These descriptors mirror web/src/lib/primitives.ts. They intentionally include
# every Desk kind, including remote and local-only kinds, so MCP clients can
# reason about the entire Desk rather than only the CRUD subset.
_PRIMITIVE_SCHEMA = [
    {"kind": "meeting", "product_noun": "Meeting", "sync_class": "content"},
    {"kind": "artifact", "product_noun": "Artifact", "sync_class": "content"},
    {"kind": "note", "product_noun": "Note", "sync_class": "content"},
    {"kind": "decision", "product_noun": "Decision", "sync_class": "content"},
    {"kind": "directory", "product_noun": "Zone", "sync_class": "organization"},
    {"kind": "kb", "product_noun": "Knowledge", "sync_class": "organization"},
    {"kind": "project", "product_noun": "Project", "sync_class": "organization"},
    {"kind": "repository", "product_noun": "Repository", "sync_class": "organization"},
    {"kind": "recipe", "product_noun": "Agent", "sync_class": "capability"},
    {"kind": "chain", "product_noun": "Sequence", "sync_class": "capability"},
    {"kind": "workflow", "product_noun": "Workflow", "sync_class": "capability"},
    {"kind": "coder", "product_noun": "Coder session", "sync_class": "presence"},
    {"kind": "game", "product_noun": "Game", "sync_class": "local"},
    {"kind": "roadmap", "product_noun": "Roadmap", "sync_class": "organization"},
    {"kind": "story", "product_noun": "Story", "sync_class": "local"},
    {"kind": "workbench", "product_noun": "Workbench", "sync_class": "capability"},
    {"kind": "layout", "product_noun": "Layout", "sync_class": "local"},
    {"kind": "people", "product_noun": "People", "sync_class": "local"},
]

# Mirrors web/src/desk/verbRegistry.ts, including verbs derived from DESK_TOOLS.
# ``server`` means the external MCP verb dispatcher can invoke it; all other
# registered Desk verbs remain UI-owned presentation actions.
_VERBS = [
    ("desk.new-note", "New Note", "floor", "⌘N"),
    ("desk.new-decision", "New Decision", "floor", "⌘⇧N"),
    ("desk.new-knowledge", "New Knowledge", "floor", None),
    ("desk.new-agent", "New Agent", "floor", None),
    ("desk.new-workflow", "New Workflow", "floor", None),
    ("desk.new-workbench", "New Workbench", "floor", None),
    ("desk.new-zone", "New Zone", "floor", None),
    ("desk.toggle-view", "Spatial view / List view", "floor", None),
    ("desk.arrange", "Arrange desk", "floor", None),
    ("desk.overview", "Overview", "floor", "⌃↑"),
    ("desk.reset-layout", "Reset layout", "floor", None),
    ("desk.reset-to-seed", "Reset to seed…", "floor", None),
    ("desk.refresh", "Refresh from hub", "floor", None),
    ("object.open", "Open", "object", None),
    ("object.info", "Get Info", "object", None),
    ("object.ask-project", "Ask this project", "object", None),
    ("object.ask", "Ask AI", "object", None),
    ("object.edit", "Edit", "object", None),
    ("object.rename", "Rename", "object", "F2"),
    ("object.duplicate", "Duplicate", "object", None),
    ("object.file", "Move to Zone", "object", None),
    ("object.delete", "Delete", "object", "Delete"),
    ("zone.focus", "Focus", "object", None),
    ("go.dictate", "Speak", "go", "⌘1"),
    ("go.ask", "Ask AI", "go", "⌘I"),
    ("go.review-meetings", "Meetings", "go", "⌘2"),
    ("go.configure-settings", "Settings", "go", "⌘4"),
    ("go.open-workbenches", "Workbenches", "go", None),
    ("go.inspect-personas-and-coders", "Agents and coder sessions", "go", "⌘3"),
    ("go.configure-runs-on", "Runs on", "go", None),
    ("go.configure-integrations", "Integrations", "go", None),
    ("go.configure-commands", "Commands", "go", None),
    ("go.configure-cadence", "Cadence", "go", None),
    ("go.open-constitutional-context", "Context", "go", None),
    ("go.inspect-activity", "Activity", "go", None),
    ("go.inspect-processes", "Processes", "go", None),
    ("window.close", "Close window", "window", "⌘W"),
    ("window.minimize", "Minimize window", "window", "⌘M"),
    ("window.cycle", "Cycle windows", "window", "⌃`"),
    ("window.cycle-reverse", "Cycle Windows (Reverse)", "window", "⌃⇧`"),
    ("window.snap-left", "Snap Left", "window", None),
    ("window.snap-right", "Snap Right", "window", None),
    ("window.maximize", "Maximize", "window", None),
    ("system.search", "Search", "system", "⌘K"),
    ("system.sheet", "Keyboard shortcuts", "system", "⌘/"),
]
_SERVER_VERBS = [
    ("desk.create", "Create primitive", "server", None),
    ("desk.update", "Update primitive", "server", None),
    ("desk.delete", "Delete primitive", "server", None),
    ("workbench.add_item", "Add workbench item", "server", None),
    ("workbench.run", "Run workbench", "server", None),
]
_VERB_CATALOG = [
    {
        "id": verb_id,
        "label": label,
        "scope": scope,
        "key_binding": key,
        "designation": designation,
    }
    for verb_id, label, scope, key, designation in (
        [(verb_id, label, scope, key, "ui_only") for verb_id, label, scope, key in _VERBS]
        + [(verb_id, label, scope, key, "server") for verb_id, label, scope, key in _SERVER_VERBS]
    )
]

_STATIC_RESOURCES = [
    {
        "uri": "holdspeak://desk/schema",
        "name": "Desk primitive schema",
        "description": "Primitive kinds, product nouns, and synchronization classes.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://desk/verbs",
        "name": "Desk verb catalog",
        "description": "Registered Desk verbs, scopes, key bindings, and MCP designation.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://desk/constitution",
        "name": "HoldSpeak Constitution",
        "description": "The project’s constitutional context.",
        "mimeType": _TEXT_MIME,
    },
    {
        "uri": "holdspeak://inference/capabilities",
        "name": "Inference capabilities",
        "description": "Owner-only registered intelligence jobs and their exact compatibility requirements.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://desk/snapshot",
        "name": "Desk snapshot",
        "description": "Canonical current Desk state, including its stored objects and layout.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://workbenches",
        "name": "Workbenches",
        "description": "Canonical list of available workbenches and their current summaries.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://recipes",
        "name": "Recipes",
        "description": "Canonical list of agent recipes available on the Desk.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://dictation/journal",
        "name": "Dictation journal",
        "description": "Canonical journal of stored dictation entries.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://follow-through/board",
        "name": "Follow-Through board",
        "description": "Canonical current Follow-Through execution lanes and card provenance.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://briefs/latest",
        "name": "Latest Monday Brief",
        "description": "Latest persisted Monday Brief, or null when none has been generated.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "pipeline://events/recent",
        "name": "Recent pipeline events",
        "description": "Most recent observed pipeline events.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "pipeline://events/stats",
        "name": "Pipeline event statistics",
        "description": "Aggregate statistics for observed pipeline events.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://cadence/status",
        "name": "Cadence engine status",
        "description": "Cadence engine status: enabled, pressure, loop counts, policy count.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://people/readiness",
        "name": "People MCP readiness",
        "description": "Content-free People capability and encrypted-store readiness.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://people/relationships",
        "name": "People relationships",
        "description": "Active relationship metadata; explicit People MCP read capability required.",
        "mimeType": _JSON_MIME,
    },
    {
        "uri": "holdspeak://thoughts/unfinished",
        "name": "Unfinished thoughts",
        "description": "Bounded owner Resume projection for unfinished Thoughts.",
        "mimeType": _JSON_MIME,
    },
]

_RESOURCE_TEMPLATES = [
    {
        "uriTemplate": "holdspeak://primitives/{kind}/{id}",
        "name": "Primitive detail",
        "description": "One stored desk primitive by kind and identifier.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://workbenches/{id}",
        "name": "Workbench detail",
        "description": "One workbench, including its item and run summary.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://workbenches/{id}/runs",
        "name": "Workbench runs",
        "description": "Canonical run history for one workbench.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://recipes/{id}",
        "name": "Recipe detail",
        "description": "Canonical stored definition for one agent recipe.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://zones/{id}/members",
        "name": "Zone members",
        "description": "Canonical directory members for one Desk zone.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://meetings/{id}",
        "name": "Meeting detail",
        "description": "One archived meeting and its stored detail.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://decision-records/{id}",
        "name": "Decision record detail",
        "description": "One durable decision record with its evidence and revision trail.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "pipeline://events/recent/{service}",
        "name": "Recent pipeline events by service",
        "description": "Most recent observed pipeline events for one service.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "pipeline://events/correlation/{id}",
        "name": "Pipeline events by correlation",
        "description": "All observed pipeline events in one correlation chain.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://people/relationships/{id}",
        "name": "People relationship detail",
        "description": "One relationship with shared-intent records only; leader-private material is excluded.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://thoughts/{thought_id}/workbench",
        "name": "Thought Workbench",
        "description": "One coherent owner-only Thought Workbench projection.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://thoughts/{thought_id}/original",
        "name": "Thought Original",
        "description": "The immutable original capture for one owner Thought.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://thoughts/{thought_id}",
        "name": "Thought detail",
        "description": "One canonical Thought with its working Note and public continuity.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://thoughts/{thought_id}/reviews/{review_result_id}",
        "name": "Thought review",
        "description": "One validated receipt-gated review card with frozen cursors and egress receipt.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://inference/acquisitions/{id}",
        "name": "Model acquisition",
        "description": "Owner-only durable download, verification, installation, and activation truth.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://inference/capabilities/{capability_id}",
        "name": "Inference capability detail",
        "description": "Owner-only exact contract for one registered intelligence capability.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://projects/{project_id}",
        "name": "Project identity",
        "description": "One project identity and room fields.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://projects/{project_id}/room",
        "name": "Project room",
        "description": "Coherent room projection for one project.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://projects/{project_id}/delta",
        "name": "Project delta",
        "description": "Current delta window or honest empty state for one project.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://projects/{project_id}/updates/{update_id}",
        "name": "Project update",
        "description": "One project update by identifier.",
        "mimeType": _JSON_MIME,
    },
    {
        "uriTemplate": "holdspeak://projects/{project_id}/steward/runs/{run_id}",
        "name": "Steward run",
        "description": "Pollable steward run state with phase and steps.",
        "mimeType": _JSON_MIME,
    },
]

_PRIMITIVE_KIND_ALIASES = {
    "notes": "note", "note": "note",
    "decisions": "decision", "decision": "decision",
    "kbs": "kb", "kb": "kb",
    "directories": "directory", "directory": "directory",
    "workflows": "workflow", "workflow": "workflow",
    "chains": "chain", "chain": "chain",
}
_PRIMITIVE_DETAIL_PATTERN = re.compile(r"^holdspeak://primitives/([^/]+)/([^/]+)$")
_WORKBENCH_DETAIL_PATTERN = re.compile(r"^holdspeak://workbenches/([^/]+)$")
_WORKBENCH_RUNS_PATTERN = re.compile(r"^holdspeak://workbenches/([^/]+)/runs$")
_RECIPE_DETAIL_PATTERN = re.compile(r"^holdspeak://recipes/([^/]+)$")
_ZONE_MEMBERS_PATTERN = re.compile(r"^holdspeak://zones/([^/]+)/members$")
_MEETING_DETAIL_PATTERN = re.compile(r"^holdspeak://meetings/([^/]+)$")
_DECISION_RECORD_PATTERN = re.compile(r"^holdspeak://decision-records/([^/]+)$")
_PIPELINE_RECENT_SERVICE_PATTERN = re.compile(r"^pipeline://events/recent/([^/]+)$")
_PIPELINE_CORRELATION_PATTERN = re.compile(r"^pipeline://events/correlation/([^/]+)$")
_PEOPLE_RELATIONSHIP_PATTERN = re.compile(r"^holdspeak://people/relationships/([^/]+)$")
_THOUGHT_DETAIL_PATTERN = re.compile(r"^holdspeak://thoughts/([^/]+)$")
_THOUGHT_WORKBENCH_PATTERN = re.compile(r"^holdspeak://thoughts/([^/]+)/workbench$")
_THOUGHT_ORIGINAL_PATTERN = re.compile(r"^holdspeak://thoughts/([^/]+)/original$")
_THOUGHT_REVIEW_PATTERN = re.compile(
    r"^holdspeak://thoughts/([^/]+)/reviews/([^/]+)$"
)
_INFERENCE_ACQUISITION_PATTERN = re.compile(
    r"^holdspeak://inference/acquisitions/([^/]+)$"
)
_INFERENCE_CAPABILITY_PATTERN = re.compile(
    r"^holdspeak://inference/capabilities/([^/]+)$"
)
_PROJECT_DETAIL_PATTERN = re.compile(r"^holdspeak://projects/([^/]+)$")
_PROJECT_ROOM_PATTERN = re.compile(r"^holdspeak://projects/([^/]+)/room$")
_PROJECT_DELTA_PATTERN = re.compile(r"^holdspeak://projects/([^/]+)/delta$")
_PROJECT_UPDATE_PATTERN = re.compile(
    r"^holdspeak://projects/([^/]+)/updates/([^/]+)$"
)
_PROJECT_STEWARD_RUN_PATTERN = re.compile(
    r"^holdspeak://projects/([^/]+)/steward/runs/([^/]+)$"
)


class ResourceError(ValueError):
    """A resource failure that is safe to surface through JSON-RPC."""


def list_resources(principal: Principal | None = None) -> dict[str, list[dict[str, Any]]]:
    """Return the static resources and parameterized resource templates."""
    resources = _STATIC_RESOURCES
    if principal is None or principal.kind is not PrincipalKind.OWNER:
        resources = [
            row
            for row in resources
            if row["uri"] not in {
                "holdspeak://inference/capabilities",
            }
        ]
        templates = [
            row
            for row in _RESOURCE_TEMPLATES
            if "inference/acquisitions" not in row["uriTemplate"]
            and "inference/capabilities" not in row["uriTemplate"]
        ]
    else:
        templates = _RESOURCE_TEMPLATES
    return {"resources": resources, "resourceTemplates": templates}


def _contents(uri: str, mime_type: str, value: Any) -> dict[str, list[dict[str, str]]]:
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, default=str)
    return {"contents": [{"uri": uri, "mimeType": mime_type, "text": text}]}


def read_resource(uri: str, principal: Principal | None) -> dict[str, list[dict[str, str]]]:
    """Read one static or templated resource as MCP resource contents."""
    if principal is None:
        raise ServiceError(
            "mcp_resource_principal_required",
            "An authenticated principal is required.",
            context={"status": 401},
        )
    if uri == "holdspeak://desk/schema":
        return _contents(uri, _JSON_MIME, {"kinds": _PRIMITIVE_SCHEMA})
    if uri == "holdspeak://desk/verbs":
        return _contents(uri, _JSON_MIME, {"verbs": _VERB_CATALOG})
    if uri == "holdspeak://desk/constitution":
        try:
            text = (_REPO_ROOT / "docs/internal/CONSTITUTION.md").read_text(encoding="utf-8")
        except OSError as exc:
            raise ResourceError(f"Constitution unavailable: {exc}") from exc
        return _contents(uri, _TEXT_MIME, text)
    if uri == "holdspeak://inference/capabilities":
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "inference_capability_owner_required",
                "Owner access is required.",
                context={"status": 403},
            )
        service = InferenceCapabilityApplicationService(process_inference_capability_registry())
        return _contents(uri, _JSON_MIME, {"capabilities": service.get_capabilities(principal)})
    if match := _INFERENCE_CAPABILITY_PATTERN.fullmatch(uri):
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "inference_capability_owner_required",
                "Owner access is required.",
                context={"status": 403},
            )
        service = InferenceCapabilityApplicationService(process_inference_capability_registry())
        return _contents(
            uri,
            _JSON_MIME,
            {"capability": service.get_capability(principal, match.group(1))},
        )
    if match := _INFERENCE_ACQUISITION_PATTERN.fullmatch(uri):
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "inference_setup_owner_required", "Owner access is required.",
                context={"status": 403},
            )
        db = get_database()
        setup = InferenceSetupApplicationService(db)
        from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService

        value = InferenceAcquisitionApplicationService(
            db, setup_service=setup, auto_recover=False,
        ).get_acquisition(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if uri == "holdspeak://desk/snapshot":
        return _contents(uri, _JSON_MIME, DeskService(get_database()).snapshot(principal))
    if uri == "holdspeak://workbenches":
        return _contents(uri, _JSON_MIME, WorkbenchService(get_database()).list_workbenches(principal)[:100])
    if uri == "holdspeak://recipes":
        return _contents(uri, _JSON_MIME, RecipeService(get_database()).list_recipes(principal)[:100])
    if uri == "holdspeak://dictation/journal":
        return _contents(uri, _JSON_MIME, DictationService(get_database()).list_journal(principal, limit=100))
    if uri == "holdspeak://follow-through/board":
        board = FollowThroughService(get_database()).board(principal)
        return _contents(uri, _JSON_MIME, {
            "now": [asdict(card) for card in board.now],
            "waiting": [asdict(card) for card in board.waiting],
            "unassigned": [asdict(card) for card in board.unassigned],
            "overdue": [asdict(card) for card in board.overdue],
        })
    if uri == "holdspeak://briefs/latest":
        brief = MondayBriefService(get_database()).get_latest(principal)
        return _contents(uri, _JSON_MIME, asdict(brief) if brief is not None else None)
    if uri == "pipeline://events/recent":
        return _contents(uri, _JSON_MIME, EventQueryService(get_database()).recent(principal))
    if uri == "pipeline://events/stats":
        return _contents(uri, _JSON_MIME, EventQueryService(get_database()).stats(principal))
    if uri == "holdspeak://cadence/status":
        return _contents(uri, _JSON_MIME, CadenceService(get_database(), Config.load().cadence).status(principal))
    if uri == "holdspeak://people/readiness":
        return _contents(uri, _JSON_MIME, people_family.readiness(principal))
    if uri == "holdspeak://people/relationships":
        return _contents(uri, _JSON_MIME, people_family.list_relationships(principal))
    if uri == "holdspeak://thoughts/unfinished":
        value = RefinementThoughtService(get_database()).list_unfinished(
            principal, limit=50
        )
        return _contents(uri, _JSON_MIME, value)

    if match := _THOUGHT_WORKBENCH_PATTERN.fullmatch(uri):
        runtime = thought_family._runtime
        value = RefinementApplicationService(
            get_database(), coordinator=runtime.coordinator if runtime else None
        ).get_workbench(principal, thought_id=match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _THOUGHT_ORIGINAL_PATTERN.fullmatch(uri):
        value = RefinementApplicationService(
            get_database(), coordinator=None
        ).get_original(principal, thought_id=match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _THOUGHT_REVIEW_PATTERN.fullmatch(uri):
        value = RefinementApplicationService(
            get_database(), coordinator=None
        ).review(
            principal,
            thought_id=match.group(1),
            review_result_id=match.group(2),
        )
        return _contents(uri, _JSON_MIME, value)
    if match := _THOUGHT_DETAIL_PATTERN.fullmatch(uri):
        value = RefinementThoughtService(get_database()).get(
            principal, match.group(1)
        )
        return _contents(uri, _JSON_MIME, {"thought": value})
    if match := _PRIMITIVE_DETAIL_PATTERN.fullmatch(uri):
        kind = _PRIMITIVE_KIND_ALIASES.get(match.group(1))
        if kind is None:
            raise ResourceError(f"Unsupported primitive kind: {match.group(1)}")
        value = getattr(PrimitiveService(get_database()), f"get_{kind}")(principal, match.group(2))
        return _contents(uri, _JSON_MIME, value)
    if match := _WORKBENCH_RUNS_PATTERN.fullmatch(uri):
        value = WorkbenchService(get_database()).list_runs(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _WORKBENCH_DETAIL_PATTERN.fullmatch(uri):
        value = WorkbenchService(get_database()).get_workbench(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _RECIPE_DETAIL_PATTERN.fullmatch(uri):
        value = RecipeService(get_database()).get_recipe(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _ZONE_MEMBERS_PATTERN.fullmatch(uri):
        value = PrimitiveService(get_database()).list_directory_members(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _MEETING_DETAIL_PATTERN.fullmatch(uri):
        value = MeetingService(get_database()).get_meeting(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _DECISION_RECORD_PATTERN.fullmatch(uri):
        value = DecisionRecordService(get_database()).get(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _PIPELINE_RECENT_SERVICE_PATTERN.fullmatch(uri):
        value = EventQueryService(get_database()).recent(principal, service=match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _PIPELINE_CORRELATION_PATTERN.fullmatch(uri):
        value = EventQueryService(get_database()).by_correlation(principal, correlation_id=match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _PEOPLE_RELATIONSHIP_PATTERN.fullmatch(uri):
        value = people_family.get_relationship(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    # ── Project Room resources (SS11.2) ──────────────────────────────
    if match := _PROJECT_STEWARD_RUN_PATTERN.fullmatch(uri):
        # Must precede _PROJECT_DETAIL_PATTERN (longer path wins).
        _project_id, run_id = match.group(1), match.group(2)
        db = get_database()
        run = db.steward_runs.get_run(run_id)
        if run is None:
            raise ServiceError(
                "steward_run_not_found",
                f"Unknown steward run: {run_id}",
                context={"status": 404},
            )
        steps = db.steward_steps.list_steps(run_id)
        from holdspeak.web.routes.steward import _serialize_run, _serialize_steps
        return _contents(uri, _JSON_MIME, {
            "run": _serialize_run(run),
            "steps": _serialize_steps(steps),
        })
    if match := _PROJECT_UPDATE_PATTERN.fullmatch(uri):
        _project_id, update_id = match.group(1), match.group(2)
        from holdspeak.services.project_update_service import ProjectUpdateService
        svc = ProjectUpdateService(get_database())
        value = svc.get_update(principal, update_id)
        return _contents(uri, _JSON_MIME, value)
    if match := _PROJECT_ROOM_PATTERN.fullmatch(uri):
        from holdspeak.services.project_service import ProjectService
        value = ProjectService(get_database()).room(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    if match := _PROJECT_DELTA_PATTERN.fullmatch(uri):
        project_id = match.group(1)
        from holdspeak.services.project_service import ProjectService as _PS
        from holdspeak.services.project_delta_service import ProjectDeltaService
        db = get_database()
        ps = _PS(db)
        ps._require_project(project_id)
        # collector=None is safe: _find_open_review and _load_frozen_window
        # are read-only queries that do not use the collector.
        delta_svc = ProjectDeltaService(db, collector=None)
        open_review = delta_svc._find_open_review(project_id)
        if open_review is not None:
            window = delta_svc._load_frozen_window(open_review)
            return _contents(uri, _JSON_MIME, window)
        room_fields = db.projects.get_project_room_fields(project_id)
        last_accepted_at = (room_fields or {}).get("last_review_at")
        return _contents(uri, _JSON_MIME, {
            "open_review": None,
            "last_accepted_at": last_accepted_at,
        })
    if match := _PROJECT_DETAIL_PATTERN.fullmatch(uri):
        from holdspeak.services.project_service import ProjectService
        value = ProjectService(get_database()).get_project(principal, match.group(1))
        return _contents(uri, _JSON_MIME, value)
    raise ResourceError(f"Unknown resource: {uri}")
