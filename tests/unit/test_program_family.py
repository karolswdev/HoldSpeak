"""PG-IMPORT IMP7 (BROCREW-IMPORT-2026-11-01): the forest, in the Program window.

BroCrew: "Work is a tree, not a thread … trace any result back to what asked
for it." A Program's GET carries ``family``: the Program it came from (an
audit's fix program names it by ``origin_ref`` ``program:<id>``; a Program a
step's agent made names it by its launch) and the Programs it made, each a
plain row (name, state word, the ending word for a child, the one list line).
The list names each row's parent and gives the parent its family's count and
one worst state. A Program with no family carries an empty one.
"""
from __future__ import annotations

from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig
from tests.unit.test_program_service import _launch_principal


def _made(rig: Rig, title: str, principal=OWNER, **kw) -> str:
    return rig.service.create(principal, title=title, repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                              template="fast-cycle", control="normal", **kw)["id"]


def test_a_program_names_its_parent_and_its_children(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    audit = _made(rig, "Audit the atlas")
    lone = _made(rig, "Lone")
    fix = _made(rig, "Fix: Audit the atlas", origin_ref=f"program:{audit}")
    rig.service.plan(OWNER, audit, steps=[{"title": "Read", "brief": "x"}])
    rig.service.start(OWNER, audit)
    rig.tick()
    agent = _launch_principal(monkeypatch, rig.step(audit, 1)["launch_id"])
    made = _made(rig, "A program an agent made", principal=agent)

    family = rig.program(audit)["family"]
    assert family["parent"] is None
    assert [row["id"] for row in family["children"]] == [fix, made]
    child = family["children"][0]
    assert child["name"] == "Fix: Audit the atlas" and child["state_word"] and "line" in child
    assert child["ending"] == "none"
    up = rig.program(fix)["family"]
    assert up["parent"]["id"] == audit and up["parent"]["name"] == "Audit the atlas" and up["children"] == []
    assert rig.program(made)["family"]["parent"]["id"] == audit
    assert rig.program(lone)["family"] == {"parent": None, "children": []}

    rows = {row["id"]: row for row in rig.service.list(OWNER)["programs"]}
    assert rows[fix]["parent_id"] == audit and rows[made]["parent_id"] == audit
    assert "parent_id" not in rows[lone] and "kin" not in rows[lone]
    assert rows[audit]["kin"]["children"] == 2
    assert rows[audit]["kin"]["worst_word"] == rows[fix]["state_word"]
