"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/decision_records.py``: POST /api/decision-records/{record_id}/supersede, POST /api/decision-records/{record_id}/dispute (the service methods stay: tests seed the recall chain through them).
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _parked_body(router=None, ctx=None, **_):  # parked 2026-11-08: kept at handler indent, never mounted
    # ── HS-200-13: the lifecycle verbs the recall chain needs ──────────

    @router.post("/{record_id}/supersede")
    def supersede_record(
        record_id: str, request: Request, body: dict[str, Any] = Body(default={}),
    ) -> Any:
        """Seal ``record_id`` and name ``successor_id`` as what is current now."""
        try:
            return service().supersede(
                principal(request), record_id,
                str(body.get("successor_id") or ""), body.get("reason"),
            )
        except RightRequired as exc:
            return JSONResponse(exc.response, status_code=403)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"decision record not found: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/{record_id}/dispute")
    def dispute_record(
        record_id: str, request: Request, body: dict[str, Any] = Body(default={}),
    ) -> Any:
        """Mark a record DISPUTED (discoverable, never presented as current)."""
        try:
            return service().dispute(principal(request), record_id, body.get("reason"))
        except RightRequired as exc:
            return JSONResponse(exc.response, status_code=403)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"decision record not found: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
