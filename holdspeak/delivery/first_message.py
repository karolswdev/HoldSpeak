"""The first message of a launch: typed once the agent is up, never lost.

A launched coding agent reads its first message (the Hand-to-agent brief)
only when it is ready. Text typed at spawn time is lost behind a startup
screen (Claude Code's folder-trust prompt) or a slow start. So the launch
stores the brief as a PENDING delivery on its launch record and types it
when the agent's rider hooks register the session.

The launch record carries the whole delivery:

- ``instruction_state``: ``pending`` -> ``sent``; or ``expired`` (no
  registration in the wait), ``session_gone`` (the session ended first),
  ``interrupted`` (the hub stopped while it waited and the session is gone),
  ``hooks_missing`` (the agent has no rider hooks to say it is ready), or
  the steering refusal (``unarmed``, ``pane_mismatch``, ``transport_error``
  ...). Only a ``delivered`` receipt makes it ``sent``.
- ``pending_brief``: the brief, its principal, its parent operation and
  whether to look for Claude Code's trust prompt. Kept until the brief is
  sent, so a hub restart resumes it (``reconcile``) and the owner can resume
  it on the same launch (``resume``) instead of relaunching.
- ``trust_state`` (Claude): ``answered`` / ``not_seen`` / ``timeout`` or a
  steering refusal.

The terminal kernel receipt of a ``process.spawn`` launch is ``succeeded``
only when the brief was sent; a session that ends with the brief undelivered
is ``failed`` (the launch state says ``ended_undelivered``).
"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from .. import coder_steering

#: How long a launch waits for its rider to register before it gives up on
#: typing the first message (the owner may first answer a dialog in the pane).
REGISTRATION_WAIT_SECONDS = 30 * 60

#: How long a launch looks for Claude Code's folder-trust prompt. No matching
#: prompt in this window: ``trust_state: not_seen``, and nothing is typed.
TRUST_WAIT_SECONDS = 20.0

#: How often the launch waiter looks at the pane and the rider registry.
LAUNCH_POLL_SECONDS = 1.0

#: Claude Code 2.1.x's folder-trust prompt, line by line. Only this screen is
#: answered; any other wording is left alone (``not_seen``).
TRUST_HEADER = "Accessing workspace:"
TRUST_QUESTION = "Is this a project you created or one you trust"
TRUST_NO = "No, exit"
TRUST_YES = "Yes, I trust this folder"
TRUST_FOOTER = "Enter to confirm"
_CURSOR = "❯"  # the ❯ that marks the selected choice

#: The states after which nothing is typed again.
DELIVERED = "sent"
UNDELIVERED_END = "ended_undelivered"


# ── the trust prompt ─────────────────────────────────────────────────


def parse_trust_prompt(lines: list[str]) -> Optional[dict[str, Any]]:
    """The LIVE folder-trust prompt on a pane, or ``None``.

    Live means the prompt is the bottom of the screen: its footer is the last
    non-blank line, so a prompt left in the scrollback above other output is
    not live. Returns ``{paths, cursor}``: ``paths`` are the readings of the
    path block (Ink breaks a long path over lines; the break may stand for
    nothing or for one space) and ``cursor`` is ``"yes"``, ``"no"`` or
    ``None``."""
    rows = [str(line).rstrip() for line in lines]
    while rows and not rows[-1].strip():
        rows.pop()
    if not rows or TRUST_FOOTER not in rows[-1]:
        return None
    header = max((i for i, row in enumerate(rows) if row.strip() == TRUST_HEADER), default=None)
    if header is None:
        return None
    region = rows[header + 1:]
    question = next((i for i, row in enumerate(region) if TRUST_QUESTION in row), None)
    if question is None:
        return None
    path_rows: list[str] = []
    for row in region[:question]:
        if not row.strip():
            if path_rows:
                break
            continue
        path_rows.append(row)
    if not path_rows:
        return None
    pad = min(len(row) - len(row.lstrip(" ")) for row in path_rows)
    parts = [row[pad:] for row in path_rows]
    paths = {"".join(parts), " ".join(parts)}
    no_row = next((row for row in region[question:] if TRUST_NO in row), None)
    yes_row = next((row for row in region[question:] if TRUST_YES in row), None)
    if no_row is None or yes_row is None:
        return None
    cursor = "yes" if _CURSOR in yes_row else ("no" if _CURSOR in no_row else None)
    return {"paths": paths, "cursor": cursor}


def trust_prompt_for(lines: list[str], worktree_path: str) -> Optional[dict[str, Any]]:
    """The live trust prompt when it names EXACTLY ``worktree_path``."""
    prompt = parse_trust_prompt(lines)
    if prompt is None:
        return None
    path = str(worktree_path)
    expected = {path}
    home = str(Path.home())
    if path.startswith(home + "/"):
        expected.add("~" + path[len(home):])
    return prompt if prompt["paths"] & expected else None


# ── the delivery ─────────────────────────────────────────────────────


def _principal_record(principal: Any) -> dict[str, str]:
    kind = getattr(principal, "kind", None)
    return {
        "kind": str(getattr(kind, "value", kind) or "owner"),
        "identity": str(getattr(principal, "identity", "") or "owner-session"),
    }


def _principal_from(stored: Mapping[str, Any]) -> Any:
    from ..principals import Principal, PrincipalKind

    try:
        kind = PrincipalKind(str(stored.get("kind") or "owner"))
    except ValueError:
        kind = PrincipalKind.OWNER
    return Principal(kind, str(stored.get("identity") or "owner-session"))


class FirstMessage:
    """The pending first message of the launches of one ``LaunchService``."""

    def __init__(self, service: Any) -> None:
        self._svc = service
        self._lock = threading.Lock()
        self._running: set[str] = set()
        self._watched: set[str] = set()
        self._threads: dict[str, threading.Thread] = {}
        self._stop = threading.Event()

    # the public verbs ------------------------------------------------------

    def hold(
        self, launch_id: str, text: str, principal: Any, *,
        operation_id: str = "", agent: str = "agent", trust: bool = False,
        state: str = "pending",
    ) -> dict[str, Any]:
        """Store the brief as this launch's pending first message."""
        return self._svc._ledger.update(
            launch_id,
            instruction_state=state,
            pending_brief={
                "text": text,
                "principal": _principal_record(principal),
                "operation_id": operation_id,
                "agent": agent,
                "trust": bool(trust),
            },
        ) or {}

    def start(self, launch_id: str) -> None:
        """Wait for registration, then type the brief (one waiter per launch)."""
        with self._lock:
            if launch_id in self._running or self._stop.is_set():
                return
            self._running.add(launch_id)
            thread = threading.Thread(
                target=self._guarded, args=(launch_id,), name=f"launch-brief-{launch_id}", daemon=True
            )
            self._threads[launch_id] = thread
        thread.start()

    def join(self, launch_id: str, timeout: float = 30.0) -> None:
        """Wait for this launch's waiter to finish (tests; a clean shutdown)."""
        with self._lock:
            thread = self._threads.get(launch_id)
        if thread is not None:
            thread.join(timeout)

    def close(self, timeout: float = 30.0) -> None:
        """Stop every waiter of this service (a hub shutting down): each
        leaves its launch as it is, so the next service resumes it."""
        self._stop.set()
        with self._lock:
            threads = list(self._threads.values())
        for thread in threads:
            thread.join(timeout)

    def retarget(self, launch_id: str) -> Optional[dict[str, Any]]:
        """The launch record with a terminal target that proves itself NOW.

        A restarted hub has a fresh target registry: the stored target is
        unknown to it. The session's pane is then read from the live tmux
        session and its immutable target issued again, the way the launch
        first bound it. ``None`` when no live pane proves itself."""
        svc = self._svc
        record = svc._ledger.get(launch_id) or {}
        target = record.get("target") or {}
        if target.get("target_id"):
            verified = svc._targets.verify(target.get("target_id"), target.get("target_generation"))
            if verified.get("status") == "ok":
                return record
        pane = svc._first_pane(str(record.get("session") or ""))
        if not pane:
            return None
        issued = svc._targets.issue(f"pane:{pane}")
        if issued.get("status") != "issued":
            return None
        return svc._ledger.update(launch_id, target={
            "target_id": issued["target_id"],
            "target_generation": issued["target_generation"],
            "pane_id": issued["pane_id"],
        })

    def resume(self, launch_id: str) -> dict[str, Any]:
        """Deliver the pending brief of an existing launch (no relaunch)."""
        from .factory_launch import LaunchRefused

        record = self._svc._ledger.get(launch_id)
        if record is None:
            raise LaunchRefused("launch_unknown", f"unknown launch {launch_id!r}")
        if record.get("instruction_state") == DELIVERED:
            return record
        if not isinstance(record.get("pending_brief"), Mapping):
            raise LaunchRefused("brief_not_held", "this launch holds no brief to deliver")
        if not self._svc._session_alive(str(record.get("session") or "")):
            self._svc._ledger.update(launch_id, instruction_state="session_gone")
            raise LaunchRefused("session_gone", "the agent session has ended")
        record = self._svc._ledger.update(launch_id, instruction_state="pending") or record
        self.start(launch_id)
        self.watch(launch_id)
        return record

    def reconcile(self) -> dict[str, int]:
        """After a hub (or launch service) restart: every launch still
        ``pending`` resumes when its session lives, else it is
        ``interrupted``, never silently lost. Live launches get their
        completion watch back."""
        summary = {"resumed": 0, "interrupted": 0}
        for record in self._svc._ledger.list():
            launch_id = str(record.get("launch_id") or "")
            if not launch_id or record.get("state") not in ("launched", "registered"):
                continue
            alive = self._svc._session_alive(str(record.get("session") or ""))
            if record.get("instruction_state") == "delivering":
                # The hub stopped in the middle of a send: whether the text
                # reached the pane is unknown. Named, never retyped by itself.
                self._svc._ledger.update(launch_id, instruction_state="interrupted")
                summary["interrupted"] += 1
            elif record.get("instruction_state") == "pending":
                if alive and isinstance(record.get("pending_brief"), Mapping):
                    self.start(launch_id)
                    summary["resumed"] += 1
                else:
                    self._svc._ledger.update(launch_id, instruction_state="interrupted")
                    summary["interrupted"] += 1
            self.watch(launch_id)
        return summary

    def watch(self, launch_id: str) -> None:
        """Issue the launch's terminal kernel receipt when its session ends."""
        record = self._svc._ledger.get(launch_id) or {}
        session = str(record.get("session") or "")
        if not session:
            return
        with self._lock:
            if launch_id in self._watched:
                return
            self._watched.add(launch_id)

        def watch() -> None:
            try:
                while self._svc._session_alive(session):
                    if self._stop.is_set():
                        return  # shutting down: the next service watches it
                    time.sleep(LAUNCH_POLL_SECONDS)
                self.settle(launch_id)
            finally:
                with self._lock:
                    self._watched.discard(launch_id)

        threading.Thread(target=watch, name=f"launch-{launch_id}", daemon=True).start()

    def settle(self, launch_id: str) -> Optional[str]:
        """The session ended: the launch is ``complete`` when its brief was
        sent (or it had none), else ``ended_undelivered``; the kernel
        receipt says the same (``succeeded`` / ``failed``)."""
        from ..principals import Principal, PrincipalKind

        record = self._svc._ledger.get(launch_id) or {}
        held = isinstance(record.get("pending_brief"), Mapping)
        delivered = record.get("instruction_state") == DELIVERED or (
            not held and record.get("instruction_state") in (None, DELIVERED)
        )
        state = "complete" if delivered else UNDELIVERED_END
        updates: dict[str, Any] = {"state": state, "completed_at": _iso_now()}
        if not delivered and record.get("instruction_state") == "pending":
            updates["instruction_state"] = "session_gone"
        operation_id = str(record.get("operation_id") or "")
        kernel = self._svc._kernel
        if operation_id and kernel is not None:
            node = Principal(PrincipalKind.NODE, self._svc._local_node_id)
            try:
                if kernel.store.receipt(operation_id) is None:
                    kernel.receipt(
                        operation_id, "succeeded" if delivered else "failed",
                        f"launch:{launch_id}", node,
                    )
            except Exception as exc:
                updates["receipt_error"] = str(exc)[:200]
        # The receipt first, then the state a reader waits on.
        self._svc._ledger.update(launch_id, **updates)
        return state

    # the waiter --------------------------------------------------------------

    def _guarded(self, launch_id: str) -> None:
        try:
            self._wait_and_send(launch_id)
        except Exception:  # the store went away (shutdown): say so, never raise
            try:
                self._svc._ledger.update(launch_id, instruction_state="error")
            except Exception:
                pass
        finally:
            with self._lock:
                self._running.discard(launch_id)

    def _wait_and_send(self, launch_id: str) -> None:
        svc = self._svc
        record = svc._ledger.get(launch_id) or {}
        held = record.get("pending_brief") if isinstance(record.get("pending_brief"), Mapping) else None
        if held is None:
            return
        principal = _principal_from(held.get("principal") or {})
        attempt_id = str(record.get("attempt_id") or "")
        session = str(record.get("session") or "")
        trust = _Trust(self, record, principal, held) if held.get("trust") else None
        deadline = time.monotonic() + REGISTRATION_WAIT_SECONDS
        while True:
            if self._stop.is_set():
                return  # this service is shutting down; the launch stays pending
            now_state = (svc._ledger.get(launch_id) or {}).get("instruction_state")
            if now_state != "pending":
                return  # another waiter (a restarted service) took it, or it was settled
            if not svc._session_alive(session):
                svc._ledger.update(launch_id, instruction_state="session_gone")
                return
            if trust is not None:
                trust.look()
            try:
                svc.bind_rider_claims()
            except Exception:
                pass  # a claims read failure is retried on the next poll
            attempt = svc._attempts.get(attempt_id) if attempt_id else None
            if attempt is not None and attempt.session_id:
                if trust is not None:
                    trust.registered()
                break
            if time.monotonic() >= deadline:
                svc._ledger.update(launch_id, instruction_state="expired")
                return
            time.sleep(LAUNCH_POLL_SECONDS)
        # One send, ever: claim the delivery under the ledger's lock. A second
        # waiter on the same launch (a recreated service) finds it taken.
        with _claim_lock(getattr(svc._ledger, "_path", "")):
            if self._stop.is_set():
                return
            if (svc._ledger.get(launch_id) or {}).get("instruction_state") != "pending":
                return
            fresh = self.retarget(launch_id)
            if fresh is None:
                svc._ledger.update(launch_id, instruction_state="target_gone")
                return
            record = fresh
            svc._ledger.update(launch_id, instruction_state="delivering")
        sent = svc._send_instruction(
            record, str(held.get("text") or ""), principal,
            {"agent_profile_id": held.get("agent")}, str(held.get("operation_id") or ""),
        )
        current = svc._ledger.get(launch_id) or dict(record)
        commands = dict(current.get("commands") or {})
        commands["instruction"] = sent.get("command_id")
        outcome = str((sent.get("receipt") or {}).get("outcome") or "")
        if outcome == "delivered":
            svc._ledger.update(
                launch_id, commands=commands, instruction_state=DELIVERED, pending_brief=None,
            )
        else:
            # The receipt decides: a refused or failed send keeps the brief
            # held, so the owner can resume it on this launch.
            svc._ledger.update(
                launch_id, commands=commands, instruction_state=outcome or "not_delivered",
            )

    def send_keys(
        self, record: Mapping[str, Any], keys: list[str], principal: Any, held: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Named keys to the launch's own pane as a child ``process.input``
        (the steering path re-checks the pane identity and receipts it)."""
        svc = self._svc
        target = record.get("target") or {}
        coder_steering.arm(
            str(record.get("session") or ""), str(target.get("pane_id") or ""), runner=svc._runner,
        )
        request: dict[str, Any] = {
            "node_id": svc._local_node_id,
            "target_id": target.get("target_id"),
            "target_generation": target.get("target_generation"),
            "operation": {"family": "coder_steering", "verb": "terminal.keys"},
            "payload": {
                "keys": list(keys),
                "session_key": record.get("session"),
                "agent": str(held.get("agent") or "agent"),
            },
        }
        if held.get("operation_id"):
            request["parent_operation_id"] = str(held["operation_id"])
        return svc._commands.submit_process_input(request, principal)


class _Trust:
    """Answer Claude Code's folder-trust prompt for exactly this launch's
    worktree: move to Yes at most once, confirm at most once. Nothing is
    typed for any other screen, prompt, path or pane."""

    def __init__(self, delivery: FirstMessage, record: Mapping[str, Any], principal: Any,
                 held: Mapping[str, Any]) -> None:
        self._delivery = delivery
        self._svc = delivery._svc
        self._record = record
        self._principal = principal
        self._held = held
        self._launch_id = str(record.get("launch_id") or "")
        self._path = self._svc._worktree_path(record)
        self._deadline = time.monotonic() + TRUST_WAIT_SECONDS
        self.state: Optional[str] = None if self._path else "not_seen"
        self._seen = False
        # The progress lives on the launch record, so a second waiter (a
        # resume, a restarted hub) never moves or confirms again.
        self._moved = bool(record.get("trust_moved"))
        self._confirmed = bool(record.get("trust_confirmed"))

    def _set(self, state: str) -> None:
        self.state = state
        self._svc._ledger.update(self._launch_id, trust_state=state)

    def registered(self) -> None:
        if self.state is None:
            self._set("answered" if self._confirmed else "not_seen")

    def look(self) -> None:
        if self.state is not None:
            return
        if time.monotonic() >= self._deadline:
            self._set("timeout" if self._seen else "not_seen")
            return
        record = self._delivery.retarget(self._launch_id)
        if record is None:
            return  # no live pane proves itself now; the session check decides
        self._record = record
        pane = str((record.get("target") or {}).get("pane_id") or "")
        peek = coder_steering.peek_pane(pane, lines=60, runner=self._svc._runner)
        if peek.get("status") != "live":
            return
        prompt = trust_prompt_for(list(peek.get("lines") or []), self._path)
        if prompt is None:
            if self._confirmed:
                self._set("answered")  # our prompt is gone after the one confirm
            return
        self._seen = True
        if self._confirmed:
            return  # one delivered Enter, ever: an unchanged frame gets nothing
        if prompt["cursor"] == "yes":
            if self._press(["Enter"]):
                self._confirmed = True
                self._svc._ledger.update(self._launch_id, trust_confirmed=True)
        elif prompt["cursor"] == "no" and not self._moved:
            self._moved = True
            self._svc._ledger.update(self._launch_id, trust_moved=True)
            self._press(["Down"])

    def _press(self, keys: list[str]) -> bool:
        sent = self._delivery.send_keys(self._record, keys, self._principal, self._held)
        current = self._svc._ledger.get(self._launch_id) or {}
        commands = dict(current.get("commands") or {})
        commands["trust"] = [*(commands.get("trust") or []), sent.get("command_id")]
        self._svc._ledger.update(self._launch_id, commands=commands)
        outcome = str((sent.get("receipt") or {}).get("outcome") or "")
        if outcome != "delivered":
            self._set(outcome or "refused")  # pane changed, not armed: stop
            return False
        return True


_CLAIM_LOCKS: dict[str, threading.Lock] = {}
_CLAIM_GUARD = threading.Lock()


def _claim_lock(key: Any) -> threading.Lock:
    with _CLAIM_GUARD:
        return _CLAIM_LOCKS.setdefault(str(key), threading.Lock())


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = [
    "FirstMessage",
    "LAUNCH_POLL_SECONDS",
    "REGISTRATION_WAIT_SECONDS",
    "TRUST_WAIT_SECONDS",
    "parse_trust_prompt",
    "trust_prompt_for",
]
