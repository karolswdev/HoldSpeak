# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_config.py to restore.

# ruff: noqa


# --- TestHotkeyConfig::test_default_values: P1/P3: builds a config dataclass and reads back the defaults or the values it just passed; isinstance on sub-configs
# (was a method of class TestHotkeyConfig)
def test_default_values(self):
    """HotkeyConfig has correct default values."""
    config = HotkeyConfig()
    assert config.key == "alt_r"
    assert config.display == "\u2325R"  # ⌥R


# --- TestHotkeyConfig::test_custom_values: P1/P3: builds a config dataclass and reads back the defaults or the values it just passed; isinstance on sub-configs
# (was a method of class TestHotkeyConfig)
def test_custom_values(self):
    """HotkeyConfig accepts custom values."""
    config = HotkeyConfig(key="f5", display="F5")
    assert config.key == "f5"
    assert config.display == "F5"


# --- TestModelConfig: P1/P3: builds a config dataclass and reads back the defaults or the values it just passed; isinstance on sub-configs
class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_default_model_is_base(self):
        """Default model name is 'base'."""
        config = ModelConfig()
        assert config.name == "base"
        assert config.warm_on_start is True

    def test_custom_model_name(self):
        """ModelConfig accepts custom model names."""
        config = ModelConfig(name="large", warm_on_start=False)
        assert config.name == "large"
        assert config.warm_on_start is False

    @pytest.mark.parametrize(
        "model_name",
        ["tiny", "base", "small", "medium", "large"],
    )
    def test_valid_whisper_models(self, model_name):
        """All valid Whisper model names can be set."""
        config = ModelConfig(name=model_name)
        assert config.name == model_name


# --- TestUIConfig: P1/P3: builds a config dataclass and reads back the defaults or the values it just passed; isinstance on sub-configs
class TestUIConfig:
    """Tests for UIConfig dataclass."""

    def test_default_values(self):
        """UIConfig has correct default values (HS-139-01: dead fields removed)."""
        config = UIConfig()
        assert config.desk_sounds is True
        # HS-139-01: show_audio_meter, history_lines, theme no longer exist.
        assert not hasattr(config, "show_audio_meter")
        assert not hasattr(config, "history_lines")
        assert not hasattr(config, "theme")


# --- TestMeetingConfig: P1/P3: builds a config dataclass and reads back the defaults or the values it just passed; isinstance on sub-configs
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
        assert config.intel_provider == "local"
        from holdspeak.intel.models import DEFAULT_INTEL_MODEL_PATH
        assert config.intel_realtime_model == DEFAULT_INTEL_MODEL_PATH
        assert config.intel_summary_model is None
        assert config.intel_retry_base_seconds == 30
        assert config.intel_retry_max_seconds == 900
        assert config.intel_retry_max_attempts == 6
        # HS-139-01: intel_retry_failure_alert_percent and
        # intel_retry_failure_hysteresis_minutes deleted (dead).
        assert not hasattr(config, "intel_retry_failure_alert_percent")
        assert not hasattr(config, "intel_retry_failure_hysteresis_minutes")
        assert not hasattr(config, "intel_queue_poll_seconds")
        assert config.intel_retry_failure_webhook_url is None
        assert config.intel_retry_failure_webhook_header_name is None
        assert config.intel_retry_failure_webhook_header_value is None
        assert config.intel_cloud_model == "gpt-5-mini"
        assert config.intel_cloud_api_key_env == "OPENAI_API_KEY"
        assert config.intel_cloud_base_url is None
        # HS-139-02: web_auto_open deleted (hardcoded true at consumer).
        assert not hasattr(config, "web_auto_open")
        assert config.mir_enabled is True
        assert config.routing_profile == "balanced"
        # HS-2-09 (spec §9.9) — MIR-01 routing pipeline knobs.
        # PHILO-15 08: on by default (strong defaults).
        assert config.intent_router_enabled is True
        assert config.intent_window_seconds == 90
        assert config.intent_step_seconds == 30
        assert config.intent_score_threshold == 0.6
        assert config.intent_hysteresis_windows == 1
        # HS-134-08: plugin_profile deleted; routing_profile is the ONE field.
        assert config.routing_profile == "balanced"

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


