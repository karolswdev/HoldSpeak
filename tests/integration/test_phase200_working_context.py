"""HS-200-10 Lane B: the promotion VERB, through the real service.

Lane A built the BOUNDARY -- the three tables, the guarded FTS triggers, the
graph-route fence and the two relevance call-site belts -- and proved it by
writing `context_promotions` rows directly, in the order the verb must use.
This file drives the verb itself: `InterviewService.command()` with the two new
event kinds, on the transaction `command()` already opens.

The lesson this phase paid for twice: **a test that cannot fail on the real
path is not proof.**  So every fence here is exercised through
`InterviewService.command()` with a real Thread, a real user message and a real
part -- never by calling a private helper -- and every assertion is paired with
the case that must still SUCCEED, so a fence that over-reaches fails as loudly
as one that is missing.

Ordering (ruling C1): the boundary landed before the verb it bounds.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID
from holdspeak.services.interview_service import InterviewService
from holdspeak.services.thread_modes import seed_modes
from holdspeak.services.thread_service import ThreadService

OWNER = Principal(PrincipalKind.OWNER, "hs-200-10-owner")
AGENT = Principal(PrincipalKind.AGENT, "hs-200-10-agent")

# D0's Tuesday sentence, carrying a token that appears in nothing else so an
# assertion can look at the actual bytes rather than at a ref list.
RARE = "kestrelmark"
CONSTRAINT = (
    f"We cannot take another {RARE} cutover without a rollback rehearsal. "
    "That is not negotiable."
)
TITLE = f"We cannot take another {RARE} cutover without a rollback rehearsal"


class Rig:
    """One Interview Thread, and the smallest honest way to drive it."""

    def __init__(self, db: Database, thread_id: str) -> None:
        self.db = db
        self.tid = thread_id
        self.svc = InterviewService(db)

    def say(self, text: str, *, sensitive: bool = False, draft: bool = False) -> str:
        message = self.db.threads.append_message(self.tid, role="user")
        self.db.threads.append_part(
            message.id, kind="text", text=text, sensitive=sensitive, draft=draft
        )
        return message.id

    def command(self, event: dict[str, Any], *, command_id: str | None = None,
                expected_revision: int | None = None) -> dict[str, Any]:
        revision = self.svc.get(self.tid)["revision"] if expected_revision is None else expected_revision
        return self.svc.command(
            OWNER, self.tid, command_id=command_id or uuid.uuid4().hex,
            expected_revision=revision, event=event,
        )

    def record(self, *, fact_id: str = "goal", quote: str = CONSTRAINT,
               text: str = "Rollback rehearsal before every cutover",
               basis: str = "stated", message_id: str | None = None) -> str:
        source = message_id or self.say(quote)
        self.command({"kind": "fact", "fact_id": fact_id, "text": text, "basis": basis,
                      "source_message_id": source, "quote": quote})
        return source

    def promote(self, *, fact_id: str = "goal", **extra: Any) -> dict[str, Any]:
        return self.command({"kind": "promote", "fact_id": fact_id, **extra})

    def rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
        with self.db._connection() as conn:
            return conn.execute(sql, params).fetchall()

    def note_for(self, result: dict[str, Any]) -> Any:
        return self.db.notes.get(result["promotion"]["target_ref"].split(":", 1)[1])

    def promotion_row(self, promotion_id: str) -> Any:
        return self.rows("SELECT * FROM context_promotions WHERE promotion_id=?", (promotion_id,))[0]

    def dependent(self, canonical_ref: str, consumer_id: str = "thought-1") -> Any:
        """Register one consumer of a record, the shape `_persist_manifest` writes.

        The reconcile point that writes these for real lives in
        `refinement_context_service._persist_manifest`, which this lane does not
        own; the revoke rule under test reads the row, it does not write it.
        """
        with self.db._connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO context_dependents(canonical_ref,consumer_kind,consumer_id,"
                "consumer_revision,bound_manifest_sha256,bound_at,stale_since,stale_reason) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (canonical_ref, "thought", consumer_id, 1, "sha256:manifest",
                 "2026-09-07T09:00:00Z", None, ""),
            )
        return consumer_id

    def dependent_state(self, canonical_ref: str, consumer_id: str = "thought-1") -> str:
        row = self.rows(
            "SELECT stale_reason FROM context_dependents WHERE canonical_ref=? AND consumer_id=?",
            (canonical_ref, consumer_id),
        )
        return str(row[0]["stale_reason"]) if row else "<missing>"

    def fts_ids(self) -> set[str]:
        return {str(row[0]) for row in self.rows("SELECT source_id FROM notes_memory_fts")}

    def fts_matches(self, term: str) -> set[str]:
        return {
            str(row[0])
            for row in self.rows("SELECT source_id FROM notes_memory_fts WHERE notes_memory_fts MATCH ?", (term,))
        }


@pytest.fixture
def rig(tmp_path: Path):
    db = Database(tmp_path / "promotion.db")
    seed_modes(db)
    thread = ThreadService(db, broadcast=lambda *_: None).create(recipe_id=INTERVIEW_MODE_ID)
    yield Rig(db, thread["id"])
    db.close()


# ── The verb: what a promotion writes, and what it refuses to write ──────


def test_promotion_records_locator_and_never_copies_the_quote(rig: Rig) -> None:
    """Provenance is a LOCATOR and a HASH, never a copy.

    A substring check over EVERY column of the row: if any of them carried the
    words, revoking the source would leave the text behind and the design's
    central provenance claim would be false.
    """
    rig.record()
    result = rig.promote()
    row = rig.promotion_row(result["promotion"]["promotion_id"])

    values = {key: row[key] for key in row.keys()}
    for key, value in values.items():
        assert CONSTRAINT not in str(value), f"{key} carries the quotation"
        assert RARE not in str(value), f"{key} carries a word of the quotation"
    # The locator addresses it instead: an ordinal and an offset.
    locator = json.loads(str(row["quote_locator_json"]))
    assert locator["part_ordinal"] == 0
    assert locator["char_length"] == len(CONSTRAINT)
    source = rig.rows("SELECT text FROM thread_message_parts WHERE message_id=? AND ordinal=?",
                      (str(row["source_message_id"]), locator["part_ordinal"]))[0]
    excerpt = str(source["text"])[locator["char_start"]:locator["char_start"] + locator["char_length"]]
    assert excerpt == CONSTRAINT
    # And the hash proves the locator still addresses what it named.
    assert rig.svc.promotions(OWNER, rig.tid)[0]["source_available"] is True


def test_only_a_stated_fact_may_be_promoted_and_the_body_is_his_words(rig: Rig) -> None:
    """The canonical record carries HIS words, never the model's paraphrase."""
    rig.record(fact_id="inferred-one", basis="inferred",
               text="They seem to want rollback rehearsals")
    with pytest.raises(ServiceError, match="stated"):
        rig.promote(fact_id="inferred-one")

    rig.record(fact_id="stated-one")
    note = rig.note_for(rig.promote(fact_id="stated-one"))
    assert note.body_markdown == CONSTRAINT
    # The title is minted from the quote's leading clause, so the context
    # picker (which searches TITLE only) can still find it by his own words.
    assert note.title == TITLE
    assert "Rollback rehearsal before every cutover" not in note.title


