"""Typed persistence adapters for MIR contracts (HS-2-05 / spec §9.5).

The underlying `MeetingDatabase` already implements the full MIR-D-001..D-006
surface (intent_windows + intent_window_scores tables, plugin_runs table,
artifacts + artifact_sources tables, schema versioning, idempotent
`CREATE TABLE IF NOT EXISTS` migrations). This module wraps each writer with
a typed-contract front-door so callers don't have to hand-shuffle field
positions or remember the mapping from `ArtifactLineage` to the
`source_type`/`source_ref` source-tuple shape `record_artifact`
expects.

Known semantic gap: `record_plugin_run` does not persist
`PluginRun.started_at` / `PluginRun.finished_at` — only `duration_ms` and
the row's `created_at` (now). HS-2-10 (observability hardening) is the
right place to either add columns or carry the timestamps in the row's
`metadata_json` if the read path ends up needing them.
"""

from __future__ import annotations

from typing import Any, Optional

from ..db import MeetingDatabase
from .contracts import ArtifactLineage, IntentScore, IntentWindow, PluginRun


def record_intent_window(
    db: MeetingDatabase,
    window: IntentWindow,
    score: IntentScore,
    *,
    profile: str = "balanced",
    active_intents: Optional[list[str]] = None,
    override_intents: Optional[list[str]] = None,
    transcript_hash: str = "",
    transcript_excerpt: str = "",
) -> None:
    """Persist a typed `IntentWindow` + its `IntentScore` in one call (MIR-D-001, MIR-D-002)."""
    if window.window_id != score.window_id:
        raise ValueError(
            f"IntentScore.window_id={score.window_id!r} does not match "
            f"IntentWindow.window_id={window.window_id!r}"
        )
    db.record_intent_window(
        meeting_id=window.meeting_id,
        window_id=window.window_id,
        start_seconds=window.start_seconds,
        end_seconds=window.end_seconds,
        transcript_hash=transcript_hash,
        transcript_excerpt=transcript_excerpt or window.transcript[:512],
        profile=profile,
        threshold=score.threshold,
        active_intents=list(active_intents or score.labels_above_threshold()),
        intent_scores=dict(score.scores),
        override_intents=list(override_intents or []),
        tags=list(window.tags),
        metadata=dict(window.metadata),
    )


def record_plugin_run(
    db: MeetingDatabase,
    run: PluginRun,
    *,
    output: Optional[dict[str, Any]] = None,
) -> None:
    """Persist a typed `PluginRun` (MIR-D-003).

    `run.started_at` / `run.finished_at` are not persisted — see module
    docstring for the documented gap. `run.duration_ms` is preserved.
    """
    db.record_plugin_run(
        meeting_id=run.meeting_id,
        window_id=run.window_id,
        plugin_id=run.plugin_id,
        plugin_version=run.plugin_version,
        status=run.status,
        idempotency_key=run.idempotency_key,
        duration_ms=run.duration_ms,
        output=output,
        error=run.error,
        deduped=(run.status == "deduped"),
    )


def record_plugin_runs(db: MeetingDatabase, runs: list[PluginRun]) -> None:
    """Convenience: persist a batch of `PluginRun` records in order."""
    for run in runs:
        record_plugin_run(db, run)


def record_artifact_with_lineage(
    db: MeetingDatabase,
    *,
    artifact_id: str,
    meeting_id: str,
    artifact_type: str,
    title: str,
    body_markdown: str,
    plugin_id: str,
    plugin_version: str,
    lineage: ArtifactLineage,
    structured_json: Optional[dict[str, Any]] = None,
    confidence: float = 1.0,
    status: str = "draft",
) -> None:
    """Persist a synthesized artifact + its `ArtifactLineage` (MIR-D-004, MIR-F-011)."""
    if lineage.artifact_id != artifact_id:
        raise ValueError(
            f"ArtifactLineage.artifact_id={lineage.artifact_id!r} does not match "
            f"artifact_id={artifact_id!r}"
        )
    if lineage.meeting_id != meeting_id:
        raise ValueError(
            f"ArtifactLineage.meeting_id={lineage.meeting_id!r} does not match "
            f"meeting_id={meeting_id!r}"
        )
    sources: list[tuple[str, str]] = []
    for window_id in lineage.window_ids:
        sources.append(("window", window_id))
    for plugin_run_key in lineage.plugin_run_keys:
        sources.append(("plugin_run", plugin_run_key))

    db.record_artifact(
        artifact_id=artifact_id,
        meeting_id=meeting_id,
        artifact_type=artifact_type,
        title=title,
        body_markdown=body_markdown,
        structured_json=structured_json or {},
        confidence=confidence,
        status=status,
        plugin_id=plugin_id,
        plugin_version=plugin_version,
        sources=sources,
    )
