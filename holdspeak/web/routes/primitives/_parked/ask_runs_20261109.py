# PARKED 2026-11-09: AskService owns the retained-run projection.
class _ParkedBody:
        @router.get("/api/ask/runs")
        def api_ask_runs(request: Request) -> Any:
            # Ask hub gap 5: the asks a window left running, by invocation id.
            from ....services.ask_service import runs
            ids=[part for part in str(request.query_params.get("ids") or "").split(",") if part.strip()][:20]
            return JSONResponse({"runs":runs(ids)})
