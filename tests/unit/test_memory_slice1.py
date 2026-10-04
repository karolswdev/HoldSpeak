"""Memory slice 1 fences (docs/internal/MEMORY-DESIGN.md §1, §3.1, §5).

Each test goes through the real producers and the real sweep.  The engine is
``FixtureEmbedder`` (real-model vectors from a file) or a counting engine
that gives fixed vectors; the code under test is never doubled.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from holdspeak.db import Database
from holdspeak.inference_capabilities import builtin_capability_definitions
from holdspeak.meeting_session.models import MeetingState, TranscriptSegment
from holdspeak.memory.admission import ADMITTED_KINDS, memory_admits
from holdspeak.memory.chunker import CHUNK_CHARS, chunk_units
from holdspeak.memory.defense import REDACTED, redact
from holdspeak.memory.embedder import cut_unit
from holdspeak.memory.fusion import reciprocal_rank_fusion
from holdspeak.memory.retain import embed_pending, rebuild, sweep
from datetime import datetime

MEMORY_TABLES = ("memory_sources", "memory_chunks", "memory_embeddings")


class HashEngine:
    """A fixed vector per text.  It counts calls and can fail on a given call."""

    model_id = "hash-engine@8"
    dim = 8

    def __init__(self, fail_on_call: int | None = None) -> None:
        self.calls = 0
        self.fail_on_call = fail_on_call

    def _vector(self, text: str) -> np.ndarray:
        raw = np.frombuffer(hashlib.sha256(text.encode()).digest()[:8], dtype=np.uint8)
        return cut_unit(raw.astype(np.float32) + 1.0, 8)[0]

    def embed_documents(self, texts):
        self.calls += 1
        if self.fail_on_call is not None and self.calls == self.fail_on_call:
            raise RuntimeError("engine stopped")
        return np.vstack([self._vector(text) for text in texts])

    def embed_query(self, text):
        return self._vector(text)


def _dump(db: Database) -> str:
    """Every value of every memory table, as text."""
    out = []
    with db._connection() as conn:
        for table in MEMORY_TABLES:
            for row in conn.execute(f"SELECT * FROM {table}"):
                out.append(json.dumps([str(value) for value in tuple(row) if not isinstance(value, bytes)]))
    return "\n".join(out)


def _meeting(db: Database, meeting_id: str, lines: list[str]) -> None:
    started = datetime(2026, 9, 1, 10, 0, 0)
    db.meetings.save_meeting(
        MeetingState(
            id=meeting_id, started_at=started, ended_at=started, title=f"Meeting {meeting_id}",
            segments=[
                TranscriptSegment(text=line, speaker="Me", start_time=float(i), end_time=float(i) + 1)
                for i, line in enumerate(lines)
            ],
        )
    )


def _notes(db: Database, count: int) -> None:
    for index in range(count):
        db.notes.upsert(note_id=f"n{index:02d}", title=f"Note {index}", body_markdown=f"Body number {index} about topic {index}.")


# ── schema ───────────────────────────────────────────────────────────


def test_memory_tables_are_made_on_open_and_on_an_older_database(tmp_path: Path) -> None:
    db = Database(tmp_path / "a.db")
    with db._connection() as conn:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert set(MEMORY_TABLES) <= names
        # An older database: the tables are absent.  The reconcile adds them
        # on the next open and touches no source row.
        for table in MEMORY_TABLES:
            conn.execute(f"DROP TABLE {table}")
    db.notes.upsert(note_id="keep", title="Keep", body_markdown="A source row.")
    db.close()
    again = Database(tmp_path / "a.db")
    with again._connection() as conn:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert set(MEMORY_TABLES) <= names
        assert conn.execute("SELECT count(*) FROM notes WHERE id='keep'").fetchone()[0] == 1


def test_memory_embed_is_a_background_capability_on_every_boundary() -> None:
    capability = next(c for c in builtin_capability_definitions() if c.id == "memory.embed")
    assert (capability.group_id, capability.group_label) == ("background", "Background")
    assert capability.owner_visibility == "owner"  # assignable in Settings
    assert set(capability.allowed_boundaries) == {"local", "private_network", "mesh", "cloud"}
    assert capability.output_kind == "embedding"
    assert capability.output_schema["properties"]["vectors"]["type"] == "array"


# ── admission: one function, shared with the keyword index ───────────


def test_people_content_has_no_way_in(tmp_path: Path) -> None:
    """A People note with a unique word, then the whole pipeline: the word is
    in no memory row, no keyword row, and no search answer."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.people_service import PeopleService

    owner = Principal(PrincipalKind.OWNER, "memory-fence-owner")
    db = Database(tmp_path / "holdspeak.db")
    store = EncryptedPeopleStore(tmp_path / "people-private" / "people.v1.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    relationship = people.create_relationship(owner, {"display_name": "Zorvane Quillfeather"})
    note = people.create_note(
        owner, relationship["id"], {"topic": "Growth", "body": "PEOPLESENTINEL wants a promotion by spring."}
    )
    assert "PEOPLESENTINEL" in people.list_notes(owner, relationship["id"])[0]["body"]
    db.notes.upsert(note_id="plain", title="Plain", body_markdown="A plain desk note about spring planning.")

    engine = HashEngine()
    counts = rebuild(db, engine)
    assert counts["sources"] == 1 and counts["vectors"] == 1
    dump = _dump(db)
    assert "PEOPLESENTINEL" not in dump and "Quillfeather" not in dump
    assert note["id"] not in dump and relationship["id"] not in dump
    db.memory.set_embedder(engine)
    hits = db.memory.search("PEOPLESENTINEL promotion spring").hits
    assert [hit.source_ref for hit in hits] == ["note:plain"]
    assert all("PEOPLESENTINEL" not in hit.snippet for hit in hits)

    # The admission function has no People kind, under any name.
    for kind in ("people", "person", "people_note", "grounding_note", "relationship", "one_on_one"):
        assert kind not in ADMITTED_KINDS
        assert memory_admits(kind, {"id": note["id"], "body": "PEOPLESENTINEL"}) is False
    # The raw main database file holds none of it either.
    db.close()
    for path in tmp_path.glob("holdspeak.db*"):
        assert b"PEOPLESENTINEL" not in path.read_bytes()


def test_sensitive_parts_drafts_and_deleted_threads_never_enter(tmp_path: Path) -> None:
    db = Database(tmp_path / "t.db")
    thread = db.threads.create_thread(title="Salary talk")
    plain = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(plain.id, kind="text", text="We talked about the roadmap PLAINWORD.")
    secret = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(secret.id, kind="text", text="SENSITIVEWORD salary figure", sensitive=True)
    draft = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(draft.id, kind="text", text="DRAFTWORD not sent yet", draft=True)
    only_sensitive = db.threads.create_thread(title="Private")
    message = db.threads.append_message(only_sensitive.id, role="user")
    db.threads.append_part(message.id, kind="text", text="ONLYSENSITIVE content", sensitive=True)

    rebuild(db, HashEngine())
    dump = _dump(db)
    assert "PLAINWORD" in dump
    for word in ("SENSITIVEWORD", "DRAFTWORD", "ONLYSENSITIVE"):
        assert word not in dump
    assert f"thread:{only_sensitive.id}" not in dump

    # The thread is deleted: the next sweep removes what was derived from it.
    assert db.threads.soft_delete(thread.id)
    stats = sweep(db)
    assert stats["gone"] == 1
    assert "PLAINWORD" not in _dump(db).replace('"gone"', "")
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM memory_chunks").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM memory_embeddings").fetchone()[0] == 0
        assert conn.execute(
            "SELECT state FROM memory_sources WHERE source_ref=?", (f"thread:{thread.id}",)
        ).fetchone()[0] == "gone"


