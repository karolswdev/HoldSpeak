from __future__ import annotations

import hashlib

import pytest

from holdspeak.db import Database


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def test_claim_is_durable_and_terminal_receipt_cannot_be_overwritten(tmp_path) -> None:
    database = Database(tmp_path / "delivery.db")
    repo = database.dictation_deliveries

    first = repo.claim("device:1", request_hash=_hash("one"))
    concurrent = repo.claim("device:1", request_hash=_hash("one"))
    assert first["claim_state"] == "claimed"
    assert concurrent["claim_state"] == "pending"

    completed = repo.complete(
        "device:1",
        response_status=200,
        response={"success": True, "delivered": True, "final_text": "one"},
    )
    cached = repo.claim("device:1", request_hash=_hash("one"))
    assert completed["status"] == "succeeded"
    assert cached["claim_state"] == "succeeded"
    assert cached["response"]["delivered"] is True

    # A late second finisher observes the first Receipt; it cannot rewrite it.
    late = repo.fail(
        "device:1",
        response_status=502,
        response={"error": "late"},
        error="late",
    )
    assert late["status"] == "succeeded"
    assert late["response"]["delivered"] is True


def test_claim_refuses_same_identity_for_different_content(tmp_path) -> None:
    repo = Database(tmp_path / "delivery.db").dictation_deliveries
    repo.claim("device:1", request_hash=_hash("one"))

    with pytest.raises(ValueError, match="different request"):
        repo.claim("device:1", request_hash=_hash("two"))


def test_failed_terminal_receipt_is_durable_and_cannot_be_upgraded(tmp_path) -> None:
    """HS-93-05: a failed Receipt replays as failed. A late success claim
    cannot rewrite history into a delivery that never happened."""
    repo = Database(tmp_path / "delivery.db").dictation_deliveries
    repo.claim("device:2", request_hash=_hash("one"))
    repo.fail(
        "device:2",
        response_status=500,
        response={"error": "rewrite backend unavailable", "delivered": False},
        error="rewrite backend unavailable",
    )

    cached = repo.claim("device:2", request_hash=_hash("one"))
    assert cached["claim_state"] == "failed"
    assert cached["response_status"] == 500
    assert cached["response"]["delivered"] is False

    late = repo.complete(
        "device:2",
        response_status=200,
        response={"success": True, "delivered": True},
    )
    assert late["status"] == "failed"
    assert late["response"]["delivered"] is False


def test_terminal_receipt_still_refuses_a_changed_payload(tmp_path) -> None:
    """The payload binding outlives the pending window: even after a terminal
    Receipt, the same id never accepts different content."""
    repo = Database(tmp_path / "delivery.db").dictation_deliveries
    repo.claim("device:3", request_hash=_hash("one"))
    repo.complete(
        "device:3",
        response_status=200,
        response={"success": True, "delivered": True},
    )

    with pytest.raises(ValueError, match="different request"):
        repo.claim("device:3", request_hash=_hash("two"))


def test_finishing_an_unclaimed_id_is_refused(tmp_path) -> None:
    """A Receipt may only land on a claimed identity; there is no blind write."""
    repo = Database(tmp_path / "delivery.db").dictation_deliveries
    with pytest.raises(KeyError):
        repo.complete(
            "device:ghost",
            response_status=200,
            response={"success": True},
        )
