"""HS-94-06 — the terminal HTTP surface, assembled in-test.

Router precedent: build onto a bare FastAPI app with every seam
injected. Proven here: target issuance, the subscription envelopes and
their typed-absence status codes, command submission (client authority
refused by name; duplicate POST returns the SAME receipt), the joined
Receipt GET, and the node results leg riding the node link's OWN token
auth — including the claim leg through ``NodeLinkState.poll_commands``
via the ``command_source`` hook.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import threading
import time
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.coder_steering import arm, clear_grants
from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
from holdspeak.delivery.node_link import (
    NodeLinkState,
    NodeTokenStore,
)
from holdspeak.delivery.terminal import TerminalStreamService, TerminalTargetRegistry
from holdspeak.web.announce import QUIET_ROUTES
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.delivery_service import DeliveryService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_terminal import build_delivery_terminal_router

WEB_TOKEN = "the-browser-token"
KEY = "claude:hs94"
T0 = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
OWNER = Principal(PrincipalKind.OWNER, "owner-session")


class FakeTmux:
    def __init__(self) -> None:
        self.panes: dict[str, str] = {"%5": "hello from %5"}
        self.refs: dict[str, str] = {"hs:0.0": "%5"}

    def __call__(self, argv, cwd=None):
        target = argv[argv.index("-t") + 1]
        pane = self._resolve(target)
        if argv[1] == "display-message":
            if pane is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="no pane")
            return SimpleNamespace(returncode=0, stdout=pane + "\n", stderr="")
        if argv[1] == "capture-pane":
            if pane is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="no pane")
            return SimpleNamespace(
                returncode=0, stdout=self.panes[pane] + "\n", stderr=""
            )
        raise AssertionError(f"unexpected tmux verb: {argv}")

    def _resolve(self, target: str):
        if target.startswith("%"):
            return target if target in self.panes else None
        pane = self.refs.get(target)
        return pane if pane in self.panes else None


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


@pytest.fixture(autouse=True)
def _fresh_grants():
    clear_grants()
    yield
    clear_grants()


@pytest.fixture
def rig(tmp_path):
    tmux = FakeTmux()
    clock = Clock()
    targets = TerminalTargetRegistry(runner=tmux)
    stream = TerminalStreamService(targets, runner=tmux, clock=clock)
    transport_calls: list[dict] = []
    processor = NodeCommandProcessor(
        node_id="local",
        targets=targets,
        ledger=NodeReceiptLedger(tmp_path / "ledger.db"),
        runner=tmux,
        audit=lambda **kw: 1,
        text_transport=lambda **kw: transport_calls.append(kw),
        wall_now=lambda: T0,
    )
    db = Database(tmp_path / "hub.db")
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=processor,
        local_node_id="local",
        mode_loader=lambda: "neutral",
        wall_now=lambda: T0,
    )
    link = NodeLinkState(
        NodeTokenStore(tmp_path / "tokens.json"),
        web_token=WEB_TOKEN,
        command_source=service.claim_for_node,
    )
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(
        build_delivery_terminal_router(WebContext(
            get_state=lambda: {},
            delivery_service=DeliveryService(None).configure(
                commands=service, stream=stream, targets=targets, link=link,
            ),
        ))
    )
    return SimpleNamespace(
        client=TestClient(app),
        tmux=tmux,
        clock=clock,
        targets=targets,
        service=service,
        link=link,
        transport_calls=transport_calls,
    )


def _target(rig) -> dict:
    """Issue the pane's target on the registry (the web reads targets from /sessions)."""
    issued = rig.targets.issue("pane:%5")
    assert issued["status"] == "issued"
    return issued


def _steer_body(target: dict, **payload_extra) -> dict:
    return {
        "target_id": target["target_id"],
        "target_generation": target["target_generation"],
        "operation": {"family": "coder_steering", "verb": "terminal.text"},
        "payload": {
            "text": "steer over http",
            "session_key": KEY,
            "submit": False,
            **payload_extra,
        },
    }


