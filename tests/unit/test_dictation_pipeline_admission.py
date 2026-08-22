"""HS-131-09 Part B: every dictation pipeline model call is an admitted child.

Classify, the OpenAI-compatible ``response_format`` compatibility leg, the intent
router's second attempt, and rewrite each become ONE trusted
``inference.invoke@1`` child of the live speech session, against ONE exact frozen
deployment revision. A mesh leg reuses the HS-131-07 envelope the runner built
from that admitted revision and warrant — it never constructs a target of its
own. Prompts and rewritten text never reach a kernel row.

Only the provider transport is faked. The plans, the parents, the runner, the
receipts, the frozen revisions, and the refusals are production code.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from types import SimpleNamespace
from pathlib import Path
from typing import Any

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from tests.unit.admitted_context import admitted_context
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.speech_session import (
    CAPABILITY_INTENT_CLASSIFY,
    CAPABILITY_PUNCTUATE,
    CAPABILITY_REWRITE,
    CONTRACT_INTENT_CLASSIFY,
    CONTRACT_REWRITE,
    AdmittedDictationRuntime,
    SpeechProviderFailure,
    SpeechSessionRefused,
    admit_hold_session,
)
from holdspeak.speech_session.plan import CAPABILITY_NOT_PLANNED


def _admitted_engine(session: Any, capability: str) -> Any:
    """Stand in for the engine the RUNNER builds: it carries the dispatch context."""
    revision = session.plan.deployment(session.plan.primary(capability))
    return SimpleNamespace(
        _dispatch_context=admitted_context(revision=revision, attempt_ordinal=1)
    )

pytestmark = pytest.mark.timeout(90, method="signal")

PROMPT_SENTINEL = "PINEAPPLEQUARTERLYSECRET"
REWRITE_SENTINEL = "ELDERBERRYCONFIDENTIALDRAFT"


# --------------------------------------------------------------------- fakes


class FakeSchema:
    """The structured-output schema the router hands the runtime."""

    block_ids = ("ai_prompt_buildout",)


#: The endpoint the rig's profile adopts, and therefore the endpoint the frozen
#: revision names. A fake backend must advertise EXACTLY this to be dispatched
#: unchanged — that is the anti-retargeting check, exercised on every test here.
FROZEN_PROFILE_ID = "prof_frozen"
FROZEN_BASE_URL = "http://127.0.0.1:1234/v1"
FROZEN_MODEL = "qwen-local"


class FakeBackend:
    """A dictation LLM backend reduced to its two provider-reaching methods."""

    backend = "openai_compatible"
    base_url = FROZEN_BASE_URL
    model = FROZEN_MODEL

    def __init__(self, *, failures: int = 0) -> None:
        self.classify_calls: list[dict[str, Any]] = []
        self.rewrite_calls: list[str] = []
        self.failures = int(failures)

    def load(self) -> None:
        return None

    def info(self) -> dict[str, Any]:
        return {"backend": self.backend}

    def classify(self, prompt: str, schema: Any, **kwargs: Any) -> dict[str, Any]:
        self.classify_calls.append({"prompt": prompt, **kwargs})
        if len(self.classify_calls) <= self.failures:
            raise RuntimeError("provider said no")
        return {
            "matched": True,
            "block_id": "ai_prompt_buildout",
            "confidence": 0.9,
            "extras": {},
        }

    def rewrite(self, prompt: str, **kwargs: Any) -> str:
        self.rewrite_calls.append(prompt)
        return REWRITE_SENTINEL


class FakeIntel:
    """The engine the runner builds from the admitted revision."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def run_prompt(self, *, system_prompt: str = "", user_prompt: str, **kwargs: Any) -> str:
        self.prompts.append(user_prompt)
        return json.dumps(
            {"matched": True, "block_id": "ai_prompt_buildout", "confidence": 0.5, "extras": {}}
        )


# ----------------------------------------------------------------- the rig


def _config(*, profile_id: str = "prof_frozen") -> Config:
    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router", "project-rewriter"]
    # HS-131-09: the session freezes ONE deployment revision for the provider
    # legs, and the dispatch is bound to it. Pointing the runtime at a real
    # profile is what makes "the receipt names the frozen revision" and "the call
    # landed at the frozen endpoint" the same assertion.
    config.dictation.runtime.profile_id = profile_id
    return config


