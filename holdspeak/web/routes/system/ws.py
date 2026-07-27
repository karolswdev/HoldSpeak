"""The one /ws socket per page (the runtime bus endpoint).

Bodies moved verbatim from routes/system.py (HS-79-02, the Phase-63 discipline).
"""
from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ....logging_config import get_logger
from ...context import WebContext

log = get_logger("web.routes.system")


def build_ws_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        from .... import web_auth
        from ....principals import (
            Principal,
            PrincipalKind,
            PrincipalRight,
            UNAUTHENTICATED,
            agent_credentials,
            derive_owner,
        )

        # Native clients can send the same bearer/header auth as HTTP;
        # browsers use the encoded subprotocol because WebSocket() cannot
        # set request headers. Neither path places a credential in the URL.
        provided = web_auth.extract_request_token(
            authorization=websocket.headers.get("authorization"),
            header_token=websocket.headers.get("x-holdspeak-token"),
        ) or web_auth.extract_websocket_token(
            websocket.headers.get("sec-websocket-protocol")
        )
        principal = derive_owner(provided, ctx.web_auth_token)
        if principal is None:
            principal = agent_credentials.derive(provided)
        if principal is None:
            node_token = websocket.headers.get("x-holdspeak-node-token")
            node_store = getattr(websocket.app.state, "node_token_store", None)
            node_id = node_store.principal_identity(node_token) if node_store else None
            if node_id:
                principal = Principal(PrincipalKind.NODE, node_id)
        principal = principal or UNAUTHENTICATED
        websocket.state.principal = principal
        if not principal.permits(PrincipalRight.OWNER):
            reason = f"principal={principal.name} missing_right={PrincipalRight.OWNER.value}"
            log.warning(f"Rejected WebSocket: {reason}")
            await websocket.close(code=1008, reason=reason)
            return

        offered = {
            item.strip()
            for item in str(websocket.headers.get("sec-websocket-protocol") or "").split(",")
        }
        selected_protocol = (
            web_auth.WEBSOCKET_PROTOCOL
            if web_auth.WEBSOCKET_PROTOCOL in offered
            else None
        )
        log.info("WebSocket connection attempt")
        try:
            await ctx.ws.connect(websocket, subprotocol=selected_protocol)
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
