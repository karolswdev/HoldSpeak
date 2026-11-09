# PARKED 2026-11-09 (door/thought-dictation-meeting): a live Meeting job runs through the engine door: no route-execution replay identity (a window runs only on new segments), and the door's one retry on the next engine follows a refusal.
# Moved from tests/unit/test_meetings_live_cutover.py; its helpers are still there.

from tests.unit.test_meetings_live_cutover import *  # noqa: F401,F403


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


def test_meeting_kernel_refusal_is_terminal_without_retry_or_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from holdspeak.kernel.model import KernelRefused
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    _profile(
        db,
        "meeting-refusal-fallback",
        claims=("language", "structured_output", _result_claim("meeting.live_analysis")),
    )
    assignment = InferenceAssignmentService(db).resolve_effective(
        OWNER, capability_id="meeting.live_analysis"
    )
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "meeting-refusal-fallback",
            "expected_revision": assignment["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "meeting.live_analysis"},
            "entries": [
                {"profile_id": "meeting-profile", "profile_revision": 1},
                {"profile_id": "meeting-refusal-fallback", "profile_revision": 1},
            ],
        },
    )

    class RefusingEngine:
        active_provider = "fixture"
        active_model = "refusing"

        @staticmethod
        def analyze(_transcript: str, *, stream: bool = False) -> IntelResult:
            assert stream is False
            raise KernelRefused("meeting_provider_refused")

    engine = RefusingEngine()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    session.start()
    session._state.segments.append(
        TranscriptSegment(text="Refused work", speaker="Me", start_time=0.0, end_time=1.0)
    )
    session._run_intel_analysis()

    # A refusal is the job's answer: no retry on the next engine.
    runs = _door_runs(db, "meeting.live_analysis")
    assert len(runs) == 1 and runs[0][0] == "" and runs[0][1] != "succeeded", runs
