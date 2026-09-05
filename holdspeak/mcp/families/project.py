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
        "description": "Manually evaluate a graduated watch: snapshot, diff, transitions, observations.",
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

def _service():
    """Compose the same ProjectService the web application edge uses."""
    from holdspeak.services.project_service import ProjectService
    db = get_database()
    return ProjectService(db)


def _delta_service():
    """Compose ProjectDeltaService (same wiring as web context)."""
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.services.project_service import ProjectService
    db = get_database()
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


def _update_service():
    """Compose ProjectUpdateService (same wiring as web context)."""
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_update_service import ProjectUpdateService
    db = get_database()
    ps = ProjectService(db)
    return ProjectUpdateService(db, project_service=ps)


def _steward_service():
    """Compose ProjectStewardService (same wiring as web context)."""
    from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_steward_service import ProjectStewardService
    from holdspeak.services.project_update_service import ProjectUpdateService
    db = get_database()
    ps = ProjectService(db)
    collector = ProjectEvidenceCollector(db)
    delta = ProjectDeltaService(db, collector=collector, project_service=ps)
    us = ProjectUpdateService(db, project_service=ps)
    return ProjectStewardService(
        db, collector=collector, delta=delta,
        update_service=us, project_service=ps,
    )


def _connections_service():
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


def _setup_service():
    """Compose ProjectSetupService (same wiring as web context)."""
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_setup_service import ProjectSetupService
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import default_snapshot_fetcher
    db = get_database()
    ps = ProjectService(db)
    ga = _github_adapter()
    ja = _jira_adapter()
    fetcher = default_snapshot_fetcher(jira_adapter=ja)
    ws = WatchService(db, snapshot_fetcher=fetcher)
    return ProjectSetupService(
        db, project_service=ps, watch_service=ws,
        github_adapter=ga,
        jira_adapter=ja,
        connections_service=_connections_service(),
    )


def _watch_service():
    """Compose WatchService (same wiring as web context, HS-166-03 rider-a)."""
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import default_snapshot_fetcher
    db = get_database()
    ja = _jira_adapter()
    fetcher = default_snapshot_fetcher(jira_adapter=ja)
    return WatchService(db, snapshot_fetcher=fetcher)


def _github_adapter():
    """Return the GitHubProviderAdapter or None (same as web context)."""
    from holdspeak.services.github_provider import GitHubProviderAdapter
    db = get_database()
    try:
        return GitHubProviderAdapter(db)
    except Exception:
        return None


