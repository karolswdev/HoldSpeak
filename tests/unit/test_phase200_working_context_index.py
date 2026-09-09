"""HS-200-10 Lane C: the reverse index, the content hash, and two fences.

Three things, and the third is two fences Lane A could not reach from the
files it owned.

**The reverse index (ruling C5, AC2/AC3).**  `refinement_attachment_visible`
is keyed `(thought_id, attachment_revision, ordinal)` with the ref only a
PAYLOAD column, and revisions are never pruned -- so "who consumes note:n1?"
is a scan of every revision of every Thought, and nothing can mark a consumer
that is not open.  `context_dependents` answers it in one seek with ONE row
per (record, consumer), written at ONE reconcile point per consumer kind:
`RefinementContextService._persist_manifest` for `consumer_kind='thought'`.

**The content hash (counsel P0-1).**  `_leaf`'s digest folds `last_modified`
into itself, so a byte-identical re-save would report the owner's constraint
as `corrected` when it did not move.  `promotion_content_sha256` is a new
recipe over `{ref, title, body_markdown, tags}` and nothing else.

**L4 and P0-C.**  The frozen-ref replay in `thread_service._assemble_payload`,
and the sync fence in `sync_service` -- "the one P0 whose failure he could
actually meet", because everything else in this story starts empty on his
machine.

THE LAW THIS PHASE PAID FOR: **a test that cannot fail on the real path is not
proof.**  So every fence test here drives the REAL path -- `attach_context` /
`detach_context` through the service, `start_turn` and `_assemble_payload`
through a real `ThreadService`, `SyncService.pull` -> `SyncService.push`
between two real Databases -- never a helper picked for convenience, and each
carries a POSITIVE CONTROL that must survive, so a fence that over-reaches
fails as loudly as one that is missing.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.db.memory import rebuild_memory_index
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.refinement_context_service import (
    EVERYDAY_CONTEXT_REF,
    RefinementContextService,
    note_promotion_revision_in_transaction,
    promotion_content_sha256,
    promotion_content_state_in_transaction,
)
from holdspeak.services.refinement_thought_service import (
    INBOX_DIRECTORY_ID,
    RefinementThoughtService,
)
from holdspeak.services.thread_service import ThreadService


OWNER = Principal(PrincipalKind.OWNER, "index-owner")
EVERYDAY_ID = EVERYDAY_CONTEXT_REF.split(":", 1)[1]

CONSTRAINT = (
    "We cannot take another cutover without a rollback rehearsal. "
    "That is not negotiable."
)
PROMOTED_TOKEN = "kestrelmark"
CONTROL_TOKEN = "wrenmark"
QUERY = "cutover rollback rehearsal"


# ── shared rig ───────────────────────────────────────────────────────────


def _wall_clock() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _insert_promotion(
    conn: sqlite3.Connection,
    target_ref: str,
    *,
    promotion_id: str = "",
    thread_id: str = "thread-interview",
    fact_id: str = "fact-1",
    disclosure_state: str = "active",
    content_sha256: str = "",
    created_at: str = "",
    updated_at: str = "2026-09-07T09:00:00Z",
) -> str:
    """One `context_promotions` row, every column named.

    Lane B owns the verb (`InterviewService.command`); this writes the row in
    the order that verb must use.
    """
    promotion_id = promotion_id or f"cp_{thread_id}_{fact_id}"
    # The promotion happens NOW, in wall-clock terms, which is what makes the
    # "was this thread_refs row frozen BEFORE the promotion?" question in L4
    # answerable.  `thread_refs.created_at` is a REAL unix time.
    created_at = created_at or _wall_clock()
    conn.execute(
        """INSERT INTO context_promotions(
               promotion_id, thread_id, fact_id, source_message_id,
               quote_sha256, quote_locator_json, target_kind, target_ref,
               target_revision_label, target_content_sha256,
               disclosure_state, request_sha256, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            promotion_id, thread_id, fact_id, "msg-1",
            "sha256:quote", '{"part_ordinal": 0}', "note", target_ref,
            "2026-09-07T09:00:00Z", content_sha256,
            disclosure_state, "sha256:request",
            created_at, updated_at,
        ),
    )
    return promotion_id


def _promote_new_note(
    db: Database, note_id: str, title: str, body: str, *,
    fact_id: str = "fact-1", tags: list[str] | None = None,
) -> None:
    """New-Note mode, in the order L1 depends on: row FIRST, note SECOND."""
    with db._connection() as conn:
        _insert_promotion(conn, f"note:{note_id}", fact_id=fact_id)
    db.notes.upsert(
        note_id=note_id, title=title, body_markdown=body, tags=tags or [],
        last_modified="2026-09-07T09:00:00Z", created_at="2026-09-07T09:00:00Z",
    )


def _cursors(thought: dict) -> dict[str, int]:
    return {
        "expected_aggregate_revision": thought["aggregate_revision"],
        "expected_working_revision": thought["working_revision"],
        "expected_attachment_revision": thought["attachment_revision"],
    }


def _dependents(db: Database, canonical_ref: str) -> list[dict[str, Any]]:
    """Who consumes this record -- ONE seek, no Thought loaded."""
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM context_dependents WHERE canonical_ref=?"
            " ORDER BY consumer_kind, consumer_id", (canonical_ref,)).fetchall()]


def _rows_for(db: Database, consumer_id: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM context_dependents WHERE consumer_kind='thought'"
            " AND consumer_id=? ORDER BY canonical_ref", (consumer_id,)).fetchall()]


@pytest.fixture
def rig(tmp_path: Path):
    db = Database(tmp_path / "working-context-index.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    # The promoted canonical record -- one Note, no copies.
    _promote_new_note(
        db, "promoted",
        "We cannot take another cutover without a rollback rehearsal",
        f"{CONSTRAINT} {PROMOTED_TOKEN}", tags=["constraint"],
    )
    # The positive control: an ordinary Note the owner typed.
    db.notes.upsert(
        note_id="control", title="Cutover notes",
        body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}", tags=["today"],
        last_modified="2026-09-07T09:00:00Z",
    )
    return db, RefinementThoughtService(db), RefinementContextService(db)


def _thought(thoughts: RefinementThoughtService, key: str) -> dict[str, Any]:
    return thoughts.create(
        OWNER, request_id=f"create-{key}", raw_text="Turn this into a plan.",
        source={"kind": "typed"},
        initial_note={"id": f"working-{key}", "title": f"Plan {key}"},
    )


