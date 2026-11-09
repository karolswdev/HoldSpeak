# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_doctor_config_honesty.py to restore.

# ruff: noqa


# --- test_config_default_carries_current_version: P1: a default equals the constant it is set from
def test_config_default_carries_current_version() -> None:
    assert Config().config_version == CONFIG_VERSION
