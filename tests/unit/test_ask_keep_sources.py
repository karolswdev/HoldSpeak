"""Ask Keep persists canonical typed sources without running a model."""

from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.ask_service import AskService
from holdspeak.services.errors import ValidationError


OWNER = Principal(PrincipalKind.OWNER, "ask-keep-sources-owner")


@pytest.fixture
def rig(tmp_path: Path):
    db = Database(tmp_path / "ask-keep.db")
    db.notes.upsert(note_id="source-note", title="Release gate", body_markdown="Restore before release.")
    db.kbs.upsert(kb_id="source-knowledge", name="Release notes", member_ids=["note:source-note"])
    db.directories.upsert(directory_id="source-zone", name="Release")
    db.directory_memberships.upsert(primitive_id="note:source-note", directory_id="source-zone")
    db.projects.create_project(project_id="source-project", name="Release")
    db.project_relationships.upsert(project_id="source-project", resource_ref="note:source-note")
    service = AskService(db, broker=_configure(db))
    yield db, service
    db.close()


def test_keep_persists_note_and_knowledge_sources_with_exact_prompt_and_relationships(rig):
    db, service = rig
    prompt = "What must happen first?\n\nSelected text:\n> Restore before release."
    result = service.keep(
        OWNER,
        "Verify the restore path first.",
        [
            {"id": "source-note", "kind": "note", "ref": "note:source-note", "title": "Release gate"},
            {"id": "source-knowledge", "kind": "kb", "ref": "knowledge:source-knowledge", "title": "Release notes"},
        ],
        lens="Ask",
        prompt=prompt,
    )
    artifact_id = result["artifact_id"]
    db.close()
    reopened = Database(db.db_path)
    try:
        artifact = reopened.plugins.get_artifact(artifact_id)
        assert artifact is not None
        assert artifact.body_markdown == "Verify the restore path first."
        assert {(source["source_type"], source["source_ref"]) for source in artifact.sources} == {
            ("note", "note:source-note"),
            ("knowledge", "knowledge:source-knowledge"),
            ("ask", "Ask"),
        }
        assert artifact.structured_json["qualified_refs"] == ["note:source-note", "knowledge:source-knowledge"]
        assert artifact.structured_json["provenance"]["prompt"] == prompt
        assert artifact.structured_json["relationship_snapshot"]["note:source-note"] == {
            "zone_id": "source-zone",
            "knowledge_ids": ["source-knowledge"],
            "project_ids": ["source-project"],
        }
        assert [item.id for item in reopened.plugins.list_artifacts_by_source("note", "note:source-note")] == [artifact_id]
        assert [item.id for item in reopened.plugins.list_artifacts_by_source("knowledge", "knowledge:source-knowledge")] == [artifact_id]
    finally:
        reopened.close()


def test_keep_accepts_real_zone_grounding_as_a_typed_source(rig):
    db, service = rig
    result = service.keep(
        OWNER,
        "The release note names the restore gate.",
        [],
        prompt="Review the release zone.",
        grounding={"refs": ["zone:source-zone"]},
    )
    artifact = db.plugins.get_artifact(result["artifact_id"])
    assert artifact is not None
    assert {"source_type": "zone", "source_ref": "zone:source-zone"} in artifact.sources
    assert artifact.structured_json["qualified_refs"] == ["zone:source-zone"]
    assert artifact.structured_json["provenance"]["prompt"] == "Review the release zone."


def test_keep_rejects_an_unknown_qualified_source_kind(rig):
    db, service = rig
    with pytest.raises(ValidationError, match="unknown resource kind: invented"):
        service.keep(OWNER, "An answer", [{"ref": "invented:source-note"}])
    assert db.plugins.list_run_artifacts() == []


def test_artifact_store_still_rejects_an_unknown_source_type(rig):
    db, _service = rig
    with pytest.raises(ValueError, match="Invalid artifact source type: 'invented'"):
        db.plugins.record_artifact(
            artifact_id="invalid-source",
            meeting_id="",
            artifact_type="plugin_output",
            title="Invalid",
            sources=[{"source_type": "invented", "source_ref": "invented:source-note"}],
        )
    assert db.plugins.get_artifact("invalid-source") is None
