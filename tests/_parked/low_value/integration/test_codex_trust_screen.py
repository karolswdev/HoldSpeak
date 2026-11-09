# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_codex_trust_screen.py to restore.

# ruff: noqa


# --- test_the_redraw_keeps_the_capture: P2: tests the test file's own redraw() helper against its capture, not the hub
def test_the_redraw_keeps_the_capture() -> None:
    assert redraw(CAPTURED_WORKTREE, CAPTURED_ROOT) == CAPTURED.read_text(encoding="utf-8")
