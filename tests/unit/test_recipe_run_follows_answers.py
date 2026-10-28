"""W6-D (2026-10-28): a recipe run with no engine of its own follows Answers.

On a fresh desk the Mode window said "No default model" while Ask answered:
``recipe.run`` had no row and did not follow ``ask.answer``. It now follows
it, like desk chat and calls; its own row still wins.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from holdspeak.db import Database
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile


def _assign(service: InferenceAssignmentService, capability_id: str, profile_id: str) -> None:
    service.set_assignment(OWNER, {
        "command_id": f"{capability_id}-{profile_id}", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": capability_id},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


def _recipe_run(service: InferenceAssignmentService) -> dict[str, Any]:
    summary = service.assignment_summary(OWNER)
    rows = {row["id"]: row for row in summary["task_overrides"]}
    return rows["recipe.run"]


def test_recipe_run_follows_the_answers_engine_when_unset(tmp_path: Path) -> None:
    db = Database(tmp_path / "desk.db")
    service = InferenceAssignmentService(db)
    _profile(db, "answers-engine")
    _assign(service, "ask.answer", "answers-engine")
    row = _recipe_run(service)
    assert row["has_override"] is False
    effective = row["effective"]
    assert effective["status"] == "assigned"
    assert effective["inherited_from"] == "capability"
    assert effective["assignment"]["scope"] == {"kind": "capability", "capability_id": "ask.answer"}
    assert [e["profile_id"] for e in effective["assignment"]["entries"]] == ["answers-engine"]


def test_an_own_recipe_run_assignment_still_wins(tmp_path: Path) -> None:
    db = Database(tmp_path / "desk.db")
    service = InferenceAssignmentService(db)
    _profile(db, "answers-engine")
    _profile(db, "recipe-engine")
    _assign(service, "ask.answer", "answers-engine")
    _assign(service, "recipe.run", "recipe-engine")
    row = _recipe_run(service)
    assert row["has_override"] is True
    effective = row["effective"]
    assert effective["assignment"]["scope"] == {"kind": "capability", "capability_id": "recipe.run"}
    assert [e["profile_id"] for e in effective["assignment"]["entries"]] == ["recipe-engine"]
