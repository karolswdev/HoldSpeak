"""The browser open-mic interval: ONE admitted parent, many utterances (HS-131-09).

A click-to-toggle open mic is one authority lifetime, so it admits exactly one
``dictation.session`` when the AUTHENTICATED route opens it, and every utterance
in that interval is a trusted child of that parent. The client never names the
parent: it receives an opaque server-issued handle bound to the authenticated
identity and a monotonic session generation, and the server resolves the live
interval itself. A handle the server did not mint — or one from another identity
or a retired generation — is refused by name.

Two fences shape the interval (Sol ruling):

* **The ceiling** — ``open + 30 minutes`` and 1,024 children. An indefinitely
  armed mic never keeps authority, and a model-heavy interval may legitimately
  exhaust the budget first.
* **The inactivity lease** — ``last utterance + 90 seconds``, kept as a field on
  this interval and refreshed atomically INSIDE the first Whisper child claim of
  each utterance (Sol Amendment 8). Zero extra round trips; empty audio, VAD
  decisions, and buffering never refresh it, because none of them claims a child.

Reaching any fence (inactivity, ceiling, budget, cancel, revocation) forces the
CLIENT interval closed (Sol Amendment 3): the utterance response carries the
named terminal status, the client drops its interval, and continuing needs a
fresh authenticated click — one visible interval never crosses authority epochs.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from ..logging_config import get_logger
from .plan import (
    BROWSER_CEILING_REACHED,
    BROWSER_HANDLE_REFUSED,
    BROWSER_INACTIVITY_LAPSED,
    BROWSER_STOPPED_DURING_OPEN,
    PARENT_DICTATION_SESSION,
    SpeechSessionRefused,
)
from .session import SessionGeneration, SpeechSession, admit_speech_session

log = get_logger("speech_session")

#: The hard authority ceiling of one open-mic interval.
BROWSER_CEILING_SECONDS = 30 * 60.0
#: The inactivity lease, measured from the last utterance that actually reached
#: the model.
BROWSER_INACTIVITY_SECONDS = 90.0
#: A model-heavy interval may exhaust this before the ceiling; visible closure
#: plus a fresh click is the correct outcome.
BROWSER_CHILD_BUDGET = 1024

#: The ONE terminal status the client honors. Named, not a bare 4xx: the client
#: closes its interval and requires a fresh click when it sees this.
MIC_INTERVAL_CLOSED = "closed"


@dataclass
class BrowserMicInterval:
    """One live open-mic interval: its handle, its parent, and its lease."""

    handle: str
    identity: str
    generation: int
    session: SpeechSession
    opened_at: float
    lease_until: float
    utterances: int = 0
    refreshes: int = 0
    closed_reason: str = ""
    _lock: Any = field(default_factory=threading.Lock)

    @property
    def ceiling_at(self) -> float:
        return self.opened_at + BROWSER_CEILING_SECONDS

    def fence_reason(self, *, now: Optional[float] = None) -> str:
        """The named reason this interval may no longer accept an utterance, or ``""``."""
        moment = time.time() if now is None else float(now)
        if self.closed_reason:
            return self.closed_reason
        if moment >= self.ceiling_at:
            return BROWSER_CEILING_REACHED
        if moment >= self.lease_until:
            return BROWSER_INACTIVITY_LAPSED
        # The parent itself is the authority on cancellation, revocation, and
        # budget exhaustion; the fence carrier reads it.
        return str(self.session.fence.reason(now=moment))

    def refresh_lease(self, *, now: Optional[float] = None) -> float:
        """Extend the inactivity lease, bounded by the ceiling (Sol Amendment 8).

        Atomic: called from inside a claimed Whisper child, possibly on a worker
        thread, while another request may be reading the same field.

        A lease that has ALREADY lapsed at claim time is never resurrected: a
        request that passed the fence and then sat in the transcription queue past
        the lease refuses by name here, INSIDE the claim and before any model
        dispatch, instead of extending an authority that had expired.
        """
        moment = time.time() if now is None else float(now)
        with self._lock:
            if self.closed_reason:
                raise SpeechSessionRefused(self.closed_reason)
            if moment >= self.ceiling_at:
                raise SpeechSessionRefused(BROWSER_CEILING_REACHED)
            if moment >= self.lease_until:
                raise SpeechSessionRefused(BROWSER_INACTIVITY_LAPSED)
            self.lease_until = min(self.ceiling_at, moment + BROWSER_INACTIVITY_SECONDS)
            self.refreshes += 1
            return self.lease_until

    def transcription(self) -> Any:
        """A per-utterance admission whose FIRST claim refreshes the lease."""
        with self._lock:
            self.utterances += 1
            ordinal = self.utterances
        return self.session.transcription(
            on_claim=self.refresh_lease,
            utterance_ref=f"{self.handle}:{ordinal}",
        )

    def close(self, reason: str = "") -> str:
        """Cancel and close the parent exactly once, recording the honest reason."""
        with self._lock:
            if self.closed_reason:
                return self.closed_reason
            self.closed_reason = reason or "browser_mic_closed"
        return str(self.session.cancel_and_close())


class BrowserMicSessions:
    """The device-local registry of live open-mic intervals, one per identity."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._intervals: dict[str, BrowserMicInterval] = {}
        self._generation = SessionGeneration()

    # ------------------------------------------------------------------ open

    def open(
        self,
        principal: Any,
        *,
        config_snapshot: Any = None,
        registry_snapshot: Any = None,
        now: Optional[float] = None,
    ) -> BrowserMicInterval:
        """Admit ONE ``dictation.session`` for this authenticated identity.

        Opening again replaces the previous interval only by CLOSING it first: two
        live parents for one visible mic would be two authorities for one lamp.

        Sol Amendment 1, applied to the browser: admission is not instantaneous,
        so a stop that lands DURING it retires this generation. The open then
        cancels the parent it just admitted, publishes nothing, and refuses by
        name — a stop can never leave an orphan interval holding authority.
        """
        identity = _identity(principal)
        token = self._generation.begin()
        started = time.time() if now is None else float(now)
        session = admit_speech_session(
            kind=PARENT_DICTATION_SESSION,
            principal=principal,
            insertion_aim="browser-open-mic",
            config_snapshot=config_snapshot,
            registry_snapshot=registry_snapshot,
            deadline_seconds=BROWSER_CEILING_SECONDS,
            child_budget=BROWSER_CHILD_BUDGET,
            now=started,
        )
        interval = BrowserMicInterval(
            handle="mic_" + uuid.uuid4().hex,
            identity=identity,
            generation=token,
            session=session,
            opened_at=started,
            lease_until=min(
                started + BROWSER_CEILING_SECONDS, started + BROWSER_INACTIVITY_SECONDS
            ),
        )
        with self._lock:
            live = self._generation.is_live(token)
            previous = self._intervals.pop(identity, None) if live else None
            if live:
                self._intervals[identity] = interval
        if previous is not None:
            previous.close("browser_mic_replaced")
        if not live:
            # The stop won the race. The freshly admitted parent is cancelled and
            # closed here; it was never published, so nothing can reach it.
            log.info("browser open mic cancelled: a stop won the acquisition race")
            interval.close(BROWSER_STOPPED_DURING_OPEN)
            raise SpeechSessionRefused(BROWSER_STOPPED_DURING_OPEN)
        log.info("browser open mic admitted: parent=%s", session.operation_id)
        return interval

    # --------------------------------------------------------------- resolve

    def resolve(self, principal: Any, handle: str = "") -> Optional[BrowserMicInterval]:
        """The live interval this authenticated request may use, or ``None``.

        A blank handle means "whatever interval this identity has open" — the
        server's own answer. A NON-blank handle must be one this registry minted
        for THIS identity and generation; anything else (notably a kernel parent
        id a client tried to supply) is refused by name, never honored.
        """
        identity = _identity(principal)
        with self._lock:
            interval = self._intervals.get(identity)
        wanted = str(handle or "").strip()
        if wanted:
            if interval is None or wanted != interval.handle:
                raise SpeechSessionRefused(BROWSER_HANDLE_REFUSED)
            if not self._generation.is_live(interval.generation):
                raise SpeechSessionRefused(BROWSER_HANDLE_REFUSED)
        if interval is None:
            return None
        reason = interval.fence_reason()
        if reason:
            self.close(principal, reason=reason)
            raise SpeechSessionRefused(reason)
        return interval

    # ----------------------------------------------------------------- close

    def close(self, principal: Any, *, reason: str = "browser_mic_closed") -> str:
        """Close this identity's interval; explicit stop cancels and closes.

        The generation is retired even when there is NO interval to pop: an open
        may still be mid-admission, and retiring here is what makes that open see
        it lost and cancel its own parent.
        """
        identity = _identity(principal)
        with self._lock:
            interval = self._intervals.pop(identity, None)
            self._generation.retire()
        if interval is None:
            return ""
        interval.close(reason)
        log.info("browser open mic closed: %s", reason)
        return str(interval.handle)

    def live(self, principal: Any) -> Optional[BrowserMicInterval]:
        with self._lock:
            return self._intervals.get(_identity(principal))

    def reset(self) -> None:
        """Drop every interval (test isolation and runtime shutdown)."""
        with self._lock:
            intervals = list(self._intervals.values())
            self._intervals.clear()
            # An open still mid-admission must also lose: a reset ends every
            # authority epoch this registry has issued.
            self._generation.retire()
        for interval in intervals:
            interval.close("browser_mic_reset")


def _identity(principal: Any) -> str:
    """The authenticated identity an interval is bound to.

    Derived from the route principal ONLY. A client-supplied identity or parent id
    never reaches this function.
    """
    if principal is None:
        raise SpeechSessionRefused(BROWSER_HANDLE_REFUSED)
    name = str(getattr(getattr(principal, "name", ""), "value", getattr(principal, "name", "")))
    identity = str(getattr(principal, "identity", "") or "")
    if not identity or name in ("", "none"):
        raise SpeechSessionRefused(BROWSER_HANDLE_REFUSED)
    return f"{name}:{identity}"


_SESSIONS = BrowserMicSessions()


def browser_mic_sessions() -> BrowserMicSessions:
    """The one device-local registry of open-mic intervals."""
    return _SESSIONS


__all__ = [
    "BROWSER_CEILING_SECONDS",
    "BROWSER_CHILD_BUDGET",
    "BROWSER_INACTIVITY_SECONDS",
    "BrowserMicInterval",
    "BrowserMicSessions",
    "MIC_INTERVAL_CLOSED",
    "browser_mic_sessions",
]
