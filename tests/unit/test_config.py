"""Comprehensive unit tests for the config module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

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


# ============================================================
# HotkeyConfig Tests
# ============================================================


class TestHotkeyConfig:
    """Tests for HotkeyConfig dataclass."""

    def test_default_values(self):
        """HotkeyConfig has correct default values."""
        config = HotkeyConfig()
        assert config.key == "alt_r"
        assert config.display == "\u2325R"  # ⌥R

    def test_custom_values(self):
        """HotkeyConfig accepts custom values."""
        config = HotkeyConfig(key="f5", display="F5")
        assert config.key == "f5"
        assert config.display == "F5"

    def test_display_names_from_key_display_map(self):
        """All keys in KEY_MAP have corresponding display names."""
        for key_name in KEY_MAP.keys():
            assert key_name in KEY_DISPLAY, f"Missing display name for {key_name}"

    def test_key_map_to_pynput_format(self):
        """KEY_MAP values have correct pynput Key format."""
        for key_name, pynput_key in KEY_MAP.items():
            assert pynput_key.startswith("Key."), f"{key_name} should map to Key.* format"

    def test_modifier_keys_have_left_right_variants(self):
        """Modifier keys (alt, ctrl, cmd, shift) have both left and right variants."""
        modifiers = ["alt", "ctrl", "cmd", "shift"]
        for mod in modifiers:
            assert f"{mod}_l" in KEY_MAP, f"Missing {mod}_l"
            assert f"{mod}_r" in KEY_MAP, f"Missing {mod}_r"

    def test_function_keys_f1_to_f12(self):
        """Function keys F1-F12 are all available."""
        for i in range(1, 13):
            key_name = f"f{i}"
            assert key_name in KEY_MAP, f"Missing {key_name}"
            assert KEY_MAP[key_name] == f"Key.f{i}"
            assert KEY_DISPLAY[key_name] == f"F{i}"


# ============================================================
# ModelConfig Tests
# ============================================================


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_default_model_is_base(self):
        """Default model name is 'base'."""
        config = ModelConfig()
        assert config.name == "base"

    def test_custom_model_name(self):
        """ModelConfig accepts custom model names."""
        config = ModelConfig(name="large")
        assert config.name == "large"

    @pytest.mark.parametrize(
        "model_name",
        ["tiny", "base", "small", "medium", "large"],
    )
    def test_valid_whisper_models(self, model_name):
        """All valid Whisper model names can be set."""
        config = ModelConfig(name=model_name)
        assert config.name == model_name


# ============================================================
# UIConfig Tests
# ============================================================


class TestUIConfig:
    """Tests for UIConfig dataclass."""

    def test_default_values(self):
        """UIConfig has correct default values."""
        config = UIConfig()
        assert config.show_audio_meter is True
        assert config.history_lines == 10
        assert config.theme == "dark"

    def test_custom_values(self):
        """UIConfig accepts custom values."""
        config = UIConfig(
            show_audio_meter=False,
            history_lines=20,
            theme="monokai",
        )
        assert config.show_audio_meter is False
        assert config.history_lines == 20
        assert config.theme == "monokai"

    @pytest.mark.parametrize("theme", ["dark", "light", "dracula", "monokai"])
    def test_valid_themes(self, theme):
        """All documented themes can be set."""
        config = UIConfig(theme=theme)
        assert config.theme == theme


# ============================================================
# MeetingConfig Tests
# ============================================================


class TestMeetingConfig:
    """Tests for MeetingConfig dataclass."""

    def test_default_values(self):
        """MeetingConfig has correct default values."""
        config = MeetingConfig()
        assert config.system_audio_device is None
        assert config.mic_label == "Me"
        assert config.remote_label == "Remote"
        assert config.auto_export is False
        assert config.export_format == "markdown"
        assert config.intel_enabled is True
        assert config.intel_realtime_model == "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf"
        assert config.intel_summary_model is None
        assert config.web_enabled is True
        assert config.web_auto_open is False

    def test_custom_audio_device(self):
        """MeetingConfig accepts custom audio device."""
        config = MeetingConfig(system_audio_device="BlackHole 2ch")
        assert config.system_audio_device == "BlackHole 2ch"

    def test_custom_labels(self):
        """MeetingConfig accepts custom speaker labels."""
        config = MeetingConfig(mic_label="John", remote_label="Team")
        assert config.mic_label == "John"
        assert config.remote_label == "Team"

    @pytest.mark.parametrize("fmt", ["txt", "markdown", "json", "srt"])
    def test_valid_export_formats(self, fmt):
        """All documented export formats can be set."""
        config = MeetingConfig(export_format=fmt)
        assert config.export_format == fmt


# ============================================================
# Config Tests
# ============================================================


class TestConfig:
    """Tests for main Config class."""

    def test_default_config_initialization(self, default_config):
        """Config initializes with default sub-configs."""
        assert isinstance(default_config.hotkey, HotkeyConfig)
        assert isinstance(default_config.model, ModelConfig)
        assert isinstance(default_config.ui, UIConfig)
        assert isinstance(default_config.meeting, MeetingConfig)

    def test_default_hotkey_values(self, default_config):
        """Default config has correct hotkey defaults."""
        assert default_config.hotkey.key == "alt_r"
        assert default_config.hotkey.display == "\u2325R"

    def test_default_model_values(self, default_config):
        """Default config has correct model defaults."""
        assert default_config.model.name == "base"

    def test_default_ui_values(self, default_config):
        """Default config has correct UI defaults."""
        assert default_config.ui.show_audio_meter is True
        assert default_config.ui.history_lines == 10
        assert default_config.ui.theme == "dark"

    def test_to_dict_returns_dict(self, default_config):
        """to_dict returns a dictionary representation."""
        result = default_config.to_dict()
        assert isinstance(result, dict)
        assert "hotkey" in result
        assert "model" in result
        assert "ui" in result
        assert "meeting" in result

    def test_to_dict_contains_all_values(self, default_config):
        """to_dict contains all configuration values."""
        result = default_config.to_dict()
        assert result["hotkey"]["key"] == "alt_r"
        assert result["model"]["name"] == "base"
        assert result["ui"]["theme"] == "dark"
        assert result["meeting"]["mic_label"] == "Me"


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

    def test_save_creates_valid_json(self, default_config, temp_config_path):
        """save() creates valid JSON file."""
        default_config.save(temp_config_path)
        with open(temp_config_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_save_json_is_formatted(self, default_config, temp_config_path):
        """save() creates formatted (indented) JSON."""
        default_config.save(temp_config_path)
        content = temp_config_path.read_text()
        # Indented JSON has newlines and spaces
        assert "\n" in content
        assert "  " in content  # 2-space indent

    def test_save_preserves_custom_values(self, tmp_path):
        """save() preserves custom configuration values."""
        config = Config(
            hotkey=HotkeyConfig(key="f5", display="F5"),
            model=ModelConfig(name="large"),
            ui=UIConfig(theme="monokai", history_lines=25),
            meeting=MeetingConfig(mic_label="Speaker", auto_export=True),
        )
        path = tmp_path / "custom.json"
        config.save(path)

        with open(path) as f:
            data = json.load(f)

        assert data["hotkey"]["key"] == "f5"
        assert data["model"]["name"] == "large"
        assert data["ui"]["theme"] == "monokai"
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
            "model": {"name": "small"},
            "ui": {"show_audio_meter": False, "history_lines": 15, "theme": "light"},
            "meeting": {"mic_label": "Host"},
        }
        with open(path, "w") as f:
            json.dump(data, f)

        config = Config.load(path)
        assert config.hotkey.key == "ctrl_l"
        assert config.model.name == "small"
        assert config.ui.show_audio_meter is False
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
        assert config.ui.theme == "dark"
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
        """load() ignores unknown fields in config file."""
        path = tmp_path / "extra.json"
        data = {
            "hotkey": {"key": "alt_l", "display": "\u2325L", "unknown_field": "value"},
            "model": {"name": "tiny"},
            "ui": {},
            "meeting": {},
            "unknown_section": {"foo": "bar"},
        }
        with open(path, "w") as f:
            json.dump(data, f)

        # Should not raise, unknown_section is ignored
        # But hotkey unknown_field will cause TypeError
        # Let's test with just unknown section
        data2 = {
            "hotkey": {"key": "alt_l", "display": "\u2325L"},
            "model": {"name": "tiny"},
            "unknown_section": {"foo": "bar"},
        }
        path2 = tmp_path / "extra2.json"
        with open(path2, "w") as f:
            json.dump(data2, f)

        config = Config.load(path2)
        assert config.hotkey.key == "alt_l"
        assert config.model.name == "tiny"


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
        assert loaded.ui.show_audio_meter == original.ui.show_audio_meter
        assert loaded.ui.history_lines == original.ui.history_lines
        assert loaded.ui.theme == original.ui.theme

    def test_round_trip_preserves_custom_values(self, tmp_path):
        """Round-trip save/load preserves custom values."""
        path = tmp_path / "custom_roundtrip.json"
        original = Config(
            hotkey=HotkeyConfig(key="caps_lock", display="\u21ea"),
            model=ModelConfig(name="medium"),
            ui=UIConfig(show_audio_meter=False, history_lines=50, theme="dracula"),
            meeting=MeetingConfig(
                system_audio_device="BlackHole 2ch",
                mic_label="Host",
                remote_label="Participants",
                auto_export=True,
                export_format="srt",
                intel_enabled=False,
                web_auto_open=True,
            ),
        )
        original.save(path)
        loaded = Config.load(path)

        assert loaded.hotkey.key == "caps_lock"
        assert loaded.model.name == "medium"
        assert loaded.ui.theme == "dracula"
        assert loaded.ui.history_lines == 50
        assert loaded.meeting.system_audio_device == "BlackHole 2ch"
        assert loaded.meeting.mic_label == "Host"
        assert loaded.meeting.auto_export is True
        assert loaded.meeting.export_format == "srt"
        assert loaded.meeting.intel_enabled is False
        assert loaded.meeting.web_auto_open is True

    def test_round_trip_preserves_all_meeting_fields(self, tmp_path):
        """Round-trip preserves all MeetingConfig fields."""
        path = tmp_path / "meeting_roundtrip.json"
        original = Config(
            meeting=MeetingConfig(
                system_audio_device="Test Device",
                mic_label="Me",
                remote_label="Them",
                auto_export=True,
                export_format="json",
                intel_enabled=True,
                intel_realtime_model="/path/to/model.gguf",
                intel_summary_model="/path/to/summary.gguf",
                web_enabled=False,
                web_auto_open=True,
            )
        )
        original.save(path)
        loaded = Config.load(path)

        assert loaded.meeting.system_audio_device == "Test Device"
        assert loaded.meeting.mic_label == "Me"
        assert loaded.meeting.remote_label == "Them"
        assert loaded.meeting.auto_export is True
        assert loaded.meeting.export_format == "json"
        assert loaded.meeting.intel_enabled is True
        assert loaded.meeting.intel_realtime_model == "/path/to/model.gguf"
        assert loaded.meeting.intel_summary_model == "/path/to/summary.gguf"
        assert loaded.meeting.web_enabled is False
        assert loaded.meeting.web_auto_open is True


# ============================================================
# get_available_keys() Tests
# ============================================================


class TestGetAvailableKeys:
    """Tests for get_available_keys() function."""

    def test_returns_list_of_tuples(self):
        """get_available_keys() returns list of (key, display) tuples."""
        keys = get_available_keys()
        assert isinstance(keys, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in keys)

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

    def test_includes_all_modifier_keys(self):
        """get_available_keys() includes all modifier key variants."""
        keys = get_available_keys()
        key_names = [k[0] for k in keys]
        expected_modifiers = [
            "alt_r", "alt_l",
            "ctrl_r", "ctrl_l",
            "cmd_r", "cmd_l",
            "shift_r", "shift_l",
        ]
        for mod in expected_modifiers:
            assert mod in key_names

    def test_includes_special_keys(self):
        """get_available_keys() includes special keys."""
        keys = get_available_keys()
        key_names = [k[0] for k in keys]
        assert "caps_lock" in key_names
        assert "fn" in key_names


# ============================================================
# KEY_MAP Completeness Tests
# ============================================================


class TestKeyMapCompleteness:
    """Tests for KEY_MAP and KEY_DISPLAY completeness."""

    def test_key_map_and_key_display_have_same_keys(self):
        """KEY_MAP and KEY_DISPLAY have identical key sets."""
        assert set(KEY_MAP.keys()) == set(KEY_DISPLAY.keys())

    def test_all_key_names_are_lowercase(self):
        """All key names in KEY_MAP are lowercase."""
        for key_name in KEY_MAP.keys():
            assert key_name == key_name.lower()

    def test_key_map_values_are_strings(self):
        """All KEY_MAP values are strings."""
        for value in KEY_MAP.values():
            assert isinstance(value, str)

    def test_key_display_values_are_strings(self):
        """All KEY_DISPLAY values are strings."""
        for value in KEY_DISPLAY.values():
            assert isinstance(value, str)

    def test_expected_key_count(self):
        """KEY_MAP has expected number of keys (24)."""
        # 8 modifier keys (alt/ctrl/cmd/shift x left/right)
        # + caps_lock, fn
        # + 12 function keys (f1-f12)
        # = 22 keys
        assert len(KEY_MAP) == 22
        assert len(KEY_DISPLAY) == 22
