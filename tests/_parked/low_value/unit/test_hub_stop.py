# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_hub_stop.py to restore.

# ruff: noqa


# --- test_the_stop_bounds_are_seconds: P1: asserts two module constants are <= 5
def test_the_stop_bounds_are_seconds() -> None:
    assert memory_conductor.STOP_JOIN_SECONDS <= 5.0
    assert intel_queue_conductor.STOP_JOIN_SECONDS <= 5.0
