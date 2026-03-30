"""Deterministic MIR routing helpers."""

from __future__ import annotations

from threading import Lock
from typing import Mapping, Optional

from .contracts import RouteDecision
from .signals import extract_intent_signals

SUPPORTED_INTENTS: tuple[str, ...] = (
    "architecture",
    "delivery",
    "product",
    "incident",
    "comms",
)

DEFAULT_PROFILE = "balanced"
DEFAULT_INTENT_THRESHOLD = 0.6
DEFAULT_HYSTERESIS = 0.05

PROFILE_PLUGIN_BASE_CHAINS: dict[str, list[str]] = {
    "balanced": ["requirements_extractor", "action_owner_enforcer"],
    "architect": ["requirements_extractor", "mermaid_architecture", "adr_drafter"],
    "delivery": ["action_owner_enforcer", "milestone_planner", "dependency_mapper"],
    "product": ["scope_guard", "customer_signal_extractor"],
    "incident": ["incident_timeline", "risk_heatmap", "stakeholder_update_drafter"],
}

_INTENT_PLUGIN_CHAIN: dict[str, list[str]] = {
    "architecture": ["requirements_extractor", "mermaid_architecture", "adr_drafter"],
    "delivery": ["action_owner_enforcer", "milestone_planner", "dependency_mapper"],
    "product": ["scope_guard", "customer_signal_extractor"],
    "incident": ["incident_timeline", "runbook_delta"],
    "comms": ["stakeholder_update_drafter", "decision_announcement_drafter"],
}

_COUNTER_LOCK = Lock()
_ROUTER_COUNTERS: dict[str, int] = {
    "routed_windows": 0,
    "dropped_windows": 0,
}


def reset_router_counters() -> None:
    with _COUNTER_LOCK:
        _ROUTER_COUNTERS["routed_windows"] = 0
        _ROUTER_COUNTERS["dropped_windows"] = 0


def get_router_counters() -> dict[str, int]:
    with _COUNTER_LOCK:
        return {
            "routed_windows": int(_ROUTER_COUNTERS["routed_windows"]),
            "dropped_windows": int(_ROUTER_COUNTERS["dropped_windows"]),
        }


def _record_route_counter(*, dropped: bool) -> None:
    with _COUNTER_LOCK:
        if dropped:
            _ROUTER_COUNTERS["dropped_windows"] += 1
        else:
            _ROUTER_COUNTERS["routed_windows"] += 1


def available_profiles() -> list[str]:
    return list(PROFILE_PLUGIN_BASE_CHAINS.keys())


def normalize_profile(profile: Optional[str]) -> str:
    candidate = str(profile or "").strip().lower()
    if candidate in PROFILE_PLUGIN_BASE_CHAINS:
        return candidate
    return DEFAULT_PROFILE


def normalize_intent_scores(intent_scores: Optional[Mapping[str, object]]) -> dict[str, float]:
    normalized = {intent: 0.0 for intent in SUPPORTED_INTENTS}
    if not isinstance(intent_scores, Mapping):
        return normalized

    for key, value in intent_scores.items():
        intent = str(key or "").strip().lower()
        if intent not in normalized:
            continue
        try:
            score = float(value)
        except Exception:
            score = 0.0
        normalized[intent] = min(1.0, max(0.0, score))
    return normalized


def normalize_override_intents(override_intents: Optional[list[str]]) -> list[str]:
    if not isinstance(override_intents, list):
        return []
    unique: list[str] = []
    for raw in override_intents:
        intent = str(raw or "").strip().lower()
        if intent in SUPPORTED_INTENTS and intent not in unique:
            unique.append(intent)
    return unique


def select_active_intents(
    intent_scores: Optional[Mapping[str, object]],
    *,
    threshold: float = DEFAULT_INTENT_THRESHOLD,
    previous_intents: Optional[list[str]] = None,
    hysteresis: float = DEFAULT_HYSTERESIS,
) -> list[str]:
    scores = normalize_intent_scores(intent_scores)
    gate = min(1.0, max(0.0, float(threshold)))
    hysteresis_floor = min(1.0, max(0.0, gate - max(0.0, float(hysteresis))))
    previous = set(normalize_override_intents(previous_intents))

    active: list[str] = []
    for intent in SUPPORTED_INTENTS:
        score = scores[intent]
        if score >= gate:
            active.append(intent)
            continue
        if intent in previous and score >= hysteresis_floor:
            active.append(intent)

    active.sort(key=lambda intent: (-scores[intent], intent))
    return active


def _dedupe_keep_order(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def build_plugin_chain(profile: str, active_intents: list[str]) -> list[str]:
    normalized_profile = normalize_profile(profile)
    chain = list(PROFILE_PLUGIN_BASE_CHAINS.get(normalized_profile, []))
    for intent in active_intents:
        chain.extend(_INTENT_PLUGIN_CHAIN.get(intent, []))
    if not chain:
        chain = ["requirements_extractor"]
    return _dedupe_keep_order(chain)


def preview_route(
    *,
    profile: Optional[str],
    intent_scores: Optional[Mapping[str, object]],
    threshold: float = DEFAULT_INTENT_THRESHOLD,
    previous_intents: Optional[list[str]] = None,
    override_intents: Optional[list[str]] = None,
) -> RouteDecision:
    normalized_profile = normalize_profile(profile)
    normalized_scores = normalize_intent_scores(intent_scores)
    override = normalize_override_intents(override_intents)

    if override:
        active_intents = list(override)
        hysteresis_applied = False
    else:
        active_intents = select_active_intents(
            normalized_scores,
            threshold=threshold,
            previous_intents=previous_intents,
        )
        prev = set(normalize_override_intents(previous_intents))
        hysteresis_applied = any(intent in prev for intent in active_intents)

    decision = RouteDecision(
        profile=normalized_profile,
        active_intents=active_intents,
        plugin_chain=build_plugin_chain(normalized_profile, active_intents),
        intent_scores=normalized_scores,
        threshold=min(1.0, max(0.0, float(threshold))),
        hysteresis_applied=hysteresis_applied,
        override_intents=override,
    )
    _record_route_counter(dropped=len(decision.active_intents) == 0)
    return decision


def preview_route_from_transcript(
    *,
    profile: Optional[str],
    transcript: str | None,
    tags: Optional[list[str]] = None,
    threshold: float = DEFAULT_INTENT_THRESHOLD,
    previous_intents: Optional[list[str]] = None,
    override_intents: Optional[list[str]] = None,
) -> RouteDecision:
    """Convenience wrapper: derive intent scores from transcript then preview route."""
    return preview_route(
        profile=profile,
        intent_scores=extract_intent_signals(transcript, tags=tags),
        threshold=threshold,
        previous_intents=previous_intents,
        override_intents=override_intents,
    )
