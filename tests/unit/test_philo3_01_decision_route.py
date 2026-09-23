"""PHILO-3-01 (A1): the desk decision create route answers, and the fence proves it did not.

The defect: ``build_desk_decisions_router`` ran ``del ctx`` while its ``_svc``
closure still read ``ctx``, so ``POST /api/decisions`` answered 500
"cannot access free variable 'ctx'" on every desk (aa865f57, HS-200-45).
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_decisions_router, build_primitives_router

REPO = Path(__file__).resolve().parents[2]
ROUTE = "holdspeak/web/routes/primitives/decisions.py"
PRE_FIX_COMMIT = "7ce95358"  # main with the ratified Phase 3 charter; still carries `del ctx`

BODY = {
    "title": "Adopt the event bus for desk frames",
    "status": "accepted",
    "decision_markdown": "We use the one bus for every desk frame.",
    "context_markdown": "Source: meeting mtg-philo3-01 review",
    "tags": ["source:meeting:mtg-philo3-01"],
}


def _app(db: Database, monkeypatch, router_factory) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)

    # The hub's order (holdspeak/web_server.py): the lifecycle router is
    # included BEFORE the primitives router, so it owns GET /api/decisions/{id}.
    app.include_router(build_decisions_router(None))
    app.include_router(router_factory(WebContext(get_state=lambda: {})))
    return TestClient(app, raise_server_exceptions=False)


def test_post_decision_through_the_real_route_reads_back(tmp_path, monkeypatch):
    client = _app(Database(tmp_path / "d.db"), monkeypatch, build_primitives_router)
    created = client.post("/api/decisions", json=BODY)
    assert created.status_code == 201, created.text
    decision = created.json()["decision"]
    assert decision["id"].startswith("decision")

    read = client.get(f"/api/decisions/{decision['id']}")
    assert read.status_code == 200, read.text
    back = read.json()["decision"]
    assert back["id"] == decision["id"]
    assert back["title"] == BODY["title"]
    assert back["decision_markdown"] == BODY["decision_markdown"]
    assert back["context_markdown"] == BODY["context_markdown"]
    assert back["tags"] == BODY["tags"]
    assert back["status"] == "accepted"

    listed = client.get("/api/decisions").json()["decisions"]
    assert [d["id"] for d in listed] == [decision["id"]]


def test_pre_fix_route_answers_500_on_create(tmp_path, monkeypatch):
    source = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:{ROUTE}"],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout
    assert "    del ctx\n" in source  # the pre-fix shape this fence exercises
    name = "holdspeak.web.routes.primitives._philo3_01_prefix_decisions"
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "holdspeak.web.routes.primitives"
    sys.modules[name] = module
    try:
        exec(compile(source, f"<{PRE_FIX_COMMIT}:{ROUTE}>", "exec"), module.__dict__)
        client = _app(Database(tmp_path / "p.db"), monkeypatch, module.build_desk_decisions_router)
        created = client.post("/api/decisions", json=BODY)
    finally:
        sys.modules.pop(name, None)
    assert created.status_code == 500
    assert "cannot access free variable 'ctx'" in created.text
