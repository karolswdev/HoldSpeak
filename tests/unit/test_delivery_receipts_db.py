"""HS-94-06 — receipt durability, both halves.

The node ledger survives a process restart with the SAME receipts and
the SAME epoch (that stability is exactly what distinguishes "never
executed" from ``indeterminate_after_node_reset``); a rebuilt ledger
mints a NEW epoch. The hub table keeps hash/head only — the payload
never lands in the hub database — and joins the node half idempotently.
"""

from __future__ import annotations

import sqlite3

from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger

RECEIPT = {
    "receipt_schema": 1,
    "receipt_id": "receipt_abc123",
    "command_id": "11111111-2222-3333-4444-555555555555",
    "state": "succeeded",
    "outcome": "delivered",
    "applied_sequence": 1,
}

ENVELOPE = {
    "command_id": "11111111-2222-3333-4444-555555555555",
    "issued_at": "2026-07-15T12:00:00Z",
    "expires_at": "2026-07-15T12:00:30Z",
    "target": {
        "node_id": "local",
        "target_id": "term_x",
        "target_generation": "gen_x",
    },
    "operation": {"family": "coder_steering", "verb": "terminal.text"},
    "authority": {
        "actor": "owner",
        "control_posture": "neutral",
        "decision": "allowed_by_active_grant",
        "policy_version": "operation-policy/v2",
        "grant_id": "claude:hs94",
    },
    "payload_sha256": "sha256:feedface",
    "payload_head": "the first 120 chars only",
    "expected_sequence": 1,
}


def test_ledger_receipts_and_epoch_survive_reopen(tmp_path) -> None:
    path = tmp_path / "ledger.db"
    ledger = NodeReceiptLedger(path)
    epoch = ledger.epoch
    assert epoch.startswith("epoch_")
    ledger.commit(
        RECEIPT["command_id"], RECEIPT, target_id="term_x", advance_sequence=True
    )
    assert ledger.next_sequence("term_x") == 2

    reopened = NodeReceiptLedger(path)
    assert reopened.epoch == epoch  # SAME ledger, same epoch
    assert reopened.get(RECEIPT["command_id"]) == RECEIPT
    assert reopened.next_sequence("term_x") == 2
    assert reopened.next_sequence("term_other") == 1


def test_a_rebuilt_ledger_is_a_new_epoch_with_no_memory(tmp_path) -> None:
    first = NodeReceiptLedger(tmp_path / "a.db")
    first.commit(RECEIPT["command_id"], RECEIPT, target_id="term_x")
    fresh = NodeReceiptLedger(tmp_path / "b.db")  # the unclean-reset stand-in
    assert fresh.epoch != first.epoch
    assert fresh.get(RECEIPT["command_id"]) is None


def test_ledger_commit_is_first_write_wins(tmp_path) -> None:
    ledger = NodeReceiptLedger(tmp_path / "ledger.db")
    ledger.commit(RECEIPT["command_id"], RECEIPT, target_id="term_x")
    impostor = {**RECEIPT, "outcome": "rewritten-history"}
    ledger.commit(RECEIPT["command_id"], impostor, target_id="term_x")
    assert ledger.get(RECEIPT["command_id"])["outcome"] == "delivered"


def test_refusal_commit_does_not_advance_the_sequence(tmp_path) -> None:
    ledger = NodeReceiptLedger(tmp_path / "ledger.db")
    ledger.commit(
        RECEIPT["command_id"],
        {**RECEIPT, "state": "refused", "outcome": "sequence_conflict"},
        target_id="term_x",
        advance_sequence=False,
    )
    assert ledger.next_sequence("term_x") == 1


def test_hub_half_stores_head_and_hash_never_the_payload(tmp_path) -> None:
    db = Database(tmp_path / "hub.db")
    secret = "the full steer text that must never reach the hub database"
    envelope = {**ENVELOPE, "payload": {"text": secret}}
    db.delivery_receipts.record_sent(envelope, dispatch_epoch="epoch_1")

    row = db.delivery_receipts.get(ENVELOPE["command_id"])
    assert row["payload_head"] == "the first 120 chars only"
    assert row["payload_sha256"] == "sha256:feedface"
    assert row["hub_state"] == "sent"
    assert row["dispatch_epoch"] == "epoch_1"
    assert row["authority"]["decision"] == "allowed_by_active_grant"

    # Sweep every stored byte: the payload text appears NOWHERE.
    conn = sqlite3.connect(str(tmp_path / "hub.db"))
    dump = "\n".join(conn.iterdump())
    conn.close()
    assert secret not in dump


def test_hub_attach_receipt_is_idempotent_first_wins(tmp_path) -> None:
    db = Database(tmp_path / "hub.db")
    db.delivery_receipts.record_sent(ENVELOPE)
    db.delivery_receipts.attach_receipt(RECEIPT)
    row = db.delivery_receipts.get(ENVELOPE["command_id"])
    assert row["hub_state"] == "complete"
    assert row["receipt"]["receipt_id"] == "receipt_abc123"

    db.delivery_receipts.attach_receipt({**RECEIPT, "receipt_id": "receipt_late"})
    row = db.delivery_receipts.get(ENVELOPE["command_id"])
    assert row["receipt"]["receipt_id"] == "receipt_abc123"


def test_hub_pending_worklist_and_states(tmp_path) -> None:
    db = Database(tmp_path / "hub.db")
    db.delivery_receipts.record_sent(ENVELOPE)
    assert db.delivery_receipts.pending_for_node("local") == [
        ENVELOPE["command_id"]
    ]
    db.delivery_receipts.set_state(
        ENVELOPE["command_id"], "indeterminate_after_node_reset"
    )
    assert db.delivery_receipts.pending_for_node("local") == []
    assert (
        db.delivery_receipts.get(ENVELOPE["command_id"])["hub_state"]
        == "indeterminate_after_node_reset"
    )
