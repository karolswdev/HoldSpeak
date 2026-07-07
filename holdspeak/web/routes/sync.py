"""HSM-10-02 — the desktop sync receiver (mobile ⇄ desktop continuity).

The Python side of the mobile sync transport (`HTTPSyncProvider` in the Apple
runtime). Two routes on the user's own server:

- ``GET /api/sync/pull`` — serialize the desktop's synced primitives as a
  contract change-set: per kind a list of ``{meta:{id, kind, last_modified,
  deleted}, value}`` records. Covers meetings + artifacts (already shipped) and,
  as part of the Primitive Framework hub, the desk's new first-class primitives:
  notes, kbs, recipes, chains, workflows, directories and directory memberships
  (the canonical filing map `primitive_id -> directory_id`). Read-only.
- ``POST /api/sync/push`` — receive a pushed change-set. Every kind is *merged
  into the live store* with last-write-wins on ``last_modified`` and tombstone
  deletes: the desk primitives through their repositories, and meetings +
  artifacts through ``MeetingRepository``/``PluginArtifactRepository``, so a
  meeting or artifact pushed from a peer is immediately queryable via the normal
  read paths (``GET /api/meetings/{id}``, ``.../artifacts``), matching the other
  kinds. A copy of the pushed meeting/artifact records is also kept in a durable
  JSON inbox (``<db_dir>/sync_inbox/``) as a replayable audit trail.

The wire is snake_case, ISO-8601 UTC ``Z`` timestamps, last-write-by
``last_modified`` conflict resolution, and tombstone deletes — mirroring how
meetings/artifacts sync today (SERIALIZATION-CONTRACT §11).
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.sync")

# The full sync taxonomy. Meetings/artifacts are the shipped content primitives;
# the rest are the Primitive Framework desk primitives, each backed by a real
# repository on the hub. Keep this in lockstep with the mobile/web SyncKind enum.
SYNC_KINDS = frozenset(
    {"meeting", "artifact", "note", "kb", "recipe", "chain", "workflow",
     "directory", "directory_membership", "profile", "model"}
)

# Repository-backed primitives the push route merges into the live store (the key
# is both the change-set bucket name and the repo attribute on the Database).
#   bucket -> (db attribute, repo-id kwarg, upsert-field map from `value`)
_MERGEABLE: dict[str, tuple[str, str, dict[str, str]]] = {
    "notes": ("notes", "note_id", {
        "title": "title", "body_markdown": "body_markdown", "tags": "tags",
    }),
    "kbs": ("kbs", "kb_id", {"name": "name", "member_ids": "member_ids"}),
    "recipes": ("recipes", "recipe_id", {
        "name": "name", "avatar": "avatar", "role": "role",
        "system_prompt": "system_prompt", "user_template": "user_template",
        "tools": "tools", "kb_id": "kb_id", "profile_id": "profile_id",
        # v7 (Phase 77): the pinned context rides the wire both ways now.
        "manual_context": "manual_context", "use_zone_context": "use_zone_context",
    }),
    # Runtime profiles (Phase 24) — SHAPE ONLY; no api key field crosses the wire.
    "profiles": ("profiles", "profile_id", {
        "name": "name", "kind": "kind", "model_file": "model_file",
        "base_url": "base_url", "model": "model", "node": "node",
        "context_limit": "context_limit", "requires_key": "requires_key",
    }),
    "chains": ("chains", "chain_id", {"name": "name", "steps": "steps"}),
    "workflows": ("workflows", "workflow_id", {
        "name": "name", "prompt": "prompt", "graph_json": "graph_json",
    }),
    "directories": ("directories", "directory_id", {
        "name": "name", "parent_id": "parent_id",
    }),
    # Membership: the synced filing map. Keyed by `primitive_id` (the record id),
    # value carries the `directory_id` edge. Supersedes the legacy `filed` maps.
    "directory_memberships": ("directory_memberships", "primitive_id", {
        "directory_id": "directory_id",
    }),
    # Model MANIFESTS (HSM-16-08): availability only — id/node/name/capabilities.
    # No path/url/bytes field exists on either side; the binary NEVER syncs.
    "models": ("model_manifests", "manifest_id", {
        "node": "node", "name": "name", "capabilities": "capabilities",
    }),
}

# bucket name -> the kind string each record's meta must carry.
_BUCKET_KIND = {
    "meetings": "meeting", "artifacts": "artifact", "notes": "note",
    "kbs": "kb", "recipes": "recipe", "chains": "chain", "workflows": "workflow",
    "directories": "directory", "directory_memberships": "directory_membership",
    "profiles": "profile", "models": "model",
}


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
    return str(value)


def _records_valid(records: Any) -> bool:
    """Every record is a `synced<T>` with a well-formed `meta` (id + known kind)."""
    if not isinstance(records, list):
        return False
    for rec in records:
        if not isinstance(rec, dict):
            return False
        meta = rec.get("meta")
        if not isinstance(meta, dict):
            return False
        if not meta.get("id") or meta.get("kind") not in SYNC_KINDS:
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
    return {
        "meta": {
            "id": rec.id,
            "kind": kind,
            "last_modified": rec.last_modified,
            "deleted": deleted,
        },
        "value": None if deleted else rec.to_dict(),
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


def _meeting_state_from_value(value: dict[str, Any]) -> Any:
    """A pushed meeting `value` (the `MeetingState.to_dict` wire shape) → a
    `MeetingState`, ready to hand to ``MeetingRepository.save_meeting``.

    The exact inverse of `MeetingState.to_dict`: started/ended timestamps,
    transcript segments, bookmarks and the latest intel snapshot all round-trip.
    """
    from ...meeting_session import (
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
    )


def _merge_meetings(db: Any, records: list[dict[str, Any]]) -> int:
    """Live-merge pushed meeting records (LWW on `last_modified`, tombstone-aware).

    The LWW stamp for the stored copy is the meeting's `started_at` ISO — exactly
    the field ``pull`` emits as the meeting's `last_modified`, so the conflict key
    is symmetric across surfaces.
    """
    merged = 0
    for rec in records:
        meta = rec["meta"]
        rec_id = str(meta["id"]).strip()
        if not rec_id:
            continue
        incoming_lm = _parse_dt(meta.get("last_modified"))
        existing = db.meetings.get_meeting(rec_id)
        if existing is not None and incoming_lm is not None:
            # The stored copy's LWW key is `started_at` — the field `pull` emits
            # as the meeting's `last_modified`, so the conflict key is symmetric.
            if existing.started_at >= incoming_lm:
                continue
        if meta.get("deleted"):
            db.meetings.delete_meeting(rec_id)
            merged += 1
            continue
        value = rec.get("value") or {}
        if not isinstance(value, dict):
            continue
        state = _meeting_state_from_value({**value, "id": rec_id})
        if not state.id:
            continue
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


def _hub_model_name(ctx: WebContext) -> str:
    """The hub's own model, for its live manifest row: the cloud model id when
    intel targets an endpoint, else the local GGUF's stem. Never a path — the
    manifest advertises availability, not location.

    The intel knobs live on ``Config.meeting``, not the top-level ``Config`` —
    reading them off the wrong level raised inside the ``except`` and the hub
    silently never advertised its own model (the HSM-16-08 latent bug; the
    guard test now exercises this body with a real ``Config``).
    """
    try:
        from ...config import Config

        meeting = Config.load().meeting
        if not meeting.intel_enabled:
            return ""
        if meeting.intel_provider == "cloud":
            return str(meeting.intel_cloud_model or "")
        from pathlib import Path as _P

        stem = _P(str(meeting.intel_realtime_model or "")).name
        return stem[:-5] if stem.lower().endswith(".gguf") else stem
    except Exception:
        return ""


def build_sync_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/sync/pull")
    async def api_sync_pull(limit: int = 50) -> Any:
        from ...db import get_database

        db = get_database()
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
                    # NOTE: started_at as last_modified is a transport-grade stamp;
                    # conflict-grade last-modified (updated_at) is HSM-10-03.
                    "last_modified": _iso(summary.started_at), "deleted": False,
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
        directories = [_primitive_record(d, "directory")
                       for d in db.directories.list(include_deleted=True, limit=bounded)]
        # Membership rides the wire too (organization, not layout). The record's
        # synced id is its `primitive_id` (the `id` property), the value carries
        # the `directory_id` edge.
        directory_memberships = [
            _primitive_record(m, "directory_membership")
            for m in db.directory_memberships.list(include_deleted=True, limit=bounded)
        ]

        # Model MANIFESTS (HSM-16-08): every node's pushed rows, PLUS the hub's own
        # model as a live virtual row (computed from config, never stored) — so a
        # companion knows what "run it on your desktop" would actually run. The
        # binary never rides; a manifest is id/node/name/capabilities only.
        models = [_primitive_record(m, "model")
                  for m in db.model_manifests.list(include_deleted=True, limit=bounded)]
        hub_model = _hub_model_name(ctx)
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

        return JSONResponse({
            "meetings": meetings,
            "artifacts": artifacts,
            "notes": notes,
            "kbs": kbs,
            "recipes": recipes,
            "chains": chains,
            "workflows": workflows,
            "profiles": profiles,
            "directories": directories,
            "directory_memberships": directory_memberships,
            "models": models,
        })

    @router.post("/api/sync/push")
    async def api_sync_push(request: Request) -> Any:
        from ...db import get_database

        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"success": False, "error": "invalid JSON"}, status_code=400)

        known_buckets = set(_BUCKET_KIND)
        if not isinstance(body, dict) or not (set(body) & known_buckets):
            return JSONResponse(
                {"success": False, "error": "expected a change_set with at least one of "
                 + ", ".join(sorted(known_buckets))},
                status_code=422,
            )

        # HSM-10-03 — validate the envelope: every record needs a well-formed sync
        # header (id + a known kind). Malformed → 422, never stored/merged.
        for bucket in known_buckets:
            if not _records_valid(body.get(bucket) or []):
                return JSONResponse(
                    {"success": False,
                     "error": f"malformed sync record in {bucket} (need meta.id + meta.kind)"},
                    status_code=422,
                )

        db = get_database()
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

        # Desk primitives: merge into the live store, last-write-wins on
        # last_modified, tombstone deletes.
        for bucket, (attr, id_kwarg, field_map) in _MERGEABLE.items():
            repo = getattr(db, attr)
            merged = 0
            for rec in body.get(bucket) or []:
                meta = rec["meta"]
                value = rec.get("value") or {}
                rec_id = str(meta["id"])
                incoming_lm = str(meta.get("last_modified") or "")
                existing = repo.get(rec_id, include_deleted=True)
                # Last-write-wins: skip if the stored copy is newer.
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
                for value_key, upsert_key in field_map.items():
                    if value_key in value:
                        kwargs[upsert_key] = value[value_key]
                repo.upsert(**kwargs)
                merged += 1
            received[bucket] = merged

        return JSONResponse({"success": True, "received": received})

    return router
