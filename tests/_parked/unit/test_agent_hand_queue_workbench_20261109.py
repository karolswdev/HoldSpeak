# PARKED 2026-11-09: WorkbenchRunner hand tests; retained queue readers remain live.
"""HS-S31 (D18/G31): the shared queue outcome contract.

``queue_outcome`` answers one queue id's outcome from retained evidence only
(the live row, else the retained record): waiting, launched, failed,
cancelled or unknown. Every Waiting Automation occurrence that holds the id
reads the same answer; a read never starts, re-queues or repeats a hand.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.delivery import factory_launch
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_hand_queue import HandQueue, queue_outcome, start_queued
from holdspeak.services.automation_runs import results_of, sync_queue_outcomes
from holdspeak.services.workbench_runner import WorkbenchRunner
from holdspeak.services.workbench_service import WorkbenchService

OWNER = Principal(PrincipalKind.OWNER, "hs-s31-test-owner")


@pytest.fixture(autouse=True)
def _queue_home(tmp_path, monkeypatch):
    # The default queue file sits beside the launch ledger: keep both in tmp.
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", tmp_path / "launches.json")


class _Broker:
    class projection_stager:  # noqa: N801 (the runner reads .register)
        @staticmethod
        def register(*_args):
            return None


class _QueueingHand:
    """Every hand waits for a free agent: it lands in the real shared queue."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def hand_item(self, _principal, **kwargs):
        self.calls.append(kwargs["id"])
        entry = HandQueue().add(kwargs["kind"], kwargs["id"], instruction=kwargs.get("instruction"),
                                profile=kwargs.get("profile"))
        return {"status": "queued", "queue_id": entry["queue_id"], "profile": kwargs.get("profile")}


class _Service:
    """``start_queued``'s service: a free slot, and each hand answers or refuses."""

    def __init__(self, refuse: frozenset[str] = frozenset()) -> None:
        self.refuse = refuse
        self.calls: list[str] = []

    def has_free_slot(self) -> bool:
        return True

    def hand(self, _principal, kind, item_id, **_kwargs):
        self.calls.append(f"{kind}:{item_id}")
        if item_id in self.refuse:
            error = RuntimeError("refused")
            error.code = "item_unknown"  # type: ignore[attr-defined]
            raise error
        return {"status": "launched", "launch_id": f"launch-{item_id}", "origin_ref": {"kind": kind, "id": item_id}}


def _two_automations_one_source(tmp_path: Path, monkeypatch):
    db = Database(tmp_path / "s31.db")
    db.notes.upsert(note_id="s31-note", title="Action", body_markdown="Do this.")
    hand = _QueueingHand()
    monkeypatch.setattr("holdspeak.services.agent_hand_service.default_agent_hand_service", lambda _db: hand)
    service = WorkbenchService(db)
    ids = []
    for name in ("First automation", "Second automation"):
        made = service.create_automation(OWNER, name=name, sentence={
            "do": "hand_to_agent", "about": ["note:s31-note"], "with": "codex-default", "put_in": "today"})
        WorkbenchRunner(db, _Broker())._run_hand(OWNER, db.workbenches.get(made["id"]))
        ids.append(made["id"])
    return db, ids, hand


def _hands(db, workbench_ids):
    return [json.loads(item.context_json)["agent_hand"] for wb in workbench_ids
            for item in db.workbench_items.list_for_workbench(wb)]


def test_each_outcome_comes_from_retained_evidence_and_a_replay_answers_the_same() -> None:
    queue = HandQueue()
    waiting = queue.add("note", "a")
    cancelled = queue.add("note", "b")
    refused = queue.add("note", "c")
    launched = queue.add("note", "d")
    assert queue_outcome(waiting["queue_id"])["outcome"] == "waiting"
    assert queue.remove(cancelled["queue_id"]) is True
    [failed_answer, launched_answer] = start_queued(_Service(refuse=frozenset({"c"})), queue=_OnlyIds(
        queue, {refused["queue_id"], launched["queue_id"]}))
    assert failed_answer["status"] == "refused" and launched_answer["status"] == "launched"
    answers = {entry["queue_id"]: queue_outcome(entry["queue_id"]) for entry in (waiting, cancelled, refused, launched)}
    assert {key: value["outcome"] for key, value in answers.items()} == {
        waiting["queue_id"]: "waiting", cancelled["queue_id"]: "cancelled",
        refused["queue_id"]: "failed", launched["queue_id"]: "launched"}
    assert answers[refused["queue_id"]]["code"] == "item_unknown"
    assert (answers[launched["queue_id"]]["launch_id"], answers[launched["queue_id"]]["source_ref"]) == ("launch-d", "note:d")
    # The same id replayed: a second Cancel is refused and every answer stays.
    assert queue.remove(cancelled["queue_id"]) is False
    assert queue.remove(launched["queue_id"], outcome="cancelled") is False
    assert {key: queue_outcome(key) for key in answers} == answers


