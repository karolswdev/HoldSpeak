"""Typed contracts for MIR intent routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PLUGIN_RUN_STATUSES: frozenset[str] = frozenset(
    {"success", "error", "timeout", "deduped", "blocked", "queued"}
)


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
class IntentScore:
    """Multi-label intent scoring output for a single window (MIR-F-002)."""

    window_id: str
    scores: dict[str, float]
    threshold: float

    def labels_above_threshold(self) -> list[str]:
        return sorted(
            (label for label, score in self.scores.items() if score >= self.threshold),
            key=lambda lbl: (-self.scores[lbl], lbl),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "scores": dict(self.scores),
            "threshold": float(self.threshold),
        }


@dataclass(frozen=True)
class IntentTransition:
    """Event emitted when the dominant active-intent set changes (MIR-F-005)."""

    window_id: str
    previous_active: list[str]
    current_active: list[str]
    added: list[str]
    removed: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "previous_active": list(self.previous_active),
            "current_active": list(self.current_active),
            "added": list(self.added),
            "removed": list(self.removed),
        }


@dataclass(frozen=True)
class PluginRun:
    """Canonical record of one plugin execution against a window (MIR-D-003)."""

    plugin_id: str
    plugin_version: str
    window_id: str
    meeting_id: str
    profile: str
    status: str
    idempotency_key: str
    started_at: float
    finished_at: float
    duration_ms: float
    error: str | None = None
    output: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.status not in PLUGIN_RUN_STATUSES:
            raise ValueError(
                f"PluginRun.status={self.status!r} not in {sorted(PLUGIN_RUN_STATUSES)}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "window_id": self.window_id,
            "meeting_id": self.meeting_id,
            "profile": self.profile,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "started_at": float(self.started_at),
            "finished_at": float(self.finished_at),
            "duration_ms": float(self.duration_ms),
            "error": self.error,
            "output": dict(self.output) if isinstance(self.output, dict) else None,
        }


@dataclass(frozen=True)
class ArtifactLineage:
    """Lineage of one synthesized artifact back to its source windows + plugin runs (MIR-D-004, MIR-F-011)."""

    artifact_id: str
    meeting_id: str
    window_ids: list[str]
    plugin_run_keys: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "meeting_id": self.meeting_id,
            "window_ids": list(self.window_ids),
            "plugin_run_keys": list(self.plugin_run_keys),
        }


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