def test_the_people_section_refuses_promotion_and_a_person_ref_refuses_itself(rig: Rig) -> None:
    """F1 and F4: the People boundary, from both directions."""
    rig.record()
    # F4 -- `person` is not a resource kind, so `qualified_ref` refuses it.
    with pytest.raises(ServiceError) as person:
        rig.promote(target_ref="person:rel-1", expected_target_revision="whatever")
    assert person.value.code == "promotion_target_unsupported"

    # F1 -- the section gate. The same fact, refused because of where he is.
    rig.command({"kind": "section", "section": "people"})
    with pytest.raises(ServiceError, match="storage boundary"):
        rig.promote()
    assert rig.rows("SELECT count(*) c FROM context_promotions")[0]["c"] == 0

    # And it succeeds again once he leaves the section: the fence is the
    # boundary, not a broken verb.
    rig.command({"kind": "section", "section": "goals"})
    assert rig.promote()["promotion"]["minted"] is True


def test_a_sensitive_or_draft_part_cannot_source_a_promotion(rig: Rig) -> None:
    """F2, re-run INSIDE the promotion transaction.

    The fence is `_prune_unavailable_facts` running on the command's own
    connection before the reducer sees the state, so a part re-classified
    sensitive or draft between recording and promotion takes the fact with it.
    """
    for fact_id, column in (("sensitive-fact", "sensitive"), ("draft-fact", "draft")):
        source = rig.record(fact_id=fact_id)
        with rig.db._connection() as conn:
            conn.execute(f"UPDATE thread_message_parts SET {column}=1 WHERE message_id=?", (source,))
        with pytest.raises(ServiceError, match="Unknown interview fact"):
            rig.promote(fact_id=fact_id)
    assert rig.rows("SELECT count(*) c FROM context_promotions")[0]["c"] == 0

    # The control: an ordinary part promotes.
    rig.record(fact_id="ordinary-fact")
    assert rig.promote(fact_id="ordinary-fact")["promotion"]["minted"] is True


def test_promotion_into_the_default_or_everyday_context_is_refused(rig: Rig) -> None:
    """F3, written for the APPEND mode -- the only mode where it can fire.

    In new-Note mode the service mints the ref, so a newly minted record cannot
    already be in default context and the fence is structurally unreachable
    (counsel C8).
    """
    rig.record()
    rig.db.notes.upsert(note_id="standing-note", title="Standing constraints",
                        body_markdown="Existing text.")
    revision = str(rig.db.notes.get("standing-note").last_modified)

    with rig.db._connection() as conn:
        conn.execute("UPDATE refinement_default_context_current SET refs_json=? WHERE id=1",
                     (json.dumps(["note:standing-note"]),))
    with pytest.raises(ServiceError) as default_context:
        rig.promote(target_ref="note:standing-note", expected_target_revision=revision)
    assert default_context.value.code == "promotion_into_default_context"

    # The other limb of the same fence: membership of the Everyday KB.
    with rig.db._connection() as conn:
        conn.execute("UPDATE refinement_default_context_current SET refs_json='[]' WHERE id=1")
    rig.db.kbs.upsert(kb_id="hs-seed-everyday-context", name="Everyday context")
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO knowledge_memberships(knowledge_id,resource_ref,created_at,last_modified,deleted) "
                     "VALUES(?,?,?,?,0)",
                     ("hs-seed-everyday-context", "note:standing-note",
                      "2026-09-07T09:00:00Z", "2026-09-07T09:00:00Z"))
    with pytest.raises(ServiceError) as everyday:
        rig.promote(target_ref="note:standing-note", expected_target_revision=revision)
    assert everyday.value.code == "promotion_into_default_context"
    assert rig.rows("SELECT count(*) c FROM context_promotions")[0]["c"] == 0

    # The control: an ordinary Note outside both accepts the append.
    rig.db.notes.upsert(note_id="ordinary-note", title="Cutover notes", body_markdown="Existing text.")
    ordinary = str(rig.db.notes.get("ordinary-note").last_modified)
    assert rig.promote(target_ref="note:ordinary-note", expected_target_revision=ordinary)["promotion"]["minted"]


