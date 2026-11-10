# PARKED 20261109 (ops/connections): the hand-written provider routes.
# The routes are produced from ``holdspeak/provider_operations.py`` (``web/routes/providers.py``).
# Not imported. Restore with ``git revert``.
"""HS-161-04 + HS-166-01 + HS-166-02 + HS-174-07: Provider routes.

GET  /api/providers                                         -- manifest list
GET  /api/providers/github/connection                       -- live probe result
POST /api/providers/github/connection/recheck               -- re-probe live
GET  /api/providers/github/discover                         -- bounded discovery
POST /api/providers/github/validate-repo                    -- typed repo fallback
GET  /api/providers/jira/connections                        -- all Jira connections
POST /api/providers/jira/connections                        -- add a Jira connection
POST /api/providers/jira/connections/{ref}/recheck          -- recheck one connection
GET  /api/providers/jira/discover                           -- bounded Jira discovery
POST /api/providers/jira/search                             -- JQL search
POST /api/providers/jira/validate-scope                     -- typed project validation
GET  /api/providers/confluence/connections                   -- all Confluence connections
POST /api/providers/confluence/connections/{ref}/recheck     -- recheck one connection
GET  /api/providers/confluence/discover                      -- bounded space discovery
POST /api/providers/confluence/validate                      -- typed space validation
POST /api/watches/{watch_id}/evaluate                        -- manual evaluate_once

Parse-and-serialize ONLY: the ProviderAdapter + WatchService docstring law.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ServiceError, ValidationError
from ...services.provider_manifest_service import (
    collect_provider_manifests,
)
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.providers")


def build_providers_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["providers"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── GET /api/providers ──────────────────────────────────────────

    @router.get("/api/providers")
    def list_providers(request: Request) -> Any:
        """The manifest list: native + github + jira providers."""
        try:
            providers = collect_provider_manifests(
                github_adapter=ctx.github_provider,
                jira_adapter=ctx.jira_provider,
                confluence_adapter=ctx.confluence_provider,
                principal=principal(request),
            )
            return JSONResponse({"providers": providers})
        except Exception as exc:
            return error_500(exc, log, "Failed to list providers")

    # ── GET /api/providers/github/connection ─────────────────────────

    # ── POST /api/providers/github/connection/recheck ────────────────

    # ── GET /api/providers/github/discover ───────────────────────────

    @router.get("/api/providers/github/discover")
    async def github_discover(
        request: Request,
        query: str | None = None,
        cursor: int | None = None,
        limit: int = 30,
    ) -> Any:
        """Bounded discovery on the wire (adapter.discover; pagination surfaced)."""
        try:
            adapter = ctx.github_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "GitHub provider is not configured"},
                    status_code=404,
                )
            result = await run_in_threadpool(
                adapter.discover,
                principal(request),
                query=query,
                cursor=cursor,
                limit=limit,
            )
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to discover GitHub repositories")

    # ── POST /api/providers/github/validate-repo ─────────────────────

    # ── GET /api/providers/jira/connections ───────────────────────────

    def _enrich_jira_row(row: dict[str, Any]) -> dict[str, Any]:
        """Derive account + recovery from the raw DB row for the wire.

        DB rows carry ``external_connection_ref`` (site|email), ``state``,
        ``last_error_code``, ``last_error_detail`` but NOT ``account`` or
        ``recovery``.  The UI needs them: account for display, recovery
        for the in-world login command.  HS-166-04.
        """
        ref = row.get("external_connection_ref") or row.get("connection_ref") or ""
        site, email = ("", "")
        if "|" in ref:
            parts = ref.split("|", 1)
            site, email = parts[0], parts[1]
        enriched = dict(row)
        enriched["connection_ref"] = ref
        enriched["account"] = {"site": site, "email": email}
        state = row.get("state", "")
        if state == "owner_action_required":
            enriched["recovery"] = {
                "command": f"acli jira auth login --site {site} --email {email} --token",
                "hint": "Authenticate with your Atlassian API token",
            }
        else:
            enriched.setdefault("recovery", None)
        return enriched

    @router.get("/api/providers/jira/connections")
    def jira_connections(request: Request) -> Any:
        """List all Jira connections + known acli accounts."""
        try:
            adapter = ctx.jira_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "Jira provider is not configured"},
                    status_code=404,
                )
            p = principal(request)
            rows = adapter.list_connections(p)
            enriched = [_enrich_jira_row(r) for r in rows]
            known = adapter.known_accounts(p)
            return JSONResponse({"connections": enriched, "known_accounts": known})
        except Exception as exc:
            return error_500(exc, log, "Failed to list Jira connections")

    # ── POST /api/providers/jira/connections ──────────────────────────

    @router.post("/api/providers/jira/connections")
    async def jira_add_connection(request: Request) -> Any:
        """Add a Jira connection: body {site, email}."""
        try:
            adapter = ctx.jira_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "Jira provider is not configured"},
                    status_code=404,
                )
            body = await request.json()
            site = body.get("site", "")
            email = body.get("email", "")
            if not site or not email:
                return JSONResponse(
                    {"code": "validation_error",
                     "message": "site and email are required"},
                    status_code=400,
                )
            result = adapter.add_connection(principal(request), site, email)
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to add Jira connection")

    # ── DELETE /api/providers/{jira|confluence}/connections/{ref} ─────
    # Betterment ST2: Accounts' Remove (with Undo on the face: Undo adds the
    # row again).  It removes HoldSpeak's row only, never acli's profile.

    @router.delete("/api/providers/{provider}/connections/{ref}")
    def atlassian_remove_connection(provider: str, ref: str, request: Request) -> Any:
        """Remove one Jira or Confluence connection row."""
        try:
            adapter = {"jira": ctx.jira_provider, "confluence": ctx.confluence_provider}.get(provider)
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": f"{provider} provider is not configured"},
                    status_code=404,
                )
            removed = adapter.remove_connection(principal(request), ref)
            if not removed:
                return JSONResponse({"code": "not_found", "message": "No such account"}, status_code=404)
            return JSONResponse({"removed": True, "provider": provider, "connection_ref": ref})
        except ValidationError as exc:
            return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, f"Failed to remove {provider} connection")

    # ── POST /api/providers/jira/connections/{ref}/recheck ────────────

    @router.post("/api/providers/jira/connections/{ref}/recheck")
    def jira_connection_recheck(ref: str, request: Request) -> Any:
        """Recheck one Jira connection (switch + status probe)."""
        try:
            adapter = ctx.jira_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "Jira provider is not configured"},
                    status_code=404,
                )
            result = adapter.connection_status(principal(request), ref)
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to recheck Jira connection")

    # ── GET /api/providers/jira/discover ────────────────────────────

    @router.get("/api/providers/jira/discover")
    def jira_discover(
        request: Request,
        connection_ref: str = "",
        kind: str = "projects",
        query: str = "",
        project_key: str = "",
        cursor: int | None = None,
        limit: int = 30,
    ) -> Any:
        """Bounded Jira discovery (adapter.discover; pagination surfaced)."""
        try:
            adapter = ctx.jira_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "Jira provider is not configured"},
                    status_code=404,
                )
            if not connection_ref:
                return JSONResponse(
                    {"code": "validation_error",
                     "message": "connection_ref is required"},
                    status_code=400,
                )
            result = adapter.discover(
                principal(request),
                connection_ref,
                kind=kind,
                query=query,
                project_key=project_key,
                cursor=cursor,
                limit=limit,
            )
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to discover Jira resources")

    # ── POST /api/providers/jira/search ──────────────────────────────

    # ── POST /api/providers/jira/validate-scope ──────────────────────

    # ── GET /api/providers/confluence/connections ───────────────────────

    def _enrich_confluence_row(row: dict[str, Any]) -> dict[str, Any]:
        """Derive account + recovery from the raw DB row for the wire.

        Same grammar as ``_enrich_jira_row``.  HS-174-07.
        """
        ref = row.get("external_connection_ref") or row.get("connection_ref") or ""
        site, email = ("", "")
        if "|" in ref:
            parts = ref.split("|", 1)
            site, email = parts[0], parts[1]
        enriched = dict(row)
        enriched["connection_ref"] = ref
        enriched["account"] = {"site": site, "email": email}
        state = row.get("state", "")
        if state == "owner_action_required":
            enriched["recovery"] = {
                "command": f"acli confluence auth login --site {site} --email {email} --token",
                "hint": "Authenticate with your Atlassian API token",
            }
        else:
            enriched.setdefault("recovery", None)
        return enriched

    @router.get("/api/providers/confluence/connections")
    def confluence_connections(request: Request) -> Any:
        """List all Confluence connections."""
        try:
            adapter = ctx.confluence_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "Confluence provider is not configured"},
                    status_code=404,
                )
            p = principal(request)
            rows = adapter.list_connections(p)
            enriched = [_enrich_confluence_row(r) for r in rows]
            return JSONResponse({"connections": enriched})
        except Exception as exc:
            return error_500(exc, log, "Failed to list Confluence connections")

    # ── POST /api/providers/confluence/connections ───────────────────
    # PHILO-17 U29: Confluence gets its Add, as Jira has (body {site, email}).

    @router.post("/api/providers/confluence/connections")
    async def confluence_add_connection(request: Request) -> Any:
        """Add a Confluence connection: body {site, email}."""
        try:
            adapter = ctx.confluence_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "Confluence provider is not configured"},
                    status_code=404,
                )
            body = await request.json()
            site = body.get("site", "") if isinstance(body, dict) else ""
            email = body.get("email", "") if isinstance(body, dict) else ""
            if not site or not email:
                return JSONResponse(
                    {"code": "validation_error",
                     "message": "site and email are required"},
                    status_code=400,
                )
            result = adapter.add_connection(principal(request), site, email)
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to add Confluence connection")

    # ── POST /api/providers/confluence/connections/{ref}/recheck ────────

    # ── GET /api/providers/confluence/discover ────────────────────────

    @router.get("/api/providers/confluence/discover")
    def confluence_discover(
        request: Request,
        connection_ref: str = "",
        kind: str = "spaces",
        query: str = "",
        cursor: int | None = None,
        limit: int = 30,
    ) -> Any:
        """Bounded Confluence discovery (spaces)."""
        try:
            adapter = ctx.confluence_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "Confluence provider is not configured"},
                    status_code=404,
                )
            if not connection_ref:
                return JSONResponse(
                    {"code": "validation_error",
                     "message": "connection_ref is required"},
                    status_code=400,
                )
            result = adapter.discover(
                principal(request),
                connection_ref,
                kind=kind,
                query=query,
                cursor=cursor,
                limit=limit,
            )
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to discover Confluence resources")

    # ── POST /api/providers/confluence/validate ───────────────────────

    # ── POST /api/watches/{watch_id}/evaluate ────────────────────────

    @router.post("/api/watches/{watch_id}/evaluate")
    def evaluate_watch(watch_id: str, request: Request) -> Any:
        """Manual evaluate_once (WatchService.evaluate_once).

        Manual only; scheduling is P5's.
        """
        # PHILO-9-02: the declared project.watch.evaluate, admitted (egress):
        # one kernel operation and its receipt.
        from ... import operations
        from ._room_kernel import kernel_fields, kernel_refusal, refusal_fields

        try:
            result, kernel = operations.for_context(ctx).invoke_receipted(
                principal(request), "project.watch.evaluate", {"watch_id": watch_id},
                held={"graduated_only": False},
            )
            return JSONResponse({"success": True, **result, **kernel_fields(kernel)})
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            status = 404 if isinstance(exc, NotFound) else int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail, **refusal_fields(exc)},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to evaluate watch")

    return router
