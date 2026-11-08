"""PARKED 20261108 (subtraction day, Lane R): service methods only a parked route called.

Parked from ``holdspeak/services/activity_meeting_candidate_service.py`` ``ActivityMeetingCandidateService``: preview, update_status.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Transport-neutral activity meeting-candidate operations (HS-123-07)."""
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from typing import Any
from ...db.core import Database
from ...principals import Principal
from ..errors import NotFound, ValidationError


@observe_service
class ParkedActivityMeetingCandidateService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def preview(self, principal: Principal, limit: int) -> dict[str, Any]:
        from ...activity_candidates import preview_calendar_meeting_candidates
        records = self._db.activity.list_activity_records(limit=max(1, min(int(limit), 500)))
        candidates = preview_calendar_meeting_candidates(records, limit=limit)
        return {"count": len(candidates), "candidates": [self._payload(c) for c in candidates]}

    def update_status(self, principal: Principal, candidate_id: str, status: str) -> dict[str, Any]:
        try: candidate = self._db.activity.update_activity_meeting_candidate_status(candidate_id, status)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        if candidate is None: raise NotFound("activity meeting candidate", candidate_id)
        return {"candidate": self._payload(candidate)}

