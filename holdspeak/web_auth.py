"""Web-runtime authentication (HS-25-02).

HoldSpeak's web runtime has always relied on binding ``127.0.0.1`` as its only
safeguard. That is fine while the runtime stays on the local machine, but Phase
15 (cross-network reach) deliberately removes that assumption. This module adds
the token primitive that gates the runtime the moment it binds a non-loopback
host.

Policy (per HS-25-02 decision): **enforced only off-loopback**.
- Loopback binds stay fully open — zero local friction, exactly as today.
- A non-loopback bind requires a token, both to bind at all (``nonloopback_bind_blocked``)
  and on every request (``verify_web_token`` in the runtime's auth middleware).

Mirrors the device-PSK pattern in :mod:`holdspeak.device_audio`
(``hmac.compare_digest``, lazy ``ensure_*`` generation).
"""

from __future__ import annotations

import hmac
import ipaddress
import secrets
import base64
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .config import Config

# Hostnames (not IPs) that mean "this machine only".
_LOOPBACK_HOSTNAMES = {"localhost", ""}
_WEBSOCKET_AUTH_PREFIX = "holdspeak.auth.v1."
WEBSOCKET_PROTOCOL = "holdspeak.v1"


def generate_web_token() -> str:
    """Return a fresh URL-safe token (~32 chars, 192 bits of entropy)."""
    return secrets.token_urlsafe(24)


def verify_web_token(provided: Optional[str], expected: Optional[str]) -> bool:
    """Constant-time token comparison.

    Returns ``False`` (without calling ``hmac.compare_digest``) when either side
    is empty, so an instance with no token configured cannot be authenticated by
    sending an empty token.
    """
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def is_loopback_host(host: Optional[str]) -> bool:
    """True when binding ``host`` keeps the runtime on the local machine only."""
    value = (host or "").strip().lower()
    if value in _LOOPBACK_HOSTNAMES:
        return True
    # IPv6 literals may arrive bracketed (e.g. "[::1]").
    value = value.strip("[]")
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        # A non-IP hostname that isn't 'localhost' can't be proven local —
        # fail safe and treat it as non-loopback.
        return False


def ensure_web_token(config: "Config", *, save_path: Optional[Path] = None) -> str:
    """Return the web auth token, generating + persisting it on first use.

    Mirrors :func:`holdspeak.device_audio.ensure_device_psk`: mutates
    ``config.meeting.web_auth_token`` and saves the config when it was empty; a
    non-empty token is returned unchanged without touching disk.
    """
    if config.meeting.web_auth_token:
        return config.meeting.web_auth_token
    config.meeting.web_auth_token = generate_web_token()
    config.save(save_path)
    return config.meeting.web_auth_token


def nonloopback_bind_blocked(
    host: Optional[str], token: Optional[str]
) -> tuple[bool, Optional[str]]:
    """Return ``(blocked, reason)`` for a requested bind.

    A non-loopback bind without a configured token is refused — it would expose
    an unauthenticated runtime. Loopback binds are always allowed.
    """
    if is_loopback_host(host):
        return False, None
    if not token:
        return (
            True,
            f"Refusing to bind non-loopback host {host!r} without an auth token. "
            "Set meeting.web_auth_token, or bind 127.0.0.1 for local-only use.",
        )
    return False, None


def extract_request_token(
    *,
    authorization: Optional[str] = None,
    header_token: Optional[str] = None,
    query_token: Optional[str] = None,
) -> Optional[str]:
    """Pull a token from request inputs, in priority order.

    Accepts ``X-HoldSpeak-Token``, ``Authorization: Bearer <token>``, or a
    ``?token=`` query parameter (the last makes plain browser navigation work
    over a tunnel, Jupyter-style).
    """
    if header_token and header_token.strip():
        return header_token.strip()
    if authorization:
        prefix = "bearer "
        if authorization.lower().startswith(prefix):
            candidate = authorization[len(prefix):].strip()
            if candidate:
                return candidate
    if query_token and query_token.strip():
        return query_token.strip()
    return None


def websocket_auth_protocol(token: str) -> str:
    """Encode a bearer token as a WebSocket subprotocol offer.

    Browsers cannot add an Authorization header to a WebSocket handshake.
    Subprotocols are sent in a header rather than the URL, keeping credentials
    out of request targets, browser history, and ordinary access logs.
    """

    clean = str(token or "").strip()
    if not clean:
        raise ValueError("websocket auth token is required")
    encoded = base64.urlsafe_b64encode(clean.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{_WEBSOCKET_AUTH_PREFIX}{encoded}"


def extract_websocket_token(protocol_header: Optional[str]) -> Optional[str]:
    """Extract the credential from ``Sec-WebSocket-Protocol`` offers."""

    for offered in str(protocol_header or "").split(","):
        protocol = offered.strip()
        if protocol.startswith(_WEBSOCKET_AUTH_PREFIX):
            candidate = protocol[len(_WEBSOCKET_AUTH_PREFIX) :].strip()
            if not candidate:
                return None
            try:
                padding = "=" * (-len(candidate) % 4)
                return base64.b64decode(
                    candidate + padding, altchars=b"-_", validate=True
                ).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                return None
    return None
