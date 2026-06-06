"""HS-45-04: replay — re-run a stored utterance through the current pipeline.

`POST /api/dictation/journal/{id}/replay` re-runs the entry's stored transcript
through the dry-run pipeline (no typing, no new journal row) and returns a
before → after diff. The payoff: correct an utterance's target, replay it, and
the routing demonstrably changes — proven offline (no mic, no LLM) via the
target-correction nudge the dry-run applies.
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
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


_BLOCKS = dedent(
    """
    version: 1
    default_match_confidence: 0.6
    blocks:
      - id: quick_note
        description: a note block
        match: {examples: ["jot this down"]}
        inject: {mode: replace, template: "{raw_text}"}
    """
).strip()


@pytest.fixture
def proj(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    root = tmp_path / "proj"
    (root / ".holdspeak").mkdir(parents=True)
    (root / ".holdspeak" / "blocks.yaml").write_text(_BLOCKS, encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname="proj"\n', encoding="utf-8")
    return root


def _use_config(monkeypatch, *, corrections_enabled: bool) -> None:
    monkeypatch.setattr(
        Config,
        "load",
        classmethod(
            lambda cls, *a, **k: Config(
                dictation=DictationConfig(
                    pipeline=DictationPipelineConfig(
                        enabled=True,
                        stages=["kb-enricher"],  # runs offline (no runtime)
                        corrections_enabled=corrections_enabled,
                    ),
                    runtime=LLMRuntimeConfig(),
                )
            )
        ),
    )


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


def test_replay_reruns_transcript_without_typing_or_new_row(
    persistent_db: Database, proj: Path, monkeypatch
) -> None:
    _use_config(monkeypatch, corrections_enabled=False)
    entry = persistent_db.dictation_journal.record(
        source="dictation",
        transcript="jot this down for later",
        final_text="jot this down for later",
        target_profile="terminal",
        project_root=str(proj),
    )
    before_count = persistent_db.dictation_journal.count()
    client = _client(persistent_db)
    resp = client.post(f"/api/dictation/journal/{entry.id}/replay")
    assert resp.status_code == 200
    body = resp.json()
    assert body["entry_id"] == entry.id
    assert "before" in body and "after" in body
    assert body["after"]["final_text"]  # a fresh pipeline result came back
    # Replay never journals a new row and never mutates the original.
    assert persistent_db.dictation_journal.count() == before_count
    assert persistent_db.dictation_journal.get(entry.id).target_profile == "terminal"


def test_replay_after_target_correction_changes_routing(
    persistent_db: Database, proj: Path, monkeypatch
) -> None:
    """The payoff: correct the target, replay, and the routing changes — offline."""
    _use_config(monkeypatch, corrections_enabled=True)
    entry = persistent_db.dictation_journal.record(
        source="dictation",
        transcript="send the weekly digest to the browser tab",
        final_text="send the weekly digest to the browser tab",
        target_profile="terminal_shell",
        project_root=str(proj),
    )
    client = _client(persistent_db)

    # baseline replay — no correction yet
    base = client.post(f"/api/dictation/journal/{entry.id}/replay").json()
    base_target = base["after"]["target_profile"]

    # correct the target for this utterance (in-moment teach, HS-45-03)
    client.post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "target", "value": "browser"},
    )

    # replay again — the target-correction nudge redirects the routed target
    after = client.post(f"/api/dictation/journal/{entry.id}/replay").json()
    assert after["after"]["target_profile"] == "browser"
    assert after["after"]["target_profile"] != base_target
    assert after["changed"] is True


def test_replay_missing_entry_404(persistent_db: Database, proj: Path, monkeypatch) -> None:
    _use_config(monkeypatch, corrections_enabled=False)
    client = _client(persistent_db)
    assert client.post("/api/dictation/journal/9999/replay").status_code == 404


def test_replay_without_repo_404(monkeypatch) -> None:
    monkeypatch.setattr(config_module, "CONFIG_FILE", Path(tempfile.mkdtemp()) / "c.json")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        )
    )
    client = TestClient(server.app)
    assert client.post("/api/dictation/journal/1/replay").status_code == 404


def test_journal_card_has_replay_action(persistent_db: Database) -> None:
    """The Replay action + before/after styles ship in the page/bundle."""
    client = _client(persistent_db)
    body = client.get("/dictation").text
    built = (
        Path(__file__).resolve().parents[2]
        / "holdspeak" / "static" / "_built" / "_astro"
    )
    js = "\n".join(p.read_text() for p in built.glob("dictation.astro_astro_type_script*.js"))
    assert "data-journal-replay" in js  # the per-entry Replay action
    assert "replayJournalEntry" in js
    css = "\n".join(p.read_text() for p in built.glob("dictation*.css"))
    assert "replay-row" in css  # the before/after diff styles
    # Re-insert is focus-safe: preview + copy, never OS-typing from the web.
    assert "Preview only" in js
