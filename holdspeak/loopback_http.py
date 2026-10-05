"""The one rule for an engine on THIS machine (Article III: a LOCAL lamp means
no byte leaves the machine).

* **Loopback** is an IP literal in 127.0.0.0/8 or ``::1``, or the literal word
  ``localhost``.  Nothing else: ``localhost.localdomain``, ``*.localhost`` or
  any other name can resolve anywhere, so it is never loopback.
* **The word ``localhost`` is never resolved.**  ``pin_loopback_url`` rewrites
  it to ``127.0.0.1`` before any connect, so the address the lamp names is the
  address the bytes go to.
* **A request to a loopback engine** ignores HTTP proxy settings and follows
  no redirect (a redirect is not an engine): ``loopback_get`` for urllib
  callers, ``loopback_httpx_client`` for the OpenAI client.

This module imports nothing from the rest of HoldSpeak at import time;
``endpoint_lamp`` reads the one egress classifier (``intel.providers``).
"""
from __future__ import annotations

import ipaddress
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

LOOPBACK_WORD = "localhost"
PINNED_LOOPBACK = "127.0.0.1"



class NotLoopbackError(ValueError):
    """A loopback-only request was asked to reach another address."""


def _host(value: str) -> str:
    return str(value or "").strip().strip("[]").lower()


def is_loopback_engine_host(host: str) -> bool:
    """True only for a loopback IP literal or the exact word ``localhost``."""
    text = _host(host)
    if text == LOOPBACK_WORD:
        return True
    try:
        return ipaddress.ip_address(text).is_loopback
    except ValueError:
        return False


def is_loopback_url(url: str) -> bool:
    return is_loopback_engine_host(urlparse(str(url or "")).hostname or "")


def pin_loopback_url(url: str) -> str:
    """``localhost`` → ``127.0.0.1`` (port, path and query kept); else unchanged."""
    parsed = urlparse(str(url or ""))
    if _host(parsed.hostname or "") != LOOPBACK_WORD:
        return str(url or "")
    netloc = PINNED_LOOPBACK + (f":{parsed.port}" if parsed.port else "")
    return urlunparse(parsed._replace(netloc=netloc))


def endpoint_lamp(url: str) -> str:
    """The lamp for an endpoint URL: local, private_network or cloud.

    The ONE classifier decides: ``intel.providers.egress_boundary`` (HS-130-04,
    hardened by #855: LOCAL only where the transport pins loopback).  A URL
    with no host is ``cloud``.  Every surface gets one verdict (Astra, #875).
    """
    from .intel.providers import egress_boundary

    return egress_boundary(cloud=True, base_url=str(url or ""))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise HTTPError(req.full_url, code, "redirect refused: not an engine", headers, fp)


_LOOPBACK_OPENER = build_opener(ProxyHandler({}), _NoRedirect())


def loopback_get(url: str, *, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
    """GET one loopback URL: pinned literal, no proxy, no redirect."""
    if not is_loopback_url(url):
        raise NotLoopbackError(f"not a loopback address: {url!r}")
    request = Request(pin_loopback_url(url), headers=headers, method="GET")
    with _LOOPBACK_OPENER.open(request, timeout=timeout) as response:  # noqa: S310 - loopback only
        return int(getattr(response, "status", 200) or 200), response.read()


def loopback_httpx_client(timeout: Any = None) -> Any:
    """An httpx client for a loopback engine: no proxy, no redirect."""
    import httpx

    kwargs: dict[str, Any] = {"trust_env": False, "follow_redirects": False}
    if timeout is not None:
        kwargs["timeout"] = timeout
    return httpx.Client(**kwargs)


__all__ = [
    "NotLoopbackError",
    "PINNED_LOOPBACK",
    "endpoint_lamp",
    "is_loopback_engine_host",
    "is_loopback_url",
    "loopback_get",
    "loopback_httpx_client",
    "pin_loopback_url",
]
