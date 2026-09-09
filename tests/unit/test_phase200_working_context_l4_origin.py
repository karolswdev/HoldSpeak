"""HS-200-10 P0-1: the L4 replay fence reads the ORIGIN, never a clock.

Ruling B1 keyed the frozen-ref replay fence on TIME.  A `thread_refs` row
frozen AFTER a promotion's `created_at` was kept, on the argument that L1/L2/L3
already keep a promoted record out of every relevance result, so anything
frozen after the promotion could only have arrived BY REFERENCE.

**That premise holds only on the device that recorded the promotion, and the
same commit made promotions cross-device.**  No clock skew is required:

  1. He promotes on the laptop.  `context_promotions.created_at` is that
     laptop's wall clock (`interview_service.py:493-501`).
  2. The desktop has not synced.  Its FTS corpus is unfenced -- exactly the
     hazard `sync_service.py:38-52` exists for.
  3. A turn on the desktop runs the RELEVANCE pass, which returns the promoted
     note and freezes the whole body into `thread_refs.frozen_json` with
     `"sensitive": False` (`thread_service.py:376-420`).
  4. Sync lands.  `_sweep_promoted_from_corpus` (`sync_service.py:672-700`)
     repairs the corpus and does **not** touch `thread_refs`.
  5. Every later turn: the frozen row's LOCAL `created_at` is later than the
     promotion's REMOTE one, the time fence keeps it, and the pre-promotion
     body replays to the model forever on that device.

The fix records HOW the ref arrived at the moment it is frozen, and the fence
reads that stamp.  `thread_refs.origin` is an ALLOW-LIST of one value:
`'reference'` replays, `'relevance'` and `''` (unknown -- every row written
before the column existed) fence.

THE LAW THIS PHASE PAID FOR (`reference_lying_test_doubles`): a test that
cannot fail on the real path is not proof.  So every test here drives the REAL
turn through `ThreadService.start_turn` and the REAL assembly through
`_assemble_payload`, asserts on the BYTES the model would have received, and
carries a POSITIVE CONTROL -- an unpromoted note that IS retrieved, and a
promoted note attached BY REFERENCE that IS delivered -- so a fence that
over-reaches fails as loudly as one that is missing.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_service import ThreadService


OWNER = Principal(PrincipalKind.OWNER, "l4-origin-owner")

CONSTRAINT = (
    "We cannot take another cutover without a rollback rehearsal. "
    "That is not negotiable."
)
PROMOTED_TOKEN = "kestrelmark"
CONTROL_TOKEN = "wrenmark"
QUERY = "cutover rollback rehearsal"


# ── rig ──────────────────────────────────────────────────────────────────


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
    last_payload: Any = None

    @property
    def inference_adoption_service(self) -> _FakeAdoption:
        return _FakeAdoption()


def _thread_service(db: Database) -> ThreadService:
    return ThreadService(db, broadcast=lambda *_: None, broker=_FakeBroker())


def _insert_promotion(
    conn: sqlite3.Connection,
    target_ref: str,
    *,
    created_at: str,
    promotion_id: str = "cp-1",
    disclosure_state: str = "active",
) -> None:
    """One `context_promotions` row, every column named.

    `created_at` is explicit in every call here: it is the field the broken
    fence read, so no test may take it by default.
    """
    conn.execute(
        """INSERT INTO context_promotions(
               promotion_id, thread_id, fact_id, source_message_id,
               quote_sha256, quote_locator_json, target_kind, target_ref,
               target_revision_label, target_content_sha256,
               disclosure_state, request_sha256, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (promotion_id, "thread-interview", "fact-1", "msg-1",
         "sha256:quote", '{"part_ordinal": 0}', "note", target_ref,
         "2026-09-07T09:00:00Z", "", disclosure_state, "sha256:request",
         created_at, created_at),
    )


