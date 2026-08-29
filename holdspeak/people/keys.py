"""Key custody boundary for the encrypted People sidecar.

The memory implementation is intentionally injectable for tests only.  Runtime
code must use :class:`NativeKeyStore`, which refuses every fallback backend.
:class:`FileKeyStore` is the deliberate dev-only bypass (HS-149-01).
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import threading
import uuid
from pathlib import Path
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


class FileKeyStore:
    """Dev-only file-backed key store (HS-149-01, L3 seam).

    Activated ONLY when ``HOLDSPEAK_PEOPLE_KEYSTORE_FILE`` is set.  The env
    value IS the key file path.  Create-on-first-use with 0600 permissions.
    Same ``key_id`` contract as :class:`NativeKeyStore`; never used in
    production (the composition point in ``production_people_store`` honours
    the env; unset means byte-identical production behaviour).

    The file format is a JSON object ``{key_id: base64-encoded-key}``.
    """

    _lock = threading.Lock()

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def get(self, key_id: str) -> bytes:
        data = self._load()
        encoded = data.get(key_id)
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
        with self._lock:
            data = self._load()
            data[key_id] = base64.b64encode(key).decode("ascii")
            self._save(data)

    def delete(self, key_id: str) -> None:
        with self._lock:
            data = self._load()
            data.pop(key_id, None)
            self._save(data)

    def _load(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text(encoding="utf-8")
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                raise PeopleKeyError("people_key_invalid")
            return {str(k): str(v) for k, v in obj.items()}
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise PeopleKeyError("people_key_store_locked") from exc

    def _save(self, data: dict[str, str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        try:
            fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                os.write(fd, json.dumps(data).encode("utf-8"))
            finally:
                os.close(fd)
            tmp.replace(self._path)
        except OSError as exc:
            raise PeopleKeyError("people_key_store_locked") from exc


def new_key_id() -> str:
    return f"people-key-v1:{uuid.uuid4()}"


def new_key() -> bytes:
    return secrets.token_bytes(KEY_BYTES)
