"""PHILO-7-01: THE RENAME REPAIR — a rename writes the name only.

Astra's charter check r2 (finding 2, MISSED 1) reproduced both through the real
service: a knowledge-base rename read ``existing.member_ids`` and replaced the
membership set with that snapshot, so a member added between the read and the
write was tombstoned; a zone rename read ``existing.parent_id`` and wrote it
back, so a move made between the read and the write was reversed.

Each fence below is a REAL-PRODUCER INTERLEAVING: the real ``PrimitiveService``
over a real SQLite database. The rename runs; the fence pauses it right after
its own real read of the row (the repository ``get`` returns the true row) and,
before the rename continues, makes another real service call. Then the rename
finishes and the fence asserts that the other action SURVIVED. No read is
mocked and no row is injected. The fence also asserts that the interleaving
really happened (the pause fired exactly once), so it can never pass empty.

This file imports no symbol the story adds, so it runs unchanged on a
``git archive`` copy of main (red) and on the branch (green).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from holdspeak.db import Database
from holdspeak.db import primitives as db_primitives
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.primitive_service import PrimitiveService

OWNER = Principal(PrincipalKind.OWNER, "owner")


def _pause_after_read(
    monkeypatch: pytest.MonkeyPatch, repository: type, target_id: str, interleave: Callable[[], None]
) -> list[str]:
    """Run *interleave* once, right after the next real ``get(target_id)`` returns.

    The real ``get`` runs first and its row is returned unchanged: the rename
    holds exactly what the database held at its read. Only then does the other
    real call run. Returns the list the fence reads to prove the pause fired.
    """
    real_get = repository.get
    fired: list[str] = []

    def get_then_interleave(self: Any, row_id: str, *args: Any, **kwargs: Any) -> Any:
        row = real_get(self, row_id, *args, **kwargs)
        if armed and str(row_id) == target_id:
            armed.clear()  # one pause only; the interleaved call reads freely
            fired.append(row_id)
            interleave()
        return row

    armed = [True]
    monkeypatch.setattr(repository, "get", get_then_interleave)
    return fired


def test_a_kb_rename_keeps_a_member_added_during_the_rename(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "kb-rename.db")
    service = PrimitiveService(db)
    kb = service.create_kb(OWNER, name="Reading", member_ids=["note:a"])
    assert [m["resource_ref"] for m in service.list_kb_members(OWNER, kb["id"])] == ["note:a"]

    # The other real call: kb.member.add of a NEW reference, made after the
    # rename read the knowledge base and before it writes.
    fired = _pause_after_read(
        monkeypatch, db_primitives.KBRepository, kb["id"],
        lambda: service.add_kb_member(OWNER, kb["id"], "note:b"),
    )
    renamed = service.update_kb(OWNER, kb["id"], name="Reading list")
    monkeypatch.undo()

    assert fired == [kb["id"]], "the rename never read the knowledge base; nothing was interleaved"
    assert renamed["name"] == "Reading list"
    live = {m["resource_ref"] for m in service.list_kb_members(OWNER, kb["id"])}
    assert live == {"note:a", "note:b"}, f"the rename tombstoned the member added during it: {sorted(live)}"
    assert set(service.get_kb(OWNER, kb["id"])["member_ids"]) == {"note:a", "note:b"}


def test_a_zone_rename_keeps_a_move_made_during_the_rename(tmp_path: Path, monkeypatch) -> None:
    db = Database(tmp_path / "zone-rename.db")
    service = PrimitiveService(db)
    p1 = service.create_directory(OWNER, directory_id="p1", name="Work")
    p2 = service.create_directory(OWNER, directory_id="p2", name="Home")
    zone = service.create_directory(OWNER, name="Plans", parent_id=p1["id"])
    assert service.get_directory(OWNER, zone["id"])["directory"]["parent_id"] == "p1"

    # The other real call: a zone move by parent_id from p1 to p2, made after
    # the rename read the zone and before it writes.
    fired = _pause_after_read(
        monkeypatch, db_primitives.DirectoryRepository, zone["id"],
        lambda: service.update_directory(OWNER, zone["id"], parent_id=p2["id"]),
    )
    renamed = service.update_directory(OWNER, zone["id"], name="Plans 2026")
    monkeypatch.undo()

    assert fired == [zone["id"]], "the rename never read the zone; nothing was interleaved"
    assert renamed["name"] == "Plans 2026"
    after = service.get_directory(OWNER, zone["id"])["directory"]
    assert after["parent_id"] == "p2", f"the rename reversed the move made during it: parent_id={after['parent_id']!r}"
    assert after["name"] == "Plans 2026"


# ── the admitted rows stay as they were (the repair touches renames only) ──


def test_a_kb_update_with_member_ids_still_sets_the_membership(tmp_path: Path) -> None:
    service = PrimitiveService(Database(tmp_path / "kb-members.db"))
    kb = service.create_kb(OWNER, name="Reading", member_ids=["note:a", "note:b"])
    updated = service.update_kb(OWNER, kb["id"], name="Renamed", member_ids=["note:c"])
    assert updated["name"] == "Renamed" and updated["member_ids"] == ["note:c"]
    assert {m["resource_ref"] for m in service.list_kb_members(OWNER, kb["id"])} == {"note:c"}


def test_a_zone_update_with_parent_id_still_moves_and_null_goes_to_the_root(tmp_path: Path) -> None:
    service = PrimitiveService(Database(tmp_path / "zone-move.db"))
    service.create_directory(OWNER, directory_id="p1", name="Work")
    zone = service.create_directory(OWNER, name="Plans", parent_id="p1")
    moved = service.update_directory(OWNER, zone["id"], name="Plans B", parent_id=None)
    assert moved["parent_id"] is None and moved["name"] == "Plans B"


def test_a_plain_rename_still_refuses_a_taken_name_and_an_unknown_id(tmp_path: Path) -> None:
    from holdspeak.services.errors import ConflictError, NotFound

    service = PrimitiveService(Database(tmp_path / "zone-taken.db"))
    service.create_directory(OWNER, directory_id="a", name="Alpha")
    service.create_directory(OWNER, directory_id="b", name="Beta")
    with pytest.raises(ConflictError):
        service.update_directory(OWNER, "b", name="alpha")
    with pytest.raises(NotFound):
        service.update_directory(OWNER, "missing", name="x")
    with pytest.raises(NotFound):
        service.update_kb(OWNER, "missing", name="x")
