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
from datetime import datetime, timezone
from types import SimpleNamespace
from pathlib import Path
from typing import Any

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.speech_session import (
    CAPABILITY_INTENT_CLASSIFY,
    CAPABILITY_PUNCTUATE,
    CAPABILITY_REWRITE,
    CONTRACT_INTENT_CLASSIFY,
    CONTRACT_REWRITE,
    AdmittedDictationRuntime,
    SpeechSessionRefused,
    admit_hold_session,
)
from holdspeak.speech_session.plan import CAPABILITY_NOT_PLANNED

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


def _seed_profile(db: Database, *, profile_id: str = "prof_frozen", base_url: str = FROZEN_BASE_URL,
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
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: engine
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


def test_the_response_format_retry_is_a_separate_child(tmp_path, monkeypatch):
    """Sol/story: a second real request to a model is a second child."""
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

    result = runtime.classify(PROMPT_SENTINEL, schema, max_tokens=64, temperature=0.0)

    assert result["block_id"] == "ai_prompt_buildout"
    # Two real requests to the endpoint...
    assert len(completions.calls) == 2
    assert "response_format" in completions.calls[0]
    assert "response_format" not in completions.calls[1]
    # ...and two admitted children with DISTINCT attempt ordinals and receipts.
    children = _invocations(db)
    assert len(children) == 2
    assert [request.attempt_ordinal for request in requests] == [1, 2]
    assert {row["parent_operation_id"] for row in children} == {session.operation_id}
    assert (_receipt(db, children[0]["operation_id"]) or {}).get("outcome") == "failed"
    assert (_receipt(db, children[1]["operation_id"]) or {}).get("outcome") == "succeeded"


def test_the_routers_second_classify_attempt_is_a_separate_child(tmp_path, monkeypatch):
    """`intent_router.py` retries once; each attempt is its own child."""
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

    assert result.intent.matched is True
    assert len(backend.classify_calls) == 2
    children = _invocations(db)
    assert len(children) == 2
    assert [request.attempt_ordinal for request in requests] == [1, 2]
    outcomes = [(_receipt(db, row["operation_id"]) or {}).get("outcome") for row in children]
    assert outcomes == ["failed", "succeeded"]


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

    bound = admission.target(elsewhere, None, CAPABILITY_REWRITE)

    # The dispatch target was rebuilt from the frozen revision's own fields.
    assert bound is not elsewhere
    assert bound.base_url == FROZEN_BASE_URL
    assert bound.model == FROZEN_MODEL
    assert bound.api_key_env == frozen.secret_slot
    # And it is cached: one construction per revision per session, not per call.
    assert admission.target(elsewhere, None, CAPABILITY_REWRITE) is bound

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
