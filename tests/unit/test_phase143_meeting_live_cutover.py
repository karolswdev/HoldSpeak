"""Phase 143 Story 08 migration-cutover proofs."""

from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
from typing import Any

from holdspeak.db import Database
from holdspeak.intel import ActionItem, IntelResult
from holdspeak.meeting_session.models import Bookmark, TranscriptSegment
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


class _LiveEngine:
    active_provider = "fixture"
    active_model = "meeting-profile"

    def __init__(self) -> None:
        self.analysis_calls = 0
        self.labels = 0
        self.titles = 0

    def analyze(self, _transcript: str, *, stream: bool = False) -> Any:
        self.analysis_calls += 1
        assert stream is False  # Phase-B buffers; no primary token channel.
        return IntelResult(
            topics=["Budget"],
            action_items=[ActionItem(task="Send deck", owner="Me")],
            summary="Budget review.",
            raw_response="private",
        )

    def generate_bookmark_label_with_context(self, **_kwargs: Any) -> str:
        self.labels += 1
        return "Budget decision"

    def generate_title(self, _transcript: str) -> str:
        self.titles += 1
        return "Budget review"


def test_live_bundle_routes_analysis_label_and_title_after_receipt_election(
    tmp_path: Path, monkeypatch
) -> None:
    """One elected validated result reaches each Meeting surface, never tokens."""
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    engine = _LiveEngine()
    broadcasts: list[tuple[str, Any]] = []
    session.on_broadcast = lambda kind, value: broadcasts.append((kind, value))
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)

    session.start()
    session._state.segments.append(
        TranscriptSegment(text="Discussed the budget", speaker="Me", start_time=0.0, end_time=5.0)
    )
    session._run_intel_analysis(final=True)
    session._state.bookmarks.append(Bookmark(timestamp=2.0, label="Bookmark @ 00:02"))
    session._refine_bookmark_labels("Budget review.")
    _outcome, title, _result = session._admitted_auto_title("Discussed the budget")

    assert session._state.intel is not None
    assert session._state.intel.summary == "Budget review."
    assert session._state.bookmarks[0].label == "Budget decision"
    assert title == {"title": "Budget review"}
    assert (engine.analysis_calls, engine.labels, engine.titles) == (1, 1, 1)
    assert not [event for event in broadcasts if event[0] == "intel_token"]
    with db._connection() as conn:
        executions = conn.execute(
            "SELECT terminal_outcome FROM inference_route_executions ORDER BY started_at"
        ).fetchall()
    assert [row["terminal_outcome"] for row in executions] == ["succeeded"] * 3


def test_replaying_identical_live_material_reuses_the_elected_execution(
    tmp_path: Path, monkeypatch
) -> None:
    """Deterministic operation/command identities prevent repeat model egress."""
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    engine = _LiveEngine()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    session.start()
    monkeypatch.setattr(type(session), "duration", property(lambda _self: 5.0))
    session._state.segments.append(
        TranscriptSegment(text="Repeat this exact window", speaker="Me", start_time=0.0, end_time=5.0)
    )

    session._run_intel_analysis()
    session._run_intel_analysis()
    first = session._admitted_auto_title("Repeat this exact window")
    second = session._admitted_auto_title("Repeat this exact window")

    assert engine.analysis_calls == 1
    assert engine.titles == 1
    assert first[1] == second[1] == {"title": "Budget review"}
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == 2


