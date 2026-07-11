"""The one Vite/React Web shell (HS-91-09).

Every product URL reads the same built ``index.html``. React Router owns route
selection in the browser; FastAPI keeps explicit paths so API routes can never
be swallowed by a broad SPA fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.pages")

_HOLDSPEAK_DIR = Path(__file__).resolve().parent.parent.parent
_SHELL_PATH = _HOLDSPEAK_DIR / "static" / "_built" / "index.html"

# Canonical product routes plus deliberate compatibility aliases. Keep this in
# sync with web/src/routes.tsx and the Phase-91 parity ledger.
SPA_ROUTES = (
    "/",
    "/desk",
    "/welcome",
    "/setup",
    "/dictation",
    "/live",
    "/history",
    "/meetings",
    "/settings",
    "/activity",
    "/commands",
    "/cadence",
    "/studio",
    "/workbench",
    "/profiles",
    "/companion",
    "/presence",
    "/docs/dictation-runtime",
    "/design/components",
)


def _react_shell() -> HTMLResponse:
    try:
        html = _SHELL_PATH.read_text(encoding="utf-8")
    except Exception as exc:
        log.error(f"Failed to read Vite React shell: {exc}")
        html = (
            "<!doctype html><html><head><meta charset='utf-8'/>"
            "<title>HoldSpeak</title></head><body><h1>HoldSpeak</h1>"
            "<p>The React Web build is missing. Run "
            "<code>cd web &amp;&amp; npm run build</code>.</p></body></html>"
        )
    return HTMLResponse(html)


def build_pages_router(ctx: WebContext) -> APIRouter:
    """Register every browser route against the same side-effect-free reader."""
    del ctx
    router = APIRouter()

    async def react_shell() -> Any:
        return _react_shell()

    for route in SPA_ROUTES:
        router.add_api_route(route, react_shell, methods=["GET"], include_in_schema=False)

    return router