def _seed_two_notes(db: Database) -> None:
    """The promoted sentence and the positive control, both unpromoted yet."""
    db.notes.upsert(note_id="control", title="Cutover notes",
                    body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}",
                    last_modified="2026-09-07T09:00:00Z")
    db.notes.upsert(note_id="promoted", title="Rollback rehearsal",
                    body_markdown=f"{CONSTRAINT} {PROMOTED_TOKEN}",
                    last_modified="2026-09-07T09:00:00Z")


def _frozen_texts(db: Database, thread_id: str) -> list[str]:
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT frozen_json FROM thread_refs WHERE thread_id=?", (thread_id,)
        ).fetchall()
    return [json.loads(str(row[0])).get("text", "") for row in rows if row[0]]


def _origins(db: Database, thread_id: str) -> dict[str, str]:
    """ref_id -> origin, straight off the receipt table."""
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT ref_id, origin FROM thread_refs WHERE thread_id=?",
            (thread_id,),
        ).fetchall()
    return {str(row[0]): str(row[1] or "") for row in rows}


def _system_text(payload: dict[str, Any]) -> str:
    return "\n\n".join(m["content"] for m in payload["messages"]
                       if m["role"] == "system")


def _replay(service: ThreadService, db: Database, thread_id: str) -> str:
    last = db.threads.list_path(thread_id)[-1]
    return _system_text(service._assemble_payload(
        thread_id, last.id, db.threads.get(thread_id)))


def _run_relevance_turn(service: ThreadService, thread_id: str) -> None:
    asyncio.run(service.start_turn(OWNER, thread_id, QUERY))
    time.sleep(0.5)


# ── the defect ───────────────────────────────────────────────────────────


def test_a_relevance_body_frozen_before_a_promotion_synced_in_never_replays(
    tmp_path: Path,
) -> None:
    """THE CROSS-DEVICE REPRODUCTION.  Fails against the time-keyed fence.

    This is the desktop of the scenario in the module docstring.  Its
    `thread_refs` row is frozen at LOCAL now; the promotion that arrives on the
    next sync carries the laptop's EARLIER wall clock.  Under the time fence
    `now >= 09:00` reads as "arrived by reference" and the body replays
    forever.  Under the origin fence the row says `'relevance'` and it does
    not.

    The FTS row is deleted after the freeze, standing in for
    `_sweep_promoted_from_corpus` (`sync_service.py:672-700`), which repairs
    the corpus and leaves `thread_refs` alone -- the whole reason the replay is
    a separate fence.
    """
    db = Database(tmp_path / "desktop.db")
    _seed_two_notes(db)

    service = _thread_service(db)
    thread = service.create(title="Desktop, pre-sync")
    _run_relevance_turn(service, thread["id"])

    frozen = _frozen_texts(db, thread["id"])
    # The relevance pass RAN and froze BOTH bodies.  Without this the rest of
    # the test would pass on an empty context.
    assert any(PROMOTED_TOKEN in text for text in frozen), frozen
    assert any(CONTROL_TOKEN in text for text in frozen), frozen

    # ── sync lands: the promotion arrives carrying the LAPTOP's clock, which
    # is EARLIER than this device's freeze, and the corpus is swept.
    with db._connection() as conn:
        _insert_promotion(conn, "note:promoted", created_at="2026-09-07T09:00:00Z")
        conn.execute("DELETE FROM notes_memory_fts WHERE source_id='promoted'")

    system = _replay(service, db, thread["id"])
    # POSITIVE CONTROL: the unpromoted note still replays.  A fence that broke
    # grounding outright would pass the next assertion for the wrong reason.
    assert CONTROL_TOKEN in system, system
    assert PROMOTED_TOKEN not in system, system
    # THE RECEIPT IS INTACT.  Only the replay is fenced; rewriting the row
    # would falsify what turn 1 actually saw.
    assert any(PROMOTED_TOKEN in text for text in _frozen_texts(db, thread["id"]))


