"""HS-151-07: speech head pre-check at meeting bundle admission.

Pin tests for the six counsel-ruled pins (P1-P6):
P1 owner WITH speech head -> bundle includes transcription (4 routes).
P2 owner WITHOUT speech head -> intel-only; record_only with
   reason_code=transcription_no_speech_assignment.
P3 SERVICE scheduled-recording principal WITH speech head + assignments -> WITH transcription.
P4 refusal-never-silent: the record_only status + detail persist on meeting state.
P5 no wake/deferred/dictation regression (focused suite proxies).
P6 intel routes unaffected: existing admission tests stay green.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, _set

pytestmark = pytest.mark.timeout(60, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "meeting-owner")

_BUNDLE_CAPABILITIES = (
    "meeting.live_analysis",
    "meeting.bookmark_label",
    "meeting.auto_title",
    "speech.transcribe",
)

_INTEL_ONLY_CAPABILITIES = (
    "meeting.live_analysis",
    "meeting.bookmark_label",
    "meeting.auto_title",
)


class FakeRecorder:
    def __init__(self, **kwargs: Any) -> None:
        self.started = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> tuple[list[Any], list[Any]]:
        return [], []

    def get_pending_chunks(self, since: float = 0.0) -> tuple[list[Any], list[Any]]:
        return [], []

    def get_pending_device_chunks(self) -> list[Any]:
        return []


class FakeJournal:
    def __init__(self, meeting_id: str) -> None:
        self.meeting_id = meeting_id

    def append(self, *args: Any, **kwargs: Any) -> None:
        return None

    def finalize(self) -> None:
        return None

    def mark_recoverable(self, reason: str) -> None:
        return None


def _assign_all_routes(db: Database) -> None:
    """Seed a coherent profile + assignments for ALL four meeting bundle capabilities."""
    _profile(
        db,
        "meeting-profile",
        claims=(
            "language",
            "structured_output",
            *(_result_claim(cap) for cap in _BUNDLE_CAPABILITIES),
        ),
        modalities=("language", "audio"),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(_BUNDLE_CAPABILITIES, 1):
        scope = {"kind": "capability", "capability_id": capability}
        try:
            expected = int(assignments.get_assignment(OWNER, scope)["revision"])
        except Exception:
            from holdspeak.services.errors import NotFound

            expected = 0
        _set(
            assignments,
            f"meeting-bundle-assignment-{ordinal}",
            scope,
            "meeting-profile",
            expected=expected,
        )


def _assign_intel_only_routes(db: Database) -> None:
    """Seed assignments for ONLY the three intel capabilities, NO speech.transcribe.

    The startup migration may create a speech.transcribe head on HOMEs where
    mlx_whisper is importable.  This fixture seeds the intel routes and then
    CLEARS the speech.transcribe head so the admission pre-check finds it absent.
    """
    _profile(
        db,
        "meeting-profile",
        claims=(
            "language",
            "structured_output",
            *(_result_claim(cap) for cap in _INTEL_ONLY_CAPABILITIES),
        ),
        modalities=("language",),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(_INTEL_ONLY_CAPABILITIES, 1):
        scope = {"kind": "capability", "capability_id": capability}
        try:
            expected = int(assignments.get_assignment(OWNER, scope)["revision"])
        except Exception:
            from holdspeak.services.errors import NotFound

            expected = 0
        _set(
            assignments,
            f"intel-only-assignment-{ordinal}",
            scope,
            "meeting-profile",
            expected=expected,
        )


def _clear_speech_head(db: Database) -> None:
    """Remove the speech.transcribe assignment head so admission finds it absent."""
    with db._connection() as conn:
        conn.execute(
            "DELETE FROM inference_assignment_heads WHERE assignment_key=?",
            ("capability:speech.transcribe",),
        )
        conn.commit()


def _build_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    assign_speech: bool = True,
    principal: Principal | None = None,
) -> tuple[Database, Any, Any]:
    db = Database(tmp_path / "admission.db")
    if assign_speech:
        _assign_all_routes(db)
    else:
        _assign_intel_only_routes(db)
    broker = _configure(db)
    if not assign_speech:
        # The startup migration may have created the speech head on this machine;
        # clear it AFTER _configure so the admission pre-check finds it absent.
        _clear_speech_head(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)

    class _Transcriber:
        model_name = "meeting-profile"

        def transcribe(self, *_args: Any, **_kwargs: Any) -> str:
            return ""

    from holdspeak.meeting_session import MeetingSession

    return db, broker, MeetingSession(
        _Transcriber(),  # type: ignore[arg-type]
        principal=principal or OWNER,
        intel_enabled=True,
    )


# ---------------------------------------------------------------- P1
def test_p1_owner_with_speech_head_admits_four_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Owner with a speech.transcribe assignment head gets all 4 routes + preload."""
    _db, _broker, session = _build_session(tmp_path, monkeypatch, assign_speech=True)

    state = session.start()

    bundle = session._route_bundle
    assert bundle is not None
    member_capabilities = frozenset(m["capability_id"] for m in bundle["members"])
    assert member_capabilities == frozenset({*_BUNDLE_CAPABILITIES, "speech.preload"})
    assert state.capture_status == "recording"
    # Transcription should NOT be record_only when speech head is present
    assert state.transcription_status != "record_only" or state.transcription_status is None


