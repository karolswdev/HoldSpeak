"""Project Room MCP twin: read + command tools over ProjectService (MCP-001 parity).

HS-165-01: read tools (project.list / get / get_room).
HS-165-02: command tools — the same verbs, the same laws.  Every command
tool is a THIN driver over the exact service seam the Web route calls:
no SQL, no verb re-implementation.  command_id replay safety (MCP-002)
rides the services' own idempotency machinery.
HS-165-03: driver tools — steward, setup, providers, watch graduation.
HS-165-04: PROJECT_PALETTE — the scoped allow-list for agent sessions.
"""
from __future__ import annotations

from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service

import hashlib
import json
import sqlite3
import threading
from typing import Any

from holdspeak.db import get_database
from holdspeak.db.updates import PublishedUpdateError
from holdspeak.principals import Principal
from holdspeak.services.errors import ConflictError, NotFound, ServiceError, ValidationError

# HS-165-03: graduated watch boundary — these states belong to the
# graduated WatchSpec@1 machinery (project.watch.* tools).  Legacy
# rows (state='') belong to the reactions family (watch.*/reaction.*).
_GRADUATED_WATCH_STATES = frozenset({"active", "tested", "paused", "retired"})


# ── Tool schemas ─────────────────────────────────────────────────────

TOOLS: list[dict[str, Any]] = [
    # ── reads (HS-165-01) ────────────────────────────────────────────
    {
        "name": "project.list",
        "description": "List all projects. Optionally include archived projects.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.list@1",
            "type": "object",
            "properties": {
                "include_archived": {
                    "type": "boolean",
                    "description": "Include archived projects (default false).",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.get",
        "description": "Get one project by id.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.get@1",
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.get_room",
        "description": "Get the coherent room projection for one project (identity, items, meetings, resources, changes, review, needsYou, sources, health, sinceRead, decisions, commitments, target).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.get_room@1",
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    # ── commands (HS-165-02) ─────────────────────────────────────────
    {
        "name": "project.create",
        "description": "Create a new project. Returns the created project with command envelope.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.create@1",
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name (required)."},
                "description": {"type": "string", "description": "Project description."},
                "keywords": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Keyword strings.",
                },
                "team_members": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Team member strings.",
                },
                "context": {"type": "object", "description": "Arbitrary context object."},
                "detection_threshold": {
                    "type": "number",
                    "description": "Detection threshold (0.0-1.0, default 0.4).",
                },
                "command_id": {
                    "type": "string",
                    "description": "Caller-supplied idempotency key. Generated if absent; always returned.",
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.update",
        "description": "Patch a project's fields. Accepts expected_revision for optimistic concurrency.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.update@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "patch": {
                    "type": "object",
                    "description": "Fields to update (name, description, keywords, lifecycle, purpose, etc.).",
                },
                "expected_revision": {
                    "type": "integer",
                    "description": "Optimistic concurrency guard. Refuses stale typed if mismatched.",
                },
                "command_id": {
                    "type": "string",
                    "description": "Caller-supplied idempotency key.",
                },
            },
            "required": ["project_id", "patch"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.archive",
        "description": "Archive a project (soft-delete). Accepts expected_revision.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.archive@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "expected_revision": {
                    "type": "integer",
                    "description": "Optimistic concurrency guard.",
                },
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.restore",
        "description": "Restore an archived project. Accepts expected_revision.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.restore@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "expected_revision": {
                    "type": "integer",
                    "description": "Optimistic concurrency guard.",
                },
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.link",
        "description": "Associate a meeting with a project. Accepts expected_revision.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.link@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "meeting_id": {"type": "string", "description": "Meeting identifier."},
                "expected_revision": {
                    "type": "integer",
                    "description": "Optimistic concurrency guard.",
                },
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id", "meeting_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.unlink",
        "description": "Disassociate a meeting from a project. Accepts expected_revision.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.unlink@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "meeting_id": {"type": "string", "description": "Meeting identifier."},
                "expected_revision": {
                    "type": "integer",
                    "description": "Optimistic concurrency guard.",
                },
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id", "meeting_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.open_review",
        "description": "Open a deterministic review window for a project. Returns the review (proposals, source manifest). One-open-review law: if already open, returns the existing review.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.open_review@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.get_delta",
        "description": "Get the open review window or the honest empty state for a project.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.get_delta@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.decide_proposal",
        "description": "Apply a decision verb (accept/edit_accept/defer/dismiss) to a review proposal.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.decide_proposal@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "review_id": {"type": "string", "description": "Review window identifier."},
                "proposal_id": {"type": "string", "description": "Proposal identifier."},
                "verb": {
                    "type": "string",
                    "description": "Decision verb: accept, edit_accept, defer, or dismiss.",
                },
                "patch": {
                    "type": "object",
                    "description": "Optional patch for edit_accept verb.",
                },
                "deferred_until": {
                    "type": "string",
                    "description": "ISO-8601 date for defer verb.",
                },
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id", "review_id", "proposal_id", "verb"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.accept_review",
        "description": "Atomically accept an open review. Bumps project revision, supersedes undecided proposals.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.accept_review@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "review_id": {"type": "string", "description": "Review window identifier."},
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id", "review_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.list_updates",
        "description": "List updates for a project, optionally filtered by lifecycle (draft/published/superseded).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.list_updates@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "lifecycle": {
                    "type": "string",
                    "description": "Filter by lifecycle: draft, published, or superseded.",
                },
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.draft_update",
        "description": "Draft a project update using the deterministic or model generator.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.draft_update@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "generator": {
                    "type": "string",
                    "description": "Generator: 'deterministic' (default) or 'model'.",
                },
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.update_draft",
        "description": "Save the owner's edit of a draft update (body_md). Refuses published updates.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.update_draft@1",
            "type": "object",
            "properties": {
                "update_id": {"type": "string", "description": "Update identifier."},
                "body_md": {"type": "string", "description": "New Markdown body."},
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["update_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.publish_update",
        "description": "Publish a draft update. One transaction: lifecycle -> published + project revision law.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.publish_update@1",
            "type": "object",
            "properties": {
                "update_id": {"type": "string", "description": "Update identifier."},
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["update_id"],
            "additionalProperties": False,
        },
    },
    # ── PHILO-9-01: items and resources (the charter's table) ────────
    {
        "name": "project.item.list",
        "description": "",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.item.list@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "item_type": {"type": "string", "enum": ["milestone", "risk", "dependency", "signal", "workstream"]},
                "limit": {"type": "integer"},
                "offset": {"type": "integer", "minimum": 0},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.item.create",
        "description": "",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.item.create@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "item_type": {"type": "string", "enum": ["milestone", "risk", "dependency", "signal", "workstream"]},
                "title": {"type": "string", "minLength": 1},
                "summary": {"type": ["string", "null"]},
                "severity": {"type": ["string", "null"], "enum": ["critical", "high", "medium", "low", None]},
                "owner_ref": {"type": ["string", "null"]},
                "due_at": {"type": ["string", "null"]},
                "sort_key": {"type": ["number", "null"]},
                "lifecycle": {"type": "string", "enum": [
                    "planned", "reached", "missed", "dropped", "open", "mitigated", "accepted", "closed",
                    "healthy", "at_risk", "broken", "resolved", "active", "retired", "paused", "done"]},
                "details": {"type": ["object", "null"]},
                "expected_revision": {"type": "integer"},
                "command_id": {"type": "string"},
            },
            "required": ["project_id", "item_type", "title"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.item.update",
        "description": "",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.item.update@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "item_id": {"type": "string"},
                "patch": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 1},
                        "summary": {"type": ["string", "null"]},
                        "severity": {"type": ["string", "null"], "enum": ["critical", "high", "medium", "low", None]},
                        "owner_ref": {"type": ["string", "null"]},
                        "due_at": {"type": ["string", "null"]},
                        "sort_key": {"type": ["number", "null"]},
                        "details": {"type": ["object", "null"]},
                        "lifecycle": {"type": "string"},
                    },
                    "additionalProperties": False,
                    "minProperties": 1,
                },
                "expected_revision": {"type": "integer"},
                "command_id": {"type": "string"},
            },
            "required": ["project_id", "item_id", "patch"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.item.transition",
        "description": "",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.item.transition@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "item_id": {"type": "string"},
                "verb": {"type": "string", "minLength": 1},
                "expected_revision": {"type": "integer"},
                "command_id": {"type": "string"},
            },
            "required": ["project_id", "item_id", "verb"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.resource.list",
        "description": "",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.resource.list@1",
            "type": "object",
            "properties": {"project_id": {"type": "string"}},
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.resource.add",
        "description": "",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.resource.add@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "resource_ref": {"type": "string"},
                "relationship": {"type": "string", "enum": ["member", "source", "output", "related"]},
                "expected_revision": {"type": "integer"},
                "command_id": {"type": "string"},
            },
            "required": ["project_id", "resource_ref"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.resource.remove",
        "description": "",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.resource.remove@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "resource_ref": {"type": "string"},
                "expected_revision": {"type": "integer"},
                "command_id": {"type": "string"},
            },
            "required": ["project_id", "resource_ref"],
            "additionalProperties": False,
        },
    },
    # ── steward driver tools (HS-165-03) ────────────────────────────
    {
        "name": "project.configure_steward",
        "description": (
            "Read or update the steward policy for a project. "
            "GET: omit all optional fields. PUT: supply at least one field to update. "
            "Includes unattended_enabled (bounded-delegation ruling). "
            "Emits steward.configured event on write."
        ),
        "inputSchema": {
            "$id": "holdspeak://mcp/project.configure_steward@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "enabled": {"type": "boolean", "description": "Enable/disable the steward."},
                "unattended_enabled": {"type": "boolean", "description": "Allow unattended runs (bounded delegation)."},
                "eligible_effect_kinds": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Effect kinds the steward may execute.",
                },
                "max_retries": {"type": "integer", "minimum": 0, "maximum": 100},
                "max_actions_per_run": {"type": "integer", "minimum": 0, "maximum": 1000},
                "cooldown_seconds": {"type": "integer", "minimum": 0, "maximum": 86400},
                "evaluation_cadence_minutes": {
                    "type": "integer", "minimum": 1, "maximum": 10080,
                    "description": "Evaluation cadence in minutes (1..10080). Applied to all project watches.",
                },
                "bounds": {"type": "object", "description": "Arbitrary bounds object."},
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.run_steward",
        "description": (
            "Start a steward run. Returns run_id IMMEDIATELY (MCP-003); "
            "phase execution proceeds on a background thread. "
            "Typed refusals: active_run_exists (STW-002), steward_disabled, cooldown_active."
        ),
        "inputSchema": {
            "$id": "holdspeak://mcp/project.run_steward@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "watermark": {"type": "string", "description": "Caller-supplied watermark for correlation."},
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.stop_steward",
        "description": "Set the durable stop request on a steward run (STW-003).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.stop_steward@1",
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Steward run identifier."},
            },
            "required": ["run_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.get_steward_run",
        "description": "Poll a steward run: state, phase, steps, and receipts.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.get_steward_run@1",
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Steward run identifier."},
            },
            "required": ["run_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.steward.trigger",
        "description": "Trigger evaluate_due + run_due NOW through the conductor seam. "
                       "Unwired = typed refusal. Reuses the 163 same-watermark contract.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.steward.trigger@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    # ── setup driver tools (HS-165-03) ──────────────────────────────
    {
        "name": "project.setup.start",
        "description": "Start a new durable setup interview session.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.setup.start@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.setup.resume",
        "description": "Resume (read) an existing setup interview session.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.setup.resume@1",
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Setup session identifier."},
            },
            "required": ["session_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.setup.answer",
        "description": "Answer an interview question in a setup session.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.setup.answer@1",
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Setup session identifier."},
                "question_id": {"type": "string", "description": "Question identifier."},
                "payload": {"type": "object", "description": "Answer payload."},
            },
            "required": ["session_id", "question_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.setup.suggest",
        "description": "Generate watch proposals for a setup session based on answers so far.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.setup.suggest@1",
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Setup session identifier."},
            },
            "required": ["session_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.setup.finalize",
        "description": (
            "Atomically finalize a setup session: create the project, "
            "activate selected+passed proposals as graduated watches, "
            "establish baselines. All-or-nothing."
        ),
        "inputSchema": {
            "$id": "holdspeak://mcp/project.setup.finalize@1",
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Setup session identifier."},
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["session_id"],
            "additionalProperties": False,
        },
    },
    # ── provider driver tools (HS-165-03) ───────────────────────────
    {
        "name": "provider.list",
        "description": "List configured providers (native + GitHub) with their capabilities.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.list@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.github_connection",
        "description": "Get the GitHub provider connection status.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.github_connection@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.github_discover",
        "description": "Bounded discovery of GitHub repositories through the configured adapter.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.github_discover@1",
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional search query."},
                "cursor": {"type": "integer", "description": "Pagination cursor."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Page size (default 30)."},
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.github_validate_repo",
        "description": "Validate a GitHub repository by owner/repo string.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.github_validate_repo@1",
            "type": "object",
            "properties": {
                "owner_repo": {"type": "string", "description": "GitHub owner/repo (e.g. 'octocat/Hello-World')."},
            },
            "required": ["owner_repo"],
            "additionalProperties": False,
        },
    },
    # ── Jira provider driver tools (HS-166-01) ─────────────────────
    {
        "name": "provider.jira_connections",
        "description": "List all Jira connections (site+email pairs) and their status.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_connections@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.jira_add_connection",
        "description": "Add a Jira connection by site and email (no credentials stored).",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_add_connection@1",
            "type": "object",
            "properties": {
                "site": {"type": "string", "description": "Atlassian site (e.g. 'mysite' or 'mysite.atlassian.net')."},
                "email": {"type": "string", "description": "Account email address."},
            },
            "required": ["site", "email"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.jira_connection",
        "description": "Recheck one Jira connection status (switch + auth status probe).",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_connection@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
            },
            "required": ["connection_ref"],
            "additionalProperties": False,
        },
    },
    # ── Jira discovery + search tools (HS-166-02) ─────────────────
    {
        "name": "provider.jira_discover",
        "description": "Discover Jira resources (projects, issue types, statuses) for a connection.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_discover@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "kind": {"type": "string", "description": "Resource kind: projects, issue_types, statuses.", "default": "projects"},
                "query": {"type": "string", "description": "Filter text (substring match on key/name for projects).", "default": ""},
                "project_key": {"type": "string", "description": "Project key (required for issue_types and statuses).", "default": ""},
                "cursor": {"type": "integer", "description": "Offset cursor for pagination."},
                "limit": {"type": "integer", "description": "Max items to return (capped at 100).", "default": 30},
            },
            "required": ["connection_ref"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.jira_search",
        "description": "Search Jira issues by JQL query.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_search@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "jql": {"type": "string", "description": "JQL query (passed through verbatim)."},
                "limit": {"type": "integer", "description": "Max items to return (capped at 200).", "default": 50},
                "enrich": {"type": "boolean", "description": "Enrich each item with duedate, resolution, etc. via workitem view.", "default": False},
            },
            "required": ["connection_ref", "jql"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.jira_validate_scope",
        "description": "Validate a Jira project key (the validate_repo twin).",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_validate_scope@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "project_key": {"type": "string", "description": "Jira project key (e.g. 'KAN')."},
            },
            "required": ["connection_ref", "project_key"],
            "additionalProperties": False,
        },
    },
    # ── Confluence provider driver tools (HS-174-07) ─────────────────
    {
        "name": "provider.confluence_connections",
        "description": "List all Confluence connections (site+email pairs) and their status.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.confluence_connections@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.confluence_discover",
        "description": "Discover Confluence spaces for a connection.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.confluence_discover@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "kind": {"type": "string", "description": "Resource kind: spaces.", "default": "spaces"},
                "query": {"type": "string", "description": "Filter text (substring match on key/name).", "default": ""},
                "cursor": {"type": "integer", "description": "Offset cursor for pagination."},
                "limit": {"type": "integer", "description": "Max items to return (capped at 100).", "default": 30},
            },
            "required": ["connection_ref"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.confluence_validate_space",
        "description": "Validate a Confluence space key.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.confluence_validate_space@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "space_key": {"type": "string", "description": "Confluence space key (e.g. 'GOV')."},
            },
            "required": ["connection_ref", "space_key"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.setup.clarify_jira_scope",
        "description": "Clarify the Jira scope for a Jira proposal in a setup session.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.setup.clarify_jira_scope@1",
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Setup session ID."},
                "proposal_id": {"type": "string", "description": "Proposal ID."},
                "connection_ref": {"type": "string", "description": "Jira connection ref (site|email)."},
                "projects": {"type": "array", "items": {"type": "string"}, "description": "Project keys."},
                "issue_types": {"type": "array", "items": {"type": "string"}, "description": "Issue type names."},
            },
            "required": ["session_id", "proposal_id"],
            "additionalProperties": False,
        },
    },
    # ── graduated watch driver tools (HS-165-03) ────────────────────
    # The 164 boundary rule's MCP twin: these tools operate ONLY on
    # graduated rows (state in active/tested/paused/retired).  Legacy
    # rows (state='') belong to the reactions family (watch.*/reaction.*).
    {
        "name": "project.watch.inspect",
        "description": "Get a graduated watch with its rules, circuit state, and evaluation history.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.watch.inspect@1",
            "type": "object",
            "properties": {
                "watch_id": {"type": "string", "description": "Watch identifier."},
            },
            "required": ["watch_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.watch.test",
        "description": "Run a bounded, non-mutating read test on a graduated watch (ACT-002).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.watch.test@1",
            "type": "object",
            "properties": {
                "watch_id": {"type": "string", "description": "Watch identifier."},
            },
            "required": ["watch_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.watch.evaluate",
        "description": "Manually evaluate a graduated watch: snapshot, diff, transitions, observations. Records watch_effects the Steward can act on (HS-200-43), keyed identically to a scheduled evaluation, so a manual run and the scheduler cannot double-mint. The first evaluation of a watch with no baseline is silent: it establishes the baseline and returns state=baselined with zero transitions.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.watch.evaluate@1",
            "type": "object",
            "properties": {
                "watch_id": {"type": "string", "description": "Watch identifier."},
            },
            "required": ["watch_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.watch.set_rules",
        "description": "Replace rules for a graduated watch (WatchCondition@1 + WatchAction@1). "
                       "Optionally set evaluation_cadence_minutes (1..10080).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.watch.set_rules@2",
            "type": "object",
            "properties": {
                "watch_id": {"type": "string", "description": "Watch identifier."},
                "rules": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Ordered rule list (condition + actions).",
                },
                "evaluation_cadence_minutes": {
                    "type": "integer",
                    "description": "Evaluation cadence in minutes (1..10080). "
                                   "Floor = 1 min (conductor tick), ceiling = 7 days.",
                    "minimum": 1,
                    "maximum": 10080,
                },
            },
            "required": ["watch_id", "rules"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.watch.pause",
        "description": "Pause a graduated watch (stops evaluation).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.watch.pause@1",
            "type": "object",
            "properties": {
                "watch_id": {"type": "string", "description": "Watch identifier."},
            },
            "required": ["watch_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.watch.resume",
        "description": "Resume a paused graduated watch (state -> active).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.watch.resume@1",
            "type": "object",
            "properties": {
                "watch_id": {"type": "string", "description": "Watch identifier."},
            },
            "required": ["watch_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.watch.retire",
        "description": "Retire a graduated watch (ACT-009). Retains history, stops evaluation.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.watch.retire@1",
            "type": "object",
            "properties": {
                "watch_id": {"type": "string", "description": "Watch identifier."},
            },
            "required": ["watch_id"],
            "additionalProperties": False,
        },
    },
    # ── HS-172-06: suggested source tools ──────────────────────────
    {
        "name": "project.suggested_sources",
        "description": "List pending suggested sources for a Room (HS-172-06). Returns transcript-derived repo and issue mentions not yet added as Watch sources.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.suggested_sources@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project / Room identifier."},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.add_suggested_source",
        "description": "Accept a suggested source and create a Watch source on the Room (HS-172-06). Receipted (Article V).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.add_suggested_source@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project / Room identifier."},
                "reference": {"type": "string", "description": "The source reference to accept (e.g. owner/repo or PROJ-123)."},
            },
            "required": ["project_id", "reference"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.dismiss_suggested_source",
        "description": "Dismiss a suggested source so it never recurs for this Room (HS-172-06).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.dismiss_suggested_source@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project / Room identifier."},
                "reference": {"type": "string", "description": "The source reference to dismiss (e.g. owner/repo or PROJ-123)."},
            },
            "required": ["project_id", "reference"],
            "additionalProperties": False,
        },
    },
    # ── HS-168-02: connection tools ─────────────────────────────────
    {
        "name": "connection.list",
        "description": "List all tool connections with their readiness state (HS-168-02). Returns the same shape as GET /api/connections.",
        "inputSchema": {
            "$id": "holdspeak://mcp/connection.list@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "connection.recheck",
        "description": "Recheck one provider connection (HS-168-02). Returns the refreshed tool entry.",
        "inputSchema": {
            "$id": "holdspeak://mcp/connection.recheck@1",
            "type": "object",
            "properties": {
                "provider_id": {
                    "type": "string",
                    "description": "Provider to recheck: github, jira, calendar, models.",
                },
                "ref": {
                    "type": "string",
                    "description": "Optional Jira connection ref (site|email) to recheck a specific connection.",
                },
            },
            "required": ["provider_id"],
            "additionalProperties": False,
        },
    },
]


