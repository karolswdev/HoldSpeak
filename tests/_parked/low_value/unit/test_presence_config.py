# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_presence_config.py to restore.

# ruff: noqa


# --- test_presence_defaults_off_and_round_trips: P1/P3: a default is False and Config saves and loads a bool
def test_presence_defaults_off_and_round_trips(isolated_config) -> None:
    assert Config().presence.enabled is False
    cfg = Config()
    cfg.presence.enabled = True
    cfg.save(isolated_config)
    assert json.loads(isolated_config.read_text())["presence"]["enabled"] is True
    assert Config.load(isolated_config).presence.enabled is True
