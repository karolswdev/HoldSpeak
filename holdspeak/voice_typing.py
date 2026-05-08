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
from typing import Optional

import numpy as np

from .audio import AudioSource
from .logging_config import get_logger

log = get_logger("voice_typing.session")


class VoiceTypingSession:
    """One-at-a-time voice typing arbiter.

    Hotkey-driven and device-driven callers share a single
    instance. The instance owns the lifecycle of whatever
    :class:`AudioSource` is passed to :meth:`begin`; ``begin``
    starts the source and ``end`` stops it.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._owner: Optional[str] = None
        self._source: Optional[AudioSource] = None

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._owner is not None

    @property
    def active_owner(self) -> Optional[str]:
        with self._lock:
            return self._owner

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
            if self._owner is not None:
                log.info(
                    "voice_typing_begin_rejected",
                    extra={"owner": owner, "active_owner": self._owner},
                )
                return False
            self._owner = owner
            self._source = source

        try:
            source.start_recording()
        except Exception:
            with self._lock:
                self._owner = None
                self._source = None
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
            if self._owner != owner:
                return
            source = self._source
            self._owner = None
            self._source = None

        if source is not None:
            try:
                source.stop_recording()
            except Exception:
                pass


__all__ = ["VoiceTypingSession"]
