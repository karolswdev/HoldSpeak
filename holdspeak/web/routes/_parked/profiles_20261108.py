"""PARKED 20261108 (evening, the unreached-routes census): routes no client calls.

Parked from ``holdspeak/web/routes/primitives/profiles.py``: POST /api/profiles, DELETE /api/profiles/{profile_id}, PUT /api/profiles/{profile_id}.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Runtime profiles CRUD (the key never rides the wire).

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.profile_service import ProfileService
from ....services.errors import ServiceError, ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body

log = get_logger("web.routes.primitives")




def parked_build_profiles_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.post("/api/profiles")
    def api_create_profile(request: Request) -> Any:
        return _profiles_read_only()

    @router.put("/api/profiles/{profile_id}")
    def api_update_profile(profile_id: str, request: Request) -> Any:
        return _profiles_read_only()

    @router.delete("/api/profiles/{profile_id}")
    def api_delete_profile(profile_id: str) -> Any:
        return _profiles_read_only()

    # HS-134-02: GET /api/profiles retired — the target contract is the only
    # read shape; writes were already rejected (HS-112-01).
    # `/api/inference-targets` is the one write path.
    def _profiles_read_only() -> JSONResponse:
        return JSONResponse(
            {
                "error": "/api/profiles is read-only; write via /api/inference-targets",
                "write_path": "/api/inference-targets",
            },
            status_code=405,
        )

    return router
