"""Meeting and dictation pipeline configuration (HS-117-12).

Extracted from the monolithic ``holdspeak/config.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..errors import ConfigError
from .model import LLMRuntimeConfig
from .ui import MacrosConfig


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
    # endpoint -- self-hosted LAN, Ollama, vLLM, llama.cpp-server, or a real cloud
    # API; set intel_cloud_base_url) | "auto" (local-first, then the endpoint).
    intel_provider: str = "local"
    # Suggested default -- bring your own GGUF (see docs/MODELS.md). Names are a
    # moving target; this points at a current small/mid instruct model.
    intel_realtime_model: str = "~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf"
    intel_temperature: float = 0.2
    intel_summary_model: Optional[str] = None  # Falls back to realtime if None
    intel_deferred_enabled: bool = True  # Queue intel when no suitable local model is available
    # HS-139-01: intel_queue_poll_seconds deleted — dead setting (never
    # threaded to IntelQueue; queue uses hardcoded 120.0 default).
    intel_retry_base_seconds: int = 30  # Initial deferred-intel retry delay
    intel_retry_max_seconds: int = 900  # Maximum deferred-intel retry delay
    intel_retry_max_attempts: int = 6  # Attempts before marking deferred intel as failed
    # HS-139-01: intel_retry_failure_alert_percent and
    # intel_retry_failure_hysteresis_minutes deleted — dead settings
    # (never threaded to IntelQueue; queue uses hardcoded constants).
    intel_retry_failure_webhook_url: Optional[str] = None  # Optional POST endpoint for sustained failure alerts
    intel_retry_failure_webhook_header_name: Optional[str] = None  # Optional custom header name for alert webhooks
    intel_retry_failure_webhook_header_value: Optional[str] = None  # Optional custom header value for alert webhooks
    # DEAD legacy fallbacks (HS-112-01): read only by the one-time migration
    # in `migrate_legacy_endpoints`, never by feature code.
    intel_cloud_model: str = "gpt-5-mini"
    intel_cloud_api_key_env: str = "OPENAI_API_KEY"
    intel_cloud_base_url: Optional[str] = None
    intel_cloud_reasoning_effort: Optional[str] = None
    intel_cloud_store: bool = False
    # The ONE pointer for the meeting-intel cloud leg: an InferenceTarget id
    # in the profiles table. None = hub default. A dangling id degrades
    # honestly at resolution time, never a crash.
    intel_profile_id: Optional[str] = None

    # Web dashboard
    # HS-139-02: web_auto_open deleted — default true, nobody toggles
    # this. Hardcoded at the single consumer (web_runtime.py:581).
    # Owner web-runtime credential (HS-25-02, hardened HS-106-02). Generated
    # lazily and required for owner authority on every bind, including loopback.
    # The auto-open URL bootstraps it without a visible login step.
    web_auth_token: str = ""
    mir_enabled: bool = True  # Enable multi-intent routing controls in web runtime
    # The ONE meeting routing profile (HS-130-05, HS-134-08): balanced,
    # architect, delivery, product, incident. Read by
    # `effective_routing_profile()`, which both the runtime and doctor go
    # through so they can never name different values.
    routing_profile: str = "balanced"

    # MIR-01 routing pipeline gating + tuning (spec $9.9). The pipeline runs
    # at MeetingSession.stop() finalization (HS-2-06) when enabled. Defaults
    # are conservative (off + matching the in-code defaults of
    # build_intent_windows / DEFAULT_INTENT_THRESHOLD / DEFAULT_HYSTERESIS).
    intent_router_enabled: bool = False  # off by default -- opt-in
    intent_window_seconds: int = 90      # rolling-window length
    intent_step_seconds: int = 30        # rolling-window step
    intent_score_threshold: float = 0.6  # gate above which an intent is "active"
    intent_hysteresis_windows: int = 1   # damping windows; converted to float via intent_hysteresis()
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
    # switch on AND the actuator id on the per-project allow-list.
    # HS-139-08: permissive defaults (owner ruling: ledger-not-gate).
    # allow_actuators=True with a wildcard allow-list so actuators run by
    # default. Approval is always additionally required (the proposal lifecycle).
    allow_actuators: bool = True
    allowed_actuators: list[str] = field(default_factory=lambda: ["*"])
    # HS-38-03: the webhook write connector's host allow-list (the resolved
    # granularity for the HS-38-01 deferral). A webhook actuator may POST only to
    # a host on this list; a proposal whose target host is not a member is refused
    # before egress.
    # HS-139-08: permissive default — wildcard means any host is allowed.
    webhook_allowed_hosts: list[str] = field(default_factory=lambda: ["*"])
    # HS-61-01: the Send-to-Slack incoming-webhook URL. Default-empty = the
    # feature is invisible (no aftercare buttons, the export route refuses).
    # Setting it is the consent for that URL's host: the Slack connector's
    # manifest allow-lists exactly this host, nothing else. Slack treats
    # webhook URLs as credentials -- this value never rides a proposal payload,
    # a broadcast, or a non-settings API response.
    slack_webhook_url: str = ""

    # HSM-14: a generic outbound webhook for the iPad desk's Webhook connector
    # (Discord / Zapier / n8n / any endpoint). Default-empty = the connector is
    # offline. Same credential rule as Slack: the URL stays on the host, its
    # host is the only thing the webhook connector's manifest allow-lists, and
    # it never rides a proposal payload, a broadcast, or a non-settings response.
    companion_webhook_url: str = ""

    # HSM-14: the default repo (owner/name) the iPad desk's GitHub connector files
    # issues into via `gh issue create`. Auth is the host's already-authenticated
    # local `gh` -- no token is stored or crosses the wire. Default-empty = the
    # connector is offline.
    companion_github_repo: str = ""

    # Speaker diarization
    diarization_enabled: bool = False  # Identify multiple speakers in system audio
    diarize_mic: bool = False  # Also diarize mic input (for on-site meetings)
    cross_meeting_recognition: bool = True  # Recognize speakers across meetings
    similarity_threshold: float = 0.75  # Cosine similarity for speaker matching

    def __post_init__(self) -> None:
        # HS-112-01: one pointer sentinel -- None means hub default.
        self.intel_profile_id = (
            str(self.intel_profile_id or "").strip() or None
        )
        # MIR-01 spec $9.9 -- conservative validation. Reject on construction
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
        if not isinstance(self.routing_profile, str) or not self.routing_profile.strip():
            raise ValueError(
                f"routing_profile must be a non-empty string, "
                f"got {self.routing_profile!r}"
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

        # HS-37-04: same shape as disabled_plugins -- a list of actuator plugin
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

        # HS-38-03: the webhook host allow-list -- normalized like the others, but
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

        # HS-61-01: the Slack webhook URL -- empty is fine (the feature is
        # off); anything else must pass THE rule (https with a host; plain
        # http for loopback only), the same one the settings boundary
        # enforces with a 400. Imported lazily: config loads everywhere and
        # the export module pulls in the plugin stack.
        slack_url = str(self.slack_webhook_url or "").strip()
        if slack_url:
            from ..slack_export import slack_webhook_host

            try:
                slack_webhook_host(slack_url)
            except ValueError as exc:
                raise ValueError(f"slack_webhook_url: {exc}") from exc
        self.slack_webhook_url = slack_url

    def effective_routing_profile(self) -> str:
        """The ONE meeting routing profile (HS-130-05) — see the module-level
        :func:`effective_routing_profile`. Sugar for ``self``."""
        return effective_routing_profile(self)

    def intent_hysteresis(self) -> float:
        """Convert `intent_hysteresis_windows` (int) to the float gap value
        used by `iter_intent_transitions(hysteresis=...)`. Each window of
        damping subtracts 0.05 from the threshold gate; capped at 0.5 to
        keep hysteresis below half the score range."""
        return min(0.5, max(0.0, 0.05 * float(self.intent_hysteresis_windows)))


_ROUTING_PROFILE_DEFAULT = "balanced"


def effective_routing_profile(meeting_cfg: object) -> str:
    """The ONE meeting routing profile accessor (HS-130-05, HS-134-08).

    Reads ``routing_profile`` — the single canonical field after the
    legacy ``mir_profile``/``plugin_profile`` pair was deleted (HS-134-08,
    pre-release cleanup). Reads via ``getattr`` so it works on a real
    ``MeetingConfig`` or any config-shaped object.
    """
    rp = str(getattr(meeting_cfg, "routing_profile", "") or "").strip()
    return rp or _ROUTING_PROFILE_DEFAULT


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


class DictationConfigError(ConfigError):
    """Raised when dictation config validation fails (DIR-C-002)."""

    code: str = "DICTATION_CONFIG_ERROR"


# HS-59-02: attach modes for spoken-symbol entries, mirroring the built-in
# punctuation tables' spacing semantics ("none" = plain replacement, the
# safe default: spacing is left exactly as spoken).
VALID_SYMBOL_ATTACH = ("none", "left", "right", "both")


def validate_spoken_symbols(raw: object) -> list[dict]:
    """Validate `dictation.spoken_symbols` entries; raise actionably.

    Each entry is ``{"spoken": str, "symbol": str, "attach": mode}``. The
    spoken phrase and symbol must be non-empty; attach defaults to "none".
    """
    if raw in (None, ""):
        return []
    if not isinstance(raw, list):
        raise DictationConfigError("dictation.spoken_symbols must be a list")
    validated: list[dict] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise DictationConfigError(
                f"spoken_symbols[{index}] must be an object with spoken/symbol/attach"
            )
        spoken = str(item.get("spoken", "")).strip()
        symbol = str(item.get("symbol", ""))
        attach = str(item.get("attach", "none") or "none").strip().lower()
        if not spoken:
            raise DictationConfigError(
                f"spoken_symbols[{index}]: the spoken phrase must not be empty"
            )
        if not symbol:
            raise DictationConfigError(
                f"spoken_symbols[{index}] ({spoken!r}): the symbol must not be empty"
            )
        if attach not in VALID_SYMBOL_ATTACH:
            raise DictationConfigError(
                f"spoken_symbols[{index}] ({spoken!r}): attach must be one of "
                f"{', '.join(VALID_SYMBOL_ATTACH)}"
            )
        key = spoken.lower()
        if key in seen:
            raise DictationConfigError(
                f"spoken_symbols: duplicate spoken phrase {spoken!r}"
            )
        seen.add(key)
        validated.append({"spoken": spoken, "symbol": symbol, "attach": attach})
    return validated


@dataclass
class DictationPipelineConfig:
    """DIR-01 dictation pipeline config (spec $9.4). OFF by default."""

    # HS-139-02: pinned to True (was False). The pipeline is core
    # functionality; toggling it off breaks dictation. Removed from the
    # settings surface and service-writable set.
    enabled: bool = True
    stages: list[str] = field(default_factory=lambda: ["intent-router", "kb-enricher"])
    max_total_latency_ms: int = 600
    target_profile_override: str = "auto"
    # HS-39-01: number of project-rewriter passes (draft -> critique -> refine).
    # 1 = single-pass, byte-identical to pre-Phase-39. Extra passes are
    # latency-budget-gated and skipped before they would breach
    # `max_total_latency_ms`.
    rewrite_passes: int = 1
    # HS-39-02: consult the session correction store when routing. OFF by
    # default -- with it off (or the store empty) routing is byte-identical.
    # HS-139-02: pinned to True (was False). Correction memory is a
    # pillar feature. Removed from the settings surface.
    corrections_enabled: bool = True
    # HS-39-03: model-assisted target detection. When ON, a heuristic result
    # below `target_detect_llm_below` confidence is re-classified by the LLM
    # runtime (enum-constrained, degrades to the heuristic on any failure).
    # OFF by default => detection is byte-identical; a manual override always
    # wins over both the heuristic and the LLM.
    target_detect_llm_enabled: bool = False
    target_detect_llm_below: float = 0.8
    # HS-45-01: the persistent dictation journal. ON by default and local-only --
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
        # HS-39-01: bound rewrite passes -- at least one, with a sane upper
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


@dataclass
class DictationConfig:
    """Container for the DIR-01 dictation feature."""

    pipeline: DictationPipelineConfig = field(default_factory=DictationPipelineConfig)
    runtime: LLMRuntimeConfig = field(default_factory=LLMRuntimeConfig)
    macros: MacrosConfig = field(default_factory=MacrosConfig)
    # HS-59-02: the spoken-symbol dictionary -- user-defined spoken->symbol
    # entries merged over the built-in punctuation table (user wins).
    # Default empty = byte-identical typing.
    spoken_symbols: list = field(default_factory=list)
    # HS-75-01: preview before it types (backlog candidate M). When on, a
    # finished dictation arms a one-shot preview (the P60 wake grammar)
    # instead of typing; /api/dictation/preview/type commits it. Off by
    # default = today's behavior, byte-identical.
    preview_before_type: bool = False

    def __post_init__(self) -> None:
        self.spoken_symbols = validate_spoken_symbols(self.spoken_symbols)