def test_the_fence_does_not_consult_a_clock_at_all(tmp_path: Path) -> None:
    """The same desktop, with the promotion's clock set to the far FUTURE.

    Both directions of skew must land on the same answer, because the answer
    does not come from a clock.  Paired with the test above, this pins that
    `created_at` is no longer read: one run has the promotion before the
    freeze, the other after, and the fenced outcome is identical.
    """
    db = Database(tmp_path / "future-clock.db")
    _seed_two_notes(db)
    service = _thread_service(db)
    thread = service.create(title="Skewed forward")
    _run_relevance_turn(service, thread["id"])

    with db._connection() as conn:
        _insert_promotion(conn, "note:promoted", created_at="2099-01-01T00:00:00Z")
        conn.execute("DELETE FROM notes_memory_fts WHERE source_id='promoted'")

    system = _replay(service, db, thread["id"])
    assert CONTROL_TOKEN in system, system
    assert PROMOTED_TOKEN not in system, system


def test_an_unparseable_promotion_clock_changes_nothing(tmp_path: Path) -> None:
    """A garbage timestamp used to be the fail-closed special case.

    It is now simply not read.  The fence still holds, and the control still
    replays -- so the fence did not fall back to "fence everything".
    """
    db = Database(tmp_path / "bad-clock.db")
    _seed_two_notes(db)
    service = _thread_service(db)
    thread = service.create(title="Garbage clock")
    _run_relevance_turn(service, thread["id"])

    with db._connection() as conn:
        _insert_promotion(conn, "note:promoted", created_at="not-a-timestamp")
        conn.execute("DELETE FROM notes_memory_fts WHERE source_id='promoted'")

    system = _replay(service, db, thread["id"])
    assert CONTROL_TOKEN in system, system
    assert PROMOTED_TOKEN not in system, system


# ── C2': reachable by reference ──────────────────────────────────────────


def test_a_promoted_note_attached_by_reference_still_reaches_the_model(
    tmp_path: Path,
) -> None:
    """THE POSITIVE CONTROL FOR THE WHOLE FIX.

    C2' promises a promoted record stays reachable by an explicit ref.  A
    blanket ref-keyed fence -- "drop every promoted note" -- would pass every
    test above and silently lose accepted input.  This is the test that
    refuses it.

    The promotion's clock is set LATER than the attach, the shape the old time
    fence would have dropped, so this also proves the new fence keeps a
    by-reference ref that the old one would have fenced.
    """
    db = Database(tmp_path / "by-reference.db")
    with db._connection() as conn:
        _insert_promotion(conn, "note:promoted", created_at="2099-01-01T00:00:00Z")
    db.notes.upsert(note_id="promoted", title="Rollback rehearsal",
                    body_markdown=f"{CONSTRAINT} {PROMOTED_TOKEN}",
                    last_modified="2026-09-07T09:00:00Z")

    service = _thread_service(db)
    thread = service.create(title="Explicit attach")
    asyncio.run(service.start_turn(OWNER, thread["id"], "What does this mean?",
                                   refs=["note:promoted"]))
    time.sleep(0.5)

    frozen = _frozen_texts(db, thread["id"])
    assert any(PROMOTED_TOKEN in text for text in frozen), frozen
    assert _origins(db, thread["id"])["promoted"] == "reference"

    system = _replay(service, db, thread["id"])
    assert PROMOTED_TOKEN in system, system


def test_an_unpromoted_note_found_by_relevance_still_replays(
    tmp_path: Path,
) -> None:
    """Retrieval is not broken.  The fence is about promotion, nothing else."""
    db = Database(tmp_path / "unpromoted.db")
    _seed_two_notes(db)
    service = _thread_service(db)
    thread = service.create(title="No promotion anywhere")
    _run_relevance_turn(service, thread["id"])

    system = _replay(service, db, thread["id"])
    assert CONTROL_TOKEN in system, system
    assert PROMOTED_TOKEN in system, system


