"""Ask transport adapters; orchestration belongs to :mod:`holdspeak.services.ask_service`."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .... import db as hsdb
from ....db import get_observer

def _database() -> Any:
    return getattr(hsdb, "get_database")()
from ....grounding_rails import hydrate_rails_refs
from ....services.ask_service import AskService
from ....services.errors import ServiceError
from ....principals import Principal, PrincipalKind
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _run_frame
from ....logging_config import get_logger
log=get_logger("web.routes.primitives")

def _error(exc: ServiceError) -> JSONResponse:
    payload=dict(exc.context); payload.setdefault("error",exc.detail)
    # Betterment Q1: every refusal names its reason token, so the face says
    # why in words (runWords.ts) and never "did not answer" for a question
    # that never reached the engine.
    payload.setdefault("reason",AskService.refusal_reason(exc))
    if exc.code == "grounding_not_found": return JSONResponse(payload,status_code=400)
    return JSONResponse(payload,status_code=int(payload.pop("status", 400 if exc.code == "validation_error" else 409)))

def build_ask_service(ctx: WebContext) -> AskService:
    """The hub's Ask transport, assembled once.

    HS-200-41 lifted this out of ``build_ask_router`` so the ask-task Resume
    route can dispatch through the SAME transport under a saved
    ``invocation_id`` instead of assembling a second, divergent one.
    """
    from ..sync import _hub_model_name
    from .._thread_factory import thread_service_from_ctx
    # Betterment Q7: an Ask on an HTTP engine that takes tool calls runs the
    # hub's tool loop (the Thread turn) with the Ask's prompt and palette.
    return AskService(_database(),hub_model=lambda: _hub_model_name(ctx),broadcast=lambda state, **frame: _run_frame(ctx,state,**frame),rails_hydrator=lambda refs,principal: hydrate_rails_refs(refs,principal=principal),observer=get_observer(),progress=lambda event: _ask_progress(ctx,event),thread_service=lambda **overrides: thread_service_from_ctx(ctx,**overrides),text=lambda event: _ask_text(ctx,event))

def _ask_progress(ctx: WebContext, event: dict[str, Any]) -> None:
    """Betterment Q2: one running Ask's progress (busy, trying again) to the face."""
    if ctx.broadcast is None: return
    try: ctx.broadcast("ask_progress", event)
    except Exception as exc: log.debug(f"ask progress frame dropped: {exc}")

def _ask_text(ctx: WebContext, event: dict[str, Any]) -> None:
    """Ask hub gap 1: one running Ask's words so far, to the face."""
    if ctx.broadcast is None: return
    try: ctx.broadcast("ask_text", event)
    except Exception as exc: log.debug(f"ask text frame dropped: {exc}")

def build_ask_router(ctx: WebContext) -> APIRouter:
    router=APIRouter()
    def principal(request: Request) -> Principal:
        return getattr(request.state, "principal", Principal(PrincipalKind.OWNER, "owner-session"))
    def service() -> AskService:
        return build_ask_service(ctx)
    @router.get("/api/models")
    async def api_list_models(request: Request) -> Any:
        try: return JSONResponse({"models":service().list_models(principal(request))})
        except Exception as exc: return error_500(exc,log,"Failed to list models")
    @router.get("/api/ask/engine")
    async def api_ask_engine(request: Request) -> Any:
        # Betterment Q7: can the Answers engine use the desk's tools? The
        # Ask window's engine line says so.
        try:
            import asyncio
            return JSONResponse(await asyncio.to_thread(service().engine_tools))
        except Exception as exc: return error_500(exc,log,"Failed to read the Answers engine")
    @router.post("/api/grounding/resolve")
    async def api_resolve_grounding(request: Request) -> Any:
        body=await _json_body(request)
        if body is None: return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try: return JSONResponse(service().resolve_grounding(principal(request),body.get("refs") if isinstance(body.get("refs"),list) else []))
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to resolve grounding")
    @router.post("/api/ask")
    async def api_ask(request: Request) -> Any:
        body=await _json_body(request)
        if body is None: return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:
            # HS-200-41 (ruling B3): the caller may pin the invocation identity
            # it already saved, so an answer that lands after the tab is gone
            # can be CLAIMED out of ask_results instead of paid for twice.
            # AskService has always taken one (ask_service.py); only the
            # transport never offered it.
            invocation_id=(str(body.get("invocation_id")).strip() or None) if body.get("invocation_id") else None
            context=body.get("context") if isinstance(body.get("context"),list) else []
            if body.get("thread") is True or body.get("thread_id"):
                # Betterment Q4: the Ask window keeps every Ask as a thread;
                # a thread_id continues that thread.  Ask hub gap 5: the run
                # is its own task, so a window that closes (its request
                # dropped) does not end it; the answer is kept and claimed
                # back through /api/ask/runs.
                import asyncio
                run=asyncio.ensure_future(service().ask_in_thread(principal(request),str(body.get("prompt") or ""),body.get("grounding"),thread_id=str(body.get("thread_id") or ""),lens=str(body.get("lens") or "Ask"),context=context,invocation_id=invocation_id,source_snapshot=body.get("source_snapshot")))
                run.add_done_callback(lambda task: task.cancelled() or task.exception())
                result=await asyncio.shield(run)
                return JSONResponse(result)
            result=await service().ask(principal(request),str(body.get("prompt") or ""),body.get("grounding"),lens=str(body.get("lens") or "Ask"),context=context,model=body.get("model"),inference_target_id=body.get("inference_target_id"),profile_id=body.get("profile_id"),max_tokens=body.get("max_tokens"),temperature=body.get("temperature"),invocation_id=invocation_id,source_snapshot=body.get("source_snapshot"))
            return JSONResponse(result)
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to run ask")
    @router.post("/api/ask/keep")
    async def api_ask_keep(request: Request) -> Any:
        body=await _json_body(request)
        if body is None: return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:
            result=service().keep(principal(request),str(body.get("output") or ""),body.get("context") if isinstance(body.get("context"),list) else [],lens=str(body.get("lens") or "Ask"),prompt=str(body.get("prompt") or ""),grounding=body.get("grounding"))
            return JSONResponse(result,status_code=201)
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to keep ask")
    @router.get("/api/ask/runs")
    async def api_ask_runs(request: Request) -> Any:
        # Ask hub gap 5: the asks a window left running, by invocation id.
        from ....services.ask_service import runs
        ids=[part for part in str(request.query_params.get("ids") or "").split(",") if part.strip()][:20]
        return JSONResponse({"runs":runs(ids)})
    @router.post("/api/ask/{invocation_id}/cancel")
    async def api_cancel_ask(invocation_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service().cancel(principal(request), invocation_id))
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to cancel ask")
    return router
