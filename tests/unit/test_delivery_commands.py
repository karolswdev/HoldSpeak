"""HS-94-06 — the command envelope and its idempotent receipts.

Contract §8 proven end to end without tmux: the node processing order
(dedup → expiry → target/generation → policy → sequence → chokepoint →
persist), duplicate envelopes returning the SAME receipt with ONE
execution, out-of-order refusal that types nothing, the recycled-pane
generation refusal that also revokes the grant, the Phase-93 posture
matrix consumed as ONE policy decision, and reconcile-by-command_id
including ``indeterminate_after_node_reset``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import holdspeak.delivery.commands as commands_mod
from holdspeak.coder_steering import active_grants, arm, clear_grants
from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery.commands import (
    COMMAND_SCHEMA,
    CommandRefused,
    HubCommandService,
    NodeCommandProcessor,
    build_envelope,
    payload_digest,
    validate_envelope,
)
from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.operation_policy import POLICY_VERSION

T0 = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
KEY = "claude:hs94"


class FakeTmux:
    def __init__(self) -> None:
        self.panes: dict[str, str] = {"%5": "ready"}
        self.refs: dict[str, str] = {"hs:0.0": "%5"}

    def __call__(self, argv, cwd=None):
        verb = argv[1]
        if verb == "display-message":
            pane = self._resolve(argv[argv.index("-t") + 1])
            if pane is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="no pane")
            return SimpleNamespace(returncode=0, stdout=pane + "\n", stderr="")
        if verb == "kill-pane":
            pane = self._resolve(argv[argv.index("-t") + 1])
            if pane is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="no pane")
            del self.panes[pane]
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected tmux verb: {argv}")

    def _resolve(self, target: str):
        if target.startswith("%"):
            return target if target in self.panes else None
        pane = self.refs.get(target)
        return pane if pane in self.panes else None


class Transport:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def __call__(self, **kw):
        self.sent.append(kw)


@pytest.fixture(autouse=True)
def _fresh_grants():
    clear_grants()
    yield
    clear_grants()


@pytest.fixture
def tmux() -> FakeTmux:
    return FakeTmux()


@pytest.fixture
def rig(tmp_path, tmux):
    """targets + ledger + processor + hub service over a real hub DB."""
    targets = TerminalTargetRegistry(runner=tmux)
    ledger = NodeReceiptLedger(tmp_path / "ledger.db")
    transport = Transport()
    keys_transport = Transport()
    audit_rows: list[dict] = []
    processor = NodeCommandProcessor(
        node_id="local",
        targets=targets,
        ledger=ledger,
        runner=tmux,
        audit=lambda **kw: audit_rows.append(kw) or len(audit_rows),
        text_transport=transport,
        keys_transport=keys_transport,
        wall_now=lambda: T0,
    )
    db = Database(tmp_path / "hub.db")
    modes = {"mode": "neutral"}
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=processor,
        local_node_id="local",
        mode_loader=lambda: modes["mode"],
        wall_now=lambda: T0,
    )
    return SimpleNamespace(
        targets=targets,
        ledger=ledger,
        processor=processor,
        service=service,
        transport=transport,
        keys_transport=keys_transport,
        audit_rows=audit_rows,
        modes=modes,
        db=db,
        tmux=tmux,
    )


def _issued(rig, ref="hs:0.0") -> dict:
    issued = rig.targets.issue(ref)
    assert issued["status"] == "issued"
    return issued


def _authority(decision="allowed_by_active_grant", posture="neutral", grant=KEY):
    return {
        "actor": "owner",
        "control_posture": posture,
        "decision": decision,
        "policy_version": POLICY_VERSION,
        "grant_id": grant,
    }


def _envelope(rig, target, *, verb="terminal.text", payload=None, seq=1, **kw):
    return build_envelope(
        node_id="local",
        target_id=target["target_id"],
        target_generation=target["target_generation"],
        family="coder_factory" if verb.startswith("factory.") else "coder_steering",
        verb=verb,
        payload=payload
        or {"text": "steer it", "session_key": KEY, "submit": False},
        expected_sequence=seq,
        authority=kw.pop("authority", _authority()),
        now=kw.pop("now", T0),
        **kw,
    )


def _arm(tmux, mode="neutral"):
    armed = arm(KEY, "hs:0.0", runner=tmux, control_mode=mode)
    assert armed["status"] == "armed"
    return armed


# ── envelope validation ──────────────────────────────────────────────


def test_envelope_shape_round_trip(rig) -> None:
    target = _issued(rig)
    env = _envelope(rig, target)
    assert env["command_schema"] == COMMAND_SCHEMA
    assert env["payload_sha256"] == payload_digest(env["payload"])
    assert env["payload_head"] == "steer it"
    assert env["authority"]["policy_version"] == POLICY_VERSION
    assert validate_envelope(env) == env


def test_tampered_payload_refuses_by_hash(rig) -> None:
    target = _issued(rig)
    env = _envelope(rig, target)
    env["payload"]["text"] = "something else entirely"
    with pytest.raises(CommandRefused) as exc:
        validate_envelope(env)
    assert exc.value.reason == "payload_hash_mismatch"


def test_unknown_operation_and_fields_refuse_by_name(rig) -> None:
    target = _issued(rig)
    env = _envelope(rig, target)
    bad = {**env, "smuggled": True}
    with pytest.raises(CommandRefused) as exc:
        validate_envelope(bad)
    assert exc.value.reason == "envelope_field_not_allowed"


# ── the §8 order on the node ─────────────────────────────────────────


def test_duplicate_envelope_returns_same_receipt_and_executes_once(rig, tmux) -> None:
    _arm(tmux)
    target = _issued(rig)
    env = _envelope(rig, target)
    first = rig.processor.process(env)
    assert first["state"] == "succeeded"
    assert first["outcome"] == "delivered"
    assert first["applied_sequence"] == 1
    assert first["node_audit_id"] == 1

    again = rig.processor.process(env)
    assert again == first  # the SAME receipt, byte for byte
    assert len(rig.transport.sent) == 1  # ONE keystroke ever reached tmux
    assert rig.processor.executions == 1


def test_expired_command_refuses_before_anything(rig, tmux) -> None:
    _arm(tmux)
    target = _issued(rig)
    env = _envelope(rig, target, now=T0 - timedelta(minutes=10), ttl_seconds=5)
    out = rig.processor.process(env)
    assert out["state"] == "refused"
    assert out["outcome"] == "command_expired"
    assert rig.transport.sent == []
    # The refusal itself is deduplicated: a retry answers identically.
    assert rig.processor.process(env) == out


def test_out_of_order_expected_sequence_refuses_without_typing(rig, tmux) -> None:
    _arm(tmux)
    target = _issued(rig)
    out = rig.processor.process(_envelope(rig, target, seq=3))
    assert out["state"] == "refused"
    assert out["outcome"] == "sequence_conflict"
    assert "3" in out["error"] and "1" in out["error"]
    assert rig.transport.sent == []
    # The slot was not consumed: the corrected command delivers at seq 1.
    ok = rig.processor.process(_envelope(rig, target, seq=1))
    assert ok["outcome"] == "delivered"
    assert ok["applied_sequence"] == 1
    assert rig.ledger.next_sequence(target["target_id"]) == 2


def test_recycled_pane_generation_refuses_revokes_and_types_nothing(
    rig, tmux
) -> None:
    _arm(tmux)
    target = _issued(rig)
    env = _envelope(rig, target)
    # The pane is recycled under the same mutable address.
    del tmux.panes["%5"]
    tmux.panes["%9"] = "the impostor"
    tmux.refs["hs:0.0"] = "%9"

    out = rig.processor.process(env)
    assert out["state"] == "refused"
    assert out["outcome"] == "generation_mismatch"
    assert out["revoked"] is True
    assert active_grants() == {}  # the crown case: the grant died with the pane
    assert rig.transport.sent == []


def test_target_gone_refuses_typed(rig, tmux) -> None:
    _arm(tmux)
    target = _issued(rig, ref="pane:%5")
    del tmux.panes["%5"]
    out = rig.processor.process(_envelope(rig, target))
    assert out["state"] == "refused"
    assert out["outcome"] == "target_gone"
    assert rig.transport.sent == []


def test_policy_version_mismatch_refuses(rig, tmux) -> None:
    target = _issued(rig)
    authority = _authority()
    authority["policy_version"] = "operation-policy/v999"
    out = rig.processor.process(_envelope(rig, target, authority=authority))
    assert out["state"] == "refused"
    assert out["outcome"] == "policy_version_mismatch"


def test_unarmed_key_sequence_and_unknown_key_refuse_through_chokepoint(
    rig, tmux
) -> None:
    _arm(tmux)
    target = _issued(rig)
    bad = _envelope(
        rig,
        target,
        verb="terminal.keys",
        payload={"keys": ["rm -rf /"], "session_key": KEY},
    )
    out = rig.processor.process(bad)
    assert out["state"] == "refused"
    assert out["outcome"] == "unknown_key"
    assert rig.keys_transport.sent == []

    ok = rig.processor.process(
        _envelope(
            rig,
            target,
            verb="terminal.keys",
            payload={"keys": ["C-c", "Enter"], "session_key": KEY},
        )
    )
    assert ok["outcome"] == "delivered"
    assert rig.keys_transport.sent[0]["keys"] == [("named", "C-c"), ("named", "Enter")]


def test_disarm_is_never_blocked_by_a_recycled_pane(rig, tmux) -> None:
    _arm(tmux)
    target = _issued(rig)
    del tmux.panes["%5"]
    tmux.panes["%9"] = "impostor"
    tmux.refs["hs:0.0"] = "%9"
    out = rig.processor.process(
        _envelope(
            rig,
            target,
            verb="terminal.disarm",
            payload={"session_key": KEY},
            authority=_authority(decision="allowed_audited_act", grant=None),
        )
    )
    assert out["state"] == "succeeded"
    assert out["outcome"] == "disarmed"
    assert active_grants() == {}


def test_factory_kill_rides_the_grant_gate_and_ends_the_pane(rig, tmux) -> None:
    _arm(tmux)
    target = _issued(rig)
    out = rig.processor.process(
        _envelope(
            rig,
            target,
            verb="factory.kill",
            payload={"session_key": KEY, "scope": "pane"},
            authority=_authority(decision="grant_gate"),
        )
    )
    assert out["state"] == "succeeded"
    assert out["outcome"] == "killed"
    assert "%5" not in tmux.panes
    assert active_grants() == {}  # kill disarms its own grant


# ── the posture matrix, ONE policy decision ──────────────────────────


@pytest.mark.parametrize("mode", ["safe", "neutral"])
def test_secure_and_normal_require_the_grant(rig, tmux, mode, monkeypatch) -> None:
    rig.modes["mode"] = mode
    target = _issued(rig)
    resolutions: list[str] = []
    real = commands_mod.resolve_policy

    def counting(op, **kw):
        resolutions.append(op.operation_id)
        return real(op, **kw)

    monkeypatch.setattr(commands_mod, "resolve_policy", counting)
    request = {
        "target_id": target["target_id"],
        "target_generation": target["target_generation"],
        "operation": {"family": "coder_steering", "verb": "terminal.text"},
        "payload": {"text": "go", "session_key": KEY, "submit": False},
    }

    refused = rig.service.submit(request)
    assert refused["receipt"]["state"] == "refused"
    assert refused["receipt"]["outcome"] == "unarmed"
    assert rig.transport.sent == []
    assert len(resolutions) == 1  # ONE decision consumed end to end

    _arm(tmux, mode=mode)
    allowed = rig.service.submit(request)
    assert allowed["receipt"]["outcome"] == "delivered"
    assert allowed["receipt"]["authority_basis"] == "scoped_grant"
    assert len(rig.transport.sent) == 1
    assert len(resolutions) == 2


def test_yolo_registered_target_is_promptless(rig, tmux) -> None:
    rig.modes["mode"] = "yolo"
    target = _issued(rig)
    assert active_grants() == {}  # NO grant exists, nothing to prompt for
    out = rig.service.submit(
        {
            "target_id": target["target_id"],
            "target_generation": target["target_generation"],
            "operation": {"family": "coder_steering", "verb": "terminal.text"},
            "payload": {"text": "full speed", "session_key": KEY, "submit": False},
        }
    )
    assert out["receipt"]["state"] == "succeeded"
    assert out["receipt"]["outcome"] == "delivered"
    assert out["receipt"]["authority_basis"] == "control_posture"
    assert rig.transport.sent[0]["pane"] == "%5"


def test_client_supplied_authority_refuses_by_name(rig) -> None:
    target = _issued(rig)
    with pytest.raises(CommandRefused) as exc:
        rig.service.submit(
            {
                "target_id": target["target_id"],
                "target_generation": target["target_generation"],
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {"text": "x", "session_key": KEY},
                "authority": {"decision": "allowed_by_active_grant", "actor": "root"},
            }
        )
    assert exc.value.reason == "authority_not_client_settable"


def test_mutable_pane_selector_cannot_address_a_command(rig) -> None:
    with pytest.raises(CommandRefused) as exc:
        rig.service.submit(
            {
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {"text": "x", "session_key": KEY},
            }
        )
    assert exc.value.reason == "target_incomplete"


# ── reconciliation by command_id ─────────────────────────────────────


def test_lost_response_reconciles_to_the_same_receipt(rig, tmux) -> None:
    _arm(tmux)
    target = _issued(rig)
    command_id = "6f0e6c2e-6b7a-4f6e-9a3d-2c1b0a998877"
    request = {
        "command_id": command_id,
        "target_id": target["target_id"],
        "target_generation": target["target_generation"],
        "operation": {"family": "coder_steering", "verb": "terminal.text"},
        "payload": {"text": "did this land?", "session_key": KEY, "submit": False},
        "expected_sequence": 1,
    }
    first = rig.service.submit(request)
    assert first["receipt"]["outcome"] == "delivered"

    # The response was lost: the client retries the SAME command_id.
    retry = rig.service.submit(request)
    assert retry["duplicate"] is True
    assert retry["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]
    assert rig.processor.executions == 1
    assert len(rig.transport.sent) == 1

    # And the aggregate Receipt joins both halves.
    joined = rig.service.receipt(command_id)
    assert joined["hub_state"] == "complete"
    assert joined["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]
    assert joined["payload_head"] == "did this land?"


def test_remote_claim_lost_receipt_and_node_reset_is_indeterminate(rig) -> None:
    request = {
        "node_id": "node_remote42",
        "target_id": "term_remote",
        "target_generation": "gen_remote",
        "operation": {"family": "coder_steering", "verb": "terminal.text"},
        "payload": {"text": "remote steer", "session_key": KEY},
        "expected_sequence": 1,
    }
    sent = rig.service.submit(request)
    assert sent["state"] == "sent"
    cid = sent["command_id"]
    assert rig.service.repo.get(cid)["hub_state"] == "sent"

    claimed = rig.service.claim_for_node("node_remote42")
    assert [c["command_id"] for c in claimed] == [cid]
    assert rig.service.repo.get(cid)["hub_state"] == "claimed"
    # §8.1 privacy: the hub half retains hash + head, never the payload.
    row = rig.service.repo.get(cid)
    assert row["payload_head"] == "remote steer"
    assert "payload" not in row

    # The node never answers: asking for the Receipt records unknown and
    # queues a reconcile probe (inspect/reconcile — never a blind retry).
    pending = rig.service.receipt(cid)
    assert pending["hub_state"] == "unknown"
    probes = rig.service.claim_for_node("node_remote42")
    assert probes == [{"kind": "reconcile", "command_id": cid}]

    # The node comes back with a FRESH ledger (unclean reset).
    answer = {
        "command_id": cid,
        "reconcile": "unknown_command",
        "ledger_epoch": "epoch_after_the_fire",
    }
    ack = rig.service.record_results("node_remote42", [answer])
    assert ack == {"ok": True, "processed": 1}
    assert rig.service.repo.get(cid)["hub_state"] == "indeterminate_after_node_reset"


def test_hub_restart_before_claim_is_honestly_not_executed(rig, tmp_path) -> None:
    sent = rig.service.submit(
        {
            "node_id": "node_remote42",
            "target_id": "term_remote",
            "target_generation": "gen_remote",
            "operation": {"family": "coder_steering", "verb": "terminal.text"},
            "payload": {"text": "queued forever", "session_key": KEY},
            "expected_sequence": 1,
        }
    )
    # A new service over the SAME hub DB: the memory queue died with the hub.
    reborn = HubCommandService(
        repo=rig.db.delivery_receipts,
        processor=rig.processor,
        local_node_id="local",
        mode_loader=lambda: "neutral",
    )
    out = reborn.receipt(sent["command_id"])
    assert out["hub_state"] == "not_executed"


def test_remote_receipt_joins_by_command_id(rig) -> None:
    sent = rig.service.submit(
        {
            "node_id": "node_remote42",
            "target_id": "term_remote",
            "target_generation": "gen_remote",
            "operation": {"family": "coder_steering", "verb": "terminal.text"},
            "payload": {"text": "landed remotely", "session_key": KEY},
            "expected_sequence": 1,
        }
    )
    cid = sent["command_id"]
    (env,) = rig.service.claim_for_node("node_remote42")
    receipt = {
        "receipt_schema": 1,
        "receipt_id": "receipt_remote1",
        "command_id": cid,
        "node_id": "node_remote42",
        "target_id": "term_remote",
        "target_generation": "gen_remote",
        "state": "succeeded",
        "outcome": "delivered",
        "applied_sequence": 1,
        "payload_sha256": env["payload_sha256"],
        "payload_head": env["payload_head"],
    }
    rig.service.record_results("node_remote42", [receipt])
    joined = rig.service.receipt(cid)
    assert joined["hub_state"] == "complete"
    assert joined["receipt"]["receipt_id"] == "receipt_remote1"
    # Idempotent: the same result posting again changes nothing.
    rig.service.record_results("node_remote42", [receipt])
    assert rig.service.receipt(cid)["receipt"]["receipt_id"] == "receipt_remote1"
