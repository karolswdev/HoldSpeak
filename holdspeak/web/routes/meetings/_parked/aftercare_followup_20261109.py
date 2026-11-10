# PARKED 2026-11-09: The follow-up read is produced from its operation.
class _ParkedBody:
        @router.get("/api/meetings/{meeting_id}/followup-draft")
        def api_get_meeting_followup_draft(meeting_id: str, request: Request) -> Any:
            try: return JSONResponse(_svc(ctx).get_followup_draft(_principal(request), meeting_id))
            except Exception as exc: return _error(exc, "Failed to build meeting follow-up draft")
