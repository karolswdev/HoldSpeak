"""Voice-typing session ownership.

A single ``VoiceTypingSession`` arbitrates between callers that
want to drive a hold-to-record session against an
:class:`AudioSource`. It enforces the phase-14 v1 rule of one
active voice-typing recording at a time across all devices and
the local hotkey: when one owner already holds the session,
:meth:`begin` returns ``False`` instead of starting a parallel
recording.

The session also encapsulates the start/stop calls on the source
so the caller does not have to remember to wrap them with the
ownership lock.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import numpy as np

from .audio import AudioSource
from .logging_config import get_logger

log = get_logger("voice_typing.session")


class VoiceTypingSession:
    """One-at-a-time audio-floor arbiter.

    The single owner model for all capture in the web runtime: the
    hotkey and device voice-typing paths claim the floor via
    :meth:`begin` (which also owns the :class:`AudioSource` lifecycle
    — ``begin`` starts it, ``end`` stops it), while a meeting — which
    drives its own multi-stream recorder and can't use the
    single-source begin/end model — claims it via :meth:`acquire` /
    :meth:`release`. All three share one lock, so a meeting and a
    voice-typing session can never hold the mic at once; first to
    acquire wins until it releases.
    """

    def __init__(self, *, clock: Optional[Callable[[], float]] = None) -> None:
        self._lock = threading.Lock()
        self._owner: Optional[str] = None
        self._source: Optional[AudioSource] = None
        # HS-112-06: an owner that cannot be trusted to release (the browser's
        # open mic — a tab can vanish) claims on a LEASE. When the lease is not
        # renewed the floor frees itself, so a closed tab can never wedge the
        # hotkey. Owners in the process (hotkey, meeting, wake, devices) claim
        # with no lease and behave exactly as before.
        self._lease_expires: Optional[float] = None
        self._clock = clock or time.monotonic

    def _expire_locked(self) -> None:
        """Drop a leased claim whose lease has run out. Call under the lock."""
        if self._lease_expires is None or self._owner is None:
            return
        if self._clock() < self._lease_expires:
            return
        expired = self._owner
        self._owner = None
        self._source = None
        self._lease_expires = None
        log.info("audio_floor_lease_expired", extra={"owner": expired})

    @property
    def is_active(self) -> bool:
        with self._lock:
            self._expire_locked()
            return self._owner is not None

    @property
    def active_owner(self) -> Optional[str]:
        with self._lock:
            self._expire_locked()
            return self._owner

    def renew(self, owner: str, lease_seconds: float) -> bool:
        """Extend a leased claim. ``False`` when ``owner`` no longer holds it.

        The leased owner's heartbeat: a browser holding the floor for its
        open mic calls this on an interval. A ``False`` answer is the honest
        signal that the floor was lost (the lease lapsed, or the claim was
        never made) — the caller must stop capturing.
        """
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        with self._lock:
            self._expire_locked()
            if self._owner != owner or self._lease_expires is None:
                return False
            self._lease_expires = self._clock() + lease_seconds
            return True

    def acquire(self, owner: str, *, lease_seconds: Optional[float] = None) -> bool:
        """Claim the audio floor *without* binding an :class:`AudioSource`.

        For owners that drive their own capture (e.g. a meeting's
        multi-stream ``MeetingRecorder`` capturing mic + system + devices
        concurrently, which doesn't fit the single-source ``begin``/``end``
        hold-to-record model). The claim shares the same one-at-a-time lock
        as :meth:`begin`, so once a meeting holds the floor the hotkey and
        device voice-typing paths — which ``begin`` through this same
        instance — are rejected, and vice versa. One owner model, defined
        precedence: first to hold the floor keeps it until they release.

        Returns ``True`` if the caller now owns the floor; ``False`` if
        another owner already holds it (silent, like :meth:`begin`).

        ``lease_seconds`` claims on a lease (HS-112-06): the claim frees
        itself if it is not renewed in time. Re-claiming as the SAME leased
        owner renews rather than refusing, so a client that missed a
        heartbeat recovers without dropping the floor to a third party.
        """
        if not owner:
            raise ValueError("owner must be non-empty")
        if lease_seconds is not None and lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")

        with self._lock:
            self._expire_locked()
            if self._owner is not None:
                if self._owner == owner and self._lease_expires is not None:
                    if lease_seconds is not None:
                        self._lease_expires = self._clock() + lease_seconds
                    return True
                log.info(
                    "audio_floor_acquire_rejected",
                    extra={"owner": owner, "active_owner": self._owner},
                )
                return False
            self._owner = owner
            self._source = None
            self._lease_expires = (
                self._clock() + lease_seconds if lease_seconds is not None else None
            )

        log.info(
            "audio_floor_acquire",
            extra={"owner": owner, "lease_seconds": lease_seconds},
        )
        return True

    def release(self, owner: str) -> None:
        """Release a floor claimed via :meth:`acquire`.

        No-op when ``owner`` does not match the active owner (so it is safe
        to call unconditionally on any meeting-end path). Does not stop a
        source — :meth:`acquire` never bound one.
        """
        with self._lock:
            self._expire_locked()
            if self._owner != owner:
                return
            self._owner = None
            self._source = None
            self._lease_expires = None

        log.info("audio_floor_release", extra={"owner": owner})

    def begin(self, source: AudioSource, *, owner: str) -> bool:
        """Try to claim the session and start ``source``.

        Returns ``True`` if the caller now owns the session;
        ``False`` if another owner is already active. ``False``
        is silent — the active session is left untouched and no
        log is emitted at higher than info severity.
        """
        if not owner:
            raise ValueError("owner must be non-empty")

        with self._lock:
            self._expire_locked()
            if self._owner is not None:
                log.info(
                    "voice_typing_begin_rejected",
                    extra={"owner": owner, "active_owner": self._owner},
                )
                return False
            self._owner = owner
            self._source = source
            self._lease_expires = None

        try:
            source.start_recording()
        except Exception:
            with self._lock:
                self._owner = None
                self._source = None
                self._lease_expires = None
            raise

        log.info("voice_typing_begin", extra={"owner": owner})
        return True

    def end(self, owner: str) -> Optional[np.ndarray]:
        """Stop the session and return its audio.

        Returns the captured ndarray if ``owner`` matches the
        active session. Returns ``None`` (no exception) when:

        - no session is active, or
        - the active session is held by a *different* owner.

        Both conditions are normal in racing flows (e.g., a
        hotkey release arrives after a device session already
        ran to completion) and should not blow up the caller.
        """
        with self._lock:
            self._expire_locked()
            if self._owner is None:
                return None
            if self._owner != owner:
                log.info(
                    "voice_typing_end_owner_mismatch",
                    extra={"requesting_owner": owner, "active_owner": self._owner},
                )
                return None
            source = self._source
            self._owner = None
            self._source = None
            self._lease_expires = None

        if source is None:
            return None

        audio = source.stop_recording()
        log.info("voice_typing_end", extra={"owner": owner, "samples": int(getattr(audio, "size", 0))})
        return audio

    def cancel(self, owner: str) -> None:
        """Drop the session without returning audio.

        Useful for disconnect cleanup paths where the audio is
        being discarded anyway. No-op when the active owner does
        not match.
        """
        with self._lock:
            self._expire_locked()
            if self._owner != owner:
                return
            source = self._source
            self._owner = None
            self._source = None
            self._lease_expires = None

        if source is not None:
            try:
                source.stop_recording()
            except Exception:
                pass


__all__ = ["VoiceTypingSession"]
