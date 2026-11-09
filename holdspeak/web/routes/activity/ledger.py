"""The activity ledger's routes, produced from ``holdspeak/activity_operations.py`` (2026-11-09)."""
from __future__ import annotations

from fastapi import APIRouter

from .... import operations
from ....db import get_database, get_observer
from ....logging_config import get_logger
from ....services.activity_ledger_service import ActivityLedgerService
from ...context import WebContext
from .._produced import envelope, produced

log = get_logger("web.routes.activity")

_WORDS = {
    "activity.status": "Failed to read activity status",
    "activity.records": "Failed to read activity records",
    "activity.refresh": "Failed to refresh activity",
    "activity.settings.update": "Failed to update activity settings",
    "activity.records.delete": "Failed to delete activity records",
}


def build_ledger_router(ctx: WebContext) -> APIRouter:
    rows = [op for op in operations.ACTIVITY_OPERATIONS if op.name in _WORDS]
    return produced(ctx, rows, {name: envelope(log, words) for name, words in _WORDS.items()}, module=__name__,
                    activity_ledger_service=lambda: ActivityLedgerService(get_database(), observer=get_observer()))
