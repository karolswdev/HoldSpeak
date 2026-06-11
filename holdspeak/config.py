"""Configuration management for HoldSpeak."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default config location
CONFIG_DIR = Path.home() / ".config" / "holdspeak"
CONFIG_FILE = CONFIG_DIR / "config.json"

# The config format version. Bumped when the on-disk shape changes in a way that
# needs forward coercion. A config without this field is treated as pre-versioning
# and coerced forward; a config newer than this build is loaded but flagged rather
# than silently honored.
CONFIG_VERSION = 1


def _coerce(dc_type, data, *, section: str):
    """Build a config dataclass from a dict, dropping unknown/legacy keys.

    A stale or unknown key — e.g. a config option retired in a later version
    (the HS-32-06-removed ``meeting.web_enabled`` was found in the wild) — must
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


@dataclass
class HotkeyConfig:
    """Hotkey configuration."""
    key: str = "alt_r"  # pynput key name
    display: str = "⌥R"  # Display string for UI


@dataclass
class ModelConfig:
    """Whisper model configuration."""
    name: str = "base"
    warm_on_start: bool = True
    backend: str = "auto"  # "auto" | "mlx" | "faster-whisper"
    # Available: tiny, base, small, medium, large
    # HS-25-05: hard ceiling (seconds) on a single transcription so a hung model
    # can't freeze the pipeline. Generous by default to never clip a legitimate
    # long utterance; <= 0 disables. On timeout the utterance is abandoned and
    # the pipeline returns to idle for the next one.
    transcribe_timeout_seconds: float = 120.0


@dataclass
class UIConfig:
    """UI configuration."""
    show_audio_meter: bool = True
    history_lines: int = 10
    theme: str = "dark"  # dark, light, dracula, monokai


