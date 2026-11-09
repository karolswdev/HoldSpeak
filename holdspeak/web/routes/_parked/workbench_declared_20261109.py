"""PARKED 20261109 (ops/programs-work): two hand-written workbench routes, now produced.

GET /api/automations/prepared and POST /api/workbenches/{id}/items/{item_id}/restore
are rows in ``holdspeak/automation_operations.py`` (automation.prepared.read,
automation.item.restore): each produces its route (same method, path, status and
answer) and its MCP tool. Kept here as they stood in
``web/routes/primitives/workbenches.py``.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
    @router.get("/api/automations/prepared")
    def api_prepared_for_today(request: Request) -> Any:
        """Betterment daily D9: Today's Prepared block (the newest result of an
        automation whose Put it in is Today) and the automation Prepare now
        runs. Each is null when there is none."""
        try:
            return JSONResponse(_svc().prepared_for_today(_principal(request)))
        except Exception as exc:
            return error_500(exc, log, "Failed to read the prepared day")

    @router.post("/api/workbenches/{workbench_id}/items/{item_id}/restore")
    def api_restore_item(workbench_id: str, item_id: str, request: Request) -> Any:
        try:
            item = _svc().restore_item(_principal(request), workbench_id, item_id)
            return JSONResponse({"item": item})
        except NotFound:
            return _not_found("item", item_id)
        except ConflictError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to restore Workbench item")

'''
