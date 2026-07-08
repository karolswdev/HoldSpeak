"""HS-26-01: the route-module seam (WebContext + build_core_router).

Pins the pattern the rest of Phase 26 follows: a router built from a WebContext
(not the server instance), behavior identical to the old inline handlers.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_core_router


def _client(get_state) -> TestClient:
    app = FastAPI()
    app.include_router(build_core_router(WebContext(get_state=get_state)))
    return TestClient(app)


def test_health_route_returns_ok():
    client = _client(lambda: {})
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_state_route_returns_get_state_payload():
    client = _client(lambda: {"id": "m1", "duration": 7})
    resp = client.get("/api/state")
    assert resp.status_code == 200
    assert resp.json() == {"id": "m1", "duration": 7}


def test_state_route_fails_soft_when_get_state_raises():
    def _boom():
        raise RuntimeError("state unavailable")

    resp = _client(_boom).get("/api/state")
    # Preserve the old inline behavior: log + return an empty object, not a 500.
    assert resp.status_code == 200
    assert resp.json() == {}


def test_context_module_has_no_route_import_cycle():
    # WebContext must not import any route module (routers import the context,
    # never the reverse) — guards against an import cycle as the package grows.
    #
    # The popped modules are restored afterwards (HS-86-03): leaving the
    # package out of sys.modules meant the next in-test package import
    # rebuilt it EMPTY of submodule attributes, and every later
    # string-path monkeypatch through holdspeak.web.routes.* failed —
    # an order-dependent break that hid for sixty phases.
    import sys

    import holdspeak.web

    saved_context = sys.modules.pop("holdspeak.web.context", None)
    saved_routes = sys.modules.pop("holdspeak.web.routes", None)
    try:
        import holdspeak.web.context  # noqa: F401

        assert "holdspeak.web.routes" not in sys.modules
    finally:
        if saved_context is not None:
            sys.modules["holdspeak.web.context"] = saved_context
            holdspeak.web.context = saved_context
        if saved_routes is not None:
            sys.modules["holdspeak.web.routes"] = saved_routes
            holdspeak.web.routes = saved_routes
