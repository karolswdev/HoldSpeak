"""Astra's review of PR #795: five findings, one fence each.

Each test is red on the first cut of slice 1 and green after the fix.  All
writes go through the real producers; the engine gives fixed vectors by text.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from holdspeak.db import Database
from holdspeak.meeting_session.models import MeetingState, TranscriptSegment
from holdspeak.memory.retain import embed_pending, rebuild, sweep


class TextEngine:
    """One fixed unit vector per text.  ``near`` texts sit next to the question."""

    model_id = "text-engine@8"
    dim = 8

    def __init__(self, near: tuple[str, ...] = ()) -> None:
        self.near = near

    def _vector(self, text: str) -> np.ndarray:
        import hashlib

        for rank, word in enumerate(self.near):
            if word in text:
                vector = np.zeros(8, dtype=np.float32)
                vector[0] = 1.0
                vector[1] = 0.05 * rank  # a later word is a little further away
                return vector / np.linalg.norm(vector)
        raw = np.frombuffer(hashlib.sha256(text.encode()).digest()[:8], dtype=np.uint8).astype(np.float32)
        raw[0] = 0.0
        return raw / (np.linalg.norm(raw) or 1.0)

    def embed_documents(self, texts):
        return np.vstack([self._vector(text) for text in texts])

    def embed_query(self, text):
        vector = np.zeros(8, dtype=np.float32)
        vector[0] = 1.0
        return vector


def _everything(result) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False)


# ── 1 (P1): admission is checked at READ time, against the current source ──


def test_a_part_recreated_as_sensitive_never_surfaces_from_the_vector_index(tmp_path: Path) -> None:
    db = Database(tmp_path / "p1.db")
    thread = db.threads.create_thread(title="Compensation")
    message = db.threads.append_message(thread.id, role="user")
    part = db.threads.append_part(message.id, kind="text", text="NEARWORD the raise is nine percent")
    engine = TextEngine(near=("NEARWORD",))
    rebuild(db, engine)
    db.memory.set_embedder(engine)
    assert "nine percent" in _everything(db.memory.search("salary raise"))

    # The owner makes it sensitive: the part is deleted and written again.
    assert db.threads.delete_part(part.id)
    again = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(again.id, kind="text", text="NEARWORD the raise is nine percent", sensitive=True)

    # No sweep has run.  The index still holds the old chunk and its vector.
    assert db.memory_index.stats()["vectors"] == 1
    answer = db.memory.search("salary raise")
    assert "nine percent" not in _everything(answer) and "NEARWORD" not in _everything(answer)
    assert answer.hits == []


def test_a_source_that_left_never_surfaces_before_the_next_sweep(tmp_path: Path) -> None:
    db = Database(tmp_path / "p1b.db")
    db.notes.upsert(note_id="gone", title="Gone", body_markdown="NEARWORD deleted note text")
    db.notes.upsert(note_id="promoted", title="Promoted", body_markdown="NEARWORD promoted note text")
    db.notes.upsert(note_id="edited", title="Edited", body_markdown="NEARWORD the old wording OLDTEXT")
    db.notes.upsert(note_id="kept", title="Kept", body_markdown="NEARWORD kept note text")
    started = datetime(2026, 9, 1, 10, 0, 0)
    db.meetings.save_meeting(MeetingState(
        id="m1", started_at=started, ended_at=started, title="Parked later",
        segments=[TranscriptSegment(text="NEARWORD parked meeting text", speaker="Me", start_time=0.0, end_time=1.0)],
    ))
    engine = TextEngine(near=("NEARWORD",))
    rebuild(db, engine)
    db.memory.set_embedder(engine)
    assert len(db.memory.search("anything").hits) == 5

    db.notes.delete("gone")
    db.meetings.delete_meeting("m1")
    db.notes.upsert(note_id="edited", title="Edited", body_markdown="Entirely new wording")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO context_promotions(
                   promotion_id, thread_id, fact_id, source_message_id,
                   quote_sha256, quote_locator_json, target_kind, target_ref,
                   target_revision_label, target_content_sha256,
                   disclosure_state, request_sha256, created_at, updated_at)
               VALUES ('cp1','th1','f1','msg-1','sha256:q','{}','note','note:promoted',
                       '2026-09-07T09:00:00Z','sha256:c','active','sha256:r',
                       '2026-09-07T09:00:00Z','2026-09-07T09:00:00Z')"""
        )
    answer = db.memory.search("anything")
    assert [hit.source_ref for hit in answer.hits] == ["note:kept"]
    # The cached chunk text of a changed source is never the snippet.
    assert "OLDTEXT" not in _everything(answer)


# ── 2 (P1): a secret is in nothing memory indexes and nothing it returns ──


