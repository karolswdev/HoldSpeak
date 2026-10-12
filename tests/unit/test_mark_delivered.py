"""PHILO-9-02 (the Q0 ruling; R4-2; Codex Astra r5): mark it delivered, under Article XI.

``project.mark_update_delivered`` (MCP) and ``POST /api/updates/{id}/delivered``
(HTTP) reach one declared operation. A NEW capability: no red is claimed; the
proof is the read-backs through the real hub and a mutation of each rule
(``scripts``-free: the mutation runs are recorded in the evidence).

* Each mark of a PUBLISHED update is one admitted operation with its own
  receipt and appends one ``project_update_deliveries`` row whose
  ``operation_id`` is that operation; ``delivered_at`` is the confirmation
  time (the operation's admission); two marks are two rows and two receipts.
* A draft is refused ``update_not_published`` with a receipt and no row.
* Idempotency: the same principal, ``command_id`` and payload answer the
  original row, time, operation and receipt; a changed payload is refused
  ``idempotency_conflict``; a new key makes a second row; an MCP call without
  ``command_id`` is a new delivery. Two concurrent requests with one key: one
  row.
* The row: ``operation_id`` NOT NULL UNIQUE REFERENCES ``kernel_operations``;
  ``project_id`` from the stored update; the insert, the terminal state and
  the receipt in ONE transaction: a failure injected after the insert leaves
  no row, no terminal state and no receipt, and a replay then succeeds once.
"""
from __future__ import annotations

import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _room(hub: Hub, *, publish: bool = True) -> tuple[str, str]:
    c = hub.client
    pid = c.post("/api/projects", json={"name": "Payments ledger cutover"}).json()["project"]["id"]
    update = c.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    if publish:
        assert c.post(f"/api/updates/{update}/publish", json={}).status_code == 200
    return pid, update


def _rows(hub: Hub, update: str) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM project_update_deliveries WHERE update_id=? ORDER BY delivered_at, rowid", (update,))]


def _operation(hub: Hub, operation_id: str) -> dict[str, Any]:
    with hub.db._connection() as conn:
        op = dict(conn.execute("SELECT * FROM kernel_operations WHERE operation_id=?", (operation_id,)).fetchone())
        receipts = [dict(r) for r in conn.execute("SELECT * FROM kernel_receipts WHERE operation_id=?", (operation_id,))]
    op["receipts"] = receipts
    return op


def _marks(hub: Hub) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT o.operation_id, o.state, r.outcome FROM kernel_operations o LEFT JOIN kernel_receipts r"
            " ON r.operation_id=o.operation_id WHERE o.name='project.mark_update_delivered' ORDER BY o.created_at")]


def _mark_http(hub: Hub, update: str, body: dict[str, Any] | None = None) -> Any:
    return hub.client.post(f"/api/updates/{update}/delivered", json=body or {})


