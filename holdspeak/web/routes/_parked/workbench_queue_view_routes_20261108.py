"""PARKED 20261108 (queue view park): the routes only the old queue view called.

Owner ruling 2026-11-08: every automation run is a Program (#2032/#2033); the
item-queue runner is parked, so the queue view (WorkbenchWindow, behind RAW) is
parked with it (web/src/desk/_parked/automations/WorkbenchWindow_20261108.tsx).
Its routes had no other caller (hub, MCP, web, apple/):

- POST   /api/workbenches/{workbench_id}/items/park
- POST   /api/workbenches/{workbench_id}/items/restore
- POST   /api/workbenches/{workbench_id}/items/{item_id}/retry-mint
- POST   /api/workbenches/{workbench_id}/voice/resolve
- GET    /api/skills
- DELETE /api/workbenches/{workbench_id}/memory
- POST   /api/workbenches/{workbench_id}/memory/{index}/promote
  (all from holdspeak/web/routes/primitives/workbenches.py, inside
  build_workbenches_router)
- GET    /workbenches/{workbench_id}/resourceful/history
  (from holdspeak/web/routes/automations.py, inside
  build_automations_router; mounted under /api)

Their service methods are parked in
holdspeak/services/_parked/workbench_queue_view_ops_20261108.py.
WorkbenchService.resolve_voice and ResourcefulService.history stay:
kernel placement and resourceful tests drive them directly.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
    @router.post("/api/workbenches/{workbench_id}/items/park")
    async def api_park_items(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _svc().park_items(
                _principal(request), workbench_id, body.get("item_ids")
            )
            return JSONResponse(result)
        except NotFound as exc:
            return _not_found(exc.kind, exc.id)
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ConflictError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except Exception as exc:
            return error_500(exc, log, "Failed to park Workbench items")

    @router.post("/api/workbenches/{workbench_id}/items/restore")
    async def api_restore_items(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _svc().restore_items(
                _principal(request), workbench_id, body.get("item_ids")
            )
            return JSONResponse(result)
        except NotFound as exc:
            return _not_found(exc.kind, exc.id)
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ConflictError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except Exception as exc:
            return error_500(exc, log, "Failed to restore Workbench items")

    @router.post("/api/workbenches/{workbench_id}/items/{item_id}/retry-mint")
    def api_retry_mint(workbench_id: str, item_id: str, request: Request) -> Any:
        try:
            result = _svc().retry_mint(_principal(request), workbench_id, item_id)
            return JSONResponse({"artifact_id": result["artifact_id"]}, status_code=201 if result["created"] else 200)
        except NotFound:
            return _not_found("item", item_id)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to retry mint")

    @router.post("/api/workbenches/{workbench_id}/voice/resolve")
    async def api_voice_resolve(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _svc().resolve_voice(
                _principal(request), workbench_id, str(body.get("transcript") or "").strip(),
                str(body.get("request_id") or ""),
            )
            return JSONResponse(result)
        except NotFound:
            return _not_found("automation", workbench_id)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to resolve voice references")

    @router.get("/api/skills")
    def api_list_skills(request: Request, recipe_id: str | None = None) -> Any:
        try:
            return JSONResponse({"skills": _svc().list_skills(_principal(request), recipe_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list skills")

    @router.delete("/api/workbenches/{workbench_id}/memory")
    def api_clear_memory(workbench_id: str, request: Request) -> Any:
        try:
            _svc().clear_memory(_principal(request), workbench_id)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to clear memory")

    @router.post("/api/workbenches/{workbench_id}/memory/{index}/promote")
    def api_promote_memory(workbench_id: str, index: int, request: Request) -> Any:
        try:
            skill = _svc().promote_memory(_principal(request), workbench_id, index)
            return JSONResponse({"skill": skill}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to promote memory to skill")

    # holdspeak/web/routes/automations.py
    @router.get("/workbenches/{workbench_id}/resourceful/history")
    def resourceful_history(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"history": resourceful.history(
                principal(request), workbench_id,
            )})
        except ServiceError as exc:
            return _error(exc)
'''