# ── the stamp itself ─────────────────────────────────────────────────────


def test_the_relevance_pass_stamps_relevance_and_an_attach_stamps_reference(
    tmp_path: Path,
) -> None:
    """The receipt says how each ref arrived, on the real turn path."""
    db = Database(tmp_path / "stamps.db")
    _seed_two_notes(db)
    service = _thread_service(db)

    relevance_thread = service.create(title="Relevance")
    _run_relevance_turn(service, relevance_thread["id"])
    stamped = _origins(db, relevance_thread["id"])
    assert stamped, stamped
    assert set(stamped.values()) == {"relevance"}, stamped

    reference_thread = service.create(title="Reference")
    asyncio.run(service.start_turn(OWNER, reference_thread["id"],
                                   "What does this mean?",
                                   refs=["note:control"]))
    time.sleep(0.5)
    assert _origins(db, reference_thread["id"]) == {"control": "reference"}


def test_a_row_written_before_the_column_existed_is_unknown_and_fences(
    tmp_path: Path,
) -> None:
    """Unknown must fence.  This is the default's whole justification.

    An existing `thread_refs` row carries no origin -- the reconciled default
    is `''`, not `'relevance'`, because the database does not KNOW how that row
    arrived and a receipt must not assert what it does not know.  The fence is
    an allow-list, so `''` behaves as fenced without anyone having to guess.

    The row is inserted the way a pre-column writer would have: every column
    named, `origin` omitted entirely.
    """
    db = Database(tmp_path / "legacy-row.db")
    _seed_two_notes(db)
    service = _thread_service(db)
    thread = service.create(title="Legacy rows")
    # A real user message so `_assemble_payload` has a path to walk.
    asyncio.run(service.start_turn(OWNER, thread["id"], "hello"))
    time.sleep(0.5)

    body = json.dumps({"kind": "note", "title": "Rollback rehearsal",
                       "subtitle": "", "text": f"{CONSTRAINT} {PROMOTED_TOKEN}"},
                      separators=(",", ":"), sort_keys=True)
    control_body = json.dumps({"kind": "note", "title": "Cutover notes",
                               "subtitle": "", "text": f"{CONSTRAINT} {CONTROL_TOKEN}"},
                              separators=(",", ":"), sort_keys=True)
    with db._connection() as conn:
        for row_id, ref_id, frozen in (("tr_legacy_p", "promoted", body),
                                       ("tr_legacy_c", "control", control_body)):
            conn.execute(
                "INSERT INTO thread_refs(id,thread_id,message_id,ref_kind,ref_id,"
                "version,frozen_json,created_at) VALUES (?,?,?,?,?,'',?,?)",
                (row_id, thread["id"], None, "note", ref_id, frozen, time.time()),
            )
        _insert_promotion(conn, "note:promoted", created_at="2026-09-07T09:00:00Z")

    assert _origins(db, thread["id"])["promoted"] == ""

    system = _replay(service, db, thread["id"])
    # The unpromoted legacy row still replays: unknown does not mean "drop".
    assert CONTROL_TOKEN in system, system
    assert PROMOTED_TOKEN not in system, system


def test_the_origin_stamp_rests_on_groundings_own_switch(tmp_path: Path) -> None:
    """The invariant the stamp depends on, pinned so it cannot drift.

    `hydrate_refs_detailed` runs its global relevance pass if and only if the
    call carried NO explicit source (`grounding.py:220-228`).  That is what
    lets `start_turn` stamp a whole batch of blocks from one flag.  If the
    global pass ever ran ALONGSIDE explicit refs, a relevance hit would be
    stamped `'reference'` and the fence would open -- so the coupling is
    asserted here rather than left as a comment.
    """
    db = Database(tmp_path / "switch.db")
    _seed_two_notes(db)
    service = _thread_service(db)
    thread = service.create(title="Explicit plus a matching query")
    # The text matches BOTH notes; only `control` is attached.
    asyncio.run(service.start_turn(OWNER, thread["id"], QUERY,
                                   refs=["note:control"]))
    time.sleep(0.5)
    # `promoted` is absent because the global pass did not run at all.
    assert _origins(db, thread["id"]) == {"control": "reference"}


