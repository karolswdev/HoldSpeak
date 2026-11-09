"""PARKED 20261109 (ops/settings): provider routes no client calls.

Parked from ``holdspeak/web/routes/providers.py``: POST /api/providers/github/validate-repo,
POST /api/providers/jira/search, POST /api/providers/jira/validate-scope,
POST /api/providers/confluence/validate. The MCP tools provider.github_validate_repo,
provider.jira_search, provider.jira_validate_scope and provider.confluence_validate_space
reach the same adapters. Not imported. Kept for history; restore with ``git revert``.
"""
from __future__ import annotations


class _ParkedBody:  # the handlers, at their route-builder indent; never imported
    def _routes(self, router, principal, ctx):  # noqa: ANN001
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


        @router.post("/api/providers/jira/search")
        async def jira_search(request: Request) -> Any:
            """JQL search: body {connection_ref, jql, limit?, enrich?}."""
            try:
                adapter = ctx.jira_provider
                if adapter is None:
                    return JSONResponse(
                        {"code": "provider_not_configured",
                         "message": "Jira provider is not configured"},
                        status_code=404,
                    )
                body = await request.json()
                conn_ref = body.get("connection_ref", "")
                jql = body.get("jql", "")
                if not conn_ref or not jql:
                    return JSONResponse(
                        {"code": "validation_error",
                         "message": "connection_ref and jql are required"},
                        status_code=400,
                    )
                result = adapter.search(
                    principal(request),
                    conn_ref,
                    jql=jql,
                    limit=body.get("limit", 50),
                    enrich=bool(body.get("enrich", False)),
                )
                return JSONResponse(result)
            except ValidationError as exc:
                return JSONResponse(
                    {"code": exc.code, "message": exc.detail},
                    status_code=400,
                )
            except Exception as exc:
                return error_500(exc, log, "Failed to search Jira issues")


        @router.post("/api/providers/jira/validate-scope")
        async def jira_validate_scope(request: Request) -> Any:
            """Typed project validation: body {connection_ref, project_key}."""
            try:
                adapter = ctx.jira_provider
                if adapter is None:
                    return JSONResponse(
                        {"code": "provider_not_configured",
                         "message": "Jira provider is not configured"},
                        status_code=404,
                    )
                body = await request.json()
                conn_ref = body.get("connection_ref", "")
                project_key = body.get("project_key", "")
                if not conn_ref or not project_key:
                    return JSONResponse(
                        {"code": "validation_error",
                         "message": "connection_ref and project_key are required"},
                        status_code=400,
                    )
                result = adapter.validate_scope(
                    principal(request),
                    conn_ref,
                    project_key,
                )
                return JSONResponse(result)
            except ValidationError as exc:
                return JSONResponse(
                    {"code": exc.code, "message": exc.detail},
                    status_code=400,
                )
            except Exception as exc:
                return error_500(exc, log, "Failed to validate Jira scope")


        @router.post("/api/providers/confluence/validate")
        async def confluence_validate_scope(request: Request) -> Any:
            """Typed space validation: body {connection_ref, space_key}."""
            try:
                adapter = ctx.confluence_provider
                if adapter is None:
                    return JSONResponse(
                        {"code": "provider_not_configured",
                         "message": "Confluence provider is not configured"},
                        status_code=404,
                    )
                body = await request.json()
                conn_ref = body.get("connection_ref", "")
                space_key = body.get("space_key", "")
                if not conn_ref or not space_key:
                    return JSONResponse(
                        {"code": "validation_error",
                         "message": "connection_ref and space_key are required"},
                        status_code=400,
                    )
                result = adapter.validate_scope(
                    principal(request),
                    conn_ref,
                    space_key,
                )
                return JSONResponse(result)
            except ValidationError as exc:
                return JSONResponse(
                    {"code": exc.code, "message": exc.detail},
                    status_code=400,
                )
            except Exception as exc:
                return error_500(exc, log, "Failed to validate Confluence scope")

