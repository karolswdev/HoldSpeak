"""Meeting artifact synthesis from MIR plugin runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from ..artifacts import ArtifactDraft, ArtifactSourceRef, artifact_status_from_confidence

_ARTIFACT_TYPE_BY_PLUGIN: dict[str, str] = {
    "requirements_extractor": "requirements",
    "action_owner_enforcer": "action_items",
    "mermaid_architecture": "diagram",
    "adr_drafter": "adr",
    "milestone_planner": "milestone_plan",
    "dependency_mapper": "dependency_map",
    "scope_guard": "scope_review",
    "customer_signal_extractor": "customer_signals",
    "incident_timeline": "incident_timeline",
    "risk_heatmap": "risk_register",
    "stakeholder_update_drafter": "stakeholder_update",
    "runbook_delta": "runbook_delta",
    "decision_announcement_drafter": "decision_announcement",
    "project_detector": "project_association",
}


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _coerce_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _stable_json_hash(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _RunView:
    run_id: str
    meeting_id: str
    window_id: str
    plugin_id: str
    plugin_version: str
    status: str
    output: dict[str, Any]
    created_at: str


def _as_run_view(item: object) -> _RunView | None:
    meeting_id = _clean_text(getattr(item, "meeting_id", None))
    if not meeting_id and isinstance(item, dict):
        meeting_id = _clean_text(item.get("meeting_id"))
    if not meeting_id:
        return None

    run_id_value = getattr(item, "id", None)
    if run_id_value is None and isinstance(item, dict):
        run_id_value = item.get("id")
    run_id = _clean_text(run_id_value)
    if not run_id:
        run_id = f"run:{meeting_id}:unknown"

    window_id = _clean_text(getattr(item, "window_id", None))
    if not window_id and isinstance(item, dict):
        window_id = _clean_text(item.get("window_id"))
    plugin_id = _clean_text(getattr(item, "plugin_id", None))
    if not plugin_id and isinstance(item, dict):
        plugin_id = _clean_text(item.get("plugin_id"))
    plugin_version = _clean_text(getattr(item, "plugin_version", None))
    if not plugin_version and isinstance(item, dict):
        plugin_version = _clean_text(item.get("plugin_version"))
    status = _clean_text(getattr(item, "status", None))
    if not status and isinstance(item, dict):
        status = _clean_text(item.get("status"))
    output_raw = getattr(item, "output", None)
    if output_raw is None and isinstance(item, dict):
        output_raw = item.get("output")
    output = dict(output_raw) if isinstance(output_raw, dict) else {}
    created_at = _clean_text(getattr(item, "created_at", ""))
    if not created_at and isinstance(item, dict):
        created_at = _clean_text(item.get("created_at"))

    if not window_id or not plugin_id:
        return None
    return _RunView(
        run_id=run_id,
        meeting_id=meeting_id,
        window_id=window_id,
        plugin_id=plugin_id,
        plugin_version=plugin_version or "unknown",
        status=status.lower() or "unknown",
        output=output,
        created_at=created_at,
    )


def synthesize_meeting_artifacts(
    *,
    meeting_id: str,
    plugin_runs: Iterable[object],
    max_artifacts: int = 200,
) -> list[ArtifactDraft]:
    """Merge plugin-run outputs into deduped meeting artifacts with lineage."""
    clean_meeting_id = _clean_text(meeting_id)
    if not clean_meeting_id:
        return []

    accepted: list[_RunView] = []
    for raw_run in plugin_runs:
        run = _as_run_view(raw_run)
        if run is None or run.meeting_id != clean_meeting_id:
            continue
        if run.status not in {"success", "deduped"}:
            continue
        accepted.append(run)

    if not accepted:
        return []

    accepted.sort(key=lambda run: (run.created_at, run.run_id))
    grouped: dict[tuple[str, str], list[_RunView]] = {}
    for run in accepted:
        dedupe_hash = _stable_json_hash(run.output)
        grouped.setdefault((run.plugin_id, dedupe_hash), []).append(run)

    artifacts: list[ArtifactDraft] = []
    for (plugin_id, payload_hash), runs in grouped.items():
        if len(artifacts) >= max_artifacts:
            break

        canonical = runs[-1]
        artifact_type = _ARTIFACT_TYPE_BY_PLUGIN.get(plugin_id, "plugin_output")
        title = plugin_id.replace("_", " ").title()
        summary = _clean_text(canonical.output.get("summary"))
        if not summary:
            summary = f"{title} output synthesized from {len(runs)} plugin run(s)."

        confidences = [
            max(0.0, min(1.0, _coerce_float(run.output.get("confidence_hint"), 0.55)))
            for run in runs
        ]
        confidence = sum(confidences) / max(1, len(confidences))
        status = artifact_status_from_confidence(confidence)

        unique_run_ids = sorted({run.run_id for run in runs})
        unique_window_ids = sorted({run.window_id for run in runs})
        merged_intents = sorted(
            {
                _clean_text(intent).lower()
                for run in runs
                for intent in (run.output.get("active_intents") or [])
                if _clean_text(intent)
            }
        )

        sources: list[ArtifactSourceRef] = []
        for window_id in unique_window_ids:
            sources.append(ArtifactSourceRef(source_type="intent_window", source_ref=window_id))
        for run_id in unique_run_ids:
            sources.append(ArtifactSourceRef(source_type="plugin_run", source_ref=run_id))

        artifact_key = f"{clean_meeting_id}|{plugin_id}|{payload_hash}"
        artifact_id = "art-" + hashlib.sha256(artifact_key.encode("utf-8")).hexdigest()[:20]
        body_markdown = (
            f"### {title}\n\n"
            f"{summary}\n\n"
            f"- Source windows: {', '.join(unique_window_ids) if unique_window_ids else 'none'}\n"
            f"- Source plugin runs: {', '.join(unique_run_ids) if unique_run_ids else 'none'}"
        )

        artifacts.append(
            ArtifactDraft(
                artifact_id=artifact_id,
                meeting_id=clean_meeting_id,
                artifact_type=artifact_type,
                title=title,
                body_markdown=body_markdown,
                structured_json={
                    "summary": summary,
                    "plugin_id": plugin_id,
                    "plugin_run_ids": unique_run_ids,
                    "window_ids": unique_window_ids,
                    "active_intents": merged_intents,
                    "run_count": len(runs),
                    "dedupe_hash": payload_hash,
                },
                confidence=round(confidence, 4),
                status=status,
                plugin_id=plugin_id,
                plugin_version=canonical.plugin_version,
                sources=sources,
            )
        )

    artifacts.sort(key=lambda artifact: (artifact.plugin_id, artifact.artifact_id))
    return artifacts[:max_artifacts]

