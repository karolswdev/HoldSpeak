"""Transport-neutral activity enrichment operations (HS-123-07)."""
from __future__ import annotations
from typing import Any
from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ValidationError, ServiceError


class ActivityEnrichmentService:
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _connector(c: Any) -> dict[str, Any]:
        return {"id": c.id, "enabled": c.enabled, "settings": c.settings, "last_run_at": c.last_run_at.isoformat() if c.last_run_at else None, "last_error": c.last_error, "created_at": c.created_at.isoformat(), "updated_at": c.updated_at.isoformat()}

    def _descriptor(self, connector_id: str) -> Any:
        from ..activity_connectors import get_descriptor
        descriptor = get_descriptor(connector_id)
        if descriptor is None: raise NotFound("activity enrichment connector", connector_id)
        return descriptor

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

    def update_connector(self, principal: Principal, connector_id: str, settings: dict[str, Any]) -> dict[str, Any]:
        from ..activity_connectors import KNOWN_CONNECTOR_IDS
        if connector_id not in KNOWN_CONNECTOR_IDS: raise NotFound("activity enrichment connector", connector_id)
        descriptor = self._descriptor(connector_id)
        config = settings.get("settings")
        if config:
            allowed = descriptor.manifest.setting_keys(); unknown = sorted(set(config) - allowed)
            if unknown: raise ValidationError(f"Connector {connector_id!r} does not declare setting key(s): {unknown}. Allowed: {sorted(allowed)}.")
        try: connector = self._db.activity.upsert_activity_enrichment_connector(connector_id=connector_id, enabled=settings.get("enabled"), settings=config)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"connector": self._connector(connector)}

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

    def clear_annotations(self, principal: Principal, connector_id: str) -> dict[str, Any]:
        d = self._descriptor(connector_id)
        if "annotations" not in d.capabilities: raise ValidationError(f"Connector {connector_id} does not produce annotations")
        return {"deleted": int(self._db.activity.delete_activity_annotations(source_connector_id=connector_id)), "connector_id": connector_id, "runs_deleted": int(self._db.activity.delete_connector_runs(connector_id=connector_id))}

    def clear_candidates(self, principal: Principal, connector_id: str) -> dict[str, Any]:
        d = self._descriptor(connector_id)
        if "candidates" not in d.capabilities: raise ValidationError(f"Connector {connector_id} does not produce candidates")
        return {"deleted": int(self._db.activity.delete_activity_meeting_candidates(source_connector_id=connector_id)), "connector_id": connector_id, "runs_deleted": int(self._db.activity.delete_connector_runs(connector_id=connector_id))}

    def list_annotations(self, principal: Principal, source_connector_id: str | None, annotation_type: str | None, activity_record_id: int | None, limit: int) -> dict[str, Any]:
        try: clean = max(1, min(int(limit), 500))
        except (TypeError, ValueError): clean = 100
        anns = self._db.activity.list_activity_annotations(source_connector_id=source_connector_id, annotation_type=annotation_type, activity_record_id=activity_record_id, limit=clean)
        return {"annotations": [{"id": a.id, "activity_record_id": a.activity_record_id, "source_connector_id": a.source_connector_id, "annotation_type": a.annotation_type, "title": a.title, "value": a.value, "confidence": a.confidence, "created_at": a.created_at.isoformat(), "updated_at": a.updated_at.isoformat()} for a in anns]}

    def briefing(self, principal: Principal) -> dict[str, Any]:
        anns = self._db.activity.list_activity_annotations(source_connector_id="meeting_context", annotation_type="meeting_context_briefing", limit=20); b = anns[0] if anns else None
        runs = self._db.activity.list_connector_runs(connector_id="meeting_context", limit=1); r = runs[0] if runs else None
        return {"briefing": {"id": b.id, "title": b.title, "value": b.value, "updated_at": b.updated_at.isoformat()} if b else None, "last_run": r.to_payload() if r else None}

    def run_pipeline(self, principal: Principal, pipeline_id: str) -> dict[str, Any]:
        from ..connector_runtime import NotAPipelineError, PipelineRunner, UnknownPipelineError
        d = self._descriptor(pipeline_id)
        if d.manifest.kind != "pipeline": raise ValidationError(f"Connector {pipeline_id!r} is kind={d.manifest.kind!r}, not a pipeline")
        try: result = PipelineRunner(self._db, principal=principal).run(pipeline_id)
        except UnknownPipelineError as exc: raise NotFound("pipeline", pipeline_id) from exc
        except NotAPipelineError as exc: raise ValidationError(str(exc)) from exc
        return {"result": result.to_payload()}

    def list_runs(self, principal: Principal, connector_id: str, limit: int) -> dict[str, Any]:
        self._descriptor(connector_id)
        try: clean = max(1, min(int(limit), 200))
        except (TypeError, ValueError): clean = 10
        return {"connector_id": connector_id, "runs": [r.to_payload() for r in self._db.activity.list_connector_runs(connector_id=connector_id, limit=clean)]}

    def preview_github(self, principal: Principal, limit: int) -> dict[str, Any]:
        from ..activity_github import CONNECTOR_ID, preview_github_cli_enrichment
        c = self._db.activity.get_activity_enrichment_connector(CONNECTOR_ID) or self._db.activity.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
        result = preview_github_cli_enrichment(self._db.activity.list_activity_records(limit=max(1, min(int(limit), 500))), limit=limit)
        return {**result, "connector": self._connector(c)}

    def run_github(self, principal: Principal, settings: dict[str, Any]) -> dict[str, Any]:
        return self._run_cli(principal, "github", settings)

    def preview_jira(self, principal: Principal, limit: int) -> dict[str, Any]:
        from ..activity_jira import CONNECTOR_ID, preview_jira_cli_enrichment
        c = self._db.activity.get_activity_enrichment_connector(CONNECTOR_ID) or self._db.activity.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
        result = preview_jira_cli_enrichment(self._db.activity.list_activity_records(entity_type="jira_ticket", limit=max(1, min(int(limit), 500))), limit=limit)
        return {**result, "connector": self._connector(c)}

    def run_jira(self, principal: Principal, settings: dict[str, Any]) -> dict[str, Any]:
        return self._run_cli(principal, "jira", settings)

    def _run_cli(self, principal: Principal, kind: str, overrides: dict[str, Any]) -> dict[str, Any]:
        if kind == "github":
            from ..activity_github import CONNECTOR_ID, run_github_cli_enrichment as runner
            from ..connector_packs import github_cli as pack
            kinds = ("github_pull_request", "github_issue")
        else:
            from ..activity_jira import CONNECTOR_ID, run_jira_cli_enrichment as runner
            from ..connector_packs import jira_cli as pack
            kinds = ("jira_ticket",)
        from ..connector_sdk import resolve_setting
        c = self._db.activity.get_activity_enrichment_connector(CONNECTOR_ID) or self._db.activity.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
        if not c.enabled: raise ServiceError("forbidden", f"{kind.title()} activity enrichment connector is disabled", context={"connector": self._connector(c)})
        values = c.settings or {}
        limit = overrides.get("limit") if overrides.get("limit") is not None else resolve_setting(pack.MANIFEST, values, "limit")
        timeout = overrides.get("timeout_seconds") if overrides.get("timeout_seconds") is not None else resolve_setting(pack.MANIFEST, values, "timeout_seconds")
        max_bytes = overrides.get("max_bytes") if overrides.get("max_bytes") is not None else resolve_setting(pack.MANIFEST, values, "max_bytes")
        records = [r for entity in kinds for r in self._db.activity.list_activity_records(entity_type=entity, limit=max(1, min(int(limit), 500)))]
        results = runner(self._db, records, limit=max(1, min(int(limit), 100)), timeout_seconds=max(.1, float(timeout)), max_bytes=max(1024, min(int(max_bytes), 1048576)), principal=principal)
        c = self._db.activity.get_activity_enrichment_connector(CONNECTOR_ID) or c
        return {"success": True, "connector": self._connector(c), "count": len(results), "results": [r.to_payload() for r in results]}
