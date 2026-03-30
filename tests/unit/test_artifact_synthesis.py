from __future__ import annotations

from types import SimpleNamespace

from holdspeak.plugins.synthesis import synthesize_meeting_artifacts


def test_synthesis_dedupes_identical_outputs_and_keeps_lineage() -> None:
    runs = [
        SimpleNamespace(
            id=101,
            meeting_id="m-1",
            window_id="m-1:w0001",
            plugin_id="requirements_extractor",
            plugin_version="1.0.0",
            status="success",
            output={
                "summary": "Define API contract and acceptance criteria.",
                "confidence_hint": 0.82,
                "active_intents": ["architecture", "delivery"],
            },
            created_at="2026-03-29T18:00:00",
        ),
        SimpleNamespace(
            id=102,
            meeting_id="m-1",
            window_id="m-1:w0002",
            plugin_id="requirements_extractor",
            plugin_version="1.0.0",
            status="deduped",
            output={
                "summary": "Define API contract and acceptance criteria.",
                "confidence_hint": 0.82,
                "active_intents": ["architecture", "delivery"],
            },
            created_at="2026-03-29T18:00:05",
        ),
    ]

    artifacts = synthesize_meeting_artifacts(meeting_id="m-1", plugin_runs=runs)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.plugin_id == "requirements_extractor"
    assert artifact.artifact_type == "requirements"
    source_refs = {(source.source_type, source.source_ref) for source in artifact.sources}
    assert ("intent_window", "m-1:w0001") in source_refs
    assert ("intent_window", "m-1:w0002") in source_refs
    assert ("plugin_run", "101") in source_refs
    assert ("plugin_run", "102") in source_refs


def test_synthesis_skips_failed_runs() -> None:
    runs = [
        SimpleNamespace(
            id=201,
            meeting_id="m-2",
            window_id="m-2:w0001",
            plugin_id="risk_heatmap",
            plugin_version="1.0.0",
            status="error",
            output={"summary": "ignored"},
            created_at="2026-03-29T18:10:00",
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-2", plugin_runs=runs)
    assert artifacts == []


def test_synthesis_marks_low_confidence_as_needs_review() -> None:
    runs = [
        SimpleNamespace(
            id=301,
            meeting_id="m-3",
            window_id="m-3:w0001",
            plugin_id="scope_guard",
            plugin_version="1.0.0",
            status="success",
            output={
                "summary": "Potential scope creep in release notes.",
                "confidence_hint": 0.21,
                "active_intents": ["product"],
            },
            created_at="2026-03-29T18:20:00",
        )
    ]
    artifacts = synthesize_meeting_artifacts(meeting_id="m-3", plugin_runs=runs)
    assert len(artifacts) == 1
    assert artifacts[0].status == "needs_review"
    assert artifacts[0].confidence < 0.55

