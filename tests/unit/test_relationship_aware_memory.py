"""Parent-context recall and authoritative one-hop memory expansion."""

from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.grounding import hydrate_refs_detailed


def _note(db: Database, note_id: str, title: str, body: str) -> None:
    db.notes.upsert(
        note_id=note_id,
        title=title,
        body_markdown=body,
        last_modified="2026-01-01",
        created_at="2026-01-01",
    )


def test_transcript_child_recalls_parent_and_expands_real_lineage(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "parent_graph.db")
    db.projects.create_project(project_id="p1", name="Launch")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings(id,started_at,title) VALUES ('m1','2026-02-01','Launch review')"
        )
        conn.execute(
            """INSERT INTO segments(meeting_id,text,speaker,start_time,end_time)
               VALUES ('m1','The zephyr rollout starts Friday','Ada',0,4)"""
        )
        conn.execute(
            """INSERT INTO meeting_projects(meeting_id,project_id,source,confidence)
               VALUES ('m1','p1','manual',1)"""
        )
    db.plugins.record_artifact(
        artifact_id="a1",
        meeting_id="m1",
        artifact_type="memo",
        title="Rollout checklist",
        body_markdown="Owners and gates",
        updated_at="2026-02-02",
    )

    result = db.memory.search("zephyr", project_id="p1")
    assert [hit.source_ref for hit in result.hits] == ["meeting:m1", "artifact:a1"]
    meeting, artifact = result.hits
    assert meeting.retrieval_origin == "lexical"
    assert "<mark>zephyr</mark>" in meeting.snippet.lower()
    assert artifact.retrieval_origin == "relationship"
    assert artifact.related_to == "meeting:m1"
    assert artifact.relationship == "meeting_artifact"
    ranking = result.to_dict()["ranking"]
    assert ranking["relationship_expansion"]["expanded_count"] == 1
    assert ranking["parent_context"].startswith("matching transcript")


def test_project_thread_search_is_scoped_and_hydrates_parent(tmp_path: Path) -> None:
    db = Database(tmp_path / "thread_scope.db")
    db.projects.create_project(project_id="p1", name="One")
    db.projects.create_project(project_id="p2", name="Two")
    _note(db, "n1", "One", "first project")
    _note(db, "n2", "Two", "second project")
    db.project_relationships.upsert(project_id="p1", resource_ref="note:n1")
    db.project_relationships.upsert(project_id="p2", resource_ref="note:n2")

    for note_id, title in (("n1", "P1 thread"), ("n2", "P2 thread")):
        thread = db.threads.create_thread(title=title)
        message = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(message.id, kind="text", text="zephyr planning")
        db.threads.freeze_refs(
            thread.id,
            message.id,
            [{"ref_kind": "note", "ref_id": note_id}],
        )

    secret = db.threads.create_thread(title="Private draft")
    secret_message = db.threads.append_message(secret.id, role="user")
    db.threads.append_part(
        secret_message.id, kind="text", text="zephyr secret", sensitive=True
    )
    db.threads.freeze_refs(
        secret.id,
        secret_message.id,
        [{"ref_kind": "note", "ref_id": "n1"}],
    )

    result = db.memory.search("zephyr", project_id="p1", kinds=["thread"])
    assert len(result.hits) == 1
    assert result.hits[0].title == "P1 thread"

    grounded = hydrate_refs_detailed(
        db, [], [], "summary", qualified_refs=["project:p1"], query="zephyr"
    )
    thread_blocks = [block for block in grounded.blocks if block.kind == "thread"]
    assert len(thread_blocks) == 1
    assert thread_blocks[0].title == "P1 thread"
    assert "user: zephyr planning" in thread_blocks[0].text


def test_decision_record_raw_source_edges_are_scoped_and_bidirectional(
    tmp_path: Path,
) -> None:
    """Exercise the exact `(source_type, raw id)` shape the service persists."""
    db = Database(tmp_path / "record_edges.db")
    db.projects.create_project(project_id="p1", name="Launch")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings(id,started_at,title) VALUES ('m1','2026-03-01','Review')"
        )
        conn.execute(
            """INSERT INTO meeting_projects(meeting_id,project_id,source,confidence)
               VALUES ('m1','p1','manual',1)"""
        )
        conn.execute(
            """INSERT INTO segments(meeting_id,text,speaker,start_time,end_time)
               VALUES ('m1','zephyr evidence was approved','Mina',0,2)"""
        )
        conn.execute(
            """INSERT INTO decision_records
               (id,decision_text,rationale,source_type,source_id,created_at,updated_at)
               VALUES ('dr1','Adopt aurora routing','Canonical verdict','meeting','d1',
                       '2026-03-01','2026-03-01')"""
        )
        conn.execute(
            """INSERT INTO decision_record_sources
               (id,record_id,source_type,source_ref,created_at)
               VALUES ('drs1','dr1','meeting','m1','2026-03-01')"""
        )

    from_record = db.memory.search(
        "aurora", project_id="p1", kinds=["decision_record", "meeting"]
    )
    assert [hit.source_ref for hit in from_record.hits] == [
        "decision_record:dr1",
        "meeting:m1",
    ]
    assert from_record.hits[1].relationship == "decision_record_source"

    from_meeting = db.memory.search(
        "zephyr", project_id="p1", kinds=["meeting", "decision_record"]
    )
    assert [hit.source_ref for hit in from_meeting.hits] == [
        "meeting:m1",
        "decision_record:dr1",
    ]
    assert from_meeting.hits[1].relationship == "supports_decision_record"


def test_relationship_fanout_cannot_monopolize_a_bounded_page(tmp_path: Path) -> None:
    db = Database(tmp_path / "bounded_graph.db")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings(id,started_at,title) VALUES ('m1','2026-03-01','Review')"
        )
        conn.execute(
            """INSERT INTO segments(meeting_id,text,speaker,start_time,end_time)
               VALUES ('m1','zephyr fanout','Mina',0,2)"""
        )
    for index in range(6):
        db.plugins.record_artifact(
            artifact_id=f"a{index}",
            meeting_id="m1",
            artifact_type="memo",
            title=f"Evidence {index}",
            body_markdown="supporting material",
            updated_at=f"2026-03-0{index + 1}",
        )

    result = db.memory.search("zephyr", kinds=["meeting", "artifact"])

    assert result.lexical_total == 1
    assert result.expanded_total == 2
    assert [hit.retrieval_origin for hit in result.hits] == [
        "lexical",
        "relationship",
        "relationship",
    ]


def test_long_model_prompt_keeps_both_query_ends_bounded(tmp_path: Path) -> None:
    db = Database(tmp_path / "long_query.db")
    _note(db, "n1", "Needle", "tailneedle is the governing term")
    filler = " ".join(f"unmatchedterm{index}" for index in range(40))

    result = db.memory.search(f"headneedle {filler} tailneedle", kinds=["note"])

    assert [hit.source_ref for hit in result.hits] == ["note:n1"]
