"""The audio floor, read and claimable from the browser — HS-112-06.

The one-at-a-time arbiter (``VoiceTypingSession``) has always governed the
host's own capture: the hotkey, device voice-typing, a meeting's recorder,
the wake listener. The Desk's open mic captures in the BROWSER, on the same
physical machine, and until now it was invisible to that arbiter — a meeting
and an open mic could both hold the microphone and neither would know.

These three routes put the browser on the existing model rather than building
a second one:

* ``GET  /api/dictation/floor``          — who holds it (a lamp, not a lock).
* ``POST /api/dictation/floor/claim``    — claim it as ``open_mic``, on a
  LEASE, so a closed tab cannot wedge the hotkey; re-claiming renews.
* ``POST /api/dictation/floor/release``  — drop it.

A refused claim answers 409 with the active owner NAMED, which is what the
room renders in flow ("FLOOR HELD MEETING"). When no arbiter is wired (a
partial test context) the routes say so — ``arbitrated: false`` — instead of
inventing a floor that does not exist.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ....logging_config import get_logger
from ...context import WebContext

log = get_logger("web.routes.dictation.floor")

#: The browser open mic's name on the floor. One owner, every tab — a second
#: tab claiming while the first holds simply renews the same claim.
OPEN_MIC_OWNER = "open_mic"

#: Lease bounds. The client renews at roughly half the lease it asked for.
DEFAULT_LEASE_SECONDS = 20.0
MAX_LEASE_SECONDS = 120.0


class FloorClaim(BaseModel):
    lease_seconds: Optional[float] = None


def build_floor_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _session() -> Any:
        return getattr(ctx, "voice_session", None)

    def _lease(requested: Optional[float]) -> float:
        if requested is None or requested <= 0:
            return DEFAULT_LEASE_SECONDS
        return min(float(requested), MAX_LEASE_SECONDS)

    @router.get("/api/dictation/floor")
    async def api_audio_floor() -> Any:
        """Who holds the audio floor right now."""
        session = _session()
        if session is None:
            return {"arbitrated": False, "held": False, "owner": None}
        owner = session.active_owner
        return {"arbitrated": True, "held": owner is not None, "owner": owner}

    @router.post("/api/dictation/floor/claim")
    async def api_audio_floor_claim(payload: FloorClaim | None = None) -> Any:
        """Claim the floor for the browser's open mic, on a lease."""
        session = _session()
        lease = _lease(payload.lease_seconds if payload else None)
        if session is None:
            # Nothing to arbitrate against: say so rather than pretend.
            return {"arbitrated": False, "held": True, "owner": OPEN_MIC_OWNER,
                    "lease_seconds": lease}
        if session.acquire(OPEN_MIC_OWNER, lease_seconds=lease):
            return {
                "arbitrated": True,
                "held": True,
                "owner": OPEN_MIC_OWNER,
                "lease_seconds": lease,
            }
        owner = session.active_owner
        log.info("audio_floor_open_mic_refused", extra={"active_owner": owner})
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "refusal": f"floor_held_{owner or 'unknown'}",
                "owner": owner,
                "held": True,
                "arbitrated": True,
            },
        )

    @router.post("/api/dictation/floor/release")
    async def api_audio_floor_release() -> Any:
        """Drop the browser's claim. Safe to call when it holds nothing."""
        session = _session()
        if session is not None:
            session.release(OPEN_MIC_OWNER)
        return {"held": False, "owner": None}

    return router


__all__ = ["build_floor_router", "OPEN_MIC_OWNER", "DEFAULT_LEASE_SECONDS"]
