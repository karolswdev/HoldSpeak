"""Transport-neutral activity project-rule operations (HS-123-07)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from typing import Any
from ..db.core import Database
from ..principals import Principal


@observe_service
class ActivityRulesService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    @staticmethod
    def _rule(rule: Any) -> dict[str, Any]:
        return {"id": rule.id, "project_id": rule.project_id, "project_name": rule.project_name, "name": rule.name, "enabled": rule.enabled, "priority": rule.priority, "match_type": rule.match_type, "pattern": rule.pattern, "entity_type": rule.entity_type, "created_at": rule.created_at.isoformat(), "updated_at": rule.updated_at.isoformat()}

    def list(self, principal: Principal, include_disabled: bool = True) -> dict[str, Any]:
        return {"rules": [self._rule(r) for r in self._db.activity.list_activity_project_rules(include_disabled=include_disabled)]}

    def delete(self, principal: Principal, rule_id: str) -> dict[str, Any]:
        return {"deleted": self._db.activity.delete_activity_project_rule(rule_id)}
