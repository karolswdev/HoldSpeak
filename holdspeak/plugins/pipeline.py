"""End-to-end MIR routing pipeline (HS-2-06 / spec §9.6).

Wires HS-2-03 (windowing/scoring), HS-2-04 (dispatch), and HS-2-05
(typed persistence) into one callable that processes a finalized
meeting state. Per-stage failures degrade gracefully (MIR-F-012):
exceptions are caught and surfaced in `MIRPipelineResult.errors`
without aborting downstream stages or raising into the caller's
control flow.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from ..artifacts import ArtifactDraft
from .contracts import ArtifactLineage, IntentScore, IntentTransition, IntentWindow, PluginRun
from .dispatch import dispatch_window
from .host import PluginHost
from .persistence import record_intent_window, record_plugin_run
from .scoring import iter_intent_transitions, score_window
from .synthesis import synthesize_and_persist

# Note: `build_intent_windows` is imported lazily inside `process_meeting_state`
# to avoid a circular import. `holdspeak/intent_timeline.py` imports
# `IntentWindow` from `.plugins.contracts`, which loads `holdspeak.plugins`
# which loads this module — pulling `build_intent_windows` here at module
# scope would land us mid-init of `intent_timeline`.


class _MeetingDatabaseLike(Protocol):
    """Subset of `MeetingDatabase` used by `MIRPipeline`."""

    def record_intent_window(self, **kwargs: Any) -> None: ...
    def record_plugin_run(self, **kwargs: Any) -> None: ...


@dataclass(frozen=True)
class MIRPipelineResult:
    """Outcome of one pipeline pass over a meeting."""

    windows: list[IntentWindow] = field(default_factory=list)
    scores: list[IntentScore] = field(default_factory=list)
    transitions: list[IntentTransition] = field(default_factory=list)
    runs: list[PluginRun] = field(default_factory=list)
    artifacts: list[ArtifactDraft] = field(default_factory=list)
    artifact_lineages: list[ArtifactLineage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _state_segments(state: Any) -> list[Mapping[str, Any]]:
    """Project `MeetingState.segments` into the dict shape `build_intent_windows` expects."""
    raw = getattr(state, "segments", None) or []
    out: list[Mapping[str, Any]] = []
    for seg in raw:
        out.append(
            {
                "start_time": float(getattr(seg, "start_time", 0.0)),
                "end_time": float(getattr(seg, "end_time", 0.0)),
                "speaker": str(getattr(seg, "speaker", "") or ""),
                "text": str(getattr(seg, "text", "") or ""),
            }
        )
    return out


def process_meeting_state(
    state: Any,
    host: PluginHost,
    *,
    profile: str = "balanced",
    threshold: float = 0.6,
    hysteresis: float = 0.05,
    window_seconds: float = 90.0,
    step_seconds: float = 30.0,
    db: Optional[_MeetingDatabaseLike] = None,
    timeout_seconds: Optional[float] = None,
    defer_heavy: bool = True,
    synthesize: bool = False,
    max_artifacts: int = 200,
) -> MIRPipelineResult:
    """Run the MIR pipeline over a meeting state, in process, returning typed results.

    Stages:
      1. windowing — rolling windows from `state.segments`.
      2. scoring — typed `IntentScore` per window.
      3. transitions — typed `IntentTransition` events with hysteresis.
      4. dispatch — plugin chain per window via `host`.
      5. persistence — typed writes via `db` (skipped when `db is None`).

    Each stage is wrapped in `try/except`; failures are recorded as
    error strings on the returned result and downstream stages still
    receive whatever the upstream successfully produced. Nothing in
    here raises into the caller — the meeting-session stop path can
    invoke this without polluting its own error handling.
    """
    meeting_id = str(getattr(state, "id", "") or "").strip()
    if not meeting_id:
        return MIRPipelineResult(errors=["state.id missing or empty"])

    errors: list[str] = []

    # 1. Windowing — lazy import to avoid the
    # plugins.__init__ ↔ intent_timeline circular load described above.
    from ..intent_timeline import build_intent_windows

    try:
        windows = build_intent_windows(
            _state_segments(state),
            meeting_id=meeting_id,
            window_seconds=window_seconds,
            step_seconds=step_seconds,
        )
    except Exception as exc:
        return MIRPipelineResult(errors=[f"windowing: {type(exc).__name__}: {exc}"])

    if not windows:
        return MIRPipelineResult()

    # 2. Scoring.
    scores: list[IntentScore] = []
    for window in windows:
        try:
            scores.append(score_window(window, threshold=threshold))
        except Exception as exc:
            errors.append(f"scoring[{window.window_id}]: {type(exc).__name__}: {exc}")

    # 3. Transitions (best-effort over whatever scored cleanly).
    try:
        transitions = iter_intent_transitions(scores, hysteresis=hysteresis)
    except Exception as exc:
        transitions = []
        errors.append(f"transitions: {type(exc).__name__}: {exc}")

    # 4. Dispatch — per window so one bad chain doesn't block siblings.
    runs: list[PluginRun] = []
    score_by_id = {s.window_id: s for s in scores}
    for window in windows:
        score = score_by_id.get(window.window_id)
        if score is None:
            continue
        try:
            runs.extend(
                dispatch_window(
                    host,
                    score,
                    window=window,
                    profile=profile,
                    timeout_seconds=timeout_seconds,
                    defer_heavy=defer_heavy,
                )
            )
        except Exception as exc:
            errors.append(f"dispatch[{window.window_id}]: {type(exc).__name__}: {exc}")

    # 5. Persistence — only if a db was supplied.
    if db is not None:
        for window in windows:
            score = score_by_id.get(window.window_id)
            if score is None:
                continue
            try:
                record_intent_window(db, window, score, profile=profile)
            except Exception as exc:
                errors.append(
                    f"persist_window[{window.window_id}]: {type(exc).__name__}: {exc}"
                )
        for run in runs:
            try:
                record_plugin_run(db, run)
            except Exception as exc:
                errors.append(
                    f"persist_run[{run.window_id}/{run.plugin_id}]: {type(exc).__name__}: {exc}"
                )

    # 6. Synthesis — only if requested AND a db was supplied (synthesis reads
    #    from db.list_plugin_runs to get persisted output payloads, then
    #    persists each artifact via db.record_artifact).
    artifacts: list[ArtifactDraft] = []
    artifact_lineages: list[ArtifactLineage] = []
    if synthesize and db is not None:
        try:
            artifacts, artifact_lineages = synthesize_and_persist(
                db,
                meeting_id,
                max_artifacts=max_artifacts,
            )
        except Exception as exc:
            errors.append(f"synthesis: {type(exc).__name__}: {exc}")

    return MIRPipelineResult(
        windows=list(windows),
        scores=list(scores),
        transitions=list(transitions),
        runs=list(runs),
        artifacts=list(artifacts),
        artifact_lineages=list(artifact_lineages),
        errors=list(errors),
    )
