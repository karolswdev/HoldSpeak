"""Activity / connector / plugin-job routes (HS-26-04).

The activity-intelligence cluster moved off `MeetingWebServer._create_app`:
activity status/records/refresh/settings, domain + project rules, enrichment
connectors (incl. GitHub/Jira preview+run), extension ingest, annotations,
meeting candidates, and the deferred plugin-job queue. Handlers move verbatim;
only the closure target changes (`self.` -> `ctx.`).

The activity payload helpers and `_meeting_payload_id` are used only by these
routes, so they were relocated here (out of `web_server`). `_meeting_callback_payload`
(shared with `routes/meetings.py`) and `_parse_iso_datetime` (still used by
`web_server` itself) are imported from `web_server` — HS-26-06 re-homes them.
`/api/projects/{project_id}/briefings` is a `/api/projects/*` path and stays
inline for HS-26-05.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...web_requests import (
    _ActivityCliEnrichmentRunRequest,
    _ActivityDomainRuleRequest,
    _ActivityEnrichmentConnectorRequest,
    _ActivityExtensionEventsRequest,
    _ActivityMeetingCandidateRequest,
    _ActivityMeetingCandidateStatusRequest,
    _ActivityProjectRuleRequest,
    _ActivitySettingsRequest,
    _PluginJobProcessRequest,
)
from ...web_server import _meeting_callback_payload, _parse_iso_datetime
from ..context import WebContext

log = get_logger("web.routes.activity")


def _model_fields_set(model: Any) -> set[str]:
    fields = getattr(model, "model_fields_set", None)
    if fields is not None:
        return set(fields)
    fields = getattr(model, "__fields_set__", None)
    if fields is not None:
        return set(fields)
    return set()


def _activity_project_rule_payload(rule: Any) -> dict[str, Any]:
    return {
        "id": rule.id,
        "project_id": rule.project_id,
        "project_name": rule.project_name,
        "name": rule.name,
        "enabled": rule.enabled,
        "priority": rule.priority,
        "match_type": rule.match_type,
        "pattern": rule.pattern,
        "entity_type": rule.entity_type,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat(),
    }


def _activity_record_payload(record: Any) -> dict[str, Any]:
    return {
        "id": record.id,
        "source_browser": record.source_browser,
        "source_profile": record.source_profile,
        "url": record.url,
        "title": record.title,
        "domain": record.domain,
        "visit_count": record.visit_count,
        "first_seen_at": record.first_seen_at.isoformat() if record.first_seen_at else None,
        "last_seen_at": record.last_seen_at.isoformat() if record.last_seen_at else None,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "project_id": record.project_id,
    }


def _activity_meeting_candidate_payload(candidate: Any) -> dict[str, Any]:
    return {
        "id": getattr(candidate, "id", None),
        "source_connector_id": candidate.source_connector_id,
        "source_activity_record_id": candidate.source_activity_record_id,
        "dedupe_key": getattr(candidate, "dedupe_key", ""),
        "title": candidate.title,
        "starts_at": candidate.starts_at.isoformat() if candidate.starts_at else None,
        "ends_at": candidate.ends_at.isoformat() if candidate.ends_at else None,
        "meeting_url": candidate.meeting_url,
        "started_meeting_id": getattr(candidate, "started_meeting_id", None),
        "confidence": candidate.confidence,
        "status": getattr(candidate, "status", "preview"),
        "created_at": candidate.created_at.isoformat() if getattr(candidate, "created_at", None) else None,
        "updated_at": candidate.updated_at.isoformat() if getattr(candidate, "updated_at", None) else None,
    }


def _activity_enrichment_connector_payload(connector: Any) -> dict[str, Any]:
    return {
        "id": connector.id,
        "enabled": connector.enabled,
        "settings": connector.settings,
        "last_run_at": connector.last_run_at.isoformat() if connector.last_run_at else None,
        "last_error": connector.last_error,
        "created_at": connector.created_at.isoformat(),
        "updated_at": connector.updated_at.isoformat(),
    }


def _meeting_payload_id(meeting_data: Any) -> Optional[str]:
    if not isinstance(meeting_data, dict):
        return None
    meeting_id = meeting_data.get("id")
    if meeting_id not in (None, ""):
        return str(meeting_id)
    nested = meeting_data.get("meeting")
    if isinstance(nested, dict) and nested.get("id") not in (None, ""):
        return str(nested["id"])
    return None


def build_activity_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    # === Local activity intelligence routes ===

    def _activity_status_payload() -> dict[str, Any]:
        from ...activity_history import discover_browser_history_sources
        from ...db import get_database

        db = get_database()
        settings = db.get_activity_privacy_settings()
        rules = db.list_activity_domain_rules()
        checkpoints = db.list_activity_import_checkpoints()
        checkpoint_payload = [
            {
                "source_browser": checkpoint.source_browser,
                "source_profile": checkpoint.source_profile,
                "source_path_hash": checkpoint.source_path_hash,
                "last_visit_raw": checkpoint.last_visit_raw,
                "last_imported_at": checkpoint.last_imported_at.isoformat() if checkpoint.last_imported_at else None,
                "last_error": checkpoint.last_error,
                "enabled": checkpoint.enabled,
            }
            for checkpoint in checkpoints
        ]
        discovered = [
            {
                "source_browser": source.source_browser,
                "source_profile": source.source_profile,
                "source_path_hash": source.source_path_hash,
                "readable": source.path.is_file(),
                "enabled": bool(source.enabled and settings["enabled"]),
            }
            for source in discover_browser_history_sources()
        ]
        return {
            "settings": settings,
            "sources": discovered,
            "checkpoints": checkpoint_payload,
            "domain_rules": rules,
            "record_count": len(db.list_activity_records(limit=5000)),
        }

    @router.get("/api/activity/status")
    async def api_activity_status() -> Any:
        try:
            return JSONResponse(_activity_status_payload())
        except Exception as e:
            log.error(f"Failed to read activity status: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/records")
    async def api_activity_records(
        project_id: Optional[str] = None,
        domain: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 100,
    ) -> Any:
        try:
            from ...activity_context import build_activity_context
            from ...db import get_database

            db = get_database()
            bundle = build_activity_context(
                db=db,
                project_id=project_id,
                limit=limit,
                refresh=False,
            ).to_dict()
            records = bundle["records"]
            if domain:
                clean_domain = domain.strip().lower()
                records = [record for record in records if record.get("domain") == clean_domain]
            if entity_type:
                clean_type = entity_type.strip().lower()
                records = [record for record in records if record.get("entity_type") == clean_type]
            bundle["records"] = records
            return JSONResponse(bundle)
        except Exception as e:
            log.error(f"Failed to read activity records: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/refresh")
    async def api_activity_refresh() -> Any:
        try:
            from ...activity_history import import_browser_history
            from ...db import get_database

            db = get_database()
            results = import_browser_history(db=db)
            return JSONResponse(
                {
                    "results": [
                        {
                            "source_browser": result.source_browser,
                            "source_profile": result.source_profile,
                            "source_path_hash": result.source_path_hash,
                            "imported_count": result.imported_count,
                            "checkpoint_raw": result.checkpoint_raw,
                            "enabled": result.enabled,
                            "error": result.error,
                        }
                        for result in results
                    ],
                    "status": _activity_status_payload(),
                }
            )
        except Exception as e:
            log.error(f"Failed to refresh activity: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.put("/api/activity/settings")
    async def api_activity_settings(payload: _ActivitySettingsRequest) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            settings = db.update_activity_privacy_settings(
                enabled=payload.enabled,
                retention_days=payload.retention_days,
            )
            return JSONResponse({"settings": settings, "status": _activity_status_payload()})
        except Exception as e:
            log.error(f"Failed to update activity settings: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/domains")
    async def api_activity_domain_rule(payload: _ActivityDomainRuleRequest) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            rule = db.upsert_activity_domain_rule(
                domain=payload.domain,
                action=payload.action,
            )
            return JSONResponse({"rule": rule, "status": _activity_status_payload()})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to update activity domain rule: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.delete("/api/activity/domains/{domain}")
    async def api_delete_activity_domain_rule(domain: str) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            deleted = db.delete_activity_domain_rule(domain)
            return JSONResponse({"deleted": deleted, "status": _activity_status_payload()})
        except Exception as e:
            log.error(f"Failed to delete activity domain rule: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/project-rules")
    async def api_activity_project_rules(include_disabled: bool = True) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            rules = db.list_activity_project_rules(include_disabled=include_disabled)
            return JSONResponse({"rules": [_activity_project_rule_payload(rule) for rule in rules]})
        except Exception as e:
            log.error(f"Failed to list activity project rules: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/project-rules")
    async def api_create_activity_project_rule(payload: _ActivityProjectRuleRequest) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            rule = db.create_activity_project_rule(
                project_id=payload.project_id or "",
                name=payload.name or "",
                match_type=payload.match_type or "",
                pattern=payload.pattern or "",
                entity_type=payload.entity_type,
                priority=payload.priority if payload.priority is not None else 100,
                enabled=True if payload.enabled is None else payload.enabled,
            )
            return JSONResponse({"rule": _activity_project_rule_payload(rule)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to create activity project rule: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.put("/api/activity/project-rules/{rule_id}")
    async def api_update_activity_project_rule(
        rule_id: str,
        payload: _ActivityProjectRuleRequest,
    ) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            fields: dict[str, Any] = {}
            present = _model_fields_set(payload)
            for key in (
                "project_id",
                "name",
                "enabled",
                "priority",
                "match_type",
                "pattern",
                "entity_type",
            ):
                if key in present:
                    fields[key] = getattr(payload, key)
            rule = db.update_activity_project_rule(rule_id, **fields)
            if rule is None:
                return JSONResponse({"error": "activity project rule not found"}, status_code=404)
            return JSONResponse({"rule": _activity_project_rule_payload(rule)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to update activity project rule: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.delete("/api/activity/project-rules/{rule_id}")
    async def api_delete_activity_project_rule(rule_id: str) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            return JSONResponse({"deleted": db.delete_activity_project_rule(rule_id)})
        except Exception as e:
            log.error(f"Failed to delete activity project rule: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/project-rules/preview")
    async def api_preview_activity_project_rule(payload: _ActivityProjectRuleRequest) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            matches = db.preview_activity_project_rule(
                project_id=payload.project_id or "",
                match_type=payload.match_type or "",
                pattern=payload.pattern or "",
                entity_type=payload.entity_type,
                limit=50,
            )
            return JSONResponse(
                {
                    "count": len(matches),
                    "matches": [_activity_record_payload(record) for record in matches],
                }
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to preview activity project rule: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/project-rules/apply")
    async def api_apply_activity_project_rules(limit: Optional[int] = None) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            updated = db.apply_activity_project_rules(limit=limit)
            return JSONResponse({"updated": updated})
        except Exception as e:
            log.error(f"Failed to apply activity project rules: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/enrichment/connectors")
    async def api_list_activity_enrichment_connectors() -> Any:
        try:
            from ...activity_connectors import enrichment_descriptors
            from ...activity_github import github_cli_status
            from ...activity_jira import jira_cli_status
            from ...db import get_database

            db = get_database()
            connectors = []
            for descriptor in enrichment_descriptors():
                state = db.get_activity_enrichment_connector(descriptor.id)
                if state is None:
                    state = db.upsert_activity_enrichment_connector(connector_id=descriptor.id)
                payload = _activity_enrichment_connector_payload(state)
                payload["label"] = descriptor.label
                payload["kind"] = descriptor.kind
                payload["capabilities"] = list(descriptor.capabilities)
                payload["requires_cli"] = descriptor.requires_cli
                payload["description"] = descriptor.description
                payload["source"] = descriptor.source
                cli_status = descriptor.cli_status()
                if cli_status is not None:
                    payload["cli_status"] = cli_status
                connectors.append(payload)
            return JSONResponse(
                {
                    "connectors": connectors,
                    # Kept for backwards-compat with the existing
                    # /activity preview/run endpoints; new clients
                    # should read connector.cli_status instead.
                    "github": github_cli_status(),
                    "jira": jira_cli_status(),
                }
            )
        except Exception as e:
            log.error(f"Failed to list activity enrichment connectors: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.put("/api/activity/enrichment/connectors/{connector_id}")
    async def api_update_activity_enrichment_connector(
        connector_id: str,
        payload: _ActivityEnrichmentConnectorRequest,
    ) -> Any:
        from ...activity_connectors import KNOWN_CONNECTOR_IDS, get_descriptor

        if connector_id not in KNOWN_CONNECTOR_IDS:
            return JSONResponse(
                {"error": f"Unknown activity enrichment connector: {connector_id}"},
                status_code=404,
            )

        descriptor = get_descriptor(connector_id)
        if descriptor is not None and payload.settings:
            allowed = descriptor.manifest.setting_keys()
            unknown = sorted(set(payload.settings) - allowed)
            if unknown:
                return JSONResponse(
                    {
                        "error": (
                            f"Connector {connector_id!r} does not declare "
                            f"setting key(s): {unknown}. Allowed: "
                            f"{sorted(allowed)}."
                        ),
                    },
                    status_code=400,
                )
        try:
            from ...db import get_database

            db = get_database()
            connector = db.upsert_activity_enrichment_connector(
                connector_id=connector_id,
                enabled=payload.enabled,
                settings=payload.settings,
            )
            return JSONResponse({"connector": _activity_enrichment_connector_payload(connector)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to update activity enrichment connector: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/extension/events")
    async def api_ingest_activity_extension_events(
        payload: _ActivityExtensionEventsRequest,
    ) -> Any:
        """HS-9-03: companion-extension event ingestion. Loopback-only
        in practice — the runtime binds to 127.0.0.1 by default. Per
        the parser contract, events that ship sensitive fields
        (cookies, body, form data, etc.), private-browsing flags, or
        non-http(s) URLs are rejected, never persisted.

        HS-13-02: gates the call on the firefox_ext pack's
        `loopback:http` permission as defense-in-depth. The
        check is honest enforcement, not a sandbox — a pack
        that drops the permission must not be able to ingest
        events even if its endpoint is still mounted."""
        from ...activity_extension import ingest_extension_events
        from ...connector_packs import firefox_ext
        from ...connector_runtime import PermissionDenied, PermissionGate
        from ...db import get_database

        gate = PermissionGate(firefox_ext.MANIFEST)
        try:
            gate.accept_loopback_event()
        except PermissionDenied as exc:
            return JSONResponse({"error": str(exc)}, status_code=403)

        try:
            db = get_database()
            result = ingest_extension_events(db, payload.events)
            return JSONResponse(result.to_payload())
        except Exception as e:
            log.error(f"Failed to ingest activity extension events: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/enrichment/connectors/{connector_id}/dry-run")
    async def api_connector_dry_run(connector_id: str, limit: int = 25) -> Any:
        from ...activity_connector_preview import (
            MAX_LIMIT,
            UnknownConnectorError,
            dry_run as connector_dry_run,
        )
        from ...db import get_database

        try:
            clean_limit = max(1, min(int(limit), MAX_LIMIT))
        except (TypeError, ValueError):
            clean_limit = 25
        try:
            db = get_database()
            result = connector_dry_run(db, connector_id, limit=clean_limit)
            return JSONResponse({"dry_run": result.to_payload()})
        except UnknownConnectorError:
            return JSONResponse(
                {"error": f"Unknown activity enrichment connector: {connector_id}"},
                status_code=404,
            )
        except Exception as e:
            log.error(f"Failed to dry-run activity enrichment connector: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.delete("/api/activity/enrichment/connectors/{connector_id}/annotations")
    async def api_clear_activity_enrichment_annotations(connector_id: str) -> Any:
        from ...activity_connectors import get_descriptor

        descriptor = get_descriptor(connector_id)
        if descriptor is None:
            return JSONResponse(
                {"error": f"Unknown activity enrichment connector: {connector_id}"},
                status_code=404,
            )
        if "annotations" not in descriptor.capabilities:
            return JSONResponse(
                {
                    "error": (
                        f"Connector {connector_id} does not produce annotations"
                    ),
                },
                status_code=400,
            )
        try:
            from ...db import get_database

            db = get_database()
            deleted = db.delete_activity_annotations(source_connector_id=connector_id)
            # HS-13-05: run history is part of the pack's
            # output; clearing annotations clears the matching
            # run rows so the user sees a fresh slate after a
            # reset.
            runs_deleted = db.delete_connector_runs(connector_id=connector_id)
            return JSONResponse(
                {
                    "deleted": int(deleted),
                    "connector_id": connector_id,
                    "runs_deleted": int(runs_deleted),
                }
            )
        except Exception as e:
            log.error(f"Failed to clear activity enrichment annotations: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.delete("/api/activity/enrichment/connectors/{connector_id}/candidates")
    async def api_clear_activity_enrichment_candidates(connector_id: str) -> Any:
        from ...activity_connectors import get_descriptor

        descriptor = get_descriptor(connector_id)
        if descriptor is None:
            return JSONResponse(
                {"error": f"Unknown activity enrichment connector: {connector_id}"},
                status_code=404,
            )
        if "candidates" not in descriptor.capabilities:
            return JSONResponse(
                {
                    "error": (
                        f"Connector {connector_id} does not produce candidates"
                    ),
                },
                status_code=400,
            )
        try:
            from ...db import get_database

            db = get_database()
            deleted = db.delete_activity_meeting_candidates(source_connector_id=connector_id)
            runs_deleted = db.delete_connector_runs(connector_id=connector_id)
            return JSONResponse(
                {
                    "deleted": int(deleted),
                    "connector_id": connector_id,
                    "runs_deleted": int(runs_deleted),
                }
            )
        except Exception as e:
            log.error(f"Failed to clear activity enrichment candidates: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/annotations")
    async def api_list_activity_annotations(
        source_connector_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
        activity_record_id: Optional[int] = None,
        limit: int = 100,
    ) -> Any:
        """HS-13-07: read-only listing for the
        `meeting_context_briefing` annotations (and any other
        connector annotations a power user wants to inspect)."""
        from ...db import get_database

        try:
            clean_limit = max(1, min(int(limit), 500))
        except (TypeError, ValueError):
            clean_limit = 100
        try:
            db = get_database()
            annotations = db.list_activity_annotations(
                source_connector_id=source_connector_id,
                annotation_type=annotation_type,
                activity_record_id=activity_record_id,
                limit=clean_limit,
            )
            return JSONResponse(
                {
                    "annotations": [
                        {
                            "id": ann.id,
                            "activity_record_id": ann.activity_record_id,
                            "source_connector_id": ann.source_connector_id,
                            "annotation_type": ann.annotation_type,
                            "title": ann.title,
                            "value": ann.value,
                            "confidence": ann.confidence,
                            "created_at": ann.created_at.isoformat(),
                            "updated_at": ann.updated_at.isoformat(),
                        }
                        for ann in annotations
                    ],
                }
            )
        except Exception as e:
            log.error(f"Failed to list activity annotations: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/briefing")
    async def api_activity_briefing() -> Any:
        """HS-13-08: project briefing surface for `/`.

        Returns the most-recent `meeting_context_briefing`
        annotation (the dashboard renders its markdown
        inline), plus the most recent `connector_runs` row
        for the meeting_context pipeline so the panel can
        show a status pill ("success" / "stale" / "danger")
        and a "Last refreshed" timestamp.

        Single-user model: the most-recently-updated
        briefing is treated as the "current project". A
        multi-project switcher can layer on top of this in
        phase 14 — the data already supports it.
        """
        from ...db import get_database

        try:
            db = get_database()
            annotations = db.list_activity_annotations(
                source_connector_id="meeting_context",
                annotation_type="meeting_context_briefing",
                limit=20,
            )
            briefing = annotations[0] if annotations else None
            runs = db.list_connector_runs(
                connector_id="meeting_context", limit=1
            )
            last_run = runs[0] if runs else None
            payload = {
                "briefing": (
                    {
                        "id": briefing.id,
                        "title": briefing.title,
                        "value": briefing.value,
                        "updated_at": briefing.updated_at.isoformat(),
                    }
                    if briefing
                    else None
                ),
                "last_run": last_run.to_payload() if last_run else None,
            }
            return JSONResponse(payload)
        except Exception as e:
            log.error(f"Failed to fetch activity briefing: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/enrichment/pipelines/{pipeline_id}/run")
    async def api_run_pipeline(pipeline_id: str) -> Any:
        """HS-13-08: kick off a pipeline pack on demand.

        Wraps `PipelineRunner` so the dashboard's "Refresh
        briefing" button has a single endpoint to call.
        Returns the `PipelineRunResult.to_payload()` so the
        UI can render which steps ran / were skipped /
        failed.
        """
        from ...activity_connectors import get_descriptor
        from ...connector_runtime import (
            NotAPipelineError,
            PipelineRunner,
            UnknownPipelineError,
        )
        from ...db import get_database

        descriptor = get_descriptor(pipeline_id)
        if descriptor is None:
            return JSONResponse(
                {"error": f"Unknown pipeline: {pipeline_id}"},
                status_code=404,
            )
        if descriptor.manifest.kind != "pipeline":
            return JSONResponse(
                {
                    "error": (
                        f"Connector {pipeline_id!r} is "
                        f"kind={descriptor.manifest.kind!r}, not a pipeline"
                    ),
                },
                status_code=400,
            )
        try:
            db = get_database()
            runner = PipelineRunner(db)
            try:
                result = runner.run(pipeline_id)
            except (UnknownPipelineError, NotAPipelineError) as exc:
                return JSONResponse({"error": str(exc)}, status_code=404)
            return JSONResponse({"result": result.to_payload()})
        except Exception as e:
            log.error(f"Failed to run pipeline {pipeline_id}: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/enrichment/connectors/{connector_id}/runs")
    async def api_list_activity_enrichment_runs(
        connector_id: str,
        limit: int = 10,
    ) -> Any:
        """HS-13-05: per-connector run history."""
        from ...activity_connectors import get_descriptor
        from ...db import get_database

        descriptor = get_descriptor(connector_id)
        if descriptor is None:
            return JSONResponse(
                {"error": f"Unknown activity enrichment connector: {connector_id}"},
                status_code=404,
            )
        try:
            clean_limit = max(1, min(int(limit), 200))
        except (TypeError, ValueError):
            clean_limit = 10
        try:
            db = get_database()
            runs = db.list_connector_runs(
                connector_id=connector_id, limit=clean_limit
            )
            return JSONResponse(
                {
                    "connector_id": connector_id,
                    "runs": [run.to_payload() for run in runs],
                }
            )
        except Exception as e:
            log.error(f"Failed to list connector runs: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/enrichment/github/preview")
    async def api_preview_github_activity_enrichment(limit: int = 50) -> Any:
        try:
            from ...activity_github import CONNECTOR_ID, preview_github_cli_enrichment
            from ...db import get_database

            db = get_database()
            connector = db.get_activity_enrichment_connector(CONNECTOR_ID)
            if connector is None:
                connector = db.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
            records = db.list_activity_records(limit=max(1, min(int(limit), 500)))
            preview = preview_github_cli_enrichment(records, limit=limit)
            return JSONResponse(
                {
                    **preview,
                    "connector": _activity_enrichment_connector_payload(connector),
                }
            )
        except Exception as e:
            log.error(f"Failed to preview GitHub activity enrichment: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/enrichment/github/run")
    async def api_run_github_activity_enrichment(
        payload: Optional[_ActivityCliEnrichmentRunRequest] = None,
    ) -> Any:
        try:
            from ...activity_github import CONNECTOR_ID, run_github_cli_enrichment
            from ...db import get_database

            db = get_database()
            connector = db.get_activity_enrichment_connector(CONNECTOR_ID)
            if connector is None:
                connector = db.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
            if not connector.enabled:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "GitHub activity enrichment connector is disabled",
                        "connector": _activity_enrichment_connector_payload(connector),
                    },
                    status_code=403,
                )

            from ...connector_packs import github_cli as github_cli_pack
            from ...connector_sdk import resolve_setting

            settings = connector.settings or {}
            limit = (
                payload.limit
                if payload and payload.limit is not None
                else resolve_setting(github_cli_pack.MANIFEST, settings, "limit")
            )
            timeout_seconds = (
                payload.timeout_seconds
                if payload and payload.timeout_seconds is not None
                else resolve_setting(
                    github_cli_pack.MANIFEST, settings, "timeout_seconds"
                )
            )
            max_bytes = (
                payload.max_bytes
                if payload and payload.max_bytes is not None
                else resolve_setting(
                    github_cli_pack.MANIFEST, settings, "max_bytes"
                )
            )
            records = db.list_activity_records(
                entity_type="github_pull_request",
                limit=max(1, min(int(limit), 500)),
            )
            issue_records = db.list_activity_records(
                entity_type="github_issue",
                limit=max(1, min(int(limit), 500)),
            )
            results = run_github_cli_enrichment(
                db,
                [*records, *issue_records],
                limit=max(1, min(int(limit), 100)),
                timeout_seconds=max(0.1, float(timeout_seconds)),
                max_bytes=max(1024, min(int(max_bytes), 1048576)),
            )
            connector = db.get_activity_enrichment_connector(CONNECTOR_ID) or connector
            return JSONResponse(
                {
                    "success": True,
                    "connector": _activity_enrichment_connector_payload(connector),
                    "count": len(results),
                    "results": [result.to_payload() for result in results],
                }
            )
        except ValueError as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to run GitHub activity enrichment: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.get("/api/activity/enrichment/jira/preview")
    async def api_preview_jira_activity_enrichment(limit: int = 50) -> Any:
        try:
            from ...activity_jira import CONNECTOR_ID, preview_jira_cli_enrichment
            from ...db import get_database

            db = get_database()
            connector = db.get_activity_enrichment_connector(CONNECTOR_ID)
            if connector is None:
                connector = db.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
            records = db.list_activity_records(entity_type="jira_ticket", limit=max(1, min(int(limit), 500)))
            preview = preview_jira_cli_enrichment(records, limit=limit)
            return JSONResponse(
                {
                    **preview,
                    "connector": _activity_enrichment_connector_payload(connector),
                }
            )
        except Exception as e:
            log.error(f"Failed to preview Jira activity enrichment: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/enrichment/jira/run")
    async def api_run_jira_activity_enrichment(
        payload: Optional[_ActivityCliEnrichmentRunRequest] = None,
    ) -> Any:
        try:
            from ...activity_jira import CONNECTOR_ID, run_jira_cli_enrichment
            from ...db import get_database

            db = get_database()
            connector = db.get_activity_enrichment_connector(CONNECTOR_ID)
            if connector is None:
                connector = db.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
            if not connector.enabled:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Jira activity enrichment connector is disabled",
                        "connector": _activity_enrichment_connector_payload(connector),
                    },
                    status_code=403,
                )

            from ...connector_packs import jira_cli as jira_cli_pack
            from ...connector_sdk import resolve_setting

            settings = connector.settings or {}
            limit = (
                payload.limit
                if payload and payload.limit is not None
                else resolve_setting(jira_cli_pack.MANIFEST, settings, "limit")
            )
            timeout_seconds = (
                payload.timeout_seconds
                if payload and payload.timeout_seconds is not None
                else resolve_setting(
                    jira_cli_pack.MANIFEST, settings, "timeout_seconds"
                )
            )
            max_bytes = (
                payload.max_bytes
                if payload and payload.max_bytes is not None
                else resolve_setting(
                    jira_cli_pack.MANIFEST, settings, "max_bytes"
                )
            )
            records = db.list_activity_records(
                entity_type="jira_ticket",
                limit=max(1, min(int(limit), 500)),
            )
            results = run_jira_cli_enrichment(
                db,
                records,
                limit=max(1, min(int(limit), 100)),
                timeout_seconds=max(0.1, float(timeout_seconds)),
                max_bytes=max(1024, min(int(max_bytes), 1048576)),
            )
            connector = db.get_activity_enrichment_connector(CONNECTOR_ID) or connector
            return JSONResponse(
                {
                    "success": True,
                    "connector": _activity_enrichment_connector_payload(connector),
                    "count": len(results),
                    "results": [result.to_payload() for result in results],
                }
            )
        except ValueError as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to run Jira activity enrichment: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.get("/api/activity/meeting-candidates/preview")
    async def api_preview_activity_meeting_candidates(limit: int = 50) -> Any:
        try:
            from ...activity_candidates import preview_calendar_meeting_candidates
            from ...db import get_database

            db = get_database()
            records = db.list_activity_records(limit=max(1, min(int(limit), 500)))
            previews = preview_calendar_meeting_candidates(records, limit=limit)
            return JSONResponse(
                {
                    "count": len(previews),
                    "candidates": [_activity_meeting_candidate_payload(candidate) for candidate in previews],
                }
            )
        except Exception as e:
            log.error(f"Failed to preview activity meeting candidates: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/activity/meeting-candidates")
    async def api_activity_meeting_candidates(
        source_connector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            candidates = db.list_activity_meeting_candidates(
                source_connector_id=source_connector_id,
                status=status,
                limit=limit,
            )
            return JSONResponse(
                {
                    "count": len(candidates),
                    "candidates": [_activity_meeting_candidate_payload(candidate) for candidate in candidates],
                }
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to list activity meeting candidates: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/meeting-candidates")
    async def api_create_activity_meeting_candidate(
        payload: _ActivityMeetingCandidateRequest,
    ) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            candidate = db.create_activity_meeting_candidate(
                source_connector_id=payload.source_connector_id or "calendar_activity",
                source_activity_record_id=payload.source_activity_record_id,
                title=payload.title or "",
                starts_at=_parse_iso_datetime(payload.starts_at),
                ends_at=_parse_iso_datetime(payload.ends_at),
                meeting_url=payload.meeting_url,
                confidence=payload.confidence if payload.confidence is not None else 0.0,
                status=payload.status or "candidate",
            )
            return JSONResponse({"candidate": _activity_meeting_candidate_payload(candidate)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to create activity meeting candidate: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.put("/api/activity/meeting-candidates/{candidate_id}/status")
    async def api_update_activity_meeting_candidate_status(
        candidate_id: str,
        payload: _ActivityMeetingCandidateStatusRequest,
    ) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            candidate = db.update_activity_meeting_candidate_status(
                candidate_id,
                payload.status,
            )
            if candidate is None:
                return JSONResponse({"error": "activity meeting candidate not found"}, status_code=404)
            return JSONResponse({"candidate": _activity_meeting_candidate_payload(candidate)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to update activity meeting candidate: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/activity/meeting-candidates/{candidate_id}/start")
    async def api_start_activity_meeting_candidate(candidate_id: str) -> Any:
        if ctx.on_start is None:
            return JSONResponse(
                {"success": False, "error": "Meeting start control not supported"},
                status_code=501,
            )

        try:
            from ...db import get_database

            db = get_database()
            candidate = db.get_activity_meeting_candidate(candidate_id)
            if candidate is None:
                return JSONResponse({"error": "activity meeting candidate not found"}, status_code=404)

            result = ctx.on_start()
            meeting_data = _meeting_callback_payload(result)

            title_warning = None
            if ctx.on_update_meeting is not None and str(candidate.title or "").strip():
                try:
                    updated = ctx.on_update_meeting(title=candidate.title, tags=None)
                    updated_payload = _meeting_callback_payload(updated)
                    if updated_payload is not None:
                        meeting_data = updated_payload
                except Exception as e:
                    title_warning = str(e)
                    log.error(f"Failed to apply candidate title to started meeting: {e}")

            meeting_id = _meeting_payload_id(meeting_data)
            candidate = db.mark_activity_meeting_candidate_started(
                candidate.id,
                meeting_id=meeting_id,
            )
            if candidate is None:
                return JSONResponse({"error": "activity meeting candidate not found"}, status_code=404)

            if meeting_data is not None:
                ctx.broadcast(
                    "meeting_started",
                    {
                        **meeting_data,
                        "activity_meeting_candidate_id": candidate.id,
                        "activity_meeting_candidate_title": candidate.title,
                        "activity_meeting_candidate_url": candidate.meeting_url,
                    },
                )
            response_payload: dict[str, Any] = {
                "success": True,
                "candidate": _activity_meeting_candidate_payload(candidate),
                "meeting": meeting_data,
            }
            if title_warning:
                response_payload["warning"] = f"Meeting started, but title update failed: {title_warning}"
            return JSONResponse(response_payload)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to start activity meeting candidate: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.delete("/api/activity/meeting-candidates")
    async def api_delete_activity_meeting_candidates(
        source_connector_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            deleted = db.delete_activity_meeting_candidates(
                source_connector_id=source_connector_id,
                status=status,
            )
            return JSONResponse({"deleted": deleted})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to delete activity meeting candidates: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.delete("/api/activity/records")
    async def api_delete_activity_records(
        domain: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            deleted = db.delete_activity_records(domain=domain, project_id=project_id)
            return JSONResponse({"deleted": deleted, "status": _activity_status_payload()})
        except Exception as e:
            log.error(f"Failed to delete activity records: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/plugin-jobs")
    async def api_list_plugin_jobs(
        status: str = "all",
        meeting_id: Optional[str] = None,
        limit: int = 200,
    ) -> Any:
        """List deferred MIR plugin-run queue jobs."""
        try:
            from ...db import get_database

            db = get_database()
            jobs = db.list_plugin_run_jobs(status=status, meeting_id=meeting_id, limit=limit)
            now = datetime.now()
            return JSONResponse(
                {
                    "jobs": [
                        {
                            "id": job.id,
                            "meeting_id": job.meeting_id,
                            "window_id": job.window_id,
                            "plugin_id": job.plugin_id,
                            "plugin_version": job.plugin_version,
                            "transcript_hash": job.transcript_hash,
                            "idempotency_key": job.idempotency_key,
                            "status": job.status,
                            "requested_at": job.requested_at.isoformat(),
                            "updated_at": job.updated_at.isoformat(),
                            "attempts": job.attempts,
                            "last_error": job.last_error,
                            "retry_scheduled": (
                                job.status == "queued"
                                and bool(job.last_error)
                                and job.requested_at > now
                            ),
                            "next_retry_at": (
                                job.requested_at.isoformat()
                                if (
                                    job.status == "queued"
                                    and bool(job.last_error)
                                    and job.requested_at > now
                                )
                                else None
                            ),
                        }
                        for job in jobs
                    ]
                }
            )
        except Exception as e:
            log.error(f"Failed to list deferred plugin jobs: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.get("/api/plugin-jobs/summary")
    async def api_plugin_jobs_summary() -> Any:
        """Return aggregate telemetry for deferred MIR plugin-run queue."""
        try:
            from ...db import get_database

            db = get_database()
            summary = db.get_plugin_run_job_summary()
            return JSONResponse(
                {
                    "total_jobs": summary.total_jobs,
                    "queued_jobs": summary.queued_jobs,
                    "running_jobs": summary.running_jobs,
                    "failed_jobs": summary.failed_jobs,
                    "queued_due_jobs": summary.queued_due_jobs,
                    "scheduled_retry_jobs": summary.scheduled_retry_jobs,
                    "next_retry_at": (
                        summary.next_retry_at.isoformat() if summary.next_retry_at else None
                    ),
                }
            )
        except Exception as e:
            log.error(f"Failed to load deferred plugin-job summary: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @router.post("/api/plugin-jobs/process")
    async def api_process_plugin_jobs(payload: Optional[_PluginJobProcessRequest] = None) -> Any:
        """Process deferred plugin-run queue jobs now."""
        if ctx.on_process_plugin_jobs is None:
            return JSONResponse(
                {"success": False, "error": "Deferred plugin queue processing not supported"},
                status_code=501,
            )
        max_jobs = payload.max_jobs if payload is not None else None
        if max_jobs is not None and int(max_jobs) <= 0:
            return JSONResponse(
                {"success": False, "error": "max_jobs must be greater than 0"},
                status_code=400,
            )
        mode = (payload.mode if payload is not None else None) or "respect_backoff"
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in {"respect_backoff", "retry_now"}:
            return JSONResponse(
                {"success": False, "error": "mode must be respect_backoff or retry_now"},
                status_code=400,
            )
        include_scheduled = normalized_mode == "retry_now"
        try:
            result = ctx.on_process_plugin_jobs(
                max_jobs=max_jobs,
                include_scheduled=include_scheduled,
            )
            payload_data = dict(result) if isinstance(result, dict) else {"processed": int(result)}
            payload_data["mode"] = normalized_mode
            payload_data["success"] = True
            ctx.broadcast("plugin_jobs_processed", payload_data)
            return JSONResponse(payload_data)
        except Exception as e:
            log.error(f"Failed to process deferred plugin jobs: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.post("/api/plugin-jobs/{job_id}/retry-now")
    async def api_retry_plugin_job_now(job_id: int) -> Any:
        """Reschedule one deferred MIR plugin-run job for immediate retry."""
        try:
            from ...db import get_database

            db = get_database()
            job = db.get_plugin_run_job(job_id) if hasattr(db, "get_plugin_run_job") else None
            if job is None:
                return JSONResponse({"success": False, "error": "Plugin job not found"}, status_code=404)
            if str(job.status).strip().lower() == "running":
                return JSONResponse(
                    {"success": False, "error": "Cannot retry a running plugin job"},
                    status_code=409,
                )

            db.retry_plugin_run_job(
                int(job_id),
                error="Manual retry requested from web UI.",
                retry_at=datetime.now(),
            )
            updated = db.get_plugin_run_job(job_id) if hasattr(db, "get_plugin_run_job") else None
            return JSONResponse(
                {
                    "success": True,
                    "job": (
                        {
                            "id": updated.id,
                            "meeting_id": updated.meeting_id,
                            "window_id": updated.window_id,
                            "plugin_id": updated.plugin_id,
                            "plugin_version": updated.plugin_version,
                            "status": updated.status,
                            "requested_at": updated.requested_at.isoformat(),
                            "updated_at": updated.updated_at.isoformat(),
                            "attempts": updated.attempts,
                            "last_error": updated.last_error,
                        }
                        if updated is not None
                        else None
                    ),
                }
            )
        except Exception as e:
            log.error(f"Failed to retry deferred plugin job {job_id}: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.post("/api/plugin-jobs/{job_id}/cancel")
    async def api_cancel_plugin_job(job_id: int) -> Any:
        """Cancel one deferred MIR plugin-run job."""
        try:
            from ...db import get_database

            db = get_database()
            job = db.get_plugin_run_job(job_id) if hasattr(db, "get_plugin_run_job") else None
            if job is None:
                return JSONResponse({"success": False, "error": "Plugin job not found"}, status_code=404)
            if str(job.status).strip().lower() == "running":
                return JSONResponse(
                    {"success": False, "error": "Cannot cancel a running plugin job"},
                    status_code=409,
                )
            db.complete_plugin_run_job(job_id)
            return JSONResponse({"success": True})
        except Exception as e:
            log.error(f"Failed to cancel deferred plugin job {job_id}: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    return router
