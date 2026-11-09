# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_core_path_smoke.py to restore.

# ruff: noqa


# --- test_core_path_smoke_assertion_is_not_vacuous: P2: tests the test (that a hard-coded wrong string lacks the words); no product code runs
def test_core_path_smoke_assertion_is_not_vacuous() -> None:
    """Mutation guard: the substring assertion *rejects* a wrong transcript, so a
    broken transcription path would turn the smoke test red (no backend needed)."""
    wrong = _normalize("Goodbye everyone, see you later.")
    assert "quick brown fox" not in wrong
    assert "lazy dog" not in wrong
