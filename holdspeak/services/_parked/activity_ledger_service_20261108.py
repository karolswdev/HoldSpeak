"""PARKED 20261108 (subtraction day, Lane R): service methods only a parked route called.

Parked from ``holdspeak/services/activity_ledger_service.py`` ``ActivityLedgerService``: delete_domain_rule, upsert_domain_rule.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Transport-neutral activity ledger operations (HS-123-07)."""
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from typing import Any
from ...db.core import Database
from ...principals import Principal
from ..errors import ValidationError


@observe_service
class ParkedActivityLedgerService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def upsert_domain_rule(self, principal: Principal, domain: str, rule: str) -> dict[str, Any]:
        try: value = self._db.activity.upsert_activity_domain_rule(domain=domain, action=rule)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"rule": value, "status": self.status(principal)}

    def delete_domain_rule(self, principal: Principal, domain: str) -> dict[str, Any]:
        return {"deleted": self._db.activity.delete_activity_domain_rule(domain), "status": self.status(principal)}

