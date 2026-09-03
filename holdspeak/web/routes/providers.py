"""HS-161-04 + HS-166-01: Provider routes -- connection, discovery, validation.

GET  /api/providers                                    -- manifest list
GET  /api/providers/github/connection                  -- live probe result
POST /api/providers/github/connection/recheck          -- re-probe live
GET  /api/providers/github/discover                    -- bounded discovery
POST /api/providers/github/validate-repo               -- typed repo fallback
GET  /api/providers/jira/connections                   -- all Jira connections
POST /api/providers/jira/connections                   -- add a Jira connection
POST /api/providers/jira/connections/{ref}/recheck     -- recheck one connection
POST /api/watches/{watch_id}/evaluate                  -- manual evaluate_once

Parse-and-serialize ONLY: the ProviderAdapter + WatchService docstring law.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.providers")


# The native provider families the interview already suggests (INT-010).
# Shape mirrors GitHubProviderAdapter.manifest() for uniform rendering.
_NATIVE_PROVIDERS: list[dict[str, Any]] = [
    {
        "provider_id": "native",
        "transport": "local_domain",
        "capabilities": {
            "discover": False,
            "read": True,
            "subscribe": False,
            "effect": False,
        },
        "families": ["meetings", "decisions", "door"],
    },
]


def collect_provider_manifests(
    *,
    github_adapter: Any = None,
    jira_adapter: Any = None,
    principal: Any = None,
) -> list[dict[str, Any]]:
    """Shared helper: build the manifest list for both HTTP and MCP surfaces.

    HS-166-01: ONE function builds the provider list; the HTTP route and
    the MCP ``provider.list`` tool both call this -- never duplicate the
    enumeration.  Adapters are optional: ``None`` means the provider is
    not configured (omitted from the list).

    Each provider entry carries a ``readiness`` object computed from
    persisted rows + ``shutil.which`` only (NEVER runs the CLI).
    """
    providers: list[dict[str, Any]] = list(_NATIVE_PROVIDERS)
    if github_adapter is not None:
        entry = github_adapter.manifest()
        if principal is not None and hasattr(github_adapter, "readiness"):
            entry["readiness"] = github_adapter.readiness(principal)
        providers.append(entry)
    if jira_adapter is not None:
        entry = jira_adapter.manifest()
        if principal is not None and hasattr(jira_adapter, "readiness"):
            entry["readiness"] = jira_adapter.readiness(principal)
        providers.append(entry)
    return providers


def build_providers_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["providers"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── GET /api/providers ──────────────────────────────────────────

    @router.get("/api/providers")
    async def list_providers(request: Request) -> Any:
        """The manifest list: native + github + jira providers."""
        try:
            providers = collect_provider_manifests(
                github_adapter=ctx.github_provider,
                jira_adapter=ctx.jira_provider,
                principal=principal(request),
            )
            return JSONResponse({"providers": providers})
        except Exception as exc:
            return error_500(exc, log, "Failed to list providers")

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
            result = adapter.connection_status(principal(request))
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
            result = adapter.connection_status(principal(request))
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to recheck GitHub connection")

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
            result = adapter.discover(
                principal(request),
                query=query,
                cursor=cursor,
                limit=limit,
            )
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to discover GitHub repositories")

    # ── POST /api/providers/github/validate-repo ─────────────────────

    @router.post("/api/providers/github/validate-repo")
    async def github_validate_repo(request: Request) -> Any:
        """Typed repo validation: body {owner_repo}."""
        try:
            adapter = ctx.github_provider
            if adapter is None:
                return JSONResponse(
                    {"code": "provider_not_configured",
                     "message": "GitHub provider is not configured"},
                    status_code=404,
                )
            body = await request.json()
            owner_repo = body.get("owner_repo", "")
            if not owner_repo:
                return JSONResponse(
                    {"code": "validation_error",
                     "message": "owner_repo is required"},
                    status_code=400,
                )
            result = adapter.validate_repo(principal(request), owner_repo)
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to validate GitHub repository")

    # ── GET /api/providers/jira/connections ───────────────────────────

    @router.get("/api/providers/jira/connections")
    async def jira_connections(request: Request) -> Any:
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
            known = adapter.known_accounts(p)
            return JSONResponse({"connections": rows, "known_accounts": known})
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

    # ── POST /api/providers/jira/connections/{ref}/recheck ────────────

    @router.post("/api/providers/jira/connections/{ref}/recheck")
    async def jira_connection_recheck(ref: str, request: Request) -> Any:
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

    # ── POST /api/watches/{watch_id}/evaluate ────────────────────────

    @router.post("/api/watches/{watch_id}/evaluate")
    async def evaluate_watch(watch_id: str, request: Request) -> Any:
        """Manual evaluate_once (WatchService.evaluate_once).

        Manual only; scheduling is P5's.
        """
        try:
            result = ctx.watch_service.evaluate_once(
                principal(request), watch_id,
            )
            return JSONResponse({"success": True, **result})
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            status = int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to evaluate watch")

    return router
