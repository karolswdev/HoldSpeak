"""PARKED 20261108 (evening, the unreached-routes census): routes no client calls.

Parked from ``holdspeak/web/routes/briefing.py``: GET /api/reach/packages.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
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

import json
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from ....logging_config import get_logger
from ....services.errors import ServiceError
from ...context import WebContext

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




def parked_build_briefing_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/reach/packages")
    async def api_reach_packages(request: Request) -> Any:
        program_id = str(request.query_params.get("program_id") or "")
        return await _owner(request, lambda principal: {"packages": _service().packages(principal, program_id)},
                            what="list")

    return router
