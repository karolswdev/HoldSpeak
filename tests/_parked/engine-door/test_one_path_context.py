# PARKED 2026-11-09 (door/speech-capture): dictation stages run on the runner's engine for the revision the door picked; ProviderAdmission no longer rebinds the pipeline's own runtime onto a frozen revision (target/prepared/dispatch_through are gone).
# Moved from tests/unit/test_one_path_context.py; its helpers are still there.

from tests.unit.test_one_path_context import *  # noqa: F401,F403


def test_a_dictation_rebind_needs_the_childs_own_context(no_construction: Recorder) -> None:
    frozen = revision()
    admission = ProviderAdmission(broker=None, principal=None, plan=Plan(frozen), parent=None)
    # The pipeline's runtime points somewhere else: dispatching needs a REBUILD.
    retargeted = SimpleNamespace(
        backend="openai_compatible", base_url="http://elsewhere:9/v1", model="other-model",
        timeout_seconds=8.0,
    )

    with pytest.raises(KernelRefused) as uncontextual:
        admission.target(retargeted, None, CAPABILITY_REWRITE)
    assert uncontextual.value.reason == CONTEXT_REQUIRED
    assert no_construction.calls == []

    with pytest.raises(KernelRefused) as foreign:
        admission.target(
            retargeted,
            SimpleNamespace(_dispatch_context=context_for(revision(rid="dep_elsewhere"))),
            CAPABILITY_REWRITE,
        )
    assert foreign.value.reason == CONTEXT_MISMATCH
    assert no_construction.calls == []

    context = context_for(frozen)
    admitted_engine = SimpleNamespace(_dispatch_context=context)
    bound = admission.target(retargeted, admitted_engine, CAPABILITY_REWRITE)
    assert no_construction.calls, "the admitted child never got its target"
    assert bound is not retargeted


def test_the_target_cache_is_not_a_ride_for_an_unadmitted_caller(
    no_construction: Recorder,
) -> None:
    frozen = revision()
    admission = ProviderAdmission(broker=None, principal=None, plan=Plan(frozen), parent=None)
    retargeted = SimpleNamespace(
        backend="openai_compatible", base_url="http://elsewhere:9/v1", model="other-model",
        timeout_seconds=8.0,
    )
    context = context_for(frozen)
    first = admission.target(retargeted, SimpleNamespace(_dispatch_context=context),
                             CAPABILITY_REWRITE)

    # Cached — one construction per revision per session.
    assert admission.target(retargeted, SimpleNamespace(_dispatch_context=context),
                            CAPABILITY_REWRITE) is first
    assert len(no_construction.calls) == 1

    # …but the cache entry is not an ambient permit for a contextless caller.
    with pytest.raises(KernelRefused) as riding:
        admission.target(retargeted, None, CAPABILITY_REWRITE)
    assert riding.value.reason == CONTEXT_REQUIRED


def test_an_agreeing_runtime_needs_no_context_because_it_constructs_nothing(
    no_construction: Recorder,
) -> None:
    """The fence is on CONSTRUCTION: an already-correct target is not rebuilt."""
    frozen = revision()
    admission = ProviderAdmission(broker=None, principal=None, plan=Plan(frozen), parent=None)
    already_right = SimpleNamespace(
        backend="openai_compatible", base_url=frozen.endpoint, model=frozen.model,
    )

    assert admission.target(already_right, None, CAPABILITY_REWRITE) is already_right
    assert admission.prepared(already_right, CAPABILITY_REWRITE) is already_right
    assert no_construction.calls == []


def test_an_unbindable_engine_still_refuses_before_admission() -> None:
    """`prepared` keeps naming the unbindable backend with no operation behind it."""
    frozen = revision(engine="paired_runtime", endpoint="")
    admission = ProviderAdmission(broker=None, principal=None, plan=Plan(frozen), parent=None)

    with pytest.raises(SpeechSessionRefused):
        admission.prepared(SimpleNamespace(backend="openai_compatible"), CAPABILITY_REWRITE)
