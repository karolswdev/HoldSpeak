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


# --- HS-39-05: depth readiness assembler -----------------------------------

from holdspeak.dictation_telemetry import build_depth_readiness  # noqa: E402


def test_depth_guidance_fires_when_p95_near_budget():
    d = build_depth_readiness(
        stage_quantiles={"intent-router": {"p50": 100, "p95": 500, "count": 5}},
        rewrite_pass_ms=[100.0, 100.0],
        run_count=5,
        budget_ms=600,
        corrections_enabled=True,
        corrections_size=2,
        corrections_recent=["fix the cli thing"],
    )
    assert d["runs"] == 5
    assert d["rewrite_pass_ms"] == [100.0, 100.0]
    assert d["corrections"] == {"enabled": True, "size": 2, "recent": ["fix the cli thing"]}
    # 500 >= 600 * 0.66 (396) → guidance for intent-router.
    assert any(g["stage_id"] == "intent-router" for g in d["guidance"])


def test_depth_no_guidance_when_comfortably_under_budget():
    d = build_depth_readiness(
        stage_quantiles={"intent-router": {"p50": 50, "p95": 100, "count": 5}},
        rewrite_pass_ms=[],
        run_count=5,
        budget_ms=600,
        corrections_enabled=False,
        corrections_size=0,
        corrections_recent=[],
    )
    assert d["guidance"] == []


def test_depth_empty_is_valid():
    d = build_depth_readiness(
        stage_quantiles={},
        rewrite_pass_ms=[],
        run_count=0,
        budget_ms=600,
        corrections_enabled=False,
        corrections_size=0,
        corrections_recent=[],
    )
    assert d["runs"] == 0 and d["stages"] == {} and d["guidance"] == []
