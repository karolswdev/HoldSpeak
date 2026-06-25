"""Meeting / speaker / intel routes (HS-26-02).

The largest cluster moved off `MeetingWebServer._create_app`: meeting
lifecycle + bookmark, meeting-scoped action-item mutations, the DB-backed
meeting/speaker listings and exports, global action-item routes, and the
deferred-intel queue routes. Handlers are moved verbatim — only the closure
target changes from the server instance to the shared `WebContext`.

The lifecycle/mutation handlers read callbacks (`on_*`, `broadcast`) from the
context; the DB-backed read routes close over no server state and call the
module-level `get_database()` directly, exactly as before.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from ...logging_config import get_logger
from ...web_requests import (
    _ActionItemEditRequest,
    _ActionItemReviewRequest,
    _ActionItemUpdateRequest,
    _AftercareFileIssueRequest,
    _BookmarkRequest,
    _GlobalActionItemEditRequest,
    _GlobalActionItemReviewRequest,
    _GlobalActionItemUpdateRequest,
    _IntelProcessRequest,
    _MeetingStartRequest,
    _CompanionSlackRequest,
    _ProposalDecisionRequest,
    _SlackExportRequest,
    _SpeakerUpdateRequest,
    _StopRequest,
    _UpdateMeetingRequest,
)
from ..runtime_support import _UnknownDeviceError, _meeting_callback_payload, error_500
from ..context import WebContext

log = get_logger("web.routes.meetings")


def _parse_facet_date(value: Optional[str], *, end_of_day: bool = False):
    """Parse a facet date param (ISO date or datetime); None on blank/garbage.

    A bare date used as the range end is made inclusive of the whole day.
    """
    from datetime import datetime

    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if end_of_day and len(text) == 10:  # a bare YYYY-MM-DD
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    return parsed


def build_meetings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.post("/api/bookmark")
    async def api_bookmark(payload: Optional[_BookmarkRequest] = None) -> Any:
        try:
            label = payload.label if payload is not None else ""
            result = ctx.on_bookmark(label)
        except Exception as e:
            log.error(f"on_bookmark failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        bookmark_data: Any = None
        if hasattr(result, "to_dict"):
            try:
                bookmark_data = result.to_dict()
            except Exception:
                bookmark_data = None
        elif isinstance(result, dict):
            bookmark_data = result

        if bookmark_data is not None:
            ctx.broadcast("bookmark", bookmark_data)

        return JSONResponse({"success": True})

    async def _handle_stop_request(callback: Callable[[], Any]) -> Any:
        try:
            result = callback()
        except Exception as e:
            log.error(f"on_stop failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        stopped_data: Any = None
        if hasattr(result, "to_dict"):
            try:
                stopped_data = result.to_dict()
            except Exception:
                stopped_data = None
        elif isinstance(result, dict):
            stopped_data = result
        else:
            stopped_data = {"status": "stopped"}

        ctx.broadcast("stopped", stopped_data)
        return JSONResponse({"success": True})

    @router.post("/api/meeting/start")
    async def api_meeting_start(
        payload: Optional[_MeetingStartRequest] = None,
    ) -> Any:
        if ctx.on_start is None:
            return JSONResponse(
                {"success": False, "error": "Meeting start control not supported"},
                status_code=501,
            )

        devices = list(payload.devices) if payload and payload.devices else []

        try:
            result = ctx.on_start(devices=devices) if devices else ctx.on_start()
        except _UnknownDeviceError as exc:
            return JSONResponse(
                {"success": False, "error": str(exc), "device_id": exc.device_id},
                status_code=404,
            )
        except Exception as e:
            log.error(f"on_start failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        meeting_data = _meeting_callback_payload(result)

        if meeting_data is not None:
            ctx.broadcast("meeting_started", meeting_data)
        return JSONResponse({"success": True, "meeting": meeting_data})

    @router.post("/api/meeting/stop")
    async def api_meeting_stop(_: Optional[_StopRequest] = None) -> Any:
        callback = ctx.on_meeting_stop or ctx.on_stop
        return await _handle_stop_request(callback)

    @router.post("/api/stop")
    async def api_stop(_: Optional[_StopRequest] = None) -> Any:
        # Backward-compatible alias.
        return await _handle_stop_request(ctx.on_stop)

    @router.patch("/api/action-items/{item_id}")
    async def api_update_action_item(
        item_id: str, payload: _ActionItemUpdateRequest
    ) -> Any:
        if ctx.on_update_action_item is None:
            return JSONResponse(
                {"success": False, "error": "Action item updates not supported"},
                status_code=501,
            )

        status = payload.status
        if status not in ("done", "pending", "dismissed"):
            return JSONResponse(
                {"success": False, "error": f"Invalid status: {status}"},
                status_code=400,
            )

        try:
            result = ctx.on_update_action_item(item_id, status)
        except Exception as e:
            log.error(f"on_update_action_item failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if result is None:
            return JSONResponse(
                {"success": False, "error": "Action item not found"},
                status_code=404,
            )

        # Broadcast the update to all connected clients
        ctx.broadcast("action_item_updated", result)

        return JSONResponse({"success": True, "action_item": result})

    @router.patch("/api/action-items/{item_id}/review")
    async def api_update_action_item_review(
        item_id: str, payload: _ActionItemReviewRequest
    ) -> Any:
        if ctx.on_update_action_item_review is None:
            return JSONResponse(
                {"success": False, "error": "Action item review updates not supported"},
                status_code=501,
            )

        review_state = str(payload.review_state or "").strip().lower()
        if review_state not in ("pending", "accepted"):
            return JSONResponse(
                {"success": False, "error": f"Invalid review_state: {review_state}"},
                status_code=400,
            )

        try:
            result = ctx.on_update_action_item_review(item_id, review_state)
        except Exception as e:
            log.error(f"on_update_action_item_review failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if result is None:
            return JSONResponse(
                {"success": False, "error": "Action item not found"},
                status_code=404,
            )

        ctx.broadcast("action_item_updated", result)
        return JSONResponse({"success": True, "action_item": result})

    @router.patch("/api/action-items/{item_id}/edit")
    async def api_edit_action_item(
        item_id: str, payload: _ActionItemEditRequest
    ) -> Any:
        if ctx.on_edit_action_item is None:
            return JSONResponse(
                {"success": False, "error": "Action item edits not supported"},
                status_code=501,
            )

        task = str(payload.task or "").strip()
        if not task:
            return JSONResponse(
                {"success": False, "error": "Action item task cannot be empty"},
                status_code=400,
            )

        try:
            result = ctx.on_edit_action_item(
                item_id,
                task=task,
                owner=payload.owner,
                due=payload.due,
            )
        except Exception as e:
            log.error(f"on_edit_action_item failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if result is None:
            return JSONResponse(
                {"success": False, "error": "Action item not found"},
                status_code=404,
            )

        ctx.broadcast("action_item_updated", result)
        return JSONResponse({"success": True, "action_item": result})

    @router.patch("/api/meeting")
    async def api_update_meeting(payload: _UpdateMeetingRequest) -> Any:
        """Update meeting title and/or tags."""
        try:
            meeting_data: Optional[dict[str, Any]] = None
            if ctx.on_update_meeting is not None:
                result = ctx.on_update_meeting(title=payload.title, tags=payload.tags)
                if hasattr(result, "to_dict"):
                    try:
                        meeting_data = result.to_dict()
                    except Exception:
                        meeting_data = None
                elif isinstance(result, dict):
                    meeting_data = result
            else:
                if payload.title is not None and ctx.on_set_title is not None:
                    ctx.on_set_title(payload.title)
                if payload.tags is not None and ctx.on_set_tags is not None:
                    ctx.on_set_tags(payload.tags)
                try:
                    meeting_data = ctx.get_state() or {}
                except Exception:
                    meeting_data = None

            if isinstance(meeting_data, dict):
                ctx.broadcast(
                    "meeting_updated",
                    {
                        "title": meeting_data.get("title"),
                        "tags": meeting_data.get("tags") if isinstance(meeting_data.get("tags"), list) else [],
                    },
                )
            return JSONResponse({"success": True, "meeting": meeting_data})
        except Exception as e:
            log.error(f"Failed to update meeting: {e}")
            return JSONResponse(
                {"success": False, "error": str(e)}, status_code=500
            )

    @router.get("/api/meetings")
    async def api_list_meetings(
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        speaker: Optional[str] = None,
        tag: Optional[str] = None,
        has_open_actions: bool = False,
    ) -> Any:
        """List meetings, with HS-55-04 server-side facets composing with search.

        Facets filter in SQL over the whole archive. With ``search``, the
        full-text hits flow through the same faceted query, so both branches
        return the same summary shape (this also fixed search results
        previously returning full ``to_dict`` payloads whose nested
        ``intel_status`` broke the status pill).
        """
        try:
            from ...db import get_database
            db = get_database()

            parsed_from = _parse_facet_date(date_from)
            parsed_to = _parse_facet_date(date_to, end_of_day=True)

            search_ids: Optional[list[str]] = None
            if search:
                results = db.meetings.search_transcripts(search, limit=500)
                search_ids = list(dict.fromkeys([r[0] for r in results]))

            meetings = db.meetings.list_meetings(
                limit=limit,
                offset=offset,
                date_from=parsed_from,
                date_to=parsed_to,
                tag=tag,
                speaker=speaker,
                has_open_actions=has_open_actions,
                meeting_ids=search_ids,
            )
            filtered = bool(search or date_from or date_to or speaker or tag or has_open_actions)
            return JSONResponse({
                "meetings": [
                    {
                        "id": m.id,
                        "started_at": m.started_at.isoformat(),
                        "ended_at": m.ended_at.isoformat() if m.ended_at else None,
                        "title": m.title,
                        "duration_seconds": m.duration_seconds,
                        "segment_count": m.segment_count,
                        "action_item_count": m.action_item_count,
                        "tags": m.tags,
                        "intel_status": m.intel_status,
                        "intel_status_detail": m.intel_status_detail,
                    }
                    for m in meetings
                ],
                "total": len(meetings) if filtered else db.meetings.get_meeting_count(),
            })
        except Exception as e:
            log.error(f"Failed to list meetings: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/speakers")
    async def api_list_speakers() -> Any:
        """List known speakers with aggregate stats."""
        try:
            from ...db import get_database

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
            from ...db import get_database

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
            from ...db import get_database

            db = get_database()
            updated = False

            if payload.name is not None:
                name = payload.name.strip()
                if not name:
                    return JSONResponse({"success": False, "error": "Speaker name cannot be empty"}, status_code=400)
                updated = db.meetings.update_speaker_name(speaker_id, name) or updated

            if payload.avatar is not None:
                avatar = payload.avatar.strip()
                if not avatar:
                    return JSONResponse({"success": False, "error": "Speaker avatar cannot be empty"}, status_code=400)
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

    @router.get("/api/meetings/facets")
    async def api_meeting_facets() -> Any:
        """Distinct speakers + tags for the /history filter row (HS-55-04).

        Registered before ``/api/meetings/{meeting_id}`` so "facets" never
        matches as a meeting id.
        """
        try:
            from ...db import get_database
            db = get_database()
            return JSONResponse(db.meetings.list_facet_values())
        except Exception as e:
            log.error(f"Failed to list meeting facets: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/meetings/{meeting_id}")
    async def api_get_meeting(meeting_id: str) -> Any:
        """Get meeting details from database."""
        try:
            from ...db import get_database
            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"}, status_code=404
                )
            return JSONResponse(meeting.to_dict())
        except Exception as e:
            log.error(f"Failed to get meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.delete("/api/meetings/{meeting_id}")
    async def api_delete_meeting(meeting_id: str) -> Any:
        """Delete a meeting (HS-55-02: e.g. a failed import's honest row)."""
        try:
            from ...db import get_database
            db = get_database()
            if not db.meetings.delete_meeting(meeting_id):
                return JSONResponse(
                    {"error": "Meeting not found"}, status_code=404
                )
            return JSONResponse({"deleted": meeting_id})
        except Exception as e:
            log.error(f"Failed to delete meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/meetings/{meeting_id}/export")
    async def api_export_meeting(
        meeting_id: str,
        format: str = "markdown",
    ) -> Any:
        """Render a saved meeting handoff export."""
        export_format = str(format or "").strip().lower()
        if export_format == "md":
            export_format = "markdown"
        if export_format not in {"markdown", "json"}:
            return JSONResponse(
                {"error": f"Invalid export format: {format}"},
                status_code=400,
            )

        try:
            from ...db import get_database
            from ...meeting_exports import render_meeting_export

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"}, status_code=404
                )

            artifacts = db.plugins.list_artifacts(meeting_id, limit=200)
            content = render_meeting_export(
                meeting,
                export_format,  # type: ignore[arg-type]
                artifacts=artifacts,
            )
            extension = "md" if export_format == "markdown" else "json"
            media_type = (
                "text/markdown; charset=utf-8"
                if export_format == "markdown"
                else "application/json; charset=utf-8"
            )
            filename = f"holdspeak-meeting-{meeting_id}.{extension}"
            return Response(
                content=content,
                media_type=media_type,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception as e:
            log.error(f"Failed to export meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/meetings/{meeting_id}/intent-timeline")
    async def api_get_meeting_intent_timeline(
        meeting_id: str,
        limit: int = 200,
    ) -> Any:
        """Get persisted MIR intent timeline for one meeting."""
        try:
            from ...db import get_database
            from ...intent_timeline import detect_intent_transitions

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"},
                    status_code=404,
                )

            windows = db.plugins.list_intent_windows(meeting_id, limit=limit)
            transitions = detect_intent_transitions(
                [(window.window_id, list(window.active_intents)) for window in windows]
            )
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "windows": [
                        {
                            "meeting_id": window.meeting_id,
                            "window_id": window.window_id,
                            "start_seconds": window.start_seconds,
                            "end_seconds": window.end_seconds,
                            "transcript_hash": window.transcript_hash,
                            "transcript_excerpt": window.transcript_excerpt,
                            "profile": window.profile,
                            "threshold": window.threshold,
                            "active_intents": window.active_intents,
                            "intent_scores": window.intent_scores,
                            "override_intents": window.override_intents,
                            "tags": window.tags,
                            "metadata": window.metadata,
                            "created_at": window.created_at.isoformat(),
                            "updated_at": window.updated_at.isoformat(),
                        }
                        for window in windows
                    ],
                    "transitions": transitions,
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load meeting intent timeline")

    @router.get("/api/meetings/{meeting_id}/plugin-runs")
    async def api_get_meeting_plugin_runs(
        meeting_id: str,
        limit: int = 500,
        window_id: Optional[str] = None,
    ) -> Any:
        """Get persisted MIR plugin-run history for one meeting."""
        try:
            from ...db import get_database

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"},
                    status_code=404,
                )

            runs = db.plugins.list_plugin_runs(meeting_id, window_id=window_id, limit=limit)
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "window_id": window_id,
                    "runs": [
                        {
                            "id": run.id,
                            "meeting_id": run.meeting_id,
                            "window_id": run.window_id,
                            "plugin_id": run.plugin_id,
                            "plugin_version": run.plugin_version,
                            "status": run.status,
                            "idempotency_key": run.idempotency_key,
                            "duration_ms": run.duration_ms,
                            "output": run.output,
                            "error": run.error,
                            "deduped": run.deduped,
                            "created_at": run.created_at.isoformat(),
                            "updated_at": run.updated_at.isoformat(),
                        }
                        for run in runs
                    ],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load meeting plugin runs")

    @router.get("/api/meetings/{meeting_id}/artifacts")
    async def api_get_meeting_artifacts(
        meeting_id: str,
        limit: int = 200,
    ) -> Any:
        """Get synthesized artifacts and lineage for one meeting."""
        try:
            from ...db import get_database

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"},
                    status_code=404,
                )

            artifacts = db.plugins.list_artifacts(meeting_id, limit=limit)
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "artifacts": [
                        {
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
                            "created_at": artifact.created_at.isoformat(),
                            "updated_at": artifact.updated_at.isoformat(),
                        }
                        for artifact in artifacts
                    ],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load meeting artifacts")

    @router.get("/api/meetings/{meeting_id}/aftercare")
    async def api_get_meeting_aftercare(meeting_id: str) -> Any:
        """Read-only aftercare digest for one meeting (HS-49-01).

        Aggregates what's still open (by owner), what was decided, and a real
        diff against the chronologically previous meeting. Pure read — no writes,
        no side effects. Returns `is_empty` so the surface can stay quiet when
        there is nothing open, nothing decided, and nothing changed.
        """
        try:
            from ...db import get_database
            from ...meeting_aftercare import compute_meeting_aftercare

            db = get_database()
            digest = compute_meeting_aftercare(db, meeting_id)
            if digest is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)
            # HS-61-02: the capability flag the Send-to-Slack buttons gate on.
            # A bool only — the webhook URL is a credential and never rides
            # an aftercare response.
            from ...config import Config

            digest["slack_configured"] = bool(
                Config.load().meeting.slack_webhook_url
            )
            return JSONResponse(digest)
        except Exception as e:
            return error_500(e, log, "Failed to load meeting aftercare")

    @router.get("/api/meetings/{meeting_id}/followup-draft")
    async def api_get_meeting_followup_draft(meeting_id: str) -> Any:
        """A local, copyable follow-up draft for one meeting (HS-49-04).

        Assembled deterministically from the aftercare digest — decisions, open
        items by owner, and the since-last-meeting delta. Preview + copy only:
        nothing is sent and no connector is opened. Honest when there's little to
        say (no padding). Pure read; 404 for an unknown meeting.
        """
        try:
            from ...db import get_database
            from ...meeting_aftercare import build_followup_draft, compute_meeting_aftercare

            db = get_database()
            digest = compute_meeting_aftercare(db, meeting_id)
            if digest is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "markdown": build_followup_draft(digest),
                    "is_empty": digest["is_empty"],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to build meeting follow-up draft")

    def _proposal_to_dict(proposal: Any) -> dict[str, Any]:
        return {
            "id": proposal.id,
            "meeting_id": proposal.meeting_id,
            "window_id": proposal.window_id,
            "plugin_id": proposal.plugin_id,
            "plugin_version": proposal.plugin_version,
            "status": proposal.status,
            "target": proposal.target,
            "action": proposal.action,
            "preview": proposal.preview,
            "payload": proposal.payload,
            "reversible": proposal.reversible,
            "required_capabilities": proposal.required_capabilities,
            "decided_by": proposal.decided_by,
            "result": proposal.result,
            "error": proposal.error,
            "created_at": proposal.created_at,
            "decided_at": proposal.decided_at,
            "executed_at": proposal.executed_at,
        }

    def _actuator_result_event(proposal: Any) -> dict[str, Any]:
        """The wire-safe `actuator_result` payload (preview only, never the
        machine payload — the Phase-56 lock)."""
        return {
            "id": getattr(proposal, "id", ""),
            "meeting_id": getattr(proposal, "meeting_id", ""),
            "status": getattr(proposal, "status", ""),
            "target": getattr(proposal, "target", ""),
            "action": getattr(proposal, "action", ""),
            "preview": getattr(proposal, "preview", ""),
            "reversible": bool(getattr(proposal, "reversible", False)),
            "error": getattr(proposal, "error", None),
        }

    def _execute_slack_proposal(db: Any, proposal: Any, *, actor: str) -> Any:
        """HS-61-01: the execute leg for an approved Send-to-Slack proposal.

        The repo had no production execute path at all before this — the
        `ActuatorExecutor` was host-injected in dogfoods only. For `slack`
        proposals the approval IS the moment the user wants the send, so the
        decision route executes right here, through the full executor guard
        stack (status gate, payload parity, audit).

        On consent: the user configured `meeting.slack_webhook_url` (consent
        for exactly that host — the connector's manifest allow-lists it and
        nothing else) and just approved this very action. That pair is the
        Phase-52 "configuring is consent" model PLUS a per-action approval,
        so this executor instance runs with its master switch on rather than
        demanding a third toggle (`allow_actuators`) be flipped too.

        The webhook URL is a credential: it is read from config at execution
        time and injected by the connector in memory only — never stored on
        the proposal, never broadcast, never returned.
        """
        from ...config import Config
        from ...plugins.actuator_executor import ActuatorExecutor
        from ...slack_export import build_slack_connector

        url = Config.load().meeting.slack_webhook_url
        if not url:
            # Configured when proposed, unconfigured by execution time: an
            # honest terminal failure (retryable via failed -> approved once
            # the URL is back), never a silent drop.
            updated = db.actuators.transition_proposal(
                proposal.id,
                to_status="failed",
                actor=actor,
                detail="slack export: no webhook URL configured at execution time",
                error="Slack is not configured (meeting.slack_webhook_url is empty)",
            )
            ctx.broadcast("actuator_result", _actuator_result_event(updated))
            return updated

        executor = ActuatorExecutor(
            db,
            connector=build_slack_connector(url),
            allow_actuators=True,
            actor=actor,
            on_result=lambda event: ctx.broadcast("actuator_result", event),
        )
        return executor.execute(proposal.id)

    @router.get("/api/meetings/{meeting_id}/proposals")
    async def api_get_meeting_proposals(
        meeting_id: str,
        status: Optional[str] = None,
    ) -> Any:
        """List actuator proposals for one meeting (HS-37-03).

        A pure DB read — viewing a proposal performs **no** side effect.
        """
        try:
            from ...db import get_database

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)

            proposals = db.actuators.list_proposals(meeting_id, status=status)
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "proposals": [_proposal_to_dict(p) for p in proposals],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load meeting proposals")

    @router.post("/api/meetings/{meeting_id}/proposals/{proposal_id}/decision")
    async def api_decide_meeting_proposal(
        meeting_id: str,
        proposal_id: str,
        payload: _ProposalDecisionRequest,
    ) -> Any:
        """Approve or reject an actuator proposal (HS-37-03).

        Approving only flips DB state to `approved` (+ `decided_by` + an audit
        entry); it performs **no** side effect — execution is HS-37-04. Rejecting
        is terminal. Illegal decisions (e.g. on an already-executed proposal)
        return 400.
        """
        decision = str(payload.decision or "").strip().lower()
        if decision not in ("approved", "rejected"):
            return JSONResponse(
                {"success": False, "error": f"Invalid decision: {decision!r}"},
                status_code=400,
            )
        try:
            from ...db import get_database

            db = get_database()
            existing = db.actuators.get_proposal(proposal_id)
            if existing is None or existing.meeting_id != meeting_id:
                return JSONResponse(
                    {"success": False, "error": "Proposal not found"},
                    status_code=404,
                )
            try:
                updated = db.actuators.transition_proposal(
                    proposal_id,
                    to_status=decision,
                    actor=(payload.decided_by or "web-user").strip() or "web-user",
                )
            except ValueError as ve:
                # Illegal lifecycle transition (e.g. already executed/rejected).
                return JSONResponse(
                    {"success": False, "error": str(ve)}, status_code=400
                )
            if decision == "rejected":
                # HS-56-03: a rejection is a terminal result the presence
                # mascot can reflect. Wire-safe: preview only, never the
                # machine payload.
                ctx.broadcast(
                    "actuator_result",
                    {
                        "id": updated.id,
                        "meeting_id": updated.meeting_id,
                        "status": "rejected",
                        "target": updated.target,
                        "action": updated.action,
                        "preview": updated.preview,
                        "reversible": bool(updated.reversible),
                        "error": None,
                    },
                )
            if decision == "approved" and updated.target == "slack":
                # HS-61-01: a Send-to-Slack approval executes immediately —
                # see _execute_slack_proposal for the consent reasoning. Other
                # targets keep today's behavior (approval flips state only).
                updated = _execute_slack_proposal(
                    db,
                    updated,
                    actor=(payload.decided_by or "web-user").strip() or "web-user",
                )
            return JSONResponse({"success": True, "proposal": _proposal_to_dict(updated)})
        except Exception as e:
            return error_500(e, log, "Failed to decide meeting proposal")

    @router.post("/api/meetings/{meeting_id}/aftercare/file-issue")
    async def api_aftercare_file_issue(
        meeting_id: str, payload: _AftercareFileIssueRequest
    ) -> Any:
        """Turn an accepted action item into a GitHub-issue actuator proposal (HS-49-03).

        Closing the loop reuses the existing propose -> approve -> execute flow:
        this records a `proposed` proposal only. Nothing leaves the machine here —
        execution still requires a separate human approval (the decision endpoint)
        plus `allow_actuators` + the per-project allow-list + a host-injected
        connector. No new write primitive; idempotent per (meeting, action item).
        """
        repo = str(payload.repo or "").strip()
        if not repo:
            return JSONResponse(
                {"success": False, "error": "A target repo (owner/name) is required"},
                status_code=400,
            )
        try:
            from ...db import get_database
            from ...plugins.builtin.github_issue_actuator import (
                GithubIssueActuator,
                build_github_issue_proposal,
            )

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)

            item = db.meetings.get_action_item(payload.action_item_id)
            if item is None or item.meeting_id != meeting_id:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )
            # Only a human-reviewed (accepted) action can be filed — this is the
            # "take what I just accepted and track it" seam, not auto-filing.
            if item.review_state != "accepted":
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Only an accepted action item can be filed as an issue",
                    },
                    status_code=400,
                )

            spec = build_github_issue_proposal(
                task=item.task,
                owner=item.owner,
                due=item.due,
                meeting_title=meeting.title or "meeting",
                repo=repo,
            )
            proposal = db.actuators.record_proposal(
                meeting_id=meeting_id,
                window_id=f"{meeting_id}:aftercare",
                plugin_id=GithubIssueActuator.id,
                plugin_version=GithubIssueActuator.version,
                idempotency_key=f"aftercare-issue:{meeting_id}:{item.id}",
                target=spec["target"],
                action=spec["action"],
                preview=spec["preview"],
                payload=spec["payload"],
                reversible=spec["reversible"],
                required_capabilities=spec["required_capabilities"],
            )
            # HS-56-03: the live in-meeting path already broadcasts proposals;
            # the aftercare path now does too, with the identical wire-safe
            # shape (the human preview only — never the machine payload).
            ctx.broadcast(
                "actuator_proposed",
                {
                    "id": proposal.id,
                    "meeting_id": proposal.meeting_id,
                    "plugin_id": proposal.plugin_id,
                    "status": proposal.status,
                    "target": proposal.target,
                    "action": proposal.action,
                    "preview": proposal.preview,
                    "reversible": bool(proposal.reversible),
                    "created_at": proposal.created_at.isoformat()
                    if hasattr(proposal.created_at, "isoformat")
                    else proposal.created_at,
                },
            )
            return JSONResponse(
                {"success": True, "proposal": _proposal_to_dict(proposal)}
            )
        except Exception as e:
            return error_500(e, log, "Failed to file aftercare issue")

    @router.post("/api/meetings/{meeting_id}/export/slack")
    async def api_export_meeting_to_slack(
        meeting_id: str, payload: _SlackExportRequest
    ) -> Any:
        """Propose sending one aftercare artifact to Slack (HS-61-01).

        Records a `proposed` actuator proposal whose preview IS the exact
        message text Slack would receive — nothing is sent here; execution
        happens only when the proposal is approved (the decision endpoint).
        Refuses up front when no webhook URL is configured (the feature is
        invisible then), when `what` is unknown, or when the meeting's
        aftercare is empty (no padding gets sent to a channel).

        Wire safety: the stored payload carries only the message body. The
        webhook URL is a credential — it stays in config, joined to the POST
        in memory at execution time only.
        """
        import hashlib

        from ...config import Config
        from ...slack_export import EXPORT_KINDS, slack_message_for

        what = str(payload.what or "").strip().lower()
        if what not in EXPORT_KINDS:
            return JSONResponse(
                {
                    "success": False,
                    "error": f"Unknown export kind: {what!r} (expected 'digest' or 'followup')",
                },
                status_code=400,
            )
        if not Config.load().meeting.slack_webhook_url:
            return JSONResponse(
                {
                    "success": False,
                    "error": "Slack is not configured (set the webhook URL in Settings first)",
                },
                status_code=400,
            )
        try:
            from ...db import get_database
            from ...meeting_aftercare import compute_meeting_aftercare
            from ...plugins.builtin.webhook_post_actuator import WebhookPostActuator

            db = get_database()
            digest = compute_meeting_aftercare(db, meeting_id)
            if digest is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)
            if digest.get("is_empty"):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "This meeting has nothing open, decided, or changed to send",
                    },
                    status_code=400,
                )

            text = slack_message_for(digest, what)
            # Identical content dedupes to the existing proposal; edited
            # aftercare (a new item, a corrected decision) re-proposes.
            content_key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            proposal = db.actuators.record_proposal(
                meeting_id=meeting_id,
                window_id=f"{meeting_id}:aftercare",
                plugin_id=WebhookPostActuator.id,
                plugin_version=WebhookPostActuator.version,
                idempotency_key=f"slack-export:{meeting_id}:{what}:{content_key}",
                target="slack",
                action="post_message",
                preview=text,
                payload={"body": {"text": text}},
                reversible=False,  # a posted message cannot be unsent
                required_capabilities=["actuator"],
            )
            # The same wire-safe shape every proposal broadcast uses (the
            # human preview only — never the machine payload).
            ctx.broadcast(
                "actuator_proposed",
                {
                    "id": proposal.id,
                    "meeting_id": proposal.meeting_id,
                    "plugin_id": proposal.plugin_id,
                    "status": proposal.status,
                    "target": proposal.target,
                    "action": proposal.action,
                    "preview": proposal.preview,
                    "reversible": bool(proposal.reversible),
                    "created_at": proposal.created_at.isoformat()
                    if hasattr(proposal.created_at, "isoformat")
                    else proposal.created_at,
                },
            )
            return JSONResponse(
                {"success": True, "proposal": _proposal_to_dict(proposal)}
            )
        except Exception as e:
            return error_500(e, log, "Failed to propose Slack export")

    # ----- HSM-14: the iPad desk (a companion) routes a connector send through
    # the HOST's actuator framework. The companion holds NO credential; it
    # proposes arbitrary text, the host executes with the webhook joined in
    # memory at execution time. Same propose -> approve -> execute as Phase 61.
    _COMPANION_MEETING_ID = "companion"

    @router.post("/api/companion/slack/propose")
    async def api_companion_slack_propose(payload: _CompanionSlackRequest) -> Any:
        """Propose sending arbitrary companion (desk) text to Slack (HSM-14).

        A non-meeting-scoped sibling of the aftercare Slack export: the iPad
        drops a generated card onto its Slack connector, and that becomes a
        `proposed` actuator proposal here. The preview IS the exact message
        body; the webhook URL is never accepted from or returned to the
        companion — it stays on the host, joined at execution time only.
        """
        import hashlib

        from ...config import Config

        text = str(payload.text or "").strip()
        if not text:
            return JSONResponse({"success": False, "error": "text is required"}, status_code=400)
        if not Config.load().meeting.slack_webhook_url:
            return JSONResponse(
                {"success": False, "error": "Slack is not configured on the host (set the webhook URL in Settings first)"},
                status_code=400,
            )
        try:
            from datetime import datetime

            from ...db import get_database
            from ...meeting_session import MeetingState
            from ...plugins.builtin.webhook_post_actuator import WebhookPostActuator

            db = get_database()
            # actuator_proposals.meeting_id is a NOT NULL FK to meetings(id); a
            # companion send isn't tied to a meeting, so it hangs off one hidden
            # sentinel row (excluded from list_meetings). Created on demand.
            if db.meetings.get_meeting(_COMPANION_MEETING_ID) is None:
                db.meetings.save_meeting(
                    MeetingState(
                        id=_COMPANION_MEETING_ID,
                        started_at=datetime.now(),
                        title="Desk · companion sends",
                    )
                )
            body = f"*{payload.title.strip()}*\n{text}" if (payload.title or "").strip() else text
            content_key = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            proposal = db.actuators.record_proposal(
                meeting_id=_COMPANION_MEETING_ID,
                window_id="companion:slack",
                plugin_id=WebhookPostActuator.id,
                plugin_version=WebhookPostActuator.version,
                idempotency_key=f"companion-slack:{content_key}",
                target="slack",
                action="post_message",
                preview=body,
                payload={"body": {"text": body}},
                reversible=False,
                required_capabilities=["actuator"],
            )
            ctx.broadcast(
                "actuator_proposed",
                {
                    "id": proposal.id,
                    "meeting_id": proposal.meeting_id,
                    "plugin_id": proposal.plugin_id,
                    "status": proposal.status,
                    "target": proposal.target,
                    "action": proposal.action,
                    "preview": proposal.preview,
                    "reversible": bool(proposal.reversible),
                },
            )
            return JSONResponse({"success": True, "proposal": _proposal_to_dict(proposal)})
        except Exception as e:
            return error_500(e, log, "Failed to propose companion Slack send")

    @router.post("/api/companion/slack/{proposal_id}/decision")
    async def api_decide_companion_slack(
        proposal_id: str, payload: _ProposalDecisionRequest
    ) -> Any:
        """Approve (→ execute) or reject a companion Slack proposal (HSM-14).

        Mirrors the meeting decision route but scoped to companion proposals.
        Approving a `slack` proposal executes immediately through the full
        guarded executor (status gate, payload parity, manifest allow-list),
        with the webhook URL injected in memory by the connector — never on the
        proposal, never returned.
        """
        decision = str(payload.decision or "").strip().lower()
        if decision not in ("approved", "rejected"):
            return JSONResponse({"success": False, "error": f"Invalid decision: {decision!r}"}, status_code=400)
        try:
            from ...db import get_database

            db = get_database()
            existing = db.actuators.get_proposal(proposal_id)
            if existing is None or existing.meeting_id != _COMPANION_MEETING_ID:
                return JSONResponse({"success": False, "error": "Proposal not found"}, status_code=404)
            try:
                updated = db.actuators.transition_proposal(
                    proposal_id,
                    to_status=decision,
                    actor=(payload.decided_by or "companion").strip() or "companion",
                )
            except ValueError as ve:
                return JSONResponse({"success": False, "error": str(ve)}, status_code=400)
            if decision == "rejected":
                ctx.broadcast("actuator_result", _actuator_result_event(updated))
            if decision == "approved" and updated.target == "slack":
                updated = _execute_slack_proposal(
                    db, updated, actor=(payload.decided_by or "companion").strip() or "companion"
                )
            return JSONResponse({"success": True, "proposal": _proposal_to_dict(updated)})
        except Exception as e:
            return error_500(e, log, "Failed to decide companion Slack proposal")

    @router.get("/api/all-action-items")
    async def api_list_all_action_items(
        include_completed: bool = False,
        owner: Optional[str] = None,
        meeting_id: Optional[str] = None,
    ) -> Any:
        """List action items across all meetings from database."""
        try:
            from ...db import get_database
            db = get_database()
            items = db.meetings.list_action_items(
                include_completed=include_completed,
                owner=owner,
                meeting_id=meeting_id,
            )
            return JSONResponse({
                "action_items": [
                    {
                        "id": item.id,
                        "task": item.task,
                        "owner": item.owner,
                        "due": item.due,
                        "status": item.status,
                        "review_state": item.review_state,
                        "source_timestamp": item.source_timestamp,
                        "meeting_id": item.meeting_id,
                        "meeting_title": item.meeting_title,
                        "meeting_date": item.meeting_date.isoformat(),
                        "created_at": item.created_at.isoformat(),
                        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
                    }
                    for item in items
                ]
            })
        except Exception as e:
            log.error(f"Failed to list action items: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.patch("/api/all-action-items/{item_id}")
    async def api_update_global_action_item(
        item_id: str, payload: _GlobalActionItemUpdateRequest
    ) -> Any:
        """Update action item status in database."""
        status = payload.status
        if status not in ("done", "pending", "dismissed"):
            return JSONResponse(
                {"success": False, "error": f"Invalid status: {status}"},
                status_code=400,
            )

        try:
            from ...db import get_database
            db = get_database()
            success = db.meetings.update_action_item_status(item_id, status)
            if not success:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )
            updated = db.meetings.get_action_item(item_id) if hasattr(db.meetings, "get_action_item") else None
            return JSONResponse(
                {
                    "success": True,
                    "action_item": (
                        {
                            "id": updated.id,
                            "task": updated.task,
                            "owner": updated.owner,
                            "due": updated.due,
                            "status": updated.status,
                            "review_state": updated.review_state,
                            "source_timestamp": updated.source_timestamp,
                            "meeting_id": updated.meeting_id,
                            "meeting_title": updated.meeting_title,
                            "meeting_date": updated.meeting_date.isoformat(),
                            "created_at": updated.created_at.isoformat(),
                            "completed_at": (
                                updated.completed_at.isoformat()
                                if updated.completed_at
                                else None
                            ),
                            "reviewed_at": (
                                updated.reviewed_at.isoformat()
                                if updated.reviewed_at
                                else None
                            ),
                        }
                        if updated is not None
                        else None
                    ),
                }
            )
        except Exception as e:
            log.error(f"Failed to update action item: {e}")
            return JSONResponse(
                {"success": False, "error": str(e)}, status_code=500
            )

    @router.patch("/api/all-action-items/{item_id}/review")
    async def api_review_global_action_item(
        item_id: str, payload: _GlobalActionItemReviewRequest
    ) -> Any:
        """Update action item review state."""
        review_state = str(payload.review_state or "").strip().lower()
        if review_state not in ("pending", "accepted"):
            return JSONResponse(
                {"success": False, "error": f"Invalid review_state: {review_state}"},
                status_code=400,
            )

        try:
            from ...db import get_database
            db = get_database()
            success = db.meetings.update_action_item_review_state(item_id, review_state)
            if not success:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )
            updated = db.meetings.get_action_item(item_id) if hasattr(db.meetings, "get_action_item") else None
            return JSONResponse(
                {
                    "success": True,
                    "action_item": (
                        {
                            "id": updated.id,
                            "task": updated.task,
                            "owner": updated.owner,
                            "due": updated.due,
                            "status": updated.status,
                            "review_state": updated.review_state,
                            "source_timestamp": updated.source_timestamp,
                            "meeting_id": updated.meeting_id,
                            "meeting_title": updated.meeting_title,
                            "meeting_date": updated.meeting_date.isoformat(),
                            "created_at": updated.created_at.isoformat(),
                            "completed_at": (
                                updated.completed_at.isoformat()
                                if updated.completed_at
                                else None
                            ),
                            "reviewed_at": (
                                updated.reviewed_at.isoformat()
                                if updated.reviewed_at
                                else None
                            ),
                        }
                        if updated is not None
                        else None
                    ),
                }
            )
        except Exception as e:
            log.error(f"Failed to update action item review state: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.patch("/api/all-action-items/{item_id}/edit")
    async def api_edit_global_action_item(
        item_id: str, payload: _GlobalActionItemEditRequest
    ) -> Any:
        """Edit action item details and auto-accept the item."""
        task = str(payload.task or "").strip()
        if not task:
            return JSONResponse(
                {"success": False, "error": "Action item task cannot be empty"},
                status_code=400,
            )

        owner = payload.owner
        due = payload.due
        try:
            from ...db import get_database
            db = get_database()
            success = db.meetings.edit_action_item(
                item_id,
                task=task,
                owner=owner,
                due=due,
            )
            if not success:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )
            updated = db.meetings.get_action_item(item_id) if hasattr(db.meetings, "get_action_item") else None
            return JSONResponse(
                {
                    "success": True,
                    "action_item": (
                        {
                            "id": updated.id,
                            "task": updated.task,
                            "owner": updated.owner,
                            "due": updated.due,
                            "status": updated.status,
                            "review_state": updated.review_state,
                            "source_timestamp": updated.source_timestamp,
                            "meeting_id": updated.meeting_id,
                            "meeting_title": updated.meeting_title,
                            "meeting_date": updated.meeting_date.isoformat(),
                            "created_at": updated.created_at.isoformat(),
                            "completed_at": (
                                updated.completed_at.isoformat()
                                if updated.completed_at
                                else None
                            ),
                            "reviewed_at": (
                                updated.reviewed_at.isoformat()
                                if updated.reviewed_at
                                else None
                            ),
                        }
                        if updated is not None
                        else None
                    ),
                }
            )
        except ValueError as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to edit action item: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.get("/api/intel/jobs")
    async def api_list_intel_jobs(
        status: str = "all",
        limit: int = 20,
        history_limit: int = 5,
    ) -> Any:
        """List deferred intelligence jobs."""
        try:
            from ...db import get_database
            from ...config import Config

            db = get_database()
            jobs = db.intel.list_intel_jobs(status=status, limit=limit)
            retry_max_attempts = max(1, int(Config.load().meeting.intel_retry_max_attempts))
            now = datetime.now()
            bounded_history_limit = max(1, min(int(history_limit), 20))
            return JSONResponse(
                {
                    "jobs": [
                        {
                            "meeting_id": job.meeting_id,
                            "status": job.status,
                            "transcript_hash": job.transcript_hash,
                            "requested_at": job.requested_at.isoformat(),
                            "updated_at": job.updated_at.isoformat(),
                            "attempts": job.attempts,
                            "last_error": job.last_error,
                            "meeting_title": job.meeting_title,
                            "started_at": job.started_at.isoformat() if job.started_at else None,
                            "intel_status_detail": job.intel_status_detail,
                            "retry_scheduled": (
                                job.status == "queued"
                                and bool(job.last_error)
                                and job.requested_at > now
                            ),
                            "next_retry_at": (
                                job.requested_at.isoformat()
                                if (
                                    job.status == "queued"
                                    and bool(job.last_error)
                                    and job.requested_at > now
                                )
                                else None
                            ),
                            "retries_remaining": max(0, retry_max_attempts - int(job.attempts)),
                            "retry_max_attempts": retry_max_attempts,
                            "retry_history": [
                                {
                                    "attempt": event.attempt,
                                    "outcome": event.outcome,
                                    "error": event.error,
                                    "retry_at": event.retry_at.isoformat() if event.retry_at else None,
                                    "created_at": event.created_at.isoformat(),
                                }
                                for event in db.intel.list_intel_job_attempts(
                                    job.meeting_id,
                                    limit=bounded_history_limit,
                                )
                            ],
                        }
                        for job in jobs
                    ]
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to list intel jobs")

    @router.get("/api/intel/summary")
    async def api_intel_queue_summary() -> Any:
        """Return aggregate deferred-intel queue telemetry."""
        try:
            from ...db import get_database

            db = get_database()
            summary = db.intel.get_intel_queue_summary()
            return JSONResponse(
                {
                    "total_jobs": summary.total_jobs,
                    "queued_jobs": summary.queued_jobs,
                    "running_jobs": summary.running_jobs,
                    "failed_jobs": summary.failed_jobs,
                    "queued_due_jobs": summary.queued_due_jobs,
                    "scheduled_retry_jobs": summary.scheduled_retry_jobs,
                    "next_retry_at": (
                        summary.next_retry_at.isoformat() if summary.next_retry_at else None
                    ),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load intel queue summary")

    @router.post("/api/intel/process")
    async def api_process_intel_jobs(payload: Optional[_IntelProcessRequest] = None) -> Any:
        """Process queued deferred-intel jobs now."""
        try:
            from ...config import Config
            from ...intel_queue import drain_intel_queue

            cfg = Config.load().meeting
            max_jobs = payload.max_jobs if payload is not None else None
            mode = (payload.mode if payload is not None else None) or "respect_backoff"
            normalized_mode = str(mode).strip().lower()
            if normalized_mode not in {"respect_backoff", "retry_now"}:
                return JSONResponse(
                    {"success": False, "error": "mode must be respect_backoff or retry_now"},
                    status_code=400,
                )
            include_scheduled = normalized_mode == "retry_now"

            # HS-56-04: when deferred intel completes, the meeting's open
            # work becomes knowable — the presence mascot's aftercare card.
            def _on_meeting_ready(meeting_id: str) -> None:
                from ...meeting_aftercare import build_aftercare_ready_event

                event = build_aftercare_ready_event(get_database(), meeting_id)
                if event is not None:
                    ctx.broadcast("aftercare_ready", event)

            processed = drain_intel_queue(
                cfg.intel_realtime_model,
                on_meeting_ready=_on_meeting_ready,
                provider=cfg.intel_provider,
                cloud_model=cfg.intel_cloud_model,
                cloud_api_key_env=cfg.intel_cloud_api_key_env,
                cloud_base_url=cfg.intel_cloud_base_url,
                cloud_reasoning_effort=cfg.intel_cloud_reasoning_effort,
                cloud_store=cfg.intel_cloud_store,
                retry_base_seconds=cfg.intel_retry_base_seconds,
                retry_max_seconds=cfg.intel_retry_max_seconds,
                retry_max_attempts=cfg.intel_retry_max_attempts,
                include_scheduled=include_scheduled,
                max_jobs=max_jobs,
            )
            return JSONResponse(
                {
                    "success": True,
                    "processed": processed,
                    "mode": normalized_mode,
                }
            )
        except Exception as e:
            log.error(f"Failed to process intel jobs: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.post("/api/intel/retry/{meeting_id}")
    async def api_retry_intel_job(meeting_id: str) -> Any:
        """Requeue deferred intelligence for a specific meeting."""
        try:
            from ...db import get_database

            db = get_database()
            ok = db.intel.requeue_intel_job(meeting_id, reason="Manual retry requested from web UI.")
            if not ok:
                return JSONResponse({"success": False, "error": "Meeting not found or transcript is empty"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as e:
            log.error(f"Failed to retry intel job: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    return router
