"""Typed plugin-chain dispatch for MIR routing (HS-2-04 / spec §9.4).

Bridges `IntentScore` + `IntentWindow` into `PluginRun` contract records by
running the route-derived chain through the existing `PluginHost`. The host
already owns idempotency, timeouts, capability gating, deferred queueing,
and per-plugin failure isolation — this module wraps each invocation with
real wall-clock boundaries so the typed `PluginRun` records carry honest
`started_at` / `finished_at` values that the existing
`PluginRunResult.duration_ms` alone can't supply.
"""

from __future__ import annotations

import hashlib
import time
from typing import Iterable

from .contracts import IntentScore, IntentWindow, PluginRun
from .host import PluginHost, PluginRunResult, build_idempotency_key
from .router import preview_route


def _transcript_hash(transcript: str) -> str:
    return hashlib.sha256(transcript.encode("utf-8")).hexdigest()


def _to_plugin_run(
    result: PluginRunResult,
    *,
    window: IntentWindow,
    profile: str,
    started_at: float,
    finished_at: float,
) -> PluginRun:
    return PluginRun(
        plugin_id=result.plugin_id,
        plugin_version=result.plugin_version,
        window_id=window.window_id,
        meeting_id=window.meeting_id,
        profile=profile,
        status=result.status,
        idempotency_key=result.idempotency_key,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=result.duration_ms,
        error=result.error,
        output=dict(result.output) if isinstance(result.output, dict) else None,
    )


def dispatch_window(
    host: PluginHost,
    score: IntentScore,
    *,
    window: IntentWindow,
    profile: str,
    transcript_hash: str | None = None,
    override_intents: list[str] | None = None,
    timeout_seconds: float | None = None,
    defer_heavy: bool = True,
) -> list[PluginRun]:
    """Dispatch the route-derived plugin chain for one scored window.

    Returns one `PluginRun` per plugin in the chain. Per-plugin failures are
    surfaced as `status="error"` records; they do not abort sibling plugins
    (MIR-R-004). `host.execute` already prevents duplicate work via its
    idempotency cache (MIR-F-008).
    """
    decision = preview_route(
        profile=profile,
        intent_scores=score.scores,
        threshold=score.threshold,
        override_intents=override_intents,
    )
    th = transcript_hash if transcript_hash is not None else _transcript_hash(window.transcript)

    base_context: dict[str, object] = {
        "active_intents": list(decision.active_intents),
        "profile": decision.profile,
        "window_id": window.window_id,
        "meeting_id": window.meeting_id,
        "transcript": window.transcript,
    }

    runs: list[PluginRun] = []
    for plugin_id in decision.plugin_chain:
        started_at = time.time()
        try:
            result = host.execute(
                plugin_id,
                context=dict(base_context),
                meeting_id=window.meeting_id,
                window_id=window.window_id,
                transcript_hash=th,
                timeout_seconds=timeout_seconds,
                defer_heavy=defer_heavy,
            )
            finished_at = time.time()
            runs.append(
                _to_plugin_run(
                    result,
                    window=window,
                    profile=decision.profile,
                    started_at=started_at,
                    finished_at=finished_at,
                )
            )
        except Exception as exc:
            finished_at = time.time()
            runs.append(
                PluginRun(
                    plugin_id=plugin_id,
                    plugin_version="unknown",
                    window_id=window.window_id,
                    meeting_id=window.meeting_id,
                    profile=decision.profile,
                    status="error",
                    idempotency_key=build_idempotency_key(
                        meeting_id=window.meeting_id,
                        window_id=window.window_id,
                        plugin_id=plugin_id,
                        transcript_hash=th,
                    ),
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=(finished_at - started_at) * 1000.0,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
    return runs


def dispatch_windows(
    host: PluginHost,
    pairs: Iterable[tuple[IntentWindow, IntentScore]],
    *,
    profile: str,
    timeout_seconds: float | None = None,
    defer_heavy: bool = True,
) -> list[PluginRun]:
    """Dispatch chains for a sequence of scored windows in document order.

    Overlapping windows producing the same `(meeting_id, window_id, plugin_id,
    transcript_hash)` are de-duplicated by the host's idempotency cache
    (MIR-F-009 — overlapping windows do not produce duplicate artifact runs).
    """
    out: list[PluginRun] = []
    for window, score in pairs:
        out.extend(
            dispatch_window(
                host,
                score,
                window=window,
                profile=profile,
                timeout_seconds=timeout_seconds,
                defer_heavy=defer_heavy,
            )
        )
    return out
