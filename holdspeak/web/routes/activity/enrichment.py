"""The activity enrichment routes, produced from ``holdspeak/activity_operations.py`` (2026-11-09).

``POST /api/activity/extension/events`` is the browser extension's door (the
loopback permission gate refuses it ``forbidden``: a 403 with ``success: false``).
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....db import get_database, get_observer
from ....logging_config import get_logger
from ....services.activity_enrichment_service import ActivityEnrichmentService
from ....services.errors import ServiceError
from ...context import WebContext
from .._produced import envelope, produced

log = get_logger("web.routes.activity")

_WORDS = {
    "activity.connector.list": "Failed to list activity enrichment connectors",
    "activity.extension.ingest": "Failed to ingest activity extension events",
    "activity.connector.dry_run": "Failed to dry-run activity enrichment connector",
    "activity.briefing": "Failed to fetch activity briefing",
}


def _forbidden_first(answer: Callable[..., Any]) -> Callable[..., Any]:
    """The loopback gate's ``forbidden`` as the route answered it; every other error through *answer*."""

    async def wrapped(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            value = await run_in_threadpool(fn)
        except Exception as exc:
            if isinstance(exc, ServiceError) and exc.code == "forbidden":
                return JSONResponse({"success": False, "error": str(exc), **exc.context}, status_code=403)
            failure = exc

            def again() -> Any:
                raise failure

            return await answer(again, status=status)
        return JSONResponse(value, status_code=status)

    return wrapped


def build_enrichment_router(ctx: WebContext) -> APIRouter:
    rows = [op for op in operations.ACTIVITY_OPERATIONS if op.name in _WORDS]
    answers = {name: _forbidden_first(envelope(log, words)) for name, words in _WORDS.items()}
    return produced(ctx, rows, answers, module=__name__,
                    activity_enrichment_service=lambda: ActivityEnrichmentService(get_database(), observer=get_observer()))
