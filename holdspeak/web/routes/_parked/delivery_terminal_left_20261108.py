"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/delivery_terminal.py``: POST /api/delivery/terminal/targets, GET /api/delivery/terminal/commands/{command_id}.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _parked_body(router=None, ctx=None, **_):  # parked 2026-11-08: kept at handler indent, never mounted
    @router.post("/api/delivery/terminal/targets")
    async def api_terminal_target(body: _TargetRequest) -> Any:
        """Issue/refresh the immutable target for a pane ref. The
        response is the ONLY way a client learns a target_id — commands
        and subscriptions never accept a raw pane selector."""
        try:
            issued = await asyncio.to_thread(_targets().issue, body.ref)
        except Exception as exc:
            log.error(f"target issue failure: {exc}")
            return JSONResponse({"error": "terminal_target_failure"}, status_code=500)
        if issued["status"] != "issued":
            status = 404 if issued["status"] == "pane_gone" else 503
            return JSONResponse(issued, status_code=status)
        issued["node_id"] = local_node_id
        return issued


    @router.get("/api/delivery/terminal/commands/{command_id}")
    async def api_terminal_receipt(command_id: str) -> Any:
        try:
            out = await asyncio.to_thread(_service().receipt, command_id)
        except Exception as exc:
            log.error(f"terminal receipt failure: {exc}")
            return JSONResponse(
                {"error": "terminal_receipt_failure"}, status_code=500
            )
        if out is None:
            return JSONResponse(
                {"error": "unknown_command_id"}, status_code=404
            )
        return JSONResponse(out)