def test_a_parked_meeting_leaves_memory_and_comes_back_on_restore(tmp_path: Path) -> None:
    db = Database(tmp_path / "m.db")
    _meeting(db, "m1", ["The PARKEDWORD budget is approved."])
    _meeting(db, "m2", ["Lunch is at noon."])
    engine = HashEngine()
    rebuild(db, engine)
    db.memory.set_embedder(engine)
    assert "PARKEDWORD" in _dump(db)

    db.meetings.delete_meeting("m1")  # the product parks; it never deletes
    # Before the next sweep the chunk is still there; recall must not use it.
    refs = {hit.source_ref for hit in db.memory.search("budget approved").hits}
    assert "meeting:m1" not in refs
    sweep(db)
    assert "PARKEDWORD" not in _dump(db)
    assert db.memory_index.stats()["vectors"] == 1

    db.meetings.restore_meeting("m1")
    sweep(db)
    embed_pending(db, engine)
    assert "PARKEDWORD" in _dump(db)
    assert "meeting:m1" in {hit.source_ref for hit in db.memory.search("PARKEDWORD budget").hits}


def test_promoted_and_deleted_notes_never_enter_either_index(tmp_path: Path) -> None:
    db = Database(tmp_path / "n.db")
    db.notes.upsert(note_id="kept", title="Kept", body_markdown="KEPTWORD stays.")
    db.notes.upsert(note_id="promoted", title="Promoted", body_markdown="PROMOTEDWORD is context.")
    db.notes.upsert(note_id="deleted", title="Deleted", body_markdown="DELETEDWORD is gone.")
    db.notes.delete("deleted")
    with db._connection() as conn:
        # The promotion row, every column named (the interview service writes it).
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
    engine = HashEngine()
    counts = rebuild(db, engine)
    dump = _dump(db)
    assert "KEPTWORD" in dump
    assert "PROMOTEDWORD" not in dump and "DELETEDWORD" not in dump
    # The keyword index was rebuilt by the same admission function.
    assert counts["keyword_rows"] == 1
    with db._connection() as conn:
        assert [row[0] for row in conn.execute("SELECT source_id FROM notes_memory_fts")] == ["kept"]
    db.memory.set_embedder(engine)
    assert {hit.source_ref for hit in db.memory.search("PROMOTEDWORD DELETEDWORD KEPTWORD").hits} == {"note:kept"}


