"""HS-143-10 Slice 3 — voice resolution uses the canonical controller route."""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.workbench_service import WorkbenchService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

OWNER = Principal(PrincipalKind.OWNER, "owner")


class _VoiceEngine:
    def __init__(self) -> None:
        self.calls = 0

    def run_prompt(self, **_kwargs: object) -> str:
        self.calls += 1
        return '{"zone_ids":["zone-focus"]}'


def test_voice_resolution_has_one_controller_receipt_for_its_real_attempt(tmp_path: Path) -> None:
    db = Database(tmp_path / "voice-route.db")
    broker = _configure(db)
    _profile(db, "voice-model", claims=("language", _result_claim("voice.reference_resolve")))
    recipe = db.recipes.upsert(recipe_id="voice-recipe", name="Voice")
    workbench = db.workbenches.upsert(workbench_id="voice-workbench", name="Voice", recipe_id=recipe.id)
    db.directories.upsert(directory_id="zone-focus", name="Focus")
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "voice-route", "expected_revision": 0,
        "scope": {"kind": "subject", "subject_kind": "workbench", "subject_id": workbench.id, "capability_id": "voice.reference_resolve"},
        "entries": [{"profile_id": "voice-model", "profile_revision": 1}],
    })
    engine = _VoiceEngine()
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine

    result = WorkbenchService(db).resolve_voice(OWNER, workbench.id, "focus please", "voice-request")

    assert result["refs"] == [{"name": "Focus", "id": "zone-focus", "ref": "zone:zone-focus", "kind": "zone"}]
    assert result["attempts"] == 1 and engine.calls == 1
    receipt = result["route_execution_receipt"]
    assert receipt["outcome"] == "succeeded" and len(receipt["attempts"]) == 1
    with db._connection() as conn:
        parent = conn.execute("SELECT operation_id FROM kernel_parent_runs WHERE kind='voice_reference_resolve'").fetchone()
        attempt = conn.execute("SELECT child_receipt_sha256 FROM inference_route_attempts").fetchone()
    assert parent is not None and attempt["child_receipt_sha256"]
