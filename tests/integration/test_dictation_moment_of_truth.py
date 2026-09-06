"""HS-45-03: the moment of truth — correct a journaled run in flow, and teach.

`POST /api/dictation/journal/{id}/correct` records a correction (reusing the
Phase-40 store, so future routing is nudged) keyed on the entry's own
transcript, then flips the journal entry's `corrected` flag and links the
correction. Covers: the flag flips, the teach is the same kind the Memory tab
manages and would nudge a similar utterance (the intent-router nudge path), the
dry-run carries a `journal_id`, secret-like transcripts don't teach, and the
in-moment affordance is focus-safe.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import (
    Config,
    DictationConfig,
    DictationPipelineConfig,
    LLMRuntimeConfig,
)
from holdspeak.db import Database, reset_database
from holdspeak.kernel.runtime import _configure
from holdspeak.plugins.dictation.corrections import best_match_in
from holdspeak.plugins.dictation.journal import DictationJournalRecorder
from holdspeak.web.routes.dictation._helpers import _run_dictation_dry_run_text
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
    database = Database(temp_dir / "journal.db")
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


# ── correct-attach endpoint ────────────────────────────────────────────

def test_correct_flips_flag_and_records_correction(
    persistent_db: Database, settings_path: Path
) -> None:
    entry = persistent_db.dictation_journal.record(
        source="dry_run",
        transcript="ship the new billing flow to the agent",
        final_text="...",
        block_id="quick_note",
        target_profile="notes",
    )
    client = _client(persistent_db)
    resp = client.post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "intent", "value": "agent_task_buildout"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["corrected"] is True
    assert body["taught"] is True
    assert body["correction_id"] is not None

    # the journal entry is now flagged + linked
    after = persistent_db.dictation_journal.get(entry.id)
    assert after.corrected is True
    assert after.correction_id == body["correction_id"]

    # the correction is durable + keyed on the entry's transcript
    stored = persistent_db.dictation_corrections.recent_corrections()
    assert len(stored) == 1
    assert stored[0].kind == "intent"
    assert stored[0].value == "agent_task_buildout"
    assert stored[0].gist == "ship the new billing flow to the agent"


def test_correction_nudges_a_similar_future_utterance(
    persistent_db: Database, settings_path: Path
) -> None:
    """The teach is real: a similar later utterance matches the corrected block
    via the same Jaccard nudge the intent-router uses."""
    entry = persistent_db.dictation_journal.record(
        source="dry_run", transcript="ship the new billing flow to the agent", final_text="x"
    )
    client = _client(persistent_db)
    client.post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "intent", "value": "agent_task_buildout"},
    )
    # The server's live correction store now carries the teach (write-through).
    listed = client.get("/api/dictation/corrections").json()
    assert listed["size"] == 1
    # The intent-router nudge path: a similar utterance resolves to the block.
    from holdspeak.plugins.dictation.corrections import Correction

    corrections = [
        Correction(kind=it["kind"], key=it["key"], value=it["value"], sequence=i)
        for i, it in enumerate(listed["items"])
    ]
    match = best_match_in(corrections, "intent", "please ship the billing flow to the agent now")
    assert match is not None
    assert match.value == "agent_task_buildout"


def test_correct_missing_entry_404(persistent_db: Database, settings_path: Path) -> None:
    client = _client(persistent_db)
    resp = client.post("/api/dictation/journal/9999/correct", json={"kind": "intent", "value": "b"})
    assert resp.status_code == 404


def test_correct_rejects_bad_kind(persistent_db: Database, settings_path: Path) -> None:
    entry = persistent_db.dictation_journal.record(
        source="dry_run", transcript="t", final_text="f"
    )
    client = _client(persistent_db)
    resp = client.post(
        f"/api/dictation/journal/{entry.id}/correct", json={"kind": "nope", "value": "b"}
    )
    assert resp.status_code == 400


def test_correct_secret_transcript_teaches_nothing_and_writes_nothing(
    persistent_db: Database, settings_path: Path
) -> None:
    """HS-176-02 (R4): a refused teach writes NOTHING.

    Through Phase 175 `mark_corrected` fired outside `if recorded`, so a secret
    gist that was never stored still flipped the row's `corrected` flag and
    linked whatever correction happened to be newest. The row now stays clean
    and the response names the refusal.
    """
    # The journal redacts secrets, so a real entry can't carry one — but assert
    # the teach path itself drops a secret-like gist.
    entry = persistent_db.dictation_journal.record(
        source="dry_run", transcript="token is sk-abcdef0123456789abcd", final_text="x"
    )
    client = _client(persistent_db)
    resp = client.post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "intent", "value": "agent_task_buildout"},
    )
    body = resp.json()
    assert body["corrected"] is False
    assert body["recorded"] is False and body["taught"] is False  # secret gist → not stored
    assert body["reason"] == "secret"
    assert body["correction_id"] is None
    assert persistent_db.dictation_corrections.recent_corrections() == []
    row = persistent_db.dictation_journal.get(entry.id)
    assert row.corrected is False and row.correction_id is None


# ── dry-run carries a journal_id ───────────────────────────────────────

_BLOCKS = dedent(
    """
    version: 1
    default_match_confidence: 0.6
    blocks:
      - id: note_block
        description: a note block
        match: {examples: ["jot this down"]}
        inject: {mode: replace, template: "{raw_text}"}
    """
).strip()


def test_dry_run_returns_journal_id(persistent_db: Database, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / "proj"
    (root / ".holdspeak").mkdir(parents=True)
    (root / ".holdspeak" / "blocks.yaml").write_text(_BLOCKS, encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname="proj"\n', encoding="utf-8")
    config = Config(
        dictation=DictationConfig(
            pipeline=DictationPipelineConfig(enabled=True, stages=["kb-enricher"]),
            runtime=LLMRuntimeConfig(),
        )
    )
    monkeypatch.setattr(
        Config, "load", classmethod(lambda cls, *a, **k: config)
    )
    monkeypatch.setattr("holdspeak.db.get_database", lambda: persistent_db)
    _configure(persistent_db)
    recorder = DictationJournalRecorder(repository=persistent_db.dictation_journal)
    result = _run_dictation_dry_run_text(
        "jot this down",
        str(root),
        None,
        suggestions={},
        config_snapshot=config,
        admission=None,
        fence=None,
        journal=recorder,
    )
    assert result["journal_id"] is not None
    assert persistent_db.dictation_journal.get(result["journal_id"]) is not None


# ── focus-safe in-moment affordance ────────────────────────────────────

def test_moment_affordance_present_and_focus_safe(persistent_db: Database) -> None:
    client = _client(persistent_db)
    body = client.get("/dictation").text
    assert '<div id="root"></div>' in body
    # The in-moment affordance lives with the result panel the core renders
    # (it moved out of DictationCore.tsx when the core was split); the surface is
    # both files, so both are read.
    root = Path(__file__).resolve().parents[2] / "web/src/pages/cores"
    source = "\n".join(
        [(root / "DictationCore.tsx").read_text()]
        + [part.read_text() for part in sorted((root / "dictation").glob("*.ts*"))]
    )
    assert "Correct this result" in source
    assert "Teach correction" in source
    assert "/api/dictation/corrections" in source
    # Focus-safe: the in-moment surface must never auto-focus an input (the same
    # invariant as desktop presence — the dictation flow is sacred).
    assert "autofocus" not in source.lower()
    assert ".focus()" not in source
