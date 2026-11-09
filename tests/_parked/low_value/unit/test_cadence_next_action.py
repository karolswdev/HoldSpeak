# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_cadence_next_action.py to restore.

# ruff: noqa


# --- test_generator_is_deterministic: P1: calls a pure function twice and compares; cannot fail
def test_generator_is_deterministic():
    loop = _loop(owner="Karol")
    assert generate_next_action(loop).kind == generate_next_action(loop).kind