# ── Service composition ──────────────────────────────────────────────

def _setup_proposal_tool(verb: str, description: str, *, repo: bool = False) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "session_id": {"type": "string", "minLength": 1},
        "proposal_id": {"type": "string", "minLength": 1},
    }
    if repo:
        fields["repo"] = {"type": "string", "minLength": 1}
    return {
        "name": f"project.setup.{verb}", "description": description,
        "inputSchema": {"$id": f"holdspeak://mcp/project.setup.{verb}@1", "type": "object",
                        "properties": fields, "required": ["session_id", "proposal_id"], "additionalProperties": False},
    }


TOOLS.extend([
    _setup_proposal_tool("select_proposal", "Select an existing setup proposal before testing/finalizing it; creates no Watch yet."),
    _setup_proposal_tool("deselect_proposal", "Deselect a setup proposal before finalization."),
    _setup_proposal_tool("test_proposal", "Run the actual bounded source test for a setup proposal, recording its result before activation."),
    _setup_proposal_tool("clarify_repo_scope", "Discover or validate a GitHub repository for an existing setup proposal; omitted repo discovers authorized repositories.", repo=True),
])


def _build_service():
    """Compose the same ProjectService the web application edge uses."""
    from holdspeak.services.project_service import ProjectService
    db = db_or(get_database)
    return ProjectService(db)


