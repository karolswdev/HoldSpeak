"""Memory slice 2: the new source kinds and ``memory_chunks_fts``
(docs/internal/MEMORY-DESIGN.md §3.1, §3.2, §5, §8 row 2).

The kinds: the Brief's items, dictation, steward runs, Room ask answers; and
the meeting summary and each topic as chunks of their own.  Keyword search
over a new kind reads ``memory_chunks_fts`` and works with NO embedding
engine (the owner's path today).

Every row is made by its real producer on an isolated HOME: the Brief route,
the People routes, the dictation journal recorder, the steward's
``run_once``, the Room ask routes with the hub's real ``/api/ask``.
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot  # noqa: E402

from holdspeak.memory.retain import rebuild, refs_for_change, sweep  # noqa: E402
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment  # noqa: E402
from holdspeak.principals import Principal, PrincipalKind  # noqa: E402
from holdspeak.runtime import composition  # noqa: E402
from holdspeak.services.memory_grounding import memory_context  # noqa: E402
from tests.integration.test_phase200_task_resume import rig as ask_rig  # noqa: E402,F401

OWNER = Principal(PrincipalKind.OWNER, "memory-slice2")


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    monkeypatch.setenv("HOME", str(tmp_path))
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text
    return response.json()


def _refs(db: Any, query: str, **scope: Any) -> list[str]:
    return [hit.source_ref for hit in db.memory.search(query, **scope).hits]


def _memory_text(db: Any) -> str:
    """Every text a memory table holds: the ledger, the chunks, the chunk FTS."""
    with db._connection() as conn:
        parts = [str(r[0]) for r in conn.execute("SELECT title FROM memory_sources")]
        parts += [str(r[0]) for r in conn.execute("SELECT text FROM memory_chunks")]
        parts += [str(r[0]) for r in conn.execute("SELECT text FROM memory_chunks_fts")]
    return "\n".join(parts)


def _fts_in_step(db: Any) -> None:
    """Every chunk has exactly its one keyword row, and no other row exists."""
    with db._connection() as conn:
        chunks = conn.execute("SELECT rowid,id,source_ref,text FROM memory_chunks ORDER BY rowid").fetchall()
        rows = conn.execute(
            "SELECT rowid,chunk_id,source_ref,text FROM memory_chunks_fts ORDER BY rowid"
        ).fetchall()
    assert [tuple(r) for r in chunks] == [tuple(r) for r in rows]


# ── R2: a word only in the summary ──────────────────────────────────────


def _meeting(hub: Hub) -> None:
    hub.db.meetings.save_meeting(MeetingState(
        id="m-kestrel",
        started_at=datetime(2026, 10, 1, 9, 0, 0),
        title="Ledger sync",
        segments=[TranscriptSegment(text="We looked at the kestrel dashboards.", speaker="Avery",
                                    start_time=1.0, end_time=2.0)],
        intel=IntelSnapshot(timestamp=3.0, topics=["Obsidianware licence", "Pellucid rollout"],
                            summary="Team agreed the zephyrine migration plan."),
    ))


def test_r2_a_word_only_in_the_summary_is_found_by_search_and_memory_context(hub: Hub) -> None:
    _meeting(hub)
    assert hub.db.memory.embedder is None  # no engine: the keyword path
    found = hub.db.memory.search("zephyrine")
    assert [hit.source_ref for hit in found.hits] == ["meeting:m-kestrel"]
    assert found.hits[0].retrieval_origin == "lexical"
    memory = memory_context(hub.db, query="zephyrine")
    assert [excerpt.ref for excerpt in memory.excerpts] == ["meeting:m-kestrel"]
    assert memory.excerpts[0].citable

    sweep(hub.db)
    with hub.db._connection() as conn:
        held = "\n".join(str(r[0]) for r in conn.execute(
            "SELECT text FROM memory_chunks WHERE source_ref='meeting:m-kestrel'"))
    assert "zephyrine" in held and "Pellucid rollout" in held
    _fts_in_step(hub.db)


# ── the Brief's items, and the People fence ─────────────────────────────


def _people_commitment(hub: Hub, word: str) -> str:
    _ok(hub.client.post("/api/people/setup"))
    relationship = _ok(hub.client.post(
        "/api/people/relationships", json={"display_name": "Dana"}), 201)["relationship"]
    request = _ok(hub.client.post(
        f"/api/people/relationships/{relationship['id']}/requests",
        json={"body": f"Review the {word} promotion case"}), 201)["request"]
    commitment = _ok(hub.client.post(f"/api/people/requests/{request['id']}/accept", json={}))["commitment"]
    return str(commitment["id"])


def test_a_brief_item_is_found_with_no_engine_and_its_1_1_row_is_never_memory(hub: Hub) -> None:
    is_error, action = hub.mcp("door.add_item", {
        "task": "Sign the tamarack contract", "owner": "Me", "due": date.today().isoformat(),
    })
    assert not is_error, action
    _people_commitment(hub, "gravelin")
    brief = _ok(hub.client.post("/api/brief/generate"))
    brief = brief.get("brief") or brief

    with hub.db._connection() as conn:
        items = [dict(r) for r in conn.execute(
            "SELECT id,text,source_ref FROM monday_brief_items WHERE brief_id=?", (brief["id"],))]
    tamarack = next(item for item in items if "tamarack" in item["text"])
    people_rows = [item for item in items if "people_commitment:" in str(item["source_ref"])]
    assert people_rows, items  # the Brief holds the 1:1 row (as "1:1 commitment")

    stats = sweep(hub.db)
    assert stats["complete"] == 1
    assert hub.db.memory.embedder is None
    hits = hub.db.memory.search("tamarack", kinds="brief_item").hits
    assert [hit.source_ref for hit in hits] == [f"brief_item:{tamarack['id']}"]
    assert hits[0].retrieval_origin == "lexical" and hits[0].title.startswith("Brief ")
    assert "<mark>tamarack</mark>" in hits[0].snippet.casefold()
    # Plain context for a drafter: no window opens one Brief item.
    memory = memory_context(hub.db, query="tamarack contract")
    brief_lines = [e for e in memory.excerpts if e.kind == "brief_item"]
    assert brief_lines and not brief_lines[0].citable
    # A Brief item belongs to no Project.
    pid = _ok(hub.client.post("/api/projects", json={"name": "Atlas"}))["project"]["id"]
    assert _refs(hub.db, "tamarack", kinds="brief_item", project_id=pid) == []

    # People custody: the 1:1 row is not a source, and no People word is held.
    with hub.db._connection() as conn:
        held = {str(r[0]) for r in conn.execute("SELECT source_ref FROM memory_sources")}
    for row in people_rows:
        assert f"brief_item:{row['id']}" not in held
    assert "gravelin" not in _memory_text(hub.db).casefold()
    assert _refs(hub.db, "gravelin") == []
    assert _refs(hub.db, "commitment", kinds="brief_item") == []
    _fts_in_step(hub.db)


def test_prep_and_dictation_that_name_a_person_hold_no_people_store_field(hub: Hub) -> None:
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder, passthrough_run

    _people_commitment(hub, "gravelin")
    pid = _ok(hub.client.post("/api/projects", json={"name": "Atlas"}))["project"]["id"]
    _ok(hub.client.post(f"/api/projects/{pid}/briefs/prepare",
                        json={"purpose": "Dana 1:1 vellichor review", "generator": "deterministic"}))
    said = "Ask Dana about the vellichor review"
    DictationJournalRecorder(hub.db.dictation_journal).record(
        passthrough_run(said), source="dictation", transcript=said)

    sweep(hub.db)
    assert _refs(hub.db, "vellichor", kinds="prep_brief") and _refs(hub.db, "vellichor", kinds="dictation")
    held = _memory_text(hub.db)
    assert "Dana" in held                       # his own words name her
    assert "gravelin" not in held.casefold()    # the People store's words never
    assert _refs(hub.db, "gravelin") == []


# ── dictation ───────────────────────────────────────────────────────────


def test_a_dictation_is_found_a_dry_run_is_not_and_a_deleted_entry_leaves(hub: Hub) -> None:
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder, passthrough_run

    recorder = DictationJournalRecorder(hub.db.dictation_journal)
    said = "Move the marrowind rollout to Thursday"
    entry = recorder.record(passthrough_run(said), source="dictation", transcript=said)
    test = "the quarnelle pipeline test"
    recorder.record(passthrough_run(test), source="dry_run", transcript=test)

    sweep(hub.db)
    hits = hub.db.memory.search("marrowind").hits
    assert [hit.source_ref for hit in hits] == [f"dictation:{entry.id}"]
    assert hits[0].title == "Dictation" and "marrowind" in hits[0].snippet
    assert _refs(hub.db, "quarnelle") == []
    assert "quarnelle" not in _memory_text(hub.db)
    # No Project holds a dictation.
    pid = _ok(hub.client.post("/api/projects", json={"name": "Atlas"}))["project"]["id"]
    assert _refs(hub.db, "marrowind", project_id=pid) == []

    # Deleted: gone from recall at once (read time), then from the index.
    assert hub.db.dictation_journal.delete(entry.id)
    assert _refs(hub.db, "marrowind") == []
    assert sweep(hub.db)["gone"] == 1
    assert "marrowind" not in _memory_text(hub.db)
    _fts_in_step(hub.db)


# ── steward runs ────────────────────────────────────────────────────────


def test_a_finished_steward_run_is_found_in_its_project_and_a_queued_one_is_not(hub: Hub) -> None:
    pid = _ok(hub.client.post("/api/projects", json={"name": "Halcyonite"}))["project"]["id"]
    run_id = hub.root.project_steward_service.run_once(OWNER, pid)
    assert hub.db.steward_runs.get_run(run_id)["state"] == "completed"
    other = _ok(hub.client.post("/api/projects", json={"name": "Halcyonite two"}))["project"]["id"]
    hub.db.steward_runs.insert_run(run_id="run-queued", project_id=other)

    sweep(hub.db)
    with hub.db._connection() as conn:
        text = conn.execute(
            "SELECT text FROM memory_chunks WHERE source_ref=?", (f"steward_run:{run_id}",)
        ).fetchone()[0]
    assert "Outcome: completed" in text and "{" not in text  # words, not the JSON
    assert _refs(hub.db, "halcyonite", kinds="steward_run") == [f"steward_run:{run_id}"]
    assert _refs(hub.db, "halcyonite", kinds="steward_run", project_id=pid) == [f"steward_run:{run_id}"]
    assert _refs(hub.db, "halcyonite", kinds="steward_run", project_id=other) == []
    hit = hub.db.memory.search("halcyonite", kinds="steward_run").hits[0]
    assert hit.project_id == pid
    assert refs_for_change("steward", run_id) == [f"steward_run:{run_id}"]
    _fts_in_step(hub.db)


# ── Room ask answers ────────────────────────────────────────────────────


def test_a_room_ask_answer_is_memory_until_he_discards_it(ask_rig) -> None:  # noqa: F811
    db, client, engine, _path = ask_rig
    engine.answer = "Add two ostrakite nodes before the freeze."
    pid = _ok(client.post("/api/projects", json={"name": "Capacity"}))["project"]["id"]
    task = _ok(client.post(f"/api/projects/{pid}/ask-tasks",
                           json={"purpose": "How many nodes for brennick?", "lens": "Project"}), 201)["task"]
    resumed = _ok(client.post(f"/api/ask-tasks/{task['id']}/resume"))
    assert resumed["task"]["state"] == "accepted"
    # A desk Ask keeps no question and is unkept output: not memory.
    engine.answer = "The solvayne answer."
    _ok(client.post("/api/ask", json={"prompt": "Anything about solvayne?", "lens": "Ask"}))

    sweep(db)
    ref = f"ask_answer:{task['id']}"
    hits = db.memory.search("ostrakite").hits
    assert [hit.source_ref for hit in hits] == [ref]
    assert hits[0].title == "How many nodes for brennick?" and hits[0].project_id == pid
    assert _refs(db, "brennick", kinds="ask_answer", project_id=pid) == [ref]
    assert _refs(db, "solvayne") == []
    memory = memory_context(db, project_id=pid, query="ostrakite nodes")
    assert [e.ref for e in memory.excerpts if e.kind == "ask_answer"] == [ref]
    assert refs_for_change("ask_task", task["id"]) == [ref]

    _ok(client.post(f"/api/ask-tasks/{task['id']}/discard"))
    assert _refs(db, "ostrakite") == []  # at once, before any sweep
    assert sweep(db)["gone"] == 1
    assert "ostrakite" not in _memory_text(db)
    _fts_in_step(db)


# ── laws: rebuildable; the index and the FTS stay in step ───────────────


def test_rebuild_gives_the_same_hits_for_the_new_kinds(hub: Hub) -> None:
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder, passthrough_run

    _meeting(hub)
    said = "The marrowind review is on Friday"
    DictationJournalRecorder(hub.db.dictation_journal).record(
        passthrough_run(said), source="dictation", transcript=said)
    pid = _ok(hub.client.post("/api/projects", json={"name": "Halcyonite"}))["project"]["id"]
    hub.root.project_steward_service.run_once(OWNER, pid)
    sweep(hub.db)

    def answers() -> list[list[tuple[str, str]]]:
        return [
            [(hit.source_ref, hit.snippet) for hit in hub.db.memory.search(query).hits]
            for query in ("marrowind", "halcyonite", "zephyrine", "pellucid")
        ]

    before = answers()
    assert all(before), before
    rebuild(hub.db)
    assert answers() == before
    _fts_in_step(hub.db)


def test_an_existing_database_gets_the_table_and_the_next_sweep_fills_it(tmp_path: Path) -> None:
    """The owner's database: chunks from chunker 1, no ``memory_chunks_fts``.
    The reconcile creates the table; the version bump makes the next sweep
    cut every source again, which writes its keyword rows."""
    from holdspeak.db import Database, reset_database
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder, passthrough_run

    reset_database()
    path = tmp_path / "old.db"
    db = Database(path)
    said = "The marrowind review is on Friday"
    DictationJournalRecorder(db.dictation_journal).record(
        passthrough_run(said), source="dictation", transcript=said)
    sweep(db)
    with db._connection() as conn:
        conn.execute("DROP TABLE memory_chunks_fts")
        conn.execute("UPDATE memory_sources SET chunker_version=1")
    db.close()

    db = Database(path)  # the reconcile runs on open
    try:
        assert _refs(db, "marrowind") == []  # the table is there, still empty
        assert sweep(db)["written"] == 1
        assert [ref.partition(":")[0] for ref in _refs(db, "marrowind")] == ["dictation"]
        _fts_in_step(db)
    finally:
        db.close()
        reset_database()


# ── Astra's review of #832 ──────────────────────────────────────────────


def test_p1_the_version_bump_keeps_every_vector_and_recall_has_no_gap(tmp_path: Path) -> None:
    """A desk indexed and embedded under chunker 1 (no keyword table rows).
    Under chunker 2 a question with no keyword match still finds the meeting
    by its vector: before the sweep, after the sweep, and with an engine that
    fails every embed call.  The bump writes the same chunks, so no vector
    is dropped and nothing waits to be embedded."""
    from holdspeak.db import Database, reset_database
    from holdspeak.memory.retain import MemorySource, embed_pending, prepare
    from test_memory_slice1 import HashEngine

    reset_database()
    db = Database(tmp_path / "v1.db")
    try:
        db.meetings.save_meeting(MeetingState(
            id="short", started_at=datetime(2026, 10, 1, 9, 0, 0), title="Short",
            segments=[TranscriptSegment(text="We looked at the kestrel dashboards.",
                                        speaker="Avery", start_time=1.0, end_time=2.0)],
            intel=IntelSnapshot(timestamp=3.0, topics=["Obsidianware licence"],
                                summary="Team agreed the zephyrine migration plan."),
        ))
        with db._connection() as conn:
            seg_id = conn.execute("SELECT id FROM segments WHERE meeting_id='short'").fetchone()[0]
            started = conn.execute("SELECT started_at FROM meetings WHERE id='short'").fetchone()[0]
        assert started == "2026-10-01T09:00:00"
        engine = HashEngine()
        # The index exactly as chunker 1 (main before this PR) wrote it: its
        # meeting units, packed, version 1, and no keyword table rows.
        v1 = MemorySource(
            "meeting:short", "meeting", "Short", "2026-10-01T09:00:00",
            [
                (str(seg_id), "Avery: We looked at the kestrel dashboards."),
                ("summary", "Summary: Team agreed the zephyrine migration plan."),
                ("topics", "Topics: Obsidianware licence"),
            ],
        )
        content_sha, chunks = prepare(v1)
        db.memory_index.replace_source(
            source_ref=v1.ref, kind=v1.kind, title=v1.title, occurred_at=v1.occurred_at,
            content_sha=content_sha, chunker_version=1, chunks=chunks,
        )
        assert embed_pending(db, engine) > 0
        with db._connection() as conn:
            conn.execute("DELETE FROM memory_chunks_fts")
            vectors = conn.execute(
                "SELECT item_id,content_sha,vector FROM memory_embeddings ORDER BY item_id").fetchall()
        db.memory.set_embedder(engine)

        def vector_refs() -> list[str]:
            found = db.memory.search("a question with other words").hits
            return [hit.source_ref for hit in found if hit.retrieval_origin == "vector"]

        assert vector_refs() == ["meeting:short"]           # before the sweep
        assert sweep(db)["written"] == 1                      # the bump re-wrote it
        assert vector_refs() == ["meeting:short"]           # after, before any embed
        assert db.memory_index.pending_count(engine.model_id) == 0
        with db._connection() as conn:
            assert conn.execute(
                "SELECT item_id,content_sha,vector FROM memory_embeddings ORDER BY item_id"
            ).fetchall() == vectors
        failing = HashEngine(fail_on_call=1)
        assert embed_pending(db, failing) == 0 and failing.calls == 0
        assert vector_refs() == ["meeting:short"]           # an engine failure changes nothing
        assert _refs(db, "zephyrine") == ["meeting:short"]
        _fts_in_step(db)
    finally:
        db.close()
        reset_database()


def test_p2_an_edited_dictation_is_not_found_by_its_old_words(hub: Hub) -> None:
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder

    from types import SimpleNamespace

    run = SimpleNamespace(final_text="", stage_results=[], total_elapsed_ms=0.0, warnings=[], intent=None)
    entry = DictationJournalRecorder(hub.db.dictation_journal).record(
        run, source="dictation", transcript="The vellichor launch is Friday")
    sweep(hub.db)
    assert _refs(hub.db, "vellichor") == [f"dictation:{entry.id}"]

    assert hub.db.dictation_journal.update_transcript(entry.id, "The tamarack launch is Monday")
    assert _refs(hub.db, "vellichor") == []  # at once, before any sweep
    sweep(hub.db)
    hits = hub.db.memory.search("tamarack").hits
    assert [hit.source_ref for hit in hits] == [f"dictation:{entry.id}"]
    assert "tamarack" in hits[0].snippet and "vellichor" not in hits[0].snippet


def test_p3_equal_time_ranges_give_equal_answers(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    """The journal stores the hub's local wall time (``datetime.now()``).
    In Denver 09:00 local is 15:00Z; both spellings of the range find it."""
    import time
    from datetime import datetime as real_datetime

    from holdspeak.db import journal as journal_module
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder, passthrough_run

    monkeypatch.setenv("TZ", "America/Denver")
    time.tzset()
    try:
        class Fixed(real_datetime):
            @classmethod
            def now(cls, tz=None):
                return real_datetime(2026, 10, 4, 9, 0, 0)

        monkeypatch.setattr(journal_module, "datetime", Fixed)
        said = "The quorvane cutover is done"
        entry = DictationJournalRecorder(hub.db.dictation_journal).record(
            passthrough_run(said), source="dictation", transcript=said)
        monkeypatch.setattr(journal_module, "datetime", real_datetime)
        sweep(hub.db)
        ref = f"dictation:{entry.id}"

        def within(start: str, end: str) -> list[str]:
            return _refs(hub.db, "quorvane", time_from=start, time_to=end)

        assert within("2026-10-04T14:30:00+00:00", "2026-10-04T15:30:00+00:00") == [ref]
        assert within("2026-10-04T08:30:00-06:00", "2026-10-04T09:30:00-06:00") == [ref]
        assert within("2026-10-04T08:30:00", "2026-10-04T09:30:00") == [ref]  # local wall time
        assert within("2026-10-04T16:00:00+00:00", "2026-10-04T17:00:00+00:00") == []
        assert within("2026-10-04T09:30:00-06:00", "2026-10-04T10:30:00-06:00") == []
    finally:
        monkeypatch.delenv("TZ", raising=False)
        time.tzset()
