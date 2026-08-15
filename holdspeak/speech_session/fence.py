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
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar

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

T = TypeVar("T")


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
    #: The election lock (HS-131-15, Sol Amendment 6). Cancellation and
    #: model-derived publication contend for THIS lock, so "check liveness, then
    #: publish" is one atomic decision instead of a check-then-write race.
    #: Re-entrant so a publication callback may consult the fence it won.
    election: Any = field(
        default_factory=threading.RLock, compare=False, repr=False
    )
    #: The durable publication claim currently owned by THIS callback thread.
    #: A speech callback may close its parent while its claim is live; passing the
    #: exact token lets that terminal update clear the claim atomically. Another
    #: thread or process has no token and therefore cannot transition the parent.
    _publication: Any = field(
        default_factory=threading.local, compare=False, repr=False
    )

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
        """Fence this session locally, the instant cancellation is decided.

        Takes the election lock: a publication that is already INSIDE the gate
        finishes first and cancellation observes it, rather than the two landing
        half-and-half (HS-131-15).
        """
        with self.election:
            self.cancelled.set()

    @property
    def publication_claim_id(self) -> str:
        """The exact durable publication token owned by this callback thread."""
        return str(getattr(self._publication, "claim_id", "") or "")

    def _claim_publication(self) -> tuple[str, str]:
        """Atomically prove liveness and claim the durable publication slot.

        ``BEGIN IMMEDIATE`` makes the joined parent/warrant read and the claim CAS
        one SQLite writer election. A cancellation or revocation that commits
        first is observed here; a claim that commits first is observed by those
        transitions, which wait until this bounded callback releases it.
        """
        claim_id = "pub_" + uuid.uuid4().hex
        moment = time.time()
        if not self.operation_id:
            return "", SESSION_NOT_ADMITTED
        if self.cancelled.is_set():
            return "", SESSION_NOT_LIVE
        bound = self.effective_deadline
        if bound and moment >= bound:
            return "", SESSION_EXPIRED
        try:
            with self.broker.store._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT p.state,p.deadline_at,p.publication_claim_id,"
                    "o.warrant_json,o.warrant_revoked "
                    "FROM kernel_parent_runs p "
                    "JOIN kernel_operations o ON o.operation_id=p.operation_id "
                    "WHERE p.operation_id=?",
                    (str(self.operation_id),),
                ).fetchone()
                reason = _row_fence_reason(row, now=moment)
                if reason:
                    return "", reason
                if str(row["publication_claim_id"] or ""):
                    return "", SESSION_NOT_LIVE
                changed = conn.execute(
                    "UPDATE kernel_parent_runs SET publication_claim_id=?,"
                    "publication_claimed_at=?,updated_at=? "
                    "WHERE operation_id=? AND state='OPEN' "
                    "AND publication_claim_id=''",
                    (claim_id, moment, moment, str(self.operation_id)),
                ).rowcount
                if changed != 1:
                    return "", SESSION_NOT_LIVE
        except Exception as exc:
            log.error(
                "speech session publication claim failed: %s", type(exc).__name__
            )
            return "", SESSION_NOT_ADMITTED
        return claim_id, ""

    def _release_publication_once(self, claim_id: str) -> None:
        """Clear this callback's exact durable token in one transaction."""
        with self.broker.store._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE kernel_parent_runs SET publication_claim_id='',"
                "publication_claimed_at=NULL,updated_at=? "
                "WHERE operation_id=? AND publication_claim_id=?",
                (time.time(), str(self.operation_id), str(claim_id)),
            )

    def _recover_publication_release(self, claim_id: str) -> None:
        """Retry a completed callback's exact release until storage recovers.

        The callback has already run, so replay is forbidden. Clearing only its
        random claim token is safe even if terminal close already cleared it. A
        daemon retry keeps a transient SQLite fault from stranding an OPEN parent
        for the rest of this live process; startup lease reconciliation remains the
        crash recovery owner.
        """
        delay = 0.01
        while True:
            time.sleep(delay)
            try:
                self._release_publication_once(claim_id)
            except Exception:
                delay = min(delay * 2.0, 1.0)
                continue
            log.info("speech session publication release recovered")
            return

    def _release_publication(self, claim_id: str) -> None:
        """Release this callback's durable slot unless terminal close cleared it."""
        try:
            self._release_publication_once(claim_id)
            return
        except Exception as exc:
            # The callback may already have produced its effect. Never replay it to
            # paper over an unreadable release. Its exact token remains owned by this
            # completed callback and is safe to clear as soon as storage recovers.
            log.error(
                "speech session publication release deferred: %s", type(exc).__name__
            )
        worker = threading.Thread(
            target=self._recover_publication_release,
            args=(claim_id,),
            daemon=True,
            name="speech-publication-release",
        )
        try:
            worker.start()
        except RuntimeError:
            # Thread creation can be refused during interpreter shutdown. In a live
            # process, recover synchronously rather than abandon the durable claim.
            self._recover_publication_release(claim_id)

    def publish(
        self, stage: str, publication: Callable[[], T]
    ) -> tuple[bool, Optional[T]]:
        """Elect ONE model-derived publication against every cancellation path.

        The local ``RLock`` serializes threads sharing this immutable carrier. The
        durable claim serializes a different process — or a second broker over the
        same database — with the same liveness decision. The bounded callback runs
        while both elections are owned; its terminal close may clear the exact
        durable token atomically.

        Returns ``(True, value)`` when this publication won and its callback ran,
        or ``(False, None)`` when the session was already cancelled, expired,
        revoked, closed, or another publication owns the parent.
        """
        with self.election:
            claim_id, reason = self._claim_publication()
            if not claim_id:
                log.info(
                    "speech session lost the publication election at %s: %s",
                    stage,
                    reason,
                )
                return False, None
            previous = self.publication_claim_id
            self._publication.claim_id = claim_id
            try:
                return True, publication()
            finally:
                if previous:
                    self._publication.claim_id = previous
                else:
                    try:
                        del self._publication.claim_id
                    except AttributeError:
                        pass
                self._release_publication(claim_id)

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


def _row_fence_reason(row: Any, *, now: Optional[float] = None) -> str:
    """Classify one joined parent/warrant row without performing another read."""
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
    return SESSION_EXPIRED if expires and moment >= expires else ""


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
    return _row_fence_reason(_parent_row(broker, operation_id), now=now)


__all__ = [
    "LIVE_PARENT_STATES",
    "SessionFence",
    "parent_fence_reason",
    "parent_state",
]
