"""The Line's two secrets, in the hub's keystore (never a plain file of ours).

- ``calls.line.sip_password``: the SIP registration password of the line
  (a Telnyx credential connection's password). baresip's ``accounts`` file
  needs it; the hub sends it to the Line node in the ``hello`` answer and the
  node writes it only into that 0600 file.
- ``calls.line.telnyx_api_key``: the Telnyx provisioning key. Only the
  Telnyx setup flow (LINE-3b) reads it; a Telnyx API key is not a SIP password.

The keystore is the one the channel keys use: the macOS Keychain or the
Linux Secret Service, or the rig's ``HOLDSPEAK_CHANNEL_KEYSTORE_FILE``.

Dev only: when a slot is empty, ``TELNYX_API_KEY`` and
``HOLDSPEAK_LINE_SIP_PASSWORD`` are read from the environment, with one log
line each ("read from the environment; move it to the keystore in Settings ▸
Calls ▸ Line"). The keystore is the product path.
"""
from __future__ import annotations

import os
import threading
from typing import Any, Optional

from ..logging_config import get_logger

log = get_logger("line.secrets")

SERVICE = "HoldSpeak Line"
SIP_PASSWORD = "calls.line.sip_password"
TELNYX_API_KEY = "calls.line.telnyx_api_key"
SLOTS = (SIP_PASSWORD, TELNYX_API_KEY)
#: The dev fallback for each slot.
ENV = {SIP_PASSWORD: "HOLDSPEAK_LINE_SIP_PASSWORD", TELNYX_API_KEY: "TELNYX_API_KEY"}

_warned: set[str] = set()
_lock = threading.Lock()


class _Missing(Exception):
    pass


def _store() -> Any:
    """The keystore (the rig's key file, else the native keychain), or None."""
    from ..services.channel_key_file import FileChannelKeyStore, channel_keystore_path

    path = channel_keystore_path()
    if path is not None:
        return FileChannelKeyStore(path, SERVICE, _Missing, "missing", "locked")
    from ..people.keys import home_has_a_keychain

    if not home_has_a_keychain():
        return None
    try:
        import keyring

        backend = keyring.get_keyring()
    except Exception as exc:
        log.info(f"line secrets: no keychain ({exc})")
        return None

    class _Chain:
        def get(self, slot: str) -> str:
            value = backend.get_password(SERVICE, slot)
            if not value:
                raise _Missing("missing")
            return value

        def put(self, slot: str, value: str) -> None:
            if value:
                backend.set_password(SERVICE, slot, value)
            else:
                try:
                    backend.delete_password(SERVICE, slot)
                except Exception:
                    pass

    return _Chain()


def _from_keystore(slot: str) -> str:
    store = _store()
    if store is None:
        return ""
    try:
        return str(store.get(slot) or "")
    except Exception:
        return ""


def read(slot: str) -> str:
    """The secret: the keystore first, then (dev only) the environment."""
    if slot not in SLOTS:
        raise KeyError(slot)
    value = _from_keystore(slot)
    if value:
        return value
    value = os.environ.get(ENV[slot], "").strip()
    if value:
        with _lock:
            if slot not in _warned:
                _warned.add(slot)
                log.warning(f"{ENV[slot]} read from the environment; move it to the keystore in Settings ▸ Calls ▸ Line")
    return value


def where(slot: str) -> str:
    """``keystore``, ``environment`` or ``missing`` (never the value)."""
    if _from_keystore(slot):
        return "keystore"
    return "environment" if os.environ.get(ENV[slot], "").strip() else "missing"


def write(slot: str, value: Optional[str]) -> None:
    """Keep (or, with an empty value, forget) a secret in the keystore."""
    if slot not in SLOTS:
        raise KeyError(slot)
    store = _store()
    if store is None:
        raise RuntimeError("line_keystore_unavailable")
    store.put(slot, str(value or ""))


def presence() -> dict[str, str]:
    """Each secret's place, for Settings ▸ Calls ▸ Line."""
    return {"sip_password": where(SIP_PASSWORD), "telnyx_api_key": where(TELNYX_API_KEY)}


__all__ = ["ENV", "SIP_PASSWORD", "SLOTS", "TELNYX_API_KEY", "presence", "read", "where", "write"]