# ── AC2: two Thoughts, one record, no copies ─────────────────────────────


def test_two_thoughts_share_one_promoted_note_and_neither_owns_a_copy(rig) -> None:
    """AC2 at Thought scope, and the index answers the reverse question.

    Thursday he attaches the constraint to the architecture Thought; Friday he
    attaches the SAME Note to the update Thought.  There is one Note.  Neither
    Thought owns it.  Saturday he edits it ONCE and both read stale -- proved
    here through the index, with neither Thought loaded.
    """
    db, thoughts, context = rig
    a, b = _thought(thoughts, "a"), _thought(thoughts, "b")

    context.attach_context(OWNER, a["id"], visible_ref="note:promoted",
                           request_id="attach-a", **_cursors(a))
    context.attach_context(OWNER, b["id"], visible_ref="note:promoted",
                           request_id="attach-b", **_cursors(b))

    # ONE row per (record, consumer) -- never one per revision.
    consumers = _dependents(db, "note:promoted")
    assert {(r["consumer_kind"], r["consumer_id"]) for r in consumers} == {
        ("thought", a["id"]), ("thought", b["id"])}
    assert len(consumers) == 2
    assert all(r["stale_reason"] == "" and r["stale_since"] is None for r in consumers)

    # There is exactly ONE editable record.  No copy was minted anywhere.
    with db._connection() as conn:
        assert conn.execute(
            "SELECT count(*) FROM notes WHERE body_markdown LIKE ?",
            (f"%{PROMOTED_TOKEN}%",)).fetchone()[0] == 1

    # He softens it once.
    db.notes.upsert(note_id="promoted",
                    title="We cannot take another cutover without a rollback rehearsal",
                    body_markdown=f"{CONSTRAINT} Unless reversible in five minutes. {PROMOTED_TOKEN}",
                    tags=["constraint"], last_modified="2026-09-08T09:00:00Z")

    assert {r["consumer_id"]: r["stale_reason"] for r in _dependents(db, "note:promoted")} == {
        a["id"]: "stale", b["id"]: "stale"}

    # The PULL agrees for display, on both, without either being refreshed.
    assert thoughts.get(OWNER, a["id"])["attachments"][0]["state"] == "stale"
    assert thoughts.get(OWNER, b["id"])["attachments"][0]["state"] == "stale"

    # Refreshing ONE re-binds only that one: the other still reads stale.
    current_a = thoughts.get(OWNER, a["id"])
    context.refresh_context(OWNER, a["id"], visible_ref="note:promoted",
                            request_id="refresh-a", **_cursors(current_a))
    assert {r["consumer_id"]: r["stale_reason"] for r in _dependents(db, "note:promoted")} == {
        a["id"]: "", b["id"]: "stale"}


def test_correcting_the_note_marks_every_dependent_without_opening_it(rig) -> None:
    """AC3's push half.  Nothing here loads a Thought, and nothing can.

    Today's staleness is entirely detect-on-read: `project_in_transaction`
    recomputes and compares only once you HOLD the Thought.  A cadence run
    that would dispatch against a moved record has nothing to consult.
    """
    db, thoughts, context = rig
    a, b, c = (_thought(thoughts, k) for k in ("a", "b", "c"))
    for thought, rid in ((a, "attach-a"), (b, "attach-b")):
        context.attach_context(OWNER, thought["id"], visible_ref="note:promoted",
                               request_id=rid, **_cursors(thought))
    # `c` consumes the CONTROL note: it must not be marked by this correction.
    context.attach_context(OWNER, c["id"], visible_ref="note:control",
                           request_id="attach-c", **_cursors(c))

    db.notes.upsert(note_id="promoted", title="Softened",
                    body_markdown="Unless reversible in five minutes.",
                    tags=["constraint"], last_modified="2026-09-08T09:00:00Z")

    marked = {r["consumer_id"]: r["stale_reason"] for r in _dependents(db, "note:promoted")}
    assert marked == {a["id"]: "stale", b["id"]: "stale"}
    assert all(r["stale_since"] for r in _dependents(db, "note:promoted"))
    # The control consumer is untouched -- the push is ref-keyed, not global.
    assert _dependents(db, "note:control")[0]["stale_reason"] == ""


def test_thread_grounding_is_a_copy_and_this_design_does_not_change_it(
    tmp_path: Path,
) -> None:
    """Ruling C7's narrowing PROVED, not asserted in prose.

    AC2 says "two Threads".  A Thought's grounding is a live REFERENCE --
    `refinement_attachment_visible` stores refs and hashes and the body is
    re-read at prompt time.  A Thread's grounding is a frozen COPY:
    `thread_refs.frozen_json` carries the block's full text, written once.
    Correcting the Note moves the Thought and leaves the Thread's copy exactly
    where it was.  That gap is real, it is declared against ACCEPTANCE's
    P200-A08, and this test is the record of it.
    """
    db = Database(tmp_path / "narrowing.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    db.notes.upsert(note_id="shared", title="Rollback rehearsal",
                    body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}", tags=["c"],
                    last_modified="2026-09-07T09:00:00Z")
    thoughts, context = RefinementThoughtService(db), RefinementContextService(db)
    thought = _thought(thoughts, "narrow")
    context.attach_context(OWNER, thought["id"], visible_ref="note:shared",
                           request_id="attach-narrow", **_cursors(thought))

    service = _thread_service(db)
    thread = service.create(title="Architecture")
    asyncio.run(service.start_turn(OWNER, thread["id"], "rollback rehearsal cutover",
                                   refs=["note:shared"]))
    time.sleep(0.5)
    frozen_before = _frozen_texts(db, thread["id"])
    assert any(CONTROL_TOKEN in text for text in frozen_before), frozen_before

    db.notes.upsert(note_id="shared", title="Rollback rehearsal",
                    body_markdown="Softened entirely.", tags=["c"],
                    last_modified="2026-09-08T09:00:00Z")

    # The THOUGHT tracks the correction, by reference and through the index.
    assert thoughts.get(OWNER, thought["id"])["attachments"][0]["state"] == "stale"
    assert _dependents(db, "note:shared")[0]["stale_reason"] == "stale"
    # The THREAD still holds its own copy of the old words.  Unchanged by
    # this design, and undeliverable here without rewriting the Thread prompt
    # path (settled design, "cannot promise" #5).
    assert _frozen_texts(db, thread["id"]) == frozen_before
    assert any(CONTROL_TOKEN in text for text in _frozen_texts(db, thread["id"]))


