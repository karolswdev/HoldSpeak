"""Fast tests (owner ruling 2026-10-03): the two speed seams change no behavior.

Astra's review of #763 found two cases where a seam and stock FastAPI gave
different answers. Each case is a test here.
"""
from __future__ import annotations

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from starlette.testclient import TestClient

from holdspeak.web.routes._mount import mount_router


def _custom_id(route) -> str:
    return f"custom_{route.name}"


def _probe_router(**settings) -> APIRouter:
    router = APIRouter(**settings)

    @router.get("/probe")
    def probe() -> str:
        return "ok"

    return router


def _facts(app: FastAPI) -> tuple[str, str]:
    response = TestClient(app).get("/probe")
    operation = app.openapi()["paths"]["/probe"]["get"]["operationId"]
    return response.headers["content-type"].split(";")[0], operation


@pytest.mark.parametrize("where", ["app", "child", "parent"])
@pytest.mark.parametrize(
    "settings, expected",
    [
        ({"default_response_class": PlainTextResponse}, ("text/plain", "probe_probe_get")),
        ({"generate_unique_id_function": _custom_id}, ("application/json", "custom_probe")),
    ],
    ids=["response_class", "unique_id"],
)
def test_a_mount_with_a_router_setting_answers_as_stock_include_does(where, settings, expected) -> None:
    def build(mount) -> FastAPI:
        if where == "app":  # Astra's case: the setting is on the app that mounts
            app = FastAPI(**settings)
            mount(app, _probe_router())
            return app
        app = FastAPI()
        if where == "child":
            mount(app, _probe_router(**settings))
        else:
            parent = APIRouter(**settings)
            mount(parent, _probe_router())
            app.include_router(parent)
        return app

    stock = _facts(build(lambda parent, child: parent.include_router(child)))
    assert stock == expected
    assert _facts(build(mount_router)) == stock


def test_a_plain_mount_moves_the_same_route_objects() -> None:
    app, child = FastAPI(), _probe_router()
    route = child.routes[0]
    mount_router(app, child)
    assert route in app.router.routes
    assert _facts(app) == ("application/json", "probe_probe_get")


class _Amount(BaseModel):
    value: int


def _amount_app() -> FastAPI:
    app = FastAPI()

    @app.post("/amount")
    def amount(body: _Amount) -> dict:
        return {"value": body.value}

    return app


def test_a_rebuilt_model_gets_its_new_constraint_in_the_next_app() -> None:
    """The suite shares route field adapters (tests/conftest.py); a model
    rebuilt with a new constraint must not get the adapter made before it."""
    assert TestClient(_amount_app()).post("/amount", json={"value": -1}).status_code == 200
    original = _Amount.model_fields["value"]
    try:
        _Amount.model_fields["value"] = Field(ge=0)
        _Amount.model_fields["value"].annotation = int
        _Amount.model_rebuild(force=True)
        assert TestClient(_amount_app()).post("/amount", json={"value": -1}).status_code == 422
        assert TestClient(_amount_app()).post("/amount", json={"value": 1}).status_code == 200
    finally:
        _Amount.model_fields["value"] = original
        _Amount.model_rebuild(force=True)
