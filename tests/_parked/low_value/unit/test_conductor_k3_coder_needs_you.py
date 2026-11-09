# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_conductor_k3_coder_needs_you.py to restore.

# ruff: noqa


# --- test_a_coder_is_a_coverage_kind: P1: asserts a string is in a constant tuple
def test_a_coder_is_a_coverage_kind() -> None:
    assert "coder" in COVERAGE_KINDS
