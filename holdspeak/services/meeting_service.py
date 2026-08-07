"""Transport-neutral meeting lifecycle and archive operations (HS-122-04).

The live capture engine remains owned by the runtime.  Its callbacks are bound
at composition time, so this module can serve HTTP, MCP, and tests without
importing a web-layer type.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from ..db.core import Database
from ..meeting_exports import render_meeting_export
from ..principals import Principal
from .primitive_service import NotFound, ValidationError


class MeetingService:
    """One service boundary for meeting capture and persisted meeting data."""

    def __init__(self, db: Database) -> None:
        self._db = db
        self._on_start: Callable[..., Any] | None = None
        self._on_stop: Callable[[], Any] | None = None
        self._on_bookmark: Callable[[str], Any] | None = None
        self._on_update: Callable[..., Any] | None = None

    def bind_lifecycle(
        self,
        *,
        on_start: Callable[..., Any] | None = None,
        on_stop: Callable[[], Any] | None = None,
        on_bookmark: Callable[[str], Any] | None = None,
        on_update: Callable[..., Any] | None = None,
    ) -> None:
        """Bind runtime-owned capture callbacks at an application edge."""
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_bookmark = on_bookmark
        self._on_update = on_update

    def list_meetings(
        self,
        principal: Principal,
        query: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 50,
        cursor: str | int | None = None,
        *,
        speaker: str | None = None,
        tag: str | None = None,
        has_open_actions: bool = False,
    ) -> dict[str, Any]:
        """Return archive summaries, preserving the web archive's filters."""
        bounded_limit = max(1, min(int(limit), 500))
        offset = self._offset(cursor)
        parsed_from = self._parse_date(from_date)
        parsed_to = self._parse_date(to_date, end_of_day=True)
        search_ids: list[str] | None = None
        if query and query.strip():
            search_ids = list(
                dict.fromkeys(
                    meeting_id
                    for meeting_id, _ in self._db.meetings.search_transcripts(
                        query.strip(), limit=500
                    )
                )
            )
        meetings = self._db.meetings.list_meetings(
            limit=bounded_limit,
            offset=offset,
            date_from=parsed_from,
            date_to=parsed_to,
            speaker=speaker,
            tag=tag,
            has_open_actions=has_open_actions,
            meeting_ids=search_ids,
        )
        filtered = bool(query or from_date or to_date or speaker or tag or has_open_actions)
        total = len(meetings) if filtered else self._db.meetings.get_meeting_count()
        return {
            "meetings": [self._summary_payload(meeting) for meeting in meetings],
            "total": total,
            "next_cursor": str(offset + len(meetings)) if len(meetings) == bounded_limit else None,
        }

    def get_meeting(
        self,
        principal: Principal,
        meeting_id: str | None = None,
        include: str | None = None,
        *,
        id: str | None = None,
    ) -> dict[str, Any]:
        """Return a meeting; ``id`` is accepted for adapter-facing callers."""
        resolved_id = id if id is not None else meeting_id
        if not resolved_id:
            raise ValidationError("meeting id is required")
        meeting = self._db.meetings.get_meeting(resolved_id)
        if meeting is None:
            raise NotFound("meeting", resolved_id)
        return meeting.to_dict()

    def start_capture(
        self, principal: Principal, config: dict[str, Any] | None = None
    ) -> dict[str, Any] | Any:
        if self._on_start is None:
            raise ValidationError("Meeting start control not supported")
        devices = list((config or {}).get("devices") or [])
        result = self._on_start(devices=devices) if devices else self._on_start()
        return self._callback_payload(result)

    def stop_capture(
        self, principal: Principal, meeting_id: str | None = None
    ) -> dict[str, Any] | Any:
        if self._on_stop is None:
            raise ValidationError("Meeting stop control not supported")
        return self._callback_payload(self._on_stop()) or {"status": "stopped"}

    def bookmark(
        self,
        principal: Principal,
        meeting_id: str | None = None,
        *,
        label: str = "",
    ) -> dict[str, Any] | Any:
        if self._on_bookmark is None:
            raise ValidationError("Meeting bookmark control not supported")
        return self._callback_payload(self._on_bookmark(label))

    def update_meeting(
        self, principal: Principal, meeting_id: str, **patch: Any
    ) -> dict[str, Any]:
        title = patch.get("title")
        tags = patch.get("tags")
        if title is not None and not isinstance(title, str):
            raise ValidationError("meeting title must be a string")
        if tags is not None and not isinstance(tags, list):
            raise ValidationError("meeting tags must be a list")
        if self._on_update is not None:
            result = self._on_update(title=title, tags=tags)
            return self._callback_payload(result) or {}

        existing = self._db.meetings.get_meeting(meeting_id)
        if existing is None:
            raise NotFound("meeting", meeting_id)
        updated = self._db.meetings.update_meeting_metadata(
            meeting_id,
            title if title is not None else (existing.title or ""),
            tags if tags is not None else existing.tags,
        )
        if not updated:
            raise NotFound("meeting", meeting_id)
        return self.get_meeting(principal, meeting_id)

    def delete_meeting(self, principal: Principal, meeting_id: str) -> bool:
        if not self._db.meetings.delete_meeting(meeting_id):
            raise NotFound("meeting", meeting_id)
        return True

    def export_meeting(
        self, principal: Principal, meeting_id: str, format: str
    ) -> dict[str, str]:
        export_format = str(format or "").strip().lower()
        if export_format == "md":
            export_format = "markdown"
        if export_format not in {"markdown", "json"}:
            raise ValidationError(f"Invalid export format: {format}")
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            raise NotFound("meeting", meeting_id)
        content = render_meeting_export(
            meeting,
            export_format,  # type: ignore[arg-type]
            artifacts=self._db.plugins.list_artifacts(meeting_id, limit=200),
        )
        extension = "md" if export_format == "markdown" else "json"
        return {
            "content": content,
            "media_type": (
                "text/markdown; charset=utf-8"
                if export_format == "markdown"
                else "application/json; charset=utf-8"
            ),
            "filename": f"holdspeak-meeting-{meeting_id}.{extension}",
        }

    def search_artifacts(
        self, principal: Principal, query: str, limit: int = 50
    ) -> dict[str, Any]:
        clean_query = str(query or "").strip()
        if not clean_query:
            raise ValidationError("query is required")
        return self._db.memory.search(
            clean_query, kinds=("artifact",), limit=limit
        ).to_dict()

    @staticmethod
    def _callback_payload(result: Any) -> dict[str, Any] | Any | None:
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return result if isinstance(result, dict) else None

    @staticmethod
    def _parse_date(value: str | None, *, end_of_day: bool = False) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValidationError(f"Invalid date: {value}") from exc
        if end_of_day and len(text) == 10:
            return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return parsed

    @staticmethod
    def _offset(cursor: str | int | None) -> int:
        if cursor in (None, ""):
            return 0
        try:
            return max(0, int(cursor))
        except (TypeError, ValueError) as exc:
            raise ValidationError("cursor must be a non-negative integer") from exc

    @staticmethod
    def _summary_payload(meeting: Any) -> dict[str, Any]:
        return {
            "id": meeting.id,
            "started_at": meeting.started_at.isoformat(),
            "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
            "title": meeting.title,
            "duration_seconds": meeting.duration_seconds,
            "segment_count": meeting.segment_count,
            "action_item_count": meeting.action_item_count,
            "tags": meeting.tags,
            "intel_status": meeting.intel_status,
            "intel_status_detail": meeting.intel_status_detail,
            "capture_status": meeting.capture_status,
            "capture_failure": meeting.capture_failure,
            "capture_checkpoint_seconds": meeting.capture_checkpoint_seconds,
            "provenance": meeting.provenance,
        }
