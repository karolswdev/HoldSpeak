"""The owner's access rows never grant agent authority or record a credential."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.access_operations import PROFILE_OPERATIONS, REMOTE_ACCESS_OPERATIONS
from holdspeak.channel_operations import CHANNEL_OPERATIONS
from holdspeak.gate_operations import GATE_OPERATIONS
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.settings_operations import (
    CREDENTIAL_OPERATIONS,
    SETTINGS_ROUTE_OPERATIONS,
    TELEGRAM_SECRET_OPERATIONS,
)

OWNER = Principal(PrincipalKind.OWNER, "owner")
AGENT = Principal(PrincipalKind.AGENT, "helper")
SECRET = "marker-owner-value-that-must-never-be-recorded"
ROWS = (
    REMOTE_ACCESS_OPERATIONS
    + PROFILE_OPERATIONS
    + CREDENTIAL_OPERATIONS
    + TELEGRAM_SECRET_OPERATIONS
    + tuple(r for r in CHANNEL_OPERATIONS if r.held)
    + tuple(r for r in SETTINGS_ROUTE_OPERATIONS if r.service == "authority_service" or (r.service == "settings_service" and r.effect == "write"))
    + tuple(
        r for r in GATE_OPERATIONS if r.method in {"full_call", "issue_agent", "decide"}
    )
)


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r.name)
def test_every_access_row_refuses_an_agent_before_recording_any_secret(
    row: Any,
) -> None:
    class Never:
        def __getattr__(self, name: str) -> Any:
            def run(*_args, **_kwargs):
                raise AssertionError(f"Agent reached {name}")
            return run

    assert row.owner_only and "owner_required" in row.refusals
    if row.effect == "write":
        assert row.owner_press
    registry = operations.bind({row.service: Never()}, (row,))
    with pytest.raises(operations.OperationOwnerRequired):
        registry.invoke(
            AGENT,
            row.name,
            {"actor": "owner", "value": SECRET},
            held={field: SECRET for field in row.held},
        )
    if row.tool_schema is not None:
        from holdspeak.mcp.tool_authority import THREAD_EXCLUDED
        assert row.tool_name in THREAD_EXCLUDED


@pytest.fixture
def rig(tmp_path, monkeypatch):
    from holdspeak.config import Config
    from holdspeak.db import Database
    from holdspeak.services.credential_service import CredentialService
    from holdspeak.services.settings_service import SettingsService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.settings import build_settings_router
    import holdspeak.config as config_module

    monkeypatch.delenv("TELNYX_API_KEY", raising=False)
    monkeypatch.delenv("HOLDSPEAK_LINE_SIP_PASSWORD", raising=False)
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "keys.json"))
    Config().save()
    events = []

    class Observer:
        def on_event(self, event):
            events.append(asdict(event))

    db = Database(tmp_path / "access.db")
    credentials = CredentialService(db, observer=Observer())
    settings = SettingsService(db, observer=Observer())
    ctx = WebContext(
        get_state=lambda: {}, credential_service=credentials, settings_service=settings
    )
    registry = operations.for_context(ctx)
    captured = []
    invoke = registry.invoke

    def record(principal, name, args=None, **kwargs):
        captured.append((name, args))
        return invoke(principal, name, args, **kwargs)

    registry.invoke = record
    ctx.operations = registry
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_settings_router(ctx))
    return TestClient(app), credentials, settings, captured, events


@pytest.mark.parametrize(
    "secret_id", ["device_psk", "line_sip_password", "line_telnyx_api_key"]
)
def test_secret_http_write_holds_the_value_and_records_only_redacted_state(
    rig, secret_id
):
    from holdspeak.line import secrets
    from holdspeak.config import Config

    client, credentials, settings, calls, events = rig
    response = client.put(f"/api/settings/secrets/{secret_id}", json={"value": SECRET})
    assert response.status_code == 200, response.text
    assert response.json()["secrets"][secret_id]["configured"] is True
    assert SECRET not in response.text + json.dumps(calls) + json.dumps(events)
    if secret_id in secrets.SECRET_IDS:
        assert secrets.read(secrets.SECRET_IDS[secret_id]) == SECRET
    else:
        assert Config.load().device.psk == SECRET
    removed = client.delete(f"/api/settings/secrets/{secret_id}")
    assert removed.status_code == 200, removed.text
    assert removed.json()["secrets"][secret_id]["configured"] is False
    assert SECRET not in json.dumps(events)


@pytest.mark.parametrize("principal", [OWNER, AGENT])
def test_settings_refuses_each_credential_path_without_recording_the_value(
    rig, principal
):
    from holdspeak.line.secrets import SETTINGS_FIELDS
    from holdspeak.services.credential_service import SECRET_PATHS, RETIRED_CREDENTIAL_PATHS
    from holdspeak.services.errors import ValidationError

    _client, _credentials, settings, _calls, events = rig
    for path in [*SECRET_PATHS.values(), *SETTINGS_FIELDS.values(), *RETIRED_CREDENTIAL_PATHS]:
        patch = SECRET
        for key in reversed(path):
            patch = {key: patch}
        with pytest.raises(ValidationError) as caught:
            settings.update_settings(principal, patch)
        assert caught.value.code == "credential_in_settings_patch"
    assert SECRET not in json.dumps(events)


def test_gate_actor_from_a_non_owner_body_cannot_reach_a_decision(tmp_path):
    from holdspeak.db import Database
    from holdspeak.services.gate_service import GateService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.gate_routes import build_gate_router

    app = FastAPI()

    @app.middleware("http")
    async def agent(request, call_next):
        request.state.principal = AGENT
        return await call_next(request)

    app.include_router(
        build_gate_router(
            WebContext(
                get_state=lambda: {},
                gate_service=GateService(Database(tmp_path / "gate.db")),
            )
        )
    )
    response = TestClient(app).post(
        "/api/gate/proposals/unknown/decide",
        json={"actor": "owner", "decision": "approved"},
    )
    assert response.status_code == 403
    assert response.json()["error"] == "owner_required"


def test_gate_owner_body_cannot_supply_an_actor(tmp_path):
    registry = operations.bind(
        {"gate_service": object()},
        tuple(r for r in GATE_OPERATIONS if r.method == "decide"),
    )
    with pytest.raises(operations.OperationRefused) as caught:
        registry.invoke(
            OWNER,
            "gate.decide",
            {"actor": "owner", "proposal_id": "unknown", "decision": "approved"},
        )
    assert caught.value.code == "authority_in_arguments"


def test_a_credential_save_and_a_settings_edit_preserve_both_values(rig, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from holdspeak.config import Config

    _client, credentials, settings, _calls, _events = rig
    ready, release = threading.Event(), threading.Event()
    save = Config.save

    def held_save(config, *args, **kwargs):
        if config.device.psk == SECRET and config.ui.desk_sounds:
            ready.set()
            assert release.wait(5)
        return save(config, *args, **kwargs)

    monkeypatch.setattr(Config, "save", held_save)
    with ThreadPoolExecutor(max_workers=2) as pool:
        credential = pool.submit(credentials.replace, OWNER, "device_psk", SECRET)
        try:
            assert ready.wait(5)
            edit = pool.submit(settings.update_settings, OWNER, {"ui": {"desk_sounds": False}})
            # If the writer is unsynchronized, it completes here against old
            # state and the held credential save would overwrite its edit.
            try:
                edit.result(timeout=0.1)
            except TimeoutError:
                pass
        finally:
            release.set()
        credential.result(timeout=5)
        assert edit.result(timeout=5)["success"]
    persisted = Config.load()
    assert persisted.device.psk == SECRET and persisted.ui.desk_sounds is False
