"""The Dreaming backlog's third source: the canon (2026-11-01).

A night with no "dream" task still has work: the desk sweep's KNOWN_REDS and
the UX-canon scanner's findings, read by rule from the night Program's own
repository, become Door tasks (at most 5 a night, inside ``within``), never
the same item twice while its task is open. The scanner here is the rig
repository's own ``scripts/ux_canon_scan.py`` (it writes the real scanner's
``--json`` shape); the sweep file is real Python syntax, read, never run.
"""
from __future__ import annotations

from pathlib import Path

from holdspeak.services import program_canon
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

SWEEP = '''
from typing import Any
KNOWN_REDS: dict[tuple[str, int], list[Any]] = {
    ("desk", 1440): [
        Red("overlap", r"^People x Conductor", "the People icon overlaps the Conductor icon by 5 px", maybe=True),
    ],
    ("room", 1440): [
        Red("still", r"^Pause moved", "Room: a late read moves the body after the window settles", maybe=True),
    ],
}
'''

SCANNER = '''import json, sys
args = sys.argv[1:]
out = args[args.index("--json") + 1]
faces = {
    "TodayView": [{"file": "desk/pullouts/views/TodayView.tsx", "line": 12, "rule": "raw-ids", "text": "Raw id in JSX"},
                  {"file": "desk/pullouts/views/TodayView.tsx", "line": 40, "rule": "A3-prose", "text": "Prose line"}],
    "NoteEditor": [{"file": "desk/notes/NoteEditor.tsx", "line": 7, "rule": "emoji", "text": "Emoji in JSX text"}],
    "PeopleCore": [{"file": "pages/cores/PeopleCore.tsx", "line": 3, "rule": "B", "text": "Outside the night"}],
    "Gadgets": [{"file": "desk/kit/gadgets.tsx", "line": 9, "rule": "A8", "text": "A raw button"},
                {"file": "desk/kit/gadgets.tsx", "line": 19, "rule": "A8", "text": "Another raw button"}],
}
json.dump({"totals": {}, "faces": faces}, open(out, "w"))
'''


def _repo(rig: Rig) -> None:
    (rig.repo / "tests" / "e2e").mkdir(parents=True)
    (rig.repo / "tests" / "e2e" / "test_desk_sweep.py").write_text(SWEEP, encoding="utf-8")
    (rig.repo / "scripts").mkdir()
    (rig.repo / "scripts" / "ux_canon_scan.py").write_text(SCANNER, encoding="utf-8")


def _night(rig: Rig) -> dict:
    pid = rig.service.create(OWNER, title="Dreaming", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle")["id"]
    program = rig.service.store.get_program(pid)
    program["within"] = ["web/src/desk/", "docs/"]
    rig.service.store.save_program(program)
    return rig.service.store.get_program(pid)


def _canon_tasks(rig: Rig) -> list:
    return [row for row in rig.db.meetings.list_action_items(include_completed=False)
            if getattr(row, "source_type", "") == "canon"]


def test_the_canon_files_five_door_tasks_inside_within_and_never_twice_while_open(tmp_path) -> None:
    rig = Rig(tmp_path)
    _repo(rig)
    program = _night(rig)
    first = program_canon.file_items(rig.runner, program, limit=8)
    assert len(first) == 5  # at most 5 a night, whatever the room
    tasks = [row.task for row in _canon_tasks(rig)]
    assert len(tasks) == 5
    assert "Fix the desk sweep's known red (desk at 1440): the People icon overlaps the Conductor icon by 5 px" in tasks
    assert ("Fix the UX-canon finding (raw-ids) in web/src/desk/pullouts/views/TodayView.tsx:12: Raw id in JSX"
            in tasks)
    assert not any("PeopleCore" in task for task in tasks)  # outside `within`
    assert all(item["kind"] == "action" for item in first)
    # The next night: the open ones are not filed again; only what is left.
    second = program_canon.file_items(rig.runner, program, limit=5)
    assert [item["task"] for item in second] == [
        "Fix the UX-canon finding (A3-prose) in web/src/desk/pullouts/views/TodayView.tsx:40: Prose line",
        "Fix the UX-canon finding (emoji) in web/src/desk/notes/NoteEditor.tsx:7: Emoji in JSX text"]
    assert program_canon.file_items(rig.runner, program, limit=5) == []
    # Done, and still in the canon: it may come back.
    done = next(row for row in _canon_tasks(rig) if "known red (desk at 1440)" in row.task)
    rig.db.meetings.update_action_item_status(done.id, "done")
    again = program_canon.file_items(rig.runner, program, limit=5)
    assert [item["task"] for item in again] == [done.task]


def test_a_night_with_no_dream_task_reads_the_canon(tmp_path) -> None:
    from datetime import datetime

    from holdspeak.services import program_night

    rig = Rig(tmp_path)
    _repo(rig)
    program = _night(rig)
    program["control"] = "normal"
    program["night"] = program_night_shape()
    rig.service.store.save_program(program)
    start = datetime.now().astimezone()
    added = program_night.read_backlog(rig.runner, rig.service.store.get_program(program["id"]), start, start)
    assert added == 0  # below YOLO: he takes each with Add to tonight
    lines = [row["line"] for row in rig.service.store.list_checkpoints(program["id"])]
    assert "The backlog has 5 items for tonight; Add to tonight takes each" in lines
    assert len(_canon_tasks(rig)) == 5


def test_a_repository_with_no_canon_files_nothing(tmp_path) -> None:
    rig = Rig(tmp_path)
    assert program_canon.file_items(rig.runner, _night(rig)) == []
    assert program_canon.known_reds(Path(tmp_path)) == []


def program_night_shape() -> dict:
    from holdspeak.services.program_text import parse_night

    return parse_night("23:30–07:00 · at most 8 steps")
