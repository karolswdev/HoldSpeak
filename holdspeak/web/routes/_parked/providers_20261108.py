"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/providers.py``: POST /api/providers/confluence/connections/{ref}/recheck, GET /api/providers/github/connection, POST /api/providers/github/connection/recheck.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
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

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ValidationError
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.providers")


def parked_build_providers_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["providers"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── GET /api/providers ──────────────────────────────────────────

    # ── GET /api/providers/github/connection ─────────────────────────

    @router.get("/api/providers/github/connection")
    async def github_connection(request: Request) -> Any:
        """The persisted connection status (adapter.connection_status)."""
        try:
            adapter = ctx.github_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "GitHub provider is not configured"},
                    status_code=404,
                )
            result = await run_in_threadpool(adapter.connection_status, principal(request))
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to get GitHub connection status")

    # ── POST /api/providers/github/connection/recheck ────────────────

    @router.post("/api/providers/github/connection/recheck")
    async def github_connection_recheck(request: Request) -> Any:
        """Re-probe live (calls connection_status fresh)."""
        try:
            adapter = ctx.github_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "GitHub provider is not configured"},
                    status_code=404,
                )
            from starlette.concurrency import run_in_threadpool

            # PHILO-10-02: the probe runs gh -- off the event loop.
            result = await run_in_threadpool(adapter.connection_status, principal(request))
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to recheck GitHub connection")

    # ── GET /api/providers/github/discover ───────────────────────────

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

    # ── POST /api/providers/jira/connections ──────────────────────────

    # ── DELETE /api/providers/{jira|confluence}/connections/{ref} ─────
    # Betterment ST2: Accounts' Remove (with Undo on the face: Undo adds the
    # row again).  It removes HoldSpeak's row only, never acli's profile.

    # ── POST /api/providers/jira/connections/{ref}/recheck ────────────

    # ── GET /api/providers/jira/discover ────────────────────────────

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

    # ── POST /api/providers/confluence/connections ───────────────────
    # PHILO-17 U29: Confluence gets its Add, as Jira has (body {site, email}).

    # ── POST /api/providers/confluence/connections/{ref}/recheck ────────

    @router.post("/api/providers/confluence/connections/{ref}/recheck")
    def confluence_connection_recheck(ref: str, request: Request) -> Any:
        """Recheck one Confluence connection (switch + status probe)."""
        try:
            adapter = ctx.confluence_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "Confluence provider is not configured"},
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
            return error_500(exc, log, "Failed to recheck Confluence connection")

    # ── GET /api/providers/confluence/discover ────────────────────────

    # ── POST /api/providers/confluence/validate ───────────────────────

    # ── POST /api/watches/{watch_id}/evaluate ────────────────────────

    return router
