# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_attention.py to restore.

# ruff: noqa


# --- TestRanking::test_the_five_classes_in_the_ratified_order: P1: asserts a constant tuple; the next test checks the real ranking
# (was a method of class TestRanking)
def test_the_five_classes_in_the_ratified_order(self) -> None:
    assert RANK_CLASSES == ("overdue", "due_today", "not_run", "no_due_date", "waiting")
