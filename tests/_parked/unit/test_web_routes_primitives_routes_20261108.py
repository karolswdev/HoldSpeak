"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/unit/test_web_routes_primitives.py``: test_profile_crud_roundtrip, test_model_library_generated_target_has_no_legacy_target_route_side_door, test_inference_target_probe_discovers_models_for_that_target. Not collected.
"""
from __future__ import annotations
"""Primitive Framework — Note + Agent CRUD routes and the persona-run seam.

Builds a minimal app with just `build_primitives_router` over a real tmp-path
Database (the handlers do `from ...db import get_database` at call time, so we
point the singleton at a tmp DB). The persona-run endpoint is exercised with the
intel engine stubbed so no model is loaded.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _kernel_fields import plain  # noqa: E402  (PHILO-7-02)



@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness",
        lambda: ("ready", ""),
    )
    # Existing blank Recipe/Sequence fixtures model a configured hub. Seed that
    # configuration through the canonical default assignment rather than the
    # retired ambient placement fallback.
    default_model = tmp_path / "primitive-default.gguf"
    default_model.touch()
    db.profiles.upsert(
        profile_id="primitive-default", name="Primitive default", kind="onDevice",
        model_file=str(default_model),
    )
    InferenceAssignmentService(db).set_assignment(
        Principal(PrincipalKind.OWNER, "primitive-test-owner"),
        {
            "command_id": "primitive-test-default-assignment",
            "expected_revision": 0,
            "scope": {"kind": "global"},
            "entries": [{"profile_id": "legacy-primitive-default"}],
        },
    )
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "primitive-test-owner")
        return await call_next(request)

    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield TestClient(app)
    reset_database()


def _assert_admitted_parent_run(body: dict, child_count: int) -> None:
    """HS-131-04 parent summary: each actual model call remains a child receipt."""
    assert body["parent_operation_id"].startswith("op_")
    assert body["parent_native_id"]
    assert body["result_ref"] == f"artifact:{body['artifact_id']}"
    assert len(body["children"]) == child_count
    assert all(child["operation_id"].startswith("op_") for child in body["children"])
    assert all(child["invocation_id"] for child in body["children"])
    assert all(child["outcome"] == "succeeded" for child in body["children"])


def _assert_admitted_run(body: dict, recipe_id: str, input_text: str) -> None:
    # The runner receipt is now broker-owned, rather than projected in the
    # legacy invocation/correlation response shape. The returned projection
    # still names the executed recipe, exact destination, input provenance,
    # and durable artifact.
    assert body["artifact_id"]
    assert body["recipe_id"] == recipe_id
    assert body["actual_placement"]["target_id"] == "primitive-default"
    assert body["sources"] == [{"source_type": "recipe", "source_ref": recipe_id}]
    assert input_text in body["name"]


# ── Run a chain (crew) ───────────────────────────────────────────────────────
def _make_agent(client: TestClient, name: str, template: str) -> str:
    return client.post("/api/recipes", json={
        "name": name, "system_prompt": f"SYS-{name}", "user_template": template,
    }).json()["recipe"]["id"]


# ── Run a workflow ───────────────────────────────────────────────────────────
def _stub_intel(monkeypatch, output="WF-OUT", provider="local"):
    class _FakeIntel:
        active_provider = provider

        def __init__(self):
            self.captured = {}

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            self.captured["system_prompt"] = system_prompt
            self.captured["user_prompt"] = user_prompt
            return output

    fake = _FakeIntel()
    # HS-131-13: the admitted `this_machine` child builds `MeetingIntel` from
    # its FROZEN revision, so the same double goes on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: fake)
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: fake
    )
    return fake


# A real Workbench Blueprint shape: entry -> summarize -> rewrite -> output, a single
# linear chain (Swift-Codable snake_case tagged-union node kinds).
def _linear_graph() -> dict:
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Summary then Exec",
        "entry": "e1",
        "nodes": [
            {"id": "e1", "kind": {"entry": {}}, "failure_policy": None},
            {"id": "sum", "kind": {"summarize": {}}, "failure_policy": None},
            {"id": "rw", "kind": {"rewrite": {"tone": "executive"}}, "failure_policy": None},
            {"id": "out", "kind": {"output": {}}, "failure_policy": None},
        ],
        "exec_edges": [
            {"from": {"node": "e1", "name": "then"}, "to": "sum"},
            {"from": {"node": "sum", "name": "then"}, "to": "rw"},
            {"from": {"node": "rw", "name": "then"}, "to": "out"},
        ],
        "data_edges": [],
    }


