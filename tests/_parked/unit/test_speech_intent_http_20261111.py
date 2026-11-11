# PARKED: unused intent HTTP adapters; the MCP tools remain tested.
from test_speech_declared_operations import *

@pytest.mark.parametrize(
    "name,args",
    [("intents.controls", {}), ("intents.preview", {"transcript": "Review"})],
)
def test_intent_tools_and_http_use_the_same_bound_service(
    tmp_path, monkeypatch, name, args
):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.db import Database
    from holdspeak.mcp.families import declared
    from holdspeak.mcp import tools
    from holdspeak.services.dictation_service import (
        DictationService,
        bind_dictation_runtime,
    )
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.dictation.intents import build_intents_router

    db = Database(tmp_path / "dictation.db")
    try:
        owner = Principal(PrincipalKind.OWNER, "owner")
        ctx = WebContext(
            get_state=dict,
            on_get_intent_controls=lambda: {"profile": "architect"},
            on_route_preview=lambda **kw: {
                "transcript": kw["transcript"],
                "profile": kw["profile"],
            },
        )
        ctx.dictation_service = bind_dictation_runtime(DictationService(db), ctx)
        registry = operations.bind_available(
            {"dictation_service": ctx.dictation_service}
        )
        ctx.operations = registry
        monkeypatch.setattr(tools, "runtime_registry", lambda: registry)
        app = FastAPI()

        @app.middleware("http")
        async def owner_edge(request, call_next):
            request.state.principal = owner
            return await call_next(request)

        app.include_router(build_intents_router(ctx))
        row = registry.descriptor(name)
        method, path = row.http
        client = TestClient(app)
        response = (
            client.get(path, params=args)
            if method == "GET"
            else client.request(method, path, json=args)
        )
        assert response.status_code == 200, response.text
        assert declared.dispatch(row.tool_name, args, owner) == response.json()
        assert registry.target(name) is ctx.dictation_service
    finally:
        db.close()
