# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_actuator_executor.py to restore.

# ruff: noqa


# --- test_config_actuator_policy_defaults_safe: P1: asserts two config default literals
def test_config_actuator_policy_defaults_safe() -> None:
    # HS-139-08: permissive defaults (owner ruling: ledger-not-gate).
    from holdspeak.config import MeetingConfig

    cfg = MeetingConfig()
    assert cfg.allow_actuators is True
    assert cfg.allowed_actuators == ["*"]