# ---------------------------------------------------------------- P2
def test_p2_owner_without_speech_head_admits_intel_only_record_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Owner WITHOUT a speech head gets 3 intel routes; transcription_status=record_only."""
    _db, _broker, session = _build_session(tmp_path, monkeypatch, assign_speech=False)

    state = session.start()

    bundle = session._route_bundle
    assert bundle is not None
    member_capabilities = frozenset(m["capability_id"] for m in bundle["members"])
    # Only the 3 intel capabilities, no speech.transcribe, no speech.preload
    assert member_capabilities == frozenset(_INTEL_ONLY_CAPABILITIES)
    assert len(bundle["members"]) == 3
    # Transcription should be record_only with the correct reason
    assert state.transcription_status == "record_only"
    detail = state.transcription_status_detail
    assert detail is not None
    assert detail["reason_code"] == "transcription_no_speech_assignment"
    assert detail["repair"] == "repair_audio_model_lifecycle"
    assert detail["family"] == "speech-recognition-route-assignments"
    # Raw capture still started
    assert state.capture_status == "recording"
    # Bundle should NOT have derived_preloads
    assert not bundle.get("derived_preloads")
    # Budget groups should only have meeting-intelligence (no transcription/preload)
    group_ids = {g["id"] for g in bundle.get("budget_groups", [])}
    assert "meeting-intelligence" in group_ids
    assert "meeting-transcription" not in group_ids
    assert "meeting-preload" not in group_ids


# ---------------------------------------------------------------- P3
def test_p3_service_principal_with_speech_head_admits_with_transcription(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The conductor-fired SERVICE session with speech head gets transcription."""
    service_principal = Principal(
        PrincipalKind.SERVICE,
        "scheduled-recording",
        frozenset({
            ("meeting.session", 1),
            ("inference.invoke", 1),
            ("inference.cancel", 1),
        }),
        "scheduled-recording:armed-schedule",
    )
    _db, _broker, session = _build_session(
        tmp_path, monkeypatch, assign_speech=True, principal=service_principal
    )

    state = session.start()

    bundle = session._route_bundle
    assert bundle is not None
    member_capabilities = frozenset(m["capability_id"] for m in bundle["members"])
    assert "speech.transcribe" in member_capabilities
    assert "speech.preload" in member_capabilities
    assert state.capture_status == "recording"


# ---------------------------------------------------------------- P4
def test_p4_record_only_status_and_detail_persist_on_meeting_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The record_only status + detail must persist on the durable meeting state."""
    db, _broker, session = _build_session(tmp_path, monkeypatch, assign_speech=False)

    state = session.start()

    assert state.transcription_status == "record_only"
    assert state.transcription_status_detail is not None
    assert state.transcription_status_detail["reason_code"] == "transcription_no_speech_assignment"
    # Verify it persists in the database
    durable = db.meetings.get_meeting(state.id)
    assert durable is not None
    assert durable.transcription_status == "record_only"
