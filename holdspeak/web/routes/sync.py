"""HSM-10-02 — the desktop sync receiver (mobile ⇄ desktop continuity).

The Python side of the mobile sync transport (`HTTPSyncProvider` in the Apple
runtime). Two routes on the user's own server:

- ``GET /api/sync/pull`` — serialize the desktop's meetings + artifacts as a
  contract change-set (the HSM-10-01 envelope: ``{meetings, artifacts}`` of
  ``{meta:{id, kind, last_modified, deleted}, value}``). Read-only.
- ``POST /api/sync/push`` — receive a pushed change-set into a durable inbox
  (``<db_dir>/sync_inbox/``). It accepts + persists; **merging pushed records into
  the live store (with conflict resolution) is HSM-10-03**, not this story.

The wire is snake_case, matching the contract coder on the mobile side
(SERIALIZATION-CONTRACT §11). No new DB schema — the inbox is plain JSON files —
so this is purely additive to the shipped desktop product.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.sync")


def _iso(value: Any) -> Any:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


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

        return JSONResponse({"meetings": meetings, "artifacts": artifacts})

    @router.post("/api/sync/push")
    async def api_sync_push(request: Request) -> Any:
        from ...db import get_database

        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"success": False, "error": "invalid JSON"}, status_code=400)
        if not isinstance(body, dict) or ("meetings" not in body and "artifacts" not in body):
            return JSONResponse(
                {"success": False, "error": "expected a change_set with meetings/artifacts"},
                status_code=422,
            )

        n_meetings = len(body.get("meetings") or [])
        n_artifacts = len(body.get("artifacts") or [])

        inbox = get_database().db_path.parent / "sync_inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        # Lexically-ordered name from the existing count (no clock dependency).
        idx = len(list(inbox.glob("inbox-*.json")))
        dest = inbox / f"inbox-{idx:06d}.json"
        dest.write_text(json.dumps(body), encoding="utf-8")

        log.info(f"sync push received: meetings={n_meetings} artifacts={n_artifacts} -> {dest.name}")
        return JSONResponse(
            {"success": True, "received": {"meetings": n_meetings, "artifacts": n_artifacts}}
        )

    return router
