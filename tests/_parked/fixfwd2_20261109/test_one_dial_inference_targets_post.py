# PARKED 2026-11-09 (fix forward 2): POST /api/inference-targets had no client and was parked with the
# primitives profiles router (#2127, holdspeak/web/routes/primitives/_parked/profiles_20261109.py); the read is
# the declared inference.targets.list, and the service writes. Moved from tests/unit/test_one_dial.py.

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.principals import Principal, PrincipalKind
from tests.unit.test_one_dial import *  # noqa: F401,F403


# ── /api/profiles read routes retired (HS-134-02) ─────────────────────


@pytest.fixture
def client(db, monkeypatch) -> TestClient:
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.profiles import build_profiles_router

    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "one-dial-test-owner")
        return await call_next(request)

    app.include_router(build_profiles_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


def test_inference_targets_stays_the_write_path(client, db) -> None:
    resp = client.post(
        "/api/inference-targets",
        json={"name": "LAN", "kind": "openAICompatible",
              "base_url": "http://192.168.1.43:8080/v1", "model": "q"},
    )
    assert resp.status_code == 201
    assert resp.json()["inference_target"]["id"]