SECRETS = (
    "TITLE_SENTINEL", "BODY_SENTINEL", "ARTIFACT_SENTINEL", "THREAD_SENTINEL", "MEETING_SENTINEL",
    "ONEWORDSENTINEL",  # no separator: one keyword token, so a token index would hold it whole
)


def _index_tables(conn: sqlite3.Connection) -> list[str]:
    """Every table memory owns: ``memory_*`` and the memory keyword tables
    with their FTS shadow tables."""
    names = [str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    return sorted(name for name in names if name.startswith("memory_") or "_memory_fts" in name)


def _grep(db: Database, tables: list[str]) -> list[str]:
    found = []
    with db._connection() as conn:
        for table in tables:
            for row in conn.execute(f'SELECT * FROM "{table}"'):
                blob = " ".join(
                    value.decode("utf-8", "ignore") if isinstance(value, bytes) else str(value)
                    for value in tuple(row)
                ).casefold()
                found.extend(f"{table}: {secret}" for secret in SECRETS if secret.casefold() in blob)
    return sorted(set(found))


def test_a_secret_is_in_no_memory_table_and_no_search_result(tmp_path: Path) -> None:
    db = Database(tmp_path / "p2.db")
    db.notes.upsert(
        note_id="s1", title="Deploy token=TITLE_SENTINEL",
        body_markdown="NEARWORD staging deploy uses password=BODY_SENTINEL for the API. Also secret=hunter2ONEWORDSENTINEL here.",
    )
    db.plugins.record_artifact(
        artifact_id="a1", meeting_id="", artifact_type="memo", title="Deploy memo",
        body_markdown="NEARWORD the deploy key is api_key=ARTIFACT_SENTINEL today.",
    )
    thread = db.threads.create_thread(title="Deploy chat")
    message = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(message.id, kind="text", text="NEARWORD deploy with secret=THREAD_SENTINEL please")
    started = datetime(2026, 9, 1, 10, 0, 0)
    db.meetings.save_meeting(MeetingState(
        id="m1", started_at=started, ended_at=started, title="Deploy sync",
        segments=[TranscriptSegment(text="NEARWORD the deploy token=MEETING_SENTINEL was read aloud", speaker="Me", start_time=0.0, end_time=1.0)],
    ))
    engine = TextEngine(near=("NEARWORD",))

    def check(stage: str) -> None:
        with db._connection() as conn:
            tables = _index_tables(conn)
        assert {"notes_memory_fts", "notes_memory_fts_content", "artifacts_memory_fts_content", "memory_chunks"} <= set(tables)
        assert _grep(db, tables) == [], stage
        for embedder in (None, engine):
            db.memory.set_embedder(embedder)
            for query in ("deploy", "staging deploy password", "token", "TITLE_SENTINEL", "BODY_SENTINEL api key"):
                answer = db.memory.search(query, limit=50)
                if "SENTINEL" not in query or embedder is not None:
                    assert answer.hits, (stage, query)
                text = _everything(answer)
                assert not [secret for secret in SECRETS if secret in text], (stage, query, embedder)
        recent = json.dumps(db.memory.recent(limit=50))
        assert not [secret for secret in SECRETS if secret in recent], stage

    def results_clean(stage: str) -> None:
        for embedder in (None, engine):
            db.memory.set_embedder(embedder)
            for query in ("deploy", "staging deploy password", "BODY_SENTINEL"):
                text = _everything(db.memory.search(query, limit=50))
                assert not [secret for secret in SECRETS if secret in text], (stage, query)

    # Before any sweep the triggers have copied the raw text; no RESULT may
    # carry it even then.
    results_clean("before the sweep")
    assert sweep(db)["scrubbed"] == 2  # the note and the artifact
    embed_pending(db, engine)
    check("sweep")
    # A source update makes the trigger copy the raw text again, with no
    # change to the memory hash.  The next sweep scrubs it again.
    with db._connection() as conn:
        conn.execute("UPDATE notes SET tags_json='[\"x\"]' WHERE id='s1'")
        assert "BODY_SENTINEL" in str(tuple(conn.execute("SELECT * FROM notes_memory_fts").fetchone()))
    results_clean("after a source update")
    again = sweep(db)
    assert again["written"] == 0 and again["scrubbed"] == 1
    check("second sweep")
    rebuild(db, engine)
    check("rebuild")
    # The secret is not a search key either: the keyword tables hold no token of it.
    db.memory.set_embedder(None)
    assert [hit.kind for hit in db.memory.search("BODY_SENTINEL").hits if hit.kind in ("note", "artifact")] == []


# ── 3 (P2): parked is honoured for every kind ─────────────────────────────


def test_a_parked_workbench_item_is_in_no_retriever(tmp_path: Path) -> None:
    db = Database(tmp_path / "p3.db")
    db.workbenches.upsert(workbench_id="wb1", name="Bench")
    db.workbench_items.upsert(item_id="w-parked", workbench_id="wb1", title="Parked item", body="NEARWORD parked bench text")
    db.workbench_items.upsert(item_id="w-live", workbench_id="wb1", title="Live item", body="NEARWORD live bench text")
    engine = TextEngine(near=("NEARWORD",))
    rebuild(db, engine)
    db.memory.set_embedder(engine)
    assert {hit.source_ref for hit in db.memory.search("bench text").hits} == {"workbench_item:w-parked", "workbench_item:w-live"}

    parked, _error, _missing = db.workbench_items.park_many("wb1", ["w-parked"])
    assert parked == ["w-parked"]
    # Before the sweep: neither the keyword pass nor the vector pass returns it.
    for embedder in (None, engine):
        db.memory.set_embedder(embedder)
        assert {hit.source_ref for hit in db.memory.search("bench text").hits} == {"workbench_item:w-live"}
    assert "workbench_item:w-parked" not in {row["source_ref"] for row in db.memory.recent(limit=50)}
    sweep(db)
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM memory_chunks WHERE source_ref='workbench_item:w-parked'").fetchone()[0] == 0
    db.workbench_items.restore_many("wb1", ["w-parked"])
    sweep(db)
    embed_pending(db, engine)
    db.memory.set_embedder(engine)
    assert "workbench_item:w-parked" in {hit.source_ref for hit in db.memory.search("bench text").hits}


# ── 4 (P2): the scope is applied before the top-k cut ─────────────────────


def test_other_projects_cannot_exhaust_scoped_recall(tmp_path: Path) -> None:
    db = Database(tmp_path / "p4.db")
    db.projects.create_project(project_id="a", name="A")
    db.projects.create_project(project_id="b", name="B")
    # 450 sources of project B sit NEARER the question than project A's note.
    for index in range(450):
        db.notes.upsert(note_id=f"b{index:03d}", title=f"B {index}", body_markdown=f"CLOSEST text number {index}")
        db.project_relationships.upsert(project_id="b", resource_ref=f"note:b{index:03d}")
    db.notes.upsert(note_id="a-note", title="A note", body_markdown="SECOND the one matching note of project A")
    db.project_relationships.upsert(project_id="a", resource_ref="note:a-note")
    engine = TextEngine(near=("CLOSEST", "SECOND"))
    rebuild(db, engine)
    db.memory.set_embedder(engine)

    scoped = db.memory.search("the question", project_id="a", limit=10)
    assert [hit.source_ref for hit in scoped.hits] == ["note:a-note"]
    # Kinds and time are scope too.
    db.notes.upsert(note_id="a-note", title="A note", body_markdown="SECOND the one matching note of project A")
    kinds = db.memory.search("the question", kinds="note", exclude_refs=[f"note:b{index:03d}" for index in range(450)], limit=10)
    assert [hit.source_ref for hit in kinds.hits] == ["note:a-note"]


# ── 5 (P2): a second database handle never serves an obsolete vector ──────


def test_a_warm_reader_sees_a_source_replaced_through_another_handle(tmp_path: Path) -> None:
    path = tmp_path / "p5.db"
    writer = Database(path)
    writer.notes.upsert(note_id="n9", title="Note", body_markdown="FARWORD the first wording")
    writer.notes.upsert(note_id="n2", title="Other", body_markdown="An unrelated note")
    engine = TextEngine(near=("NEARWORD",))
    rebuild(writer, engine)

    reader = Database(path)
    reader.memory.set_embedder(engine)

    def score() -> float:
        hits = {hit.source_ref: hit for hit in reader.memory.search("the question", limit=10).hits}
        return hits["note:n9"].normalized_score if "note:n9" in hits else -1.0

    before = score()  # the reader is warm: its matrix holds the first vector
    assert 0 <= before < 0.9

    # The other handle replaces the source: same chunk id, same row count,
    # and (it is the newest row of each table) the same max rowid.
    writer.notes.delete("n9")
    sweep(writer)  # the chunk and its vector leave
    writer.notes.upsert(note_id="n9", title="Note", body_markdown="NEARWORD the second wording")
    sweep(writer)
    embed_pending(writer, engine)
    with writer._connection() as conn:
        assert conn.execute("SELECT count(*) FROM memory_embeddings").fetchone()[0] == 2

    answer = reader.memory.search("the question", limit=10)
    top = answer.hits[0]
    assert top.source_ref == "note:n9" and top.normalized_score > 0.99  # the NEW vector
    assert "second wording" in top.snippet and "first wording" not in _everything(answer)
