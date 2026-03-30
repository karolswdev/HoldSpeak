"""Typed contracts for MIR intent routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class IntentWindow:
    """Rolling transcript window used for intent routing."""

    window_id: str
    meeting_id: str
    start_seconds: float
    end_seconds: float
    transcript: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    """Deterministic routing output for one intent window."""

    profile: str
    active_intents: list[str]
    plugin_chain: list[str]
    intent_scores: dict[str, float]
    threshold: float
    hysteresis_applied: bool
    override_intents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "active_intents": list(self.active_intents),
            "plugin_chain": list(self.plugin_chain),
            "intent_scores": dict(self.intent_scores),
            "threshold": float(self.threshold),
            "hysteresis_applied": bool(self.hysteresis_applied),
            "override_intents": list(self.override_intents),
        }
