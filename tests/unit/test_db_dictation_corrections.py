"""HS-40-02: DictationCorrectionRepository — persistence for dictation memory."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from holdspeak.db import Database, reset_database


@pytest.fixture
def db() -> Database:
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "corrections.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_record_and_recent_round_trip(db: Database) -> None:
    repo = db.dictation_corrections
    rec = repo.record_correction(kind="intent", gist="fix the cli thing", value="code_exercise")
    assert rec.id > 0
    assert rec.kind == "intent"
    assert rec.gist == "fix the cli thing"
    assert rec.value == "code_exercise"
    assert rec.created_at

    recent = repo.recent_corrections()
    assert len(recent) == 1
    assert recent[0].value == "code_exercise"


def test_recent_is_newest_first_and_limited(db: Database) -> None:
    repo = db.dictation_corrections
    for i in range(5):
        repo.record_correction(kind="intent", gist=f"utterance {i}", value=f"block_{i}")
    recent = repo.recent_corrections(limit=3)
    assert [r.value for r in recent] == ["block_4", "block_3", "block_2"]


def test_record_rejects_bad_kind_and_empty(db: Database) -> None:
    repo = db.dictation_corrections
    with pytest.raises(ValueError):
        repo.record_correction(kind="nonsense", gist="x", value="y")
    with pytest.raises(ValueError):
        repo.record_correction(kind="intent", gist="   ", value="y")
    with pytest.raises(ValueError):
        repo.record_correction(kind="intent", gist="x", value="")
    assert repo.recent_corrections() == []


def test_delete_and_clear(db: Database) -> None:
    repo = db.dictation_corrections
    a = repo.record_correction(kind="target", gist="route this", value="codex_cli")
    repo.record_correction(kind="intent", gist="and this", value="code_exercise")
    assert repo.delete_correction(a.id) is True
    assert repo.delete_correction(a.id) is False  # already gone
    assert len(repo.recent_corrections()) == 1
    removed = repo.clear()
    assert removed == 1
    assert repo.recent_corrections() == []


def test_persists_across_a_fresh_container(db: Database) -> None:
    """A new Database over the same file sees the prior corrections."""
    db.dictation_corrections.record_correction(
        kind="intent", gist="restart survivor", value="code_exercise"
    )
    reopened = Database(db.db_path)
    recent = reopened.dictation_corrections.recent_corrections()
    assert len(recent) == 1
    assert recent[0].gist == "restart survivor"
