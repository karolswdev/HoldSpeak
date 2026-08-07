"""Transport-neutral activity meeting-candidate operations (HS-123-07)."""
from __future__ import annotations
from typing import Any
from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ValidationError


class ActivityMeetingCandidateService:
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _payload(c: Any) -> dict[str, Any]:
        return {"id": getattr(c, "id", None), "source_connector_id": c.source_connector_id, "source_activity_record_id": c.source_activity_record_id, "dedupe_key": getattr(c, "dedupe_key", ""), "title": c.title, "starts_at": c.starts_at.isoformat() if c.starts_at else None, "ends_at": c.ends_at.isoformat() if c.ends_at else None, "meeting_url": c.meeting_url, "started_meeting_id": getattr(c, "started_meeting_id", None), "confidence": c.confidence, "status": getattr(c, "status", "preview"), "created_at": c.created_at.isoformat() if getattr(c, "created_at", None) else None, "updated_at": c.updated_at.isoformat() if getattr(c, "updated_at", None) else None}

    def preview(self, principal: Principal, limit: int) -> dict[str, Any]:
        from ..activity_candidates import preview_calendar_meeting_candidates
        records = self._db.activity.list_activity_records(limit=max(1, min(int(limit), 500)))
        candidates = preview_calendar_meeting_candidates(records, limit=limit)
        return {"count": len(candidates), "candidates": [self._payload(c) for c in candidates]}

    def list(self, principal: Principal, source_connector_id: str | None, status: str | None, limit: int) -> dict[str, Any]:
        try: candidates = self._db.activity.list_activity_meeting_candidates(source_connector_id=source_connector_id, status=status, limit=limit)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"count": len(candidates), "candidates": [self._payload(c) for c in candidates]}

    def create(self, principal: Principal, fields: dict[str, Any]) -> dict[str, Any]:
        from ..web.runtime_support import _parse_iso_datetime
        try: candidate = self._db.activity.create_activity_meeting_candidate(source_connector_id=fields.get("source_connector_id") or "calendar_activity", source_activity_record_id=fields.get("source_activity_record_id"), title=fields.get("title") or "", starts_at=_parse_iso_datetime(fields.get("starts_at")), ends_at=_parse_iso_datetime(fields.get("ends_at")), meeting_url=fields.get("meeting_url"), confidence=fields.get("confidence") if fields.get("confidence") is not None else 0.0, status=fields.get("status") or "candidate")
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"candidate": self._payload(candidate)}

    def update_status(self, principal: Principal, candidate_id: str, status: str) -> dict[str, Any]:
        try: candidate = self._db.activity.update_activity_meeting_candidate_status(candidate_id, status)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        if candidate is None: raise NotFound("activity meeting candidate", candidate_id)
        return {"candidate": self._payload(candidate)}

    def candidate_for_start(self, principal: Principal, candidate_id: str) -> dict[str, Any]:
        candidate = self._db.activity.get_activity_meeting_candidate(candidate_id)
        if candidate is None: raise NotFound("activity meeting candidate", candidate_id)
        return self._payload(candidate)

    def start(self, principal: Principal, candidate_id: str, meeting_data: Any, title_warning: str | None = None) -> dict[str, Any]:
        candidate = self._db.activity.get_activity_meeting_candidate(candidate_id)
        if candidate is None: raise NotFound("activity meeting candidate", candidate_id)
        meeting_id = meeting_data.get("id") if isinstance(meeting_data, dict) else None
        if meeting_id in (None, "") and isinstance(meeting_data, dict) and isinstance(meeting_data.get("meeting"), dict): meeting_id = meeting_data["meeting"].get("id")
        candidate = self._db.activity.mark_activity_meeting_candidate_started(candidate.id, meeting_id=str(meeting_id) if meeting_id not in (None, "") else None)
        if candidate is None: raise NotFound("activity meeting candidate", candidate_id)
        result = {"success": True, "candidate": self._payload(candidate), "meeting": meeting_data}
        if title_warning: result["warning"] = f"Meeting started, but title update failed: {title_warning}"
        return result

    def delete(self, principal: Principal, source_connector_id: str | None, status: str | None) -> dict[str, Any]:
        try: deleted = self._db.activity.delete_activity_meeting_candidates(source_connector_id=source_connector_id, status=status)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"deleted": deleted}
