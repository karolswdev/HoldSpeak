"""AG14: one source item per hand, durable idempotency, and Done results."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
import time

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.automation_runs import new_results, prepared_for_today, results_of, sync_agent_results
from holdspeak.services.workbench_runner import WorkbenchRunner
from holdspeak.services.workbench_service import WorkbenchService


OWNER = Principal(PrincipalKind.OWNER, "ag14-test-owner")


class _Stager:
    def register(self, *_args):
        return None


class _Broker:
    projection_stager = _Stager()


def _automation(tmp_path: Path, *, source_count: int = 2):
    db = Database(tmp_path / "ag14.db")
    sources = []
    for index in range(source_count):
        note_id = f"ag14-note-{index}"
        db.notes.upsert(note_id=note_id, title=f"Action {index}", body_markdown="Do this.")
        sources.append(f"note:{note_id}")
    wb = WorkbenchService(db).create_automation(
        OWNER,
        name="Hand source work",
        sentence={"do": "hand_to_agent", "about": sources, "with": "codex-default", "review_by": "claude", "put_in": "today"},
    )
    return db, db.workbenches.get(wb["id"])


def test_manual_run_hands_each_source_once_and_rerun_starts_none(tmp_path, monkeypatch):
    db, wb = _automation(tmp_path)
    calls = []

    class FakeHand:
        def hand_item(self, _principal, **kwargs):
            calls.append(kwargs["id"])
            return {"status": "launched", "launch_id": f"launch-{len(calls)}", "profile": kwargs["profile"]}

    monkeypatch.setattr("holdspeak.services.agent_hand_service.default_agent_hand_service", lambda _db: FakeHand())
    runner = WorkbenchRunner(db, _Broker())
    first = runner._run_hand(OWNER, wb)
    second = runner._run_hand(OWNER, db.workbenches.get(wb.id))

    assert len(calls) == 2
    assert len(first["agents_started"]) == 2
    assert len(second["agents_started"]) == 0
    assert len(second["skipped"]) == 2
    assert {json.loads(item.context_json)["agent_hand"]["status"] for item in db.workbench_items.list_for_workbench(wb.id)} == {"launched"}


def test_concurrent_run_claims_a_source_once(tmp_path, monkeypatch):
    db, wb = _automation(tmp_path, source_count=1)
    calls = []
    lock = Lock()

    class FakeHand:
        def hand_item(self, _principal, **kwargs):
            with lock:
                calls.append(kwargs["id"])
            time.sleep(0.05)
            return {"status": "launched", "launch_id": "launch-once", "profile": "codex-default"}

    monkeypatch.setattr("holdspeak.services.agent_hand_service.default_agent_hand_service", lambda _db: FakeHand())

    def run_once():
        return WorkbenchRunner(db, _Broker())._run_hand(OWNER, db.workbenches.get(wb.id))

    with ThreadPoolExecutor(max_workers=2) as pool:
        answers = list(pool.map(lambda _index: run_once(), range(2)))
    assert len(calls) == 1
    assert sum(len(answer["agents_started"]) for answer in answers) == 1


def test_agent_done_becomes_new_automation_result_and_today_row(tmp_path, monkeypatch):
    db, wb = _automation(tmp_path, source_count=1)

    class FakeHand:
        def hand_item(self, _principal, **_kwargs):
            return {"status": "launched", "launch_id": "launch-done", "profile": "codex-default"}

    monkeypatch.setattr("holdspeak.services.agent_hand_service.default_agent_hand_service", lambda _db: FakeHand())
    WorkbenchRunner(db, _Broker())._run_hand(OWNER, wb)
    monkeypatch.setattr(
        "holdspeak.services.agent_flights.agent_flights",
        lambda _db: [{"launch_id": "launch-done", "state": "done", "turn_id": "turn-1", "agent": "codex"}],
    )
    monkeypatch.setattr("holdspeak.services.agent_helpers.last_words", lambda _db, _launch: "Done: the item is ready.")

    assert sync_agent_results(db) == 1
    result = results_of(db, wb.id)[0]
    assert result["status"] == "done"
    assert result["new"] is True
    assert result["text"] == "Done: the item is ready."
    assert new_results(db)[0]["workbench_id"] == wb.id
    assert prepared_for_today(db, OWNER)["workbench_id"] == wb.id
