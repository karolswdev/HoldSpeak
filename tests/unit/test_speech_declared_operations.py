"""The speech rows keep browser and node authority out of an agent's hands."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from holdspeak import operations
from holdspeak.principals import Principal, PrincipalKind


SPEECH_ROWS = (
    operations.DICTATION_OPERATIONS
    + operations.MEDIA_OPERATIONS
    + tuple(
        row for row in operations.DEVICE_OPERATIONS if row.service == "mesh_service"
    )
)


@pytest.mark.parametrize(
    "row",
    [
        row
        for row in SPEECH_ROWS
        if row.owner_only
        or (
            row.tool_schema is None
            and row.service != "mesh_service"
            and (row.http is None or row.http[1].startswith("/api/"))
        )
    ],
    ids=lambda row: row.name,
)
def test_owner_and_browser_rows_refuse_agents_before_the_service(row):
    service = Mock()
    registry = operations.bind({row.service: service}, (row,))
    agent = Principal(PrincipalKind.AGENT, "speech-worker")
    with pytest.raises(operations.OperationOwnerRequired) as refused:
        registry.invoke(agent, row.name, {})
    assert refused.value.code == "owner_required"
    assert service.mock_calls == []
    assert row.owner_only


def test_relay_rows_keep_the_credential_in_transport_custody(tmp_path):
    from holdspeak.db import Database
    from holdspeak.services.errors import ServiceError
    from holdspeak.services.mesh_service import MeshService

    db = Database(tmp_path / "mesh.db")
    try:
        service = MeshService(db)
        rows = tuple(
            row
            for row in SPEECH_ROWS
            if row.service == "mesh_service"
            and row.http[1].startswith("/api/mesh/relay/")
        )
        assert rows, "Relay callbacks need declared rows"
        registry = operations.bind({"mesh_service": service}, rows)
        for row in rows:
            assert row.held == ("credential",)
            assert row.http and row.http[1].startswith("/api/mesh/relay/")
            assert not any(face.startswith("mcp:") for face in row.exposure)
            with pytest.raises(ServiceError) as refused:
                registry.invoke(
                    Principal(PrincipalKind.AGENT, "worker"),
                    row.name,
                    {"job_id": "not-a-job"} if "{job_id}" in row.http[1] else {},
                    held={
                        "credential": SimpleNamespace(node_id="worker", generation=1)
                    },
                )
            assert refused.value.code == "mesh_node_authentication_required"
    finally:
        db.close()


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


def test_observation_keeps_captured_audio_out_of_pipeline_events(tmp_path):
    import asyncio
    from holdspeak.db import Database
    from holdspeak.services.dictation_service import (
        DictationService,
        bind_dictation_runtime,
    )
    from holdspeak.services.errors import ServiceError
    from holdspeak.web.context import WebContext

    events = []
    db = Database(tmp_path / "audio.db")
    try:
        service = bind_dictation_runtime(
            DictationService(db, observer=SimpleNamespace(on_event=events.append)),
            WebContext(get_state=dict, on_transcribe=lambda *a, **kw: "unused"),
        )
        with pytest.raises(ServiceError):
            asyncio.run(
                service.transcribe_audio(
                    Principal(PrincipalKind.OWNER, "owner"),
                    b"PRIVATE_AUDIO_DO_NOT_RECORD",
                )
            )
        event = next(event for event in events if event.method == "transcribe_audio")
        assert "PRIVATE_AUDIO_DO_NOT_RECORD" not in event.args_summary
        assert "<withheld>" in event.args_summary
    finally:
        db.close()


def test_http_only_rows_state_why_they_have_no_tool():
    for row in SPEECH_ROWS:
        if row.tool_schema is None:
            assert "HTTP-only" in row.description
            assert any(face.startswith("http:") for face in row.exposure)
            assert not any(face.startswith("mcp:") for face in row.exposure)


def test_owner_readiness_stays_out_of_agent_readable_observation(tmp_path, monkeypatch):
    from holdspeak.db import Database
    from holdspeak.services import dictation_readiness
    from holdspeak.services.dictation_service import DictationService

    events = []
    db = Database(tmp_path / "readiness.db")
    try:
        monkeypatch.setattr(
            dictation_readiness, "readiness", lambda source, root, *, db: {"path": root}
        )
        service = DictationService(db, observer=SimpleNamespace(on_event=events.append))
        registry = operations.bind_available({"dictation_service": service})
        result = registry.invoke(
            Principal(PrincipalKind.OWNER, "owner"),
            "dictation.readiness",
            {"project_root": "/PRIVATE_OWNER_PROJECT"},
        )
        assert result == {"path": "/PRIVATE_OWNER_PROJECT"}
        event = next(event for event in events if event.method == "readiness")
        assert "PRIVATE_OWNER_PROJECT" not in event.args_summary + event.result_summary
        assert "<withheld>" in event.result_summary
    finally:
        db.close()


@pytest.mark.parametrize("fails", [False, True])
def test_async_template_write_announces_only_after_completion(monkeypatch, fails):
    import asyncio
    from dataclasses import replace
    from holdspeak.runtime import composition

    sent = []
    monkeypatch.setattr(
        composition, "_installed", SimpleNamespace(_send_desk_changed=sent.append)
    )
    template = next(
        row for row in SPEECH_ROWS if row.name == "dictation.blocks.from_template"
    )

    async def create(principal, **args):
        await asyncio.sleep(0)
        assert sent == []
        if fails:
            raise RuntimeError("save failed")
        return {"id": "new-block"}

    row = replace(
        template,
        held=(),
        call=lambda service, principal, args: create(principal, **args),
    )
    registry = operations.bind({row.service: object()}, (row,))

    async def run():
        pending = registry.invoke(
            Principal(PrincipalKind.OWNER, "owner"), row.name, {"payload": {}}
        )
        assert sent == []
        if fails:
            with pytest.raises(RuntimeError, match="save failed"):
                await pending
            assert sent == []
        else:
            assert await pending == {"id": "new-block"}
            assert len(sent) == 1

    asyncio.run(run())