def test_admission_rules_one_by_one() -> None:
    assert memory_admits("note", {"deleted": 0})
    assert not memory_admits("note", {"deleted": 1})
    assert not memory_admits("note", {"deleted": 0, "promoted": True})
    assert memory_admits("meeting", {"parked": 0})
    assert not memory_admits("meeting", {"parked": 1})
    assert memory_admits("decision", {"deleted": 0, "source_state": "linked"})
    assert not memory_admits("decision", {"deleted": 0, "source_state": "source_deleted"})
    assert memory_admits("thread_part", {"sensitive": 0, "draft": 0, "part_kind": "text"})
    assert not memory_admits("thread_part", {"sensitive": 1, "draft": 0, "part_kind": "text"})
    assert not memory_admits("thread_part", {"sensitive": 0, "draft": 1, "part_kind": "text"})
    assert not memory_admits("thread_part", {"sensitive": 0, "draft": 0, "part_kind": "reasoning"})
    assert not memory_admits("thread_part", {"message_deleted_at": 12.0, "part_kind": "text"})
    assert not memory_admits("workbench_item", {"status": "dismissed"})
    assert not memory_admits("cadence", {"status": "killed"})
    assert not memory_admits("", {}) and not memory_admits("unknown_kind", {"deleted": 0})


# ── secrets ──────────────────────────────────────────────────────────


def test_a_secret_is_redacted_before_it_is_stored_or_embedded(tmp_path: Path) -> None:
    db = Database(tmp_path / "s.db")
    db.notes.upsert(
        note_id="s1", title="Deploy notes",
        body_markdown="Use token=hunter2SECRETVALUE for the staging API. The key is ghp_abcdefghijklmnopqrstuvwxyz0123.",
    )

    seen: list[str] = []

    class Spy(HashEngine):
        def embed_documents(self, texts):
            seen.extend(texts)
            return super().embed_documents(texts)

    rebuild(db, Spy())
    dump = _dump(db)
    assert "hunter2SECRETVALUE" not in dump and "ghp_abcdefghijklmnop" not in dump
    assert REDACTED in dump
    assert seen and all("hunter2SECRETVALUE" not in text and "ghp_" not in text for text in seen)


@pytest.mark.parametrize(
    "secret",
    [
        "Bearer abcdef123456",
        "api_key=sk_live_1234567890",
        "password: correct-horse",
        "ghp_abcdefghijklmnopqrstuvwxyz0123",
        "xoxb-1234567890-abcdefghij",
        "postgres://admin:s3cretpass@db.internal:5432/ledger",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----",
        "4111 1111 1111 1111",
    ],
)
def test_defense_redacts_each_secret_shape(secret: str) -> None:
    text = redact(f"before {secret} after")
    assert REDACTED in text
    assert text.startswith("before ") and text.endswith(" after")
    for piece in ("s3cretpass", "MIIEowIBAAKCAQEA", "1111 1111", "abcdef123456", "correct-horse"):
        assert piece not in text


