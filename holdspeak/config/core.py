"""Config dataclass shell, load/save, coercion, version migration (HS-117-12).

The ``Config`` class composes domain sections from sibling modules. This is
the only file that knows how to read/write ``config.json``.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Optional

from .meeting import (
    DictationConfig,
    DictationPipelineConfig,
    MeetingConfig,
)
from .model import LLMRuntimeConfig, ModelConfig
from .ui import HotkeyConfig, MacrosConfig, UIConfig
from .device import DeviceConfig, MeshConfig, PresenceConfig, WakeWordConfig
from .integrations import CadenceConfig, RailsObserverConfig, TelegramConfig

logger = logging.getLogger(__name__)

# Default config location
CONFIG_DIR = Path.home() / ".config" / "holdspeak"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _active_config_file() -> Path:
    """Honor legacy patches to the public ``holdspeak.config`` facade.

    The package split keeps this module as the implementation owner, while
    callers historically patched ``holdspeak.config.CONFIG_FILE`` as their
    test/runtime seam. Resolve that facade dynamically so the split preserves
    the public contract.
    """
    facade = sys.modules.get("holdspeak.config")
    return getattr(facade, "CONFIG_FILE", CONFIG_FILE)


# HS-112-01 -- the one dial. Endpoint/model identity lives ONLY in the
# profiles table (`InferenceTarget`); these config fields are dead legacy
# fallbacks kept solely as the source for the one silent migration below.
# Feature code never reads them; the settings API never writes or returns
# them.
LEGACY_ENDPOINT_FIELDS: dict[str, tuple[str, ...]] = {
    "meeting": (
        "intel_cloud_model",
        "intel_cloud_api_key_env",
        "intel_cloud_base_url",
    ),
    "dictation.runtime": (
        "openai_compatible_model",
        "openai_compatible_api_key_env",
        "openai_compatible_base_url",
    ),
}

LEGACY_INTEL_PROFILE_ID = "legacy-intel"
LEGACY_DICTATION_PROFILE_ID = "legacy-dictation"

# The config format version. Bumped when the on-disk shape changes in a way that
# needs forward coercion. A config without this field is treated as pre-versioning
# and coerced forward; a config newer than this build is loaded but flagged rather
# than silently honored.
CONFIG_VERSION = 1


def _coerce(dc_type, data, *, section: str):
    """Build a config dataclass from a dict, dropping unknown/legacy keys.

    A stale or unknown key -- e.g. a config option retired in a later version
    (the HS-32-06-removed ``meeting.web_enabled`` was found in the wild) -- must
    **not** discard the user's whole config. Previously ``load()`` constructed
    each sub-config as ``DcType(**data)`` inside a broad ``except: return
    cls()``, so one unrecognized key made the *entire* config silently fall back
    to defaults (a configured ``intel_cloud_base_url`` would be ignored on every
    load with no error). Here unknown keys are dropped with a warning so the rest
    of the section still loads.
    """
    known = {f.name for f in fields(dc_type)}
    extra = sorted(k for k in data if k not in known)
    if extra:
        logger.warning(
            "config: ignoring unknown key(s) in [%s]: %s", section, ", ".join(extra)
        )
    return dc_type(**{k: v for k, v in data.items() if k in known})


def _coerce_config_version(raw) -> int:
    """Resolve the on-disk config_version into the value to load with.

    - Missing (a pre-versioning config) or not an int: coerce forward to the
      current version. No fields are dropped; the rest of load() keeps every
      known key, so an older shape upgrades in place.
    - Older than this build: coerce forward to the current version (the forward
      upgrade is a no-op today; this is where a real migration would hook in).
    - Newer than this build: keep the stored value and warn. Loading proceeds so
      the user is not locked out, but doctor flags it rather than pretending the
      config is understood.
    """
    if not isinstance(raw, int):
        return CONFIG_VERSION
    if raw < CONFIG_VERSION:
        logger.info("config: coercing config_version %s forward to %s", raw, CONFIG_VERSION)
        return CONFIG_VERSION
    if raw > CONFIG_VERSION:
        logger.warning(
            "config: config_version %s is newer than this build (%s); "
            "loading anyway, some settings may be ignored",
            raw,
            CONFIG_VERSION,
        )
        return raw
    return raw


def migrate_legacy_endpoints(config: "Config", path: Optional[Path] = None, *, db=None) -> bool:
    """The ONE silent legacy-endpoint migration (HS-112-01).

    A configured legacy endpoint (``intel_cloud_*`` with no pointer, or a
    dictation endpoint backend with no pointer) is minted ONCE as a synthetic
    row in the profiles table and the feature pointer is set to it; the config
    is saved so the migration never recurs. Idempotent: a set pointer skips
    its leg; a fresh config mints nothing. A missing/unopenable DB is a
    silent no-op (retried on the next load). Returns whether anything minted.
    """
    meeting = config.meeting
    runtime = config.dictation.runtime

    intel_base = str(meeting.intel_cloud_base_url or "").strip()
    intel_needed = not meeting.intel_profile_id and (
        bool(intel_base) or meeting.intel_provider == "cloud"
    )
    dictation_needed = not runtime.profile_id and runtime.backend == "openai_compatible"
    if not (intel_needed or dictation_needed):
        return False

    try:
        if db is None:
            from ..db import get_database

            db = get_database()
        from ..intel.models import DEFAULT_CLOUD_BASE_URL

        if intel_needed:
            db.profiles.upsert(
                profile_id=LEGACY_INTEL_PROFILE_ID,
                name="Migrated intel endpoint",
                kind="openAICompatible",
                base_url=intel_base or DEFAULT_CLOUD_BASE_URL,
                model=str(meeting.intel_cloud_model or "").strip(),
                requires_key=not bool(intel_base),
            )
            meeting.intel_profile_id = LEGACY_INTEL_PROFILE_ID
        if dictation_needed:
            db.profiles.upsert(
                profile_id=LEGACY_DICTATION_PROFILE_ID,
                name="Migrated dictation endpoint",
                kind="openAICompatible",
                base_url=str(runtime.openai_compatible_base_url or "").strip()
                or "http://127.0.0.1:8000/v1",
                model=str(runtime.openai_compatible_model or "").strip(),
                requires_key=False,
            )
            runtime.profile_id = LEGACY_DICTATION_PROFILE_ID
        config.save(path)
    except Exception as exc:
        logger.warning("config: legacy endpoint migration skipped (%s)", exc)
        return False
    return True


def migrate_routing_profile(config: "Config", path: Optional[Path] = None) -> bool:
    """The ONE one-time meeting routing-profile convergence (HS-130-05).

    `mir_profile` (once read by the runtime) and `plugin_profile` (once
    reported by doctor) collapse into `meeting.routing_profile`. If a legacy
    field carries a non-default value and `routing_profile` is still the
    default, adopt it (mir_profile wins, matching what the runtime historically
    read), reset the legacy fields to the default so the migration never
    recurs, and save. Idempotent: once `routing_profile` is non-default (or a
    fresh config leaves everything at the default) this is a no-op. Returns
    whether anything was migrated.
    """
    meeting = config.meeting
    if str(meeting.routing_profile or "").strip() not in ("", "balanced"):
        # Already migrated or explicitly set -- never re-adopt a legacy value.
        return False
    mir = str(meeting.mir_profile or "").strip()
    plugin = str(meeting.plugin_profile or "").strip()
    chosen = ""
    if mir and mir != "balanced":
        chosen = mir
    elif plugin and plugin != "balanced":
        chosen = plugin
    if not chosen:
        return False
    meeting.routing_profile = chosen
    # Consume the legacy owners so the accessor and doctor read one value and
    # the migration is a one-shot.
    meeting.mir_profile = "balanced"
    meeting.plugin_profile = "balanced"
    try:
        config.save(path)
    except Exception as exc:  # pragma: no cover - save failure is non-fatal
        logger.warning("config: routing-profile migration save skipped (%s)", exc)
    return True


@dataclass
class Config:
    """Main configuration container."""
    config_version: int = CONFIG_VERSION
    # HS-92-08: one policy preset for FUTURE operations. It never weakens hard
    # auth/secret/destination/payload/pane/audit/config/schema invariants.
    control_mode: str = "neutral"
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    meeting: MeetingConfig = field(default_factory=MeetingConfig)
    dictation: DictationConfig = field(default_factory=DictationConfig)
    device: DeviceConfig = field(default_factory=DeviceConfig)
    presence: PresenceConfig = field(default_factory=PresenceConfig)
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)
    mesh: MeshConfig = field(default_factory=MeshConfig)
    cadence: CadenceConfig = field(default_factory=CadenceConfig)
    cadence_telegram: TelegramConfig = field(default_factory=TelegramConfig)
    rails_observer: RailsObserverConfig = field(default_factory=RailsObserverConfig)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from file, or create default."""
        config_path = path or _active_config_file()

        if not config_path.exists():
            config = cls()
            config.save(config_path)
            return config

        try:
            with open(config_path) as f:
                data = json.load(f)

            config_version = _coerce_config_version(data.get("config_version"))

            dictation_data = data.get("dictation", {}) or {}
            pipeline_data = dictation_data.get("pipeline", {}) or {}
            runtime_data = dictation_data.get("runtime", {}) or {}
            macros_data = dictation_data.get("macros", {}) or {}
            dictation = DictationConfig(
                pipeline=_coerce(
                    DictationPipelineConfig, pipeline_data, section="dictation.pipeline"
                ),
                runtime=_coerce(
                    LLMRuntimeConfig, runtime_data, section="dictation.runtime"
                ),
                macros=_coerce(MacrosConfig, macros_data, section="dictation.macros"),
                spoken_symbols=dictation_data.get("spoken_symbols", []) or [],
                preview_before_type=bool(
                    dictation_data.get("preview_before_type", False)
                ),
            )

            config = cls(
                config_version=config_version,
                control_mode=(
                    str(data.get("control_mode", "neutral")).strip().lower()
                    if str(data.get("control_mode", "neutral")).strip().lower()
                    in {"safe", "neutral", "yolo"}
                    else "neutral"
                ),
                hotkey=_coerce(HotkeyConfig, data.get("hotkey", {}) or {}, section="hotkey"),
                model=_coerce(ModelConfig, data.get("model", {}) or {}, section="model"),
                ui=_coerce(UIConfig, data.get("ui", {}) or {}, section="ui"),
                meeting=_coerce(MeetingConfig, data.get("meeting", {}) or {}, section="meeting"),
                dictation=dictation,
                device=_coerce(DeviceConfig, data.get("device", {}) or {}, section="device"),
                presence=_coerce(PresenceConfig, data.get("presence", {}) or {}, section="presence"),
                wake_word=_coerce(WakeWordConfig, data.get("wake_word", {}) or {}, section="wake_word"),
                mesh=_coerce(MeshConfig, data.get("mesh", {}) or {}, section="mesh"),
                cadence=_coerce(CadenceConfig, data.get("cadence", {}) or {}, section="cadence"),
                cadence_telegram=_coerce(
                    TelegramConfig, data.get("cadence_telegram", {}) or {}, section="cadence_telegram"
                ),
                rails_observer=_coerce(
                    RailsObserverConfig, data.get("rails_observer", {}) or {}, section="rails_observer"
                ),
            )
            # HS-112-01: the one-time legacy-endpoint migration runs only on
            # the real install's config (an explicit path is a test/tool
            # load and stays inert).
            if path is None:
                migrate_legacy_endpoints(config, config_path)
                migrate_routing_profile(config, config_path)
            return config
        except Exception as exc:
            # Last-resort fallback for a genuinely broken config (bad JSON, wrong
            # top-level type, or a value a sub-config's __post_init__ rejects).
            # Unknown/legacy keys no longer reach here -- _coerce drops them -- so
            # this should be rare; log it rather than swallowing silently.
            logger.warning(
                "config: failed to load %s (%s); using defaults", config_path, exc
            )
            return cls()

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        config_path = path or _active_config_file()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
