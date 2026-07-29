from __future__ import annotations

import pytest

import holdspeak.db.core as db_core
from holdspeak.cadence_telegram import call_telegram
from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.kernel import runtime as kernel_runtime
from holdspeak.kernel.external_egress import (
    EGRESS_EXECUTIONS,
    EgressOperationRefused,
    LOCAL_OWNER,
    run_external_egress,
)
from holdspeak.setup_status import _trust_block


@pytest.fixture
def egress_runtime(tmp_path, monkeypatch):
    db = Database(tmp_path / "egress-kernel.db")
    monkeypatch.setattr(db_core, "_db", db)
    EGRESS_EXECUTIONS._plans.clear()
    EGRESS_EXECUTIONS._operation_ids.clear()
    EGRESS_EXECUTIONS._results.clear()
    return db, kernel_runtime._configure(db)


def _latest_full(broker):
    result = list(EGRESS_EXECUTIONS._results.values())[-1]
    return broker.read(
        [f"operation:{result['operation_id']}"], "full", "committed", LOCAL_OWNER
    )["objects"][0]


def test_destination_and_data_classes_are_receipted_and_feed_one_badge(egress_runtime) -> None:
    db, broker = egress_runtime
    sent: list[bytes] = []
    result = run_external_egress(
        connector_id="cadence-telegram",
        destination="telegram:sendmessage:chat-42",
        data_classes=("cadence_message",),
        payload_material={"chat_id": "chat-42", "text": "digest only"},
        sender=lambda body: sent.append(body) or {"ok": True},
        args=(b"on-wire",),
        allowed_destinations=("telegram:sendmessage:chat-42",),
        broker=broker,
    )

    full = _latest_full(broker)
    assert result == {"ok": True}
    assert sent == [b"on-wire"]
    assert full["receipt"]["outcome"] == "succeeded"
    assert full["native_receipts"] == [
        {
            "receipt_ref": full["receipt"]["result_ref"],
            "native_id": full["canonical"]["native_id"],
            "destination": "telegram:sendmessage:chat-42",
            "data_classes": ["cadence_message"],
            "outcome": "succeeded",
        }
    ]
    trust = _trust_block(Config(), database=db)
    assert trust["last_egress"] == {
        "id": "kernel_external_egress",
        "name": "telegram:sendmessage:chat-42",
        "receipt": full["receipt"]["receipt_id"],
    }


def test_telegram_send_receipt_names_method_and_chat(egress_runtime, monkeypatch) -> None:
    _, broker = egress_runtime

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"ok":true}'

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: Response())
    assert call_telegram("secret-token", "sendMessage", {"chat_id": "42", "text": "hi"}) == {"ok": True}
    full = _latest_full(broker)
    assert full["native_receipts"][0]["destination"] == "telegram:sendmessage:42"
    assert "secret-token" not in str(full)


def test_destination_refusal_has_terminal_receipt_and_never_calls_sender(egress_runtime) -> None:
    _, broker = egress_runtime
    called = False

    def sender():
        nonlocal called
        called = True

    with pytest.raises(EgressOperationRefused) as caught:
        run_external_egress(
            connector_id="proof-webhook",
            destination="evil.example:443",
            data_classes=("connector_request",),
            payload_material={"digest": "only"},
            sender=sender,
            allowed_destinations=("allowed.example:443",),
            broker=broker,
        )

    assert called is False
    assert caught.value.reason == "external_egress_destination_not_allowed:evil.example:443"
    assert caught.value.receipt["state"] == "refused"
    assert caught.value.receipt["outcome"] == caught.value.reason
