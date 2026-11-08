"""PARKED 20261108 (subtraction day, Lane R): service methods only a parked route called.

Parked from ``holdspeak/services/activity_rules_service.py`` ``ActivityRulesService``: apply.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Transport-neutral activity project-rule operations (HS-123-07)."""
from holdspeak.services.observer import NullObserver, PipelineObserver
from typing import Any
from ...db.core import Database
from ...principals import Principal


class ParkedActivityRulesService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def apply(self, principal: Principal, limit: int | None) -> dict[str, Any]:
        return {"updated": self._db.activity.apply_activity_project_rules(limit=limit)}
