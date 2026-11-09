# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_artifact_synthesis_persist.py to restore.

# ruff: noqa


# --- test_to_artifact_lineage_separates_window_and_plugin_run_sources: P5: the field mapping is covered end to end by test_synthesize_and_persist_writes_artifacts_with_lineage
def test_to_artifact_lineage_separates_window_and_plugin_run_sources() -> None:
    draft = ArtifactDraft(
        artifact_id="art-001",
        meeting_id="m-1",
        artifact_type="requirements",
        title="Requirements summary",
        body_markdown="body",
        structured_json={},
        confidence=0.8,
        status="draft",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        sources=[
            ArtifactSourceRef(source_type="intent_window", source_ref="m-1:w0001"),
            ArtifactSourceRef(source_type="intent_window", source_ref="m-1:w0002"),
            ArtifactSourceRef(source_type="plugin_run", source_ref="101"),
            ArtifactSourceRef(source_type="plugin_run", source_ref="102"),
        ],
    )

    lineage = to_artifact_lineage(draft)

    assert isinstance(lineage, ArtifactLineage)
    assert lineage.artifact_id == "art-001"
    assert lineage.meeting_id == "m-1"
    assert lineage.window_ids == ["m-1:w0001", "m-1:w0002"]
    assert lineage.plugin_run_keys == ["101", "102"]


# --- test_to_artifact_lineage_empty_sources_yields_empty_lists: P5: the field mapping is covered end to end by test_synthesize_and_persist_writes_artifacts_with_lineage
def test_to_artifact_lineage_empty_sources_yields_empty_lists() -> None:
    draft = ArtifactDraft(
        artifact_id="art-empty",
        meeting_id="m-1",
        artifact_type="t",
        title="t",
        body_markdown="",
        structured_json={},
        confidence=0.5,
        status="needs_review",
        plugin_id="p",
        plugin_version="v",
        sources=[],
    )

    lineage = to_artifact_lineage(draft)

    assert lineage.window_ids == []
    assert lineage.plugin_run_keys == []