# ── the reconciler ───────────────────────────────────────────────────────


_THREAD_REFS_WITH_ORIGIN = """CREATE TABLE IF NOT EXISTS thread_refs (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL REFERENCES threads(id),
    message_id TEXT REFERENCES thread_messages(id),
    ref_kind TEXT NOT NULL DEFAULT '',
    ref_id TEXT NOT NULL DEFAULT '',
    version TEXT NOT NULL DEFAULT '',
    frozen_json TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    origin TEXT NOT NULL DEFAULT ''
);"""

_THREAD_REFS_BEFORE = _THREAD_REFS_WITH_ORIGIN.replace(
    "    created_at REAL NOT NULL,\n    origin TEXT NOT NULL DEFAULT ''\n",
    "    created_at REAL NOT NULL\n",
)


def _older_schema() -> str:
    """The canonical schema with `thread_refs.origin` surgically removed."""
    from holdspeak.db.schema import SCHEMA_SQL

    assert SCHEMA_SQL.count(_THREAD_REFS_WITH_ORIGIN) == 1, (
        "older-schema surgery missed the thread_refs definition"
    )
    older = SCHEMA_SQL.replace(_THREAD_REFS_WITH_ORIGIN, _THREAD_REFS_BEFORE)
    assert _THREAD_REFS_WITH_ORIGIN not in older
    return older


def test_an_older_database_picks_up_origin_and_its_rows_read_as_unknown(
    tmp_path: Path,
) -> None:
    """The schema is declarative and self-reconciling; this is additive.

    The column has to ARRIVE on a database that predates it, and the value the
    reconciler leaves on the rows already there has to be the fencing one.
    `_constant_default_for` (`db/reconcile.py:834-855`) supplies the constant
    for the ALTER, so this asserts the outcome rather than the mechanism.
    """
    import sqlite3

    from holdspeak.db.reconcile import reconcile_schema

    path = tmp_path / "older-thread-refs.db"
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_older_schema())
    columns = {str(row["name"]) for row in
               conn.execute("PRAGMA table_info(thread_refs)")}
    assert "origin" not in columns, columns

    conn.execute(
        "INSERT INTO threads(id,title,recipe_id,created_at,updated_at)"
        " VALUES ('t1','Older','',0,0)")
    conn.execute(
        "INSERT INTO thread_refs(id,thread_id,message_id,ref_kind,ref_id,"
        "version,frozen_json,created_at) VALUES ('tr1','t1',NULL,'note','n1',"
        "'','{}',1.0)")
    conn.commit()

    assert reconcile_schema(conn) is True

    columns = {str(row["name"]) for row in
               conn.execute("PRAGMA table_info(thread_refs)")}
    assert "origin" in columns, columns
    # UNKNOWN, not 'relevance': the database does not know how that row
    # arrived, and the L4 allow-list fences anything that is not 'reference'.
    value = conn.execute("SELECT origin FROM thread_refs WHERE id='tr1'").fetchone()[0]
    assert str(value or "") == "", repr(value)
    conn.close()


# ── the real cross-device path: two Databases, the real verb, the real sync ──
#
# Everything above reproduces the defect on ONE database, standing in for the
# post-sync corpus repair with a hand-written `DELETE` from `notes_memory_fts`.
# That is a simulation, and a simulation cannot prove the sequencing it stands
# for.  What follows drives BOTH devices for real: the promotion is minted by
# `InterviewService.command()`, it crosses the wire through `SyncService.pull`
# -> `SyncService.push`, and `_merge_context_promotions` and
# `_sweep_promoted_from_corpus` (`sync_service.py:672-700`) actually run.


