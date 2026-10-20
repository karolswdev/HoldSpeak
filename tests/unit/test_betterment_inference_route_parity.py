"""Betterment ST0/C4: face assignment and frozen route lookup stay in parity."""

from __future__ import annotations

import pytest

from holdspeak.db import Database
from holdspeak.inference_capabilities import (
    installed_meeting_plugin_capability_definitions,
)
from holdspeak.services.errors import ValidationError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_route_plan_service import (
    InferenceRoutePlanService,
    ROUTE_PLANNING_AUTHORITY,
)
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim


def _set(
    service: InferenceAssignmentService,
    scope: dict[str, str],
    profile_id: str,
    command_id: str,
) -> dict[str, object]:
    return service.set_assignment(
        OWNER,
        {
            "command_id": command_id,
            "expected_revision": 0,
            "scope": scope,
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        },
    )


def test_route_freezer_preserves_speech_no_global_fallback(tmp_path) -> None:
    db = Database(tmp_path / "speech-global.db")
    assignments = InferenceAssignmentService(db)
    _profile(db, "chat-engine")
    _set(assignments, {"kind": "global"}, "chat-engine", "speech-global")

    effective = assignments.resolve_effective(OWNER, capability_id="speech.transcribe")
    assert effective["status"] == "no_assignment"

    with pytest.raises(ValidationError) as refused:
        InferenceRoutePlanService(db).freeze_route_plan(
            ROUTE_PLANNING_AUTHORITY,
            command_id="freeze-speech-global",
            capability_id="speech.transcribe",
        )
    assert refused.value.code == "no_assignment"


@pytest.mark.parametrize(
    "scope",
    (
        {"kind": "capability", "capability_id": "speech.transcribe"},
        {"kind": "group", "group_id": "speech_recognition"},
    ),
    ids=("capability", "group"),
)
def test_frozen_speech_route_uses_explicit_face_assignment(
    tmp_path, scope: dict[str, str]
) -> None:
    db = Database(tmp_path / f"speech-{scope['kind']}.db")
    assignments = InferenceAssignmentService(db)
    _profile(db, "chat-engine")
    _profile(
        db,
        "speech-engine",
        claims=("audio", _result_claim("speech.transcribe")),
        modalities=("audio",),
    )
    _set(assignments, {"kind": "global"}, "chat-engine", f"speech-{scope['kind']}-global")
    _set(assignments, scope, "speech-engine", f"speech-{scope['kind']}-explicit")

    effective = assignments.resolve_effective(OWNER, capability_id="speech.transcribe")
    frozen = InferenceRoutePlanService(db).freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id=f"freeze-speech-{scope['kind']}",
        capability_id="speech.transcribe",
    )

    assert effective["status"] == "assigned"
    assert effective["inherited_from"] == scope["kind"]
    assert effective["assignment"]["entries"][0]["profile_id"] == "speech-engine"
    assert frozen["source"]["inherited_from"] == scope["kind"]
    assert frozen["source"]["assignment_id"] == effective["assignment"]["id"]
    assert [entry["profile_id"] for entry in frozen["entries"]] == ["speech-engine"]


def test_frozen_installed_plugin_route_follows_summary_before_group_and_global(
    tmp_path,
) -> None:
    db = Database(tmp_path / "plugin-summary.db")
    assignments = InferenceAssignmentService(db)
    plugin = installed_meeting_plugin_capability_definitions()[0].id
    plugin_claim = _result_claim(plugin)
    summary_claim = _result_claim("meeting.deferred_analysis")

    _profile(
        db,
        "summary-engine",
        claims=("language", summary_claim, plugin_claim, "meeting_plugin"),
    )
    _profile(
        db,
        "group-engine",
        claims=("language", plugin_claim, "meeting_plugin"),
    )
    _profile(
        db,
        "global-engine",
        claims=("language", plugin_claim, "meeting_plugin"),
    )
    _set(assignments, {"kind": "global"}, "global-engine", "plugin-global")
    _set(
        assignments,
        {"kind": "group", "group_id": "meetings"},
        "group-engine",
        "plugin-group",
    )
    _set(
        assignments,
        {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
        "summary-engine",
        "plugin-summary",
    )

    effective = assignments.resolve_effective(OWNER, capability_id=plugin)
    frozen = InferenceRoutePlanService(db).freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-installed-plugin",
        capability_id=plugin,
    )

    assert effective["status"] == "assigned"
    assert effective["inherited_from"] == "capability"
    assert effective["assignment"]["entries"][0]["profile_id"] == "summary-engine"
    assert frozen["source"]["inherited_from"] == "capability"
    assert frozen["source"]["assignment_id"] == effective["assignment"]["id"]
    assert [entry["profile_id"] for entry in frozen["entries"]] == ["summary-engine"]
