"""The explicit cancellation carrier for one admitted speech session (HS-131-09).

Sol OQ5 ruling: the immutable outer context and its cancellation check travel
EXPLICITLY down the dictation continuation — ``_kick_off_transcribe``,
``_transcribe_and_type``, ``_transcribe_wake``, ``transcribe_audio``, provider
continuations, ``process_transcript``, preview issuance, and the pipeline
callbacks. Each closure captures its OWN :class:`SessionFence`; there is no
ambient mutable "current dictation session" field anywhere for a late thread to
read.

The fence answers ONE question — *may this session still publish?* — and answers
it by name. It is checked before the provider stages, before rewrite/pipeline
publication, before preview issuance, and immediately before the delivery seam;
a fenced session DISCARDS its text. Delivery keeps its own separate effect
admission after the fence, never a duplicate inference-side receipt.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import json

from ..logging_config import get_logger
from .plan import (
    SESSION_CLOSED,
    SESSION_EXPIRED,
    SESSION_NOT_ADMITTED,
    SESSION_NOT_LIVE,
    SESSION_REVOKED,
)

log = get_logger("speech_session")

#: The parent states under which the session may still publish. Every other
#: state (CANCELLING, CANCELLED, SUCCEEDED, FAILED, REFUSED, INDETERMINATE) is a
#: fence: new work is refused by the kernel and late text is discarded here.
LIVE_PARENT_STATES = frozenset({"OPEN"})


@dataclass(frozen=True)
class SessionFence:
    """One immutable liveness/cancellation check bound to one parent.

    Frozen on purpose: a closure that captured this fence cannot be retargeted at
    another session, and nothing can widen the deadline it was admitted under.
    """

    broker: Any
    operation_id: str
    deadline_at: float
    cancelled: threading.Event = field(default_factory=threading.Event)
    #: At most one entry: the SEALED deadline (Sol Amendment 2). A list, because
    #: the fence itself stays frozen — a closure that captured it cannot be
    #: retargeted, and :meth:`seal` only ever LOWERS the bound.
    sealed: list[float] = field(default_factory=list)

    @property
    def effective_deadline(self) -> float:
        """The tightest deadline this fence knows: sealed if sealed, else admitted."""
        return float(self.sealed[0]) if self.sealed else float(self.deadline_at)

    def seal(self, deadline_at: float) -> float:
        """Lower this fence to the now-known real end; never raise it.

        Without this, a session sealed to ``release + 90s`` kept publishing
        against the ORIGINAL ``press + 30m + 90s`` ceiling in memory.
        """
        current = self.effective_deadline
        value = float(deadline_at) if not current else min(current, float(deadline_at))
        self.sealed[:] = [value]
        return value

    def cancel(self) -> None:
        """Fence this session locally, the instant cancellation is decided."""
        self.cancelled.set()

    def reason(self, *, now: Optional[float] = None) -> str:
        """The NAMED reason this session may no longer publish, or ``""``.

        Ordered cheapest-first: the in-memory cancellation flag, then the
        effective (sealed) deadline, then ONE indexed read of the durable parent
        row joined to its operation. The durable read is what makes a warrant
        revocation, a warrant expiry, a deadline sealed by another thread, an
        expiry reconciled elsewhere, or another thread's cancellation visible to
        this closure.
        """
        if not self.operation_id:
            return SESSION_NOT_ADMITTED
        if self.cancelled.is_set():
            return SESSION_NOT_LIVE
        moment = time.time() if now is None else float(now)
        bound = self.effective_deadline
        if bound and moment >= bound:
            return SESSION_EXPIRED
        return parent_fence_reason(self.broker, self.operation_id, now=moment)

    def live(self, *, now: Optional[float] = None) -> bool:
        return self.reason(now=now) == ""

    def discarded(self, stage: str) -> bool:
        """True when ``stage`` must discard its text; logs the safe reason only."""
        reason = self.reason()
        if not reason:
            return False
        log.info("speech session fenced before %s: %s", stage, reason)
        return True


def _parent_row(broker: Any, operation_id: str) -> Any:
    """One indexed read of the durable parent row joined to its operation."""
    if broker is None or not operation_id:
        return None
    try:
        with broker.store._connection() as conn:
            return conn.execute(
                "SELECT p.state,p.deadline_at,o.warrant_json,o.warrant_revoked"
                " FROM kernel_parent_runs p"
                " JOIN kernel_operations o ON o.operation_id=p.operation_id"
                " WHERE p.operation_id=?",
                (str(operation_id),),
            ).fetchone()
    except Exception as exc:  # a fence that cannot read refuses to publish
        log.error("speech session fence read failed: %s", type(exc).__name__)
        return None


def parent_state(broker: Any, operation_id: str) -> str:
    """The durable parent state, or ``""`` when the row is unknown.

    Kept as the narrow state-only question; :func:`parent_fence_reason` is what
    the fence itself asks, because state alone misses a revocation or an expiry.
    """
    row = _parent_row(broker, operation_id)
    return "" if row is None else str(row["state"])


def parent_fence_reason(broker: Any, operation_id: str, *, now: Optional[float] = None) -> str:
    """The NAMED durable reason this parent may no longer publish, or ``""``.

    Checks, in one read: the parent state, the PERSISTED (possibly sealed)
    deadline, the operation's warrant revocation flag, and the warrant's own
    execution expiry. A late provider return after ``release + 90s`` or after the
    owner revoked the warrant therefore cannot reach preview or delivery, even
    though the in-memory carrier was built under the original admitted ceiling.
    """
    row = _parent_row(broker, operation_id)
    if row is None:
        return SESSION_NOT_ADMITTED
    state = str(row["state"])
    if state not in LIVE_PARENT_STATES:
        return SESSION_CLOSED if state == "SUCCEEDED" else SESSION_NOT_LIVE
    if bool(row["warrant_revoked"]):
        return SESSION_REVOKED
    moment = time.time() if now is None else float(now)
    deadline = float(row["deadline_at"] or 0.0)
    if deadline and moment >= deadline:
        return SESSION_EXPIRED
    try:
        warrant = json.loads(str(row["warrant_json"] or "{}"))
    except Exception:
        warrant = {}
    expires = float(warrant.get("execution_expires_at") or 0.0)
    if expires and moment >= expires:
        return SESSION_EXPIRED
    return ""


__all__ = [
    "LIVE_PARENT_STATES",
    "SessionFence",
    "parent_fence_reason",
    "parent_state",
]
