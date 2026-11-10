"""Owner-local Desk UI feedback routes.

Produced from ``holdspeak/feedback_operations.py`` (2026-11-09), served by
``services/ui_feedback.FeedbackService``: the switch's read, the save and the
transcription. The save and the transcription are owner only. A refusal
answers ``{success: false, error}``: 404 while feedback is off or for an
unknown bundle, 400 for a bad payload, 409 for a reused id, 403 for anyone
but the owner.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....feedback_operations import FEEDBACK_OPERATIONS
from ....logging_config import get_logger
from ....operations import OperationRefused
from ....services.errors import ServiceError
from ....services.ui_feedback import FeedbackRefused, UIFeedbackConflict, UIFeedbackError
from ...operation_routes import operation_router
from .._mount import mount_router

log = get_logger("web.routes.system")


def _refused(error: str, status: int) -> JSONResponse:
    return JSONResponse({"success": False, "error": error}, status_code=status)


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except FeedbackRefused as exc:
        return _refused(str(exc), exc.status)
    except UIFeedbackConflict as exc:
        return _refused(str(exc), 409)
    except UIFeedbackError as exc:
        return _refused(str(exc), 400)
    except OperationRefused as exc:
        return _refused(exc.detail, 400)
    except ServiceError as exc:  # owner_required (403)
        return _refused(exc.detail, int((exc.context or {}).get("status") or 400))
    except Exception as exc:  # pragma: no cover - filesystem-specific failures
        log.exception("Failed to save local UI feedback: %s", exc)
        return _refused("The local feedback bundle could not be saved.", 500)


def build_ui_feedback_router(ctx: Any) -> APIRouter:
    router = APIRouter()

    def registry() -> Any:
        from ....services.ui_feedback import FeedbackService

        return operations.for_context(ctx, feedback_service=lambda: FeedbackService(ctx))

    mount_router(router, operation_router(FEEDBACK_OPERATIONS, registry, _answer, module=__name__))
    return router


__all__ = ["build_ui_feedback_router"]
