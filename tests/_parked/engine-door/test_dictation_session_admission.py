# PARKED 2026-11-09 (door/speech-capture): the session freezes no plan legs: each stage names the door job it asks (SpeechSessionPlan.job), and the door picks the engine at the call.
# Moved from tests/unit/test_dictation_session_admission.py; its helpers are still there.

from tests.unit.test_dictation_session_admission import *  # noqa: F401,F403


def test_the_plan_freezes_ordered_per_capability_revisions(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    config = Config()
    # Pipeline explicitly OFF (HS-139-02 flipped the default to True): no
    # provider-backed stage is planned, so a stage dispatch would refuse by
    # name instead of silently reaching a model.
    config.dictation.pipeline.enabled = False
    plain = admit_hold_session(config_snapshot=config).plan
    assert set(plain.capabilities) == {CAPABILITY_WHISPER_TRANSCRIBE, CAPABILITY_WHISPER_PRELOAD}

    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router", "project-rewriter"]
    staged = admit_hold_session(config_snapshot=config).plan
    assert {"intent-classify", "rewrite"} <= set(staged.capabilities)
    # punctuate is NOT planned: today's punctuation pass is lexical, not a model.
    assert "punctuate" not in staged.capabilities
    for name, revisions in staged.capabilities.items():
        assert revisions and all(str(item).startswith("dep_") for item in revisions)
    # Whisper is its own deployment, never the dictation-LLM leg.
    assert staged.primary(CAPABILITY_WHISPER_TRANSCRIBE) == _whisper_revision(db, config)
    assert staged.primary("intent-classify") != staged.primary(CAPABILITY_WHISPER_TRANSCRIBE)
    # The plan summary the parent carries is content-free.
    assert "insertion_context_sha256" in staged.summary()
    assert staged.config_revision != plain.config_revision


# PARKED 2026-11-09 (door/speech-capture): speech no longer has a v1/routed split behind migration markers or route bundles: every session runs its stages through the engine door's chain (the markers, the bundle members and the frozen transcription entry are gone).

@pytest.mark.requires_local_dictation_route
def test_phase_d_couples_speech_and_writing_markers_for_one_complete_pipeline(
    tmp_path, monkeypatch
):
    """R4: partial migration stays v1; both markers produce one all-routed parent."""
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.speech_session import admit_one_shot_session
    from holdspeak.speech_session.plan import pipeline_provider_capabilities

    def configured_rewrite(session: Any) -> str:
        runtime = _PipelineBackend()
        # The test backend is the physical provider boundary. Legacy resolution
        # freezes the configured 127.0.0.1 profile; the migrated assignment
        # freezes the production on-device profile created by ``_build_host``.
        if session._route_bundle is None:
            runtime.base_url = "http://127.0.0.1:1234/v1"
            runtime.model = "qwen-local"
        else:
            runtime.backend = "local"
            runtime.model = ""
        return session.provider().rewrite(runtime, "rewrite this", max_tokens=32, temperature=0.0)

    # Startup's real speech migration with no writing marker remains wholly
    # legacy. ``legacy=None`` retains that production startup state unchanged.
    db, _broker, host, _unused = _build_host(tmp_path, monkeypatch, legacy=None)
    db.profiles.upsert(
        profile_id="phase-d-legacy-pipeline",
        name="Phase D legacy pipeline",
        kind="openAICompatible",
        base_url="http://127.0.0.1:1234/v1",
        model="qwen-local",
    )
    host.config.dictation.pipeline.enabled = True
    host.config.dictation.pipeline.stages = ["project-rewriter"]
    host.config.dictation.runtime.profile_id = "phase-d-legacy-pipeline"
    assert InferenceAssignmentService(db).migration_marker(
        hold_gesture_principal(), family="thoughts-writing-route-assignments"
    ) is None
    assert pipeline_provider_capabilities(host.config) == ("rewrite",)
    legacy = admit_one_shot_session(
        principal=hold_gesture_principal(), config_snapshot=host.config
    )
    assert legacy._route_bundle is None
    assert legacy.plan.has("rewrite"), legacy.plan.summary()
    assert _transcriber(FakeImpl()).transcribe(
        np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=legacy.transcription()
    ) == TEXT_SENTINEL
    assert configured_rewrite(legacy) == "REWRITTEN"
    legacy_children = _operations(db, name="inference.invoke")
    assert len(legacy_children) == 2
    assert {row["parent_operation_id"] for row in legacy_children} == {legacy.operation_id}
    legacy.close("succeeded")

    # The same normal pipeline after both production migrations freezes all of
    # its configured routes in one parent bundle and never emits a plain child.
    # The retained v1 resolver is forbidden here: if it ran, this production
    # object probe would fail before a bundle could be admitted.
    from holdspeak.speech_session.plan import DictationSessionPlanResolver

    def legacy_resolver_called(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("fully routed speech invoked the legacy resolver")

    monkeypatch.setattr(DictationSessionPlanResolver, "resolve", legacy_resolver_called)
    routed_tmp = tmp_path / "routed"
    routed_tmp.mkdir()
    db, _broker, host, _unused = _build_host(routed_tmp, monkeypatch, legacy=False)
    host.config.dictation.pipeline.enabled = True
    host.config.dictation.pipeline.stages = ["project-rewriter"]
    routed = admit_one_shot_session(
        principal=hold_gesture_principal(), config_snapshot=host.config
    )
    assert routed._route_bundle is not None
    # This carrier remains only for entry validation/history.  It contains no
    # legacy deployment choice; every executable member is the atomic bundle.
    assert routed.plan.capabilities == {}
    assert "punctuate" not in routed.plan.capabilities
    assert _transcriber(FakeImpl()).transcribe(
        np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=routed.transcription()
    ) == TEXT_SENTINEL

    class RoutedEngine:
        active_provider = "fixture"
        active_model = "phase-d-coupled-profile"

        @staticmethod
        def run_prompt(**_kwargs: Any) -> str:
            return "REWRITTEN"

    # Only the physical configured-model edge is bounded. The production route
    # admission, controller, bundle, attempt, and receipt still execute intact.
    _broker.inference_runner._engine_factory = lambda _revision, **_kwargs: RoutedEngine()
    assert configured_rewrite(routed) == "REWRITTEN"
    members = [item["capability_id"] for item in routed._route_bundle["members"]]
    assert members == ["speech.transcribe", "speech.rewrite", "speech.preload"]
    routed_children = _operations(db, name="inference.invoke")
    assert len(routed_children) == 2
    # The rewrite is one job through the engine door; the speech child is the
    # route bundle's.
    door = [row for row in routed_children if str(row["native_id"]).startswith("door_" + "speech.rewrite".encode().hex())]
    assert len(door) == 1
    with db._connection() as conn:
        routed_child_ids = {row["operation_id"] for row in routed_children} - {door[0]["operation_id"]}
        route_child_ids = {
            row["child_operation_id"]
            for row in conn.execute(
                "SELECT child_operation_id FROM inference_route_attempts "
                "WHERE child_operation_id IS NOT NULL"
            )
        }
    assert routed_child_ids == route_child_ids
    routed.close("succeeded")


@pytest.mark.requires_local_dictation_route
def test_phase_d_egress_refuses_a_missing_frozen_transcription_entry(
    tmp_path, monkeypatch
):
    """A broken bundle cannot relabel an unknown transcription route ``local``."""
    from holdspeak.speech_session import admit_one_shot_session
    from holdspeak.speech_session.provider import ROUTED_EGRESS_ROUTE_MISSING

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    session = admit_one_shot_session(
        principal=_browser_principal(), config_snapshot=host.config
    )
    assert session._route_bundle is not None
    route_id = next(
        str(item["route_plan_id"])
        for item in session._route_bundle["members"]
        if item["capability_id"] == "speech.transcribe"
    )
    with db._connection() as conn:
        conn.execute("DELETE FROM inference_route_plan_entries WHERE plan_id=?", (route_id,))
        conn.commit()

    with pytest.raises(SpeechSessionRefused) as excinfo:
        _ = session.provider().egress_boundary
    assert excinfo.value.reason == ROUTED_EGRESS_ROUTE_MISSING
    session.close("succeeded")
