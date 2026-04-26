"""Unit tests for the typed scoring + transition helpers (HS-2-03 / spec §9.3)."""

from __future__ import annotations

from holdspeak.intent_timeline import build_intent_windows
from holdspeak.plugins.contracts import IntentScore, IntentTransition, IntentWindow
from holdspeak.plugins.scoring import (
    iter_intent_transitions,
    score_window,
    score_windows,
)


def _window(window_id: str, transcript: str, *, tags: list[str] | None = None) -> IntentWindow:
    return IntentWindow(
        window_id=window_id,
        meeting_id="m1",
        start_seconds=0.0,
        end_seconds=30.0,
        transcript=transcript,
        tags=list(tags or []),
    )


def test_score_window_returns_typed_intent_score_with_window_id() -> None:
    window = _window(
        "m1:w0001",
        "We need an architecture design review for API schema and service interface.",
    )

    score = score_window(window, threshold=0.6)

    assert isinstance(score, IntentScore)
    assert score.window_id == "m1:w0001"
    assert score.threshold == 0.6
    assert set(score.scores.keys()) == {
        "architecture",
        "delivery",
        "product",
        "incident",
        "comms",
    }
    assert score.scores["architecture"] > 0.0
    assert score.scores["architecture"] >= score.scores["delivery"]


def test_score_window_supports_multi_label_above_threshold_mir_f_002() -> None:
    # Transcript carrying both architecture and incident keywords above a permissive gate.
    window = _window(
        "m1:w0002",
        "Architecture design ADR for API schema; incident postmortem covered "
        "outage severity rollback mitigation and blast radius.",
    )

    score = score_window(window, threshold=0.4)
    above = score.labels_above_threshold()

    # MIR-F-002 / MIR-F-004: more than one label above threshold for a single window.
    assert len(above) >= 2
    assert "architecture" in above
    assert "incident" in above


def test_score_window_tag_boost_promotes_intent() -> None:
    base = score_window(_window("m1:w0003", "Quick recap and mitigation check."), threshold=0.5)
    boosted = score_window(
        _window("m1:w0003", "Quick recap and mitigation check.", tags=["incident"]),
        threshold=0.5,
    )

    assert boosted.scores["incident"] >= base.scores["incident"]


def test_score_windows_preserves_input_order() -> None:
    windows = [
        _window("m1:w0001", "Architecture design review."),
        _window("m1:w0002", "Sprint milestone owner deadline."),
        _window("m1:w0003", "Customer feedback on the new feature scope."),
    ]

    scores = score_windows(windows, threshold=0.4)

    assert [s.window_id for s in scores] == ["m1:w0001", "m1:w0002", "m1:w0003"]
    assert all(isinstance(s, IntentScore) for s in scores)


def test_iter_intent_transitions_emits_typed_events_on_change() -> None:
    scores = [
        IntentScore(
            window_id="w0",
            scores={
                "architecture": 0.81,
                "delivery": 0.10,
                "product": 0.10,
                "incident": 0.10,
                "comms": 0.10,
            },
            threshold=0.6,
        ),
        IntentScore(
            window_id="w1",
            scores={
                "architecture": 0.81,
                "delivery": 0.72,
                "product": 0.10,
                "incident": 0.10,
                "comms": 0.10,
            },
            threshold=0.6,
        ),
        IntentScore(
            window_id="w2",
            scores={
                "architecture": 0.10,
                "delivery": 0.81,
                "product": 0.10,
                "incident": 0.10,
                "comms": 0.10,
            },
            threshold=0.6,
        ),
    ]

    transitions = iter_intent_transitions(scores, hysteresis=0.0)

    assert all(isinstance(t, IntentTransition) for t in transitions)
    assert [t.window_id for t in transitions] == ["w0", "w1", "w2"]
    assert transitions[0].added == ["architecture"]
    assert transitions[0].removed == []
    assert transitions[1].added == ["delivery"]
    assert transitions[1].removed == []
    assert transitions[2].added == []
    assert transitions[2].removed == ["architecture"]


def test_iter_intent_transitions_hysteresis_suppresses_oscillation_mir_f_005() -> None:
    # Architecture stays just above hysteresis floor in window 1, so it should NOT drop.
    scores = [
        IntentScore(
            window_id="w0",
            scores={
                "architecture": 0.71,
                "delivery": 0.10,
                "product": 0.10,
                "incident": 0.10,
                "comms": 0.10,
            },
            threshold=0.7,
        ),
        IntentScore(
            window_id="w1",
            scores={
                "architecture": 0.66,  # below threshold, but within 0.05 hysteresis
                "delivery": 0.10,
                "product": 0.10,
                "incident": 0.10,
                "comms": 0.10,
            },
            threshold=0.7,
        ),
    ]

    transitions = iter_intent_transitions(scores, hysteresis=0.05)

    # Only the first window should have produced a transition (architecture entering active);
    # the dip in w1 stays inside the hysteresis band so the active set is unchanged.
    assert len(transitions) == 1
    assert transitions[0].window_id == "w0"
    assert transitions[0].added == ["architecture"]


def test_iter_intent_transitions_empty_input_returns_empty() -> None:
    assert iter_intent_transitions([]) == []


def test_score_windows_works_end_to_end_with_build_intent_windows() -> None:
    segments = [
        {"start_time": 0.0, "end_time": 12.0, "text": "Architecture design review for API schema."},
        {"start_time": 14.0, "end_time": 28.0, "text": "Sprint milestone owner deadline planning."},
        {"start_time": 33.0, "end_time": 47.0, "text": "Incident outage severity mitigation rollback."},
    ]

    windows = build_intent_windows(segments, meeting_id="m1", window_seconds=20.0, step_seconds=20.0)
    scores = score_windows(windows, threshold=0.4)

    assert len(scores) == len(windows)
    # Each window should be classified into at least one intent given the keyword density.
    classified = sum(1 for s in scores if s.labels_above_threshold())
    assert classified >= 2
