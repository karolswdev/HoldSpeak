"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/scheduled_recordings.py``: GET /api/scheduled-recordings/{schedule_id}.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _parked_body(router=None, ctx=None, **_):  # parked 2026-11-08: kept at handler indent, never mounted
    @router.get("/{schedule_id}")
    def get_schedule(request: Request, schedule_id: str) -> Any:
        try:
            result = _service().get_schedule(_principal(request), schedule_id)
            return JSONResponse({"success": True, "schedule": result})
        except (NotFound, ValidationError, ConflictError) as exc:
            return _error_response(exc)
        except Exception as exc:
            return _error_response(exc)
