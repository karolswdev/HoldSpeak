# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_version_ssot.py to restore.

# ruff: noqa


# --- test_version_is_not_the_unknown_fallback: P5: the pyproject-match test already fails on the fallback
def test_version_is_not_the_unknown_fallback() -> None:
    # Running the test suite means the package is importable; the fallback
    # placeholder should never be what we resolve to.
    assert holdspeak.__version__ != "0.0.0+unknown"
