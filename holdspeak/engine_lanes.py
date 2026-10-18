"""Ask goes first (Betterment Q2).

A question the owner waits for must not queue behind background work on a
busy engine.  A LAN llama.cpp server often has ONE slot: while meeting
analysis or memory work holds it, an Ask waits for the slot, and on the
2026-10-17 walk it ran out its 60 s deadline twice (asking/RECON.md step 8).

This module is the one process-wide gate, at the runner (every physical
inference call passes ``InferenceRunner.invoke`` or ``invoke_stream``):

* While a foreground turn (``ask.answer``, ``chat.turn``) is admitted to an
  engine, a background call (meeting analysis, ``memory.*`` and the other
  Background jobs) does not START on that engine.  It waits, and goes on when
  the turn ends.  A background call already in flight is never stopped: the
  Ask waits for that one call only.
* ``busy_with(engine)`` names the background job in flight on an engine, so
  the Ask can say why it waits.

An engine is the server the bytes go to: the deployment's endpoint (or its
destination when it has none) and model.  Two assignments on the same server
share its slot, so they share a lane.
"""
from __future__ import annotations

import threading
import time
from collections import Counter
from contextlib import contextmanager
from typing import Any, Iterable, Iterator

# The contracts of a turn the owner waits for.  ``holdspeak.ask`` and
# ``holdspeak.thread`` are the classic (pre-route) contracts of the same turns.
FOREGROUND_CONTRACTS = frozenset({"ask.answer", "chat.turn", "holdspeak.ask", "holdspeak.thread"})

# A background call never waits longer than this for a foreground turn.  A
# turn ends within its own deadline (60 s per attempt); this only stops a lost
# release from holding background work forever.
MAX_HOLD_SECONDS = 300.0

_MEETING_ANALYSIS = "meeting analysis"
_MEMORY_WORK = "memory work"


def _background_labels() -> dict[str, str]:
    """Contract name -> the job's words, for every Background job."""
    labels: dict[str, str] = {
        "meeting.deferred.analysis": _MEETING_ANALYSIS,
        "meeting.auto.title": _MEETING_ANALYSIS,
        # The classic memory contracts (memory/*.py) carry the same names.
        "memory.extract": _MEMORY_WORK,
        "memory.consolidate": _MEMORY_WORK,
        "memory.page": _MEMORY_WORK,
        "memory.embed": _MEMORY_WORK,
    }
    try:
        from .inference_capabilities import builtin_capability_definitions

        for capability in builtin_capability_definitions():
            if capability.group_id != "background":
                continue
            name = capability.operation_contract.name
            labels.setdefault(
                name, _MEMORY_WORK if name.startswith("memory.") else capability.label.lower(),
            )
    except Exception:  # pragma: no cover - the fixed set above still holds
        pass
    return labels


BACKGROUND_LABELS: dict[str, str] = _background_labels()


def contract_of(request: Any) -> str:
    """The contract name of one ``InvocationRequest``, or ``""``."""
    origin = getattr(request, "definition_origin", None)
    return str(getattr(origin, "contract", "") or "")


def background_label(request: Any) -> str:
    """The job's words when this request is background work, else ``""``."""
    return BACKGROUND_LABELS.get(contract_of(request), "")


def engine_key(database: Any, deployment_revision_id: str) -> str:
    """The server one deployment revision sends to (its lane)."""
    ident = str(deployment_revision_id or "")
    if not ident or database is None:
        return ident
    try:
        with database._connection() as conn:
            row = conn.execute(
                "SELECT destination_id, endpoint, model FROM deployment_revisions WHERE id=?",
                (ident,),
            ).fetchone()
    except Exception:
        return ident
    if row is None:
        return ident
    place = str(row["endpoint"] or "").strip().rstrip("/") or str(row["destination_id"] or "")
    return f"{place}|{row['model']}"


class EngineLanes:
    """Foreground turns and background calls, per engine."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._foreground: Counter[str] = Counter()
        self._background: dict[str, dict[int, str]] = {}
        self._tokens = 0

    @contextmanager
    def foreground(self, keys: Iterable[str]) -> Iterator[None]:
        """Hold every engine in ``keys`` for one foreground turn."""
        held = sorted({key for key in keys if key})
        with self._cond:
            for key in held:
                self._foreground[key] += 1
        try:
            yield
        finally:
            with self._cond:
                for key in held:
                    self._foreground[key] -= 1
                    if self._foreground[key] <= 0:
                        del self._foreground[key]
                self._cond.notify_all()

    @contextmanager
    def background(self, key: str, label: str, *, max_wait: float = MAX_HOLD_SECONDS) -> Iterator[float]:
        """Run one background call on ``key`` once no foreground turn holds it.

        Yields the seconds it waited.
        """
        started = time.monotonic()
        with self._cond:
            while key and self._foreground.get(key, 0) > 0:
                left = max_wait - (time.monotonic() - started)
                if left <= 0:
                    break
                self._cond.wait(timeout=min(left, 1.0))
            self._tokens += 1
            token = self._tokens
            self._background.setdefault(key, {})[token] = label
        try:
            yield time.monotonic() - started
        finally:
            with self._cond:
                calls = self._background.get(key, {})
                calls.pop(token, None)
                if not calls:
                    self._background.pop(key, None)
                self._cond.notify_all()

    def busy_with(self, key: str) -> str:
        """The words for the background job in flight on ``key``, or ``""``."""
        with self._cond:
            calls = self._background.get(key) or {}
            return next(iter(calls.values()), "")

    def holds(self, key: str) -> bool:
        """True while a foreground turn holds ``key``."""
        with self._cond:
            return self._foreground.get(key, 0) > 0


LANES = EngineLanes()
