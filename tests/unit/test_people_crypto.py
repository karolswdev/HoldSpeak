from __future__ import annotations

import pytest

from holdspeak.people.crypto import PeopleCryptoError, decrypt_payload, encrypt_payload


def test_aes_gcm_round_trips_canonical_json_and_never_reuses_a_nonce() -> None:
    key = b"k" * 32
    first = encrypt_payload(key=key, key_id="key-1", record_id="record-1", kind="request", payload={"body": "SENTINEL request", "z": 1, "a": 2})
    second = encrypt_payload(key=key, key_id="key-1", record_id="record-1", kind="request", payload={"a": 2, "z": 1, "body": "SENTINEL request"})

    assert first.nonce != second.nonce
    assert b"SENTINEL request" not in first.ciphertext
    assert decrypt_payload(key=key, record_id="record-1", kind="request", envelope=first) == {"a": 2, "body": "SENTINEL request", "z": 1}


@pytest.mark.parametrize("record_id,kind,key_id", [("other", "request", "key-1"), ("record-1", "promise", "key-1"), ("record-1", "request", "key-2")])
def test_aad_binds_record_kind_and_key_id(record_id: str, kind: str, key_id: str) -> None:
    key = b"k" * 32
    envelope = encrypt_payload(key=key, key_id="key-1", record_id="record-1", kind="request", payload={"body": "SENTINEL"})
    if key_id != envelope.key_id:
        from holdspeak.people.crypto import Envelope
        envelope = Envelope(key_id, envelope.nonce, envelope.ciphertext)
    with pytest.raises(PeopleCryptoError, match="authentication"):
        decrypt_payload(key=key, record_id=record_id, kind=kind, envelope=envelope)
