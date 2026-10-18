"""Betterment E5: what a job runs on when it has no row of its own.

FOLLOWUPS ST0: speech never takes the default (a chat engine). FOLLOWUPS C4:
a meeting plugin follows the meeting summary's row. The real assignment
service over a real database; no engine runs.
"""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.inference_capabilities import installed_meeting_plugin_capability_definitions
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim


def _set(service: InferenceAssignmentService, scope: dict, profile_id: str) -> None:
    service.set_assignment(OWNER, {
        "command_id": f"set-{profile_id}-{scope['kind']}", "expected_revision": 0, "scope": scope,
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


def test_speech_has_no_engine_when_only_everything_else_is_set(tmp_path: Path) -> None:
    db = Database(tmp_path / "what.db")
    _profile(db, "chat-engine")
    service = InferenceAssignmentService(db)
    _set(service, {"kind": "global"}, "chat-engine")
    assert service.resolve_effective(OWNER, capability_id="speech.transcribe")["status"] == "no_assignment"
    # A text job still follows Everything else.
    answers = service.resolve_effective(OWNER, capability_id="ask.answer")
    assert answers["inherited_from"] == "global"


def test_a_meeting_plugin_follows_the_summary_row(tmp_path: Path) -> None:
    db = Database(tmp_path / "what.db")
    _profile(db, "summary-engine", claims=("language", _result_claim("meeting.deferred_analysis")))
    service = InferenceAssignmentService(db)
    _set(service, {"kind": "capability", "capability_id": "meeting.deferred_analysis"}, "summary-engine")
    plugin = installed_meeting_plugin_capability_definitions()[0].id
    effective = service.resolve_effective(OWNER, capability_id=plugin)
    assert effective["status"] != "no_assignment", effective
    assert effective["inherited_from"] == "capability"
    assert effective["assignment"]["entries"][0]["profile_id"] == "summary-engine"
