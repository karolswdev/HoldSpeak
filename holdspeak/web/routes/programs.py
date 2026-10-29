"""Programs transport (2026-10-28); the work is ``services/program_service.py``.

GET    /api/programs                               the Programs, waiting first
POST   /api/programs                               create {title, goal, repository | project_id,
                                                   base_branch, control, check_command, template,
                                                   default_profile, default_engine, reviewer_profile,
                                                   reviewer_engine, prefer_idle, origin_ref, for_person_id,
                                                   runs_on, allowed_profiles, may_handoff, usage_warning_share}
GET    /api/programs/templates                     the templates (§10)
GET    /api/programs/{id}                          the Program, its steps, checkpoints, your turn
PATCH  /api/programs/{id}                          {title, goal, control, prefer_idle, project_id, spend_limit_usd,
                                                   default_profile, default_engine, reviewer_profile, reviewer_engine}
POST   /api/programs/{id}/plan                     {steps: [...], size: "auto"|null, replace: bool}
POST   /api/programs/{id}/from-desk                one step per open action of its Project
POST   /api/programs/{id}/start | /park | /resume
POST   /api/programs/{id}/steps/{sid}/checkpoint   {line}
POST   /api/programs/{id}/steps/{sid}/decide       {kind, choice, finding_id?, reason?}
POST   /api/programs/{id}/steps/{sid}/race         {n}
POST   /api/programs/{id}/steps/{sid}/handoff      {to: profile | {profile, engine}, preview: bool} (owner only;
                                                   PG19: preview returns the brief, nothing moves)
POST   /api/programs/{id}/decisions/{did}/overturn undo one engine decision (owner only)
POST   /api/programs/{id}/close                    he closes a finished Program (Secure)

Every handler runs the service off the event loop (``run_in_threadpool``).
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...principals import Principal, PrincipalKind
from ...services.errors import NotFound, ServiceError, ValidationError
from ..context import WebContext

log = get_logger("web.routes.programs")

_CREATE_FIELDS = (
    "title", "goal", "repository", "project_id", "base_branch", "control", "check_command", "template",
    "default_profile", "default_engine", "reviewer_profile", "reviewer_engine", "prefer_idle", "origin_ref",
    "for_person_id", "spend_limit_usd", "runs_on", "allowed_profiles", "may_handoff", "usage_warning_share", "may_call",
)


_UPDATE_FIELDS = (
    "title", "goal", "control", "prefer_idle", "project_id", "spend_limit_usd", "default_profile", "default_engine",
    "reviewer_profile", "reviewer_engine", "runs_on", "allowed_profiles", "may_handoff", "usage_warning_share", "may_call",
)


def _principal(request: Request) -> Any:
    return getattr(request.state, "principal", Principal(PrincipalKind.OWNER, "owner-session"))


async def _body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = None
    return body if isinstance(body, dict) else {}


def _refused(exc: ServiceError) -> JSONResponse:
    payload = dict(exc.context)
    status = int(payload.pop("status", 404 if isinstance(exc, NotFound) else 400 if isinstance(exc, ValidationError) else 409))
    return JSONResponse({"error": exc.code, "code": exc.code, "detail": exc.detail, **payload}, status_code=status)


async def _call(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return _refused(exc)
    except Exception as exc:
        log.error(f"programs route failed: {exc}", exc_info=True)
        return JSONResponse({"error": "program_failed", "code": "program_failed",
                             "detail": "The program service failed. The log names the cause."}, status_code=500)


def _service() -> Any:
    from ...services.program_service import default_program_service

    return default_program_service()


def build_programs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/programs")
    async def api_programs_list(request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().list(principal))

    @router.get("/api/programs/templates")
    async def api_programs_templates() -> Any:
        from ...program_templates import TEMPLATES

        return await _call(lambda: {"templates": [
            {key: template[key] for key in ("id", "name", "description")} for template in TEMPLATES]})

    @router.post("/api/programs")
    async def api_programs_create(request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        args = {key: body.get(key) for key in _CREATE_FIELDS if key in body}
        args.setdefault("title", "")
        return await _call(lambda: _service().create(principal, **args), status=201)

    @router.get("/api/programs/{program_id}")
    async def api_programs_get(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().get(principal, program_id))

    @router.patch("/api/programs/{program_id}")
    async def api_programs_update(program_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        fields = {key: body[key] for key in _UPDATE_FIELDS if key in body}
        return await _call(lambda: _service().update(principal, program_id, **fields))

    @router.post("/api/programs/{program_id}/plan")
    async def api_programs_plan(program_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().plan(
            principal, program_id, steps=body.get("steps") if isinstance(body.get("steps"), list) else [],
            size=body.get("size"), replace=bool(body.get("replace")),
        ))

    @router.post("/api/programs/{program_id}/from-desk")
    async def api_programs_from_desk(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().plan_from_project(principal, program_id))

    @router.post("/api/programs/{program_id}/start")
    async def api_programs_start(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().start(principal, program_id))

    @router.post("/api/programs/{program_id}/park")
    async def api_programs_park(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().park(principal, program_id))

    @router.post("/api/programs/{program_id}/resume")
    async def api_programs_resume(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().resume(principal, program_id))

    @router.post("/api/programs/{program_id}/steps/{step_id}/checkpoint")
    async def api_programs_checkpoint(program_id: str, step_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().checkpoint(principal, program_id, step_id, str(body.get("line") or "")))

    @router.post("/api/programs/{program_id}/steps/{step_id}/decide")
    async def api_programs_decide(program_id: str, step_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().decide(
            principal, program_id, step_id, kind=str(body.get("kind") or ""), choice=str(body.get("choice") or ""),
            finding_id=body.get("finding_id"), reason=body.get("reason"),
        ))

    @router.post("/api/programs/{program_id}/steps/{step_id}/race")
    async def api_programs_race(program_id: str, step_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().race(principal, program_id, step_id, int(body.get("n") or 0)))

    @router.post("/api/programs/{program_id}/steps/{step_id}/handoff")
    async def api_programs_handoff(program_id: str, step_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().handoff(
            principal, program_id, step_id, body.get("to"), preview=bool(body.get("preview")),
        ))

    @router.post("/api/programs/{program_id}/decisions/{decision_id}/overturn")
    async def api_programs_overturn(program_id: str, decision_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().overturn(principal, program_id, decision_id))

    @router.post("/api/programs/{program_id}/close")
    async def api_programs_close(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().close(principal, program_id))

    return router


__all__ = ["build_programs_router"]
