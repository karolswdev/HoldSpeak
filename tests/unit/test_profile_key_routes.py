from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.profile_key_store import ProfileKeyStore
from holdspeak.services.profile_key_service import ProfileKeyService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.primitives.profiles import build_profiles_router


class _Profiles:
    def __init__(self, record): self.record = record
    def get(self, _id): return self.record


class _Db:
    def __init__(self, record): self.profiles = _Profiles(record)


def _client(tmp_path, record):
    app = FastAPI()
    service = ProfileKeyService(_Db(record), store=ProfileKeyStore(tmp_path / "keys.json"))

    @app.middleware("http")
    async def principal(request: Request, call_next):
        kind = request.headers.get("x-test-principal")
        request.state.principal = (
            Principal(PrincipalKind.OWNER, "owner") if kind == "owner"
            else Principal(PrincipalKind.AGENT, "agent") if kind == "agent" else None
        )
        return await call_next(request)

    app.include_router(build_profiles_router(WebContext(get_state=lambda: {}, profile_key_service=service)))
    return TestClient(app)


def test_secret_subresource_is_owner_only_and_redacted(tmp_path):
    record = SimpleNamespace(id="endpoint", kind="openAICompatible", requires_key=True)
    client = _client(tmp_path, record)
    sentinel = "route-sentinel-never-returned"
    owner = {"x-test-principal": "owner"}
    put = client.put("/api/inference-targets/endpoint/secret", headers=owner, json={"value": sentinel})
    assert put.status_code == 200
    assert put.json() == {"success": True, "secret": {"required": True, "present": True}}
    assert sentinel not in put.text
    assert client.delete("/api/inference-targets/endpoint/secret", headers=owner).json() == {
        "success": True, "secret": {"required": True, "present": False},
    }
    assert client.put("/api/inference-targets/endpoint/secret", json={"value": sentinel}).status_code == 403
    assert client.put("/api/inference-targets/endpoint/secret", headers={"x-test-principal": "agent"}, json={"value": sentinel}).status_code == 403


def test_secret_subresource_rejects_bad_target_and_body(tmp_path):
    owner = {"x-test-principal": "owner"}
    missing = _client(tmp_path, None)
    assert missing.put("/api/inference-targets/missing/secret", headers=owner, json={"value": "x"}).status_code == 404
    mesh = _client(tmp_path, SimpleNamespace(id="mesh", kind="meshNode", requires_key=False))
    assert mesh.put("/api/inference-targets/mesh/secret", headers=owner, json={"value": "x"}).status_code == 400
    endpoint = _client(tmp_path, SimpleNamespace(id="endpoint", kind="openAICompatible", requires_key=True))
    assert endpoint.put("/api/inference-targets/endpoint/secret", headers=owner, json={"value": "x", "extra": True}).status_code == 400
