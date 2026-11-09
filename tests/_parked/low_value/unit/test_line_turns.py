# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_line_turns.py to restore.

# ruff: noqa


# --- test_the_default_times_are_the_designs: P1: asserts three default constants equal (1.5, 10.0, 25.0)
def test_the_default_times_are_the_designs() -> None:
    t = Timing()
    assert (t.first_fill, t.second_fill, t.give_up) == (1.5, 10.0, 25.0)