def test_no_row_and_no_record_is_unknown_never_cancelled_or_failed(tmp_path) -> None:
    assert queue_outcome("queue_never_seen")["outcome"] == "unknown"
    broken = tmp_path / "broken" / "agent_hand_queue.json"
    broken.parent.mkdir()
    broken.write_text("{not json", encoding="utf-8")
    assert HandQueue(broken).outcome("queue_any")["outcome"] == "unknown"


def test_a_cancelled_entry_ends_every_occurrence_that_holds_it_and_is_never_revived(tmp_path, monkeypatch) -> None:
    db, workbenches, hand = _two_automations_one_source(tmp_path, monkeypatch)
    hands = _hands(db, workbenches)
    # Two Automations, one source: the shared queue keeps one entry for both.
    assert [row["status"] for row in hands] == ["queued", "queued"]
    assert len({row["queue_id"] for row in hands}) == 1 and len(HandQueue().list()) == 1
    queue_id = hands[0]["queue_id"]
    assert HandQueue().remove(queue_id) is True          # his Cancel (DELETE /api/agent/hand/queue/{id})
    assert sync_queue_outcomes(db) == 2                  # zero to many consumers: both read it
    for wb in workbenches:
        [row] = results_of(db, wb)
        assert (row["status"], row["error"]) == ("failed", "Cancelled before it started")
    assert {row["status"] for row in _hands(db, workbenches)} == {"cancelled"}
    # Never revived: a Run and the heartbeat start nothing; a second read writes nothing.
    calls = len(hand.calls)
    for wb in workbenches:
        WorkbenchRunner(db, _Broker())._run_hand(OWNER, db.workbenches.get(wb))
    service = _Service()
    assert start_queued(service) == [] and service.calls == []
    assert len(hand.calls) == calls
    assert sync_queue_outcomes(db) == 0


def test_an_unknown_effect_is_not_repeated(tmp_path, monkeypatch) -> None:
    db, workbenches, hand = _two_automations_one_source(tmp_path, monkeypatch)
    # The queue file is lost (no live row, no retained record): the outcome is unknown.
    queue_file = Path(factory_launch.DEFAULT_LAUNCHES_PATH).with_name("agent_hand_queue.json")
    queue_file.unlink()
    queue_id = _hands(db, workbenches)[0]["queue_id"]
    assert queue_outcome(queue_id)["outcome"] == "unknown"
    assert sync_queue_outcomes(db) == 0
    assert {row["status"] for row in _hands(db, workbenches)} == {"queued"}
    calls = len(hand.calls)
    for wb in workbenches:
        WorkbenchRunner(db, _Broker())._run_hand(OWNER, db.workbenches.get(wb))
    service = _Service()
    assert start_queued(service) == [] and service.calls == []
    assert len(hand.calls) == calls


def test_a_launch_the_heartbeat_did_not_attach_is_read_from_its_record_once(tmp_path, monkeypatch) -> None:
    db, workbenches, _hand = _two_automations_one_source(tmp_path, monkeypatch)
    queue_id = _hands(db, workbenches)[0]["queue_id"]
    # The heartbeat started it, then the hub stopped before it attached the launch.
    [answer] = start_queued(_Service())
    assert answer["launch_id"] == "launch-s31-note"
    assert queue_outcome(queue_id)["outcome"] == "launched"
    assert sync_queue_outcomes(db) == 2
    assert {(row["status"], row["launch_id"]) for row in _hands(db, workbenches)} == {("launched", "launch-s31-note")}
    # The same id replayed: no second attach, no stale downgrade.
    assert sync_queue_outcomes(db) == 0


class _OnlyIds:
    """A view of the queue that lists only some ids (the rest stay waiting)."""

    def __init__(self, queue: HandQueue, ids: set[str]) -> None:
        self._queue, self._ids = queue, ids

    def list(self):
        return [row for row in self._queue.list() if row["queue_id"] in self._ids]

    def remove(self, queue_id, **kwargs):
        return self._queue.remove(queue_id, **kwargs)
