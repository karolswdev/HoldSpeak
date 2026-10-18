"""Remote-node steering relay route registration (HS-89-03).

A configured remote node owns its tmux authority and authoritative audit;
this hub only relays its typed success or refusal.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse


def register_relay_routes(router: APIRouter) -> None:
    """Attach the relay peek, arm, disarm, steer and keys endpoints to ``router``."""

    async def _relay(
        node: str, verb: str, key: str, *, method: str = "POST", body: Any = None
    ):
        from .... import coder_steering_relay

        result = await asyncio.to_thread(
            coder_steering_relay.relay, node, verb, key, method=method, body=body
        )
        return JSONResponse(
            result, status_code=coder_steering_relay.relay_http_code(result)
        )

    @router.get("/api/coders/relay/{node}/peek")
    async def api_relay_peek(
        node: str, key: str, lines: int = 200, last_hash: Optional[str] = None, raw: int = 0
    ) -> Any:
        verb = f"peek?lines={lines}" + (f"&last_hash={last_hash}" if last_hash else "")
        return await _relay(node, verb + ("&raw=1" if raw else ""), key, method="GET")

    @router.post("/api/coders/relay/{node}/arm")
    async def api_relay_arm(node: str, payload: Optional[dict[str, Any]] = None) -> Any:
        body = payload if isinstance(payload, dict) else {}
        key = str(body.get("key", "")).strip()
        if not key:
            return JSONResponse({"error": "key is required"}, status_code=400)
        ttl = {"ttl_seconds": body["ttl_seconds"]} if "ttl_seconds" in body else {}
        return await _relay(node, "arm", key, body=ttl)

    @router.post("/api/coders/relay/{node}/disarm")
    async def api_relay_disarm(
        node: str, payload: Optional[dict[str, Any]] = None
    ) -> Any:
        body = payload if isinstance(payload, dict) else {}
        key = str(body.get("key", "")).strip()
        if not key:
            return JSONResponse({"error": "key is required"}, status_code=400)
        return await _relay(node, "disarm", key, body={})

    @router.post("/api/coders/relay/{node}/steer")
    async def api_relay_steer(
        node: str, payload: Optional[dict[str, Any]] = None
    ) -> Any:
        body = payload if isinstance(payload, dict) else {}
        key = str(body.get("key", "")).strip()
        if not key:
            return JSONResponse({"error": "key is required"}, status_code=400)
        forwarded = {k: v for k, v in body.items() if k != "key"}
        return await _relay(node, "steer", key, body=forwarded)

    @router.post("/api/coders/relay/{node}/keys")
    async def api_relay_keys(
        node: str, payload: Optional[dict[str, Any]] = None
    ) -> Any:
        body = payload if isinstance(payload, dict) else {}
        key = str(body.get("key", "")).strip()
        if not key:
            return JSONResponse({"error": "key is required"}, status_code=400)
        forwarded = {item: value for item, value in body.items() if item != "key"}
        return await _relay(node, "keys", key, body=forwarded)
