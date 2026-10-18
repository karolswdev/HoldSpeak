"""Ask my whole desk (Betterment Q7; DECISIONS #16).

When the engine on the **Answers** row can use tools, an Ask looks things up
and acts on the desk, and its answer shows **Looked at**, **Wrote** and
**Prepared**:

- An agent CLI on this Mac (``cli:<preset>``) already gets the CONDUCTOR set
  through its run credential on every call (MCP M1, ``intel/cli_engine.py``).
  The Ask names its trace key around the engine call (``run_trace.for_item``),
  so the calls the hub serves for that run are the Ask's (MCP M2).
- An HTTP engine whose server takes tool calls (the Check's own question,
  ``setup_runtime.endpoint_tool_support``) runs the hub's tool loop: the Thread
  turn (``ThreadService.start_turn``) with the ASK palette and the Ask system
  prompt. A call the loop holds for his press shows in the Ask window with
  Allow once and Deny (``ask_progress`` frames, state ``hold``); the press
  goes to ``POST /api/threads/{id}/decide``.
- Any other engine keeps today's grounded Ask (About in the prompt).

Sends are only prepared (``channel.prepare``); send, config and authority
tools are not in either set and are refused.
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from types import SimpleNamespace
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind

log = get_logger("services.ask_desk")

#: The tool modes of the Answers engine.
CLI = "cli"
LOOP = "loop"
NONE = ""

#: The system prompt of an Ask that can use the desk's tools.
DESK_PROMPT = (
    "You answer the owner's questions about his work, and you can use the tools of his desk "
    "(HoldSpeak). Read memory pages first (memory.page), then memory.search, then the records "
    "(meetings, notes, people, projects, decisions, Jira). The objects named under About are where "
    "to start, not a limit. Answer in plain words and name the records you used. Change the desk "
    "only when he asks you to: add a task with door.add_item, write a note with desk.create, "
    "propose a decision (status proposed). Never send anything: channel.prepare only prepares a "
    "send, and he presses Send. If a tool is refused, say so and go on without it."
)

#: Words for a held tool call (the Ask window says what waits for his press).
_HOLD_WORDS = {
    "desk.create": "Write on your desk",
    "desk.update": "Change an item on your desk",
    "desk.delete": "Remove an item from your desk",
    "door.add_item": "Add a task",
    "follow_through.complete": "Mark a task done",
    "zone.file": "Put an item in a drawer",
    "project.item.create": "Add an item to a project",
    "channel.prepare": "Prepare a send",
}

#: How long one Ask waits for the hub's tool loop (holds included).
LOOP_LIMIT_SECONDS = 15 * 60.0
#: How long the Check's answer about an engine's tools is kept.
_SUPPORT_TTL_SECONDS = 600.0

_support_cache: dict[tuple[str, str], tuple[float, str]] = {}
_support_lock = threading.Lock()

#: A running loop Ask: the Ask's invocation id -> the turn's assistant message.
_LOOP_TURNS: dict[str, str] = {}

_OWNER = Principal(PrincipalKind.OWNER, "owner-session")


def hold_words(name: str) -> str:
    return _HOLD_WORDS.get(str(name or ""), "Change your desk")


def _answers_deployment(db: Any) -> Optional[SimpleNamespace]:
    """The first engine on the Answers row: kind, endpoint, model and profile."""
    from .inference_assignment_service import InferenceAssignmentService
    from .model_profile_service import resolve_v1_profile_execution

    try:
        effective = InferenceAssignmentService(db).resolve_effective(_OWNER, capability_id="ask.answer")
    except Exception as exc:
        log.info(f"Answers engine not read: {exc}")
        return None
    assignment = effective.get("assignment") if isinstance(effective, dict) else None
    entries = (assignment or {}).get("entries") or []
    if not entries:
        return None
    entry = entries[0]
    profile_id = str(entry.get("profile_id") or "")
    with db._connection() as conn:
        if int(entry.get("profile_schema_version", 2)) == 1:
            row = conn.execute(
                "SELECT * FROM profiles WHERE id=? AND deleted=0", (profile_id.removeprefix("legacy-"),),
            ).fetchone()
            if row is None:
                return None
            try:
                deployment = resolve_v1_profile_execution(SimpleNamespace(**dict(row)), db=db).deployment_revision
            except Exception:
                return None
            return SimpleNamespace(
                kind=str(deployment.kind), endpoint=str(deployment.endpoint or ""),
                model=str(deployment.model or ""), profile_id=profile_id.removeprefix("legacy-"),
            )
        binding = conn.execute(
            """SELECT b.deployment_revision_id FROM model_profile_binding_heads h
                 JOIN model_profile_binding_revisions b
                   ON b.binding_id=h.binding_id AND b.revision=h.revision
                WHERE h.profile_id=? AND b.profile_revision=?""",
            (profile_id, int(entry.get("profile_revision") or 0)),
        ).fetchone()
        if binding is None:
            return None
        row = conn.execute(
            "SELECT kind, endpoint, model FROM deployment_revisions WHERE id=?",
            (binding["deployment_revision_id"],),
        ).fetchone()
    if row is None:
        return None
    return SimpleNamespace(
        kind=str(row["kind"]), endpoint=str(row["endpoint"] or ""), model=str(row["model"] or ""),
        profile_id=profile_id,
    )


def _server_takes_tools(endpoint: str, model: str, profile_id: str) -> str:
    """The Check's answer for this server: ``yes``, ``no`` or ``unknown``.

    The same questions the Check asks (``/models`` capabilities, llama.cpp
    ``/props``, and the one-token request only to a keyless private address),
    kept for ten minutes."""
    key = (endpoint, model)
    now = time.monotonic()
    with _support_lock:
        cached = _support_cache.get(key)
        if cached and now - cached[0] < _SUPPORT_TTL_SECONDS:
            return cached[1]
    from ..setup_runtime import discover_endpoint_models, endpoint_tool_support

    api_key = ""
    try:
        from ..intel.providers import profile_key_env
        from ..profile_key_store import resolve_profile_key

        api_key = resolve_profile_key(profile_key_env(profile_id)) or ""
    except Exception:
        api_key = ""
    answer = "unknown"
    try:
        import ipaddress

        try:
            address = ipaddress.ip_address((urlparse(endpoint).hostname or "").strip("[]"))
            private = address.is_private or address.is_loopback
        except ValueError:
            private = False
        found = discover_endpoint_models(endpoint, api_key=api_key or None)
        answer = endpoint_tool_support(
            endpoint, model=model, api_key=api_key or None,
            lan=private and not api_key, tools_claimed=bool(found.get("toolsClaimed")),
        )
    except Exception as exc:
        log.info(f"tool support not read for {endpoint}: {exc}")
    with _support_lock:
        _support_cache[key] = (now, answer)
    return answer


def server_tools_on() -> bool:
    """``HOLDSPEAK_ASK_SERVER_TOOLS=off`` (rigs set it): no Ask asks an HTTP
    engine's server whether it takes tool calls, and none runs the loop."""
    import os

    return os.environ.get("HOLDSPEAK_ASK_SERVER_TOOLS", "on").strip().lower() not in {"off", "0", "false", "no"}


