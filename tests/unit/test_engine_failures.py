"""A door job that did not run waits on the owner (Needs you), and Retry.

The record is the runner's own receipt (no other write): the latest receipt
of a (job, kind, key) that is not a success is one row; a success clears it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import engine_door
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.needs_you_membership import engine_items
from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

OWNER = Principal(PrincipalKind.OWNER, "engine-owner")
JOB = "decision.promotion_draft"


class _Engine:
    down = True

    def run_prompt(self, **_kwargs: Any) -> str:
        if _Engine.down:
            raise RuntimeError("connection refused by /Users/someone/model.gguf")
        return "answered"


@pytest.fixture
def broker(tmp_path: Path) -> Any:
    db = Database(tmp_path / "engine-failures.db")
    _profile(db, "drafts")
    for job in (JOB, "background.rails_summary"):
        InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
            "command_id": f"assign-{job}", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": job},
            "entries": [{"profile_id": "drafts", "profile_revision": 1}],
        })
    broker = _configure(db)
    _Engine.down = True
    broker.inference_runner._engine_factory = lambda _revision, **_kw: _Engine()
    return broker


def _run(broker: Any, retry: Any = None) -> None:
    engine_door.run(broker, OWNER, JOB, {"system_prompt": "s", "user_prompt": "u"}, retry=retry)


def test_a_failed_job_is_one_row_in_his_words_and_a_success_clears_it(broker: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setitem(engine_door.RETRY, "test.kind", engine_door.RetryKind(
        words="the test draft", object_kind="decision", open_ref=lambda key: f"decision:{key}",
        run=lambda _p, key: calls.append(key) or _run(broker, ("test.kind", key)),
    ))
    for _ in range(2):  # two failures of one job are one row
        with pytest.raises(engine_door.EngineDoorError):
            _run(broker, ("test.kind", "dec-1"))
    (item,) = engine_door.failure_items(broker.database)
    assert item["engine"] == "drafts" and item["words"] == "the test draft"
    assert item["reason"] in {"it gave no answer", "it could not be reached"}
    assert item["can_retry"] is True and item["open_ref"] == "decision:dec-1"
    (row,) = engine_items([item])
    assert row["title"] == f"drafts could not run the test draft · {item['reason']}"
    assert row["engine"]["verbs"][0]["body"] == {"kind": "test.kind", "key": "dec-1"}
    assert "/Users" not in str(row) and "refused" not in str(row)

    _Engine.down = False
    engine_door.retry(OWNER, "test.kind", "dec-1")
    assert calls == ["dec-1"]
    assert engine_door.failure_items(broker.database) == []


def test_a_job_with_no_retry_key_opens_engines_and_has_no_retry(broker: Any) -> None:
    with pytest.raises(engine_door.EngineDoorError):
        _run(broker)
    (item,) = engine_door.failure_items(broker.database)
    assert item["can_retry"] is False and item["open_ref"] == engine_door.ENGINES_REF
    assert item["words"] == "the decision draft"
    assert engine_items([item])[0]["engine"]["verbs"] == []
    with pytest.raises(engine_door.EngineDoorError) as refused:
        engine_door.retry(OWNER, "", "")
    assert refused.value.code == "no_retry"


def test_retry_on_a_rails_journal_rewrites_its_note_with_the_summary(broker: Any) -> None:
    from holdspeak import rails_observer

    db = broker.database
    summarizer = rails_observer.build_profile_summarizer(
        db=db, broker=broker, principal=rails_observer.observer_principal(),
    )
    events = [{"ts": "t1", "event": "gate_pass", "story": "HS-1", "repo": "code"}]
    degraded = rails_observer.summarize_batch(events, summarize_fn=summarizer)
    assert degraded["degraded"] is True
    note = rails_observer.record_journal_entry(db, degraded, title="Rails journal")
    (item,) = engine_door.failure_items(db)
    assert item["kind"] == "rails.journal" and item["open_ref"] == f"note:{note.id}"

    _Engine.down = False
    rails_observer.retry_journal(OWNER, item["retry_key"], db=db, broker=broker)
    rewritten = db.notes.get(note.id)
    assert "answered" in rewritten.body_markdown and "summary unavailable" not in rewritten.body_markdown
    assert "- t1" in rewritten.body_markdown
    assert engine_door.failure_items(db) == []