@dataclass
class MeetingConfig:
    """Meeting mode configuration."""
    # Audio devices (None = use system default)
    mic_device: Optional[str] = None  # e.g., "MacBook Pro Microphone"
    system_audio_device: Optional[str] = None  # e.g., "BlackHole 2ch"
    mic_label: str = "Me"
    remote_label: str = "Remote"

    # Export
    auto_export: bool = False
    export_format: str = "markdown"  # txt, markdown, json, srt

    # Intel (LLM-powered analysis)
    intel_enabled: bool = True
    # intel_provider: "local" (in-process GGUF) | "cloud" (any OpenAI-compatible
    # endpoint — self-hosted LAN, Ollama, vLLM, llama.cpp-server, or a real cloud
    # API; set intel_cloud_base_url) | "auto" (local-first, then the endpoint).
    intel_provider: str = "local"
    # Suggested default — bring your own GGUF (see docs/MODELS.md). Names are a
    # moving target; this points at a current small/mid instruct model.
    intel_realtime_model: str = "~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf"
    intel_summary_model: Optional[str] = None  # Falls back to realtime if None
    intel_deferred_enabled: bool = True  # Queue intel when no suitable local model is available
    intel_queue_poll_seconds: int = 120  # Background retry interval for deferred intel jobs
    intel_retry_base_seconds: int = 30  # Initial deferred-intel retry delay
    intel_retry_max_seconds: int = 900  # Maximum deferred-intel retry delay
    intel_retry_max_attempts: int = 6  # Attempts before marking deferred intel as failed
    intel_retry_failure_alert_percent: float = 50.0  # UI alert threshold for failed/total queue ratio
    intel_retry_failure_hysteresis_minutes: float = 5.0  # Failure rate must stay above threshold for this duration
    intel_retry_failure_webhook_url: Optional[str] = None  # Optional POST endpoint for sustained failure alerts
    intel_retry_failure_webhook_header_name: Optional[str] = None  # Optional custom header name for alert webhooks
    intel_retry_failure_webhook_header_value: Optional[str] = None  # Optional custom header value for alert webhooks
    intel_cloud_model: str = "gpt-5-mini"
    intel_cloud_api_key_env: str = "OPENAI_API_KEY"
    intel_cloud_base_url: Optional[str] = None
    intel_cloud_reasoning_effort: Optional[str] = None
    intel_cloud_store: bool = False

    # Web dashboard
    web_auto_open: bool = False  # Auto-open browser on meeting start
    # Web-runtime auth token (HS-25-02). Empty = unset. Required only when the
    # runtime binds a non-loopback host; generated lazily by
    # holdspeak.web_auth.ensure_web_token. Loopback stays open regardless.
    web_auth_token: str = ""
    mir_enabled: bool = True  # Enable multi-intent routing controls in web runtime
    mir_profile: str = "balanced"  # balanced, architect, delivery, product, incident

    # MIR-01 routing pipeline gating + tuning (spec §9.9). The pipeline runs
    # at MeetingSession.stop() finalization (HS-2-06) when enabled. Defaults
    # are conservative (off + matching the in-code defaults of
    # build_intent_windows / DEFAULT_INTENT_THRESHOLD / DEFAULT_HYSTERESIS).
    intent_router_enabled: bool = False  # off by default — opt-in
    intent_window_seconds: int = 90      # rolling-window length
    intent_step_seconds: int = 30        # rolling-window step
    intent_score_threshold: float = 0.6  # gate above which an intent is "active"
    intent_hysteresis_windows: int = 1   # damping windows; converted to float via intent_hysteresis()
    plugin_profile: str = "balanced"     # routing profile selecting the chain
    # HS-35-03: per-project plugin enable/disable. Plugin ids listed here are
    # dropped from the *executed* set at dispatch (recorded as `skipped`, not
    # failed) while the *built* chain is unchanged. Empty (default) = today's
    # behavior: every chain-selected plugin runs.
    disabled_plugins: list[str] = field(default_factory=list)
    # HS-36-05: LLM-assisted per-segment intent probe. When on, each routing window's
    # lexical intent scores are augmented (max) by an LLM probe of the window text, so
    # brief/paraphrased intents (e.g. an incident described as "it fell over") aren't
    # diluted below threshold and silently dropped. Off by default (opt-in, like the
    # rest of MIR); sends the window transcript to the configured intel endpoint, so it
    # honors the same provider/egress posture as the plugins. Falls back to lexical
    # scoring on any probe failure.
    intent_segment_probe_enabled: bool = False

    # HS-37-04: actuator execution policy (the governance gate). Actuators
    # PROPOSE by default; *executing* an approved proposal needs BOTH the master
    # switch on AND the actuator id on the per-project allow-list. Default-safe:
    # allow_actuators=False and an empty allow-list mean no external side effect
    # ever runs, even for an approved proposal. (Approval is always additionally
    # required — see the proposal lifecycle.)
    allow_actuators: bool = False
    allowed_actuators: list[str] = field(default_factory=list)
    # HS-38-03: the webhook write connector's host allow-list (the resolved
    # granularity for the HS-38-01 deferral). A webhook actuator may POST only to
    # a host on this list; a proposal whose target host is not a member is refused
    # before egress. Default-empty ⇒ nothing posts, even with actuators enabled.
    webhook_allowed_hosts: list[str] = field(default_factory=list)

    # Speaker diarization
    diarization_enabled: bool = False  # Identify multiple speakers in system audio
    diarize_mic: bool = False  # Also diarize mic input (for on-site meetings)
    cross_meeting_recognition: bool = True  # Recognize speakers across meetings
    similarity_threshold: float = 0.75  # Cosine similarity for speaker matching

    def __post_init__(self) -> None:
        # MIR-01 spec §9.9 — conservative validation. Reject on construction
        # so typos / drifted user-config values surface immediately rather
        # than at first meeting stop.
        if self.intent_window_seconds <= 0:
            raise ValueError(
                f"intent_window_seconds must be > 0, got {self.intent_window_seconds!r}"
            )
        if self.intent_step_seconds <= 0:
            raise ValueError(
                f"intent_step_seconds must be > 0, got {self.intent_step_seconds!r}"
            )
        if not 0.0 <= self.intent_score_threshold <= 1.0:
            raise ValueError(
                f"intent_score_threshold must be in [0.0, 1.0], "
                f"got {self.intent_score_threshold!r}"
            )
        if self.intent_hysteresis_windows < 0:
            raise ValueError(
                f"intent_hysteresis_windows must be >= 0, "
                f"got {self.intent_hysteresis_windows!r}"
            )
        if not isinstance(self.plugin_profile, str) or not self.plugin_profile.strip():
            raise ValueError(
                f"plugin_profile must be a non-empty string, "
                f"got {self.plugin_profile!r}"
            )
        if not isinstance(self.disabled_plugins, list) or not all(
            isinstance(p, str) for p in self.disabled_plugins
        ):
            raise ValueError(
                f"disabled_plugins must be a list of plugin-id strings, "
                f"got {self.disabled_plugins!r}"
            )
        # Normalize in place: strip blanks, dedupe, preserve order. An unknown
        # id is a harmless no-op at dispatch, so we don't validate against the
        # plugin registry here.
        seen: set[str] = set()
        normalized: list[str] = []
        for raw in self.disabled_plugins:
            pid = raw.strip()
            if pid and pid not in seen:
                seen.add(pid)
                normalized.append(pid)
        self.disabled_plugins = normalized

        # HS-37-04: same shape as disabled_plugins — a list of actuator plugin
        # ids explicitly cleared to execute on this project. Unknown ids are a
        # harmless no-op (an actuator that isn't registered never runs).
        if not isinstance(self.allowed_actuators, list) or not all(
            isinstance(p, str) for p in self.allowed_actuators
        ):
            raise ValueError(
                f"allowed_actuators must be a list of actuator-id strings, "
                f"got {self.allowed_actuators!r}"
            )
        seen_act: set[str] = set()
        normalized_act: list[str] = []
        for raw in self.allowed_actuators:
            aid = raw.strip()
            if aid and aid not in seen_act:
                seen_act.add(aid)
                normalized_act.append(aid)
        self.allowed_actuators = normalized_act

        # HS-38-03: the webhook host allow-list — normalized like the others, but
        # lowercased (DNS hostnames are case-insensitive). Default-empty refuses
        # every host, so a misconfigured webhook actuator posts nowhere.
        if not isinstance(self.webhook_allowed_hosts, list) or not all(
            isinstance(h, str) for h in self.webhook_allowed_hosts
        ):
            raise ValueError(
                f"webhook_allowed_hosts must be a list of host strings, "
                f"got {self.webhook_allowed_hosts!r}"
            )
        seen_host: set[str] = set()
        normalized_hosts: list[str] = []
        for raw in self.webhook_allowed_hosts:
            host = raw.strip().lower()
            if host and host not in seen_host:
                seen_host.add(host)
                normalized_hosts.append(host)
        self.webhook_allowed_hosts = normalized_hosts

    def intent_hysteresis(self) -> float:
        """Convert `intent_hysteresis_windows` (int) to the float gap value
        used by `iter_intent_transitions(hysteresis=...)`. Each window of
        damping subtracts 0.05 from the threshold gate; capped at 0.5 to
        keep hysteresis below half the score range."""
        return min(0.5, max(0.0, 0.05 * float(self.intent_hysteresis_windows)))


