"""Transport-neutral activity meeting-candidate operations (HS-123-07)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from typing import Any
from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ValidationError


@observe_service
class ActivityMeetingCandidateService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    @staticmethod
    def _payload(c: Any) -> dict[str, Any]:
        return {"id": getattr(c, "id", None), "source_connector_id": c.source_connector_id, "source_activity_record_id": c.source_activity_record_id, "dedupe_key": getattr(c, "dedupe_key", ""), "title": c.title, "starts_at": c.starts_at.isoformat() if c.starts_at else None, "ends_at": c.ends_at.isoformat() if c.ends_at else None, "meeting_url": c.meeting_url, "started_meeting_id": getattr(c, "started_meeting_id", None), "confidence": c.confidence, "status": getattr(c, "status", "preview"), "created_at": c.created_at.isoformat() if getattr(c, "created_at", None) else None, "updated_at": c.updated_at.isoformat() if getattr(c, "updated_at", None) else None}

    def list(self, principal: Principal, source_connector_id: str | None, status: str | None, limit: int) -> dict[str, Any]:
        try: candidates = self._db.activity.list_activity_meeting_candidates(source_connector_id=source_connector_id, status=status, limit=limit)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"count": len(candidates), "candidates": [self._payload(c) for c in candidates]}

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
