"""HS-45-01: the dictation journal — repository + recorder unit tests.

Covers the persistence spine the rest of Phase 45 reads/writes: record/list/
get/delete/wipe, retention prune-on-insert, source tagging + filtering, the
`mark_corrected` linkage HS-45-03 uses, and the `DictationJournalRecorder`
bridge (PipelineRun extraction, secret redaction, the disabled / no-repository
no-op, and best-effort failure swallowing).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.plugins.dictation.journal import (
    DictationJournalRecorder,
    extract_stage_ms,
    filter_secret,
)


@pytest.fixture()
def db(tmp_path) -> Database:
    return Database(tmp_path / "journal.db")


# --- repository ------------------------------------------------------------

def test_record_and_get_round_trips_every_field(db: Database) -> None:
    rec = db.dictation_journal.record(
        source="dictation",
        transcript="add idempotency to charge",
        final_text="Add an idempotency key to POST /charge.",
        intent="agent_task",
        block_id="agent_task_buildout",
        target_profile="terminal",
        project_root="/work/ledger",
        stage_ms={"intent-router": 12.5, "project-rewriter": 880.0},
        total_ms=905.3,
        rewrite_pass_ms=[400.0, 480.0],
        confidence=0.82,
        warnings=["intent-router: low confidence"],
        retention=500,
    )
    assert rec.id > 0
    fetched = db.dictation_journal.get(rec.id)
    assert fetched is not None
    assert fetched.source == "dictation"
    assert fetched.transcript == "add idempotency to charge"
    assert fetched.final_text == "Add an idempotency key to POST /charge."
    assert fetched.intent == "agent_task"
    assert fetched.block_id == "agent_task_buildout"
    assert fetched.target_profile == "terminal"
    assert fetched.project_root == "/work/ledger"
    assert fetched.stage_ms == {"intent-router": 12.5, "project-rewriter": 880.0}
    assert fetched.total_ms == pytest.approx(905.3)
    assert fetched.rewrite_pass_ms == [400.0, 480.0]
    assert fetched.confidence == pytest.approx(0.82)
    assert fetched.warnings == ["intent-router: low confidence"]
    assert fetched.corrected is False
    assert fetched.correction_id is None


def test_unknown_source_rejected(db: Database) -> None:
    with pytest.raises(ValueError):
        db.dictation_journal.record(source="bogus", transcript="x", final_text="y")


def test_recent_is_newest_first_and_source_filterable(db: Database) -> None:
    db.dictation_journal.record(source="dictation", transcript="one", final_text="1")
    db.dictation_journal.record(source="dry_run", transcript="two", final_text="2")
    db.dictation_journal.record(source="dictation", transcript="three", final_text="3")

    all_rows = db.dictation_journal.recent()
    assert [r.transcript for r in all_rows] == ["three", "two", "one"]

    only_dry = db.dictation_journal.recent(source="dry_run")
    assert [r.transcript for r in only_dry] == ["two"]

    limited = db.dictation_journal.recent(limit=2)
    assert [r.transcript for r in limited] == ["three", "two"]


def test_retention_prunes_to_last_n_on_insert(db: Database) -> None:
    for i in range(10):
        db.dictation_journal.record(
            source="dictation",
            transcript=f"utt {i}",
            final_text=f"out {i}",
            retention=3,
        )
    rows = db.dictation_journal.recent()
    assert db.dictation_journal.count() == 3
    # Only the three most recent survive.
    assert [r.transcript for r in rows] == ["utt 9", "utt 8", "utt 7"]


def test_delete_and_clear(db: Database) -> None:
    a = db.dictation_journal.record(source="dictation", transcript="a", final_text="A")
    b = db.dictation_journal.record(source="dictation", transcript="b", final_text="B")
    assert db.dictation_journal.delete(a.id) is True
    assert db.dictation_journal.delete(a.id) is False  # already gone
    assert db.dictation_journal.count() == 1
    assert db.dictation_journal.get(b.id) is not None
    removed = db.dictation_journal.clear()
    assert removed == 1
    assert db.dictation_journal.count() == 0


def test_mark_corrected_sets_flag_and_links_correction(db: Database) -> None:
    rec = db.dictation_journal.record(
        source="dictation", transcript="route me", final_text="routed"
    )
    assert db.dictation_journal.mark_corrected(rec.id, correction_id=42) is True
    after = db.dictation_journal.get(rec.id)
    assert after is not None
    assert after.corrected is True
    assert after.correction_id == 42
    assert db.dictation_journal.mark_corrected(9999) is False  # missing row


# --- recorder bridge -------------------------------------------------------

@dataclass(frozen=True)
class _FakeIntent:
    matched: bool = True
    block_id: str | None = "agent_task_buildout"
    confidence: float = 0.91
    raw_label: str | None = "agent_task"
    extras: dict = field(default_factory=dict)


@dataclass(frozen=True)
class _FakeStage:
    stage_id: str
    elapsed_ms: float
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class _FakeRun:
    final_text: str
    stage_results: list
    intent: Any
    warnings: list
    total_elapsed_ms: float


@dataclass(frozen=True)
class _FakeTarget:
    id: str


def _sample_run(final_text: str = "Enriched task.") -> _FakeRun:
    return _FakeRun(
        final_text=final_text,
        stage_results=[
            _FakeStage("intent-router", 8.0),
            _FakeStage(
                "project-rewriter",
                900.0,
                metadata={"rewrite_pass_ms": [430.0, 470.0]},
            ),
        ],
        intent=_FakeIntent(),
        warnings=["intent-router: heads up"],
        total_elapsed_ms=908.0,
    )


def test_extract_stage_ms_mirrors_telemetry() -> None:
    stage_ms, passes = extract_stage_ms(_sample_run())
    assert stage_ms == {"intent-router": 8.0, "project-rewriter": 900.0}
    assert passes == [430.0, 470.0]


def test_recorder_persists_run_with_context(db: Database) -> None:
    recorder = DictationJournalRecorder(repository=db.dictation_journal)
    wrote = recorder.record(
        _sample_run(),
        source="dry_run",
        transcript="add idempotency",
        target_profile=_FakeTarget(id="terminal"),
        project_root="/work/ledger",
        retention=500,
    )
    assert wrote is True
    [row] = db.dictation_journal.recent()
    assert row.source == "dry_run"
    assert row.transcript == "add idempotency"
    assert row.final_text == "Enriched task."
    assert row.intent == "agent_task"
    assert row.block_id == "agent_task_buildout"
    assert row.confidence == pytest.approx(0.91)
    assert row.target_profile == "terminal"
    assert row.project_root == "/work/ledger"
    assert row.stage_ms == {"intent-router": 8.0, "project-rewriter": 900.0}
    assert row.rewrite_pass_ms == [430.0, 470.0]
    assert row.warnings == ["intent-router: heads up"]


def test_recorder_disabled_writes_nothing(db: Database) -> None:
    recorder = DictationJournalRecorder(repository=db.dictation_journal)
    assert recorder.record(
        _sample_run(), source="dictation", transcript="x", enabled=False
    ) is False
    assert db.dictation_journal.count() == 0


def test_recorder_without_repository_is_noop() -> None:
    recorder = DictationJournalRecorder(repository=None)
    assert recorder.record(_sample_run(), source="dictation", transcript="x") is False


def test_recorder_rejects_unknown_source(db: Database) -> None:
    recorder = DictationJournalRecorder(repository=db.dictation_journal)
    assert recorder.record(_sample_run(), source="bogus", transcript="x") is False
    assert db.dictation_journal.count() == 0


def test_secrets_are_redacted_before_persistence(db: Database) -> None:
    secret = "my api_key is sk-abcdef0123456789abcd please use it"
    assert filter_secret(secret) == "[redacted: possible secret]"

    recorder = DictationJournalRecorder(repository=db.dictation_journal)
    recorder.record(
        _sample_run(final_text=secret),
        source="dictation",
        transcript=secret,
    )
    [row] = db.dictation_journal.recent()
    # The known secret value never landed, in either field.
    assert "sk-abcdef0123456789abcd" not in row.transcript
    assert "sk-abcdef0123456789abcd" not in row.final_text
    assert row.transcript == "[redacted: possible secret]"
    assert row.final_text == "[redacted: possible secret]"


def test_recorder_swallows_repository_failure(db: Database) -> None:
    class _Boom:
        def record(self, **_kwargs):
            raise RuntimeError("disk full")

    recorder = DictationJournalRecorder(repository=_Boom())
    # Must not raise into the dictation path; returns False.
    assert recorder.record(_sample_run(), source="dictation", transcript="x") is False
