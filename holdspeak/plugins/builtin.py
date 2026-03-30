"""Deterministic built-in MIR plugins used by the runtime host."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .host import PluginHost


def _snippet(text: str, *, limit: int = 140) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 3)].rstrip() + "..."


@dataclass
class DeterministicPlugin:
    """Lightweight plugin that emits stable structured output."""

    id: str
    kind: str
    version: str = "0.1.0"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        transcript = str(context.get("transcript") or "").strip()
        active_intents = [
            str(intent).strip().lower()
            for intent in (context.get("active_intents") or [])
            if str(intent).strip()
        ]
        token_count = len(transcript.split()) if transcript else 0
        confidence_hint = min(1.0, 0.35 + (0.1 * len(active_intents)))
        return {
            "plugin_id": self.id,
            "kind": self.kind,
            "summary": _snippet(transcript) or f"{self.id} processed preview context.",
            "token_count": token_count,
            "active_intents": active_intents,
            "confidence_hint": round(confidence_hint, 3),
        }


_BUILTIN_PLUGIN_DEFS: tuple[tuple[str, str], ...] = (
    ("requirements_extractor", "synthesizer"),
    ("action_owner_enforcer", "validator"),
    ("mermaid_architecture", "artifact_generator"),
    ("adr_drafter", "artifact_generator"),
    ("milestone_planner", "synthesizer"),
    ("dependency_mapper", "synthesizer"),
    ("scope_guard", "validator"),
    ("customer_signal_extractor", "signals"),
    ("incident_timeline", "synthesizer"),
    ("risk_heatmap", "synthesizer"),
    ("stakeholder_update_drafter", "artifact_generator"),
    ("runbook_delta", "artifact_generator"),
    ("decision_announcement_drafter", "artifact_generator"),
)


def register_builtin_plugins(host: PluginHost) -> list[str]:
    """Register deterministic built-in plugins onto the provided host."""
    registered: list[str] = []
    for plugin_id, kind in _BUILTIN_PLUGIN_DEFS:
        host.register(DeterministicPlugin(id=plugin_id, kind=kind))
        registered.append(plugin_id)
    return registered