def test_defense_keeps_plain_text_and_numbers_that_are_not_cards() -> None:
    plain = "The cutover is on 2026-11-03 and costs 1234 5678 9012 3456 euros for 400 seats."
    assert redact(plain) == plain  # the 16 digits fail the Luhn check
    assert redact("") == ""


# ── idempotent, resumable, crash-safe ────────────────────────────────


def test_a_second_run_writes_nothing_and_calls_no_engine(tmp_path: Path) -> None:
    db = Database(tmp_path / "i.db")
    _notes(db, 6)
    engine = HashEngine()
    first = sweep(db)
    assert first["written"] == 6 and first["complete"] == 1
    assert embed_pending(db, engine) == 6
    before = _dump(db)
    calls = engine.calls

    second = sweep(db)
    assert second == {"seen": 6, "written": 0, "unchanged": 6, "gone": 0, "scrubbed": 0, "complete": 1}
    assert embed_pending(db, engine) == 0
    assert engine.calls == calls
    assert _dump(db) == before

    # One source changes: only that source is written and embedded again.
    db.notes.upsert(note_id="n03", title="Note 3", body_markdown="A new body for note three.")
    third = sweep(db)
    assert third["written"] == 1 and third["unchanged"] == 5
    assert embed_pending(db, engine) == 1


def test_a_sweep_that_stops_half_way_resumes_and_completes(tmp_path: Path) -> None:
    db = Database(tmp_path / "c.db")
    _notes(db, 9)
    whole = Database(tmp_path / "whole.db")
    _notes(whole, 9)
    sweep(whole)

    partial = sweep(db, max_sources=4)  # the process died after four sources
    assert partial["written"] == 4 and partial["complete"] == 0
    with db._connection() as conn:
        done = [row[0] for row in conn.execute("SELECT source_ref FROM memory_sources ORDER BY 1")]
        assert len(done) == 4
        # Each finished source is whole: ledger row and chunks together.
        for ref in done:
            assert conn.execute("SELECT count(*) FROM memory_chunks WHERE source_ref=?", (ref,)).fetchone()[0] >= 1
        assert conn.execute("SELECT count(*) FROM memory_chunks").fetchone()[0] == 4
    half = _chunks(db)

    resumed = sweep(db)
    assert resumed["written"] == 5 and resumed["unchanged"] == 4 and resumed["complete"] == 1
    full = _chunks(db)
    assert full == _chunks(whole)  # the same index as a sweep that never stopped
    assert {key: full[key] for key in half} == half  # finished rows did not change


def _chunks(db: Database) -> dict[str, tuple]:
    with db._connection() as conn:
        return {
            row["id"]: (row["source_ref"], row["ordinal"], row["text"], row["content_sha"])
            for row in conn.execute("SELECT * FROM memory_chunks")
        }


def test_an_engine_that_dies_mid_run_never_changes_recall_for_finished_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "e.db")
    _notes(db, 10)
    sweep(db)

    dying = HashEngine(fail_on_call=3)
    with pytest.raises(RuntimeError):
        embed_pending(db, dying, batch_size=4)
    # Two batches committed; the third wrote nothing.
    assert db.memory_index.stats()["vectors"] == 8

    engine = HashEngine()
    db.memory.set_embedder(engine)
    question = "Body number 9 about topic 9."

    def vector_scores() -> dict[str, float]:
        result = db.memory.search(question, limit=50)
        return {hit.source_ref: hit.normalized_score for hit in result.hits if hit.retrieval_origin == "vector"}

    def all_vector_rows() -> dict[str, float]:
        rows = db.memory._vector_rows(
            question, engine, selected=("note",), project=None, start=None, end=None, excluded=set()
        )
        return {row["source_ref"]: row["normalized_score"] for row in rows}

    half = all_vector_rows()
    assert len(half) == 8
    assert embed_pending(db, engine, batch_size=4) == 2  # the re-run completes
    full = all_vector_rows()
    assert len(full) == 10
    assert {ref: full[ref] for ref in half} == half  # finished rows: same score
    assert vector_scores() is not None

    # A changed chunk: its old vector is not used, and no stale row answers.
    db.notes.upsert(note_id="n00", title="Note 0", body_markdown="Entirely different words now.")
    sweep(db)
    assert "note:n00" not in all_vector_rows()
    assert embed_pending(db, engine) == 1
    assert "note:n00" in all_vector_rows()
    assert db.memory_index.stats()["vectors"] == db.memory_index.stats()["chunks"] == 10


