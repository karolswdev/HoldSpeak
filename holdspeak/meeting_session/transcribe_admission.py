"""Admitted meeting transcription: one child per interval (HS-131-09).

Meeting transcription runs under the EXISTING ``meeting.session`` parent
HS-131-08 already admits — never a second parent and never a dictation session.
The plan's transcription capability names the LOCAL WHISPER deployment, so a
transcription child can never be mistaken for the leg the analysis prompt runs
on, and an interval with no live parent is dropped before Whisper.
"""

from __future__ import annotations

import math
from typing import Any

from .intel_plan import (
    CAPABILITY_NOT_PLANNED,
    CAPABILITY_WHISPER_PRELOAD,
    CAPABILITY_WHISPER_TRANSCRIBE,
)

# Sol Amendment 6: a transcription-bearing session spends ONE child per
# transcription interval, so the advertised 12-hour session would
# deterministically exhaust a 4096 allocation (4320 intervals) before any intel
# child ran. Transcription therefore buys its own headroom explicitly.
TRANSCRIPTION_INTERVAL_SECONDS = 10.0
TRANSCRIPTION_BUDGET_HEADROOM = 2
#: The named refusal a dropped transcription interval reports.
TRANSCRIPTION_NOT_ADMITTED = "meeting_transcription_not_admitted"


def session_child_budget(
    *,
    transcription: bool,
    session_seconds: float,
    interval_seconds: float = TRANSCRIPTION_INTERVAL_SECONDS,
    intelligence_budget: int,
) -> int:
    """The frozen child allocation for one live meeting session.

    Sol Amendment 6, verbatim: a transcription-bearing plan adds
    ``ceil(session_max_duration / TRANSCRIBE_INTERVAL) + 2`` children to the 4096
    intelligence allocation — 8418 at 10 s over 12 h.
    """
    if not transcription:
        return int(intelligence_budget)
    intervals = math.ceil(max(0.0, float(session_seconds)) / max(0.001, float(interval_seconds)))
    return int(intelligence_budget) + int(intervals) + TRANSCRIPTION_BUDGET_HEADROOM


class TranscribeAdmissionMixin:
    """The session-side handle each transcription interval dispatches under."""

    def _transcription_admission(self) -> Any:
        """Returns ``None`` when no live parent remains — the caller then drops
        the interval BEFORE Whisper (never an unadmitted fallback)."""
        plan, parent = self._intel_plan, self._intel_parent
        if plan is None or parent is None or getattr(self, "_intel_closed", False):
            self._transcription_refusal = (
                self._transcription_refusal or TRANSCRIPTION_NOT_ADMITTED
            )
            return None
        if not plan.has(CAPABILITY_WHISPER_TRANSCRIBE):
            self._transcription_refusal = CAPABILITY_NOT_PLANNED
            return None
        from ..speech_session.transcription import TranscriptionAdmission

        return TranscriptionAdmission(
            broker=self._intel_broker(),
            principal=self.intel_principal,
            plan=plan,
            parent=parent,
            capability=CAPABILITY_WHISPER_TRANSCRIBE,
            preload_capability=CAPABILITY_WHISPER_PRELOAD,
        )


__all__ = [
    "TRANSCRIPTION_BUDGET_HEADROOM",
    "TRANSCRIPTION_INTERVAL_SECONDS",
    "TRANSCRIPTION_NOT_ADMITTED",
    "TranscribeAdmissionMixin",
    "session_child_budget",
]
