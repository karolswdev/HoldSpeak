"""AES-GCM envelopes for People records.

Only canonical JSON reaches this module.  The associated data binds an envelope
to its immutable record identity, kind, and key id, preventing row swapping.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


FORMAT_VERSION = 1
KEY_BYTES = 32
NONCE_BYTES = 12


class PeopleCryptoError(ValueError):
    """A content-free encryption or authentication failure."""


@dataclass(frozen=True)
class Envelope:
    """The only payload representation persisted by the People sidecar."""

    key_id: str
    nonce: bytes
    ciphertext: bytes
    format_version: int = FORMAT_VERSION


def canonical_json(value: Any) -> bytes:
    """Encode a value deterministically without accepting non-JSON structures."""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PeopleCryptoError("people_payload_invalid") from exc


def associated_data(record_id: str, kind: str, key_id: str) -> bytes:
    """Stable, unambiguous AAD for one People record envelope."""
    if not record_id or not kind or not key_id:
        raise PeopleCryptoError("people_envelope_identity_invalid")
    return b"holdspeak.people.v1\0" + b"\0".join(
        item.encode("utf-8") for item in (record_id, kind, key_id)
    )


def _validate_key(key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) != KEY_BYTES:
        raise PeopleCryptoError("people_key_invalid")


def encrypt_payload(*, key: bytes, key_id: str, record_id: str, kind: str, payload: Any) -> Envelope:
    """Encrypt canonical JSON with a fresh 96-bit AES-GCM nonce."""
    _validate_key(key)
    nonce = secrets.token_bytes(NONCE_BYTES)
    ciphertext = AESGCM(key).encrypt(nonce, canonical_json(payload), associated_data(record_id, kind, key_id))
    return Envelope(key_id=key_id, nonce=nonce, ciphertext=ciphertext)


def decrypt_payload(*, key: bytes, record_id: str, kind: str, envelope: Envelope) -> Any:
    """Authenticate and decode one record; never return partially trusted text."""
    _validate_key(key)
    if envelope.format_version != FORMAT_VERSION or len(envelope.nonce) != NONCE_BYTES:
        raise PeopleCryptoError("people_envelope_invalid")
    try:
        plaintext = AESGCM(key).decrypt(
            envelope.nonce,
            envelope.ciphertext,
            associated_data(record_id, kind, envelope.key_id),
        )
        value = json.loads(plaintext.decode("utf-8"))
    except (InvalidTag, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PeopleCryptoError("people_envelope_authentication_failed") from exc
    return value
