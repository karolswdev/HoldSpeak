"""Authenticated, content-redacting transport for the encrypted People sidecar."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

from ...principals import UNAUTHENTICATED
from ...services.people_service import OwnerAliasTaken, PeopleServiceError, SeriesAlreadyLinked
from ...services.errors import NotFound
from ...services.workbench_service import WorkbenchService
from ...services.project_service import ProjectService
from ..context import WebContext


def _failure(exc: PeopleServiceError) -> HTTPException:
    """The public error code deliberately never contains relationship content."""
    code = str(exc)
    if code == "people_owner_required":
        return HTTPException(status_code=403, detail=code)
    if code in {"people_store_unavailable", "people_store_write_failed"}:
        return HTTPException(status_code=503, detail="people_store_unavailable")
    if code == "series_already_linked" and isinstance(exc, SeriesAlreadyLinked):
        return HTTPException(status_code=409, detail={
            "code": "series_already_linked",
            "holder_id": exc.holder_id,
            "holder_name": exc.holder_name,
        })
    if code == "owner_alias_taken" and isinstance(exc, OwnerAliasTaken):
        return HTTPException(status_code=409, detail={
            "code": "owner_alias_taken",
            "holder_id": exc.holder_id,
            "holder_name": exc.holder_name,
        })
    if code == "owner_alias_reserved":
        return HTTPException(status_code=422, detail=code)
    if code.endswith("_not_found"):
        return HTTPException(status_code=404, detail=code)
    return HTTPException(status_code=400, detail=code)


def build_people_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/people", tags=["people"])
    service = ctx.people_service
    if service is None:
        # Isolated route fixtures must inject the encrypted service.  There is no
        # fallback to the ordinary database or an in-memory plaintext notebook.
        raise RuntimeError("People service is not configured")

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def workbenches() -> WorkbenchService:
        from ...db import get_database, get_observer
        return WorkbenchService(get_database(), observer=get_observer())

    def projects() -> ProjectService:
        from ...db import get_database, get_observer
        return ProjectService(get_database(), observer=get_observer())

    @router.get("/readiness")
    async def readiness(request: Request) -> dict[str, str]:
        try:
            return service.readiness(principal(request))
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/resolve")
    async def resolve(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        """HS-172-04: resolve a Watch identity to a People relationship id.

        Returns only the relationship id -- never the name or alias
        (Article III: nothing crosses the People boundary).
        """
        try:
            identity = str(body.get("identity") or "").strip()
            if not identity:
                return {"relationship_id": None}
            result = service.resolve_relationship_by_watch_identity(identity)
            rel = result.get("relationship")
            return {"relationship_id": rel.get("id") if rel else None}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/setup")
    async def setup(request: Request) -> dict[str, str]:
        try:
            return service.setup(principal(request))
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships")
    async def relationships(request: Request, include_archived: bool = False) -> dict[str, list[dict[str, Any]]]:
        try:
            return {"relationships": service.list_relationships(principal(request), include_archived=include_archived)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships", status_code=201)
    async def create_relationship(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"relationship": service.create_relationship(principal(request), body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}")
    async def relationship(request: Request, relationship_id: str) -> dict[str, Any]:
        try:
            return {"relationship": service.get_relationship(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/archive")
    async def archive_relationship(request: Request, relationship_id: str) -> dict[str, Any]:
        try:
            return {"relationship": service.archive_relationship(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/projects/{project_id}")
    async def link_project(request: Request, relationship_id: str, project_id: str) -> dict[str, Any]:
        try:
            owner = principal(request)
            projects().get_project(owner, project_id)
            return {"relationship": service.link_project(owner, relationship_id, project_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc
        except NotFound as exc:
            raise HTTPException(status_code=404, detail="people_project_not_found") from exc

    @router.delete("/relationships/{relationship_id}/projects/{project_id}")
    async def unlink_project(request: Request, relationship_id: str, project_id: str) -> dict[str, Any]:
        try:
            return {"relationship": service.unlink_project(principal(request), relationship_id, project_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}/brief")
    async def relationship_brief(request: Request, relationship_id: str) -> dict[str, Any]:
        """HS-149-04: read-time 1:1 brief across the encrypted/plaintext boundary."""
        try:
            from ...db import get_database
            db = get_database()
            return {"brief": service.one_on_one_brief(principal(request), relationship_id, db=db)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}/one-on-ones")
    async def one_on_ones(request: Request, relationship_id: str) -> dict[str, list[dict[str, Any]]]:
        try:
            return {"one_on_ones": service.list_one_on_ones(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/one-on-ones", status_code=201)
    async def create_one_on_one(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"one_on_one": service.create_one_on_one(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/one-on-ones/{session_id}/agenda", status_code=201)
    async def add_agenda_item(request: Request, session_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"agenda_item": service.add_agenda_item(principal(request), session_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/requests", status_code=201)
    async def create_request(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"request": service.create_request(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}/notes")
    async def notes(request: Request, relationship_id: str) -> dict[str, list[dict[str, Any]]]:
        try:
            return {"notes": service.list_notes(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/notes", status_code=201)
    async def create_note(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"note": service.create_note(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/calendar-links")
    async def link_calendar_series(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"relationship": service.link_calendar_series(
                principal(request), relationship_id,
                str(body.get("uid") or ""),
                str(body.get("source_id") or ""),
                str(body.get("label") or ""),
            )}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.delete("/relationships/{relationship_id}/calendar-links")
    async def unlink_calendar_series(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"relationship": service.unlink_calendar_series(
                principal(request), relationship_id,
                str(body.get("uid") or ""),
                str(body.get("source_id") or ""),
            )}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/owner-aliases")
    async def link_owner_alias(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"relationship": service.link_owner_alias(
                principal(request), relationship_id,
                str(body.get("alias") or ""),
            )}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.delete("/relationships/{relationship_id}/owner-aliases")
    async def unlink_owner_alias(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"relationship": service.unlink_owner_alias(
                principal(request), relationship_id,
                str(body.get("alias") or ""),
            )}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/requests/{request_id}/accept")
    async def accept_request(request: Request, request_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"commitment": service.accept_request(principal(request), request_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/history")
    async def history(request: Request, relationship_id: str | None = None) -> dict[str, Any]:
        try:
            return {"history": service.history_summary(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/commitments/{commitment_id}/execution")
    async def commitment_execution(request: Request, commitment_id: str) -> dict[str, Any]:
        try:
            commitment = service.get_commitment(principal(request), commitment_id)
            items = []
            wb = workbenches()
            for link in commitment.get("execution_links") or []:
                if not isinstance(link, dict) or link.get("kind") != "workbench_item":
                    continue
                try:
                    item = wb.get_item(principal(request), str(link.get("workbench_id") or ""), str(link.get("item_id") or ""))
                except NotFound:
                    item = {**link, "status": "missing", "result": None, "result_artifact_id": None}
                items.append(item)
            return {"commitment": commitment, "items": items}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/commitments/{commitment_id}/workbench", status_code=201)
    async def send_commitment_to_workbench(
        request: Request,
        commitment_id: str,
        body: dict[str, Any] = Body(default={}),
    ) -> dict[str, Any]:
        try:
            owner = principal(request)
            commitment = service.get_commitment(owner, commitment_id)
            workbench_id = str(body.get("workbench_id") or "").strip()
            if not workbench_id:
                raise PeopleServiceError("people_workbench_required")
            wb = workbenches()
            wb.get_workbench(owner, workbench_id)
            for link in commitment.get("execution_links") or []:
                if isinstance(link, dict) and link.get("workbench_id") == workbench_id:
                    try:
                        existing = wb.get_item(owner, workbench_id, str(link.get("item_id") or ""))
                        return {"commitment": commitment, "item": existing, "created": False}
                    except NotFound:
                        pass
            text = str(commitment.get("body") or "").strip()
            relationship = service.get_relationship(owner, str(commitment.get("relationship_id") or ""))
            project_grounding: list[dict[str, Any]] = []
            project_service = projects()
            for project_id in relationship.get("project_refs") or []:
                try:
                    project = project_service.get_project(owner, str(project_id))
                    resources = project_service.list_resources(owner, str(project_id))
                except NotFound:
                    continue
                project_grounding.append({
                    "id": project.get("id"),
                    "name": project.get("name"),
                    "description": project.get("description"),
                    "keywords": project.get("keywords"),
                    "context": project.get("context"),
                    "resources": [resource.get("resource_ref") for resource in resources],
                })
            item = wb.add_item(
                owner,
                workbench_id,
                title=text,
                body=(
                    "Complete this relationship follow-through item. Return a concrete deliverable "
                    "and a concise completion summary.\n\nCommitment:\n" + text
                ),
                grounding={"people_commitment": text, "projects": project_grounding},
                context={
                    "source": "people_commitment",
                    "people_commitment_id": commitment_id,
                    "relationship_id": commitment.get("relationship_id"),
                    "project_ids": [project.get("id") for project in project_grounding],
                },
            )
            try:
                linked = service.attach_execution(
                    owner,
                    commitment_id,
                    workbench_id=workbench_id,
                    item_id=str(item["id"]),
                )
            except Exception:
                wb.delete_item(owner, workbench_id, str(item["id"]))
                raise
            return {"commitment": linked, "item": item, "created": True}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc
        except NotFound as exc:
            raise HTTPException(status_code=404, detail="people_workbench_not_found") from exc

    @router.post("/commitments/{commitment_id}/transition")
    async def transition_commitment(
        request: Request,
        commitment_id: str,
        body: dict[str, Any] = Body(default={}),
    ) -> dict[str, Any]:
        """Browser twin of the MCP commitment-transition application call."""
        try:
            result = service.transition(
                principal(request),
                f"people:{commitment_id}",
                str(body.get("verb") or ""),
            )
            return {"transition": result}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/commitments/{commitment_id}/satisfy")
    async def satisfy_commitment(
        request: Request,
        commitment_id: str,
        body: dict[str, Any] = Body(default={}),
    ) -> dict[str, Any]:
        try:
            owner = principal(request)
            commitment = service.get_commitment(owner, commitment_id)
            wb = workbenches()
            evidence: list[dict[str, Any]] = []
            for link in commitment.get("execution_links") or []:
                if not isinstance(link, dict) or link.get("kind") != "workbench_item":
                    continue
                try:
                    item = wb.get_item(owner, str(link.get("workbench_id") or ""), str(link.get("item_id") or ""))
                except NotFound:
                    continue
                evidence.append({
                    "kind": "workbench_item",
                    "workbench_id": item["workbench_id"],
                    "item_id": item["id"],
                    "status": item["status"],
                    "artifact_id": item.get("result_artifact_id"),
                    "completed_at": item.get("completed_at"),
                })
            result = service.satisfy_commitment(
                owner,
                commitment_id,
                rationale=str(body.get("rationale") or ""),
                evidence=evidence,
            )
            return {"commitment": result}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    return router