# A branching Blueprint we MUST NOT linearize: entry -> branch -> {true,false}.
def _branching_graph() -> dict:
    return {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Branchy",
        "entry": "e1",
        "nodes": [
            {"id": "e1", "kind": {"entry": {}}, "failure_policy": None},
            {"id": "br", "kind": {"branch": {"condition": {"contains": {"keyword": "x"}}}},
             "failure_policy": None},
            {"id": "a", "kind": {"summarize": {}}, "failure_policy": None},
            {"id": "b", "kind": {"summarize": {}}, "failure_policy": None},
        ],
        "exec_edges": [
            {"from": {"node": "e1", "name": "then"}, "to": "br"},
            {"from": {"node": "br", "name": "true"}, "to": "a"},
            {"from": {"node": "br", "name": "false"}, "to": "b"},
        ],
        "data_edges": [],
    }


def test_profile_crud_roundtrip(client: TestClient) -> None:
    """HS-134-02 — targets CRUD over the one write path; the /api/profiles
    GET routes are retired (the target contract is the only read shape)."""
    created = client.post("/api/inference-targets", json={
        "name": "Claude", "kind": "openAICompatible",
        "base_url": "https://api.anthropic.com/v1", "model": "claude-3.5-sonnet",
        "context_limit": 200000, "requires_key": True,
    })
    assert created.status_code == 201, created.text
    target = created.json()["inference_target"]
    pid = target["id"]
    assert "api_key" not in target and "apiKey" not in target

    # HS-134-02: read through the one target API.
    listed = client.get("/api/inference-targets").json()
    assert any(t["id"] == pid for t in listed["targets"])
    got = client.get(f"/api/inference-targets/{pid}").json()["inference_target"]
    assert got["kind"] == "external_service" and got["context_limit"] == 200000
    # endpoint/node now ride the target contract (HS-134-02).
    assert got["endpoint"] == "https://api.anthropic.com/v1"

    assert client.put(f"/api/profiles/{pid}", json={"name": "X"}).status_code == 405
    upd = client.put(f"/api/inference-targets/{pid}", json={"name": "Claude 3.7", "context_limit": 128000})
    assert upd.status_code == 200
    assert upd.json()["inference_target"]["name"] == "Claude 3.7"
    assert upd.json()["inference_target"]["context_limit"] == 128000

    assert client.delete(f"/api/profiles/{pid}").status_code == 405
    assert client.delete(f"/api/inference-targets/{pid}").status_code == 200
    assert client.get(f"/api/inference-targets/{pid}").status_code == 404


def test_model_library_generated_target_has_no_legacy_target_route_side_door(client: TestClient) -> None:
    """S3: legacy target reads remain, generated library adapters do not."""
    db = hsdb.get_database()
    db.profiles.upsert(
        profile_id="library_provider_private", name="Private library adapter", kind="openAICompatible",
        base_url="http://127.0.0.1:9011/v1", model="private-model", requires_key=True,
    )
    listed = client.get("/api/inference-targets")
    assert listed.status_code == 200
    assert all(target["id"] != "library_provider_private" for target in listed.json()["targets"])
    for method, path in (
        ("get", "/api/inference-targets/library_provider_private"),
        ("put", "/api/inference-targets/library_provider_private"),
        ("post", "/api/inference-targets/library_provider_private/probe"),
        ("put", "/api/inference-targets/library_provider_private/secret"),
        ("delete", "/api/inference-targets/library_provider_private/secret"),
        ("delete", "/api/inference-targets/library_provider_private"),
    ):
        request = getattr(client, method)
        response = request(path, json={}) if method == "put" else request(path)
        assert response.status_code == 404


def test_inference_target_probe_discovers_models_for_that_target(client: TestClient, monkeypatch) -> None:
    created = client.post("/api/inference-targets", json={
        "name": "LAN llama", "kind": "openAICompatible",
        "base_url": "http://192.168.1.43:8080/v1", "model": "",
    })
    target_id = created.json()["inference_target"]["id"]
    seen = {}

    def discover(base_url, *, api_key=None, **_kwargs):
        seen.update(base_url=base_url, api_key=api_key)
        return {"ok": True, "models": ["qwen", "llama"], "detail": "Found 2 models."}

    from holdspeak.intel.providers import profile_key_env

    monkeypatch.setenv(profile_key_env(target_id), "target-key")
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", discover)

    response = client.post(f"/api/inference-targets/{target_id}/probe")

    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] is True
    assert isinstance(body["latency_ms"], int)
    assert body["models"] == ["qwen", "llama"]
    assert body["error"] is None
    assert seen == {"base_url": "http://192.168.1.43:8080/v1", "api_key": "target-key"}
    assert client.post("/api/inference-targets/missing/probe").status_code == 404


