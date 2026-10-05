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
