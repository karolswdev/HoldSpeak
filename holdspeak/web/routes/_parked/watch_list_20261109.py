# PARKED 2026-11-09: The project watch list is produced from its operation.
class _ParkedBody:
        # ── GET /api/projects/{project_id}/watches ───────────────────

        @router.get("/api/projects/{project_id}/watches")
        def list_project_watches(
            project_id: str, request: Request,
            state: str | None = None,
        ) -> Any:
            try:
                watches = ctx.watch_service.list_watches(
                    principal(request),
                    project_id=project_id,
                    state=state,
                )
                return JSONResponse({"watches": watches})
            except Exception as exc:
                return error_500(exc, log, "Failed to list project watches")