def test_a_vector_for_a_chunk_that_changed_during_the_engine_call_is_dropped(tmp_path: Path) -> None:
    db = Database(tmp_path / "r.db")
    _notes(db, 2)
    sweep(db)

    class Racing(HashEngine):
        def embed_documents(self, texts):
            vectors = super().embed_documents(texts)
            db.notes.upsert(note_id="n00", title="Note 0", body_markdown="Changed while the engine ran.")
            sweep(db)
            return vectors

    engine = Racing()
    assert embed_pending(db, engine, max_batches=1) == 1  # only the unchanged chunk landed
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT e.item_id FROM memory_embeddings e JOIN memory_chunks c"
            " ON c.id=e.item_id AND c.content_sha=e.content_sha"
        ).fetchall()
        assert [row[0] for row in rows] == ["note:n01#0"]


def test_rebuild_command_drops_and_builds_the_index(tmp_path: Path, monkeypatch, capsys) -> None:
    import holdspeak.db as hsdb
    from holdspeak import main as hs_main

    db = Database(tmp_path / "cli.db")
    _notes(db, 3)
    sweep(db)
    with db._connection() as conn:
        conn.execute("UPDATE memory_chunks SET text='corrupt'")
        conn.execute("DELETE FROM notes_memory_fts")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr("sys.argv", ["holdspeak", "memory", "rebuild"])
    hs_main.main()
    out = capsys.readouterr().out
    assert "Memory rebuilt:" in out and "sources=3" in out and "chunks=3" in out
    assert "corrupt" not in _dump(db)
    assert len(db.memory.search("topic").hits) == 3


# ── the small parts ──────────────────────────────────────────────────


def test_chunker_cuts_on_units_and_keeps_the_title_in_front() -> None:
    short = chunk_units("Offsite", [("", "The team meets in Lisbon.")])
    assert [(c.ordinal, c.text) for c in short] == [(0, "Offsite\nThe team meets in Lisbon.")]

    turns = [(str(i), f"Speaker {i}: " + "word " * 60) for i in range(12)]
    chunks = chunk_units("Weekly sync", turns)
    assert len(chunks) > 1
    assert all(len(c.text) <= CHUNK_CHARS for c in chunks)
    assert all(c.text.startswith("Weekly sync\n") for c in chunks)
    assert chunks[0].anchor == "0" and int(chunks[1].anchor) > 0  # anchor = first turn of the chunk
    body = " ".join(c.text.split("\n", 1)[1] for c in chunks)
    assert all(f"Speaker {i}:" in body for i in range(12))  # nothing lost

    long_unit = chunk_units("", [("a", "Sentence one is here. " * 200)])
    assert len(long_unit) > 3 and all(len(c.text) <= CHUNK_CHARS for c in long_unit)
    assert chunk_units("", []) == [] and chunk_units("", [("", "   ")]) == []
    assert [c.text for c in chunk_units("Only a title", [])] == ["Only a title"]


def test_reciprocal_rank_fusion_k_60() -> None:
    fused = reciprocal_rank_fusion({"keyword": ["a", "b", "c"], "vector": ["c", "a", "d"], "relation": []})
    scores = {key: score for key, score, _ in fused}
    assert scores["a"] == pytest.approx(1 / 61 + 1 / 62)
    assert scores["c"] == pytest.approx(1 / 63 + 1 / 61)
    assert scores["b"] == pytest.approx(1 / 62) and scores["d"] == pytest.approx(1 / 63)
    assert [key for key, _, _ in fused] == ["a", "c", "b", "d"]
    assert dict((key, found) for key, _, found in fused)["a"] == ("keyword", "vector")
    # A key twice in one list counts once, at its best rank.
    twice = reciprocal_rank_fusion({"keyword": ["a", "a", "b"]})
    assert [(key, score) for key, score, _ in twice] == [("a", pytest.approx(1 / 61)), ("b", pytest.approx(1 / 62))]


def test_cut_unit_cuts_and_renormalises() -> None:
    vectors = np.arange(1, 13, dtype=np.float32).reshape(2, 6)
    cut = cut_unit(vectors, 4)
    assert cut.shape == (2, 4) and cut.dtype == np.float32
    assert np.allclose(np.linalg.norm(cut, axis=1), 1.0)
    assert np.allclose(cut[0], vectors[0, :4] / np.linalg.norm(vectors[0, :4]))
    with pytest.raises(ValueError):
        cut_unit(vectors, 7)