# --- TestConfig: P1/P3: builds a config dataclass and reads back the defaults or the values it just passed; isinstance on sub-configs
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
        assert default_config.model.warm_on_start is True

    def test_default_ui_values(self, default_config):
        """Default config has correct UI defaults (HS-139-01: dead fields removed)."""
        assert default_config.ui.desk_sounds is True

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
        assert result["model"]["warm_on_start"] is True
        assert result["ui"]["desk_sounds"] is True
        assert result["meeting"]["mic_label"] == "Me"


# --- TestHotkeyConfig::test_modifier_keys_have_left_right_variants: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestHotkeyConfig)
def test_modifier_keys_have_left_right_variants(self):
    """Modifier keys (alt, ctrl, cmd, shift) have both left and right variants."""
    modifiers = ["alt", "ctrl", "cmd", "shift"]
    for mod in modifiers:
        assert f"{mod}_l" in KEY_MAP, f"Missing {mod}_l"
        assert f"{mod}_r" in KEY_MAP, f"Missing {mod}_r"


# --- TestHotkeyConfig::test_function_keys_f1_to_f12: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestHotkeyConfig)
def test_function_keys_f1_to_f12(self):
    """Function keys F1-F12 are all available."""
    for i in range(1, 13):
        key_name = f"f{i}"
        assert key_name in KEY_MAP, f"Missing {key_name}"
        assert KEY_MAP[key_name] == f"Key.f{i}"
        assert KEY_DISPLAY[key_name] == f"F{i}"


# --- TestGetAvailableKeys::test_returns_list_of_tuples: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestGetAvailableKeys)
def test_returns_list_of_tuples(self):
    """get_available_keys() returns list of (key, display) tuples."""
    keys = get_available_keys()
    assert isinstance(keys, list)
    assert all(isinstance(item, tuple) and len(item) == 2 for item in keys)


# --- TestGetAvailableKeys::test_includes_all_modifier_keys: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestGetAvailableKeys)
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


# --- TestGetAvailableKeys::test_includes_special_keys: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestGetAvailableKeys)
def test_includes_special_keys(self):
    """get_available_keys() includes special keys."""
    keys = get_available_keys()
    key_names = [k[0] for k in keys]
    assert "caps_lock" in key_names
    assert "fn" in key_names


# --- TestKeyMapCompleteness::test_all_key_names_are_lowercase: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestKeyMapCompleteness)
def test_all_key_names_are_lowercase(self):
    """All key names in KEY_MAP are lowercase."""
    for key_name in KEY_MAP.keys():
        assert key_name == key_name.lower()


# --- TestKeyMapCompleteness::test_key_map_values_are_strings: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestKeyMapCompleteness)
def test_key_map_values_are_strings(self):
    """All KEY_MAP values are strings."""
    for value in KEY_MAP.values():
        assert isinstance(value, str)


# --- TestKeyMapCompleteness::test_key_display_values_are_strings: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestKeyMapCompleteness)
def test_key_display_values_are_strings(self):
    """All KEY_DISPLAY values are strings."""
    for value in KEY_DISPLAY.values():
        assert isinstance(value, str)


# --- TestKeyMapCompleteness::test_expected_key_count: P1/P3: re-reads constant dict entries, their Python types, and a hand-kept count (docstring says 24, asserts 22)
# (was a method of class TestKeyMapCompleteness)
def test_expected_key_count(self):
    """KEY_MAP has expected number of keys (24)."""
    # 8 modifier keys (alt/ctrl/cmd/shift x left/right)
    # + caps_lock, fn
    # + 12 function keys (f1-f12)
    # = 22 keys
    assert len(KEY_MAP) == 22
    assert len(KEY_DISPLAY) == 22


