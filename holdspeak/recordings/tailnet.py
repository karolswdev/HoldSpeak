"""The hub's Tailscale address, when Tailscale Serve proxies to this hub.

``tailscale serve status --json`` names each served host and its handlers;
the one whose ``/`` handler proxies to ``127.0.0.1:<hub port>`` is this hub's
tailnet address (``https://karols-macbook-pro.tailad9943.ts.net``). Read at
most once a minute, off the loop; no Tailscale, or Serve off: ``None``.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import threading
import time
from typing import Any, Callable, Optional

CACHE_SECONDS = 60.0
TAILSCALE_CANDIDATES = (
    "/opt/homebrew/bin/tailscale",
    "/usr/local/bin/tailscale",
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
)

_lock = threading.Lock()
_cache: dict[int, tuple[float, Optional[str]]] = {}


def _tailscale() -> Optional[str]:
    found = shutil.which("tailscale")
    if found:
        return found
    for candidate in TAILSCALE_CANDIDATES:
        if shutil.which(candidate):
            return candidate
    return None


def _serve_status() -> Optional[dict[str, Any]]:
    binary = _tailscale()
    if not binary:
        return None
    try:
        done = subprocess.run(
            [binary, "serve", "status", "--json"],
            capture_output=True, timeout=4, check=False, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    try:
        status = json.loads(done.stdout.decode("utf-8", "ignore") or "{}")
    except ValueError:
        return None
    return status if isinstance(status, dict) else None


def base_from_status(status: Optional[dict[str, Any]], port: int) -> Optional[str]:
    """The ``https://<host>`` whose ``/`` proxies to this hub's port."""
    if not status or not port:
        return None
    targets = {f"http://127.0.0.1:{port}", f"http://localhost:{port}", f"127.0.0.1:{port}", f"localhost:{port}"}
    for host, served in (status.get("Web") or {}).items():
        handlers = (served or {}).get("Handlers") or {}
        proxy = str((handlers.get("/") or {}).get("Proxy") or "").rstrip("/")
        if proxy in targets:
            name, _, listen = str(host).partition(":")
            return f"https://{name}" if listen in {"", "443"} else f"https://{name}:{listen}"
    return None


def tailnet_base(port: int, *, read: Callable[[], Optional[dict[str, Any]]] = _serve_status) -> Optional[str]:
    now = time.monotonic()
    with _lock:
        hit = _cache.get(port)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
    base = base_from_status(read(), port)
    with _lock:
        _cache[port] = (now, base)
    return base


def forget() -> None:
    with _lock:
        _cache.clear()


__all__ = ["base_from_status", "forget", "tailnet_base"]