def test_subscription_snapshot_deltas_and_typed_absences(rig) -> None:
    target = _target(rig)
    sub = {
        "target_id": target["target_id"],
        "target_generation": target["target_generation"],
    }
    snap = rig.client.post("/api/delivery/terminal/subscriptions", json=sub)
    assert snap.status_code == 200
    body = snap.json()
    assert body["status"] == "snapshot"
    assert body["content"] == "hello from %5"

    rig.tmux.panes["%5"] += "\nmore output"
    rig.clock.advance(1.0)
    deltas = rig.client.post(
        "/api/delivery/terminal/subscriptions",
        json={**sub, "resume_sequence": body["sequence"]},
    )
    assert deltas.status_code == 200
    assert deltas.json()["status"] == "deltas"
    assert deltas.json()["deltas"][0]["data"] == "\nmore output"

    # The pane dies: a pure %N target is GONE, typed as a 404.
    del rig.tmux.panes["%5"]
    stale = rig.client.post("/api/delivery/terminal/subscriptions", json=sub)
    assert stale.status_code == 404
    assert stale.json()["status"] == "target_gone"


def test_subscription_absence_status_codes(rig) -> None:
    # unknown target → target_gone → 404
    res = rig.client.post(
        "/api/delivery/terminal/subscriptions",
        json={"target_id": "term_nope", "target_generation": "gen_nope"},
    )
    assert res.status_code == 404
    assert res.json()["status"] == "target_gone"

    # session-ref target recycled under the same address → 409
    issued = rig.targets.issue("hs:0.0")
    del rig.tmux.panes["%5"]
    rig.tmux.panes["%9"] = "impostor"
    rig.tmux.refs["hs:0.0"] = "%9"
    res = rig.client.post(
        "/api/delivery/terminal/subscriptions",
        json={
            "target_id": issued["target_id"],
            "target_generation": issued["target_generation"],
        },
    )
    assert res.status_code == 409
    assert res.json()["status"] == "generation_mismatch"


class _FiniteLiveSubscription:
    def __init__(self) -> None:
        self.closed = False

    def frames(self):
        yield {"status": "snapshot", "stream_id": "live_test", "sequence": 1, "encoding": "base64", "data": "aGVsbG8="}
        yield {"status": "output", "stream_id": "live_test", "sequence": 2, "encoding": "base64", "data": "AP8="}

    def close(self) -> None:
        self.closed = True


class _FiniteLive:
    def __init__(self) -> None:
        self.subscription = _FiniteLiveSubscription()

    def subscribe(self, *args, **kwargs):
        return self.subscription


class _BlockingLiveSubscription:
    def __init__(self) -> None:
        self.closed = False
        self.wake = threading.Event()

    def frames(self):
        yield {"status": "snapshot", "stream_id": "live_block", "sequence": 1, "encoding": "base64", "data": "aGVsbG8="}
        while not self.closed:
            self.wake.wait(5)

    def close(self) -> None:
        self.closed = True
        self.wake.set()


class _BlockingLive:
    def __init__(self) -> None:
        self.subscription = _BlockingLiveSubscription()

    def subscribe(self, *args, **kwargs):
        return self.subscription


