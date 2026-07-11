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
