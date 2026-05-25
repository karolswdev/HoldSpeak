"""Normalized telemetry summaries for dictation readiness and dry-run output."""

from __future__ import annotations

from typing import Any, Mapping

_FALLBACK_REASON_CATEGORIES = {
    "no_hs_context": "no_context",
    "unsupported_runtime": "runtime_unavailable",
    "rewrite_failed": "runtime_unavailable",
    "empty_rewrite": "malformed_output",
    "rewrite_too_long": "malformed_output",
    "empty_blockset": "no_context",
    "no_match": "no_match",
    "below_threshold": "no_match",
    "unknown_block": "no_context",
    "unresolved_placeholder": "malformed_output",
    "classify_failed": "malformed_output",
}


def summarize_stage(stage: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact, UI-safe summary for one serialized stage result."""

    metadata = stage.get("metadata") if isinstance(stage.get("metadata"), Mapping) else {}
    warnings = stage.get("warnings") if isinstance(stage.get("warnings"), list) else []
    reason = _stage_reason(stage, metadata, warnings)
    changed = bool(metadata.get("changed")) if "changed" in metadata else None
    failed = bool(metadata.get("failed"))
    fallback_category = _fallback_category(reason, warnings, failed)
    status = "error" if failed else "fallback" if fallback_category else "ok"
    return {
        "stage_id": str(stage.get("stage_id") or ""),
        "status": status,
        "reason": reason,
        "fallback": fallback_category is not None,
        "fallback_category": fallback_category,
        "elapsed_ms": float(stage.get("elapsed_ms") or 0.0),
        "changed": changed,
        "warning_count": len(warnings),
    }


def summarize_dry_run(
    *,
    runtime_status: str,
    runtime_detail: str,
    stages: list[dict[str, Any]],
    warnings: list[str],
    total_elapsed_ms: float,
    max_total_latency_ms: int | float | None,
) -> dict[str, Any]:
    """Return a dry-run telemetry envelope for API and web rendering."""

    stage_summaries = [summarize_stage(stage) for stage in stages]
    fallbacks = [
        {
            "stage_id": item["stage_id"],
            "category": item["fallback_category"],
            "reason": item["reason"],
        }
        for item in stage_summaries
        if item["fallback"]
    ]
    if runtime_status in {"disabled", "unavailable", "missing_model"}:
        fallbacks.insert(
            0,
            {
                "stage_id": "runtime",
                "category": "runtime_unavailable" if runtime_status != "disabled" else "runtime_disabled",
                "reason": runtime_detail or runtime_status,
            },
        )

    budget = float(max_total_latency_ms or 0.0)
    over_budget = budget > 0 and total_elapsed_ms > budget
    status = "ok"
    if runtime_status in {"disabled", "unavailable", "missing_model"} or fallbacks:
        status = "fallback"
    if over_budget:
        status = "slow"
    return {
        "status": status,
        "summary": _dry_run_summary(status, fallbacks, over_budget),
        "latency": {
            "total_elapsed_ms": float(total_elapsed_ms),
            "max_total_latency_ms": budget or None,
            "over_budget": over_budget,
        },
        "stages": stage_summaries,
        "fallbacks": fallbacks,
        "warning_count": len(warnings),
    }


def summarize_readiness_telemetry(
    *,
    runtime_payload: Mapping[str, Any],
    max_total_latency_ms: int | float | None,
) -> dict[str, Any]:
    """Return session-scoped readiness telemetry from runtime counters."""

    counters = runtime_payload.get("counters") if isinstance(runtime_payload.get("counters"), Mapping) else {}
    session = runtime_payload.get("session") if isinstance(runtime_payload.get("session"), Mapping) else {}
    fallback_flags: list[dict[str, str]] = []
    runtime_status = str(runtime_payload.get("status") or "unknown")
    if runtime_status in {"disabled", "unavailable", "missing_model"}:
        fallback_flags.append(
            {
                "category": "runtime_unavailable" if runtime_status != "disabled" else "runtime_disabled",
                "reason": str(runtime_payload.get("detail") or runtime_status),
            }
        )
    if session.get("llm_disabled_for_session"):
        fallback_flags.append(
            {
                "category": "timeout",
                "reason": str(session.get("disabled_reason") or "LLM disabled for this session"),
            }
        )
    classify_calls = int(counters.get("classify_calls") or 0)
    classify_failures = int(counters.get("classify_failures") or 0)
    status = "ok" if not fallback_flags else "fallback"
    return {
        "status": status,
        "summary": "fallback active" if fallback_flags else "session counters available",
        "latency": {
            "max_total_latency_ms": float(max_total_latency_ms or 0.0) or None,
            "cold_start_cap_ms": (float(max_total_latency_ms or 0.0) * 5.0) if max_total_latency_ms else None,
        },
        "counters": {
            "model_loads": int(counters.get("model_loads") or 0),
            "classify_calls": classify_calls,
            "classify_failures": classify_failures,
            "constrained_retries": int(counters.get("constrained_retries") or 0),
            "classify_successes": max(0, classify_calls - classify_failures),
        },
        "session": dict(session),
        "fallbacks": fallback_flags,
    }


def _stage_reason(
    stage: Mapping[str, Any],
    metadata: Mapping[str, Any],
    warnings: list[Any],
) -> str:
    reason = str(metadata.get("reason") or "").strip()
    if reason:
        return reason
    if metadata.get("failed"):
        return "failed"
    if _warnings_look_like_classify_failure(warnings):
        return "classify_failed"
    intent = stage.get("intent") if isinstance(stage.get("intent"), Mapping) else None
    if intent is not None:
        return "matched" if intent.get("matched") else "no_match"
    if metadata.get("applied_block"):
        return "applied"
    return "completed"


def _fallback_category(reason: str, warnings: list[Any], failed: bool) -> str | None:
    if failed:
        return "error"
    if _warnings_look_like_classify_failure(warnings):
        return "malformed_output"
    return _FALLBACK_REASON_CATEGORIES.get(reason)


def _warnings_look_like_classify_failure(warnings: list[Any]) -> bool:
    text = " ".join(str(item).lower() for item in warnings)
    return "classify" in text and ("failed" in text or "exhausted" in text)


def _dry_run_summary(status: str, fallbacks: list[dict[str, Any]], over_budget: bool) -> str:
    if over_budget:
        return "over latency budget"
    if fallbacks:
        first = fallbacks[0]
        return f"fallback: {first.get('category') or first.get('reason')}"
    return "all stages completed"