def _seed_profile(db: Database, *, profile_id: str = FROZEN_PROFILE_ID, base_url: str = FROZEN_BASE_URL,
                  model: str = FROZEN_MODEL) -> None:
    db.profiles.upsert(
        profile_id=profile_id, name=profile_id, kind="openAICompatible",
        base_url=base_url, model=model,
    )


def _rig(tmp_path: Path, monkeypatch, *, engine: Any = None):
    """A real database, broker, admitted hold session, and provider admission."""
    db = Database(tmp_path / "pipeline.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    _seed_profile(db)
    broker = _configure(db)
    engine = engine if engine is not None else FakeIntel()
    # `this_machine` resolves through the production builder, so the frozen
    # revision -> engine path is exercised rather than bypassed.
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: engine
    )
    requests: list[Any] = []
    real_invoke = broker.inference_runner.invoke

    def observed_invoke(request: Any, *args: Any, **kwargs: Any) -> Any:
        requests.append(request)
        return real_invoke(request, *args, **kwargs)

    monkeypatch.setattr(broker.inference_runner, "invoke", observed_invoke)
    session = admit_hold_session(config_snapshot=_config())
    return db, broker, session, engine, requests


def _invocations(db: Database) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM kernel_operations WHERE name='inference.invoke'"
                " ORDER BY created_at"
            )
        ]


def _receipt(db: Database, operation_id: str) -> dict[str, Any] | None:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE operation_id=?", (operation_id,)
        ).fetchone()
    return None if row is None else dict(row)


def _contract(request: Any) -> str:
    return str(getattr(request.definition_origin, "contract", ""))


# -------------------------------------------------------- classify + rewrite


def test_classify_and_rewrite_are_children_with_frozen_revisions(tmp_path, monkeypatch):
    db, _broker, session, _engine, requests = _rig(tmp_path, monkeypatch)
    backend = FakeBackend()
    runtime = AdmittedDictationRuntime(backend, session.provider())

    result = runtime.classify(PROMPT_SENTINEL, FakeSchema(), max_tokens=64, temperature=0.0)
    rewritten = runtime.rewrite(PROMPT_SENTINEL, max_tokens=128, temperature=0.1)

    assert result["block_id"] == "ai_prompt_buildout"
    assert rewritten == REWRITE_SENTINEL
    children = _invocations(db)
    assert len(children) == 2
    parent = session.operation_id
    assert [row["parent_operation_id"] for row in children] == [parent, parent]
    # Each child names ONE exact entry the plan already froze — no late lookup.
    classify_revision = session.plan.primary(CAPABILITY_INTENT_CLASSIFY)
    rewrite_revision = session.plan.primary(CAPABILITY_REWRITE)
    assert [request.deployment_revision for request in requests] == [
        classify_revision,
        rewrite_revision,
    ]
    assert [_contract(request) for request in requests] == [
        CONTRACT_INTENT_CLASSIFY,
        CONTRACT_REWRITE,
    ]
    # One terminal receipt each.
    for row in children:
        assert (_receipt(db, row["operation_id"]) or {}).get("outcome") == "succeeded"


def test_no_prompt_or_rewritten_text_reaches_any_kernel_row(tmp_path, monkeypatch):
    db, _broker, session, _engine, requests = _rig(tmp_path, monkeypatch)
    runtime = AdmittedDictationRuntime(FakeBackend(), session.provider())

    runtime.classify(PROMPT_SENTINEL, FakeSchema(), max_tokens=64, temperature=0.0)
    runtime.rewrite(PROMPT_SENTINEL, max_tokens=128, temperature=0.1)
    session.close("succeeded")

    with db._connection() as conn:
        for table in (
            "kernel_operations",
            "kernel_receipts",
            "kernel_journal",
            "kernel_parent_runs",
        ):
            for row in conn.execute(f"SELECT * FROM {table}"):
                blob = "|".join(str(value) for value in dict(row).values())
                assert PROMPT_SENTINEL not in blob, table
                assert REWRITE_SENTINEL not in blob, table


