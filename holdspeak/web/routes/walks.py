"""The Walk (2026-11-07): a guided feedback walk on the desk from one link.

POST /api/walks                 the script → {id, token, url_path: "/w/<token>"}        OWNER
GET  /api/walks/{id}            the script, the answers and the shot folder              OWNER
GET  /w/{token}                 a known token: 303 to the desk with ``?walk=<token>``;
                                an unknown token: the desk shell with 404
GET  /api/w/{token}             {title, steps, answers}                                  WALK TOKEN
POST /api/w/{token}/answer      {ref, choice, words?, window_png?} → {ref, choice, …}    WALK TOKEN

The token routes are admitted at the edge by ``principals.walk_route`` alone;
the handler checks the token through ``services/walk_service.py`` and is the
only authority. The token creates no owner session and reaches no other route.
Wrong tokens count against the briefing page's per-address limit (one limit).
The token is never logged.

The answer route is bounded before it reads (Codex review of #1808): a
blocked address gets 429 and an unknown token 404 (one miss) with no body
read; a body over WALK_BODY_BYTES = 24 MiB gets 413 before JSON parses it
(one 16 MiB PNG is 21.4 MiB in base64, so the largest valid shot still fits).
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...services.errors import ServiceError
from ..context import WebContext
from .briefing import PAGE_HEADERS, BodyTooLarge, _address, _body, _bounded_body, _refused, _too_large
from .pages import _react_shell

log = get_logger("web.routes.walks")

#: The 404 shell is the desk itself (it opens as usual), so it keeps the
#: page headers but not the page's Content-Security-Policy.
WALK_BODY_BYTES = 24 * 1024 * 1024

SHELL_HEADERS = {key: value for key, value in PAGE_HEADERS.items() if key != "Content-Security-Policy"}


def _service() -> Any:
    from ...services.walk_service import default_walk_service

    return default_walk_service()


def _misses() -> Any:
    from ...services.briefing_service import MISSES

    return MISSES


async def _run(fn: Callable[[], Any], *, status: int = 200, headers: dict[str, str] | None = None,
               what: str) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status, headers=headers)
    except ServiceError as exc:
        return _refused(exc, headers)
    except Exception as exc:
        # The route's name only: a token path must never reach the log.
        log.error(f"walk {what} failed: {type(exc).__name__}", exc_info=False)
        return JSONResponse({"error": "walk_failed", "code": "walk_failed",
                             "detail": "The walk could not answer. Nothing changed."},
                            status_code=500, headers=headers)


def _too_many() -> JSONResponse:
    return JSONResponse({"error": "too_many_tries", "code": "too_many_tries",
                         "detail": "Too many tries. Wait one minute."}, status_code=429, headers=PAGE_HEADERS)


async def _page(request: Request, fn: Callable[[], Any], *, what: str) -> JSONResponse:
    address = _address(request)
    if _misses().blocked(address):
        return _too_many()

    def guarded() -> Any:
        try:
            return fn()
        except ServiceError as exc:
            if exc.code == "walk_not_found":
                _misses().miss(address)
            raise

    return await _run(guarded, headers=PAGE_HEADERS, what=what)


def build_walks_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter()

    @router.post("/api/walks")
    async def api_walk_create(request: Request) -> Any:
        body = await _body(request)
        return await _run(lambda: _service().create(body), status=201, what="create")

    @router.get("/api/walks/{walk_id}")
    async def api_walk_read(walk_id: str) -> Any:
        return await _run(lambda: _service().read(walk_id), what="read")

    @router.get("/w/{token}", include_in_schema=False)
    async def walk_page(token: str, request: Request) -> Any:
        address = _address(request)
        if not _misses().blocked(address) and await run_in_threadpool(_service().known, token):
            return RedirectResponse(f"/?walk={token}", status_code=303, headers=PAGE_HEADERS)
        _misses().miss(address)
        shell = await run_in_threadpool(_react_shell)
        return HTMLResponse(shell.body, status_code=404, headers=SHELL_HEADERS)

    @router.get("/api/w/{token}")
    async def api_walk_page(token: str, request: Request) -> Any:
        return await _page(request, lambda: _service().page(token), what="page")

    @router.post("/api/w/{token}/answer")
    async def api_walk_answer(token: str, request: Request) -> Any:
        # The miss limit and the token first: nothing reads the body before.
        address = _address(request)
        if _misses().blocked(address):
            return _too_many()
        if not await run_in_threadpool(_service().known, token):
            _misses().miss(address)
            from ...services.walk_service import WalkRefused

            return _refused(WalkRefused("walk_not_found", "This walk is not known.", status=404), PAGE_HEADERS)
        try:
            body = await _bounded_body(request, WALK_BODY_BYTES)
        except BodyTooLarge:
            return _too_large(PAGE_HEADERS)
        return await _page(request, lambda: _service().answer(
            token, body.get("ref"), body.get("choice"), words=body.get("words"),
            window_png=body.get("window_png"),
        ), what="answer")

    return router


__all__ = ["build_walks_router"]
