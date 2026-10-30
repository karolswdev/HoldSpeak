"""The Line (2026-10-29): Settings ▸ Calls ▸ Line (``calls.line``,
``calls.daily_limit``), its two secrets in the hub's keystore (write only;
the read says where each is), the adapter choice, the node's wire routes and
the faces' status and test call."""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "line-owner")


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database

    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(fake / "keys.json"))
    monkeypatch.delenv("TELNYX_API_KEY", raising=False)
    monkeypatch.delenv("HOLDSPEAK_LINE_SIP_PASSWORD", raising=False)
    monkeypatch.delenv("HOLDSPEAK_AI_PHONE", raising=False)
    monkeypatch.delenv("HOLDSPEAK_LINE", raising=False)
    monkeypatch.setattr(config_module, "CONFIG_FILE", fake / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", fake / "holdspeak.db")
    reset_database()
    yield fake
    reset_database()


def test_the_line_keys_round_trip_and_both_secrets_go_to_the_keystore_only(home, monkeypatch, caplog) -> None:
    from holdspeak.config import Config
    from holdspeak.db import get_database
    from holdspeak.line import secrets
    from holdspeak.services.settings_service import SettingsService

    service = SettingsService(get_database())
    fresh = service.get_settings(OWNER)["calls"]
    assert fresh["daily_limit"] == 20
    assert fresh["line"] == {"adapter": "", "where": "this_mac", "account": {
        "kind": "sip", "user": "holdspeak", "domain": "", "outbound": "", "password_ref": "",
        "connection_id": "", "number": "", "codecs": ["opus", "PCMU", "PCMA"]}, "secrets": {"sip_password": "missing", "telnyx_api_key": "missing"}}
    result = service.update_settings(OWNER, {"calls": {"daily_limit": 5, "line": {
        "adapter": "line", "where": "node:karol", "telnyx_api_key": "KEY-abc",
        "account": {"kind": "telnyx", "user": "hsline", "password": "sip-pass-1", "codecs": "PCMU,PCMA"}}}})
    assert result.get("success") is not False, result
    read = service.get_settings(OWNER)["calls"]
    assert read["daily_limit"] == 5 and read["line"]["where"] == "node:karol"
    assert read["line"]["account"]["password_ref"] == "calls.line.sip_password"
    assert read["line"]["secrets"] == {"sip_password": "keystore", "telnyx_api_key": "keystore"}
    text = json.dumps(read) + (home / ".holdspeak" / "config.json").read_text()
    assert "sip-pass-1" not in text and "KEY-abc" not in text  # never in the read, never in the file
    assert secrets.read(secrets.SIP_PASSWORD) == "sip-pass-1" and secrets.read(secrets.TELNYX_API_KEY) == "KEY-abc"
    # The face sends its read back: the secrets stay; an empty field keeps them; null forgets.
    service.update_settings(OWNER, {"calls": {**read, "line": {**read["line"], "account": {**read["line"]["account"], "password": ""}}}})
    assert secrets.where(secrets.SIP_PASSWORD) == "keystore"
    service.update_settings(OWNER, {"calls": {"line": {"account": {"password": None}}}})
    assert secrets.where(secrets.SIP_PASSWORD) == "missing"
    assert Config.load().calls.line["account"]["password_ref"] == ""


def test_the_environment_is_a_dev_fallback_said_once(home, monkeypatch, caplog) -> None:
    from holdspeak.line import secrets

    monkeypatch.setattr(secrets, "_warned", set())
    monkeypatch.setenv("TELNYX_API_KEY", "KEY-env")
    with caplog.at_level(logging.WARNING):
        assert secrets.read(secrets.TELNYX_API_KEY) == "KEY-env"
        assert secrets.read(secrets.TELNYX_API_KEY) == "KEY-env"
    said = [r.getMessage() for r in caplog.records if "TELNYX_API_KEY" in r.getMessage()]
    assert said == ["TELNYX_API_KEY read from the environment; move it to the keystore in Settings ▸ Calls ▸ Line"]
    assert "KEY-env" not in caplog.text
    assert secrets.presence() == {"sip_password": "missing", "telnyx_api_key": "environment"}
    secrets.write(secrets.TELNYX_API_KEY, "KEY-kept")
    assert secrets.read(secrets.TELNYX_API_KEY) == "KEY-kept" and secrets.where(secrets.TELNYX_API_KEY) == "keystore"


def test_the_adapter_is_the_line_when_baresip_is_found_else_ai_phone_else_none(home, monkeypatch, tmp_path) -> None:
    from holdspeak.calls import service as calls_service
    from holdspeak.calls.aiphone import AiPhone
    from holdspeak.config.calls import CallsConfig
    from holdspeak.line import supervisor
    from holdspeak.line.adapter import Line

    found = {"baresip": None, "ai-phone": None}
    monkeypatch.setattr(supervisor.shutil, "which", lambda name: found.get(name))
    monkeypatch.setattr(calls_service.AiPhone, "from_settings",
                        classmethod(lambda cls, _dir="": AiPhone(["ai-phone"]) if found["ai-phone"] else None))
    cfg = CallsConfig()
    assert calls_service.pick_adapter(cfg) == "none"
    found["ai-phone"] = "/opt/bin/ai-phone"
    assert calls_service.pick_adapter(cfg) == "ai-phone"
    found["baresip"] = "/opt/homebrew/bin/baresip"
    assert calls_service.pick_adapter(cfg) == "line"
    assert calls_service.pick_adapter(CallsConfig(line={"adapter": "ai-phone"})) == "ai-phone"
    monkeypatch.setenv("HOLDSPEAK_AI_PHONE", "python3 fake.py")  # a rig names ai-phone whole
    assert calls_service.pick_adapter(cfg) == "ai-phone"
    assert calls_service.pick_adapter(CallsConfig(line={"adapter": "line"})) == "line"
    monkeypatch.delenv("HOLDSPEAK_AI_PHONE")
    monkeypatch.setenv("HOLDSPEAK_LINE", "off")  # every rig: never the Line
    assert calls_service.pick_adapter(CallsConfig(line={"adapter": "line"})) == "ai-phone"
    monkeypatch.delenv("HOLDSPEAK_LINE")
    assert calls_service.line_node_name("node:karol") == "karol" and calls_service.line_node_name("this_mac") == "this-mac"
    monkeypatch.setattr(calls_service, "_settings", lambda: CallsConfig(line={"where": "node:karol"}))
    phone = calls_service.default_phone()
    assert isinstance(phone, Line) and phone.node == "karol"


def _app(monkeypatch) -> tuple[Any, Any]:
    from holdspeak.calls import service as calls_service
    from holdspeak.line import hub as line_hub
    from holdspeak.web.context import WebContext
    import holdspeak.web.routes.calls as calls_routes

    fresh_hub = line_hub.LineHub()
    monkeypatch.setattr(line_hub, "LINE_HUB", fresh_hub)
    monkeypatch.setattr(calls_routes, "LINE_HUB", fresh_hub)
    monkeypatch.setattr(calls_service, "_LINES", {})
    from holdspeak.line import adapter

    monkeypatch.setattr(adapter, "LINE_HUB", fresh_hub)
    app = FastAPI()
    app.include_router(calls_routes.build_calls_router(WebContext(get_state=lambda: {}, broadcast=lambda k, d: None)))
    return app, fresh_hub


def test_the_wire_routes_carry_hello_events_and_the_long_poll(home, monkeypatch) -> None:
    from holdspeak.line import secrets
    from holdspeak.services.settings_service import SettingsService
    from holdspeak.db import get_database

    SettingsService(get_database()).update_settings(OWNER, {"owner": {"name": "Karol"}, "calls": {"line": {
        "account": {"kind": "telnyx", "user": "hsline", "password": "sip-pass-2"}}}})
    app, line_hub = _app(monkeypatch)
    with TestClient(app) as client:
        hello = client.post("/api/calls/line/hello", json={
            "node": "this-mac", "version": "line-2",
            "lines": [{"id": "main", "kind": "telnyx", "address": "sip:hsline@sip.telnyx.com", "state": "registered"}]})
        assert hello.status_code == 200, hello.text
        config = hello.json()["config"]
        # The node gets the SIP password (for its 0600 accounts file) and never the Telnyx key.
        assert config == {"account": {"kind": "telnyx", "user": "hsline", "domain": "", "outbound": "",
                                      "number": "", "codecs": ["opus", "PCMU", "PCMA"]},
                          "password": "sip-pass-2", "daily_limit": 20, "owner": "Karol"}
        assert secrets.read(secrets.TELNYX_API_KEY) == ""
        empty = client.post("/api/calls/line/next", json={"node": "this-mac", "after": 0, "wait_s": 0})
        assert empty.json() == {"commands": []}
        cmd = line_hub.queue("this-mac", "say", call_id="c1", text="Hello.")
        got = client.post("/api/calls/line/next", json={"node": "this-mac", "after": 0, "wait_s": 5}).json()
        assert got == {"commands": [{"id": cmd, "op": "say", "call_id": "c1", "text": "Hello."}]}
        assert client.post("/api/calls/line/next", json={"node": "this-mac", "after": cmd, "wait_s": 0}).json() == {"commands": []}
        acked = client.post("/api/calls/line/events", json={"node": "this-mac", "events": [
            {"seq": 1, "kind": "incoming", "call_id": "c1", "remote": "sip:+1212@x"},
            {"seq": 1, "kind": "incoming", "call_id": "c1", "remote": "again"}]})
        assert acked.json() == {"acked": 1}
        assert line_hub.take("this-mac", "listen")["remote"] == "sip:+1212@x"
        assert line_hub.take("this-mac", "listen") is None  # a repeated seq is taken once
        assert client.post("/api/calls/line/hello", json={}).status_code == 400
        status = client.get("/api/calls/line/status").json()
        assert status == {"node": "this-mac", "state": "ready", "words": "Ready", "address": "sip:hsline@sip.telnyx.com",
                          "secrets": {"sip_password": "keystore", "telnyx_api_key": "missing"},
                          "machine": {}}, status
        monkeypatch.setenv("HOLDSPEAK_LINE", "off")
        assert client.post("/api/calls/line/hello", json={"node": "x"}).status_code == 409
        assert client.get("/api/calls/line/status").json()["state"] == "off"


def test_the_status_says_where_the_line_is_and_a_test_call_needs_the_line(home, monkeypatch) -> None:
    from holdspeak.calls import service as calls_service
    from holdspeak.line import supervisor

    monkeypatch.setattr(supervisor.shutil, "which", lambda name: "/opt/homebrew/bin/baresip" if name == "baresip" else None)
    app, line_hub = _app(monkeypatch)
    fresh = calls_service.CallsService()
    import holdspeak.web.routes.calls as calls_routes

    monkeypatch.setattr(calls_routes, "CALLS", fresh)
    with TestClient(app) as client:
        status = client.get("/api/calls/status").json()
        assert status["line"]["state"] == "not_running" and status["line"]["words"] == "Not running"
        assert status["aiphone"]["state"] == "off"
        assert [s["words"] for s in status["steps"][:3]] == [
            "Install the line: brew install baresip", "Start it: holdspeak line",
            "Add a line: a SIP address, or a Telnyx number"]
        assert [s["done"] for s in status["steps"][:3]] == [True, False, False]
        line_hub.hello("this-mac", lines=[{"id": "main", "kind": "sip", "address": "sip:holdspeak@127.0.0.1:5060",
                                           "state": "listening"}])
        status = client.get("/api/calls/status").json()
        assert status["line"]["state"] == "ready" and [s["done"] for s in status["steps"][:3]] == [True, True, True]
        refused = client.post("/api/calls/line/test", json={})
        assert refused.status_code == 409 and refused.json()["reason"] == "no_number"
        # A test call: the scripted node answers, the Line says one line and hangs up.
        stop = threading.Event()

        def node() -> None:
            async def run() -> None:
                after = 0
                while not stop.is_set():
                    for command in await line_hub.next("this-mac", after=after, wait=0.2):
                        after = command["id"]
                        reply = {"call": {"outcome": "answered", "call_id": "c9"}, "say": {"result": "said"},
                                 "hangup": {"result": "hung_up"}}[command["op"]]
                        line_hub.post_events("this-mac", [{"seq": after, "kind": "result", "cmd": after,
                                                            "call_id": "c9", **reply}])
                    line_hub.hello("this-mac", lines=[{"id": "main", "kind": "sip", "state": "listening"}])
            asyncio.run(run())

        thread = threading.Thread(target=node, daemon=True)
        thread.start()
        try:
            tested = client.post("/api/calls/line/test", json={"to": "sip:karol@100.64.0.9"})
        finally:
            stop.set()
            thread.join(5)
        assert tested.json() == {"result": "answered", "to": "sip:karol@100.64.0.9"}, tested.text
