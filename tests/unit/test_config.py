"""Comprehensive unit tests for the config module."""

from __future__ import annotations

import json
import pytest

from holdspeak.config import (
    Config,
    HotkeyConfig,
    ModelConfig,
    UIConfig,
    MeetingConfig,
    KEY_MAP,
    KEY_DISPLAY,
    get_available_keys,
)


def test_control_mode_round_trips_and_invalid_values_fail_to_neutral(tmp_path) -> None:
    path = tmp_path / "config.json"
    config = Config(control_mode="yolo")
    config.save(path)
    assert Config.load(path).control_mode == "yolo"


def test_thought_ai_target_round_trips_and_blank_inherits_this_device(tmp_path) -> None:
    path = tmp_path / "config.json"
    config = Config()
    config.thoughts.inference_target_id = "preset_openrouter_qwen38_27b"
    config.save(path)
    assert Config.load(path).thoughts.inference_target_id == "preset_openrouter_qwen38_27b"

    path.write_text('{"thoughts":{"inference_target_id":"  "}}')
    assert Config.load(path).thoughts.inference_target_id is None

    # HS-139-08: invalid values fall to yolo (was neutral).
    raw = json.loads(path.read_text())
    raw["control_mode"] = "unbounded"
    path.write_text(json.dumps(raw))
    assert Config.load(path).control_mode == "yolo"


# ============================================================
# HotkeyConfig Tests
# ============================================================


class TestHotkeyConfig:
    """Tests for HotkeyConfig dataclass."""

    def test_display_names_from_key_display_map(self):
        """All keys in KEY_MAP have corresponding display names."""
        for key_name in KEY_MAP.keys():
            assert key_name in KEY_DISPLAY, f"Missing display name for {key_name}"

    def test_key_map_to_pynput_format(self):
        """KEY_MAP values have correct pynput Key format."""
        for key_name, pynput_key in KEY_MAP.items():
            assert pynput_key.startswith("Key."), f"{key_name} should map to Key.* format"

# ============================================================
# ModelConfig Tests
# ============================================================


# ============================================================
# UIConfig Tests
# ============================================================


# ============================================================
# MeetingConfig Tests
# ============================================================


# ============================================================
# Config Tests
# ============================================================


# ============================================================
# Config.save() Tests
# ============================================================


class TestConfigSave:
    """Tests for Config.save() method."""

    def test_save_creates_file(self, default_config, temp_config_path):
        """save() creates the config file."""
        assert not temp_config_path.exists()
        default_config.save(temp_config_path)
        assert temp_config_path.exists()

    def test_save_creates_parent_directories(self, default_config, tmp_path):
        """save() creates parent directories if they don't exist."""
        nested_path = tmp_path / "deep" / "nested" / "config.json"
        assert not nested_path.parent.exists()
        default_config.save(nested_path)
        assert nested_path.exists()

    def test_save_preserves_custom_values(self, tmp_path):
        """save() preserves custom configuration values."""
        config = Config(
            hotkey=HotkeyConfig(key="f5", display="F5"),
            model=ModelConfig(name="large"),
            ui=UIConfig(desk_sounds=False),
            meeting=MeetingConfig(mic_label="Speaker", auto_export=True),
        )
        path = tmp_path / "custom.json"
        config.save(path)

        with open(path) as f:
            data = json.load(f)

        assert data["hotkey"]["key"] == "f5"
        assert data["model"]["name"] == "large"
        assert data["model"]["warm_on_start"] is True
        assert data["ui"]["desk_sounds"] is False
        assert data["meeting"]["mic_label"] == "Speaker"


# ============================================================
# Config.load() Tests
# ============================================================


