"""Connector-enrichment routes — HS-34-02 split of `activity.py`.

`/api/activity/enrichment/*` (connectors, dry-run, runs, annotations/candidates
clear, pipelines, GitHub/Jira preview+run) plus `/api/activity/extension/events`,
`/api/activity/annotations`, and `/api/activity/briefing`. The connector payload
shaper is used only by this group.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import (
    _ActivityCliEnrichmentRunRequest,
    _ActivityEnrichmentConnectorRequest,
    _ActivityExtensionEventsRequest,
)
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.activity")


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


def build_enrichment_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/activity/enrichment/connectors")
    async def api_list_activity_enrichment_connectors() -> Any:
        try:
            from ....activity_connectors import enrichment_descriptors
            from ....activity_github import github_cli_status
            from ....activity_jira import jira_cli_status
            from ....db import get_database

            db = get_database()
            connectors = []
            for descriptor in enrichment_descriptors():
                state = db.activity.get_activity_enrichment_connector(descriptor.id)
                if state is None:
                    state = db.activity.upsert_activity_enrichment_connector(connector_id=descriptor.id)
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
            return error_500(e, log, "Failed to list activity enrichment connectors")

    @router.put("/api/activity/enrichment/connectors/{connector_id}")
    async def api_update_activity_enrichment_connector(
        connector_id: str,
        payload: _ActivityEnrichmentConnectorRequest,
    ) -> Any:
        from ....activity_connectors import KNOWN_CONNECTOR_IDS, get_descriptor

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
            from ....db import get_database

            db = get_database()
            connector = db.activity.upsert_activity_enrichment_connector(
                connector_id=connector_id,
                enabled=payload.enabled,
                settings=payload.settings,
            )
            return JSONResponse({"connector": _activity_enrichment_connector_payload(connector)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to update activity enrichment connector")

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
        from ....activity_extension import ingest_extension_events
        from ....connector_packs import firefox_ext
        from ....connector_runtime import PermissionDenied, PermissionGate
        from ....db import get_database

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
            return error_500(e, log, "Failed to ingest activity extension events")

    @router.get("/api/activity/enrichment/connectors/{connector_id}/dry-run")
    async def api_connector_dry_run(connector_id: str, limit: int = 25) -> Any:
        from ....activity_connector_preview import (
            MAX_LIMIT,
            UnknownConnectorError,
            dry_run as connector_dry_run,
        )
        from ....db import get_database

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
            return error_500(e, log, "Failed to dry-run activity enrichment connector")

    @router.delete("/api/activity/enrichment/connectors/{connector_id}/annotations")
    async def api_clear_activity_enrichment_annotations(connector_id: str) -> Any:
        from ....activity_connectors import get_descriptor

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
            from ....db import get_database

            db = get_database()
            deleted = db.activity.delete_activity_annotations(source_connector_id=connector_id)
            # HS-13-05: run history is part of the pack's
            # output; clearing annotations clears the matching
            # run rows so the user sees a fresh slate after a
            # reset.
            runs_deleted = db.activity.delete_connector_runs(connector_id=connector_id)
            return JSONResponse(
                {
                    "deleted": int(deleted),
                    "connector_id": connector_id,
                    "runs_deleted": int(runs_deleted),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to clear activity enrichment annotations")

    @router.delete("/api/activity/enrichment/connectors/{connector_id}/candidates")
    async def api_clear_activity_enrichment_candidates(connector_id: str) -> Any:
        from ....activity_connectors import get_descriptor

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
            from ....db import get_database

            db = get_database()
            deleted = db.activity.delete_activity_meeting_candidates(source_connector_id=connector_id)
            runs_deleted = db.activity.delete_connector_runs(connector_id=connector_id)
            return JSONResponse(
                {
                    "deleted": int(deleted),
                    "connector_id": connector_id,
                    "runs_deleted": int(runs_deleted),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to clear activity enrichment candidates")

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
        from ....db import get_database

        try:
            clean_limit = max(1, min(int(limit), 500))
        except (TypeError, ValueError):
            clean_limit = 100
        try:
            db = get_database()
            annotations = db.activity.list_activity_annotations(
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
            return error_500(e, log, "Failed to list activity annotations")

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
        from ....db import get_database

        try:
            db = get_database()
            annotations = db.activity.list_activity_annotations(
                source_connector_id="meeting_context",
                annotation_type="meeting_context_briefing",
                limit=20,
            )
            briefing = annotations[0] if annotations else None
            runs = db.activity.list_connector_runs(
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
            return error_500(e, log, "Failed to fetch activity briefing")

    @router.post("/api/activity/enrichment/pipelines/{pipeline_id}/run")
    async def api_run_pipeline(pipeline_id: str) -> Any:
        """HS-13-08: kick off a pipeline pack on demand.

        Wraps `PipelineRunner` so the dashboard's "Refresh
        briefing" button has a single endpoint to call.
        Returns the `PipelineRunResult.to_payload()` so the
        UI can render which steps ran / were skipped /
        failed.
        """
        from ....activity_connectors import get_descriptor
        from ....connector_runtime import (
            NotAPipelineError,
            PipelineRunner,
            UnknownPipelineError,
        )
        from ....db import get_database

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
            return error_500(e, log, f"Failed to run pipeline {pipeline_id}")

    @router.get("/api/activity/enrichment/connectors/{connector_id}/runs")
    async def api_list_activity_enrichment_runs(
        connector_id: str,
        limit: int = 10,
    ) -> Any:
        """HS-13-05: per-connector run history."""
        from ....activity_connectors import get_descriptor
        from ....db import get_database

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
            runs = db.activity.list_connector_runs(
                connector_id=connector_id, limit=clean_limit
            )
            return JSONResponse(
                {
                    "connector_id": connector_id,
                    "runs": [run.to_payload() for run in runs],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to list connector runs")

    @router.get("/api/activity/enrichment/github/preview")
    async def api_preview_github_activity_enrichment(limit: int = 50) -> Any:
        try:
            from ....activity_github import CONNECTOR_ID, preview_github_cli_enrichment
            from ....db import get_database

            db = get_database()
            connector = db.activity.get_activity_enrichment_connector(CONNECTOR_ID)
            if connector is None:
                connector = db.activity.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
            records = db.activity.list_activity_records(limit=max(1, min(int(limit), 500)))
            preview = preview_github_cli_enrichment(records, limit=limit)
            return JSONResponse(
                {
                    **preview,
                    "connector": _activity_enrichment_connector_payload(connector),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to preview GitHub activity enrichment")

    @router.post("/api/activity/enrichment/github/run")
    async def api_run_github_activity_enrichment(
        payload: Optional[_ActivityCliEnrichmentRunRequest] = None,
    ) -> Any:
        try:
            from ....activity_github import CONNECTOR_ID, run_github_cli_enrichment
            from ....db import get_database

            db = get_database()
            connector = db.activity.get_activity_enrichment_connector(CONNECTOR_ID)
            if connector is None:
                connector = db.activity.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
            if not connector.enabled:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "GitHub activity enrichment connector is disabled",
                        "connector": _activity_enrichment_connector_payload(connector),
                    },
                    status_code=403,
                )

            from ....connector_packs import github_cli as github_cli_pack
            from ....connector_sdk import resolve_setting

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
            records = db.activity.list_activity_records(
                entity_type="github_pull_request",
                limit=max(1, min(int(limit), 500)),
            )
            issue_records = db.activity.list_activity_records(
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
            connector = db.activity.get_activity_enrichment_connector(CONNECTOR_ID) or connector
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
            from ....activity_jira import CONNECTOR_ID, preview_jira_cli_enrichment
            from ....db import get_database

            db = get_database()
            connector = db.activity.get_activity_enrichment_connector(CONNECTOR_ID)
            if connector is None:
                connector = db.activity.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
            records = db.activity.list_activity_records(entity_type="jira_ticket", limit=max(1, min(int(limit), 500)))
            preview = preview_jira_cli_enrichment(records, limit=limit)
            return JSONResponse(
                {
                    **preview,
                    "connector": _activity_enrichment_connector_payload(connector),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to preview Jira activity enrichment")

    @router.post("/api/activity/enrichment/jira/run")
    async def api_run_jira_activity_enrichment(
        payload: Optional[_ActivityCliEnrichmentRunRequest] = None,
    ) -> Any:
        try:
            from ....activity_jira import CONNECTOR_ID, run_jira_cli_enrichment
            from ....db import get_database

            db = get_database()
            connector = db.activity.get_activity_enrichment_connector(CONNECTOR_ID)
            if connector is None:
                connector = db.activity.upsert_activity_enrichment_connector(connector_id=CONNECTOR_ID)
            if not connector.enabled:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Jira activity enrichment connector is disabled",
                        "connector": _activity_enrichment_connector_payload(connector),
                    },
                    status_code=403,
                )

            from ....connector_packs import jira_cli as jira_cli_pack
            from ....connector_sdk import resolve_setting

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
            records = db.activity.list_activity_records(
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
            connector = db.activity.get_activity_enrichment_connector(CONNECTOR_ID) or connector
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

    return router
