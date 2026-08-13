"""HS-131-10 Stage A: the adapter fence is a CONTEXT, not a parameter name.

`InferenceRunner.invoke` is the one admission path, but that is only true while a
product surface cannot build the same engine the runner builds. Every allowlisted
adapter factory therefore demands the opaque context the runner minted for the
child it JUST claimed — bound to that operation id, the immutable revision id, its
destination, a positive attempt ordinal, and the authenticated warrant basis.

These are runtime proofs, not source census (that is the Stage-B AST suite). Each
refusal case asserts the exact named reason AND that nothing was constructed or
dispatched: the constructors are replaced with recorders that fail the test if the
fence let a call through.
"""

from __future__ import annotations

import dataclasses
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import (
    HUB_DEFAULT_CLOUD_ID,
    PAIRED_DEVICE_EXECUTION_UNSUPPORTED,
    THIS_MACHINE_ID,
    build_intel_for_revision,
    local_pinned_meeting_intel,
    resolve_inference_target,
)
from holdspeak.intel.providers import build_meeting_intel_for_profile, configured_meeting_intel
from holdspeak.kernel.dispatch_context import (
    CONTEXT_MISMATCH,
    CONTEXT_REQUIRED,
    LEGACY_UNCONTEXTUAL,
    DispatchContext,
    dispatch_context_of,
    require_dispatch_context,
)
from holdspeak.kernel.inference_runner import InferenceRunner, InvocationRequest, ServiceContract
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.speech_session.plan import (
    CAPABILITY_REWRITE,
    WHISPER_KIND,
    SpeechSessionRefused,
)
from holdspeak.speech_session.provider import ProviderAdmission
from holdspeak.speech_session.revision_target import bound_target, rebind
from tests.unit.admitted_context import admitted_context, claimed_witness

OWNER = Principal(PrincipalKind.OWNER, "owner")

#: The shape the kernel's `claim` hands back: a warrant it has already verified.
SIGNED = {"expires_at": 1.0, "signature": "e3b0c44298fc1c14"}


def revision(
    *,
    rid: str = "dep_one",
    destination: str = "profile-one",
    kind: str = "private_endpoint",
    engine: str = "openai_compatible",
    endpoint: str = "http://127.0.0.1:8080/v1",
    model: str = "qwen3.5-4b",
    model_path: Any = None,
    node: str = "",
) -> SimpleNamespace:
    """A frozen-revision stand-in: the factories only read these fields."""
    return SimpleNamespace(
        id=rid, destination_id=destination, kind=kind, engine=engine, model=model,
        node=node, boundary="private_endpoint", endpoint=endpoint,
        model_path=model_path, secret_slot="HOLDSPEAK_PROFILE_ONE_KEY",
    )


def context_for(frozen: Any, *, attempt: int = 1) -> DispatchContext:
    """A context minted the ONE way one can be minted: by actually being admitted.

    HS-131-10 round 2 (Terra finding A, second pass): round 1 still let a TEST
    write down an operation id and a warrant-shaped mapping and get a witness,
    which made the fence's central claim true of production and false of its own
    proof. ``mint_claim_witness`` no longer exists; the issuer is handed out once,
    at import of ``holdspeak/kernel/executor.py``. So this runs a REAL kernel
    admission — submit, decide, claim — and mints the context out of the witness
    that claim issued. The operation id is whatever the kernel claimed; the
    warrant is the one it verified.
    """
    return admitted_context(revision=frozen, attempt_ordinal=attempt)


