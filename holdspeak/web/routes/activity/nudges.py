"""The activity nudge routes, produced from ``holdspeak/activity_operations.py`` (2026-11-09)."""
from __future__ import annotations

from fastapi import APIRouter

from .... import operations
from ....db import get_database, get_observer
from ....logging_config import get_logger
from ....services.activity_nudge_service import ActivityNudgeService
from ...context import WebContext
from .._produced import envelope, produced

log = get_logger("web.routes.activity.nudges")

_WORDS = {
    "activity.nudge.list": "Failed to compute activity nudges",
    "activity.nudge.dismiss": "Failed to dismiss activity nudge",
    "activity.nudge.select": "Failed to select activity record for dictation",
}


def build_nudges_router(ctx: WebContext) -> APIRouter:
    rows = [op for op in operations.ACTIVITY_OPERATIONS if op.name in _WORDS]
    return produced(ctx, rows, {name: envelope(log, words) for name, words in _WORDS.items()}, module=__name__,
                    activity_nudge_service=lambda: ActivityNudgeService(get_database(), observer=get_observer()))
