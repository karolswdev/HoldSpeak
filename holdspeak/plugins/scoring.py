"""Typed multi-label scoring + transition helpers built on the existing
deterministic signal extractor and router primitives. HS-2-03 / spec §9.3."""

from __future__ import annotations

from collections.abc import Iterable

from .contracts import IntentScore, IntentTransition, IntentWindow
from .router import (
    DEFAULT_HYSTERESIS,
    DEFAULT_INTENT_THRESHOLD,
    normalize_intent_scores,
    select_active_intents,
)
from .signals import extract_intent_signals


def score_window(
    window: IntentWindow,
    *,
    threshold: float = DEFAULT_INTENT_THRESHOLD,
) -> IntentScore:
    """Multi-label score one rolling window (MIR-F-001, MIR-F-002)."""
    raw = extract_intent_signals(window.transcript, tags=list(window.tags))
    normalized = normalize_intent_scores(raw)
    clamped_threshold = min(1.0, max(0.0, float(threshold)))
    return IntentScore(
        window_id=window.window_id,
        scores=dict(normalized),
        threshold=clamped_threshold,
    )


def score_windows(
    windows: Iterable[IntentWindow],
    *,
    threshold: float = DEFAULT_INTENT_THRESHOLD,
) -> list[IntentScore]:
    """Score a sequence of windows in document order."""
    return [score_window(window, threshold=threshold) for window in windows]


def iter_intent_transitions(
    scored_windows: Iterable[IntentScore],
    *,
    hysteresis: float = DEFAULT_HYSTERESIS,
) -> list[IntentTransition]:
    """Emit typed transitions when the active-intent set changes (MIR-F-005)."""
    transitions: list[IntentTransition] = []
    previous: list[str] = []
    for score in scored_windows:
        current = select_active_intents(
            score.scores,
            threshold=score.threshold,
            previous_intents=previous,
            hysteresis=hysteresis,
        )
        added = sorted(set(current) - set(previous))
        removed = sorted(set(previous) - set(current))
        if added or removed:
            transitions.append(
                IntentTransition(
                    window_id=score.window_id,
                    previous_active=list(previous),
                    current_active=list(current),
                    added=added,
                    removed=removed,
                )
            )
        previous = current
    return transitions
