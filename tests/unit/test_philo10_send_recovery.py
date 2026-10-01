"""PHILO-10-01: the crash rule and recovery across take-over AND reaping (design sections 4 and 4a).

Through the REAL hub on an isolated HOME, the Room's REAL take-over
(``services/project_kernel._replayed`` -> ``_take_over``) and the REAL liveness
reaper (``kernel/liveness.reap_expired``, its clock moved past the execution
deadline). Each fence runs over both forms: the prepared row (``send_id``) and
the owner's inline form (``document_ref`` + ``destination_id`` + ``preview_digest``).
The invariant: per send key, ONE dispatch, ONE terminal receipt, ONE history
row -- except a send that ends before its dispatch boundary: ZERO dispatches and
no history row, only its receipt. The restart fence (R3) kills a real hub
process: ``test_philo10_send_restart.py``.

| Fence | Order | Green |
|---|---|---|
| R1 | dispatch, settle write fails -> take-over -> replay | take-over reads the file back (SENT) or answers UNKNOWN; the replay answers the settled row |
| R2 | dispatch, silent -> the real reaper -> replay | row ``unknown`` (``reaped``) with its history row in the receipt's transaction; the replay answers it |
| R4 | the reaper and a take-over race on one key | one wins; the other changes nothing |
| R5 | a file send reaped with the file present | UNKNOWN with ``found_on_disk``: path + sha256 + size |
| R6 | reaped before the boundary | row stays ``prepared`` (or none), zero dispatches, no history, receipt ``reaped_before_dispatch`` |

The deliberate mutations (drop the reap effect: R2, R5 red; drop the replay
hook: R1 red; settle outside the strict terminal: R4 red; drop the boundary's
claimed guard: R6 red; recovery that dispatches again: the crash rule red) are
recorded in the evidence.
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import (  # noqa: E402
    DispatchSpy, Hub, _boot, destination, files, history, in_thread, op, ops, reap_past_deadline, room, send,
    send_body, sends, source, history_for_ref, until,
)

FORMS = ["send_id", "inline"]
SOURCE_KINDS = ["project_update", "desk_decision"]


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _setup(hub: Hub, tmp_path: Path, form: str, key: str, source_kind: str = "project_update") -> tuple[str, Path, dict[str, Any]]:
    folder = tmp_path / "out"
    document_ref = source(hub, source_kind)
    dest = destination(hub, folder)
    return document_ref, folder, send_body(hub, form, document_ref, dest, key)


def _send_ops(hub: Hub) -> list[dict[str, Any]]:
    return ops(hub, "channel.send")


def _fail_the_settle_once(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """The settle write fails AFTER the effect ran (it rolls back: no row move, no receipt)."""
    from holdspeak.services import channel_service

    real = channel_service.settle_in_transaction
    failed: list[int] = []

    def settle(conn: Any, **kwargs: Any) -> Any:
        settled = real(conn, **kwargs)
        if not failed:
            failed.append(1)
            raise RuntimeError("injected: the settle write failed after the effect")
        return settled

    monkeypatch.setattr(channel_service, "settle_in_transaction", settle)
    return failed


def _one_of_each(hub: Hub, document_ref: str, *, history_outcome: str | None, kernel_state: str) -> dict[str, Any]:
    [operation] = _send_ops(hub)
    assert (operation["state"], operation["receipts"]) == (kernel_state, 1), operation
    rows = history_for_ref(hub, document_ref)
    if history_outcome is None:
        assert rows == [], rows
    else:
        assert [(r["outcome"], r["operation_id"]) for r in rows] == [(history_outcome, operation["operation_id"])]
    return operation


# ── R1: the settle write fails -> the Room's take-over -> replay ─────────


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("on_disk", ["intact", "tampered"])
@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_r1_a_failed_settle_is_taken_over_without_a_second_dispatch_and_the_replay_answers_it(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, form: str, on_disk: str, source_kind: str,
) -> None:
    document_ref, folder, body = _setup(hub, tmp_path, form, f"r1-{form}-{on_disk}-{source_kind}", source_kind)
    spy = DispatchSpy(monkeypatch)
    _fail_the_settle_once(monkeypatch)
    failed = send(hub, body)
    assert failed.status_code == 500, failed.text
    [operation] = _send_ops(hub)
    assert (operation["state"], operation["receipts"]) == ("claimed", 0), operation  # nothing invented
    [row] = sends(hub)
    assert row["state"] == "dispatching" and row["send_operation_id"] == operation["operation_id"]
    [written] = files(folder)
    if on_disk == "tampered":
        written.write_bytes(written.read_bytes() + b"edited by someone")
    taken_over = send(hub, body)  # the same key: the Room's take-over
    assert taken_over.status_code == 200, taken_over.text
    expected = "sent" if on_disk == "intact" else "unknown"
    assert taken_over.json()["outcome"] == expected
    assert taken_over.json()["operation_id"] == operation["operation_id"]
    replayed = send(hub, body)  # and again: the replay answers the settled row
    assert replayed.status_code == 200, replayed.text
    assert replayed.json()["send"] == taken_over.json()["send"]
    assert replayed.json()["receipt"]["receipt_id"] == taken_over.json()["receipt"]["receipt_id"]
    assert spy.calls == 1 and files(folder) == [written]
    if expected == "sent":
        proof = taken_over.json()["send"]["proof"]
        assert proof == {"path": str(written), "sha256": hashlib.sha256(written.read_bytes()).hexdigest(),
                         "size": written.stat().st_size}
        _one_of_each(hub, document_ref, history_outcome="sent", kernel_state="succeeded")
    else:
        assert taken_over.json()["send"]["reason"] == "read_back_mismatch"
        _one_of_each(hub, document_ref, history_outcome="unknown", kernel_state="indeterminate")


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_the_same_key_again_makes_no_second_effect(hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                   form: str, source_kind: str) -> None:
    document_ref, folder, body = _setup(hub, tmp_path, form, f"again-{form}-{source_kind}", source_kind)
    spy = DispatchSpy(monkeypatch)
    first = send(hub, body).json()
    for _ in range(3):
        again = send(hub, body).json()
        assert again["send"] == first["send"] and again["operation_id"] == first["operation_id"]
    assert spy.calls == 1 and len(files(folder)) == 1
    _one_of_each(hub, document_ref, history_outcome="sent", kernel_state="succeeded")


@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_a_new_key_is_a_new_send(hub: Hub, tmp_path: Path, source_kind: str) -> None:
    document_ref, folder, body = _setup(hub, tmp_path, "inline", f"first-press-{source_kind}", source_kind)
    assert send(hub, body).json()["outcome"] == "sent"
    assert send(hub, {**body, "command_id": "second-press"}).json()["outcome"] == "sent"
    assert len(files(folder)) == 2 and len(history_for_ref(hub, document_ref)) == 2


# ── R2 / R5: silent -> the real reaper -> replay ─────────────────────────


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("hold", ["before", "after"], ids=["R2-no-file", "R5-file-present"])
@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_r2_r5_the_reaper_settles_a_silent_send_and_the_replay_answers_it(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, form: str, hold: str, source_kind: str,
) -> None:
    document_ref, folder, body = _setup(hub, tmp_path, form, f"r2-{form}-{hold}-{source_kind}", source_kind)
    spy = DispatchSpy(monkeypatch, hold=hold)
    thread, answer = in_thread(lambda: send(hub, body))
    assert spy.entered.wait(30)
    [row] = [r for r in sends(hub) if r["state"] == "dispatching"]
    reaped = reap_past_deadline(hub)
    operation_id = row["send_operation_id"]
    assert {"operation_id": operation_id, "state": "indeterminate",
            "outcome": "execution_liveness_expired"} in reaped["reaped"], reaped
    settled = hub.db.channel_sends.get(row["id"])
    assert (settled["state"], settled["reason"]) == ("unknown", "reaped"), settled
    _one_of_each(hub, document_ref, history_outcome="unknown", kernel_state="indeterminate")
    proof = json.loads(settled["proof_json"]) if settled["proof_json"] else None
    if hold == "after":  # R5: the file is there with the digest: recorded, still UNKNOWN
        [written] = files(folder)
        assert proof == {"found_on_disk": {"path": str(written), "sha256": settled["payload_digest"],
                                           "size": written.stat().st_size}}
    else:
        assert proof is None
    spy.release.set()
    thread.join(60)
    [late] = answer
    assert late.status_code == 200 and late.json()["outcome"] == "unknown", late.text
    replayed = send(hub, body)
    assert replayed.status_code == 200, replayed.text
    assert (replayed.json()["outcome"], replayed.json()["send"]["reason"]) == ("unknown", "reaped")
    assert replayed.json()["receipt"]["outcome"] == "execution_liveness_expired"
    assert spy.calls == 1 and len(files(folder)) <= 1
    _one_of_each(hub, document_ref, history_outcome="unknown", kernel_state="indeterminate")


# ── R4: the reaper and a take-over race on one key ──────────────────────


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_r4_the_reaper_and_a_take_over_race_and_one_wins(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, form: str, source_kind: str,
) -> None:
    from holdspeak.services.channel_contract import FileChannel

    document_ref, folder, body = _setup(hub, tmp_path, form, f"r4-{form}-{source_kind}", source_kind)
    spy = DispatchSpy(monkeypatch)
    _fail_the_settle_once(monkeypatch)
    assert send(hub, body).status_code == 500
    entered, release = threading.Event(), threading.Event()
    real_recover = FileChannel.recover

    def recover(channel: Any, row: Any) -> Any:
        outcome = real_recover(channel, row)  # the take-over's read-back says SENT
        entered.set()
        assert release.wait(60)
        return outcome

    monkeypatch.setattr(FileChannel, "recover", recover)
    thread, answer = in_thread(lambda: send(hub, body))  # the take-over
    assert entered.wait(30)
    reaped = reap_past_deadline(hub)  # the reaper wins the race
    assert reaped["count"] == 1, reaped
    release.set()
    thread.join(60)
    [took_over] = answer
    assert took_over.status_code == 200, took_over.text
    # The loser changed nothing: the row, the receipt and the history are the reaper's.
    [row] = sends(hub)
    assert (row["state"], row["reason"]) == ("unknown", "reaped"), row
    assert took_over.json()["send"]["state"] == "unknown"
    assert took_over.json()["receipt"]["outcome"] == "execution_liveness_expired"
    _one_of_each(hub, document_ref, history_outcome="unknown", kernel_state="indeterminate")
    assert spy.calls == 1 and len(files(folder)) == 1


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_r4_a_take_over_that_wins_leaves_the_reaper_nothing(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, form: str, source_kind: str,
) -> None:
    document_ref, folder, body = _setup(hub, tmp_path, form, f"r4b-{form}-{source_kind}", source_kind)
    spy = DispatchSpy(monkeypatch)
    _fail_the_settle_once(monkeypatch)
    assert send(hub, body).status_code == 500
    assert send(hub, body).json()["outcome"] == "sent"  # the take-over wins
    assert reap_past_deadline(hub)["count"] == 0
    _one_of_each(hub, document_ref, history_outcome="sent", kernel_state="succeeded")
    assert spy.calls == 1


# ── R6: reaped before the boundary ──────────────────────────────────────


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_r6_a_send_reaped_before_its_boundary_dispatches_nothing_and_writes_no_history(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, form: str, source_kind: str,
) -> None:
    from holdspeak.services.channel_contract import FileChannel

    document_ref, folder, body = _setup(hub, tmp_path, form, f"r6-{form}-{source_kind}", source_kind)
    spy = DispatchSpy(monkeypatch)
    entered, release = threading.Event(), threading.Event()
    real_check = FileChannel.check_before_dispatch

    def check(channel: Any, target: Any, **kw: Any) -> Any:
        entered.set()
        assert release.wait(60)
        return real_check(channel, target, **kw)

    monkeypatch.setattr(FileChannel, "check_before_dispatch", check)
    thread, answer = in_thread(lambda: send(hub, body))
    assert entered.wait(30)
    reaped = reap_past_deadline(hub)
    [operation] = _send_ops(hub)
    assert {"operation_id": operation["operation_id"], "state": "indeterminate",
            "outcome": "execution_liveness_expired"} in reaped["reaped"], reaped
    assert op(hub, operation["operation_id"])["outcome"] == "reaped_before_dispatch"
    release.set()
    thread.join(60)
    [late] = answer
    assert late.status_code == 409 and late.json()["code"] == "operation_ended_before_dispatch", late.text
    assert late.json()["receipt"]["outcome"] == "reaped_before_dispatch"
    assert spy.calls == 0 and files(folder) == []
    rows = sends(hub)
    assert [r["state"] for r in rows] == (["prepared"] if form == "send_id" else [])
    _one_of_each(hub, document_ref, history_outcome=None, kernel_state="indeterminate")
    replayed = send(hub, body)  # a refusal before the boundary still raises, with its receipt
    assert replayed.status_code == 409 and replayed.json()["receipt"]["outcome"] == "reaped_before_dispatch"
    assert spy.calls == 0


def test_the_reaper_leaves_every_other_operation_as_it_was(hub: Hub, tmp_path: Path) -> None:
    """The effect is ``None`` off channel.send: a reaped non-send Room operation writes no send row."""
    from holdspeak.kernel.channel_send import channel_send_ended_effect

    assert channel_send_ended_effect(None, {"name": "project.publish_update", "operation_id": "op_x"}, "r") is None
