"""The one /ws socket per page (the runtime bus endpoint).

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


def build_ws_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        log.info(f"WebSocket connection attempt from {websocket.client}")
        try:
            await ctx.ws.connect(websocket)
            log.info("WebSocket connected successfully")
        except Exception as e:
            log.error(f"WebSocket connect failed: {e}", exc_info=True)
            return

        try:
            # Optional initial state push via REST endpoint; for WS we at
            # least emit current duration immediately if available.
            duration = ctx.current_formatted_duration()
            if duration is not None:
                await websocket.send_json({"type": "duration", "data": duration})

            while True:
                # Keep connection alive; ignore client messages for now.
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
                elif message.startswith("{"):
                    # Accept JSON no-op messages without error.
                    try:
                        json.loads(message)
                    except Exception:
                        pass
        except WebSocketDisconnect:
            pass
        except Exception as e:
            log.debug(f"WebSocket error: {e}")
        finally:
            await ctx.ws.disconnect(websocket)


    return router
