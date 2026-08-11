"""Voice-lane support: identity, the terminal mic status, and the audio floor (HS-131-09).

Carved out of ``voice.py`` so the route bodies stay the route bodies. Nothing here
holds state; the route module re-imports these names, so a test that patches
``...routes.system.voice._route_principal`` still patches what the routes call.
"""
from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....speech_session import MIC_INTERVAL_CLOSED
from ...context import WebContext

log = get_logger("web.routes.system")


_BROWSER_MIC_OWNER = "browser_mic"


def _resolve_config(ctx: WebContext) -> Any:
    """Load the runtime config for pipeline processing."""
    from ....config import Config
    return Config.load()


def _resolve_server(ctx: WebContext) -> Any:
    """Build a server-like namespace the dictation pipeline can read."""
    from types import SimpleNamespace
    return SimpleNamespace(
        dictation_corrections=ctx.corrections,
        dictation_telemetry=ctx.telemetry,
        dictation_journal=ctx.journal,
    )


def _route_principal(request: Any) -> Any:
    """The AUTHENTICATED identity an open-mic interval is bound to.

    Server-derived, always: a client-supplied principal or parent id never
    reaches admission (the design's recorded note, and the Sol principals
    ruling).
    """
    from ....principals import UNAUTHENTICATED

    return getattr(getattr(request, "state", None), "principal", None) or UNAUTHENTICATED


def _mic_interval_closed(reason: str, detail: str) -> JSONResponse:
    """The ONE terminal status the client honors (Sol Amendment 3).

    A browser interval that hit its inactivity lease, its 30-minute ceiling, its
    child budget, a cancel, or a revocation is CLOSED — the client drops the
    interval and a fresh authenticated click starts a new one. A silently
    replaced parent would let one visible interval cross authority epochs.
    """
    return JSONResponse(
        {
            "success": False,
            "mic_interval": MIC_INTERVAL_CLOSED,
            "reason": str(reason),
            "error": detail,
        },
        status_code=409,
    )


def _claim_browser_audio_floor(ctx: WebContext) -> bool:
    """Claim the audio floor for the browser mic, returning True if granted."""
    session = getattr(ctx, "voice_session", None)
    if session is None:
        return True  # no arbiter -- nothing to contend with
    return session.acquire(_BROWSER_MIC_OWNER, lease_seconds=30.0)


def _release_browser_audio_floor(ctx: WebContext) -> None:
    """Release the browser mic's audio floor claim."""
    session = getattr(ctx, "voice_session", None)
    if session is not None:
        session.release(_BROWSER_MIC_OWNER)
