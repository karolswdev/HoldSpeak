"""Typed contracts for the DIR-01 dictation pipeline.

Defined in `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §6.4. Stage
code consumes/produces these types; the pipeline executor (HS-1-03)
chains stages by passing `Utterance` + the prior `StageResult`s into
each `Transducer.run`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

# `ProjectContext` is intentionally typed as a plain dict here. The
# producing module (`holdspeak/plugins/project_detector.py`) returns a
# context dict; HS-1-06 (kb-enricher) reads keys off it. A stronger
# dataclass alias can land later without breaking this contract.
ProjectContext = dict[str, Any]


@dataclass(frozen=True)
class Utterance:
    """One post-Whisper, post-TextProcessor utterance entering the pipeline."""

    raw_text: str
    audio_duration_s: float
    transcribed_at: datetime
    project: ProjectContext | None = None


@dataclass(frozen=True)
class IntentTag:
    """Router output: which block matched, with what confidence + extras."""

    matched: bool
    block_id: str | None
    confidence: float
    raw_label: str | None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StageResult:
    """One stage's output. Pipeline accumulates these in order."""

    stage_id: str
    text: str
    intent: IntentTag | None
    elapsed_ms: float
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Transducer(Protocol):
    """Pluggable transcript-in, transcript-out stage."""

    id: str
    version: str
    requires_llm: bool

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult: ...
