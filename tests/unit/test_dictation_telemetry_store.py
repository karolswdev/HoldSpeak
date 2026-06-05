"""HS-39-05: session dictation telemetry store + quantiles."""

from __future__ import annotations

from types import SimpleNamespace

from holdspeak.plugins.dictation.telemetry_store import DictationTelemetryStore, quantile


def _run(stages: list[tuple[str, float, dict]], total: float = 0.0) -> SimpleNamespace:
    return SimpleNamespace(
        stage_results=[
            SimpleNamespace(stage_id=s, elapsed_ms=ms, metadata=meta) for (s, ms, meta) in stages
        ],
        total_elapsed_ms=total,
    )


def test_quantile_basics():
    assert quantile([], 0.5) is None
    assert quantile([5.0], 0.95) == 5.0
    assert quantile([0.0, 10.0], 0.5) == 5.0


def test_empty_store_is_nulls_not_error():
    st = DictationTelemetryStore()
    assert st.run_count() == 0
    assert st.stage_quantiles() == {}
    assert st.latest_rewrite_pass_ms() == []


def test_records_and_computes_quantiles():
    st = DictationTelemetryStore()
    for ms in (10, 20, 30, 40, 100):
        st.record_run(_run([("intent-router", float(ms), {})]))
    q = st.stage_quantiles()["intent-router"]
    assert q["count"] == 5
    assert q["p50"] == 30.0  # median of 10,20,30,40,100
    assert q["p95"] >= 40.0


def test_latest_rewrite_pass_ms_uses_most_recent_with_passes():
    st = DictationTelemetryStore()
    st.record_run(_run([("project-rewriter", 200.0, {"rewrite_pass_ms": [90.0, 110.0]})]))
    st.record_run(_run([("intent-router", 10.0, {})]))  # no rewrite passes
    assert st.latest_rewrite_pass_ms() == [90.0, 110.0]


def test_ring_caps_at_capacity():
    st = DictationTelemetryStore(cap=3)
    for i in range(5):
        st.record_run(_run([("s", float(i), {})]))
    assert st.run_count() == 3
