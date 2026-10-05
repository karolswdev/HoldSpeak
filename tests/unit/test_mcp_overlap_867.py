"""Astra's three interleavings on #867: two concurrent calls, the real producer delayed.

The guards are in the writes, so they hold for any transport (these calls go
through ``server.handle_message``, with no per-key lock of ``POST /api/mcp``):

1. ``project.open_review`` x2 on one project -> ONE open review
   (``ProjectDeltaService._store_window``: check + insert in one BEGIN IMMEDIATE).
2. ``project.draft_update`` x2 with one command_id -> ONE draft
   (``ProjectUpdateService._claim_draft_command``).
3. ``project.watch.test`` overlapped by ``project.watch.set_rules`` -> the test
   answers ``stale`` and revision 2 is not marked passed
   (``update_watch_spec(expected_revision=...)``).
"""
from __future__ import annotations

import threading
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_update_service import ProjectUpdateService
from holdspeak.services.watch_service import WatchService
from tests.unit.test_project_mcp_commands import (  # noqa: F401 - fixtures
    _call,
    _seed_project,
    db,
    mcp_project,
)
from tests.unit.test_watch_service import OWNER as WATCH_OWNER, _make_watch


def _review_id(value: Any) -> Any:
    """The first ``review_id`` anywhere in a tool answer."""
    if isinstance(value, dict):
        if isinstance(value.get("review_id"), str):
            return value["review_id"]
        for item in value.values():
            if (found := _review_id(item)) is not None:
                return found
    return None


def _both(target: Any, *args_list: tuple) -> list[Any]:
    results: list[Any] = [None] * len(args_list)

    def run(index: int, args: tuple) -> None:
        results[index] = target(*args)

    threads = [threading.Thread(target=run, args=(i, a)) for i, a in enumerate(args_list)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    return results


def test_two_concurrent_open_reviews_make_one_review(db: Database, monkeypatch) -> None:
    pid = _seed_project(db, "proj-overlap-review", "Overlap Review")
    gate = threading.Barrier(2, timeout=5)
    real = ProjectDeltaService._observations_after_cursor

    def delayed(self, *args, **kwargs):
        # Both calls have passed the early "is a review open?" check here.
        try:
            gate.wait()
        except threading.BrokenBarrierError:
            pass
        return real(self, *args, **kwargs)

    monkeypatch.setattr(ProjectDeltaService, "_observations_after_cursor", delayed)
    answers = _both(_call, ("project.open_review", {"project_id": pid}),
                    ("project.open_review", {"project_id": pid}))
    assert all(is_error is False for is_error, _ in answers), answers
    with db._connection() as conn:
        open_reviews = conn.execute(
            "SELECT COUNT(*) FROM project_reviews WHERE project_id = ? AND status = 'open'",
            (pid,),
        ).fetchone()[0]
    assert open_reviews == 1
    ids = {_review_id(data) for _, data in answers}
    assert len(ids) == 1 and None not in ids, answers


def test_two_concurrent_drafts_with_one_command_id_make_one_draft(db: Database, monkeypatch) -> None:
    pid = _seed_project(db, "proj-overlap-draft", "Overlap Draft")
    calls: list[str] = []
    second_done = threading.Event()
    real = ProjectUpdateService.draft_update

    def delayed(self, *args, **kwargs):
        calls.append("draft")
        second_done.wait(3)  # the other call answers while this one drafts
        return real(self, *args, **kwargs)

    monkeypatch.setattr(ProjectUpdateService, "draft_update", delayed)
    arguments = {"project_id": pid, "command_id": "cmd-overlap-draft"}

    def call() -> Any:
        try:
            return _call("project.draft_update", arguments)
        finally:
            if len(calls) == 1 and threading.current_thread().name != "first":
                second_done.set()

    first = threading.Thread(target=lambda: results.append(call()), name="first")
    results: list[Any] = []
    first.start()
    while not calls and first.is_alive():
        threading.Event().wait(0.01)
    results.append(call())  # the second call, while the first drafts
    second_done.set()
    first.join(30)

    assert calls == ["draft"], f"the producer drafted {len(calls)} times"
    codes = sorted(str(data.get("code")) for is_error, data in results if is_error)
    assert codes == ["command_in_progress"], results


def test_a_watch_test_overlapped_by_set_rules_answers_stale(tmp_path) -> None:
    db = Database(tmp_path / "overlap-watch.db")
    _make_watch(db, "watch-overlap")
    db.automations.update_watch_spec("watch-overlap", revision=1)
    fetching = threading.Event()
    rules_set = threading.Event()

    def fetcher(principal, **kwargs):
        fetching.set()
        rules_set.wait(5)  # set_rules lands while the provider read runs
        return [{"number": 7, "state": "open", "title": "Seven"}]

    service = WatchService(db, snapshot_fetcher=fetcher)
    result: dict[str, Any] = {}
    tester = threading.Thread(target=lambda: result.update(service.test_watch(WATCH_OWNER, "watch-overlap")))
    tester.start()
    assert fetching.wait(5)
    WatchService(db).set_rules(WATCH_OWNER, "watch-overlap", [{
        "condition": {"operator": "any", "clauses": [
            {"field": "state", "comparison": "equals", "value": "open"}]},
        "actions": [{"kind": "project.observe"}],
    }])
    rules_set.set()
    tester.join(10)

    watch = db.automations.get_watch("watch-overlap")
    assert int(watch["revision"]) == 2
    assert watch["test_state"] == "stale", "revision 2 was marked by a test of revision 1"
    assert result["test_state"] == "stale"


@pytest.mark.parametrize("name", ["project.draft_update"])
def test_a_failed_draft_releases_its_command_id(db: Database, monkeypatch, name: str) -> None:
    pid = _seed_project(db, "proj-overlap-retry", "Retry")

    def broken(self, *args, **kwargs):
        raise RuntimeError("engine fell over")

    monkeypatch.setattr(ProjectUpdateService, "draft_update", broken)
    is_error, _ = _call(name, {"project_id": pid, "command_id": "cmd-retry"})
    assert is_error is True
    monkeypatch.undo()
    from holdspeak.mcp import server
    from types import SimpleNamespace
    from holdspeak.mcp.families import project as project_family
    from tests.unit.test_project_mcp_commands import OWNER

    monkeypatch.setattr(project_family, "get_database", lambda: db)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")
    is_error, data = _call(name, {"project_id": pid, "command_id": "cmd-retry"})
    assert is_error is False, data
