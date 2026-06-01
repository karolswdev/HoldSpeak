"""Meeting artifact synthesis from MIR plugin runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional

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


_REQUIREMENT_TYPE_LABELS: dict[str, str] = {
    "functional": "Functional",
    "non_functional": "Non-functional",
    "constraint": "Constraints",
    "acceptance": "Acceptance criteria",
}


def _requirements_body(requirements: list[dict[str, Any]] | None) -> str:
    """Render requirements grouped by type as markdown sections (HS-27-04)."""
    if not requirements:
        return ""
    grouped: dict[str, list[str]] = {}
    for item in requirements:
        text = _clean_text(item.get("text"))
        if not text:
            continue
        req_type = str(item.get("type") or "functional").strip().lower() or "functional"
        grouped.setdefault(req_type, []).append(text)
    parts: list[str] = []
    # Stable order: known types first (in label order), then any stragglers.
    ordered = list(_REQUIREMENT_TYPE_LABELS) + [t for t in grouped if t not in _REQUIREMENT_TYPE_LABELS]
    for req_type in ordered:
        texts = grouped.get(req_type)
        if not texts:
            continue
        label = _REQUIREMENT_TYPE_LABELS.get(req_type, req_type.replace("_", " ").title())
        lines = [f"**{label}**"]
        lines.extend(f"- {text}" for text in texts)
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _risk_body(risks: list[dict[str, Any]] | None) -> str:
    """Render a risk register as a markdown table (HS-28-04)."""
    if not risks:
        return ""
    lines = ["| Risk | Impact | Likelihood | Mitigation | Owner |", "|---|---|---|---|---|"]
    for risk in risks:
        name = _clean_text(risk.get("risk")) or "(unspecified)"
        impact = _clean_text(risk.get("impact")) or "—"
        likelihood = _clean_text(risk.get("likelihood")) or "—"
        mitigation = _clean_text(risk.get("mitigation")) or "—"
        owner = _clean_text(risk.get("owner")) or "—"
        lines.append(f"| {name} | {impact} | {likelihood} | {mitigation} | {owner} |")
    return "\n".join(lines)


def _milestone_body(milestones: list[dict[str, Any]] | None) -> str:
    """Render a milestone plan as markdown sections (HS-28-03)."""
    if not milestones:
        return ""
    parts: list[str] = []
    for milestone in milestones:
        name = _clean_text(milestone.get("name")) or "(unnamed milestone)"
        target = _clean_text(milestone.get("target"))
        lines = [f"**{name}**" + (f" — {target}" if target else "")]
        deliverables = milestone.get("deliverables")
        if isinstance(deliverables, list) and deliverables:
            lines.append("- Deliverables: " + ", ".join(_clean_text(d) for d in deliverables if _clean_text(d)))
        dependencies = milestone.get("dependencies")
        if isinstance(dependencies, list) and dependencies:
            lines.append("- Dependencies: " + ", ".join(_clean_text(d) for d in dependencies if _clean_text(d)))
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _adr_body(adrs: list[dict[str, Any]] | None) -> str:
    """Render Architecture Decision Records as markdown sections (HS-28-02)."""
    if not adrs:
        return ""
    parts: list[str] = []
    for adr in adrs:
        title = _clean_text(adr.get("title")) or "(untitled decision)"
        status = _clean_text(adr.get("status")) or "proposed"
        lines = [f"**{title}** — _{status}_"]
        for label, key in (("Context", "context"), ("Decision", "decision"), ("Consequences", "consequences")):
            value = _clean_text(adr.get(key))
            if value:
                lines.append(f"- {label}: {value}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _dependency_body(deps: list[dict[str, Any]] | None) -> str:
    """Render dependency edges as a markdown list (HS-29-01)."""
    if not deps:
        return ""
    lines: list[str] = []
    for dep in deps:
        src = _clean_text(dep.get("from")) or "(?)"
        dst = _clean_text(dep.get("to")) or "(?)"
        note = _clean_text(dep.get("note"))
        lines.append(f"- {src} → {dst}" + (f" — {note}" if note else ""))
    return "\n".join(lines)


_SCOPE_VERDICT_LABELS = {
    "in_scope": "In scope",
    "out_of_scope": "Out of scope",
    "scope_creep": "Scope creep",
}


def _scope_body(findings: list[dict[str, Any]] | None) -> str:
    """Render scope findings grouped by verdict (HS-29-01)."""
    if not findings:
        return ""
    grouped: dict[str, list[str]] = {}
    for finding in findings:
        item = _clean_text(finding.get("item"))
        if not item:
            continue
        verdict = str(finding.get("verdict") or "in_scope").strip().lower() or "in_scope"
        rationale = _clean_text(finding.get("rationale"))
        grouped.setdefault(verdict, []).append(item + (f" — {rationale}" if rationale else ""))
    parts: list[str] = []
    ordered = list(_SCOPE_VERDICT_LABELS) + [v for v in grouped if v not in _SCOPE_VERDICT_LABELS]
    for verdict in ordered:
        items = grouped.get(verdict)
        if not items:
            continue
        label = _SCOPE_VERDICT_LABELS.get(verdict, verdict.replace("_", " ").title())
        lines = [f"**{label}**"]
        lines.extend(f"- {item}" for item in items)
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _customer_signal_body(signals: list[dict[str, Any]] | None) -> str:
    """Render customer signals as a markdown list (HS-29-01)."""
    if not signals:
        return ""
    lines: list[str] = []
    for sig in signals:
        text = _clean_text(sig.get("signal"))
        if not text:
            continue
        sig_type = _clean_text(sig.get("type")).replace("_", " ") or "signal"
        quote = _clean_text(sig.get("quote"))
        lines.append(f"- _{sig_type}_: {text}" + (f' — "{quote}"' if quote else ""))
    return "\n".join(lines)


# --- Per-artifact-type body renderers (HS-28-01) ---------------------------
#
# Each renderer takes the canonical plugin output and returns either
# `(inner_block, extra_structured_json_keys)` for a custom artifact body, or
# `None` to fall back to the default body (and add no extra structured keys).
# `_compose_body` wraps the inner block in the shared `### title / summary /
# block / source` template so every body — custom or default — is identical to
# the pre-registry hand-branched output (byte-for-byte; see
# `test_artifact_synthesis_diagram.py`). To add a new artifact body, write a
# renderer and register it in `_ARTIFACT_RENDERERS` — no dispatch edits.


@dataclass(frozen=True)
class _RenderContext:
    output: dict[str, Any]


_Rendered = Optional[tuple[str, dict[str, Any]]]


def _compose_body(*, title: str, summary: str, source_lines: str, block: Optional[str]) -> str:
    if block:
        return f"### {title}\n\n{summary}\n\n{block}\n\n{source_lines}"
    return f"### {title}\n\n{summary}\n\n{source_lines}"


def _render_diagram(ctx: _RenderContext) -> _Rendered:
    # HS-16-03: embed the plugin's Mermaid block verbatim (the plugin validates
    # syntax; synthesis does not).
    raw = ctx.output.get("mermaid")
    if not (isinstance(raw, str) and raw.strip()):
        return None
    mermaid = raw.strip()
    return f"```mermaid\n{mermaid}\n```", {"mermaid": mermaid}


def _render_action_items(ctx: _RenderContext) -> _Rendered:
    # HS-27-01: an ownership-gap checklist.
    raw_items = ctx.output.get("action_items")
    if not (isinstance(raw_items, list) and raw_items):
        return None
    items = [item for item in raw_items if isinstance(item, dict)]
    if not items:
        return None
    block = "\n".join(_action_item_line(item) for item in items)
    return block, {"action_items": items}


def _render_decisions(ctx: _RenderContext) -> _Rendered:
    # HS-27-03: decisions + open questions.
    raw_decisions = ctx.output.get("decisions")
    decisions: list[dict[str, Any]] | None = None
    if isinstance(raw_decisions, list) and raw_decisions:
        decisions = [item for item in raw_decisions if isinstance(item, dict)] or None
    raw_questions = ctx.output.get("open_questions")
    open_questions: list[str] | None = None
    if isinstance(raw_questions, list) and raw_questions:
        open_questions = [str(q).strip() for q in raw_questions if str(q).strip()] or None
    if not (decisions or open_questions):
        return None
    extra: dict[str, Any] = {}
    if decisions:
        extra["decisions"] = decisions
    if open_questions:
        extra["open_questions"] = open_questions
    return _decision_body(decisions, open_questions), extra


def _render_requirements(ctx: _RenderContext) -> _Rendered:
    # HS-27-04: requirements grouped by type.
    raw_reqs = ctx.output.get("requirements")
    if not (isinstance(raw_reqs, list) and raw_reqs):
        return None
    requirements = [item for item in raw_reqs if isinstance(item, dict)]
    if not requirements:
        return None
    return _requirements_body(requirements), {"requirements": requirements}


def _render_adrs(ctx: _RenderContext) -> _Rendered:
    # HS-28-02: Architecture Decision Records.
    raw_adrs = ctx.output.get("adrs")
    if not (isinstance(raw_adrs, list) and raw_adrs):
        return None
    adrs = [item for item in raw_adrs if isinstance(item, dict)]
    if not adrs:
        return None
    return _adr_body(adrs), {"adrs": adrs}


def _render_milestones(ctx: _RenderContext) -> _Rendered:
    # HS-28-03: delivery milestone plan.
    raw_milestones = ctx.output.get("milestones")
    if not (isinstance(raw_milestones, list) and raw_milestones):
        return None
    milestones = [item for item in raw_milestones if isinstance(item, dict)]
    if not milestones:
        return None
    return _milestone_body(milestones), {"milestones": milestones}


def _render_risks(ctx: _RenderContext) -> _Rendered:
    # HS-28-04: risk register.
    raw_risks = ctx.output.get("risks")
    if not (isinstance(raw_risks, list) and raw_risks):
        return None
    risks = [item for item in raw_risks if isinstance(item, dict)]
    if not risks:
        return None
    return _risk_body(risks), {"risks": risks}


def _render_dependencies(ctx: _RenderContext) -> _Rendered:
    # HS-29-01: dependency map.
    raw = ctx.output.get("dependencies")
    if not (isinstance(raw, list) and raw):
        return None
    deps = [item for item in raw if isinstance(item, dict)]
    if not deps:
        return None
    return _dependency_body(deps), {"dependencies": deps}


def _render_scope(ctx: _RenderContext) -> _Rendered:
    # HS-29-01: scope review.
    raw = ctx.output.get("findings")
    if not (isinstance(raw, list) and raw):
        return None
    findings = [item for item in raw if isinstance(item, dict)]
    if not findings:
        return None
    return _scope_body(findings), {"findings": findings}


def _render_customer_signals(ctx: _RenderContext) -> _Rendered:
    # HS-29-01: customer signals.
    raw = ctx.output.get("signals")
    if not (isinstance(raw, list) and raw):
        return None
    signals = [item for item in raw if isinstance(item, dict)]
    if not signals:
        return None
    return _customer_signal_body(signals), {"signals": signals}


_ARTIFACT_RENDERERS: dict[str, Callable[[_RenderContext], _Rendered]] = {
    "diagram": _render_diagram,
    "action_items": _render_action_items,
    "decisions": _render_decisions,
    "requirements": _render_requirements,
    "adr": _render_adrs,
    "milestone_plan": _render_milestones,
    "risk_register": _render_risks,
    "dependency_map": _render_dependencies,
    "scope_review": _render_scope,
    "customer_signals": _render_customer_signals,
}


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

        # Per-artifact-type body via the renderer registry (HS-28-01). The
        # renderer returns a custom inner block + extra structured_json keys, or
        # None to fall back to the default body. The default body is byte-for-byte
        # the legacy template; see `_ARTIFACT_RENDERERS` / `_compose_body` above.
        renderer = _ARTIFACT_RENDERERS.get(artifact_type)
        rendered = renderer(_RenderContext(output=canonical.output)) if renderer else None
        block = rendered[0] if rendered is not None else None
        extra_structured = rendered[1] if rendered is not None else {}

        body_markdown = _compose_body(
            title=title, summary=summary, source_lines=source_lines, block=block
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
        structured_json.update(extra_structured)

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

