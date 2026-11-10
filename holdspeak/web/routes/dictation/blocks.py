"""The template HTTP transport; creation and preview are one declared service job."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....services.errors import ServiceError
from ...context import WebContext
from ...operation_routes import operation_router, _principal
from ._declared import registry_for, _answer
from ._helpers import _run_cancellable_entry


def build_blocks_router(
    ctx: WebContext, project_doc_suggestions: dict[str, dict[str, str]]
) -> APIRouter:
    registry = registry_for(ctx)

    async def api_dictation_blocks_create_from_template(
        request: Request,
        payload: dict[str, Any],
        scope: str = "global",
        project_root: Optional[str] = None,
    ) -> Any:
        async def run_entry(aim: str, work: Any) -> Any:
            return await _run_cancellable_entry(request, aim, work)

        try:
            body, status = await registry().invoke(
                _principal(request),
                "dictation.blocks.from_template",
                {"payload": payload, "scope": scope, "project_root": project_root},
                held={
                    "project_doc_suggestions": project_doc_suggestions,
                    "run_entry": run_entry,
                },
            )
            return JSONResponse(body, status_code=status)
        except ServiceError as exc:
            return JSONResponse(
                exc.context.get("body") or {"error": exc.detail, "code": exc.code},
                status_code=int(exc.context.get("status") or 400),
            )
        except operations.OperationRefused as exc:
            return JSONResponse(
                {"error": exc.detail, "code": exc.code}, status_code=400
            )

    return operation_router(
        [
            d
            for d in operations.DICTATION_OPERATIONS
            if d.name == "dictation.blocks.from_template"
        ],
        registry,
        _answer,
        module=__name__,
        hand_written={
            "dictation.blocks.from_template": lambda d: api_dictation_blocks_create_from_template
        },
    )
