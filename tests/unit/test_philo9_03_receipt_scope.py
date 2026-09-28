"""PHILO-9-03 (Codex Astra r2 finding 3): the census of every pipeline receipt
producer the Room's RECEIPTS reads. A receipt belongs to a Room only by the
PRODUCER's project-identity field (``_RECEIPT_SCOPE``), never by a value in
the payload. Every Room write method must declare where that field lives, and
an ``args`` declaration must name a real ``project_id`` parameter. The
mutation drops one declaration and the census bites."""
from __future__ import annotations

import inspect

from holdspeak.services import project_service as ps
from holdspeak.services.project_service import ProjectService
from holdspeak.services.watch_service import WatchService


def census(scope: dict[str, tuple[str, str]]) -> list[str]:
    problems = [f"{m}: no project-identity declaration" for m in sorted(ps.ROOM_WRITE_METHODS - set(scope))]
    problems += [f"{m}: declared but not a Room write" for m in sorted(set(scope) - ps.ROOM_WRITE_METHODS)]
    for method, (side, key) in scope.items():
        owner = ProjectService if hasattr(ProjectService, method) else WatchService
        fn = getattr(owner, method, None)
        if fn is None:
            problems.append(f"{method}: no producer")
            continue
        if side == "args" and key not in inspect.signature(fn).parameters:
            problems.append(f"{method}: declares args.{key} but takes no such parameter")
        if (side, key) not in {("args", "project_id"), ("result", "id"), ("result", "project_id")}:
            problems.append(f"{method}: unknown identity field {side}.{key}")
    return problems


def test_every_room_write_producer_declares_its_project_identity_field() -> None:
    assert census(ps._RECEIPT_SCOPE) == []


def test_mutation_a_producer_without_a_declaration_is_caught() -> None:
    mutated = dict(ps._RECEIPT_SCOPE)
    mutated.pop("create_item")
    assert census(mutated) == ["create_item: no project-identity declaration"]


def test_free_text_equal_to_another_projects_id_does_not_scope_a_receipt() -> None:
    # B's item whose TITLE is A's id: the producer's field says B.
    args = '{"project_id":"proj-b","payload":{"item_type":"risk","title":"proj-a"}}'
    assert ps._receipt_project("create_item", args, "{}") == "proj-b"
    # B named after A's id: the created project's own id is B.
    assert ps._receipt_project("create_project", '{"fields":{"name":"proj-a"}}', '{"id":"proj-b","name":"proj-a"}') == "proj-b"
    # A truncated result still yields its top-level identity, never a nested one.
    assert ps._receipt_project("pause_watch", '{"watch_id":"w1"}', '{"id":"w1","project_id":"proj-a","rules":{"x":"proj-b') == "proj-a"
    assert ps._receipt_project("pause_watch", '{"watch_id":"w1"}', '{"id":"w1","rules":{"project_id":"proj-a"}}') is None