def _build_delta_service():
    """Compose ProjectDeltaService (same wiring as web context)."""
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.services.project_service import ProjectService
    db = db_or(get_database)
    ps = ProjectService(db)
    # collector=None is safe for decide_proposal/accept_review which
    # do not invoke the collector.  open_review DOES need it; composed
    # The real collector: collect_all is DB-only work (native adapters
    # read the DB; the WatchAdapter reads stored snapshots and NEVER
    # calls a provider -- proven in HS-164). Same composition as
    # web_server's recovery block: true MCP-001 parity for open_review.
    from holdspeak.services.project_evidence_collector import (
        ProjectEvidenceCollector,
    )
    delta_svc = ProjectDeltaService(
        db,
        collector=ProjectEvidenceCollector(db),
        project_service=ps,
    )
    return delta_svc


def _build_update_service():
    """Compose ProjectUpdateService (same wiring as web context)."""
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_update_service import ProjectUpdateService
    db = db_or(get_database)
    ps = ProjectService(db)
    return ProjectUpdateService(db, project_service=ps)


def _build_steward_service():
    """Compose ProjectStewardService (same wiring as web context)."""
    from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_steward_service import ProjectStewardService
    from holdspeak.services.project_update_service import ProjectUpdateService
    db = db_or(get_database)
    ps = ProjectService(db)
    collector = ProjectEvidenceCollector(db)
    delta = ProjectDeltaService(db, collector=collector, project_service=ps)
    us = ProjectUpdateService(db, project_service=ps)
    return ProjectStewardService(
        db, collector=collector, delta=delta,
        update_service=us, project_service=ps,
    )