def test_target_kind_is_derived_from_the_ref_not_the_caller(rig: Rig) -> None:
    """C10: a ref names its own kind.

    `artifact:a1` passes `qualified_ref` -- `artifact` is one of the twenty
    kinds -- so a caller-supplied `target_kind` would send the note branch to
    `SELECT ... FROM notes WHERE id='a1'`.  The event has no `target_kind`
    field at all, and an unsupported kind refuses before any table is read.
    """
    rig.record()
    rig.db.notes.upsert(note_id="a1", title="A note whose id collides", body_markdown="Not the target.")

    with pytest.raises(ServiceError) as unsupported:
        rig.promote(target_ref="artifact:a1", expected_target_revision="whatever")
    assert unsupported.value.code == "promotion_target_unsupported"
    assert unsupported.value.context["target_kind"] == "artifact"
    # The note that shares the id was not read, written, or promoted.
    assert rig.db.notes.get("a1").body_markdown == "Not the target."
    assert rig.rows("SELECT count(*) c FROM context_promotions")[0]["c"] == 0

    # A caller-supplied `target_kind` is not a field this verb accepts.
    with pytest.raises(ServiceError, match="Invalid promotion fields"):
        rig.command({"kind": "promote", "fact_id": "goal", "target_kind": "note",
                     "target_ref": "artifact:a1"})


def test_two_promotions_of_one_fact_mint_one_note(rig: Rig) -> None:
    """P0-4: two clicks, two command ids, ONE Note.

    `command_id` is caller-supplied, so the replay guard cannot cover two
    deliberate clicks.  The deterministic mint from (thread_id, fact_id) is what
    does: the second promote collides on the row that already exists and becomes
    an `updated_at` touch.
    """
    rig.record()
    first = rig.promote()["promotion"]
    before = rig.promotion_row(first["promotion_id"])

    second = rig.promote()["promotion"]
    after = rig.promotion_row(second["promotion_id"])

    assert second["target_ref"] == first["target_ref"]
    assert first["minted"] is True and second["minted"] is False
    assert rig.rows("SELECT count(*) c FROM context_promotions")[0]["c"] == 1
    assert rig.rows("SELECT count(*) c FROM notes")[0]["c"] == 1
    assert str(after["updated_at"]) > str(before["updated_at"])
    assert str(after["created_at"]) == str(before["created_at"])
    # Two commands really were applied: this is not the replay guard.
    assert rig.svc.get(rig.tid)["revision"] == 3


def test_a_second_promotion_into_one_note_does_not_append_the_quote_twice(rig: Rig) -> None:
    """The append mode's half of P0-4: idempotence has to be about BYTES."""
    rig.record()
    rig.db.notes.upsert(note_id="standing-note", title="Standing constraints", body_markdown="Existing text.")
    revision = str(rig.db.notes.get("standing-note").last_modified)
    rig.promote(target_ref="note:standing-note", expected_target_revision=revision)
    after_first = rig.db.notes.get("standing-note").body_markdown

    rig.promote(target_ref="note:standing-note", expected_target_revision=revision)

    assert rig.db.notes.get("standing-note").body_markdown == after_first
    assert after_first.count(CONSTRAINT) == 1


def test_promotion_into_a_moved_note_refuses_on_the_expected_revision(rig: Rig) -> None:
    """The optimistic cursor: a Note that moved refuses `promotion_target_conflict`.

    `last_modified` is written at SECOND resolution (`primitives._now_iso`), so
    the two edits here carry explicit cursors -- the same API the shipped
    attachment test uses.  That granularity is the shipped `_mutate` grammar's,
    not this verb's: the authority on whether content moved is the content hash,
    and this cursor is the caller's read-your-own-write check.
    """
    rig.record()
    rig.db.notes.upsert(note_id="standing-note", title="Standing constraints",
                        body_markdown="Existing text.", last_modified="2026-09-07T09:00:00Z")
    stale_cursor = str(rig.db.notes.get("standing-note").last_modified)
    rig.db.notes.upsert(note_id="standing-note", title="Standing constraints",
                        body_markdown="Existing text, edited.", last_modified="2026-09-07T10:00:00Z")

    with pytest.raises(ServiceError) as conflict:
        rig.promote(target_ref="note:standing-note", expected_target_revision=stale_cursor)
    assert conflict.value.code == "promotion_target_conflict"
    assert conflict.value.context["status"] == 409
    assert rig.db.notes.get("standing-note").body_markdown == "Existing text, edited."

    # The control: the cursor the caller would have re-read succeeds.
    fresh = str(rig.db.notes.get("standing-note").last_modified)
    assert rig.promote(target_ref="note:standing-note", expected_target_revision=fresh)["promotion"]["minted"]

    # A Note that is gone is a Note that moved, in the extreme.
    with pytest.raises(ServiceError) as missing:
        rig.promote(fact_id="goal", target_ref="note:no-such-note", expected_target_revision="whatever")
    assert missing.value.code == "promotion_target_conflict"


