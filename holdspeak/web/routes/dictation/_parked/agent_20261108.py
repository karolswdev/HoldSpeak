"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/dictation/agent.py``: GET /api/dictation/agent-context, POST /api/dictation/agent-context/clear, POST /api/dictation/agent-context/summarize.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Agent-context + agent-hook routes — HS-34-01 split of `dictation.py`.

`/api/dictation/project-context`, `/api/dictation/agent-context*`,
`/api/dictation/agent-hooks`.
"""


from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .....agent_context.models import DEFAULT_RECENT_MAX_AGE_SECONDS
from .....logging_config import get_logger
from ....context import WebContext
from .._helpers import _resolve_project_context

log = get_logger("web.routes.dictation")


def parked_build_agent_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/dictation/agent-context")
    def api_dictation_agent_context(project_root: Optional[str] = None) -> Any:
        """Return the latest captured agent question for the selected project."""
        from .....agent_context import get_recent_awaiting_agent_session

        project: dict[str, Any] | None = None
        project_error: str | None = None
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            if project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project_error = str(exc)

        session = (
            get_recent_awaiting_agent_session(project_root=project["root"], max_age_seconds=DEFAULT_RECENT_MAX_AGE_SECONDS)
            if project
            else None
        )
        return JSONResponse(
            {
                "project": project,
                "project_error": project_error,
                "session": session.to_dict() if session else None,
                "awaiting_response": bool(session and session.awaiting_response),
                "max_age_seconds": DEFAULT_RECENT_MAX_AGE_SECONDS,
            }
        )

    @router.post("/api/dictation/agent-context/clear")
    def api_dictation_agent_context_clear(
        payload: Optional[dict[str, Any]] = None,
        project_root: Optional[str] = None,
    ) -> Any:
        """Clear the captured assistant text shown by the Dictation page."""
        from .....agent_context import clear_agent_session_response

        body = payload if isinstance(payload, dict) else {}
        body_project_root = body.get("project_root")
        effective_project_root = project_root or (body_project_root if isinstance(body_project_root, str) else None)
        try:
            project = _resolve_project_context(effective_project_root)
        except ValueError as exc:
            if effective_project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project = None

        session = clear_agent_session_response(
            agent=body.get("agent") if isinstance(body.get("agent"), str) else None,
            session_id=body.get("session_id") if isinstance(body.get("session_id"), str) else None,
            project_root=project["root"] if project else None,
            max_age_seconds=DEFAULT_RECENT_MAX_AGE_SECONDS,
        )
        return JSONResponse(
            {
                "cleared": session is not None,
                "session": session.to_dict() if session else None,
            }
        )

    @router.post("/api/dictation/agent-context/summarize")
    def api_dictation_agent_context_summarize(
        payload: Optional[dict[str, Any]] = None,
        project_root: Optional[str] = None,
    ) -> Any:
        """Generate and persist a bounded external-agent context summary."""
        from .....agent_context import (
            get_recent_awaiting_agent_session,
            set_agent_session_summary,
        )
        from .....agent_summarizer import summarize_agent_session

        body = payload if isinstance(payload, dict) else {}
        provider = str(body.get("provider") or "").strip().lower()
        if provider not in {"codex", "claude"}:
            return JSONResponse(
                {"error": "provider must be one of: codex, claude"},
                status_code=400,
            )
        body_project_root = body.get("project_root")
        effective_project_root = project_root or (body_project_root if isinstance(body_project_root, str) else None)
        try:
            project = _resolve_project_context(effective_project_root)
        except ValueError as exc:
            if effective_project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project = None

        session = get_recent_awaiting_agent_session(
            project_root=project["root"] if project else None,
            agent=body.get("agent") if isinstance(body.get("agent"), str) else None,
            max_age_seconds=DEFAULT_RECENT_MAX_AGE_SECONDS,
        )
        if session is None:
            return JSONResponse(
                {"error": "no recent captured agent message is awaiting a response"},
                status_code=404,
            )
        try:
            summary = summarize_agent_session(
                session,
                provider=provider,  # type: ignore[arg-type]
                timeout_seconds=float(body.get("timeout_seconds") or 20.0),
            )
        except FileNotFoundError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=502)

        updated = set_agent_session_summary(
            agent=session.agent,
            session_id=session.session_id,
            summary=summary.to_dict(),
        )
        return JSONResponse(
            {
                "summary": summary.to_dict(),
                "session": updated.to_dict() if updated else None,
            }
        )

    return router
