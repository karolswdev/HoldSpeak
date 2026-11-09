# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_plugin_disable.py to restore.

# ruff: noqa


# --- test_skipped_is_a_known_status: P1: a status string is in a constant tuple; a config default is an empty list
def test_skipped_is_a_known_status() -> None:
    assert "skipped" in PLUGIN_RUN_STATUSES


# --- test_config_disabled_plugins_default_empty: P1: a status string is in a constant tuple; a config default is an empty list
def test_config_disabled_plugins_default_empty() -> None:
    assert MeetingConfig().disabled_plugins == []
