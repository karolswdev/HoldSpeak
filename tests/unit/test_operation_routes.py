"""A produced route trusts only the principal the edge set (Codex on #2051).

``operation_router`` reads ``request.state.principal``. A request with none
(a router mounted without the hub's edge) is UNAUTHENTICATED, never the owner,
so the registry refuses an owner-only operation with ``owner_required``.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.web.operation_routes import operation_router
from holdspeak.web.routes.phone import _call


OWNER = Principal(PrincipalKind.OWNER, "owner-session")


class _Phone:
    def __init__(self) -> None:
        self.callers: list[Any] = []

    def push_key(self, principal: Any) -> dict[str, Any]:
        self.callers.append(principal)
        return {"saved": []}


def _app(phone: _Phone, *, principal: Any = None) -> TestClient:
    descriptor = next(op for op in operations.PHONE_OPERATIONS if op.name == "phone.push_key")
    assert descriptor.owner_only and descriptor.http == ("GET", "/api/phone/push")
    registry = operations.for_context(None, phone_service=lambda: phone)
    app = FastAPI()
    if principal is not None:
        @app.middleware("http")
        async def _edge(request, call_next):
            request.state.principal = principal
            return await call_next(request)
    app.include_router(operation_router([descriptor], lambda: registry, _call, module=__name__))
    return TestClient(app)


def test_a_produced_owner_only_route_with_no_principal_is_refused() -> None:
    phone = _Phone()
    response = _app(phone).get("/api/phone/push")
    assert response.status_code == 403, response.text
    assert response.json()["code"] == "owner_required"
    assert phone.callers == []


def test_a_produced_owner_only_route_with_the_owner_principal_passes() -> None:
    phone = _Phone()
    response = _app(phone, principal=OWNER).get("/api/phone/push")
    assert response.status_code == 200, response.text
    assert response.json() == {"saved": []}
    assert phone.callers == [OWNER]


def test_every_declared_args_schema_is_a_valid_json_schema() -> None:
    """The check a descriptor made at construction, once per test run (2026-11-09:
    275 meta-schema checks were 0.1 s of every hub start)."""
    from jsonschema import Draft202012Validator

    for descriptor in operations.DESCRIPTORS:
        Draft202012Validator.check_schema(dict(descriptor.args_schema))


def test_a_body_that_contradicts_the_path_is_refused_by_name() -> None:
    """Codex on #2122: the old kernel decide and receipt routes rejected a body
    ``operation_id``; a produced route overwrote it with the path's. A body or
    query naming a path parameter with another value is refused as
    ``path_body_mismatch`` (400) on every produced route; the same value passes."""
    seen: list[dict[str, Any]] = []

    class _Registry:
        def invoke(self, principal: Any, name: str, args: dict[str, Any], *, shape: str = "web") -> Any:
            seen.append(dict(args))
            return {"ok": True}

    descriptor = next(d for d in operations.DESCRIPTORS
                      if d.http and d.http[0] == "POST" and "{" in d.http[1] and not d.owner_only)
    path_param = descriptor.http[1].split("{", 1)[1].split("}", 1)[0].split(":", 1)[0]
    app = FastAPI()
    app.include_router(operation_router([descriptor], lambda: _Registry(), _call, module=__name__))
    client = TestClient(app)
    url = descriptor.http[1]
    for part in [p for p in descriptor.http[1].split("/") if p.startswith("{")]:
        url = url.replace(part, "abc")
    refused = client.post(url, json={path_param: "xyz"})
    assert refused.status_code == 400, refused.text
    assert "path_body_mismatch" in refused.text
    assert seen == []
    agreed = client.post(url, json={path_param: "abc"})
    assert agreed.status_code in (200, 201, 202), agreed.text
    assert seen and seen[0][path_param] == "abc"
