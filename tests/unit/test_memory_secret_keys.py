"""A secret is never a search key, and never reaches a model through a
source attached by hand (the open items of #830 and #852, 2026-10-05).

Every source is written by its real producer (the note, meeting and thread
repositories).  The search is the real ``MemoryRepository.search``; the
hydration is the real ``grounding`` path a chat turn and Ask use.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.grounding import hydrate_refs_detailed, live_block
from holdspeak.meeting_session.models import MeetingState, TranscriptSegment

BODY = "Q7xLm2Vp9RtK4wZs8NbY"
SECRET = f"ghp_{BODY}"


def _note(db: Database) -> str:
    db.notes.upsert(note_id="n-key", title="Deploy", body_markdown=f"Atlas deploy token is {SECRET} for now.")
    return "note:n-key"


def _meeting(db: Database) -> str:
    started = datetime(2026, 10, 5, 10, 0, 0)
    db.meetings.save_meeting(MeetingState(
        id="m-key", started_at=started, ended_at=started, title="Atlas deploy sync",
        segments=[TranscriptSegment(text=f"Use {SECRET} for the Atlas deploy.", speaker="Dana",
                                    start_time=0.0, end_time=1.0)],
    ))
    return "meeting:m-key"


def _thread(db: Database) -> str:
    thread = db.threads.create_thread(title="Atlas deploy")
    message = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(message.id, kind="text", text=f"Atlas deploy key {SECRET} works.")
    return f"thread:{thread.id}"


SOURCES = {"note": _note, "meeting": _meeting, "thread": _thread}


def _found(db: Database, query: str) -> list[str]:
    return [hit.source_ref.split("#", 1)[0] for hit in db.memory.search(query).hits]


@pytest.mark.parametrize("kind", sorted(SOURCES))
def test_a_secret_is_never_a_search_key(tmp_path: Path, kind: str) -> None:
    db = Database(tmp_path / "keys.db")
    ref = SOURCES[kind](db)
    # The source is found by its plain words, with the secret redacted.
    hits = db.memory.search("Atlas deploy").hits
    assert ref in [hit.source_ref.split("#", 1)[0] for hit in hits]
    assert all(SECRET not in hit.snippet and BODY not in hit.snippet for hit in hits)
    # The secret, whole or its body alone, finds nothing.
    assert ref not in _found(db, SECRET)
    assert ref not in _found(db, BODY)
    assert ref not in _found(db, f"{BODY} weather")  # with a word no source holds


@pytest.mark.parametrize("kind", sorted(SOURCES))
def test_a_source_attached_by_hand_is_redacted_before_a_model_reads_it(tmp_path: Path, kind: str) -> None:
    db = Database(tmp_path / "attach.db")
    ref = SOURCES[kind](db)
    result = hydrate_refs_detailed(db, [], [], "full", qualified_refs=[ref])
    assert result.blocks and not result.unknown
    text = "\n".join(block.title + "\n" + block.text for block in result.blocks)
    assert "Atlas" in text and SECRET not in text and BODY not in text
    # The later turn's replay of a block he named (the hand-attach rule).
    replay = live_block(db, ref, via="")
    assert replay is not None and BODY not in replay.text


def test_a_meeting_attached_by_id_is_redacted(tmp_path: Path) -> None:
    db = Database(tmp_path / "attach-id.db")
    _meeting(db)
    for expand in ("summary", "full"):
        result = hydrate_refs_detailed(db, ["m-key"], [], expand)
        assert result.blocks and BODY not in result.blocks[0].text


# ── Astra, #871 round 2: the check uses the search's own matcher ─────────


def test_a_piece_of_a_secret_finds_nothing_in_a_substring_kind(tmp_path: Path) -> None:
    """A canonical-store kind (an action item) is matched by LIKE, a
    substring: a piece of the secret found it.  The redacted text does not
    hold the piece, so the hit is dropped; its public words still find it."""
    from tests.unit.test_memory_every_job import _meeting_with_action

    db = Database(tmp_path / "piece.db")
    action = _meeting_with_action(db, "m-rotate", f"Rotate {SECRET} on the Atlas deploy")
    ref = f"action:{action}"
    assert ref in _found(db, "Rotate Atlas deploy")
    for piece in (BODY[:8], BODY, SECRET):
        assert not [hit for hit in _found(db, piece) if "m-rotate" in hit], piece  # the action and its meeting


def test_an_accent_folded_secret_finds_nothing(tmp_path: Path) -> None:
    """FTS5 folds accents: "cafe" matched "password=café"."""
    db = Database(tmp_path / "accent.db")
    db.notes.upsert(note_id="n-cafe", title="Weather", body_markdown="Atlas weather report. password=café")
    assert "note:n-cafe" not in _found(db, "cafe")
    assert "note:n-cafe" in _found(db, "Atlas weather")


def test_a_public_word_still_finds_a_source_that_holds_a_secret(tmp_path: Path) -> None:
    """The query is OR: "Atlas quorumdb" finds the note by its public
    "Atlas", though "quorumdb" is only inside the secret."""
    db = Database(tmp_path / "public.db")
    db.notes.upsert(note_id="n-q", title="Weather", body_markdown="Atlas weather report. password=quorumdb")
    assert "note:n-q" in _found(db, "Atlas quorumdb")
    assert "note:n-q" not in _found(db, "quorumdb")


def test_a_schema_with_token_and_api_key_fields_is_not_redacted(tmp_path: Path) -> None:
    """Astra, #871: a label followed by a type or an identifier is not a
    secret.  A real value after the same label still is."""
    from holdspeak.memory.defense import redact

    schema = "Atlas compiler schema: token: Identifier; api_key: Optional[str]."
    assert redact(schema) == schema
    assert redact("token: str, password: bool") == "token: str, password: bool"
    for real in ("api_key: sk-abcdefghijklmnopqrstuvwx", "token=hunter2", "password: fluffy",
                 f"token: {SECRET}", "Authorization: Bearer abcdefghijklmnopqrstuvwxyz"):
        assert "[redacted]" in redact(real) and "hunter2" not in redact(real) and BODY not in redact(real), real
    db = Database(tmp_path / "schema.db")
    db.notes.upsert(note_id="n-schema", title="Compiler", body_markdown=schema)
    result = hydrate_refs_detailed(db, [], [], "full", qualified_refs=["note:n-schema"])
    assert schema in result.blocks[0].text  # attached by hand: the schema reaches the model whole
