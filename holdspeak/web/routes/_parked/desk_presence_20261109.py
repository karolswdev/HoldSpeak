# Parked 2026-11-09: presence is a declared HTTP-only Desk service operation.
from __future__ import annotations
class _ParkedBody:
    @router.post("/api/desk/presence")
    async def desk_presence(request: Request) -> Any:
        """Betterment daily D8: the window in front of the owner (memory only).
        The heartbeat raises no notice about the window he is looking at."""
        from ... import desk_presence

        try:
            body = await request.json()
        except Exception:
            body = {}
        body = body if isinstance(body, dict) else {}
        front = body.get("front")
        desk_presence.report(str(front)[:200] if front else None, bool(body.get("visible")))
        if body.get("visible"):
            # PG-IMPORT IMP3: the edge of his visits, on disk (Today's "Since
            # you were last here"); off the loop, and never a failed report.
            def keep() -> None:
                try:
                    from ...db import get_database
                    from ...services.last_here import touch

                    touch(get_database())
                except Exception as exc:
                    log.debug(f"presence not kept: {exc}")

            await run_in_threadpool(keep)
        return {"ok": True}
