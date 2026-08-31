"""Transport-neutral project and relationship operations (HS-123-05).

HS-158-02 graduation: every accepted write increments projects.revision
exactly once, appends a project_changes row and a ServiceEventLedger event
in the same transaction (DOM-003, DOM-004, API-004).  Optional
expected_revision / command_id enforce optimistic concurrency (API-001)
and idempotent replay (API-002, DOM-010).  Absent params = legacy behavior
(API-006).

HS-158-03: item commands under the revision law (create/update/transition/
list).  Items are Project-OWNED records (SS5.3), not citizens (SS3.2).
changed_refs carries ``project:<id>``; the item id rides in the result
payload.  Event kind is ``project.updated`` (SS10 has no item event kind).
"""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from ..db.core import Database
from ..db.relationships import qualified_ref
from ..logging_config import get_logger
from ..meeting_aftercare import compute_project_since_last_meeting
from ..principals import Principal
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

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        self._ledger = ServiceEventLedger(db)

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

        return {
            "project_id": project_id,
            "revision": revision,
            "observed_at": observed_at,
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
            "review": dict(_ABSENT_SECTION),
            "sources": dict(_ABSENT_SECTION),
            "updates": dict(_ABSENT_SECTION),
            "steward": dict(_ABSENT_SECTION),
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
                connector_id = spec.get("provider", {}).get("id", "native")
                query_kind = spec.get("subject", {}).get("kind", "")
                query = spec.get("subject", {}).get("scope", {})
                trigger = spec.get("trigger") or CADENCE_PRESETS.get("normal", {})
                mode = spec.get("mode", "yolo")

                # Insert into connector_watches with graduated columns
                conn.execute(
                    """
                    INSERT INTO connector_watches (
                        id, connector_id, query_kind, name, query_json, enabled,
                        schema_version, project_id, intent, subject_kind,
                        trigger_kind, trigger_json, mode, state, revision,
                        baseline_state, test_state, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        watch_id, connector_id, query_kind, watch_name,
                        json.dumps(query, sort_keys=True, separators=(",", ":")),
                        1,  # enabled
                        "WatchSpec@1", project_id,
                        spec.get("intent", ""),
                        query_kind,
                        trigger.get("kind", "poll"),
                        json.dumps(trigger, sort_keys=True, separators=(",", ":")),
                        mode, "active", 1,
                        "established",  # ACT-005: baseline without events
                        "passed",  # carried from proposal test
                        now_iso, now_iso,
                    ),
                )

                # 3. Create watch_rules
                rules = spec.get("rules", [])
                for ordinal, rule in enumerate(rules):
                    rule_id = f"wrule_{uuid.uuid4().hex[:12]}"
                    conn.execute(
                        """
                        INSERT INTO watch_rules (
                            id, watch_id, ordinal, condition_schema, condition_json,
                            action_schema, action_json, enabled, revision,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rule_id, watch_id, ordinal,
                            "WatchCondition@1",
                            json.dumps(
                                rule.get("condition", {}),
                                sort_keys=True, separators=(",", ":"),
                            ),
                            "WatchAction@1",
                            json.dumps(
                                rule.get("actions", []),
                                sort_keys=True, separators=(",", ":"),
                            ),
                            1, 0, now_iso, now_iso,
                        ),
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

        # The upsert through the repo layer (its own connection/transaction)
        row = self._db.project_relationships.upsert(
            project_id=project_id, resource_ref=ref_str,
            relationship=str(body.get("relationship") or "member"),
            source="manual", confidence=1.0,
        )

        with self._db._connection() as conn:
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

        result = row.to_dict()
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

        deleted = self._db.project_relationships.delete(project_id, ref_str)

        with self._db._connection() as conn:
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

        # The legacy repo layer does its own connection
        self._db.projects.associate_meeting_project(
            meeting_id=meeting_id, project_id=project_id,
            source="manual", confidence=1.0,
        )

        with self._db._connection() as conn:
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

        self._db.projects.disassociate_meeting_project(
            meeting_id=meeting_id, project_id=project_id,
        )

        with self._db._connection() as conn:
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
