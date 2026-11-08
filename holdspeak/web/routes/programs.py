"""Programs transport (2026-10-28); the work is ``services/program_service.py``.

The routes are produced from the one table of Programs operations
(``services/program_operations.py``), the rows the MCP tools come from too
(2026-11-08). The evidence read answers a file, so it stays hand-written
(``HAND_WRITTEN``). The paths:

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
POST   /api/programs/{id}/start | /park | /resume
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
from __future__ import annotations

import inspect
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...principals import Principal, PrincipalKind
from ...services import program_operations
from ...services.errors import NotFound, ServiceError, ValidationError
from ..context import WebContext

log = get_logger("web.routes.programs")


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


def _evidence(op: program_operations.ProgramOperation) -> Callable[..., Any]:
    """The log text or the shot image of one requirement (a file, not JSON)."""

    call = op.call

    async def endpoint(program_id: str, requirement_id: str, request: Request) -> Any:
        principal = _principal(request)

        def read() -> Any:
            try:
                found = call(program_operations.program_service(), principal,
                             {"program_id": program_id, "requirement_id": requirement_id})
            except ServiceError as exc:
                return _refused(exc)
            if found["media"].startswith("image/"):
                return FileResponse(found["path"], media_type=found["media"])
            from pathlib import Path

            text = Path(found["path"]).read_text(encoding="utf-8", errors="replace")
            return PlainTextResponse(text[-200_000:])

        return await run_in_threadpool(read)

    endpoint.__name__ = endpoint.__qualname__ = op.handler_name
    return endpoint


#: The routes the table cannot produce: each answers a file.
HAND_WRITTEN: dict[str, Callable[[program_operations.ProgramOperation], Callable[..., Any]]] = {
    "program.requirement_evidence": _evidence,
}


def _endpoint(op: program_operations.ProgramOperation) -> Callable[..., Any]:
    """One row's handler: the path parameters over the JSON body (the query for
    a GET), the row's HTTP call off the event loop, its status."""
    method, path = op.http or ("", "")
    call = op.web or op.call
    names = [part[1:-1] for part in path.split("/") if part.startswith("{")]

    async def endpoint(request: Request, **params: str) -> Any:
        principal = _principal(request)
        source = dict(request.query_params) if method == "GET" else await _body(request)
        args = {**source, **params}
        return await _call(lambda: call(program_operations.program_service(), principal, args), status=op.status)

    # FastAPI reads the path parameters and the handler name from the
    # signature and the name: the OpenAPI document stays the one it was.
    endpoint.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
        [inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, annotation=str) for name in names]
        + [inspect.Parameter("request", inspect.Parameter.KEYWORD_ONLY, annotation=Request)],
        return_annotation=Any,
    )
    endpoint.__name__ = endpoint.__qualname__ = op.handler_name
    return endpoint


def build_programs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    for op in program_operations.OPERATIONS:
        if op.http is None:
            continue
        method, path = op.http
        make = HAND_WRITTEN.get(op.name, _endpoint)
        router.add_api_route(path, make(op), methods=[method])
    return router


__all__ = ["HAND_WRITTEN", "build_programs_router"]