def _jira_adapter():
    """Return the JiraProviderAdapter or None (same as web context)."""
    from holdspeak.services.jira_provider import JiraProviderAdapter
    db = get_database()
    try:
        return JiraProviderAdapter(db)
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
    db = get_database()
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

    # ── reads (HS-165-01) ────────────────────────────────────────────

    if name == "project.list":
        svc = _service()
        filters: dict[str, Any] = {}
        if arguments.get("include_archived"):
            filters["include_archived"] = True
        return {"projects": svc.list_projects(principal, filters)}

    if name == "project.get":
        project_id = _require_id(arguments, "project_id")
        return _service().get_project(principal, project_id)

    if name == "project.get_room":
        project_id = _require_id(arguments, "project_id")
        return _service().room(principal, project_id)

    # ── lifecycle commands (HS-165-02) ───────────────────────────────
    # Mirrors: holdspeak/web/routes/projects.py

    if name == "project.create":
        # Web parity: projects.py:63 api_create_project
        # Service seam: ProjectService.create_project
        payload = dict(arguments)
        cmd_id = payload.pop("command_id", None)
        result = _service().create_project(
            principal, payload, command_id=cmd_id,
        )
        return {"success": True, "project": result}

    if name == "project.update":
        # Web parity: projects.py:88 api_update_project
        # Service seam: ProjectService.update_project
        project_id = _require_id(arguments, "project_id")
        patch = arguments.get("patch") or {}
        expected_rev = arguments.get("expected_revision")
        cmd_id = arguments.get("command_id")
        result = _service().update_project(
            principal, project_id, patch,
            expected_revision=expected_rev,
            command_id=cmd_id,
        )
        return {"success": True, "project": result}

    if name == "project.archive":
        # Web parity: projects.py:108 api_archive_project
        # Service seam: ProjectService.archive_project
        project_id = _require_id(arguments, "project_id")
        expected_rev = arguments.get("expected_revision")
        cmd_id = arguments.get("command_id")
        _service().archive_project(
            principal, project_id,
            expected_revision=expected_rev,
            command_id=cmd_id,
        )
        return {"success": True}

    if name == "project.restore":
        # Web parity: projects.py:122 api_restore_project
        # Service seam: ProjectService.restore_project
        project_id = _require_id(arguments, "project_id")
        expected_rev = arguments.get("expected_revision")
        cmd_id = arguments.get("command_id")
        result = _service().restore_project(
            principal, project_id,
            expected_revision=expected_rev,
            command_id=cmd_id,
        )
        return {"success": True, "project": result}

    # ── link / unlink (meeting association) ──────────────────────────
    # Mirrors: projects.py:193 api_associate_meeting, :207 api_disassociate_meeting

    if name == "project.link":
        # Service seam: ProjectService.associate_meeting
        project_id = _require_id(arguments, "project_id")
        meeting_id = _require_id(arguments, "meeting_id")
        expected_rev = arguments.get("expected_revision")
        cmd_id = arguments.get("command_id")
        _service().associate_meeting(
            principal, project_id, meeting_id,
            expected_revision=expected_rev,
            command_id=cmd_id,
        )
        return {"success": True}

    if name == "project.unlink":
        # Service seam: ProjectService.disassociate_meeting
        project_id = _require_id(arguments, "project_id")
        meeting_id = _require_id(arguments, "meeting_id")
        expected_rev = arguments.get("expected_revision")
        cmd_id = arguments.get("command_id")
        _service().disassociate_meeting(
            principal, project_id, meeting_id,
            expected_revision=expected_rev,
            command_id=cmd_id,
        )
        return {"success": True}

    # ── review commands ──────────────────────────────────────────────
    # Mirrors: holdspeak/web/routes/project_reviews.py

    if name == "project.open_review":
        # Web parity: project_reviews.py:37 open_review
        # Service seam: ProjectDeltaService.open_review
        project_id = _require_id(arguments, "project_id")
        return _delta_service().open_review(principal, project_id)

    if name == "project.get_delta":
        # Web parity: project_reviews.py:89 get_delta
        # Service seam: ProjectDeltaService._find_open_review + _load_frozen_window
        # (same private seams the Web route uses -- parity-warts-included ruling)
        project_id = _require_id(arguments, "project_id")
        svc = _service()
        svc._require_project(project_id)
        delta_svc = _delta_service()
        open_review = delta_svc._find_open_review(project_id)
        if open_review is not None:
            return delta_svc._load_frozen_window(open_review)
        # Honest empty state (WEB-STA-004) -- parity with the Web
        # route's empty branch incl. source_coverage (counsel S-2).
        db = get_database()
        room_fields = db.projects.get_project_room_fields(project_id)
        last_accepted_at = (room_fields or {}).get("last_review_at")
        source_coverage = None
        try:
            reviews = delta_svc._db.project_observations.list_reviews(
                project_id, status="accepted", limit=1,
            )
            if reviews:
                manifest_json = reviews[0].get("source_manifest_json", "{}")
                manifest = (
                    json.loads(manifest_json)
                    if isinstance(manifest_json, str) else manifest_json
                )
                source_coverage = {
                    k: v.get("state", "unknown")
                    for k, v in manifest.items()
                }
        except Exception:
            pass
        return {
            "open_review": None,
            "last_accepted_at": last_accepted_at,
            "source_coverage": source_coverage,
        }

    if name == "project.decide_proposal":
        # Web parity: project_reviews.py:144 decide_proposal
        # Service seam: ProjectDeltaService.decide_proposal
        # COPIED ROUTE GLUE: proposal-belongs-to-review check (project_reviews.py:157-174)
        project_id = _require_id(arguments, "project_id")
        review_id = _require_id(arguments, "review_id")
        proposal_id = _require_id(arguments, "proposal_id")
        verb = str(arguments.get("verb") or "").strip()
        patch = arguments.get("patch")
        deferred_until = arguments.get("deferred_until")
        cmd_id = arguments.get("command_id")

        # Route glue: verify proposal belongs to this review
        db = get_database()
        proposal = db.project_observations.get_proposal(proposal_id)
        if proposal is None:
            raise NotFound("proposal", proposal_id)
        if proposal.get("review_window_key") != review_id:
            raise ServiceError(
                "not_found",
                f"Proposal {proposal_id!r} does not belong to review {review_id!r}",
                context={"proposal_id": proposal_id, "review_id": review_id},
            )

        return _delta_service().decide_proposal(
            principal, project_id, proposal_id, verb,
            patch=patch,
            deferred_until=deferred_until,
            command_id=cmd_id,
        )

    if name == "project.accept_review":
        # Web parity: project_reviews.py:206 accept_review
        # Service seam: ProjectDeltaService.accept_review
        project_id = _require_id(arguments, "project_id")
        review_id = _require_id(arguments, "review_id")
        cmd_id = arguments.get("command_id")
        return _delta_service().accept_review(
            principal, project_id, review_id,
            command_id=cmd_id,
        )

    # ── update commands ──────────────────────────────────────────────
    # Mirrors: holdspeak/web/routes/project_updates.py

    if name == "project.list_updates":
        # Web parity: project_updates.py:48 api_list_updates
        # Service seam: ProjectUpdateService.list_updates
        project_id = _require_id(arguments, "project_id")
        lifecycle = arguments.get("lifecycle")
        updates = _update_service().list_updates(
            principal, project_id, lifecycle=lifecycle,
        )
        return {"updates": updates}

    if name == "project.draft_update":
        # Web parity: project_updates.py:68 api_draft_update
        # Service seam: ProjectUpdateService.draft_update_command
        project_id = _require_id(arguments, "project_id")
        generator = str(arguments.get("generator") or "deterministic").strip()
        cmd_id = arguments.get("command_id")
        result = _update_service().draft_update_command(
            principal, project_id,
            generator=generator, command_id=cmd_id,
        )
        return {"success": True, "update": result}

    if name == "project.update_draft":
        # Web parity: project_updates.py:94 api_save_update
        # Service seam: ProjectUpdateService.save_update
        update_id = _require_id(arguments, "update_id")
        body_md = arguments.get("body_md")
        cmd_id = arguments.get("command_id")
        try:
            result = _update_service().save_update(
                principal, update_id,
                body_md=body_md, command_id=cmd_id,
            )
        except PublishedUpdateError as exc:
            raise ConflictError(
                str(exc),
                code="published_update",
            ) from exc
        return {"success": True, "update": result}

    if name == "project.publish_update":
        # Web parity: project_updates.py:160 api_publish_update
        # Service seam: ProjectUpdateService.publish_update
        update_id = _require_id(arguments, "update_id")
        cmd_id = arguments.get("command_id")
        try:
            result = _update_service().publish_update(
                principal, update_id, command_id=cmd_id,
            )
        except PublishedUpdateError as exc:
            raise ConflictError(
                str(exc),
                code="published_update",
            ) from exc
        return {"success": True, "update": result}

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
        db = get_database()
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
            return {
                "success": False,
                "code": "scheduler_not_wired",
                "message": "The conductor's scheduler services are not wired "
                           "(set_scheduler_services has not been called)",
            }

        eval_outcomes = wired_watch.evaluate_due(principal) if wired_watch is not None else []
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
            get_database().automations.update_watch_spec(
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


# ── MCP-007: PROJECT_PALETTE ─────────────────────────────────────────
# The scoped allow-list for agent sessions.  Contains exactly the tools
# in this family (project.* + provider.*); the SS15 acceptance scenario
# needs no companions from other families -- every point (setup, watch,
# steward, delta, review) resolves within this family's tools.
PROJECT_PALETTE: frozenset[str] = frozenset(t["name"] for t in TOOLS)


__all__ = ["TOOLS", "PROJECT_PALETTE", "dispatch"]