def _interview_thread(db: Database) -> str:
    from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID
    from holdspeak.services.thread_modes import seed_modes

    seed_modes(db)
    return ThreadService(db, broadcast=lambda *_: None).create(
        recipe_id=INTERVIEW_MODE_ID)["id"]


def _promote_through_the_real_verb(
    db: Database, quote: str, *, into: str = "",
) -> str:
    """His sentence -> a fact -> a promotion, all through the service.

    Returns the promoted note id.  Nothing here writes `context_promotions` or
    `notes` by hand: the row under test has to be the one the product writes,
    or the sweep that keys on it proves nothing.

    *into* selects the mode.  Empty mints a new Note; a note id promotes INTO
    an existing one (`append`), which is how a record he has already attached
    somewhere becomes a promoted record -- the sequence the by-reference
    control below needs.
    """
    from holdspeak.services.interview_service import InterviewService

    thread_id = _interview_thread(db)
    service = InterviewService(db)
    message = db.threads.append_message(thread_id, role="user")
    db.threads.append_part(message.id, kind="text", text=quote)

    def _command(event: dict[str, Any]) -> dict[str, Any]:
        return service.command(
            OWNER, thread_id, command_id=uuid.uuid4().hex,
            expected_revision=service.get(thread_id)["revision"], event=event)

    _command({"kind": "fact", "fact_id": "goal", "basis": "stated",
              "text": "Rollback rehearsal before every cutover",
              "source_message_id": message.id, "quote": quote})
    event: dict[str, Any] = {"kind": "promote", "fact_id": "goal"}
    if into:
        event["target_ref"] = f"note:{into}"
        event["expected_target_revision"] = db.notes.get(into).last_modified
    promotion = _command(event)["promotion"]
    assert promotion["minted"] is True, promotion
    note_id = str(promotion["target_ref"]).split(":", 1)[1]
    if into:
        assert note_id == into, (note_id, into)
        assert db.notes.get(note_id).body_markdown.endswith(quote)
    else:
        assert db.notes.get(note_id).body_markdown == quote
    return note_id


def _fts_ids(db: Database) -> set[str]:
    with db._connection() as conn:
        return {str(row[0]) for row in
                conn.execute("SELECT source_id FROM notes_memory_fts")}


def _promotion_ids(db: Database) -> set[str]:
    with db._connection() as conn:
        return {str(row[0]) for row in
                conn.execute("SELECT promotion_id FROM context_promotions")}


def _laptop(tmp_path: Path) -> tuple[Database, str]:
    """Device A: one ordinary note he typed, one note he promoted."""
    a = Database(tmp_path / "device-a.db")
    a.notes.upsert(note_id="control", title="Cutover notes",
                   body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}",
                   last_modified="2026-09-07T09:00:00Z")
    note_id = _promote_through_the_real_verb(a, f"{CONSTRAINT} {PROMOTED_TOKEN}")
    # Device A's own corpus is fenced at construction (F0/L1).
    assert _fts_ids(a) == {"control"}, _fts_ids(a)
    return a, note_id