# ── P0-1: the content hash contains content, and nothing else ────────────


def test_the_content_hash_excludes_the_timestamp(rig) -> None:
    """P0-1.  A byte-identical re-save must NOT report his constraint moved.

    `NoteRepository._upsert_in_transaction` writes
    `last_modified=excluded.last_modified` UNCONDITIONALLY on ON CONFLICT --
    there is no "did anything change" guard at the primitive.  `_leaf`'s digest
    folds `last_modified` (and `deleted`) in, so reusing it would make the
    promotion read `corrected` about a sentence nobody touched: unsupported
    prose presented as checked fact, produced by the comparator itself.
    """
    db, _thoughts, _context = rig
    with db._connection() as conn:
        before = note_promotion_revision_in_transaction(conn, "note:promoted")
        _insert_promotion(conn, "note:leaf-probe", promotion_id="cp-probe",
                          fact_id="fact-probe")
    assert before is not None

    # Byte-identical body, title and tags.  A NEW `last_modified`.
    db.notes.upsert(
        note_id="promoted",
        title="We cannot take another cutover without a rollback rehearsal",
        body_markdown=f"{CONSTRAINT} {PROMOTED_TOKEN}", tags=["constraint"],
        last_modified="2026-09-09T17:45:00Z",
    )

    with db._connection() as conn:
        after = note_promotion_revision_in_transaction(conn, "note:promoted")
        state = promotion_content_state_in_transaction(
            conn, "note:promoted", before["content_sha256"])
    assert after is not None
    # The LABEL moved -- it is `last_modified`, and it is display only.
    assert after["label"] != before["label"]
    assert after["label"] == "2026-09-09T17:45:00Z"
    # The COMPARATOR did not.  The promotion reads `current`, not `corrected`.
    assert after["content_sha256"] == before["content_sha256"]
    assert state == "current"

    # And the contrast that makes the assertion mean something: `_leaf`'s
    # shipped recipe DOES move, which is exactly why it was not reused.
    with db._connection() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id='promoted'").fetchone()
        leaf_after = RefinementContextService._leaf(row, "note:promoted", "")
    assert leaf_after["leaf_content_sha256"] != before["content_sha256"]

    # A real correction still moves the comparator.
    db.notes.upsert(
        note_id="promoted",
        title="We cannot take another cutover without a rollback rehearsal",
        body_markdown="Unless reversible in five minutes.", tags=["constraint"],
        last_modified="2026-09-09T17:45:00Z",
    )
    with db._connection() as conn:
        assert promotion_content_state_in_transaction(
            conn, "note:promoted", before["content_sha256"]) == "corrected"


def test_the_content_hash_covers_title_and_tags_and_the_ref(rig) -> None:
    """`{ref, title, body_markdown, tags}` -- all four, and only those four."""
    base = dict(ref="note:promoted", title="T", body_markdown="B", tags=["x"])
    digest = promotion_content_sha256(**base)
    assert digest != promotion_content_sha256(**{**base, "ref": "note:other"})
    assert digest != promotion_content_sha256(**{**base, "title": "T2"})
    assert digest != promotion_content_sha256(**{**base, "body_markdown": "B2"})
    assert digest != promotion_content_sha256(**{**base, "tags": ["x", "y"]})
    assert digest == promotion_content_sha256(**base)


def test_a_deleted_or_missing_target_reads_unavailable(rig) -> None:
    db, _t, _c = rig
    with db._connection() as conn:
        bound = note_promotion_revision_in_transaction(conn, "note:promoted")["content_sha256"]
    db.notes.delete("promoted")
    with db._connection() as conn:
        assert note_promotion_revision_in_transaction(conn, "note:promoted") is None
        assert promotion_content_state_in_transaction(conn, "note:promoted", bound) == "unavailable"
        assert promotion_content_state_in_transaction(conn, "note:ghost", bound) == "unavailable"


def test_an_unchanged_last_modified_resave_diverges_index_from_pull(rig) -> None:
    """The REAL arbitration case, and the one the first draft got wrong.

    `NoteRepository.upsert` takes an explicit `last_modified`.  A re-save
    carrying the SAME one still UPDATEs `notes` -- so the trigger fires and the
    index marks `stale` -- while moving NEITHER the content hash nor `_leaf`'s
    visible hash, so the pull still reads `current`.

    Where they disagree: **the pull wins for display and the index wins for
    refusal.**  Exact where the owner is looking; fail-closed where something
    would run unattended.  A trigger cannot hash, so the push is deliberately
    conservative: over-marking says "check this", under-marking is the breach.
    """
    db, thoughts, context = rig
    thought = _thought(thoughts, "arb")
    context.attach_context(OWNER, thought["id"], visible_ref="note:promoted",
                           request_id="attach-arb", **_cursors(thought))
    assert _dependents(db, "note:promoted")[0]["stale_reason"] == ""

    db.notes.upsert(
        note_id="promoted",
        title="We cannot take another cutover without a rollback rehearsal",
        body_markdown=f"{CONSTRAINT} {PROMOTED_TOKEN}", tags=["constraint"],
        last_modified="2026-09-07T09:00:00Z",   # UNCHANGED, explicitly
    )

    # The INDEX marks it -- conservative, fail-closed.
    assert _dependents(db, "note:promoted")[0]["stale_reason"] == "stale"
    # The PULL still reads `current` -- exact, and what the owner's face shows.
    assert thoughts.get(OWNER, thought["id"])["attachments"][0]["state"] == "current"
    # And `materialize` does NOT refuse, because the pull is the authority for
    # the attached path.
    current = thoughts.get(OWNER, thought["id"])
    assert context.materialize(thought["id"], current["attachment_revision"],
                               current["attachment_sha256"]).material


# ── AC3: the lattice, from the WRITE side ────────────────────────────────


