# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_native_surfaces_guard.py to restore.

# ruff: noqa


# --- test_ledger_is_closed: P1: asserts a constant set to {} in the same file equals {}
def test_ledger_is_closed() -> None:
    """HS-98-07: the seam is retired. The ledger only ever shrank and
    is now empty — reopening it would let the page grammar return."""
    assert ALLOWED == {}, "the Phase 98 conversion ledger never reopens"
