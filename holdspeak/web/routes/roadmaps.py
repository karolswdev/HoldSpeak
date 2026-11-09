"""Read-only Delivery Workbench roadmap routes (HS-113-07), produced from their declared rows (2026-11-09).

The reads live in ``services/roadmap_service.py`` (with the process cache
and the background rebuild) and are declared in
``holdspeak/repository_operations.py``.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from ...logging_config import get_logger
from ...repository_operations import ROADMAP_OPERATIONS
from ...services.roadmap_service import RoadmapService
from ..context import WebContext
from ._produced import envelope, produced

log = get_logger("web.routes.roadmaps")


def build_roadmaps_router(ctx: WebContext, *, repo_root: Path | None = None) -> APIRouter:
    """The read-only roadmap API. ``repo_root`` is a test seam: a context the hub did not compose
    reads that checkout; the hub's routes reach its composed service (this checkout)."""
    roadmaps = RoadmapService(repo_root=repo_root)
    answer = envelope(log, "Failed to read the roadmaps", not_found=lambda exc: {"error": "Roadmap not found"})
    return produced(ctx, ROADMAP_OPERATIONS, answer, module=__name__, roadmap_service=lambda: roadmaps)
