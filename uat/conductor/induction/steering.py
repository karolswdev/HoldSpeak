"""Live-steering staging — drive the product's own `/api/coders/*` routes.

The product owns tmux and the steering registry; the harness only calls its
routes (spawn a pane, peek it, arm a grant, send keys, read the audit). No tmux
code and no ``holdspeak`` import here — the pane is resolved to its ``pane:%N``
key through the product's own attach-to-any-pane discovery
(``GET /api/coders/steering/panes``).

Spawned tmux sessions are named ``uat-<run>-<name>`` so they're identifiable and
never collide with the owner's real panes; the conductor kills them on teardown.
"""

from __future__ import annotations

import json
import subprocess
from urllib.parse import quote

from .product_client import ProductClient


def session_name(run_id: str, name: str) -> str:
    short = run_id.replace("run-", "").split("-")[-1]
    return f"uat-{short}-{name}"


def pane_key_for_session(client: ProductClient, session: str) -> str | None:
    """Resolve a tmux session name to its ``pane:%N`` steering key, or None."""
    try:
        panes = client.get_json("/api/coders/steering/panes").get("panes", [])
    except Exception:
        return None
    for p in panes:
        if p.get("session") == session:
            return f"pane:{p.get('pane_id')}"
    return None


def enc(key: str) -> str:
    """URL-encode a ``pane:%N`` key (the ``%`` must not read as an escape)."""
    return quote(key, safe=":")


def spawn(client: ProductClient, session: str, command: str) -> dict:
    resp = client.post_json(
        "/api/coders/factory/spawn", {"name": session, "command": command}
    )
    return {"status_code": resp.status_code, **(_json(resp))}


def arm(client: ProductClient, session: str, ttl_seconds: int = 120) -> dict:
    key = pane_key_for_session(client, session)
    if key is None:
        return {"ok": False, "error": f"no pane for session {session!r}"}
    resp = client.post_json(f"/api/coders/{enc(key)}/arm", {"ttl_seconds": ttl_seconds})
    return {"ok": resp.status_code == 200, "status_code": resp.status_code, "key": key, **_json(resp)}


def send_keys(client: ProductClient, session: str, keys: list[str]) -> dict:
    key = pane_key_for_session(client, session)
    if key is None:
        return {"ok": False, "error": f"no pane for session {session!r}"}
    resp = client.post_json(f"/api/coders/{enc(key)}/keys", {"keys": keys})
    return {"ok": resp.status_code == 200, "status_code": resp.status_code, "key": key, **_json(resp)}


def steer(client: ProductClient, session: str, text: str) -> dict:
    key = pane_key_for_session(client, session)
    if key is None:
        return {"ok": False, "error": f"no pane for session {session!r}"}
    resp = client.post_json(f"/api/coders/{enc(key)}/steer", {"text": text})
    return {"ok": resp.status_code == 200, "status_code": resp.status_code, "key": key, **_json(resp)}


def kill_session(session: str) -> None:
    """Tear down a spawned tmux session (cleanup; tmux is a system tool)."""
    subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)


def _json(resp) -> dict:
    try:
        body = resp.json()
        return body if isinstance(body, dict) else {"body": body}
    except (json.JSONDecodeError, ValueError):
        return {}
