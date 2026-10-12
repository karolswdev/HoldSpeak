"""HS-48-03: the one-tap right/wrong correction ritual.

The face half is vitest (web/src/pages/cores/dictation/__tests__/
speakFaceTeach.test.tsx, teachLoop.test.tsx). These tests exercise the
backend writes the ritual posts to.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.db import Database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def persistent_db():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "ritual.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _client(database: Database) -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    return TestClient(server.app)


# ── the path the ritual posts to still teaches (one decision, real write) ────

def test_ritual_correct_path_teaches_and_marks(persistent_db: Database, settings_path: Path) -> None:
    cfg = Config()
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=settings_path)
    rec = persistent_db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about launch", final_text="x"
    )
    # The "Wrong block -> action_item" one-tap path is a single POST.
    resp = _client(persistent_db).post(
        f"/api/dictation/journal/{rec.id}/correct", json={"kind": "intent", "value": "action_item"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["corrected"] is True and body["taught"] is True
    # the entry is now flagged corrected (the ritual hides the ask for these)
    assert persistent_db.dictation_journal.get(rec.id).corrected is True
    # and the correction landed in the store (teachable across restarts)
    stored = persistent_db.dictation_corrections.recent_corrections()
    assert any(r.kind == "intent" and r.value == "action_item" for r in stored)


# ── HS-101 B3: edit the transcript record in place (the smallest write) ──────

def test_journal_transcript_edit_in_place(persistent_db: Database, settings_path: Path) -> None:
    Config().save(path=settings_path)
    rec = persistent_db.dictation_journal.record(
        source="dictation", transcript="ship the native winners brief", final_text="x"
    )
    client = _client(persistent_db)
    resp = client.put(
        f"/api/dictation/journal/{rec.id}", json={"transcript": "ship the Native Innards brief"}
    )
    assert resp.status_code == 200 and resp.json()["updated"] is True
    assert (
        persistent_db.dictation_journal.get(rec.id).transcript
        == "ship the Native Innards brief"
    )
    # an emptied record refuses rather than blanking (Article VI)
    refuse = client.put(f"/api/dictation/journal/{rec.id}", json={"transcript": "   "})
    assert refuse.status_code == 422
    # a missing entry names itself
    gone = client.put("/api/dictation/journal/999999", json={"transcript": "y"})
    assert gone.status_code == 404
    # editing never fakes a correction: the taught act stays separate
    assert persistent_db.dictation_journal.get(rec.id).corrected is False
