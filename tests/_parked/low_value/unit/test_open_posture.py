# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_open_posture.py to restore.

# ruff: noqa


# --- test_fresh_config_defaults_yolo: P5: each asserts one default that test_fresh_config_load_from_empty_dir asserts together
def test_fresh_config_defaults_yolo():
    """A Config() with no on-disk file defaults to YOLO."""
    from holdspeak.config.core import Config

    config = Config()
    assert config.control_mode == "yolo"


# --- test_fresh_config_actuators_permissive: P5: each asserts one default that test_fresh_config_load_from_empty_dir asserts together
def test_fresh_config_actuators_permissive():
    """A fresh Config() has actuators on with a wildcard allowlist."""
    from holdspeak.config.core import Config

    config = Config()
    assert config.meeting.allow_actuators is True
    assert config.meeting.allowed_actuators == ["*"]


# --- test_fresh_config_webhook_hosts_permissive: P5: each asserts one default that test_fresh_config_load_from_empty_dir asserts together
def test_fresh_config_webhook_hosts_permissive():
    """A fresh Config() has a wildcard webhook host allowlist."""
    from holdspeak.config.core import Config

    config = Config()
    assert config.meeting.webhook_allowed_hosts == ["*"]
