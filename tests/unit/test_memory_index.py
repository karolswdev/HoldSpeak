"""HS-109-04 memory FTS freshness, ranking, filters, and overflow."""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.grounding import GROUNDING_MAX_REFS, hydrate_refs_detailed


def _decision(
    db: Database,
    decision_id: str,
    text: str,
    *,
    project: str | None = None,
    decided_at: str = "2026-01-01T00:00:00",
    meeting_id: str = "source-meeting",
) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions
               (id,text,rationale,decided_at,date_basis,source_artifact_id,
                source_meeting_id,source_state,project_key,lifecycle,
                created_at,updated_at,last_modified,deleted)
               VALUES (?,?,?,?,'meeting_date',?,?, 'linked',?,'recorded',?,?,?,0)""",
            (
                decision_id,
                text,
                "because " + text,
                decided_at,
                "source-artifact-" + decision_id,
                meeting_id,
                project,
                decided_at,
                decided_at,
                decided_at,
            ),
        )


def _artifact(db: Database, artifact_id: str, title: str, body: str, updated: str) -> None:
    db.plugins.record_artifact(
        artifact_id=artifact_id,
        meeting_id="",
        artifact_type="memo",
        title=title,
        body_markdown=body,
        updated_at=updated,
    )


def _note(db: Database, note_id: str, title: str, body: str, updated: str) -> None:
    db.notes.upsert(
        note_id=note_id,
        title=title,
        body_markdown=body,
        last_modified=updated,
        created_at=updated,
    )
    with db._connection() as conn:
        conn.execute("UPDATE notes SET updated_at=? WHERE id=?", (updated, note_id))


def test_triggers_refresh_and_drop_each_kind(tmp_path: Path) -> None:
    db = Database(tmp_path / "freshness.db")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings(id,started_at,title) VALUES ('source-meeting','2026-01-01','Source')"
        )

    _decision(db, "d1", "alpha decision")
    assert [hit.source_ref for hit in db.memory.search("alpha").hits] == ["decision:d1"]
    with db._connection() as conn:
        conn.execute(
            "UPDATE decisions SET text='beta decision', rationale='because beta' WHERE id='d1'"
        )
    assert db.memory.search("alpha").total == 0
    assert db.memory.search("beta").total == 1
    with db._connection() as conn:
        conn.execute("DELETE FROM meetings WHERE id='source-meeting'")
    assert db.memory.search("beta").total == 0
    assert db.decisions.get("d1").source_state == "source_deleted"

    _artifact(db, "a1", "Alpha artifact", "artifact body", "2026-01-02T00:00:00")
    assert db.memory.search("alpha", kinds=["artifact"]).total == 1
    _artifact(db, "a1", "Beta artifact", "changed", "2026-01-03T00:00:00")
    assert db.memory.search("alpha", kinds=["artifact"]).total == 0
    assert db.memory.search("beta", kinds=["artifact"]).total == 1
    assert db.plugins.delete_artifact("a1") is True
    assert db.memory.search("beta", kinds=["artifact"]).total == 0

    _note(db, "n1", "Alpha note", "note body", "2026-01-04T00:00:00")
    assert db.memory.search("alpha", kinds=["note"]).total == 1
    _note(db, "n1", "Beta note", "changed", "2026-01-05T00:00:00")
    assert db.memory.search("alpha", kinds=["note"]).total == 0
    assert db.memory.search("beta", kinds=["note"]).total == 1
    assert db.notes.delete("n1") is True
    assert db.memory.search("beta", kinds=["note"]).total == 0


def test_ranking_is_deterministic_normalized_and_interleaved(tmp_path: Path) -> None:
    db = Database(tmp_path / "ranking.db")
    _decision(db, "d1", "retry policy retry policy", decided_at="2024-01-01T00:00:00")
    _decision(db, "d2", "retry policy", decided_at="2026-01-01T00:00:00")
    _artifact(db, "a1", "Retry policy", "retry " * 200, "2025-01-01T00:00:00")
    _note(db, "n1", "Retry policy", "short retry policy", "2025-06-01T00:00:00")

    first = db.memory.search("retry policy").hits
    second = db.memory.search("retry policy").hits
    assert [hit.source_ref for hit in first] == [hit.source_ref for hit in second]
    assert {hit.kind for hit in first[:3]} == {"decision", "artifact", "note"}
    assert [hit.kind_rank for hit in first[:3]] == [1, 1, 1]
    assert first[3].kind == "decision" and first[3].kind_rank == 2
    assert all(0.0 <= hit.normalized_score <= 1.0 for hit in first)
    assert [hit.rank for hit in first] == list(range(1, len(first) + 1))


def test_project_kind_time_filters_and_idempotent_rebuild(tmp_path: Path) -> None:
    db = Database(tmp_path / "filters.db")
    db.projects.create_project(project_id="p1", name="One")
    db.projects.create_project(project_id="p2", name="Two")
    _decision(db, "d1", "retention answer", project="p1", decided_at="2024-01-01T00:00:00")
    _decision(db, "d2", "retention answer", project="p2", decided_at="2026-01-01T00:00:00")
    _note(db, "n1", "Retention", "retention answer", "2025-01-01T00:00:00")
    db.project_relationships.upsert(project_id="p1", resource_ref="note:n1")

    p1 = db.memory.search("retention", project_id="p1")
    assert {hit.source_ref for hit in p1.hits} == {"decision:d1", "note:n1"}
    recent = db.memory.search("retention", time_from="2025-06-01T00:00:00")
    assert [hit.source_ref for hit in recent.hits] == ["decision:d2"]
    historical = db.memory.search("retention", time_to="2025-01-01T00:00:00")
    assert {hit.source_ref for hit in historical.hits} == {"decision:d1", "note:n1"}
    notes = db.memory.search("retention", kinds="note", project_id="p1")
    assert [hit.source_ref for hit in notes.hits] == ["note:n1"]
    assert db.memory.rebuild() == db.memory.rebuild() == {
        "decisions": 2,
        "artifacts": 0,
        "notes": 1,
        "total": 3,
    }


def test_project_grounding_counts_overflow_and_labels_recency(tmp_path: Path) -> None:
    db = Database(tmp_path / "overflow.db")
    db.projects.create_project(project_id="p1", name="Archive")
    for index in range(GROUNDING_MAX_REFS + 3):
        note_id = f"n{index:02d}"
        _note(
            db,
            note_id,
            f"Retry {index}",
            "retry budget policy",
            f"2026-01-{index + 1:02d}T00:00:00",
        )
        db.project_relationships.upsert(
            project_id="p1",
            resource_ref=f"note:{note_id}",
            last_modified=f"2026-01-{index + 1:02d}T00:00:00",
        )

    relevant = hydrate_refs_detailed(
        db, [], [], "summary", qualified_refs=["project:p1"], query="retry policy"
    )
    assert relevant.selection == "relevance"
    assert relevant.matched_count == GROUNDING_MAX_REFS + 3
    assert relevant.overflow_count == 3
    assert len(relevant.blocks) == GROUNDING_MAX_REFS
    assert all(ref.startswith("note:") for ref in relevant.source_refs)

    fallback = hydrate_refs_detailed(
        db, [], [], "summary", qualified_refs=["project:p1"]
    )
    assert fallback.selection == "recency_fallback"
    assert fallback.matched_count == GROUNDING_MAX_REFS + 3
    assert fallback.overflow_count == 3
    assert fallback.blocks[0].ref == f"n{GROUNDING_MAX_REFS + 2:02d}"
