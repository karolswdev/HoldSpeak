"""Principal-aware synchronization boundary."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import json
import base64
import hashlib
from dataclasses import dataclass, replace
from typing import Any, Callable

from ..logging_config import get_logger
from ..db.refinement_thoughts import RefinementThoughtRepository
from ..principals import Principal
from ..principals import PrincipalKind
from .errors import ConflictError, ValidationError

log = get_logger("services.sync")

@dataclass(frozen=True)
class SyncKindSpec:
    """One authoritative declaration of a syncable kind's wire obligations."""

    kind: str
    bucket: str
    schema: str | None
    mergeable: bool = False
    pull_serializer: Callable[[dict[str, list[dict[str, Any]]]], list[dict[str, Any]]] | None = None
    merger: Callable[[Any, "SyncKindSpec", list[dict[str, Any]]], int] | None = None


# The Python/web contract. Add a kind here, then provide the declared schema and
# serializer/merger; all public taxonomy views below are derived from it.
SYNC_REGISTRY = (
    SyncKindSpec("meeting", "meetings", "meeting.schema.json"),
    SyncKindSpec("artifact", "artifacts", "artifact.schema.json"),
    SyncKindSpec("note", "notes", "note.schema.json", True),
    SyncKindSpec("refinement_thought", "refinement_thoughts", "refinement-thought.schema.json"),
    SyncKindSpec("kb", "kbs", "kb.schema.json", True),
    SyncKindSpec("recipe", "recipes", "recipe.schema.json", True),
    SyncKindSpec("chain", "chains", "chain.schema.json", True),
    SyncKindSpec("workflow", "workflows", "workflow.schema.json", True),
    SyncKindSpec("directory", "directories", "directory.schema.json", True),
    SyncKindSpec("directory_membership", "directory_memberships", "directory-membership.schema.json", True),
    SyncKindSpec("knowledge_membership", "knowledge_memberships", "knowledge-membership.schema.json"),
    SyncKindSpec("project", "projects", "project.schema.json"),
    SyncKindSpec("project_relationship", "project_relationships", "project-relationship.schema.json"),
    SyncKindSpec("profile", "profiles", "profile.schema.json", True),
    SyncKindSpec("model", "models", "model-manifest.schema.json", True),
    SyncKindSpec("workbench", "workbenches", "workbench.schema.json", True),
    SyncKindSpec("decision_record", "decision_records", "decision-record.schema.json"),
    SyncKindSpec("decision_record_source", "decision_record_sources", "decision-record-source.schema.json"),
    SyncKindSpec("decision_record_work", "decision_record_work", "decision-record-work.schema.json"),
    SyncKindSpec("decision_record_revision", "decision_record_revisions", "decision-record-revision.schema.json"),
    SyncKindSpec("deployment_revision", "deployment_revisions", "deployment-revision.schema.json"),
)
SYNC_KINDS = frozenset(spec.kind for spec in SYNC_REGISTRY)
_BUCKET_KIND = {spec.bucket: spec.kind for spec in SYNC_REGISTRY}
SYNC_BUCKETS = frozenset(_BUCKET_KIND)
SYNC_SCHEMAS = {spec.kind: spec.schema for spec in SYNC_REGISTRY}
SYNC_MERGER_KINDS = frozenset(spec.kind for spec in SYNC_REGISTRY if spec.mergeable)


def qualified_sync_kind(bucket: str, kind: str) -> bool:
    """Whether a record kind is valid for its specific change-set bucket."""
    return _BUCKET_KIND.get(bucket) == kind


# Repository-backed primitive mergers. The bucket and kind are derived from the
# registry above rather than separately named taxonomies.
_MERGEABLE: dict[str, tuple[str, str, dict[str, str]]] = {
    "notes": ("notes", "note_id", {"title": "title", "body_markdown": "body_markdown", "tags": "tags"}),
    "kbs": ("kbs", "kb_id", {"name": "name", "member_ids": "member_ids"}),
    "recipes": ("recipes", "recipe_id", {"name": "name", "avatar": "avatar", "role": "role", "system_prompt": "system_prompt", "user_template": "user_template", "tools": "tools", "kb_id": "kb_id", "profile_id": "profile_id", "manual_context": "manual_context", "use_zone_context": "use_zone_context"}),
    "profiles": ("profiles", "profile_id", {"name": "name", "kind": "kind", "model_file": "model_file", "base_url": "base_url", "model": "model", "node": "node", "context_limit": "context_limit", "requires_key": "requires_key"}),
    "chains": ("chains", "chain_id", {"name": "name", "steps": "steps"}),
    "workflows": ("workflows", "workflow_id", {"name": "name", "prompt": "prompt", "graph_json": "graph_json"}),
    "directories": ("directories", "directory_id", {"name": "name", "parent_id": "parent_id"}),
    "directory_memberships": ("directory_memberships", "primitive_id", {"directory_id": "directory_id"}),
    "models": ("model_manifests", "manifest_id", {"node": "node", "name": "name", "capabilities": "capabilities"}),
    "workbenches": ("workbenches", "workbench_id", {"name": "name", "recipe_id": "recipe_id", "profile_id": "profile_id", "resolver_profile_id": "resolver_profile_id", "schedule": "schedule", "schedule_enabled": "schedule_enabled", "item_order": "item_order"}),
}


class _EmptySyncRepo:
    """Compatibility view for older embedded/test hubs during additive rollout."""

    def list(self, **_: Any) -> list[Any]:
        return []


def _iso(value: Any) -> Any:
    """A timestamp → strict wire ISO-8601: seconds precision, always ``Z``.

    The iPad decodes the change-set with Foundation's ``.iso8601`` strategy,
    which rejects fractional seconds and timezone-less strings — one naive
    ``datetime.isoformat()`` on the wire fails the WHOLE pull decode on every
    Swift client (surfacing as a permanent "Offline · queued" pill).
    """
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        s = value.isoformat(timespec="seconds")
        if s.endswith("+00:00"):
            return s[:-6] + "Z"
        return s if s.endswith("Z") else s + "Z"
    raw = str(value).strip()
    if not raw:
        return raw
    try:
        from datetime import datetime, timezone
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except ValueError:
        return raw


def _records_valid(records: Any, *, bucket: str | None = None) -> bool:
    """Every record is a `synced<T>` with a well-formed `meta` (id + known kind)."""
    if not isinstance(records, list):
        return False
    for rec in records:
        if not isinstance(rec, dict):
            return False
        meta = rec.get("meta")
        if not isinstance(meta, dict):
            return False
        kind = meta.get("kind")
        if not meta.get("id") or kind not in SYNC_KINDS:
            return False
        if bucket is not None and not qualified_sync_kind(bucket, str(kind)):
            return False
    return True


def _artifact_value(artifact: Any) -> dict[str, Any]:
    """An `ArtifactSummary` → the Phase-0 `Artifact` contract dict."""
    return {
        "id": artifact.id,
        # Run-born artifacts store NULL; the wire keeps a plain string ("") so
        # every decoder (the iPad's non-optional meetingId included) is unmoved.
        "meeting_id": artifact.meeting_id or "",
        "artifact_type": artifact.artifact_type,
        "title": artifact.title,
        "body_markdown": artifact.body_markdown,
        "structured_json": artifact.structured_json,
        "confidence": artifact.confidence,
        "status": artifact.status,
        "plugin_id": artifact.plugin_id,
        "plugin_version": artifact.plugin_version,
        "sources": artifact.sources,
        # 'meeting' | 'run' (v6). Explicit on the wire so a decoder never has
        # to infer run-born from the empty meeting_id.
        "origin": artifact.origin,
    }


