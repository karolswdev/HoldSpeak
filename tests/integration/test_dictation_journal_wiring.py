"""HS-45-01: the dry-run path journals through the recorder (no mic, offline).

Drives the real browser dry-run executor (`_run_dictation_dry_run_text`) — the
same function `/api/dictation/dry-run` calls — with the pipeline enabled over a
seeded local project, and asserts:

- a real run persists exactly one `source='dry_run'` journal row carrying the
  transcript, routing, final text, and per-stage latency;
- `journal_enabled=False` writes **no** row *and* the returned `final_text` is
  byte-identical (the journal is a pure side-channel);
- no LLM endpoint is needed — the intent-router scores lexically.
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from holdspeak.config import (
    Config,
    DictationConfig,
    DictationPipelineConfig,
    LLMRuntimeConfig,
)
from holdspeak.db import Database
from holdspeak.plugins.dictation.journal import DictationJournalRecorder
from holdspeak.web.routes.dictation._helpers import _run_dictation_dry_run_text


_BLOCKS_YAML = dedent(
    """
    version: 1
    default_match_confidence: 0.6
    blocks:
      - id: deploy_block
        description: Deploy-intent test block
        match:
          examples:
            - "deploy this branch to production"
        inject:
          mode: replace
          template: "[deploy in {project.name}] {raw_text}"
    """
).strip()


def _seed_project(tmp_path: Path) -> Path:
    root = tmp_path / "myproj"
    (root / ".holdspeak").mkdir(parents=True)
    (root / ".holdspeak" / "blocks.yaml").write_text(_BLOCKS_YAML, encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname = "myproj"\n', encoding="utf-8")
    return root


def _config(*, journal_enabled: bool) -> Config:
    return Config(
        dictation=DictationConfig(
            pipeline=DictationPipelineConfig(
                enabled=True,
                stages=["kb-enricher"],  # runs offline (no runtime needed)
                journal_enabled=journal_enabled,
                journal_retention=500,
            ),
            runtime=LLMRuntimeConfig(),  # no endpoint; intent-router is lexical
        )
    )


def _run(tmp_path, monkeypatch, *, journal_enabled: bool):
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _seed_project(tmp_path)
    monkeypatch.setattr(Config, "load", classmethod(lambda cls, *a, **k: _config(journal_enabled=journal_enabled)))

    db = Database(tmp_path / "journal.db")
    recorder = DictationJournalRecorder(repository=db.dictation_journal)
    result = _run_dictation_dry_run_text(
        "deploy this branch to production",
        str(root),
        None,
        suggestions={},
        journal=recorder,
    )
    return db, result


def test_dry_run_persists_one_journal_row(tmp_path, monkeypatch) -> None:
    db, result = _run(tmp_path, monkeypatch, journal_enabled=True)

    rows = db.dictation_journal.recent()
    assert len(rows) == 1
    row = rows[0]
    assert row.source == "dry_run"
    assert row.transcript == "deploy this branch to production"
    assert row.final_text == result["final_text"]
    # the kb-enricher stage's latency was captured (offline, no runtime)
    assert "kb-enricher" in row.stage_ms
    assert row.total_ms == pytest.approx(result["total_elapsed_ms"])


def test_journal_disabled_writes_nothing_and_output_is_byte_identical(
    tmp_path, monkeypatch
) -> None:
    db_off, result_off = _run(tmp_path / "off", monkeypatch, journal_enabled=False)
    assert db_off.dictation_journal.count() == 0

    db_on, result_on = _run(tmp_path / "on", monkeypatch, journal_enabled=True)
    # Journaling on vs off must not change a single byte of what gets typed.
    assert result_off["final_text"] == result_on["final_text"]
    assert db_on.dictation_journal.count() == 1