def test_a_relevance_body_frozen_before_a_real_sync_is_fenced_on_every_later_turn(
    tmp_path: Path,
) -> None:
    """THE CROSS-DEVICE DEFECT, END TO END, WITH NOTHING SIMULATED.

    1. The laptop mints a promotion through the real verb.
    2. The desktop receives the NOTE bucket alone -- the ordering hazard
       `_sweep_promoted_from_corpus` exists for.  `notes_memory_ai` fires with
       no promotion row in sight and the body enters the desktop's corpus.
    3. A real turn on the desktop runs the relevance pass and freezes the whole
       body into `thread_refs.frozen_json`, LATER than the laptop's promotion.
    4. The real sync lands.  The sweep repairs the corpus and leaves
       `thread_refs` untouched -- which is exactly why the replay needs its own
       fence.
    5. Under the time-keyed fence the desktop replayed that body to the model
       forever.  Under the origin fence the row says `'relevance'` and it never
       replays -- on this turn or any later one.
    """
    from holdspeak.services.sync_service import SyncService

    a, promoted_id = _laptop(tmp_path)
    b = Database(tmp_path / "device-b.db")

    body = SyncService(a).pull(OWNER)
    assert body["context_promotions"], "the promotion did not ride the wire"

    # -- step 2: the notes land alone, and the desktop's corpus is unfenced.
    SyncService(b).push(OWNER, {"notes": body["notes"]})
    assert _fts_ids(b) == {"control", promoted_id}, "the hazard did not reproduce"
    assert not _promotion_ids(b), "the desktop must not know about it yet"

    # -- step 3: a real turn freezes both bodies.
    service = _thread_service(b)
    thread = service.create(title="Desktop, before the sync")
    _run_relevance_turn(service, thread["id"])
    frozen = _frozen_texts(b, thread["id"])
    assert any(PROMOTED_TOKEN in text for text in frozen), frozen
    assert any(CONTROL_TOKEN in text for text in frozen), frozen
    # The freeze is LATER than the promotion: this is the shape the time fence
    # read as "arrived by reference".
    with b._connection() as conn:
        froze_at = float(conn.execute(
            "SELECT MAX(created_at) FROM thread_refs WHERE thread_id=?",
            (thread["id"],)).fetchone()[0])
    from datetime import datetime
    promoted_at = datetime.fromisoformat(
        str(body["context_promotions"][0]["value"]["created_at"]).replace("Z", "+00:00")
    ).timestamp()
    assert froze_at >= promoted_at, (froze_at, promoted_at)

    # -- step 4: the REAL sync, promotions included.
    SyncService(b).push(OWNER, body)
    assert _promotion_ids(b) == _promotion_ids(a)
    # The sweep ran: the corpus is repaired and the control survives it.
    assert _fts_ids(b) == {"control"}
    # And it did NOT touch the receipt -- which is the whole point.
    assert any(PROMOTED_TOKEN in text for text in _frozen_texts(b, thread["id"]))

    # -- step 5: the replay, on this turn and on a later one.
    system = _replay(service, b, thread["id"])
    assert CONTROL_TOKEN in system, system
    assert PROMOTED_TOKEN not in system, system

    _run_relevance_turn(service, thread["id"])
    later = _replay(service, b, thread["id"])
    # POSITIVE CONTROL: the unpromoted note frozen the same way, on the same
    # thread, in the same batch, is still replayed.  A fence that broke
    # grounding outright would satisfy the assertion after it for the wrong
    # reason.
    assert CONTROL_TOKEN in later, later
    assert PROMOTED_TOKEN not in later, later


