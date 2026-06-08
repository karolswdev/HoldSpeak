"""Activity / connector / plugin-job routes (HS-26-04; sub-split HS-34-02).

The activity-intelligence cluster moved off `MeetingWebServer._create_app` in
Phase 26 as one 1,319-line / 38-handler `build_activity_router(ctx)`. HS-34-02
split that single factory into a `routes/activity/` sub-package by domain — each
`build_*_router(ctx)` registers absolute `/api/...` paths, and this `__init__`
composes them via `include_router`, so the **full route table is identical** and
`build_activity_router` stays the public entry point (`routes/__init__.py` imports
it unchanged).

Domains:
- `ledger`       — `/api/activity/status`, `records`, `refresh`, `settings`, `domains`
- `rules`        — `/api/activity/project-rules*`
- `enrichment`   — `/api/activity/enrichment/*`, `extension/events`, `annotations`, `briefing`
- `candidates`   — `/api/activity/meeting-candidates*`
- `plugin_jobs`  — `/api/plugin-jobs*`

Each group's payload shapers are used only within that group (no shared state), so
they live with their handlers. The only cross-cutting helpers
(`_meeting_callback_payload`, `_parse_iso_datetime`, `error_500`) come from the
neutral `web/runtime_support` module — no route module imports `web_server`.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...context import WebContext
from .candidates import build_candidates_router
from .enrichment import build_enrichment_router
from .ledger import build_ledger_router
from .nudges import build_nudges_router
from .plugin_jobs import build_plugin_jobs_router
from .rules import build_rules_router

__all__ = ["build_activity_router"]


def build_activity_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    router.include_router(build_ledger_router(ctx))
    router.include_router(build_rules_router(ctx))
    router.include_router(build_enrichment_router(ctx))
    router.include_router(build_candidates_router(ctx))
    router.include_router(build_plugin_jobs_router(ctx))
    router.include_router(build_nudges_router(ctx))
    return router
