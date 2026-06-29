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

    @router.get("/welcome")
    async def welcome_wizard() -> Any:
        """Serve the first-run wizard (HS-43-01) — a full-screen takeover, read
        from the Astro-built _built/welcome/index.html."""
        page = _HOLDSPEAK_DIR / "static" / "_built" / "welcome" / "index.html"
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built welcome wizard: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>Welcome to HoldSpeak</title></head>"
                "<body><h1>Welcome to HoldSpeak</h1>"
                "<p>Wizard not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/setup")
    async def setup_page() -> Any:
        """Serve the welcome / setup surface (HS-42-03), read from the
        Astro-built _built/setup/index.html. Driven client-side by
        GET /api/setup/status."""
        page = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "setup"
            / "index.html"
        )
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built setup page: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>HoldSpeak Setup</title></head>"
                "<body><h1>HoldSpeak Setup</h1>"
                "<p>Setup UI not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/history")
    async def history_dashboard() -> Any:
        """Serve the history dashboard (HS-10-08: now read from the
        Astro-built _built/history/index.html)."""
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
        """Serve the global Settings page (HS-42-02: a real shell-level
        route, read from the Astro-built _built/settings/index.html — the
        History → Settings move is complete)."""
        page = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "settings"
            / "index.html"
        )
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built settings page: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>HoldSpeak Settings</title></head>"
                "<body><h1>HoldSpeak Settings</h1>"
                "<p>Settings UI not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

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

    @router.get("/cadence")
    async def cadence_dashboard() -> Any:
        """Serve the Cadence coach surface (CAD-2-04: the Astro-built
        _built/cadence/index.html, driven by /api/cadence/*)."""
        page = (
            _HOLDSPEAK_DIR
            / "static"
            / "_built"
            / "cadence"
            / "index.html"
        )
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read cadence.html: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>HoldSpeak Cadence</title></head>"
                "<body><h1>Cadence</h1><p>Page unavailable.</p></body></html>"
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

    @router.get("/commands")
    async def commands_board() -> Any:
        """Serve the Voice Commands board (HS-52-05), read from the Astro-built
        _built/commands/index.html. Driven client-side by GET/PUT /api/settings and
        POST /api/commands/test."""
        page = _HOLDSPEAK_DIR / "static" / "_built" / "commands" / "index.html"
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built commands page: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>Voice Commands</title></head>"
                "<body><h1>Voice Commands</h1>"
                "<p>Commands UI not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/desk")
    async def desk_page() -> Any:
        """Serve the Web Desk (Primitive Framework authoring port), read from the
        Astro-built _built/desk/index.html. The TopNav links here, so it needs a
        real route (it was previously reachable only at /_built/desk/, a dead nav
        link). Driven client-side by the /api/* primitive routes."""
        page = _HOLDSPEAK_DIR / "static" / "_built" / "desk" / "index.html"
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built desk page: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>HoldSpeak Desk</title></head>"
                "<body><h1>The Desk</h1>"
                "<p>Desk UI not built. Run <code>npm run build</code> "
                "in <code>web/</code>.</p></body></html>"
            )
        return HTMLResponse(html)

    @router.get("/profiles")
    async def profiles_page() -> Any:
        """Serve the Runtime Profiles surface (HSM-24-05), read from the
        Astro-built _built/profiles/index.html. Driven client-side by
        GET/POST/PUT/DELETE /api/profiles. SHAPE only — the API key never
        reaches the browser; it lives in the hub's secrets."""
        page = _HOLDSPEAK_DIR / "static" / "_built" / "profiles" / "index.html"
        try:
            html = page.read_text(encoding="utf-8")
        except Exception as e:
            log.error(f"Failed to read built profiles page: {e}")
            html = (
                "<!doctype html><html><head><meta charset='utf-8'/>"
                "<title>Runtime Profiles</title></head>"
                "<body><h1>Runtime Profiles</h1>"
                "<p>Profiles UI not built. Run <code>npm run build</code> "
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
