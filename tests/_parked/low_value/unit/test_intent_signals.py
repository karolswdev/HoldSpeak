# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intent_signals.py to restore.

# ruff: noqa


# --- test_extract_intent_signals_returns_all_supported_intents: P6: asserts the score dict has the constant's keys, not a score
def test_extract_intent_signals_returns_all_supported_intents() -> None:
    scores = extract_intent_signals("Architecture review for API schema and latency.")
    assert set(scores.keys()) == set(SUPPORTED_INTENTS)
