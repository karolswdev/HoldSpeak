"""Transport-neutral activity ledger operations (HS-123-07)."""
from __future__ import annotations
from typing import Any
from ..db.core import Database
from ..principals import Principal
from .errors import ValidationError


class ActivityLedgerService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def status(self, principal: Principal) -> dict[str, Any]:
        from ..activity_history import discover_browser_history_sources
        settings = self._db.activity.get_activity_privacy_settings()
        return {"settings": settings, "sources": [{"source_browser": s.source_browser, "source_profile": s.source_profile, "source_path_hash": s.source_path_hash, "readable": s.path.is_file(), "enabled": bool(s.enabled and settings["enabled"])} for s in discover_browser_history_sources()], "checkpoints": [{"source_browser": c.source_browser, "source_profile": c.source_profile, "source_path_hash": c.source_path_hash, "last_visit_raw": c.last_visit_raw, "last_imported_at": c.last_imported_at.isoformat() if c.last_imported_at else None, "last_error": c.last_error, "enabled": c.enabled} for c in self._db.activity.list_activity_import_checkpoints()], "domain_rules": self._db.activity.list_activity_domain_rules(), "record_count": len(self._db.activity.list_activity_records(limit=5000))}

    def list_records(self, principal: Principal, project_id: str | None, domain: str | None, entity_type: str | None, limit: int) -> dict[str, Any]:
        from ..activity_context import build_activity_context
        bundle = build_activity_context(db=self._db, project_id=project_id, limit=limit, refresh=False).to_dict()
        records = bundle["records"]
        if domain: records = [r for r in records if r.get("domain") == domain.strip().lower()]
        if entity_type: records = [r for r in records if r.get("entity_type") == entity_type.strip().lower()]
        bundle["records"] = records
        return bundle

    def refresh(self, principal: Principal) -> dict[str, Any]:
        from ..activity_history import import_browser_history
        results = import_browser_history(db=self._db)
        return {"results": [{"source_browser": r.source_browser, "source_profile": r.source_profile, "source_path_hash": r.source_path_hash, "imported_count": r.imported_count, "checkpoint_raw": r.checkpoint_raw, "enabled": r.enabled, "error": r.error} for r in results], "status": self.status(principal)}

    def update_settings(self, principal: Principal, settings: dict[str, Any]) -> dict[str, Any]:
        result = self._db.activity.update_activity_privacy_settings(enabled=settings["enabled"], retention_days=settings["retention_days"])
        return {"settings": result, "status": self.status(principal)}

    def upsert_domain_rule(self, principal: Principal, domain: str, rule: str) -> dict[str, Any]:
        try: value = self._db.activity.upsert_activity_domain_rule(domain=domain, action=rule)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"rule": value, "status": self.status(principal)}

    def delete_domain_rule(self, principal: Principal, domain: str) -> dict[str, Any]:
        return {"deleted": self._db.activity.delete_activity_domain_rule(domain), "status": self.status(principal)}

    def delete_records(self, principal: Principal, domain: str | None, project_id: str | None) -> dict[str, Any]:
        return {"deleted": self._db.activity.delete_activity_records(domain=domain, project_id=project_id), "status": self.status(principal)}
