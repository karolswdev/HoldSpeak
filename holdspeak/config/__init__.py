"""HoldSpeak configuration package (HS-117-12).

Re-exports the full public surface so existing ``from holdspeak.config import X``
imports keep working unchanged.
"""
# Core: Config, load/save, coercion, constants, legacy migration
from .core import (  # noqa: F401
    CONFIG_DIR,
    CONFIG_FILE,
    CONFIG_VERSION,
    Config,
    LEGACY_DICTATION_PROFILE_ID,
    LEGACY_ENDPOINT_FIELDS,
    LEGACY_INTEL_PROFILE_ID,
    _coerce,
    _coerce_config_version,
    migrate_legacy_endpoints,
)

# Meeting & dictation
from .meeting import (  # noqa: F401
    DictationConfig,
    DictationConfigError,
    DictationPipelineConfig,
    MeetingConfig,
    VALID_SYMBOL_ATTACH,
    validate_spoken_symbols,
)

# Model / LLM runtime
from .model import (  # noqa: F401
    LLMRuntimeConfig,
    ModelConfig,
)

# UI, hotkeys, voice macros
from .ui import (  # noqa: F401
    KEY_DISPLAY,
    KEY_MAP,
    HotkeyConfig,
    MacrosConfig,
    UIConfig,
    VoiceMacro,
    VoiceMacroAction,
    VoiceMacroError,
    get_available_keys,
)

# Device, presence, mesh, wake word
from .device import (  # noqa: F401
    DeviceConfig,
    MeshConfig,
    PresenceConfig,
    WakeWordConfig,
)

# Integrations: Cadence, Telegram, Rails observer
from .integrations import (  # noqa: F401
    CadenceConfig,
    RailsObserverConfig,
    TelegramConfig,
    ThoughtsConfig,
)
