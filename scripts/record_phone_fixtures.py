#!/usr/bin/env python3
"""Record the hub's own Phone answers for the faces lane (the test diet's
SCAR LAW: nothing typed by hand, every field a face reads is the hub's).

It runs the real ``PhoneService`` on a fresh database (a null push, no number
line), drives it through the REAL routes (``web/routes/phone.py`` on a
FastAPI ``TestClient``) with the fake phone (``tests/fixtures/fake_phone_device.py``)
into each state the faces draw, then reads every answer back through the
routes and the real Needs you row builder.

    HOME=$(mktemp -d) uv run python scripts/record_phone_fixtures.py

It writes ``web/src/desk/calls/__fixtures__/``: phone.pair.json,
phone.settings.json (``GET /api/phone/status``), phone.devices.json,
phone.thread.json (``GET /api/phone/messages``), phone.calls.json,
phone.events.json, needs_you.phone.json.

    HOME=$(mktemp -d) uv run python scripts/record_phone_fixtures.py --push

records only the Apple push key answers (PHONE-APNS-KEY), with the fake APNs
server (``tests/fixtures/fake_apns.py``) in Apple's place: phone.push.missing.json,
phone.settings.noKey.json, phone.push.put.json, phone.push.stored.json,
phone.push.notP8.json, phone.push.development.json and
phone.push.test.{accepted,stale,refused}.json.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "web" / "src" / "desk" / "calls" / "__fixtures__"


class _NoNumber:
    """No line on this rig: calls ring the paired phone only."""

    def number(self) -> str:
        return ""

    def available(self) -> tuple[bool, str]:
        return False, "your number is not set in Settings ▸ Calls"

    def sms_available(self) -> bool:
        return False


def _app(service: Any) -> Any:
    from fastapi import FastAPI, Request

    from holdspeak.phone import service as phone_module
    from holdspeak.principals import UNAUTHENTICATED
    from holdspeak.web.routes.phone import build_phone_router

    phone_module._DEFAULT = service  # the hub's one instance
    phone_module._DEFAULT_DB = service.db
    phone_module.default_phone_service = lambda db=None: service
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        token = str(request.headers.get("authorization") or "")
        request.state.principal = UNAUTHENTICATED if token.count(".") == 2 else phone_module.OWNER
        return await call_next(request)

    app.include_router(build_phone_router(None))  # type: ignore[arg-type]
    return app


def _get(client: Any, path: str) -> Any:
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def _wait(predicate: Any, seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("the phone did not get there in time")


def record(root: Path) -> dict[str, Any]:
    os.environ.setdefault("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(root / "keys.json"))
    from fastapi.testclient import TestClient

    from holdspeak.db import Database
    from holdspeak.phone.push import NullPush
    from holdspeak.phone.service import PhoneService
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.needs_you_membership import phone_items
    from tests.fixtures.fake_phone_device import FakePhoneDevice

    service = PhoneService(Database(root / "phone.db"), push=NullPush(), number=_NoNumber(),
                           ring_seconds=0.3, rering_seconds=0.3)
    # The faces draw a day-time desk: a run at night would hold every message
    # for quiet hours (PH12), so the recording does not follow the wall clock.
    service._quiet = lambda at=None: False  # type: ignore[method-assign]
    client = TestClient(_app(service), base_url="https://karol-mac.tail1234.ts.net")
    out: dict[str, Any] = {}

    pair = client.post("/api/phone/pair")
    assert pair.status_code == 201, pair.text
    out["phone.pair.json"] = pair.json()
    device = FakePhoneDevice(client, name="Karol's iPhone", platform="ios")
    device.pair(pair.json()["token"])

    # the thread: a desk question, his reply; a message from an agent he has not answered
    asked = client.post("/api/phone/messages", json={"text": "The nightly build is red. Retry it now?"}).json()
    device.events()
    device.read(asked["id"])
    device.reply("Yes, retry it.", asked["id"])
    service.get_replies(0)
    agent = Principal(PrincipalKind.AGENT, "agent-lane")
    service.reach("agent_question", level="normal", text="Which branch is the release: main or release/1.4?",
                  origin_ref="agent:lane-runbook:1")
    service.send_from_desk("Phone: the iPhone rings is finished: every step is done.",
                           origin_ref="program:program-demo:program_done")

    # the calls: answered and ended, missed (a message and a row), held (an agent's)
    answered = client.post("/api/phone/calls", json={"reason": "The runbook step waits to merge"}).json()
    device.accept(answered["call_id"])
    device.end(answered["call_id"])
    missed = client.post("/api/phone/calls", json={"reason": "The deploy waits for your go"}).json()
    _wait(lambda: any(row["origin_ref"] == f"phone_call:{missed['call_id']}" for row in service.store.recent_messages()))
    service.call(agent, reason="The schema step wants to drop a column")

    out["phone.settings.json"] = _get(client, "/api/phone/status")
    out["phone.devices.json"] = _get(client, "/api/phone/devices")
    out["phone.thread.json"] = _get(client, "/api/phone/messages")
    out["phone.calls.json"] = _get(client, "/api/phone/calls")
    out["phone.events.json"] = _get(client, "/api/phone/events")
    out["needs_you.phone.json"] = {"items": phone_items(service.needs_you_items())}
    service.stop()
    return out


def record_push(root: Path) -> dict[str, Any]:
    os.environ.setdefault("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(root / "keys.json"))
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from fastapi.testclient import TestClient

    from holdspeak.db import Database
    from holdspeak.phone.service import PhoneService
    from tests.fixtures.fake_apns import FakeApns
    from tests.fixtures.fake_phone_device import FakePhoneDevice

    pem = ec.generate_private_key(ec.SECP256R1()).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    out: dict[str, Any] = {}
    with FakeApns() as apns:
        service = PhoneService(Database(root / "phone.db"), number=_NoNumber(), apns_host=apns.url)
        service._quiet = lambda at=None: False  # type: ignore[method-assign]
        client = TestClient(_app(service), base_url="https://karol-mac.tail1234.ts.net")
        pair = client.post("/api/phone/pair")
        device = FakePhoneDevice(client, name="Karol's iPhone", platform="ios")
        device.pair(pair.json()["token"])
        out["phone.push.missing.json"] = _get(client, "/api/phone/push")
        out["phone.settings.noKey.json"] = _get(client, "/api/phone/status")
        put = client.put("/api/phone/push", json={"p8": pem})
        assert put.status_code == 200, put.text
        out["phone.push.put.json"] = put.json()
        refused = client.put("/api/phone/push", json={"p8": "not a key"})
        assert refused.status_code == 400, refused.text
        out["phone.push.notP8.json"] = refused.json()
        for body in ({"key_id": "KEY1234567"}, {"team_id": "TEAM123456"}):
            assert client.put("/api/phone/push", json=body).status_code == 200
        out["phone.push.stored.json"] = _get(client, "/api/phone/push")
        xcode = client.put("/api/phone/push", json={"host": "development"})
        assert xcode.status_code == 200, xcode.text
        out["phone.push.development.json"] = xcode.json()
        assert client.put("/api/phone/push", json={"host": "app_store"}).status_code == 200
        for name, answer in (("accepted", (200, {})), ("stale", (400, {"reason": "BadDeviceToken"})),
                             ("refused", (403, {"reason": "InvalidProviderToken"}))):
            apns.answers[device.push_token or ""] = answer
            tested = client.post("/api/phone/push/test")
            assert tested.status_code == 200, tested.text
            out[f"phone.push.test.{name}.json"] = tested.json()
        service.stop()
    return out


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        recorded = record_push(Path(tmp)) if "--push" in sys.argv[1:] else record(Path(tmp))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in recorded.items():
        (OUT / name).write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO) / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
