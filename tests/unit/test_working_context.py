"""HS-200-10 Lane A: the boundary around a promoted canonical record.

Ruling C2' -- **reachable by reference, never by relevance**.  A promoted
canonical record does not enter the relevance pool; it is reached by an
explicit ref (the context picker, an attach, a `Carry into brief`) and never
by a relevance search.

The lesson this phase paid for: **a test that cannot fail on the real path is
not proof.**  The first draft of this design shipped its best test asserting
over the ATTACHMENT envelope while the leak arrived through a different one --
it would have gone green while the boundary was open.  So every test here

  (a) carries a POSITIVE CONTROL that IS returned, so the test fails the
      moment the fence is deleted or over-reaches, and
  (b) drives the REAL entry point -- `hydrate_refs_detailed` on the
      *unattached* shape `ask_service.py` uses, or `MemoryRepository.search` --
      never a helper picked for convenience.

The four layers under test (settled design D2.4):

  L1  corpus exclusion by construction -- the guarded `notes_memory_ai` /
      `notes_memory_au` triggers and the guarded `rebuild_memory_index`
  L2  the GRAPH route fence -- promoted refs unioned into `excluded` inside
      `MemoryRepository.search`, because `_load_related_row`'s `note` branch
      reads `FROM notes` directly and never touches the corpus at all
  L3  the belt at grounding's two relevance CALL SITES (never inside the
      shared `_hydrate_members`)

L4 (the frozen-ref replay) lives in `thread_service.py`, which this lane does
not own; the sync fence (P0-C) lives in `sync_service.py`, likewise.  Both are
declared unbuilt-here in the lane report.

The promotion VERB itself is Lane B's.  Where a test needs a promotion to
exist, it writes the `context_promotions` row directly, in the order the verb
must use (row FIRST, note SECOND -- that ordering is what makes L1
construction rather than filtering).  Lane B's integration test covers the
real path.
"""

from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.db.memory import rebuild_memory_index
from holdspeak.grounding import hydrate_refs_detailed


# The Tuesday sentence from D0, plus a token that appears in NOTHING else, so
# an assertion can look at the actual bytes rather than at a ref list.
CONSTRAINT = (
    "We cannot take another cutover without a rollback rehearsal. "
    "That is not negotiable."
)
PROMOTED_TOKEN = "kestrelmark"
CONTROL_TOKEN = "wrenmark"
QUERY = "cutover rollback rehearsal"