class Recorder:
    """Every physical constructor, replaced by something that records instead.

    A construction that happens while the context is missing or forged is the
    failure these tests are looking for, so the recorder IS the assertion.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def constructor(self, label: str) -> type:
        """A real class (isinstance checks in the product code still work)."""
        recorder = self

        class Constructed:
            def __init__(self, *_args: Any, **kwargs: Any) -> None:
                recorder.calls.append({"target": label, **kwargs})
                self.kwargs = dict(kwargs)
                self.provider = ""
                self._active_provider = None

        Constructed.__name__ = label
        return Constructed


@pytest.fixture
def no_construction(monkeypatch: Any) -> Recorder:
    """Every physical engine constructor in the migrated branches, wired to a recorder."""
    recorder = Recorder()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", recorder.constructor("MeetingIntel"))
    monkeypatch.setattr(
        "holdspeak.intel.mesh_relay.MeshRelayIntel", recorder.constructor("MeshRelayIntel")
    )
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel",
        recorder.constructor("build_configured_meeting_intel"),
    )
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime_openai_compatible.OpenAICompatibleRuntime",
        recorder.constructor("OpenAICompatibleRuntime"),
    )
    return recorder


# --------------------------------------------------------------- the mint itself


def test_the_mint_binds_the_five_facts_of_the_claimed_child() -> None:
    frozen = revision()
    context = context_for(frozen, attempt=3)

    # The operation is the one the kernel ACTUALLY claimed — not a literal the
    # caller chose, which is the whole difference from round 1.
    assert context.operation_id.startswith("op_") and len(context.operation_id) > 3
    assert context.revision_id == frozen.id
    assert context.destination_id == frozen.destination_id
    assert context.attempt_ordinal == 3
    assert context.warrant_basis and context.warrant_basis != SIGNED["signature"]
    # The diagnostic value is content-free: identity, never warrant material.
    assert context.journal_value() == {
        "operation_id": context.operation_id, "revision": frozen.id,
        "destination": frozen.destination_id, "attempt": 3,
    }
    assert "signature" not in context.journal_value()
    assert require_dispatch_context(context, frozen) is context


#: "leave the claim's own warrant alone" — distinct from an explicit ``None``,
#: which several rows below deliberately submit.
_CLAIMED = object()


@pytest.mark.parametrize(
    ("kwargs", "why"),
    [
        ({"frozen": SimpleNamespace(id="", destination_id="d")}, "no immutable revision id"),
        ({"frozen": SimpleNamespace(id="dep_one", destination_id="")}, "no destination"),
        ({"frozen": None}, "no revision at all"),
        ({"attempt": 0}, "attempt ordinal is not positive"),
        ({"attempt": -1}, "attempt ordinal is negative"),
        ({"attempt": "first"}, "attempt ordinal is not a number"),
        ({"warrant": None}, "no warrant"),
        ({"warrant": {}}, "empty warrant"),
        ({"warrant": {"expires_at": 1.0}}, "warrant carries no authenticated basis"),
        ({"warrant": {"signature": ""}}, "blank basis"),
        ({"warrant": "signed"}, "warrant is not a mapping"),
        ({"warrant": SIGNED}, "a well-formed warrant the claim never witnessed"),
    ],
)
def test_the_mint_refuses_every_incomplete_binding(kwargs: dict[str, Any], why: str) -> None:
    """The two retired rows — a blank/absent operation id — are no longer
    expressible: the operation comes from the claim, so there is no argument to
    blank out. `test_the_mint_refuses_everything_that_is_not_a_live_claim_witness`
    carries that coverage instead."""
    call: dict[str, Any] = {"frozen": revision(), "attempt": 1, "warrant": _CLAIMED}
    call.update(kwargs)
    warrant = {} if call["warrant"] is _CLAIMED else {"warrant": call["warrant"]}
    with pytest.raises(KernelRefused) as refusal:
        admitted_context(
            revision=call["frozen"], attempt_ordinal=call["attempt"], **warrant
        )
    assert refusal.value.reason == CONTEXT_REQUIRED, why


def test_the_mint_refuses_everything_that_is_not_a_live_claim_witness() -> None:
    """The mint's input is an EVENT, not a shape (HS-131-10 Terra finding A).

    Before this, a product module could write ``operation_id="op_1"`` and
    ``warrant={"signature": "x"}`` and hold a valid dispatch context — the two
    literals were the whole proof. Now the only way in is the object
    ``ExecutorPlane.claim`` minted, checked by identity and spent on use.
    """
    from dataclasses import replace as dataclass_replace

    from holdspeak.kernel.claim_witness import ClaimWitness
    from holdspeak.kernel.dispatch_context import _issue_dispatch_context

    frozen = revision()
    real, warrant = claimed_witness()

    def mint_with(witness: Any, basis: Any = None) -> Any:
        return _issue_dispatch_context(
            witness=witness, revision=frozen, warrant=warrant if basis is None else basis
        )

    for forged, why in (
        (None, "no witness at all"),
        ("op_claimed", "an operation id is not a witness"),
        (SimpleNamespace(operation_id="op_claimed", warrant_basis="sig"), "duck type"),
    ):
        with pytest.raises(KernelRefused) as refusal:
            mint_with(forged)
        assert refusal.value.reason == CONTEXT_REQUIRED, why

    # A witness cannot be constructed at all without the module's private mint.
    with pytest.raises(KernelRefused):
        ClaimWitness(operation_id="op_claimed", warrant_basis="sig")

    # A field-for-field copy of a REAL witness is not the witness that was issued.
    with pytest.raises(KernelRefused) as refusal:
        mint_with(dataclass_replace(real))
    assert refusal.value.reason == CONTEXT_REQUIRED

    # The warrant bound to the context must be the one the claim witnessed.
    with pytest.raises(KernelRefused) as refusal:
        mint_with(real, {"signature": "a-different-basis"})
    assert refusal.value.reason == CONTEXT_REQUIRED

    # It works exactly once: one claim, one context.
    context = mint_with(real)
    assert context.operation_id and context.operation_id.startswith("op_")
    with pytest.raises(KernelRefused) as refusal:
        mint_with(real)
    assert refusal.value.reason == CONTEXT_REQUIRED


def test_there_is_no_importable_way_to_mint_a_witness() -> None:
    """Round 2 (Terra blocker 4): the mint is a capability, not a function.

    Round 1 exported ``mint_claim_witness(operation_id=..., warrant=...)``. Two
    literals any module can type were therefore sufficient authority to build any
    adapter in the codebase — the fence held only because nobody had typed them.

    There is now nothing to call. The issuer is created once and handed to
    ``executor.py`` at import; the installer refuses every caller after that, so a
    product module (or this test) cannot obtain a second one.
    """
    import holdspeak.kernel.claim_witness as claim_witness

    assert not hasattr(claim_witness, "mint_claim_witness")
    assert "mint_claim_witness" not in claim_witness.__all__
    assert not any("mint" in name for name in claim_witness.__all__)

    # The one-shot installer was already spent by `executor.py`'s import.
    with pytest.raises(KernelRefused) as spent:
        claim_witness._install_claim_issuer()
    assert spent.value.reason == "adapter_context_required"

    # …and it stays spent, so a retry loop is not a way in either.
    with pytest.raises(KernelRefused):
        claim_witness._install_claim_issuer()


def test_a_context_cannot_be_built_copied_or_impersonated() -> None:
    frozen = revision()
    real = context_for(frozen)

    # Direct construction: there is no mint to pass, so the class refuses itself.
    with pytest.raises(KernelRefused) as built:
        DispatchContext(
            operation_id="op_claimed", revision_id=frozen.id,
            destination_id=frozen.destination_id, attempt_ordinal=1, warrant=SIGNED,
        )
    assert built.value.reason == CONTEXT_REQUIRED

    # A duck-typed look-alike with every field is not a context.
    duck = SimpleNamespace(
        operation_id="op_claimed", revision_id=frozen.id,
        destination_id=frozen.destination_id, attempt_ordinal=1, warrant=SIGNED,
        warrant_basis=SIGNED["signature"],
    )
    with pytest.raises(KernelRefused) as ducked:
        require_dispatch_context(duck, frozen)
    assert ducked.value.reason == CONTEXT_REQUIRED

    # A REPLACE of a genuinely issued context keeps the private mint but is not
    # the object the runner issued — the registry is identity-based.
    forged = dataclasses.replace(real, operation_id="op_someone_else")
    with pytest.raises(KernelRefused) as replaced:
        require_dispatch_context(forged, frozen)
    assert replaced.value.reason == CONTEXT_REQUIRED

    # And the ONE legacy marker is not a context either.
    for value in (None, "", {}, LEGACY_UNCONTEXTUAL):
        with pytest.raises(KernelRefused) as absent:
            require_dispatch_context(value, frozen)
        assert absent.value.reason == CONTEXT_REQUIRED


def test_a_real_context_presented_for_other_work_is_a_mismatch() -> None:
    frozen = revision()
    context = context_for(frozen, attempt=2)
    mine = context.operation_id

    with pytest.raises(KernelRefused) as wrong_operation:
        require_dispatch_context(context, frozen, operation_id="op_yours")
    assert wrong_operation.value.reason == CONTEXT_MISMATCH

    with pytest.raises(KernelRefused) as wrong_attempt:
        require_dispatch_context(context, frozen, operation_id=mine, attempt_ordinal=1)
    assert wrong_attempt.value.reason == CONTEXT_MISMATCH

    with pytest.raises(KernelRefused) as wrong_revision:
        require_dispatch_context(context, revision(rid="dep_other"))
    assert wrong_revision.value.reason == CONTEXT_MISMATCH

    with pytest.raises(KernelRefused) as wrong_destination:
        require_dispatch_context(context, revision(destination="profile-two"))
    assert wrong_destination.value.reason == CONTEXT_MISMATCH

    # The exact binding still passes: mismatch is about disagreement, not strictness.
    assert require_dispatch_context(
        context, frozen, operation_id=mine, attempt_ordinal=2
    ) is context


def test_validation_is_in_memory_and_reads_no_configuration(monkeypatch: Any) -> None:
    """The dictation hot path pays string compares — never a row, config, or clock."""
    import threading

    # Scoped to THIS thread. `time.time` is process-global, and a kernel rig in
    # the same process legitimately keeps background workers (lease refreshers,
    # watchdog timers) that read the clock; tripping on those proves nothing about
    # validation and only raises unraisable-exception noise from another thread.
    caller = threading.get_ident()
    real_time = time.time

    def explode(*_args: Any, **_kwargs: Any) -> Any:
        if threading.get_ident() != caller:
            return real_time()
        raise AssertionError("context validation read something it must not read")

    # Minted BEFORE the traps: obtaining a context takes a real admission (which
    # of course reads rows and a clock). What must read nothing is VALIDATION,
    # which is the hot-path cost every dispatch pays.
    frozen = revision()
    context = context_for(frozen)

    monkeypatch.setattr("holdspeak.config.Config.load", staticmethod(explode))
    monkeypatch.setattr("holdspeak.deployment_revisions.resolve_deployment_revision", explode)
    monkeypatch.setattr(time, "time", explode)

    assert require_dispatch_context(context, frozen) is context
    with pytest.raises(KernelRefused):
        require_dispatch_context(None, frozen)


# ------------------------------------------------- the migrated factory branches


@pytest.mark.parametrize(
    "forged",
    [None, "", {}, "not-a-context", SimpleNamespace(operation_id="op", revision_id="dep_one")],
    ids=["missing", "empty", "null-mapping", "string", "duck-typed"],
)
def test_every_migrated_factory_refuses_before_anything_is_constructed(
    forged: Any, no_construction: Recorder
) -> None:
    frozen = revision()

    for call in (
        lambda: build_intel_for_revision(frozen, context=forged),
        lambda: local_pinned_meeting_intel("/model.gguf", context=forged),
        lambda: configured_meeting_intel(context=forged),
        lambda: build_meeting_intel_for_profile(
            kind="openAICompatible", base_url=frozen.endpoint, model=frozen.model,
            profile_id=frozen.destination_id, deployment_revision=frozen, context=forged,
        ),
        lambda: rebind(SimpleNamespace(backend="openai_compatible"), frozen, context=forged),
        lambda: bound_target(
            SimpleNamespace(backend="openai_compatible", base_url="http://elsewhere/v1",
                            model="other"),
            frozen, context=forged,
        ),
    ):
        with pytest.raises(KernelRefused) as refusal:
            call()
        assert refusal.value.reason == CONTEXT_REQUIRED

    assert no_construction.calls == [], "an adapter was constructed behind the fence"


def test_a_wrong_revision_context_refuses_before_construction(no_construction: Recorder) -> None:
    frozen = revision()
    other = context_for(revision(rid="dep_elsewhere", destination="profile-two"))

    for call in (
        lambda: build_intel_for_revision(frozen, context=other),
        lambda: build_meeting_intel_for_profile(
            kind="openAICompatible", base_url=frozen.endpoint, model=frozen.model,
            profile_id=frozen.destination_id, deployment_revision=frozen, context=other,
        ),
        lambda: rebind(SimpleNamespace(backend="openai_compatible"), frozen, context=other),
    ):
        with pytest.raises(KernelRefused) as refusal:
            call()
        assert refusal.value.reason == CONTEXT_MISMATCH

    # Same immutable revision id, different destination: still not this engine.
    same_id_other_destination = revision(destination="profile-two")
    with pytest.raises(KernelRefused) as destination:
        build_intel_for_revision(
            same_id_other_destination, context=context_for(revision())
        )
    assert destination.value.reason == CONTEXT_MISMATCH
    assert no_construction.calls == []


@pytest.mark.parametrize(
    ("frozen", "branch"),
    [
        (revision(rid="dep_cloud", destination=HUB_DEFAULT_CLOUD_ID, kind="external_service"),
         "hub cloud"),
        (revision(rid="dep_local", destination=THIS_MACHINE_ID, kind="this_device",
                  engine="local", endpoint="", model_path="/model.gguf"), "this machine"),
        (revision(rid="dep_profile"), "named profile endpoint"),
        (revision(rid="dep_mesh", destination="node-one", kind="mesh_node", engine="mesh",
                  endpoint="", node="walk-edge"), "mesh node"),
    ],
)
def test_the_context_is_bound_through_every_branch(
    frozen: Any, branch: str, no_construction: Recorder
) -> None:
    context = context_for(frozen)
    engine = build_intel_for_revision(frozen, warrant=SIGNED, context=context)

    assert no_construction.calls, f"{branch} constructed nothing"
    assert dispatch_context_of(engine) is context, f"{branch} lost the dispatch context"


def test_a_frozen_paired_revision_refuses_instead_of_rereading_mutable_config(
    no_construction: Recorder, monkeypatch: Any
) -> None:
    """Round 2 (Terra blocker 7): a paired revision was executed from live config.

    ``paired_device`` mapped to the profile kind ``desktop``, which no branch of
    ``_profile_engine`` builds, so it fell through to ``configured_meeting_intel``
    and re-read the user's CURRENT meeting configuration at dispatch time. A
    revision frozen with model ``FROZEN-MODEL`` therefore ran against whatever the
    config said in that moment, while the receipt still named the frozen revision.

    Paired execution happens on the paired device: there is nothing here to build
    out of the revision's own fields, so it refuses by name before any physical
    work rather than silently retargeting.
    """
    frozen = revision(rid="dep_paired", destination="paired-hub", kind="paired_device",
                      engine="paired", endpoint="", model="FROZEN-MODEL")

    class _MutableConfigEngine:
        source = "mutable-config-at-dispatch-time"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel",
        lambda: _MutableConfigEngine(),
    )

    with pytest.raises(KernelRefused) as refusal:
        build_intel_for_revision(frozen, warrant=SIGNED, context=context_for(frozen))
    assert refusal.value.reason == PAIRED_DEVICE_EXECUTION_UNSUPPORTED
    assert no_construction.calls == []


def test_a_real_context_is_not_authority_for_a_deployment_it_was_not_minted_for(
    no_construction: Recorder,
) -> None:
    """Round 2 (Terra blocker 5): a factory with nothing to compare compared nothing.

    ``local_pinned_meeting_intel`` validated ``require_dispatch_context(context)``
    with NO expected revision, so a context genuinely minted for a REMOTE child
    was enough to build a LOCAL engine — the gate proved that some child had been
    admitted, not that this deployment was the one it was admitted for. The same
    hole sat in ``configured_meeting_intel`` and in
    ``build_meeting_intel_for_profile(..., deployment_revision=None)``.
    """
    remote = revision(rid="dep_remote", destination="remote-endpoint")
    local = revision(rid="dep_local", destination=THIS_MACHINE_ID, kind="this_device",
                     engine="local", endpoint="", model_path="/model.gguf")
    genuine = context_for(remote)

    # A real context, for real work — but not for THIS engine.
    with pytest.raises(KernelRefused) as crossed:
        local_pinned_meeting_intel("/model.gguf", context=genuine, revision=local)
    assert crossed.value.reason == CONTEXT_MISMATCH

    # And a factory asked to build with no expected revision at all refuses:
    # there is nothing the caller could be proving.
    for call, why in (
        (lambda: local_pinned_meeting_intel("/model.gguf", context=genuine), "no revision"),
        (lambda: configured_meeting_intel(context=genuine), "configured, no revision"),
        (
            lambda: build_meeting_intel_for_profile(
                kind="openAICompatible", base_url=remote.endpoint, model=remote.model,
                profile_id=remote.destination_id, deployment_revision=None,
                context=genuine,
            ),
            "profile builder, no revision",
        ),
    ):
        with pytest.raises(KernelRefused) as unbound:
            call()
        assert unbound.value.reason == CONTEXT_REQUIRED, why

    # The exact pairing still builds: this is about disagreement, not strictness.
    assert configured_meeting_intel(context=genuine, revision=remote) is not None
    assert no_construction.calls, "the correctly bound call constructed nothing"


def test_the_whisper_branch_carries_the_context_too() -> None:
    """A slotted engine handle still proves admission (HS-131-09 speech leg)."""
    frozen = revision(rid="dep_whisper", destination="whisper-local", kind=WHISPER_KIND,
                      engine="mlx", endpoint="")
    context = context_for(frozen)

    engine = build_intel_for_revision(frozen, context=context)

    assert engine.revision is frozen
    assert dispatch_context_of(engine) is context


def test_the_named_legacy_marker_is_the_only_uncontextual_way_through(
    no_construction: Recorder,
) -> None:
    """The ONE remaining marker scope (the mesh receiver) buys no admission.

    HS-131-13 deleted `build_intel_for_target`, so the marker family is down to
    `commands/mesh_serve.py:MeshServeWorker._engine_for_run` — still a blocking
    finding, and still handed an engine that carries NO context, which is exactly
    what stops a marker-built engine from passing the dispatch-leg gate.
    """
    frozen = revision()
    engine = build_intel_for_revision(frozen, context=LEGACY_UNCONTEXTUAL)

    assert no_construction.calls
    assert dispatch_context_of(engine) is None, "a legacy finding must not look admitted"


# --------------------------------------------------------- the dictation seams


class Plan:
    """The frozen plan a dictation session opened with (only what `target` reads)."""

    def __init__(self, frozen: Any) -> None:
        self._frozen = frozen

    def primary(self, _capability: str) -> str:
        return self._frozen.id

    def deployment(self, revision_id: str) -> Any:
        return self._frozen if revision_id == self._frozen.id else None


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


# ------------------------------------------------------------------ the runner


@pytest.fixture
def rig(tmp_path: Path):
    db = Database(tmp_path / "context.db")
    db.profiles.upsert(profile_id="local", name="Local", kind="onDevice",
                       model_file="/model.gguf")
    frozen = capture_deployment_revision(db, resolve_inference_target(db, "local"))
    return db, _configure(db), frozen


class Adapter:
    def __init__(self) -> None:
        self.dispatches = 0

    def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> str:
        self.dispatches += 1
        return "result"

    def cancel(self) -> str:
        return "cancelled"


def invocation(frozen: Any, *, attempt: int = 1) -> InvocationRequest:
    payload = {"question": "private prompt"}
    return InvocationRequest(
        deployment_revision=frozen.id,
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=time.time() + 30, payload=payload, attempt_ordinal=attempt,
    )


def test_the_runner_issues_one_context_for_the_child_it_just_claimed(rig: Any) -> None:
    db, broker, frozen = rig
    seen: list[dict[str, Any]] = []

    def factory(value: Any, **kwargs: Any) -> Any:
        seen.append({"revision": value, **kwargs})
        return SimpleNamespace()

    runner = InferenceRunner(broker, db, engine_factory=factory, principal_provider=lambda: OWNER)
    adapter = Adapter()
    outcome = runner.invoke(invocation(frozen, attempt=2), adapter)

    assert outcome.outcome == "succeeded" and adapter.dispatches == 1
    # ONE calling convention: the injected factory is handed the same revision,
    # warrant, and context the real factory gets — no identity special case.
    assert len(seen) == 1
    assert seen[0]["revision"].id == frozen.id
    assert seen[0]["warrant"]["signature"]
    context = seen[0]["context"]
    assert context.operation_id == outcome.operation_id
    assert context.revision_id == frozen.id
    assert context.destination_id == frozen.destination_id
    assert context.attempt_ordinal == 2
    assert context.warrant_basis == seen[0]["warrant"]["signature"]
    # It is the live claimed child's own context, valid for exactly that work.
    assert require_dispatch_context(
        context, frozen, operation_id=outcome.operation_id, attempt_ordinal=2
    ) is context


def test_each_attempt_gets_its_own_context(rig: Any) -> None:
    db, broker, frozen = rig
    issued: list[Any] = []
    runner = InferenceRunner(
        broker, db,
        engine_factory=lambda _revision, **kwargs: issued.append(kwargs["context"]) or SimpleNamespace(),
        principal_provider=lambda: OWNER,
    )

    first = runner.invoke(invocation(frozen, attempt=1), Adapter())
    second = runner.invoke(invocation(frozen, attempt=2), Adapter())

    assert [context.attempt_ordinal for context in issued] == [1, 2]
    assert issued[0] is not issued[1]
    assert {context.operation_id for context in issued} == {
        first.operation_id, second.operation_id
    }


def test_an_engine_carrying_a_foreign_context_never_reaches_the_adapter(rig: Any) -> None:
    db, broker, frozen = rig
    foreign = context_for(revision(rid="dep_elsewhere"))
    adapter = Adapter()
    runner = InferenceRunner(
        broker, db,
        engine_factory=lambda _revision, **_kwargs: SimpleNamespace(_dispatch_context=foreign),
        principal_provider=lambda: OWNER,
    )

    outcome = runner.invoke(invocation(frozen), adapter)

    assert adapter.dispatches == 0, "a foreign context dispatched anyway"
    # One admitted child, one terminal refused receipt, zero physical attempts.
    assert outcome.outcome == "refused"
    assert broker.store.receipt(outcome.operation_id)["outcome"] == "refused"


def test_one_engine_may_serve_two_attempts_and_keeps_no_state_between_them(rig: Any) -> None:
    """A cached adapter is fine SEQUENTIALLY, and carries nothing away with it.

    Round 2: the binding is released as each attempt ends, so a reused engine
    cannot hand a later child an earlier child's operation, revision, or warrant
    basis. Between attempts it carries no context at all — which is also why the
    concurrent case (proved in the cardinality suite) refuses rather than
    silently borrowing a live one.
    """
    db, broker, frozen = rig
    reused = SimpleNamespace()
    seen: list[Any] = []
    runner = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kwargs: reused,
        principal_provider=lambda: OWNER,
    )

    class Watching(Adapter):
        def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> Any:
            seen.append(dispatch_context_of(engine))
            return super().dispatch(engine, payload, cancellation)

    first = runner.invoke(invocation(frozen, attempt=1), Watching())
    assert dispatch_context_of(reused) is None, "a finished attempt left its context behind"
    second = runner.invoke(invocation(frozen, attempt=2), Watching())

    assert first.outcome == second.outcome == "succeeded"
    # Each dispatch saw ITS OWN child, and nothing survives the second either.
    assert [context.operation_id for context in seen] == [
        first.operation_id, second.operation_id
    ]
    assert [context.attempt_ordinal for context in seen] == [1, 2]
    assert dispatch_context_of(reused) is None


def test_the_real_factory_runs_under_the_runners_context(rig: Any, monkeypatch: Any) -> None:
    """End to end: the default factory builds only because the runner admitted a child."""
    db, broker, frozen = rig
    built: list[Any] = []

    class Engine:
        def __init__(self, **kwargs: Any) -> None:
            built.append(kwargs)

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", Engine)
    runner = InferenceRunner(broker, db, principal_provider=lambda: OWNER)
    adapter = Adapter()

    outcome = runner.invoke(invocation(frozen), adapter)

    assert outcome.outcome == "succeeded" and built and adapter.dispatches == 1
    # And the same construction refuses outright without the runner behind it.
    with pytest.raises(KernelRefused) as refusal:
        build_intel_for_revision(frozen)
    assert refusal.value.reason == CONTEXT_REQUIRED
