"""Tests for normalized dictation telemetry summaries."""

from __future__ import annotations

from holdspeak.dictation_telemetry import (
    summarize_dry_run,
    summarize_readiness_telemetry,
    summarize_stage,
)


def test_summarize_stage_marks_context_fallback() -> None:
    summary = summarize_stage(
        {
            "stage_id": "project-rewriter",
            "elapsed_ms": 1.5,
            "warnings": [],
            "metadata": {"reason": "no_hs_context", "changed": False},
        }
    )

    assert summary["status"] == "fallback"
    assert summary["reason"] == "no_hs_context"
    assert summary["fallback_category"] == "no_context"


def test_summarize_stage_marks_classify_failure_as_malformed_output() -> None:
    summary = summarize_stage(
        {
            "stage_id": "intent-router",
            "elapsed_ms": 2.0,
            "warnings": ["classify retries exhausted; returning no-match"],
            "metadata": {"taxonomy_size": 2},
        }
    )

    assert summary["status"] == "fallback"
    assert summary["fallback_category"] == "malformed_output"
    assert summary["reason"] == "classify_failed"


def test_summarize_dry_run_includes_latency_budget_and_runtime_fallback() -> None:
    telemetry = summarize_dry_run(
        runtime_status="unavailable",
        runtime_detail="no model configured",
        stages=[],
        warnings=["runtime unavailable"],
        total_elapsed_ms=42.0,
        max_total_latency_ms=100,
    )

    assert telemetry["status"] == "fallback"
    assert telemetry["latency"]["over_budget"] is False
    assert telemetry["fallbacks"][0]["stage_id"] == "runtime"
    assert telemetry["fallbacks"][0]["category"] == "runtime_unavailable"


def test_summarize_readiness_telemetry_exposes_session_counters() -> None:
    telemetry = summarize_readiness_telemetry(
        runtime_payload={
            "status": "available",
            "detail": "ready",
            "counters": {
                "model_loads": 1,
                "classify_calls": 4,
                "classify_failures": 1,
                "constrained_retries": 2,
            },
            "session": {"llm_disabled_for_session": False, "disabled_reason": None},
        },
        max_total_latency_ms=250,
    )

    assert telemetry["status"] == "ok"
    assert telemetry["counters"]["classify_successes"] == 3
    assert telemetry["latency"]["cold_start_cap_ms"] == 1250.0
