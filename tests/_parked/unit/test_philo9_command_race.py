"""PHILO-9-02 (law 9): the same-key race closed as a CLASS, not one site at a time.

Carried from PHILO-9-01 (Codex Astra r3 on PR #680, finding 3, MISSED): the
replay lookup ran BEFORE the write's transaction, so two callers with one key
could both find it absent and both write. Two sites share the shape:

* ``JournalStore.create_operation`` -- the kernel's replay by ``(principal,
  idempotency_key)``: the loser's INSERT hit the UNIQUE constraint and raised
  a raw ``IntegrityError`` (never a replay).
* ``ProjectService`` -- ``_check_idempotency`` then ``_record_command ... ON
  CONFLICT DO UPDATE``: two revisions and two change rows for one command.

Each fence makes the interleaving deterministic, the same way on main and on
the branch: both callers are held just past their lookup until the other has
arrived (or one second has passed). On main both write; with the write lock
taken before the lookup, the second caller cannot pass it until the first
committed, finds the first's record, and replays.
"""
from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Any

import pytest


class _Meet:
    """Hold each caller until both arrived, or ``timeout`` passed (never a deadlock)."""

    def __init__(self, parties: int = 2, timeout: float = 1.0) -> None:
        self._lock = threading.Lock()
        self._count = 0
        self._parties = parties
        self._all = threading.Event()
        self._timeout = timeout

    def arrive(self) -> None:
        with self._lock:
            self._count += 1
            if self._count >= self._parties:
                self._all.set()
        self._all.wait(self._timeout)


def _run_both(target: Any) -> list[Any]:
    results: list[Any] = [None, None]

    def worker(index: int) -> None:
        try:
            results[index] = target()
        except Exception as exc:  # the loser's raw failure is the red
            results[index] = exc

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    return results


def test_the_kernel_replay_lookup_holds_the_write_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.db.core import Database
    from holdspeak.kernel import journal_atomic
    from holdspeak.kernel.journal import JournalStore

    database = Database(tmp_path / "race.db")
    store = JournalStore(database._connection)
    meet = _Meet()
    real_insert = journal_atomic.insert_operation

    def held_insert(conn: Any, values: Any, now: float) -> None:
        meet.arrive()  # past the lookup; the other caller now reaches its own
        real_insert(conn, values, now)

    monkeypatch.setattr(journal_atomic, "insert_operation", held_insert)

    def create() -> Any:
        operation_id = "op_" + uuid.uuid4().hex
        return store.create_operation({
            "operation_id": operation_id, "request_id": "req-1", "idempotency_key": "same-key",
            "name": "project.archive", "version": 1, "principal_kind": "owner",
            "principal_identity": "owner-session", "target_ref": "project:p1", "placement": "node:x",
            "envelope_sha256": "sha256:same", "policy_version": "1", "authority_basis": "b",
            "state": "admitting", "native_id": "n1",
        })

    results = _run_both(create)
    failures = [r for r in results if isinstance(r, Exception)]
    assert failures == [], f"the loser raised instead of replaying: {failures!r}"
    assert results[0]["operation_id"] == results[1]["operation_id"], "two callers, two operations for one key"
    with database._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE idempotency_key='same-key'").fetchone()[0] == 1


def test_a_room_command_replay_holds_the_write_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.db.core import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.project_service import ProjectService

    database = Database(tmp_path / "race.db")
    service = ProjectService(database)
    owner = Principal(PrincipalKind.OWNER, "owner-session")
    project = service.create_project(owner, {"name": "Race"})
    pid = project["id"]
    with database._connection() as conn:
        start = conn.execute("SELECT revision FROM projects WHERE id=?", (pid,)).fetchone()[0]
    note = "note:n-race"
    meet = _Meet()
    real_check = ProjectService._check_idempotency

    def held_check(self: Any, *args: Any, **kwargs: Any) -> Any:
        replay = real_check(self, *args, **kwargs)
        if replay is None:
            meet.arrive()  # both found the command absent
        return replay

    monkeypatch.setattr(ProjectService, "_check_idempotency", held_check)
    results = _run_both(lambda: service.add_resource(owner, pid, note, command_id="cmd-race-1"))
    failures = [r for r in results if isinstance(r, Exception)]
    assert failures == [], f"a caller raised: {failures!r}"
    with database._connection() as conn:
        revisions = conn.execute("SELECT revision FROM projects WHERE id=?", (pid,)).fetchone()[0]
        changes = conn.execute(
            "SELECT COUNT(*) FROM project_changes WHERE project_id=? AND change_kind='project.resource.linked'", (pid,),
        ).fetchone()[0]
    assert changes == 1, f"one command wrote {changes} change rows"
    assert revisions == start + 1, "one command bumped the revision twice"
    assert results[0] == results[1], "the replay did not answer the original response"


def test_a_room_command_race_on_a_delete_answers_the_original_true_twice(tmp_path: Path,
                                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """Astra r3's DELETE shape: the first answers true, the second false, the replay false. One answer: true."""
    from holdspeak.db.core import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.project_service import ProjectService

    database = Database(tmp_path / "race.db")
    service = ProjectService(database)
    owner = Principal(PrincipalKind.OWNER, "owner-session")
    pid = service.create_project(owner, {"name": "Race"})["id"]
    service.add_resource(owner, pid, "note:n-del")
    meet = _Meet()
    real_check = ProjectService._check_idempotency

    def held_check(self: Any, *args: Any, **kwargs: Any) -> Any:
        replay = real_check(self, *args, **kwargs)
        if replay is None:
            meet.arrive()
        return replay

    monkeypatch.setattr(ProjectService, "_check_idempotency", held_check)
    results = _run_both(lambda: service.remove_resource(owner, pid, "note:n-del", command_id="cmd-race-del"))
    assert results == [True, True], results
