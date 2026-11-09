# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intel_profile_resolution.py to restore.

# ruff: noqa


# --- test_config_round_trips_intel_profile_id: P1/P5: saves a literal field and loads it back; the settings-route round trip below covers the user path
def test_config_round_trips_intel_profile_id(tmp_path) -> None:
    from holdspeak.config import Config

    path = tmp_path / "config.json"
    cfg = Config()
    cfg.meeting.intel_profile_id = "p-43"
    cfg.save(path)
    assert Config.load(path).meeting.intel_profile_id == "p-43"
