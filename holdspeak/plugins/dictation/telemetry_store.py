"""HS-39-05: session-scoped dictation pipeline telemetry.

The pipeline's own ring buffer (DIR-F-009) resets every `build_pipeline`, so it
never accumulates across utterances. This bounded, thread-safe store is fed via
the pipeline's `on_run` hook from the dry-run + live paths and survives across
runs within a session, so `/api/dictation/readiness` can report per-stage
latency quantiles + per-pass timings. In-memory only (no persistence).
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field

DEFAULT_CAP = 20


@dataclass(frozen=True)
class RunRecord:
    stage_ms: dict[str, float]
    total_ms: float
    rewrite_pass_ms: list[float] = field(default_factory=list)


def quantile(sorted_vals: list[float], q: float) -> float | None:
    """Linear-interpolated percentile over a pre-sorted list (None if empty)."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


class DictationTelemetryStore:
    """Bounded ring of recent pipeline runs' per-stage timings (one per session)."""

    def __init__(self, cap: int = DEFAULT_CAP) -> None:
        self._cap = max(1, int(cap))
        self._runs: deque[RunRecord] = deque(maxlen=self._cap)
        self._lock = threading.Lock()

    def record_run(self, run: object) -> None:
        """`on_run` hook — extract per-stage timings from a `PipelineRun`."""
        stage_ms: dict[str, float] = {}
        rewrite_pass_ms: list[float] = []
        for sr in getattr(run, "stage_results", []) or []:
            sid = str(getattr(sr, "stage_id", "") or "")
            if not sid:
                continue
            stage_ms[sid] = float(getattr(sr, "elapsed_ms", 0.0) or 0.0)
            meta = getattr(sr, "metadata", {}) or {}
            if sid == "project-rewriter" and meta.get("rewrite_pass_ms"):
                rewrite_pass_ms = [float(x) for x in meta["rewrite_pass_ms"]]
        record = RunRecord(
            stage_ms=stage_ms,
            total_ms=float(getattr(run, "total_elapsed_ms", 0.0) or 0.0),
            rewrite_pass_ms=rewrite_pass_ms,
        )
        with self._lock:
            self._runs.append(record)

    def _snapshot(self) -> list[RunRecord]:
        with self._lock:
            return list(self._runs)

    def run_count(self) -> int:
        return len(self._snapshot())

    def __len__(self) -> int:
        return self.run_count()

    def stage_quantiles(self) -> dict[str, dict[str, float | int | None]]:
        """Per-stage {p50, p95, count} over the recent runs (empty → {})."""
        by_stage: dict[str, list[float]] = {}
        for r in self._snapshot():
            for sid, ms in r.stage_ms.items():
                by_stage.setdefault(sid, []).append(ms)
        out: dict[str, dict[str, float | int | None]] = {}
        for sid, vals in by_stage.items():
            vals.sort()
            out[sid] = {
                "p50": _round(quantile(vals, 0.5)),
                "p95": _round(quantile(vals, 0.95)),
                "count": len(vals),
            }
        return out

    def latest_rewrite_pass_ms(self) -> list[float]:
        """The most recent run's per-pass rewrite timings (HS-39-01), or []."""
        for r in reversed(self._snapshot()):
            if r.rewrite_pass_ms:
                return list(r.rewrite_pass_ms)
        return []


def _round(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None