def test_a_capability_the_plan_never_froze_refuses_by_name(tmp_path, monkeypatch):
    _db, _broker, session, _engine, requests = _rig(tmp_path, monkeypatch)
    admission = session.provider()

    # Today's punctuation pass is lexical, so no plan declares it. A seam that
    # tried to reach a provider for it refuses BEFORE any request exists.
    assert not admission.declares(CAPABILITY_PUNCTUATE)
    with pytest.raises(SpeechSessionRefused) as raised:
        admission.punctuate(FakeBackend(), PROMPT_SENTINEL)
    assert raised.value.reason == CAPABILITY_NOT_PLANNED
    assert _invocations(_db) == []


# ------------------------------------------------- the compatibility retry


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


_BadRequest.__name__ = "BadRequestError"


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


def test_router_failure_does_not_mint_a_second_child(tmp_path, monkeypatch):
    from holdspeak.plugins.dictation.builtin.intent_router import IntentRouter
    from holdspeak.plugins.dictation.contracts import Utterance

    db, _broker, session, _engine, requests = _rig(tmp_path, monkeypatch)
    backend = FakeBackend(failures=1)
    runtime = AdmittedDictationRuntime(backend, session.provider())

    from holdspeak.plugins.dictation.blocks import (
        Block,
        InjectMode,
        InjectSpec,
        LoadedBlocks,
        MatchSpec,
    )

    blocks = LoadedBlocks(
        version=1,
        blocks=(
            Block(
                id="ai_prompt_buildout",
                description="AI prompt buildout phase",
                match=MatchSpec(examples=("Claude, build a function that...",)),
                inject=InjectSpec(mode=InjectMode.APPEND, template="{raw_text}"),
            ),
        ),
        default_match_confidence=0.6,
        source_path=None,
    )

    router = IntentRouter(runtime, blocks)
    result = router.run(
        Utterance(
            raw_text=PROMPT_SENTINEL,
            audio_duration_s=1.0,
            transcribed_at=datetime(2026, 8, 10, tzinfo=timezone.utc),
        ),
        [],
    )

    assert result.intent.matched is False
    assert len(backend.classify_calls) == 1
    children = _invocations(db)
    assert len(children) == 1
    assert [request.attempt_ordinal for request in requests] == [1]
    outcomes = [(_receipt(db, row["operation_id"]) or {}).get("outcome") for row in children]
    assert outcomes == ["failed"]


# ------------------------------------------------------------------- mesh


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


# ------------------------------------------------------------- the fence


def test_a_cancelled_session_refuses_the_next_provider_child(tmp_path, monkeypatch):
    db, _broker, session, _engine, requests = _rig(tmp_path, monkeypatch)
    backend = FakeBackend()
    admission = session.provider()
    runtime = AdmittedDictationRuntime(backend, admission)

    runtime.classify(PROMPT_SENTINEL, FakeSchema(), max_tokens=64, temperature=0.0)
    session.cancel_and_close()

    with pytest.raises(SpeechSessionRefused):
        runtime.rewrite(PROMPT_SENTINEL, max_tokens=128, temperature=0.1)

    # The rewrite never reached the provider, and the honest classify child keeps
    # its own terminal receipt.
    assert backend.rewrite_calls == []
    children = _invocations(db)
    assert len(children) == 1
    assert (_receipt(db, children[0]["operation_id"]) or {}).get("outcome") == "succeeded"


def test_the_pipeline_publishes_nothing_once_the_session_is_fenced(tmp_path, monkeypatch):
    """`run_dictation_pipeline` discards text and journals nothing when fenced."""
    from holdspeak.dictation_runner import run_dictation_pipeline

    _db, _broker, session, _engine, requests = _rig(tmp_path, monkeypatch)
    admission = session.provider()
    session.cancel_and_close()

    class _Journal:
        def __init__(self) -> None:
            self.rows: list[Any] = []

        def record(self, *args: Any, **kwargs: Any) -> None:
            self.rows.append(args)

    journal = _Journal()

    from types import SimpleNamespace

    final = run_dictation_pipeline(
        PROMPT_SENTINEL,
        config=_config(),
        server=SimpleNamespace(dictation_journal=journal),
        audio_duration_s=1.0,
        transcribed_at=None,
        admission=admission,
    )

    assert final == ""
    assert journal.rows == []


# --------------------------------- Sol defect 5: no silent retargeting


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


# ============ ROUND 2 (coordinator finding): the FALLBACK is a publication ====