def _build_connections_service():
    """Compose ConnectionsService (same wiring as web context, HS-168-02)."""
    from holdspeak.config import Config
    from holdspeak.mcp.families.inference_assignments import _service as _assignment_service
    from holdspeak.services.connections_service import ConnectionsService
    # Parity with the web composition (counsel S-2): calendar reads the
    # config, models reads the assignment summary — the sidecar must not
    # report both as not_configured.
    return ConnectionsService(
        github_adapter=_github_adapter(),
        jira_adapter=_jira_adapter(),
        config_loader=Config.load,
        inference_assignment_service=_assignment_service(),
    )


def _build_setup_service():
    """Compose ProjectSetupService (same wiring as web context)."""
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_setup_service import ProjectSetupService
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import default_snapshot_fetcher
    db = db_or(get_database)
    ps = ProjectService(db)
    ga = _github_adapter()
    ja = _jira_adapter()
    ca = _confluence_adapter()
    fetcher = default_snapshot_fetcher(jira_adapter=ja, confluence_adapter=ca)
    ws = WatchService(db, snapshot_fetcher=fetcher)
    return ProjectSetupService(
        db, project_service=ps, watch_service=ws,
        github_adapter=ga,
        jira_adapter=ja,
        connections_service=_connections_service(),
    )


def _build_watch_service():
    """Compose WatchService (same wiring as web context, HS-174-07 rider)."""
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import default_snapshot_fetcher
    db = db_or(get_database)
    ja = _jira_adapter()
    ca = _confluence_adapter()
    fetcher = default_snapshot_fetcher(jira_adapter=ja, confluence_adapter=ca)
    return WatchService(db, snapshot_fetcher=fetcher)


def _build_github_adapter():
    """Return the GitHubProviderAdapter or None (same as web context)."""
    from holdspeak.services.github_provider import GitHubProviderAdapter
    db = db_or(get_database)
    try:
        return GitHubProviderAdapter(db)
    except Exception:
        return None


def _build_jira_adapter():
    """Return the JiraProviderAdapter or None (same as web context)."""
    from holdspeak.services.jira_provider import JiraProviderAdapter
    db = db_or(get_database)
    try:
        return JiraProviderAdapter(db)
    except Exception:
        return None


def _build_confluence_adapter():
    """Return the ConfluenceProviderAdapter or None (same as web context)."""
    from holdspeak.services.confluence_provider import ConfluenceProviderAdapter
    db = db_or(get_database)
    try:
        return ConfluenceProviderAdapter(db)
    except Exception:
        return None


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash for idempotency (mirrors steward route)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _record_steward_command(
    db: Any,
    command_id: str,
    project_id: str,
    command_kind: str,
    request_hash: str,
    result: dict[str, Any],
) -> None:
    """Record a completed steward command via the DB layer (MCP-001: no SQL)."""
    result_json = json.dumps(result, ensure_ascii=False, default=str)
    try:
        db.projects.insert_project_command(
            command_id=command_id,
            project_id=project_id,
            command_kind=command_kind,
            request_hash=request_hash,
            status="completed",
        )
    except sqlite3.IntegrityError:
        # The command row already exists (replay); anything else must
        # surface through the tool's error mapping.
        pass
    db.projects.complete_project_command(
        command_id,
        status="completed",
        result_json=result_json,
    )


# The native provider families (mirrors providers.py:31-43).
# One source of truth for the native provider list (counsel S-3):
from holdspeak.web.routes.providers import _NATIVE_PROVIDERS  # noqa: E402
# HS-166-01: shared helper for provider list (ONE function, never duplicate).
from holdspeak.web.routes.providers import collect_provider_manifests  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────────

def _require_id(arguments: dict[str, Any], key: str) -> str:
    """Extract a required string id from arguments, raising typed on absence."""
    value = str(arguments.get(key) or "").strip()
    if not value:
        raise ServiceError(
            "project_request_invalid",
            f"{key} is required.",
            context={"status": 400},
        )
    return value


def _require_graduated_watch(watch_id: str) -> dict[str, Any]:
    """Load a watch and refuse if it is a legacy (reactions-family) row.

    HS-165-03 boundary rule: graduated tools operate ONLY on rows
    whose state is in _GRADUATED_WATCH_STATES.  Legacy rows (state='')
    belong to the reactions family.
    """
    db = db_or(get_database)
    watch = db.automations.get_watch(watch_id)
    if not watch:
        raise NotFound("watch", watch_id)
    state = watch.get("state") or ""
    if state not in _GRADUATED_WATCH_STATES:
        raise ServiceError(
            "legacy_watch_boundary",
            f"Watch {watch_id!r} is a legacy row (state={state!r}). "
            f"Use the reactions family tools (watch.list / watch.refresh) instead.",
            context={"watch_id": watch_id, "state": state, "status": 409},
        )
    return watch


# ── Steward serialization (mirrors steward.py:370-481) ───────────────

def _serialize_run(run):
    """Delegate to the steward route's serializer -- ONE source
    of truth (the resources.py precedent); a copy drifts."""
    from holdspeak.web.routes.steward import _serialize_run as _r
    return _r(run)

def _serialize_step(step):
    """Delegate to the steward route's serializer -- ONE source
    of truth (the resources.py precedent); a copy drifts."""
    from holdspeak.web.routes.steward import _serialize_step as _r
    return _r(step)

def _serialize_policy(policy):
    """Delegate to the steward route's serializer -- ONE source
    of truth (the resources.py precedent); a copy drifts."""
    from holdspeak.web.routes.steward import _serialize_policy as _r
    return _r(policy)

