"""The lifetime of one interactive Thread turn (HS-S34).

A turn starts in ``ThreadService.start_turn`` and runs on its own thread.
This module keeps the turns that run now and the observers that wait on
them (the Ask and the Calls, through ``ask_desk.run_loop``):

- **Detach** is explicit and idempotent (``TurnObserver.detach``). A
  detached observer gets nothing more from the turn.
- **Cancellation and saved completion are two terminal facts.** The turn
  seals its fact once, before it saves its answer (``Turn.seal``). A cancel
  before the seal stops the turn; a cancel after the seal is refused. The
  fact is never inferred from an observer that is gone.
- **A late answer is saved on the turn** and the next ``read`` gives it.

This is not a general job runtime: it keeps only the Thread turn.
"""
from __future__ import annotations

import json
import threading
from typing import Any, Callable, Optional

RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
#: The row says the turn runs, but no turn runs in this process (a restart).
INTERRUPTED = "interrupted"
MISSING = "missing"


class _ToolExecutorAggregator:
    """Class-level view across concurrent per-turn tool executors.

    The ``/decide`` route (HS-152-02) accesses ``svc._tool_executor``
    and looks up handles by ``call_id``; this aggregator merges handles
    from all active executors so concurrent turns coexist.
    """

    def __init__(self) -> None:
        self._executors: dict[str, Any] = {}  # assistant_msg_id -> executor

    @property
    def _handles(self) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for ex in self._executors.values():
            merged.update(ex._handles)
        return merged

    def decide(self, handle: Any, decision: str, answer: Any = None) -> None:
        for ex in self._executors.values():
            if handle.call_id in ex._handles:
                ex.decide(handle, decision, answer)
                return
        raise ValueError(f"No active executor for call {handle.call_id}")

    def register(self, msg_id: str, executor: Any) -> None:
        self._executors[msg_id] = executor

    def unregister(self, msg_id: str) -> None:
        self._executors.pop(msg_id, None)

    def held(self, msg_id: str) -> list[Any]:
        """The calls of one turn that wait for a decision."""
        executor = self._executors.get(msg_id)
        if executor is None:
            return []
        return [h for h in list(executor._handles.values()) if h.state == "awaiting_decision"]


class Turn:
    """One running turn: its cancel signal, its terminal fact, its observers."""

    def __init__(self, message_id: str, thread_id: str, cancel_event: Optional[threading.Event] = None) -> None:
        self.message_id = message_id
        self.thread_id = thread_id
        self.cancel_event = cancel_event or threading.Event()
        #: "" while the turn can still be cancelled; then CANCELLED, COMPLETED or FAILED.
        self.terminal = ""
        #: True when the terminal row is written.
        self.saved = False
        self._lock = threading.Lock()
        self._closed = threading.Event()
        self._observers: list[TurnObserver] = []
        #: The owner's Stop for the pass that runs now (``engine_door.stop``).
        self.stop: Optional[Callable[[], Any]] = None
        self._stopping = False

    def seal(self, outcome: str) -> str:
        """Decide the terminal fact once: CANCELLED when a cancel came first,
        else ``outcome``. After this, a cancel is refused."""
        with self._lock:
            if not self.terminal:
                self.terminal = CANCELLED if self.cancel_event.is_set() or self._stopping else outcome
            return self.terminal

    def cancel(self) -> bool:
        with self._lock:
            if self.terminal:
                return False
            stop, self._stopping = self.stop, True
            if stop is None:
                self.cancel_event.set()
                return True

        def stop_then_signal() -> None:
            # The runner stops the live pass first, so the stop is on its
            # record (his decision, never a failure); then the turn ends.
            try:
                stop()
            except Exception:
                pass
            self.cancel_event.set()

        threading.Thread(target=stop_then_signal, daemon=True).start()
        return True


class TurnObserver:
    """One wait on a turn. ``detach`` ends it; a second ``detach`` does nothing."""

    def __init__(self, turn: Turn) -> None:
        self._turn = turn
        self.attached = True

    @property
    def message_id(self) -> str:
        return self._turn.message_id

    @property
    def finished(self) -> bool:
        """True when the turn has saved its terminal row and ended."""
        return self._turn._closed.is_set()

    def wait(self, timeout: Optional[float] = None) -> bool:
        return self._turn._closed.wait(timeout)

    def detach(self) -> None:
        with self._turn._lock:
            if self in self._turn._observers:
                self._turn._observers.remove(self)
            self.attached = False


_TURNS: dict[str, Turn] = {}
_LOCK = threading.Lock()


def open_turn(message_id: str, thread_id: str, cancel_event: Optional[threading.Event] = None) -> Turn:
    turn = Turn(message_id, thread_id, cancel_event)
    with _LOCK:
        _TURNS[message_id] = turn
    return turn


def get(message_id: str) -> Optional[Turn]:
    with _LOCK:
        return _TURNS.get(str(message_id or ""))


def live() -> list[Turn]:
    with _LOCK:
        return list(_TURNS.values())


def close_turn(message_id: str) -> None:
    """The turn's thread ended: it leaves the registry; its observers' waits end."""
    with _LOCK:
        turn = _TURNS.pop(message_id, None)
    if turn is not None:
        turn._closed.set()


def cancel(message_id: str) -> bool:
    """Stop a running turn. False when no turn runs or its terminal fact is sealed."""
    turn = get(message_id)
    return turn.cancel() if turn is not None else False


def observe(message_id: str) -> Optional[TurnObserver]:
    """Attach to a running turn. None when the turn has ended: ``read`` it."""
    turn = get(message_id)
    if turn is None:
        return None
    observer = TurnObserver(turn)
    with turn._lock:
        turn._observers.append(observer)
    return observer


def observers(message_id: str) -> list[TurnObserver]:
    turn = get(message_id)
    if turn is None:
        return []
    with turn._lock:
        return list(turn._observers)


def read(threads: Any, message_id: str) -> dict[str, Any]:
    """The turn's answer row as it is saved: its state and the last pass's words."""
    message = threads.get_message(message_id)
    if message is None:
        return {"state": MISSING, "text": "", "error": {}, "invocation_id": "", "egress_scope": "", "model": ""}
    error: dict[str, Any] = {}
    raw_error = str(getattr(message, "error_json", "") or "")
    if raw_error:
        try:
            error = json.loads(raw_error)
        except ValueError:
            error = {"error": raw_error}
    if getattr(message, "aborted_at", None) is not None:
        state = CANCELLED
    elif getattr(message, "streaming", 0):
        state = RUNNING if get(message_id) is not None else INTERRUPTED
    else:
        state = FAILED if error else COMPLETED
    # The answer is the last pass's words; earlier passes said what they
    # would look at (each pass that calls tools keeps its own text part).
    texts = [
        str(part.text).strip() for part in threads.get_parts(message_id)
        if part.kind == "text" and part.text and part.text.strip() and not part.draft
    ]
    return {
        "state": state,
        "text": texts[-1] if texts else "",
        "error": error,
        "invocation_id": str(getattr(message, "invocation_id", "") or ""),
        "egress_scope": str(getattr(message, "egress_scope", "") or ""),
        "model": str(getattr(message, "model_id", "") or ""),
    }


__all__ = [
    "CANCELLED", "COMPLETED", "FAILED", "INTERRUPTED", "MISSING", "RUNNING",
    "Turn", "TurnObserver", "cancel", "close_turn", "get", "live", "observe", "observers", "open_turn", "read",
]