def test_promotion_replays_and_a_changed_payload_conflicts(rig: Rig) -> None:
    """The promotion inherits `command()`'s whole concurrency contract."""
    rig.record()
    event = {"kind": "promote", "fact_id": "goal"}
    first = rig.command(event, command_id="promote-once")
    replay = rig.command(event, command_id="promote-once", expected_revision=first["revision"] - 1)

    assert replay["replayed"] is True
    assert replay["revision"] == first["revision"]
    # A replay returns the durable state and no outcome: the reducer did not run.
    assert "promotion" not in replay
    assert rig.rows("SELECT count(*) c FROM context_promotions")[0]["c"] == 1

    with pytest.raises(ServiceError, match="different change"):
        rig.command({"kind": "promote", "fact_id": "goal", "target_ref": "note:elsewhere"},
                    command_id="promote-once")
    with pytest.raises(ServiceError, match="reload"):
        rig.command(event, command_id="another", expected_revision=0)


def test_promotion_requires_the_owner(rig: Rig) -> None:
    """The model records; the owner disposes."""
    rig.record()
    with pytest.raises(ServiceError) as refused:
        rig.svc.command(AGENT, rig.tid, command_id="agent-promote", expected_revision=1,
                        event={"kind": "promote", "fact_id": "goal"})
    assert refused.value.code == "owner_required"
    assert rig.rows("SELECT count(*) c FROM context_promotions")[0]["c"] == 0


# ── F0 through the REAL verb: the body never reaches the corpus ──────────


def test_promoting_through_the_real_verb_never_lets_the_body_reach_the_corpus(rig: Rig) -> None:
    """The end-to-end Lane A could only approximate with a direct INSERT.

    The promotion row is written BEFORE the Note on the same connection, so when
    `notes_memory_ai` fires its guard already sees the promotion: the body is
    never written to the relevance corpus at all, not even transiently.  The
    control note -- the same words, no promotion -- IS indexed, so this test
    fails if the fence is removed AND if it over-reaches.
    """
    rig.db.notes.upsert(note_id="control", title="Cutover notes", body_markdown=CONSTRAINT)
    rig.record()

    result = rig.promote()["promotion"]
    note_id = result["target_ref"].split(":", 1)[1]

    assert rig.rows("SELECT count(*) c FROM notes_memory_fts WHERE source_id=?", (note_id,))[0]["c"] == 0
    assert rig.fts_matches(RARE) == {"control"}
    # The record itself is intact and reachable by reference.
    assert rig.db.notes.get(note_id).body_markdown == CONSTRAINT


def test_appending_into_an_existing_note_removes_it_from_the_corpus(rig: Rig) -> None:
    """The append mode: a Note already in the pool leaves it, atomically.

    This is a real cost and the correct direction: a Note that is mostly his own
    writing leaves the relevance pool permanently once it carries
    system-extracted text.
    """
    rig.db.notes.upsert(note_id="standing-note", title="Standing constraints",
                        body_markdown=f"Existing {RARE} text.")
    rig.db.notes.upsert(note_id="control", title="Other notes", body_markdown=f"Another {RARE} line.")
    assert rig.fts_matches(RARE) == {"standing-note", "control"}
    rig.record()

    revision = str(rig.db.notes.get("standing-note").last_modified)
    rig.promote(target_ref="note:standing-note", expected_target_revision=revision)

    assert "standing-note" not in rig.fts_ids()
    assert rig.fts_matches(RARE) == {"control"}
    assert CONSTRAINT in rig.db.notes.get("standing-note").body_markdown
    assert "Existing" in rig.db.notes.get("standing-note").body_markdown


def test_the_append_mode_corpus_delete_holds_when_the_trigger_refresh_was_botched(rig: Rig) -> None:
    """Why the append mode deletes from the corpus itself.

    On a healthy database the DELETE is belt: the revised `notes_memory_au`
    already declines to re-index a promoted record, and the mutation run
    confirms it -- removing the DELETE alone changes nothing there.  It becomes
    load-bearing on a database whose trigger refresh did not land, which is the
    only state where the promotion transaction is the last line of defence.
    This test installs the PRE-HS-200-10 trigger body and proves the verb still
    leaves the body out of the corpus.
    """
    rig.db.notes.upsert(note_id="standing-note", title="Standing constraints",
                        body_markdown=f"Existing {RARE} text.")
    with rig.db._connection() as conn:
        conn.execute("DROP TRIGGER notes_memory_au")
        conn.execute(
            "CREATE TRIGGER notes_memory_au AFTER UPDATE ON notes BEGIN "
            "DELETE FROM notes_memory_fts WHERE source_id=OLD.id; "
            "INSERT INTO notes_memory_fts(source_id,title,body_markdown) "
            "SELECT NEW.id,NEW.title,NEW.body_markdown WHERE NEW.deleted=0; END"
        )
    rig.record()

    rig.promote(target_ref="note:standing-note",
                expected_target_revision=str(rig.db.notes.get("standing-note").last_modified))

    assert "standing-note" not in rig.fts_ids()
    assert rig.fts_matches(RARE) == set()
    assert CONSTRAINT in rig.db.notes.get("standing-note").body_markdown


# ── Revocation: the claim, not the record ───────────────────────────────


