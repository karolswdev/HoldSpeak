"""The launch pre-flight route list covers every served HTML page route.

The browser half (every listed route loads with zero page errors) stays in
tests/e2e/test_desk_sweep.py and imports PAGE_ROUTES from here (the e2e preflight is parked).

replaces: tests/e2e/test_route_preflight.py::test_preflight_covers_every_html_route
"""
from __future__ import annotations

import pytest

pytest.importorskip(
    "fastapi.testclient", reason="requires meeting/web dependencies (install with `.[meeting]`)"
)

pytestmark = [pytest.mark.requires_meeting]

# The HTML page routes the runtime serves. Kept in sync with pages.py by
# test_preflight_covers_every_html_route below — a new page route fails that
# guard until it is listed here (and thus swept).
PAGE_ROUTES = [
    "/",
    "/live",
    "/welcome",
    "/setup",
    "/studio",
    "/desk",
    "/workbench",
    "/history",
    "/meetings",
    "/settings",
    "/activity",
    "/dictation",
    "/commands",
    "/companion",
    "/conductor",
    "/presence",
    "/cadence",
    "/profiles",
    "/models",
    "/terminals",
    "/docs/dictation-runtime",
    "/design/components",
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
