# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_streaming_mic_honesty.py to restore.

# ruff: noqa


# --- test_the_floor_is_claimed_on_the_shared_lease_constant: P1: asserts a constant equals the test's copy of it
def test_the_floor_is_claimed_on_the_shared_lease_constant(dictate):
    """The claim and the heartbeat read the same number, so they cannot drift."""
    clock = _Clock()
    floor = VoiceTypingSession(clock=clock)
    seen: list[str | None] = []

    def between() -> None:
        seen.append(floor.active_owner)

    dictate(_stream(2), floor=floor, between=between)

    assert seen[0] == "browser_mic"
    assert voice_support.BROWSER_FLOOR_LEASE_SECONDS == TEST_LEASE_SECONDS
