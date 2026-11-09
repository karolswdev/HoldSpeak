# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_philo15_decisions_day_one.py to restore.

# ruff: noqa


# --- test_the_summary_schema_asks_for_decisions: P1/P6: checks a schema constant contains the word decisions; the parser and run tests prove decisions arrive
def test_the_summary_schema_asks_for_decisions() -> None:
    from holdspeak.intel.parsing import INTEL_JSON_SCHEMA, INTEL_SCHEMA, _json_only_messages

    assert "decisions" in INTEL_SCHEMA
    assert "decisions" in INTEL_JSON_SCHEMA["required"]
    prompt = _json_only_messages("t")[1]["content"]
    assert "decisions" in prompt
