"""Plugin and routing primitives for MIR controls."""

from .contracts import IntentWindow, RouteDecision
from .builtin import DeterministicPlugin, register_builtin_plugins
from .host import DeferredPluginRun, PluginHost, PluginRunResult, build_idempotency_key
from .queue import (
    RETRY_BASE_SECONDS as PLUGIN_QUEUE_RETRY_BASE_SECONDS,
    RETRY_MAX_ATTEMPTS as PLUGIN_QUEUE_RETRY_MAX_ATTEMPTS,
    RETRY_MAX_SECONDS as PLUGIN_QUEUE_RETRY_MAX_SECONDS,
    compute_retry_delay_seconds,
    drain_plugin_run_queue,
    process_next_plugin_run_job,
)
from .router import (
    DEFAULT_INTENT_THRESHOLD,
    DEFAULT_PROFILE,
    PROFILE_PLUGIN_BASE_CHAINS,
    SUPPORTED_INTENTS,
    available_profiles,
    get_router_counters,
    normalize_profile,
    preview_route,
    preview_route_from_transcript,
    reset_router_counters,
    select_active_intents,
)
from .signals import SUPPORTED_INTENTS as SIGNAL_INTENTS, extract_intent_signals
from .synthesis import synthesize_meeting_artifacts

__all__ = [
    "DEFAULT_INTENT_THRESHOLD",
    "DEFAULT_PROFILE",
    "PROFILE_PLUGIN_BASE_CHAINS",
    "DeterministicPlugin",
    "DeferredPluginRun",
    "PluginHost",
    "PluginRunResult",
    "SUPPORTED_INTENTS",
    "IntentWindow",
    "RouteDecision",
    "build_idempotency_key",
    "compute_retry_delay_seconds",
    "drain_plugin_run_queue",
    "get_router_counters",
    "SIGNAL_INTENTS",
    "available_profiles",
    "extract_intent_signals",
    "normalize_profile",
    "preview_route",
    "preview_route_from_transcript",
    "register_builtin_plugins",
    "reset_router_counters",
    "select_active_intents",
    "synthesize_meeting_artifacts",
    "process_next_plugin_run_job",
    "PLUGIN_QUEUE_RETRY_BASE_SECONDS",
    "PLUGIN_QUEUE_RETRY_MAX_SECONDS",
    "PLUGIN_QUEUE_RETRY_MAX_ATTEMPTS",
]