@dataclass
class LLMRuntimeConfig:
    """DIR-01 dictation LLM runtime config (spec §9.4)."""

    backend: str = "auto"  # "auto" | "mlx" | "llama_cpp" | "openai_compatible"
    # Suggested defaults — bring your own model (see docs/MODELS.md). These point
    # at current small instruct models; swap for whatever you run locally.
    mlx_model: str = "~/Models/mlx/Qwen3.5-8B-MLX-4bit"
    llama_cpp_model_path: str = "~/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf"
    openai_compatible_model: str = "qwen3.5-8b-instruct"
    openai_compatible_base_url: str = "http://127.0.0.1:8000/v1"
    openai_compatible_api_key_env: str = "OPENAI_API_KEY"
    openai_compatible_timeout_seconds: float = 8.0
    n_ctx: int = 2048
    n_threads: Optional[int] = None
    n_gpu_layers: int = -1
    warm_on_start: bool = False
    eviction_idle_seconds: int = 0


_KNOWN_DICTATION_STAGES = ("intent-router", "project-rewriter", "kb-enricher")
_MAX_REWRITE_PASSES = 5
_KNOWN_TARGET_PROFILE_OVERRIDES = {
    "auto",
    "claude_code",
    "codex_cli",
    "terminal_shell",
    "browser",
    "editor",
    "chat",
}


