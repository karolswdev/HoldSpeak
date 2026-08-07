"""Audited coder-session factory route registration."""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse


def register_factory_routes(router: APIRouter) -> None:
    """Attach the independent spawn and rename endpoints to ``router``."""

    @router.post("/api/coders/factory/spawn")
    async def api_factory_spawn(payload: Optional[dict[str, Any]] = None) -> Any:
        from .... import coder_factory

        body = payload if isinstance(payload, dict) else {}
        name = str(body.get("name", "")).strip()
        command = body.get("command")
        result = await asyncio.to_thread(
            coder_factory.spawn, name, command=(str(command) if command else None)
        )
        code = 200 if result["status"] == "spawned" else 409
        return JSONResponse(result, status_code=code)

    @router.post("/api/coders/factory/rename")
    async def api_factory_rename(payload: Optional[dict[str, Any]] = None) -> Any:
        from .... import coder_factory

        body = payload if isinstance(payload, dict) else {}
        target = str(body.get("target", "")).strip()
        new_name = str(body.get("name", "")).strip()
        if not target:
            return JSONResponse({"error": "target is required"}, status_code=400)
        result = await asyncio.to_thread(coder_factory.rename, target, new_name)
        code = 200 if result["status"] == "renamed" else 409
        return JSONResponse(result, status_code=code)
