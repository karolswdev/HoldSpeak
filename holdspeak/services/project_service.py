"""Transport-neutral project and relationship operations (HS-123-05).

HS-158-02 graduation: every accepted write increments projects.revision
exactly once, appends a project_changes row and a ServiceEventLedger event
in the same transaction (DOM-003, DOM-004, API-004).  Optional
expected_revision / command_id enforce optimistic concurrency (API-001)
and idempotent replay (API-002, DOM-010).  Absent params = legacy behavior
(API-006).  HS-173-08 / 158 S-1: the four legacy-wrapping methods
(add/remove_resource, associate/disassociate_meeting) folded from three
separate transactions into one atomic transaction each.

HS-158-03: item commands under the revision law (create/update/transition/
list).  Items are Project-OWNED records (SS5.3), not citizens (SS3.2).
changed_refs carries ``project:<id>``; the item id rides in the result
payload.  Event kind is ``project.updated`` (SS10 has no item event kind).
"""
from __future__ import annotations

import logging
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..db.core import Database
from ..db.relationships import qualified_ref
from ..logging_config import get_logger
from ..meeting_aftercare import compute_project_since_last_meeting
from ..principals import Principal, PrincipalKind
from ..project_contracts import (
    CommandResultEnvelope,
    ProjectError,
    ProjectErrorCode,
    ResultKind,
    generate_pchg_id,
    generate_pcmd_id,
    generate_pitem_id,
    generate_psrc_id,
)
from ..refs import format as format_ref, parse as parse_ref
from .errors import ConflictError, NotFound, ValidationError
from .project_setup_service import CADENCE_PRESETS
from .service_event_ledger import ServiceEventLedger

_log = get_logger("services.project_service")


# ── HS-175 counsel C8: the hub's local week, one helper ──────────────
#
# Calendar events are stored UTC (``YYYY-MM-DDTHH:MM:SSZ``); the owner's
# week is his local week.  Every "this week" read in this service and the
# calendar sources route goes through this helper so the Monday boundary
# is the hub's local Monday (``datetime.now().astimezone()``), consistent
# with the arrival's strip.


def local_now(now: datetime | None = None) -> datetime:
    """The hub's local, tz-aware now (or ``now`` made aware in local tz)."""
    if now is None:
        return datetime.now().astimezone()
    if now.tzinfo is None:
        return now.astimezone()
    return now


def localize(wall: datetime) -> datetime:
    """A naive LOCAL wall-clock -> aware, with THAT instant's offset.

    Counsel re-read condition 4 (DST): ``datetime.now().astimezone()`` yields
    a FIXED offset; arithmetic in it crosses a DST edge an hour off.  A
    naive value's ``.astimezone()`` consults the system zone's rules for the
    instant itself, so every bound carries its own true offset.
    """
    return wall.replace(tzinfo=None).astimezone()


