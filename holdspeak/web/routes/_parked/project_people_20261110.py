# PARKED: the Room people projection is a declared ProjectService operation.
class _ParkedBody:
    @router.get("/api/projects/{project_id}/people")
    def api_project_people(project_id: str, request: Request) -> Any:
        """The Room's PEOPLE projection (read-only).

        HS-200-14: linked people with their open commitments and observable
        facts, the owners nobody is linked to (ambiguous / not linked), and
        the ledger's own state -- a locked or missing store is NAMED here,
        never an empty list.  The ``people`` key keeps 172-07's row shape.
        """
        try:
            from ...services.room_people_service import room_people_preparation
            people_svc = ctx.people_service
            result = room_people_preparation(
                service, people_svc, project_id, principal(request),
            )
            return JSONResponse(result)
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project people")
