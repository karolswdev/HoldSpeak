"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/cadence.py``: POST /api/cadence/closeout/apply, GET /api/cadence/loops/{loop_id}, POST /api/cadence/run-now.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _parked_body(router=None, ctx=None, **_):  # parked 2026-11-08: kept at handler indent, never mounted
    @router.post("/closeout/apply")
    def closeout_apply(request: Request, body: dict = Body(default={})) -> dict[str, Any]:
        return service.apply_closeout(principal(request), body)


    @router.get("/loops/{loop_id}")
    async def loop_detail(request: Request, loop_id: str) -> dict[str, Any]:
        try:
            return await service.get_loop(principal(request), loop_id)
        except ServiceError as exc:
            _raise(exc)


    @router.post("/run-now")
    def run_now(request: Request) -> dict[str, Any]:
        return service.run_now(principal(request))
