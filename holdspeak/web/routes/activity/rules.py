"""The activity project-rule routes, produced from ``holdspeak/activity_operations.py`` (2026-11-09)."""
from __future__ import annotations

from fastapi import APIRouter

from .... import operations
from ....db import get_database, get_observer
from ....logging_config import get_logger
from ....services.activity_rules_service import ActivityRulesService
from ...context import WebContext
from .._produced import envelope, produced

log = get_logger("web.routes.activity")

_WORDS = {
    "activity.rule.list": "Failed to list activity project rules",
    "activity.rule.delete": "Failed to delete activity project rule",
}


def build_rules_router(ctx: WebContext) -> APIRouter:
    rows = [op for op in operations.ACTIVITY_OPERATIONS if op.name in _WORDS]
    return produced(ctx, rows, {name: envelope(log, words) for name, words in _WORDS.items()}, module=__name__,
                    activity_rules_service=lambda: ActivityRulesService(get_database(), observer=get_observer()))
