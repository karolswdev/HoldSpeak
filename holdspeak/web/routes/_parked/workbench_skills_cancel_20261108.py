"""PARKED 20261108 (workbench fold): four workbench routes no live face calls.

- POST   /api/workbenches/{workbench_id}/runs/{parent_operation_id}/cancel
- POST   /api/skills
- PUT    /api/skills/{skill_id}
- DELETE /api/skills/{skill_id}

The web had no caller of the cancel or POST/DELETE skill routes; its one
``updateSkill`` caller was a parked test (web/src/_parked/desk/components/
__tests__/workbenchSkillsGuard.test.ts). Their service methods are parked in
``holdspeak/services/_parked/workbench_skill_writers_20261108.py``. They
stood in ``holdspeak/web/routes/primitives/workbenches.py``, inside
``build_workbenches_router``.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
    @router.post("/api/workbenches/{workbench_id}/runs/{parent_operation_id}/cancel")
    def api_cancel_workbench_run(workbench_id: str, parent_operation_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"disposition": _svc().cancel_run(_principal(request), parent_operation_id)})
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to cancel automation run")

    @router.post("/api/skills")
    async def api_create_skill(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            skill = _svc().create_skill(
                _principal(request), title=str(body.get("title") or ""), body=str(body.get("body", "")),
                **{k: v for k, v in body.items() if k not in {"title", "body"}},
            )
            return JSONResponse({"skill": skill}, status_code=201)
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create skill")

    @router.put("/api/skills/{skill_id}")
    async def api_update_skill(skill_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse({"skill": _svc().update_skill(_principal(request), skill_id, **body)})
        except NotFound:
            return _not_found("skill", skill_id)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update skill")

    @router.delete("/api/skills/{skill_id}")
    def api_delete_skill(skill_id: str, request: Request) -> Any:
        try:
            _svc().delete_skill(_principal(request), skill_id)
            return JSONResponse({"success": True})
        except NotFound:
            return _not_found("skill", skill_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete skill")

'''
