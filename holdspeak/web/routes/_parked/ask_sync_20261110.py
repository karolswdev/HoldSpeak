# PARKED: synchronous Ask adapters are produced from their existing tool operations.
class _ParkedBody:
    @router.post("/api/grounding/resolve")
    async def api_resolve_grounding(request: Request) -> Any:
        body=await _json_body(request)
        if body is None: return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try: return JSONResponse(service().resolve_grounding(principal(request),body.get("refs") if isinstance(body.get("refs"),list) else []))
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to resolve grounding")
    @router.post("/api/ask/keep")
    async def api_ask_keep(request: Request) -> Any:
        body=await _json_body(request)
        if body is None: return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:
            result=service().keep(principal(request),str(body.get("output") or ""),body.get("context") if isinstance(body.get("context"),list) else [],lens=str(body.get("lens") or "Ask"),prompt=str(body.get("prompt") or ""),grounding=body.get("grounding"))
            return JSONResponse(result,status_code=201)
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to keep ask")
    @router.post("/api/ask/{invocation_id}/cancel")
    def api_cancel_ask(invocation_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service().cancel(principal(request), invocation_id))
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to cancel ask")
