# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_config_intent_router.py to restore.

# ruff: noqa


# --- test_intent_router_defaults_are_on: P1: asserts six config defaults
def test_intent_router_defaults_are_on() -> None:
    config = MeetingConfig()
    # PHILO-15 08 (B02, strong defaults): the extractor chain is on by default.
    assert config.intent_router_enabled is True
    assert config.intent_window_seconds == 90
    assert config.intent_step_seconds == 30
    assert config.intent_score_threshold == 0.6
    assert config.intent_hysteresis_windows == 1
    assert config.routing_profile == "balanced"
