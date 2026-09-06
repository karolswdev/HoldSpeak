"""Pins the relationship-aware memory boundary across HoldSpeak features."""

from __future__ import annotations

from holdspeak.db import Database
from holdspeak.grounding import hydrate_refs_detailed
from holdspeak.workbench_conductor import _hydrate_item_grounding


TOKEN = "ecosystem_aurora"


def _seed(db: Database) -> None:
    now = "2026-08-31T12:00:00+00:00"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO projects(id,name,created_at,updated_at) VALUES('p1','Launch',?,?)",
            (now, now),
        )
        conn.execute(
            "INSERT INTO meetings(id,started_at,title) VALUES('m1',?,'Launch review')",
            (now,),
        )
        conn.execute(
            "INSERT INTO meeting_projects(meeting_id,project_id) VALUES('m1','p1')"
        )
        conn.execute(
            "INSERT INTO segments(meeting_id,text,speaker,start_time,end_time) VALUES('m1','supporting meeting context','Me',0,1)"
        )
        conn.execute(
            """INSERT INTO decision_records
               (id,decision_text,rationale,source_type,source_id,created_at,updated_at)
               VALUES('dr1',?,'canonical rationale','desk','dd1',?,?)""",
            (f"Decision {TOKEN}", now, now),
        )
        conn.execute(
            """INSERT INTO desk_decisions
               (id,title,decision_markdown,context_markdown,created_at,updated_at)
               VALUES('dd1','Authored decision',?,'context',?,?)""",
            (f"Choose {TOKEN}", now, now),
        )
        conn.execute(
            """INSERT INTO action_items
               (id,meeting_id,task,status,created_at)
               VALUES('a1','m1',?,'pending',?)""",
            (f"Deliver {TOKEN}", now),
        )
        conn.execute(
            """INSERT INTO project_items
               (id,project_id,item_type,title,summary,created_at,updated_at)
               VALUES('pi1','p1','risk','Launch risk',?,?,?)""",
            (f"Risk around {TOKEN}", now, now),
        )
        conn.execute(
            """INSERT INTO workbench_items
               (id,workbench_id,title,body,result,created_at,last_modified)
               VALUES('wi1','w1','Workbench finding',?,?,?,?)""",
            (f"Investigate {TOKEN}", "Resolved safely", now, now),
        )
        conn.execute(
            """INSERT INTO cadence_loops
               (id,source_type,source_id,project,title,summary,created_at,updated_at)
               VALUES('c1','project','p1','p1','Review loop',?,?,?)""",
            (f"Follow up {TOKEN}", now, now),
        )
    for ref in (
        "decision_record:dr1",
        "desk_decision:dd1",
        "workbench_item:wi1",
    ):
        db.project_relationships.upsert(project_id="p1", resource_ref=ref)


def test_memory_search_covers_content_bearing_feature_stores(tmp_path) -> None:
    db = Database(tmp_path / "ecosystem.db")
    _seed(db)

    expected = {
        "decision_record",
        "desk_decision",
        "action",
        "project_item",
        "workbench_item",
        "cadence",
    }
    result = db.memory.search(TOKEN, project_id="p1")
    kinds = {hit.kind for hit in result.hits}

    assert expected <= kinds
    assert "meeting" in kinds  # authoritative action -> source Meeting edge
    assert any(
        hit.retrieval_origin == "relationship" and hit.relationship == "source_meeting"
        for hit in result.hits
    )


def test_every_new_memory_kind_hydrates_as_citable_context(tmp_path) -> None:
    db = Database(tmp_path / "hydrate.db")
    _seed(db)
    refs = [
        "decision_record:dr1",
        "desk_decision:dd1",
        "action:a1",
        "project_item:pi1",
        "workbench_item:wi1",
        "cadence:c1",
    ]

    hydrated = hydrate_refs_detailed(db, [], [], "summary", qualified_refs=refs)

    assert hydrated.unknown == []
    assert {f"{block.kind}:{block.ref}" for block in hydrated.blocks} == set(refs)


def test_unattached_model_context_uses_ecosystem_retrieval(tmp_path) -> None:
    db = Database(tmp_path / "automatic.db")
    db.notes.upsert(
        note_id="n1",
        title="Architecture",
        body_markdown=f"The foundation keyword is {TOKEN}.",
    )

    hydrated = hydrate_refs_detailed(
        db,
        [],
        [],
        "summary",
        query=f"What is {TOKEN}?",
        include_memory=True,
    )
    workbench = _hydrate_item_grounding(
        db,
        "{}",
        query=f"Explain {TOKEN}",
    )

    assert hydrated.selection == "ecosystem_relevance"
    assert hydrated.source_refs == ["note:n1"]
    assert TOKEN in workbench
