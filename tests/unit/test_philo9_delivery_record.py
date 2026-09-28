"""PHILO-9-01: the delivery record (the owner's Q0 ruling, "Several per update").

Story 01 owns the table ``project_update_deliveries``, its append-only
repository and the read-backs; ``project.mark_update_delivered`` and its route
land in PHILO-9-02 with their admission (R4-2). A delivery is a new capability:
no red is claimed; the proofs are the read-backs and the mutations below.

* The additive reconcile creates the table on an EXISTING database.
* The repository appends; it has no update or delete path, and no module in
  ``holdspeak/`` writes the table any other way.
* A delivery never writes ``project_updates`` -- fenced by a MUTATION: a
  delivery that also writes the published update turns the fence red.
* Two rows for one update read back in order through ``project.list_updates``
  (MCP and HTTP) and the Room read; a draft is refused.
* The operation link is real: ``operation_id`` references a real kernel
  operation (minted here by the owner's admitted decision writes), unique.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _tool(hub: Hub, name: str, arguments: dict[str, Any]) -> Any:
    is_error, value = hub.mcp(name, arguments)
    assert not is_error, value
    return value


def _published(hub: Hub) -> tuple[str, str]:
    pid = hub.client.post("/api/projects", json={"name": "Payments ledger cutover"}).json()["project"]["id"]
    update_id = hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    assert hub.client.post(f"/api/updates/{update_id}/publish", json={}).status_code == 200
    return pid, update_id


def _operation(hub: Hub, title: str) -> str:
    """A REAL kernel operation: the owner's admitted decision write mints it."""
    made = hub.client.post("/api/decisions", json={"title": title}).json()
    assert made.get("operation_id"), made
    return made["operation_id"]


def _update_row(hub: Hub, update_id: str) -> dict[str, Any]:
    with hub.db._connection() as conn:
        return dict(conn.execute("SELECT * FROM project_updates WHERE id = ?", (update_id,)).fetchone())


def test_the_reconcile_creates_the_table_on_an_existing_database(tmp_path: Path) -> None:
    from holdspeak.db import Database

    path = tmp_path / "existing.db"
    Database(path)
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE project_update_deliveries")  # the database as main left it
    conn.commit()
    assert not conn.execute("SELECT name FROM sqlite_master WHERE name='project_update_deliveries'").fetchone()
    conn.close()
    Database(path)  # opening it reconciles
    conn = sqlite3.connect(path)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(project_update_deliveries)")]
    foreign = {(row[2], row[3]) for row in conn.execute("PRAGMA foreign_key_list(project_update_deliveries)")}
    indexes = {row[1] for row in conn.execute("PRAGMA index_list(project_update_deliveries)")}
    conn.close()
    assert columns == ["id", "update_id", "project_id", "delivered_at", "delivered_to", "operation_id"]
    assert foreign == {("project_updates", "update_id"), ("kernel_operations", "operation_id")}
    assert "idx_project_update_deliveries_update" in indexes


def test_the_repository_has_no_update_or_delete_path() -> None:
    from holdspeak.db.updates import UpdateDeliveriesRepository

    public = sorted(name for name in vars(UpdateDeliveriesRepository) if not name.startswith("_") and name != "table")
    assert public == ["insert_delivery", "insert_delivery_in_transaction", "list_for_update", "list_for_updates"]
    writers = []
    for path in (REPO / "holdspeak").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"(UPDATE|DELETE\s+FROM)\s+project_update_deliveries", text, re.IGNORECASE):
            writers.append(str(path.relative_to(REPO)))
    assert writers == [], f"a row is final; these modules rewrite it: {writers}"


def _deliver(hub: Hub, update_id: str, operation_id: str, to: str | None,
             insert: Callable[..., dict[str, Any]] | None = None) -> dict[str, Any]:
    insert = insert or hub.db.project_update_deliveries.insert_delivery
    return insert(update_id=update_id, operation_id=operation_id, delivered_to=to)


def _assert_the_update_is_untouched(hub: Hub, update_id: str, insert: Callable[..., dict[str, Any]] | None) -> None:
    before = _update_row(hub, update_id)
    _deliver(hub, update_id, _operation(hub, "untouched"), "Priya", insert)
    assert _update_row(hub, update_id) == before, "a delivery wrote project_updates"


def test_a_delivery_never_writes_the_published_update(hub: Hub) -> None:
    _pid, update_id = _published(hub)
    _assert_the_update_is_untouched(hub, update_id, None)


def test_the_untouched_fence_turns_red_on_a_delivery_that_writes_the_update(hub: Hub) -> None:
    """The MUTATION: a delivery that also stamps the published update."""
    _pid, update_id = _published(hub)
    real = hub.db.project_update_deliveries.insert_delivery

    def mutant(**kwargs: Any) -> dict[str, Any]:
        row = real(**kwargs)
        with hub.db._connection() as conn:
            conn.execute("UPDATE project_updates SET updated_at = '2099-01-01T00:00:00+00:00' WHERE id = ?",
                         (kwargs["update_id"],))
        return row

    with pytest.raises(AssertionError, match="a delivery wrote project_updates"):
        _assert_the_update_is_untouched(hub, update_id, mutant)


def test_a_draft_is_refused_and_an_operation_is_used_once(hub: Hub) -> None:
    from holdspeak.db.updates import UpdateNotPublishedError

    pid, update_id = _published(hub)
    draft = hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    with pytest.raises(UpdateNotPublishedError):
        _deliver(hub, draft, _operation(hub, "draft"), None)
    with pytest.raises(LookupError):
        _deliver(hub, "upd-none", _operation(hub, "none"), None)
    op = _operation(hub, "once")
    _deliver(hub, update_id, op, "Priya")
    with pytest.raises(sqlite3.IntegrityError):
        _deliver(hub, update_id, op, "Tomas")  # operation_id is UNIQUE
    with pytest.raises(sqlite3.IntegrityError):
        _deliver(hub, update_id, "op_not_a_kernel_operation", "Tomas")  # it references kernel_operations


def test_two_deliveries_read_back_in_order_on_every_read(hub: Hub) -> None:
    pid, update_id = _published(hub)
    first = _deliver(hub, update_id, _operation(hub, "first"), "Priya")
    second = _deliver(hub, update_id, _operation(hub, "second"), "Tomas")
    assert first["project_id"] == second["project_id"] == pid  # derived from the stored update

    def rows(deliveries: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
        return [(d["id"], d["delivered_to"], d["operation_id"]) for d in deliveries]

    expected = rows([first, second])
    over_mcp = _tool(hub, "project.list_updates", {"project_id": pid})["updates"]
    over_http = hub.client.get(f"/api/projects/{pid}/updates").json()["updates"]
    room = hub.client.get(f"/api/projects/{pid}/room").json()["updates"]
    for updates in (over_mcp, over_http):
        published = next(u for u in updates if u["id"] == update_id)
        assert rows(published["deliveries"]) == expected
    assert rows(room["latest_published"]["deliveries"]) == expected
    assert [d["delivered_at"] for d in room["latest_published"]["deliveries"]] == [first["delivered_at"], second["delivered_at"]]
    # A draft carries none.
    draft = hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]
    listed = {u["id"]: u for u in hub.client.get(f"/api/projects/{pid}/updates").json()["updates"]}
    assert listed[draft["id"]]["deliveries"] == []
    assert json.loads(json.dumps(listed[update_id]["deliveries"])) == over_http[[u["id"] for u in over_http].index(update_id)]["deliveries"]