def _insert_promotion(
    db: Database,
    target_ref: str,
    *,
    thread_id: str = "thread-interview",
    fact_id: str = "fact-1",
    disclosure_state: str = "active",
    conn: sqlite3.Connection | None = None,
) -> None:
    """Write one `context_promotions` row, every column named.

    Lane B owns the verb that writes this for real (`InterviewService`).
    """
    sql = """INSERT INTO context_promotions(
                 promotion_id, thread_id, fact_id, source_message_id,
                 quote_sha256, quote_locator_json, target_kind, target_ref,
                 target_revision_label, target_content_sha256,
                 disclosure_state, request_sha256, created_at, updated_at)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    params = (
        f"cp_{thread_id}_{fact_id}",
        thread_id,
        fact_id,
        "msg-1",
        "sha256:quote",
        '{"part_ordinal": 0}',
        "note",
        target_ref,
        "2026-09-07T09:00:00Z",
        "sha256:content",
        disclosure_state,
        "sha256:request",
        "2026-09-07T09:00:00Z",
        "2026-09-07T09:00:00Z",
    )
    if conn is not None:
        conn.execute(sql, params)
        return
    with db._connection() as own:
        own.execute(sql, params)


def _promote_new_note(
    db: Database,
    note_id: str,
    title: str,
    body: str,
    *,
    fact_id: str = "fact-1",
) -> None:
    """New-Note mode, in the order L1 depends on.

    The promotion row is written BEFORE the note, so when `notes_memory_ai`
    fires the guard already sees the promotion and the body is never written to
    the corpus at all -- not even transiently.  The deterministic mint (P0-4)
    is what makes the ref knowable before the note exists.
    """
    _insert_promotion(db, f"note:{note_id}", fact_id=fact_id)
    db.notes.upsert(
        note_id=note_id,
        title=title,
        body_markdown=body,
        last_modified="2026-09-07T09:00:00Z",
        created_at="2026-09-07T09:00:00Z",
    )


def _note(db: Database, note_id: str, title: str, body: str) -> None:
    db.notes.upsert(
        note_id=note_id,
        title=title,
        body_markdown=body,
        last_modified="2026-09-07T09:00:00Z",
        created_at="2026-09-07T09:00:00Z",
    )


def _fts_ids(db: Database) -> set[str]:
    with db._connection() as conn:
        return {
            str(row[0])
            for row in conn.execute("SELECT source_id FROM notes_memory_fts")
        }


def _rig(tmp_path: Path, name: str = "boundary.db") -> Database:
    """One ordinary note and one promoted note, both matching the query.

    The ordinary note is the POSITIVE CONTROL: every retrieval assertion below
    checks that it IS returned, so a fence that over-reaches fails just as
    loudly as a fence that is missing.
    """
    db = Database(tmp_path / name)
    _note(db, "control", "Cutover notes", f"{CONSTRAINT} {CONTROL_TOKEN}")
    _promote_new_note(
        db,
        "promoted",
        "We cannot take another cutover without a rollback rehearsal",
        f"{CONSTRAINT} {PROMOTED_TOKEN}",
    )
    return db


# ── L1 + L3: the unattached retrieval pass ───────────────────────────────


def test_a_promoted_record_is_never_returned_by_the_unattached_retrieval_pass(
    tmp_path: Path,
) -> None:
    """The P0-0 re-enactment, through the REAL envelope.

    `hydrate_refs_detailed` with empty ref lists and `include_memory=True` is
    the exact shape `ask_service.py:516-522` uses on EVERY Thought refinement,
    `recipe_service.py:111-120` on every recipe run, and
    `thread_service.py:380-390` on every plain chat turn.  Not attaching is the
    TRIGGER CONDITION for automatic retrieval, not an escape from it.
    """
    db = _rig(tmp_path)

    result = hydrate_refs_detailed(
        db, [], [], "summary", [], query=QUERY, include_memory=True
    )

    # The pass actually RAN -- otherwise this test proves nothing at all.
    assert result.selection == "ecosystem_relevance"
    # The control IS returned: the fence is not simply breaking retrieval.
    assert "note:control" in result.source_refs
    assert any(CONTROL_TOKEN in block.text for block in result.blocks)
    # The promoted record is absent by ref AND by bytes.
    assert "note:promoted" not in result.source_refs
    assert not any(PROMOTED_TOKEN in block.text for block in result.blocks)


def test_a_revoked_promotion_still_keeps_the_record_out_of_relevance(
    tmp_path: Path,
) -> None:
    """The fence keys on the EXISTENCE of a promotion, never its state.

    Once a record has been minted or appended to by promotion it never joins
    the relevance pool, revoked or not.  That errs closed and removes a class
    of state-dependent bugs.
    """
    db = Database(tmp_path / "revoked.db")
    _note(db, "control", "Cutover notes", f"{CONSTRAINT} {CONTROL_TOKEN}")
    _insert_promotion(db, "note:promoted", disclosure_state="revoked")
    _note(db, "promoted", "Rollback rehearsal", f"{CONSTRAINT} {PROMOTED_TOKEN}")

    result = hydrate_refs_detailed(
        db, [], [], "summary", [], query=QUERY, include_memory=True
    )
    assert "note:control" in result.source_refs
    assert "note:promoted" not in result.source_refs


# ── L2: the GRAPH route, which no corpus fence can reach ─────────────────


def _seed_graph(db: Database) -> None:
    """A lexical THREAD seed with two `note:` neighbours, one promoted.

    `_load_related_row`'s note branch reads `FROM notes WHERE id=? AND
    deleted=0` DIRECTLY (holdspeak/db/memory.py) and its rows are woven into
    the same hit list.  A note can therefore be retrieved on words it does NOT
    contain -- which is why neither note body carries the query word.
    """
    now = time.time()
    _note(db, "graph-control", "Payment ladder", f"Ladder rungs {CONTROL_TOKEN}")
    _promote_new_note(
        db,
        "graph-promoted",
        "Rollback rehearsal is not negotiable",
        f"Ladder rungs {PROMOTED_TOKEN}",
    )
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO threads(id,title,created_at,updated_at,last_turn_at)"
            " VALUES (?,?,?,?,?)",
            ("t-graph", "Zephyr planning", now, now, now),
        )
        conn.execute(
            "INSERT INTO thread_messages(id,thread_id,role,created_at,updated_at)"
            " VALUES (?,?,?,?,?)",
            ("m-graph", "t-graph", "user", now, now),
        )
        conn.execute(
            "INSERT INTO thread_message_parts(id,message_id,ordinal,kind,text)"
            " VALUES (?,?,0,'text',?)",
            (uuid.uuid4().hex, "m-graph", "the zephyr migration plan"),
        )
        for ref_id in ("graph-control", "graph-promoted"):
            conn.execute(
                "INSERT INTO thread_refs(id,thread_id,message_id,ref_kind,ref_id,"
                "version,frozen_json,created_at) VALUES (?,?,?,?,?,'','',?)",
                (uuid.uuid4().hex, "t-graph", "m-graph", "note", ref_id, now),
            )


def test_a_promoted_record_is_not_returned_through_the_GRAPH_route(
    tmp_path: Path,
) -> None:
    """L2, isolated.  Without this test L1 alone looks green and the boundary
    is open: the graph route never touches `notes_memory_fts`, so the corpus
    fence is irrelevant to it.
    """
    db = Database(tmp_path / "graph.db")
    _seed_graph(db)

    hits = db.memory.search("zephyr").hits
    refs = [hit.source_ref for hit in hits]

    # The seed matched lexically, so the expansion actually ran.
    assert any(ref.startswith("thread:t-graph") for ref in refs)
    # The control arrived BY THE GRAPH -- on a word its body does not contain.
    control = [hit for hit in hits if hit.source_ref == "note:graph-control"]
    assert control, refs
    assert control[0].retrieval_origin == "relationship"
    # The promoted neighbour did not arrive at all.
    assert "note:graph-promoted" not in refs


def test_the_graph_route_is_fenced_through_the_unattached_grounding_pass(
    tmp_path: Path,
) -> None:
    """The same route, driven from the real entry point rather than the repo."""
    db = Database(tmp_path / "graph-grounding.db")
    _seed_graph(db)

    result = hydrate_refs_detailed(
        db, [], [], "summary", [], query="zephyr", include_memory=True
    )
    assert result.selection == "ecosystem_relevance"
    assert any(CONTROL_TOKEN in block.text for block in result.blocks)
    assert not any(PROMOTED_TOKEN in block.text for block in result.blocks)


# ── L3: the two relevance call sites, observed in isolation ──────────────


class _Hit:
    def __init__(self, source_ref: str) -> None:
        self.source_ref = source_ref


class _UnfencedSearch:
    def __init__(self, refs: list[str]) -> None:
        self.hits = [_Hit(ref) for ref in refs]
        self.total = len(refs)
        self.lexical_total = len(refs)


class _UnfencedMemory:
    """A memory repository whose `search` has NOT applied L2.

    On the real path L2 removes a promoted ref before grounding ever sees it,
    so L3 is a belt that never fires -- which is exactly why it needs its own
    test.  This double reproduces the one thing L3 exists for: a hit list that
    reaches a relevance call site carrying a promoted ref by some route L2 did
    not cover.  It keeps the REAL `promoted_refs`, so the fence under test is
    the shipped one.
    """

    def __init__(self, real: Any, refs: list[str]) -> None:
        self._real = real
        self._refs = refs

    def search(self, *args: Any, **kwargs: Any) -> _UnfencedSearch:
        return _UnfencedSearch(list(self._refs))

    def promoted_refs(self) -> set[str]:
        return self._real.promoted_refs()


class _DbWithMemory:
    def __init__(self, db: Any, memory: Any) -> None:
        self._db = db
        self.memory = memory

    def __getattr__(self, name: str) -> Any:
        return getattr(self._db, name)


def test_the_global_relevance_call_site_drops_a_promoted_ref(
    tmp_path: Path,
) -> None:
    """L3 at `grounding.py`'s global pass, immediately before `_hydrate_members`."""
    db = _rig(tmp_path, "l3-global.db")
    handle = _DbWithMemory(db, _UnfencedMemory(db.memory, ["note:control", "note:promoted"]))

    result = hydrate_refs_detailed(
        handle, [], [], "summary", [], query=QUERY, include_memory=True
    )
    assert result.selection == "ecosystem_relevance"
    assert "note:control" in result.source_refs
    assert "note:promoted" not in result.source_refs
    assert not any(PROMOTED_TOKEN in block.text for block in result.blocks)


def test_the_project_scoped_relevance_call_site_drops_a_promoted_ref(
    tmp_path: Path,
) -> None:
    """L3 at `grounding.py`'s project-scoped relevance branch.

    The `recency_fallback` branch beside it is deliberately NOT filtered: it is
    a by-reference member listing of a container the owner attached on purpose,
    the same shape `knowledge:` and `zone:` take (see the P0-A guard below).
    """
    db = _rig(tmp_path, "l3-project.db")
    db.projects.create_project(project_id="p1", name="Payments")
    handle = _DbWithMemory(db, _UnfencedMemory(db.memory, ["note:control", "note:promoted"]))

    result = hydrate_refs_detailed(
        handle, [], [], "summary", ["project:p1"], query=QUERY, include_memory=True
    )
    assert result.selection == "relevance"
    assert "note:control" in result.source_refs
    assert "note:promoted" not in result.source_refs


# ── counsel-on-built F2: L3 must not fail OPEN ──────────────────────


class _MemoryThatCannotAnswerTheFence:
    """A memory handle that answers `search` but NOT `promoted_refs`.

    This is the shape counsel found L3 failing OPEN on.  `_promoted_refs` in
    `db/memory.py` carries the opposite discipline in its own docstring --
    "Deliberately not exception-guarded ... swallowing that would fail OPEN,
    the one direction this fence must never fail" -- and L3 did precisely what
    L2 refuses to do: `getattr(memory, "promoted_refs", None) is None` returned
    the members UNFENCED.

    A handle that produced relevance hits IS acting as a memory repository; if
    it cannot answer the fence question, the honest outcome is a refusal, not
    a prompt built out of a pool nobody checked.
    """

    def __init__(self, refs: list[str]) -> None:
        self._refs = refs

    def search(self, *args: Any, **kwargs: Any) -> _UnfencedSearch:
        return _UnfencedSearch(list(self._refs))


class _DbWithoutMemory:
    """A handle opened before the memory indexes existed: no repository."""

    memory = None

    def __init__(self, db: Any) -> None:
        self._db = db

    def __getattr__(self, name: str) -> Any:
        return getattr(self._db, name)


def test_a_memory_handle_that_cannot_answer_the_fence_refuses_instead_of_hydrating(
    tmp_path: Path,
) -> None:
    """F2: a `search`-bearing handle with no `promoted_refs` must RAISE.

    Before the fix this call returned `note:promoted` hydrated with its body
    in the prompt -- the exact leak ruling C2' exists to kill, produced by the
    fence itself.
    """
    db = _rig(tmp_path, "l3-no-fence.db")
    handle = _DbWithMemory(
        db, _MemoryThatCannotAnswerTheFence(["note:control", "note:promoted"])
    )

    with pytest.raises(AttributeError) as excinfo:
        hydrate_refs_detailed(
            handle, [], [], "summary", [], query=QUERY, include_memory=True
        )
    assert "promoted_refs" in str(excinfo.value)


def test_the_project_scoped_call_site_refuses_the_same_unanswerable_handle(
    tmp_path: Path,
) -> None:
    """The second relevance call site takes the same refusal."""
    db = _rig(tmp_path, "l3-no-fence-project.db")
    db.projects.create_project(project_id="p1", name="Payments")
    handle = _DbWithMemory(
        db, _MemoryThatCannotAnswerTheFence(["note:control", "note:promoted"])
    )

    with pytest.raises(AttributeError):
        hydrate_refs_detailed(
            handle, [], [], "summary", ["project:p1"], query=QUERY,
            include_memory=True,
        )


def test_a_handle_with_no_memory_repository_at_all_still_hydrates_by_reference(
    tmp_path: Path,
) -> None:
    """The POSITIVE CONTROL for the refusal above, and the case it exempts.

    `_memory_repo` returns None for a handle that carries no memory index, and
    both call sites guard on `memory is not None`, so no relevance search runs
    and there is no relevance pool to fence.  Recall stays an enrichment, never
    a precondition: by-reference hydration is untouched.
    """
    db = _rig(tmp_path, "no-memory.db")
    handle = _DbWithoutMemory(db)

    result = hydrate_refs_detailed(
        handle, [], [], "summary", ["note:promoted"], query=QUERY,
        include_memory=True,
    )
    assert result.source_refs == ["note:promoted"]
    assert PROMOTED_TOKEN in result.blocks[0].text
    assert result.selection == "explicit"


def test_the_fence_is_a_no_op_only_for_a_handle_with_no_repository() -> None:
    """The two branches of the F2 decision, asserted directly on the predicate.

    `None` -- no repository at all -- is the ONLY no-op.  Anything else that
    cannot answer `promoted_refs` refuses.
    """
    from holdspeak.grounding import _drop_promoted

    assert _drop_promoted(None, ["note:promoted"]) == ["note:promoted"]
    with pytest.raises(AttributeError):
        _drop_promoted(_MemoryThatCannotAnswerTheFence([]), ["note:promoted"])


# ── P0-A: the by-reference path must NOT be fenced ───────────────────────


def test_an_explicitly_attached_knowledge_or_zone_container_still_hydrates_a_promoted_member(
    tmp_path: Path,
) -> None:
    """The P0-A regression guard.

    `_hydrate_members` is SHARED: `_hydrate_container` reaches it from the
    explicit `knowledge:` and `zone:` branches.  A filter placed inside it
    would drop a promoted Note out of a container the owner attached on
    purpose -- SILENTLY, because `_hydrate_members` reports `unknown` only on a
    ref parse failure.

    This test's only job is to fail the moment someone "simplifies" the two
    relevance call sites back into the shared function.
    """
    db = _rig(tmp_path, "container.db")
    db.kbs.upsert(
        kb_id="kb1",
        name="Payments constraints",
        member_ids=["note:promoted"],
        last_modified="2026-09-07T09:00:00Z",
    )
    db.knowledge_memberships.upsert(knowledge_id="kb1", resource_ref="note:promoted")
    db.directories.upsert(directory_id="z1", name="Payments")
    db.directory_memberships.upsert(primitive_id="note:promoted", directory_id="z1")

    kb_result = hydrate_refs_detailed(
        db, [], [], "summary", ["knowledge:kb1"], query=QUERY, include_memory=True
    )
    assert any(PROMOTED_TOKEN in block.text for block in kb_result.blocks), (
        "an explicitly attached KB must still hydrate its promoted member"
    )
    assert kb_result.unknown == []

    zone_result = hydrate_refs_detailed(
        db, [], [], "summary", ["zone:z1"], query=QUERY, include_memory=True
    )
    assert any(PROMOTED_TOKEN in block.text for block in zone_result.blocks), (
        "an explicitly attached zone must still hydrate its promoted member"
    )
    assert zone_result.unknown == []


def test_by_reference_hydration_of_a_direct_note_ref_is_unaffected(
    tmp_path: Path,
) -> None:
    """Attach is unbroken: `_hydrate_qualified`'s note branch still returns the body."""
    db = _rig(tmp_path, "by-ref.db")

    result = hydrate_refs_detailed(
        db, [], [], "summary", ["note:promoted"], query=QUERY, include_memory=True
    )
    assert result.source_refs == ["note:promoted"]
    assert PROMOTED_TOKEN in result.blocks[0].text
    assert result.selection == "explicit"


# ── P0-B: the counters stay honest ───────────────────────────────────────


def test_search_totals_and_page_length_survive_the_exclusion(
    tmp_path: Path,
) -> None:
    """The P0-B guard, driven on the ROUTE where placement actually matters.

    The predicate must land on the shipped `excluded` plumbing, which is
    applied BEFORE the sort and before `lexical_total`.  If it migrated to the
    `MemoryHit` constructor (or anywhere after `total = len(interleaved)`),
    `total` would count a record never returned, the page would come back
    shorter than `limit` with no explanation, and `grounding.py` would book the
    withheld source as mere OVERFLOW -- "incomplete observation presented as an
    all-clear", produced by the fence itself.

    It has to be the GRAPH route.  On the lexical route L1 keeps the promoted
    body out of the corpus, so it never enters `interleaved` at all and the
    counters are honest wherever the predicate sits -- a first draft of this
    test used that route and passed against a deliberately late filter.  A test
    that cannot fail on the real path is not proof.
    """
    db = Database(tmp_path / "totals-graph.db")
    _seed_graph(db)

    search = db.memory.search("zephyr")
    refs = [hit.source_ref for hit in search.hits]
    assert refs == ["thread:t-graph#m-graph", "note:graph-control"]
    assert search.total == len(search.hits) == 2, (
        "a withheld graph neighbour must never be counted in `total`"
    )
    assert search.lexical_total == 1

    result = hydrate_refs_detailed(
        db, [], [], "summary", [], query="zephyr", include_memory=True
    )
    assert result.overflow_count == 0, (
        "a withheld source must never be booked as overflow"
    )


def test_lexical_totals_and_the_overflow_receipt_stay_honest(
    tmp_path: Path,
) -> None:
    """The same accounting on the lexical route: nothing withheld, nothing
    booked as overflow, and the page is the honest post-exclusion length."""
    db = Database(tmp_path / "totals.db")
    for ordinal in range(3):
        _note(
            db,
            f"control-{ordinal}",
            f"Cutover notes {ordinal}",
            f"{CONSTRAINT} {CONTROL_TOKEN}",
        )
    _promote_new_note(
        db, "promoted", "Rollback rehearsal", f"{CONSTRAINT} {PROMOTED_TOKEN}"
    )

    search = db.memory.search(QUERY, kinds=["note"])
    assert [hit.source_ref for hit in search.hits] == [
        "note:control-0",
        "note:control-1",
        "note:control-2",
    ]
    assert search.total == 3
    assert search.lexical_total == 3
    assert len(search.hits) == 3

    result = hydrate_refs_detailed(
        db, [], [], "summary", [], query=QUERY, include_memory=True
    )
    assert result.selection == "ecosystem_relevance"
    assert len(result.blocks) == 3
    assert result.overflow_count == 0, (
        "a withheld source must never be booked as overflow"
    )
    assert result.matched_count == 3


def test_memory_search_does_not_return_a_promoted_record(tmp_path: Path) -> None:
    """CONTRACTS.md "search": `MemoryRepository.search` over the `note` kind.

    The `memory.search` MCP tool is a thin dispatch over this repository
    method; the MCP family is not this lane's file.
    """
    db = _rig(tmp_path, "search.db")
    hits = db.memory.search(QUERY, kinds=["note"]).hits
    assert [hit.source_ref for hit in hits] == ["note:control"]


# ── L1: the corpus, by construction ──────────────────────────────────────


def test_the_promoted_body_is_absent_from_the_fts_corpus(tmp_path: Path) -> None:
    """Construction, not filtering: the body was never written to the corpus."""
    db = _rig(tmp_path, "corpus.db")
    assert _fts_ids(db) == {"control"}


def test_a_full_rebuild_cannot_re_admit_a_promoted_record(tmp_path: Path) -> None:
    """`rebuild_memory_index` carries the same predicate as the triggers."""
    db = _rig(tmp_path, "rebuild.db")
    counts = db.memory.rebuild()
    assert counts["notes"] == 1
    assert _fts_ids(db) == {"control"}

    with db._connection() as conn:
        rebuild_memory_index(conn)
    assert _fts_ids(db) == {"control"}


def test_a_promotion_over_an_existing_note_self_heals_the_corpus_on_the_next_write(
    tmp_path: Path,
) -> None:
    """The append mode's residue.

    An existing note is already indexed when the promotion lands, so the
    promotion transaction owes an atomic `DELETE FROM notes_memory_fts` --
    that DELETE belongs to Lane B's verb.  What this lane owes is that the
    guarded `notes_memory_au` then DECLINES to re-insert on every later write,
    and that a full rebuild cannot re-admit it.  Both are asserted here.
    """
    db = Database(tmp_path / "append.db")
    _note(db, "existing", "Cutover notes", f"{CONSTRAINT} {PROMOTED_TOKEN}")
    assert _fts_ids(db) == {"existing"}

    _insert_promotion(db, "note:existing")
    # Before the next write the stale row is still there -- which is precisely
    # why the verb owes the atomic DELETE.
    assert _fts_ids(db) == {"existing"}

    _note(db, "existing", "Cutover notes", f"{CONSTRAINT} {PROMOTED_TOKEN} edited")
    assert _fts_ids(db) == set()

    db.memory.rebuild()
    assert _fts_ids(db) == set()


def test_the_belt_predicate_holds_even_if_the_trigger_refresh_was_botched(
    tmp_path: Path,
) -> None:
    """Belt as well as braces -- and this test says honestly what it pins.

    L1 is the construction; `_note_rows`' own `NOT EXISTS` predicate is the
    belt that survives an older database whose trigger bodies were never
    refreshed.  On the REAL path that belt is redundant with L2, which removes
    the ref from `interleaved` before anything is counted -- so a test driving
    `MemoryRepository.search` passes with the belt deleted, and would be a
    false green if it claimed to pin it (checked: mutating the belt out leaves
    the whole `search`-driven suite green).

    The belt's subject IS `_note_rows`, so this test drives `_note_rows`.  It
    pins the second, independent mechanism; it does NOT prove the boundary --
    the tests above do that.
    """
    from holdspeak.db.memory import MemoryRepository, _match_expression

    db = _rig(tmp_path, "belt.db")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO notes_memory_fts(source_id,title,body_markdown)"
            " SELECT id,title,body_markdown FROM notes WHERE id='promoted'"
        )
        indexed = {
            str(row[0])
            for row in conn.execute("SELECT source_id FROM notes_memory_fts")
        }
        assert indexed == {"control", "promoted"}
        rows = MemoryRepository._note_rows(
            conn, _match_expression(QUERY), None, None, None
        )
    assert [row["source_ref"] for row in rows] == ["note:control"]


# ── The cost is bounded: by-reference discovery survives ─────────────────


def test_the_context_picker_still_finds_a_promoted_note_by_title(
    tmp_path: Path,
) -> None:
    """The repair path for the usability loss F0 deliberately accepts.

    The picker searches `notes` directly with `title LIKE ... COLLATE NOCASE`
    -- title only, never body.  D2.2 therefore mints the title from the quote,
    so the owner searches for words he actually said and finds them.  This
    test is what makes "the cost is bounded" a fact rather than a hope.
    """
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.refinement_context_service import RefinementContextService
    from holdspeak.services.refinement_thought_service import (
        INBOX_DIRECTORY_ID,
        RefinementThoughtService,
    )

    db = _rig(tmp_path, "picker.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    owner = Principal(PrincipalKind.OWNER, "picker-owner")
    thought = RefinementThoughtService(db).create(
        owner,
        request_id="picker-thought",
        raw_text="Turn this into a plan.",
        source={"kind": "typed"},
        initial_note={"id": "picker-working-note", "title": "Rough plan"},
    )

    page = RefinementContextService(db).list_context(
        owner, thought["id"], query="rollback rehearsal"
    )
    found = [item["ref"] for item in page["results"]]
    assert "note:promoted" in found, found


# ── AC3: the staleness lattice, from the trigger side ────────────────────


def _dependent(
    db: Database,
    canonical_ref: str,
    *,
    consumer_id: str = "thought-1",
    stale_reason: str = "",
    stale_since: str | None = None,
) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO context_dependents(
                   canonical_ref, consumer_kind, consumer_id, consumer_revision,
                   bound_manifest_sha256, bound_at, stale_since, stale_reason)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                canonical_ref,
                "thought",
                consumer_id,
                3,
                "sha256:manifest",
                "2026-09-07T09:00:00Z",
                stale_since,
                stale_reason,
            ),
        )


def _dependent_row(db: Database, canonical_ref: str, consumer_id: str = "thought-1"):
    with db._connection() as conn:
        return conn.execute(
            "SELECT stale_reason, stale_since FROM context_dependents"
            " WHERE canonical_ref=? AND consumer_kind='thought' AND consumer_id=?",
            (canonical_ref, consumer_id),
        ).fetchone()


def test_a_fresh_dependent_goes_stale_on_a_note_edit_without_opening_the_consumer(
    tmp_path: Path,
) -> None:
    """The reverse push: the consumer is marked without being loaded."""
    db = Database(tmp_path / "lattice-stale.db")
    _note(db, "n1", "Constraint", CONSTRAINT)
    _dependent(db, "note:n1")

    _note(db, "n1", "Constraint", CONSTRAINT + " unless reversible in five minutes")

    row = _dependent_row(db, "note:n1")
    assert row["stale_reason"] == "stale"
    assert row["stale_since"]


def test_the_first_staleness_time_is_kept_across_further_edits(
    tmp_path: Path,
) -> None:
    """`COALESCE(stale_since, datetime('now'))` -- the FIRST time, not the last."""
    db = Database(tmp_path / "lattice-coalesce.db")
    _note(db, "n1", "Constraint", CONSTRAINT)
    _dependent(db, "note:n1", stale_reason="stale", stale_since="2026-01-01T00:00:00")

    _note(db, "n1", "Constraint", CONSTRAINT + " edited again")

    assert _dependent_row(db, "note:n1")["stale_since"] == "2026-01-01T00:00:00"


def test_a_note_save_after_a_revocation_leaves_forbidden_intact(
    tmp_path: Path,
) -> None:
    """P0-2 directly.  `forbidden` is TERMINAL.

    `refinement_thought_service` writes a working Note on EVERY accepted
    revision, so a trigger that downgraded `forbidden` to `stale` would turn a
    revocation into an ordinary refreshable staleness on the very next save --
    and a consumer fencing on `forbidden` would then dispatch.  That is
    "unauthorized disclosure or execution outside the applicable scope",
    defeated by this design's own push.

    Without the `CASE WHEN stale_reason = 'forbidden'` limb this test fails.
    """
    db = Database(tmp_path / "lattice-forbidden.db")
    _note(db, "n1", "Constraint", CONSTRAINT)
    _dependent(db, "note:n1", stale_reason="forbidden", stale_since="2026-01-01T00:00:00")
    # A second consumer that is NOT under revocation -- the positive control.
    _dependent(db, "note:n1", consumer_id="thought-2")

    _note(db, "n1", "Constraint", CONSTRAINT + " softened")

    assert _dependent_row(db, "note:n1")["stale_reason"] == "forbidden"
    assert _dependent_row(db, "note:n1", "thought-2")["stale_reason"] == "stale"


def test_a_soft_delete_marks_dependents_unavailable_but_never_downgrades_forbidden(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "lattice-soft.db")
    _note(db, "n1", "Constraint", CONSTRAINT)
    _dependent(db, "note:n1", stale_reason="forbidden")
    _dependent(db, "note:n1", consumer_id="thought-2")

    db.notes.upsert(
        note_id="n1",
        title="Constraint",
        body_markdown=CONSTRAINT,
        last_modified="2026-09-08T09:00:00Z",
        deleted=True,
    )

    assert _dependent_row(db, "note:n1")["stale_reason"] == "forbidden"
    assert _dependent_row(db, "note:n1", "thought-2")["stale_reason"] == "unavailable"


def test_a_hard_delete_marks_dependents_unavailable_but_never_downgrades_forbidden(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "lattice-hard.db")
    _note(db, "n1", "Constraint", CONSTRAINT)
    _dependent(db, "note:n1", stale_reason="forbidden")
    _dependent(db, "note:n1", consumer_id="thought-2")

    with db._connection() as conn:
        conn.execute("DELETE FROM notes WHERE id='n1'")

    assert _dependent_row(db, "note:n1")["stale_reason"] == "forbidden"
    assert _dependent_row(db, "note:n1", "thought-2")["stale_reason"] == "unavailable"


def test_a_note_with_no_dependents_matches_zero_rows(tmp_path: Path) -> None:
    """The `WHERE` hits the PK's leading column: one index probe, no rows."""
    db = Database(tmp_path / "lattice-empty.db")
    _note(db, "n1", "Constraint", CONSTRAINT)
    _dependent(db, "note:other")

    _note(db, "n1", "Constraint", CONSTRAINT + " edited")

    assert _dependent_row(db, "note:other")["stale_reason"] == ""


# ── The tables themselves ────────────────────────────────────────────────


def test_the_three_tables_and_three_indexes_exist(tmp_path: Path) -> None:
    db = Database(tmp_path / "tables.db")
    with db._connection() as conn:
        names = {
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','index')"
            )
        }
    assert {
        "context_promotions",
        "context_promotion_suppressions",
        "context_dependents",
        "idx_context_promotions_target",
        "idx_context_promotions_source",
        "idx_context_dependents_consumer",
    } <= names


def test_target_kind_and_disclosure_state_carry_no_check_constraint(
    tmp_path: Path,
) -> None:
    """Stories 11, 13, 17 and 20 widen this vocabulary; widening a SQLite
    CHECK is a table rebuild, so the service validates instead."""
    db = Database(tmp_path / "nocheck.db")
    with db._connection() as conn:
        _insert_promotion(db, "note:x", fact_id="widened", conn=conn)
        conn.execute(
            "UPDATE context_promotions SET target_kind='project_facet',"
            " disclosure_state='superseded' WHERE target_ref='note:x'"
        )
        row = conn.execute(
            "SELECT target_kind, disclosure_state FROM context_promotions"
            " WHERE target_ref='note:x'"
        ).fetchone()
    assert row["target_kind"] == "project_facet"
    assert row["disclosure_state"] == "superseded"


def test_one_fact_may_carry_several_promotions_into_one_record(
    tmp_path: Path,
) -> None:
    """`UNIQUE (thread_id, fact_id, target_ref)` deliberately permits N
    promotions into one target_ref -- the append mode is the design's own
    second mode -- which is what makes P0-3's revoke rule necessary."""
    db = Database(tmp_path / "unique.db")
    _insert_promotion(db, "note:n1", fact_id="f1")
    _insert_promotion(db, "note:n1", fact_id="f2")
    with db._connection() as conn:
        count = conn.execute(
            "SELECT count(*) FROM context_promotions WHERE target_ref='note:n1'"
        ).fetchone()[0]
        try:
            _insert_promotion(db, "note:n1", fact_id="f1", conn=conn)
            duplicated = True
        except sqlite3.IntegrityError:
            duplicated = False
    assert count == 2
    assert duplicated is False
