"""Agent-context + agent-hook routes — HS-34-01 split of `dictation.py`.

`/api/dictation/project-context`, `/api/dictation/agent-hooks`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ._helpers import _resolve_project_context

log = get_logger("web.routes.dictation")


def build_agent_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/dictation/project-context")
    def api_dictation_project_context(project_root: Optional[str] = None) -> Any:
        """Validate and describe the active/manual dictation project root."""
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        root = Path(project["root"])
        return JSONResponse(
            {
                "project": project,
                "paths": {
                    "blocks": str(root / ".holdspeak" / "blocks.yaml"),
                    "project_kb": str(root / ".holdspeak" / "project.yaml"),
                },
            }
        )

    @router.get("/api/dictation/agent-hooks")
    def api_dictation_agent_hooks(capture_messages: bool = True) -> Any:
        """Return copy-ready Claude/Codex hook templates and recent status."""
        from ....agent_context import (
            AGENT_CONTEXT_FILE,
            claude_hook_template,
            codex_hook_template,
            get_recent_agent_session,
        )
        from ....agent_summarizer import summarizer_provider_statuses

        templates = {
            "claude": claude_hook_template(capture_messages=capture_messages),
            "codex": codex_hook_template(capture_messages=capture_messages),
        }
        agents: dict[str, dict[str, Any]] = {}
        for agent, template in templates.items():
            latest = get_recent_agent_session(agent=agent, max_age_seconds=7 * 24 * 60 * 60)
            agents[agent] = {
                "latest_session": latest.to_dict() if latest else None,
                "template": template,
                "template_json": json.dumps(template, indent=2, sort_keys=True),
            }
        return JSONResponse(
            {
                "capture_messages": capture_messages,
                "registry_path": str(AGENT_CONTEXT_FILE),
                "destinations": {
                    "claude": "~/.claude/settings.json or project .claude/settings.json",
                    "codex": "~/.codex/hooks.json or project .codex/hooks.json",
                },
                "summarizers": summarizer_provider_statuses(),
                "agents": agents,
            }
        )

    return router
