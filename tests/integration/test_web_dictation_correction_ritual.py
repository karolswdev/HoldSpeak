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

_REPO = Path(__file__).resolve().parents[2]
_DECK_DIR = _REPO / "web/src/pages/cores/dictation"
# HS-132-12: HS-117-08 decomposed the cockpit — the ritual itself lives in
# dictation/ResultPanel.tsx and the wire it posts to in dictation/useSpeakDeck.ts.
_RITUAL = _DECK_DIR / "ResultPanel.tsx"
_DECK_WIRE = _DECK_DIR / "useSpeakDeck.ts"


def _ritual_source() -> str:
    return _RITUAL.read_text()


def _wire_source() -> str:
    return _DECK_WIRE.read_text()


def _dictation_script() -> str:
    """The whole Dictation program: the shell plus every sub-component."""
    parts = [(_REPO / "web/src/pages/cores/DictationCore.tsx").read_text()]
    for source in sorted(_DECK_DIR.glob("*.ts*")):
        if source.name.endswith(".test.tsx"):
            continue
        parts.append(source.read_text())
    return "\n".join(parts)


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
    ritual = _ritual_source()
    # HS-111-01 renamed the affirm verb Right → OK; the one-tap ritual,
    # the disclose path, and the teach POST are unchanged.
    for marker in ("Marked OK", "Wrong", "Correct this result", "Teach correction"):
        assert marker in ritual, marker
    wire = _wire_source()
    assert "/api/dictation/journal/" in wire and "/correct" in wire


def test_ritual_is_wired_into_dry_run_result() -> None:
    ritual = _ritual_source()
    assert 'setVerdict("right")' in ritual and 'setVerdict("wrong")' in ritual
    assert "journal_id" in _wire_source()


def test_ritual_is_focus_safe() -> None:
    # The standing dictation invariant: zero programmatic focus theft.
    assert ".focus()" not in _dictation_script()


def test_ritual_uses_shared_react_controls() -> None:
    # HS-111-08: the Disclosure species retired; FoldGadget is the ONE
    # disclosure the shared kit provides.
    ritual = _ritual_source()
    assert "<Button" in ritual and "<FoldGadget" in ritual
    assert "dangerouslySetInnerHTML" not in _dictation_script()


def test_dry_run_moment_host_present(persistent_db: Database, settings_path: Path) -> None:
    Config().save(path=settings_path)
    response = _client(persistent_db).get("/dictation")
    assert '<div id="root"></div>' in response.text
    assert "Pipeline result" in _ritual_source()
    assert "/api/dictation/dry-run" in _wire_source()
    assert "autofocus" not in _dictation_script().lower()


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
