"""Dictation / agent-hook / intent-control routes (HS-26-03; sub-split HS-34-01).

The dictation pipeline cluster moved off `MeetingWebServer._create_app` in Phase
26 as one 1,607-line `build_dictation_router(ctx)`. HS-34-01 split that single
factory into a `routes/dictation/` sub-package by domain — each
`build_*_router(ctx)` here registers absolute `/api/...` paths, and this
`__init__` composes them via `include_router`, so the **full route table is
identical** and `build_dictation_router` stays the public entry point
(`routes/__init__.py` imports it unchanged).

All HTTP verbs come from DictationService's declared rows. The pipeline and
block adapters hold request cancellation/fresh-session callbacks; services own
their jobs and the shared suggestion state supplied here. The socket is separate.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...context import WebContext
from .._mount import mount_router
from ._declared import build_declared_router
from .blocks import build_blocks_router
from .intents import build_intents_router
from .pipeline import build_pipeline_router

__all__ = ["build_dictation_router"]


def build_dictation_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    # Shared per-app store: dry-run / from-template detect suggestions, the
    # project-doc-suggestion routes read + clear them.
    project_doc_suggestions: dict[str, dict[str, str]] = {}
    # HS-39-04: session set of dismissed-suggestion signatures so a dismissed
    # suggestion doesn't re-surface for a near-duplicate utterance.
    dismissed_suggestion_signatures: set[str] = set()

    mount_router(router, build_intents_router(ctx))
    mount_router(router, build_declared_router(ctx, (
        "dictation.readiness", "dictation.project_context", "dictation.agent_hooks", "dictation.project_hs.get",
        "dictation.project_hs.put", "dictation.block_templates", "dictation.blocks.list",
        "dictation.blocks.create",
    )))
    mount_router(router, build_blocks_router(ctx, project_doc_suggestions))
    mount_router(router, build_declared_router(ctx, (
        "dictation.blocks.update", "dictation.blocks.delete", "dictation.project_kb.get",
        "dictation.project_kb.put", "dictation.project_kb.start",
        # HS-112-06: the audio floor, claimable by the browser's open mic.
        "dictation.floor.claim", "dictation.floor.release",
    )))
    mount_router(router,
        build_pipeline_router(ctx, project_doc_suggestions, dismissed_suggestion_signatures)
    )
    mount_router(router, build_declared_router(ctx, (
        "dictation.corrections.list", "dictation.learning_digest", "dictation.corrections.add",
        "dictation.corrections.remove", "dictation.list", "dictation.journal.update",
        "dictation.journal.delete", "dictation.journal.clear", "dictation.journal.correct",
    )))

    return router