class DictationConfigError(ValueError):
    """Raised when dictation config validation fails (DIR-C-002)."""


@dataclass
class DictationPipelineConfig:
    """DIR-01 dictation pipeline config (spec §9.4). OFF by default."""

    enabled: bool = False
    stages: list[str] = field(default_factory=lambda: ["intent-router", "kb-enricher"])
    max_total_latency_ms: int = 600
    target_profile_override: str = "auto"
    # HS-39-01: number of project-rewriter passes (draft → critique → refine).
    # 1 = single-pass, byte-identical to pre-Phase-39. Extra passes are
    # latency-budget-gated and skipped before they would breach
    # `max_total_latency_ms`.
    rewrite_passes: int = 1
    # HS-39-02: consult the session correction store when routing. OFF by
    # default — with it off (or the store empty) routing is byte-identical.
    corrections_enabled: bool = False
    # HS-39-03: model-assisted target detection. When ON, a heuristic result
    # below `target_detect_llm_below` confidence is re-classified by the LLM
    # runtime (enum-constrained, degrades to the heuristic on any failure).
    # OFF by default ⇒ detection is byte-identical; a manual override always
    # wins over both the heuristic and the LLM.
    target_detect_llm_enabled: bool = False
    target_detect_llm_below: float = 0.8
    # HS-45-01: the persistent dictation journal. ON by default and local-only —
    # privacy is delivered by local + secret-filter + retention + wipe, not by
    # default-off (otherwise "it remembers" never lands). When off, no journal
    # rows are written and the typed output is byte-identical.
    journal_enabled: bool = True
    # Last-N retention cap: the journal repository prunes to this many
    # most-recent rows on each insert. Must be >= 1.
    journal_retention: int = 500

    def __post_init__(self) -> None:
        # DIR-C-002: reject unknown stage IDs at config load time so
        # typos surface immediately instead of silently no-op'ing on
        # the live path.
        unknown = [s for s in self.stages if s not in _KNOWN_DICTATION_STAGES]
        if unknown:
            raise DictationConfigError(
                f"unknown dictation stage id(s): {unknown}; "
                f"known stages are {list(_KNOWN_DICTATION_STAGES)}"
            )
        # HS-39-01: bound rewrite passes — at least one, with a sane upper
        # cap so a typo can't fan out into a runaway per-utterance LLM loop.
        if not (1 <= self.rewrite_passes <= _MAX_REWRITE_PASSES):
            raise DictationConfigError(
                f"rewrite_passes must be between 1 and {_MAX_REWRITE_PASSES}; "
                f"got {self.rewrite_passes!r}"
            )
        # HS-39-03: the model-assisted target threshold is a confidence in
        # [0.0, 1.0].
        if not (0.0 <= self.target_detect_llm_below <= 1.0):
            raise DictationConfigError(
                "target_detect_llm_below must be between 0.0 and 1.0; "
                f"got {self.target_detect_llm_below!r}"
            )
        # HS-45-01: the journal retention cap is a last-N bound; one row is the
        # floor (a zero/negative cap would prune away every write).
        if self.journal_retention < 1:
            raise DictationConfigError(
                f"journal_retention must be >= 1; got {self.journal_retention!r}"
            )
        self.target_profile_override = str(self.target_profile_override or "auto").strip().lower()
        if self.target_profile_override not in _KNOWN_TARGET_PROFILE_OVERRIDES:
            raise DictationConfigError(
                f"unknown target_profile_override {self.target_profile_override!r}; "
                f"known values are {sorted(_KNOWN_TARGET_PROFILE_OVERRIDES)}"
            )


# HS-52-02: voice command macros. A user maps a spoken keyword to a deterministic
# action; speaking the keyword fires the action instead of typing. The kinds map to
# the user's request: open a website, open/launch an app, run a shell command, type a
# snippet. OFF by default.
_KNOWN_MACRO_ACTION_KINDS = ("open_url", "launch_app", "shell", "type_text")


