"""Key custody boundary for the encrypted People sidecar.

The memory implementation is intentionally injectable for tests only.  Runtime
code must use :class:`NativeKeyStore`, which refuses every fallback backend.
"""

from __future__ import annotations

import base64
import secrets
import uuid
from typing import Protocol

from .crypto import KEY_BYTES


class PeopleKeyError(RuntimeError):
    """Stable content-free key-custody failure."""


class KeyStore(Protocol):
    def get(self, key_id: str) -> bytes: ...
    def put(self, key_id: str, key: bytes) -> None: ...
    def delete(self, key_id: str) -> None: ...


class MemoryKeyStore:
    """Test-only ephemeral store; never construct from production wiring."""

    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def get(self, key_id: str) -> bytes:
        try:
            return self.values[key_id]
        except KeyError as exc:
            raise PeopleKeyError("people_key_missing") from exc

    def put(self, key_id: str, key: bytes) -> None:
        if len(key) != KEY_BYTES:
            raise PeopleKeyError("people_key_invalid")
        self.values[key_id] = bytes(key)

    def delete(self, key_id: str) -> None:
        self.values.pop(key_id, None)


class NativeKeyStore:
    """macOS Keychain / Linux Secret Service only; no file or env fallback."""

    service_name = "HoldSpeak People"
    _ALLOWED_BACKENDS = {
        "keyring.backends.macOS.Keyring",
        "keyring.backends.SecretService.Keyring",
    }

    def __init__(self, backend: object | None = None) -> None:
        try:
            import keyring
        except ImportError as exc:  # pragma: no cover - dependency packaging proof
            raise PeopleKeyError("people_key_store_unavailable") from exc
        self._keyring = keyring
        self._backend = backend if backend is not None else keyring.get_keyring()
        backend_name = f"{type(self._backend).__module__}.{type(self._backend).__name__}"
        if backend_name not in self._ALLOWED_BACKENDS:
            raise PeopleKeyError("people_key_store_not_native")

    def get(self, key_id: str) -> bytes:
        try:
            encoded = self._backend.get_password(self.service_name, key_id)
        except Exception as exc:
            raise PeopleKeyError("people_key_store_locked") from exc
        if not encoded:
            raise PeopleKeyError("people_key_missing")
        try:
            key = base64.b64decode(encoded.encode("ascii"), validate=True)
        except (UnicodeEncodeError, ValueError) as exc:
            raise PeopleKeyError("people_key_invalid") from exc
        if len(key) != KEY_BYTES:
            raise PeopleKeyError("people_key_invalid")
        return key

    def put(self, key_id: str, key: bytes) -> None:
        if len(key) != KEY_BYTES:
            raise PeopleKeyError("people_key_invalid")
        try:
            self._backend.set_password(
                self.service_name, key_id, base64.b64encode(key).decode("ascii")
            )
        except Exception as exc:
            raise PeopleKeyError("people_key_store_locked") from exc

    def delete(self, key_id: str) -> None:
        try:
            self._backend.delete_password(self.service_name, key_id)
        except Exception as exc:
            raise PeopleKeyError("people_key_store_locked") from exc


def new_key_id() -> str:
    return f"people-key-v1:{uuid.uuid4()}"


def new_key() -> bytes:
    return secrets.token_bytes(KEY_BYTES)
