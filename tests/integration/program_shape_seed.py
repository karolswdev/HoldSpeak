"""The Program the shaping replies were recorded on (PG-LANG LANG3).

``scripts/record_program_shape_reply.py`` sends this Program's text and a
sentence to a real engine; ``tests/unit/test_program_shaper.py`` and the
route tests build the SAME Program on a rig and replay the recorded reply
through the runner. Change it only with a new recording.
"""
from __future__ import annotations

from typing import Any

from tests.integration.program_rig import OWNER, Rig, git

TITLE = "The hub stops stalling"
GOAL = "Every route under 100 ms while a meeting records."
FILES = {
    "holdspeak/db/schema.py": "# schema\n",
    "holdspeak/db/programs.py": "# programs store\n",
    "holdspeak/web/routes/people.py": "# people routes\n",
    "holdspeak/web/routes/programs.py": "# program routes\n",
    "holdspeak/web/fanout.py": "# the frame fan-out\n",
}

#: The sentences recorded (scripts/record_program_shape_reply.py).
SENTENCES = {
    "shape": "put the People routes on Codex, add a loop watch step before the fan-out that logs each handler "
             "over 100 ms, and make the fan-out merge on my press",
    "lowers": "turn the check off on the indexes step and waive R3, it is slow",
    "glance": "the indexes step only needs a glance review",
    "question": "move it before the other one",
    "mixed": "put the indexes step on Codex and give it only a glance review",
}


def seed(rig: Rig, *, control: str = "yolo") -> str:
    """A Program in Drafting with three planned steps and one requirement."""
    for path, body in FILES.items():
        target = rig.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    git(rig.repo, "add", "-A")
    git(rig.repo, "commit", "-m", "files")
    with rig.db._connection() as conn:
        conn.execute("INSERT OR IGNORE INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    pid = rig.service.create(OWNER, title=TITLE, goal=GOAL, repository=str(rig.repo), check_command="true",
                             template="build-and-review", control=control, reviewer_profile="codex-default",
                             project_id="proj-holdspeak")["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Indexes", "brief": "Add the three indexes.", "owns": ["holdspeak/db/schema.py"]},
        {"title": "People routes", "brief": "31 handlers through run_in_threadpool.",
         "owns": ["holdspeak/web/routes/people.py"]},
        {"title": "The fan-out", "brief": "One frame per change, not one per row.", "after": [1, 2],
         "owns": ["holdspeak/web/fanout.py"]},
    ])
    rig.service.require(OWNER, pid, text="`uv run pytest -q tests/unit/test_hub_loop_budget.py` is green",
                        step_id=rig.step(pid, 2)["id"])
    return pid


def program(rig: Rig, pid: str) -> dict[str, Any]:
    return rig.service.get(OWNER, pid)