class VoiceMacroError(ValueError):
    """Raised when a voice command macro fails validation (HS-52-02)."""


@dataclass
class VoiceMacroAction:
    """What a macro does: one deterministic action ``kind`` + its single ``payload``.

    ``kind`` is one of ``open_url`` / ``launch_app`` / ``shell`` / ``type_text``;
    ``payload`` is that kind's single value (a URL, an app name or path, a shell
    command, or the snippet text). The transcriber never composes this — the user
    configures it, which is the consent the dispatcher acts on.
    """

    kind: str
    payload: str = ""

    def __post_init__(self) -> None:
        kind = str(self.kind or "").strip().lower()
        if kind not in _KNOWN_MACRO_ACTION_KINDS:
            raise VoiceMacroError(
                f"unknown voice macro action kind {self.kind!r}; "
                f"known kinds are {list(_KNOWN_MACRO_ACTION_KINDS)}"
            )
        self.kind = kind
        self.payload = str(self.payload or "")
        if not self.payload.strip():
            raise VoiceMacroError(f"voice macro action {kind!r} needs a non-empty payload")

    def preview(self) -> str:
        """The one plain-language line of exactly what this fires.

        Single source of truth so the card, the editor, and any audit read identically
        (design §10). Keep these strings in lockstep with the UI.
        """
        if self.kind == "open_url":
            return f"opens {self.payload}"
        if self.kind == "launch_app":
            return f"launches {self.payload}"
        if self.kind == "shell":
            return f"runs: {self.payload}"
        if self.kind == "type_text":
            return f"types: {self.payload}"
        return self.payload


@dataclass
class VoiceMacro:
    """A spoken keyword mapped to a deterministic action (HS-52-02)."""

    keyword: str
    action: VoiceMacroAction

    def __post_init__(self) -> None:
        if isinstance(self.action, dict):
            self.action = VoiceMacroAction(
                **{k: v for k, v in self.action.items() if k in {"kind", "payload"}}
            )
        elif not isinstance(self.action, VoiceMacroAction):
            raise VoiceMacroError("voice macro action must be an object")
        keyword = str(self.keyword or "").strip()
        if not keyword:
            raise VoiceMacroError("voice macro keyword must not be empty")
        self.keyword = keyword

    def matches(self, transcript: str) -> bool:
        """Deterministic whole-utterance match: the normalized transcript equals the
        normalized keyword (case-folded, trimmed). Selecting which macro, never
        composing one. The dispatcher (HS-52-04) uses this."""
        return _normalize_macro_keyword(transcript) == _normalize_macro_keyword(self.keyword)


def _normalize_macro_keyword(text: str) -> str:
    return str(text or "").strip().casefold().rstrip(".!?,")


@dataclass
class MacrosConfig:
    """Voice command macros (HS-52-02). OFF by default, byte-identical when off."""

    enabled: bool = False
    items: list[VoiceMacro] = field(default_factory=list)

    def __post_init__(self) -> None:
        coerced: list[VoiceMacro] = []
        for raw in self.items:
            if isinstance(raw, VoiceMacro):
                coerced.append(raw)
            elif isinstance(raw, dict):
                coerced.append(
                    VoiceMacro(**{k: v for k, v in raw.items() if k in {"keyword", "action"}})
                )
            else:
                raise VoiceMacroError("each voice macro must be an object")
        self.items = coerced
        self.enabled = bool(self.enabled)


@dataclass
class DictationConfig:
    """Container for the DIR-01 dictation feature."""

    pipeline: DictationPipelineConfig = field(default_factory=DictationPipelineConfig)
    runtime: LLMRuntimeConfig = field(default_factory=LLMRuntimeConfig)
    macros: MacrosConfig = field(default_factory=MacrosConfig)


@dataclass
class DeviceConfig:
    """Remote-audio-device config (AIPI-Lite & compatible clients).

    The PSK is generated lazily on first use by
    :func:`holdspeak.device_audio.ensure_device_psk` so existing
    installs that never touch the device path don't get their
    config rewritten on upgrade.
    """

    psk: str = ""