def _primitive_record(rec: Any, kind: str) -> dict[str, Any]:
    """A primitive dataclass → a `{meta, value}` sync record.

    A tombstone carries NO payload (`value` is null exactly when
    `meta.deleted`) — the contract rule Sync.swift documents and the
    ChangeSet schema enforces (HS-72-01 caught the hub emitting full values
    on tombstones, violating its own contract).
    """
    deleted = bool(rec.deleted)
    value = rec.to_dict()
    for key in ("created_at", "updated_at", "last_modified"):
        if value.get(key):
            value[key] = _iso(value[key])
    return {
        "meta": {
            "id": rec.id,
            "kind": kind,
            "last_modified": _iso(rec.last_modified),
            "deleted": deleted,
        },
        "value": None if deleted else value,
    }


def _deployment_revision_record(revision: Any) -> dict[str, Any]:
    return {
        "meta": {"id": revision.id, "kind": "deployment_revision", "last_modified": revision.id, "deleted": False},
        "value": revision.to_dict(),
    }


def _project_record(project: Any) -> dict[str, Any]:
    modified = _iso(project.updated_at)
    value = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "is_archived": bool(project.is_archived),
        "created_at": _iso(project.created_at),
        "updated_at": modified,
        "last_modified": modified,
        "deleted": False,
    }
    return {
        "meta": {"id": project.id, "kind": "project",
                 "last_modified": modified, "deleted": False},
        "value": value,
    }


def _parse_dt(value: Any) -> Any:
    """ISO-8601 string → naive datetime; tolerant of a trailing ``Z`` (UTC).

    Returned naive (tzinfo dropped) to match how every other meeting path stores
    timestamps (naive ``datetime.now()``); a stored mix of naive/aware stamps
    breaks ``MeetingState.duration`` (naive ``now`` minus an aware ``started_at``).
    """
    from datetime import datetime

    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo is not None else value
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    return parsed.replace(tzinfo=None) if parsed.tzinfo is not None else parsed


def meeting_state_from_sync_value(value: dict[str, Any]) -> Any:
    """A pushed meeting `value` (the `MeetingState.to_dict` wire shape) → a
    `MeetingState`, ready to hand to ``MeetingRepository.save_meeting``.

    The exact inverse of `MeetingState.to_dict`: started/ended timestamps,
    transcript segments, bookmarks and the latest intel snapshot all round-trip.
    """
    from ..meeting_session import (
        Bookmark,
        IntelSnapshot,
        MeetingState,
        TranscriptSegment,
    )

    segments = [
        TranscriptSegment(
            text=str(seg.get("text") or ""),
            speaker=str(seg.get("speaker") or ""),
            start_time=float(seg.get("start_time") or 0.0),
            end_time=float(seg.get("end_time") or 0.0),
            is_bookmarked=bool(seg.get("is_bookmarked")),
            speaker_id=seg.get("speaker_id"),
            device_id=seg.get("device_id"),
        )
        for seg in (value.get("segments") or [])
        if isinstance(seg, dict)
    ]
    bookmarks = []
    for bm in value.get("bookmarks") or []:
        if not isinstance(bm, dict):
            continue
        created = _parse_dt(bm.get("created_at"))
        kwargs: dict[str, Any] = {
            "timestamp": float(bm.get("timestamp") or 0.0),
            "label": str(bm.get("label") or ""),
        }
        if created is not None:
            kwargs["created_at"] = created
        bookmarks.append(Bookmark(**kwargs))

    intel = None
    raw_intel = value.get("intel")
    if isinstance(raw_intel, dict):
        intel = IntelSnapshot(
            timestamp=float(raw_intel.get("timestamp") or 0.0),
            topics=[str(t) for t in (raw_intel.get("topics") or [])],
            action_items=list(raw_intel.get("action_items") or []),
            summary=str(raw_intel.get("summary") or ""),
        )

    status_block = value.get("intel_status")
    if isinstance(status_block, dict):
        intel_status = str(status_block.get("state") or "disabled")
        intel_status_detail = status_block.get("detail")
        intel_requested_at = _parse_dt(status_block.get("requested_at"))
        intel_completed_at = _parse_dt(status_block.get("completed_at"))
    else:
        intel_status = "disabled"
        intel_status_detail = None
        intel_requested_at = None
        intel_completed_at = None

    started = _parse_dt(value.get("started_at"))
    if started is None:
        from datetime import datetime

        started = datetime.now()

    return MeetingState(
        id=str(value.get("id") or "").strip(),
        started_at=started,
        ended_at=_parse_dt(value.get("ended_at")),
        title=value.get("title"),
        tags=[str(t) for t in (value.get("tags") or [])],
        segments=segments,
        bookmarks=bookmarks,
        intel=intel,
        intel_status=intel_status,
        intel_status_detail=intel_status_detail,
        intel_requested_at=intel_requested_at,
        intel_completed_at=intel_completed_at,
        mic_label=str(value.get("mic_label") or "Me"),
        remote_label=str(value.get("remote_label") or "Remote"),
        web_url=value.get("web_url"),
        capture_status=str(value.get("capture_status") or (
            "finalized" if value.get("ended_at") else "recoverable"
        )),
        capture_failure=value.get("capture_failure"),
        capture_checkpoint_at=_parse_dt(value.get("capture_checkpoint_at")),
        capture_checkpoint_seconds=float(value.get("capture_checkpoint_seconds") or 0.0),
        provenance=str(value.get("provenance") or "native"),
        sync_modified_at=_parse_dt(value.get("sync_modified_at")),
    )


def _merge_meetings(db: Any, records: list[dict[str, Any]]) -> int:
    """Live-merge pushed meeting records (LWW on `last_modified`, tombstone-aware).

    Equal-clock divergent values keep local as the deterministic winner and save
    the incoming value in ``meeting_sync_conflicts`` for explicit recovery.
    """
    merged = 0
    for rec in records:
        meta = rec["meta"]
        rec_id = str(meta["id"]).strip()
        if not rec_id:
            continue
        incoming_lm = _parse_dt(meta.get("last_modified"))
        existing = db.meetings.get_meeting(rec_id)
        value = rec.get("value") or {}
        if existing is not None and incoming_lm is not None:
            local_lm = getattr(existing, "sync_modified_at", None) or existing.started_at
            if local_lm > incoming_lm:
                continue
            if local_lm == incoming_lm:
                incoming_compare = (
                    meeting_state_from_sync_value({**value, "id": rec_id}).to_dict()
                    if isinstance(value, dict) else {}
                )
                local_compare = existing.to_dict()
                # Computed presentation fields and the transport clock are not
                # authored content and cannot create a false conflict.
                for payload in (incoming_compare, local_compare):
                    payload.pop("duration", None)
                    payload.pop("formatted_duration", None)
                    payload.pop("sync_modified_at", None)
                if meta.get("deleted") or incoming_compare != local_compare:
                    db.meetings.record_sync_conflict(
                        rec_id,
                        local_value=existing.to_dict(),
                        incoming_value={"deleted": bool(meta.get("deleted")), **incoming_compare},
                    )
                continue
        if meta.get("deleted"):
            db.meetings.delete_meeting(rec_id)
            merged += 1
            continue
        if not isinstance(value, dict):
            continue
        state = meeting_state_from_sync_value({**value, "id": rec_id})
        state.sync_modified_at = incoming_lm
        if not state.id:
            continue
        try:
            db.meetings.save_meeting(state, sync_modified_at=incoming_lm)
        except TypeError as exc:
            # Compatibility with narrow repository fakes/adapters that predate
            # the optional clock keyword; the canonical repository accepts it.
            if "sync_modified_at" not in str(exc):
                raise
            db.meetings.save_meeting(state)
        merged += 1
    return merged


