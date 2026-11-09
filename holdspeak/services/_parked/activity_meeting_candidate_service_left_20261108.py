"""PARKED 20261108 (late evening, the left-routes pass): service methods only a parked route called.

Parked from ``holdspeak/services/activity_meeting_candidate_service.py``: ActivityMeetingCandidateService.create, .delete.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


class _ParkedBody:  # parked 2026-11-08: kept at method indent, never imported
    def create(self, principal: Principal, fields: dict[str, Any]) -> dict[str, Any]:
        from ..timestamps import parse_iso_datetime as _parse_iso_datetime
        try: candidate = self._db.activity.create_activity_meeting_candidate(source_connector_id=fields.get("source_connector_id") or "calendar_activity", source_activity_record_id=fields.get("source_activity_record_id"), title=fields.get("title") or "", starts_at=_parse_iso_datetime(fields.get("starts_at")), ends_at=_parse_iso_datetime(fields.get("ends_at")), meeting_url=fields.get("meeting_url"), confidence=fields.get("confidence") if fields.get("confidence") is not None else 0.0, status=fields.get("status") or "candidate")
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"candidate": self._payload(candidate)}


    def delete(self, principal: Principal, source_connector_id: str | None, status: str | None) -> dict[str, Any]:
        try: deleted = self._db.activity.delete_activity_meeting_candidates(source_connector_id=source_connector_id, status=status)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"deleted": deleted}
