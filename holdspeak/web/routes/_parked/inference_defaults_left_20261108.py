"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/inference_assignments.py``: GET /api/inference/defaults, POST /api/inference/defaults/use-proposal (the face that read them, web/src/desk/firstrun/Found.tsx, is parked).
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


    # Owner ruling 2026-10-05: the batteries-included default.  One read says,
    # per capability, assigned / inherited_from_default / proposed /
    # needs_setup; one press ("Use it") assigns a proposed network or cloud
    # engine.  No face yet.
    @router.get("/api/inference/defaults")
    async def get_defaults(request: Request) -> Any:
        try:
            _owner(request)
            defaults = ctx.inference_default_service
            if defaults is None:
                return JSONResponse(
                    {"code": "inference_defaults_unavailable", "message": "Defaults are not available."},
                    status_code=503,
                )
            return await run_in_threadpool(defaults.state, request.state.principal)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read defaults")

    @router.post("/api/inference/defaults/use-proposal")
    async def use_proposal(request: Request) -> Any:
        try:
            body = await _json(request)
            if set(body) != {"proposal_id"} or not isinstance(body.get("proposal_id"), str):
                raise ServiceError(
                    "inference_default_request_invalid", "Use it has an invalid request shape.", context={"status": 400}
                )
            defaults = ctx.inference_default_service
            if defaults is None:
                return JSONResponse(
                    {"code": "inference_defaults_unavailable", "message": "Defaults are not available."},
                    status_code=503,
                )
            return defaults.use_proposal(request.state.principal, body["proposal_id"])
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to use the proposed default")
