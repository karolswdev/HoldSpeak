"""HSM-10-02 — the desktop sync receiver (mobile ⇄ desktop continuity).

The Python side of the mobile sync transport (`HTTPSyncProvider` in the Apple
runtime). Two routes on the user's own server:

- ``GET /api/sync/pull`` — serialize the desktop's synced primitives as a
  contract change-set: per kind a list of ``{meta:{id, kind, last_modified,
  deleted}, value}`` records. Covers meetings + artifacts (already shipped) and,
  as part of the Primitive Framework hub, the desk's new first-class primitives:
  notes, kbs, agents, chains, workflows. Read-only.
- ``POST /api/sync/push`` — receive a pushed change-set. Meetings/artifacts land
  in a durable JSON inbox (``<db_dir>/sync_inbox/``) exactly as before; the new
  desk primitives are *merged into the live store* with last-write-wins on
  ``last_modified`` and tombstone deletes, since they have real repositories.

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
    {"meeting", "artifact", "note", "kb", "agent", "chain", "workflow"}
)

# Repository-backed primitives the push route merges into the live store (the key
# is both the change-set bucket name and the repo attribute on the Database).
#   bucket -> (db attribute, repo-id kwarg, upsert-field map from `value`)
_MERGEABLE: dict[str, tuple[str, str, dict[str, str]]] = {
    "notes": ("notes", "note_id", {
        "title": "title", "body_markdown": "body_markdown", "tags": "tags",
    }),
    "kbs": ("kbs", "kb_id", {"name": "name", "member_ids": "member_ids"}),
    "agents": ("agents", "agent_id", {
        "name": "name", "avatar": "avatar", "role": "role",
        "system_prompt": "system_prompt", "user_template": "user_template",
        "tools": "tools", "kb_id": "kb_id",
    }),
    "chains": ("chains", "chain_id", {"name": "name", "steps": "steps"}),
    "workflows": ("workflows", "workflow_id", {
        "name": "name", "prompt": "prompt", "graph_json": "graph_json",
    }),
}

# bucket name -> the kind string each record's meta must carry.
_BUCKET_KIND = {
    "meetings": "meeting", "artifacts": "artifact", "notes": "note",
    "kbs": "kb", "agents": "agent", "chains": "chain", "workflows": "workflow",
}


def _iso(value: Any) -> Any:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


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
        "meeting_id": artifact.meeting_id,
        "artifact_type": artifact.artifact_type,
        "title": artifact.title,
        "body_markdown": artifact.body_markdown,
        "structured_json": artifact.structured_json,
        "confidence": artifact.confidence,
        "status": artifact.status,
        "plugin_id": artifact.plugin_id,
        "plugin_version": artifact.plugin_version,
        "sources": artifact.sources,
    }


def _primitive_record(rec: Any, kind: str) -> dict[str, Any]:
    """A primitive dataclass → a `{meta, value}` sync record."""
    value = rec.to_dict()
    return {
        "meta": {
            "id": rec.id,
            "kind": kind,
            "last_modified": rec.last_modified,
            "deleted": bool(rec.deleted),
        },
        "value": value,
    }


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

        # The Primitive Framework desk primitives. `include_deleted=True` so
        # tombstones propagate to the other surfaces, just like a real sync.
        notes = [_primitive_record(n, "note")
                 for n in db.notes.list(include_deleted=True, limit=bounded)]
        kbs = [_primitive_record(k, "kb")
               for k in db.kbs.list(include_deleted=True, limit=bounded)]
        agents = [_primitive_record(a, "agent")
                  for a in db.agents.list(include_deleted=True, limit=bounded)]
        chains = [_primitive_record(c, "chain")
                  for c in db.chains.list(include_deleted=True, limit=bounded)]
        workflows = [_primitive_record(w, "workflow")
                     for w in db.workflows.list(include_deleted=True, limit=bounded)]

        return JSONResponse({
            "meetings": meetings,
            "artifacts": artifacts,
            "notes": notes,
            "kbs": kbs,
            "agents": agents,
            "chains": chains,
            "workflows": workflows,
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

        # Meetings/artifacts: durable JSON inbox (merge into the live store is
        # HSM-10-03 territory; unchanged here).
        n_meetings = len(body.get("meetings") or [])
        n_artifacts = len(body.get("artifacts") or [])
        if n_meetings or n_artifacts:
            inbox = db.db_path.parent / "sync_inbox"
            inbox.mkdir(parents=True, exist_ok=True)
            idx = len(list(inbox.glob("inbox-*.json")))
            dest = inbox / f"inbox-{idx:06d}.json"
            dest.write_text(json.dumps(
                {"meetings": body.get("meetings") or [],
                 "artifacts": body.get("artifacts") or []}
            ), encoding="utf-8")
            log.info(f"sync push inboxed: meetings={n_meetings} artifacts={n_artifacts} -> {dest.name}")
        received["meetings"] = n_meetings
        received["artifacts"] = n_artifacts

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
