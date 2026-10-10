"""Web-runtime credential primitives.

``is_loopback_host`` is intentionally only a bind-safety classifier.  Request
authority is derived from credentials by :mod:`holdspeak.principals`, including
on loopback (HS-106-02).
"""

from __future__ import annotations

import hmac
import ipaddress
import secrets
import base64
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


def authenticated_browser_url(url: str, token: str) -> str:
    """Attach the owner bootstrap credential to a browser launch URL.

    The React bootstrap captures it into tab-scoped storage and immediately
    scrubs it from the address bar, so first load remains ceremony-free.
    """
    parts = urlsplit(str(url))
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["token"] = str(token)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


_WILDCARD_HOSTS = {"0.0.0.0", "::", "[::]"}


def _lan_ipv4() -> Optional[str]:
    """The primary outbound IPv4 address (no packet is sent), or None."""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.168.255.255", 1))
            ip = probe.getsockname()[0]
    except OSError:
        return None
    return None if not ip or ip.startswith("127.") or ip == "0.0.0.0" else ip


def reachable_urls(url: str, *, lan_ip: Optional[str] = None) -> list[str]:
    """The addresses a person can open for a hub served at ``url``.

    PHILO-17 wayin: a wildcard bind (``HOLDSPEAK_WEB_HOST=0.0.0.0``) serves on
    every interface, but ``http://0.0.0.0:8765`` opens on no iPad. Print
    loopback for this Mac first, then the LAN address for other devices. Any
    other host is returned as it is.
    """
    parts = urlsplit(str(url))
    host = (parts.hostname or "").strip()
    if host not in _WILDCARD_HOSTS and f"[{host}]" not in _WILDCARD_HOSTS:
        return [str(url)]
    port = f":{parts.port}" if parts.port else ""

    def at(name: str) -> str:
        return urlunsplit((parts.scheme, f"{name}{port}", parts.path, parts.query, parts.fragment))

    urls = [at("127.0.0.1")]
    ip = lan_ip if lan_ip is not None else _lan_ipv4()
    if ip:
        urls.append(at(ip))
    return urls


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
