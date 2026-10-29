"""Enrolment: a Line node on another machine gets its own credential (LINE-3).

The owner presses "Install the Line on <machine>" in Settings ▸ Calls ▸ Line.
The hub mints a one-time code (10 minutes, once). On that machine,
``holdspeak line enrol --hub <url> --code <code>`` redeems it: the hub pairs
the node in its node token store (the same custody as every node,
``holdspeak/delivery/node_link.py``; never a second store) with the scope
``calls.line``, so the credential reaches the Line's three wire routes and
nothing else. Revoke it from Settings (``DELETE /api/calls/line/nodes/<name>``).

The store key is ``line:<name>``, so a Line node never replaces a delivery or
mesh node of the same machine name.
"""
from __future__ import annotations

import re
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

SCOPE = "calls.line"
PREFIX = "line:"
#: A code lives this long, and works once.
CODE_SECONDS = 600.0
#: No 0/O, 1/I/L: a code is read off one screen and typed on another.
_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")


class EnrolError(ValueError):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def store_key(node: str) -> str:
    return PREFIX + node


def node_of(store_name: str) -> str:
    """The Line node's name from its store key (``""``: not a Line pairing)."""
    return store_name[len(PREFIX):] if str(store_name or "").startswith(PREFIX) else ""


def clean_name(node: str) -> str:
    name = str(node or "").strip().lower()
    if not _NAME.match(name) or name == "this-mac":
        raise EnrolError("bad_name", "A machine name is 1 to 32 letters, digits or dashes (not this-mac).")
    return name


@dataclass
class _Code:
    node: str
    expires: float


class EnrolCodes:
    """The hub's open codes, in memory: a restart of the hub ends them."""

    def __init__(self, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._codes: dict[str, _Code] = {}
        self._lock = threading.Lock()
        self._clock = clock

    def mint(self, node: str) -> dict[str, Any]:
        name = clean_name(node)
        raw = "".join(secrets.choice(_ALPHABET) for _ in range(8))
        code = f"{raw[:4]}-{raw[4:]}"
        with self._lock:
            now = self._clock()
            self._codes = {c: v for c, v in self._codes.items() if v.expires > now and v.node != name}
            self._codes[code] = _Code(name, now + CODE_SECONDS)
        return {"node": name, "code": code, "expires_in": int(CODE_SECONDS)}

    def take(self, code: str) -> str:
        """The node the code was minted for; the code is gone after this."""
        key = str(code or "").strip().upper().replace(" ", "")
        if len(key) == 8:
            key = f"{key[:4]}-{key[4:]}"
        with self._lock:
            found = self._codes.pop(key, None)
            now = self._clock()
        if found is None:
            raise EnrolError("code_unknown", "This code is not known. Make a new one in Settings ▸ Calls ▸ Line.")
        if found.expires <= now:
            raise EnrolError("code_expired", "This code is more than 10 minutes old. Make a new one.")
        return found.node


def redeem(codes: EnrolCodes, store: Any, code: str) -> dict[str, Any]:
    """Pair the node the code names: ``{node, token}``. A node enrolled before
    is enrolled again (its old credential is revoked first)."""
    node = codes.take(code)
    key = store_key(node)
    active = store.pairing(key)
    if active is not None:
        store.revoke(key)
    _node_id, token, _snapshot = store.pair(key, scope=SCOPE)
    return {"node": node, "token": token}


def enrolled(store: Any) -> list[dict[str, Any]]:
    """The Line nodes in the store, names and dates only (never a token)."""
    rows = []
    for row in store.status_rows() if store is not None else []:
        node = node_of(row.get("name", ""))
        if node and row.get("scope") == SCOPE and not row.get("revoked"):
            rows.append({"node": node, "enrolled_at": row.get("created_at", "")})
    return rows


def revoke(store: Any, node: str) -> bool:
    key = store_key(clean_name(node))
    if store.pairing(key) is None:
        return False
    store.revoke(key)
    return True


def wire_node(credential: Any, body_node: str) -> Optional[str]:
    """The node a wire request speaks for. A line credential speaks only for
    its own node (the body's name must match or be empty); the owner (a local
    node on the hub token) names it in the body. ``None``: refused."""
    if credential is not None and getattr(credential, "scope", "") == SCOPE:
        own = node_of(credential.name)
        if not own or (body_node and body_node != own):
            return None
        return own
    return body_node


#: The hub's one set of open codes.
CODES = EnrolCodes()

__all__ = [
    "CODES", "CODE_SECONDS", "EnrolCodes", "EnrolError", "PREFIX", "SCOPE", "clean_name", "enrolled", "node_of",
    "redeem", "revoke", "store_key", "wire_node",
]
