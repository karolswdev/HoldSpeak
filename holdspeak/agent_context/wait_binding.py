"""The owner's displayed wait, bound to its prompt and original pane process.

The prompt token is content-addressed. The pane proof is captured by the hook
producer when the wait starts, never derived from a delivery's current target.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Mapping

ANSWER_READ_AGAIN = "The answer was not sent; read the question again."


def _field(session: Any, name: str, default: Any = None) -> Any:
    return session.get(name, default) if isinstance(session, Mapping) else getattr(session, name, default)


def capture_pane(session: Any) -> dict[str, str | None]:
    """Existing tmux identity probe; rigs opt out before any machine read."""
    target = _field(session, "tmux_pane")
    proof = {"wait_pane_id": str(target or "") or None, "wait_pane_fingerprint": None}
    if not target or os.environ.get("HOLDSPEAK_WAIT_PANE_PROBE", "").lower() in {"off", "0", "false"}:
        return proof
    from ..coder_steering import resolve_pane_identity
    try:
        identity = resolve_pane_identity(str(target))
        if identity.get("status") == "ok":
            proof.update(wait_pane_id=identity.get("pane_id"), wait_pane_fingerprint=identity.get("fingerprint"))
    except Exception:
        pass  # No proof never authorizes an answer.
    return proof


def owner_wait(session: Any) -> dict[str, Any]:
    from .models import is_blocked, wait_kind
    if not is_blocked(session):
        return {}
    kind = wait_kind(session)
    command, complete, screen_revision = None, False, None
    if kind == "approve":
        from .screen_watch import STORE
        row = STORE.get(f"{_field(session, 'agent')}:{_field(session, 'session_id')}")
        if (row and row.state == "blocked" and row.pane_id == _field(session, "wait_pane_id")
                and row.pane_fingerprint == _field(session, "wait_pane_fingerprint")):
            command, complete, screen_revision = row.command, row.command_complete, row.prompt_revision
    revision = prompt_revision(session, command, complete, screen_revision)
    return {"wait_id": _field(session, "wait_id"), "wait_revision": revision, "wait_kind": kind,
            "expected_pane_id": _field(session, "wait_pane_id"),
            "expected_pane_fingerprint": _field(session, "wait_pane_fingerprint"),
            "command": command, "command_complete": complete, "_screen_revision": screen_revision}


def prompt_revision(session: Any, command: str | None, complete: bool, screen_revision: str | None = None) -> str:
    from .models import wait_kind
    material = [_field(session, "wait_prompt_revision"), wait_kind(session), _field(session, "question"), command, complete, screen_revision]
    return hashlib.sha256(json.dumps(material, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def answer_fields(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {key: binding.get(key) for key in ("wait_id", "wait_revision", "wait_kind", "expected_pane_id", "expected_pane_fingerprint")}


def current_session(key: str) -> Any:
    from . import list_agent_sessions
    agent, _, ident = key.partition(":")
    return next((row for row in list_agent_sessions(agent=agent) if row.session_id == ident), None)


def current_wait(key: str) -> dict[str, Any]:
    session = current_session(key)
    return owner_wait(session) if session else {}


def check_delivery(key: str, expected: Mapping[str, Any] | None, pane_id: str, *, runner: Any = None,
                   allow_permission: bool = False, typed: bool = False) -> dict[str, Any] | None:
    """Last check at the terminal boundary, including a respawn at the same %N."""
    if not expected:
        return {"status": "wait_binding_required", "detail": ANSWER_READ_AGAIN}
    current = current_wait(key)
    if answer_fields(current) != answer_fields(expected):
        return {"status": "wait_not_current", "detail": "the question or its terminal changed"}
    fingerprint = expected.get("expected_pane_fingerprint")
    from ..coder_steering import resolve_pane_identity
    identity = resolve_pane_identity(pane_id, runner=runner)
    if (not fingerprint or expected.get("expected_pane_id") != pane_id
            or identity.get("status") != "ok" or identity.get("fingerprint") != fingerprint):
        return {"status": "pane_mismatch", "detail": "the agent's terminal process changed — nothing was sent"}
    from .screen_watch import capture
    from .screen_rules import prompt_reading
    screen = capture(pane_id, runner=runner)
    if screen is None:
        return {"status": "pane_gone", "detail": "the question could not be read"}
    live = prompt_reading(screen[0])
    identity = resolve_pane_identity(pane_id, runner=runner)
    if identity.get("status") != "ok" or identity.get("fingerprint") != fingerprint:
        return {"status": "pane_mismatch", "detail": "the agent's terminal process changed — nothing was sent"}
    if current.get("wait_kind") != "approve" and live["wait"] == "approve":
        return {"status": "wait_not_current", "detail": "a permission prompt replaced the question — nothing was sent"}
    if current.get("wait_kind") == "approve":
        if expected.get("wait_revision") != prompt_revision(current_session(key), live["command"], live["command_complete"], current.get("_screen_revision")):
            return {"status": "wait_not_current", "detail": "the permission prompt changed — nothing was sent"}
        if typed or allow_permission and not current.get("command_complete"):
            return {"status": "command_incomplete", "detail": "the full command is not visible — open the raw lane"}
    if answer_fields(current_wait(key)) != answer_fields(expected):
        return {"status": "wait_not_current", "detail": "the question changed while it was read — nothing was sent"}
    return None