@pytest.mark.parametrize(
    "entry_point", ["run_dictation_pipeline", "run_pipeline_corrections_only"]
)
def test_an_exception_after_the_fence_still_publishes_nothing(
    entry_point, tmp_path, monkeypatch
):
    """A cancelled session whose run then RAISES must type nothing.

    Both entry points end in ``except Exception -> return text``. That fallback is
    a publication, and it was unconditional: fence the session, have anything in
    the run raise — a config read, project detection, the pipeline build, a stage
    — and the raw transcript was handed back to be typed, after the session had
    been cancelled. The three explicit fence checks all sat on the happy path,
    which is exactly the path a cancellation does NOT take.

    Deterministic: the exception is injected at ``build_pipeline``, which every
    run reaches inside the try and before the first fence check, so there is no
    ordering to race.
    """
    import holdspeak.dictation_runner as runner_module
    import holdspeak.plugins.dictation.assembly as assembly

    _db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)
    admission = session.provider()
    session.cancel_and_close()

    def explode(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("the run fell over after the session was cancelled")

    monkeypatch.setattr(assembly, "build_pipeline", explode)

    class _Journal:
        def __init__(self) -> None:
            self.rows: list[Any] = []

        def record(self, *args: Any, **kwargs: Any) -> None:
            self.rows.append(args)

    journal = _Journal()
    final = getattr(runner_module, entry_point)(
        PROMPT_SENTINEL,
        config=_config(),
        server=SimpleNamespace(dictation_journal=journal),
        audio_duration_s=1.0,
        transcribed_at=None,
        admission=admission,
    )

    assert final == "", f"{entry_point} typed a cancelled session's transcript"
    assert PROMPT_SENTINEL not in str(final)
    assert journal.rows == []


@pytest.mark.parametrize(
    "entry_point", ["run_dictation_pipeline", "run_pipeline_corrections_only"]
)
def test_an_exception_without_a_fence_still_falls_back_to_the_text(
    entry_point, tmp_path, monkeypatch
):
    """The guard is the FENCE, not the exception: a live session still recovers.

    The fallback exists so a pipeline bug never costs the user their words. That
    behaviour is unchanged for any session that has not been cancelled.
    """
    import holdspeak.dictation_runner as runner_module
    import holdspeak.plugins.dictation.assembly as assembly

    _db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)
    admission = session.provider()  # live: never cancelled

    def explode(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("a pipeline bug, on a healthy session")

    monkeypatch.setattr(assembly, "build_pipeline", explode)

    final = getattr(runner_module, entry_point)(
        PROMPT_SENTINEL,
        config=_config(),
        server=SimpleNamespace(dictation_journal=None),
        audio_duration_s=1.0,
        transcribed_at=None,
        admission=admission,
    )

    assert final == PROMPT_SENTINEL, f"{entry_point} lost a live session's words"


@pytest.mark.parametrize(
    "entry_point", ["run_dictation_pipeline", "run_pipeline_corrections_only"]
)
@pytest.mark.parametrize(
    "fatal",
    [
        pytest.param(
            lambda: SpeechSessionRefused("speech_child_budget_exhausted"),
            id="session-refusal",
        ),
        pytest.param(
            lambda: SpeechProviderFailure(
                "dictation.rewrite", reason="provider_budget_refused"
            ),
            id="provider-failure",
        ),
    ],
)
def test_outer_dictation_runner_never_degrades_fatal_speech_signals(
    entry_point, fatal, tmp_path, monkeypatch
):
    """Outer orchestration must preserve the same fatal channel as its stages."""
    import holdspeak.dictation_runner as runner_module
    import holdspeak.plugins.dictation.assembly as assembly

    _db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)
    admission = session.provider()

    def refuse(*_args: Any, **_kwargs: Any) -> Any:
        raise fatal()

    monkeypatch.setattr(assembly, "build_pipeline", refuse)

    with pytest.raises((SpeechSessionRefused, SpeechProviderFailure)):
        getattr(runner_module, entry_point)(
            PROMPT_SENTINEL,
            config=_config(),
            server=SimpleNamespace(dictation_journal=None),
            audio_duration_s=1.0,
            transcribed_at=None,
            admission=admission,
        )


