"""Model and LLM runtime configuration (HS-117-12).

Extracted from the monolithic ``holdspeak/config.py``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """Whisper model configuration."""
    name: str = "base"
    warm_on_start: bool = True
    backend: str = "auto"  # "auto" | "mlx" | "faster-whisper"
    # HS-59: pin transcription to one Whisper language ("pl", "de", ...) or
    # "auto" for Whisper's own per-utterance detection (today's behavior).
    # One knob serves dictation, meetings, and import: they share the
    # Transcriber. Validated against holdspeak/languages.py at the
    # settings boundary.
    language: str = "auto"
    # Available: tiny, base, small, medium, large
    # HS-25-05: hard ceiling (seconds) on a single transcription so a hung model
    # can't freeze the pipeline. Generous by default to never clip a legitimate
    # long utterance; <= 0 disables. On timeout the utterance is abandoned and
    # the pipeline returns to idle for the next one.
    transcribe_timeout_seconds: float = 120.0
    # HS-131-09 (Sol Amendment 4): the owner's EXPLICIT authority for loading a
    # local speech model BEFORE any admitted session exists. A pre-session warm
    # is a real model invocation with no session to parent it, so it runs as the
    # narrow ``local-model-preload`` service under
    # ``configured-local-model-preload:<this value>``. Blank (the default) is not
    # a refusal of warm-on-start: the preload simply DEFERS to the first admitted
    # session, or refuses before any MLX dispatch when a caller demands warmup.
    # Never inferred from local process identity.
    #
    # The value must NAME this model configuration's revision — exactly
    # ``holdspeak.speech_session.model_config_revision(config.model)`` (a
    # ``sha256:…`` hash of name/backend/language/transcribe ceiling). An arbitrary
    # nonblank string is refused ``local_model_preload_authority_mismatched``, and
    # the refusal states the revision to set, so the authority is bound to ONE
    # configuration instead of standing forever.
    local_model_preload_authority: str = ""

    def __post_init__(self) -> None:
        self.local_model_preload_authority = str(
            self.local_model_preload_authority or ""
        ).strip()


@dataclass
class LLMRuntimeConfig:
    """DIR-01 dictation LLM runtime config (spec $9.4)."""

    backend: str = "auto"  # "auto" | "mlx" | "llama_cpp" | "openai_compatible"
    # Suggested defaults -- bring your own model (see docs/MODELS.md). These point
    # at current small instruct models; swap for whatever you run locally.
    mlx_model: str = "~/Models/mlx/Qwen3.5-8B-MLX-4bit"
    llama_cpp_model_path: str = "~/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf"
    # DEAD legacy fallbacks (HS-112-01): read only by the one-time migration
    # in `migrate_legacy_endpoints`, never by feature code.
    openai_compatible_model: str = "qwen3.5-8b-instruct"
    openai_compatible_base_url: str = "http://127.0.0.1:8000/v1"
    openai_compatible_api_key_env: str = "OPENAI_API_KEY"
    # The ONE pointer for the dictation LLM leg: an InferenceTarget id in the
    # profiles table. None = hub default (the configured local backend). An
    # adopted target also selects the openai_compatible backend; a dangling
    # id degrades honestly at resolution time, never a crash.
    profile_id: Optional[str] = None
    openai_compatible_timeout_seconds: float = 8.0
    n_ctx: int = 2048
    n_threads: Optional[int] = None
    n_gpu_layers: int = -1
    warm_on_start: bool = False
    eviction_idle_seconds: int = 0

    def __post_init__(self) -> None:
        # HS-112-01: one pointer sentinel -- None means hub default.
        self.profile_id = str(self.profile_id or "").strip() or None