def test_rebinding_clears_stale_but_never_clears_forbidden(rig) -> None:
    """The lattice from the other side.  `forbidden` is TERMINAL.

    A rebind through the reconcile point clears `stale` -- the manifest just
    re-bound at the current bytes.  It must NOT clear `forbidden`: the record
    is under revocation and re-binding it is exactly what must not silently
    succeed.  Only an explicit re-promotion clears it.
    """
    db, thoughts, context = rig
    stale_thought = _thought(thoughts, "stale")
    forbidden_thought = _thought(thoughts, "forbid")
    for thought, rid in ((stale_thought, "attach-stale"),
                         (forbidden_thought, "attach-forbid")):
        context.attach_context(OWNER, thought["id"], visible_ref="note:promoted",
                               request_id=rid, **_cursors(thought))

    db.notes.upsert(note_id="promoted", title="Softened",
                    body_markdown="Unless reversible in five minutes.",
                    tags=["constraint"], last_modified="2026-09-08T09:00:00Z")
    # A revocation lands on ONE of them (Lane B's `revoke_promotion` writes
    # this; the lattice is what this test is about).
    with db._connection() as conn:
        conn.execute("UPDATE context_dependents SET stale_reason='forbidden',"
                     " stale_since='2026-01-01T00:00:00' WHERE consumer_id=?",
                     (forbidden_thought["id"],))

    for thought in (stale_thought, forbidden_thought):
        current = thoughts.get(OWNER, thought["id"])
        context.refresh_context(OWNER, thought["id"], visible_ref="note:promoted",
                                request_id=f"rebind-{thought['id']}", **_cursors(current))

    marked = {r["consumer_id"]: r for r in _dependents(db, "note:promoted")}
    assert marked[stale_thought["id"]]["stale_reason"] == ""
    assert marked[stale_thought["id"]]["stale_since"] is None
    assert marked[forbidden_thought["id"]]["stale_reason"] == "forbidden"
    # The rebind does not restart the revocation's clock either.
    assert marked[forbidden_thought["id"]]["stale_since"] == "2026-01-01T00:00:00"
    # It DID re-bind: the manifest hash moved to the current one.
    rebound = thoughts.get(OWNER, forbidden_thought["id"])
    assert marked[forbidden_thought["id"]]["bound_manifest_sha256"] == \
        rebound["attachment_sha256"]


def test_a_detach_removes_the_row_and_a_birth_creates_it(tmp_path: Path) -> None:
    """All four verbs through the ONE reconcile point.

    attach, detach and rebind go through `_mutate`; BIRTH goes through
    `apply_default_at_birth_in_transaction` -- a different call site of the
    same `_persist_manifest`, which is why "one write point" is the invariant
    and not "one caller".
    """
    db = Database(tmp_path / "verbs.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    _promote_new_note(db, "promoted", "Rollback rehearsal",
                      f"{CONSTRAINT} {PROMOTED_TOKEN}", tags=["c"])
    thoughts, context = RefinementThoughtService(db), RefinementContextService(db)

    # ATTACH
    thought = _thought(thoughts, "verbs")
    attached = context.attach_context(OWNER, thought["id"], visible_ref="note:promoted",
                                      request_id="v-attach", **_cursors(thought))
    assert [r["canonical_ref"] for r in _rows_for(db, thought["id"])] == ["note:promoted"]

    # DETACH
    context.detach_context(OWNER, thought["id"], visible_ref="note:promoted",
                           request_id="v-detach", **_cursors(attached["thought"]))
    assert _rows_for(db, thought["id"]) == []

    # BIRTH -- the default context is applied at creation, never by an attach.
    context.replace_default_context(OWNER, refs=["note:promoted"],
                                    request_id="v-default", expected_revision=0)
    born = _thought(thoughts, "born")
    rows = _rows_for(db, born["id"])
    assert [r["canonical_ref"] for r in rows] == ["note:promoted"]
    assert rows[0]["consumer_revision"] == born["attachment_revision"] == 1
    assert rows[0]["bound_manifest_sha256"] == born["attachment_sha256"]


def test_a_container_indexes_its_leaves_as_well_as_the_visible(rig) -> None:
    """Visible UNION leaf, deduped -- because a container's hash covers members.

    A `knowledge:` visible's `visible_sha256` folds in its members' metadata
    hashes, so a correction to a MEMBER note must reach the consumer.  The
    trigger fires on `note:` refs, so the member has to be in the index under
    its own ref or the correction is invisible to the reverse question.
    """
    db, thoughts, context = rig
    db.kbs.upsert(kb_id=EVERYDAY_ID, name="Everyday context",
                  member_ids=["note:control"], last_modified="2026-09-07T09:00:00Z")
    thought = _thought(thoughts, "kb")
    context.attach_context(OWNER, thought["id"], visible_ref=EVERYDAY_CONTEXT_REF,
                           request_id="attach-kb", **_cursors(thought))

    assert [r["canonical_ref"] for r in _rows_for(db, thought["id"])] == [
        EVERYDAY_CONTEXT_REF, "note:control"]

    db.notes.upsert(note_id="control", title="Cutover notes",
                    body_markdown="Rewritten.", tags=["today"],
                    last_modified="2026-09-08T09:00:00Z")
    marked = {r["canonical_ref"]: r["stale_reason"] for r in _rows_for(db, thought["id"])}
    assert marked == {EVERYDAY_CONTEXT_REF: "", "note:control": "stale"}


def test_the_index_is_one_row_per_consumer_never_one_per_revision(rig) -> None:
    """The reason this table exists.  Revisions are never pruned; rows are."""
    db, thoughts, context = rig
    thought = _thought(thoughts, "rev")
    current = thought
    for i in range(4):
        ref = "note:promoted" if i % 2 == 0 else "note:control"
        current = context.attach_context(OWNER, thought["id"], visible_ref=ref,
                                         request_id=f"churn-{i}",
                                         **_cursors(current))["thought"]
        # Exactly ONE row after every attach, however many revisions exist.
        assert [r["canonical_ref"] for r in _rows_for(db, thought["id"])] == [ref]
        current = context.detach_context(OWNER, thought["id"], visible_ref=ref,
                                         request_id=f"churn-off-{i}",
                                         **_cursors(current))["thought"]
        assert _rows_for(db, thought["id"]) == []
    with db._connection() as conn:
        revisions = conn.execute(
            "SELECT count(*) FROM refinement_attachment_revisions WHERE thought_id=?",
            (thought["id"],)).fetchone()[0]
    assert revisions >= 8, revisions
    assert _rows_for(db, thought["id"]) == []


