# PARKED 2026-11-09: The issue proposal is produced from its operation.
class _ParkedBody:
        @router.post("/api/meetings/{meeting_id}/aftercare/file-issue")
        def api_aftercare_file_issue(meeting_id: str, payload: _AftercareFileIssueRequest, request: Request) -> Any:
            try: return JSONResponse(_svc(ctx).file_issue(_principal(request), meeting_id, payload.model_dump()))
            except Exception as exc: return _error(exc, "Failed to file aftercare issue")