def test_revoking_a_source_blocks_re_promotion_and_names_the_gap(rig: Rig) -> None:
    """AC4. Revocation revokes the CLAIM THAT A SOURCE BACKS the record."""
    rig.record()
    promoted = rig.promote()["promotion"]
    target = promoted["target_ref"]
    rig.dependent(target)

    revoked = rig.command({"kind": "revoke_promotion", "promotion_id": promoted["promotion_id"]})["promotion"]

    # It names the gap to its caller: the quotation removed and where it lived.
    assert revoked["revoked"] == "source_claim"
    assert revoked["record_retained"] is True
    assert revoked["removed_quote"] == CONSTRAINT
    assert revoked["removed_quote_locator"]["char_length"] == len(CONSTRAINT)
    assert revoked["dependents_marked"] == 1
    assert revoked["dependent_state"] == "forbidden"
    assert rig.dependent_state(target) == "forbidden"
    # The record is HIS and it stays.
    assert rig.db.notes.get(target.split(":", 1)[1]).body_markdown == CONSTRAINT
    assert rig.svc.promotions(OWNER, rig.tid)[0]["disclosure_state"] == "revoked"

    # And it cannot be re-promoted: forgetting is not suppressing.
    with pytest.raises(ServiceError) as suppressed:
        rig.promote()
    assert suppressed.value.code == "promotion_suppressed"


def test_re_typing_a_revoked_quote_does_not_resurrect_the_promotion(rig: Rig) -> None:
    """The suppression is keyed by DURABLE identity, not by the words.

    He says the sentence again, the model records the same fact against the new
    message, and the promotion still refuses.  The honest limit of an
    identity-keyed suppression is asserted too: a quotation re-recorded under a
    NEW fact id is a new deliberate promotion into a new record, not a
    resurrection of the revoked one -- and it is fenced out of relevance like
    any other.
    """
    rig.record()
    promoted = rig.promote()["promotion"]
    rig.command({"kind": "revoke_promotion", "promotion_id": promoted["promotion_id"]})

    rig.record(message_id=rig.say(CONSTRAINT))
    with pytest.raises(ServiceError) as suppressed:
        rig.promote()
    assert suppressed.value.code == "promotion_suppressed"
    assert rig.rows("SELECT count(*) c FROM context_promotions")[0]["c"] == 1

    rig.record(fact_id="second-look")
    fresh = rig.promote(fact_id="second-look")["promotion"]
    assert fresh["target_ref"] != promoted["target_ref"]
    assert fresh["target_ref"].split(":", 1)[1] not in rig.fts_ids()


def test_revoking_one_of_several_promotions_does_not_poison_the_record(rig: Rig) -> None:
    """P0-3, and `forbidden` is TERMINAL, so the poison would be permanent.

    `UNIQUE (thread_id, fact_id, target_ref)` deliberately permits N promotions
    into one record.  Marking every dependent `forbidden` on the first revoke
    would poison a record the second promotion still legitimately backs.
    """
    rig.record(fact_id="first-fact")
    first = rig.promote(fact_id="first-fact")["promotion"]
    target = first["target_ref"]
    note_id = target.split(":", 1)[1]
    rig.dependent(target)

    rig.record(fact_id="second-fact", quote="Rollbacks are rehearsed quarterly.")
    revision = str(rig.db.notes.get(note_id).last_modified)
    second = rig.promote(fact_id="second-fact", target_ref=target, expected_target_revision=revision)["promotion"]

    one = rig.command({"kind": "revoke_promotion", "promotion_id": first["promotion_id"]})["promotion"]
    assert one["surviving_active_promotions"] == 1
    assert one["dependent_state"] == "stale"
    assert rig.dependent_state(target) == "stale"

    two = rig.command({"kind": "revoke_promotion", "promotion_id": second["promotion_id"]})["promotion"]
    assert two["surviving_active_promotions"] == 0
    assert two["dependent_state"] == "forbidden"
    assert rig.dependent_state(target) == "forbidden"


def test_a_revocation_is_never_downgraded_by_a_later_stale_marking(rig: Rig) -> None:
    """P0-2 from the verb's side: `forbidden` is TERMINAL.

    The sequence that reaches the downgrade is specific and it is reachable:
    a record whose only promotion is revoked goes `forbidden`; a DIFFERENT fact
    then promotes into the same record (the suppression is keyed by fact, so it
    does not fence a different one); revoking one of two survivors computes
    `stale` -- and that `stale` must not rewrite the standing `forbidden`.
    A consumer fencing on `forbidden` would otherwise see an ordinary
    refreshable staleness and dispatch.
    """
    rig.record(fact_id="first-fact")
    first = rig.promote(fact_id="first-fact")["promotion"]
    target = first["target_ref"]
    note_id = target.split(":", 1)[1]
    rig.dependent(target)

    rig.command({"kind": "revoke_promotion", "promotion_id": first["promotion_id"]})
    assert rig.dependent_state(target) == "forbidden"

    rig.record(fact_id="second-fact", quote="Rollbacks are rehearsed quarterly.")
    second = rig.promote(fact_id="second-fact", target_ref=target,
                         expected_target_revision=str(rig.db.notes.get(note_id).last_modified))["promotion"]
    rig.record(fact_id="third-fact", quote="Every cutover has a named rehearsal owner.")
    rig.promote(fact_id="third-fact", target_ref=target,
                expected_target_revision=str(rig.db.notes.get(note_id).last_modified))

    # Two active promotions; revoking one computes `stale`...
    downgrade = rig.command({"kind": "revoke_promotion", "promotion_id": second["promotion_id"]})["promotion"]
    assert downgrade["dependent_state"] == "stale"
    # ...and the standing revocation survives it.
    assert rig.dependent_state(target) == "forbidden"