def test_concurrent_edit_and_attach_leave_one_consistent_index(rig) -> None:
    """Two `BEGIN IMMEDIATE` writers, one consistent index.

    The attach opens the write transaction; the correction has to wait for it.
    Either order is lawful, but the index may not end up describing a manifest
    that never existed, and a lost mark would be the breach.
    """
    db, thoughts, context = rig
    thought = _thought(thoughts, "race")
    errors: list[BaseException] = []
    start = threading.Barrier(2)

    def _attach() -> None:
        try:
            start.wait(timeout=5)
            context.attach_context(OWNER, thought["id"], visible_ref="note:promoted",
                                   request_id="race-attach", **_cursors(thought))
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)

    def _edit() -> None:
        try:
            start.wait(timeout=5)
            db.notes.upsert(note_id="promoted", title="Softened",
                            body_markdown="Unless reversible in five minutes.",
                            tags=["constraint"], last_modified="2026-09-08T09:00:00Z")
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)

    workers = [threading.Thread(target=_attach), threading.Thread(target=_edit)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=30)
    assert not errors, errors

    rows = _rows_for(db, thought["id"])
    assert [r["canonical_ref"] for r in rows] == ["note:promoted"]
    # Exactly one row, and its bound hash is a manifest that really existed.
    current = thoughts.get(OWNER, thought["id"])
    assert rows[0]["bound_manifest_sha256"] == current["attachment_sha256"]
    # Whichever order won, the two records agree about whether it moved.
    pull_state = current["attachments"][0]["state"]
    index_state = rows[0]["stale_reason"]
    assert (pull_state, index_state) in {("current", ""), ("stale", "stale")}, \
        (pull_state, index_state)


def test_promotion_writes_no_dependent_row(rig) -> None:
    """The failure window that cannot exist.

    "Death between the record write and the index write" has no torn state to
    recover, because **a promotion writes no `context_dependents` row at all**:
    it never attaches.  Attachment stays his own separate verb.
    """
    db, _thoughts, _context = rig
    _promote_new_note(db, "second", "Another constraint", "Body two.",
                      fact_id="fact-2")
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM context_promotions").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM context_dependents").fetchone()[0] == 0


def test_promotion_and_its_dependents_survive_restart(tmp_path: Path) -> None:
    """Reopen the file: rows, marks and the first staleness time all persist."""
    path = tmp_path / "restart.db"
    db = Database(path)
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    _promote_new_note(db, "promoted", "Rollback rehearsal", CONSTRAINT, tags=["c"])
    thoughts, context = RefinementThoughtService(db), RefinementContextService(db)
    thought = _thought(thoughts, "restart")
    context.attach_context(OWNER, thought["id"], visible_ref="note:promoted",
                           request_id="restart-attach", **_cursors(thought))
    db.notes.upsert(note_id="promoted", title="Softened", body_markdown="Moved.",
                    tags=["c"], last_modified="2026-09-08T09:00:00Z")
    before = _dependents(db, "note:promoted")

    reopened = Database(path)
    after = _dependents(reopened, "note:promoted")
    assert after == before
    assert after[0]["stale_reason"] == "stale" and after[0]["stale_since"]
    with reopened._connection() as conn:
        assert conn.execute("SELECT count(*) FROM context_promotions").fetchone()[0] == 1


# ── the backfill, beside the INSERT it must agree with ───────────────────


def test_the_backfill_agrees_with_the_reconcile_point_and_is_idempotent(rig) -> None:
    """The seed's shape must agree byte-for-byte with `_persist_manifest`.

    It does, because it CALLS it.  This test drops the index out from under a
    live Thought -- the shape an older database is in -- re-seeds, and compares
    every column but `bound_at`.
    """
    db, thoughts, context = rig
    working = _thought(thoughts, "backfill")
    context.attach_context(OWNER, working["id"], visible_ref="note:promoted",
                           request_id="backfill-attach", **_cursors(working))
    completed = _thought(thoughts, "done")
    context.attach_context(OWNER, completed["id"], visible_ref="note:control",
                           request_id="backfill-done", **_cursors(completed))
    expected = _rows_for(db, working["id"])
    assert expected

    with db._connection() as conn:
        conn.execute("DELETE FROM context_dependents")
        # Only `working` Thoughts are seeded: a completed Thought consumes
        # nothing a correction must fence.
        conn.execute("UPDATE refinement_thoughts SET state='completed' WHERE id=?",
                     (completed["id"],))
        written = RefinementContextService.backfill_dependents_in_transaction(conn)
    assert written == len(expected)

    seeded = _rows_for(db, working["id"])
    assert _rows_for(db, completed["id"]) == []
    for got, want in zip(seeded, expected, strict=True):
        assert {k: v for k, v in got.items() if k != "bound_at"} == \
               {k: v for k, v in want.items() if k != "bound_at"}

    # Idempotent: a second reconcile writes nothing and disturbs nothing.
    with db._connection() as conn:
        assert RefinementContextService.backfill_dependents_in_transaction(conn) == 0
    assert _rows_for(db, working["id"]) == seeded


def test_the_backfill_never_clears_a_forbidden_mark(rig) -> None:
    db, thoughts, context = rig
    thought = _thought(thoughts, "backfill-forbid")
    context.attach_context(OWNER, thought["id"], visible_ref="note:promoted",
                           request_id="bf-attach", **_cursors(thought))
    with db._connection() as conn:
        conn.execute("UPDATE context_dependents SET stale_reason='forbidden',"
                     " stale_since='2026-01-01T00:00:00'")
        # Force the seed to consider this Thought again.
        RefinementContextService._reconcile_dependents(
            conn, thought["id"],
            {"revision": 1, "attachment_sha256": "x",
             "visible": [{"ref": "note:promoted", "leaves": []}]},
            "2026-09-09T00:00:00Z")
    row = _rows_for(db, thought["id"])[0]
    assert row["stale_reason"] == "forbidden"
    assert row["stale_since"] == "2026-01-01T00:00:00"


def test_an_empty_desk_backfills_zero_rows(tmp_path: Path) -> None:
    """Measured on his live database 2026-09-07: 8 Thoughts, 0 working."""
    db = Database(tmp_path / "empty.db")
    with db._connection() as conn:
        assert RefinementContextService.backfill_dependents_in_transaction(conn) == 0


# ── L4: the frozen-ref replay is fenced; the receipt is not ──────────────


def _thread_service(db: Database) -> ThreadService:
    return ThreadService(db, broadcast=lambda *_: None, broker=_FakeBroker())