@dataclass
class PresenceConfig:
    """Desktop-presence config (HS-43-04).

    The ambient native HUD/tray is off by default and now **config-backed** — a
    UI toggle flips ``enabled`` (persisted via /api/settings); the runtime starts
    or stops the presence host live. The legacy ``HOLDSPEAK_DESKTOP_PRESENCE=1``
    environment variable is retained only as a power-user / headless override
    (it force-enables regardless of this flag), no longer the only path.
    """

    enabled: bool = False
    # HS-56-01: Qlippy, the mascot layer on the presence surface — a second
    # opt-in on top of ``enabled`` (existing presence users keep the minimal
    # ring). Off by default; unset is byte-identical.
    mascot: bool = False


@dataclass
class Config:
    """Main configuration container."""
    config_version: int = CONFIG_VERSION
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    meeting: MeetingConfig = field(default_factory=MeetingConfig)
    dictation: DictationConfig = field(default_factory=DictationConfig)
    device: DeviceConfig = field(default_factory=DeviceConfig)
    presence: PresenceConfig = field(default_factory=PresenceConfig)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from file, or create default."""
        config_path = path or CONFIG_FILE

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
            )

            return cls(
                config_version=config_version,
                hotkey=_coerce(HotkeyConfig, data.get("hotkey", {}) or {}, section="hotkey"),
                model=_coerce(ModelConfig, data.get("model", {}) or {}, section="model"),
                ui=_coerce(UIConfig, data.get("ui", {}) or {}, section="ui"),
                meeting=_coerce(MeetingConfig, data.get("meeting", {}) or {}, section="meeting"),
                dictation=dictation,
                device=_coerce(DeviceConfig, data.get("device", {}) or {}, section="device"),
                presence=_coerce(PresenceConfig, data.get("presence", {}) or {}, section="presence"),
            )
        except Exception as exc:
            # Last-resort fallback for a genuinely broken config (bad JSON, wrong
            # top-level type, or a value a sub-config's __post_init__ rejects).
            # Unknown/legacy keys no longer reach here — _coerce drops them — so
            # this should be rare; log it rather than swallowing silently.
            logger.warning(
                "config: failed to load %s (%s); using defaults", config_path, exc
            )
            return cls()

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        config_path = path or CONFIG_FILE
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


# Key mapping from config names to pynput keys
KEY_MAP = {
    "alt_r": "Key.alt_r",
    "alt_l": "Key.alt_l",
    "ctrl_r": "Key.ctrl_r",
    "ctrl_l": "Key.ctrl_l",
    "cmd_r": "Key.cmd_r",
    "cmd_l": "Key.cmd_l",
    "shift_r": "Key.shift_r",
    "shift_l": "Key.shift_l",
    "caps_lock": "Key.caps_lock",
    "fn": "Key.fn",
    "f1": "Key.f1",
    "f2": "Key.f2",
    "f3": "Key.f3",
    "f4": "Key.f4",
    "f5": "Key.f5",
    "f6": "Key.f6",
    "f7": "Key.f7",
    "f8": "Key.f8",
    "f9": "Key.f9",
    "f10": "Key.f10",
    "f11": "Key.f11",
    "f12": "Key.f12",
}

# Display names for keys
KEY_DISPLAY = {
    "alt_r": "⌥R",
    "alt_l": "⌥L",
    "ctrl_r": "⌃R",
    "ctrl_l": "⌃L",
    "cmd_r": "⌘R",
    "cmd_l": "⌘L",
    "shift_r": "⇧R",
    "shift_l": "⇧L",
    "caps_lock": "⇪",
    "fn": "fn",
    "f1": "F1",
    "f2": "F2",
    "f3": "F3",
    "f4": "F4",
    "f5": "F5",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
}


def get_available_keys() -> list[tuple[str, str]]:
    """Get list of available hotkeys as (key_name, display_name) tuples."""
    return [(k, KEY_DISPLAY.get(k, k)) for k in KEY_MAP.keys()]
