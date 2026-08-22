"""Phase 143 Story 08 migration-cutover proofs."""

from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_adoption_service import (
    MEETING_MIGRATION_FAMILY,
    SPEECH_RECOGNITION_MIGRATION_FAMILY,
    RoutedInferenceCoordinator,
)
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


OWNER = Principal(PrincipalKind.OWNER, "meeting-migration-owner")


def _meeting_config(profile_id: str, *, provider: str = "local") -> SimpleNamespace:
    return SimpleNamespace(
        meeting=SimpleNamespace(
            intel_profile_id=profile_id,
            intel_provider=provider,
        ),
        model=SimpleNamespace(name="base", backend="auto", language="auto"),
    )


def test_meeting_assignment_migration_copies_exact_saved_profile_and_replays(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "meeting-migration.db")
    capabilities = (
        "meeting.live_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
    )
    _profile(
        db,
        "saved-meeting-profile",
        claims=("language", *(_result_claim(capability) for capability in capabilities)),
    )
    service = RoutedInferenceCoordinator(db)

    migrated = service.migrate_meeting_route_assignments(
        OWNER, _meeting_config("saved-meeting-profile")
    )

    assert migrated["family"] == MEETING_MIGRATION_FAMILY
    assert migrated["status"] == "migrated"
    assert migrated["legacy_config_read"] is True
    assert len(migrated["assignments"]) == len(capabilities)
    assignments = InferenceAssignmentService(db)
    for capability in capabilities:
        resolved = assignments.get_assignment(
            OWNER, {"kind": "capability", "capability_id": capability}
        )
        assert [
            (entry["ordinal"], entry["profile_id"], entry["profile_revision"])
            for entry in resolved["entries"]
        ] == [(1, "saved-meeting-profile", 1)]
    assert assignments.migration_marker(OWNER, family=MEETING_MIGRATION_FAMILY)

    replay = service.migrate_meeting_route_assignments(OWNER, object())
    assert replay["status"] == "migrated"
    assert replay["legacy_config_read"] is False


def test_blank_or_cloud_legacy_meeting_values_never_guess_an_assignment(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-migration-refusal.db")
    service = RoutedInferenceCoordinator(db)

    issue = service.migrate_meeting_route_assignments(
        OWNER, _meeting_config("", provider="cloud")
    )

    assert issue == {
        "schema": "InferenceAssignmentMigrationIssue@1",
        "family": MEETING_MIGRATION_FAMILY,
        "status": "needs_attention",
        "reason_code": "builtin_profile_required",
        "repair": "choose_meeting_model_profile",
        "source_sha256": issue["source_sha256"],
    }
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_assignment_heads").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_migrations WHERE family=?",
            (MEETING_MIGRATION_FAMILY,),
        ).fetchone()[0] == 0


def test_speech_recognition_without_a_saved_profile_refuses_without_preload_assignment(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "speech-migration-refusal.db")
    service = RoutedInferenceCoordinator(db)

    issue = service.migrate_speech_recognition_route_assignments(
        OWNER, _meeting_config("saved-meeting-profile")
    )

    assert issue["schema"] == "InferenceAssignmentMigrationIssue@1"
    assert issue["family"] == SPEECH_RECOGNITION_MIGRATION_FAMILY
    assert issue["reason_code"] == "builtin_profile_required"
    assert issue["repair"] == "choose_audio_model_profile"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_assignment_heads").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_migrations WHERE family=?",
            (SPEECH_RECOGNITION_MIGRATION_FAMILY,),
        ).fetchone()[0] == 0