def test_after_a_real_sync_a_promoted_note_attached_by_reference_still_arrives(
    tmp_path: Path,
) -> None:
    """C2''s promise on the receiving device: reachable BY REFERENCE.

    THE OLD TIME FENCE ACTUALLY BROKE THIS, and this is the sequence that
    broke it -- the promotion's clock landing LATER than the attach:

      1. The desktop syncs an ordinary Note he typed and ATTACHES it to a
         Thread by name.  The row is frozen at that moment.
      2. Later, on the laptop, he promotes that same Note (append mode --
         `context_promotions` names an existing record).
      3. The promotion syncs down.  Its `created_at` is AFTER the freeze, so
         the time fence read the row as "frozen before the promotion" and
         DROPPED a note he had named on purpose.

    Silent loss of accepted input is the failure B1 was written to prevent,
    and the proxy it chose committed it.  The origin fence reads `'reference'`
    off the row and delivers it.

    No clock is set by hand anywhere here: both timestamps are whatever the
    real verb and the real freeze wrote.
    """
    from holdspeak.services.sync_service import SyncService

    a = Database(tmp_path / "device-a-by-reference.db")
    a.notes.upsert(note_id="control", title="Cutover notes",
                   body_markdown=f"{CONSTRAINT} {CONTROL_TOKEN}",
                   last_modified="2026-09-07T09:00:00Z")
    # An ordinary Note he typed.  Not promoted yet -- it is IN the corpus.
    a.notes.upsert(note_id="standing", title="Rollback rehearsal",
                   body_markdown=f"{CONSTRAINT} {PROMOTED_TOKEN}",
                   last_modified="2026-09-07T09:00:00Z")
    assert _fts_ids(a) == {"control", "standing"}, _fts_ids(a)

    b = Database(tmp_path / "device-b-by-reference.db")
    SyncService(b).push(OWNER, {"notes": SyncService(a).pull(OWNER)["notes"]})
    assert {n.id for n in b.notes.list()} >= {"control", "standing"}

    # -- step 1: he attaches it BY NAME on the desktop.
    service = _thread_service(b)
    thread = service.create(title="He attached it himself")
    asyncio.run(service.start_turn(OWNER, thread["id"], "What does this mean?",
                                   refs=["note:standing"]))
    time.sleep(0.5)
    assert _origins(b, thread["id"]) == {"standing": "reference"}
    with b._connection() as conn:
        froze_at = float(conn.execute(
            "SELECT MAX(created_at) FROM thread_refs WHERE thread_id=?",
            (thread["id"],)).fetchone()[0])

    # -- step 2: the laptop promotes that same Note, LATER.
    _promote_through_the_real_verb(a, f"{CONSTRAINT} {PROMOTED_TOKEN}",
                                   into="standing")
    assert _fts_ids(a) == {"control"}, "device A did not fence its own corpus"

    body = SyncService(a).pull(OWNER)
    from datetime import datetime
    promoted_at = datetime.fromisoformat(
        str(body["context_promotions"][0]["value"]["created_at"]).replace("Z", "+00:00")
    ).timestamp()
    # The shape the time fence got wrong: the promotion is LATER than the
    # freeze, so "frozen before the promotion" was true of a ref he named.
    assert promoted_at > froze_at, (promoted_at, froze_at)

    # -- step 3: the promotion lands on the desktop.
    SyncService(b).push(OWNER, body)
    assert _promotion_ids(b) == _promotion_ids(a)
    assert _fts_ids(b) == {"control"}, "the sweep did not repair the corpus"

    # He named it.  It arrives.
    system = _replay(service, b, thread["id"])
    assert PROMOTED_TOKEN in system, system


def test_a_seed_ref_records_reference_although_the_fence_can_never_read_it(
    tmp_path: Path,
) -> None:
    """The one stamp in this design that is a RECEIPT and not a fence.

    `ThreadService.create(seed_refs=[...])` writes rows with `ref_kind='seed'`
    -- the literal is hardcoded there -- and the L4 replay fence only ever
    looks at `ref_kind == 'note'`.  So no leak test can kill this stamp, and
    this test says so plainly rather than dressing a receipt up as a guard.

    It is pinned anyway because the value is the honest one: the caller NAMED
    these refs when it opened the Thread (`web/src/desk/verbRegistry.ts:461`
    sends them from an object the owner picked), so `'reference'` is what the
    database knows, and an unstamped row here would read as UNKNOWN and assert
    less than the truth.
    """
    db = Database(tmp_path / "seed-refs.db")
    thread = ThreadService(db, broadcast=lambda *_: None).create(
        title="Opened on an object", seed_refs=["note:control"])

    with db._connection() as conn:
        rows = [(str(r[0]), str(r[1]), str(r[2] or "")) for r in conn.execute(
            "SELECT ref_kind, ref_id, origin FROM thread_refs WHERE thread_id=?",
            (thread["id"],))]
    assert rows == [("seed", "note:control", "reference")], rows
    # And the hydrated dataclass carries it, which is where the fence reads.
    assert [ref.origin for ref in db.threads.get_refs(thread["id"])] == ["reference"]
