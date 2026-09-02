"""Project Room MCP twin: read + command tools over ProjectService (MCP-001 parity).

HS-165-01: read tools (project.list / get / get_room).
HS-165-02: command tools — the same verbs, the same laws.  Every command
tool is a THIN driver over the exact service seam the Web route calls:
no SQL, no verb re-implementation.  command_id replay safety (MCP-002)
rides the services' own idempotency machinery.
"""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.db.updates import PublishedUpdateError
from holdspeak.principals import Principal
from holdspeak.services.errors import ConflictError, NotFound, ServiceError, ValidationError


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
        "description": "Get the coherent room projection for one project (identity, items, meetings, resources, changes, review).",
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


# ── Dispatch ─────────────────────────────────────────────────────────

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
        # Honest empty state (WEB-STA-004)
        db = get_database()
        room_fields = db.projects.get_project_room_fields(project_id)
        last_accepted_at = (room_fields or {}).get("last_review_at")
        return {
            "open_review": None,
            "last_accepted_at": last_accepted_at,
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

    raise LookupError(name)


__all__ = ["TOOLS", "dispatch"]
