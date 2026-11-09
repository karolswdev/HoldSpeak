# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_meeting_overlap.py to restore.

# ruff: noqa


# --- test_overlap_seconds_default: P1: asserts a private default equals 1.5
def test_overlap_seconds_default() -> None:
    session = _make_session()
    # 1.5 s default — matches the comment in __init__.
    assert session._overlap_tail_seconds == 1.5
