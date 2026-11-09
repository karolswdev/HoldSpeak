# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_hs172_loop_wire.py to restore.

# ruff: noqa


# --- TestAutoIntelTrigger::test_default_is_every: P1: a config default equals its literal
# (was a method of class TestAutoIntelTrigger)
def test_default_is_every(self) -> None:
    """Default intelligence_auto is every (owner ruling 2026-10-05)."""
    from holdspeak.config.meeting import MeetingConfig
    cfg = MeetingConfig()
    assert cfg.intelligence_auto == "every"
