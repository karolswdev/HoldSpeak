"""The callback routes invoke the composed contract and refuse owner-only reads/writes."""
from __future__ import annotations

from unittest.mock import Mock

import pytest

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.system_service import SystemService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.core import build_core_router
from holdspeak.web.routes.system.health import build_health_router
from holdspeak.web.routes.activity.plugin_jobs import build_plugin_jobs_router

OWNER = Principal(PrincipalKind.OWNER, "system-owner")
AGENT = Principal(PrincipalKind.AGENT, "system-agent")


def client(ctx, principal=OWNER):
    app = FastAPI()

    @app.middleware("http")
    async def identity(request: Request, call_next):
        request.state.principal = principal
        return await call_next(request)

    app.include_router(build_core_router(ctx))
    app.include_router(build_health_router(ctx))
    app.include_router(build_plugin_jobs_router(ctx))
    return TestClient(app)


def test_system_reads_reach_the_bound_registry_instead_of_route_callbacks(monkeypatch):
    ctx = WebContext(get_state=lambda: {"id": "fallback"})
    target = SystemService(WebContext(get_state=lambda: {"id": "composed", "duration": 7}))
    ctx.operations = operations.bind_available({"system_service": target})
    invoke = Mock(wraps=ctx.operations.invoke)
    monkeypatch.setattr(ctx.operations, "invoke", invoke)
    http = client(ctx)
    assert http.get("/api/state").json() == {"id": "composed", "duration": 7}
    assert http.get("/api/runtime/status").json()["state"]["id"] == "composed"
    assert [call.args[1] for call in invoke.call_args_list] == ["system.state", "system.runtime.status"]
    invoke.reset_mock()
    assert http.get("/api/state?token=bootstrap-credential").json()["id"] == "composed"
    assert invoke.call_args.args[2] == {}  # the auth query must never become operation data
    refused = http.get("/api/state?actor=owner")
    assert refused.status_code == 400
    assert refused.json()["code"] == "authority_in_arguments"


def test_runtime_status_keeps_the_fail_soft_state_and_named_status_failure():
    def failed():
        raise RuntimeError("status unavailable")

    ctx = WebContext(get_state=failed, on_get_status=lambda: {"mode": "dictation"})
    http = client(ctx)
    assert http.get("/api/runtime/status").json()["state"] == {}
    ctx.on_get_status = failed
    response = http.get("/api/runtime/status")
    assert response.status_code == 500
    assert response.json() == {"success": False, "error": "status unavailable"}


def test_identity_and_queue_refuse_an_agent_before_the_callback(monkeypatch):
    callback = Mock(return_value={"processed": 1})
    identity = Mock(return_value={"pid": 123})
    monkeypatch.setattr("holdspeak.runtime_identity.identity_report", identity)
    ctx = WebContext(get_state=lambda: {}, on_process_plugin_jobs=callback)
    http = client(ctx, AGENT)
    for path, verb in [("/api/system/identity", http.get), ("/api/plugin-jobs/process", http.post)]:
        response = verb(path)
        assert response.status_code == 403
        assert response.json()["code"] == "owner_required"
    callback.assert_not_called()
    identity.assert_not_called()


def test_queue_validation_retry_mode_and_one_announcement():
    callback = Mock(return_value={"processed": 2})
    announce = Mock()
    ctx = WebContext(get_state=lambda: {}, on_process_plugin_jobs=callback, broadcast=announce)
    http = client(ctx)
    for payload in ({"max_jobs": 0}, {"mode": "invalid"}):
        assert http.post("/api/plugin-jobs/process", json=payload).status_code == 400
    callback.assert_not_called()
    response = http.post("/api/plugin-jobs/process", json={"max_jobs": 2, "mode": "retry_now"})
    assert response.status_code == 200, response.text
    assert response.json() == {"processed": 2, "mode": "retry_now", "success": True}
    callback.assert_called_once_with(max_jobs=2, include_scheduled=True)
    announce.assert_called_once_with("plugin_jobs_processed", response.json())


@pytest.mark.parametrize("name,service,args", [
    ("setup.lan.scan", "setup_service", {}),
    ("concierge.retry", "concierge_service", {"kind": "summary", "key": "meeting-one"}),
])
def test_new_owner_tools_refuse_an_agent_before_service_work(name, service, args, monkeypatch):
    from holdspeak.mcp import tools
    from holdspeak.mcp.families import declared

    target = Mock()
    registry = operations.bind_available({service: target})
    monkeypatch.setattr(tools, "runtime_registry", lambda: registry)
    with pytest.raises(operations.OperationOwnerRequired) as refused:
        declared.dispatch(name, args, AGENT)
    assert refused.value.code == "owner_required"
    assert target.mock_calls == []
