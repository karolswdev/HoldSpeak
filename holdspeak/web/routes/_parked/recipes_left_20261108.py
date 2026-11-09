"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/primitives/recipes.py``: GET /api/recipes/{recipe_id} (RecipeService.get_recipe stays: MCP recipe.get and the recipe resource read it), POST /api/recipes/{recipe_id}/chat (the thread alias), POST /api/recipes/{recipe_id}/invocations/{invocation_id}/cancel.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _parked_body(router=None, ctx=None, **_):  # parked 2026-11-08: kept at handler indent, never mounted
    @router.get("/api/recipes/{recipe_id}")
    def api_get_recipe(recipe_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"recipe": _svc().get_recipe(_principal(request), recipe_id)})
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get recipe")


    @router.post("/api/recipes/{recipe_id}/chat")
    async def api_chat_recipe(recipe_id: str, request: Request) -> Any:
        # HS-151-04: recipe.chat is now an alias that creates/reuses a thread
        # bound to this recipe and starts a turn with the body's text.
        from .._thread_factory import thread_service_from_ctx
        from ....db import get_database
        body = await _json_body(request) or {}
        text = str(body.get("text") or body.get("question") or "")
        if not text.strip():
            return JSONResponse({"error": "text is required"}, status_code=400)
        db = get_database()
        thread_svc = thread_service_from_ctx(ctx)
        # Reuse newest non-deleted thread with this recipe_id, or create one.
        existing = [t for t in db.threads.list(limit=50) if t.recipe_id == recipe_id]
        if existing:
            thread_id = existing[0].id
        else:
            created = thread_svc.create(recipe_id=recipe_id, title=recipe_id)
            thread_id = created["id"]
        try:
            result = await thread_svc.start_turn(
                _principal(request), thread_id, text,
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to chat via recipe alias")



    @router.post("/api/recipes/{recipe_id}/invocations/{invocation_id}/cancel")
    def api_cancel_recipe_invocation(recipe_id: str, invocation_id: str, request: Request) -> Any:
        try:
            return JSONResponse(_svc().cancel(_principal(request), invocation_id))
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to cancel recipe invocation")
