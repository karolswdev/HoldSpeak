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

import json
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.errors import ServiceError
from ...settings_operations import SETTINGS_ROUTE_OPERATIONS, TELEGRAM_SECRET_OPERATIONS
from ..context import WebContext
from ..operation_routes import operation_router
from ._mount import mount_router

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


def _invoke(ctx: Any, request: Request, name: str, args: dict[str, Any]) -> Any:
    """One declared briefing row (``walk_operations.py``) through the hub's
    contract, else one over the module's briefing service."""
    registry = operations.for_context(ctx, briefing_service=_service)
    return registry.invoke(getattr(request.state, "principal", UNAUTHENTICATED), name, args, shape="web")


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


#: The largest body a briefing page answer reads (a choice, a reason, a time).
PAGE_BODY_BYTES = 1024 * 1024


class BodyTooLarge(Exception):
    """A token route's body is over its limit; the handler reads no more."""


async def _bounded_body(request: Request, limit: int) -> dict[str, Any]:
    """The JSON object of a token route's body, read to at most ``limit``
    bytes: a larger Content-Length is refused before any read, and a streamed
    body is refused at the first chunk past the limit (``BodyTooLarge``)."""
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            if int(declared) > limit:
                raise BodyTooLarge()
        except ValueError:
            raise BodyTooLarge() from None
    raw = bytearray()
    async for chunk in request.stream():
        raw += chunk
        if len(raw) > limit:
            raise BodyTooLarge()
    try:
        body = json.loads(bytes(raw)) if raw else None
    except ValueError:
        body = None
    return body if isinstance(body, dict) else {}


def _too_large(headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse({"error": "body_too_large", "code": "body_too_large",
                         "detail": "The answer is too large. Nothing changed."}, status_code=413, headers=headers)


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
        return await _page(request, lambda: _invoke(ctx, request, "briefing.read", {"token": token}), what="read")

    @router.get("/api/b/{token}/evidence/{ref}/{pane}")
    async def api_briefing_evidence(token: str, ref: str, pane: str, request: Request) -> Any:
        return await _page(request, lambda: _invoke(ctx, request, "briefing.evidence",
                                                    {"token": token, "ref": ref, "pane": pane}), what="evidence")

    @router.post("/api/b/{token}/answer")
    async def api_briefing_answer(token: str, request: Request) -> Any:
        try:
            body = await _bounded_body(request, PAGE_BODY_BYTES)
        except BodyTooLarge:
            return _too_large(PAGE_HEADERS)
        return await _page(request, lambda: _invoke(ctx, request, "briefing.answer", {
            "token": token, "ref": body.get("ref"), "choice": body.get("choice"),
            "reason": body.get("reason"), "later": body.get("later"), "binding": body.get("binding"),
        }), what="answer")

    @router.post("/api/reach/packages")
    async def api_reach_package_make(request: Request) -> Any:
        body = await _body(request)
        port = int((request.scope.get("server") or ("", 0))[1] or 0)

        def make(principal: Any) -> dict[str, Any]:
            made = _service().make(principal, body.get("refs"), kind=body.get("kind") or "item",
                                   send=body.get("send"), head=body.get("head"), lines=body.get("lines"))
            base = _tailnet_base(port)
            return {**made, "link": f"{base}{made['path']}" if base else None}

        return await _owner(request, make, status=201, what="make")

    @router.post("/api/reach/packages/{package_id}/revoke")
    async def api_reach_package_revoke(package_id: str, request: Request) -> Any:
        return await _owner(request, lambda _principal: _invoke(ctx, request, "briefing.revoke",
                                                                {"package_id": package_id}), what="revoke")

    # ── DIR4 to DIR6: Later, his settings, Telegram ──────────────────
    # Produced from the reach.* rows (settings_operations.py); the bot token is
    # HELD by its own handler, never an operation argument.
    rows = tuple(d for d in SETTINGS_ROUTE_OPERATIONS if d.name.startswith("reach.")) + TELEGRAM_SECRET_OPERATIONS
    mount_router(router, operation_router(
        rows, lambda: _ops(ctx), _reach_answer, module=__name__,
        hand_written={"settings.secret.telegram.token": lambda descriptor: _held_token(ctx, descriptor)},
    ))

    return router


def _ops(ctx: WebContext) -> Any:
    """The registry, with the process's one Reach and Telegram services where the context carries none."""
    from ...settings_operations import LIVE_REACH_SERVICE, LIVE_TELEGRAM_SERVICE

    return operations.for_context(ctx, reach_service=lambda: LIVE_REACH_SERVICE,
                                  telegram_service=lambda: LIVE_TELEGRAM_SERVICE)


async def _reach_answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        code = "owner_only" if exc.code == "owner_required" else exc.code
        return JSONResponse({"error": code, "code": code, "detail": exc.detail},
                            status_code=403 if exc.code == "owner_required" else 400)
    except ServiceError as exc:
        return _refused(exc)
    except Exception as exc:
        log.error(f"reach failed: {exc}", exc_info=True)
        return JSONResponse({"error": "reach_failed", "code": "reach_failed",
                             "detail": "The page service failed. Nothing changed. The log names the cause."},
                            status_code=500)


def _held_token(ctx: WebContext, descriptor: Any) -> Callable[..., Any]:
    """PUT /api/reach/telegram/token: the token leaves the body before anything reads the arguments."""

    async def api_reach_telegram_token(request: Request) -> Any:
        body = await _body(request)
        token = body.pop("token", None)
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        return await _reach_answer(lambda: _ops(ctx).invoke(
            principal, descriptor.name, body, held={"token": token}))

    return api_reach_telegram_token


__all__ = ["PAGE_HEADERS", "build_briefing_router"]
