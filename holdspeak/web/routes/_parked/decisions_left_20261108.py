"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/decisions.py``: POST /api/decisions/{decision_id}/reject.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _parked_body(router=None, ctx=None, **_):  # parked 2026-11-08: kept at handler indent, never mounted
    @router.post("/{decision_id}/reject")
    def reject_decision(decision_id: str,request: Request) -> Any:
        try: return JSONResponse(service().transition(_principal(request),decision_id,"reject",{}))
        except ServiceError as exc: return _error(exc)