def tools_mode(db: Any) -> str:
    """How the Answers engine can use the desk: ``cli``, ``loop`` or ``""``."""
    deployment = _answers_deployment(db)
    if deployment is None:
        return NONE
    from ..intel.cli_engine import cli_engines_on, is_cli_endpoint

    if is_cli_endpoint(deployment.endpoint):
        return CLI if cli_engines_on() else NONE
    scheme = urlparse(deployment.endpoint).scheme
    if scheme not in {"http", "https"} or not server_tools_on():
        return NONE
    return LOOP if _server_takes_tools(deployment.endpoint, deployment.model, deployment.profile_id) == "yes" else NONE


def cancel_loop(invocation_id: str) -> bool:
    """Stop a running loop Ask (Stop in the Ask window)."""
    from .thread_service import ThreadService

    message_id = _LOOP_TURNS.get(str(invocation_id or ""))
    event = ThreadService._active_turns.get(message_id) if message_id else None
    if event is None:
        return False
    event.set()
    return True


def _holds(message_id: str) -> list[dict[str, str]]:
    from .thread_service import ThreadService

    executor = ThreadService._tool_executor._executors.get(message_id)
    if executor is None:
        return []
    rows = []
    for handle in list(executor._handles.values()):
        if handle.state == "awaiting_decision":
            rows.append({"call_id": handle.call_id, "tool": handle.name, "words": hold_words(handle.name)})
    return rows


async def run_loop(
    service: Any,
    principal: Principal,
    *,
    thread_id: str,
    question: str,
    refs: list[str],
    invocation_id: str,
    progress: Optional[Callable[[dict[str, Any]], None]] = None,
) -> dict[str, Any]:
    """One Ask turn through the hub's tool loop; waits for its end.

    ``service`` is a ThreadService wired with the ASK palette and
    :data:`DESK_PROMPT`. Returns the turn's answer message (text, error and
    route) and its ids."""
    from .thread_service import ThreadService

    ids = await service.start_turn(principal, thread_id, question, refs=refs or None)
    message_id = str(ids["assistant_message_id"])
    _LOOP_TURNS[invocation_id] = message_id
    said: list[dict[str, str]] = []
    deadline = time.monotonic() + LOOP_LIMIT_SECONDS
    try:
        while message_id in ThreadService._active_turns:
            holds = _holds(message_id)
            if holds != said and progress is not None:
                said = holds
                try:
                    progress({"invocation_id": invocation_id, "state": "hold", "thread_id": thread_id,
                              "holds": holds})
                except Exception as exc:
                    log.debug(f"hold frame dropped: {exc}")
            if time.monotonic() > deadline:
                cancel_loop(invocation_id)
                break
            await asyncio.sleep(0.1)
        # The turn ends on its own thread: wait for its last write.
        for _ in range(50):
            message = service._threads.get_message(message_id)
            if message is None or not getattr(message, "streaming", 0):
                break
            await asyncio.sleep(0.05)
    finally:
        _LOOP_TURNS.pop(invocation_id, None)
    message = service._threads.get_message(message_id)
    # The answer is the last pass's words; earlier passes said what they
    # would look at (each pass that calls tools keeps its own text part).
    texts = [
        str(part.text).strip() for part in service._threads.get_parts(message_id)
        if part.kind == "text" and part.text and part.text.strip() and not part.draft
    ]
    text = texts[-1] if texts else ""
    error: dict[str, Any] = {}
    raw_error = str(getattr(message, "error_json", "") or "")
    if raw_error:
        try:
            error = json.loads(raw_error)
        except ValueError:
            error = {"error": raw_error}
    return {
        "user_message_id": str(ids["user_message_id"]),
        "assistant_message_id": message_id,
        "turn_invocation_id": str(getattr(message, "invocation_id", "") or ""),
        "text": text,
        "error": error,
        "aborted": message is None or getattr(message, "aborted_at", None) is not None,
        "egress_scope": str(getattr(message, "egress_scope", "") or ""),
        "model": str(getattr(message, "model_id", "") or ""),
    }


__all__ = ["CLI", "DESK_PROMPT", "LOOP", "NONE", "cancel_loop", "hold_words", "run_loop", "tools_mode"]
