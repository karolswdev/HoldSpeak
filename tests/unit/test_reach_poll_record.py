"""An empty Telegram poll is not an egress operation (owner decision 2026-11-13).

A healthy long poll answers every 25 s with nothing. Each of those was one
``external.egress`` kernel operation with five journal rows: about 3,450 a
day that said only "nothing came". The record now holds the poll's start, each
poll that returned updates, each poll that failed, and the poll's stop.
"""
from __future__ import annotations

import io
import json
import urllib.error
from typing import Any

import pytest

import holdspeak.db.core as db_core
from holdspeak.kernel import runtime as kernel_runtime
from holdspeak.kernel.external_egress import EGRESS_EXECUTIONS
from holdspeak.services import telegram_reach
from holdspeak.services.telegram_reach import TelegramReach, call_reach
from tests.unit.test_reach_telegram import Desk, keystore  # noqa: F401  (the autouse keystore fixture)

TOKEN = "123456:AAtesttokentesttokentesttokentest"


class _Answer:
    def __init__(self, body: dict[str, Any]) -> None:
        self._body = json.dumps(body).encode()

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_Answer":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None


@pytest.fixture
def kernel(tmp_path, monkeypatch):
    desk = Desk(tmp_path)
    desk.pair()
    monkeypatch.setattr(db_core, "_db", desk.rig.db)
    for held in (EGRESS_EXECUTIONS._plans, EGRESS_EXECUTIONS._operation_ids, EGRESS_EXECUTIONS._results):
        held.clear()
    kernel_runtime._configure(desk.rig.db)
    return desk


def _egress(db: Any) -> list[tuple[str, str]]:
    """Each egress operation as (its data class, its receipt state)."""
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT a.refs_json, r.state FROM kernel_operations o
                 JOIN kernel_journal a ON a.operation_id = o.operation_id AND a.event_type = 'operation.admitted'
                 JOIN kernel_receipts r ON r.operation_id = o.operation_id
                WHERE o.name = 'external.egress' ORDER BY o.created_at, a.hub_sequence"""
        ).fetchall()
    out = []
    for row in rows:
        classes = [ref.split(":", 1)[1] for ref in json.loads(row[0]) if ref.startswith("data-class:")]
        out.append((classes[0], str(row[1])))
    return out


def _telegram_says(monkeypatch, *answers: Any) -> list[Any]:
    """The Bot API answers these, in order; the last one again after that."""
    asked: list[Any] = []
    queue = list(answers)

    def urlopen(request: Any, timeout: float = 0) -> _Answer:
        asked.append(request)
        answer = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(answer, BaseException):
            raise answer
        return _Answer(answer)

    monkeypatch.setattr(telegram_reach.urllib.request, "urlopen", urlopen)
    return asked


def test_empty_polls_write_no_kernel_operation(kernel, monkeypatch) -> None:
    asked = _telegram_says(monkeypatch, {"ok": True, "result": []})

    for _ in range(5):
        answer = call_reach(TOKEN, "getUpdates", {"timeout": 25}, data_class="reach_update_cursor",
                            quiet_when_empty=True)
        assert answer == {"ok": True, "result": []}

    assert len(asked) == 5
    assert _egress(kernel.rig.db) == []


def test_a_poll_that_returns_an_update_is_one_operation(kernel, monkeypatch) -> None:
    _telegram_says(monkeypatch, {"ok": True, "result": [{"update_id": 7}]})

    answer = call_reach(TOKEN, "getUpdates", {"timeout": 25}, data_class="reach_update_cursor",
                        quiet_when_empty=True)

    assert answer["result"] == [{"update_id": 7}]
    assert _egress(kernel.rig.db) == [("reach_update_cursor", "succeeded")]


@pytest.mark.parametrize("failure", [
    TimeoutError("The read operation timed out"),
    urllib.error.HTTPError("https://api.telegram.org/", 409, "Conflict", {}, io.BytesIO(b"{}")),  # type: ignore[arg-type]
])
def test_a_poll_that_fails_is_one_operation_with_no_token(kernel, monkeypatch, failure) -> None:
    _telegram_says(monkeypatch, failure)

    answer = call_reach(TOKEN, "getUpdates", {"timeout": 25}, data_class="reach_update_cursor",
                        quiet_when_empty=True)

    assert answer["ok"] is False and TOKEN not in json.dumps(answer)
    assert _egress(kernel.rig.db) == [("reach_update_cursor", "indeterminate")]


def test_a_send_is_recorded_as_before(kernel, monkeypatch) -> None:
    _telegram_says(monkeypatch, {"ok": True, "result": {"message_id": 1}})

    call_reach(TOKEN, "sendMessage", {"chat_id": "1", "text": "Hello"})

    assert _egress(kernel.rig.db) == [("reach_package", "succeeded")]


def test_the_poll_records_its_start_once_and_its_halt(kernel, monkeypatch) -> None:
    conflict = urllib.error.HTTPError("https://api.telegram.org/", 409, "Conflict", {}, io.BytesIO(b"{}"))  # type: ignore[arg-type]
    _telegram_says(monkeypatch, {"ok": True, "result": []}, {"ok": True, "result": []}, conflict)
    production = TelegramReach(kernel.rig.db)  # no injected caller: the real transport

    production.poll_once(None)
    production.poll_once(None)

    assert _egress(kernel.rig.db) == [("reach_poll_started", "succeeded")]
    assert production.last_answer_at is not None  # an empty poll still moves the last answer

    production.poll_once(None)  # another desk reads the bot: the poll halts

    assert _egress(kernel.rig.db) == [
        ("reach_poll_started", "succeeded"),
        ("reach_update_cursor", "indeterminate"),
        ("reach_poll_stopped", "succeeded"),
    ]
    asked_before = len(_egress(kernel.rig.db))
    production.poll_once(None)  # halted: no call, no operation
    assert len(_egress(kernel.rig.db)) == asked_before


def test_the_poll_records_its_stop_when_the_hub_stops_and_a_new_start_after(kernel, monkeypatch) -> None:
    _telegram_says(monkeypatch, {"ok": True, "result": []})
    production = TelegramReach(kernel.rig.db)

    production.poll_once(None)
    production.poll_stopped("the hub stopped")
    production.poll_stopped("the hub stopped")  # said one time
    production.poll_once(None)

    assert [name for name, _state in _egress(kernel.rig.db)] == [
        "reach_poll_started", "reach_poll_stopped", "reach_poll_started"]


def test_no_record_no_poll(kernel, monkeypatch) -> None:
    asked = _telegram_says(monkeypatch, {"ok": True, "result": []})
    monkeypatch.setattr(telegram_reach, "record_poll_event", lambda *a, **k: False)  # the kernel refuses the start
    production = TelegramReach(kernel.rig.db)

    assert production.poll_once(4) == 4
    assert production.last_poll_ok is False
    assert [r for r in asked if "getUpdates" in r.full_url] == []
