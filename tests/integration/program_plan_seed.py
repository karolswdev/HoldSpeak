"""The Programs the planning replies were recorded on (PG-LANG LANG6).

``scripts/record_program_plan_reply.py`` builds each case's Program with
this repository as its repository and records the real engine's replies;
``tests/unit/test_program_planner.py`` and the route tests build the SAME
Program on a rig whose repository holds the owned files at the recorded
sizes (``seed_files``), and replay the replies through the runner. Change a
case only with a new recording.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from tests.integration.program_rig import OWNER, Rig, git

#: Journey J1 (PROGRAM-JOURNEYS-2026-10-31.md, "What he drops in"), the two
#: paragraphs as he pastes them.
J1_GOAL = (
    "After a meeting, the meeting's Note should end with a short recap: the decisions, the actions with their "
    "owners, and the open questions. It comes from the transcript we already keep, runs on the local model, and "
    "sends nothing out. It is a section of the Note that I can edit, not a new window.\n\n"
    "It must be fast: under 20 seconds after Stop on this Mac. It must not make up owners: when nobody was named, "
    "it says \"No owner\". Alice asked for this for her team's standups, so she sees it before it ships."
)

BIG_FILE_GOAL = (
    "Move the Program text apply (text_apply and _apply_text) out of holdspeak/services/program_service.py into "
    "its own module, holdspeak/services/program_text_apply.py. The service keeps a thin method that calls it. "
    "No behaviour changes: tests/unit/test_program_text.py and tests/integration/test_desk_programs.py stay green."
)

#: JRN1 (PROGRAM-JOURNEYS J1 "the draft proposes several Programs"): one
#: paste that is three separate goals, each a change that ships on its own.
SPLIT_GOAL = (
    "Three things before the standup review. First, after a meeting the meeting's Note should end with a short "
    "recap: the decisions, the actions with their owners and the open questions, from the transcript we keep.\n\n"
    "Second, the Calls window should list the last ten calls with their length and who was on them, newest "
    "first.\n\n"
    "Third, the Programs window should export the list to a new Note, one line per program with its state."
)

CASES: dict[str, dict[str, Any]] = {
    # J1 sized for the home engine's 64k (the owner: "our context maxes out
    # at 64k tokens"): every step must fit in 32k.
    "j1": {"title": "Meeting recap in the Note", "goal": J1_GOAL, "template": "build-and-review",
           "control": "normal", "check": "scripts/quick_check.sh", "budget": "64k"},
    # A goal that names a file over the working share alone
    # (program_service.py, about 50k tokens): the draft's step is too big,
    # and the planner is asked once to split it.
    "big_file": {"title": "The text apply in its own module", "goal": BIG_FILE_GOAL, "template": "build-and-review",
                 "control": "normal", "check": "scripts/quick_check.sh", "budget": "64k"},
    # JRN1: a three-goal paste; the draft proposes three Programs.
    "split_programs": {"title": "Before the standup review", "goal": SPLIT_GOAL, "template": "fast-cycle",
                       "control": "normal", "check": "scripts/quick_check.sh", "budget": "64k"},
}


#: The recording's repository is HoldSpeak: its shot command makes a Shot provable.
SHOT_CONFIG = Path(__file__).resolve().parents[2] / ".holdspeak" / "program.json"


def seed_files(rig: Rig, file_bytes: Mapping[str, int]) -> None:
    """The owned files at the sizes the recording read (filler bytes), and
    the recording repository's ``.holdspeak/program.json``."""
    config = rig.repo / ".holdspeak" / "program.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(SHOT_CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    for path, size in file_bytes.items():
        if not size:
            continue
        target = rig.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        line = "# recorded size filler\n"
        target.write_text((line * (size // len(line) + 1))[:size], encoding="utf-8")
    git(rig.repo, "add", "-A")
    git(rig.repo, "commit", "-m", "files", "--allow-empty")


def create(rig: Rig, case: Mapping[str, Any], *, repository: Optional[str] = None,
           file_bytes: Optional[Mapping[str, int]] = None) -> str:
    """The case's Program in Drafting, no steps (station 1, Dropped), with
    the case's budget."""
    if file_bytes:
        seed_files(rig, file_bytes)
    with rig.db._connection() as conn:
        conn.execute("INSERT OR IGNORE INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    pid = rig.service.create(OWNER, title=case["title"], goal=case["goal"], repository=repository or str(rig.repo),
                             check_command=case["check"], template=case["template"], control=case["control"],
                             project_id="proj-holdspeak")["id"]
    if case.get("budget"):
        # The text's ``budget 64k``: the planner reads the Program's budget.
        rig.service.update(OWNER, pid, budget_tokens=case["budget"])
    return pid
