"""Mesh discovery routes (HSM-15-10).

A single lightweight, **unauthenticated** identify endpoint: ``GET /api/mesh/info``.
A companion that has just discovered this server on the LAN (via Bonjour) needs
to confirm WHO it found and whether pairing will need a token — and it must do so
*before* it has the token. So this endpoint is deliberately reachable without
auth (the server's off-loopback auth gate exempts it) and returns only
non-sensitive identity: ``{name, version, requiresToken}``. It NEVER returns the
token or any secret.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..context import WebContext

# The off-loopback auth gate in `MeetingWebServer._create_app` exempts this path
# so a not-yet-paired companion can identify the server before it has a token.
MESH_INFO_PATH = "/api/mesh/info"


def build_mesh_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get(MESH_INFO_PATH)
    async def api_mesh_info() -> Any:
        """Identify this server to a freshly-discovered (unpaired) companion.

        Returns ONLY non-sensitive identity. No token, no secrets.
        """
        from ... import __version__
        from ...config import Config
        from ...mesh import resolve_device_name

        try:
            configured = Config.load().mesh.device_name
        except Exception:
            configured = ""
        return JSONResponse(
            {
                "name": resolve_device_name(configured),
                "version": __version__,
                "requiresToken": bool(ctx.mesh_requires_token),
            }
        )

    return router