def local_week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    """(local Monday 00:00, next local Monday 00:00) as aware datetimes,
    each localized per instant (DST-safe)."""
    current = local_now(now)
    wall = current.replace(tzinfo=None)
    monday_wall = (wall - timedelta(days=wall.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    return localize(monday_wall), localize(monday_wall + timedelta(days=7))


def utc_z(value: datetime) -> str:
    """Aware datetime -> the stored calendar_events form ``...Z``."""
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def aware_iso(value: Any) -> str | None:
    """Normalize a stored timestamp to an offset-carrying ISO string.

    SQLite's ``datetime('now')`` writes naive UTC (``YYYY-MM-DD HH:MM:SS``);
    the browser's ``new Date()`` would read that as LOCAL time and print
    the wrong clock (counsel H4-1: ``CHECKED 23:47`` beside ``READ 17:48``).
    A naive value is UTC here by construction; an aware value passes
    through.  ``None``/empty stays ``None``.
    """
    if value is None or value == "":
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat(timespec="seconds")


# ── M-1 finalize mapping tables (HS-161-07 counsel) ─────────────────
#
# _PROVIDER_TO_CONNECTOR: the watch table's connector_id is "gh", not
# "github".  Moved from the loop body to module level per counsel N-2.
#
# _SUBJECT_TO_QUERY_KIND: WatchSpec@1 subject.kind is singular
# ("pull_request"), but GitHubWatchSource.snapshot demands the plural
# wire form ("pull_requests").  The mapping lives here rather than in
# the spec so the spec vocabulary stays domain-level.
_PROVIDER_TO_CONNECTOR: dict[str, str] = {
    "github": "gh", "jira": "jira", "meeting": "meeting",
}

_SUBJECT_TO_QUERY_KIND: dict[str, str] = {
    "pull_request": "pull_requests",
    "issue": "issues",
    "branch_ci": "branch_ci",  # HS-169-04: CI on the base branch
    "meeting": "meetings",  # HS-175-04: meeting watch adapter
}


# ── Closed Project Room vocabularies (HS-158-02, SRS WEB §4) ─────────

# Project lifecycle: closed vocabulary per SRS WEB-LC §4.
# 'archived' is EXCLUDED — it is a storage state managed by archive_project/
# restore_project, not a user-settable lifecycle value via PATCH.
PROJECT_LIFECYCLES: frozenset[str] = frozenset({
    "proposed", "active", "paused", "complete", "cancelled",
})

# Maximum lengths for free-text room fields.
_POSTURE_MAX = 64
_POSTURE_REASON_MAX = 500
_SLUG_MAX = 64

# ── Closed item vocabularies (HS-158-03) ──────────────────────────────

# Severity: nullable; validated on write.
SEVERITY_LEVELS: frozenset[str] = frozenset({
    "critical", "high", "medium", "low",
})

# Explicit rank for focus ordering (CASE expression: highest first).
SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

# Item types and their closed lifecycle vocabularies.
ITEM_TYPES: frozenset[str] = frozenset({
    "milestone", "risk", "dependency", "signal", "workstream",
})

ITEM_LIFECYCLES: dict[str, tuple[str, ...]] = {
    "milestone": ("planned", "reached", "missed", "dropped"),
    "risk": ("open", "mitigated", "accepted", "closed"),
    "dependency": ("healthy", "at_risk", "broken", "resolved"),
    "signal": ("active", "retired"),
    "workstream": ("active", "paused", "done"),
}

# Default lifecycle per item type (the initial state on create).
ITEM_DEFAULT_LIFECYCLE: dict[str, str] = {
    "milestone": "planned",
    "risk": "open",
    "dependency": "healthy",
    "signal": "active",
    "workstream": "active",
}

# Provenance kinds (P1 = owner only).
PROVENANCE_KINDS: frozenset[str] = frozenset({"owner"})

# ── Closed details_json schemas per item_type (DB-004) ────────────────
#
# Each entry: field_name -> (required, validator_fn).
# Unknown fields are refused.  Common fields (title, summary, lifecycle,
# severity, owner_ref, due_at, sort_key) are COLUMNS, not in details_json.

def _is_str(v: Any) -> bool:
    return isinstance(v, str)

def _is_str_or_none(v: Any) -> bool:
    return v is None or isinstance(v, str)

def _is_number_or_none(v: Any) -> bool:
    return v is None or isinstance(v, (int, float))

_DETAILS_SCHEMAS: dict[str, dict[str, tuple[bool, Any]]] = {
    "milestone": {
        # completion_evidence_refs: optional list of ref strings
        "completion_evidence_refs": (False, lambda v: v is None or (isinstance(v, list) and all(isinstance(x, str) for x in v))),
    },
    "risk": {
        "likelihood": (True, _is_str),
        "impact": (True, _is_str),
        "mitigation": (False, _is_str_or_none),
    },
    "dependency": {
        "direction": (True, lambda v: v in ("upstream", "downstream")),
        "counterpart_ref": (True, _is_str),
        "required_by": (False, _is_str_or_none),
        "confidence": (False, _is_str_or_none),
    },
    "signal": {
        "metric": (True, _is_str),
        "unit": (False, _is_str_or_none),
        "latest_value": (False, _is_number_or_none),
        "source_ref": (False, _is_str_or_none),
        "observed_at": (False, _is_str_or_none),
    },
    "workstream": {
        # No type-specific extras.
    },
}

# ── Room projection constants (HS-158-04, DB-005/NFR-001) ───────────────
# WEB-NOW-006 spirit: the focus block shows the top-N most urgent items.
ROOM_FOCUS_CAP: int = 5
# Recent changes shown in the room projection.
ROOM_CHANGES_CAP: int = 10

# Absent-section marker for domains not yet built (Art VI, NFR-006).
_ABSENT_SECTION: dict[str, str] = {"state": "absent", "reason": "not_yet_built"}


def _format_age(iso_str: str, now: datetime) -> str:
    """Format an ISO timestamp as a human-readable age token."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00").rstrip("Z"))
        delta = now - dt.replace(tzinfo=None)
        days = delta.days
        if days > 0:
            return f"{days} DAYS"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours} HOURS"
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes} MIN AGO"
        return "JUST NOW"
    except (ValueError, TypeError):
        return ""


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash of a command's request payload (API-002)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _envelope_to_dict(env: CommandResultEnvelope) -> dict[str, Any]:
    """Serialize an envelope to a JSON-safe dict for storage/response."""
    return {
        "result_kind": env.result_kind.value,
        "project_id": env.project_id,
        "project_revision": env.project_revision,
        "changed_refs": [str(r) for r in env.changed_refs],
    }


@observe_service
class ProjectService:
    """The durable project boundary; routes only parse and serialize."""

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None,
                 delta_service: Any = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        self._ledger = ServiceEventLedger(db)
        self._delta_service = delta_service

    # ── reads (unchanged) ────────────────────────────────────────────

    def list_projects(self, principal: Principal, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        return [self._project_payload(project) for project in self._db.projects.list_projects(
            include_archived=bool(filters.get("include_archived", False))
        )]

    def get_project(self, principal: Principal, project_id: str) -> dict[str, Any]:
        return self._project_payload(self._require_project(project_id))

    def list_briefings(self, principal: Principal, project_id: str, limit: int = 50) -> dict[str, Any]:
        self._require_project(project_id)
        clean_limit = max(1, min(int(limit), 200))
        annotations = self._db.activity.list_activity_annotations(
            source_connector_id="meeting_context", annotation_type="meeting_context_briefing",
            limit=max(clean_limit * 4, 100),
        )
        rows = [{"id": ann.id, "title": ann.title, "value": ann.value,
                 "created_at": ann.created_at.isoformat(), "updated_at": ann.updated_at.isoformat()}
                for ann in annotations if isinstance(ann.value, dict) and ann.value.get("project_id") == project_id]
        return {"project_id": project_id, "briefings": rows[:clean_limit]}

    def list_meetings(self, principal: Principal, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return self._db.projects.get_project_meetings(project_id, limit=limit, offset=offset)

    def list_resources(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [row.to_dict() for row in self._db.project_relationships.list_for_project(project_id)]

    def list_resource_relationships(self, principal: Principal, resource_ref: str) -> dict[str, Any]:
        ref = qualified_ref(resource_ref)
        placement = self._db.directory_memberships.get(ref)
        return {"resource_ref": ref, "zone": placement.to_dict() if placement else None,
                "knowledge": [row.to_dict() for row in self._db.knowledge_memberships.list_for_resource(ref)],
                "projects": [row.to_dict() for row in self._db.project_relationships.list_for_resource(ref)],
                "explanations": {"zone": "Where this object lives; exactly one Zone or the Desk root.",
                                 "knowledge": "Reusable collections this object informs; membership does not move it.",
                                 "projects": "Work this object supports; a relationship does not file or copy it."}}

    def list_meeting_projects(self, principal: Principal, meeting_id: str) -> list[dict[str, Any]]:
        self._require_meeting(meeting_id)
        return self._db.projects.get_meeting_projects(meeting_id)

    def since_last_meeting(self, principal: Principal, project_id: str) -> dict[str, Any]:
        self._require_project(project_id)
        return compute_project_since_last_meeting(self._db, project_id) or {}

    def summary(self, principal: Principal, project_id: str) -> dict[str, Any]:
        self._require_project(project_id)
        return self._db.projects.get_project_summary(project_id)

    def list_action_items(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [{"id": item.id, "task": item.task, "owner": item.owner, "due": item.due,
                 "status": item.status, "review_state": item.review_state,
                 "source_timestamp": item.source_timestamp, "meeting_id": item.meeting_id,
                 "meeting_title": item.meeting_title, "meeting_date": item.meeting_date.isoformat(),
                 "created_at": item.created_at.isoformat(),
                 "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                 "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None}
                for item in self._db.projects.get_project_action_items(project_id)]

    def list_artifacts(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [{"id": item.id, "meeting_id": item.meeting_id, "artifact_type": item.artifact_type,
                 "title": item.title, "body_markdown": item.body_markdown, "confidence": item.confidence,
                 "status": item.status, "plugin_id": item.plugin_id, "created_at": item.created_at.isoformat()}
                for item in self._db.projects.get_project_artifacts(project_id)]

    # ── room projection (HS-158-04, SS6.2) ────────────────────────────

    def room(self, principal: Principal, project_id: str) -> dict[str, Any]:
        """Coherent, revision-stamped room projection (SS6.2, HS-158-04).

        Returns one dict with every section the first useful render needs.
        Per-section fault isolation (NFR-003): each sub-read is wrapped;
        a failure degrades that section without failing the response.
        404 only when the project itself is missing.

        observed_at is derived from project.updated_at (fully deterministic:
        two reads with no writes in between produce byte-identical payloads).

        Focus ordering (DB-005): severity DESC NULLS LAST, due_at ASC
        NULLS LAST, sort_key ASC NULLS LAST, created_at ASC, id ASC.
        """
        project = self._require_project(project_id)
        room_fields = self._db.projects.get_project_room_fields(project_id)

        # Orientation: identity + SS5.1 fields + revision + is_archived
        orientation = self._project_payload(project)
        revision = 0
        if room_fields:
            orientation["purpose"] = room_fields["purpose"]
            orientation["outcome_text"] = room_fields["outcome_text"]
            orientation["owner_ref"] = room_fields["owner_ref"]
            orientation["lifecycle"] = room_fields["lifecycle"]
            orientation["posture"] = room_fields["posture"]
            orientation["posture_reason"] = room_fields["posture_reason"]
            orientation["start_at"] = room_fields["start_at"]
            orientation["target_at"] = room_fields["target_at"]
            orientation["review_cadence_json"] = room_fields["review_cadence_json"]
            orientation["next_review_at"] = room_fields["next_review_at"]
            orientation["template_key"] = room_fields["template_key"]
            orientation["modules_json"] = room_fields["modules_json"]
            orientation["revision"] = room_fields["revision"]
            orientation["last_review_id"] = room_fields["last_review_id"]
            orientation["last_review_at"] = room_fields["last_review_at"]
            revision = room_fields["revision"] or 0

        # observed_at: derived from project.updated_at for full determinism
        observed_at = project.updated_at.isoformat()

        # HS-169-04: the four questions' wire data
        target_at = (room_fields or {}).get("target_at")
        room_read_at = (room_fields or {}).get("room_read_at")

        # HS-169-04: build sources first so nextCheckAt can be hoisted
        sources_section = self._room_section(
            "sources", lambda: self._read_room_sources(project_id))
        # Top-level nextCheckAt: from sources section when ok
        next_check_at = (
            sources_section.get("nextCheckAt")
            if sources_section.get("state") == "ok"
            else None
        )

        return {
            "project_id": project_id,
            "revision": revision,
            "observed_at": observed_at,
            "nextCheckAt": next_check_at,
            "project": orientation,
            "items": self._room_section(
                "items", lambda: self._read_room_items(project_id)),
            "meetings": self._room_section(
                "meetings", lambda: self._read_room_meetings(
                    principal, project_id, project)),
            "resources": self._room_section(
                "resources", lambda: self._read_room_resources(project_id)),
            "changes": self._room_section(
                "changes", lambda: self._read_room_changes(project_id)),
            "review": (
                self._room_section(
                    "review", lambda: self._read_room_review(project_id))
                if self._delta_service is not None
                else dict(_ABSENT_SECTION)
            ),
            # HS-169-04: the four questions (additive)
            "needsYou": self._room_section(
                "needsYou", lambda: self._read_room_needs_you(project_id)),
            "sources": sources_section,
            "health": self._room_section(
                "health", lambda: self._read_room_health(project_id, target_at)),
            "sinceRead": self._room_section(
                "sinceRead", lambda: self._read_room_since_read(project_id, room_read_at)),
            "decisions": self._room_section(
                "decisions", lambda: self._read_room_decisions(project_id)),
            "commitments": self._room_section(
                "commitments", lambda: self._read_room_commitments(project_id)),
            "target": self._room_section(
                "target", lambda: self._read_room_target(target_at)),
            "updates": dict(_ABSENT_SECTION),
            "steward": dict(_ABSENT_SECTION),
            # HS-174-04: pipeline receipts scoped to this project.
            "receipts": self._room_section(
                "receipts", lambda: self._read_room_receipts(project_id)),
        }

    # ── room sub-readers (fault-isolated) ────────────────────────────

    @staticmethod
    def _room_section(name: str, fn: Any) -> dict[str, Any]:
        """Run *fn* and tag the result with state=ok, or return degraded."""
        try:
            result = fn()
            result["state"] = "ok"
            return result
        except Exception as exc:
            _log.warning("room section %s degraded: %s", name, exc)
            return {"state": "degraded", "error_code": f"{name}_read_failed"}

    def _read_room_items(self, project_id: str) -> dict[str, Any]:
        """Focus block: bounded top-N items + total counts per type."""
        with self._db._connection() as conn:
            count_rows = conn.execute(
                "SELECT item_type, COUNT(*) as cnt FROM project_items "
                "WHERE project_id = ? GROUP BY item_type",
                (project_id,),
            ).fetchall()
            totals_by_type = {row["item_type"]: row["cnt"] for row in count_rows}
            total = sum(totals_by_type.values())

            # Focus: bounded, deterministically ordered (DB-005)
            # HS-158-03: explicit CASE rank for severity (highest first,
            # nulls last) instead of free-text DESC over the column.
            focus_rows = conn.execute(
                """
                SELECT * FROM project_items WHERE project_id = ?
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 0
                        WHEN 'high'     THEN 1
                        WHEN 'medium'   THEN 2
                        WHEN 'low'      THEN 3
                        ELSE 999
                    END ASC,
                    due_at IS NULL, due_at ASC,
                    sort_key IS NULL, sort_key ASC,
                    created_at ASC,
                    id ASC
                LIMIT ?
                """,
                (project_id, ROOM_FOCUS_CAP),
            ).fetchall()
        return {
            "focus": [dict(r) for r in focus_rows],
            "totals_by_type": totals_by_type,
            "total": total,
        }

    def _read_room_meetings(
        self, principal: Principal, project_id: str, project: Any,
    ) -> dict[str, Any]:
        """Meetings summary: count + latest."""
        count = project.meeting_count
        latest_list = self.list_meetings(principal, project_id, limit=1)
        return {
            "count": count,
            "latest": latest_list[0] if latest_list else None,
        }

    def _read_room_resources(self, project_id: str) -> dict[str, Any]:
        """Resources summary: count + latest linked."""
        resource_objs = self._db.project_relationships.list_for_project(
            project_id)
        count = len(resource_objs)
        return {
            "count": count,
            "latest": resource_objs[0].to_dict() if resource_objs else None,
        }

    def _read_room_changes(self, project_id: str) -> dict[str, Any]:
        """Recent changes, bounded, newest first."""
        changes = self._db.projects.list_project_changes(
            project_id, limit=ROOM_CHANGES_CAP)
        return {"recent": changes}

    def _read_room_review(self, project_id: str) -> dict[str, Any]:
        """Review section: pending_count, last_accepted_at, open_review_id.

        HS-160-05: the review section graduates from absent to real.
        Shape: {state:'ok', last_accepted_at, pending_count, open_review_id}.
        Art VI: zeros are zeros, not absence -- the domain exists now.
        """
        room_fields = self._db.projects.get_project_room_fields(project_id)
        last_accepted_at = (room_fields or {}).get("last_review_at")

        open_review_id = None
        pending_count = 0

        if self._delta_service is not None:
            try:
                open_review = self._delta_service._find_open_review(project_id)
                if open_review is not None:
                    open_review_id = open_review["id"]
                    proposals = self._db.project_observations.list_proposals(
                        project_id,
                        review_window_key=open_review_id,
                        lifecycle="open",
                    )
                    pending_count = len(proposals)
            except Exception:
                # Fault isolation: if delta reads fail, we still return
                # the section with what we have.
                pass

        return {
            "last_accepted_at": last_accepted_at,
            "pending_count": pending_count,
            "open_review_id": open_review_id,
        }

    # ── HS-169-04 room sub-readers (the four questions) ──────────────

    @staticmethod
    def _entities(snapshot: Any) -> list[dict[str, Any]]:
        """Extract entity list from a watch snapshot.

        The persisted snapshot is ``{"schema":1, "entities": {"526": {...}}}``
        (a dict keyed by entity ID, written by normalize_snapshot).  Some
        paths may pass the raw list from GitHubWatchSource.snapshot().
        Returns a flat list either way.
        """
        if isinstance(snapshot, list):
            return snapshot
        if isinstance(snapshot, dict):
            entities = snapshot.get("entities")
            if isinstance(entities, dict):
                return list(entities.values())
            if isinstance(entities, list):
                return entities
        return []

    # Severity ordering for needsYou rows
    _SEVERITY_ORDER = {"danger": 0, "warning": 1, "info": 2}

    # Change-kind phrases: raw snake_case kind -> human phrase.
    # The guard test asserts no raw kind (underscored) leaks into a phrase.
    _CHANGE_KIND_PHRASES: dict[str, str] = {
        "project.created": "created",
        "project.updated": "updated",
        "project.archived": "archived",
        "project.restored": "restored",
        "project.resource.linked": "resource linked",
        "project.resource.unlinked": "resource unlinked",
        "watch.created": "watch created",
        "watch.snapshot": "snapshot refreshed",
        "watch.evaluated": "watch evaluated",
        "watch.error": "watch error",
        "item.created": "item added",
        "item.updated": "item updated",
        "item.transitioned": "item transitioned",
        "meeting.linked": "meeting linked",
        "meeting.unlinked": "meeting unlinked",
        "review.opened": "review opened",
        "review.accepted": "review accepted",
        "update.drafted": "update drafted",
        "update.published": "update published",
        "steward.ran": "steward ran",
    }

    # Plain-reason mapping for Watch errors (HS-169-04 D4 SOURCES)
    _PLAIN_REASON_PATTERNS: list[tuple[str, str]] = [
        ("JQL parse error", "Jira rejected the query"),
        ("The value '", "Jira rejected the query"),
        ("does not exist for the field", "Jira rejected the query"),
        ("no local query adapter", "No local adapter for meeting activity yet"),
        ("lock timeout", "acli is busy"),
        ("connector_snapshot_adapter_unavailable", "No local adapter for meeting activity yet"),
    ]

    @staticmethod
    def _plain_reason(error: str | None) -> str | None:
        """Map a raw Watch error to plain words (ONCE in the service)."""
        if not error:
            return None
        lower = error.lower()
        for pattern, plain in ProjectService._PLAIN_REASON_PATTERNS:
            if pattern.lower() in lower:
                return plain
        # First line of the error, no stack
        return error.split("\n")[0][:200]

    def _read_room_needs_you(self, project_id: str) -> dict[str, Any]:
        """NEEDS YOU: items derived from Watch snapshots + Delta review."""
        watches = self._db.automations.list_project_watches(project_id)
        needs: list[dict[str, Any]] = []
        now = datetime.now()

        for watch in watches:
            connector_id = watch.get("connector_id", "")
            snapshot = watch.get("snapshot")
            if not snapshot:
                continue
            entities = self._entities(snapshot)
            query_kind = watch.get("query_kind", "")

            if connector_id == "gh" and query_kind == "pull_requests":
                # PRs whose review_requests name the owner or review_decision = changes_requested.
                # Also: a PR with failing checks that the owner authored or
                # is asked to review gets a CHECKS FAILING row (the base-branch
                # CI row is the branch_ci kind; PR-level failing checks are a
                # needs-you row ONLY when the PR is the owner's or awaits their
                # review -- otherwise it is a source token only).
                owner_login = self._get_github_owner_login()
                for entity in entities:
                    # Handle both raw (reviewRequests) and normalized (review_requests) field names
                    review_requests = entity.get("review_requests") or entity.get("reviewRequests") or []
                    review_decision = (
                        entity.get("review_decision") or entity.get("reviewDecision") or ""
                    ).lower()
                    updated_at_str = entity.get("updated_at") or entity.get("updatedAt") or ""
                    entity_id = entity.get("id") or entity.get("number") or ""
                    entity_title = entity.get("title") or ""
                    checks = str(entity.get("checks") or "").lower()

                    waiting_on_owner = (
                        (owner_login and owner_login.lower() in [r.lower() for r in review_requests])
                        or review_decision == "changes_requested"
                    )
                    if waiting_on_owner:
                        age_str = _format_age(updated_at_str, now)
                        # PR-level failing checks on a PR awaiting the owner's review
                        if checks == "failing":
                            needs.append({
                                "source": "github",
                                "title": f"#{entity_id} {entity_title}".strip(),
                                "why": f"CHECKS FAILING · {age_str}" if age_str else "CHECKS FAILING",
                                "since": updated_at_str,
                                "url": entity.get("url"),
                                "verb": "open",
                                "severity": "danger",
                            })
                        else:
                            needs.append({
                                "source": "github",
                                "title": f"#{entity_id} {entity_title}".strip(),
                                "why": f"WAITING ON YOUR REVIEW · {age_str}" if age_str else "WAITING ON YOUR REVIEW",
                                "since": updated_at_str,
                                "url": entity.get("url"),
                                "verb": "open",
                                "severity": "warning",
                            })

            elif connector_id == "gh" and query_kind == "branch_ci":
                # CI on the base branch
                for entity in entities:
                    conclusion = str(entity.get("conclusion") or "").lower()
                    if conclusion in ("failure", "timed_out", "cancelled"):
                        base_branch = entity.get("branch") or "main"
                        needs.append({
                            "source": "github",
                            "title": f"CI failing on {base_branch}",
                            "why": "CI RED",
                            "since": entity.get("updated_at") or "",
                            "url": entity.get("url"),
                            "verb": "open",
                            "severity": "danger",
                        })

            elif connector_id == "jira" and query_kind == "issues":
                # Jira entities from an OVERDUE-kind watch
                query = watch.get("query") or {}
                # An overdue watch has due_within_days in its query or its template is due_risk
                for entity in entities:
                    due_at = entity.get("due_at") or entity.get("dueDate")
                    if not due_at:
                        continue
                    try:
                        due_dt = datetime.fromisoformat(str(due_at).replace("Z", "+00:00").split("T")[0])
                        overdue_days = (now.replace(tzinfo=None) - due_dt.replace(tzinfo=None)).days
                    except (ValueError, TypeError):
                        continue
                    if overdue_days > 0:
                        jira_id = entity.get("key") or entity.get("id") or ""
                        jira_title = entity.get("summary") or entity.get("title") or ""
                        needs.append({
                            "source": "jira",
                            "title": f"{jira_id} {jira_title}".strip(),
                            "why": f"OVERDUE · {overdue_days} DAYS",
                            "since": due_at,
                            "url": entity.get("url"),
                            "verb": "open",
                            "severity": "danger",
                        })

        # Delta proposals pending
        if self._delta_service is not None:
            try:
                review_data = self._read_room_review(project_id)
                pending = review_data.get("pending_count", 0)
                if pending > 0:
                    needs.append({
                        "source": "delta",
                        "title": f"{pending} proposals waiting",
                        "why": "DECISION PENDING",
                        "since": "",
                        "url": None,
                        "verb": "decide",
                        "severity": "info",
                    })
            except Exception:
                pass

        # HS-172-03: follow-through proposals (intel-extracted decisions/actions).
        try:
            proposals = self._db.proposals.list_proposals(
                project_id=project_id, state="proposed",
            )
            for prop in proposals:
                # Resolve meeting title for provenance.
                meeting_title = ""
                try:
                    mtg = self._db.meetings.get_meeting(prop.meeting_id)
                    meeting_title = (mtg.title or "") if mtg else ""
                except Exception:
                    pass
                why_parts = ["PROPOSED"]
                if meeting_title:
                    why_parts.append(meeting_title)
                needs.append({
                    "source": "proposal",
                    "kind": "proposal",
                    "title": prop.text,
                    "why": " · ".join(why_parts),
                    "since": prop.created_at,
                    "url": None,
                    "verb": "confirm",
                    "verbHref": f"/api/proposals/{prop.id}/confirm",
                    "severity": "info",
                    "proposal_id": prop.id,
                    "proposal_kind": prop.kind,
                    "host": prop.model_host,
                    "speaker_label": prop.speaker_label,
                    "due_hint": prop.due_hint,
                    "owner_hint": prop.owner_hint,
                    "original_text": prop.original_text,
                    "meeting_title": meeting_title,
                    "created_at": prop.created_at,
                })
        except Exception:
            pass

        # HS-173: review bottleneck items (resolved reviewers whose median
        # exceeds the threshold get a NEEDS YOU row).
        try:
            from holdspeak.services.room_health_service import review_wait as _review_wait
            from datetime import timezone as _tz
            now_utc = datetime.now(_tz.utc)

            # Gather all PR entities from watches (already iterated above)
            all_pr_entities: list[dict[str, Any]] = []
            for watch in watches:
                cid = watch.get("connector_id", "")
                qk = watch.get("query_kind", "")
                snap = watch.get("snapshot")
                if cid == "gh" and qk == "pull_requests" and snap:
                    all_pr_entities.extend(self._entities(snap))

            if all_pr_entities:
                review_signal = _review_wait(all_pr_entities, now_utc)
                bottleneck_people = self._resolve_review_people(
                    project_id, review_signal.get("per_reviewer", []))
                for person in bottleneck_people:
                    median_d = person.get("median_days", 0)
                    pr_count = person.get("count", 0)
                    display = person.get("display_name", "")
                    needs.append({
                        "source": "github",
                        "kind": "review_bottleneck",
                        "title": display,
                        "why": f"REVIEW BOTTLENECK · {median_d} D MEDIAN · {pr_count} PRS WAITING",
                        "since": "",
                        "url": None,
                        "verb": "nudge",
                        "severity": "warning",
                        "relationship_id": person.get("relationship_id"),
                        "median_days": median_d,
                        "count": pr_count,
                    })
        except Exception:
            pass

        # Sort: danger > warning > info, then by age (oldest first = most urgent)
        needs.sort(key=lambda r: (
            self._SEVERITY_ORDER.get(r.get("severity", "info"), 2),
            r.get("since") or "",
        ))

        return {"items": needs, "count": len(needs)}

    def _get_github_owner_login(self) -> str | None:
        """Get the GitHub owner login from the connection service."""
        try:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT external_connection_ref FROM watch_provider_connections "
                    "WHERE provider_id = 'github' AND state != '' "
                    "ORDER BY last_connected_at DESC LIMIT 1"
                ).fetchone()
                if row and row["external_connection_ref"]:
                    return row["external_connection_ref"]
        except Exception:
            pass
        return None

    # State severity for merging: cant_check > paused > live
    _STATE_SEVERITY = {"cant_check": 0, "paused": 1, "live": 2}

    # Template order for merged source tokens (the artboard's row order)
    _TOKEN_ORDER_PREFIXES = [
        "OPEN PRS", "WAITING ON YOU", "CHECKS FAILING",
        "CI RED", "CI GREEN",
        "OVERDUE", "DUE THIS WEEK", "BLOCKED",
        "CLEAR",
    ]

    @staticmethod
    def _token_sort_key(token: str) -> int:
        """Sort key for template order. Known prefixes first; unknown last."""
        for i, prefix in enumerate(ProjectService._TOKEN_ORDER_PREFIXES):
            if token.endswith(prefix) or token == prefix:
                return i
        return len(ProjectService._TOKEN_ORDER_PREFIXES)

    def _meeting_calendar_tokens(
        self, project_id: str, *, now: datetime | None = None,
    ) -> list[str]:
        """``N THIS WEEK`` and ``NEXT DAY HH:MM`` from the Room's linked
        calendar events (HS-175 counsel C8/C9c).

        Inline query over ``calendar_event_projects`` joined to
        ``calendar_events`` (stored UTC ``...Z``); the week is the hub's
        local week and the NEXT clock is local.  A suppressed link (a
        durable Unlink, if present) does not count.
        """
        tokens: list[str] = []
        current = local_now(now)
        monday, next_monday = local_week_bounds(current)
        week_start, week_end = utc_z(monday), utc_z(next_monday)
        now_z = utc_z(current)
        try:
            with self._db._connection() as conn:
                week_row = conn.execute(
                    """SELECT COUNT(DISTINCT ce.id) AS cnt
                       FROM calendar_event_projects cep
                       JOIN calendar_events ce ON ce.id = cep.calendar_event_id
                       WHERE cep.project_id = ?
                         AND cep.match_source != 'suppressed'
                         AND ce.starts_at >= ? AND ce.starts_at < ?""",
                    (project_id, week_start, week_end),
                ).fetchone()
                next_row = conn.execute(
                    """SELECT ce.starts_at
                       FROM calendar_event_projects cep
                       JOIN calendar_events ce ON ce.id = cep.calendar_event_id
                       WHERE cep.project_id = ?
                         AND cep.match_source != 'suppressed'
                         AND ce.starts_at > ?
                       ORDER BY ce.starts_at ASC LIMIT 1""",
                    (project_id, now_z),
                ).fetchone()
        except Exception as exc:  # pragma: no cover - a missing table on an old DB
            _log.warning("meeting calendar tokens failed for %s: %s", project_id, exc)
            return tokens
        this_week = int(week_row["cnt"]) if week_row else 0
        if this_week:
            tokens.append(f"{this_week} THIS WEEK")
        if next_row and next_row["starts_at"]:
            try:
                next_dt = datetime.fromisoformat(
                    str(next_row["starts_at"]).replace("Z", "+00:00")
                )
                if next_dt.tzinfo is None:
                    next_dt = next_dt.replace(tzinfo=timezone.utc)
                # Per-instant local conversion (DST-safe), never now's offset.
                local_next = next_dt.astimezone()
                tokens.append(
                    f"NEXT {local_next.strftime('%a').upper()} {local_next.strftime('%H:%M')}"
                )
            except (ValueError, TypeError):
                pass
        return tokens

    def _read_room_sources(self, project_id: str) -> dict[str, Any]:
        """SOURCES: ONE item per (provider, scope), merged from all watches."""
        watches = self._db.automations.list_project_watches(project_id)
        # Intermediate: per-watch data, keyed by (provider, scope) for grouping
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}

        for watch in watches:
            # HS-175 counsel C7: a retired Watch is not a source row (the
            # owner said no); folding it into the live row hid Retire.
            if str(watch.get("state") or "") == "retired":
                continue
            connector_id = watch.get("connector_id", "")
            query = watch.get("query") or {}
            snapshot = watch.get("snapshot")
            entities = self._entities(snapshot)
            last_error = watch.get("last_error")
            enabled = watch.get("enabled", True)
            watch_state = str(watch.get("state") or "")
            query_kind = watch.get("query_kind", "")

            # Provider label
            provider = "github" if connector_id == "gh" else connector_id

            # Scope
            scope = query.get("repository") or ""
            if connector_id == "jira":
                projects = query.get("projects") or []
                scope = " + ".join(projects) if projects else query.get("connection_ref", "")
            elif connector_id == "meeting":
                scope = "MEETINGS"

            # Host (egress)
            host = "github.com" if connector_id == "gh" else ""
            if connector_id == "jira":
                ref = query.get("connection_ref", "")
                # connection_ref may be "site.atlassian.net|email" -- host is before |
                site = ref.split("|")[0] if "|" in ref else ref
                host = site.split("//")[-1].split("/")[0] if "//" in site else site

            # State -- HS-175 counsel C7(b): Pause writes ``state='paused'``
            # (watch_service.pause_watch) and leaves ``enabled`` alone, so the
            # row reads ``state`` first; a disabled watch is paused too.
            if watch_state == "paused" or not enabled:
                w_state = "paused"
            elif last_error:
                w_state = "cant_check"
            else:
                w_state = "live"

            # Count tokens (zero-count omitted)
            tokens: list[str] = []
            if connector_id == "gh" and query_kind == "pull_requests":
                open_count = sum(1 for e in entities if str(e.get("state", "")).lower() == "open")
                if open_count:
                    tokens.append(f"{open_count} OPEN PRS")
                owner_login = self._get_github_owner_login()
                if owner_login:
                    waiting = sum(
                        1 for e in entities
                        if owner_login.lower() in [
                            r.lower() for r in (
                                e.get("review_requests") or e.get("reviewRequests") or []
                            )
                        ]
                    )
                    if waiting:
                        tokens.append(f"{waiting} WAITING ON YOU")
                # PR-level checks failing (source token, not a needsYou row
                # unless the PR is the owner's or awaits their review)
                checks_failing = sum(
                    1 for e in entities
                    if str(e.get("checks") or "").lower() == "failing"
                )
                if checks_failing:
                    tokens.append(f"{checks_failing} CHECKS FAILING")
            elif connector_id == "gh" and query_kind == "branch_ci":
                for entity in entities:
                    conclusion = str(entity.get("conclusion") or "").lower()
                    if conclusion in ("failure", "timed_out", "cancelled"):
                        tokens.append("CI RED")
                    elif conclusion == "success":
                        tokens.append("CI GREEN")
            elif connector_id == "jira" and query_kind == "issues":
                overdue_count = 0
                due_soon_count = 0
                for entity in entities:
                    due_at = entity.get("due_at") or entity.get("dueDate")
                    if not due_at:
                        continue
                    try:
                        due_dt = datetime.fromisoformat(str(due_at).replace("Z", "+00:00").split("T")[0])
                        days = (datetime.now().replace(tzinfo=None) - due_dt.replace(tzinfo=None)).days
                    except (ValueError, TypeError):
                        continue
                    if days > 0:
                        overdue_count += 1
                    elif days >= -7:
                        due_soon_count += 1
                if overdue_count:
                    tokens.append(f"{overdue_count} OVERDUE")
                if due_soon_count:
                    tokens.append(f"{due_soon_count} DUE THIS WEEK")
            # HS-175-04: meeting watch tokens.
            # HS-175 counsel C9(c)/C8: the Watch's entities are RECORDED
            # meetings (started_at in the past) -- they can never yield a
            # future NEXT.  Both tokens read the Room's linked CALENDAR
            # events (calendar_event_projects x calendar_events) in the
            # hub's local week:  ``N THIS WEEK`` = linked events whose
            # starts_at falls in [local Monday, next local Monday);
            # ``NEXT DAY HH:MM`` = the first linked event after now, in
            # local time.  Both absent at zero (A.8).
            elif connector_id == "meeting" and query_kind == "meetings":
                tokens.extend(self._meeting_calendar_tokens(project_id))

            plain_reason = self._plain_reason(last_error)

            # Unknown connectors with no local adapter
            _KNOWN_CONNECTORS = {"gh", "jira", "confluence", "meeting"}
            if connector_id not in _KNOWN_CONNECTORS:
                if not last_error:
                    plain_reason = "No local adapter for this source yet"
                    w_state = "cant_check"

            entry = {
                "watchId": watch.get("id"),
                "provider": provider,
                "scope": scope,
                "tokens": tokens,
                # C8: SQLite's naive-UTC stamps leave here with an offset so
                # the face prints the viewer's local clock.
                "checkedAt": aware_iso(watch.get("last_success_at")),
                "nextCheckAt": aware_iso(watch.get("next_evaluation_at")),
                "host": host,
                "state": w_state,
                "plainReason": plain_reason,
                "suggested": False,
            }
            groups.setdefault((provider, scope), []).append(entry)

        # Merge groups: one source item per (provider, scope)
        sources: list[dict[str, Any]] = []
        for (_provider, _scope), items in groups.items():
            if len(items) == 1:
                merged = dict(items[0])
                merged["watchIds"] = [merged["watchId"]]
            else:
                # Merge tokens: collect, dedupe by exact label, sort to template order
                all_tokens: list[str] = []
                seen_tokens: set[str] = set()
                for item in items:
                    for tok in item["tokens"]:
                        if tok not in seen_tokens:
                            all_tokens.append(tok)
                            seen_tokens.add(tok)
                all_tokens.sort(key=self._token_sort_key)

                # checkedAt: latest non-null
                checked_vals = [i["checkedAt"] for i in items if i["checkedAt"]]
                merged_checked = max(checked_vals) if checked_vals else None

                # nextCheckAt: soonest non-null
                next_vals = [i["nextCheckAt"] for i in items if i["nextCheckAt"]]
                merged_next = min(next_vals) if next_vals else None

                # state: worst (cant_check > paused > live)
                merged_state = min(
                    (i["state"] for i in items),
                    key=lambda s: self._STATE_SEVERITY.get(s, 2),
                )

                # plainReason: first non-null
                merged_reason = next(
                    (i["plainReason"] for i in items if i["plainReason"]),
                    None,
                )

                merged = {
                    "watchId": items[0]["watchId"],
                    "watchIds": [i["watchId"] for i in items],
                    "provider": items[0]["provider"],
                    "scope": items[0]["scope"],
                    "tokens": all_tokens,
                    "checkedAt": merged_checked,
                    "nextCheckAt": merged_next,
                    "host": items[0]["host"],
                    "state": merged_state,
                    "plainReason": merged_reason,
                    "suggested": False,
                }

            # CLEAR: a live source with no tokens after merging
            if not merged["tokens"] and merged["state"] == "live" and _provider in ("github", "jira"):
                merged["tokens"] = ["CLEAR"]

            sources.append(merged)

        # Top-level nextCheckAt: soonest non-null over live sources
        live_next = [
            s["nextCheckAt"] for s in sources
            if s["state"] == "live" and s["nextCheckAt"]
        ]
        next_check_at = min(live_next) if live_next else None

        return {"items": sources, "count": len(sources), "nextCheckAt": next_check_at}

    def _read_room_health(self, project_id: str, target_at: str | None) -> dict[str, Any]:
        """HEALTH: AT RISK / ON TRACK derivation + HS-173 health signals."""
        from holdspeak.services.room_health_service import (
            ci_health as _ci_health,
            issue_aging as _issue_aging,
            merge_queue_depth as _merge_queue_depth,
            readiness as _readiness,
            review_wait as _review_wait,
        )
        from holdspeak.services.room_people_service import room_people as _room_people

        watches = self._db.automations.list_project_watches(project_id)
        now = datetime.now()

        overdue_count = 0
        ci_failing = False
        review_waiting_days: int | None = None

        # HS-173: collect entities by kind for health derivations
        pr_entities: list[dict[str, Any]] = []
        jira_entities: list[dict[str, Any]] = []
        ci_entities: list[dict[str, Any]] = []
        newest_snapshot_at: str | None = None

        for watch in watches:
            connector_id = watch.get("connector_id", "")
            query_kind = watch.get("query_kind", "")
            snapshot = watch.get("snapshot")
            entities = self._entities(snapshot)

            # Track newest snapshot timestamp for checked_at
            updated_at = watch.get("updated_at") or ""
            if updated_at and (newest_snapshot_at is None or updated_at > newest_snapshot_at):
                newest_snapshot_at = updated_at

            if connector_id == "jira" and query_kind == "issues":
                jira_entities.extend(entities)
                for entity in entities:
                    due_at = entity.get("due_at") or entity.get("dueDate")
                    if not due_at:
                        continue
                    try:
                        due_dt = datetime.fromisoformat(str(due_at).replace("Z", "+00:00").split("T")[0])
                        days = (now.replace(tzinfo=None) - due_dt.replace(tzinfo=None)).days
                    except (ValueError, TypeError):
                        continue
                    if days > 0:
                        overdue_count += 1

            elif connector_id == "gh" and query_kind == "branch_ci":
                ci_entities.extend(entities)
                for entity in entities:
                    conclusion = str(entity.get("conclusion") or "").lower()
                    if conclusion in ("failure", "timed_out", "cancelled"):
                        ci_failing = True

            elif connector_id == "gh" and query_kind == "pull_requests":
                pr_entities.extend(entities)
                owner_login = self._get_github_owner_login()
                for entity in entities:
                    review_requests = entity.get("review_requests") or entity.get("reviewRequests") or []
                    if owner_login and owner_login.lower() in [r.lower() for r in review_requests]:
                        updated_at_str = entity.get("updated_at") or entity.get("updatedAt") or ""
                        if updated_at_str:
                            try:
                                updated_dt = datetime.fromisoformat(
                                    updated_at_str.replace("Z", "+00:00").rstrip("Z")
                                )
                                age_days = (now - updated_dt.replace(tzinfo=None)).days
                                if review_waiting_days is None or age_days > review_waiting_days:
                                    review_waiting_days = age_days
                            except (ValueError, TypeError):
                                pass

        # Target passed
        target_passed = False
        if target_at:
            try:
                target_dt = datetime.fromisoformat(target_at.split("T")[0])
                target_passed = now.replace(tzinfo=None) > target_dt.replace(tzinfo=None)
            except (ValueError, TypeError):
                pass

        # AT RISK when ANY of the inputs is true
        at_risk = (
            overdue_count > 0
            or ci_failing
            or (review_waiting_days is not None and review_waiting_days > 3)
            or target_passed
        )

        # Reason: first true input in order
        reason: str | None = None
        if overdue_count > 0:
            reason = f"{overdue_count} OVERDUE"
        elif ci_failing:
            reason = "CI RED"
        elif review_waiting_days is not None and review_waiting_days > 3:
            reason = f"REVIEW WAITING {review_waiting_days} DAYS"
        elif target_passed:
            reason = "TARGET PASSED"

        # ── HS-173: health signal derivations ────────────────────────
        from datetime import timezone as _tz
        now_utc = datetime.now(_tz.utc)

        review_signal = _review_wait(pr_entities, now_utc)
        issue_signal = _issue_aging(jira_entities, now_utc)

        # CI history: try the latest steward run's OBSERVE step first,
        # fall back to the branch_ci snapshot entities.
        ci_history = self._load_ci_history(project_id) or ci_entities
        queue_depth = _merge_queue_depth(pr_entities)
        ci_signal = _ci_health(ci_history, queue=queue_depth)

        # Overdue commitments from follow-through
        ft_overdue = 0
        try:
            ft_overdue = self._count_overdue_commitments(project_id)
        except Exception:
            pass

        # Blocker count: issues with priority blocker/critical or labels
        # containing "blocker"
        blocker_count = 0
        for entity in jira_entities:
            priority = str(entity.get("priority") or "").lower()
            labels = entity.get("labels") or []
            status = str(entity.get("status") or "").lower()
            if status in ("done", "closed"):
                continue
            if priority in ("blocker", "critical") or any(
                "blocker" in str(lbl).lower() for lbl in labels
            ):
                blocker_count += 1

        release_signal = _readiness(
            review_signal=review_signal,
            ci_signal=ci_signal,
            blocker_count=blocker_count,
            overdue_count=ft_overdue,
        )

        # HS-173: resolve reviewers to people for the bottleneck rows
        people: list[dict[str, Any]] = []
        try:
            people = self._resolve_review_people(
                project_id, review_signal.get("per_reviewer", []))
        except Exception:
            pass

        # HS-173-04: enrich people rows with nudge state
        try:
            self._enrich_people_with_nudge_state(project_id, people, pr_entities)
        except Exception:
            pass

        return {
            "assessment": "at_risk" if at_risk else "on_track",
            "reason": reason,
            "inputs": {
                "overdue": overdue_count,
                "ciFailing": ci_failing,
                "reviewWaitingDays": review_waiting_days,
                "targetPassed": target_passed,
            },
            # HS-173: structured health signals
            "signals": {
                "review_wait": review_signal,
                "issue_aging": issue_signal,
                "ci": ci_signal,
                "release": release_signal,
            },
            "checked_at": newest_snapshot_at,
            "merge_queue_depth": queue_depth,
            "people": people,
        }

    def _load_ci_history(self, project_id: str) -> list[dict[str, Any]] | None:
        """Load CI history from the latest completed steward run's OBSERVE step.

        Returns a list of CI run dicts, or None when no history is available.
        The steward's OBSERVE phase persists ci_history on the step's
        observed_state_json (HS-173).
        """
        try:
            runs = self._db.steward_runs.list_runs(
                project_id, state="completed", limit=1)
            if not runs:
                return None
            run_id = runs[0]["id"]
            steps = self._db.steward_steps.list_steps(
                run_id, phase="observe", limit=1)
            if not steps:
                return None
            observed_raw = steps[0].get("observed_state_json") or "{}"
            if isinstance(observed_raw, str):
                observed = json.loads(observed_raw)
            else:
                observed = observed_raw
            history = observed.get("ci_history")
            if isinstance(history, list) and history:
                return history
        except Exception:
            pass
        return None

    def _count_overdue_commitments(self, project_id: str) -> int:
        """Count overdue commitments for a project from decision_commitments."""
        from datetime import date as _date
        today = _date.today()
        try:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM decision_commitments c "
                    "JOIN decision_records dr ON dr.source_id = c.decision_id "
                    "JOIN project_meetings pm ON pm.meeting_id = dr.source_meeting_id "
                    "WHERE pm.project_id = ? "
                    "AND c.status NOT IN ('completed', 'dismissed', 'done') "
                    "AND c.due_at IS NOT NULL AND c.due_at < ?",
                    (project_id, today.isoformat()),
                ).fetchone()
                return int(row["cnt"]) if row else 0
        except Exception:
            return 0

    def _resolve_review_people(
        self,
        project_id: str,
        per_reviewer: list[dict[str, Any]],
        threshold_days: float = 2.0,
    ) -> list[dict[str, Any]]:
        """Resolve reviewer logins to People relationships for bottleneck rows.

        Only RESOLVED reviewers whose median exceeds the threshold appear.
        Unresolved reviewers are counted in overall median but get no row
        (no raw login on the face).
        """
        people_svc = getattr(self, "_people_service", None)
        if people_svc is None:
            # Try to construct from the DB if available
            try:
                from holdspeak.services.people_service import PeopleService
                people_svc = PeopleService(self._db)
            except Exception:
                return []

        result: list[dict[str, Any]] = []
        for reviewer in per_reviewer:
            login = reviewer.get("login", "")
            median_days = reviewer.get("median_days", 0.0)
            count = reviewer.get("count", 0)
            if median_days < threshold_days:
                continue
            try:
                resolved = people_svc.resolve_relationship_by_watch_identity(login)
                if not resolved or resolved.get("state") != "ready":
                    continue
                relationship = resolved.get("relationship")
                if not relationship:
                    continue
                rel_id = relationship.get("id")
                display_name = relationship.get("display_name") or ""
                if not rel_id or not display_name:
                    continue
                result.append({
                    "relationship_id": rel_id,
                    "display_name": display_name,
                    "login": login,
                    "median_days": median_days,
                    "count": count,
                })
            except Exception:
                logging.getLogger(__name__).debug("review people: resolver skipped one reviewer", exc_info=True)
                continue
        return result

    def _enrich_people_with_nudge_state(
        self,
        project_id: str,
        people: list[dict[str, Any]],
        pr_entities: list[dict[str, Any]],
    ) -> None:
        """HS-173-04: add nudge={step_id, state, sent_at?} to each person row."""
        if not people:
            return
        # Build a map of login -> latest nudge step for this project.
        prefix = f"nudge:{project_id}:"
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM steward_steps "
                "WHERE effect_kind = 'github_comment' "
                "AND idempotency_key LIKE ? "
                "ORDER BY created_at DESC LIMIT 500",
                (prefix + "%",),
            ).fetchall()

        # Group by reviewer login, keep the most recent per login.
        nudge_by_login: dict[str, dict[str, Any]] = {}
        for row in rows:
            step = dict(row)
            idem_key = step.get("idempotency_key", "")
            # nudge:{project_id}:{repo}:{pr_number}:{login}
            parts = idem_key.split(":")
            if len(parts) >= 5:
                login = parts[-1]
            else:
                continue
            if login not in nudge_by_login:
                nudge_by_login[login] = {
                    "step_id": step["id"],
                    "state": step["state"],
                    "sent_at": step.get("completed_at") if step["state"] == "sent" else None,
                }

        for person in people:
            login = (person.get("login") or "").lower()
            if login in nudge_by_login:
                person["nudge"] = nudge_by_login[login]

    def _read_room_since_read(self, project_id: str, room_read_at: str | None) -> dict[str, Any]:
        """SINCE YOU LOOKED: changes grouped by source in phrases."""
        if room_read_at:
            # Get changes since the read marker via revision lookup
            with self._db._connection() as conn:
                # Find the revision at or after room_read_at
                row = conn.execute(
                    "SELECT MIN(project_revision) as min_rev FROM project_changes "
                    "WHERE project_id = ? AND created_at > ?",
                    (project_id, room_read_at),
                ).fetchone()
                min_rev = row["min_rev"] if row and row["min_rev"] else None
            if min_rev is not None:
                changes = self._db.projects.list_project_changes(
                    project_id, since_revision=min_rev, limit=100,
                )
            else:
                changes = []
        else:
            changes = []

        # Group changes by source and map kinds to phrases
        groups: dict[str, list[dict[str, Any]]] = {}
        for change in changes:
            kind = change.get("change_kind", "")
            # Determine source label from kind
            if kind.startswith("watch.") or kind.startswith("github."):
                source_label = "GitHub"
            elif kind.startswith("jira."):
                source_label = "Jira"
            else:
                source_label = "Room"

            phrase = self._CHANGE_KIND_PHRASES.get(kind, kind.replace("_", " ").replace(".", " "))
            summary = change.get("summary_json")
            detail = ""
            if summary:
                try:
                    s = json.loads(summary) if isinstance(summary, str) else summary
                    if isinstance(s, dict):
                        if s.get("action"):
                            detail = f" · {s['action']}"
                        elif s.get("name"):
                            detail = f" · {s['name']}"
                except (json.JSONDecodeError, TypeError):
                    pass

            entry = {
                "phrase": f"{phrase}{detail}",
                "at": change.get("created_at", ""),
                "url": None,
            }
            groups.setdefault(source_label, []).append(entry)

        # Build summary per group
        result_groups: list[dict[str, Any]] = []
        for source_label, entries in groups.items():
            # Build a short summary like "2 updated · 1 linked"
            kind_counts: dict[str, int] = {}
            for e in entries:
                verb = e["phrase"].split(" · ")[0] if " · " in e["phrase"] else e["phrase"]
                kind_counts[verb] = kind_counts.get(verb, 0) + 1
            summary_parts = [f"{count} {verb}" for verb, count in kind_counts.items()]
            result_groups.append({
                "source": source_label,
                "summary": " · ".join(summary_parts),
                "entries": entries,
            })

        return {
            "readAt": room_read_at,
            "groups": result_groups,
        }

    def _read_room_decisions(self, project_id: str) -> dict[str, Any]:
        """DECISIONS: records whose source meeting is linked to this project.

        HS-172-03: LEFT JOINs confirmed proposals so the face can render
        proposal provenance (source, meeting_title, confirmed_at, was).
        """
        # Find meetings linked to this project
        with self._db._connection() as conn:
            meeting_rows = conn.execute(
                "SELECT meeting_id FROM meeting_projects WHERE project_id = ?",
                (project_id,),
            ).fetchall()
            meeting_ids = [r["meeting_id"] for r in meeting_rows]
            if not meeting_ids:
                return {"items": []}

            # Find decision records sourced from those meetings,
            # LEFT JOIN confirmed proposals on decision_record_id.
            placeholders = ",".join("?" * len(meeting_ids))
            decision_rows = conn.execute(
                f"""SELECT DISTINCT r.id, r.decision_text, r.created_at, r.lifecycle,
                           p.id AS proposal_id,
                           p.meeting_id AS proposal_meeting_id,
                           p.kind AS proposal_kind,
                           p.original_text AS proposal_original_text,
                           p.owner_hint AS proposal_owner_hint,
                           p.due_hint AS proposal_due_hint,
                           p.text AS proposal_confirmed_text,
                           p.decided_at AS proposal_confirmed_at,
                           p.model_host AS proposal_model_host,
                           p.commitment_id AS proposal_commitment_id,
                           r.owner AS record_owner,
                           dc.due_at AS commitment_due_at,
                           dc.owner AS commitment_owner
                    FROM decision_records r
                    JOIN decision_record_sources s ON s.record_id = r.id
                    LEFT JOIN follow_through_proposals p
                         ON p.decision_record_id = r.id
                        AND p.state = 'confirmed'
                    LEFT JOIN decision_commitments dc
                         ON dc.id = p.commitment_id
                    WHERE s.source_type = 'meeting'
                      AND s.source_ref IN ({placeholders})
                      AND r.deleted = 0
                    ORDER BY r.created_at DESC""",
                meeting_ids,
            ).fetchall()

            # Resolve meeting titles for proposal provenance.
            mtg_titles: dict[str, str] = {}
            for mid in meeting_ids:
                try:
                    mtg = conn.execute(
                        "SELECT title FROM meetings WHERE id = ?", (mid,)
                    ).fetchone()
                    if mtg and mtg["title"]:
                        mtg_titles[mid] = mtg["title"]
                except Exception:
                    pass

        items = []
        seen_record_ids: set[str] = set()
        for row in decision_rows:
            rid = row["id"]
            if rid in seen_record_ids:
                continue
            seen_record_ids.add(rid)

            item: dict[str, Any] = {
                "id": rid,
                "text": row["decision_text"],
                "at": row["created_at"],
                "url": None,
            }

            # HS-172-03: proposal provenance fields.
            proposal_id = row["proposal_id"] if "proposal_id" in row.keys() else None
            if proposal_id:
                prop_meeting_id = row["proposal_meeting_id"] or ""
                item["proposal_id"] = proposal_id
                item["source"] = "meeting"
                item["meeting_title"] = mtg_titles.get(prop_meeting_id, "")
                item["confirmed_at"] = row["proposal_confirmed_at"]
                item["commitment_id"] = row["proposal_commitment_id"]

                # Build "was" dict: only fields the owner changed.
                was: dict[str, str] = {}
                orig_text = row["proposal_original_text"] or ""
                conf_text = row["proposal_confirmed_text"] or ""
                if orig_text and conf_text and orig_text != conf_text:
                    was["text"] = orig_text
                orig_owner = row["proposal_owner_hint"] or ""
                conf_owner = row["commitment_owner"] or row["record_owner"] or ""
                if orig_owner and conf_owner and orig_owner != conf_owner:
                    was["owner"] = orig_owner
                orig_due = row["proposal_due_hint"] or ""
                conf_due = row["commitment_due_at"] or ""
                if orig_due and conf_due and orig_due != conf_due:
                    was["due"] = orig_due
                if was:
                    item["was"] = was

            items.append(item)
        return {"items": items}

    def _read_room_commitments(self, project_id: str) -> dict[str, Any]:
        """COMMITMENTS: via their decision (whose source meeting is linked).

        HS-172-03: joins through decision_records.source_id to reach
        decision_commitments.decision_id (which references decisions.id,
        not decision_records.id).
        """
        # Get the decision record IDs first.
        decisions_data = self._read_room_decisions(project_id)
        record_ids = [d["id"] for d in decisions_data.get("items", [])]
        if not record_ids:
            return {"items": []}

        with self._db._connection() as conn:
            # Map decision_records.id -> decision_records.source_id (= decisions.id)
            placeholders = ",".join("?" * len(record_ids))
            source_rows = conn.execute(
                f"SELECT id, source_id FROM decision_records WHERE id IN ({placeholders})",
                record_ids,
            ).fetchall()
            decision_ids = [str(r["source_id"]) for r in source_rows if r["source_id"]]
            if not decision_ids:
                return {"items": []}

            placeholders2 = ",".join("?" * len(decision_ids))
            commitment_rows = conn.execute(
                f"""SELECT c.id, c.owner, c.due_at, c.status,
                           ai.task AS text
                    FROM decision_commitments c
                    LEFT JOIN action_items ai ON ai.id = c.action_item_id
                    WHERE c.decision_id IN ({placeholders2})
                      AND c.status != 'completed'
                    ORDER BY c.due_at ASC NULLS LAST, c.created_at ASC""",
                decision_ids,
            ).fetchall()

        items = []
        for row in commitment_rows:
            items.append({
                "id": row["id"],
                "text": row["text"] or "",
                "dueAt": row["due_at"],
                "owner": row["owner"],
            })
        return {"items": items}

    @staticmethod
    def _read_room_target(target_at: str | None) -> dict[str, Any]:
        """TARGET: days left and passed flag."""
        if not target_at:
            return {"targetAt": None, "daysLeft": None, "passed": False}
        try:
            target_dt = datetime.fromisoformat(target_at.split("T")[0])
            now = datetime.now()
            delta = (target_dt.replace(tzinfo=None) - now.replace(tzinfo=None)).days
            return {
                "targetAt": target_at,
                "daysLeft": delta if delta >= 0 else None,
                "passed": delta < 0,
            }
        except (ValueError, TypeError):
            return {"targetAt": target_at, "daysLeft": None, "passed": False}

    def _read_room_receipts(self, project_id: str) -> dict[str, Any]:
        """HS-174-04: pipeline receipts scoped to this project (last 10).

        Searches pipeline_events where the project_id appears in
        args_summary.  Each receipt carries origin/caller so the face can
        show the REMOTE badge.  Returns ``{items: [...]}``; empty list
        when none.
        """
        _LIMIT = 10
        # Scoping is a substring match on args_summary (counsel-on-built
        # 174, condition 3).  Project ids are ``proj-<12 hex>``, so a
        # collision needs one id to be a substring of another summary's
        # id -- improbable, not impossible.  The exact form is
        # ``json_extract(args_summary, '$.project_id') = ?``; V0 keeps
        # LIKE because summaries are not guaranteed to be JSON objects.
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT event_id, timestamp, service, method, "
                "       origin, caller, caller_identity, "
                "       result_summary, error "
                "FROM pipeline_events "
                "WHERE args_summary LIKE ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (f"%{project_id}%", _LIMIT),
            ).fetchall()
        items = []
        for row in rows:
            origin_val = str(row["origin"]) if row["origin"] and row["origin"] != "local" else None
            caller_val = str(row["caller"]) if row["caller"] else None
            items.append({
                "id": str(row["event_id"]),
                "op": str(row["method"]),
                "label": f"{row['service']}.{row['method']}",
                "title": f"{row['service']}.{row['method']}",
                "outcome": "error" if row["error"] else "ok",
                "origin": origin_val,
                "caller": caller_val,
                "identity": str(row["caller_identity"]) if row["caller_identity"] else None,
                "at": row["timestamp"],
                "timestamp": row["timestamp"],
            })
        return {"items": items}

    # ── read marker (HS-169-04) ─────────────────────────────────────

    def mark_room_read(self, principal: Principal, project_id: str) -> dict[str, Any]:
        """Set the per-project read marker to now."""
        self._require_project(project_id)
        now_iso = datetime.now().isoformat()
        self._db.projects.set_room_read_at(project_id, now_iso)
        return {"readAt": now_iso}

    # ── writes (graduated to revision law) ───────────────────────────

    def create_project(
        self, principal: Principal, payload: dict[str, Any],
        *, command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        name = str(payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Project name is required")
        threshold = self._threshold(payload.get("detection_threshold", 0.4))

        # Idempotency check (API-002)
        req_hash = _request_hash(payload)
        replay = self._check_idempotency(command_id, req_hash, "create_project")
        if replay is not None:
            return replay

        project_id = f"proj-{uuid.uuid4().hex[:12]}"
        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        new_revision = 1  # first revision for a new project

        with self._db._connection() as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, name, description, keywords_json, team_members_json,
                    context_json, detection_threshold, revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id, name,
                    str(payload.get("description") or ""),
                    json.dumps(self._strings(payload.get("keywords")), ensure_ascii=False),
                    json.dumps(self._strings(payload.get("team_members")), ensure_ascii=False),
                    json.dumps(payload.get("context") or {}, ensure_ascii=False),
                    threshold,
                    new_revision,
                    now_iso, now_iso,
                ),
            )

            # Change log (DOM-003)
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            project_ref = format_ref("project", project_id)
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.created",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, _request_hash({"name": name}),
                    json.dumps({"name": name}),
                    now_iso,
                ),
            )

            # Service event (API-004)
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.created",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "name": name},
                refs=[project_ref],
            )

            # Command ledger (API-002)
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.CREATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "create_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    def create_from_setup(
        self, principal: Principal, setup_payload: dict[str, Any],
        *, command_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Atomic Project creation from a setup interview (ACT-004).

        ONE transaction:
        - Create the Project row (name, purpose, outcome_text, lifecycle)
        - Activate selected+passed proposals as WatchSpec@1 rows in
          connector_watches (state='active', baseline_state='established')
        - Create watch_rules for each activated watch
        - Create project_sources bindings (semantic_role from proposal)
        - Record change + event + command

        All-or-nothing: any failure rolls back to zero Project/Watch rows.
        Baseline established WITHOUT events (ACT-005: ledger silence).
        Blank path: zero proposals is lawful (INT-002).
        """
        name = str(setup_payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Project name is required")

        req_hash = _request_hash(setup_payload)
        replay = self._check_idempotency(command_id, req_hash, "create_from_setup")
        if replay is not None:
            return replay

        project_id = f"proj-{uuid.uuid4().hex[:12]}"
        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        new_revision = 1
        proposals = setup_payload.get("proposals") or []

        with self._db._connection() as conn:
            # 1. Create the Project row
            conn.execute(
                """
                INSERT INTO projects (
                    id, name, description, keywords_json, team_members_json,
                    context_json, detection_threshold, revision,
                    purpose, outcome_text, lifecycle,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id, name,
                    str(setup_payload.get("description") or ""),
                    json.dumps([], ensure_ascii=False),
                    json.dumps([], ensure_ascii=False),
                    json.dumps({}, ensure_ascii=False),
                    0.4,  # default threshold
                    new_revision,
                    str(setup_payload.get("purpose") or ""),
                    str(setup_payload.get("outcome_text") or ""),
                    str(setup_payload.get("lifecycle") or "active"),
                    now_iso, now_iso,
                ),
            )

            # 2. Activate selected+passed proposals as Watch rows
            activated_watches: list[dict[str, Any]] = []
            for proposal in proposals:
                spec = proposal.get("spec") or {}
                if isinstance(spec, str):
                    spec = json.loads(spec)

                watch_id = f"watch_{uuid.uuid4().hex[:12]}"
                watch_name = spec.get("name", "Untitled watch")
                # Map provider spec IDs to connector_pack IDs
                # (the watch table's connector_id is "gh", not "github")
                raw_provider = spec.get("provider", {}).get("id", "native")
                connector_id = _PROVIDER_TO_CONNECTOR.get(raw_provider, raw_provider)
                # M-1 counsel: map singular subject kind to the plural
                # wire form GitHubWatchSource.snapshot demands.
                raw_kind = spec.get("subject", {}).get("kind", "")
                query_kind = _SUBJECT_TO_QUERY_KIND.get(raw_kind, raw_kind)
                # M-1 counsel: build the stored query in the shape
                # GitHubWatchSource expects: repository (singular string)
                # + query filters (state/base/search).  Mirror the shape
                # project_setup_service._native_test_read already uses.
                subject = spec.get("subject", {})
                scope = subject.get("scope", {})
                query_filters = dict(subject.get("query", {}))
                repos = scope.get("repositories", [])
                if repos:
                    query_filters["repository"] = repos[0]
                # HS-166-03: flatten jira scope into the stored query
                # the way repos[0] is flattened for gh.
                jira_connection_ref = scope.get("connection_ref") or spec.get("provider", {}).get("connection_ref")
                if jira_connection_ref:
                    query_filters["connection_ref"] = jira_connection_ref
                jira_projects = scope.get("projects", [])
                if jira_projects:
                    query_filters["projects"] = list(jira_projects)
                jira_issue_types = scope.get("issue_types", [])
                if jira_issue_types:
                    query_filters["issue_types"] = list(jira_issue_types)
                query: dict[str, Any] = query_filters
                trigger = spec.get("trigger") or CADENCE_PRESETS.get("normal", {})
                mode = spec.get("mode", "yolo")

                # Insert via sanctioned repo helper (M-1: no third door)
                self._db.automations.create_watch_in_transaction(
                    conn,
                    watch_id=watch_id,
                    connector_id=connector_id,
                    query_kind=query_kind,
                    name=watch_name,
                    query_json=json.dumps(query, sort_keys=True, separators=(",", ":")),
                    enabled=True,
                    schema_version="WatchSpec@1",
                    project_id=project_id,
                    intent=spec.get("intent", ""),
                    subject_kind=query_kind,
                    trigger_kind=trigger.get("kind", "poll"),
                    trigger_json=json.dumps(trigger, sort_keys=True, separators=(",", ":")),
                    mode=mode,
                    state="active",
                    revision=1,
                    baseline_state="established",  # ACT-005: baseline without events
                    test_state="passed",  # carried from proposal test
                    created_at=now_iso,
                    updated_at=now_iso,
                )

                # 3. Create watch_rules via sanctioned repo helper
                rules = spec.get("rules", [])
                for ordinal, rule in enumerate(rules):
                    rule_id = f"wrule_{uuid.uuid4().hex[:12]}"
                    self._db.automations.create_rule_in_transaction(
                        conn,
                        rule_id=rule_id,
                        watch_id=watch_id,
                        ordinal=ordinal,
                        condition_schema="WatchCondition@1",
                        condition_json=json.dumps(
                            rule.get("condition", {}),
                            sort_keys=True, separators=(",", ":"),
                        ),
                        action_schema="WatchAction@1",
                        action_json=json.dumps(
                            rule.get("actions", []),
                            sort_keys=True, separators=(",", ":"),
                        ),
                        enabled=True,
                        revision=0,
                        created_at=now_iso,
                        updated_at=now_iso,
                    )

                # 4. Create project_sources binding
                source_id = generate_psrc_id()
                semantic_role = spec.get("subject", {}).get("kind", "general")
                conn.execute(
                    """
                    INSERT INTO project_sources (
                        id, project_id, source_ref, label, semantic_role,
                        enabled, revision, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source_id, project_id,
                        format_ref("watch", watch_id),
                        watch_name,
                        semantic_role,
                        1, 0, now_iso, now_iso,
                    ),
                )

                activated_watches.append({
                    "watch_id": watch_id,
                    "name": watch_name,
                    "source_id": source_id,
                })

            # 5. Change log (DOM-003)
            project_ref = format_ref("project", project_id)
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.created",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, _request_hash({"name": name}),
                    json.dumps({
                        "name": name,
                        "source": "setup",
                        "watches_activated": len(activated_watches),
                    }),
                    now_iso,
                ),
            )

            # 6. Service event (API-004)
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.created",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "name": name,
                    "source": "setup",
                    "watches_activated": len(activated_watches),
                },
                refs=[project_ref],
            )

            # 7. Command ledger (API-002)
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.CREATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "create_from_setup",
                req_hash, envelope,
            )

            # S-1: mark the setup session completed inside the same
            # transaction so a crash cannot leave a dangling active
            # session whose re-finalize would create a duplicate.
            if session_id:
                self._db.automations.complete_session_in_transaction(
                    conn, session_id=session_id, project_id=project_id,
                )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        result["activated_watches"] = activated_watches
        return result

    def update_project(
        self, principal: Principal, project_id: str, patch: dict[str, Any],
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        self._require_project(project_id)

        # Idempotency check
        req_hash = _request_hash({"project_id": project_id, **patch})
        replay = self._check_idempotency(command_id, req_hash, "update_project")
        if replay is not None:
            return replay

        fields: dict[str, Any] = {}
        if "name" in patch:
            name = str(patch["name"] or "").strip()
            if not name:
                raise ValidationError("Project name cannot be empty")
            fields["name"] = name
        if "description" in patch:
            fields["description"] = str(patch["description"] or "")
        if "keywords" in patch:
            fields["keywords"] = self._strings(patch["keywords"])
        if "team_members" in patch:
            fields["team_members"] = self._strings(patch["team_members"])
        if "context" in patch:
            fields["context"] = patch["context"] or {}
        if "detection_threshold" in patch:
            fields["detection_threshold"] = self._threshold(patch["detection_threshold"])

        # ── Room fields (HS-158-02, SRS §5.1) ────────────────────────
        if "purpose" in patch:
            fields["purpose"] = str(patch["purpose"]).strip() if patch["purpose"] else None
        if "outcome_text" in patch:
            fields["outcome_text"] = str(patch["outcome_text"]).strip() if patch["outcome_text"] else None
        if "owner_ref" in patch:
            owner_ref_val = patch["owner_ref"]
            if owner_ref_val is not None:
                owner_ref_str = str(owner_ref_val).strip()
                if not owner_ref_str:
                    owner_ref_val = None
                else:
                    try:
                        parse_ref(owner_ref_str)
                    except Exception as exc:
                        raise ValidationError(
                            f"owner_ref is not a valid qualified ref: {exc}",
                            code="invalid_owner_ref",
                        ) from exc
                    owner_ref_val = owner_ref_str
            fields["owner_ref"] = owner_ref_val
        if "lifecycle" in patch:
            lc = str(patch["lifecycle"] or "").strip().lower()
            if lc == "archived":
                raise ValidationError(
                    "lifecycle 'archived' cannot be set via update; use archive_project",
                    code="invalid_lifecycle",
                )
            if lc not in PROJECT_LIFECYCLES:
                raise ValidationError(
                    f"lifecycle must be one of {sorted(PROJECT_LIFECYCLES)}, got {lc!r}",
                    code="invalid_lifecycle",
                )
            fields["lifecycle"] = lc
        if "posture" in patch:
            posture_val = str(patch["posture"]).strip() if patch["posture"] else None
            if posture_val and len(posture_val) > _POSTURE_MAX:
                raise ValidationError(
                    f"posture exceeds {_POSTURE_MAX} characters",
                    code="posture_too_long",
                )
            fields["posture"] = posture_val
        if "posture_reason" in patch:
            reason_val = str(patch["posture_reason"]).strip() if patch["posture_reason"] else None
            if reason_val and len(reason_val) > _POSTURE_REASON_MAX:
                raise ValidationError(
                    f"posture_reason exceeds {_POSTURE_REASON_MAX} characters",
                    code="posture_reason_too_long",
                )
            fields["posture_reason"] = reason_val
        for date_key in ("start_at", "target_at", "next_review_at"):
            if date_key in patch:
                date_val = patch[date_key]
                if date_val is not None:
                    date_str = str(date_val).strip()
                    if not date_str:
                        date_val = None
                    else:
                        try:
                            datetime.fromisoformat(date_str)
                        except (ValueError, TypeError) as exc:
                            raise ValidationError(
                                f"{date_key} is not valid ISO-8601: {date_str!r}",
                                code=f"invalid_{date_key}",
                            ) from exc
                        date_val = date_str
                fields[date_key] = date_val
        if "review_cadence_json" in patch:
            cadence = patch["review_cadence_json"]
            if cadence is not None:
                if not isinstance(cadence, dict):
                    raise ValidationError(
                        "review_cadence_json must be a dict",
                        code="invalid_review_cadence",
                    )
                if "every_days" in cadence:
                    try:
                        every = int(cadence["every_days"])
                    except (TypeError, ValueError) as exc:
                        raise ValidationError(
                            "review_cadence_json.every_days must be a positive integer",
                            code="invalid_review_cadence",
                        ) from exc
                    if every < 1:
                        raise ValidationError(
                            "review_cadence_json.every_days must be a positive integer",
                            code="invalid_review_cadence",
                        )
            fields["review_cadence_json"] = cadence
        if "template_key" in patch:
            tk = str(patch["template_key"]).strip() if patch["template_key"] else None
            if tk and len(tk) > _SLUG_MAX:
                raise ValidationError(
                    f"template_key exceeds {_SLUG_MAX} characters",
                    code="template_key_too_long",
                )
            fields["template_key"] = tk
        if "modules_json" in patch:
            mods = patch["modules_json"]
            if mods is not None:
                if not isinstance(mods, list):
                    raise ValidationError(
                        "modules_json must be a list of short slugs",
                        code="invalid_modules",
                    )
                cleaned: list[str] = []
                for m in mods:
                    slug = str(m).strip()
                    if len(slug) > _SLUG_MAX:
                        raise ValidationError(
                            f"modules_json entry exceeds {_SLUG_MAX} characters",
                            code="invalid_modules",
                        )
                    cleaned.append(slug)
                mods = cleaned
            fields["modules_json"] = mods

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            # Revision check (API-001)
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1

            # Apply the legacy field updates
            updates: list[str] = []
            params: list[Any] = []
            for key, value in fields.items():
                if key == "name":
                    updates.append("name = ?")
                    params.append(value)
                elif key == "description":
                    updates.append("description = ?")
                    params.append(value)
                elif key == "keywords":
                    updates.append("keywords_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "team_members":
                    updates.append("team_members_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "context":
                    updates.append("context_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "detection_threshold":
                    updates.append("detection_threshold = ?")
                    params.append(max(0.0, min(1.0, float(value))))
                # ── Room columns (HS-158-02) ─────────────────────────
                elif key in ("purpose", "outcome_text", "owner_ref",
                             "lifecycle", "posture", "posture_reason",
                             "start_at", "target_at", "next_review_at",
                             "template_key"):
                    updates.append(f"{key} = ?")
                    params.append(value)
                elif key == "review_cadence_json":
                    updates.append("review_cadence_json = ?")
                    params.append(
                        json.dumps(value, ensure_ascii=False) if value is not None else None
                    )
                elif key == "modules_json":
                    updates.append("modules_json = ?")
                    params.append(
                        json.dumps(value, ensure_ascii=False) if value is not None else None
                    )

            updates.append("revision = ?")
            params.append(new_revision)
            updates.append("updated_at = ?")
            params.append(now_iso)
            params.append(project_id)
            if updates:
                conn.execute(
                    f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                    params,
                )

            # Change log
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, _request_hash(fields),
                    json.dumps({"fields": list(fields.keys())}),
                    now_iso,
                ),
            )

            # Event
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "fields": list(fields.keys())},
                refs=[project_ref],
            )

            # Command
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "update_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    def archive_project(
        self, principal: Principal, project_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        self._require_project(project_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id, "action": "archive"})
        replay = self._check_idempotency(command_id, req_hash, "archive_project")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET is_archived = 1, lifecycle = 'archived', "
                "revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.archived",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"lifecycle": "archived"}),
                    now_iso,
                ),
            )

            # HS-167 M-2: pause active/tested watches bound to this
            # project and disable unattended policy — in the SAME
            # transaction — so an archived project never evaluates.
            from holdspeak.db.automations import AutomationRepository as _WatchRepo
            _WatchRepo.pause_project_watches_in_txn(conn, project_id, now_iso)

            policy = self._db.steward_policies.get_policy_for_project_in_transaction(
                conn, project_id,
            )
            if policy and policy.get("unattended_enabled"):
                self._db.steward_policies.update_policy_in_transaction(
                    conn, policy["id"], unattended_enabled=0,
                )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.archived",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id},
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.ARCHIVED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "archive_project",
                req_hash, envelope,
            )

        return True

    def restore_project(
        self, principal: Principal, project_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Restore an archived Project (DOM-011).

        If the project is not archived, returns a no_change result
        (API-002's honest reply).

        Watches paused by archive_project are NOT auto-resumed here —
        the owner resumes deliberately after restoring.
        """
        project = self._require_project(project_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id, "action": "restore"})
        replay = self._check_idempotency(command_id, req_hash, "restore_project")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        if not project.is_archived:
            # Not archived -- no-op per API-002
            with self._db._connection() as conn:
                current_rev = self._get_revision(conn, project_id)
                envelope = CommandResultEnvelope(
                    result_kind=ResultKind.NO_CHANGE,
                    project_id=project_id,
                    project_revision=current_rev,
                )
                self._record_command(
                    conn, cmd_id, project_id, "restore_project",
                    req_hash, envelope,
                )
            result = self._project_payload(project)
            result.update(_envelope_to_dict(envelope))
            return result

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET is_archived = 0, lifecycle = 'active', "
                "revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.restored",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"lifecycle": "active"}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.restored",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id},
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.RESTORED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "restore_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    def add_resource(
        self, principal: Principal, project_id: str,
        resource_ref: str, payload: dict[str, Any] | None = None,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        self._require_project(project_id)
        body = payload or {}
        ref_str = qualified_ref(resource_ref)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "resource_ref": ref_str, **body})
        replay = self._check_idempotency(command_id, req_hash, "add_resource")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        # HS-173-08 / 158 S-1: single transaction for revision bump +
        # resource upsert + change row + event + command.
        relation = str(body.get("relationship") or "member").strip().lower()
        if relation not in {"member", "source", "output", "related"}:
            raise ValueError(f"unknown project relationship: {relation}")

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Inline the resource upsert (was repo layer's own transaction).
            prior = conn.execute(
                "SELECT created_at FROM project_resources "
                "WHERE project_id=? AND resource_ref=?",
                (project_id, ref_str),
            ).fetchone()
            conn.execute(
                """INSERT INTO project_resources
                   (project_id, resource_ref, relationship, source, confidence,
                    created_at, last_modified, deleted)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                   ON CONFLICT(project_id, resource_ref) DO UPDATE SET
                     relationship=excluded.relationship, source=excluded.source,
                     confidence=excluded.confidence, last_modified=excluded.last_modified,
                     deleted=excluded.deleted""",
                (project_id, ref_str, relation, "manual", 1.0,
                 prior[0] if prior else now_iso, now_iso),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.resource.linked",
                    ref_str,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"resource_ref": ref_str}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.resource.linked",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "resource_ref": ref_str},
                refs=[project_ref, ref_str],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.LINKED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "add_resource",
                req_hash, envelope,
            )

        # Read the committed row through the repo layer (read-only).
        row = self._db.project_relationships.get(
            project_id, ref_str, include_deleted=True,
        )
        result = row.to_dict()  # type: ignore[union-attr]
        result.update(_envelope_to_dict(envelope))
        return result

    def remove_resource(
        self, principal: Principal, project_id: str, resource_ref: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        self._require_project(project_id)
        ref_str = qualified_ref(resource_ref)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "resource_ref": ref_str, "action": "remove"})
        replay = self._check_idempotency(command_id, req_hash, "remove_resource")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        # HS-173-08 / 158 S-1: single transaction for revision bump +
        # resource soft-delete + change row + event + command.
        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Inline the resource soft-delete (was repo layer's own transaction).
            cur = conn.execute(
                "UPDATE project_resources SET deleted=1, last_modified=? "
                "WHERE project_id=? AND resource_ref=? AND deleted=0",
                (now_iso, project_id, ref_str),
            )
            deleted = bool(cur.rowcount)

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.resource.unlinked",
                    ref_str,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"resource_ref": ref_str}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.resource.unlinked",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "resource_ref": ref_str},
                refs=[project_ref, ref_str],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UNLINKED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "remove_resource",
                req_hash, envelope,
            )

        return deleted

    def associate_meeting(
        self, principal: Principal, project_id: str, meeting_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        """Associate a meeting with a project.

        Meeting association event decision: SRS SS10 does NOT define a
        project.meeting.linked event kind.  We emit project.updated with
        the meeting ref in changed_refs/summary, since the association
        is a project mutation (it changes the project's meeting set) but
        is not a resource link (meetings have their own association table).
        """
        self._require_project(project_id)
        self._require_meeting(meeting_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "meeting_id": meeting_id,
                                  "action": "associate"})
        replay = self._check_idempotency(command_id, req_hash, "associate_meeting")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)
        meeting_ref = format_ref("meeting", meeting_id)

        # HS-173-08 / 158 S-1: single transaction for revision bump +
        # meeting association + change row + event + command.
        mid = str(meeting_id).strip()
        pid = str(project_id).strip()

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Inline meeting association (was repo layer's own transaction).
            conn.execute(
                """INSERT INTO meeting_projects
                   (meeting_id, project_id, source, confidence, detected_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(meeting_id, project_id) DO UPDATE SET
                     source = excluded.source,
                     confidence = MAX(meeting_projects.confidence, excluded.confidence),
                     detected_at = excluded.detected_at""",
                (mid, pid, "manual", 1.0, now_iso),
            )
            conn.execute(
                """INSERT INTO project_resources
                   (project_id, resource_ref, relationship, source, confidence,
                    created_at, last_modified, deleted)
                   VALUES (?, ?, 'member', ?, ?, ?, ?, 0)
                   ON CONFLICT(project_id, resource_ref) DO UPDATE SET
                     source=excluded.source,
                     confidence=MAX(project_resources.confidence, excluded.confidence),
                     last_modified=excluded.last_modified, deleted=0""",
                (pid, f"meeting:{mid}", "manual", 1.0, now_iso, now_iso),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    meeting_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"meeting_associated": meeting_id}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "meeting_associated": meeting_id,
                },
                refs=[project_ref, meeting_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(
                    parse_ref(project_ref),
                    parse_ref(meeting_ref),
                ),
            )
            self._record_command(
                conn, cmd_id, project_id, "associate_meeting",
                req_hash, envelope,
            )

        # HS-175-04: ensure the Room's meeting Watch exists after link
        try:
            from holdspeak.services.watch_service import ensure_meeting_watch
            ensure_meeting_watch(self._db, project_id, why="meeting linked")
        except Exception:
            _log.warning("ensure_meeting_watch failed for project %s", project_id)

        return True

    def disassociate_meeting(
        self, principal: Principal, project_id: str, meeting_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        """Disassociate a meeting from a project.

        Same event decision as associate_meeting: project.updated.
        """
        self._require_project(project_id)
        self._require_meeting(meeting_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "meeting_id": meeting_id,
                                  "action": "disassociate"})
        replay = self._check_idempotency(command_id, req_hash, "disassociate_meeting")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)
        meeting_ref = format_ref("meeting", meeting_id)

        # HS-173-08 / 158 S-1: single transaction for revision bump +
        # meeting disassociation + change row + event + command.
        mid = str(meeting_id).strip()
        pid = str(project_id).strip()

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Inline meeting disassociation (was repo layer's own transaction).
            conn.execute(
                "DELETE FROM meeting_projects "
                "WHERE meeting_id = ? AND project_id = ?",
                (mid, pid),
            )
            conn.execute(
                "UPDATE project_resources SET deleted=1, last_modified=? "
                "WHERE project_id=? AND resource_ref=?",
                (now_iso, pid, f"meeting:{mid}"),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    meeting_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"meeting_disassociated": meeting_id}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "meeting_disassociated": meeting_id,
                },
                refs=[project_ref, meeting_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(
                    parse_ref(project_ref),
                    parse_ref(meeting_ref),
                ),
            )
            self._record_command(
                conn, cmd_id, project_id, "disassociate_meeting",
                req_hash, envelope,
            )

        return True

    # ── item commands (HS-158-03) ──────────────────────────────────────

    def create_item(
        self, principal: Principal, project_id: str,
        payload: dict[str, Any],
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a typed item under a project (SYS-030, DOM-001).

        Items are Project-OWNED records (SS5.3); they increment the
        project's revision (not citizens, not in CITIZEN_TYPES).
        """
        self._require_project(project_id)

        item_type = str(payload.get("item_type") or "").strip()
        if item_type not in ITEM_TYPES:
            raise ValidationError(
                f"Unknown item_type: {item_type!r}; "
                f"must be one of {sorted(ITEM_TYPES)}",
                code="validation",
            )

        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValidationError("Item title is required", code="validation")

        severity = self._validate_severity(payload.get("severity"))
        lifecycle = str(payload.get("lifecycle") or "").strip() or ITEM_DEFAULT_LIFECYCLE[item_type]
        self._validate_lifecycle(item_type, lifecycle)

        owner_ref = self._validate_optional_ref(payload.get("owner_ref"), "owner_ref")
        created_by_ref = self._validate_optional_ref(
            payload.get("created_by_ref") or f"principal:{principal.identity}",
            "created_by_ref",
        )
        due_at = payload.get("due_at")
        sort_key = payload.get("sort_key")
        if sort_key is not None:
            try:
                sort_key = float(sort_key)
            except (TypeError, ValueError) as exc:
                raise ValidationError("sort_key must be a number", code="validation") from exc
        summary = payload.get("summary")

        # Validate and serialize details_json (DB-004)
        details = payload.get("details") or {}
        details_json = self._validate_details(item_type, details)

        provenance = str(payload.get("provenance_kind") or "owner").strip()
        if provenance not in PROVENANCE_KINDS:
            raise ValidationError(
                f"provenance_kind must be one of {sorted(PROVENANCE_KINDS)}",
                code="validation",
            )

        # Idempotency check
        req_hash = _request_hash({
            "project_id": project_id, "item_type": item_type,
            "title": title, **{k: v for k, v in payload.items()
                                if k not in ("command_id",)},
        })
        replay = self._check_idempotency(command_id, req_hash, "create_item")
        if replay is not None:
            return replay

        item_id = generate_pitem_id()
        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )
            new_revision = current_rev + 1

            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            conn.execute(
                """
                INSERT INTO project_items (
                    id, project_id, item_type, title, summary, lifecycle,
                    severity, owner_ref, due_at, sort_key, details_json,
                    provenance_kind, source_observation_id, created_by_ref,
                    revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    item_id, project_id, item_type, title, summary,
                    lifecycle, severity, owner_ref, due_at, sort_key,
                    details_json, provenance, payload.get("source_observation_id"),
                    created_by_ref, now_iso, now_iso,
                ),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None,
                    _request_hash({"item_id": item_id, "item_type": item_type}),
                    json.dumps({
                        "action": "item.created",
                        "item_id": item_id,
                        "item_type": item_type,
                        "title": title,
                    }),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "action": "item.created",
                    "item_id": item_id,
                    "item_type": item_type,
                },
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "create_item",
                req_hash, envelope,
            )

        item = self._db.projects.get_project_item(item_id)
        result = dict(item) if item else {"id": item_id}
        result.update(_envelope_to_dict(envelope))
        result["item_id"] = item_id
        return result

    def create_item_in_transaction(
        self, conn: Any, principal: Principal, project_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a typed item inside the caller's transaction (S-2 fix).

        Conn-accepting sibling of create_item, following the 159 M-1
        pattern (conn-threading).  The caller owns the connection and
        the transaction boundary; this method does validation (pure
        Python) then all DB writes on the provided conn.

        Preconditions (caller's job):
        - project_id exists (no _require_project read here)
        - idempotency is the caller's concern

        Returns the same result dict shape as create_item.
        """
        item_type = str(payload.get("item_type") or "").strip()
        if item_type not in ITEM_TYPES:
            raise ValidationError(
                f"Unknown item_type: {item_type!r}; "
                f"must be one of {sorted(ITEM_TYPES)}",
                code="validation",
            )

        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValidationError("Item title is required", code="validation")

        severity = self._validate_severity(payload.get("severity"))
        lifecycle = str(payload.get("lifecycle") or "").strip() or ITEM_DEFAULT_LIFECYCLE[item_type]
        self._validate_lifecycle(item_type, lifecycle)

        owner_ref = self._validate_optional_ref(payload.get("owner_ref"), "owner_ref")
        created_by_ref = self._validate_optional_ref(
            payload.get("created_by_ref") or f"principal:{principal.identity}",
            "created_by_ref",
        )
        due_at = payload.get("due_at")
        sort_key = payload.get("sort_key")
        if sort_key is not None:
            try:
                sort_key = float(sort_key)
            except (TypeError, ValueError) as exc:
                raise ValidationError("sort_key must be a number", code="validation") from exc
        summary = payload.get("summary")

        # Validate and serialize details_json (DB-004)
        details = payload.get("details") or {}
        details_json = self._validate_details(item_type, details)

        provenance = str(payload.get("provenance_kind") or "owner").strip()
        if provenance not in PROVENANCE_KINDS:
            raise ValidationError(
                f"provenance_kind must be one of {sorted(PROVENANCE_KINDS)}",
                code="validation",
            )

        item_id = generate_pitem_id()
        cmd_id = generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        current_rev = self._get_revision(conn, project_id)
        new_revision = current_rev + 1

        conn.execute(
            "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
            (new_revision, now_iso, project_id),
        )

        conn.execute(
            """
            INSERT INTO project_items (
                id, project_id, item_type, title, summary, lifecycle,
                severity, owner_ref, due_at, sort_key, details_json,
                provenance_kind, source_observation_id, created_by_ref,
                revision, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                item_id, project_id, item_type, title, summary,
                lifecycle, severity, owner_ref, due_at, sort_key,
                details_json, provenance, payload.get("source_observation_id"),
                created_by_ref, now_iso, now_iso,
            ),
        )

        change_id = generate_pchg_id(
            project_id=project_id,
            project_revision=new_revision,
            ordinal=0,
        )
        req_hash = _request_hash({
            "project_id": project_id, "item_type": item_type,
            "title": title, **{k: v for k, v in payload.items()
                                if k not in ("command_id",)},
        })
        conn.execute(
            """
            INSERT INTO project_changes (
                id, project_id, project_revision, change_kind,
                target_ref, actor_ref, command_id,
                before_hash, after_hash, summary_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                change_id, project_id, new_revision,
                "project.updated",
                project_ref,
                f"principal:{principal.identity}",
                cmd_id, None,
                _request_hash({"item_id": item_id, "item_type": item_type}),
                json.dumps({
                    "action": "item.created",
                    "item_id": item_id,
                    "item_type": item_type,
                    "title": title,
                }),
                now_iso,
            ),
        )

        self._ledger.append_in_transaction(
            conn, principal,
            event_type="project.updated",
            producer="ProjectService",
            subject_ref=project_ref,
            source_revision=str(new_revision),
            facts={
                "project_id": project_id,
                "action": "item.created",
                "item_id": item_id,
                "item_type": item_type,
            },
            refs=[project_ref],
        )

        envelope = CommandResultEnvelope(
            result_kind=ResultKind.UPDATED,
            project_id=project_id,
            project_revision=new_revision,
            changed_refs=(parse_ref(project_ref),),
        )
        self._record_command(
            conn, cmd_id, project_id, "create_item",
            req_hash, envelope,
        )

        result = _envelope_to_dict(envelope)
        result["item_id"] = item_id
        return result

    def update_item(
        self, principal: Principal, project_id: str, item_id: str,
        patch: dict[str, Any],
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update mutable fields on an item (SYS-031, DOM-006)."""
        self._require_project(project_id)
        existing = self._db.projects.get_project_item(item_id)
        if existing is None or existing["project_id"] != project_id:
            raise NotFound("project_item", item_id)

        item_type = existing["item_type"]

        # Build validated fields
        fields: dict[str, Any] = {}
        if "title" in patch:
            title = str(patch["title"] or "").strip()
            if not title:
                raise ValidationError("Item title cannot be empty", code="validation")
            fields["title"] = title
        if "summary" in patch:
            fields["summary"] = patch["summary"]
        if "severity" in patch:
            fields["severity"] = self._validate_severity(patch["severity"])
        if "owner_ref" in patch:
            fields["owner_ref"] = self._validate_optional_ref(patch["owner_ref"], "owner_ref")
        if "due_at" in patch:
            fields["due_at"] = patch["due_at"]
        if "sort_key" in patch:
            sk = patch["sort_key"]
            if sk is not None:
                try:
                    sk = float(sk)
                except (TypeError, ValueError) as exc:
                    raise ValidationError("sort_key must be a number", code="validation") from exc
            fields["sort_key"] = sk
        if "details" in patch:
            fields["details_json"] = self._validate_details(item_type, patch["details"] or {})

        # Lifecycle via update is allowed but NOT for completing milestones (DOM-007)
        if "lifecycle" in patch:
            new_lc = str(patch["lifecycle"]).strip()
            self._validate_lifecycle(item_type, new_lc)
            if item_type == "milestone" and new_lc == "reached":
                raise ValidationError(
                    "Milestones cannot be completed through a field update; "
                    "use the transition verb (DOM-007)",
                    code="validation",
                )
            fields["lifecycle"] = new_lc

        if not fields:
            raise ValidationError("No updatable fields supplied", code="validation")

        # Idempotency
        req_hash = _request_hash({"project_id": project_id, "item_id": item_id, **patch})
        replay = self._check_idempotency(command_id, req_hash, "update_item")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )
            new_revision = current_rev + 1

            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Update item fields
            item_updates: list[str] = []
            item_params: list[Any] = []
            for key, value in fields.items():
                item_updates.append(f"{key} = ?")
                item_params.append(value)
            item_updates.append("revision = revision + 1")
            item_updates.append("updated_at = ?")
            item_params.append(now_iso)
            item_params.append(item_id)
            conn.execute(
                f"UPDATE project_items SET {', '.join(item_updates)} WHERE id = ?",
                item_params,
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None,
                    _request_hash(fields),
                    json.dumps({
                        "action": "item.updated",
                        "item_id": item_id,
                        "fields": list(fields.keys()),
                    }),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "action": "item.updated",
                    "item_id": item_id,
                    "fields": list(fields.keys()),
                },
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "update_item",
                req_hash, envelope,
            )

        item = self._db.projects.get_project_item(item_id)
        result = dict(item) if item else {"id": item_id}
        result.update(_envelope_to_dict(envelope))
        result["item_id"] = item_id
        return result

    def transition_item(
        self, principal: Principal, project_id: str, item_id: str,
        verb: str, payload: dict[str, Any] | None = None,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Explicit lifecycle verb on an item (DOM-007).

        The verb IS the target lifecycle state.  DOM-007 is satisfied
        because a milestone can ONLY reach "reached" through this method
        (update_item refuses it), and this method requires an explicit
        verb from the caller -- narrative prose cannot invoke it.
        """
        self._require_project(project_id)
        existing = self._db.projects.get_project_item(item_id)
        if existing is None or existing["project_id"] != project_id:
            raise NotFound("project_item", item_id)

        body = payload or {}
        item_type = existing["item_type"]
        verb = str(verb).strip()
        self._validate_lifecycle(item_type, verb)

        current_lc = existing["lifecycle"]
        if current_lc == verb:
            # No-op: already in that state
            with self._db._connection() as conn:
                current_rev = self._get_revision(conn, project_id)
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.NO_CHANGE,
                project_id=project_id,
                project_revision=current_rev,
            )
            result = dict(existing)
            result.update(_envelope_to_dict(envelope))
            result["item_id"] = item_id
            return result

        # Idempotency
        req_hash = _request_hash({
            "project_id": project_id, "item_id": item_id,
            "verb": verb, **body,
        })
        replay = self._check_idempotency(command_id, req_hash, "transition_item")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )
            new_revision = current_rev + 1

            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            conn.execute(
                "UPDATE project_items SET lifecycle = ?, revision = revision + 1, "
                "updated_at = ? WHERE id = ?",
                (verb, now_iso, item_id),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({
                        "action": "item.transitioned",
                        "item_id": item_id,
                        "from": current_lc,
                        "to": verb,
                    }),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "action": "item.transitioned",
                    "item_id": item_id,
                    "from": current_lc,
                    "to": verb,
                },
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "transition_item",
                req_hash, envelope,
            )

        item = self._db.projects.get_project_item(item_id)
        result = dict(item) if item else {"id": item_id}
        result.update(_envelope_to_dict(envelope))
        result["item_id"] = item_id
        return result

    def list_items(
        self, principal: Principal, project_id: str,
        *, item_type: Optional[str] = None,
        limit: int = 200, offset: int = 0,
    ) -> dict[str, Any]:
        """List items for a project, bounded and deterministically ordered.

        Order: item_type ASC, sort_key ASC NULLS LAST, created_at ASC, id ASC.
        Pagination via limit/offset (sibling convention).
        """
        self._require_project(project_id)
        clean_limit = max(1, min(int(limit), 1000))
        clean_offset = max(0, int(offset))

        with self._db._connection() as conn:
            if item_type:
                if item_type not in ITEM_TYPES:
                    raise ValidationError(
                        f"Unknown item_type filter: {item_type!r}",
                        code="validation",
                    )
                rows = conn.execute(
                    """
                    SELECT * FROM project_items
                    WHERE project_id = ? AND item_type = ?
                    ORDER BY sort_key IS NULL, sort_key ASC,
                             created_at ASC, id ASC
                    LIMIT ? OFFSET ?
                    """,
                    (project_id, item_type, clean_limit, clean_offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM project_items
                    WHERE project_id = ?
                    ORDER BY item_type ASC,
                             sort_key IS NULL, sort_key ASC,
                             created_at ASC, id ASC
                    LIMIT ? OFFSET ?
                    """,
                    (project_id, clean_limit, clean_offset),
                ).fetchall()

        return {
            "items": [dict(r) for r in rows],
            "limit": clean_limit,
            "offset": clean_offset,
        }

    # ── item validation helpers ─────────────────────────────────────────

    @staticmethod
    def _validate_severity(value: Any) -> Optional[str]:
        """Validate severity (nullable, closed vocabulary)."""
        if value is None or value == "":
            return None
        sev = str(value).strip().lower()
        if sev not in SEVERITY_LEVELS:
            raise ValidationError(
                f"severity must be one of {sorted(SEVERITY_LEVELS)} or null, "
                f"got {sev!r}",
                code="validation",
            )
        return sev

    @staticmethod
    def _validate_lifecycle(item_type: str, lifecycle: str) -> None:
        """Validate lifecycle against the item type's closed vocabulary."""
        valid = ITEM_LIFECYCLES.get(item_type)
        if valid is None:
            raise ValidationError(
                f"Unknown item_type: {item_type!r}",
                code="validation",
            )
        if lifecycle not in valid:
            raise ValidationError(
                f"lifecycle {lifecycle!r} is not valid for {item_type}; "
                f"must be one of {list(valid)}",
                code="validation",
            )

    @staticmethod
    def _validate_optional_ref(value: Any, field_name: str) -> Optional[str]:
        """Validate an optional qualified ref through holdspeak.refs."""
        if value is None or value == "":
            return None
        ref_str = str(value).strip()
        try:
            parse_ref(ref_str)
        except Exception as exc:
            raise ValidationError(
                f"{field_name} is not a valid qualified ref: {ref_str!r}",
                code="validation",
            ) from exc
        return ref_str

    @staticmethod
    def _validate_details(item_type: str, details: dict[str, Any]) -> str:
        """Validate details_json against the closed per-type schema (DB-004).

        Returns the JSON string to persist.  Unknown fields or wrong types
        raise a typed validation error.
        """
        schema = _DETAILS_SCHEMAS.get(item_type)
        if schema is None:
            raise ValidationError(
                f"No details schema for item_type {item_type!r}",
                code="validation",
            )

        if not isinstance(details, dict):
            raise ValidationError(
                "details must be a JSON object",
                code="validation",
            )

        # Refuse unknown fields
        unknown = set(details.keys()) - set(schema.keys())
        if unknown:
            raise ValidationError(
                f"Unknown fields in details for {item_type}: {sorted(unknown)}",
                code="validation",
            )

        # Validate each field
        clean: dict[str, Any] = {}
        for field_name, (required, validator) in schema.items():
            value = details.get(field_name)
            if value is None and field_name not in details:
                if required:
                    raise ValidationError(
                        f"details.{field_name} is required for {item_type}",
                        code="validation",
                    )
                continue  # omitted optional field
            if not validator(value):
                raise ValidationError(
                    f"details.{field_name} has invalid type/value for {item_type}",
                    code="validation",
                )
            clean[field_name] = value

        return json.dumps(clean, ensure_ascii=False)

    # ── internal helpers ─────────────────────────────────────────────

    def _require_project(self, project_id: str) -> Any:
        project = self._db.projects.get_project(project_id)
        if project is None:
            raise NotFound("project", project_id)
        return project

    def _require_meeting(self, meeting_id: str) -> Any:
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            raise NotFound("meeting", meeting_id)
        return meeting

    @staticmethod
    def _strings(value: Any) -> list[str]:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value or []

    @staticmethod
    def _threshold(value: Any) -> float:
        try:
            threshold = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("detection_threshold must be between 0 and 1") from exc
        if not 0.0 <= threshold <= 1.0:
            raise ValidationError("detection_threshold must be between 0 and 1")
        return threshold

    @staticmethod
    def _project_payload(project: Any) -> dict[str, Any]:
        return {"id": project.id, "name": project.name, "description": project.description,
                "keywords": project.keywords, "team_members": project.team_members, "context": project.context,
                "detection_threshold": project.detection_threshold, "is_archived": project.is_archived,
                "meeting_count": project.meeting_count, "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()}

    def _get_revision(self, conn: Any, project_id: str) -> int:
        """Read the current revision inside an open transaction."""
        row = conn.execute(
            "SELECT revision FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise NotFound("project", project_id)
        return int(row["revision"])

    def _check_idempotency(
        self, command_id: Optional[str], req_hash: str, command_kind: str,
    ) -> Optional[dict[str, Any]]:
        """API-002: if command_id is given, check for replay or conflict.

        Returns stored result dict on replay, None on new command.
        Raises ConflictError on hash mismatch.
        """
        if command_id is None:
            return None
        existing = self._db.projects.get_project_command(command_id)
        if existing is None:
            return None
        if existing["status"] == "completed" and existing["request_hash"] == req_hash:
            # Replay: return stored result
            if existing["result_json"]:
                return json.loads(existing["result_json"])
            return {"result_kind": "no_change", "project_id": existing["project_id"]}
        if existing["request_hash"] != req_hash:
            raise ConflictError(
                "idempotency conflict: same command_id with different request hash",
                code="idempotency_conflict",
                context={"command_id": command_id},
            )
        # Pending command with same hash -- proceed (could be a retry after crash)
        return None

    def _record_command(
        self,
        conn: Any,
        command_id: str,
        project_id: str,
        command_kind: str,
        request_hash: str,
        envelope: CommandResultEnvelope,
    ) -> None:
        """Record a completed command in the idempotency ledger."""
        now_iso = datetime.now().isoformat()
        result_json = json.dumps(_envelope_to_dict(envelope), ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO project_commands (
                id, project_id, command_kind, request_hash,
                status, result_json, completed_at, created_at
            ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = 'completed',
                result_json = excluded.result_json,
                completed_at = excluded.completed_at
            """,
            (
                command_id, project_id, command_kind, request_hash,
                result_json, now_iso, now_iso,
            ),
        )