class TestConfigLoad:
    """Tests for Config.load() method."""

    def test_load_missing_file_returns_default(self, tmp_path):
        """load() returns default config when file doesn't exist."""
        path = tmp_path / "nonexistent.json"
        config = Config.load(path)
        assert config.hotkey.key == "alt_r"
        assert config.model.name == "base"

    def test_load_missing_file_creates_file(self, tmp_path):
        """load() creates config file when it doesn't exist."""
        path = tmp_path / "new_config.json"
        assert not path.exists()
        Config.load(path)
        assert path.exists()

    def test_load_valid_config(self, tmp_path):
        """load() correctly loads valid config file."""
        path = tmp_path / "valid.json"
        data = {
            "hotkey": {"key": "ctrl_l", "display": "\u2303L"},
            "model": {"name": "small", "warm_on_start": False},
            "ui": {"desk_sounds": False},
            "meeting": {"mic_label": "Host"},
        }
        with open(path, "w") as f:
            json.dump(data, f)

        config = Config.load(path)
        assert config.hotkey.key == "ctrl_l"
        assert config.model.name == "small"
        assert config.model.warm_on_start is False
        assert config.ui.desk_sounds is False
        assert config.meeting.mic_label == "Host"

    def test_load_partial_config_uses_defaults(self, tmp_path):
        """load() uses defaults for missing sections."""
        path = tmp_path / "partial.json"
        # Only hotkey section provided
        data = {"hotkey": {"key": "f12", "display": "F12"}}
        with open(path, "w") as f:
            json.dump(data, f)

        config = Config.load(path)
        assert config.hotkey.key == "f12"
        # Other sections should have defaults
        assert config.model.name == "base"
        assert config.ui.desk_sounds is True
        assert config.meeting.mic_label == "Me"

    def test_load_empty_json_uses_defaults(self, tmp_path):
        """load() uses defaults for empty JSON object."""
        path = tmp_path / "empty.json"
        with open(path, "w") as f:
            json.dump({}, f)

        config = Config.load(path)
        assert config.hotkey.key == "alt_r"
        assert config.model.name == "base"

    def test_load_malformed_json_returns_default(self, tmp_path):
        """load() returns default config for malformed JSON."""
        path = tmp_path / "malformed.json"
        path.write_text("{ this is not valid json }")

        config = Config.load(path)
        assert config.hotkey.key == "alt_r"
        assert config.model.name == "base"

    def test_load_invalid_type_returns_default(self, tmp_path):
        """load() returns default when JSON is valid but wrong type."""
        path = tmp_path / "array.json"
        with open(path, "w") as f:
            json.dump(["not", "a", "dict"], f)

        config = Config.load(path)
        # Should fall back to defaults on error
        assert config.hotkey.key == "alt_r"

    def test_load_with_extra_fields_ignores_unknown(self, tmp_path):
        """load() drops unknown keys \u2014 both unknown sections AND unknown
        keys *within* a section \u2014 without discarding the rest of the config."""
        path = tmp_path / "extra.json"
        data = {
            # an unknown key inside a section no longer breaks the whole load
            "hotkey": {"key": "alt_l", "display": "\u2325L", "unknown_field": "value"},
            "model": {"name": "tiny"},
            "ui": {},
            "meeting": {},
            "unknown_section": {"foo": "bar"},  # unknown top-level section
        }
        with open(path, "w") as f:
            json.dump(data, f)

        config = Config.load(path)
        # The known keys in the same section still load (no total fallback).
        assert config.hotkey.key == "alt_l"
        assert config.hotkey.display == "\u2325L"
        assert config.model.name == "tiny"
        assert config.model.warm_on_start is True

    def test_load_legacy_key_does_not_discard_whole_config(self, tmp_path):
        """A retired/legacy key in one section must not nuke the user's config.

        Regression for the wild case surfaced post-HS-32-06: the removed
        ``meeting.web_enabled`` key tripped ``MeetingConfig(**data)`` and the old
        broad ``except: return cls()`` silently discarded the *entire* config \u2014
        so a configured ``intel_cloud_base_url`` was ignored on every load. The
        legacy key must be dropped while every other configured value survives.
        """
        path = tmp_path / "legacy.json"
        data = {
            "meeting": {
                "web_enabled": True,  # retired in HS-32-06 \u2014 must be ignored
                "intel_provider": "cloud",
                "intel_cloud_base_url": "http://192.168.1.43:8080/v1",
                "intel_cloud_model": "Qwen3.5-9B-UD-Q6_K_XL.gguf",
            },
            "model": {"name": "small"},
        }
        with open(path, "w") as f:
            json.dump(data, f)

        config = Config.load(path)
        # The configured cloud endpoint survives \u2014 not silently dropped to defaults.
        assert config.meeting.intel_provider == "cloud"
        assert config.meeting.intel_cloud_base_url == "http://192.168.1.43:8080/v1"
        assert config.meeting.intel_cloud_model == "Qwen3.5-9B-UD-Q6_K_XL.gguf"
        # The legacy key is not present on the dataclass.
        assert not hasattr(config.meeting, "web_enabled")
        # A sibling section is unaffected.
        assert config.model.name == "small"

    def test_load_unknown_key_logs_warning(self, tmp_path, caplog):
        """Dropping an unknown key emits a warning (not a silent swallow)."""
        path = tmp_path / "warn.json"
        with open(path, "w") as f:
            json.dump({"meeting": {"web_enabled": True, "mic_label": "Host"}}, f)

        with caplog.at_level("WARNING", logger="holdspeak.config"):
            config = Config.load(path)

        assert config.meeting.mic_label == "Host"
        assert any(
            "web_enabled" in r.message and "meeting" in r.message for r in caplog.records
        ), caplog.text

    def test_load_pre_reckoning_config_survives(self, tmp_path, caplog):
        """HS-139-01: a config.json containing the six deleted keys loads
        cleanly — no crash, no resurrection of dead fields, sibling values
        survive, and a warning names each dropped key."""
        path = tmp_path / "pre_reckoning.json"
        data = {
            "ui": {
                "show_audio_meter": False,
                "history_lines": 25,
                "theme": "monokai",
                "desk_sounds": False,
            },
            "meeting": {
                "intel_queue_poll_seconds": 60,
                "intel_retry_failure_alert_percent": 75.0,
                "intel_retry_failure_hysteresis_minutes": 10.0,
                "mic_label": "Host",
                "intel_provider": "cloud",
            },
            "model": {"name": "small"},
        }
        with open(path, "w") as f:
            json.dump(data, f)

        with caplog.at_level("WARNING", logger="holdspeak.config"):
            config = Config.load(path)

        # Dead fields are NOT resurrected.
        assert not hasattr(config.ui, "show_audio_meter")
        assert not hasattr(config.ui, "history_lines")
        assert not hasattr(config.ui, "theme")
        assert not hasattr(config.meeting, "intel_queue_poll_seconds")
        assert not hasattr(config.meeting, "intel_retry_failure_alert_percent")
        assert not hasattr(config.meeting, "intel_retry_failure_hysteresis_minutes")
        # Sibling values survive.
        assert config.ui.desk_sounds is False
        assert config.meeting.mic_label == "Host"
        assert config.meeting.intel_provider == "cloud"
        assert config.model.name == "small"
        # _coerce warned about each dead key.
        for dead_key in (
            "show_audio_meter",
            "history_lines",
            "theme",
            "intel_queue_poll_seconds",
            "intel_retry_failure_alert_percent",
            "intel_retry_failure_hysteresis_minutes",
        ):
            assert any(
                dead_key in r.message for r in caplog.records
            ), f"expected warning for {dead_key!r}, got: {caplog.text}"


