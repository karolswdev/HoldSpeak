"""Pairing a phone, its token, and the hub's own phone secret.

- A pairing token lives 10 minutes: ``POST /api/phone/pair`` writes a device
  row in state ``pairing`` whose ``jwt_kid`` is the token's hash; the QR
  carries the token and the hub's address; the app redeems it once
  (``POST /api/phone/devices``) and the row becomes ``paired``.
- The device token is a JWT, HS256, signed with the hub's phone secret, with
  the device's ``jwt_kid`` in its header. Every request reads the device row
  again: a revoked row (or a new ``jwt_kid``) refuses the token at once.
- Each device's push secret is derived from the hub secret and its kid, so it
  is never stored and changes when the device pairs again.

The hub secret is in the key store: the channel key file when
``HOLDSPEAK_CHANNEL_KEYSTORE_FILE`` is set (a rig), else the OS keychain,
else (a HOME with no keychain) a 0600 file in HoldSpeak's data folder.

The pairing shape (a short-lived token in a QR next to the hub's address,
consumed once; a device JWT checked against the device row on every request)
is agentring's (``relay/src/routes/pairing.ts``, ``relay/src/auth.ts``).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("phone.devices")

#: A pairing token's life.
PAIR_SECONDS = 600
#: The JWT's issuer and audience.
ISSUER = "holdspeak-hub"
AUDIENCE = "phone"
_SERVICE = "HoldSpeak Phone"
_SLOT = "hub-secret"

_lock = threading.Lock()
_cached: dict[str, bytes] = {}


def b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def unb64u(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def token_hash(token: str) -> str:
    return "pt-" + hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def _secret_file(slot: str = _SLOT) -> Path:
    return Path.home() / ".local" / "share" / "holdspeak" / "phone" / slot


class _FileSecret:
    def __init__(self, path: Path) -> None:
        self.path = path

    def get(self) -> Optional[str]:
        try:
            return self.path.read_text(encoding="utf-8").strip() or None
        except OSError:
            return None

    def put(self, value: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
        os.chmod(self.path, 0o600)


def _store_for(slot: str = _SLOT) -> Any:
    """One slot of the phone key store (the hub secret, his APNs key)."""
    from ..services.channel_key_file import FileChannelKeyStore, channel_keystore_path

    path = channel_keystore_path()
    if path is not None:
        class _Err(Exception):
            pass

        keys = FileChannelKeyStore(path, _SERVICE, _Err, "missing", "locked")

        class _Keys:
            def get(self) -> Optional[str]:
                try:
                    return keys.get(slot)
                except _Err:
                    return None

            def put(self, value: str) -> None:
                keys.put(slot, value)

        return _Keys()
    from ..people.keys import home_has_a_keychain

    if home_has_a_keychain():
        try:
            import keyring

            backend = keyring.get_keyring()

            class _Chain:
                def get(self) -> Optional[str]:
                    try:
                        return backend.get_password(_SERVICE, slot)
                    except Exception:
                        return None

                def put(self, value: str) -> None:
                    backend.set_password(_SERVICE, slot, value)

            return _Chain()
        except Exception as exc:  # no keychain backend: the file below
            log.info(f"phone secret: no keychain ({exc})")
    return _FileSecret(_secret_file(slot))


def hub_secret() -> bytes:
    """The hub's phone secret (made once, then read from the key store)."""
    with _lock:
        key = os.environ.get("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", "") + "|" + str(_secret_file())
        if key in _cached:
            return _cached[key]
        store = _store_for(_SLOT)
        value = store.get()
        if not value:
            value = b64u(secrets.token_bytes(32))
            store.put(value)
        secret = unb64u(value)
        _cached[key] = secret
        return secret


def forget_cached_secret() -> None:
    """Tests: the next read goes to the store again."""
    with _lock:
        _cached.clear()


def hub_id(secret: bytes) -> str:
    """A stable, public name of this hub (not the secret)."""
    return "hub_" + hashlib.sha256(b"holdspeak-phone-hub:" + secret).hexdigest()[:16]


def push_secret(secret: bytes, jwt_kid: str) -> str:
    """The device's push secret: derived, never stored."""
    return b64u(hmac.new(secret, b"push:" + str(jwt_kid).encode("utf-8"), hashlib.sha256).digest())


def qr_payload(*, token: str, hub_urls: list[str], expires_at: str, hub: str) -> str:
    """What the QR says: the token, where the hub is, until when."""
    return json.dumps({"v": 1, "hub_id": hub, "hub_urls": hub_urls, "pair_token": token,
                       "expires_at": expires_at}, separators=(",", ":"))


def issue_jwt(secret: bytes, device_id: str, jwt_kid: str, *, now: Optional[float] = None) -> str:
    header = {"alg": "HS256", "typ": "JWT", "kid": jwt_kid}
    claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": device_id, "iat": int(now if now is not None else time.time())}
    signing = b64u(json.dumps(header, separators=(",", ":")).encode()) + "." + \
        b64u(json.dumps(claims, separators=(",", ":")).encode())
    sig = hmac.new(secret, signing.encode("ascii"), hashlib.sha256).digest()
    return signing + "." + b64u(sig)


def read_jwt(secret: bytes, token: str) -> Optional[dict[str, Any]]:
    """The claims and the kid of a well-signed device token, or None."""
    parts = str(token or "").split(".")
    if len(parts) != 3:
        return None
    try:
        header = json.loads(unb64u(parts[0]))
        claims = json.loads(unb64u(parts[1]))
        sig = unb64u(parts[2])
    except (ValueError, TypeError):
        return None
    if not isinstance(header, Mapping) or not isinstance(claims, Mapping) or header.get("alg") != "HS256":
        return None
    want = hmac.new(secret, f"{parts[0]}.{parts[1]}".encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(want, sig):
        return None
    if claims.get("iss") != ISSUER or claims.get("aud") != AUDIENCE or not isinstance(claims.get("sub"), str):
        return None
    return {"sub": claims["sub"], "kid": str(header.get("kid") or ""), "iat": claims.get("iat")}


def bearer(value: Optional[str]) -> str:
    text = str(value or "").strip()
    return text[7:].strip() if text.lower().startswith("bearer ") else ""


__all__ = [
    "AUDIENCE", "ISSUER", "PAIR_SECONDS", "b64u", "bearer", "forget_cached_secret", "hub_id", "hub_secret",
    "issue_jwt", "push_secret", "qr_payload", "read_jwt", "token_hash", "unb64u",
]
