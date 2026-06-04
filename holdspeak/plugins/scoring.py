"""Typed multi-label scoring + transition helpers built on the existing
deterministic signal extractor and router primitives. HS-2-03 / spec §9.3.

HS-36-05 adds an optional `probe`: an LLM-assisted per-segment intent probe
(`segment_probe.SegmentProbe`) whose confidences are merged element-wise (max) with the
deterministic lexical scores, so a brief/paraphrased intent the keyword scorer misses
can still clear the threshold. With `probe=None` the result is byte-identical to the
lexical-only path, so the existing router/dispatch/pipeline tests are unaffected.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

from .contracts import IntentScore, IntentTransition, IntentWindow
from .router import (
    DEFAULT_HYSTERESIS,
    DEFAULT_INTENT_THRESHOLD,
    normalize_intent_scores,
    select_active_intents,
)
from .segment_probe import SegmentProbe
from .signals import extract_intent_signals


def score_window(
    window: IntentWindow,
    *,
    threshold: float = DEFAULT_INTENT_THRESHOLD,
    probe: Optional[SegmentProbe] = None,
) -> IntentScore:
    """Multi-label score one rolling window (MIR-F-001, MIR-F-002).

    When `probe` is supplied, its per-intent confidences are merged (max) over the
    lexical scores — the probe can only *raise* an intent, never suppress one. A probe
    that raises or returns nothing leaves the lexical scores intact (graceful fallback).
    """
    raw = extract_intent_signals(window.transcript, tags=list(window.tags))
    normalized = normalize_intent_scores(raw)
    if probe is not None:
        try:
            probed = probe(window.transcript) or {}
        except Exception:
            probed = {}
        for intent, conf in probed.items():
            if intent in normalized:
                try:
                    bounded = min(1.0, max(0.0, float(conf)))
                except Exception:
                    continue
                normalized[intent] = max(normalized[intent], bounded)
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
    probe: Optional[SegmentProbe] = None,
) -> list[IntentScore]:
    """Score a sequence of windows in document order."""
    return [score_window(window, threshold=threshold, probe=probe) for window in windows]


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
