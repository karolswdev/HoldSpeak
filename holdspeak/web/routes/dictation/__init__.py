"""Dictation / agent-hook / intent-control routes (HS-26-03; sub-split HS-34-01).

The dictation pipeline cluster moved off `MeetingWebServer._create_app` in Phase
26 as one 1,607-line `build_dictation_router(ctx)`. HS-34-01 split that single
factory into a `routes/dictation/` sub-package by domain — each
`build_*_router(ctx)` here registers absolute `/api/...` paths, and this
`__init__` composes them via `include_router`, so the **full route table is
identical** and `build_dictation_router` stays the public entry point
(`routes/__init__.py` imports it unchanged).

Domains:
- `intents`       — `/api/intents/*`
- `agent`         — `/api/dictation/project-context`, `agent-context*`, `agent-hooks`
- `project_docs`  — `/api/dictation/project-hs`, `project-doc-suggestion*`
- `blocks`        — `/api/dictation/block-templates`, `blocks*`
- `kb`            — `/api/dictation/project-kb*`
- `pipeline`      — `/api/dictation/readiness`, `dry-run`

`project_docs`, `blocks`, and `pipeline` share one in-memory project-doc-suggestion
store (a dry-run detects a suggestion; the project-doc-suggestion GET reads it).
That store is created here, once per router build (per app), and passed to the
groups that touch it — preserving the original closure-scoped lifetime.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...context import WebContext
from .agent import build_agent_router
from .blocks import build_blocks_router
from .intents import build_intents_router
from .kb import build_kb_router
from .pipeline import build_pipeline_router
from .project_docs import build_project_docs_router

__all__ = ["build_dictation_router"]


def build_dictation_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    # Shared per-app store: dry-run / from-template detect suggestions, the
    # project-doc-suggestion routes read + clear them.
    project_doc_suggestions: dict[str, dict[str, str]] = {}

    router.include_router(build_intents_router(ctx))
    router.include_router(build_agent_router(ctx))
    router.include_router(build_project_docs_router(ctx, project_doc_suggestions))
    router.include_router(build_blocks_router(ctx, project_doc_suggestions))
    router.include_router(build_kb_router(ctx))
    router.include_router(build_pipeline_router(ctx, project_doc_suggestions))

    return router
