"""HS-2-09 / spec §9.9 — MIR-01 routing config knobs on MeetingConfig."""

from __future__ import annotations

import pytest

from holdspeak.config import MeetingConfig


def test_intent_router_defaults_are_conservative() -> None:
    config = MeetingConfig()
    assert config.intent_router_enabled is False  # opt-in
    assert config.intent_window_seconds == 90
    assert config.intent_step_seconds == 30
    assert config.intent_score_threshold == 0.6
    assert config.intent_hysteresis_windows == 1
    assert config.plugin_profile == "balanced"


def test_intent_hysteresis_helper_converts_windows_to_float() -> None:
    assert MeetingConfig(intent_hysteresis_windows=0).intent_hysteresis() == 0.0
    assert MeetingConfig(intent_hysteresis_windows=1).intent_hysteresis() == pytest.approx(0.05)
    assert MeetingConfig(intent_hysteresis_windows=4).intent_hysteresis() == pytest.approx(0.20)
    # Cap at 0.5 so hysteresis can't swallow more than half the score range.
    assert MeetingConfig(intent_hysteresis_windows=20).intent_hysteresis() == pytest.approx(0.5)


def test_intent_window_seconds_must_be_positive() -> None:
    with pytest.raises(ValueError, match="intent_window_seconds must be > 0"):
        MeetingConfig(intent_window_seconds=0)
    with pytest.raises(ValueError):
        MeetingConfig(intent_window_seconds=-1)


def test_intent_step_seconds_must_be_positive() -> None:
    with pytest.raises(ValueError, match="intent_step_seconds must be > 0"):
        MeetingConfig(intent_step_seconds=0)


def test_intent_score_threshold_must_be_in_unit_interval() -> None:
    MeetingConfig(intent_score_threshold=0.0)  # OK at boundary
    MeetingConfig(intent_score_threshold=1.0)  # OK at boundary
    with pytest.raises(ValueError, match=r"intent_score_threshold must be in \[0\.0, 1\.0\]"):
        MeetingConfig(intent_score_threshold=-0.1)
    with pytest.raises(ValueError):
        MeetingConfig(intent_score_threshold=1.1)


def test_intent_hysteresis_windows_must_be_non_negative() -> None:
    MeetingConfig(intent_hysteresis_windows=0)  # OK
    with pytest.raises(ValueError, match="intent_hysteresis_windows must be >= 0"):
        MeetingConfig(intent_hysteresis_windows=-1)


def test_plugin_profile_must_be_non_empty_string() -> None:
    MeetingConfig(plugin_profile="balanced")
    MeetingConfig(plugin_profile="architect")
    with pytest.raises(ValueError, match="plugin_profile must be a non-empty string"):
        MeetingConfig(plugin_profile="")
    with pytest.raises(ValueError):
        MeetingConfig(plugin_profile="   ")


def test_intent_router_fields_round_trip_via_to_dict() -> None:
    from dataclasses import asdict

    config = MeetingConfig(
        intent_router_enabled=True,
        intent_window_seconds=60,
        intent_step_seconds=20,
        intent_score_threshold=0.55,
        intent_hysteresis_windows=2,
        plugin_profile="architect",
    )
    payload = asdict(config)
    assert payload["intent_router_enabled"] is True
    assert payload["intent_window_seconds"] == 60
    assert payload["intent_step_seconds"] == 20
    assert payload["intent_score_threshold"] == 0.55
    assert payload["intent_hysteresis_windows"] == 2
    assert payload["plugin_profile"] == "architect"
