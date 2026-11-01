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
POST   /api/programs/{id}/steps/{sid}/decide       {kind, choice, finding_id?, reason?, via?}
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
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
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
    from ...services.program_service import default_program_service

    return default_program_service()


def build_programs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/programs")
    async def api_programs_list(request: Request) -> Any:
        principal, query = _principal(request), request.query_params
        return await _call(lambda: _service().list(principal, q=query.get("q"), project_id=query.get("project_id"),
                                                   person_id=query.get("person_id")))

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

    @router.post("/api/programs/from-action")
    async def api_programs_from_action(request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().from_action(principal, body.get("action_id"),
                                                          project_id=body.get("project_id")), status=201)

    @router.post("/api/programs/tonight")
    async def api_programs_add_to_night(request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().add_to_night(principal, kind=body.get("kind"), item_id=body.get("item_id"),
                                                           line=body.get("line"), program_id=body.get("program_id")))

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
            size=body.get("size"), replace=bool(body.get("replace")), before=body.get("before") or None,
            waits=body.get("waits") is not False,
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
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().park(principal, program_id, reason=body.get("reason")))

    @router.post("/api/programs/{program_id}/propose_fix")
    async def api_programs_propose_fix(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().propose_fix(principal, program_id))

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
            finding_id=body.get("finding_id"), reason=body.get("reason"), via=body.get("via"),
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

    @router.post("/api/programs/{program_id}/checkpoints/{checkpoint_id}/start-from")
    async def api_programs_start_from(program_id: str, checkpoint_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().start_from(principal, program_id, checkpoint_id))

    @router.post("/api/programs/{program_id}/decisions/{decision_id}/overturn")
    async def api_programs_overturn(program_id: str, decision_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().overturn(principal, program_id, decision_id))

    @router.patch("/api/programs/{program_id}/steps/{step_id}")
    async def api_programs_step_change(program_id: str, step_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().change_step(principal, program_id, step_id, **body))

    @router.post("/api/programs/{program_id}/steps/{step_id}/remove")
    async def api_programs_step_remove(program_id: str, step_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().remove_step(principal, program_id, step_id))

    @router.post("/api/programs/{program_id}/steps/{step_id}/amend")
    async def api_programs_step_amend(program_id: str, step_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().amend(principal, program_id, step_id, body.get("line")))

    @router.post("/api/programs/{program_id}/requirements")
    async def api_programs_require(program_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        args = {key: body[key] for key in ("text", "kind", "step_id", "each_step", "required", "spec") if key in body}
        return await _call(lambda: _service().require(principal, program_id, **args), status=201)

    @router.patch("/api/programs/{program_id}/requirements/{requirement_id}")
    async def api_programs_requirement_edit(program_id: str, requirement_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        args = {key: body[key] for key in ("text", "kind", "required", "spec") if key in body}
        return await _call(lambda: _service().edit_requirement(principal, program_id, requirement_id, **args))

    @router.post("/api/programs/{program_id}/requirements/{requirement_id}/decide")
    async def api_programs_requirement_decide(program_id: str, requirement_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().decide_requirement(
            principal, program_id, requirement_id, str(body.get("choice") or ""), line=body.get("line")))

    @router.post("/api/programs/{program_id}/proposals/{proposal_id}/decide")
    async def api_programs_proposal_decide(program_id: str, proposal_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().decide_proposal(principal, program_id, proposal_id,
                                                              str(body.get("choice") or "")))

    @router.get("/api/programs/{program_id}/requirements/{requirement_id}/evidence")
    async def api_programs_requirement_evidence(program_id: str, requirement_id: str, request: Request) -> Any:
        principal = _principal(request)

        def read() -> Any:
            try:
                found = _service().requirement_evidence(principal, program_id, requirement_id)
            except ServiceError as exc:
                return _refused(exc)
            if found["media"].startswith("image/"):
                return FileResponse(found["path"], media_type=found["media"])
            from pathlib import Path

            text = Path(found["path"]).read_text(encoding="utf-8", errors="replace")
            return PlainTextResponse(text[-200_000:])

        return await run_in_threadpool(read)

    @router.get("/api/programs/{program_id}/text")
    async def api_programs_text(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().text_get(principal, program_id))

    @router.post("/api/programs/{program_id}/text")
    async def api_programs_text_apply(program_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        dry = body.get("dry_run", body.get("preview", True))
        allow = body.get("allow_lower") if isinstance(body.get("allow_lower"), list) else []
        return await _call(lambda: _service().text_apply(
            principal, program_id, body.get("text"), dry_run=dry is not False, base=body.get("base"),
            allow_lower=[str(item) for item in allow]))

    @router.get("/api/programs/{program_id}/shape")
    async def api_programs_shape_engine(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().shape_engine(principal, program_id))

    @router.post("/api/programs/{program_id}/shape")
    async def api_programs_shape(program_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        pending = body.get("pending") if isinstance(body.get("pending"), str) else None
        return await _call(lambda: _service().shape(principal, program_id, body.get("sentence"),
                                                    apply=body.get("apply") is True, pending=pending))

    @router.delete("/api/programs/{program_id}/shape/held")
    async def api_programs_shape_held_drop(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().drop_held_shape(principal, program_id))

    @router.post("/api/programs/{program_id}/plan/draft")
    async def api_programs_plan_draft(program_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().plan_draft(
            principal, program_id, goal=body.get("goal"), template=body.get("template"), budget=body.get("budget"),
            text=body.get("text"), split=body.get("split")))

    @router.post("/api/programs/{program_id}/plan/programs")
    async def api_programs_plan_programs(program_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().apply_programs(principal, program_id, body.get("programs"),
                                                             body.get("which", "all")))

    @router.post("/api/programs/{program_id}/rounds")
    async def api_programs_rounds_open(program_id: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        names = body.get("names") if isinstance(body.get("names"), list) else None
        return await _call(lambda: _service().rounds_open(principal, program_id, names))

    @router.post("/api/programs/{program_id}/rounds/{name}/next")
    async def api_programs_round_next(program_id: str, name: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().round_next(principal, program_id, name))

    @router.post("/api/programs/{program_id}/rounds/{name}/answer")
    async def api_programs_round_answer(program_id: str, name: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().round_answer(
            principal, program_id, name, answer=body.get("answer"), option=body.get("option"),
            question_id=body.get("question_id"), skip=body.get("skip") is True, not_this=body.get("not_this") is True,
            apply=body.get("apply") is True))

    @router.post("/api/programs/{program_id}/rounds/{name}/decide")
    async def api_programs_round_decide(program_id: str, name: str, request: Request) -> Any:
        principal, body = _principal(request), await _body(request)
        return await _call(lambda: _service().round_decide(principal, program_id, name, body.get("choice")))

    @router.post("/api/programs/{program_id}/close")
    async def api_programs_close(program_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().close(principal, program_id))

    return router


__all__ = ["build_programs_router"]
