"""Dictation HTTP transports; the declared service owns each speech job."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....services.errors import ServiceError
from ...context import WebContext
from ...operation_routes import operation_router, _principal
from ._declared import registry_for, _answer
from ._helpers import _run_cancellable_entry, _open_text_entry
from ....services.dictation_readiness import _target_override_options  # noqa: F401
from ....services.dictation_jobs import PRE_EFFECT_REFUSALS, _routed_from_stages  # noqa: F401
from ....services.dictation_pipeline import _run_dictation_dry_run_text  # noqa: F401


def build_pipeline_router(
    ctx: WebContext,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
) -> APIRouter:
    registry = registry_for(ctx)

    async def run(request: Request, name: str, args: dict[str, Any]) -> Any:
        async def run_entry(aim: str, work: Any) -> Any:
            return await _run_cancellable_entry(request, aim, work)

        def open_entry(aim: str, **kwargs: Any) -> Any:
            return _open_text_entry(request, aim, **kwargs)

        held = {
            "project_doc_suggestions": project_doc_suggestions,
            "dismissed_signatures": dismissed_signatures,
            "open_entry" if name == "dictation.remote" else "run_entry": open_entry
            if name == "dictation.remote"
            else run_entry,
        }
        try:
            body, status = await registry().invoke(
                _principal(request), name, args, held=held
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

    async def api_dictation_dry_run(request: Request, payload: dict[str, Any]) -> Any:
        return await run(request, "dictation.rehearse", {"payload": payload})

    async def api_dictation_remote(request: Request, payload: dict[str, Any]) -> Any:
        return await run(request, "dictation.remote", {"payload": payload})

    async def api_dictation_journal_replay(request: Request, entry_id: int) -> Any:
        return await run(
            request, "dictation.journal.replay", {"entry_id": int(entry_id)}
        )

    handlers = {
        "dictation.rehearse": api_dictation_dry_run,
        "dictation.remote": api_dictation_remote,
        "dictation.journal.replay": api_dictation_journal_replay,
    }
    return operation_router(
        [d for d in operations.DICTATION_OPERATIONS if d.name in handlers],
        registry,
        _answer,
        module=__name__,
        hand_written={
            name: lambda d, handler=handler: handler
            for name, handler in handlers.items()
        },
    )
