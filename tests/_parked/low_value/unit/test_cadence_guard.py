# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_cadence_guard.py to restore.

# ruff: noqa


# --- test_cadence_is_off_by_default: P1: asserts a config default
def test_cadence_is_off_by_default():
    assert Config().cadence.enabled is False