def _merge_artifacts(db: Any, records: list[dict[str, Any]]) -> int:
    """Live-merge pushed artifact records (LWW on `last_modified`, tombstone-aware).

    The LWW stamp for the stored copy is the artifact's `updated_at` ISO — the
    field ``pull`` emits as the artifact's `last_modified`.
    """
    merged = 0
    for rec in records:
        meta = rec["meta"]
        rec_id = str(meta["id"]).strip()
        if not rec_id:
            continue
        incoming_lm = _parse_dt(meta.get("last_modified"))
        existing = db.plugins.get_artifact(rec_id)
        if existing is not None and incoming_lm is not None:
            # The stored copy's LWW key is `updated_at` — the field `pull` emits.
            if existing.updated_at >= incoming_lm:
                continue
        if meta.get("deleted"):
            db.plugins.delete_artifact(rec_id)
            merged += 1
            continue
        value = rec.get("value") or {}
        if not isinstance(value, dict):
            continue
        # v6 (Phase 74): empty meeting_id = a run-born artifact (origin='run',
        # NULL anchor) — a first-class citizen now, not a skip.
        meeting_id = str(value.get("meeting_id") or "").strip()
        db.plugins.record_artifact(
            artifact_id=rec_id,
            meeting_id=meeting_id,
            artifact_type=str(value.get("artifact_type") or "plugin_output"),
            title=str(value.get("title") or "Artifact"),
            body_markdown=str(value.get("body_markdown") or ""),
            structured_json=value.get("structured_json") if isinstance(value.get("structured_json"), dict) else None,
            confidence=float(value.get("confidence") or 0.0),
            status=str(value.get("status") or "draft"),
            plugin_id=str(value.get("plugin_id") or "unknown"),
            plugin_version=str(value.get("plugin_version") or "unknown"),
            sources=value.get("sources") if isinstance(value.get("sources"), list) else None,
            # Preserve the wire LWW key (naive, to match the stored stamp format)
            # so it survives the round-trip and `pull` re-emits it.
            updated_at=incoming_lm.isoformat() if incoming_lm is not None else None,
        )
        merged += 1
    return merged


def _decision_record_root(row: Any) -> dict[str, Any]:
    """Serialize a record using ``updated_at`` as its LWW clock."""
    value = dict(row)
    value["deleted"] = bool(value.get("deleted"))
    for field in ("created_at", "updated_at"):
        value[field] = _iso(value.get(field))
    return {
        "meta": {
            "id": value["id"], "kind": "decision_record",
            "last_modified": value["updated_at"], "deleted": value["deleted"],
        },
        "value": None if value["deleted"] else value,
    }


def _decision_record_child(row: Any, kind: str) -> dict[str, Any]:
    value = dict(row)
    value["created_at"] = _iso(value.get("created_at"))
    return {
        "meta": {"id": value["id"], "kind": kind,
                 "last_modified": value["created_at"], "deleted": False},
        "value": value,
    }


def _merge_decision_records(db: Any, records: list[dict[str, Any]]) -> int:
    """LWW-merge record roots; a delete is a tombstone, never evidence erasure."""
    if not records:
        return 0
    merged = 0
    with db._connection() as conn:
        for rec in records:
            meta, value = rec["meta"], rec.get("value") or {}
            record_id = str(meta["id"] or "").strip()
            if not record_id:
                continue
            incoming = str(meta.get("last_modified") or "")
            existing = conn.execute(
                "SELECT updated_at FROM decision_records WHERE id = ?", (record_id,)
            ).fetchone()
            if existing is not None and incoming and str(existing["updated_at"]) >= incoming:
                continue
            if meta.get("deleted"):
                if existing is not None:
                    conn.execute(
                        "UPDATE decision_records SET deleted = 1, updated_at = ? WHERE id = ?",
                        (incoming or existing["updated_at"], record_id),
                    )
                    merged += 1
                continue
            if not isinstance(value, dict):
                continue
            fields = ("decision_text", "rationale", "alternatives", "owner", "review_date",
                      "lifecycle", "source_type", "source_id", "created_at", "updated_at")
            values = [value.get(field) for field in fields]
            conn.execute(
                f"""INSERT INTO decision_records (id, {', '.join(fields)}, deleted)
                    VALUES (?, {', '.join('?' for _ in fields)}, 0)
                    ON CONFLICT(id) DO UPDATE SET
                    {', '.join(f'{field} = excluded.{field}' for field in fields)}, deleted = 0""",
                [record_id, *values],
            )
            merged += 1
    return merged


def _merge_decision_record_children(db: Any, table: str, records: list[dict[str, Any]]) -> int:
    """Merge append-only record evidence rows after their record roots exist."""
    if not records:
        return 0
    columns = {
        "decision_record_sources": ("id", "record_id", "source_type", "source_ref", "created_at"),
        "decision_record_work": ("id", "record_id", "work_type", "work_ref", "created_at"),
        "decision_record_revisions": ("id", "record_id", "field_name", "old_value", "new_value", "created_at"),
    }[table]
    merged = 0
    with db._connection() as conn:
        for rec in records:
            value = rec.get("value") or {}
            if rec["meta"].get("deleted") or not isinstance(value, dict):
                continue
            values = [value.get(column) for column in columns]
            if not values[0] or not values[1]:
                continue
            if conn.execute("SELECT 1 FROM decision_records WHERE id = ?", (values[1],)).fetchone() is None:
                continue
            conn.execute(
                f"INSERT OR IGNORE INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                values,
            )
            merged += 1
    return merged


