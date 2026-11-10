# Parked 2026-11-09: the Desk callback is declared in desk_operations, mounted by desk_windows.
from __future__ import annotations
class _ParkedBody:
    @router.post("/api/desk/needs-you/seen")
    def api_desk_needs_you_seen(request: Request, body: dict[str, Any] = Body(default={})) -> Any:
        """Betterment D3: he has seen these meetings' promises kept on
        arrival; they leave the NEW group (they stay in the list)."""
        try:
            ids = body.get("meeting_ids")
            if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
                return JSONResponse({"success": False, "error": "meeting_ids is a list of meeting ids"}, status_code=400)
            from holdspeak.services.needs_you_membership import mark_arrivals_seen

            return JSONResponse({"success": True, "seen": mark_arrivals_seen(_get_db(), ids)})
        except Exception as exc:
            return error_500(exc, log, "Failed to mark arrivals seen")
