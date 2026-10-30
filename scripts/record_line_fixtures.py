#!/usr/bin/env python3
"""Record the hub's own Line answers for the faces (LINE-4; the test diet's
SCAR LAW: nothing typed by hand, every field a face reads is the hub's).

It runs the real Calls and Settings routes (``web/routes/calls.py``,
``web/routes/system/settings.py``) on a FastAPI ``TestClient`` against a
fresh HOME, with a fresh ``LineHub``. The Line node is the real ``LineNode``
on the fake baresip (``tests/fixtures/fake_baresip.py``, a real separate
process replaying recorded baresip 4.12.0 events), linked in process to that
hub (``tests/fixtures/line_rig.py``). Each state the faces draw is reached
through the wire and read back through the routes.

    HOME=$(mktemp -d) uv run python scripts/record_line_fixtures.py

It writes ``web/src/desk/calls/__fixtures__/line.*.json``.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "web" / "src" / "desk" / "calls" / "__fixtures__"
HIS_SIP = "sip:karol@karol-iphone"
#: The desk's own address, as the face sends it (``window.location.origin``).
DESK = "https://holdspeak.tailnet.ts.net"
#: The home box's hello, as `holdspeak line` there says it (`node.machine_block`,
#: the values #1610 measured on karol).
KAROL = {"name": "karol", "platform": "Linux x86_64", "baresip": "4.12.0",
         "models": [{"id": "line-stt", "name": "Phone speech in (Parakeet)", "state": "ready"},
                    {"id": "line-tts", "name": "Phone speech out (Pocket TTS)", "state": "ready"}]}


class _Node:
    """A Line node on the fake baresip, run on its own loop in a thread."""

    def __init__(self, hub: Any, scenario: dict[str, Any], *, name: str = "this-mac",
                 machine: dict[str, Any] | None = None) -> None:
        self.hub, self.scenario = hub, scenario
        self.name, self.machine = name, machine
        self.ready = threading.Event()
        self.stop = threading.Event()
        self.error: BaseException | None = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        from tests.fixtures.line_rig import running_node

        async def main() -> None:
            async with running_node(self.scenario, hub=self.hub, heartbeat=0.2, name=self.name, machine=self.machine):
                self.ready.set()
                while not self.stop.is_set():
                    await asyncio.sleep(0.05)

        try:
            asyncio.run(main())
        except BaseException as exc:  # noqa: BLE001 — said by the caller
            self.error = exc
            self.ready.set()

    def __enter__(self) -> "_Node":
        self.thread.start()
        assert self.ready.wait(20), "the Line node did not start"
        if self.error:
            raise self.error
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop.set()
        self.thread.join(20)


def _wait(predicate: Any, seconds: float = 10.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("the Line did not get there in time")


def record(root: Path) -> dict[str, Any]:
    os.environ["HOLDSPEAK_CHANNEL_KEYSTORE_FILE"] = str(root / "keys.json")
    for key in ("TELNYX_API_KEY", "HOLDSPEAK_LINE_SIP_PASSWORD", "HOLDSPEAK_AI_PHONE", "HOLDSPEAK_LINE", "HOLDSPEAK_CALLS"):
        os.environ.pop(key, None)

    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient

    import holdspeak.calls.service as calls_service
    import holdspeak.line.adapter as line_adapter
    import holdspeak.line.hub as line_hub
    import holdspeak.line.supervisor as supervisor
    import holdspeak.web.routes.calls as calls_routes
    from holdspeak.db import get_database
    from holdspeak.delivery.node_link import NodeTokenStore
    from holdspeak.line import enrol as line_enrol
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.settings_service import SettingsService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.settings import build_settings_router

    hub = line_hub.LineHub()
    hub.config_fn = calls_service.line_config
    for module in (line_hub, calls_routes, line_adapter):
        module.LINE_HUB = hub  # type: ignore[attr-defined]
    calls_service._LINES.clear()
    service = calls_service.CallsService()
    calls_routes.CALLS = service  # type: ignore[attr-defined]
    baresip = {"path": None}
    supervisor.find_baresip = lambda *a, **k: baresip["path"]  # type: ignore[assignment]

    owner = Principal(PrincipalKind.OWNER, "line-owner")
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        request.state.principal = owner
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, broadcast=lambda kind, data: None,
                     settings_service=SettingsService(get_database()),
                     credential_service=object())  # the secret routes are not read here
    app.include_router(calls_routes.build_calls_router(ctx))
    app.include_router(build_settings_router(ctx))
    # The hub's node token store (the custody every node shares), in this HOME.
    app.state.node_token_store = NodeTokenStore(root / "node_auth_tokens.json")
    calls_routes.CODES = line_enrol.EnrolCodes()  # type: ignore[attr-defined]
    client = TestClient(app)

    def get(path: str) -> Any:
        answer = client.get(path)
        assert answer.status_code == 200, (path, answer.status_code, answer.text[:300])
        return answer.json()

    def put(patch: dict[str, Any]) -> Any:
        answer = client.put("/api/settings", json=patch)
        assert answer.status_code == 200 and answer.json().get("success", True) is not False, answer.text[:300]
        return answer.json()

    def calls_section() -> Any:
        return get("/api/settings")["calls"]

    out: dict[str, Any] = {}
    # His desk: Calls on, a passphrase, his SIP app first; the Line on this Mac.
    put({"owner": {"name": "Karol"}, "calls": {"enabled": True, "passphrase": "blue heron",
                                              "allowed_numbers": [HIS_SIP, "+12125550142"],
                                              "line": {"adapter": "line", "where": "this_mac"}}})

    # 1. Nothing installed: no baresip on this Mac.
    out["line.status.notInstalled.json"] = get("/api/calls/line/status")
    out["line.calls.notInstalled.json"] = get("/api/calls/status")
    # 2. baresip is here, the Line is not running (the owner's live hub on 2026-10-29).
    baresip["path"] = "/opt/homebrew/bin/baresip"
    out["line.status.notRunning.json"] = get("/api/calls/line/status")
    out["line.calls.notRunning.json"] = get("/api/calls/status")
    out["line.settings.json"] = calls_section()

    # 3. Starting: the node said hello, its line is not up yet.
    started = client.post("/api/calls/line/hello", json={"node": "this-mac", "version": "line-2", "lines": [
        {"id": "main", "kind": "sip", "address": "", "state": "starting"}]})
    assert started.status_code == 200, started.text
    out["line.status.starting.json"] = get("/api/calls/line/status")
    out["line.calls.starting.json"] = get("/api/calls/status")
    hub.reset()

    # 4. Ready: the free SIP address, the node on the fake baresip; Test call each way.
    for mode, name in (("answer", "answered"), ("busy", "busy"), ("decline", "rejected"), ("none", "noAnswer")):
        with _Node(hub, {"dial": mode}):
            _wait(lambda: get("/api/calls/line/status")["state"] == "ready")
            if mode == "answer":
                out["line.status.ready.json"] = get("/api/calls/line/status")
                out["line.calls.ready.json"] = get("/api/calls/status")
            tested = client.post("/api/calls/line/test", json={})
            assert tested.status_code == 200, tested.text
            out[f"line.test.{name}.json"] = tested.json()
        hub.reset()
        calls_service._LINES.clear()
    # The Line not running: a Test call is refused with the hub's own reason.
    refused = client.post("/api/calls/line/test", json={})
    out["line.test.notRunning.json"] = {"status": refused.status_code, "body": refused.json()}
    # No number to call.
    numbers = calls_section()["allowed_numbers"]
    put({"calls": {"allowed_numbers": []}})
    with _Node(hub, {"dial": "answer"}):
        _wait(lambda: get("/api/calls/line/status")["state"] == "ready")
        none = client.post("/api/calls/line/test", json={})
        out["line.test.noNumber.json"] = {"status": none.status_code, "body": none.json()}
    hub.reset()
    calls_service._LINES.clear()
    put({"calls": {"allowed_numbers": numbers}})

    # 5. A Telnyx number: no password yet; the API key only in his shell.
    put({"calls": {"line": {"account": {"kind": "telnyx", "user": "hsline", "domain": "sip.telnyx.com",
                                         "outbound": "sip:sip.telnyx.com;transport=tcp", "codecs": ["PCMU", "PCMA", "opus"]}}}})
    os.environ["TELNYX_API_KEY"] = "KEY-in-his-shell"
    with _Node(hub, {"dial": "answer"}):
        _wait(lambda: get("/api/calls/line/status")["state"] in {"not_set_up", "ready"})
        out["line.status.telnyxMissing.json"] = get("/api/calls/line/status")
        out["line.settings.telnyxMissing.json"] = calls_section()
        # The write: the password and the key go to the keystore.
        out["line.put.password.json"] = put({"calls": {"line": {"account": {"password": "sip-secret"}, "telnyx_api_key": "KEY-typed"}}})
        out["line.status.telnyxStored.json"] = get("/api/calls/line/status")
        out["line.settings.telnyxStored.json"] = calls_section()
    os.environ.pop("TELNYX_API_KEY", None)
    hub.reset()
    put({"calls": {"line": {"account": {"kind": "sip"}}}})

    # 6. Another machine (LINE-3): none enrolled; Install the Line on karol
    #    mints a one-time code and the command; a bad name is refused.
    out["line.nodes.none.json"] = get("/api/calls/line/nodes")
    minted = client.post("/api/calls/line/codes", json={"node": "karol", "hub": DESK})
    assert minted.status_code == 200, minted.text
    out["line.codes.karol.json"] = minted.json()
    bad = client.post("/api/calls/line/codes", json={"node": "Karol's box!", "hub": DESK})
    out["line.codes.badName.json"] = {"status": bad.status_code, "body": bad.json()}
    # karol runs the command: the code becomes karol's credential (never in a read).
    enrolled = client.post("/api/calls/line/enrol", json={"code": minted.json()["code"]})
    assert enrolled.status_code == 200, enrolled.text
    token = enrolled.json()["token"]
    # Enrolled, no hello yet: the row reads Not running.
    out["line.nodes.enrolled.json"] = get("/api/calls/line/nodes")
    # The Line on karol says hello (the real node on the fake baresip): Ready.
    with _Node(hub, {"dial": "answer"}, name="karol", machine=KAROL):
        _wait(lambda: get("/api/calls/line/nodes")["nodes"][0]["state"] == "ready")
        out["line.nodes.ready.json"] = get("/api/calls/line/nodes")
        # He picks karol as the place.
        out["line.put.whereKarol.json"] = put({"calls": {"line": {"where": "node:karol"}}})
        out["line.settings.karol.json"] = calls_section()
        _wait(lambda: get("/api/calls/line/status")["state"] == "ready")
        out["line.status.karol.json"] = get("/api/calls/line/status")
    put({"calls": {"line": {"where": "this_mac"}}})
    hub.reset()
    calls_service._LINES.clear()
    # Revoke: the credential is gone and so is the row.
    revoked = client.delete("/api/calls/line/nodes/karol")
    assert revoked.status_code == 200, revoked.text
    out["line.nodes.revoke.json"] = revoked.json()
    assert get("/api/calls/line/nodes") == out["line.nodes.none.json"]

    text = json.dumps(out)
    assert token not in text, "a node credential in a read"
    assert "sip-secret" not in text and "KEY-typed" not in text and "KEY-in-his-shell" not in text, "a secret in a read"
    return out


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        recorded = record(Path(tmp))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in recorded.items():
        (OUT / name).write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO) / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
