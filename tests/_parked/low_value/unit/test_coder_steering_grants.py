# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_coder_steering_grants.py to restore.

# ruff: noqa


# --- test_a_fresh_store_holds_zero_grants_fail_closed: P1: an empty dict starts empty
def test_a_fresh_store_holds_zero_grants_fail_closed() -> None:
    # A hub restart constructs this module fresh: nothing survives.
    assert active_grants() == {}
