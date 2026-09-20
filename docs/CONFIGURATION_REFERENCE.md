# Configuration declaration reference

<!-- GENERATED: scripts/philo_config_reference.py -->

Source snapshot: `675401a857b85336d4acaa8c65383dfc9636e4c8`.

Dataclass declarations only. Defaults are source expressions, not evaluated values. Load coercion, migrations, validation, environment variables and database-backed settings can change effective behavior. This is not a complete runtime configuration schema.

The hub configuration shell is [`Config`](../holdspeak/config/core.py). Its load/save path composes the section classes below. Use Settings for supported changes. Do not paste credentials into generated examples. Retired compatibility fields are retained only in the machine inventory.

| Class.field | Type | Declared default | Source |
| --- | --- | --- | --- |
| `Config.config_version` | `int` | `CONFIG_VERSION` | [holdspeak/config/core.py:281](../holdspeak/config/core.py) |
| `Config.machine_id` | `str` | `''` | [holdspeak/config/core.py:285](../holdspeak/config/core.py) |
| `Config.control_mode` | `str` | `'yolo'` | [holdspeak/config/core.py:289](../holdspeak/config/core.py) |
| `Config.hotkey` | `HotkeyConfig` | `field(default_factory=HotkeyConfig)` | [holdspeak/config/core.py:290](../holdspeak/config/core.py) |
| `Config.model` | `ModelConfig` | `field(default_factory=ModelConfig)` | [holdspeak/config/core.py:291](../holdspeak/config/core.py) |
| `Config.ui` | `UIConfig` | `field(default_factory=UIConfig)` | [holdspeak/config/core.py:292](../holdspeak/config/core.py) |
| `Config.meeting` | `MeetingConfig` | `field(default_factory=MeetingConfig)` | [holdspeak/config/core.py:293](../holdspeak/config/core.py) |
| `Config.dictation` | `DictationConfig` | `field(default_factory=DictationConfig)` | [holdspeak/config/core.py:294](../holdspeak/config/core.py) |
| `Config.device` | `DeviceConfig` | `field(default_factory=DeviceConfig)` | [holdspeak/config/core.py:295](../holdspeak/config/core.py) |
| `Config.presence` | `PresenceConfig` | `field(default_factory=PresenceConfig)` | [holdspeak/config/core.py:296](../holdspeak/config/core.py) |
| `Config.wake_word` | `WakeWordConfig` | `field(default_factory=WakeWordConfig)` | [holdspeak/config/core.py:297](../holdspeak/config/core.py) |
| `Config.mesh` | `MeshConfig` | `field(default_factory=MeshConfig)` | [holdspeak/config/core.py:298](../holdspeak/config/core.py) |
| `Config.cadence` | `CadenceConfig` | `field(default_factory=CadenceConfig)` | [holdspeak/config/core.py:299](../holdspeak/config/core.py) |
| `Config.cadence_telegram` | `TelegramConfig` | `field(default_factory=TelegramConfig)` | [holdspeak/config/core.py:300](../holdspeak/config/core.py) |
| `Config.rails_observer` | `RailsObserverConfig` | `field(default_factory=RailsObserverConfig)` | [holdspeak/config/core.py:301](../holdspeak/config/core.py) |
| `Config.thoughts` | `ThoughtsConfig` | `field(default_factory=ThoughtsConfig)` | [holdspeak/config/core.py:302](../holdspeak/config/core.py) |
| `Config.calendar` | `CalendarConfig` | `field(default_factory=CalendarConfig)` | [holdspeak/config/core.py:303](../holdspeak/config/core.py) |
| `DeviceConfig.psk` | `str` | `''` | [holdspeak/config/device.py:20](../holdspeak/config/device.py) |
| `PresenceConfig.enabled` | `bool` | `False` | [holdspeak/config/device.py:34](../holdspeak/config/device.py) |
| `PresenceConfig.mascot` | `bool` | `False` | [holdspeak/config/device.py:38](../holdspeak/config/device.py) |
| `MeshConfig.device_name` | `str` | `''` | [holdspeak/config/device.py:52](../holdspeak/config/device.py) |
| `WakeWordConfig.enabled` | `bool` | `False` | [holdspeak/config/device.py:70](../holdspeak/config/device.py) |
| `WakeWordConfig.model` | `str` | `'hey_jarvis'` | [holdspeak/config/device.py:71](../holdspeak/config/device.py) |
| `WakeWordConfig.threshold` | `float` | `0.5` | [holdspeak/config/device.py:72](../holdspeak/config/device.py) |
| `WakeWordConfig.armed_window_seconds` | `float` | `8.0` | [holdspeak/config/device.py:73](../holdspeak/config/device.py) |
| `WakeWordConfig.action` | `str` | `'preview'` | [holdspeak/config/device.py:74](../holdspeak/config/device.py) |
| `CalendarSource.id` | `str` | `''` | [holdspeak/config/integrations.py:21](../holdspeak/config/integrations.py) |
| `CalendarSource.label` | `str` | `''` | [holdspeak/config/integrations.py:22](../holdspeak/config/integrations.py) |
| `CalendarSource.url` | `str` | `''` | [holdspeak/config/integrations.py:23](../holdspeak/config/integrations.py) |
| `CalendarSource.enabled` | `bool` | `True` | [holdspeak/config/integrations.py:24](../holdspeak/config/integrations.py) |
| `CalendarConfig.sources` | `list[CalendarSource]` | `field(default_factory=list)` | [holdspeak/config/integrations.py:37](../holdspeak/config/integrations.py) |
| `CadenceConfig.enabled` | `bool` | `False` | [holdspeak/config/integrations.py:205](../holdspeak/config/integrations.py) |
| `CadenceConfig.pressure` | `str` | `'normal'` | [holdspeak/config/integrations.py:206](../holdspeak/config/integrations.py) |
| `CadenceConfig.use_llm` | `bool` | `False` | [holdspeak/config/integrations.py:207](../holdspeak/config/integrations.py) |
| `CadenceConfig.tick_interval_seconds` | `int` | `300` | [holdspeak/config/integrations.py:208](../holdspeak/config/integrations.py) |
| `CadenceConfig.quiet_hours_start` | `int` | `22` | [holdspeak/config/integrations.py:209](../holdspeak/config/integrations.py) |
| `CadenceConfig.quiet_hours_end` | `int` | `8` | [holdspeak/config/integrations.py:210](../holdspeak/config/integrations.py) |
| `CadenceConfig.max_nudges_per_day` | `int` | `12` | [holdspeak/config/integrations.py:211](../holdspeak/config/integrations.py) |
| `TelegramConfig.enabled` | `bool` | `False` | [holdspeak/config/integrations.py:233](../holdspeak/config/integrations.py) |
| `TelegramConfig.bot_token` | `str` | `''` | [holdspeak/config/integrations.py:234](../holdspeak/config/integrations.py) |
| `TelegramConfig.allowed_chat_ids` | `list[str]` | `field(default_factory=list)` | [holdspeak/config/integrations.py:235](../holdspeak/config/integrations.py) |
| `TelegramConfig.pairing_code` | `str` | `''` | [holdspeak/config/integrations.py:236](../holdspeak/config/integrations.py) |
| `RailsObserverConfig.enabled` | `bool` | `False` | [holdspeak/config/integrations.py:261](../holdspeak/config/integrations.py) |
| `RailsObserverConfig.profile_id` | `Optional[str]` | `None` | [holdspeak/config/integrations.py:264](../holdspeak/config/integrations.py) |
| `RailsObserverConfig.poll_seconds` | `int` | `30` | [holdspeak/config/integrations.py:265](../holdspeak/config/integrations.py) |
| `RailsObserverConfig.tail` | `int` | `20` | [holdspeak/config/integrations.py:266](../holdspeak/config/integrations.py) |
| `MeetingConfig.mic_device` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:19](../holdspeak/config/meeting.py) |
| `MeetingConfig.system_audio_device` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:20](../holdspeak/config/meeting.py) |
| `MeetingConfig.mic_label` | `str` | `'Me'` | [holdspeak/config/meeting.py:21](../holdspeak/config/meeting.py) |
| `MeetingConfig.remote_label` | `str` | `'Remote'` | [holdspeak/config/meeting.py:22](../holdspeak/config/meeting.py) |
| `MeetingConfig.auto_export` | `bool` | `False` | [holdspeak/config/meeting.py:25](../holdspeak/config/meeting.py) |
| `MeetingConfig.export_format` | `str` | `'markdown'` | [holdspeak/config/meeting.py:26](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_enabled` | `bool` | `True` | [holdspeak/config/meeting.py:29](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_provider` | `str` | `'local'` | [holdspeak/config/meeting.py:33](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_realtime_model` | `str` | `'~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf'` | [holdspeak/config/meeting.py:36](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_temperature` | `float` | `0.2` | [holdspeak/config/meeting.py:37](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_summary_model` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:38](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_deferred_enabled` | `bool` | `True` | [holdspeak/config/meeting.py:39](../holdspeak/config/meeting.py) |
| `MeetingConfig.intelligence_auto` | `str` | `'room_linked'` | [holdspeak/config/meeting.py:44](../holdspeak/config/meeting.py) |
| `MeetingConfig.auto_record` | `str` | `'off'` | [holdspeak/config/meeting.py:49](../holdspeak/config/meeting.py) |
| `MeetingConfig.auto_record_lead_minutes` | `int` | `5` | [holdspeak/config/meeting.py:51](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_retry_base_seconds` | `int` | `30` | [holdspeak/config/meeting.py:54](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_retry_max_seconds` | `int` | `900` | [holdspeak/config/meeting.py:55](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_retry_max_attempts` | `int` | `6` | [holdspeak/config/meeting.py:56](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_retry_failure_webhook_url` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:60](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_retry_failure_webhook_header_name` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:61](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_retry_failure_webhook_header_value` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:62](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_cloud_model` | `str` | `'gpt-5-mini'` | [holdspeak/config/meeting.py:65](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_cloud_api_key_env` | `str` | `'OPENAI_API_KEY'` | [holdspeak/config/meeting.py:66](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_cloud_base_url` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:67](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_cloud_reasoning_effort` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:68](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_cloud_store` | `bool` | `False` | [holdspeak/config/meeting.py:69](../holdspeak/config/meeting.py) |
| `MeetingConfig.intel_profile_id` | `Optional[str]` | `None` | [holdspeak/config/meeting.py:73](../holdspeak/config/meeting.py) |
| `MeetingConfig.web_auth_token` | `str` | `''` | [holdspeak/config/meeting.py:81](../holdspeak/config/meeting.py) |
| `MeetingConfig.mir_enabled` | `bool` | `True` | [holdspeak/config/meeting.py:82](../holdspeak/config/meeting.py) |
| `MeetingConfig.routing_profile` | `str` | `'balanced'` | [holdspeak/config/meeting.py:87](../holdspeak/config/meeting.py) |
| `MeetingConfig.intent_router_enabled` | `bool` | `False` | [holdspeak/config/meeting.py:93](../holdspeak/config/meeting.py) |
| `MeetingConfig.intent_window_seconds` | `int` | `90` | [holdspeak/config/meeting.py:94](../holdspeak/config/meeting.py) |
| `MeetingConfig.intent_step_seconds` | `int` | `30` | [holdspeak/config/meeting.py:95](../holdspeak/config/meeting.py) |
| `MeetingConfig.intent_score_threshold` | `float` | `0.6` | [holdspeak/config/meeting.py:96](../holdspeak/config/meeting.py) |
| `MeetingConfig.intent_hysteresis_windows` | `int` | `1` | [holdspeak/config/meeting.py:97](../holdspeak/config/meeting.py) |
| `MeetingConfig.disabled_plugins` | `list[str]` | `field(default_factory=list)` | [holdspeak/config/meeting.py:102](../holdspeak/config/meeting.py) |
| `MeetingConfig.intent_segment_probe_enabled` | `bool` | `False` | [holdspeak/config/meeting.py:110](../holdspeak/config/meeting.py) |
| `MeetingConfig.allow_actuators` | `bool` | `True` | [holdspeak/config/meeting.py:119](../holdspeak/config/meeting.py) |
| `MeetingConfig.allowed_actuators` | `list[str]` | `field(default_factory=lambda: ['*'])` | [holdspeak/config/meeting.py:120](../holdspeak/config/meeting.py) |
| `MeetingConfig.webhook_allowed_hosts` | `list[str]` | `field(default_factory=lambda: ['*'])` | [holdspeak/config/meeting.py:126](../holdspeak/config/meeting.py) |
| `MeetingConfig.slack_webhook_url` | `str` | `''` | [holdspeak/config/meeting.py:133](../holdspeak/config/meeting.py) |
| `MeetingConfig.companion_webhook_url` | `str` | `''` | [holdspeak/config/meeting.py:140](../holdspeak/config/meeting.py) |
| `MeetingConfig.companion_github_repo` | `str` | `''` | [holdspeak/config/meeting.py:146](../holdspeak/config/meeting.py) |
| `MeetingConfig.diarization_enabled` | `bool` | `False` | [holdspeak/config/meeting.py:149](../holdspeak/config/meeting.py) |
| `MeetingConfig.diarize_mic` | `bool` | `False` | [holdspeak/config/meeting.py:150](../holdspeak/config/meeting.py) |
| `MeetingConfig.cross_meeting_recognition` | `bool` | `True` | [holdspeak/config/meeting.py:151](../holdspeak/config/meeting.py) |
| `MeetingConfig.similarity_threshold` | `float` | `0.75` | [holdspeak/config/meeting.py:152](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.enabled` | `bool` | `True` | [holdspeak/config/meeting.py:376](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.stages` | `list[str]` | `field(default_factory=lambda: ['intent-router', 'kb-enricher'])` | [holdspeak/config/meeting.py:377](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.max_total_latency_ms` | `int` | `600` | [holdspeak/config/meeting.py:378](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.target_profile_override` | `str` | `'auto'` | [holdspeak/config/meeting.py:379](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.rewrite_passes` | `int` | `1` | [holdspeak/config/meeting.py:384](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.corrections_enabled` | `bool` | `True` | [holdspeak/config/meeting.py:389](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.target_detect_llm_enabled` | `bool` | `False` | [holdspeak/config/meeting.py:395](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.target_detect_llm_below` | `float` | `0.8` | [holdspeak/config/meeting.py:396](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.journal_enabled` | `bool` | `True` | [holdspeak/config/meeting.py:401](../holdspeak/config/meeting.py) |
| `DictationPipelineConfig.journal_retention` | `int` | `500` | [holdspeak/config/meeting.py:404](../holdspeak/config/meeting.py) |
| `DictationConfig.pipeline` | `DictationPipelineConfig` | `field(default_factory=DictationPipelineConfig)` | [holdspeak/config/meeting.py:448](../holdspeak/config/meeting.py) |
| `DictationConfig.runtime` | `LLMRuntimeConfig` | `field(default_factory=LLMRuntimeConfig)` | [holdspeak/config/meeting.py:449](../holdspeak/config/meeting.py) |
| `DictationConfig.macros` | `MacrosConfig` | `field(default_factory=MacrosConfig)` | [holdspeak/config/meeting.py:450](../holdspeak/config/meeting.py) |
| `DictationConfig.spoken_symbols` | `list` | `field(default_factory=list)` | [holdspeak/config/meeting.py:454](../holdspeak/config/meeting.py) |
| `DictationConfig.preview_before_type` | `bool` | `False` | [holdspeak/config/meeting.py:459](../holdspeak/config/meeting.py) |
| `ModelConfig.name` | `str` | `'base'` | [holdspeak/config/model.py:14](../holdspeak/config/model.py) |
| `ModelConfig.warm_on_start` | `bool` | `True` | [holdspeak/config/model.py:15](../holdspeak/config/model.py) |
| `ModelConfig.backend` | `str` | `'auto'` | [holdspeak/config/model.py:16](../holdspeak/config/model.py) |
| `ModelConfig.language` | `str` | `'auto'` | [holdspeak/config/model.py:22](../holdspeak/config/model.py) |
| `ModelConfig.transcribe_timeout_seconds` | `float` | `120.0` | [holdspeak/config/model.py:28](../holdspeak/config/model.py) |
| `ModelConfig.local_model_preload_authority` | `str` | `''` | [holdspeak/config/model.py:44](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.backend` | `str` | `'auto'` | [holdspeak/config/model.py:56](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.mlx_model` | `str` | `'~/Models/mlx/Qwen3.5-8B-MLX-4bit'` | [holdspeak/config/model.py:59](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.llama_cpp_model_path` | `str` | `'~/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf'` | [holdspeak/config/model.py:60](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.openai_compatible_model` | `str` | `'qwen3.5-8b-instruct'` | [holdspeak/config/model.py:63](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.openai_compatible_base_url` | `str` | `'http://127.0.0.1:8000/v1'` | [holdspeak/config/model.py:64](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.openai_compatible_api_key_env` | `str` | `'OPENAI_API_KEY'` | [holdspeak/config/model.py:65](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.profile_id` | `Optional[str]` | `None` | [holdspeak/config/model.py:70](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.openai_compatible_timeout_seconds` | `float` | `8.0` | [holdspeak/config/model.py:71](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.n_ctx` | `int` | `2048` | [holdspeak/config/model.py:72](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.n_threads` | `Optional[int]` | `None` | [holdspeak/config/model.py:73](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.n_gpu_layers` | `int` | `-1` | [holdspeak/config/model.py:74](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.warm_on_start` | `bool` | `False` | [holdspeak/config/model.py:75](../holdspeak/config/model.py) |
| `LLMRuntimeConfig.eviction_idle_seconds` | `int` | `0` | [holdspeak/config/model.py:76](../holdspeak/config/model.py) |
| `HotkeyConfig.key` | `str` | `'alt_r'` | [holdspeak/config/ui.py:15](../holdspeak/config/ui.py) |
| `HotkeyConfig.display` | `str` | `'⌥R'` | [holdspeak/config/ui.py:16](../holdspeak/config/ui.py) |
| `UIConfig.desk_sounds` | `bool` | `True` | [holdspeak/config/ui.py:27](../holdspeak/config/ui.py) |
| `VoiceMacroAction.kind` | `str` | `None` | [holdspeak/config/ui.py:53](../holdspeak/config/ui.py) |
| `VoiceMacroAction.payload` | `str` | `''` | [holdspeak/config/ui.py:54](../holdspeak/config/ui.py) |
| `VoiceMacro.keyword` | `str` | `None` | [holdspeak/config/ui.py:89](../holdspeak/config/ui.py) |
| `VoiceMacro.action` | `VoiceMacroAction` | `None` | [holdspeak/config/ui.py:90](../holdspeak/config/ui.py) |
| `MacrosConfig.enabled` | `bool` | `False` | [holdspeak/config/ui.py:119](../holdspeak/config/ui.py) |
| `MacrosConfig.items` | `list[VoiceMacro]` | `field(default_factory=list)` | [holdspeak/config/ui.py:120](../holdspeak/config/ui.py) |