# ============================================================
# Round-trip Tests
# ============================================================


class TestConfigRoundTrip:
    """Tests for save/load round-trip preservation."""

    def test_round_trip_preserves_defaults(self, tmp_path):
        """Round-trip save/load preserves default values."""
        path = tmp_path / "roundtrip.json"
        original = Config()
        original.save(path)
        loaded = Config.load(path)

        assert loaded.hotkey.key == original.hotkey.key
        assert loaded.hotkey.display == original.hotkey.display
        assert loaded.model.name == original.model.name
        assert loaded.model.warm_on_start == original.model.warm_on_start
        assert loaded.ui.desk_sounds == original.ui.desk_sounds

    def test_round_trip_preserves_custom_values(self, tmp_path):
        """Round-trip save/load preserves custom values."""
        path = tmp_path / "custom_roundtrip.json"
        original = Config(
            hotkey=HotkeyConfig(key="caps_lock", display="\u21ea"),
            model=ModelConfig(name="medium"),
            ui=UIConfig(desk_sounds=False),
            meeting=MeetingConfig(
                system_audio_device="BlackHole 2ch",
                auto_export=True,
                export_format="srt",
            ),
        )
        original.save(path)
        loaded = Config.load(path)

        assert loaded.hotkey.key == "caps_lock"
        assert loaded.model.name == "medium"  # field persists on disk; API strips writes
        assert loaded.model.warm_on_start is True
        assert loaded.ui.desk_sounds is False
        assert loaded.meeting.system_audio_device == "BlackHole 2ch"
        assert loaded.meeting.auto_export is True
        assert loaded.meeting.export_format == "srt"

    def test_round_trip_preserves_all_meeting_fields(self, tmp_path):
        """Round-trip preserves all MeetingConfig fields."""
        path = tmp_path / "meeting_roundtrip.json"
        original = Config(
            meeting=MeetingConfig(
                system_audio_device="Test Device",
                auto_export=True,
                export_format="json",
                intel_provider="auto",
                intel_realtime_model="/path/to/model.gguf",
                intel_summary_model="/path/to/summary.gguf",
                intel_cloud_model="gpt-5.4",
                intel_cloud_api_key_env="ALT_OPENAI_KEY",
                intel_cloud_base_url="https://api.example.com/v1",
            )
        )
        original.save(path)
        loaded = Config.load(path)

        assert loaded.meeting.system_audio_device == "Test Device"
        assert loaded.meeting.mic_label == "Me"  # HS-139-02: pinned default
        assert loaded.meeting.remote_label == "Remote"  # pinned default
        assert loaded.meeting.auto_export is True
        assert loaded.meeting.export_format == "json"
        assert loaded.meeting.intel_enabled is True  # pinned default
        assert loaded.meeting.intel_provider == "auto"
        assert loaded.meeting.intel_realtime_model == "/path/to/model.gguf"
        assert loaded.meeting.intel_summary_model == "/path/to/summary.gguf"
        assert loaded.meeting.intel_cloud_model == "gpt-5.4"
        assert loaded.meeting.intel_cloud_api_key_env == "ALT_OPENAI_KEY"
        assert loaded.meeting.intel_cloud_base_url == "https://api.example.com/v1"


