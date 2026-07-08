"""Cross-machine steering relay (HS-89-03) — the third limit falls.

Phase 87 could only steer LOCAL tmux. This reaches another machine: the far
node runs its OWN steering routes + tmux + consent spine; the hub RELAYS a
peek/arm/steer/keys command to it over authenticated HTTP, and the node
executes against its own local tmux.

The security model is deliberate: **the machine that types owns the consent
AND the audit.** The far node checks its own grant and writes its own audit
row for the keystroke it delivers — the hub is a relay, not the authority
over someone else's terminal. Honest liveness: a node that does not answer in
time refuses BY NAME (`node_offline`), never a hang, never a fabricated
success. Only the command (text / keys) + the pane key cross the wire; the
node resolves its own panes, and no secret leaves the hub beyond the node's
own bearer token.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Optional
from urllib.parse import quote

DEFAULT_RELAY_TIMEOUT_SECONDS: float = 5.0

# (method, url, headers, body, timeout) -> {"status": int, "json": Any}.
# The default is a urllib round-trip; tests inject a fake so no real HTTP runs.
RelayOpener = Callable[..., dict]


def load_nodes(env: Optional[dict] = None) -> dict[str, dict]:
    """Configured steering nodes: ``name -> {base_url, token}``.

    Sourced from ``HOLDSPEAK_STEER_NODES`` (a JSON object). Empty when unset
    or malformed — with no node configured, every relay refuses by name.
    Explicit config, never discovery: you name the machines you can drive.
    """
    raw = str((env or os.environ).get("HOLDSPEAK_STEER_NODES", "")).strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): dict(v) for k, v in data.items() if isinstance(v, dict)}


def _default_opener(method: str, url: str, headers: dict, body: Any, timeout: float) -> dict:
    data = None
    hdrs = dict(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310 — configured node only
            status = getattr(resp, "status", None) or resp.getcode()
            text = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        # A 409 (the node's typed refusal — unarmed / pane_mismatch / …) is a
        # real answer with a body, not a transport failure.
        text = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else ""
        status = int(exc.code)
    try:
        payload = json.loads(text) if text else {}
    except ValueError:
        payload = {}
    return {"status": int(status), "json": payload}


def relay(
    node: str,
    verb: str,
    key: str,
    *,
    method: str = "POST",
    body: Any = None,
    nodes: Optional[dict] = None,
    opener: Optional[RelayOpener] = None,
    timeout: float = DEFAULT_RELAY_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Relay one steering verb to a node's own `/api/coders/{key}/{verb}`.

    Returns the node's typed result stamped with ``node`` (so the caller
    knows WHERE the keystroke landed), or a typed relay refusal:
    ``unknown_node`` (not configured) / ``node_offline`` (did not answer) /
    ``node_error`` (answered with garbage). The pane key is percent-encoded
    so a `pane:%N` key survives the URL intact.
    """
    table = nodes if nodes is not None else load_nodes()
    conf = table.get(node)
    if not conf or not conf.get("base_url"):
        return {
            "status": "unknown_node",
            "node": node,
            "detail": f"no steering node named '{node}' is configured",
        }
    base = str(conf["base_url"]).rstrip("/")
    url = f"{base}/api/coders/{quote(key, safe='')}/{verb}"
    headers: dict[str, str] = {}
    token = conf.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    send = opener or _default_opener
    try:
        res = send(method, url, headers, body, timeout)
    except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
        # Honest liveness: a node that cannot be reached refuses BY NAME.
        return {
            "status": "node_offline",
            "node": node,
            "detail": f"node '{node}' did not answer: {exc}",
        }
    result = res.get("json")
    if not isinstance(result, dict) or not result:
        return {
            "status": "node_error",
            "node": node,
            "detail": "node returned no usable result",
            "relay_http_status": res.get("status"),
        }
    result["node"] = node
    result.setdefault("relay_http_status", res.get("status"))
    return result


# Relay refusals that mean the NODE could not be reached (a gateway problem),
# vs the node answering with its own typed refusal (unarmed / pane_mismatch).
RELAY_GATEWAY_STATUSES = frozenset({"unknown_node", "node_offline", "node_error"})


def relay_http_code(result: dict[str, Any]) -> int:
    """Map a relayed result to the hub's HTTP status: 502 when the node
    could not be reached, 200 on a delivered/armed/live answer, 409 for the
    node's own typed refusal."""
    status = result.get("status")
    if status in RELAY_GATEWAY_STATUSES:
        return 502
    if status in {"delivered", "armed", "disarmed", "live", "not_modified", "preview"}:
        return 200
    return 409


__all__ = [
    "DEFAULT_RELAY_TIMEOUT_SECONDS",
    "RELAY_GATEWAY_STATUSES",
    "RelayOpener",
    "load_nodes",
    "relay",
    "relay_http_code",
]
