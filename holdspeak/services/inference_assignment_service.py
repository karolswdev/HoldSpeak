"""Canonical sparse InferenceAssignment@1 authority (HS-143-04).

Assignments are hub-local configuration, not execution plans.  This service
owns the whole ordered-chain CAS and deterministic inheritance projection; it
does not perform fallback, reserve capacity, or reach a provider.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Callable, Iterable, Mapping

from ..inference_capabilities import (
    InferenceCapabilityDefinition,
    InferenceCapabilityRegistry,
    process_inference_capability_registry,
)
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound, ServiceError, ValidationError
from .model_profile_service import (
    ModelProfileService,
    adapt_v1_profile,
    resolve_v1_profile_execution,
)
from .tool_capability_service import (
    ToolCapabilityError,
    ToolCapabilityFoundation,
    parse_capability_manifest,
)


ASSIGNMENT_SCHEMA = "InferenceAssignment@1"
PROJECTION_SCHEMA = "InferenceAssignmentProjection@1"
_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,191}$")
_PROFILE_ID = re.compile(r"^[a-z][a-z0-9_-]{0,95}$")
_SUBJECT_KINDS = frozenset({"thought", "workbench", "agent", "recipe", "project"})
_BOUNDARY_ALIASES = {
    "same_device": "local",
    "local": "local",
    "private_network": "private_network",
    "private_mesh": "mesh",
    "mesh": "mesh",
    "paired": "mesh",
    "cloud": "cloud",
    "external_service": "cloud",
}
_CANONICAL_GROUPS = (
    ("thoughts_notes", "Thoughts & notes"),
    ("writing_dictation", "Writing & dictation"),
    ("speech_recognition", "Speech recognition"),
    ("meetings", "Meetings"),
    ("agents_tools", "Agents & tools"),
    ("background", "Background"),
)
_CANONICAL_GROUP_IDS = frozenset(group_id for group_id, _label in _CANONICAL_GROUPS)


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def _safe_id(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if not _ID.fullmatch(clean):
        raise ValidationError(
            f"{field} is invalid", code="inference_assignment_invalid"
        )
    return clean


class InferenceAssignmentService:
    """OWNER-only command and read service over one assignment authority."""

    def __init__(
        self,
        db: Any,
        *,
        registry: InferenceCapabilityRegistry | None = None,
        tool_capability_foundation: ToolCapabilityFoundation | None = None,
    ) -> None:
        self._db = db
        self._registry = registry or process_inference_capability_registry()
        self._profiles = ModelProfileService(db)
        # This is composition, not a caller flag: absent registration means a
        # qualified offline manifest remains non-executable by design.
        self._tool_capability_foundation = tool_capability_foundation

    def bind_tool_capability_foundation(
        self, foundation: ToolCapabilityFoundation
    ) -> None:
        """Install the one process-owned executable foundation.

        Route/assignment callers cannot provide this as request data.  Startup
        composition binds the concrete ToolTurn controller exactly once; an
        attempted replacement would make a previously saved qualification mean
        something different and is therefore refused.
        """
        if not isinstance(foundation, ToolCapabilityFoundation):
            raise ValueError("tool capability foundation is invalid")
        if (
            self._tool_capability_foundation is not None
            and self._tool_capability_foundation is not foundation
        ):
            raise ValueError("tool capability foundation is already bound")
        self._tool_capability_foundation = foundation

    @staticmethod
    def _require_owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "inference_assignment_owner_required",
                "Owner access is required",
                context={"status": 403},
            )

    def list_assignments(self, principal: Principal) -> dict[str, Any]:
        self._require_owner(principal)
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT r.*, h.assignment_key AS head_key, h.assignment_id AS head_id,
                          h.revision AS head_revision, h.cleared AS head_cleared
                     FROM inference_assignment_heads h
                     JOIN inference_assignment_revisions r
                       ON r.assignment_id=h.assignment_id AND r.revision=h.revision
                    WHERE h.cleared=0 ORDER BY r.assignment_key"""
            ).fetchall()
            assignments = [self._row_projection(conn, row) for row in rows]
        return {"schema": "InferenceAssignmentList@1", "assignments": assignments}

    def assignment_summary(self, principal: Principal) -> dict[str, Any]:
        """Return the bounded seven-row owner roster, derived only by the server."""
        self._require_owner(principal)
        with self._db._connection() as conn:
            global_row = self._head(conn, "global")
            default_projection = (
                None if global_row is None else self._row_projection(conn, global_row)
            )
            rows: list[dict[str, Any]] = [
                {
                    "id": "global",
                    "label": "Default for AI work",
                    "inherited_from": None,
                    "assignment": default_projection,
                    "status": "no_assignment"
                    if default_projection is None
                    else "assigned",
                    "repair": "Choose default" if default_projection is None else None,
                }
            ]
            owner_capabilities = tuple(
                definition
                for capability_id in self._registry.capability_ids
                for definition in (self._registry.require(capability_id),)
                if definition.owner_visibility == "owner"
            )
            # The roster's Change command needs one exact capability context for
            # group/global compatibility facts.  This is a server selection, not
            # a browser guess; global chooses the stable first owner capability.
            rows[0]["editor_capability_id"] = (
                owner_capabilities[0].id if owner_capabilities else None
            )
            unknown = sorted(
                {
                    definition.group_id
                    for definition in owner_capabilities
                    if definition.group_id not in _CANONICAL_GROUP_IDS
                }
            )
            if unknown:
                rows[0]["issues"] = [
                    {
                        "code": "unknown_owner_capability_groups",
                        "severity": "blocking",
                        "group_ids": unknown,
                    }
                ]
                rows[0]["repair"] = "Fix"
            for group_id, group_label in _CANONICAL_GROUPS:
                capabilities = tuple(
                    definition
                    for definition in owner_capabilities
                    if definition.group_id == group_id
                )
                group_row = self._head(conn, f"group:{group_id}")
                source_row = group_row or global_row
                projection = None
                issues: list[dict[str, Any]] = []
                if source_row is not None:
                    projection = self._row_projection(conn, source_row)
                    for capability in capabilities:
                        issues.extend(
                            self._compatibility_issues(
                                conn,
                                projection["committed_effect"]["entries"]
                                if "committed_effect" in projection
                                else json.loads(str(source_row["payload_json"]))[
                                    "entries"
                                ],
                                (capability,),
                            )
                        )
                    projection["issues"] = self._dedupe_issues(issues)
                rows.append(
                    {
                        "id": group_id,
                        "label": group_label,
                        "editor_capability_id": capabilities[0].id if capabilities else None,
                        "inherited_from": "group"
                        if group_row is not None
                        else ("global" if global_row is not None else None),
                        "assignment": projection,
                        "status": "no_assignment"
                        if projection is None
                        else (
                            "no_compatible_assignment"
                            if any(
                                i["severity"] == "blocking"
                                for i in projection["issues"]
                            )
                            else "assigned"
                        ),
                        "repair": "Fix"
                        if projection is not None and projection["issues"]
                        else None,
                    }
                )
            task_overrides = []
            for capability in owner_capabilities:
                exact = self._head(conn, f"capability:{capability.id}")
                effective = self._resolve(conn, capability)
                issues = (
                    []
                    if effective["assignment"] is None
                    else list(effective["assignment"].get("issues") or [])
                )
                task_overrides.append(
                    {
                        "id": capability.id,
                        "label": capability.label,
                        "group": {"id": capability.group_id, "label": capability.group_label},
                        "has_override": exact is not None,
                        "effective": effective,
                        "issues": issues,
                    }
                )
        return {
            "schema": "InferenceAssignmentSummary@1",
            "rows": rows,
            "task_overrides": task_overrides,
            "issue_count": sum(1 for row in rows if row["repair"] is not None),
        }

    def assignment_editor_projection(
        self, principal: Principal, body: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Project one closed, server-decided assignment editor.

        The browser receives candidates and compatibility facts already evaluated
        against the selected capability revision.  It never receives a profile
        locator or needs to reproduce assignment precedence.
        """
        self._require_owner(principal)
        if (
            not isinstance(body, Mapping)
            or set(body) != {"scope", "capability_id"}
            or not isinstance(body.get("capability_id"), str)
        ):
            raise ValidationError(
                "Assignment editor request has an invalid shape",
                code="inference_assignment_invalid",
            )
        scope = self._scope(body["scope"])
        capability = self._require_assignable(body["capability_id"])
        self._validate_scope_capability(scope, capability)
        with self._db._connection() as conn:
            active = self._head(conn, scope["assignment_key"])
            current = self._current(conn, scope["assignment_key"])
            configured = (
                None
                if active is None
                else self._row_projection(conn, active)
            )
            effective = self._resolve(conn, capability)
            candidates = self._editor_candidates(
                conn, scope, self._affected_capabilities(scope)
            )
        return {
            "schema": "AssignmentEditorProjection@1",
            "scope": self._public_scope(scope),
            "selected_capability": {
                "id": capability.id,
                "revision": capability.revision,
                "label": capability.label,
                "group": {"id": capability.group_id, "label": capability.group_label},
                "allowed_boundaries": list(capability.allowed_boundaries),
                "fallback_dispositions": list(capability.fallback_dispositions),
            },
            "draft_base_revision": 0 if current is None else int(current["revision"]),
            "configured_assignment": configured,
            "effective": effective,
            "candidates": candidates,
            "retry_policy": {
                "permitted_ids": list(capability.permitted_retry_policy_ids),
                "default_id": capability.default_retry_policy_id,
            },
        }

    def _editor_candidates(
        self,
        conn: Any,
        scope: Mapping[str, str],
        capabilities: Iterable[InferenceCapabilityDefinition],
    ) -> list[dict[str, Any]]:
        """Return only candidates compatible with every affected capability."""
        affected = tuple(capabilities)
        rows = conn.execute(
            """SELECT r.* FROM model_profile_revisions r
                 JOIN (SELECT profile_id, MAX(revision) AS revision
                         FROM model_profile_revisions GROUP BY profile_id) latest
                   ON latest.profile_id=r.profile_id AND latest.revision=r.revision
                 LEFT JOIN model_profile_tombstones t ON t.profile_id=r.profile_id
                WHERE t.profile_id IS NULL ORDER BY r.label COLLATE NOCASE, r.profile_id"""
        ).fetchall()
        candidates: list[dict[str, Any]] = []
        for row in rows:
            entry = {
                "ordinal": 1,
                "profile_id": str(row["profile_id"]),
                "profile_revision": int(row["revision"]),
                "profile_schema_version": 2,
            }
            issues = self._compatibility_issues(conn, [entry], affected)
            # Match the canonical command's group/global structural rule: a
            # partial member incompatibility stays visible as a server-described
            # repair, while a chain usable by no affected member is excluded.
            if self._save_blockers(scope, [entry], affected, issues):
                continue
            runtime = self._entry_runtime_projection(conn, entry)
            candidates.append(
                {
                    "profile_id": entry["profile_id"],
                    "profile_revision": entry["profile_revision"],
                    "label": str(row["label"]),
                    "boundary": runtime["boundary"],
                    "readiness": runtime["readiness"],
                    "status": "savable_with_repair" if issues else "compatible",
                    "issues": self._dedupe_issues(issues),
                }
            )
        return candidates

    def get_assignment(
        self, principal: Principal, scope: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._require_owner(principal)
        parsed = self._scope(scope)
        with self._db._connection() as conn:
            row = self._head(conn, parsed["assignment_key"])
            if row is None:
                raise NotFound("inference assignment", parsed["assignment_key"])
            return self._row_projection(conn, row)

    def set_assignment(
        self, principal: Principal, body: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._require_owner(principal)
        request = self._set_request(body)
        request_hash = _sha256({"command": "set", **request})
        receipt_context = {
            "action": "set",
            "scope": self._public_scope(request["scope"]),
            "expected_revision": request["expected_revision"],
        }
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = self._replay(
                    conn, request["command_id"], request_hash, receipt_context
                )
                if replay is not None:
                    conn.commit()
                    return replay
                current = self._current(conn, request["scope"]["assignment_key"])
                current_revision = 0 if current is None else int(current["revision"])
                if current_revision != request["expected_revision"]:
                    raise ConflictError(
                        "Assignment changed. Refresh before saving.",
                        code="inference_assignment_revision_conflict",
                        context={
                            "expected_revision": request["expected_revision"],
                            "current_revision": current_revision,
                        },
                    )
                entries = self._validate_entries(
                    conn, request["entries"], request["scope"]
                )
                affected = self._affected_capabilities(request["scope"])
                policy_id = self._validate_policy(request["retry_policy_id"], affected)
                issues = self._compatibility_issues(conn, entries, affected)
                structural = self._save_blockers(
                    request["scope"], entries, affected, issues
                )
                if structural:
                    raise ValidationError(
                        "Assignment contains an incompatible model.",
                        code="inference_assignment_incompatible",
                        context={"issues": structural},
                    )
                revision = current_revision + 1
                assignment_id = (
                    str(current["assignment_id"])
                    if current is not None
                    else "ia_" + uuid.uuid4().hex
                )
                created_at = _now()
                material = {
                    "schema": ASSIGNMENT_SCHEMA,
                    "id": assignment_id,
                    "scope": self._public_scope(request["scope"]),
                    "entries": entries,
                    "retry_policy_id": policy_id,
                    "revision": revision,
                    "created_at": created_at,
                }
                digest = _sha256(material)
                conn.execute(
                    """INSERT INTO inference_assignment_revisions
                       (assignment_id,revision,assignment_key,scope_kind,scope_id,subject_kind,
                        selector_kind,capability_id,group_id,retry_policy_id,payload_json,sha256,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        assignment_id,
                        revision,
                        request["scope"]["assignment_key"],
                        request["scope"]["scope_kind"],
                        request["scope"].get("scope_id", ""),
                        request["scope"].get("subject_kind", ""),
                        request["scope"]["selector_kind"],
                        request["scope"].get("capability_id", ""),
                        request["scope"].get("group_id", ""),
                        policy_id,
                        _canonical(material),
                        digest,
                        created_at,
                    ),
                )
                conn.execute(
                    """INSERT INTO inference_assignment_heads(assignment_key,assignment_id,revision,cleared,updated_at)
                       VALUES (?,?,?,?,?) ON CONFLICT(assignment_key) DO UPDATE SET
                       assignment_id=excluded.assignment_id,revision=excluded.revision,cleared=0,updated_at=excluded.updated_at""",
                    (
                        request["scope"]["assignment_key"],
                        assignment_id,
                        revision,
                        0,
                        created_at,
                    ),
                )
                for entry in entries:
                    conn.execute(
                        """INSERT INTO inference_assignments
                           (id,assignment_id,assignment_revision,profile_id,profile_revision,profile_schema_version,ordinal)
                           VALUES (?,?,?,?,?,?,?)""",
                        (
                            f"{assignment_id}:{revision}:{entry['ordinal']}",
                            assignment_id,
                            revision,
                            entry["profile_id"],
                            entry["profile_revision"],
                            entry["profile_schema_version"],
                            entry["ordinal"],
                        ),
                    )
                stored_row = self._head(conn, request["scope"]["assignment_key"])
                if (
                    stored_row is None
                ):  # pragma: no cover - guarded by the transaction above
                    raise ConflictError(
                        "Assignment head was not durably created.",
                        code="inference_assignment_integrity_invalid",
                    )
                result = self._row_projection(conn, stored_row)
                result = self._command_receipt(
                    result,
                    committed_effect=self._assignment_effect(
                        self._assignment_material(conn, stored_row), digest
                    ),
                    current=result,
                )
                self._record_command(
                    conn,
                    request["command_id"],
                    request_hash,
                    result,
                    context=receipt_context,
                )
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def preview_use_default(
        self,
        principal: Principal,
        *,
        scope: Mapping[str, Any],
        capability_id: str,
        invocation_id: str | None = None,
        subject_kind: str | None = None,
        subject_id: str | None = None,
    ) -> dict[str, Any]:
        self._require_owner(principal)
        parsed = self._scope(scope)
        definition = self._require_assignable(capability_id)
        self._validate_scope_capability(parsed, definition)
        with self._db._connection() as conn:
            value = self._resolve(
                conn,
                definition,
                invocation_id=invocation_id,
                subject_kind=subject_kind,
                subject_id=subject_id,
                excluded_key=parsed["assignment_key"],
            )
        return {
            "schema": "InferenceUseDefaultPreview@1",
            "clears": self._public_scope(parsed),
            "effective": value,
        }

    def clear_assignment(
        self, principal: Principal, body: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._require_owner(principal)
        allowed = {
            "command_id",
            "expected_revision",
            "scope",
            "capability_id",
            "invocation_id",
            "subject_kind",
            "subject_id",
        }
        if (
            not isinstance(body, Mapping)
            or set(body) - allowed
            or not {
                "command_id",
                "expected_revision",
                "scope",
                "capability_id",
            }.issubset(body)
        ):
            raise ValidationError(
                "Clear request has an invalid shape",
                code="inference_assignment_invalid",
            )
        parsed = self._scope(body["scope"])
        command_id = _safe_id(body["command_id"], field="command_id")
        expected = body["expected_revision"]
        if not isinstance(expected, int) or expected < 1:
            raise ValidationError(
                "expected_revision is invalid", code="inference_assignment_invalid"
            )
        capability = self._require_assignable(str(body["capability_id"]))
        self._validate_scope_capability(parsed, capability)
        capability_id = capability.id
        request = {
            "command": "clear",
            "scope": self._public_scope(parsed),
            "expected_revision": expected,
            "capability_id": capability_id,
            "invocation_id": body.get("invocation_id"),
            "subject_kind": body.get("subject_kind"),
            "subject_id": body.get("subject_id"),
        }
        request_hash = _sha256(request)
        receipt_context = {
            "action": "clear",
            "scope": self._public_scope(parsed),
            "expected_revision": expected,
            "capability_id": capability_id,
            "invocation_id": body.get("invocation_id"),
            "subject_kind": body.get("subject_kind"),
            "subject_id": body.get("subject_id"),
        }
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = self._replay(conn, command_id, request_hash, receipt_context)
                if replay is not None:
                    conn.commit()
                    return replay
                current = self._current(conn, parsed["assignment_key"])
                current_revision = 0 if current is None else int(current["revision"])
                if current_revision != expected:
                    raise ConflictError(
                        "Assignment changed. Refresh before clearing.",
                        code="inference_assignment_revision_conflict",
                        context={
                            "expected_revision": expected,
                            "current_revision": current_revision,
                        },
                    )
                revision = current_revision + 1
                assignment_id = str(current["assignment_id"])
                created_at = _now()
                tombstone = {
                    "schema": "InferenceAssignmentTombstone@1",
                    "id": assignment_id,
                    "scope": self._public_scope(parsed),
                    "revision": revision,
                    "created_at": created_at,
                }
                digest = _sha256(tombstone)
                conn.execute(
                    """INSERT INTO inference_assignment_revisions
                       (assignment_id,revision,assignment_key,scope_kind,scope_id,subject_kind,
                        selector_kind,capability_id,group_id,retry_policy_id,payload_json,sha256,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        assignment_id,
                        revision,
                        parsed["assignment_key"],
                        parsed["scope_kind"],
                        parsed.get("scope_id", ""),
                        parsed.get("subject_kind", ""),
                        parsed["selector_kind"],
                        parsed.get("capability_id", ""),
                        parsed.get("group_id", ""),
                        None,
                        _canonical(tombstone),
                        digest,
                        created_at,
                    ),
                )
                conn.execute(
                    """UPDATE inference_assignment_heads SET assignment_id=?,revision=?,cleared=1,updated_at=?
                       WHERE assignment_key=?""",
                    (assignment_id, revision, created_at, parsed["assignment_key"]),
                )
                effective = self._resolve(
                    conn,
                    self._registry.require(capability_id),
                    invocation_id=body.get("invocation_id"),
                    subject_kind=body.get("subject_kind"),
                    subject_id=body.get("subject_id"),
                )
                result = {
                    "schema": "InferenceAssignmentClearReceipt@1",
                    "cleared": self._public_scope(parsed),
                    "revision": revision,
                    "effective": effective,
                }
                result = self._command_receipt(
                    result,
                    committed_effect={**tombstone, "sha256": digest},
                    current=effective,
                )
                self._record_command(
                    conn,
                    command_id,
                    request_hash,
                    result,
                    context=receipt_context,
                )
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def resolve_effective(
        self,
        principal: Principal,
        *,
        capability_id: str,
        invocation_id: str | None = None,
        subject_kind: str | None = None,
        subject_id: str | None = None,
    ) -> dict[str, Any]:
        self._require_owner(principal)
        definition = self._require_assignable(capability_id)
        with self._db._connection() as conn:
            return self._resolve(
                conn,
                definition,
                invocation_id=invocation_id,
                subject_kind=subject_kind,
                subject_id=subject_id,
            )

    def starter_bundle_preview(
        self, principal: Principal, body: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Preview selected per-group chains; never infer or auto-apply one."""
        self._require_owner(principal)
        if not isinstance(body, Mapping) or set(body) != {"groups"}:
            raise ValidationError(
                "Starter preview has an invalid shape",
                code="inference_assignment_invalid",
            )
        with self._db._connection() as conn:
            return self._starter_preview_in_conn(conn, body["groups"])

    def apply_starter_bundle(
        self, principal: Principal, body: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Atomically apply an exact, hash-bound selected-group preview."""
        self._require_owner(principal)
        allowed = {"command_id", "preview_sha256", "groups"}
        if not isinstance(body, Mapping) or set(body) != allowed:
            raise ValidationError(
                "Starter apply has an invalid shape",
                code="inference_assignment_invalid",
            )
        command_id = _safe_id(body["command_id"], field="command_id")
        request_hash = _sha256({"command": "starter", **dict(body)})
        receipt_context = {
            "action": "starter",
            "groups": [
                {
                    "scope": {"kind": "group", "group_id": str(group["group_id"])},
                    "expected_revision": group["expected_revision"],
                }
                for group in body["groups"]
                if isinstance(group, Mapping)
                and "group_id" in group
                and "expected_revision" in group
            ],
        }
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = self._replay(conn, command_id, request_hash, receipt_context)
                if replay is not None:
                    conn.commit()
                    return replay
                preview = self._starter_preview_in_conn(conn, body["groups"])
                if str(body["preview_sha256"]) != preview["preview_sha256"]:
                    raise ConflictError(
                        "Starter preview changed. Preview the setup again.",
                        code="starter_bundle_preview_conflict",
                    )
                if any(
                    issue["severity"] == "blocking"
                    for group in preview["groups"]
                    for issue in group["issues"]
                ):
                    raise ValidationError(
                        "Starter bundle is incompatible",
                        code="inference_assignment_incompatible",
                    )
                applied: list[dict[str, Any]] = []
                for group in preview["groups"]:
                    scope = self._scope(
                        {"kind": "group", "group_id": group["group_id"]}
                    )
                    current = self._current(conn, scope["assignment_key"])
                    current_revision = (
                        0 if current is None else int(current["revision"])
                    )
                    if current_revision != group["expected_revision"]:
                        raise ConflictError(
                            "Starter assignment changed.",
                            code="inference_assignment_revision_conflict",
                        )
                    assignment_id = (
                        str(current["assignment_id"])
                        if current is not None
                        else "ia_" + uuid.uuid4().hex
                    )
                    revision, created_at = current_revision + 1, _now()
                    material = {
                        "schema": ASSIGNMENT_SCHEMA,
                        "id": assignment_id,
                        "scope": self._public_scope(scope),
                        "entries": group["entries"],
                        "retry_policy_id": group["retry_policy_id"],
                        "revision": revision,
                        "created_at": created_at,
                    }
                    digest = _sha256(material)
                    conn.execute(
                        """INSERT INTO inference_assignment_revisions
                        (assignment_id,revision,assignment_key,scope_kind,scope_id,subject_kind,selector_kind,capability_id,group_id,retry_policy_id,payload_json,sha256,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            assignment_id,
                            revision,
                            scope["assignment_key"],
                            "global",
                            "",
                            "",
                            "group",
                            "",
                            group["group_id"],
                            group["retry_policy_id"],
                            _canonical(material),
                            digest,
                            created_at,
                        ),
                    )
                    conn.execute(
                        """INSERT INTO inference_assignment_heads VALUES (?,?,?,?,?)
                           ON CONFLICT(assignment_key) DO UPDATE SET assignment_id=excluded.assignment_id,
                           revision=excluded.revision,cleared=0,updated_at=excluded.updated_at""",
                        (
                            scope["assignment_key"],
                            assignment_id,
                            revision,
                            0,
                            created_at,
                        ),
                    )
                    for entry in group["entries"]:
                        conn.execute(
                            "INSERT INTO inference_assignments VALUES (?,?,?,?,?,?,?)",
                            (
                                f"{assignment_id}:{revision}:{entry['ordinal']}",
                                assignment_id,
                                revision,
                                entry["profile_id"],
                                entry["profile_revision"],
                                entry["profile_schema_version"],
                                entry["ordinal"],
                            ),
                        )
                    stored_row = self._head(conn, scope["assignment_key"])
                    if stored_row is None:  # pragma: no cover - guarded by transaction
                        raise ConflictError(
                            "Starter assignment head was not durably created.",
                            code="inference_assignment_integrity_invalid",
                        )
                    applied.append(self._row_projection(conn, stored_row))
                result = {
                    "schema": "InferenceStarterBundleReceipt@1",
                    "assignments": applied,
                }
                result = self._command_receipt(
                    result,
                    committed_effect={
                        "schema": "InferenceStarterBundleCommittedEffect@1",
                        "assignments": [
                            self._assignment_effect(
                                self._assignment_material(
                                    conn,
                                    self._revision(
                                        conn,
                                        assignment["scope"],
                                        int(assignment["revision"]),
                                    ),
                                ),
                                str(assignment["sha256"]),
                            )
                            for assignment in applied
                        ],
                    },
                    current={"assignments": applied},
                )
                self._record_command(
                    conn,
                    command_id,
                    request_hash,
                    result,
                    context=receipt_context,
                )
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def _starter_preview_in_conn(self, conn: Any, value: Any) -> dict[str, Any]:
        if not isinstance(value, list) or not value:
            raise ValidationError(
                "Starter groups must be a non-empty array",
                code="inference_assignment_invalid",
            )
        groups: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in value:
            if not isinstance(raw, Mapping) or set(raw) != {
                "group_id",
                "expected_revision",
                "entries",
                "retry_policy_id",
            }:
                raise ValidationError(
                    "Starter group has an invalid shape",
                    code="inference_assignment_invalid",
                )
            group_id = _safe_id(raw["group_id"], field="group_id")
            if group_id in seen:
                raise ValidationError(
                    "Starter groups must be unique", code="inference_assignment_invalid"
                )
            seen.add(group_id)
            scope = self._scope({"kind": "group", "group_id": group_id})
            expected = raw["expected_revision"]
            if not isinstance(expected, int) or expected < 0:
                raise ValidationError(
                    "Starter expected_revision is invalid",
                    code="inference_assignment_invalid",
                )
            current = self._current(conn, scope["assignment_key"])
            current_revision = 0 if current is None else int(current["revision"])
            if current_revision != expected:
                raise ConflictError(
                    "Starter assignment changed.",
                    code="inference_assignment_revision_conflict",
                )
            entries = self._validate_entries(conn, raw["entries"], scope)
            capabilities = self._capabilities_for_group(group_id)
            policy = self._validate_policy(raw["retry_policy_id"], capabilities)
            groups.append(
                {
                    "group_id": group_id,
                    "expected_revision": expected,
                    "entries": entries,
                    "retry_policy_id": policy,
                    "issues": self._compatibility_issues(conn, entries, capabilities),
                }
            )
        material = {
            "schema": "InferenceStarterBundlePreview@1",
            "registry_sha256": self._registry.registry_sha256,
            "groups": groups,
        }
        return {
            **material,
            "preview_sha256": _sha256(material),
            "explicit_apply_required": True,
        }

    def migration_marker(
        self, principal: Principal, *, family: str
    ) -> dict[str, Any] | None:
        self._require_owner(principal)
        clean = _safe_id(family, field="family")
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM inference_assignment_migrations WHERE family=?", (clean,)
            ).fetchone()
        if row is None:
            return None
        result = json.loads(str(row["result_json"]))
        if str(row["result_sha256"]) != _sha256(result):
            raise ConflictError(
                "Stored migration marker integrity could not be verified.",
                code="inference_assignment_migration_integrity_invalid",
            )
        return {
            "schema": "InferenceAssignmentMigrationMarker@1",
            "family": clean,
            "marker_revision": int(row["marker_revision"]),
            "source_sha256": str(row["source_sha256"]),
            "result": result,
            "committed_at": str(row["committed_at"]),
        }

    def migrate_capability_assignments_atomically(
        self,
        principal: Principal,
        *,
        family: str,
        source_sha256: str,
        capability_entries: Mapping[str, Mapping[str, Any]],
        _prelude: Callable[[Any], None] | None = None,
    ) -> dict[str, Any]:
        """Install missing capability defaults and the cutover marker together.

        Any already-effective compatible owner assignment wins, including a
        group or global assignment.  A crash can therefore expose neither a
        partial migrated family nor assignments lacking their family marker.
        """
        self._require_owner(principal)
        clean_family = _safe_id(family, field="family")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(source_sha256)):
            raise ValidationError(
                "Migration source hash is invalid", code="inference_assignment_invalid"
            )
        if not capability_entries:
            raise ValidationError(
                "Migration assignments are empty", code="inference_assignment_invalid"
            )
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                existing = conn.execute(
                    "SELECT * FROM inference_assignment_migrations WHERE family=?",
                    (clean_family,),
                ).fetchone()
                if existing is not None:
                    stored = json.loads(str(existing["result_json"]))
                    if str(existing["result_sha256"]) != _sha256(stored):
                        raise ConflictError(
                            "Stored migration marker integrity could not be verified.",
                            code="inference_assignment_migration_integrity_invalid",
                        )
                    conn.commit()
                    return {**stored, "committed_at": str(existing["committed_at"])}

                if _prelude is not None:
                    _prelude(conn)
                proofs: dict[str, dict[str, Any]] = {}
                for capability_id, raw_entry in sorted(capability_entries.items()):
                    capability = self._require_assignable(capability_id)
                    resolved = self._resolve(conn, capability)
                    if resolved["status"] == "assigned":
                        projection = resolved["assignment"]
                        assignment_key = self._scope(projection["scope"])["assignment_key"]
                    elif resolved["status"] == "no_compatible_assignment":
                        raise ValidationError(
                            "Existing owner assignment is incompatible with migration.",
                            code="inference_assignment_incompatible",
                            context={"capability_id": capability_id},
                        )
                    else:
                        scope = self._scope(
                            {"kind": "capability", "capability_id": capability_id}
                        )
                        entries = self._validate_entries(conn, [raw_entry], scope)
                        issues = self._compatibility_issues(conn, entries, (capability,))
                        blockers = self._save_blockers(scope, entries, (capability,), issues)
                        if blockers:
                            raise ValidationError(
                                "Migration model is incompatible.",
                                code="inference_assignment_incompatible",
                                context={"issues": blockers},
                            )
                        assignment_id = "ia_" + uuid.uuid4().hex
                        created_at = _now()
                        material = {
                            "schema": ASSIGNMENT_SCHEMA,
                            "id": assignment_id,
                            "scope": self._public_scope(scope),
                            "entries": entries,
                            "retry_policy_id": None,
                            "revision": 1,
                            "created_at": created_at,
                        }
                        digest = _sha256(material)
                        conn.execute(
                            """INSERT INTO inference_assignment_revisions
                               (assignment_id,revision,assignment_key,scope_kind,scope_id,
                                subject_kind,selector_kind,capability_id,group_id,retry_policy_id,
                                payload_json,sha256,created_at)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (
                                assignment_id, 1, scope["assignment_key"], "global", "", "",
                                "capability", capability_id, "", None,
                                _canonical(material), digest, created_at,
                            ),
                        )
                        conn.execute(
                            "INSERT INTO inference_assignment_heads VALUES (?,?,?,?,?)",
                            (scope["assignment_key"], assignment_id, 1, 0, created_at),
                        )
                        for entry in entries:
                            conn.execute(
                                "INSERT INTO inference_assignments VALUES (?,?,?,?,?,?,?)",
                                (
                                    f"{assignment_id}:1:{entry['ordinal']}", assignment_id, 1,
                                    entry["profile_id"], entry["profile_revision"],
                                    entry["profile_schema_version"], entry["ordinal"],
                                ),
                            )
                        row = self._head(conn, scope["assignment_key"])
                        if row is None:  # pragma: no cover - transaction invariant
                            raise ConflictError(
                                "Migration assignment was not stored.",
                                code="inference_assignment_migration_incomplete",
                            )
                        projection = self._row_projection(conn, row, capability=capability)
                        assignment_key = scope["assignment_key"]
                    proofs[assignment_key] = {
                        "assignment_key": assignment_key,
                        "assignment_id": projection["id"],
                        "revision": projection["revision"],
                        "sha256": projection["sha256"],
                    }
                result = {
                    "schema": "InferenceAssignmentMigrationMarker@1",
                    "family": clean_family,
                    "marker_revision": 1,
                    "source_sha256": str(source_sha256),
                    "assignments": sorted(proofs.values(), key=lambda item: item["assignment_key"]),
                }
                committed_at = _now()
                conn.execute(
                    "INSERT INTO inference_assignment_migrations VALUES (?,?,?,?,?,?)",
                    (
                        clean_family, 1, source_sha256, _canonical(result),
                        _sha256(result), committed_at,
                    ),
                )
                conn.commit()
                return {**result, "committed_at": committed_at}
            except Exception:
                conn.rollback()
                raise

    def migrate_subject_assignments_atomically(
        self,
        principal: Principal,
        *,
        family: str,
        source_sha256: str,
        subject_entries: Iterable[Mapping[str, Any]],
        source_records: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Install exact subject assignments and their one-way marker together.

        Legacy record pointers are inputs to this transaction only.  Unlike the
        older capability-default helper, a record pointer must become its own
        exact subject/capability row even when a broader group or global row is
        already effective.  An existing exact subject row is owner truth and is
        never overwritten by migration.
        """
        self._require_owner(principal)
        clean_family = _safe_id(family, field="family")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(source_sha256)):
            raise ValidationError("Migration source hash is invalid", code="inference_assignment_invalid")
        rows = [dict(row) for row in subject_entries]
        records = [dict(row) for row in source_records]
        if any(set(row) != {"subject_kind", "subject_id", "capability_id", "entry"} for row in rows):
            raise ValidationError("Migration subject rows are invalid", code="inference_assignment_invalid")
        if any(set(row) != {"record_kind", "record_id", "field", "legacy_value", "legacy_read"} for row in records):
            raise ValidationError("Migration source records are invalid", code="inference_assignment_invalid")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                existing = conn.execute(
                    "SELECT * FROM inference_assignment_migrations WHERE family=?", (clean_family,)
                ).fetchone()
                if existing is not None:
                    stored = json.loads(str(existing["result_json"]))
                    if str(existing["result_sha256"]) != _sha256(stored):
                        raise ConflictError("Stored migration marker integrity could not be verified.", code="inference_assignment_migration_integrity_invalid")
                    conn.commit()
                    return {**stored, "committed_at": str(existing["committed_at"])}

                proofs: dict[str, dict[str, Any]] = {}
                for raw in sorted(rows, key=lambda item: (str(item["subject_kind"]), str(item["subject_id"]), str(item["capability_id"]))):
                    scope = self._scope({
                        "kind": "subject", "subject_kind": raw["subject_kind"],
                        "subject_id": raw["subject_id"], "capability_id": raw["capability_id"],
                    })
                    capability = self._require_assignable(scope["capability_id"])
                    current = self._current(conn, scope["assignment_key"])
                    if current is not None:
                        projection = self._row_projection(conn, current, capability=capability)
                    else:
                        entries = self._validate_entries(conn, [raw["entry"]], scope)
                        issues = self._compatibility_issues(conn, entries, (capability,))
                        blockers = self._save_blockers(scope, entries, (capability,), issues)
                        if blockers:
                            raise ValidationError("Migration model is incompatible.", code="inference_assignment_incompatible", context={"issues": blockers})
                        assignment_id, created_at = "ia_" + uuid.uuid4().hex, _now()
                        material = {
                            "schema": ASSIGNMENT_SCHEMA, "id": assignment_id,
                            "scope": self._public_scope(scope), "entries": entries,
                            "retry_policy_id": None, "revision": 1, "created_at": created_at,
                        }
                        digest = _sha256(material)
                        conn.execute(
                            """INSERT INTO inference_assignment_revisions
                               (assignment_id,revision,assignment_key,scope_kind,scope_id,subject_kind,
                                selector_kind,capability_id,group_id,retry_policy_id,payload_json,sha256,created_at)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (assignment_id, 1, scope["assignment_key"], "subject", scope["scope_id"],
                             scope["subject_kind"], "capability", capability.id, "", None,
                             _canonical(material), digest, created_at),
                        )
                        conn.execute("INSERT INTO inference_assignment_heads VALUES (?,?,?,?,?)", (scope["assignment_key"], assignment_id, 1, 0, created_at))
                        for entry in entries:
                            conn.execute("INSERT INTO inference_assignments VALUES (?,?,?,?,?,?,?)", (
                                f"{assignment_id}:1:{entry['ordinal']}", assignment_id, 1,
                                entry["profile_id"], entry["profile_revision"], entry["profile_schema_version"], entry["ordinal"],
                            ))
                        stored = self._head(conn, scope["assignment_key"])
                        if stored is None:  # pragma: no cover - transaction invariant
                            raise ConflictError("Migration assignment was not stored.", code="inference_assignment_migration_incomplete")
                        projection = self._row_projection(conn, stored, capability=capability)
                    proofs[scope["assignment_key"]] = {
                        "assignment_key": scope["assignment_key"], "assignment_id": projection["id"],
                        "revision": projection["revision"], "sha256": projection["sha256"],
                    }
                normalized_records = sorted(records, key=lambda item: (str(item["record_kind"]), str(item["record_id"]), str(item["field"])))
                result = {
                    "schema": "InferenceAssignmentMigrationMarker@1", "family": clean_family,
                    "marker_revision": 1, "source_sha256": str(source_sha256),
                    "assignments": sorted(proofs.values(), key=lambda item: item["assignment_key"]),
                    "source_records": normalized_records,
                }
                committed_at = _now()
                conn.execute("INSERT INTO inference_assignment_migrations VALUES (?,?,?,?,?,?)", (
                    clean_family, 1, source_sha256, _canonical(result), _sha256(result), committed_at,
                ))
                conn.commit()
                return {**result, "committed_at": committed_at}
            except Exception:
                conn.rollback()
                raise

    def commit_migration_marker(
        self, principal: Principal, body: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Commit a one-way family cutover marker after its adapter succeeds.

        Story 04 supplies the marker authority; adopter stories own reading a
        specific legacy Config family, writing its exact assignments, and only
        then committing this marker in their transaction.  Once committed, a
        family must never dual-read its legacy pointer again.
        """
        self._require_owner(principal)
        if not isinstance(body, Mapping) or set(body) != {
            "family",
            "marker_revision",
            "source_sha256",
            "assignments",
        }:
            raise ValidationError(
                "Migration marker has an invalid shape",
                code="inference_assignment_invalid",
            )
        family = _safe_id(body["family"], field="family")
        marker_revision = body["marker_revision"]
        source_sha256 = str(body["source_sha256"] or "")
        proofs = body["assignments"]
        if (
            not isinstance(marker_revision, int)
            or marker_revision < 1
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", source_sha256)
        ):
            raise ValidationError(
                "Migration marker revision/hash is invalid",
                code="inference_assignment_invalid",
            )
        if (
            not isinstance(proofs, list)
            or not proofs
            or any(
                not isinstance(proof, Mapping)
                or set(proof)
                != {"assignment_key", "assignment_id", "revision", "sha256"}
                for proof in proofs
            )
        ):
            raise ValidationError(
                "Migration assignment keys are invalid",
                code="inference_assignment_invalid",
            )
        for proof in proofs:
            _safe_id(proof["assignment_key"], field="assignment_key")
            _safe_id(proof["assignment_id"], field="assignment_id")
            if (
                not isinstance(proof["revision"], int)
                or proof["revision"] < 1
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(proof["sha256"]))
            ):
                raise ValidationError(
                    "Migration assignment proof is invalid",
                    code="inference_assignment_invalid",
                )
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                existing = conn.execute(
                    "SELECT * FROM inference_assignment_migrations WHERE family=?",
                    (family,),
                ).fetchone()
                result = {
                    "schema": "InferenceAssignmentMigrationMarker@1",
                    "family": family,
                    "marker_revision": marker_revision,
                    "source_sha256": source_sha256,
                    "assignments": sorted(
                        (dict(proof) for proof in proofs),
                        key=lambda item: item["assignment_key"],
                    ),
                }
                if existing is not None:
                    stored = json.loads(str(existing["result_json"]))
                    if str(existing["result_sha256"]) != _sha256(stored):
                        raise ConflictError(
                            "Stored migration marker integrity could not be verified.",
                            code="inference_assignment_migration_integrity_invalid",
                        )
                    if (
                        int(existing["marker_revision"]) != marker_revision
                        or str(existing["source_sha256"]) != source_sha256
                        or stored != result
                    ):
                        raise ConflictError(
                            "Migration family was already committed with different source truth.",
                            code="inference_assignment_migration_conflict",
                        )
                    for proof in stored["assignments"]:
                        proof_row = conn.execute(
                            """SELECT * FROM inference_assignment_revisions
                                WHERE assignment_key=? AND revision=?""",
                            (proof["assignment_key"], proof["revision"]),
                        ).fetchone()
                        if proof_row is None:
                            raise ConflictError(
                                "Migration assignment proof is missing.",
                                code="inference_assignment_migration_integrity_invalid",
                            )
                        proof_projection = self._row_projection(conn, proof_row)
                        if (
                            proof_projection["id"] != proof["assignment_id"]
                            or proof_projection["revision"] != proof["revision"]
                            or proof_projection["sha256"] != proof["sha256"]
                        ):
                            raise ConflictError(
                                "Migration assignment proof could not be verified.",
                                code="inference_assignment_migration_integrity_invalid",
                            )
                    conn.commit()
                    return {**stored, "committed_at": str(existing["committed_at"])}
                invalid: list[str] = []
                for proof in result["assignments"]:
                    row = self._head(conn, str(proof["assignment_key"]))
                    if row is None:
                        invalid.append(str(proof["assignment_key"]))
                        continue
                    projection = self._row_projection(conn, row)
                    if (
                        projection["id"] != proof["assignment_id"]
                        or projection["revision"] != proof["revision"]
                        or projection["sha256"] != proof["sha256"]
                    ):
                        invalid.append(str(proof["assignment_key"]))
                if invalid:
                    raise ConflictError(
                        "Migration assignments are not durably present.",
                        code="inference_assignment_migration_incomplete",
                        context={"invalid_assignment_keys": invalid},
                    )
                committed_at = _now()
                conn.execute(
                    "INSERT INTO inference_assignment_migrations VALUES (?,?,?,?,?,?)",
                    (
                        family,
                        marker_revision,
                        source_sha256,
                        _canonical(result),
                        _sha256(result),
                        committed_at,
                    ),
                )
                conn.commit()
                return {**result, "committed_at": committed_at}
            except Exception:
                conn.rollback()
                raise

    # ---- parsing, validation, and deterministic resolution -----------------

    def _set_request(self, body: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {
            "command_id",
            "expected_revision",
            "scope",
            "entries",
            "retry_policy_id",
        }
        if (
            not isinstance(body, Mapping)
            or set(body) - allowed
            or not {"command_id", "expected_revision", "scope", "entries"}.issubset(
                body
            )
        ):
            raise ValidationError(
                "Assignment request has an invalid shape",
                code="inference_assignment_invalid",
            )
        expected = body["expected_revision"]
        if not isinstance(expected, int) or expected < 0:
            raise ValidationError(
                "expected_revision is invalid", code="inference_assignment_invalid"
            )
        return {
            "command_id": _safe_id(body["command_id"], field="command_id"),
            "expected_revision": expected,
            "scope": self._scope(body["scope"]),
            "entries": body["entries"],
            "retry_policy_id": body.get("retry_policy_id"),
        }

    def _scope(self, value: Any) -> dict[str, str]:
        if not isinstance(value, Mapping) or "kind" not in value:
            raise ValidationError(
                "scope is invalid", code="inference_assignment_invalid"
            )
        kind = str(value["kind"] or "")
        if kind == "global" and set(value) == {"kind"}:
            return {
                "kind": kind,
                "scope_kind": "global",
                "selector_kind": "global",
                "assignment_key": "global",
            }
        if kind == "group" and set(value) == {"kind", "group_id"}:
            group_id = _safe_id(value["group_id"], field="group_id")
            if group_id not in self._group_ids():
                raise ValidationError(
                    "Unknown capability group",
                    code="unknown_inference_capability_group",
                )
            return {
                "kind": kind,
                "scope_kind": "global",
                "selector_kind": "group",
                "group_id": group_id,
                "assignment_key": f"group:{group_id}",
            }
        if kind == "capability" and set(value) == {"kind", "capability_id"}:
            capability_id = _safe_id(value["capability_id"], field="capability_id")
            self._require_assignable(capability_id)
            return {
                "kind": kind,
                "scope_kind": "global",
                "selector_kind": "capability",
                "capability_id": capability_id,
                "assignment_key": f"capability:{capability_id}",
            }
        if kind == "subject" and set(value) == {
            "kind",
            "subject_kind",
            "subject_id",
            "capability_id",
        }:
            subject_kind = str(value["subject_kind"] or "")
            if subject_kind not in _SUBJECT_KINDS:
                raise ValidationError(
                    "subject_kind is invalid", code="inference_assignment_invalid"
                )
            subject_id = _safe_id(value["subject_id"], field="subject_id")
            capability_id = _safe_id(value["capability_id"], field="capability_id")
            self._require_assignable(capability_id)
            return {
                "kind": kind,
                "scope_kind": "subject",
                "selector_kind": "capability",
                "scope_id": subject_id,
                "subject_kind": subject_kind,
                "capability_id": capability_id,
                "assignment_key": f"subject:{subject_kind}:{subject_id}:capability:{capability_id}",
            }
        if kind == "invocation" and set(value) == {
            "kind",
            "invocation_id",
            "capability_id",
        }:
            invocation_id = _safe_id(value["invocation_id"], field="invocation_id")
            capability_id = _safe_id(value["capability_id"], field="capability_id")
            self._require_assignable(capability_id)
            return {
                "kind": kind,
                "scope_kind": "invocation",
                "selector_kind": "capability",
                "scope_id": invocation_id,
                "capability_id": capability_id,
                "assignment_key": f"invocation:{invocation_id}:capability:{capability_id}",
            }
        raise ValidationError(
            "scope has an invalid shape", code="inference_assignment_invalid"
        )

    @staticmethod
    def _public_scope(scope: Mapping[str, str]) -> dict[str, str]:
        result = {"kind": scope["kind"]}
        if scope["kind"] == "group":
            result["group_id"] = scope["group_id"]
        elif scope["kind"] == "capability":
            result["capability_id"] = scope["capability_id"]
        elif scope["kind"] == "subject":
            result.update(
                subject_kind=scope["subject_kind"],
                subject_id=scope["scope_id"],
                capability_id=scope["capability_id"],
            )
        elif scope["kind"] == "invocation":
            result.update(
                invocation_id=scope["scope_id"], capability_id=scope["capability_id"]
            )
        return result

    def _validate_entries(
        self, conn: Any, value: Any, scope: Mapping[str, str]
    ) -> list[dict[str, Any]]:
        if not isinstance(value, list) or not 1 <= len(value) <= 4:
            raise ValidationError(
                "Assignment chain must contain one to four models",
                code="inference_assignment_chain_invalid",
            )
        result, seen = [], set()
        for ordinal, raw in enumerate(value, 1):
            if (
                not isinstance(raw, Mapping)
                or set(raw) - {"profile_id", "profile_revision"}
                or "profile_id" not in raw
            ):
                raise ValidationError(
                    "Assignment entry has an invalid shape",
                    code="inference_assignment_chain_invalid",
                )
            profile_id = str(raw["profile_id"] or "").strip()
            if not _PROFILE_ID.fullmatch(profile_id) or profile_id in seen:
                raise ValidationError(
                    "Assignment models must be unique stable profile IDs",
                    code="inference_assignment_chain_invalid",
                )
            seen.add(profile_id)
            revision = raw.get("profile_revision")
            legacy = profile_id.startswith("legacy-")
            if legacy:
                source_id = profile_id.removeprefix("legacy-")
                legacy_row = conn.execute(
                    "SELECT * FROM profiles WHERE id=? AND deleted=0", (source_id,)
                ).fetchone()
                if legacy_row is None or revision not in (None, 1):
                    raise ValidationError(
                        "Assignment names a missing legacy model",
                        code="inference_assignment_profile_missing",
                    )
                result.append(
                    {
                        "ordinal": ordinal,
                        "profile_id": profile_id,
                        "profile_revision": 1,
                        "profile_schema_version": 1,
                    }
                )
                continue
            if revision is None:
                row = conn.execute(
                    "SELECT MAX(revision) revision FROM model_profile_revisions WHERE profile_id=?",
                    (profile_id,),
                ).fetchone()
                revision = int(row["revision"] or 0) if row else 0
            if not isinstance(revision, int) or revision < 1:
                raise ValidationError(
                    "Assignment profile revision is invalid",
                    code="inference_assignment_chain_invalid",
                )
            profile_row = conn.execute(
                "SELECT * FROM model_profile_revisions WHERE profile_id=? AND revision=?",
                (profile_id, revision),
            ).fetchone()
            if profile_row is None:
                raise ValidationError(
                    "Assignment names a missing model revision",
                    code="inference_assignment_profile_missing",
                )
            self._profiles._revision_from_row(profile_row)
            binding = conn.execute(
                """SELECT b.* FROM model_profile_binding_heads h JOIN model_profile_binding_revisions b
                ON b.binding_id=h.binding_id AND b.revision=h.revision WHERE h.profile_id=? AND b.profile_revision=? AND b.enabled=1""",
                (profile_id, revision),
            ).fetchone()
            if binding is None:
                raise ValidationError(
                    "Assignment model has no enabled binding",
                    code="inference_assignment_binding_missing",
                )
            result.append(
                {
                    "ordinal": ordinal,
                    "profile_id": profile_id,
                    "profile_revision": revision,
                    "profile_schema_version": 2,
                }
            )
        return result

    def _affected_capabilities(
        self, scope: Mapping[str, str]
    ) -> tuple[InferenceCapabilityDefinition, ...]:
        if scope["kind"] in {"invocation", "subject", "capability"}:
            return (self._registry.require(scope["capability_id"]),)
        if scope["kind"] == "group":
            return self._capabilities_for_group(scope["group_id"])
        return tuple(
            c
            for c in self._registry._capabilities.values()
            if c.owner_visibility == "owner"
        )

    def _require_assignable(self, capability_id: str) -> InferenceCapabilityDefinition:
        definition = self._registry.require(capability_id)
        if definition.owner_visibility != "owner":
            raise ValidationError(
                "Capability is not owner-assignable.",
                code="inference_capability_not_assignable",
            )
        return definition

    @staticmethod
    def _validate_scope_capability(
        scope: Mapping[str, str], capability: InferenceCapabilityDefinition
    ) -> None:
        if (
            scope["selector_kind"] == "capability"
            and scope.get("capability_id") != capability.id
        ):
            raise ValidationError(
                "Preview capability must match the assignment scope.",
                code="inference_assignment_capability_mismatch",
            )
        if (
            scope["selector_kind"] == "group"
            and scope.get("group_id") != capability.group_id
        ):
            raise ValidationError(
                "Preview capability is not a member of the assignment group.",
                code="inference_assignment_capability_mismatch",
            )

    def _capabilities_for_group(
        self, group_id: str
    ) -> tuple[InferenceCapabilityDefinition, ...]:
        rows = tuple(
            c
            for c in self._registry._capabilities.values()
            if c.group_id == group_id and c.owner_visibility == "owner"
        )
        if not rows:
            raise ValidationError(
                "Unknown capability group", code="unknown_inference_capability_group"
            )
        return rows

    def _group_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    c.group_id
                    for c in self._registry._capabilities.values()
                    if c.owner_visibility == "owner"
                }
            )
        )

    def _validate_policy(
        self, value: Any, capabilities: Iterable[InferenceCapabilityDefinition]
    ) -> str | None:
        if value is None:
            return None
        policy_id = _safe_id(value, field="retry_policy_id")
        self._registry.retry_policy(policy_id)
        incompatible = [
            cap.id
            for cap in capabilities
            if policy_id not in cap.permitted_retry_policy_ids
        ]
        if incompatible:
            raise ValidationError(
                "Retry policy is not permitted by every affected capability",
                code="inference_assignment_policy_incompatible",
                context={"capability_ids": incompatible},
            )
        return policy_id

    @staticmethod
    def _save_blockers(
        scope: Mapping[str, str],
        entries: list[dict[str, Any]],
        capabilities: Iterable[InferenceCapabilityDefinition],
        issues: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        blocking = [issue for issue in issues if issue["severity"] == "blocking"]
        if scope["selector_kind"] == "capability":
            return blocking
        capability_count = len(tuple(capabilities))
        fully_incompatible: list[dict[str, Any]] = [
            issue for issue in blocking if not issue.get("capability_id")
        ]
        for entry in entries:
            entry_issues = {
                str(issue.get("capability_id"))
                for issue in blocking
                if issue.get("profile_id") == entry["profile_id"]
                and issue.get("capability_id")
            }
            if len(entry_issues) >= capability_count:
                fully_incompatible.extend(
                    issue
                    for issue in blocking
                    if issue.get("profile_id") == entry["profile_id"]
                )
        return fully_incompatible

    def _compatibility_issues(
        self,
        conn: Any,
        entries: list[dict[str, Any]],
        capabilities: Iterable[InferenceCapabilityDefinition],
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for entry in entries:
            if int(entry.get("profile_schema_version", 2)) == 1:
                source_id = str(entry["profile_id"]).removeprefix("legacy-")
                legacy = conn.execute(
                    "SELECT * FROM profiles WHERE id=? AND deleted=0", (source_id,)
                ).fetchone()
                if legacy is None:
                    issues.append(self._issue("profile_missing", entry, "blocking"))
                    continue
                legacy_profile = SimpleNamespace(**dict(legacy))
                deployment = resolve_v1_profile_execution(
                    legacy_profile, db=self._db
                ).deployment_revision
                boundary = _BOUNDARY_ALIASES.get(
                    str(deployment.boundary), str(deployment.boundary)
                )
                # Historical v1 declared language only.  Filenames/model names
                # are presentation, never governed audio or vision evidence.
                modalities = {"language"}
                for capability in capabilities:
                    reason = None
                    if capability.requires.structured_tools:
                        reason = "structured_tools_unsupported"
                    elif capability.requires.structured_output:
                        reason = "structured_output_unsupported"
                    elif capability.requires.audio and "audio" not in modalities:
                        reason = "audio_unsupported"
                    elif (
                        "text" in capability.input_modalities
                        and "language" not in modalities
                    ):
                        reason = "modality_unsupported"
                    elif (
                        int(legacy["context_limit"] or 0)
                        < capability.requires.minimum_context_tokens
                    ):
                        reason = "context_unsupported"
                    elif boundary not in capability.allowed_boundaries:
                        reason = "boundary_unsupported"
                    if reason:
                        issues.append(
                            {
                                **self._issue(reason, entry, "blocking"),
                                "capability_id": capability.id,
                            }
                        )
                issues.append(
                    self._issue("legacy_binding_readiness_unknown", entry, "repair")
                )
                continue
            row = conn.execute(
                "SELECT * FROM model_profile_revisions WHERE profile_id=? AND revision=?",
                (entry["profile_id"], entry["profile_revision"]),
            ).fetchone()
            profile = self._profiles._revision_from_row(row)
            binding = conn.execute(
                """SELECT b.* FROM model_profile_binding_heads h JOIN model_profile_binding_revisions b ON b.binding_id=h.binding_id AND b.revision=h.revision WHERE h.profile_id=?""",
                (profile.profile_id,),
            ).fetchone()
            if binding is None or int(binding["profile_revision"]) != int(
                entry["profile_revision"]
            ):
                issues.append(self._issue("binding_missing", entry, "blocking"))
                continue
            if not bool(binding["enabled"]):
                issues.append(self._issue("binding_disabled", entry, "repair"))
            dep_row = conn.execute(
                "SELECT * FROM deployment_revisions WHERE id=?",
                (binding["deployment_revision_id"],),
            ).fetchone()
            if dep_row is None:
                issues.append(self._issue("deployment_missing", entry, "blocking"))
                continue
            deployment = self._profiles._deployment_from_row(dep_row)
            claims = set(profile.capability_manifest.get("claims") or [])
            modalities = set(profile.supported_modalities)
            for capability in capabilities:
                reason = self._incompatibility(
                    profile, deployment, claims, modalities, capability
                )
                if reason:
                    issues.append(
                        {
                            **self._issue(reason, entry, "blocking"),
                            "capability_id": capability.id,
                        }
                    )
            observation = str(binding["readiness_observation_id"] or "")
            state = None
            if observation:
                observed = conn.execute(
                    "SELECT state,reason_code FROM model_profile_readiness_observations WHERE observation_id=?",
                    (observation,),
                ).fetchone()
                state = None if observed is None else str(observed["state"])
            if state != "ready":
                issues.append(self._issue("binding_not_ready", entry, "repair"))
        return issues

    @staticmethod
    def _issue(code: str, entry: Mapping[str, Any], severity: str) -> dict[str, Any]:
        return {
            "code": code,
            "severity": severity,
            "profile_id": entry["profile_id"],
            "profile_revision": entry["profile_revision"],
        }

    def _incompatibility(
        self,
        profile: Any,
        deployment: Any,
        claims: set[str],
        modalities: set[str],
        capability: InferenceCapabilityDefinition,
    ) -> str | None:
        required_modalities = set(capability.input_modalities)
        if "text" in required_modalities and not ({"text", "language"} & modalities):
            return "modality_unsupported"
        if "audio" in required_modalities and "audio" not in modalities:
            return "modality_unsupported"
        req = capability.requires
        typed_result_claims = {f"result_schema:{capability.output_schema_sha256}"}
        if req.structured_output and not (typed_result_claims & claims):
            return "structured_output_unsupported"
        if req.structured_tools:
            # Legacy manifests deliberately parse as palette-zero unavailable;
            # loading this release can never upgrade historic evidence.
            try:
                manifest, qualification = parse_capability_manifest(profile.capability_manifest)
            except ToolCapabilityError:
                return "tool_manifest_invalid"
            deployment_manifest = str(getattr(deployment, "capability_sha256", "") or "")
            if not deployment_manifest or manifest["sha256"] != deployment_manifest:
                return "tool_manifest_deployment_mismatch"
            foundation = self._tool_capability_foundation
            if not isinstance(foundation, ToolCapabilityFoundation):
                return "tool_capability_foundation_unavailable"
            if qualification.structured_tool_use != "qualified":
                return "structured_tools_unqualified"
            if not foundation.ready_for(
                palette=qualification.qualified_palette,
                dialect=qualification.native_tool_dialect,
            ):
                return "tool_capability_foundation_unavailable"
        if req.vision and "vision" not in claims:
            return "vision_unsupported"
        if req.audio and "audio" not in claims and "audio" not in modalities:
            return "audio_unsupported"
        if not set(req.capability_classes).issubset(claims):
            return "capability_class_unsupported"
        if (
            profile.context_support == "unavailable"
            or int(deployment.context_ceiling or 0) < req.minimum_context_tokens
        ):
            return "context_unsupported"
        boundary = _BOUNDARY_ALIASES.get(
            str(deployment.boundary), str(deployment.boundary)
        )
        if boundary not in capability.allowed_boundaries:
            return "boundary_unsupported"
        return None

    def _resolve(
        self,
        conn: Any,
        capability: InferenceCapabilityDefinition,
        *,
        invocation_id: Any = None,
        subject_kind: Any = None,
        subject_id: Any = None,
        excluded_key: str | None = None,
    ) -> dict[str, Any]:
        keys: list[tuple[str, str]] = []
        if invocation_id:
            keys.append(
                (
                    f"invocation:{_safe_id(invocation_id, field='invocation_id')}:capability:{capability.id}",
                    "invocation",
                )
            )
        if subject_kind or subject_id:
            if str(subject_kind) not in _SUBJECT_KINDS or not subject_id:
                raise ValidationError(
                    "subject is invalid", code="inference_assignment_invalid"
                )
            keys.append(
                (
                    f"subject:{subject_kind}:{_safe_id(subject_id, field='subject_id')}:capability:{capability.id}",
                    "subject",
                )
            )
        keys.extend(
            (
                (f"capability:{capability.id}", "capability"),
                (f"group:{capability.group_id}", "group"),
                ("global", "global"),
            )
        )
        for key, inherited_from in keys:
            if key == excluded_key:
                continue
            row = self._head(conn, key)
            if row is None:
                continue
            projection = self._row_projection(conn, row, capability=capability)
            blocking = [i for i in projection["issues"] if i["severity"] == "blocking"]
            return {
                "status": "no_compatible_assignment" if blocking else "assigned",
                "capability_id": capability.id,
                "inherited_from": inherited_from,
                "assignment": projection,
                "repair": "Choose model" if blocking else None,
            }
        return {
            "status": "no_assignment",
            "capability_id": capability.id,
            "inherited_from": None,
            "assignment": None,
            "repair": "Choose default",
        }

    @staticmethod
    def _head(conn: Any, key: str) -> Any:
        return conn.execute(
            """SELECT r.*, h.assignment_key AS head_key, h.assignment_id AS head_id,
                      h.revision AS head_revision, h.cleared AS head_cleared
                 FROM inference_assignment_heads h JOIN inference_assignment_revisions r
                   ON r.assignment_id=h.assignment_id AND r.revision=h.revision
                WHERE h.assignment_key=? AND h.cleared=0""",
            (key,),
        ).fetchone()

    @staticmethod
    def _current(conn: Any, key: str) -> Any:
        return conn.execute(
            """SELECT r.*, h.assignment_key AS head_key, h.assignment_id AS head_id,
                      h.revision AS head_revision, h.cleared AS head_cleared
                 FROM inference_assignment_heads h JOIN inference_assignment_revisions r
                   ON r.assignment_id=h.assignment_id AND r.revision=h.revision
                WHERE h.assignment_key=?""",
            (key,),
        ).fetchone()

    def _row_projection(
        self,
        conn: Any,
        row: Any,
        *,
        capability: InferenceCapabilityDefinition | None = None,
    ) -> dict[str, Any]:
        material = self._assignment_material(
            conn, row, require_active_head="head_key" in row.keys()
        )
        affected = (
            (capability,)
            if capability is not None
            else self._affected_capabilities(self._scope(material["scope"]))
        )
        issues = self._compatibility_issues(conn, material["entries"], affected)
        if (
            material["scope"]["kind"] in {"group", "global"}
            and material["retry_policy_id"] is not None
        ):
            invalid = [
                cap.id
                for cap in affected
                if material["retry_policy_id"] not in cap.permitted_retry_policy_ids
            ]
            if invalid:
                issues.append(
                    {
                        "code": "registry_policy_growth",
                        "severity": "blocking",
                        "capability_ids": invalid,
                    }
                )
        projection = self._projection_from_material(
            conn, material, str(row["sha256"]), issues=issues
        )
        if capability is not None:
            projection["effective_retry_policy_id"] = (
                material["retry_policy_id"] or capability.default_retry_policy_id
            )
            projection["retry_policy_source"] = (
                "assignment" if material["retry_policy_id"] else "capability_default"
            )
        elif len(affected) == 1:
            projection["effective_retry_policy_id"] = (
                material["retry_policy_id"] or affected[0].default_retry_policy_id
            )
            projection["retry_policy_source"] = (
                "assignment" if material["retry_policy_id"] else "capability_default"
            )
        else:
            projection["effective_retry_policy_id"] = material["retry_policy_id"]
            projection["retry_policy_source"] = (
                "assignment"
                if material["retry_policy_id"]
                else "per_capability_default"
            )
        return projection

    @staticmethod
    def _integrity_invalid(message: str) -> ConflictError:
        return ConflictError(
            message,
            code="inference_assignment_integrity_invalid",
        )

    def _assignment_material(
        self, conn: Any, row: Any, *, require_active_head: bool = False
    ) -> dict[str, Any]:
        """Decode one immutable row as a closed, normalized assignment value."""
        try:
            material = json.loads(str(row["payload_json"]))
            if not isinstance(material, dict) or set(material) != {
                "schema",
                "id",
                "scope",
                "entries",
                "retry_policy_id",
                "revision",
                "created_at",
            }:
                raise ValueError("root shape")
            if material["schema"] != ASSIGNMENT_SCHEMA:
                raise ValueError("schema")
            if type(material["revision"]) is not int or material["revision"] < 1:
                raise ValueError("revision")
            if not isinstance(material["id"], str) or not isinstance(
                material["created_at"], str
            ):
                raise ValueError("identity")
            if material["retry_policy_id"] is not None and not isinstance(
                material["retry_policy_id"], str
            ):
                raise ValueError("retry policy")
            entries = material["entries"]
            if not isinstance(entries, list) or not 1 <= len(entries) <= 4:
                raise ValueError("entries")
            for ordinal, entry in enumerate(entries, 1):
                if not isinstance(entry, dict) or set(entry) != {
                    "ordinal",
                    "profile_id",
                    "profile_revision",
                    "profile_schema_version",
                }:
                    raise ValueError("entry shape")
                if (
                    type(entry["ordinal"]) is not int
                    or entry["ordinal"] != ordinal
                    or not isinstance(entry["profile_id"], str)
                    or type(entry["profile_revision"]) is not int
                    or entry["profile_revision"] < 1
                    or type(entry["profile_schema_version"]) is not int
                    or entry["profile_schema_version"] not in (1, 2)
                ):
                    raise ValueError("entry value")
            parsed_scope = self._scope(material["scope"])
            if str(row["sha256"]) != _sha256(material):
                raise ValueError("hash")
            if (
                material["id"] != str(row["assignment_id"])
                or material["revision"] != int(row["revision"])
                or material["created_at"] != str(row["created_at"])
            ):
                raise ValueError("row identity")
            stored_discriminants = (
                str(row["assignment_key"]),
                str(row["scope_kind"]),
                str(row["scope_id"]),
                str(row["subject_kind"]),
                str(row["selector_kind"]),
                str(row["capability_id"]),
                str(row["group_id"]),
                row["retry_policy_id"],
            )
            expected_discriminants = (
                parsed_scope["assignment_key"],
                parsed_scope["scope_kind"],
                parsed_scope.get("scope_id", ""),
                parsed_scope.get("subject_kind", ""),
                parsed_scope["selector_kind"],
                parsed_scope.get("capability_id", ""),
                parsed_scope.get("group_id", ""),
                material["retry_policy_id"],
            )
            if stored_discriminants != expected_discriminants:
                raise ValueError("discriminants")
            if require_active_head:
                keys = set(row.keys())
                if not {"head_key", "head_id", "head_revision", "head_cleared"}.issubset(
                    keys
                ) or (
                    str(row["head_key"]) != str(row["assignment_key"])
                    or str(row["head_id"]) != str(row["assignment_id"])
                    or int(row["head_revision"]) != int(row["revision"])
                    or int(row["head_cleared"]) != 0
                ):
                    raise ValueError("head")
            normalized = [
                {
                    "ordinal": int(entry["ordinal"]),
                    "profile_id": str(entry["profile_id"]),
                    "profile_revision": int(entry["profile_revision"]),
                    "profile_schema_version": int(entry["profile_schema_version"]),
                }
                for entry in conn.execute(
                    """SELECT ordinal,profile_id,profile_revision,profile_schema_version
                         FROM inference_assignments
                        WHERE assignment_id=? AND assignment_revision=? ORDER BY ordinal""",
                    (material["id"], material["revision"]),
                ).fetchall()
            ]
            if normalized != entries:
                raise ValueError("normalized entries")
            return material
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ServiceError) as exc:
            if isinstance(exc, ConflictError) and exc.code == "inference_assignment_integrity_invalid":
                raise
            raise self._integrity_invalid(
                "Stored assignment material could not be verified."
            ) from exc

    def _tombstone_material(self, conn: Any, row: Any) -> dict[str, Any]:
        try:
            material = json.loads(str(row["payload_json"]))
            if not isinstance(material, dict) or set(material) != {
                "schema",
                "id",
                "scope",
                "revision",
                "created_at",
            }:
                raise ValueError("root shape")
            if (
                material["schema"] != "InferenceAssignmentTombstone@1"
                or type(material["revision"]) is not int
                or material["revision"] < 1
                or not isinstance(material["id"], str)
                or not isinstance(material["created_at"], str)
            ):
                raise ValueError("identity")
            parsed_scope = self._scope(material["scope"])
            expected = (
                parsed_scope["assignment_key"],
                parsed_scope["scope_kind"],
                parsed_scope.get("scope_id", ""),
                parsed_scope.get("subject_kind", ""),
                parsed_scope["selector_kind"],
                parsed_scope.get("capability_id", ""),
                parsed_scope.get("group_id", ""),
            )
            stored = tuple(
                str(row[name])
                for name in (
                    "assignment_key",
                    "scope_kind",
                    "scope_id",
                    "subject_kind",
                    "selector_kind",
                    "capability_id",
                    "group_id",
                )
            )
            count = conn.execute(
                """SELECT COUNT(*) FROM inference_assignments
                    WHERE assignment_id=? AND assignment_revision=?""",
                (row["assignment_id"], row["revision"]),
            ).fetchone()[0]
            if (
                expected != stored
                or material["id"] != str(row["assignment_id"])
                or material["revision"] != int(row["revision"])
                or material["created_at"] != str(row["created_at"])
                or row["retry_policy_id"] is not None
                or str(row["sha256"]) != _sha256(material)
                or int(count) != 0
            ):
                raise ValueError("row")
            return material
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ServiceError) as exc:
            raise self._integrity_invalid(
                "Stored assignment tombstone could not be verified."
            ) from exc

    def _revision(self, conn: Any, scope: Mapping[str, Any], revision: int) -> Any:
        parsed = self._scope(scope)
        row = conn.execute(
            """SELECT * FROM inference_assignment_revisions
                WHERE assignment_key=? AND revision=?""",
            (parsed["assignment_key"], revision),
        ).fetchone()
        if row is None:
            raise self._integrity_invalid("Committed assignment revision is missing.")
        return row

    @staticmethod
    def _assignment_effect(material: Mapping[str, Any], digest: str) -> dict[str, Any]:
        return {**json.loads(_canonical(material)), "sha256": digest}

    def _projection_from_material(
        self,
        conn: Any,
        material: Mapping[str, Any],
        digest: str,
        *,
        issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        entries = []
        for entry in material["entries"]:
            if int(entry.get("profile_schema_version", 2)) == 1:
                row = conn.execute(
                    "SELECT * FROM profiles WHERE id=?",
                    (str(entry["profile_id"]).removeprefix("legacy-"),),
                ).fetchone()
                if row is None:
                    label = "Missing model"
                else:
                    adapted = adapt_v1_profile(SimpleNamespace(**dict(row)))
                    label = str(adapted["profile"]["label"])
            else:
                row = conn.execute(
                    "SELECT label FROM model_profile_revisions WHERE profile_id=? AND revision=?",
                    (entry["profile_id"], entry["profile_revision"]),
                ).fetchone()
                label = str(row["label"]) if row else "Missing model"
            entries.append({**entry, "label": label})
            entries[-1].update(self._entry_runtime_projection(conn, entry))
        return {
            "schema": PROJECTION_SCHEMA,
            "id": material["id"],
            "revision": material["revision"],
            "sha256": digest,
            "scope": material["scope"],
            "entries": entries,
            "retry_policy_id": material["retry_policy_id"],
            "issues": issues,
            "created_at": material["created_at"],
        }

    def _entry_runtime_projection(
        self, conn: Any, entry: Mapping[str, Any]
    ) -> dict[str, Any]:
        if int(entry.get("profile_schema_version", 2)) == 1:
            row = conn.execute(
                "SELECT * FROM profiles WHERE id=? AND deleted=0",
                (str(entry["profile_id"]).removeprefix("legacy-"),),
            ).fetchone()
            if row is None:
                return {"boundary": "unknown", "readiness": "missing"}
            deployment = resolve_v1_profile_execution(
                SimpleNamespace(**dict(row)), db=self._db
            ).deployment_revision
            return {
                "boundary": _BOUNDARY_ALIASES.get(str(deployment.boundary), "unknown"),
                "readiness": "unknown",
            }
        binding = conn.execute(
            """SELECT b.* FROM model_profile_binding_heads h
                 JOIN model_profile_binding_revisions b
                   ON b.binding_id=h.binding_id AND b.revision=h.revision
                WHERE h.profile_id=? AND b.profile_revision=?""",
            (entry["profile_id"], entry["profile_revision"]),
        ).fetchone()
        if binding is None:
            return {"boundary": "unknown", "readiness": "missing"}
        deployment = conn.execute(
            "SELECT boundary FROM deployment_revisions WHERE id=?",
            (binding["deployment_revision_id"],),
        ).fetchone()
        observation = conn.execute(
            "SELECT state FROM model_profile_readiness_observations WHERE observation_id=?",
            (binding["readiness_observation_id"],),
        ).fetchone()
        return {
            "boundary": (
                "unknown"
                if deployment is None
                else _BOUNDARY_ALIASES.get(str(deployment["boundary"]), "unknown")
            ),
            "readiness": "disabled"
            if not bool(binding["enabled"])
            else ("unknown" if observation is None else str(observation["state"])),
        }

    @staticmethod
    def _dedupe_issues(issues: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        by_value = {_canonical(issue): issue for issue in issues}
        return [by_value[key] for key in sorted(by_value)]

    @staticmethod
    def _command_receipt(
        effect: Mapping[str, Any], *, committed_effect: Mapping[str, Any], current: Any
    ) -> dict[str, Any]:
        public = json.loads(_canonical(effect))
        frozen = json.loads(_canonical(committed_effect))
        return {**public, "committed_effect": frozen, "current": current}

    def _replay(
        self,
        conn: Any,
        command_id: str,
        request_hash: str,
        expected_context: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM inference_assignment_commands WHERE command_id=?",
            (command_id,),
        ).fetchone()
        if row is None:
            return None
        if str(row["request_sha256"]) != request_hash:
            raise ConflictError(
                "Command ID was already used with a different request.",
                code="inference_assignment_command_conflict",
            )
        response_json = str(row["response_json"])
        try:
            stored = json.loads(response_json)
            context = json.loads(str(row["resolution_context_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError(
                "Stored command receipt could not be decoded.",
                code="inference_assignment_command_integrity_invalid",
            ) from exc
        if str(row["response_sha256"]) != _sha256(stored):
            raise ConflictError(
                "Stored command receipt integrity could not be verified.",
                code="inference_assignment_command_integrity_invalid",
            )
        if str(row["resolution_context_sha256"]) != _sha256(context):
            raise ConflictError(
                "Stored command resolution context could not be verified.",
                code="inference_assignment_command_integrity_invalid",
            )
        if context != json.loads(_canonical(expected_context)):
            raise ConflictError(
                "Stored command resolution context does not match the request.",
                code="inference_assignment_command_integrity_invalid",
            )
        effect = stored.get("committed_effect")
        if not isinstance(effect, dict):
            raise ConflictError(
                "Stored command effect is invalid.",
                code="inference_assignment_command_integrity_invalid",
            )
        action = str(context.get("action", ""))
        if action == "set":
            scope = self._scope(context["scope"])
            revision = int(context["expected_revision"]) + 1
            historical_row = self._revision(conn, context["scope"], revision)
            material = self._assignment_material(conn, historical_row)
            reconstructed = self._assignment_effect(
                material, str(historical_row["sha256"])
            )
            if effect != reconstructed:
                raise ConflictError(
                    "Stored command effect does not match the committed assignment.",
                    code="inference_assignment_command_integrity_invalid",
                )
            historical = self._row_projection(conn, historical_row)
            current_row = self._head(conn, scope["assignment_key"])
            current = (
                None if current_row is None else self._row_projection(conn, current_row)
            )
            return self._command_receipt(
                historical, committed_effect=reconstructed, current=current
            )
        if action == "clear":
            revision = int(context["expected_revision"]) + 1
            historical_row = self._revision(conn, context["scope"], revision)
            tombstone = self._tombstone_material(conn, historical_row)
            reconstructed = {**tombstone, "sha256": str(historical_row["sha256"])}
            if effect != reconstructed:
                raise ConflictError(
                    "Stored command effect does not match the committed tombstone.",
                    code="inference_assignment_command_integrity_invalid",
                )
            capability_id = str(context["capability_id"])
            current = self._resolve(
                conn,
                self._registry.require(capability_id),
                invocation_id=context.get("invocation_id"),
                subject_kind=context.get("subject_kind"),
                subject_id=context.get("subject_id"),
            )
            public = {
                "schema": "InferenceAssignmentClearReceipt@1",
                "cleared": context["scope"],
                "revision": revision,
                "effective": current,
            }
            return self._command_receipt(
                public, committed_effect=reconstructed, current=current
            )
        if action == "starter":
            historical, current, reconstructed_assignments = [], [], []
            for group in context["groups"]:
                scope_value = group["scope"]
                revision = int(group["expected_revision"]) + 1
                historical_row = self._revision(conn, scope_value, revision)
                material = self._assignment_material(conn, historical_row)
                reconstructed_assignments.append(
                    self._assignment_effect(material, str(historical_row["sha256"]))
                )
                historical.append(self._row_projection(conn, historical_row))
                scope = self._scope(scope_value)
                row_value = self._head(conn, scope["assignment_key"])
                current.append(
                    None if row_value is None else self._row_projection(conn, row_value)
                )
            reconstructed = {
                "schema": "InferenceStarterBundleCommittedEffect@1",
                "assignments": reconstructed_assignments,
            }
            if effect != reconstructed:
                raise ConflictError(
                    "Stored command effect does not match the committed starter assignments.",
                    code="inference_assignment_command_integrity_invalid",
                )
            return self._command_receipt(
                {
                    "schema": "InferenceStarterBundleReceipt@1",
                    "assignments": historical,
                },
                committed_effect=reconstructed,
                current={"assignments": current},
            )
        raise ConflictError(
            "Stored command action is invalid.",
            code="inference_assignment_command_integrity_invalid",
        )

    @staticmethod
    def _record_command(
        conn: Any,
        command_id: str,
        request_hash: str,
        response: Mapping[str, Any],
        *,
        context: Mapping[str, Any],
    ) -> None:
        response_value = json.loads(_canonical(response))
        conn.execute(
            """INSERT INTO inference_assignment_commands
               (command_id,request_sha256,response_json,response_sha256,resolution_context_json,
                resolution_context_sha256,created_at) VALUES (?,?,?,?,?,?,?)""",
            (
                command_id,
                request_hash,
                _canonical(response_value),
                _sha256(response_value),
                _canonical(context),
                _sha256(context),
                _now(),
            ),
        )


InferenceRoutingApplicationService = InferenceAssignmentService


__all__ = [
    "ASSIGNMENT_SCHEMA",
    "InferenceAssignmentService",
    "InferenceRoutingApplicationService",
]
