# PARKED 2026-11-09 (door/speech-capture): the stage runs on the engine the door's chain names at the call, through the runner's engine (provider._DoorSpeechAdapter): the frozen-revision target binding (ProviderAdmission.target/prepared/dispatch_through, _dispatch_target, the runtime's own classify response_format leg) is gone, and a chain change is now honoured on the next call (owner, 2026-11-09).
# Moved from tests/unit/test_dictation_pipeline_admission.py; its helpers are still there.

from tests.unit.test_dictation_pipeline_admission import *  # noqa: F401,F403


class _RejectingCompletions:
    """An endpoint that rejects ``response_format`` as a bad request."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if "response_format" in kwargs:
            raise _BadRequest("unsupported response_format")
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "matched": True,
                                "block_id": "ai_prompt_buildout",
                                "confidence": 0.8,
                                "extras": {},
                            }
                        )
                    }
                }
            ]
        }


class _BadRequest(Exception):
    """The shape an OpenAI-compatible server uses to reject a parameter."""

    def __init__(self, message: str) -> None:
        super().__init__(message)

    # `_response_format_unsupported` reads the type name.
    __name__ = "BadRequestError"


def test_response_format_rejection_does_not_retry_above_controller(tmp_path, monkeypatch):
    from holdspeak.plugins.dictation.grammars import StructuredOutputSchema
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    db, _broker, session, _engine, requests = _rig(tmp_path, monkeypatch)
    completions = _RejectingCompletions()

    class _Client:
        def __init__(self, **kwargs: Any) -> None:
            self.chat = type("_Chat", (), {"completions": completions})()

    backend = OpenAICompatibleRuntime(
        model="qwen-local",
        base_url="http://127.0.0.1:1234/v1",
        api_key_env="",
        client_factory=_Client,
    )
    schema = StructuredOutputSchema(
        block_ids=("ai_prompt_buildout",), extras_per_block={"ai_prompt_buildout": {}}
    )
    runtime = AdmittedDictationRuntime(backend, session.provider())

    with pytest.raises(SpeechProviderFailure):
        runtime.classify(PROMPT_SENTINEL, schema, max_tokens=64, temperature=0.0)

    assert len(completions.calls) == 1
    assert "response_format" in completions.calls[0]
    children = _invocations(db)
    assert len(children) == 1
    assert [request.attempt_ordinal for request in requests] == [1]
    assert {row["parent_operation_id"] for row in children} == {session.operation_id}
    assert (_receipt(db, children[0]["operation_id"]) or {}).get("outcome") == "failed"


def test_mesh_classify_reuses_the_admitted_envelope(tmp_path, monkeypatch):
    """The mesh leg rides the HS-131-07 envelope, never a fresh target.

    Two facts, asserted where this story owns them:

    1. ``_dispatch_target`` binds the mesh backend to the engine the runner built
       for THIS child (from the admitted revision + the claimed warrant) instead
       of letting the backend construct a relay of its own.
    2. That engine carries the frozen revision and the warrant, and a relay built
       WITHOUT them refuses ``mesh_envelope_missing`` — so the fresh-target path
       cannot silently work.

    (The revision -> ``MeshRelayIntel`` construction itself is covered by
    ``tests/unit/test_mesh_relay_provider.py``; building it here made the test a
    hostage of another module's leaked engine patch.)
    """
    from holdspeak.deployment_revisions import capture_deployment_revision
    from holdspeak.inference_targets import DeploymentIdentity
    from holdspeak.intel.mesh_relay import MeshRelayIntel
    from holdspeak.intel.models import MeetingIntelError
    from holdspeak.plugins.dictation.runtime_mesh_relay import MeshRelayRuntime
    from holdspeak.speech_session.provider import _dispatch_target

    db, _broker, _session, _engine, _requests = _rig(tmp_path, monkeypatch)
    revision = capture_deployment_revision(
        db,
        DeploymentIdentity(
            destination_id="edge_profile",
            kind="mesh_node",
            engine="mesh",
            model="qwen-edge",
            node="edge-1",
            boundary="private_network",
            model_path=None,
            endpoint="",
            secret_slot="",
        ),
    )
    warrant = {"warrant_id": "war_edge_1"}
    admitted_engine = MeshRelayIntel(
        node="edge-1",
        model_hint="qwen-edge",
        deployment_revision=revision,
        warrant=warrant,
    )
    backend = MeshRelayRuntime(node="edge-1", model_hint="qwen-edge")

    bound = _dispatch_target(backend, admitted_engine)

    assert bound is not backend
    assert bound._intel is admitted_engine
    assert bound.node == "edge-1"
    assert admitted_engine._deployment_revision.id == revision.id
    assert admitted_engine._warrant == warrant

    # A relay the backend built for itself carries no envelope and refuses.
    own_relay = MeshRelayIntel(node="edge-1", model_hint="qwen-edge")
    db.mesh_relay.touch_worker("edge-1")
    with pytest.raises(MeetingIntelError) as raised:
        own_relay.run_prompt(user_prompt=PROMPT_SENTINEL)
    assert "mesh_envelope_missing" in str(raised.value)
    with db._connection() as conn:
        assert [dict(row) for row in conn.execute("SELECT * FROM mesh_relay_jobs")] == []
    assert _invocations(db) == []


def test_a_mesh_leg_without_an_admitted_engine_refuses(tmp_path, monkeypatch):
    """No engine, no envelope — and never a relay built on the side."""
    from holdspeak.plugins.dictation.runtime_mesh_relay import MeshRelayRuntime
    from holdspeak.speech_session.provider import MESH_ENGINE_REQUIRED, _dispatch_target

    with pytest.raises(SpeechSessionRefused) as raised:
        _dispatch_target(MeshRelayRuntime(node="edge-1"), None)
    assert raised.value.reason == MESH_ENGINE_REQUIRED


def test_a_profile_change_after_admission_cannot_retarget_the_dispatch(
    tmp_path, monkeypatch
):
    """Sol defect 5: the dispatch follows the FROZEN revision, not current config.

    The receipt names the revision the session admitted. Before this fix the
    non-mesh leg dispatched through whatever runtime the pipeline had built from
    CURRENT configuration — so editing the profile between admission and dispatch
    sent the prompt to a different endpoint under an honest-looking receipt.
    """
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)
    frozen = session.plan.deployment(session.plan.primary(CAPABILITY_REWRITE))
    assert frozen.endpoint == FROZEN_BASE_URL and frozen.model == FROZEN_MODEL

    # The owner re-points the profile AFTER the session was admitted, and the
    # pipeline rebuilds its runtime from that new configuration.
    _seed_profile(db, base_url="http://10.9.9.9:9/v1", model="somewhere-else")
    elsewhere = OpenAICompatibleRuntime(
        model="somewhere-else",
        base_url="http://10.9.9.9:9/v1",
        api_key_env="",
        client_factory=lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("the dispatch reached the RETARGETED endpoint")
        ),
    )
    admission = session.provider()
    # HS-131-10: the rebind is an adapter FACTORY, so it needs the dispatch context
    # the runner minted for the claimed child. The engine the runner built carries
    # it; a bare `None` engine now refuses by name (asserted below).
    admitted_engine = _admitted_engine(session, CAPABILITY_REWRITE)

    with pytest.raises(KernelRefused) as uncontextual:
        admission.target(elsewhere, None, CAPABILITY_REWRITE)
    assert uncontextual.value.reason == "adapter_context_required"

    bound = admission.target(elsewhere, admitted_engine, CAPABILITY_REWRITE)

    # The dispatch target was rebuilt from the frozen revision's own fields.
    assert bound is not elsewhere
    assert bound.base_url == FROZEN_BASE_URL
    assert bound.model == FROZEN_MODEL
    assert bound.api_key_env == frozen.secret_slot
    # And it is cached: one construction per revision per session, not per call.
    assert admission.target(elsewhere, admitted_engine, CAPABILITY_REWRITE) is bound

    # A real dispatch therefore never reaches the retargeted endpoint. It fails
    # honestly (nothing is listening on the frozen one) instead of succeeding
    # somewhere the receipt does not name.
    with pytest.raises(Exception):
        AdmittedDictationRuntime(elsewhere, admission).rewrite(
            PROMPT_SENTINEL, max_tokens=32, temperature=0.0
        )
    children = _invocations(db)
    assert len(children) == 1
    assert (_receipt(db, children[0]["operation_id"]) or {}).get("outcome") == "failed"


def test_an_agreeing_runtime_is_dispatched_unchanged(tmp_path, monkeypatch):
    """The fast path: a runtime that already IS the frozen target is not rebuilt."""
    _db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)
    backend = FakeBackend()
    admission = session.provider()

    assert admission.target(backend, None, CAPABILITY_REWRITE) is backend
    assert admission.target(backend, None, CAPABILITY_INTENT_CLASSIFY) is backend


def test_a_backend_that_cannot_be_rebound_refuses_by_name(tmp_path, monkeypatch):
    """Sol defect 5: an unbindable engine refuses instead of dispatching wrong."""
    from holdspeak.speech_session.plan import REVISION_TARGET_UNBINDABLE

    db = Database(tmp_path / "unbindable.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    # A PAIRED-DEVICE destination: a real frozen revision with no dictation-LLM
    # backend this process can construct.
    db.profiles.upsert(
        profile_id="prof_paired", name="prof_paired", kind="desktop",
        base_url="", model="paired-model",
    )
    _configure(db)
    session = admit_hold_session(config_snapshot=_config(profile_id="prof_paired"))
    frozen = session.plan.deployment(session.plan.primary(CAPABILITY_REWRITE))
    assert frozen.engine == "paired_runtime"
    admission = session.provider()

    with pytest.raises(SpeechSessionRefused) as raised:
        admission.rewrite(FakeBackend(), PROMPT_SENTINEL, max_tokens=32, temperature=0.0)

    assert raised.value.reason == REVISION_TARGET_UNBINDABLE
    # The refusal names the engine that could not be bound, and nothing dispatched.
    assert raised.value.detail == "paired_runtime"
    # The refusal lands BEFORE the child exists: no operation, no receipt.
    assert _invocations(db) == []
