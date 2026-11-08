"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/programs.py``: POST /api/programs/{program_id}/from-desk, POST /api/programs/{program_id}/propose_fix, POST /api/programs/{program_id}/steps/{step_id}/checkpoint, POST /api/programs/{program_id}/steps/{step_id}/remove.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Programs transport (2026-10-28); the work is ``services/program_service.py``.

GET    /api/programs?q=&project_id=&person_id=     the Programs, waiting first (PG-REQ: Find a program,
                                                   Project, Person; the group is the face's)
POST   /api/programs                               create {title, goal, repository | project_id,
                                                   base_branch, control, check_command, template,
                                                   default_profile, default_engine, reviewer_profile,
                                                   reviewer_engine, prefer_idle, origin_ref, for_person_id,
                                                   runs_on, allowed_profiles, may_handoff, usage_warning_share}
GET    /api/programs/templates                     the templates (§10)
GET    /api/programs/{id}                          the Program, its steps, checkpoints, your turn
PATCH  /api/programs/{id}                          {title, goal, control, prefer_idle, project_id, spend_limit_usd,
                                                   default_profile, default_engine, reviewer_profile ("none": no
                                                   reviewer), reviewer_engine; PG-LANG: review_depth,
                                                   planner_engine, budget_tokens, night, within, delivery,
                                                   rounds_before_start, check_command, for_person_id}
POST   /api/programs/{id}/plan                     {steps: [...], size: "auto"|null, replace: bool,
                                                   before: <step_id> (insert before), waits: bool}
POST   /api/programs/{id}/from-desk                one step per open action of its Project
POST   /api/programs/{id}/start | /park | /resume
POST   /api/programs/{id}/steps/{sid}/checkpoint   {line}
POST   /api/programs/{id}/steps/{sid}/decide       {kind, choice, finding_id?, reason?, via?,
                                                   expected_delivery_checkpoint_id? (a delivery)}
POST   /api/programs/{id}/steps/{sid}/race         {n}
POST   /api/programs/{id}/steps/{sid}/handoff      {to: profile | {profile, engine}, preview: bool} (owner only;
                                                   PG19: preview returns the brief, nothing moves)
POST   /api/programs/{id}/checkpoints/{cid}/start-from  PG20, Start from here: a new step from the
                                                   checkpoint's pinned ref (his press adds it; the step's
                                                   own agent asks, and the ladder decides)
POST   /api/programs/{id}/decisions/{did}/overturn undo one engine decision (owner only)
POST   /api/programs/{id}/close                    he closes a finished Program (Secure)
PATCH  /api/programs/{id}/steps/{sid}              PG-REQ: change a step (the §8 fields its state leaves
                                                   open); before: <step_id> | "end" moves it; 409
                                                   step_frozen names the field and the reason
POST   /api/programs/{id}/steps/{sid}/amend        {line}: a line added to a started step's brief
POST   /api/programs/{id}/steps/{sid}/remove       PG-LANG: remove a Planned or Ready step (409 step_stays)
POST   /api/programs/from-action                  JRN13: a Drafting Program from a project's action {action_id, project_id?}
POST   /api/programs/tonight                       PG-LANG LANG12: add a Door task, a note line or a step to tonight
POST   /api/programs/{id}/requirements             {text, kind?, step_id?, each_step?, required?, spec?}
PATCH  /api/programs/{id}/requirements/{rid}       {text?, kind?, required?, spec?}
POST   /api/programs/{id}/requirements/{rid}/decide {choice: met|unmet|waive|send_back, line?} (owner)
POST   /api/programs/{id}/proposals/{cid}/decide   {choice: add|apply|send|skip} (owner)
GET    /api/programs/{id}/requirements/{rid}/evidence  the log text or the shot image
GET    /api/programs/{id}/text                     PG-LANG LANG1: the Program text {text, revision, version}
POST   /api/programs/{id}/text                     {text, dry_run (default true; preview too), base?, allow_lower?: [row ids]}
                                                   -> {changes, patch, allowed_text, applied, text, revision}
GET    /api/programs/{id}/shape                    LANG3: the engine that shapes {engine, capability} (null: none)
POST   /api/programs/{id}/shape                    LANG3 {sentence, apply?, pending?}: one engine call; the text_apply answer
DELETE /api/programs/{id}/shape/held               LANG5: Not this on the rows a call left on the desk
                                                   + {say, question, engine, latency_ms, proposed_text, base, decision}
POST   /api/programs/{id}/plan/draft               LANG6 {goal?, template?, budget?; Split: text, split}: one engine
                                                   call; the text_apply answer, each row source "plan" and an added
                                                   step's size, + {say, counts, sizes, budget, engine, latency_ms}
POST   /api/programs/{id}/plan/programs            JRN1 {programs, which: all | place}: Apply all / Apply this one of a draft that proposes several Programs
POST   /api/programs/{id}/rounds                   LANG9 {names?}: the interview rounds, each open (the five defaults)
POST   /api/programs/{id}/rounds/{name}/next       LANG9: one engine call; {round, state, done, question?, engine}
POST   /api/programs/{id}/rounds/{name}/answer     LANG9 {question_id?, answer | option | skip | not_this, apply?}:
                                                   the = line, then one shaping call; the rows (source
                                                   "round:<name>") in the text_apply answer + {round, question}
POST   /api/programs/{id}/rounds/{name}/decide     LANG9 {choice: done | skip | reopen}

Every handler runs the service off the event loop (``run_in_threadpool``).
"""

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ....logging_config import get_logger
from ....principals import Principal, PrincipalKind
from ....services.errors import NotFound, ServiceError, ValidationError
from ...context import WebContext

log = get_logger("web.routes.programs")

_CREATE_FIELDS = (
    "title", "goal", "repository", "project_id", "base_branch", "control", "check_command", "template",
    "default_profile", "default_engine", "reviewer_profile", "reviewer_engine", "prefer_idle", "origin_ref",
    "for_person_id", "spend_limit_usd", "runs_on", "allowed_profiles", "may_handoff", "usage_warning_share", "may_call",
)


_UPDATE_FIELDS = (
    "title", "goal", "control", "prefer_idle", "project_id", "spend_limit_usd", "default_profile", "default_engine",
    "reviewer_profile", "reviewer_engine", "runs_on", "allowed_profiles", "may_handoff", "usage_warning_share", "may_call",
    # PG-LANG: the fields the Program text writes.
    "review_depth", "planner_engine", "budget_tokens", "night", "within", "delivery", "rounds_before_start",
    "check_command", "for_person_id",
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
    from ....services.program_service import default_program_service

    return default_program_service()


def parked_build_programs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.post("/api/programs/{program_id}/from-desk")
    async def api_programs_from_desk(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().plan_from_project(principal, program_id))

    @router.post("/api/programs/{program_id}/propose_fix")
    async def api_programs_propose_fix(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().propose_fix(principal, program_id))

    @router.post("/api/programs/{program_id}/steps/{step_id}/checkpoint")
    async def api_programs_checkpoint(program_id: str, step_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().checkpoint(principal, program_id, step_id, str(body.get("line") or "")))

    @router.post("/api/programs/{program_id}/steps/{step_id}/remove")
    async def api_programs_step_remove(program_id: str, step_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().remove_step(principal, program_id, step_id))

    return router


__all__ = ["parked_build_programs_router"]
