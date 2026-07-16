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

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.coder_steering import arm, clear_grants
from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
from holdspeak.delivery.node_link import (
    NODE_PROTOCOL,
    NodeLinkState,
    NodeTokenStore,
)
from holdspeak.delivery.terminal import TerminalStreamService, TerminalTargetRegistry
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_terminal import build_delivery_terminal_router

WEB_TOKEN = "the-browser-token"
KEY = "claude:hs94"
T0 = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)


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
    app.include_router(
        build_delivery_terminal_router(
            WebContext(get_state=lambda: {}),
            service=service,
            stream=stream,
            targets=targets,
            link=link,
        )
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
    res = rig.client.post(
        "/api/delivery/terminal/targets", json={"ref": "pane:%5"}
    )
    assert res.status_code == 200
    return res.json()


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


def test_target_issue_and_dead_pane_refusal(rig) -> None:
    issued = _target(rig)
    assert issued["status"] == "issued"
    assert issued["pane_id"] == "%5"
    assert issued["node_id"] == "local"
    gone = rig.client.post(
        "/api/delivery/terminal/targets", json={"ref": "pane:%404"}
    )
    assert gone.status_code == 404
    assert gone.json()["status"] == "pane_gone"


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
    receipt = first.json()["receipt"]
    assert receipt["state"] == "succeeded"
    assert receipt["outcome"] == "delivered"
    assert len(rig.transport_calls) == 1

    # The lost-response retry: same command_id, same receipt, ONE effect.
    again = rig.client.post("/api/delivery/terminal/commands", json=body)
    assert again.status_code == 200
    assert again.json()["receipt"]["receipt_id"] == receipt["receipt_id"]
    assert len(rig.transport_calls) == 1

    joined = rig.client.get(
        "/api/delivery/terminal/commands/aaaaaaaa-bbbb-cccc-dddd-eeeeffff0001"
    )
    assert joined.status_code == 200
    assert joined.json()["hub_state"] == "complete"
    assert joined.json()["receipt"]["receipt_id"] == receipt["receipt_id"]


def test_client_authority_is_refused_by_name(rig) -> None:
    target = _target(rig)
    res = rig.client.post(
        "/api/delivery/terminal/commands",
        json={**_steer_body(target), "authority": {"decision": "allowed"}},
    )
    assert res.status_code == 400
    assert res.json()["error"] == "authority_not_client_settable"
    assert rig.transport_calls == []


def test_unknown_command_id_receipt_is_404(rig) -> None:
    res = rig.client.get(
        "/api/delivery/terminal/commands/99999999-0000-0000-0000-000000000000"
    )
    assert res.status_code == 404
    assert res.json()["error"] == "unknown_command_id"


def test_remote_claim_rides_the_node_link_and_results_leg(rig) -> None:
    _, token = rig.link.token_store.create("studio-mac")
    rig.link.hello(
        "studio-mac",
        token,
        node_protocol=NODE_PROTOCOL,
        instance_id="proc-1",
        capabilities=["coder.steering"],
    )
    node_id = rig.link.status_of("studio-mac") and rig.link.nodes_view()["nodes"][0]["node_id"]

    sent = rig.service.submit(
        {
            "node_id": node_id,
            "target_id": "term_remote",
            "target_generation": "gen_remote",
            "operation": {"family": "coder_steering", "verb": "terminal.text"},
            "payload": {"text": "over the wire", "session_key": KEY},
            "expected_sequence": 1,
        }
    )
    assert sent["state"] == "sent"

    # The node's claim leg (HS-94-03's endpoint shape) now carries it.
    claim = rig.link.poll_commands("studio-mac", token)
    assert claim["commands_schema"] == 1
    assert [c["command_id"] for c in claim["commands"]] == [sent["command_id"]]
    envelope = claim["commands"][0]
    assert envelope["authority"]["actor"] == "owner"

    # Results leg: the node's OWN token; receipts join the hub half.
    receipt = {
        "receipt_schema": 1,
        "receipt_id": "receipt_wire1",
        "command_id": sent["command_id"],
        "node_id": node_id,
        "target_id": "term_remote",
        "target_generation": "gen_remote",
        "state": "succeeded",
        "outcome": "delivered",
        "applied_sequence": 1,
        "payload_sha256": envelope["payload_sha256"],
        "payload_head": envelope["payload_head"],
    }
    res = rig.client.post(
        "/api/delivery/terminal/node/results",
        json={"name": "studio-mac", "results": [receipt]},
        headers={"X-HoldSpeak-Node-Token": token},
    )
    assert res.status_code == 200
    assert res.json() == {"ok": True, "processed": 1}
    joined = rig.client.get(
        f"/api/delivery/terminal/commands/{sent['command_id']}"
    )
    assert joined.json()["hub_state"] == "complete"
    assert joined.json()["receipt"]["receipt_id"] == "receipt_wire1"


def test_results_leg_refuses_wrong_and_browser_tokens(rig) -> None:
    rig.link.token_store.create("studio-mac")
    wrong = rig.client.post(
        "/api/delivery/terminal/node/results",
        json={"name": "studio-mac", "results": []},
        headers={"X-HoldSpeak-Node-Token": "not-the-token"},
    )
    assert wrong.status_code == 401
    assert wrong.json()["error"] == "token_rejected"

    browser = rig.client.post(
        "/api/delivery/terminal/node/results",
        json={"name": "studio-mac", "results": []},
        headers={"X-HoldSpeak-Node-Token": WEB_TOKEN},
    )
    assert browser.status_code == 401
    assert browser.json()["error"] == "node_token_required"