def _hub_model_name(_ctx: Any = None) -> str:
    """The model the DESKTOP would actually load, for its live manifest row.

    A paired device reads this row to answer "what does 'run it on your desktop'
    run", so it must equal what the delegated execution path loads — which is
    exactly the ``paired_device`` deployment identity
    (``configured_meeting_deployment``, itself resolved through the ONE meeting
    placement policy, HS-130-05).

    HS-132-09 retired this function as an independent describer. It used to read
    ``intel_provider`` alone: ``"cloud"`` answered the cloud model id even when an
    adopted destination or a missing key meant the run would land elsewhere, and
    anything else answered the local GGUF stem even when an adopted
    ``openAICompatible``/``meshNode`` destination had won the placement. Both
    mismatch directions advertised a model the desktop would never load. It is
    now one delegation plus the enabled gate, and it names NO destination other
    than the hub itself — Ask and Recipe read their own resolved destination's
    identity, never this row.

    The intel knobs live on ``Config.meeting``, not the top-level ``Config`` —
    reading them off the wrong level raised inside the ``except`` and the hub
    silently never advertised its own model (the HSM-16-08 latent bug; the
    guard test now exercises this body with a real ``Config``).
    """
    try:
        from ..config import Config
        from ..intel.providers import configured_meeting_deployment

        if not Config.load().meeting.intel_enabled:
            return ""
        return str(configured_meeting_deployment().model or "")
    except Exception:
        return ""


def _pull_from(bucket: str) -> Callable[[dict[str, list[dict[str, Any]]]], list[dict[str, Any]]]:
    return lambda pulled: pulled.get(bucket, [])


# Every pull bucket is selected through its declared registry serializer. The
# local collection phase may omit an optional repository, but it never changes
# the public envelope's bucket set.
SYNC_REGISTRY = tuple(
    replace(spec, pull_serializer=_pull_from(spec.bucket))
    for spec in SYNC_REGISTRY
)

def _merge_primitive_spec(db: Any, spec: SyncKindSpec, records: list[dict[str, Any]]) -> int:
    """Merge one registry-declared primitive bucket into its own repository."""
    if not records:
        return 0
    attr, id_kwarg, field_map = _MERGEABLE[spec.bucket]
    repo = getattr(db, attr)
    merged = 0
    for rec in records:
        meta = rec["meta"]
        value = rec.get("value") or {}
        rec_id = str(meta["id"])
        incoming_lm = str(meta.get("last_modified") or "")
        existing = repo.get(rec_id, include_deleted=True)
        if existing is not None and existing.last_modified and incoming_lm:
            if existing.last_modified >= incoming_lm:
                continue
        kwargs: dict[str, Any] = {
            id_kwarg: rec_id,
            "last_modified": incoming_lm or None,
            "deleted": bool(meta.get("deleted")),
        }
        if value.get("created_at"):
            kwargs["created_at"] = str(value["created_at"])
        # Distinguish "field present with null" (explicit inherit — must land
        # as null on the receiving side) from "field absent from payload" (no
        # opinion — preserve the receiving value).  HS-134-07.
        existing_dict = existing.to_dict() if existing is not None else {}
        for value_key, upsert_key in field_map.items():
            if value_key in value:
                kwargs[upsert_key] = value[value_key]
            elif value_key in existing_dict:
                kwargs[upsert_key] = existing_dict[value_key]
        prior_bound = None
        if spec.bucket == "workbenches" and existing is not None:
            prior_bound = (existing.schedule, existing.schedule_enabled, existing.recipe_id, existing.profile_id)
        if spec.bucket != "workbenches":
            repo.upsert(**kwargs)
        else:
            # The incoming configuration is not authority.  Persist it, advance
            # our local bound revision, revoke the old grant, and epoch-fence its
            # open parents under the same BEGIN IMMEDIATE.
            from .schedule_delegation import ScheduleDelegationService
            service = ScheduleDelegationService(db)
            with db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                if existing is not None:
                    kwargs["schedule_revision"] = existing.schedule_revision
                current = repo.upsert_in_transaction(conn, **kwargs)
                changed = prior_bound is not None and prior_bound != (
                    current.schedule, current.schedule_enabled, current.recipe_id, current.profile_id,
                )
                if changed:
                    conn.execute("UPDATE workbenches SET schedule_revision=schedule_revision+1 WHERE id=?", (rec_id,))
                    fenced = service.revoke_in_transaction(conn, rec_id, "synced_bound_terms_changed")
                else:
                    fenced = []
            service.complete_fenced(fenced)
        merged += 1
    return merged


def _thought_sync_record(db: Any, thought: dict[str, Any]) -> dict[str, Any]:
    note = db.notes.get(thought["working_note_id"], include_deleted=True)
    revisions = db.refinement_thoughts.revisions(thought["id"])
    lifecycle = db.refinement_thoughts.lifecycle(thought["id"])
    commands = db.refinement_thoughts.commands(thought["id"])
    deleted = thought["state"] == "tombstoned"
    meta = {"id": thought["id"], "kind": "refinement_thought", "last_modified": _iso(thought["updated_at"]),
            "deleted": deleted, "expected_aggregate_revision": max(0, int(thought["aggregate_revision"]) - 1),
            "next_aggregate_revision": int(thought["aggregate_revision"]), "lifecycle_revision": int(thought["lifecycle_revision"])}
    return {
        "meta": meta,
        "value": {
            "id": thought["id"], "create_request_id": thought["create_request_id"],
            "create_payload_sha256": thought["create_payload_sha256"],
            "raw_utf8_b64": thought["raw_utf8_b64"], "raw_sha256": thought["raw_sha256"],
            "source": {"kind": thought["raw_source_kind"], "ref": thought["raw_source_ref"]},
            "raw_captured_at": thought["raw_captured_at"], "state": thought["state"],
            "created_at": thought["created_at"], "attachment_revision": thought["attachment_revision"],
            "last_modified": _iso(thought["updated_at"]), "deleted": False,
            "working_revision": thought["working_revision"], "lifecycle_revision": thought["lifecycle_revision"],
            "aggregate_revision": thought["aggregate_revision"],
            "expected_aggregate_revision": max(0, int(thought["aggregate_revision"]) - 1),
            "next_aggregate_revision": thought["aggregate_revision"],
            "working_note": note.to_dict() if note else None,
            "revisions": revisions, "lifecycle": lifecycle, "commands": commands,
        },
    }


def _merge_refinement_thought_bundles(db: Any, records: list[dict[str, Any]],
                                      note_records: list[dict[str, Any]],
                                      membership_records: list[dict[str, Any]]) -> tuple[int, set[str], set[str]]:
    """Apply thought-owned Note changes through the aggregate-command ledger."""
    return _merge_refinement_thought_ledger_bundles(db, records, note_records, membership_records)