# --- TestConfigSave::test_save_creates_valid_json: P3/P5: json.dump produces JSON with indentation; test_save_preserves_custom_values reads the same file
# (was a method of class TestConfigSave)
def test_save_creates_valid_json(self, default_config, temp_config_path):
    """save() creates valid JSON file."""
    default_config.save(temp_config_path)
    with open(temp_config_path) as f:
        data = json.load(f)
    assert isinstance(data, dict)


# --- TestConfigSave::test_save_json_is_formatted: P3/P5: json.dump produces JSON with indentation; test_save_preserves_custom_values reads the same file
# (was a method of class TestConfigSave)
def test_save_json_is_formatted(self, default_config, temp_config_path):
    """save() creates formatted (indented) JSON."""
    default_config.save(temp_config_path)
    content = temp_config_path.read_text()
    # Indented JSON has newlines and spaces
    assert "\n" in content
    assert "  " in content  # 2-space indent


# --- TestDictationPipelineValidation::test_default_stages_accepted: P1: constructs a config and reads back a default or the value it passed
# (was a method of class TestDictationPipelineValidation)
def test_default_stages_accepted(self):
    from holdspeak.config import DictationPipelineConfig

    cfg = DictationPipelineConfig()
    assert cfg.stages == ["intent-router", "kb-enricher"]


# --- TestDictationPipelineValidation::test_known_stages_accepted: P1: constructs a config and reads back a default or the value it passed
# (was a method of class TestDictationPipelineValidation)
def test_known_stages_accepted(self):
    from holdspeak.config import DictationPipelineConfig

    cfg = DictationPipelineConfig(stages=["intent-router", "project-rewriter", "kb-enricher"])
    assert cfg.stages == ["intent-router", "project-rewriter", "kb-enricher"]


# --- TestDictationPipelineValidation::test_rewrite_passes_defaults_to_one: P1: constructs a config and reads back a default or the value it passed
# (was a method of class TestDictationPipelineValidation)
def test_rewrite_passes_defaults_to_one(self):
    from holdspeak.config import DictationPipelineConfig

    assert DictationPipelineConfig().rewrite_passes == 1


# --- TestDictationPipelineValidation::test_rewrite_passes_in_range_accepted: P1: constructs a config and reads back a default or the value it passed
# (was a method of class TestDictationPipelineValidation)
def test_rewrite_passes_in_range_accepted(self):
    from holdspeak.config import DictationPipelineConfig

    assert DictationPipelineConfig(rewrite_passes=3).rewrite_passes == 3


# --- TestDictationPipelineValidation::test_corrections_enabled_defaults_on: P1: constructs a config and reads back a default or the value it passed
# (was a method of class TestDictationPipelineValidation)
def test_corrections_enabled_defaults_on(self):
    """HS-139-02: corrections_enabled pinned to True."""
    from holdspeak.config import DictationPipelineConfig

    assert DictationPipelineConfig().corrections_enabled is True


# --- TestDictationPipelineValidation::test_corrections_enabled_round_trips: P1: constructs a config and reads back a default or the value it passed
# (was a method of class TestDictationPipelineValidation)
def test_corrections_enabled_round_trips(self):
    from holdspeak.config import DictationPipelineConfig

    assert DictationPipelineConfig(corrections_enabled=True).corrections_enabled is True


# --- TestDictationPipelineValidation::test_target_detect_llm_defaults: P1: constructs a config and reads back a default or the value it passed
# (was a method of class TestDictationPipelineValidation)
def test_target_detect_llm_defaults(self):
    from holdspeak.config import DictationPipelineConfig

    cfg = DictationPipelineConfig()
    assert cfg.target_detect_llm_enabled is False
    assert cfg.target_detect_llm_below == 0.8
