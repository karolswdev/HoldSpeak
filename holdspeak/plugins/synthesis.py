"""Meeting artifact synthesis from MIR plugin runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from ..artifacts import ArtifactDraft, ArtifactSourceRef, artifact_status_from_confidence
from .contracts import ArtifactLineage

_ARTIFACT_TYPE_BY_PLUGIN: dict[str, str] = {
    "requirements_extractor": "requirements",
    "action_owner_enforcer": "action_items",
    "mermaid_architecture": "diagram",
    "decision_capture": "decisions",
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


def _action_item_line(item: dict[str, Any]) -> str:
    """Render one action item as a markdown checklist line (HS-27-01)."""
    task = _clean_text(item.get("task")) or "(unspecified task)"
    owner = _clean_text(item.get("owner")) or "—"
    due = _clean_text(item.get("due")) or "—"
    gap = item.get("gap")
    flag = f"  ⚠️ {gap.replace('_', ' ')}" if isinstance(gap, str) and gap else ""
    return f"- [ ] {task} — owner: {owner} · due: {due}{flag}"


def _decision_body(
    decisions: list[dict[str, Any]] | None, open_questions: list[str] | None
) -> str:
    """Render decisions + open questions as markdown sections (HS-27-03)."""
    parts: list[str] = []
    if decisions:
        lines = ["**Decisions**"]
        for item in decisions:
            decision = _clean_text(item.get("decision")) or "(unspecified)"
            rationale = _clean_text(item.get("rationale"))
            lines.append(f"- {decision}" + (f" — {rationale}" if rationale else ""))
        parts.append("\n".join(lines))
    if open_questions:
        lines = ["**Open questions**"]
        lines.extend(f"- {_clean_text(q)}" for q in open_questions if _clean_text(q))
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


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
        source_lines = (
            f"- Source windows: {', '.join(unique_window_ids) if unique_window_ids else 'none'}\n"
            f"- Source plugin runs: {', '.join(unique_run_ids) if unique_run_ids else 'none'}"
        )

        # Custom artifact bodies per type, so the web layer has something
        # rendering-ready. Both are strict branches; the default body is
        # byte-for-byte unchanged. TODO: once a third custom body lands, extract
        # a per-artifact-type renderer registry instead of branching here.
        #  - HS-16-03: "diagram" embeds the plugin's Mermaid block (verbatim;
        #    the plugin validates syntax, synthesis does not).
        #  - HS-27-01: "action_items" embeds an ownership-gap checklist.
        #  - HS-27-03: "decisions" embeds decisions + open questions.
        mermaid_value = ""
        if artifact_type == "diagram":
            raw_mermaid = canonical.output.get("mermaid")
            if isinstance(raw_mermaid, str) and raw_mermaid.strip():
                mermaid_value = raw_mermaid.strip()

        action_items: list[dict[str, Any]] | None = None
        if artifact_type == "action_items":
            raw_items = canonical.output.get("action_items")
            if isinstance(raw_items, list) and raw_items:
                action_items = [item for item in raw_items if isinstance(item, dict)] or None

        decisions: list[dict[str, Any]] | None = None
        open_questions: list[str] | None = None
        if artifact_type == "decisions":
            raw_decisions = canonical.output.get("decisions")
            if isinstance(raw_decisions, list) and raw_decisions:
                decisions = [item for item in raw_decisions if isinstance(item, dict)] or None
            raw_questions = canonical.output.get("open_questions")
            if isinstance(raw_questions, list) and raw_questions:
                open_questions = [str(q).strip() for q in raw_questions if str(q).strip()] or None

        if mermaid_value:
            body_markdown = (
                f"### {title}\n\n"
                f"{summary}\n\n"
                f"```mermaid\n{mermaid_value}\n```\n\n"
                f"{source_lines}"
            )
        elif action_items:
            checklist = "\n".join(_action_item_line(item) for item in action_items)
            body_markdown = (
                f"### {title}\n\n"
                f"{summary}\n\n"
                f"{checklist}\n\n"
                f"{source_lines}"
            )
        elif decisions or open_questions:
            body_markdown = (
                f"### {title}\n\n"
                f"{summary}\n\n"
                f"{_decision_body(decisions, open_questions)}\n\n"
                f"{source_lines}"
            )
        else:
            body_markdown = (
                f"### {title}\n\n"
                f"{summary}\n\n"
                f"{source_lines}"
            )

        structured_json: dict[str, Any] = {
            "summary": summary,
            "plugin_id": plugin_id,
            "plugin_run_ids": unique_run_ids,
            "window_ids": unique_window_ids,
            "active_intents": merged_intents,
            "run_count": len(runs),
            "dedupe_hash": payload_hash,
        }
        if mermaid_value:
            structured_json["mermaid"] = mermaid_value
        if action_items:
            structured_json["action_items"] = action_items
        if decisions:
            structured_json["decisions"] = decisions
        if open_questions:
            structured_json["open_questions"] = open_questions

        artifacts.append(
            ArtifactDraft(
                artifact_id=artifact_id,
                meeting_id=clean_meeting_id,
                artifact_type=artifact_type,
                title=title,
                body_markdown=body_markdown,
                structured_json=structured_json,
                confidence=round(confidence, 4),
                status=status,
                plugin_id=plugin_id,
                plugin_version=canonical.plugin_version,
                sources=sources,
            )
        )

    artifacts.sort(key=lambda artifact: (artifact.plugin_id, artifact.artifact_id))
    return artifacts[:max_artifacts]


def to_artifact_lineage(draft: ArtifactDraft) -> ArtifactLineage:
    """Project an `ArtifactDraft` into the typed `ArtifactLineage` contract (HS-2-07)."""
    window_ids = sorted(
        {src.source_ref for src in draft.sources if src.source_type == "intent_window"}
    )
    plugin_run_keys = sorted(
        {src.source_ref for src in draft.sources if src.source_type == "plugin_run"}
    )
    return ArtifactLineage(
        artifact_id=draft.artifact_id,
        meeting_id=draft.meeting_id,
        window_ids=window_ids,
        plugin_run_keys=plugin_run_keys,
    )


def synthesize_and_persist(
    db: Any,
    meeting_id: str,
    *,
    max_artifacts: int = 200,
    plugin_runs: Optional[Iterable[object]] = None,
) -> tuple[list[ArtifactDraft], list[ArtifactLineage]]:
    """Synthesize artifacts from a meeting's plugin runs and persist them (MIR-F-010, MIR-F-011).

    When `plugin_runs` is omitted, falls back to `db.list_plugin_runs(meeting_id)`
    so the caller doesn't have to re-marshal what's already on disk. Each
    drafted artifact is persisted via `db.record_artifact` with its
    `(source_type, source_ref)` lineage rows; the matching typed
    `ArtifactLineage` projections are returned alongside the drafts so the
    caller can hand them straight to a web API or CLI surface.
    """
    clean_meeting_id = _clean_text(meeting_id)
    if not clean_meeting_id:
        return ([], [])

    if plugin_runs is None:
        plugin_runs = db.list_plugin_runs(clean_meeting_id)

    drafts = synthesize_meeting_artifacts(
        meeting_id=clean_meeting_id,
        plugin_runs=plugin_runs,
        max_artifacts=max_artifacts,
    )

    lineages: list[ArtifactLineage] = []
    for draft in drafts:
        lineage = to_artifact_lineage(draft)
        lineages.append(lineage)
        sources = [(src.source_type, src.source_ref) for src in draft.sources]
        db.record_artifact(
            artifact_id=draft.artifact_id,
            meeting_id=draft.meeting_id,
            artifact_type=draft.artifact_type,
            title=draft.title,
            body_markdown=draft.body_markdown,
            structured_json=dict(draft.structured_json),
            confidence=draft.confidence,
            status=draft.status,
            plugin_id=draft.plugin_id,
            plugin_version=draft.plugin_version,
            sources=sources,
        )

    return (drafts, lineages)

