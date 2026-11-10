# PARKED 2026-11-09: Ask reads are produced from their declared operations.
class _ParkedBody:
        @router.get("/api/models")
        def api_list_models(request: Request) -> Any:
            try: return JSONResponse({"models":service().list_models(principal(request))})
            except Exception as exc: return error_500(exc,log,"Failed to list models")
        @router.get("/api/ask/engine")
        async def api_ask_engine(request: Request) -> Any:
            # Betterment Q7: can the Answers engine use the desk's tools? The
            # Ask window's engine line says so.
            try:
                import asyncio
                return JSONResponse(await asyncio.to_thread(service().engine_tools))
            except Exception as exc: return error_500(exc,log,"Failed to read the Answers engine")
