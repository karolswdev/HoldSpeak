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

try:
    from llama_cpp import Llama

    log.debug("llama_cpp imported successfully")
except Exception as exc:  # pragma: no cover
    Llama = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
    # This dependency is optional; avoid noisy errors during normal voice-typing usage.
    log.debug(f"llama_cpp not available: {exc}")
else:  # pragma: no cover
    _IMPORT_ERROR = None

try:
    from openai import OpenAI
except Exception as exc:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = exc
    log.debug(f"openai not available: {exc}")
else:  # pragma: no cover
    _OPENAI_IMPORT_ERROR = None

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
    _coerce_action_items,
    _coerce_str_list,
    _describe_cloud_exception,
    _extract_json,
    _extract_openai_message_text,
    _extract_status_code,
    _json_only_messages,
)
from .providers import (  # noqa: E402
    _effective_cloud_api_key,
    _is_self_hosted_base_url,
    _normalize_provider,
    _resolve_cloud_api_key,
    _validate_base_url,
    build_configured_meeting_intel,
    get_cloud_intel_runtime_status,
    get_intel_runtime_status,
    get_local_intel_runtime_status,
    intel_egress_posture,
    resolve_intel_provider,
    resolve_llm_capability,
)
from .engine import MeetingIntel  # noqa: E402

__all__ = [
    "ActionItem",
    "DEFAULT_INTEL_CLOUD_API_KEY_ENV",
    "DEFAULT_INTEL_CLOUD_MODEL",
    "DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS",
    "DEFAULT_INTEL_MODEL_PATH",
    "DEFAULT_INTEL_PROVIDER",
    "IntelResult",
    "Llama",
    "MeetingIntel",
    "MeetingIntelError",
    "OpenAI",
    "SELF_HOSTED_CLOUD_API_KEY_PLACEHOLDER",
    "VALID_INTEL_PROVIDERS",
    "_coerce_action_items",
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
    "build_configured_meeting_intel",
    "get_cloud_intel_runtime_status",
    "get_intel_runtime_status",
    "get_local_intel_runtime_status",
    "intel_egress_posture",
    "log",
    "resolve_intel_provider",
    "resolve_llm_capability",
]