# ============================================================
# get_available_keys() Tests
# ============================================================


class TestGetAvailableKeys:
    """Tests for get_available_keys() function."""

    def test_returns_all_keys_from_key_map(self):
        """get_available_keys() returns all keys from KEY_MAP."""
        keys = get_available_keys()
        key_names = [k[0] for k in keys]
        for expected_key in KEY_MAP.keys():
            assert expected_key in key_names

    def test_display_names_match_key_display(self):
        """get_available_keys() display names match KEY_DISPLAY."""
        keys = get_available_keys()
        for key_name, display in keys:
            expected_display = KEY_DISPLAY.get(key_name, key_name)
            assert display == expected_display

# ============================================================
# KEY_MAP Completeness Tests
# ============================================================


class TestKeyMapCompleteness:
    """Tests for KEY_MAP and KEY_DISPLAY completeness."""

    def test_key_map_and_key_display_have_same_keys(self):
        """KEY_MAP and KEY_DISPLAY have identical key sets."""
        assert set(KEY_MAP.keys()) == set(KEY_DISPLAY.keys())

class TestDictationPipelineValidation:
    """DIR-C-002: unknown stage IDs MUST be rejected at config load time."""

    def test_unknown_stage_id_rejected(self):
        from holdspeak.config import DictationConfigError, DictationPipelineConfig

        with pytest.raises(DictationConfigError) as exc:
            DictationPipelineConfig(stages=["intent-router", "made-up"])
        assert "made-up" in str(exc.value)
        assert "project-rewriter" in str(exc.value)
        assert "kb-enricher" in str(exc.value)  # surfaces the canonical list

    def test_rewrite_passes_below_one_rejected(self):
        from holdspeak.config import DictationConfigError, DictationPipelineConfig

        with pytest.raises(DictationConfigError) as exc:
            DictationPipelineConfig(rewrite_passes=0)
        assert "rewrite_passes" in str(exc.value)

    def test_rewrite_passes_above_cap_rejected(self):
        from holdspeak.config import DictationConfigError, DictationPipelineConfig

        with pytest.raises(DictationConfigError) as exc:
            DictationPipelineConfig(rewrite_passes=6)
        assert "rewrite_passes" in str(exc.value)

    def test_target_detect_llm_below_out_of_range_rejected(self):
        from holdspeak.config import DictationConfigError, DictationPipelineConfig

        with pytest.raises(DictationConfigError) as exc:
            DictationPipelineConfig(target_detect_llm_below=1.5)
        assert "target_detect_llm_below" in str(exc.value)
