# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_page_cores_guard.py to restore.

# ruff: noqa


# --- test_cores_exist: P6: asserts a directory exists and holds a file
def test_cores_exist() -> None:
    assert CORES.is_dir(), "the cores directory is the pattern's home"
    assert list(CORES.glob("*.tsx")), "at least one extracted core"