class _FakeAdoption:
    def admit(self, principal, *, command_id, capability_id, operation_id,
              payload, invocation_id, reserved_output_tokens=512):
        _FakeBroker.last_payload = payload
        return {"execution": {"id": "exec_" + uuid.uuid4().hex[:8]},
                "route_plan": {"id": "rp_test", "egress_scope": "same_device",
                               "model_id": "test-model"},
                "operation_request_plan": {"id": "orp_test"}}

    def execute_stream(self, principal, *, execution_id, adapter, on_delta,
                       publish=None, payload_redactor=None):
        from holdspeak.kernel.inference_stream import Delta
        on_delta(Delta(kind="text", text="ok"))
        on_delta(Delta(kind="usage", meta={"prompt_tokens": 1, "completion_tokens": 1}))
        on_delta(Delta(kind="done"))
        return {"outcome": "succeeded", "result": {"output": "ok"},
                "receipt": {"id": "receipt_test", "outcome": "succeeded"}}


class _FakeBroker:
    """Captures the payload the model would actually have received."""
    last_payload: Any = None

    @property
    def inference_adoption_service(self) -> _FakeAdoption:
        return _FakeAdoption()


def _frozen_texts(db: Database, thread_id: str) -> list[str]:
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT frozen_json FROM thread_refs WHERE thread_id=?", (thread_id,)
        ).fetchall()
    return [json.loads(str(row[0])).get("text", "") for row in rows if row[0]]


def _system_text(payload: dict[str, Any]) -> str:
    return "\n\n".join(m["content"] for m in payload["messages"]
                       if m["role"] == "system")


def test_a_frozen_thread_ref_never_carries_a_promoted_body(tmp_path: Path) -> None:
    """The cached projection the design's first draft never checked.

    `thread_service.start_turn` is the ONLY call site that PERSISTS what the
    relevance pass returned -- whole note bodies into `thread_refs.frozen_json`
    with `"sensitive": False`, so the sensitivity redaction in
    `_assemble_payload` can never redact them.  Drives the real turn.
    """
    db = Database(tmp_path / "freeze.db")
    db.notes.upsert(note_id="control", title="Cutover notes",
                    body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}",
                    last_modified="2026-09-07T09:00:00Z")
    _promote_new_note(db, "promoted", "Rollback rehearsal",
                      f"{CONSTRAINT} {PROMOTED_TOKEN}")

    service = _thread_service(db)
    thread = service.create(title="Plain chat")
    asyncio.run(service.start_turn(OWNER, thread["id"], QUERY))
    time.sleep(0.5)

    texts = _frozen_texts(db, thread["id"])
    # The pass RAN and the control was frozen -- otherwise this proves nothing.
    assert any(CONTROL_TOKEN in text for text in texts), texts
    assert not any(PROMOTED_TOKEN in text for text in texts), texts


def test_a_frozen_thread_ref_predating_the_promotion_is_not_replayed(
    tmp_path: Path,
) -> None:
    """L4, through the real assembly path.

    A relevance block frozen BEFORE the promotion is a durable row that
    `_assemble_payload` re-gathers and re-appends into a `system` message on
    EVERY subsequent turn.  Receipts are immutable; replays are fenced -- so
    the body must be absent from the assembled payload **while the
    `thread_refs` row still exists**.
    """
    db = Database(tmp_path / "replay.db")
    db.notes.upsert(note_id="control", title="Cutover notes",
                    body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}",
                    last_modified="2026-09-07T09:00:00Z")
    db.notes.upsert(note_id="promoted", title="Rollback rehearsal",
                    body_markdown=f"{CONSTRAINT} {PROMOTED_TOKEN}",
                    last_modified="2026-09-07T09:00:00Z")

    service = _thread_service(db)
    thread = service.create(title="Pre-promotion")
    asyncio.run(service.start_turn(OWNER, thread["id"], QUERY))
    time.sleep(0.5)

    frozen = _frozen_texts(db, thread["id"])
    assert any(PROMOTED_TOKEN in text for text in frozen), frozen
    assert any(CONTROL_TOKEN in text for text in frozen), frozen

    # ... and only NOW is the sentence promoted.
    with db._connection() as conn:
        _insert_promotion(conn, "note:promoted")
        conn.execute("DELETE FROM notes_memory_fts WHERE source_id='promoted'")

    last = db.threads.list_path(thread["id"])[-1]
    payload = service._assemble_payload(thread["id"], last.id,
                                        db.threads.get(thread["id"]))
    system = _system_text(payload)
    # The control still replays -- the fence is not simply breaking grounding.
    assert CONTROL_TOKEN in system
    # The promoted body does not.
    assert PROMOTED_TOKEN not in system
    # THE RECEIPT IS INTACT.  Rewriting it would falsify what turn 1 saw.
    assert any(PROMOTED_TOKEN in text for text in _frozen_texts(db, thread["id"]))


def test_the_replay_fence_keys_on_existence_so_a_revocation_cannot_reopen_it(
    tmp_path: Path,
) -> None:
    """A revocation must never re-open a surface promotion had closed."""
    db = Database(tmp_path / "replay-revoked.db")
    db.notes.upsert(note_id="control", title="Cutover notes",
                    body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}",
                    last_modified="2026-09-07T09:00:00Z")
    db.notes.upsert(note_id="promoted", title="Rollback rehearsal",
                    body_markdown=f"{CONSTRAINT} {PROMOTED_TOKEN}",
                    last_modified="2026-09-07T09:00:00Z")
    service = _thread_service(db)
    thread = service.create(title="Revoked")
    asyncio.run(service.start_turn(OWNER, thread["id"], QUERY))
    time.sleep(0.5)
    with db._connection() as conn:
        _insert_promotion(conn, "note:promoted", disclosure_state="revoked")

    last = db.threads.list_path(thread["id"])[-1]
    system = _system_text(service._assemble_payload(
        thread["id"], last.id, db.threads.get(thread["id"])))
    assert CONTROL_TOKEN in system
    assert PROMOTED_TOKEN not in system


def test_an_explicitly_attached_note_still_reaches_the_model(tmp_path: Path) -> None:
    """Reachable BY REFERENCE.  The fence is on relevance, not on the owner.

    This is the positive control for L4 as a whole: if the replay fence were
    keyed on the ref rather than on how it got there, attaching a promoted Note
    on purpose would silently stop working -- silent loss of accepted input.
    """
    db = Database(tmp_path / "by-reference.db")
    _promote_new_note(db, "promoted", "Rollback rehearsal",
                      f"{CONSTRAINT} {PROMOTED_TOKEN}")
    service = _thread_service(db)
    thread = service.create(title="Explicit")
    asyncio.run(service.start_turn(OWNER, thread["id"], "What does this mean?",
                                   refs=["note:promoted"]))
    time.sleep(0.5)
    frozen = _frozen_texts(db, thread["id"])
    assert any(PROMOTED_TOKEN in text for text in frozen), frozen
    # And it REPLAYS: the row was frozen after the promotion, so it can only
    # have arrived by reference, and by reference is exactly how a promoted
    # record is meant to be reachable.
    last = db.threads.list_path(thread["id"])[-1]
    system = _system_text(service._assemble_payload(
        thread["id"], last.id, db.threads.get(thread["id"])))
    assert PROMOTED_TOKEN in system


