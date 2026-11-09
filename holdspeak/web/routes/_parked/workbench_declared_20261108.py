"""PARKED 20261108 (automation operations): the hand-written bodies of nine
Automations routes, now produced from ``holdspeak/automation_operations.py``.

- PUT    /api/workbenches/{workbench_id}/when                   automation.set_when
- PUT    /api/workbenches/{workbench_id}/engine                 automation.set_engine
- POST   /api/workbenches/{workbench_id}/make-one               automation.make_one
- GET    /api/workbench-templates                               automation.template.list
- POST   /api/workbench-templates/{template_id}/instantiate     automation.template.instantiate
- POST   /api/workbenches/{workbench_id}/results/{artifact_id}/open  automation.result.open
- GET    /api/automations/new                                   automation.new.list
- GET    /api/workbenches/{workbench_id}/memory                 automation.lesson.list
- DELETE /api/workbenches/{workbench_id}/memory/{index}         automation.lesson.forget

The same paths, methods and answers are served by the produced routes in
``holdspeak/web/routes/primitives/workbenches.py`` (one row makes the route and
the MCP tool). They stood inside ``build_workbenches_router``.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
    @router.get("/api/automations/new")
    def api_new_results(request: Request) -> Any:
        """Betterment A6: one row per automation with a NEW result."""
        try:
            rows = _svc().new_results(_principal(request))
            return JSONResponse({"automations": rows, "new_count": sum(r["new_count"] for r in rows)})
        except Exception as exc:
            return error_500(exc, log, "Failed to read new automation results")

    def _a4_error(exc: ServiceError) -> JSONResponse:
        """A When or With refusal, in its own words and status."""
        status = int(exc.context.get("status") or 0)
        if not status:
            status = 400 if isinstance(exc, ValidationError) else 409 if isinstance(exc, ConflictError) else 502
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=status)

    @router.put("/api/workbenches/{workbench_id}/when")
    async def api_set_workbench_when(workbench_id: str, request: Request) -> Any:
        """Betterment A4: one When choice (schedule, event or manual)."""
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            wb = _svc().set_when(_principal(request), workbench_id, body)
            return JSONResponse({"workbench": wb})
        except NotFound:
            return _not_found("automation", workbench_id)
        except ServiceError as exc:
            return _a4_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to change when the automation runs")

    @router.put("/api/workbenches/{workbench_id}/engine")
    async def api_set_workbench_engine(workbench_id: str, request: Request) -> Any:
        """Betterment A4: With (the engine, and the Spend limit per run)."""
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            wb = _svc().set_engine(_principal(request), workbench_id, **body)
            return JSONResponse({"workbench": wb})
        except NotFound:
            return _not_found("automation", workbench_id)
        except ServiceError as exc:
            return _a4_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to choose the automation's engine")

    @router.post("/api/workbenches/{workbench_id}/results/{artifact_id}/open")
    def api_open_result(workbench_id: str, artifact_id: str, request: Request) -> Any:
        """Betterment A2: opening a result reads it (``new`` becomes ``read``)."""
        try:
            return JSONResponse({"result": _svc().open_result(_principal(request), workbench_id, artifact_id)})
        except NotFound:
            return _not_found("result", artifact_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to open the result")

    @router.post("/api/workbenches/{workbench_id}/make-one")
    def api_make_one_automation(workbench_id: str, request: Request) -> Any:
        """Betterment A9: an old queue automation takes its agent's prompt as Do."""
        try:
            return JSONResponse({"workbench": _svc().make_one_automation(_principal(request), workbench_id)})
        except NotFound:
            return _not_found("workbench", workbench_id)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to make this one automation")

    @router.get("/api/workbench-templates")
    def api_list_templates(request: Request) -> Any:
        try:
            return JSONResponse({"templates": _svc().list_templates(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list templates")

    @router.post("/api/workbench-templates/{template_id}/instantiate")
    async def api_instantiate_template(template_id: str, request: Request) -> Any:
        body = await _json_body(request) or {}
        try:
            result = _svc().instantiate_template(_principal(request), template_id, body.get("profile_id") or None)
            return JSONResponse(result, status_code=201)
        except NotFound:
            return _not_found("template", template_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to instantiate template")

    @router.get("/api/workbenches/{workbench_id}/memory")
    def api_list_memory(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"entries": _svc().list_memory(_principal(request), workbench_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to read memory")

    @router.delete("/api/workbenches/{workbench_id}/memory/{index}")
    def api_forget_memory(workbench_id: str, index: int, request: Request, at: str = "") -> Any:
        """Betterment A3: Forget one lesson; ``at`` is its timestamp."""
        try:
            _svc().forget_memory(_principal(request), workbench_id, index, at)
            return JSONResponse({"success": True})
        except NotFound:
            return _not_found("lesson", str(index))
        except Exception as exc:
            return error_500(exc, log, "Failed to forget the lesson")
'''
