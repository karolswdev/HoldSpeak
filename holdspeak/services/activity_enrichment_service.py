"""Transport-neutral activity enrichment operations (HS-123-07)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from typing import Any
from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ServiceError


@observe_service
class ActivityEnrichmentService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    @staticmethod
    def _connector(c: Any) -> dict[str, Any]:
        return {"id": c.id, "enabled": c.enabled, "settings": c.settings, "last_run_at": c.last_run_at.isoformat() if c.last_run_at else None, "last_error": c.last_error, "created_at": c.created_at.isoformat(), "updated_at": c.updated_at.isoformat()}

    def list_connectors(self, principal: Principal) -> dict[str, Any]:
        from ..activity_connectors import enrichment_descriptors
        from ..activity_github import github_cli_status
        from ..activity_jira import jira_cli_status
        connectors = []
        for d in enrichment_descriptors():
            state = self._db.activity.get_activity_enrichment_connector(d.id) or self._db.activity.upsert_activity_enrichment_connector(connector_id=d.id)
            row = self._connector(state); row.update(label=d.label, kind=d.kind, capabilities=list(d.capabilities), requires_cli=d.requires_cli, description=d.description, source=d.source)
            if (status := d.cli_status()) is not None: row["cli_status"] = status
            connectors.append(row)
        return {"connectors": connectors, "github": github_cli_status(), "jira": jira_cli_status()}

    def ingest_extension_events(self, principal: Principal, events: list[Any]) -> dict[str, Any]:
        from ..activity_extension import ingest_extension_events
        from ..connector_packs import firefox_ext
        from ..connector_runtime import PermissionDenied, PermissionGate
        try: PermissionGate(firefox_ext.MANIFEST).accept_loopback_event()
        except PermissionDenied as exc: raise ServiceError("forbidden", str(exc)) from exc
        return ingest_extension_events(self._db, events).to_payload()

    def dry_run(self, principal: Principal, connector_id: str, limit: int) -> dict[str, Any]:
        from ..activity_connector_preview import MAX_LIMIT, UnknownConnectorError, dry_run
        try: clean = max(1, min(int(limit), MAX_LIMIT))
        except (TypeError, ValueError): clean = 25
        try: result = dry_run(self._db, connector_id, limit=clean)
        except UnknownConnectorError as exc: raise NotFound("activity enrichment connector", connector_id) from exc
        return {"dry_run": result.to_payload()}

    def briefing(self, principal: Principal) -> dict[str, Any]:
        anns = self._db.activity.list_activity_annotations(source_connector_id="meeting_context", annotation_type="meeting_context_briefing", limit=20); b = anns[0] if anns else None
        runs = self._db.activity.list_connector_runs(connector_id="meeting_context", limit=1); r = runs[0] if runs else None
        return {"briefing": {"id": b.id, "title": b.title, "value": b.value, "updated_at": b.updated_at.isoformat()} if b else None, "last_run": r.to_payload() if r else None}

