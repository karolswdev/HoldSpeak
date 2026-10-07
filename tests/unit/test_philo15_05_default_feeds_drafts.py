"""PHILO-15 lane 05, ruling 1 (inventory gap 8; owner law "strong defaults,
batteries included"): the Conductor's routine answers inherit the Default
for AI work.

Cadence drafts (``background.cadence_draft``) are OWNER work: the YOLO
responder and the cadence loop admit them through ``run_owner_draft`` with an
OWNER principal, and OWNER work reads the whole assignment chain
(capability, group, global).  So the global default alone makes the drafts
route ready, the lane chip names its model, and a routine question is
answered with a receipt.

Real producers: the real assignment service, the real route planner and
broker (``_configure``), the real responder; the engine factory is the one
physical-boundary fake.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.services.agent_responder import ANSWERED, CAPABILITY
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_agent_hand import db  # noqa: F401  (db is a fixture)
from tests.unit.test_conductor_k5_supervision import (  # noqa: F401  (launched is a fixture)
    KEY,
    ROUTINE_REPLY,
    _ask,
    _Engine,
    _members,
    _responder,
    launched,
)
from tests.unit.test_phase143_inference_assignments import OWNER, _profile


def _assign_global(db: Database, profile_id: str) -> None:
    """The Default for AI work: one global assignment, nothing exact."""
    _profile(db, profile_id)
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": f"global-{profile_id}", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


def _drafts_row(db: Database) -> dict[str, Any]:
    summary = InferenceAssignmentService(db).assignment_summary(OWNER)
    [row] = [r for r in summary["task_overrides"] if r["id"] == CAPABILITY]
    return row


def test_the_default_alone_makes_the_drafts_route_ready(tmp_path: Path) -> None:
    db = Database(tmp_path / "default-only.db")
    _assign_global(db, "default-model")
    row = _drafts_row(db)
    # No exact assignment: the drafts route reads the default.
    assert row["has_override"] is False
    effective = row["effective"]
    assert effective["status"] == "assigned" and effective["inherited_from"] == "global"
    # The lane chip reads this entry (web/src/desk/lane/LaneWindow.tsx readDraftEntry).
    assert effective["assignment"]["entries"][0]["profile_id"] == "default-model"


def test_no_default_and_no_assignment_is_no_assignment(tmp_path: Path) -> None:
    db = Database(tmp_path / "none.db")
    effective = _drafts_row(db)["effective"]
    assert effective["status"] == "no_assignment" and effective["assignment"] is None


def test_yolo_answers_a_routine_question_on_the_default_alone(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    from tests.unit.test_one_path_spine import _ready_this_machine

    _ready_this_machine(tmp_path, monkeypatch)
    _assign_global(launched.db, "default-model")
    broker = _configure(launched.db)
    engine = _Engine(ROUTINE_REPLY)
    broker.inference_runner._engine_factory = lambda _revision, **_: engine

    _ask(launched, tmp_path, monkeypatch, "Shall I run the tests before I open the pull request?")
    responder = _responder(launched, tmp_path, "yolo")
    typed_before = len(launched.typed)
    assert responder.triage([KEY]) == {"notify": [], "decide": [KEY]}

    result = responder.decide(KEY)

    assert result["outcome"] == ANSWERED, result
    assert launched.typed[typed_before:][-1][1] == "Yes. Run the tests, then open the pull request."
    assert engine.prompts, "the default's engine drafted nothing"
    assert _members(launched, tmp_path) == [] and launched.notified == []
    # The receipt: the answer is in the session's steering record.
    rows = launched.db.steering.list(session_key=KEY, limit=10)
    [row] = [r for r in rows if r.outcome == "auto_answered"]
    assert row.detail == "YOLO: routine: The brief says to run the tests first."
