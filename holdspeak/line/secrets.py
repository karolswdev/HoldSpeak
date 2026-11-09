"""The Line's two secrets, in the hub's keystore (never a plain file of ours).

- ``calls.line.sip_password``: the SIP registration password of the line
  (a Telnyx credential connection's password). baresip's ``accounts`` file
  needs it; the hub sends it to the Line node in the ``hello`` answer and the
  node writes it only into that 0600 file.
- ``calls.line.telnyx_api_key``: the Telnyx provisioning key. Only the
  Telnyx setup flow (LINE-3b) reads it; a Telnyx API key is not a SIP password.

The keystore is the one keystore (``holdspeak/keystore.py``), or the rig's
``HOLDSPEAK_CHANNEL_KEYSTORE_FILE``.

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
#: Where each slot's value arrives in a settings patch (the Calls face writes it
#: there; the settings service moves it to the keystore). The one list of the
#: Line's credential fields: the settings write, its refusal of a non-owner and
#: the pipeline observer all read it.
SETTINGS_FIELDS = {
    SIP_PASSWORD: ("calls", "line", "account", "password"),
    TELNYX_API_KEY: ("calls", "line", "telnyx_api_key"),
}
#: The dev fallback for each slot.
ENV = {SIP_PASSWORD: "HOLDSPEAK_LINE_SIP_PASSWORD", TELNYX_API_KEY: "TELNYX_API_KEY"}

_warned: set[str] = set()
_lock = threading.Lock()


class _Missing(Exception):
    pass


def _store() -> Any:
    """The one keystore's Line slots (``holdspeak/keystore.py``), or None when it is not open."""
    from .. import keystore

    slots = keystore.Slots(SERVICE, _Missing, missing="missing", locked="locked", unavailable="unavailable")
    return slots if slots.available() else None


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
