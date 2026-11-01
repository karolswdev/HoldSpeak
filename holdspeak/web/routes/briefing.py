"""The briefing page and its packages (PG-DIRECTION DIR1, DIRECTION-2026-10-31.md §6, §11).

GET  /b/{token}                              the page shell (web/briefing.html); 404 shell for a bad token
GET  /api/b/{token}                          {package, items: [{ref, state, outcome?, …}], later}   BRIEFING
GET  /api/b/{token}/evidence/{ref}/{pane}    {pane, kind: rows | code, …}                         BRIEFING
POST /api/b/{token}/answer                   {ref, choice, reason?, later?} → {item}               BRIEFING
POST /api/reach/packages                     {refs, kind?, send?} → {id, token, path, link, expires_at} OWNER
POST /api/reach/packages/{id}/revoke                                                              OWNER
GET  /api/reach/packages?program_id=         the open pages of one Program                         OWNER
GET  /api/reach                              channels, ladder, quiet hours, digest, open packages   OWNER (DIR6)
PUT  /api/reach                              {telegram?, later_means?, digest?, phone_app?}         OWNER (DIR6)
POST /api/reach/later                        {ref, later} → {until, words, parked}                 OWNER (DIR4)
POST /api/reach/telegram/pair                → {code, words, expires_at}                           OWNER (DIR5)
DELETE /api/reach/telegram/pair              Unpair                                                OWNER (DIR5)
PUT  /api/reach/telegram/token               {token} → {token: keystore | missing}                  OWNER (DIR5)
POST /api/reach/digest                       send the digest now                                   OWNER (DIR5)

The page routes are admitted at the edge by ``principals.briefing_route``
alone; each handler here checks the token (hash, expiry, revocation) through
``services/briefing_service.py`` and is the only authority. An unknown, an
expired and a revoked token answer the same 404 with no data. Every page
answer carries ``Cache-Control: no-store``, ``Referrer-Policy: no-referrer``,
``X-Robots-Tag: noindex`` and the page's Content-Security-Policy. The token is
never logged: a failure logs the route's name, not its path.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...services.errors import ServiceError
from ..context import WebContext

log = get_logger("web.routes.briefing")

_SHELL = Path(__file__).resolve().parent.parent.parent / "static" / "_built" / "briefing.html"

PAGE_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Robots-Tag": "noindex",
    # §6 "Headers", plus fonts and images as data: (the build inlines its small
    # webfont files, and the shared stylesheet draws its control marks as
    # data: SVG); scripts, connections and frames stay 'self' only.
    "Content-Security-Policy": ("default-src 'self'; script-src 'self'; connect-src 'self'; "
                                "font-src 'self' data:; img-src 'self' data:; frame-ancestors 'none'"),
}


def _service() -> Any:
    from ...services.briefing_service import default_briefing_service

    return default_briefing_service()


def _tailnet_base(port: int) -> str | None:
    """The hub's tailnet address (§6 "The address"), when Tailscale Serve
    proxies to this hub; ``None`` on a rig (``HOLDSPEAK_RECORDINGS=off``
    reads no Tailscale) or with no Serve."""
    try:
        from ...recordings.service import recordings_on
        from ...recordings.tailnet import tailnet_base

        return tailnet_base(port) if port and recordings_on() else None
    except Exception:
        return None


def _address(request: Request) -> str:
    return str(getattr(request.client, "host", "") or "unknown")


async def _body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = None
    return body if isinstance(body, dict) else {}


def _refused(exc: ServiceError, headers: dict[str, str] | None = None) -> JSONResponse:
    payload = dict(exc.context)
    status = int(payload.pop("status", 409))
    return JSONResponse({"error": exc.code, "code": exc.code, "detail": exc.detail, **payload},
                        status_code=status, headers=headers)


async def _owner(request: Request, fn: Callable[[Any], Any], *, status: int = 200, what: str) -> JSONResponse:
    principal = getattr(request.state, "principal", None)
    try:
        return JSONResponse(await run_in_threadpool(fn, principal), status_code=status)
    except ServiceError as exc:
        return _refused(exc)
    except Exception as exc:
        log.error(f"reach {what} failed: {exc}", exc_info=True)
        return JSONResponse({"error": "reach_failed", "code": "reach_failed",
                             "detail": "The page service failed. Nothing changed. The log names the cause."},
                            status_code=500)


async def _page(request: Request, fn: Callable[[], Any], *, what: str) -> JSONResponse:
    """A page route: the miss limit, the headers, the one 404 for every
    token that reads nothing."""
    from ...services.briefing_service import MISSES

    address = _address(request)
    if MISSES.blocked(address):
        return JSONResponse({"error": "too_many_tries", "code": "too_many_tries",
                             "detail": "Too many tries. Wait one minute."}, status_code=429, headers=PAGE_HEADERS)
    try:
        return JSONResponse(await run_in_threadpool(fn), headers=PAGE_HEADERS)
    except ServiceError as exc:
        if exc.code == "page_expired":
            MISSES.miss(address)
        return _refused(exc, PAGE_HEADERS)
    except Exception as exc:
        # The route's name only: the path carries the token.
        log.error(f"briefing page {what} failed: {type(exc).__name__}", exc_info=False)
        return JSONResponse({"error": "page_failed", "code": "page_failed",
                             "detail": "The page could not answer. Nothing changed. Open the item on your desk."},
                            status_code=500, headers=PAGE_HEADERS)


def build_briefing_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter()

    @router.get("/b/{token}", include_in_schema=False)
    async def briefing_page(token: str, request: Request) -> Any:
        from ...services.briefing_service import MISSES

        def known() -> bool:
            try:
                _service()._package(token)
                return True
            except ServiceError:
                return False

        status = 200
        address = _address(request)
        if MISSES.blocked(address) or not await run_in_threadpool(known):
            MISSES.miss(address)
            status = 404
        try:
            html = await run_in_threadpool(_SHELL.read_text, "utf-8")
        except OSError:
            html = ("<!doctype html><html><head><meta charset='utf-8'/><title>HoldSpeak</title></head>"
                    "<body><p>The page is not built. Run npm run build in web.</p></body></html>")
        return HTMLResponse(html, status_code=status, headers=PAGE_HEADERS)

    @router.get("/api/b/{token}")
    async def api_briefing_read(token: str, request: Request) -> Any:
        return await _page(request, lambda: _service().read(token), what="read")

    @router.get("/api/b/{token}/evidence/{ref}/{pane}")
    async def api_briefing_evidence(token: str, ref: str, pane: str, request: Request) -> Any:
        return await _page(request, lambda: _service().evidence(token, ref, pane), what="evidence")

    @router.post("/api/b/{token}/answer")
    async def api_briefing_answer(token: str, request: Request) -> Any:
        body = await _body(request)
        return await _page(request, lambda: _service().answer(
            token, body.get("ref"), body.get("choice"), reason=body.get("reason"), later=body.get("later"),
        ), what="answer")

    @router.post("/api/reach/packages")
    async def api_reach_package_make(request: Request) -> Any:
        body = await _body(request)
        port = int((request.scope.get("server") or ("", 0))[1] or 0)

        def make(principal: Any) -> dict[str, Any]:
            made = _service().make(principal, body.get("refs"), kind=body.get("kind") or "item",
                                   send=body.get("send"), head=body.get("head"))
            base = _tailnet_base(port)
            return {**made, "link": f"{base}{made['path']}" if base else None}

        return await _owner(request, make, status=201, what="make")

    @router.post("/api/reach/packages/{package_id}/revoke")
    async def api_reach_package_revoke(package_id: str, request: Request) -> Any:
        return await _owner(request, lambda principal: _service().revoke(principal, package_id), what="revoke")

    @router.get("/api/reach/packages")
    async def api_reach_packages(request: Request) -> Any:
        program_id = str(request.query_params.get("program_id") or "")
        return await _owner(request, lambda principal: {"packages": _service().packages(principal, program_id)},
                            what="list")

    # ── DIR4 to DIR6: Later, his settings, Telegram ──────────────────

    @router.get("/api/reach")
    async def api_reach(request: Request) -> Any:
        return await _owner(request, lambda principal: _reach().status(principal), what="read")

    @router.put("/api/reach")
    async def api_reach_put(request: Request) -> Any:
        body = await _body(request)

        def save(principal: Any) -> dict[str, Any]:
            _reach().save_settings(principal, body)
            return _reach().status(principal)

        return await _owner(request, save, what="save")

    @router.post("/api/reach/later")
    async def api_reach_later(request: Request) -> Any:
        body = await _body(request)
        return await _owner(request, lambda principal: _reach().later(
            principal, body.get("ref"), body.get("later"), via="desk"), what="later")

    @router.post("/api/reach/telegram/pair")
    async def api_reach_telegram_pair(request: Request) -> Any:
        return await _owner(request, lambda principal: _telegram().start_pairing(principal), status=201,
                            what="pair")

    @router.delete("/api/reach/telegram/pair")
    async def api_reach_telegram_unpair(request: Request) -> Any:
        return await _owner(request, lambda principal: _telegram().unpair(principal), what="unpair")

    @router.put("/api/reach/telegram/token")
    async def api_reach_telegram_token(request: Request) -> Any:
        body = await _body(request)
        return await _owner(request, lambda principal: _telegram().save_token(principal, body.get("token")),
                            what="token")

    @router.post("/api/reach/digest")
    async def api_reach_digest(request: Request) -> Any:
        return await _owner(request, lambda principal: _reach().send_digest_now(principal), what="digest")

    return router


def _reach() -> Any:
    from ...services.reach_service import default_reach_service

    return default_reach_service()


def _telegram() -> Any:
    from ...services.telegram_reach import default_telegram_reach

    return default_telegram_reach()


__all__ = ["PAGE_HEADERS", "build_briefing_router"]
