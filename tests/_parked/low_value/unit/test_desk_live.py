# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_desk_live.py to restore.

# ruff: noqa


# --- test_transcript_pass_is_a_registered_frame: P1: asserts a name is in a constant set; the bracket test above already sends the frame
def test_transcript_pass_is_a_registered_frame() -> None:
    assert "transcript_pass" in RUNTIME_FRAME_TYPES
