"""PARKED 20261109 (ops/programs-work): the hand-written recipe writes and Keep.

POST /api/recipes, PUT and DELETE /api/recipes/{recipe_id} are rows in
``holdspeak/recipe_operations.py`` (recipe.create, recipe.update,
recipe.delete): each produces its route (same method, path, status and
answer) and its MCP tool. POST /api/recipes/{recipe_id}/keep had no caller in
``web/src`` (the chat it kept a reply of is a thread now); RecipeService.keep
stays for its own tests. Kept here as they stood in
``web/routes/primitives/recipes.py``.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
    @router.post("/api/recipes")
    async def api_create_recipe(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            fields = dict(body)
            recipe_id = str(fields.pop("id", "") or fields.pop("recipe_id", "") or "") or None
            recipe = _svc().create_recipe(
                _principal(request), recipe_id=recipe_id, **fields
            )
            return JSONResponse({"recipe": recipe}, status_code=201)
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create recipe")

    @router.put("/api/recipes/{recipe_id}")
    async def api_update_recipe(recipe_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse({
                "recipe": _svc().update_recipe(_principal(request), recipe_id, **body)
            })
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update recipe")

    @router.delete("/api/recipes/{recipe_id}")
    def api_delete_recipe(recipe_id: str, request: Request) -> Any:
        try:
            _svc().delete_recipe(_principal(request), recipe_id)
            return JSONResponse({"success": True})
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete recipe")

    @router.post("/api/recipes/{recipe_id}/keep")
    async def api_keep_recipe_reply(recipe_id: str, request: Request) -> Any:
        body = await _json_body(request) or {}
        try:
            result = _svc().keep(
                _principal(request), recipe_id,
                output=str(body.get("output") or ""), input=str(body.get("question") or ""),
                sources=body.get("sources") if isinstance(body.get("sources"), list) else None,
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to keep chat reply")

'''
