# PARKED 2026-11-09: The queue summary and process routes are produced from their operations.
class _ParkedBody:
        @router.get("/api/intel/summary")
        def api_intel_queue_summary(request: Request) -> Any:
            try: return JSONResponse(_svc(ctx).queue_summary(_principal(request)))
            except Exception as exc: return _error(exc, "Failed to load intel queue summary")
        @router.post("/api/intel/process")
        def api_process_intel_jobs(request: Request, payload: Optional[_IntelProcessRequest] = None) -> Any:
            try:
                body = payload.model_dump() if payload is not None else {}
                return JSONResponse(_svc(ctx).process_jobs(_principal(request), body))
            except Exception as exc: return _error(exc, "Failed to process intel jobs")
