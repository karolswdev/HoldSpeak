"""HS-65-01: the launch pre-flight — every page route loads with zero
uncaught page errors.

The Phase-62 find that motivates this: a SyntaxError shipped on /welcome
(and the first-run /) for roughly nineteen phases because only the pages a
dogfood happened to open ever had a zero-page-error assertion. Before
strangers `pip install holdspeak`, every served HTML route gets that
assertion, once, mechanically.

The routes are enumerated FROM the live FastAPI app (every GET route that
returns HTML), so a new page added to `pages.py` cannot escape the sweep
without also failing the "did we cover it" guard below.

Skips cleanly when Playwright/browsers are absent (CI has neither); the
green evidence run is local. Run it before any release tag:

    uv run pytest -q tests/e2e/test_route_preflight.py
"""
from __future__ import annotations

import threading
import time

import pytest

pytest.importorskip("playwright.sync_api", reason="pre-flight needs Playwright + a browser")
pytest.importorskip(
    "fastapi.testclient", reason="requires meeting/web dependencies (install with `.[meeting]`)"
)

pytestmark = [pytest.mark.requires_meeting]

# The HTML page routes the runtime serves. Kept in sync with pages.py by
# test_preflight_covers_every_html_route below — a new page route fails that
# guard until it is listed here (and thus swept).
PAGE_ROUTES = [
    "/",
    "/welcome",
    "/setup",
    "/history",
    "/settings",
    "/activity",
    "/dictation",
    "/commands",
    "/companion",
    "/presence",
    "/cadence",
    "/docs/dictation-runtime",
]


def _served_html_routes() -> list[str]:
    """Every GET route on the real app whose handler lives in pages.py."""
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    routes = []
    for route in server.app.routes:
        methods = getattr(route, "methods", set()) or set()
        path = getattr(route, "path", "")
        endpoint = getattr(route, "endpoint", None)
        module = getattr(endpoint, "__module__", "")
        if "GET" in methods and module.endswith("routes.pages") and "{" not in path:
            routes.append(path)
    return sorted(set(routes))


def test_preflight_covers_every_html_route() -> None:
    """A new page in pages.py must be added to PAGE_ROUTES (and thus swept)."""
    served = set(_served_html_routes())
    listed = set(PAGE_ROUTES)
    missing = served - listed
    assert not missing, (
        f"page routes served but not in the pre-flight sweep: {sorted(missing)}. "
        "Add them to PAGE_ROUTES so a new page cannot ship an unchecked page error."
    )
    # And nothing stale (a removed route lingering here would pass falsely).
    stale = listed - served
    assert not stale, f"PAGE_ROUTES lists routes the app no longer serves: {sorted(stale)}"


@pytest.mark.e2e
def test_every_route_loads_without_page_errors() -> None:
    from playwright.sync_api import sync_playwright

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    url = server.start()
    time.sleep(1.0)

    failures: dict[str, list[str]] = {}
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as exc:  # no browser binary installed
                pytest.skip(f"no Chromium available for the pre-flight: {exc}")
            for path in PAGE_ROUTES:
                errors: list[str] = []
                page = browser.new_page()
                page.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
                page.goto(f"{url}{path}", wait_until="networkidle")
                page.wait_for_timeout(800)
                page.close()
                if errors:
                    failures[path] = errors
            browser.close()
    finally:
        server.stop()

    assert not failures, "uncaught page errors on launch routes:\n" + "\n".join(
        f"  {path}: {errs}" for path, errs in failures.items()
    )
