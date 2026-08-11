"""The admitted hold session and its acquisition race (HS-131-09).

A desktop hold is one finite ``dictation.session``: admitted at the accepted
press (off the release-to-landed hot path), sealed on release, closed when its
bounded tail drains. Acquisition is guarded by a monotonic generation token, so a
release or an admission failure that wins the race cancels the parent instead of
leaving an orphan holding authority.
"""

from __future__ import annotations

import threading
from typing import Any

from ..logging_config import get_logger
from ..speech_session import (
    SessionGeneration,
    SpeechSessionRefused,
    admit_hold_session,
)

log = get_logger("web_runtime")


class HoldSessionMixin:
    # Sol Amendment 1: acquisition is not instantaneous. A release or an
    # admission failure that wins the race retires this generation; the loser
    # cancels the parent it admitted, tears the capture down, discards the audio.
    _hold_generation: Any = None
    _hold_state_lock: Any = None
    _hold_session: Any = None

    def _hold_state(self) -> tuple[Any, Any]:
        """Lazily bind the hold generation/lock onto whatever runtime hosts this."""
        if self._hold_generation is None:
            self._hold_generation = SessionGeneration()
            self._hold_state_lock = threading.Lock()
        return self._hold_generation, self._hold_state_lock

    def _admit_hold_session(self, token: int) -> Any:
        """Admit ONE ``dictation.session``, or return None with an honest status.

        The parent is admitted at the ACCEPTED press under the authenticated
        local-owner identity the delivery side already uses for a hold gesture. A
        stale token (release/stop already won) cancels it immediately.
        """
        generation, lock = self._hold_state()
        try:
            session = admit_hold_session(config_snapshot=self.config)
        except SpeechSessionRefused as exc:
            log.error("dictation session refused: %s", exc.reason)
            self._set_runtime_activity(
                "error",
                source="hotkey",
                label="Not admitted",
                detail="Dictation was not admitted.",
                last_event="dictation_session_refused",
                last_error=exc.reason,
            )
            return None
        except Exception as exc:
            log.error("dictation session admission failed: %s", type(exc).__name__)
            return None
        with lock:
            live = generation.is_live(token)
            if live:
                self._hold_session = session
        if not live:
            log.info("dictation session cancelled: release won the acquisition race")
            session.cancel_and_close()
            return None
        return session


__all__ = ["HoldSessionMixin"]
