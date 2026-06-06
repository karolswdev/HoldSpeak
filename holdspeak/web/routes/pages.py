"""Static HTML page routes (HS-26-05).

The Astro-built dashboard pages (`/`, `/history`, `/settings`, `/activity`,
`/dictation`, `/companion`, `/docs/dictation-runtime`). Each reads a built
`index.html` off disk and falls back to a minimal inline page. No server state —
the `ctx` parameter is kept only for seam uniformity.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.pages")

# This module sits at holdspeak/web/routes/; the built static assets live at
# holdspeak/static/_built/, three parents up.
_HOLDSPEAK_DIR = Path(__file__).resolve().parent.parent.parent

_DASHBOARD_HTML_PATH = (
    _HOLDSPEAK_DIR / "static" / "_built" / "index.html"
)


def build_pages_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def dashboard() -> Any:
        try:
            html = _DASHBOARD_HTML_PATH.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read runtime index: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8' />"
                "<title>HoldSpeak</title></head>"
                "<body><h1>HoldSpeak Runtime</h1>"
                "<p>Runtime UI missing — run "
                "<code>cd web && npm run build</code>.</p>"
                "</body></html>"
            )
        return HTMLResponse(html)

    @router.get("/history")
    async def history_dashboard() -> Any:
        """Serve the history dashboard (HS-10-08: now read from the
        Astro-built _built/history/index.html). The /settings route
        still points here because settings live as a tab inside
        the history page."""
        history_path = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "history"
            / "index.html"
        )
        try:
            html = history_path.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built history page: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8' />"
                "<title>HoldSpeak History</title></head>"
                "<body><h1>HoldSpeak History</h1>"
                "<p>History UI not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/settings")
    async def settings_dashboard() -> Any:
        """Serve web settings UI (currently integrated with history dashboard)."""
        return await history_dashboard()

    @router.get("/activity")
    async def activity_dashboard() -> Any:
        """Serve the local activity intelligence dashboard (HS-10-07:
        now read from the Astro-built _built/activity/index.html)."""
        page = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "activity"
            / "index.html"
        )
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read activity.html: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>HoldSpeak Activity</title></head>"
                "<body><h1>Local Activity</h1><p>Page unavailable.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/dictation")
    async def dictation_dashboard() -> Any:
        """Serve the dictation block-config UI (HS-10-09: now read
        from the Astro-built _built/dictation/index.html)."""
        page = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "dictation"
            / "index.html"
        )
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built dictation page: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>HoldSpeak Dictation</title></head>"
                "<body><h1>HoldSpeak Dictation</h1>"
                "<p>Dictation UI not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/companion")
    async def companion_dashboard() -> Any:
        """Serve the AI PI companion surface (HS-24-01)."""
        page = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "companion"
            / "index.html"
        )
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built companion page: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>HoldSpeak Companion</title></head>"
                "<body><h1>AI PI Companion</h1>"
                "<p>Companion UI not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/docs/dictation-runtime")
    async def dictation_runtime_docs() -> Any:
        """Serve local dictation runtime setup guidance (HS-10-09:
        now read from _built/docs/dictation-runtime/index.html)."""
        page = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "docs"
            / "dictation-runtime"
            / "index.html"
        )
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built dictation-runtime docs: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>Dictation Runtime Setup</title></head>"
                "<body><h1>Dictation Runtime Setup</h1>"
                "<p>Page unavailable.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/presence")
    async def presence_hud() -> Any:
        """Serve the minimal runtime-presence HUD (HS-41-03).

        A transparent, HUD-sized page rendering just the Signal presence card,
        driven live by the `runtime_activity` websocket. This is the content the
        native desktop webview (HS-41-04/05) loads in a frameless window."""
        page = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "presence"
            / "index.html"
        )
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built presence HUD: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>HoldSpeak Presence</title></head>"
                "<body><h1>HoldSpeak Presence</h1>"
                "<p>Presence HUD not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

    return router
