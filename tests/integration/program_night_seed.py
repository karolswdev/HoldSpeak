"""The Programs the split and the night replies were recorded on (PG-LANG LANG8, LANG12).

``scripts/record_program_night_reply.py`` builds these cases with this
repository as the Program's repository and records the real engine's
replies; ``tests/unit/test_program_sizing.py`` and
``tests/unit/test_program_night.py`` build the SAME Programs on a rig whose
repository holds the owned files at the recorded sizes (``seed_files``), and
replay the replies through the runner. Change a case only with a new
recording.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from tests.integration.program_plan_seed import seed_files
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

#: One step over the working share of a 64k budget (32k): seven planning
#: modules of the engine, about 36k tokens with its brief.
SPLIT_STEP: dict[str, Any] = {
    "title": "Name the design section in each planning module",
    "brief": ("Each planning module of the Programs engine starts with a docstring. Make the first line of each "
              "docstring name its design section (PROGRAM-LANGUAGE §4, §5, §6). No behaviour changes; the tests stay "
              "green."),
    "owns": ["holdspeak/services/program_rounds.py", "holdspeak/services/program_shaper.py",
             "holdspeak/services/program_planner.py", "holdspeak/services/program_verifier.py",
             "holdspeak/services/program_requirements.py", "holdspeak/services/program_rules.py",
             "holdspeak/services/program_handoff.py"],
}

#: Journey J2, "What he drops in": three lines, one at a time, with Add to tonight.
NIGHT_ITEMS = (
    "The Calls window's status bar says \"Line starting\" for 40 s after the Line is up.",
    "The Terminals window has raw buttons.",
    "The Engines rows at 393 clip the readiness word.",
)
NIGHT_LINE = "23:30–07:00 · at most 8 steps"
WITHIN = ["web/src/desk/", "docs/", "tests/unit/"]


def make_split(rig: Rig, *, repository: Optional[str] = None, file_bytes: Optional[Mapping[str, int]] = None,
               control: str = "yolo") -> tuple[str, str]:
    """A Running Program with a 64k budget and two steps: the one too big
    (step 1) and one after it (step 2). Not started: the caller starts it."""
    if file_bytes:
        seed_files(rig, file_bytes)
    pid = rig.service.create(OWNER, title="The planning modules say where they are from",
                             goal="Every planning module names its design section.",
                             repository=repository or str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control=control)["id"]
    rig.service.update(OWNER, pid, budget_tokens="64k")
    rig.service.plan(OWNER, pid, steps=[
        dict(SPLIT_STEP),
        {"title": "Say it in the docs", "brief": "docs/programs.md names the sections.", "owns": ["docs/programs.md"],
         "after": [1]},
    ])
    step = next(row for row in rig.service.store.list_steps(pid) if row["ordinal"] == 1)
    return pid, step["id"]


def door_task(rig: Rig, words: str) -> str:
    """A Door task (an action item), as ``door.add_item`` writes one."""
    import uuid

    from holdspeak.timestamps import utc_now_iso

    item_id = "ai_" + uuid.uuid4().hex
    with rig.db._connection() as conn:
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at, "
            "delegated_at, source_type, source_ref) VALUES (?, NULL, ?, NULL, NULL, 'open', 'accepted', ?, NULL, "
            "'desk', '')", (item_id, words, utc_now_iso()))
    return item_id


def make_night(rig: Rig, *, repository: Optional[str] = None, control: str = "yolo",
               budget: str = "64k") -> tuple[str, list[str]]:
    """Journey J2's night Program (``night 23:30–07:00 · at most 8 steps``,
    ``within``, YOLO) with its three lines added to tonight as Door tasks:
    ``(program id, the step ids)``. Started."""
    pid = rig.service.create(OWNER, title="Dreaming · HoldSpeak", goal="Small fixes on the idle engine at night.",
                             repository=repository or str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control=control)["id"]
    rig.service.update(OWNER, pid, budget_tokens=budget, night=NIGHT_LINE, within=list(WITHIN))
    steps = []
    for words in NIGHT_ITEMS:
        added = rig.service.add_to_night(OWNER, kind="action", item_id=door_task(rig, words), program_id=pid)
        steps.append(added["step_id"])
    rig.service.start(OWNER, pid)
    return pid, steps


__all__ = ["NIGHT_ITEMS", "NIGHT_LINE", "SPLIT_STEP", "WITHIN", "door_task", "make_night", "make_split"]