# ── P0-C: the fence travels with the record ──────────────────────────────
#
# "The one P0 whose failure he could actually meet", because everything else
# in this story starts empty on his machine.  F0/L1 is construction ON THE
# WRITING DEVICE ONLY.  `notes` is a synced content class today; without its
# promotion riding beside it, the note INSERT on device B fires
# `notes_memory_ai`, the guard's `NOT EXISTS` finds nothing, and the body
# enters THAT device's relevance pool -- the pre-bounce state, one device over.


def _device(tmp_path: Path, name: str) -> Database:
    return Database(tmp_path / f"{name}.db")


def _fts_ids(db: Database) -> set[str]:
    with db._connection() as conn:
        return {str(row[0]) for row in
                conn.execute("SELECT source_id FROM notes_memory_fts")}


def _promotions(db: Database) -> dict[str, dict[str, Any]]:
    with db._connection() as conn:
        return {str(row["promotion_id"]): dict(row) for row in
                conn.execute("SELECT * FROM context_promotions")}


def _sender(tmp_path: Path) -> Database:
    """Device A: one ordinary note, one promoted note."""
    a = _device(tmp_path, "device-a")
    a.notes.upsert(note_id="control", title="Cutover notes",
                   body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}",
                   last_modified="2026-09-07T09:00:00Z")
    _promote_new_note(a, "promoted", "Rollback rehearsal",
                      f"{CONSTRAINT} {PROMOTED_TOKEN}")
    assert _fts_ids(a) == {"control"}, "device A's own fence is not working"
    return a


def test_the_promotion_spec_is_registered_before_the_note_spec() -> None:
    """Registry order IS apply order: `push` iterates the tuple."""
    from holdspeak.services.sync_service import SYNC_REGISTRY
    buckets = [spec.bucket for spec in SYNC_REGISTRY]
    assert "context_promotions" in buckets
    assert buckets.index("context_promotions") < buckets.index("notes")
    spec = next(s for s in SYNC_REGISTRY if s.bucket == "context_promotions")
    assert spec.merger is not None
    # NOT the last-write-wins primitive merge: `revoked` is a monotone join.
    from holdspeak.services.sync_service import _merge_primitive_spec
    assert spec.merger is not _merge_primitive_spec


def test_a_promoted_body_does_not_enter_the_receiving_devices_corpus(
    tmp_path: Path,
) -> None:
    """The real two-device path: A.pull() -> B.push()."""
    from holdspeak.services.sync_service import SyncService
    a, b = _sender(tmp_path), _device(tmp_path, "device-b")

    body = SyncService(a).pull(OWNER)
    assert body["context_promotions"], "the promotion did not ride the wire"
    SyncService(b).push(OWNER, body)

    # Both notes arrived: sync is not broken, only fenced.
    assert {n.id for n in b.notes.list(include_deleted=True)} >= {"control", "promoted"}
    assert b.notes.get("promoted").body_markdown.endswith(PROMOTED_TOKEN)
    # The promotion arrived with it.
    assert len(_promotions(b)) == 1
    # And the body is NOT in device B's relevance corpus.  The control IS.
    assert _fts_ids(b) == {"control"}

    # The fence self-heals from here: the guarded `notes_memory_au` declines
    # to re-insert on every later write, and a full rebuild cannot re-admit it.
    b.notes.upsert(note_id="promoted", title="Rollback rehearsal",
                   body_markdown=f"{CONSTRAINT} {PROMOTED_TOKEN} edited",
                   last_modified="2026-09-10T09:00:00Z")
    assert _fts_ids(b) == {"control"}
    with b._connection() as conn:
        rebuild_memory_index(conn)
    assert _fts_ids(b) == {"control"}


def test_the_post_apply_sweep_repairs_a_note_that_landed_first(
    tmp_path: Path,
) -> None:
    """The ordering does NOT have to hold -- and here it deliberately does not.

    Two pushes: the note bucket alone, then the promotion bucket.  The note
    lands with no promotion row in sight, so `notes_memory_ai` indexes it and
    device B's corpus carries the promoted body.  The post-apply sweep is what
    repairs it, and this is the case that proves correctness does not rest on
    registry order.
    """
    from holdspeak.services.sync_service import SyncService
    a, b = _sender(tmp_path), _device(tmp_path, "device-b")
    body = SyncService(a).pull(OWNER)

    SyncService(b).push(OWNER, {"notes": body["notes"]})
    assert _fts_ids(b) == {"control", "promoted"}, "the hazard did not reproduce"

    SyncService(b).push(OWNER, {"context_promotions": body["context_promotions"]})
    assert _fts_ids(b) == {"control"}


def test_the_sweep_holds_when_the_registry_order_is_reversed(
    tmp_path: Path, monkeypatch,
) -> None:
    """The same push, with notes applied BEFORE promotions inside one call."""
    from holdspeak.services import sync_service as module
    a, b = _sender(tmp_path), _device(tmp_path, "device-b")
    body = module.SyncService(a).pull(OWNER)

    reordered = sorted(
        module.SYNC_REGISTRY,
        key=lambda spec: 0 if spec.bucket == "notes"
        else (1 if spec.bucket == "context_promotions" else 2))
    assert [s.bucket for s in reordered][:2] == ["notes", "context_promotions"]
    monkeypatch.setattr(module, "SYNC_REGISTRY", tuple(reordered))

    module.SyncService(b).push(OWNER, body)
    assert _fts_ids(b) == {"control"}