def test_a_revocation_never_downgrades_an_unavailable_dependent_to_stale(rig: Rig) -> None:
    """P0 from counsel-on-built: `unavailable` is a gap no refresh can close.

    The lattice `schema.py` declares says `unavailable` is cleared only by a
    rebind.  The revoke path's CASE protected `forbidden` and NOTHING else, so
    a dependent whose record had been deleted was silently rewritten to
    ordinary refreshable staleness whenever any OTHER promotion into that
    record was revoked while a survivor remained -- and a consumer reading
    `stale` would then attempt a refresh that cannot succeed.

    The `unavailable` row here is written by the REAL trigger
    (`context_dependents_note_au`), fired by the product's own soft delete --
    not by hand.  Beside it sits the positive control: a fresh consumer of the
    SAME record, which the same statement must mark, so a fence that
    over-reaches into "preserve everything" fails as loudly as the bug did.
    """
    rig.record(fact_id="first-fact")
    first = rig.promote(fact_id="first-fact")["promotion"]
    target = first["target_ref"]
    note_id = target.split(":", 1)[1]

    rig.record(fact_id="second-fact", quote="Rollbacks are rehearsed quarterly.")
    second = rig.promote(fact_id="second-fact", target_ref=target,
                         expected_target_revision=str(rig.db.notes.get(note_id).last_modified))["promotion"]

    gone = rig.dependent(target, "thought-gone")
    assert rig.db.notes.delete(note_id) is True
    # The product's own delete, through the shipped trigger.
    assert rig.dependent_state(target, gone) == "unavailable"
    live = rig.dependent(target, "thought-live")
    assert rig.dependent_state(target, live) == ""

    # A survivor remains, so this revocation computes ordinary staleness...
    one = rig.command({"kind": "revoke_promotion", "promotion_id": first["promotion_id"]})["promotion"]
    assert one["surviving_active_promotions"] == 1
    assert one["dependent_state"] == "stale"
    assert rig.dependent_state(target, live) == "stale"          # positive control
    assert rig.dependent_state(target, gone) == "unavailable"    # and the gap survives it

    # ...and the last revocation computes `forbidden`, which likewise does not
    # rewrite a record that is simply gone.
    two = rig.command({"kind": "revoke_promotion", "promotion_id": second["promotion_id"]})["promotion"]
    assert two["surviving_active_promotions"] == 0
    assert two["dependent_state"] == "forbidden"
    assert rig.dependent_state(target, live) == "forbidden"      # positive control
    assert rig.dependent_state(target, gone) == "unavailable"


def test_a_real_attachment_is_fenced_by_a_real_revocation(rig: Rig) -> None:
    """Lane B meets Lane C: no hand-written row anywhere in this test.

    Every other revoke test registers its consumer through `Rig.dependent`,
    which writes `context_dependents` by hand.  Here the row is written by the
    REAL reconcile point -- `RefinementContextService.attach_context` ->
    `_persist_manifest` -> `_reconcile_dependents` -- for a Thought that really
    attached the promoted Note, and the revocation runs through the real
    `InterviewService.command`.  A second Thought consuming a DIFFERENT
    promoted record is the positive control: the fence must reach the record
    that was revoked and no other.
    """
    from holdspeak.services.refinement_context_service import RefinementContextService
    from holdspeak.services.refinement_thought_service import (
        INBOX_DIRECTORY_ID, RefinementThoughtService,
    )

    rig.db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    thoughts = RefinementThoughtService(rig.db)
    contexts = RefinementContextService(rig.db)

    def consumer(ref: str, slug: str) -> str:
        thought = thoughts.create(
            OWNER, request_id=f"{slug}-capture", raw_text="Plan the cutover.",
            source={"kind": "typed"}, initial_note={"id": f"{slug}-working", "title": "Rough plan"},
        )
        contexts.attach_context(
            OWNER, thought["id"], visible_ref=ref, request_id=f"{slug}-attach",
            expected_aggregate_revision=thought["aggregate_revision"],
            expected_working_revision=thought["working_revision"],
            expected_attachment_revision=thought["attachment_revision"],
        )
        return str(thought["id"])

    rig.record(fact_id="revoked-fact")
    revoked_ref = rig.promote(fact_id="revoked-fact")["promotion"]
    rig.record(fact_id="kept-fact", quote="Rollbacks are rehearsed quarterly.")
    kept_ref = rig.promote(fact_id="kept-fact")["promotion"]["target_ref"]

    fenced = consumer(revoked_ref["target_ref"], "fenced")
    control = consumer(kept_ref, "control")

    # The row under test was written by `_reconcile_dependents`, not by the rig.
    row = rig.rows("SELECT * FROM context_dependents WHERE canonical_ref=? AND consumer_id=?",
                   (revoked_ref["target_ref"], fenced))[0]
    stored = rig.rows("SELECT attachment_sha256,attachment_revision FROM refinement_thoughts WHERE id=?",
                      (fenced,))[0]
    assert str(row["consumer_kind"]) == "thought"
    assert str(row["bound_manifest_sha256"]) == str(stored["attachment_sha256"])
    assert int(row["consumer_revision"]) == int(stored["attachment_revision"]) > 0
    assert str(row["stale_reason"]) == ""

    rig.command({"kind": "revoke_promotion", "promotion_id": revoked_ref["promotion_id"]})

    assert rig.dependent_state(revoked_ref["target_ref"], fenced) == "forbidden"
    assert rig.dependent_state(kept_ref, control) == ""


