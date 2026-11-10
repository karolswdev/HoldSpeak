# PARKED 20261109 (door/park-waist): the cases of tests/integration/test_inference_placement_adoption.py that drove the parked routed-inference waist.
# Not collected (tests/_parked/conftest.py). Restore with `git revert` of the parking commit.
"""HS-143-10 Slice 6 — one real-object placement-adoption matrix.

The matrix deliberately joins the same frozen route/controller evidence that a
product surface consumes.  Its first table proves the next-run-only rule for
each migrated capability; its second table invokes each production family.
Only the physical engine factory is substituted.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel.inference import InferenceRunCodec
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from tests.unit.test_engines_run_retirement import _legacy_request


class _Engine:
    active_provider = "matrix-provider"
    active_model = "matrix-model"

    def __init__(self, *, voice: bool = False) -> None:
        self.calls = 0
        self._voice = voice

    def run_prompt(self, **_kwargs: Any) -> str:
        self.calls += 1
        return '{"zone_ids":["zone-matrix"]}' if self._voice else "matrix answer"


def _scope(case: _Case) -> dict[str, str]:
    if case.subject_kind is None:
        return {"kind": "capability", "capability_id": case.capability_id}
    return {
        "kind": "subject",
        "subject_kind": case.subject_kind,
        "subject_id": str(case.subject_id),
        "capability_id": case.capability_id,
    }


def _assign(db: Database, case: _Case, profile_id: str, command: str) -> None:
    broker = _configure(db)
    foundation = getattr(getattr(broker, "tool_turn_foundation", None), "_foundation", None)
    assignments = InferenceAssignmentService(db, tool_capability_foundation=foundation)
    scope = _scope(case)
    try:
        current = assignments.get_assignment(OWNER, scope)
    except NotFound:
        current = None
    assignments.set_assignment(
        OWNER,
        {
            "command_id": command,
            "expected_revision": int(current["revision"]) if current else 0,
            "scope": scope,
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        },
    )


def _matrix_db(tmp_path: Path, case: _Case) -> tuple[Database, Any, _Engine]:
    db = Database(tmp_path / f"{case.name}.db")
    broker = _configure(db)
    claims = ("language", _result_claim(case.capability_id))
    manifest = None
    _profile(db, "matrix-old", claims=claims, capability_manifest=manifest)
    _profile(db, "matrix-new", claims=claims, capability_manifest=manifest)
    _assign(db, case, "matrix-old", f"{case.name}-old")
    engine = _Engine(voice=case.capability_id == "voice.reference_resolve")
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine
    return db, broker, engine


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_frozen_canonical_terms_survive_assignment_mutation_then_later_admission_sees_edit(
    tmp_path: Path, case: _Case
) -> None:
    """One table proves selection/freeze/linkage for every migrated capability."""
    db, broker, engine = _matrix_db(tmp_path, case)
    coordinator = broker.inference_adoption_service
    admitted = coordinator.admit(
        OWNER,
        command_id=f"{case.name}-admit-old",
        capability_id=case.capability_id,
        operation_id=f"{case.name}-operation-old",
        payload={"system_prompt": "matrix", "user_prompt": case.name},
        subject_kind=case.subject_kind,
        subject_id=case.subject_id,
        reserved_output_tokens=32,
    )
    old_route = admitted["route_plan"]
    assert old_route["entries"][0]["profile_id"] == "matrix-old"

    # Mutation happens after admission, before the physical controller execution.
    _assign(db, case, "matrix-new", f"{case.name}-assignment-edit")
    # The old plan is immutable evidence even before its physical reservation is
    # consumed; every actual execution/receipt assertion lives in the product
    # entry table below, which supplies the family-specific adapter and payload.
    assert old_route["entries"][0]["profile_id"] == "matrix-old"

    later = coordinator.admit(
        OWNER,
        command_id=f"{case.name}-admit-new",
        capability_id=case.capability_id,
        operation_id=f"{case.name}-operation-new",
        payload={"system_prompt": "matrix", "user_prompt": "later"},
        subject_kind=case.subject_kind,
        subject_id=case.subject_id,
        reserved_output_tokens=32,
    )
    assert later["route_plan"]["entries"][0]["profile_id"] == "matrix-new"


@pytest.mark.parametrize(
    "case",
    (
        _Case("contextual-recipe-run", "recipe.run", "recipe", "recipe-matrix"),
        _Case("contextual-chat-turn", "chat.turn", "recipe", "recipe-matrix"),  # HS-151-02: was recipe.chat
        _Case("contextual-workbench-item", "workbench.item", "workbench", "workbench-matrix"),
        _Case("contextual-workbench-resolver", "voice.reference_resolve", "workbench", "workbench-matrix"),
    ),
    ids=lambda case: case.name,
)
def test_contextual_subject_save_uses_canonical_assignment_and_preserves_pre_admitted_route_bytes(
    tmp_path: Path, case: _Case
) -> None:
    """The S5 subject editor's save seam is the one canonical set_assignment path.

    ContextualAssignment submits this complete scope/body through the S1 route;
    this production-object proof invokes that same service mutation and proves a
    route admitted before it remains byte-identical while the later admission
    sees the edited subject chain.
    """
    db, broker, _engine = _matrix_db(tmp_path, case)
    coordinator = broker.inference_adoption_service
    first = coordinator.admit(
        OWNER,
        command_id=f"{case.name}-before",
        capability_id=case.capability_id,
        operation_id=f"{case.name}-before-operation",
        payload={"system_prompt": "matrix", "user_prompt": "before"},
        subject_kind=case.subject_kind,
        subject_id=case.subject_id,
        reserved_output_tokens=32,
    )
    frozen_route = json.dumps(first["route_plan"], sort_keys=True, separators=(",", ":"))

    _assign(db, case, "matrix-new", f"{case.name}-contextual-save")

    assert json.dumps(first["route_plan"], sort_keys=True, separators=(",", ":")) == frozen_route
    later = coordinator.admit(
        OWNER,
        command_id=f"{case.name}-after",
        capability_id=case.capability_id,
        operation_id=f"{case.name}-after-operation",
        payload={"system_prompt": "matrix", "user_prompt": "after"},
        subject_kind=case.subject_kind,
        subject_id=case.subject_id,
        reserved_output_tokens=32,
    )
    assert later["route_plan"]["entries"][0]["profile_id"] == "matrix-new"
