"""HS-131-09 Part B: every dictation pipeline model call is one engine-door job.

Classify and rewrite each become ONE trusted ``inference.invoke@1`` child of the
live speech session, on the engine the door's chain names at the moment of the
call: a change in Settings › Engines is honoured on the next call. Prompts and
rewritten text never reach a kernel row.

Only the engine the runner builds is faked. The plans, the parents, the runner,
the door, the receipts, and the refusals are production code.
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
from tests.unit._speech_door import assign_profile
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
    """The engine the runner builds from the revision the door picked."""

    def __init__(self, *, failures: int = 0) -> None:
        self.prompts: list[str] = []
        self.revisions: list[str] = []
        self.failures = int(failures)

    def run_prompt(self, *, system_prompt: str = "", user_prompt: str, **kwargs: Any) -> str:
        self.prompts.append(user_prompt)
        if len(self.prompts) <= self.failures:
            raise RuntimeError("provider said no")
        if system_prompt.startswith("Rewrite"):
            return REWRITE_SENTINEL
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
    # Install the rig's database as the singleton. A temporary
    # ``get_database`` lambda is kept by any module that first imports
    # ``from holdspeak.db import get_database`` while the test runs
    # (activity_context, activity_history), and it outlives the test.
    monkeypatch.setattr("holdspeak.db.core._db", db)
    _seed_profile(db)
    broker = _configure(db)
    for job in ("speech.intent_classify", "speech.rewrite"):
        assign_profile(db, job, FROZEN_PROFILE_ID)
    engine = engine if engine is not None else FakeIntel()

    # The runner builds the engine for the revision the door picked.
    def build(revision: Any, **_kwargs: Any) -> Any:
        engine.revisions.append(str(revision.id))
        return engine

    monkeypatch.setattr(broker.inference_runner, "_engine_factory", build)
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
    # Each child names the engine the door's chain names for its stage.
    classify_revision = session.provider().revision(CAPABILITY_INTENT_CLASSIFY)
    rewrite_revision = session.provider().revision(CAPABILITY_REWRITE)
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






def test_router_failure_does_not_mint_a_second_child(tmp_path, monkeypatch):
    from holdspeak.plugins.dictation.builtin.intent_router import IntentRouter
    from holdspeak.plugins.dictation.contracts import Utterance

    db, _broker, session, engine, requests = _rig(tmp_path, monkeypatch, engine=FakeIntel(failures=1))
    backend = FakeBackend()
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
    assert len(engine.prompts) == 1
    children = _invocations(db)
    assert len(children) == 1
    assert [request.attempt_ordinal for request in requests] == [1]
    outcomes = [(_receipt(db, row["operation_id"]) or {}).get("outcome") for row in children]
    assert outcomes == ["failed"]


# ------------------------------------------------------------------- mesh



# ------------------------------------------------- the chain, at each call


def test_a_chain_change_mid_session_is_honoured_on_the_next_call(tmp_path, monkeypatch):
    """The owner re-points the rewrite job in Settings › Engines while a session
    is open: the next rewrite of the SAME session runs on the new engine, and its
    receipt names that engine. Nothing was frozen at admission."""
    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    runtime = AdmittedDictationRuntime(FakeBackend(), session.provider())
    from holdspeak.services import engine_door

    runtime.rewrite(PROMPT_SENTINEL, max_tokens=32, temperature=0.0)
    first = engine_door.engine_for(broker, "speech.rewrite").revision

    _seed_profile(db, profile_id="prof_next", base_url="http://127.0.0.1:4321/v1", model="next-model")
    assign_profile(db, "speech.rewrite", "prof_next")
    second = engine_door.engine_for(broker, "speech.rewrite").revision
    assert second != first

    assert runtime.rewrite(PROMPT_SENTINEL, max_tokens=32, temperature=0.0) == REWRITE_SENTINEL
    assert [request.deployment_revision for request in requests] == [first, second]
    assert engine.revisions == [first, second]
    children = _invocations(db)
    assert [row["parent_operation_id"] for row in children] == [session.operation_id] * 2


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

    # The rewrite never reached the engine, and the honest classify child keeps
    # its own terminal receipt.
    assert len(_engine.prompts) == 1
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
