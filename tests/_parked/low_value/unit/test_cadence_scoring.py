# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_cadence_scoring.py to restore.

# ruff: noqa


# --- test_deterministic_with_injected_now: P1: scores the same loop twice with the same clock and compares
def test_deterministic_with_injected_now():
    loop = _loop(priority="normal", created_at="2026-06-20T10:00:00")
    a = score_loop(loop, now=NOW)
    b = score_loop(loop, now=NOW)
    assert a.total == b.total