def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Dispatch project tools (MCP-001: thin drivers over service seams)."""

    if name in {"project.setup.select_proposal", "project.setup.deselect_proposal", "project.setup.test_proposal", "project.setup.clarify_repo_scope"}:
        from jsonschema import Draft202012Validator
        from holdspeak.services.project_setup_service import ProjectSetupService
        ProjectSetupService._owner(principal)
        schema = next(tool["inputSchema"] for tool in TOOLS if tool["name"] == name)
        error = next(Draft202012Validator(schema).iter_errors(arguments), None)
        if error:
            raise ValidationError(error.message)
        service = _setup_service()
        method = getattr(service, name.rsplit(".", 1)[1])
        extra = {"repo": arguments.get("repo")} if name.endswith("clarify_repo_scope") else {}
        return method(principal, arguments["session_id"], arguments["proposal_id"], **extra)

    # ── PHILO-9-01: the Room's operations, through the ONE registry ──────
    #
    # The Room's lifecycle, review and update tools, ``desk.needs_you`` and
    # the seven item/resource tools are declared operations
    # (``holdspeak.operations``), bound at hub composition to the hub's
    # ProjectService, ProjectDeltaService and ProjectUpdateService. The tool
    # names its operation; the envelope below is the transport's (the same
    # shapes these tools answered before).

    if name in ROOM_TOOL_OPERATIONS:
        return _room_tool(name, arguments, principal)

    # ── steward driver tools (HS-165-03) ────────────────────────────
    # Mirrors: holdspeak/web/routes/steward.py

    if name == "project.configure_steward":
        # Web parity: steward.py:206 api_get_steward_policy (GET)
        #              steward.py:223 api_put_steward_policy (PUT)
        # Service seam: steward_policies DB layer (same as the route)
        project_id = _require_id(arguments, "project_id")
        # Detect read vs write: if only project_id is supplied, it's a GET
        write_fields = {
            "enabled", "unattended_enabled", "eligible_effect_kinds",
            "max_retries", "max_actions_per_run", "cooldown_seconds", "bounds",
            "evaluation_cadence_minutes",
        }
        is_write = any(arguments.get(f) is not None for f in write_fields)

        svc = _steward_service()

        if not is_write:
            # GET: read the policy
            policy = svc._db.steward_policies.get_policy_for_project(project_id)
            return {"policy": _serialize_policy(policy)}

        # PUT: validate and upsert
        from holdspeak.services.project_steward_service import EFFECT_KINDS
        from holdspeak.project_contracts import generate_pstpol_id

        eligible = arguments.get("eligible_effect_kinds")
        if eligible is not None:
            if not isinstance(eligible, list):
                raise ValidationError("eligible_effect_kinds must be a list")
            invalid_kinds = [k for k in eligible if k not in EFFECT_KINDS]
            if invalid_kinds:
                raise ValidationError(
                    f"Invalid effect kinds: {invalid_kinds}. Valid: {list(EFFECT_KINDS)}"
                )

        for field in ("max_retries", "max_actions_per_run", "cooldown_seconds"):
            val = arguments.get(field)
            if val is not None:
                if not isinstance(val, int) or val < 0:
                    raise ValidationError(f"{field} must be a non-negative integer")

        enabled = arguments.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            raise ValidationError("enabled must be a boolean")
        unattended_enabled = arguments.get("unattended_enabled")
        if unattended_enabled is not None and not isinstance(unattended_enabled, bool):
            raise ValidationError("unattended_enabled must be a boolean")

        cadence_minutes = arguments.get("evaluation_cadence_minutes")
        if cadence_minutes is not None:
            if not isinstance(cadence_minutes, int) or cadence_minutes < 1:
                raise ValidationError(
                    "evaluation_cadence_minutes must be an integer >= 1"
                )
            if cadence_minutes > 10080:
                raise ValidationError(
                    "evaluation_cadence_minutes cannot exceed 10080 (7 days)"
                )

        existing = svc._db.steward_policies.get_policy_for_project(project_id)
        if existing is None:
            policy_id = generate_pstpol_id()
            svc._db.steward_policies.insert_policy(
                policy_id=policy_id,
                project_id=project_id,
                eligible_effect_kinds_json=json.dumps(eligible or []),
                max_retries=arguments.get("max_retries", 3),
                max_actions_per_run=arguments.get("max_actions_per_run", 10),
                cooldown_seconds=arguments.get("cooldown_seconds", 0),
                bounds_json=json.dumps(arguments.get("bounds", {})),
                enabled=1 if arguments.get("enabled", True) else 0,
                unattended_enabled=1 if arguments.get("unattended_enabled", False) else 0,
            )
        else:
            policy_id = existing["id"]
            update_kwargs: dict[str, Any] = {}
            if eligible is not None:
                update_kwargs["eligible_effect_kinds_json"] = json.dumps(eligible)
            if arguments.get("max_retries") is not None:
                update_kwargs["max_retries"] = arguments["max_retries"]
            if arguments.get("max_actions_per_run") is not None:
                update_kwargs["max_actions_per_run"] = arguments["max_actions_per_run"]
            if arguments.get("cooldown_seconds") is not None:
                update_kwargs["cooldown_seconds"] = arguments["cooldown_seconds"]
            if arguments.get("bounds") is not None:
                update_kwargs["bounds_json"] = json.dumps(arguments["bounds"])
            if enabled is not None:
                update_kwargs["enabled"] = 1 if enabled else 0
            if unattended_enabled is not None:
                update_kwargs["unattended_enabled"] = 1 if unattended_enabled else 0
            if update_kwargs:
                svc._db.steward_policies.update_policy(policy_id, **update_kwargs)

        if cadence_minutes is not None:
            try:
                watches = svc._db.automations.list_project_watches(project_id)
                for w in watches:
                    svc._db.automations.update_watch_spec(
                        w["id"],
                        evaluation_cadence_minutes=cadence_minutes,
                    )
            except Exception:
                pass

        policy = svc._db.steward_policies.get_policy(policy_id)

        # steward.configured event (mirrors steward.py:335-361)
        try:
            from holdspeak.services.service_event_ledger import ServiceEventLedger
            ledger = ServiceEventLedger(svc._db)
            with svc._db._connection() as conn:
                ledger.append_in_transaction(
                    conn,
                    principal,
                    event_type="steward.configured",
                    producer="steward.mcp",
                    subject_ref=f"steward_policy:{policy_id}",
                    source_revision="",
                    facts={
                        "policy_id": policy_id,
                        "project_id": project_id,
                        "enabled": bool(policy["enabled"]) if policy else False,
                        "unattended_enabled": bool(
                            policy.get("unattended_enabled", 0)
                        ) if policy else False,
                    },
                    refs=[
                        f"project:{project_id}",
                        f"steward_policy:{policy_id}",
                    ],
                )
        except Exception:
            pass  # Event emission must never fail the policy response.

        return {"success": True, "policy": _serialize_policy(policy)}

    if name == "project.run_steward":
        # Web parity: steward.py:61 api_start_steward_run
        # MCP-003: insert_run on the call thread (typed refusals surface
        # synchronously), then hand phase execution to a daemon thread.
        # run_id returned PROMPTLY.
        from holdspeak.db.steward import ActiveRunExistsError
        from holdspeak.services.project_steward_service import (
            CooldownActiveError,
            StewardDisabledError,
        )
        from holdspeak.project_contracts import generate_pcmd_id

        project_id = _require_id(arguments, "project_id")
        watermark = str(arguments.get("watermark", "") or "")
        cmd_id = arguments.get("command_id")

        req_hash = _request_hash({
            "project_id": project_id,
            "action": "run_once",
            "watermark": watermark,
        })

        # command_id replay (mirrors steward.py:78-91)
        db = db_or(get_database)
        if cmd_id is not None:
            existing = db.projects.get_project_command(cmd_id)
            if existing is not None:
                if (existing["status"] == "completed"
                        and existing["request_hash"] == req_hash):
                    if existing["result_json"]:
                        return json.loads(existing["result_json"])
                    return {"success": True, "run_id": None}
                if existing["request_hash"] != req_hash:
                    raise ConflictError(
                        "same command_id with different request hash",
                        code="idempotency_conflict",
                    )

        svc = _steward_service()

        try:
            run_id = svc.insert_run(principal, project_id, watermark=watermark)
        except ActiveRunExistsError:
            raise ServiceError(
                "active_run_exists",
                f"Project {project_id} already has an active steward run (STW-002)",
                context={"status": 409},
            )
        except StewardDisabledError:
            raise ServiceError(
                "steward_disabled",
                "The steward policy is disabled for this project",
                context={"status": 409},
            )
        except CooldownActiveError as exc:
            raise ServiceError(
                "cooldown_active",
                f"Cooling down: {exc.seconds_remaining}s remaining",
                context={"status": 409},
            )

        result_payload = {"success": True, "run_id": run_id}

        # Record command for replay
        _record_steward_command(
            svc._db, cmd_id or generate_pcmd_id(),
            project_id, "run_once", req_hash, result_payload,
        )

        # MCP-003: phase execution on a daemon thread.
        def _execute() -> None:
            try:
                svc.execute_phases(principal, run_id, project_id)
            except Exception:
                pass

        t = threading.Thread(target=_execute, daemon=True)
        t.start()

        return result_payload

    if name == "project.stop_steward":
        # Web parity: steward.py:189 api_stop_steward_run
        # Service seam: ProjectStewardService.stop
        run_id = _require_id(arguments, "run_id")
        svc = _steward_service()
        run = svc._db.steward_runs.get_run(run_id)
        if run is None:
            raise NotFound("steward_run", run_id)
        svc.stop(run_id)
        return {"success": True, "run_id": run_id}

    if name == "project.get_steward_run":
        # Web parity: steward.py:168 api_get_steward_run
        # Service seam: steward_runs + steward_steps DB layer
        run_id = _require_id(arguments, "run_id")
        svc = _steward_service()
        run = svc._db.steward_runs.get_run(run_id)
        if run is None:
            raise NotFound("steward_run", run_id)
        steps = svc._db.steward_steps.list_steps(run_id)
        return {
            "run": _serialize_run(run),
            "steps": [_serialize_step(s) for s in steps],
        }

    if name == "project.steward.trigger":
        # HS-167-02: evaluate_due + run_due NOW through the conductor's
        # get_scheduler_services seam. Web parity: steward.py trigger
        # route. Desk-wide (principal-scoped) by contract; unwired =
        # typed refusal (honest); a raised error is surfaced, never
        # dressed as success.
        from holdspeak.workbench_conductor import get_scheduler_services
        wired_watch, wired_steward = get_scheduler_services()

        if wired_watch is None and wired_steward is None:
            # HS-200-45 R6: this RAISES now. The comment above claims "a raised
            # error is surfaced, never dressed as success" -- but it was a
            # `return`, so the sidecar wrapped it with `isError: false` and a
            # naive caller read a refusal as a completed trigger. And it was
            # the ONLY branch reachable from the old sidecar, which never
            # called `set_scheduler_services`: every steward trigger over MCP
            # "succeeded" and ran nothing.
            raise ServiceError(
                # The code the HTTP 503 path and docs/PROJECT_ROOMS.md already
                # name is kept; only the ENVELOPE changes, from a returned
                # success to a raised refusal.
                "scheduler_not_wired",
                "project.steward.trigger needs the conductor's scheduler "
                "services, which only the running hub wires "
                "(set_scheduler_services is called by `holdspeak web`'s "
                "conductor). Nothing was evaluated and no steward run started. "
                "Start the hub and retry -- the stdio sidecar forwards this "
                "call to it."
            )

        # HS-200-43 F2: explicit trigger = the owner's hand = unbounded.
        eval_outcomes = (
            wired_watch.evaluate_due(principal, limit=None)
            if wired_watch is not None else []
        )
        run_outcomes = wired_steward.run_due(principal) if wired_steward is not None else []

        return {
            "success": True,
            "evaluate_outcomes": eval_outcomes,
            "run_outcomes": run_outcomes,
        }

    # ── setup driver tools (HS-165-03) ──────────────────────────────
    # Mirrors: holdspeak/web/routes/project_setup.py

    if name == "project.setup.start":
        # Web parity: project_setup.py:48 start_setup
        # Service seam: ProjectSetupService.start_setup
        return _setup_service().start_setup(principal)

    if name == "project.setup.resume":
        # Web parity: project_setup.py:60 get_setup
        # Service seam: ProjectSetupService.get_setup
        session_id = _require_id(arguments, "session_id")
        return _setup_service().get_setup(session_id)

    if name == "project.setup.answer":
        # Web parity: project_setup.py:78 answer
        # Service seam: ProjectSetupService.answer
        session_id = _require_id(arguments, "session_id")
        question_id = _require_id(arguments, "question_id")
        payload = arguments.get("payload") or {}
        return _setup_service().answer(
            principal, session_id, question_id, payload,
        )

    if name == "project.setup.suggest":
        # Web parity: project_setup.py:105 suggest
        # Service seam: ProjectSetupService.suggest
        session_id = _require_id(arguments, "session_id")
        proposals = _setup_service().suggest(principal, session_id)
        return {"proposals": proposals}

    if name == "project.setup.finalize":
        # Web parity: project_setup.py:261 finalize
        # Service seam: ProjectSetupService.finalize
        # command_id mirrors the route's body.command_id
        session_id = _require_id(arguments, "session_id")
        cmd_id = arguments.get("command_id")
        return _setup_service().finalize(
            principal, session_id, command_id=cmd_id,
        )

    if name == "project.setup.clarify_jira_scope":
        session_id = _require_id(arguments, "session_id")
        proposal_id = _require_id(arguments, "proposal_id")
        return _setup_service().clarify_jira_scope(
            principal, session_id, proposal_id,
            connection_ref=arguments.get("connection_ref", ""),
            projects=arguments.get("projects", []),
            issue_types=arguments.get("issue_types", []),
        )

    # ── provider driver tools (HS-165-03) ───────────────────────────
    # Mirrors: holdspeak/web/routes/providers.py

    if name == "provider.list":
        # Web parity: providers.py list_providers
        # HS-166-01: ONE shared helper, never duplicate the enumeration.
        return {"providers": collect_provider_manifests(
            github_adapter=_github_adapter(),
            jira_adapter=_jira_adapter(),
            confluence_adapter=_confluence_adapter(),
            principal=principal,
        )}

    if name == "provider.github_connection":
        # Web parity: providers.py:68 github_connection
        # Service seam: GitHubProviderAdapter.connection_status
        adapter = _github_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "GitHub provider is not configured",
                context={"status": 404},
            )
        return adapter.connection_status(principal)

    if name == "provider.github_discover":
        # Web parity: providers.py:104 github_discover
        # Service seam: GitHubProviderAdapter.discover
        adapter = _github_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "GitHub provider is not configured",
                context={"status": 404},
            )
        return adapter.discover(
            principal,
            query=arguments.get("query"),
            cursor=arguments.get("cursor"),
            limit=arguments.get("limit", 30),
        )

    if name == "provider.github_validate_repo":
        # Web parity: providers.py:132 github_validate_repo
        # Service seam: GitHubProviderAdapter.validate_repo
        adapter = _github_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "GitHub provider is not configured",
                context={"status": 404},
            )
        owner_repo = str(arguments.get("owner_repo", "")).strip()
        if not owner_repo:
            raise ValidationError("owner_repo is required")
        return adapter.validate_repo(principal, owner_repo)

    # ── Jira provider driver tools (HS-166-01) ──────────────────────
    # Mirrors: holdspeak/web/routes/providers.py Jira routes.
    # Serializers DELEGATE to the adapter (the 165 law: copies drift).

    if name == "provider.jira_connections":
        # Web parity: providers.py jira_connections
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        return {
            "connections": adapter.list_connections(principal),
            "known_accounts": adapter.known_accounts(principal),
        }

    if name == "provider.jira_add_connection":
        # Web parity: providers.py jira_add_connection
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        site = str(arguments.get("site", "")).strip()
        email = str(arguments.get("email", "")).strip()
        if not site or not email:
            raise ValidationError("site and email are required")
        return adapter.add_connection(principal, site, email)

    if name == "provider.jira_connection":
        # Web parity: providers.py jira_connection_recheck
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        if not ref:
            raise ValidationError("connection_ref is required")
        return adapter.connection_status(principal, ref)

    # ── Jira discovery + search tools (HS-166-02) ──────────────────
    # Mirrors: holdspeak/web/routes/providers.py Jira discover/search/validate routes.

    if name == "provider.jira_discover":
        # Web parity: providers.py jira_discover
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        if not ref:
            raise ValidationError("connection_ref is required")
        return adapter.discover(
            principal,
            ref,
            kind=arguments.get("kind", "projects"),
            query=arguments.get("query", ""),
            project_key=arguments.get("project_key", ""),
            cursor=arguments.get("cursor"),
            limit=arguments.get("limit", 30),
        )

    if name == "provider.jira_search":
        # Web parity: providers.py jira_search
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        jql = str(arguments.get("jql", "")).strip()
        if not ref or not jql:
            raise ValidationError("connection_ref and jql are required")
        return adapter.search(
            principal,
            ref,
            jql=jql,
            limit=arguments.get("limit", 50),
            enrich=bool(arguments.get("enrich", False)),
        )

    if name == "provider.jira_validate_scope":
        # Web parity: providers.py jira_validate_scope
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        project_key = str(arguments.get("project_key", "")).strip()
        if not ref or not project_key:
            raise ValidationError("connection_ref and project_key are required")
        return adapter.validate_scope(principal, ref, project_key)

    # ── Confluence provider driver tools (HS-174-07) ──────────────────
    # Mirrors: holdspeak/web/routes/providers.py Confluence routes.

    if name == "provider.confluence_connections":
        # Web parity: providers.py confluence_connections
        adapter = _confluence_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Confluence provider is not configured",
                context={"status": 404},
            )
        return {
            "connections": adapter.list_connections(principal),
        }

    if name == "provider.confluence_discover":
        # Web parity: providers.py confluence_discover
        adapter = _confluence_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Confluence provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        if not ref:
            raise ValidationError("connection_ref is required")
        return adapter.discover(
            principal,
            ref,
            kind=arguments.get("kind", "spaces"),
            query=arguments.get("query", ""),
            cursor=arguments.get("cursor"),
            limit=arguments.get("limit", 30),
        )

    if name == "provider.confluence_validate_space":
        # Web parity: providers.py confluence_validate_scope
        adapter = _confluence_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Confluence provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        space_key = str(arguments.get("space_key", "")).strip()
        if not ref or not space_key:
            raise ValidationError("connection_ref and space_key are required")
        return adapter.validate_scope(principal, ref, space_key)

    # ── graduated watch driver tools (HS-165-03) ────────────────────
    # Mirrors: holdspeak/web/routes/watches.py + providers.py:158
    # BOUNDARY: these tools operate ONLY on graduated rows.

    if name == "project.watch.inspect":
        # Web parity: watches.py:73 get_watch
        # Service seam: WatchService.get_watch
        watch_id = _require_id(arguments, "watch_id")
        _require_graduated_watch(watch_id)
        return _watch_service().get_watch(principal, watch_id)

    if name == "project.watch.test":
        # Web parity: watches.py:119 test_watch
        # Service seam: WatchService.test_watch
        watch_id = _require_id(arguments, "watch_id")
        _require_graduated_watch(watch_id)
        return _watch_service().test_watch(principal, watch_id)

    if name == "project.watch.evaluate":
        # Web parity: providers.py:158 evaluate_watch
        # Service seam: WatchService.evaluate_once
        watch_id = _require_id(arguments, "watch_id")
        _require_graduated_watch(watch_id)
        result = _watch_service().evaluate_once(principal, watch_id)
        return {"success": True, **result}

    if name == "project.watch.set_rules":
        # Web parity: watches.py:229 set_rules
        # Service seam: WatchService.set_rules
        watch_id = _require_id(arguments, "watch_id")
        _require_graduated_watch(watch_id)
        rules = arguments.get("rules") or []
        result = _watch_service().set_rules(principal, watch_id, rules)
        # HS-167-02: optional cadence write (range-fenced by schema).
        cadence = arguments.get("evaluation_cadence_minutes")
        if cadence is not None:
            cadence = int(cadence)
            if cadence < 1 or cadence > 10080:
                raise ValidationError(
                    "evaluation_cadence_minutes must be 1..10080",
                )
            db_or(get_database).automations.update_watch_spec(
                watch_id, evaluation_cadence_minutes=cadence,
            )
            result["evaluation_cadence_minutes"] = cadence
        return result

    if name == "project.watch.pause":
        # Web parity: watches.py:163 pause_watch
        # Service seam: WatchService.pause_watch
        watch_id = _require_id(arguments, "watch_id")
        _require_graduated_watch(watch_id)
        return _watch_service().pause_watch(principal, watch_id)

    if name == "project.watch.resume":
        # Web parity: watches.py:185 resume_watch
        # Service seam: WatchService.resume_watch
        watch_id = _require_id(arguments, "watch_id")
        _require_graduated_watch(watch_id)
        return _watch_service().resume_watch(principal, watch_id)

    if name == "project.watch.retire":
        # Web parity: watches.py:205 retire_watch
        # Service seam: WatchService.retire_watch
        watch_id = _require_id(arguments, "watch_id")
        _require_graduated_watch(watch_id)
        return _watch_service().retire_watch(principal, watch_id)

    # ── HS-172-06: suggested source tools ──────────────────────────

    if name == "project.suggested_sources":
        project_id = _require_id(arguments, "project_id")
        from holdspeak.services.suggested_source_service import SuggestedSourceService
        sug = SuggestedSourceService(svc._db)
        return {"suggestions": sug.list_suggestions(project_id, status="pending")}

    if name == "project.add_suggested_source":
        project_id = _require_id(arguments, "project_id")
        reference = str(arguments.get("reference") or "").strip()
        if not reference:
            raise ValidationError("reference is required")
        from holdspeak.services.suggested_source_service import SuggestedSourceService
        sug = SuggestedSourceService(svc._db)
        pending = sug.find_pending_by_reference(project_id, reference)
        suggestion = sug.accept_suggestion(pending["id"])
        resource_ref = f"{suggestion['provider']}:{suggestion['reference']}"
        try:
            resource = svc.add_resource(
                principal, project_id, resource_ref,
                {"relationship": "source", "provider": suggestion["provider"]},
            )
        except Exception:
            resource = {"resource_ref": resource_ref, "state": "accepted_no_watch"}
        return {"suggestion": suggestion, "resource": resource}

    if name == "project.dismiss_suggested_source":
        project_id = _require_id(arguments, "project_id")
        reference = str(arguments.get("reference") or "").strip()
        if not reference:
            raise ValidationError("reference is required")
        from holdspeak.services.suggested_source_service import SuggestedSourceService
        sug = SuggestedSourceService(svc._db)
        pending = sug.find_pending_by_reference(project_id, reference)
        return {"suggestion": sug.dismiss_suggestion(pending["id"])}

    # ── HS-168-02: connection tools ─────────────────────────────────

    if name == "connection.list":
        # Web parity: connections.py list_connections
        # Service seam: ConnectionsService.list_tools
        return _connections_service().list_tools(principal)

    if name == "connection.recheck":
        # Web parity: connections.py recheck_connection
        # Service seam: ConnectionsService.recheck
        provider_id = _require_id(arguments, "provider_id")
        ref = arguments.get("ref")
        return _connections_service().recheck(principal, provider_id, ref=ref)

    raise LookupError(name)


# ── PHILO-9-01: the Room's tools on the one contract ─────────────────

#: MCP tool -> the declared operation it reaches (``holdspeak.operations``).
ROOM_TOOL_OPERATIONS: dict[str, str] = {
    "project.list": "project.list",
    "project.get": "project.get",
    "project.get_room": "project.get_room",
    "project.create": "project.create",
    "project.update": "project.update",
    "project.archive": "project.archive",
    "project.restore": "project.restore",
    "project.link": "project.link",
    "project.unlink": "project.unlink",
    "project.open_review": "project.open_review",
    "project.get_delta": "project.get_delta",
    "project.decide_proposal": "project.decide_proposal",
    "project.accept_review": "project.accept_review",
    "project.list_updates": "project.list_updates",
    "project.draft_update": "project.draft_update",
    "project.update_draft": "project.update_draft",
    "project.publish_update": "project.publish_update",
    "project.item.list": "project.item.list",
    "project.item.create": "project.item.create",
    "project.item.update": "project.item.update",
    "project.item.transition": "project.item.transition",
    "project.resource.list": "project.resource.list",
    "project.resource.add": "project.resource.add",
    "project.resource.remove": "project.resource.remove",
}

#: The tools that took ``_require_id`` before PHILO-9-01 keep its refusal
#: (``project_request_invalid``) for an empty id.
_REQUIRED_IDS: dict[str, tuple[str, ...]] = {
    "project.get": ("project_id",), "project.get_room": ("project_id",),
    "project.update": ("project_id",), "project.archive": ("project_id",),
    "project.restore": ("project_id",), "project.link": ("project_id", "meeting_id"),
    "project.unlink": ("project_id", "meeting_id"), "project.open_review": ("project_id",),
    "project.get_delta": ("project_id",),
    "project.decide_proposal": ("project_id", "review_id", "proposal_id"),
    "project.accept_review": ("project_id", "review_id"),
    "project.list_updates": ("project_id",), "project.draft_update": ("project_id",),
    "project.update_draft": ("update_id",), "project.publish_update": ("update_id",),
}

#: The seven new tools: their published input schema is the charter's table
#: and is checked here, at the MCP edge (a refusal is ``validation``).
_NEW_ROOM_TOOLS = frozenset({
    "project.item.list", "project.item.create", "project.item.update", "project.item.transition",
    "project.resource.list", "project.resource.add", "project.resource.remove",
})


def _ops():
    """The hub's bound registry, else one bound over this family's bare services."""
    from holdspeak import operations
    from holdspeak.services.kernel_read_service import KernelReadService

    return operations.for_runtime(
        project_service=_service,
        project_delta_service=_delta_service,
        project_update_service=_update_service,
        kernel_read_service=lambda: runtime_service(
            "kernel_read_service", lambda: KernelReadService(db_or(get_database))),
    )


def _room_arguments(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    args = dict(arguments)
    for key in _REQUIRED_IDS.get(name, ()):
        args[key] = _require_id(arguments, key)
    if name == "project.list":
        # The tool answered only a truthy include_archived before.
        args = {"include_archived": True} if arguments.get("include_archived") else {}
    if name == "project.draft_update":
        args["generator"] = str(arguments.get("generator") or "deterministic").strip()
    return args


def _room_tool(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    from jsonschema import Draft202012Validator

    from holdspeak.operations import OperationRefused

    if name in _NEW_ROOM_TOOLS:
        schema = next(tool["inputSchema"] for tool in TOOLS if tool["name"] == name)
        error = next(iter(Draft202012Validator(schema).iter_errors(arguments)), None)
        if error is not None:
            where = ".".join(str(part) for part in error.absolute_path)
            raise ValidationError(f"Invalid arguments for {name}: {where + ': ' if where else ''}{error.message}",
                                  code="validation")
    operation = ROOM_TOOL_OPERATIONS[name]
    try:
        if operation == "desk.needs_you":  # pragma: no cover - tools.py owns desk.needs_you
            raise LookupError(name)
        result = _ops().invoke(principal, operation, _room_arguments(name, arguments))
    except OperationRefused as exc:
        # The charter's code for an argument the contract refuses is validation.
        code = "validation" if exc.code == "invalid_arguments" else exc.code
        raise ValidationError(exc.detail, code=code, context={"refusal": exc.code}) from exc
    except PublishedUpdateError as exc:
        raise ConflictError(str(exc), code="published_update") from exc
    except ServiceError:
        raise
    except ValueError as exc:
        # add_resource / remove_resource refuse a bad reference or relationship
        # with a ValueError; the charter maps it to validation.
        raise ValidationError(str(exc), code="validation") from exc
    return _room_envelope(name, result)


def _room_envelope(name: str, result: Any) -> Any:
    """The envelope each tool answered before PHILO-9-01 (unchanged)."""
    if name == "project.list":
        return {"projects": result}
    if name in {"project.create", "project.update", "project.restore"}:
        return {"success": True, "project": result}
    if name in {"project.archive", "project.link", "project.unlink"}:
        return {"success": True}
    if name == "project.list_updates":
        return {"updates": result}
    if name in {"project.draft_update", "project.update_draft", "project.publish_update"}:
        return {"success": True, "update": result}
    if name in {"project.item.create", "project.item.update", "project.item.transition"}:
        return {"success": True, "item": result}
    if name == "project.resource.list":
        return {"resources": result}
    if name == "project.resource.add":
        return {"resource": result}
    if name == "project.resource.remove":
        return {"success": True, "removed": result}
    return result


def _describe_from_operations() -> None:
    """F12: a Room tool's words ARE its operation's words (one source).

    The tool keeps its published argument types; its description and each
    argument's description come from the declared operation.
    """
    from holdspeak import operations

    declared = {d.name: d for d in operations.DESCRIPTORS}
    for tool in TOOLS:
        operation = ROOM_TOOL_OPERATIONS.get(tool["name"])
        if operation is None:
            continue
        descriptor = declared[operation]
        tool["description"] = descriptor.description
        props = descriptor.args_schema.get("properties", {})
        for key, spec in tool["inputSchema"].get("properties", {}).items():
            words = (props.get(key) or {}).get("description")
            if words:
                spec["description"] = words


_describe_from_operations()


# ── MCP-007: PROJECT_PALETTE ─────────────────────────────────────────
# The scoped allow-list for agent sessions.  Contains exactly the tools
# in this family (project.* + provider.*); the SS15 acceptance scenario
# needs no companions from other families -- every point (setup, watch,
# steward, delta, review) resolves within this family's tools.
PROJECT_PALETTE: frozenset[str] = frozenset(t["name"] for t in TOOLS)


__all__ = ["TOOLS", "PROJECT_PALETTE", "dispatch"]


# HS-200-45 R1: _service now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# delta_service= (mutual composition with the room review section). Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _service():
    """The hub's live service, else the bare composition above."""
    return runtime_service("project_service", lambda: _build_service())


