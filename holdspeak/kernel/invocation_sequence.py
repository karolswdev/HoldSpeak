"""The LOGICAL invocation a caller cancels, across its physical attempts.

HS-131-10 gave the runner a second physical attempt: a dialect signal from the
provider is admitted as its OWN child (``<iid>_r2``), with its own ordinal and
its own terminal receipt. That is right for cardinality and wrong for
cancellation, because it split the thing a caller can NAME from the thing the
runner tracks.

A caller holds ONE id: the invocation id it asked for. The runner's cancellation
registry, though, is keyed by the PHYSICAL attempt currently running. Between
attempt one terminalizing and ``_r2`` registering, that registry holds nothing at
all — so ``cancel(original_id)`` fell through to "read whatever receipt exists",
answered ``failed`` from the attempt that had just closed, and the follow-up then
dispatched and published anyway. The caller was told the work was over while the
provider was still being called.

A :class:`Sequence` is the fence. It is opened by ``InferenceRunner.invoke``
under the STABLE first invocation id, lives exactly as long as that call, and
holds the two facts the physical registry cannot:

* whether this logical invocation has been cancelled — checked before any later
  attempt is admitted, and again, atomically, as that attempt registers, so a
  cancellation landing anywhere in the handoff still prevents the dispatch and
  the publication;
* which physical attempt is live right now — so ``cancel(original_id)`` reaches
  ``_r2`` through the runner's ordinary cancellation machinery instead of missing
  it entirely.

Nothing here decides an outcome or writes a row. It only answers "may a later
attempt start, and who should be told to stop" — the runner keeps every existing
cancellation semantic.
"""

from __future__ import annotations

import threading
from typing import Any, Optional


class Sequence:
    """One logical invocation: its cancellation flag and its live attempt."""

    __slots__ = ("logical_id", "_lock", "_cancelled", "_principal", "attempts", "attempt_id")

    def __init__(self, logical_id: str) -> None:
        self.logical_id = str(logical_id)
        self._lock = threading.Lock()
        self._cancelled = False
        self._principal: Any = None
        #: Physical attempts that have registered. ``0`` means the first attempt
        #: has not reached the runner's active registry yet, where the ORIGINAL
        #: pre-dispatch cancellation semantics (a pending cancellation, honoured
        #: by the first attempt) still apply unchanged.
        self.attempts = 0
        self.attempt_id = ""

    def mark_cancelled(self, principal: Any) -> str:
        """Fence the sequence and report which physical attempt is live, if any."""
        with self._lock:
            if not self._cancelled:
                self._cancelled, self._principal = True, principal
            return self.attempt_id

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    @property
    def cancel_principal(self) -> Any:
        with self._lock:
            return self._principal

    def enter(self, attempt_id: str) -> Any:
        """Register the attempt that is starting; return a principal if fenced.

        Called by the runner INSIDE the same critical section that puts the
        attempt into the active registry, which is what closes the last window:
        a cancellation that arrived after ``invoke`` checked the flag but before
        this attempt became reachable is returned here, and the runner performs it
        as an ordinary pre-dispatch cancellation — no provider is reached.
        """
        with self._lock:
            self.attempts += 1
            self.attempt_id = str(attempt_id)
            return self._principal if self._cancelled else None

    def leave(self, attempt_id: str) -> None:
        """The attempt is over; it is no longer the one a cancellation should reach."""
        with self._lock:
            if self.attempt_id == str(attempt_id):
                self.attempt_id = ""


class SequenceRegistry:
    """The live logical invocations, keyed by their stable first invocation id."""

    def __init__(self) -> None:
        self._live: dict[str, Sequence] = {}
        self._lock = threading.Lock()

    def open(self, logical_id: str) -> Sequence:
        sequence = Sequence(logical_id)
        with self._lock:
            self._live[str(logical_id)] = sequence
        return sequence

    def close(self, sequence: Sequence) -> None:
        with self._lock:
            if self._live.get(sequence.logical_id) is sequence:
                self._live.pop(sequence.logical_id, None)

    def get(self, logical_id: str) -> Optional[Sequence]:
        with self._lock:
            return self._live.get(str(logical_id))


__all__ = ["Sequence", "SequenceRegistry"]
