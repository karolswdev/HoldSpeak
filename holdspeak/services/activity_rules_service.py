"""Transport-neutral activity project-rule operations (HS-123-07)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from typing import Any
from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ValidationError


@observe_service
class ActivityRulesService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    @staticmethod
    def _rule(rule: Any) -> dict[str, Any]:
        return {"id": rule.id, "project_id": rule.project_id, "project_name": rule.project_name, "name": rule.name, "enabled": rule.enabled, "priority": rule.priority, "match_type": rule.match_type, "pattern": rule.pattern, "entity_type": rule.entity_type, "created_at": rule.created_at.isoformat(), "updated_at": rule.updated_at.isoformat()}

    @staticmethod
    def _record(record: Any) -> dict[str, Any]:
        return {"id": record.id, "source_browser": record.source_browser, "source_profile": record.source_profile, "url": record.url, "title": record.title, "domain": record.domain, "visit_count": record.visit_count, "first_seen_at": record.first_seen_at.isoformat() if record.first_seen_at else None, "last_seen_at": record.last_seen_at.isoformat() if record.last_seen_at else None, "entity_type": record.entity_type, "entity_id": record.entity_id, "project_id": record.project_id}

    def list(self, principal: Principal, include_disabled: bool = True) -> dict[str, Any]:
        return {"rules": [self._rule(r) for r in self._db.activity.list_activity_project_rules(include_disabled=include_disabled)]}

    def create(self, principal: Principal, fields: dict[str, Any]) -> dict[str, Any]:
        try: rule = self._db.activity.create_activity_project_rule(project_id=fields.get("project_id") or "", name=fields.get("name") or "", match_type=fields.get("match_type") or "", pattern=fields.get("pattern") or "", entity_type=fields.get("entity_type"), priority=fields.get("priority") if fields.get("priority") is not None else 100, enabled=True if fields.get("enabled") is None else fields["enabled"])
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"rule": self._rule(rule)}

    def update(self, principal: Principal, rule_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        try: rule = self._db.activity.update_activity_project_rule(rule_id, **fields)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        if rule is None: raise NotFound("activity project rule", rule_id)
        return {"rule": self._rule(rule)}

    def delete(self, principal: Principal, rule_id: str) -> dict[str, Any]:
        return {"deleted": self._db.activity.delete_activity_project_rule(rule_id)}

    def preview(self, principal: Principal, rule_data: dict[str, Any], records: Any = None) -> dict[str, Any]:
        try: matches = self._db.activity.preview_activity_project_rule(project_id=rule_data.get("project_id") or "", match_type=rule_data.get("match_type") or "", pattern=rule_data.get("pattern") or "", entity_type=rule_data.get("entity_type"), limit=50)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"count": len(matches), "matches": [self._record(r) for r in matches]}

    def apply(self, principal: Principal, limit: int | None) -> dict[str, Any]:
        return {"updated": self._db.activity.apply_activity_project_rules(limit=limit)}