# HS-200-45 R1: _delta_service now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the evidence collector AND an attached project_service. Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _delta_service():
    """The hub's live service, else the bare composition above."""
    return runtime_service("project_delta_service", lambda: _build_delta_service())


# HS-200-45 R1: _update_service now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the kernel broker, so a model drafter is reachable. Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _update_service():
    """The hub's live service, else the bare composition above."""
    return runtime_service("project_update_service", lambda: _build_update_service())


# HS-200-45 R1: _steward_service now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the door_service, so a steward run can open a door. Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _steward_service():
    """The hub's live service, else the bare composition above."""
    return runtime_service("project_steward_service", lambda: _build_steward_service())


# HS-200-45 R1: _connections_service now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the hub's gh/acli runners and its assignment service. Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _connections_service():
    """The hub's live service, else the bare composition above."""
    return runtime_service("connections_service", lambda: _build_connections_service())


# HS-200-45 R1: _setup_service now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the hub's gh/acli runners. Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _setup_service():
    """The hub's live service, else the bare composition above."""
    return runtime_service("project_setup_service", lambda: _build_setup_service())


# HS-200-45 R1: _watch_service now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the hub's gh watch kwargs (_gh_watch_service_kwargs). Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _watch_service():
    """The hub's live service, else the bare composition above."""
    return runtime_service("watch_service", lambda: _build_watch_service())


# HS-200-45 R1: _github_adapter now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the hub's _gh_runner. Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _github_adapter():
    """The hub's live service, else the bare composition above."""
    return runtime_service("github_provider", lambda: _build_github_adapter())


# HS-200-45 R1: _jira_adapter now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the hub's _acli_runner. Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _jira_adapter():
    """The hub's live service, else the bare composition above."""
    return runtime_service("jira_provider", lambda: _build_jira_adapter())


# HS-200-45 R1: _confluence_adapter now asks the ONE composition root first. Inside the hub
# that returns the instance the HTTP routes use -- the one composed with
# the hub's acli runner. Outside a hub (a unit test's bare root, or the
# standalone diagnosis hatch) the root holds nothing and the bare builder above
# runs, which is the same object the pre-HS-200-45 code produced.
def _confluence_adapter():
    """The hub's live service, else the bare composition above."""
    return runtime_service("confluence_provider", lambda: _build_confluence_adapter())
