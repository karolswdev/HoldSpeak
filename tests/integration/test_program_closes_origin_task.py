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
