# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_calendar_parser.py to restore.

# ruff: noqa


# --- test_horizon_constant_is_the_declared_two_week_window: P1: asserts HORIZON_DAYS == 14; the RRULE window test already proves the window
def test_horizon_constant_is_the_declared_two_week_window() -> None:
    assert HORIZON_DAYS == 14
