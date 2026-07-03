"""Device and runtime health reads.

Bodies moved verbatim from routes/system.py (HS-79-02, the Phase-63 discipline).
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.system")
from ._shared import _normalize_runtime_status_payload


def build_health_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/devices/health")
    async def api_devices_health() -> Any:
        from ....meeting_session import _device_descriptor_to_dict

        devices = [
            _device_descriptor_to_dict(descriptor)
            for descriptor in ctx.device_registry.active()
        ]
        return JSONResponse({"devices": devices})

    @router.get("/api/runtime/status")
    async def api_runtime_status() -> Any:
        try:
            state = ctx.get_state() or {}
        except Exception as e:
            log.error(f"get_state failed: {e}")
            state = {}

        if ctx.on_get_status is not None:
            try:
                raw_payload = ctx.on_get_status()
            except Exception as e:
                log.error(f"on_get_status failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            if isinstance(raw_payload, dict):
                return JSONResponse(_normalize_runtime_status_payload(raw_payload, state))
            return JSONResponse({"status": "ok", "runtime_status": raw_payload})

        return JSONResponse(_normalize_runtime_status_payload({}, state))


    return router
