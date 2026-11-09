"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/dictation/intents.py``: PUT /api/intents/override (ctx.on_set_intent_override stays wired in the runtime).
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _parked_body(router=None, ctx=None, **_):  # parked 2026-11-08: kept at handler indent, never mounted
    @router.put("/api/intents/override")
    def api_set_intent_override(payload: _IntentOverrideRequest) -> Any:
        if ctx.on_set_intent_override is None:
            return JSONResponse(
                {"success": False, "error": "Intent override updates not supported"},
                status_code=501,
            )
        try:
            result = ctx.on_set_intent_override(payload.intents)
        except Exception as e:
            log.error(f"on_set_intent_override failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if isinstance(result, dict):
            ctx.broadcast("intent_controls_updated", result)
        return JSONResponse({"success": True, "controls": result})