@pytest.mark.parametrize(
    "entry_point", ["run_dictation_pipeline", "run_pipeline_corrections_only"]
)
def test_a_fenced_session_publishes_nothing_even_with_the_pipeline_off(
    entry_point, tmp_path, monkeypatch
):
    """The pipeline-disabled return journalled a row and typed the transcript.

    ``_fenced``'s own contract is "no journal row, no final text". The disabled
    path honoured neither: it ran ``_journal_passthrough`` and returned the
    transcript before any fence was consulted.
    """
    import holdspeak.dictation_runner as runner_module

    _db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)
    admission = session.provider()
    session.cancel_and_close()

    config = _config()
    config.dictation.pipeline.enabled = False

    class _Journal:
        def __init__(self) -> None:
            self.rows: list[Any] = []

        def record(self, *args: Any, **kwargs: Any) -> None:
            self.rows.append(args)

    journal = _Journal()
    final = getattr(runner_module, entry_point)(
        PROMPT_SENTINEL,
        config=config,
        server=SimpleNamespace(dictation_journal=journal),
        audio_duration_s=1.0,
        transcribed_at=None,
        admission=admission,
    )

    assert final == ""
    assert journal.rows == [], "a fenced session recorded a journal row"


def test_runner_journal_and_result_handoff_win_before_cancellation(
    tmp_path, monkeypatch
):
    """A journal callback already elected completes before cancellation owns the fence."""
    import holdspeak.dictation_runner as runner_module
    import holdspeak.plugins.dictation.assembly as assembly

    _db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)
    admission = session.provider()
    config = _config()
    config.dictation.pipeline.enabled = True
    run = SimpleNamespace(final_text="processed", stage_results=[])
    monkeypatch.setattr(
        assembly,
        "build_pipeline",
        lambda *_args, **_kwargs: SimpleNamespace(
            runtime_status="loaded",
            runtime=SimpleNamespace(),
            pipeline=SimpleNamespace(run=lambda _utterance: run),
        ),
    )

    journal_entered = threading.Event()
    release_journal = threading.Event()
    cancellation_started = threading.Event()
    cancellation_done = threading.Event()
    rows: list[Any] = []
    results: list[str] = []

    class Journal:
        def record(self, *args: Any, **kwargs: Any) -> None:
            journal_entered.set()
            assert release_journal.wait(5), "test never released journal publication"
            rows.append((args, kwargs))

    run_thread = threading.Thread(
        target=lambda: results.append(
            runner_module.run_pipeline_corrections_only(
                PROMPT_SENTINEL,
                config=config,
                server=SimpleNamespace(
                    dictation_journal=Journal(),
                    dictation_corrections=None,
                    dictation_telemetry=None,
                ),
                audio_duration_s=1.0,
                transcribed_at=None,
                skip_target_detection=True,
                admission=admission,
            )
        )
    )
    run_thread.start()
    assert journal_entered.wait(5), "journal never won the publication election"

    def cancel() -> None:
        cancellation_started.set()
        session.cancel_and_close()
        cancellation_done.set()

    cancel_thread = threading.Thread(target=cancel)
    cancel_thread.start()
    assert cancellation_started.wait(5)
    assert not cancellation_done.wait(0.05), "cancellation crossed journal publication"
    release_journal.set()
    run_thread.join(5)
    cancel_thread.join(5)

    assert results == ["processed"]
    assert len(rows) == 1
    assert cancellation_done.is_set()


def test_an_unreadable_fence_fails_closed() -> None:
    """We cannot tell whether this session may publish, so it may not.

    ``_fenced`` used to be ``fence is not None and fence.discarded(stage)``, so a
    fence that raised took the whole run into the ``except Exception`` fallback —
    and that fallback published. Failing closed keeps the one honest answer.
    """
    from holdspeak.dictation_runner import _fenced, _publishable

    class _Unreadable:
        def discarded(self, _stage: str) -> bool:
            raise RuntimeError("the fence cannot be read")

    admission = SimpleNamespace(fence=_Unreadable())
    assert _fenced(admission, "any stage") is True
    assert _publishable(PROMPT_SENTINEL, admission, "any stage") == ""

    # No admission at all (the legacy, unadmitted callers) is NOT fenced.
    assert _fenced(None, "any stage") is False
    assert _publishable(PROMPT_SENTINEL, None, "any stage") == PROMPT_SENTINEL