def test_removing_the_fact_does_not_revoke_its_promotion(rig: Rig) -> None:
    """The stated asymmetry: the Note is his now.

    Deliberate, and a surprise, so it is proved rather than left to be
    discovered: `remove_fact` drops the interview's copy and leaves the
    canonical record and its provenance standing.
    """
    rig.record()
    promoted = rig.promote()["promotion"]

    state = rig.command({"kind": "remove_fact", "fact_id": "goal"})

    assert state["facts"] == {}
    assert rig.svc.promotions(OWNER, rig.tid)[0]["disclosure_state"] == "active"
    assert rig.db.notes.get(promoted["target_ref"].split(":", 1)[1]).body_markdown == CONSTRAINT
    assert rig.rows("SELECT count(*) c FROM context_promotion_suppressions")[0]["c"] == 0


def test_deleting_the_source_message_leaves_the_promotion_naming_the_gap(rig: Rig) -> None:
    """The promotion is not derived from interview state, so it survives.

    The fact is pruned; the promotion stays and reads `source_unavailable`,
    which is only answerable because the locator and the hash were stored
    instead of the words.
    """
    source = rig.record()
    promoted = rig.promote()["promotion"]
    assert rig.svc.promotions(OWNER, rig.tid)[0]["state"] == "current"

    with rig.db._connection() as conn:
        conn.execute("UPDATE thread_messages SET deleted_at=? WHERE id=?", (1_800_000_000.0, source))

    assert rig.svc.get(rig.tid)["facts"] == {}
    view = rig.svc.promotions(OWNER, rig.tid)[0]
    assert view["state"] == "source_unavailable"
    assert view["source_available"] is False
    assert view["target_state"] == "current"
    assert view["promotion_id"] == promoted["promotion_id"]
    assert rig.db.notes.get(promoted["target_ref"].split(":", 1)[1]).body_markdown == CONSTRAINT


def test_a_promotion_reads_corrected_only_when_the_CONTENT_moved(rig: Rig) -> None:
    """P0-1 from the verb's side: the comparator is a content hash.

    `NoteRepository` writes `last_modified` unconditionally, so a digest folding
    the timestamp in would report a byte-identical re-save as `corrected` --
    telling him his constraint moved when it did not.
    """
    rig.record()
    promoted = rig.promote()["promotion"]
    note_id = promoted["target_ref"].split(":", 1)[1]

    rig.db.notes.upsert(note_id=note_id, title=TITLE, body_markdown=CONSTRAINT)
    assert rig.svc.promotions(OWNER, rig.tid)[0]["state"] == "current"

    rig.db.notes.upsert(note_id=note_id, title=TITLE,
                        body_markdown=CONSTRAINT + " Unless it is reversible in five minutes.")
    assert rig.svc.promotions(OWNER, rig.tid)[0]["state"] == "corrected"

    rig.db.notes.delete(note_id)
    assert rig.svc.promotions(OWNER, rig.tid)[0]["state"] == "unavailable"


# ── Transport ───────────────────────────────────────────────────────────

# The two verbs that mint or unmake a canonical record.  They belong to the
# owner's browser and to nothing else.
PROMOTION_KINDS = frozenset({"promote", "revoke_promotion"})


def _mcp_source_strings() -> tuple[set[str], int]:
    """Every string CONSTANT in the MCP package, and how many files were read.

    Equality, not substring: a docstring that says the word `promote` is not a
    finding, an event kind that IS `"promote"` is.  Read by AST over the whole
    package rather than off one family's ``TOOLS``, because a dispatcher in any
    family could name the kind.
    """
    import ast

    import holdspeak

    root = Path(holdspeak.__file__).parent / "mcp"
    files = sorted(root.rglob("*.py"))
    constants: set[str] = set()
    for path in files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                constants.add(node.value)
    return constants, len(files)


def _mcp_interview_kind_map() -> tuple[set[str], set[str]]:
    """The SHIPPING tool-name -> event-kind map, read out of `dispatch` by AST.

    Not a private constant the test could drift from: the literal the dispatcher
    actually indexes.  Returns (tool names it maps, event kinds it can produce).
    """
    import ast
    import inspect

    from holdspeak.mcp.families import interview as interview_family

    names: set[str] = set()
    kinds: set[str] = set()
    for node in ast.walk(ast.parse(inspect.getsource(interview_family))):
        if not isinstance(node, ast.Dict) or not node.keys:
            continue
        pairs = [
            (key.value, value.value)
            for key, value in zip(node.keys, node.values)
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
            and isinstance(value, ast.Constant) and isinstance(value.value, str)
        ]
        if len(pairs) != len(node.keys) or not pairs:
            continue
        if all(name.startswith("interview.") for name, _ in pairs):
            names |= {name for name, _ in pairs}
            kinds |= {kind for _, kind in pairs}
    return names, kinds