def test_assignment_edit_after_meeting_bundle_freeze_does_not_retarget_route(
    tmp_path: Path, monkeypatch
) -> None:
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    session.start()
    member = next(
        item for item in session._route_bundle["members"]
        if item["capability_id"] == "meeting.live_analysis"
    )
    before = broker.inference_adoption_service.plans.get_route_plan(
        OWNER, member["route_plan_id"]
    )
    _profile(
        db,
        "meeting-fallback-profile",
        claims=("language", "structured_output", _result_claim("meeting.live_analysis")),
    )
    assignment = InferenceAssignmentService(db).resolve_effective(
        OWNER, capability_id="meeting.live_analysis"
    )
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "edit-meeting-after-freeze",
            "expected_revision": assignment["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "meeting.live_analysis"},
            "entries": [{"profile_id": "meeting-fallback-profile", "profile_revision": 1}],
        },
    )
    after = broker.inference_adoption_service.plans.get_route_plan(
        OWNER, member["route_plan_id"]
    )
    assert after["sha256"] == before["sha256"]
    assert [entry["deployment_revision_id"] for entry in after["entries"]] == [
        entry["deployment_revision_id"] for entry in before["entries"]
    ]


def test_live_analysis_controller_owns_compatibility_retry_then_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    """Meeting routing records 1/1, 1/2, then 2/3 before one UI publication."""
    from holdspeak.kernel.provider_signals import (
        ProviderCompatibilityRetry,
        ProviderPermanentNoGeneration,
    )
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    _profile(
        db,
        "meeting-fallback-profile",
        claims=("language", "structured_output", _result_claim("meeting.live_analysis")),
    )
    assignments = InferenceAssignmentService(db)
    current = assignments.resolve_effective(OWNER, capability_id="meeting.live_analysis")
    assignments.set_assignment(
        OWNER,
        {
            "command_id": "two-entry-live-analysis",
            "expected_revision": current["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "meeting.live_analysis"},
            "entries": [
                {"profile_id": "meeting-profile", "profile_revision": 1},
                {"profile_id": "meeting-fallback-profile", "profile_revision": 1},
            ],
        },
    )

    class _ScriptedEngine:
        active_provider = "fixture"
        active_model = "scripted"

        def __init__(self) -> None:
            self.calls = 0

        def analyze(self, _transcript: str, *, stream: bool = False) -> IntelResult:
            assert stream is False
            self.calls += 1
            if self.calls == 1:
                raise ProviderCompatibilityRetry("json_mode", detail="PRIMARY_LOSER_TEXT")
            if self.calls == 2:
                raise ProviderPermanentNoGeneration()
            assert self.calls == 3
            return IntelResult(
                topics=["Elected topic"],
                action_items=[ActionItem(task="Elected action")],
                summary="ELECTED_WINNER",
                raw_response="private",
            )

    engine = _ScriptedEngine()
    received: list[str] = []
    session.on_intel = lambda snapshot: received.append(snapshot.summary)
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)

    session.start()
    session._state.segments.append(
        TranscriptSegment(text="Controller retry material", speaker="Me", start_time=0.0, end_time=5.0)
    )
    session._run_intel_analysis()

    assert engine.calls == 3
    assert received == ["ELECTED_WINNER"]
    assert "PRIMARY_LOSER_TEXT" not in received
    with db._connection() as conn:
        execution = conn.execute(
            "SELECT id,winning_attempt_id,terminal_outcome FROM inference_route_executions"
        ).fetchone()
        attempts = conn.execute(
            """SELECT id,route_leg_ordinal,physical_attempt_ordinal,leg_attempt_ordinal,
                      purpose,disposition
                 FROM inference_route_attempts WHERE execution_id=?
                 ORDER BY physical_attempt_ordinal""",
            (execution["id"],),
        ).fetchall()
    assert [(row["route_leg_ordinal"], row["physical_attempt_ordinal"], row["leg_attempt_ordinal"], row["purpose"])
            for row in attempts] == [
        (1, 1, 1, "primary"),
        (1, 2, 2, "compatibility"),
        (2, 3, 1, "fallback"),
    ]
    assert [row["disposition"] for row in attempts] == [
        "known_no_generation_transient",
        "provider_permanent",
        "owner_terminal",
    ]
    assert execution["terminal_outcome"] == "succeeded"
    assert execution["winning_attempt_id"] == attempts[2]["id"]
