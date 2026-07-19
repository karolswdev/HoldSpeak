"""HS-48-03: the one-tap right/wrong correction ritual.

The React ritual keeps "Right" client-only and lets "Wrong" disclose the
existing teach path. These assertions pin the typed source contract and
exercise the backend write it uses.
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

_SOURCE = Path(__file__).resolve().parents[2] / "web/src/pages/cores/DictationCore.tsx"


def _dictation_script() -> str:
    return _SOURCE.read_text()


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


# ── the ritual ships + is wired into both surfaces ───────────────────────────

def test_ritual_component_is_shipped() -> None:
    js = _dictation_script()
    for marker in ("Right", "Wrong", "Correct this result", "Teach correction"):
        assert marker in js, marker
    assert "/api/dictation/journal/" in js and "/correct" in js


def test_ritual_is_wired_into_dry_run_result() -> None:
    js = _dictation_script()
    assert 'setVerdict("right")' in js and 'setVerdict("wrong")' in js
    assert "journal_id" in js


def test_ritual_is_focus_safe() -> None:
    # The standing dictation invariant: zero programmatic focus theft.
    assert ".focus()" not in _dictation_script()


def test_ritual_uses_shared_react_controls() -> None:
    source = _dictation_script()
    assert "<Button" in source and "<Disclosure" in source
    assert "dangerouslySetInnerHTML" not in source


def test_dry_run_moment_host_present(persistent_db: Database, settings_path: Path) -> None:
    Config().save(path=settings_path)
    response = _client(persistent_db).get("/dictation")
    assert '<div id="root"></div>' in response.text
    source = (Path(__file__).resolve().parents[2] / "web/src/pages/cores/DictationCore.tsx").read_text()
    assert "Pipeline result" in source and "/api/dictation/dry-run" in source
    assert "autofocus" not in source.lower()


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
