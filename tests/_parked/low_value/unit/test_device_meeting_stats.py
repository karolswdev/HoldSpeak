# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_device_meeting_stats.py to restore.

# ruff: noqa


# --- test_cycle_order_constant: P1: asserts a tuple constant equals itself spelled out; the cycle test above walks the order
def test_cycle_order_constant():
    assert CYCLE_ORDER == (VIEW_NUMBERS, VIEW_SPEAKERS, VIEW_INTEL)