def _confirmed_at(operation: dict[str, Any]) -> str:
    return datetime.fromtimestamp(float(operation["created_at"]), tz=timezone.utc).isoformat(timespec="seconds")


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_each_mark_is_one_admitted_operation_its_receipt_and_its_row(hub: Hub, transport: str) -> None:
    _pid, update = _room(hub)
    if transport == "http":
        resp = _mark_http(hub, update, {"delivered_to": "Priya"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
    else:
        is_error, body = hub.mcp("project.mark_update_delivered", {"update_id": update, "delivered_to": "Priya"})
        assert is_error is False, body
    rows = _rows(hub, update)
    assert len(rows) == 1
    row = rows[0]
    operation = _operation(hub, body["operation_id"])
    assert row["operation_id"] == operation["operation_id"] == body["delivery"]["operation_id"]
    assert (operation["name"], operation["state"]) == ("project.mark_update_delivered", "succeeded")
    assert [r["state"] for r in operation["receipts"]] == ["succeeded"]
    assert row["delivered_at"] == _confirmed_at(operation)  # the time he confirmed
    assert row["delivered_to"] == "Priya"
    assert body["delivery"] == {k: row[k] for k in ("id", "update_id", "project_id", "delivered_at", "delivered_to", "operation_id")}
    # Read back on the Room's reads.
    listed = hub.client.get(f"/api/projects/{row['project_id']}/updates").json()["updates"]
    assert [d["operation_id"] for d in next(u for u in listed if u["id"] == update)["deliveries"]] == [row["operation_id"]]


def test_two_marks_are_two_rows_and_two_receipts(hub: Hub) -> None:
    _pid, update = _room(hub)
    first = _mark_http(hub, update, {"delivered_to": "Priya"}).json()
    is_error, second = hub.mcp("project.mark_update_delivered", {"update_id": update, "delivered_to": "the Tuesday staff channel"})
    assert is_error is False, second
    rows = _rows(hub, update)
    assert [r["delivered_to"] for r in rows] == ["Priya", "the Tuesday staff channel"]
    assert {r["operation_id"] for r in rows} == {first["operation_id"], second["operation_id"]}
    assert [(m["state"], m["outcome"]) for m in _marks(hub)] == [("succeeded", "succeeded")] * 2


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_a_draft_is_refused_update_not_published_with_a_receipt_and_no_row(hub: Hub, transport: str) -> None:
    _pid, update = _room(hub, publish=False)
    if transport == "http":
        resp = _mark_http(hub, update)
        assert resp.status_code == 400, resp.text
        body = resp.json()
    else:
        is_error, body = hub.mcp("project.mark_update_delivered", {"update_id": update})
        assert is_error is True, body
    assert body["code"] == "update_not_published"
    assert _rows(hub, update) == []
    assert [(m["state"], m["outcome"]) for m in _marks(hub)] == [("refused", "update_not_published")]
    assert body["operation_id"] == _marks(hub)[0]["operation_id"]


def test_a_mark_that_names_another_project_is_refused_and_the_project_comes_from_the_update(hub: Hub) -> None:
    pid, update = _room(hub)
    other = hub.client.post("/api/projects", json={"name": "Other"}).json()["project"]["id"]
    resp = _mark_http(hub, update, {"project_id": other})
    assert resp.status_code == 400, resp.text
    assert _rows(hub, update) == []
    is_error, value = hub.mcp("project.mark_update_delivered", {"update_id": update, "project_id": other})
    assert is_error is True, value
    ok = _mark_http(hub, update).json()
    assert ok["delivery"]["project_id"] == pid


# ── idempotency (Codex Astra r5) ─────────────────────────────────────────


def test_a_repeat_of_one_key_and_payload_answers_the_original(hub: Hub) -> None:
    _pid, update = _room(hub)
    body = {"delivered_to": "Priya", "command_id": "confirm-1"}
    first = _mark_http(hub, update, body).json()
    again = _mark_http(hub, update, body).json()
    assert again["delivery"] == first["delivery"] and again["operation_id"] == first["operation_id"]
    assert again["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]
    is_error, over_mcp = hub.mcp("project.mark_update_delivered", {"update_id": update, **body})
    assert is_error is False and over_mcp["delivery"] == first["delivery"], over_mcp
    assert len(_rows(hub, update)) == 1 and len(_marks(hub)) == 1


def test_one_key_with_a_changed_payload_is_refused_idempotency_conflict(hub: Hub) -> None:
    _pid, update = _room(hub)
    assert _mark_http(hub, update, {"delivered_to": "Priya", "command_id": "confirm-2"}).status_code == 200
    resp = _mark_http(hub, update, {"delivered_to": "Someone else", "command_id": "confirm-2"})
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "idempotency_conflict" and resp.json().get("receipt")
    assert [r["delivered_to"] for r in _rows(hub, update)] == ["Priya"]


def test_a_new_key_to_the_same_recipient_makes_a_second_row(hub: Hub) -> None:
    _pid, update = _room(hub)
    _mark_http(hub, update, {"delivered_to": "Priya", "command_id": "confirm-3"})
    _mark_http(hub, update, {"delivered_to": "Priya", "command_id": "confirm-4"})
    assert [r["delivered_to"] for r in _rows(hub, update)] == ["Priya", "Priya"]


def test_an_mcp_mark_without_a_key_is_a_new_delivery(hub: Hub) -> None:
    _pid, update = _room(hub)
    for _ in range(2):
        is_error, value = hub.mcp("project.mark_update_delivered", {"update_id": update, "delivered_to": "Priya"})
        assert is_error is False, value
    assert len(_rows(hub, update)) == 2


def test_two_concurrent_requests_with_one_key_make_one_row(hub: Hub) -> None:
    _pid, update = _room(hub)
    answers: list[Any] = [None, None]
    start = threading.Barrier(2)

    def mark(index: int) -> None:
        start.wait(5)
        answers[index] = _mark_http(hub, update, {"delivered_to": "Priya", "command_id": "confirm-race"})

    threads = [threading.Thread(target=mark, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(60)
    assert [a.status_code for a in answers] == [200, 200], [a.text for a in answers]
    assert answers[0].json()["delivery"] == answers[1].json()["delivery"]
    assert len(_rows(hub, update)) == 1 and len(_marks(hub)) == 1


# ── the row's constraints and the one transaction (r5) ──────────────────


def test_the_row_names_its_operation_not_null_unique_and_referenced(hub: Hub) -> None:
    _pid, update = _room(hub)
    ok = _mark_http(hub, update).json()
    with hub.db._connection() as conn:
        columns = {r["name"]: r for r in conn.execute("PRAGMA table_info(project_update_deliveries)")}
        assert columns["operation_id"]["notnull"] == 1
        keys = [dict(r) for r in conn.execute("PRAGMA foreign_key_list(project_update_deliveries)")]
        assert {(k["table"], k["from"], k["to"]) for k in keys} >= {("kernel_operations", "operation_id", "operation_id")}
        assert all(k["on_delete"] in ("NO ACTION", "RESTRICT") for k in keys), keys
        row = _rows(hub, update)[0]
        for values, why in (
            (("pdel_x1", update, row["project_id"], "t", None, None), "NULL operation_id"),
            (("pdel_x2", update, row["project_id"], "t", None, ok["operation_id"]), "a second row for one operation"),
            (("pdel_x3", update, row["project_id"], "t", None, "op_not_in_the_kernel"), "an operation the kernel never admitted"),
        ):
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO project_update_deliveries (id, update_id, project_id, delivered_at,"
                             " delivered_to, operation_id) VALUES (?, ?, ?, ?, ?, ?)", values)
                pytest.fail(why)


def test_a_failure_after_the_insert_leaves_no_row_no_state_no_receipt_and_a_replay_succeeds_once(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.db.updates import UpdateDeliveriesRepository

    _pid, update = _room(hub)
    real = UpdateDeliveriesRepository.insert_delivery_in_transaction

    def insert_then_fail(self: Any, conn: Any, **kwargs: Any) -> Any:
        real(self, conn, **kwargs)
        raise RuntimeError("injected after the insert")

    monkeypatch.setattr(UpdateDeliveriesRepository, "insert_delivery_in_transaction", insert_then_fail)
    body = {"delivered_to": "Priya", "command_id": "confirm-rollback"}
    failed = _mark_http(hub, update, body)
    assert failed.status_code == 500, failed.text
    assert _rows(hub, update) == []
    [mark] = _marks(hub)
    assert mark["state"] == "claimed" and mark["outcome"] is None, mark  # no terminal state, no receipt
    monkeypatch.setattr(UpdateDeliveriesRepository, "insert_delivery_in_transaction", real)
    time.sleep(1.1)  # the replay writes later than he confirmed
    replayed = _mark_http(hub, update, body)
    assert replayed.status_code == 200, replayed.text
    again = _mark_http(hub, update, body)
    assert again.json()["delivery"] == replayed.json()["delivery"]
    assert len(_rows(hub, update)) == 1
    assert [(m["state"], m["outcome"]) for m in _marks(hub)] == [("succeeded", "succeeded")]
    assert replayed.json()["operation_id"] == mark["operation_id"]
    # delivered_at is the confirmation (the operation's admission), not the write.
    assert _rows(hub, update)[0]["delivered_at"] == _confirmed_at(_operation(hub, mark["operation_id"]))


def test_a_delivery_leaves_the_published_update_untouched(hub: Hub) -> None:
    _pid, update = _room(hub)
    with hub.db._connection() as conn:
        before = dict(conn.execute("SELECT * FROM project_updates WHERE id=?", (update,)).fetchone())
    assert _mark_http(hub, update, {"delivered_to": "Priya"}).status_code == 200
    with hub.db._connection() as conn:
        assert dict(conn.execute("SELECT * FROM project_updates WHERE id=?", (update,)).fetchone()) == before
