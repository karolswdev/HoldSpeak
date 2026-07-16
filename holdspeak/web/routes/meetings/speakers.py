"""DB-backed speaker listing, detail, and rename/avatar routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import _SpeakerUpdateRequest
from ...runtime_support import error_500
from ...context import WebContext

log = get_logger("web.routes.meetings")


def build_speakers_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/speakers")
    async def api_list_speakers() -> Any:
        """List known speakers with aggregate stats."""
        try:
            from ....db import get_database

            db = get_database()
            speakers = db.meetings.get_all_speakers()
            payload: list[dict[str, Any]] = []
            for speaker in speakers:
                stats = db.meetings.get_speaker_stats(speaker.id)
                payload.append(
                    {
                        "id": speaker.id,
                        "name": speaker.name,
                        "avatar": speaker.avatar,
                        "sample_count": speaker.sample_count,
                        "total_segments": stats.get("total_segments", 0),
                        "total_speaking_time": stats.get("total_speaking_time", 0.0),
                        "meeting_count": stats.get("meeting_count", 0),
                        "first_seen": stats["first_seen"].isoformat() if stats.get("first_seen") else None,
                        "last_seen": stats["last_seen"].isoformat() if stats.get("last_seen") else None,
                    }
                )

            payload.sort(key=lambda s: (s.get("last_seen") or "", s.get("sample_count") or 0), reverse=True)
            return JSONResponse({"speakers": payload, "total": len(payload)})
        except Exception as e:
            return error_500(e, log, "Failed to list speakers")

    @router.get("/api/speakers/{speaker_id}")
    async def api_get_speaker(speaker_id: str, limit: int = 500) -> Any:
        """Get speaker profile, stats, and related segments grouped by meeting."""
        try:
            from ....db import get_database

            db = get_database()
            speaker = db.meetings.get_speaker(speaker_id)
            if speaker is None:
                return JSONResponse({"error": "Speaker not found"}, status_code=404)

            stats = db.meetings.get_speaker_stats(speaker_id)
            groups = db.meetings.get_speaker_segments(speaker_id, limit=limit)
            for group in groups:
                if isinstance(group.get("meeting_date"), datetime):
                    group["meeting_date"] = group["meeting_date"].isoformat()

            return JSONResponse(
                {
                    "speaker": {
                        "id": speaker.id,
                        "name": speaker.name,
                        "avatar": speaker.avatar,
                        "sample_count": speaker.sample_count,
                    },
                    "stats": {
                        "total_segments": stats.get("total_segments", 0),
                        "total_speaking_time": stats.get("total_speaking_time", 0.0),
                        "meeting_count": stats.get("meeting_count", 0),
                        "first_seen": stats["first_seen"].isoformat() if stats.get("first_seen") else None,
                        "last_seen": stats["last_seen"].isoformat() if stats.get("last_seen") else None,
                    },
                    "meetings": groups,
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to get speaker")

    @router.patch("/api/speakers/{speaker_id}")
    async def api_update_speaker(speaker_id: str, payload: _SpeakerUpdateRequest) -> Any:
        """Rename speaker and/or update avatar."""
        try:
            from ....db import get_database

            db = get_database()
            updated = False

            if payload.name is not None:
                name = payload.name.strip()
                if not name:
                    return JSONResponse({"success": False, "error": "Speaker name cannot be empty. The saved name is unchanged. Enter a name and retry."}, status_code=400)
                updated = db.meetings.update_speaker_name(speaker_id, name) or updated

            if payload.avatar is not None:
                avatar = payload.avatar.strip()
                if not avatar:
                    return JSONResponse({"success": False, "error": "Speaker avatar cannot be empty. The saved avatar is unchanged. Pick an avatar and retry."}, status_code=400)
                updated = db.meetings.update_speaker_avatar(speaker_id, avatar) or updated

            if not updated:
                return JSONResponse({"success": False, "error": "Speaker not found"}, status_code=404)

            speaker = db.meetings.get_speaker(speaker_id)
            if speaker is None:
                return JSONResponse({"success": False, "error": "Speaker not found"}, status_code=404)

            return JSONResponse(
                {
                    "success": True,
                    "speaker": {
                        "id": speaker.id,
                        "name": speaker.name,
                        "avatar": speaker.avatar,
                        "sample_count": speaker.sample_count,
                    },
                }
            )
        except Exception as e:
            log.error(f"Failed to update speaker: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    return router
