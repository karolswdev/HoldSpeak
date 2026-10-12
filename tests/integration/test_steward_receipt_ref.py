"""The test diet (2026-10-11): a steward effect's receipt names the object it made.

The Steward posture draws an openable chip for each step receipt's ``ref``
(``web/src/features/project-room/steward/model.ts`` ``receiptRefs``). Before
this, no producer wrote one, and the face test invented it (the SCAR LAW). The
real hub now writes ``update:<id>`` for a drafted update and
``action_item:<id>`` for the Door item a run filed.

The second test fences the recorded answers the face replays
(``scripts/record_steward_fixture.py``): their shape is the hub's shape.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import record_steward_fixture as recorder  # noqa: E402

from tests.integration.test_desk_agents_wire import _same_shape, _shape  # noqa: E402

pytestmark = pytest.mark.timeout(240)


@pytest.fixture(scope="module")
def recorded() -> dict[str, Any]:
    return recorder.record()


def _steps(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {step["effect_kind"]: step for step in run["detail"]["steps"]}


def test_an_applied_effect_receipt_names_the_object_it_made(recorded: dict[str, Any]) -> None:
    steps = _steps(recorded["completed"])
    draft = steps["draft_update"]
    assert draft["receipt"]["ref"] == f"update:{draft['observed']['update_id']}"
    door = steps["create_door_item"]
    assert door["receipt"]["ref"] == f"action_item:{door['observed']['door_item_id']}"
    # The ref names a real update of this Room.
    updates = {u["id"] for u in recorded["updates"]["updates"]}
    assert draft["observed"]["update_id"] in updates
    # An effect that makes no one object, or was skipped, names nothing.
    assert "ref" not in steps["refresh_sources"]["receipt"]
    assert "ref" not in steps["create_proposals"]["receipt"]
    skipped = _steps(recorded["partial"])["create_door_item"]
    assert skipped["receipt"]["outcome"] == "skipped" and "ref" not in skipped["receipt"]


def test_the_recorded_steward_answers_have_the_hubs_shape(recorded: dict[str, Any]) -> None:
    stored = json.loads(recorder.OUT.read_text())
    live = {"schema": "steward-recorded@1", "recordedBy": "scripts/record_steward_fixture.py", **recorded}
    diffs = _same_shape(_shape(stored), _shape(json.loads(json.dumps(live, default=str))))
    assert not diffs, (
        f"{recorder.OUT.name}: the stored answers are not the hub's shape "
        f"(run scripts/record_steward_fixture.py and read the diff): {diffs[:10]}"
    )