def test_a_revoked_promotion_wins_over_an_active_one_in_a_merge(
    tmp_path: Path,
) -> None:
    """The monotone join, in BOTH directions and against the clock.

    `active -> revoked` is a one-way transition, so this is a join and not a
    race.  Under last-write-wins a stale device still holding `active` could
    UN-REVOKE a revocation the owner made on his laptop.
    """
    from holdspeak.services.sync_service import SyncService

    # Direction 1: incoming `revoked` with an OLDER clock beats local `active`.
    b = _device(tmp_path, "merge-1")
    with b._connection() as conn:
        _insert_promotion(conn, "note:promoted", promotion_id="cp1",
                          disclosure_state="active",
                          updated_at="2026-09-09T09:00:00Z")
    incoming = {"context_promotions": [{
        "meta": {"id": "cp1", "kind": "context_promotion",
                 "last_modified": "2026-01-01T00:00:00Z", "deleted": False},
        "value": {"promotion_id": "cp1", "thread_id": "thread-interview",
                  "fact_id": "fact-1", "source_message_id": "msg-1",
                  "quote_sha256": "sha256:quote", "quote_locator_json": "{}",
                  "target_kind": "note", "target_ref": "note:promoted",
                  "target_revision_label": "", "target_content_sha256": "",
                  "disclosure_state": "revoked", "request_sha256": "r",
                  "created_at": "2026-01-01T00:00:00Z",
                  "updated_at": "2026-01-01T00:00:00Z"},
    }]}
    SyncService(b).push(OWNER, incoming)
    assert _promotions(b)["cp1"]["disclosure_state"] == "revoked"
    # The OLDER incoming row did not overwrite the newer non-state fields.
    assert _promotions(b)["cp1"]["updated_at"] == "2026-09-09T09:00:00Z"

    # Direction 2: local `revoked` survives a NEWER incoming `active`.
    c = _device(tmp_path, "merge-2")
    with c._connection() as conn:
        _insert_promotion(conn, "note:promoted", promotion_id="cp1",
                          disclosure_state="revoked",
                          updated_at="2026-01-01T00:00:00Z")
    newer = json.loads(json.dumps(incoming))
    newer["context_promotions"][0]["value"]["disclosure_state"] = "active"
    newer["context_promotions"][0]["value"]["updated_at"] = "2026-12-31T23:59:59Z"
    newer["context_promotions"][0]["meta"]["last_modified"] = "2026-12-31T23:59:59Z"
    SyncService(c).push(OWNER, newer)
    assert _promotions(c)["cp1"]["disclosure_state"] == "revoked"
    # The newer row's ordinary fields DID land -- only the state is a join.
    assert _promotions(c)["cp1"]["updated_at"] == "2026-12-31T23:59:59Z"


def test_sync_never_tombstones_a_promotion_row(tmp_path: Path) -> None:
    """A tombstone would be an un-revoke by another name."""
    from holdspeak.services.sync_service import SyncService
    b = _device(tmp_path, "tombstone")
    with b._connection() as conn:
        _insert_promotion(conn, "note:promoted", promotion_id="cp1")
    before = _promotions(b)["cp1"]
    # A bare tombstone, and -- the path a validity guard would otherwise cover
    # for the wrong reason -- a tombstone carrying a COMPLETE value.
    full = {"promotion_id": "cp1", "thread_id": "thread-interview",
            "fact_id": "fact-1", "source_message_id": "msg-1",
            "quote_sha256": "sha256:quote", "quote_locator_json": "{}",
            "target_kind": "note", "target_ref": "note:promoted",
            "target_revision_label": "", "target_content_sha256": "",
            "disclosure_state": "active", "request_sha256": "r",
            "created_at": "2026-12-31T23:59:59Z",
            "updated_at": "2026-12-31T23:59:59Z"}
    for value in (None, full):
        SyncService(b).push(OWNER, {"context_promotions": [{
            "meta": {"id": "cp1", "kind": "context_promotion",
                     "last_modified": "2026-12-31T23:59:59Z", "deleted": True},
            "value": value,
        }]})
        assert list(_promotions(b)) == ["cp1"]
        assert _promotions(b)["cp1"] == before
    # And the hub never EMITS a promotion tombstone either.
    b.notes.upsert(note_id="promoted", title="t", body_markdown="b")
    b.notes.delete("promoted")
    emitted = SyncService(b).pull(OWNER)["context_promotions"]
    assert emitted and all(not rec["meta"]["deleted"] for rec in emitted)
    assert all(rec["value"]["deleted"] is False for rec in emitted)


def test_desk_snapshot_and_sync_pull_still_carry_the_body(tmp_path: Path) -> None:
    """CONTRACTS.md "export": the boundary's TRUE shape, recorded honestly.

    This asserts the KNOWN, DECLARED egress rather than a false negative.
    `SyncService.pull` and `desk.snapshot` DO carry a promoted body, by design
    -- blocking sync would break synchronisation of the owner's own record, and
    that exposure predates this story and covers every note he has ever
    written.  F0 fences RELEVANCE.  It does not close whole-table egress, and
    this design does not pretend to.
    """
    from holdspeak.services.desk_service import DeskService
    from holdspeak.services.sync_service import SyncService
    a = _sender(tmp_path)

    pulled = SyncService(a).pull(OWNER)
    bodies = [rec["value"]["body_markdown"] for rec in pulled["notes"]
              if rec["value"]]
    assert any(PROMOTED_TOKEN in body for body in bodies), \
        "sync.pull's declared egress changed shape -- re-read the boundary"

    snapshot = DeskService(a).snapshot(OWNER)
    assert PROMOTED_TOKEN in json.dumps(snapshot), \
        "desk.snapshot's declared egress changed shape -- re-read the boundary"


def test_reconcile_actually_calls_the_backfill(rig) -> None:
    """HS-200-10: the seed is WIRED, not merely written.

    `backfill_dependents_in_transaction` shipped built, tested and never called;
    a reverse index that is only seeded in its own unit test is blind to every
    consumer that predates the table on a real desk. This drives
    `reconcile_schema` -- the real entry point every database opening runs --
    rather than the backfill helper, so it fails if the call site in
    `db/reconcile.py` is removed. Deleting the rows first is exactly the shape
    an older database arrives in.
    """
    from holdspeak.db.reconcile import reconcile_schema

    db, thoughts, context = rig
    working = _thought(thoughts, "wired")
    context.attach_context(OWNER, working["id"], visible_ref="note:promoted",
                           request_id="wired-attach", **_cursors(working))
    expected = _rows_for(db, working["id"])
    assert expected, "the attach wrote no dependent rows; the rig is wrong"

    with db._connection() as conn:
        conn.execute("DELETE FROM context_dependents")
    assert _rows_for(db, working["id"]) == []

    with db._connection() as conn:
        reconcile_schema(conn)

    seeded = _rows_for(db, working["id"])
    assert len(seeded) == len(expected), (
        "reconcile_schema left the reverse index empty — the backfill is built "
        "but not called, so every consumer predating the table stays invisible "
        "to a correction"
    )
