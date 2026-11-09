"""Meeting intelligence extraction for local and OpenAI-compatible providers (HS-34-04 package).

Phase 34 split the 1,066-line intel.py module into this package:
models (dataclasses + constants) <- parsing (JSON coercion) / providers
(resolution + egress posture) <- engine (MeetingIntel). The optional-dependency
import head (Llama / OpenAI) lives here so tests can monkeypatch
holdspeak.intel.OpenAI / holdspeak.intel.Llama; providers/engine read them via
the package. The full public surface is re-exported, so
`from holdspeak.intel import X` is unchanged."""

from __future__ import annotations

from ..logging_config import get_logger

log = get_logger("intel")


def _import_llama() -> dict:
    try:
        from llama_cpp import Llama
    except Exception as exc:  # pragma: no cover
        # This dependency is optional; avoid noisy errors during normal voice-typing usage.
        log.debug(f"llama_cpp not available: {exc}")
        return {"Llama": None, "_IMPORT_ERROR": exc}
    log.debug("llama_cpp imported successfully")
    return {"Llama": Llama, "_IMPORT_ERROR": None}


def _import_openai() -> dict:
    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover
        log.debug(f"openai not available: {exc}")
        return {"OpenAI": None, "_OPENAI_IMPORT_ERROR": exc}
    return {"OpenAI": OpenAI, "_OPENAI_IMPORT_ERROR": None}


#: The optional clients, imported at first read (2026-11-09): ``openai`` alone
#: took 0.3 s of the hub's start, and the hub builds no client at start.
_LAZY = {"Llama": _import_llama, "_IMPORT_ERROR": _import_llama,
         "OpenAI": _import_openai, "_OPENAI_IMPORT_ERROR": _import_openai}


def __getattr__(name: str):
    load = _LAZY.get(name)
    if load is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    for key, value in load().items():
        globals().setdefault(key, value)  # a test's patch already set stays
    return globals()[name]


from .models import (  # noqa: E402
    ActionItem,
    DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    DEFAULT_INTEL_CLOUD_MODEL,
    DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS,
    DEFAULT_INTEL_MODEL_PATH,
    DEFAULT_INTEL_PROVIDER,
    IntelResult,
    MeetingIntelError,
    SELF_HOSTED_CLOUD_API_KEY_PLACEHOLDER,
    VALID_INTEL_PROVIDERS,
    _generate_action_item_id,
)
from .parsing import (  # noqa: E402
    INTEL_JSON_SCHEMA,
    INTEL_SCHEMA,
    _coerce_action_items,
    _coerce_decisions,
    _coerce_str_list,
    _describe_cloud_exception,
    _extract_json,
    _extract_openai_message_text,
    _extract_status_code,
    _json_only_messages,
    intel_response_format,
)
from .providers import (  # noqa: E402
    _effective_cloud_api_key,
    _is_self_hosted_base_url,
    _normalize_provider,
    _resolve_cloud_api_key,
    _validate_base_url,
    get_cloud_intel_runtime_status,
    get_intel_runtime_status,
    get_local_intel_runtime_status,
    intel_egress_posture,
    resolve_intel_provider,
    resolve_llm_capability,
    resolve_meeting_placement,
)
from .engine import MeetingIntel  # noqa: E402

__all__ = [
    "ActionItem",
    "DEFAULT_INTEL_CLOUD_API_KEY_ENV",
    "DEFAULT_INTEL_CLOUD_MODEL",
    "DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS",
    "DEFAULT_INTEL_MODEL_PATH",
    "DEFAULT_INTEL_PROVIDER",
    "INTEL_JSON_SCHEMA",
    "INTEL_SCHEMA",
    "IntelResult",
    "Llama",
    "MeetingIntel",
    "MeetingIntelError",
    "OpenAI",
    "SELF_HOSTED_CLOUD_API_KEY_PLACEHOLDER",
    "VALID_INTEL_PROVIDERS",
    "_coerce_action_items",
    "_coerce_decisions",
    "_coerce_str_list",
    "_describe_cloud_exception",
    "_effective_cloud_api_key",
    "_extract_json",
    "_extract_openai_message_text",
    "_extract_status_code",
    "_generate_action_item_id",
    "_is_self_hosted_base_url",
    "_json_only_messages",
    "_normalize_provider",
    "_resolve_cloud_api_key",
    "_validate_base_url",
    "get_cloud_intel_runtime_status",
    "get_intel_runtime_status",
    "get_local_intel_runtime_status",
    "intel_egress_posture",
    "intel_response_format",
    "log",
    "resolve_intel_provider",
    "resolve_llm_capability",
    "resolve_meeting_placement",
]
