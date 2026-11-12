# Parked: proposal confirm and dismiss now use declared operations.
class _ParkedBody:
    @router.post("/api/proposals/{proposal_id}/confirm")
    def api_confirm_proposal(
        proposal_id: str,
        request: Request,
        body: dict[str, Any] = Body(default={}),
    ) -> Any:
        try:
            result = _service(ctx).confirm_proposal(
                _principal(request),
                proposal_id,
                text=body.get("text"),
                owner=body.get("owner"),
                due=body.get("due"),
            )
            if "error" in result:
                return JSONResponse({"success": False, **result}, status_code=_status(result))
            return JSONResponse({"success": True, **result})
        except Exception as exc:
            return error_500(exc, log, "Failed to confirm proposal")

    @router.post("/api/proposals/{proposal_id}/dismiss")
    def api_dismiss_proposal(
        proposal_id: str,
        request: Request,
    ) -> Any:
        try:
            result = _service(ctx).dismiss_proposal(_principal(request), proposal_id)
            if "error" in result:
                return JSONResponse({"success": False, **result}, status_code=_status(result))
            return JSONResponse({"success": True, **result})
        except Exception as exc:
            return error_500(exc, log, "Failed to dismiss proposal")
