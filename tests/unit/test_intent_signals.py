from __future__ import annotations

from holdspeak.plugins.signals import SUPPORTED_INTENTS, extract_intent_signals


def test_extract_intent_signals_returns_all_supported_intents() -> None:
    scores = extract_intent_signals("Architecture review for API schema and latency.")
    assert set(scores.keys()) == set(SUPPORTED_INTENTS)


def test_extract_intent_signals_detects_architecture_vs_delivery() -> None:
    scores = extract_intent_signals(
        "We need an architecture design review for API schema and service interface."
    )
    assert scores["architecture"] > 0.0
    assert scores["architecture"] > scores["delivery"]


def test_extract_intent_signals_tag_boost_applies() -> None:
    scores = extract_intent_signals(
        "Quick recap and mitigation check.",
        tags=["incident"],
    )
    assert scores["incident"] > 0.0


def test_extract_intent_signals_empty_input_is_zeroed() -> None:
    scores = extract_intent_signals("", tags=[])
    assert all(value == 0.0 for value in scores.values())