@pytest.mark.requires_meeting
def test_the_browser_route_admits_promotion_and_lists_it_back(tmp_path: Path) -> None:
    """AC4 needs a `promotion_id` the owner can reach, so a READ route ships.

    Without it `revoke_promotion` is unreachable: `promotion_id` existed only
    inside the single `promote` response, and `interview.get` does not carry
    promotions.  The route is owner-only in the same shape as the verbs -- the
    check lives in the SERVICE, proved here against an agent principal, not
    only in the handler.
    """
    from fastapi.testclient import TestClient

    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    reset_database()
    try:
        db = get_database(tmp_path / "transport.db")
        seed_modes(db)
        server = MeetingWebServer(WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None, on_stop=lambda *_a, **_k: None,
            get_state=lambda: None), host="127.0.0.1")
        client = TestClient(server.app)
        tid = client.post("/api/threads", json={"recipe_id": INTERVIEW_MODE_ID}).json()["id"]
        rig = Rig(db, tid)
        rig.record()

        empty = client.get(f"/api/threads/{tid}/interview/promotions")
        assert empty.status_code == 200, empty.text
        assert empty.json() == {"promotions": []}

        promote = client.post(f"/api/threads/{tid}/interview", json={
            "command_id": "route-promote", "expected_revision": rig.svc.get(tid)["revision"],
            "event": {"kind": "promote", "fact_id": "goal"}})
        assert promote.status_code == 200, promote.text
        promotion = promote.json()["promotion"]
        assert promotion["minted"] is True

        # The whole point of the route: the id the owner needs to revoke.
        listed = client.get(f"/api/threads/{tid}/interview/promotions")
        assert listed.status_code == 200, listed.text
        assert [row["promotion_id"] for row in listed.json()["promotions"]] == [promotion["promotion_id"]]
        assert listed.json()["promotions"][0]["disclosure_state"] == "active"

        revoke = client.post(f"/api/threads/{tid}/interview", json={
            "command_id": "route-revoke", "expected_revision": rig.svc.get(tid)["revision"],
            "event": {"kind": "revoke_promotion",
                      "promotion_id": listed.json()["promotions"][0]["promotion_id"]}})
        assert revoke.status_code == 200, revoke.text
        assert revoke.json()["promotion"]["revoked"] == "source_claim"
        after = client.get(f"/api/threads/{tid}/interview/promotions")
        assert after.json()["promotions"][0]["disclosure_state"] == "revoked"

        # A kind the MCP map HAS and the browser allowlist does not: the
        # allowlist is a real gate, not a comment.
        refused = client.post(f"/api/threads/{tid}/interview", json={
            "command_id": "route-fact", "expected_revision": rig.svc.get(tid)["revision"],
            "event": {"kind": "fact", "fact_id": "sneak", "text": "x", "basis": "stated",
                      "source_message_id": "m", "quote": "y"}})
        # The body matters, not just the code: admitting `fact` would ALSO
        # answer 400 (its own validation refuses the forged source message), so
        # a status-only assertion cannot tell the gate from the fallout.
        assert refused.status_code == 400, refused.text
        assert refused.json() == {"error": "Unsupported interview control"}

        # Owner-only, enforced where the verbs enforce it.
        with pytest.raises(ServiceError) as denied:
            InterviewService(db).promotions(AGENT, tid)
        assert denied.value.code == "owner_required"
    finally:
        reset_database()


@pytest.mark.requires_meeting
def test_no_mcp_tool_anywhere_can_mint_or_revoke_a_canonical_record() -> None:
    """Ruling C6 as amended, guarded over the WHOLE registry.

    The earlier guard read ONE family's ``TOOLS``, so a promote tool registered
    in any other family passed it.  Three assertions replace it: no tool name in
    the whole registry names these verbs; the two event kinds appear nowhere in
    the MCP package as string constants at all, so no dispatcher can name one;
    and the browser allowlist against the MCP kind map is pinned in both
    directions.

    The two surfaces are NOT wholly disjoint and the assertion says so honestly:
    `section` is legitimately on both -- the model may change section.  What
    must be disjoint is the promotion pair, and the rest of the relationship is
    pinned exactly rather than approximated.

    `requires_meeting` is still necessary: `holdspeak.mcp.tools` imports the web
    routers transitively (`holdspeak/web/routes/activity/__init__.py`), so the
    registry cannot be read at all without fastapi installed.
    """
    from holdspeak.mcp.tools import TOOLS
    from holdspeak.web.routes.threads import INTERVIEW_BROWSER_EVENT_KINDS

    names = {str(tool["name"]) for tool in TOOLS}
    # Non-vacuity: this is the real, whole registry.
    assert len(names) > 100 and {"interview.record_fact", "interview.get"} <= names
    assert not {name for name in names if "promot" in name or "revoke" in name}

    constants, scanned = _mcp_source_strings()
    # Non-vacuity: the scan does see event kinds where they exist.
    assert scanned > 10 and {"fact", "suggestion", "section"} <= constants
    assert PROMOTION_KINDS.isdisjoint(constants)

    mapped, mcp_kinds = _mcp_interview_kind_map()
    interview_names = {str(tool["name"]) for tool in TOOLS if str(tool["name"]).startswith("interview.")}
    # Non-vacuity: the map is the complete kind source for the family's verbs.
    assert mapped and mapped | {"interview.get"} == interview_names
    assert PROMOTION_KINDS <= INTERVIEW_BROWSER_EVENT_KINDS
    assert PROMOTION_KINDS.isdisjoint(mcp_kinds)
    assert INTERVIEW_BROWSER_EVENT_KINDS - mcp_kinds == {
        "remove_fact", "disposition", "status", "promote", "revoke_promotion"}
    assert mcp_kinds - INTERVIEW_BROWSER_EVENT_KINDS == {"fact", "suggestion"}
