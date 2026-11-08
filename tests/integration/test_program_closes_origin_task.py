"""The first real night (2026-11-01): a step made from a Door task closes the
task when it merges, with the merge as its evidence (J4 station 5). Before,
the backlog's tasks stayed open after their steps merged (a remote with no
PR: no follow-through closed them)."""
from __future__ import annotations

from tests.integration.program_night_seed import door_task
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


def _status(rig: Rig, item_id: str) -> str:
    rows = rig.db.meetings.list_action_items(include_completed=True)
    return next(str(row.status) for row in rows if str(row.id) == item_id)


def test_a_merged_step_closes_its_door_task_once_with_the_merge(tmp_path) -> None:
    rig = Rig(tmp_path, github=False)  # a bare remote: HoldSpeak merges, no PR
    task = door_task(rig, "dream: add docs/glossary.md")
    pid = rig.service.create(OWNER, title="Night", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Glossary", "brief": "Add docs/glossary.md.",
                                         "origin_ref": f"action:{task}"}])
    rig.service.start(OWNER, pid)
    rig.tick()
    assert _status(rig, task) == "open"
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"docs/glossary.md": "A program is a goal in steps.\n"})
    rig.tick(4)
    step = rig.step(pid, 1)
    assert step["state"] in ("merged", "done"), step["state"]
    assert _status(rig, task) == "done"
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid)]
    closed = [line for line in lines if line.startswith("Closed its Door task with the merge ")]
    assert len(closed) == 1, lines
    # The evidence is the commit on main (the merge), not the builder's commit.
    merged = rig.service.store.list_steps(pid)[0]["facts"]["merged_commit"]
    assert closed[0] == f"Closed its Door task with the merge {merged[:8]} as evidence"
    rig.tick(2)  # merged → done does not close it again
    assert len([line for line in (row["line"] for row in rig.service.store.list_checkpoints(pid))
                if line.startswith("Closed its Door task")]) == 1


def test_a_parked_step_leaves_its_door_task_open(tmp_path) -> None:
    rig = Rig(tmp_path)
    task = door_task(rig, "dream: something")
    pid = rig.service.create(OWNER, title="Night", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Something", "brief": "Do it.", "origin_ref": f"action:{task}"}])
    rig.service.start(OWNER, pid)
    rig.tick()
    rig.service.park(OWNER, pid)
    assert _status(rig, task) == "open"


def test_only_the_step_bound_to_the_action_closes_it(tmp_path, monkeypatch) -> None:
    """HS-S21 (D14/G21 = A): a Program made from an action closes it through
    the one row that carries it (the Add well's bound append), never through
    an ordinary row or the Program's own origin."""
    from types import SimpleNamespace

    rig = Rig(tmp_path, github=False)
    monkeypatch.setattr(rig.service, "_project_source", lambda project_id: SimpleNamespace(primary_path=str(rig.repo)))
    task = door_task(rig, "dream: add docs/glossary.md and docs/terms.md")
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-docs', 'Docs')")
    pid = rig.service.from_action(OWNER, task, project_id="proj-docs")["id"]
    with rig.db._connection() as conn:
        conn.execute("UPDATE programs SET check_command=?, control='yolo' WHERE id=?", (f"sh {FAKE_CHECK}", pid))
    rig.service.plan(OWNER, pid, steps=[{"title": "Terms", "brief": "Add docs/terms.md."}])
    rig.service.plan(OWNER, pid, steps=[{"title": "Glossary", "brief": "Add docs/glossary.md.", "origin_ref": f"action:{task}"}])
    assert [step["origin_ref"] for step in rig.service.store.list_steps(pid)] == [None, f"action:{task}"]
    rig.service.start(OWNER, pid)
    rig.tick()
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"docs/terms.md": "Terms.\n"})
    rig.tick(4)
    assert rig.step(pid, 1)["state"] in ("merged", "done")
    assert _status(rig, task) == "open"  # the ordinary row and the Program's origin close nothing
    rig.tick()
    rig.agent.finish(rig.step(pid, 2)["launch_id"], {"docs/glossary.md": "A program is a goal in steps.\n"})
    rig.tick(4)
    assert rig.step(pid, 2)["state"] in ("merged", "done")
    assert _status(rig, task) == "done"
