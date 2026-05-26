"""Tests for the Settings/load_settings config layer."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bridge import Settings


def _kwargs(**overrides):
    """Required-field defaults so each test only specifies what it cares about."""
    base = {
        "holdspeak_host": "127.0.0.1",
        "holdspeak_port": 12345,
        "holdspeak_psk": "abc123",
        "device_id": "aipi-test",
    }
    base.update(overrides)
    return base


def test_settings_rejects_empty_psk():
    """Empty HOLDSPEAK_PSK should fail at config load, not silently flow
    through to a downstream Hello validation error."""
    with pytest.raises(ValidationError, match="must not be empty"):
        Settings(_env_file=None, **_kwargs(holdspeak_psk=""))  # type: ignore[arg-type]


def test_settings_normalises_log_level_to_upper():
    s = Settings(_env_file=None, **_kwargs(log_level="debug"))  # type: ignore[arg-type]
    assert s.log_level == "DEBUG"


def test_settings_defaults_label_to_device_id_when_blank():
    s = Settings(_env_file=None, **_kwargs(device_label=""))  # type: ignore[arg-type]
    assert s.device_label == s.device_id == "aipi-test"


def test_settings_keeps_explicit_label():
    s = Settings(  # type: ignore[arg-type]
        _env_file=None, **_kwargs(device_id="aipi-x", device_label="Living Room")
    )
    assert s.device_label == "Living Room"


def test_settings_accepts_audio_monitor_command():
    s = Settings(  # type: ignore[arg-type]
        _env_file=None,
        **_kwargs(audio_monitor_cmd="aplay -q -f S16_LE -r 16000 -c 1 -t raw -"),
    )

    assert s.audio_monitor_cmd.startswith("aplay")


def test_settings_accepts_companion_poll_interval():
    s = Settings(_env_file=None, **_kwargs(companion_poll_interval_s=0.75))  # type: ignore[arg-type]

    assert s.companion_poll_interval_s == 0.75