def _merge_refinement_thought_ledger_bundles(db: Any, records: list[dict[str, Any]],
                                             note_records: list[dict[str, Any]],
                                             membership_records: list[dict[str, Any]]) -> tuple[int, set[str], set[str]]:
    """The sole aggregate sync law: validate an immutable command suffix, then install it atomically."""
    from .refinement_thought_service import RefinementThoughtService

    service = RefinementThoughtService(db)
    principal = Principal(PrincipalKind.NODE, "paired-sync")
    note_by_id = {str(rec["meta"]["id"]): rec for rec in note_records}
    bundle_ids = {str(rec["meta"]["id"]) for rec in records}
    exact_terminal_memberships: set[str] = set()
    for rec in records:
        value = rec.get("value")
        if not isinstance(value, dict) or value.get("state") != "tombstoned" or not isinstance(value.get("working_note"), dict):
            continue
        thought_id = str((rec.get("meta") or {}).get("id") or value.get("id") or "")
        with db._connection() as conn:
            fence = conn.execute("SELECT terminal_fingerprint FROM refinement_thought_sync_tombstones WHERE thought_id=?", (thought_id,)).fetchone()
        if fence and str(fence["terminal_fingerprint"]) == _terminal_fingerprint(value):
            exact_terminal_memberships.add(f"note:{value['working_note']['id']}")
    for note_id in note_by_id:
        owned = db.refinement_thoughts.get_by_note(note_id)
        if owned and owned["id"] not in bundle_ids:
            raise ConflictError("thought-owned note sync requires its aggregate revision", code="thought_sync_revision_required")
    for member in membership_records:
        ref = str((member.get("meta") or {}).get("id") or "")
        if ref.startswith("note:"):
            if ref in exact_terminal_memberships:
                continue
            owned = db.refinement_thoughts.get_by_note(ref.split(":", 1)[1])
            if owned and owned["state"] == "tombstoned":
                raise ConflictError("tombstoned thought cannot be filed", code="thought_tombstoned")
            with db._connection() as conn:
                fenced = conn.execute("SELECT 1 FROM refinement_thought_sync_tombstones WHERE terminal_working_note_id=?", (ref.split(":", 1)[1],)).fetchone()
            if fenced:
                raise ConflictError("tombstoned thought cannot be filed", code="thought_tombstoned")
    merged, consumed_notes, consumed_memberships = 0, set(), set()
    for rec in records:
        meta, value = dict(rec.get("meta") or {}), rec.get("value")
        if not isinstance(value, dict):
            raise ValidationError("thought sync requires aggregate value", code="thought_sync_invalid")
        thought_id = str(meta.get("id") or value.get("id") or "")
        if not thought_id or thought_id != str(value.get("id") or ""):
            raise ValidationError("thought sync id is invalid", code="thought_sync_invalid")
        try:
            raw = base64.b64decode(str(value["raw_utf8_b64"]), validate=True)
        except Exception as exc:
            raise ValidationError("thought raw bytes are invalid", code="thought_raw_hash_mismatch") from exc
        if hashlib.sha256(raw).hexdigest() != str(value["raw_sha256"]):
            raise ValidationError("thought raw hash does not match payload", code="thought_raw_hash_mismatch")
        _validate_thought_ledger_bundle(value)
        incoming_aggregate = int(value["aggregate_revision"])
        local = db.refinement_thoughts.get(thought_id)
        if local is None:
            with db._connection() as conn:
                fence = conn.execute("SELECT aggregate_revision,terminal_fingerprint FROM refinement_thought_sync_tombstones WHERE thought_id=?", (thought_id,)).fetchone()
            if fence:
                if value["state"] == "tombstoned" and str(fence["terminal_fingerprint"]) == _terminal_fingerprint(value):
                    merged += 1
                    consumed_notes.add(str(value["working_note"]["id"])); consumed_memberships.add(f"note:{value['working_note']['id']}")
                    continue
                raise ConflictError("thought sync tombstone is terminal", code="thought_tombstoned")
            if value["state"] == "tombstoned":
                terminal = value["lifecycle"][-1]
                with db._connection() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    conn.execute("""INSERT INTO refinement_thought_sync_tombstones
                       (thought_id,expected_revision,aggregate_revision,lifecycle_revision,lifecycle_sha256,terminal_working_note_id,terminal_fingerprint,last_modified,tombstoned_at)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                       (thought_id,incoming_aggregate-1,incoming_aggregate,int(value["lifecycle_revision"]),str(terminal["entry_sha256"]),str(value["working_note"]["id"]),_terminal_fingerprint(value),str(meta.get("last_modified") or ""),str(meta.get("last_modified") or "")))
                merged += 1
                note_id = str(value["working_note"]["id"])
                consumed_notes.add(note_id)
                consumed_memberships.add(f"note:{note_id}")
                continue
            service.install_sync_bundle(principal, value=value, raw_utf8=raw)
            local = db.refinement_thoughts.get(thought_id)
        local_commands = db.refinement_thoughts.commands(thought_id)
        incoming_commands = list(value["commands"])
        common = min(len(local_commands), len(incoming_commands))
        for idx in range(common):
            if _command_identity(local_commands[idx]) != _command_identity(incoming_commands[idx]):
                raise ConflictError("thought aggregate history diverged", code="thought_aggregate_conflict")
        if int(local["aggregate_revision"]) > incoming_aggregate:
            raise ConflictError("thought sync is stale", code="thought_revision_conflict")
        if int(local["aggregate_revision"]) == incoming_aggregate:
            if _aggregate_fingerprint(db, local) != _incoming_fingerprint(value):
                raise ConflictError("thought aggregate diverged", code="thought_aggregate_conflict")
        else:
            service.apply_sync_bundle(principal, thought_id=thought_id, value=value)
        note_id = str(value["working_note"]["id"])
        consumed_notes.add(note_id)
        if value["state"] == "tombstoned":
            # A tombstone consumes/gates its qualified organization edge; live
            # filing remains independently LWW-convergent.
            consumed_memberships.add(f"note:{note_id}")
            terminal = value["lifecycle"][-1]
            with db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("""INSERT OR IGNORE INTO refinement_thought_sync_tombstones
                    (thought_id,expected_revision,aggregate_revision,lifecycle_revision,lifecycle_sha256,terminal_working_note_id,terminal_fingerprint,last_modified,tombstoned_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""", (thought_id,incoming_aggregate-1,incoming_aggregate,int(value["lifecycle_revision"]),str(terminal["entry_sha256"]),note_id,_terminal_fingerprint(value),str(meta.get("last_modified") or ""),str(meta.get("last_modified") or "")))
        merged += 1
    return merged, consumed_notes, consumed_memberships


def _command_identity(item: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(item.get(k) for k in ("aggregate_revision", "command_kind", "prior_working_revision", "next_working_revision", "prior_lifecycle_revision", "next_lifecycle_revision", "prior_attachment_revision", "next_attachment_revision", "canonical_sha256", "lifecycle_sha256", "accepted_at"))


def _validate_thought_ledger_bundle(value: dict[str, Any]) -> None:
    required = ("aggregate_revision", "lifecycle_revision", "working_revision", "attachment_revision", "commands", "lifecycle", "revisions", "working_note")
    if any(key not in value for key in required):
        raise ValidationError("thought sync bundle is missing cursors", code="thought_sync_revision_required")
    aggregate, lifecycle, working = int(value["aggregate_revision"]), int(value["lifecycle_revision"]), int(value["working_revision"])
    commands, lifecycles, revisions = list(value["commands"]), list(value["lifecycle"]), list(value["revisions"])
    if [int(x.get("aggregate_revision") or 0) for x in commands] != list(range(1, aggregate + 1)):
        raise ValidationError("thought aggregate command history is incomplete", code="thought_revision_history_invalid")
    if [int(x.get("lifecycle_revision") or 0) for x in lifecycles] != list(range(1, lifecycle + 1)):
        raise ValidationError("thought lifecycle history is incomplete", code="thought_revision_history_invalid")
    if [int(x.get("revision") or 0) for x in revisions] != list(range(1, working + 1)):
        raise ValidationError("thought revision history is incomplete", code="thought_revision_history_invalid")
    work_hash = {int(x["revision"]): str(x["content_sha256"]) for x in revisions}
    for item in revisions:
        if work_hash[int(item["revision"])] != RefinementThoughtRepository.content_hash(str(item.get("title") or ""),str(item.get("body_markdown") or ""),list(item.get("tags") or [])):
            raise ValidationError("thought revision hash does not match payload", code="thought_revision_hash_mismatch")
    final = revisions[-1]
    note = value["working_note"]
    if RefinementThoughtRepository.content_hash(str(note.get("title") or ""),str(note.get("body_markdown") or ""),list(note.get("tags") or [])) != str(final["content_sha256"]):
        raise ValidationError("working note does not equal its declared revision", code="thought_working_snapshot_invalid")
    life_hash: dict[int, str] = {}
    life_state: dict[int, str] = {}
    life_entry: dict[int, dict[str, Any]] = {}
    for entry in lifecycles:
        expected = RefinementThoughtRepository.lifecycle_hash(thought_id=str(value["id"]), lifecycle_revision=int(entry["lifecycle_revision"]),aggregate_revision=int(entry["aggregate_revision"]),prior_state=entry.get("prior_state"),state=str(entry["state"]),command=str(entry["command"]),occurred_at=str(entry["occurred_at"]))
        if str(entry.get("entry_sha256") or "") != expected:
            raise ValidationError("thought lifecycle encoding/hash is invalid", code="thought_lifecycle_hash_mismatch")
        revision = int(entry["lifecycle_revision"])
        life_hash[revision], life_state[revision], life_entry[revision] = expected, str(entry["state"]), entry
    prior_working = prior_lifecycle = prior_attachment = prior_aggregate = 0
    prior_state: str | None = None
    for command in commands:
        aggregate_revision = int(command["aggregate_revision"])
        next_working, next_lifecycle, next_attachment = (int(command["next_working_revision"]), int(command["next_lifecycle_revision"]), int(command["next_attachment_revision"]))
        if aggregate_revision != prior_aggregate + 1 or (int(command["prior_working_revision"]), int(command["prior_lifecycle_revision"]), int(command["prior_attachment_revision"])) != (prior_working, prior_lifecycle, prior_attachment):
            raise ValidationError("thought command cursor continuity is invalid", code="thought_revision_history_invalid")
        kind = str(command.get("command_kind") or "")
        lifecycle_changed = next_lifecycle == prior_lifecycle + 1
        entry = life_entry.get(next_lifecycle) if lifecycle_changed else None
        allowed = False
        if kind == "create":
            allowed = prior_aggregate == 0 and prior_state is None and (next_working, next_lifecycle, next_attachment) == (1, 1, 0) and entry is not None and entry.get("prior_state") is None and entry.get("state") == "working" and entry.get("command") == "create"
        elif kind == "replace_working":
            allowed = prior_state == "working" and (next_working, next_lifecycle, next_attachment) == (prior_working + 1, prior_lifecycle, prior_attachment) and entry is None
        elif kind == "complete":
            allowed = prior_state == "working" and (next_working, next_lifecycle, next_attachment) == (prior_working, prior_lifecycle + 1, prior_attachment) and entry is not None and entry.get("prior_state") == "working" and entry.get("state") == "completed" and entry.get("command") == "complete"
        elif kind == "resume":
            allowed = prior_state == "completed" and (next_working, next_lifecycle, next_attachment) == (prior_working, prior_lifecycle + 1, prior_attachment) and entry is not None and entry.get("prior_state") == "completed" and entry.get("state") == "working" and entry.get("command") == "resume"
        elif kind == "tombstone":
            allowed = prior_state in {"working", "completed"} and (next_working, next_lifecycle, next_attachment) == (prior_working, prior_lifecycle + 1, prior_attachment) and entry is not None and entry.get("prior_state") == prior_state and entry.get("state") == "tombstoned" and entry.get("command") == "tombstone"
        if not allowed or next_working not in work_hash:
            raise ValidationError("thought command transition is invalid", code="thought_revision_history_invalid")
        lifecycle_hash = life_hash[next_lifecycle] if lifecycle_changed else None
        if command.get("lifecycle_sha256") != lifecycle_hash:
            raise ValidationError("thought command lifecycle hash is invalid", code="thought_lifecycle_hash_mismatch")
        next_state = life_state[next_lifecycle] if lifecycle_changed else prior_state
        snapshot={"id":str(value["id"]),"raw_sha256":str(value["raw_sha256"]),"state":next_state,"working_revision":next_working,"lifecycle_revision":next_lifecycle,"attachment_revision":next_attachment,"aggregate_revision":aggregate_revision}
        expected=RefinementThoughtRepository.aggregate_hash(snapshot,working_sha256=work_hash[next_working],lifecycle_sha256=lifecycle_hash)
        if str(command.get("canonical_sha256") or "") != expected:
            raise ValidationError("thought aggregate command hash is invalid", code="thought_aggregate_conflict")
        prior_working, prior_lifecycle, prior_attachment, prior_aggregate, prior_state = next_working, next_lifecycle, next_attachment, aggregate_revision, str(next_state)
    if (prior_working, prior_lifecycle, prior_attachment, prior_aggregate, prior_state) != (working, lifecycle, int(value["attachment_revision"]), aggregate, str(value["state"])):
        raise ValidationError("thought final aggregate cursor/state is inconsistent", code="thought_revision_history_invalid")


def _aggregate_fingerprint(db: Any, thought: dict[str, Any]) -> tuple[Any, ...]:
    note = db.notes.get(thought["working_note_id"], include_deleted=True)
    return (thought["state"],thought["aggregate_revision"],thought["lifecycle_revision"],thought["working_revision"],thought["attachment_revision"],tuple(_command_identity(x) for x in db.refinement_thoughts.commands(thought["id"])),note.title if note else None,note.body_markdown if note else None,tuple(note.tags) if note else ())


def _incoming_fingerprint(value: dict[str, Any]) -> tuple[Any, ...]:
    note=value["working_note"]
    return (value["state"],value["aggregate_revision"],value["lifecycle_revision"],value["working_revision"],value["attachment_revision"],tuple(_command_identity(x) for x in value["commands"]),note.get("title"),note.get("body_markdown"),tuple(note.get("tags") or []))


def _terminal_fingerprint(value: dict[str, Any]) -> str:
    """Stable identity for the only tombstone replay that is idempotent."""
    material = {"aggregate": _incoming_fingerprint(value), "raw_sha256": value["raw_sha256"], "working_note_id": value["working_note"]["id"]}
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), default=list).encode("utf-8")).hexdigest()


SYNC_REGISTRY = tuple(
    replace(spec, merger=_merge_primitive_spec if spec.bucket in _MERGEABLE else None)
    for spec in SYNC_REGISTRY
)


@observe_service
class SyncService:
    def __init__(self, db: Any, *, hub_model_name: Any = _hub_model_name, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._hub_model_name = hub_model_name
        self._observer = observer or NullObserver()

    def pull(self, principal: Principal, *, limit: int = 50) -> dict[str, Any]:
        db = self._db
        bounded = max(1, min(int(limit), 500))
        meetings: list[dict[str, Any]] = []
        artifacts: list[dict[str, Any]] = []
        
        for summary in db.meetings.list_meetings(limit=bounded):
            state = db.meetings.get_meeting(summary.id)
            if state is None:
                continue
            meetings.append({
                "meta": {
                    "id": summary.id, "kind": "meeting",
                    "last_modified": _iso(
                        getattr(state, "sync_modified_at", None) or summary.started_at
                    ),
                    "deleted": False,
                },
                "value": state.to_dict(),
            })
            for art in db.plugins.list_artifacts(summary.id):
                artifacts.append({
                    "meta": {
                        "id": art.id, "kind": "artifact",
                        "last_modified": _iso(art.updated_at), "deleted": False,
                    },
                    "value": _artifact_value(art),
                })
        
        # v6 (Phase 74): the run-born lane — artifacts with no meeting anchor
        # (a persona/chain/workflow run's output; lineage is the anchor).
        for art in db.plugins.list_run_artifacts(limit=bounded):
            artifacts.append({
                "meta": {
                    "id": art.id, "kind": "artifact",
                    "last_modified": _iso(art.updated_at), "deleted": False,
                },
                "value": _artifact_value(art),
            })
        
        # The Primitive Framework desk primitives. `include_deleted=True` so
        # tombstones propagate to the other surfaces, just like a real sync.
        notes = [_primitive_record(n, "note")
                 for n in db.notes.list(include_deleted=True, limit=bounded)]
        refinement_thoughts = [
            _thought_sync_record(db, thought)
            for thought in getattr(db, "refinement_thoughts", _EmptySyncRepo()).list()
        ]
        kbs = [_primitive_record(k, "kb")
               for k in db.kbs.list(include_deleted=True, limit=bounded)]
        recipes = [_primitive_record(a, "recipe")
                   for a in db.recipes.list(include_deleted=True, limit=bounded)]
        chains = [_primitive_record(c, "chain")
                  for c in db.chains.list(include_deleted=True, limit=bounded)]
        workflows = [_primitive_record(w, "workflow")
                     for w in db.workflows.list(include_deleted=True, limit=bounded)]
        profiles = [_primitive_record(p, "profile")
                    for p in db.profiles.list(include_deleted=True, limit=bounded)]
        workbenches = [_primitive_record(w, "workbench")
                       for w in getattr(db, "workbenches", _EmptySyncRepo()).list(
                           include_deleted=True, limit=bounded
                       )]
        directories = [_primitive_record(d, "directory")
                       for d in db.directories.list(include_deleted=True, limit=bounded)]
        # Membership rides the wire too (organization, not layout). The record's
        # synced id is its `primitive_id` (the `id` property), the value carries
        # the `directory_id` edge.
        directory_memberships = [
            _primitive_record(m, "directory_membership")
            for m in db.directory_memberships.list(include_deleted=True, limit=bounded)
        ]
        knowledge_memberships = [
            _primitive_record(m, "knowledge_membership")
            for m in getattr(db, "knowledge_memberships", _EmptySyncRepo()).list(
                include_deleted=True, limit=bounded
            )
        ]
        project_relationships = [
            _primitive_record(m, "project_relationship")
            for m in getattr(db, "project_relationships", _EmptySyncRepo()).list(
                include_deleted=True, limit=bounded
            )
        ]
        projects = [
            _project_record(project)
            for project in db.projects.list_projects(include_archived=True)
        ] if hasattr(db, "projects") else []
        
        # Model MANIFESTS (HSM-16-08): every node's pushed rows, PLUS the hub's own
        # model as a live virtual row (computed from config, never stored) — so a
        # companion knows what "run it on your desktop" would actually run. The
        # binary never rides; a manifest is id/node/name/capabilities only.
        models = [_primitive_record(m, "model")
                  for m in db.model_manifests.list(include_deleted=True, limit=bounded)]
        hub_model = self._hub_model_name()
        if hub_model:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            models.append({
                "meta": {"id": "desktop:intel", "kind": "model",
                         "last_modified": now, "deleted": False},
                "value": {"id": "desktop:intel", "node": "desktop", "name": hub_model,
                          "capabilities": ["language"], "created_at": now,
                          "last_modified": now, "deleted": False},
            })
        
        # Record roots carry their own LWW clocks and tombstones; their
        # immutable evidence children follow as separate, idempotent buckets.
        record_rows: list[Any] = []
        child_rows: dict[str, list[Any]] = {
            "decision_record_sources": [], "decision_record_work": [],
            "decision_record_revisions": [],
        }
        if hasattr(db, "_connection"):
            with db._connection() as conn:
                record_rows = conn.execute(
                    "SELECT * FROM decision_records ORDER BY updated_at DESC, id DESC LIMIT ?", (bounded,)
                ).fetchall()
                record_ids = [row["id"] for row in record_rows]
                placeholders = ", ".join("?" for _ in record_ids)
                child_rows: dict[str, list[Any]] = {}
                for table in ("decision_record_sources", "decision_record_work", "decision_record_revisions"):
                    child_rows[table] = conn.execute(
                        f"SELECT * FROM {table} WHERE record_id IN ({placeholders})" if placeholders else f"SELECT * FROM {table} WHERE 0",
                        record_ids,
                    ).fetchall()
        decision_records = [_decision_record_root(row) for row in record_rows]
        decision_record_sources = [_decision_record_child(row, "decision_record_source") for row in child_rows["decision_record_sources"]]
        decision_record_work = [_decision_record_child(row, "decision_record_work") for row in child_rows["decision_record_work"]]
        decision_record_revisions = [_decision_record_child(row, "decision_record_revision") for row in child_rows["decision_record_revisions"]]
        deployment_revisions = [
            _deployment_revision_record(revision)
            for revision in getattr(db, "deployment_revisions", _EmptySyncRepo()).list(limit=bounded)
        ]

        pulled = {
            "meetings": meetings, "artifacts": artifacts, "notes": notes,
            "refinement_thoughts": refinement_thoughts,
            "kbs": kbs, "recipes": recipes, "chains": chains,
            "workflows": workflows, "profiles": profiles, "workbenches": workbenches,
            "directories": directories, "directory_memberships": directory_memberships,
            "knowledge_memberships": knowledge_memberships,
            "project_relationships": project_relationships, "projects": projects,
            "models": models, "decision_records": decision_records,
            "decision_record_sources": decision_record_sources,
            "decision_record_work": decision_record_work,
            "decision_record_revisions": decision_record_revisions,
            "deployment_revisions": deployment_revisions,
        }
        return {
            spec.bucket: spec.pull_serializer(pulled) if spec.pull_serializer else []
            for spec in SYNC_REGISTRY
        }

    def push(self, principal: Principal, payload: Any) -> dict[str, Any]:
        try:
            body = payload
        except Exception:
            raise ValidationError("invalid JSON", code="invalid_json")
        
        known_buckets = set(_BUCKET_KIND)
        if not isinstance(body, dict) or not (set(body) & known_buckets):
            raise ValidationError("expected a change_set with at least one of " + ", ".join(sorted(known_buckets)))
        
        # HSM-10-03 — validate the envelope: every record needs a well-formed sync
        # header (id + a known kind). Malformed → 422, never stored/merged.
        for bucket in known_buckets:
            if not _records_valid(body.get(bucket) or [], bucket=bucket):
                raise ValidationError(f"malformed sync record in {bucket} (need meta.id + meta.kind)")
        
        db = self._db
        received: dict[str, int] = {}
        
        # Meetings/artifacts: live-merge into their real tables (LWW on
        # last_modified, tombstone-aware) so a pushed meeting/artifact is
        # immediately queryable via the normal read paths, matching the desk
        # primitives. A copy of the pushed records is also kept in the durable
        # JSON inbox as a replayable audit trail.
        meeting_records = body.get("meetings") or []
        artifact_records = body.get("artifacts") or []
        if meeting_records or artifact_records:
            inbox = db.db_path.parent / "sync_inbox"
            inbox.mkdir(parents=True, exist_ok=True)
            idx = len(list(inbox.glob("inbox-*.json")))
            dest = inbox / f"inbox-{idx:06d}.json"
            dest.write_text(json.dumps(
                {"meetings": meeting_records, "artifacts": artifact_records}
            ), encoding="utf-8")
        # Meetings merge before artifacts so each artifact's meeting FK exists.
        received["meetings"] = _merge_meetings(db, meeting_records)
        received["artifacts"] = _merge_artifacts(db, artifact_records)
        log.info(
            "sync push merged: meetings=%s/%s artifacts=%s/%s",
            received["meetings"], len(meeting_records),
            received["artifacts"], len(artifact_records),
        )
        
        # Record roots merge before their append-only source/work/revision
        # evidence, allowing a complete record to arrive in one change set.
        record_records = body.get("decision_records") or []
        received["decision_records"] = _merge_decision_records(db, record_records)
        for table, bucket in (
            ("decision_record_sources", "decision_record_sources"),
            ("decision_record_work", "decision_record_work"),
            ("decision_record_revisions", "decision_record_revisions"),
        ):
            received[bucket] = _merge_decision_record_children(db, table, body.get(bucket) or [])

        project_records = body.get("projects") or []
        merged_projects = 0
        for rec in project_records:
            meta, value = rec["meta"], rec.get("value") or {}
            project_id = str(meta["id"])
            existing = db.projects.get_project(project_id)
            incoming = str(meta.get("last_modified") or "")
            if existing is not None and incoming:
                local_clock, incoming_clock = _iso(existing.updated_at), _iso(incoming)
                if local_clock == incoming_clock:
                    if (existing.name != str(value.get("name") or existing.name)
                            or existing.description != str(value.get("description") or existing.description)
                            or existing.is_archived != bool(meta.get("deleted") or value.get("is_archived"))):
                        raise ConflictError("project conflict at equal sync clock", context={"conflict": {"kind": "project", "id": project_id, "last_modified": incoming_clock}})
                    continue
                if local_clock > incoming_clock:
                    continue
            if existing is None and not meta.get("deleted"):
                db.projects.create_project(
                    project_id=project_id,
                    name=str(value.get("name") or project_id),
                    description=str(value.get("description") or ""),
                    # Preserve the incoming clock (the relationship buckets
                    # already do): a destination that restamps arrival time
                    # can never detect an equal-clock conflict again.
                    updated_at=incoming or None,
                )
            elif existing is not None:
                db.projects.update_project(
                    project_id,
                    name=str(value.get("name") or existing.name),
                    description=str(value.get("description") or existing.description),
                    is_archived=bool(meta.get("deleted") or value.get("is_archived")),
                    updated_at=incoming or None,
                )
            merged_projects += 1
        received["projects"] = merged_projects
        
        # Independent relationship axes use composite ids and therefore merge
        # through their purpose-built repositories instead of `_MERGEABLE`.
        for bucket, repo_name, owner_key in (
            ("knowledge_memberships", "knowledge_memberships", "knowledge_id"),
            ("project_relationships", "project_relationships", "project_id"),
        ):
            merged = 0
            records = body.get(bucket) or []
            repo = getattr(db, repo_name, None)
            if repo is None and records:
                raise ConflictError(f"hub does not support {bucket}")
            for rec in records:
                meta, value = rec["meta"], rec.get("value") or {}
                owner = str(value.get(owner_key) or "").strip()
                ref = str(value.get("resource_ref") or "").strip()
                if not owner or not ref:
                    continue
                existing = repo.get(owner, ref, include_deleted=True)
                incoming = str(meta.get("last_modified") or "")
                if existing is not None and incoming:
                    local_clock, incoming_clock = _iso(existing.last_modified), _iso(incoming)
                    if local_clock == incoming_clock:
                        relationship_changed = (
                            bool(existing.deleted) != bool(meta.get("deleted"))
                            or (bucket == "project_relationships" and (
                                existing.relationship != str(value.get("relationship") or "member")
                                or existing.source != str(value.get("source") or "manual")
                                or existing.confidence != float(value.get("confidence", 1.0))
                            ))
                        )
                        if relationship_changed:
                            raise ConflictError("relationship conflict at equal sync clock", context={"conflict": {"kind": _BUCKET_KIND[bucket], "id": str(meta["id"]), "last_modified": incoming_clock}})
                        continue
                    if local_clock > incoming_clock:
                        continue
                kwargs: dict[str, Any] = {
                    owner_key: owner, "resource_ref": ref,
                    "last_modified": incoming or None,
                    "deleted": bool(meta.get("deleted")),
                }
                if bucket == "project_relationships":
                    kwargs.update(
                        relationship=value.get("relationship") or "member",
                        source=value.get("source") or "manual",
                        confidence=value.get("confidence", 1.0),
                    )
                repo.upsert(**kwargs)
                merged += 1
            received[bucket] = merged
        
        revision_merged = 0
        from ..deployment_revisions import DeploymentRevision
        for rec in body.get("deployment_revisions") or []:
            if rec["meta"].get("deleted"):
                continue
            value = rec.get("value")
            if not isinstance(value, dict) or value.get("id") != rec["meta"]["id"]:
                continue
            if "secret" in value or "credential" in value:
                raise ValidationError("deployment revision must not carry credentials")
            try:
                db.deployment_revisions.upsert(DeploymentRevision(**value))
            except TypeError as exc:
                raise ValidationError("malformed deployment revision") from exc
            revision_merged += 1
        received["deployment_revisions"] = revision_merged

        thought_merged, consumed_notes, consumed_memberships = _merge_refinement_thought_bundles(
            db, body.get("refinement_thoughts") or [], body.get("notes") or [],
            body.get("directory_memberships") or [],
        )
        received["refinement_thoughts"] = thought_merged
        if consumed_notes:
            body = dict(body)
            body["notes"] = [rec for rec in body.get("notes") or [] if str(rec["meta"]["id"]) not in consumed_notes]
        if consumed_memberships:
            body = dict(body)
            body["directory_memberships"] = [
                rec for rec in body.get("directory_memberships") or []
                if str(rec["meta"]["id"]) not in consumed_memberships
            ]

        # Primitive merge dispatch is registry-owned; adding an unrelated
        # bucket therefore cannot make an optional repository mandatory.
        for spec in SYNC_REGISTRY:
            if spec.merger is not None:
                received[spec.bucket] = spec.merger(db, spec, body.get(spec.bucket) or [])
        return {"success": True, "received": received}