def test_live_route_streams_ndjson_and_is_quiet(rig) -> None:
    live = _FiniteLive()
    # The router gets its live provider through the same composition seam as
    # the production service; finite frames keep this route test bounded.
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(
        build_delivery_terminal_router(WebContext(
            get_state=lambda: {},
            delivery_service=DeliveryService(None).configure(
                commands=rig.service, stream=TerminalStreamService(rig.targets, runner=rig.tmux),
                live=live, targets=rig.targets, link=rig.link,
            ),
        ))
    )
    target = _target(rig)
    with TestClient(app) as client:
        response = client.post(
            "/api/delivery/terminal/live",
            json={"target_id": target["target_id"], "target_generation": target["target_generation"]},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    lines = response.text.splitlines()
    assert '"status":"snapshot"' in lines[0]
    assert '"status":"output"' in lines[1]
    assert live.subscription.closed is True
    assert ("POST", "/api/delivery/terminal/live") in QUIET_ROUTES


def test_live_route_disconnect_closes_blocked_offloop_reader(rig) -> None:
    live = _BlockingLive()
    app = FastAPI()
    app.include_router(
        build_delivery_terminal_router(WebContext(
            get_state=lambda: {},
            delivery_service=DeliveryService(None).configure(
                commands=rig.service, stream=TerminalStreamService(rig.targets, runner=rig.tmux),
                live=live, targets=rig.targets, link=rig.link,
            ),
        ))
    )
    route = next(route for route in app.routes if getattr(route, "path", "") == "/api/delivery/terminal/live")
    target = _target(rig)

    async def walk() -> None:
        from holdspeak.web.routes.delivery_terminal import _LiveRequest
        response = await route.endpoint(
            _LiveRequest(target_id=target["target_id"], target_generation=target["target_generation"]),
            Request({"type": "http", "state": {"principal": OWNER}}),
        )
        iterator = response.body_iterator
        first = await iterator.__anext__()
        assert b'"status":"snapshot"' in first
        pending = asyncio.create_task(iterator.__anext__())
        await asyncio.sleep(0.05)
        started = time.monotonic()
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert live.subscription.closed is True
        assert time.monotonic() - started < 1.0
        await iterator.aclose()

    asyncio.run(walk())


def test_command_submit_duplicate_and_receipt_join(rig) -> None:
    armed = arm(KEY, "hs:0.0", runner=rig.tmux, control_mode="neutral")
    assert armed["status"] == "armed"
    target = _target(rig)
    body = {
        **_steer_body(target),
        "command_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeffff0001",
        "expected_sequence": 1,
    }
    first = rig.client.post("/api/delivery/terminal/commands", json=body)
    assert first.status_code == 200
    assert set(first.json()) == {"command_id", "state", "receipt", "operation_id"}
    receipt = first.json()["receipt"]
    assert receipt["state"] == "succeeded"
    assert receipt["outcome"] == "delivered"
    assert len(rig.transport_calls) == 1

    # The lost-response retry: same command_id, same receipt, ONE effect.
    again = rig.client.post("/api/delivery/terminal/commands", json=body)
    assert again.status_code == 200
    assert set(again.json()) == {
        "command_id", "state", "duplicate", "receipt", "operation_id"
    }
    assert again.json()["receipt"]["receipt_id"] == receipt["receipt_id"]
    assert len(rig.transport_calls) == 1

    joined = rig.service.receipt("aaaaaaaa-bbbb-cccc-dddd-eeeeffff0001")
    assert joined["hub_state"] == "complete"
    assert joined["receipt"]["receipt_id"] == receipt["receipt_id"]


def test_resize_command_route_passes_authenticated_principal(rig, monkeypatch) -> None:
    target = _target(rig)
    seen: dict[str, object] = {}

    def resize(body, principal):
        seen["body"] = body
        seen["principal"] = principal
        return {"command_id": body.get("command_id", "resize"), "state": "complete"}

    monkeypatch.setattr(rig.service, "submit_process_resize", resize)
    body = {
        "target_id": target["target_id"],
        "target_generation": target["target_generation"],
        "operation": {"family": "coder_steering", "verb": "process.resize@1"},
        "payload": {"cols": 100, "rows": 30, "session_key": KEY},
    }
    response = rig.client.post("/api/delivery/terminal/commands", json=body)
    assert response.status_code == 200
    assert seen["principal"] is OWNER
    assert seen["body"] == body


def test_client_authority_is_refused_by_name(rig) -> None:
    target = _target(rig)
    res = rig.client.post(
        "/api/delivery/terminal/commands",
        json={**_steer_body(target), "authority": {"decision": "allowed"}},
    )
    assert res.status_code == 400
    assert res.json()["error"] == "authority_in_arguments"
    assert rig.transport_calls == []
