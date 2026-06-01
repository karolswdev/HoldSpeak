"""Built-in MIR plugins shipped with the runtime host.

The package keeps the deterministic-stub `DeterministicPlugin` and the
generic `register_builtin_plugins` registrar that existed when this was
a single module, alongside real plugin implementations (one per
submodule). Phase 16 ships `mermaid_architecture` as the first real
LLM-backed synthesizer; the remaining plugin IDs continue to register
as `DeterministicPlugin` stubs until their own stories land.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..host import PluginHost
from .action_owner_enforcer import (
    ActionOwnerEnforcerPlugin,
    _extract_action_items,
)
from .adr_drafter import (
    AdrDrafterPlugin,
    _extract_adrs,
)
from .decision_capture import (
    DecisionCapturePlugin,
    _extract_decisions,
)
from .mermaid_architecture import (
    MermaidArchitecturePlugin,
    _extract_mermaid_block,
)
from .milestone_planner import (
    MilestonePlannerPlugin,
    _extract_milestones,
)
from .requirements_extractor import (
    RequirementsExtractorPlugin,
    _extract_requirements,
)
from .risk_heatmap import (
    RiskHeatmapPlugin,
    _extract_risks,
)

# Real plugin classes keyed by ID; every other ID falls back to the stub.
_REAL_PLUGINS = {
    "mermaid_architecture": MermaidArchitecturePlugin,
    "action_owner_enforcer": ActionOwnerEnforcerPlugin,
    "decision_capture": DecisionCapturePlugin,
    "requirements_extractor": RequirementsExtractorPlugin,
    "adr_drafter": AdrDrafterPlugin,
    "milestone_planner": MilestonePlannerPlugin,
    "risk_heatmap": RiskHeatmapPlugin,
}


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
    ("decision_capture", "synthesizer"),  # HS-27-03: net-new, ubiquitous
)


def register_builtin_plugins(host: PluginHost) -> list[str]:
    """Register built-in plugins onto the provided host.

    Plugin IDs in `_REAL_PLUGINS` register as their real class; every other
    entry registers as a `DeterministicPlugin` stub until its dedicated phase
    ships.
    """
    registered: list[str] = []
    for plugin_id, kind in _BUILTIN_PLUGIN_DEFS:
        real_cls = _REAL_PLUGINS.get(plugin_id)
        if real_cls is not None:
            host.register(real_cls())
        else:
            host.register(DeterministicPlugin(id=plugin_id, kind=kind))
        registered.append(plugin_id)
    return registered


__all__ = [
    "ActionOwnerEnforcerPlugin",
    "AdrDrafterPlugin",
    "DecisionCapturePlugin",
    "DeterministicPlugin",
    "MermaidArchitecturePlugin",
    "MilestonePlannerPlugin",
    "RequirementsExtractorPlugin",
    "RiskHeatmapPlugin",
    "_BUILTIN_PLUGIN_DEFS",
    "_extract_action_items",
    "_extract_adrs",
    "_extract_decisions",
    "_extract_mermaid_block",
    "_extract_milestones",
    "_extract_requirements",
    "_extract_risks",
    "register_builtin_plugins",
]
