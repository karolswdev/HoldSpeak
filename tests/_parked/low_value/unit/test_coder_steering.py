# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_coder_steering.py to restore.

# ruff: noqa


# --- test_peek_invokes_capture_pane_with_the_pinned_flags: P7: pins the exact tmux argv; the peek tests above prove the lines that come back
def test_peek_invokes_capture_pane_with_the_pinned_flags() -> None:
    run = _runner_returning(_completed("x"))
    peek_pane("%5", lines=50, runner=run)
    assert run.calls == [
        ["tmux", "capture-pane", "-p", "-e", "-t", "%5", "-S", "-50"]
    ]
