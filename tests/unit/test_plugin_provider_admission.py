"""HS-131-14 — plugins receive admitted intelligence, or none at all.

Fifteen modules used to build their own provider: fourteen builtins through a
``_cached_provider`` fallback and the segment probe through the same uncontextual
factory. Each of those was a model invocation with no admitted child behind it —
no frozen revision, no cancellation seam, no receipt (Articles II.2, V.4,
XI.1-3).

What replaces them is one narrow handle, and this suite is its adversary. Three
layers:

1. **The matrix** — every one of the fifteen modules, over an admitted handle and
   over every way a handle can be absent, forged, revoked, or wrong. Each refusal
   asserts the exact name AND that the completion leaf was never reached.
2. **The host contract** — the handle is per-invocation. It lives on no host
   attribute and no plugin attribute, so a worker the host timed out and
   abandoned cannot observe or borrow the next child's authority, and cannot be
   represented as a success.
3. **The admitted path** — a real broker, real children, real receipts, real
   staged projections: two plugins under one parent are two children with two
   contexts and two terminal receipts; a provider failure earns a ``failed``
   receipt and materializes nothing; a dialect retry is a second admitted child
   and only the winner materializes.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, NamedTuple

import pytest

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.kernel.dispatch_context import bind_dispatch_context
from holdspeak.kernel.provider_signals import (
    ProviderCompatibilityRetry,
    ProviderIndeterminate,
)
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.action_owner_enforcer import ActionOwnerEnforcerPlugin
from holdspeak.plugins.builtin.adr_drafter import AdrDrafterPlugin
from holdspeak.plugins.builtin.customer_signal_extractor import CustomerSignalExtractorPlugin
from holdspeak.plugins.builtin.decision_announcement_drafter import (
    DecisionAnnouncementDrafterPlugin,
)
from holdspeak.plugins.builtin.decision_capture import DecisionCapturePlugin
from holdspeak.plugins.builtin.dependency_mapper import DependencyMapperPlugin
from holdspeak.plugins.builtin.incident_timeline import IncidentTimelinePlugin
from holdspeak.plugins.builtin.mermaid_architecture import MermaidArchitecturePlugin
from holdspeak.plugins.builtin.milestone_planner import MilestonePlannerPlugin
from holdspeak.plugins.builtin.requirements_extractor import RequirementsExtractorPlugin
from holdspeak.plugins.builtin.risk_heatmap import RiskHeatmapPlugin
from holdspeak.plugins.builtin.runbook_delta import RunbookDeltaPlugin
from holdspeak.plugins.builtin.scope_guard import ScopeGuardPlugin
from holdspeak.plugins.builtin.stakeholder_update_drafter import (
    StakeholderUpdateDrafterPlugin,
)
from holdspeak.plugins.host import (
    PLUGIN_LLM_ENGINE_NOT_INJECTABLE,
    PluginHost,
)
from holdspeak.plugins.intelligence import (
    IntelligenceConsumer,
    PLUGIN_DISPATCH_CANCELLED,
    PLUGIN_DISPATCH_CARDINALITY,
    PLUGIN_DISPATCH_CHAIN_CARDINALITY,
    PLUGIN_DISPATCH_CONTEXT_MISMATCH,
    PLUGIN_DISPATCH_ENGINE_INCOMPATIBLE,
    PLUGIN_DISPATCH_ENGINE_UNADMITTED,
    PLUGIN_DISPATCH_FORGED,
    PLUGIN_DISPATCH_KEY,
    PLUGIN_DISPATCH_RELEASED,
    PLUGIN_DISPATCH_REQUIRED,
    PluginDispatch,
    PluginDispatchRefused,
    PluginDispatchRevoked,
    PluginProviderFailure,
    _issue_plugin_dispatch,
)
from holdspeak.plugins.segment_probe import build_segment_probe
from tests.unit.plugin_dispatch_rig import (
    DeafEngine,
    StubEngine,
    admitted_dispatch,
    admitted_engine,
    unbind,
)

TRANSCRIPT = (
    "We decided to adopt the event sourced write path. Priya owns the migration "
    "plan by Friday. The staging deploy fell over and we rolled it back; the "
    "customer asked for an export button, and we will announce the change."
)

#: A response every parser either accepts or honestly rejects. The matrix asserts
#: AUTHORITY, not parsing — the fourteen per-plugin suites own the parsing.
CANNED = "```json\n{}\n```"


class Module(NamedTuple):
    """One intelligence-consuming module, driven through its own front door."""

    id: str
    #: Run one intel attempt with this handle (``None`` = none supplied at all).
    invoke: Callable[[Any], Any]
    #: The refusal a MISSING handle produces, or "" when the module degrades.
    missing_reason: str


def _builtin(plugin_cls: Any) -> Callable[[Any], Any]:
    def invoke(handle: Any) -> Any:
        plugin = plugin_cls()
        context: dict[str, Any] = {
            "transcript": TRANSCRIPT,
            "active_intents": ["architecture", "delivery"],
            "tags": ["api"],
            "project_name": "HoldSpeak",
            "transcript_segments": [
                {"text": TRANSCRIPT, "speaker": "Me", "start_time": 0.0, "end_time": 30.0}
            ],
        }
        if handle is not None:
            context[PLUGIN_DISPATCH_KEY] = handle
        return plugin.run(context)

    return invoke


def _probe(handle: Any) -> Any:
    probe = build_segment_probe(handle)
    return probe(TRANSCRIPT) if probe is not None else None


BUILTINS: tuple[tuple[str, Any], ...] = (
    ("action_owner_enforcer", ActionOwnerEnforcerPlugin),
    ("adr_drafter", AdrDrafterPlugin),
    ("customer_signal_extractor", CustomerSignalExtractorPlugin),
    ("decision_announcement_drafter", DecisionAnnouncementDrafterPlugin),
    ("decision_capture", DecisionCapturePlugin),
    ("dependency_mapper", DependencyMapperPlugin),
    ("incident_timeline", IncidentTimelinePlugin),
    ("mermaid_architecture", MermaidArchitecturePlugin),
    ("milestone_planner", MilestonePlannerPlugin),
    ("requirements_extractor", RequirementsExtractorPlugin),
    ("risk_heatmap", RiskHeatmapPlugin),
    ("runbook_delta", RunbookDeltaPlugin),
    ("scope_guard", ScopeGuardPlugin),
    ("stakeholder_update_drafter", StakeholderUpdateDrafterPlugin),
)

MODULES: tuple[Module, ...] = tuple(
    Module(plugin_id, _builtin(cls), PLUGIN_DISPATCH_REQUIRED)
    for plugin_id, cls in BUILTINS
) + (
    # The fifteenth module degrades instead of refusing: with no handle there is
    # no probe object at all, and the caller scores lexically.
    Module("segment_probe", _probe, ""),
)

MODULE_IDS = [module.id for module in MODULES]


def test_the_matrix_covers_every_intelligence_consuming_module() -> None:
    """Fifteen modules — the fourteen `_cached_provider` builtins plus the probe."""
    assert len(MODULES) == 15
    registered = PluginHost()
    llm_plugins = {
        plugin_id
        for plugin_id in register_builtin_plugins(registered)
        if "llm" in (getattr(registered.get_plugin(plugin_id), "required_capabilities", None) or [])
    }
    assert llm_plugins == {module.id for module in MODULES} - {"segment_probe"}


# ============================================================ 1. the matrix


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_an_admitted_handle_dispatches_on_exactly_that_child(module: Module) -> None:
    """The happy path: ONE completion, on the engine the runner built."""
    handle, engine, context = admitted_dispatch(CANNED)
    module.invoke(handle)
    assert len(engine.calls) == 1, f"{module.id}: expected exactly one completion"
    assert engine.calls[0]["messages"], f"{module.id}: dispatched an empty prompt"
    assert handle.operation_id == context.operation_id
    assert handle.revision_id == context.revision_id
    assert handle.destination_id == context.destination_id
    assert handle.attempt_ordinal == context.attempt_ordinal
    assert handle.warrant_basis == context.warrant_basis
    assert handle.calls == 1


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_no_handle_refuses_by_name_and_builds_nothing(module: Module) -> None:
    """The deleted fallback: with no handle there is no provider, full stop."""
    if not module.missing_reason:
        assert module.invoke(None) is None  # the probe degrades to lexical
        return
    with pytest.raises(PluginDispatchRefused) as refusal:
        module.invoke(None)
    assert refusal.value.reason == module.missing_reason
    assert refusal.value.plugin_id == module.id


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_a_forged_look_alike_refuses_before_the_leaf(module: Module) -> None:
    """A duck-typed handle is not a handle: shape is not admission."""

    class LookAlike:
        operation_id = "op_invented"
        revision_id = "dep_invented"
        calls = 0

        def chat(self, *_args: Any, **_kwargs: Any) -> str:  # pragma: no cover
            raise AssertionError("a look-alike must never dispatch")

    with pytest.raises(PluginDispatchRefused) as refusal:
        module.invoke(LookAlike())
    assert refusal.value.reason == PLUGIN_DISPATCH_FORGED


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_a_released_handle_refuses_before_the_leaf(module: Module) -> None:
    """The stale case the runner's own unbinding cannot cover on its own.

    A raw ``DispatchContext`` stays in the kernel's issued registry after the
    attempt ends, so "the context still validates" proves nothing about whether
    THIS run may still act. The host's release is the revocation.
    """
    handle, engine, _context = admitted_dispatch(CANNED)
    handle.release()
    with pytest.raises(PluginDispatchRevoked) as refusal:
        module.invoke(handle)
    assert refusal.value.reason == PLUGIN_DISPATCH_RELEASED
    assert engine.calls == []


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_a_handle_whose_attempt_ended_refuses_before_the_leaf(module: Module) -> None:
    """The runner unbinds the context as each attempt finishes; the handle notices."""
    handle, engine, context = admitted_dispatch(CANNED)
    unbind(engine, context)  # exactly what `InferenceRunner._attempt`'s finally does
    with pytest.raises(PluginDispatchRevoked) as refusal:
        module.invoke(handle)
    assert refusal.value.reason == PLUGIN_DISPATCH_CONTEXT_MISMATCH
    assert engine.calls == []


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_a_cross_child_engine_refuses_before_the_leaf(module: Module) -> None:
    """A second child rebound the shared engine: this handle is no longer its owner."""
    handle, engine, context = admitted_dispatch(CANNED)
    _other_handle, _other_engine, later = admitted_dispatch(CANNED, rid="dep_other")
    bind_dispatch_context(engine, later)  # the next child takes the engine
    with pytest.raises(PluginDispatchRevoked) as refusal:
        module.invoke(handle)
    assert refusal.value.reason == PLUGIN_DISPATCH_CONTEXT_MISMATCH
    assert engine.calls == []
    assert context is not later


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_a_cancelled_child_refuses_before_the_leaf(module: Module) -> None:
    """The child's own signal fences new physical work, not just its output."""
    cancellation = threading.Event()
    handle, engine, _context = admitted_dispatch(CANNED, cancellation=cancellation)
    cancellation.set()
    with pytest.raises(PluginDispatchRevoked) as refusal:
        module.invoke(handle)
    assert refusal.value.reason == PLUGIN_DISPATCH_CANCELLED
    assert engine.calls == []


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_a_provider_failure_is_the_childs_outcome_not_a_plugin_summary(
    module: Module,
) -> None:
    """Un-absorbable by `except Exception`, and carrying no provider text."""
    leak = "TRANSCRIPT-FRAGMENT-THAT-MUST-NOT-REACH-THE-JOURNAL"

    def boom(_messages: Any, **_kwargs: Any) -> str:
        raise RuntimeError(leak)

    handle, _engine, _context = admitted_dispatch(boom)
    with pytest.raises(PluginProviderFailure) as failure:
        module.invoke(handle)
    assert failure.value.reason == "RuntimeError"
    assert leak not in str(failure.value)


@pytest.mark.parametrize("module", MODULES, ids=MODULE_IDS)
def test_a_dialect_signal_reaches_the_runner_untouched(module: Module) -> None:
    """One physical attempt, one child: the follow-up is the RUNNER's to admit."""
    signal = ProviderCompatibilityRetry("max_completion_tokens")

    def dialect(_messages: Any, **_kwargs: Any) -> str:
        raise signal

    handle, _engine, _context = admitted_dispatch(dialect)
    with pytest.raises(ProviderCompatibilityRetry) as raised:
        module.invoke(handle)
    assert raised.value is signal, "the dialect signal was re-wrapped on the way out"


def test_an_engine_with_no_chat_seam_refuses_at_issue() -> None:
    """Incompatible: the refusal lands before the plugin runs, so no prompt exists."""
    engine, _context = admitted_engine(engine=DeafEngine())
    with pytest.raises(PluginDispatchRefused) as refusal:
        _issue_plugin_dispatch(engine=engine, plugin_id="decision_capture")
    assert refusal.value.reason == PLUGIN_DISPATCH_ENGINE_INCOMPATIBLE


def test_an_unadmitted_engine_cannot_produce_a_handle_at_all() -> None:
    """No context bound = no admitted child = no handle to hand a plugin."""
    with pytest.raises(PluginDispatchRefused) as refusal:
        _issue_plugin_dispatch(engine=StubEngine(CANNED), plugin_id="decision_capture")
    assert refusal.value.reason == PLUGIN_DISPATCH_ENGINE_UNADMITTED


def test_the_handle_cannot_be_constructed_outside_the_mint() -> None:
    """Opaque structurally, not by convention: the mint is the only way in."""
    _handle, engine, context = admitted_dispatch(CANNED)
    with pytest.raises(PluginDispatchRefused) as refusal:
        PluginDispatch(engine=engine, context=context, cancellation=None)
    assert refusal.value.reason == PLUGIN_DISPATCH_FORGED


# ==================================================== 2. the host's contract


class _Deterministic:
    """A plugin that needs no model: it must keep working with no handle."""

    id = "deterministic_probe"
    version = "1.0.0"
    kind = "synthesizer"
    execution_mode = "inline"
    required_capabilities: list[str] = []

    def __init__(self) -> None:
        self.runs = 0

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        self.runs += 1
        assert PLUGIN_DISPATCH_KEY not in context, "a non-llm plugin saw the handle"
        return {"summary": f"{len(str(context.get('transcript') or ''))} chars"}


class _IgnoresTheHandle:
    """An `llm` plugin that never asks for the model: it simply does none."""

    id = "ignores_the_handle"
    version = "1.0.0"
    required_capabilities = ["llm"]

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        assert PLUGIN_DISPATCH_KEY in context, "the handle was not delivered"
        return {"summary": "no model work"}


def _host(*plugins: Any, timeout: float = 5.0) -> PluginHost:
    host = PluginHost(default_timeout_seconds=timeout, enabled_capabilities={"llm"})
    for plugin in plugins:
        host.register(plugin)
    return host


def _execute(host: PluginHost, plugin_id: str, **kwargs: Any) -> Any:
    # `defer_heavy=False`: every builtin declares `execution_mode="deferred"`, and
    # the admitted path always runs the chain inline under its child.
    kwargs.setdefault("defer_heavy", False)
    return host.execute(
        plugin_id,
        context={"transcript": TRANSCRIPT},
        meeting_id="m-1",
        window_id="m-1:full",
        transcript_hash="h-1",
        **kwargs,
    )


def test_a_deterministic_plugin_runs_with_no_handle_and_no_child() -> None:
    plugin = _Deterministic()
    result = _execute(_host(plugin), plugin.id)
    assert result.status == "success"
    assert plugin.runs == 1


def test_an_llm_plugin_with_no_handle_errors_by_name_and_builds_nothing() -> None:
    host = _host(DecisionCapturePlugin())
    result = _execute(host, "decision_capture")
    assert result.status == "error"
    assert PLUGIN_DISPATCH_REQUIRED in str(result.error)


def test_an_llm_plugin_that_ignores_the_handle_simply_does_no_model_work() -> None:
    """The handle is DELIVERED, not installed — and there is no fallback to take."""
    host = _host(_IgnoresTheHandle())
    dispatch, engine, _context = admitted_dispatch(CANNED)
    result = _execute(host, "ignores_the_handle", dispatch=dispatch)
    assert result.status == "success"
    assert engine.calls == []


def test_the_handle_lives_on_the_invocation_and_nowhere_else() -> None:
    """No host slot, no plugin slot: there is nothing for a later run to borrow."""
    plugin = DecisionCapturePlugin()
    host = _host(plugin)
    dispatch, engine, _context = admitted_dispatch(CANNED)
    caller_context = {"transcript": TRANSCRIPT}

    host.execute(
        "decision_capture", context=caller_context, meeting_id="m", window_id="w",
        transcript_hash="h", dispatch=dispatch, defer_heavy=False,
    )

    assert engine.calls, "the admitted run never reached the engine"
    assert not hasattr(plugin, "plugin_dispatch")
    assert not hasattr(plugin, "_cached_provider")
    assert not hasattr(host, "_llm_engine")
    assert not hasattr(host, "_dispatch")
    assert PLUGIN_DISPATCH_KEY not in caller_context

    # ...and the NEXT run, with no handle, refuses instead of reusing the last one.
    result = host.execute(
        "decision_capture", context={"transcript": TRANSCRIPT}, meeting_id="m",
        window_id="w2", transcript_hash="h2", defer_heavy=False,
    )
    assert result.status == "error"
    assert PLUGIN_DISPATCH_REQUIRED in str(result.error)
    assert len(engine.calls) == 1


def test_a_handle_smuggled_in_the_caller_context_is_stripped() -> None:
    """Authority is the host's to grant: a caller cannot supply its own."""
    host = _host(DecisionCapturePlugin())
    stolen, engine, _context = admitted_dispatch(CANNED)
    result = host.execute(
        "decision_capture",
        context={"transcript": TRANSCRIPT, PLUGIN_DISPATCH_KEY: stolen},
        meeting_id="m", window_id="w", transcript_hash="h", defer_heavy=False,
    )
    assert result.status == "error"
    assert PLUGIN_DISPATCH_REQUIRED in str(result.error)
    assert engine.calls == []


def test_a_timed_out_worker_is_indeterminate_and_cannot_borrow_a_later_child() -> None:
    """The race the old ambient slots lost.

    The host abandons a worker on timeout but cannot stop it. With a physical
    attempt already in flight the outcome is UNKNOWN — never a `timeout` record an
    admitted child could close `succeeded` over — and the abandoned worker, holding
    only its own released handle, can neither complete late nor see the next
    child's engine.
    """
    started = threading.Event()
    release = threading.Event()
    late: dict[str, Any] = {}

    def slow(_messages: Any, **_kwargs: Any) -> str:
        started.set()
        release.wait(5.0)
        return CANNED

    class _Slow:
        id = "slow_llm"
        version = "1.0.0"
        required_capabilities = ["llm"]
        intel_temperature = 0.2
        intel_max_tokens = 64

        def _call_intel(self, messages: Any, context: Any) -> str:  # noqa: D401
            from holdspeak.plugins.intelligence import (
                plugin_dispatch_of,
                require_plugin_dispatch,
            )

            handle = require_plugin_dispatch(plugin_dispatch_of(context), plugin_id=self.id)
            first = handle.chat(messages, temperature=0.2, max_tokens=64)
            # The abandoned worker keeps going and tries a SECOND completion.
            try:
                handle.chat(messages, temperature=0.2, max_tokens=64)
            except BaseException as exc:  # noqa: BLE001 - recording the refusal IS the test
                late["reason"] = getattr(exc, "reason", "")
                late["handle"] = handle
            return first

        def run(self, context: dict[str, Any]) -> dict[str, Any]:
            return {"summary": self._call_intel([{"role": "user", "content": "x"}], context)}

    host = _host(_Slow(), timeout=0.05)
    engine, _context = admitted_engine(engine=StubEngine(slow))
    with host.issued_dispatch(engine) as dispatch:
        with pytest.raises(ProviderIndeterminate):
            _execute(host, "slow_llm", dispatch=dispatch, timeout_seconds=0.05)
        assert started.is_set()

    # The dispatch is released as the block unwinds; now let the worker finish.
    release.set()
    for _ in range(200):
        if "reason" in late:
            break
        time.sleep(0.01)
    assert late.get("reason") == PLUGIN_DISPATCH_RELEASED, late
    assert dispatch.released

    # A LATER child's engine is unreachable from the abandoned worker's handle.
    later_engine, _later_context = admitted_engine(CANNED, rid="dep_later")
    with pytest.raises(PluginDispatchRevoked):
        late["handle"].chat([{"role": "user", "content": "x"}])
    assert later_engine.calls == []


def test_a_timeout_that_beats_the_claim_records_a_timeout_and_sends_nothing(
    monkeypatch,
) -> None:
    """The host's timeout ELECTION, on the exact timeline that used to lose it.

    Old shape: `if dispatch.calls: ...` read the handle, and the release came
    later, when `issued_dispatch` unwound. Between those two the abandoned worker
    could claim — so the host recorded an ordinary `timeout` ("nothing physical
    happened") and the request went out anyway, under a run the host had already
    given up on.

    The timeline here is forced, not hoped for: the worker parks AFTER
    `_validated_engine` and BEFORE the atomic claim; the host times out and
    elects; only then is the worker unparked. One atomic `release()` decides both
    facts, so an ordinary `timeout` verdict is a PROMISE that no request will ever
    be sent, and the worker's claim refuses.
    """
    parked = threading.Event()
    proceed = threading.Event()
    refused = threading.Event()
    late: dict[str, Any] = {}

    real_validate = PluginDispatch._validated_engine

    def paused_validate(self: Any, plugin_id: str = "") -> Any:
        engine_arg = real_validate(self, plugin_id)
        parked.set()
        assert proceed.wait(5.0), "the barrier never opened"
        return engine_arg

    monkeypatch.setattr(PluginDispatch, "_validated_engine", paused_validate)

    class _ParksBeforeTheClaim(IntelligenceConsumer):
        id = "parks_before_claim"
        version = "1.0.0"
        required_capabilities = ["llm"]
        intel_temperature = 0.2
        intel_max_tokens = 64

        def run(self, context: dict[str, Any]) -> dict[str, Any]:
            try:
                return {"summary": self._call_intel([{"role": "user", "content": "x"}], context)}
            except PluginDispatchRevoked as refusal:
                late["reason"] = refusal.reason
                raise
            finally:
                refused.set()

    host = _host(_ParksBeforeTheClaim(), timeout=0.05)
    engine, _context = admitted_engine(CANNED)

    with host.issued_dispatch(engine) as dispatch:
        # The host gives up while the worker is parked in the window.
        result = _execute(host, "parks_before_claim", dispatch=dispatch, timeout_seconds=0.05)
        assert parked.is_set(), "the worker never reached the window"
        # The election said UNCLAIMED, so an ordinary timeout is the honest record.
        assert result.status == "timeout"

        # Now unpark, still INSIDE the block, so the contextmanager's release
        # cannot be what saves us — only the election can.
        proceed.set()
        assert refused.wait(5.0), "the abandoned worker never finished"

    # THE payoff: the `timeout` record above was a promise, and it held.
    assert engine.calls == [], "a request was sent after the host recorded a timeout"
    assert late.get("reason") == PLUGIN_DISPATCH_RELEASED, late
    assert dispatch.calls == 0
    assert dispatch.released
    # The repeat release from `issued_dispatch` reports the SAME verdict.
    assert dispatch.release() is False


# ------------------------------------------------- cardinality: one handle, one call


def test_a_second_completion_on_one_handle_refuses_before_the_leaf() -> None:
    """A handle names ONE child, ONE ordinal, ONE receipt — so ONE attempt.

    A plugin that asked twice would perform two physical attempts under a single
    terminal receipt, and the journal would record one. That is the exact
    cardinality Article XI.2 forbids, so the second ask never reaches a provider.
    """
    plugin = _DoubleCaller()
    handle, engine, _context = admitted_dispatch(CANNED)
    with pytest.raises(PluginDispatchRevoked) as refusal:
        plugin.run({PLUGIN_DISPATCH_KEY: handle})
    assert refusal.value.reason == PLUGIN_DISPATCH_CARDINALITY
    assert plugin.second_refusal == PLUGIN_DISPATCH_CARDINALITY
    assert len(engine.calls) == 1, "a second physical attempt reached the provider"
    assert handle.calls == 1 and handle.spent


def test_concurrent_calls_on_one_handle_yield_one_leaf_and_one_refusal() -> None:
    """The claim is atomic: two threads cannot both pass "not spent yet".

    A flag read followed by a separate write is a race a scheduler wins about as
    often as it likes; this asserts the invariant that makes the count honest —
    exactly one physical attempt, exactly one named refusal, whoever wins.
    """
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def slow_leaf(_messages: Any, **_kwargs: Any) -> str:
        time.sleep(0.02)  # widen the window between claim and return
        return CANNED

    handle, engine, _context = admitted_dispatch(slow_leaf)

    def ask() -> None:
        barrier.wait(5.0)
        try:
            handle.chat([{"role": "user", "content": "x"}], plugin_id="racer")
        except PluginDispatchRevoked as refusal:
            with lock:
                outcomes.append(refusal.reason)
        else:
            with lock:
                outcomes.append("completed")

    threads = [threading.Thread(target=ask) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10.0)

    assert sorted(outcomes) == sorted([PLUGIN_DISPATCH_CARDINALITY, "completed"]), outcomes
    assert len(engine.calls) == 1
    assert handle.calls == 1


def test_a_release_between_validation_and_the_claim_still_sends_nothing(
    monkeypatch,
) -> None:
    """The release-vs-claim race, made deterministic and then closed.

    Validating `_released` and claiming separately leaves a window the host's
    timeout wins: release lands between the two and a physical request goes out
    under authority that was already withdrawn. This parks a caller EXACTLY in
    that window, revokes the handle from another thread, and then lets it
    proceed — the claim, which re-reads revocation under the lock `release` also
    takes, refuses and no request is ever sent.
    """
    parked = threading.Event()
    proceed = threading.Event()
    outcome: dict[str, Any] = {}

    real_validate = PluginDispatch._validated_engine

    def paused_validate(self: Any, plugin_id: str = "") -> Any:
        engine = real_validate(self, plugin_id)
        parked.set()
        assert proceed.wait(5.0), "the barrier never opened"
        return engine

    monkeypatch.setattr(PluginDispatch, "_validated_engine", paused_validate)

    handle, engine, _context = admitted_dispatch(CANNED)

    def ask() -> None:
        try:
            handle.chat([{"role": "user", "content": "x"}], plugin_id="racer")
        except PluginDispatchRevoked as refusal:
            outcome["reason"] = refusal.reason
        else:
            outcome["reason"] = "completed"

    caller = threading.Thread(target=ask)
    caller.start()
    assert parked.wait(5.0), "the caller never reached the window"

    # The host times the worker out and revokes, mid-window.
    started_at = time.monotonic()
    handle.release()
    assert time.monotonic() - started_at < 1.0, "release blocked on the caller"

    proceed.set()
    caller.join(10.0)

    assert outcome["reason"] == PLUGIN_DISPATCH_RELEASED, outcome
    assert engine.calls == [], "a request was sent after the handle was revoked"
    assert handle.calls == 0


def test_release_during_an_in_flight_call_never_waits_and_authorizes_nothing_more(
    monkeypatch,
) -> None:
    """A revocation that arrives too late cannot un-send — but ends the handle.

    The one attempt is already physical, so its outcome is indeterminate and the
    projection stager fences it. What must still hold: `release` returns
    immediately (the host thread is not parked behind a model), and the handle
    never returns to LIVE, so nothing further is authorized.
    """
    in_flight = threading.Event()
    finish = threading.Event()
    calls: list[str] = []

    def slow_leaf(_messages: Any, **_kwargs: Any) -> str:
        in_flight.set()
        assert finish.wait(5.0)
        calls.append("served")
        return CANNED

    handle, engine, _context = admitted_dispatch(slow_leaf)

    worker = threading.Thread(
        target=lambda: handle.chat([{"role": "user", "content": "x"}], plugin_id="slow")
    )
    worker.start()
    assert in_flight.wait(5.0)
    assert handle.in_flight

    started_at = time.monotonic()
    handle.release()
    elapsed = time.monotonic() - started_at
    assert elapsed < 1.0, f"release waited {elapsed:.2f}s on a provider"
    assert not finish.is_set(), "the provider had not returned yet"

    finish.set()
    worker.join(10.0)
    assert calls == ["served"]
    assert len(engine.calls) == 1

    # The in-flight attempt settled, and the handle is finished either way.
    assert not handle.in_flight
    with pytest.raises(PluginDispatchRevoked) as refusal:
        handle.chat([{"role": "user", "content": "x"}], plugin_id="slow")
    assert refusal.value.reason == PLUGIN_DISPATCH_RELEASED
    assert len(engine.calls) == 1


def test_a_handle_offered_to_a_multi_plugin_chain_refuses_before_any_plugin_runs() -> None:
    """An admitted handle belongs to one plugin child, never to a chain.

    Sharing one across a chain would give every plugin in it the same child's
    revision, ordinal, and receipt — and, since the handle is single-use, would
    silently starve every plugin after the first. It fails closed instead, before
    the first plugin runs.
    """
    host = _host(DecisionCapturePlugin(), ScopeGuardPlugin())
    handle, engine, _context = admitted_dispatch(CANNED)
    with pytest.raises(PluginDispatchRefused) as refusal:
        host.execute_chain(
            ["decision_capture", "scope_guard"],
            context={"transcript": TRANSCRIPT},
            meeting_id="m", window_id="w", transcript_hash="h",
            defer_heavy=False, dispatch=handle,
        )
    assert refusal.value.reason == PLUGIN_DISPATCH_CHAIN_CARDINALITY
    assert engine.calls == []
    assert handle.calls == 0
    # An EMPTY chain is refused for the same reason: a handle with no child to
    # spend it on is an admitted attempt nobody ever makes.
    with pytest.raises(PluginDispatchRefused) as empty:
        host.execute_chain(
            [], context={"transcript": TRANSCRIPT},
            meeting_id="m", window_id="w", transcript_hash="h",
            defer_heavy=False, dispatch=handle,
        )
    assert empty.value.reason == PLUGIN_DISPATCH_CHAIN_CARDINALITY


def test_a_one_plugin_chain_with_a_handle_is_the_admitted_shape() -> None:
    """What the admitted caller actually passes: one child, one plugin, one call."""
    host = _host(DecisionCapturePlugin())
    handle, engine, _context = admitted_dispatch(CANNED)
    results = host.execute_chain(
        ["decision_capture"],
        context={"transcript": TRANSCRIPT},
        meeting_id="m", window_id="w", transcript_hash="h",
        defer_heavy=False, dispatch=handle,
    )
    assert [result.status for result in results] == ["success"]
    assert len(engine.calls) == 1
    assert engine.calls[0]["max_tokens"] == DecisionCapturePlugin.intel_max_tokens


def test_an_unadmitted_chain_still_runs_every_deterministic_plugin() -> None:
    """The chain gate is about HANDLES, not about chains.

    A caller with no admitted handle keeps running its whole chain exactly as
    before — deterministic plugins do no model work, so there is no cardinality
    to protect.
    """
    first, second = _Deterministic(), _Deterministic()
    second.id = "deterministic_probe_2"
    host = _host(first, second)
    results = host.execute_chain(
        ["deterministic_probe", "deterministic_probe_2"],
        context={"transcript": TRANSCRIPT},
        meeting_id="m", window_id="w", transcript_hash="h",
        defer_heavy=False,
    )
    assert [result.status for result in results] == ["success", "success"]
    assert (first.runs, second.runs) == (1, 1)


# ================================================== 3. the admitted path


class _AdmittedEngine:
    """The engine the runner builds for each claimed child."""

    active_provider = "local"

    def __init__(self, respond: Any = CANNED) -> None:
        self._respond = respond
        self.completions: list[dict[str, Any]] = []
        self.contexts: list[Any] = []

    def analyze(self, transcript: str, *, stream: bool = False) -> Any:
        from holdspeak.intel import IntelResult

        return IntelResult(topics=["t"], action_items=[], summary="s", raw_response="{}")

    def generate_title(self, transcript: str) -> str:
        return "Title"

    def _chat_completion_text(self, messages: Any, *, temperature: float, max_tokens: int) -> str:
        from holdspeak.kernel.dispatch_context import dispatch_context_of

        self.contexts.append(dispatch_context_of(self))
        self.completions.append({"messages": messages, "max_tokens": max_tokens})
        if callable(self._respond):
            return self._respond(messages, temperature=temperature, max_tokens=max_tokens)
        return self._respond


class _Cfg:
    class meeting:  # noqa: N801 - config shape
        intel_provider = "local"
        intel_profile_id = None
        intel_cloud_model = "gpt-5-mini"
        intel_cloud_api_key_env = "OPENAI_API_KEY"
        intel_cloud_base_url = None
        intel_cloud_reasoning_effort = None
        intel_cloud_store = False
        intel_realtime_model = None
        intel_enabled = True
        intel_deferred_enabled = True
        disabled_plugins: list[str] = []
        intent_router_enabled = True
        mir_profile = "balanced"


class _Route:
    def __init__(self, chain: tuple[str, ...]) -> None:
        self._chain = list(chain)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": "balanced",
            "threshold": 0.5,
            "active_intents": ["architecture"],
            "intent_scores": {"architecture": 0.9},
            "plugin_chain": list(self._chain),
        }


def _meeting(db: Any, meeting_id: str) -> MeetingState:
    from datetime import datetime

    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 12, 9, 0, 0),
        ended_at=datetime(2026, 8, 12, 9, 30, 0),
        title="Write path",
        tags=["architecture"],
        segments=[
            TranscriptSegment(text=TRANSCRIPT, speaker="Me", start_time=0.0, end_time=30.0)
        ],
    )
    db.meetings.save_meeting(state)
    return state


def _admitted_rig(tmp_path: Path, monkeypatch, chain: tuple[str, ...], engine: Any):
    db = Database(tmp_path / "admitted.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    broker = _configure(db)
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: _Cfg))
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript",
        lambda **kwargs: _Route(chain),
    )
    host = PluginHost(default_timeout_seconds=10.0, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    return db, broker, host


def _job(db: Any, broker: Any, meeting_id: str, plugins: tuple[str, ...]) -> Any:
    from holdspeak.meeting_session.deferred_admission import DeferredIntelJob

    return DeferredIntelJob.admit(
        db,
        meeting_id=meeting_id,
        attempt=1,
        transcript_hash="h-1",
        plugin_ids=plugins,
        meeting_config=_Cfg.meeting,
        broker=broker,
    )


def _rows(db: Any, table: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table}")]


def _children(db: Any, parent: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """SELECT o.operation_id, o.native_id, r.outcome
                   FROM kernel_operations o
                   LEFT JOIN kernel_receipts r ON r.operation_id = o.operation_id
                   WHERE o.parent_operation_id=? AND o.name='inference.invoke'
                   ORDER BY o.operation_id""",
                (parent,),
            )
        ]


@pytest.mark.parametrize("chain", [("decision_capture", "scope_guard")])
def test_two_admitted_plugins_are_two_children_two_contexts_two_receipts(
    tmp_path: Path, monkeypatch, chain: tuple[str, ...]
) -> None:
    """Cardinality and provenance, end to end under one deferred job parent."""
    from holdspeak.meeting_plugins import run_meeting_plugin_chain

    engine = _AdmittedEngine()
    db, broker, host = _admitted_rig(tmp_path, monkeypatch, chain, engine)
    state = _meeting(db, "m-two")
    job = _job(db, broker, state.id, chain)

    summary = run_meeting_plugin_chain(db, state, host=host, admission=job)
    job.close()

    assert set(summary["plugin_statuses"]) == set(chain)
    # One physical completion per plugin, each under its OWN dispatch context.
    assert len(engine.completions) == 2
    assert len(engine.contexts) == 2
    assert engine.contexts[0] is not None and engine.contexts[1] is not None
    assert engine.contexts[0] is not engine.contexts[1]
    assert engine.contexts[0].operation_id != engine.contexts[1].operation_id

    children = _children(db, job.parent.operation_id)
    assert len(children) == 2, children
    assert {child["outcome"] for child in children} == {"succeeded"}
    assert len({child["operation_id"] for child in children}) == 2
    # Every child dispatched on the plan's frozen revision for its own capability.
    assert {context.revision_id for context in engine.contexts} == {
        job.plan.primary(f"plugin:{plugin_id}") for plugin_id in chain
    }
    # ...and the staged projections became the real rows.
    runs = {row["plugin_id"] for row in _rows(db, "plugin_runs")}
    assert runs == set(chain)


class _LegacyHost:
    """A host from before the handle: it has no way to be given the child's engine."""

    def __init__(self) -> None:
        self.executed: list[str] = []

    def list_plugins(self) -> list[str]:
        return ["decision_capture"]

    def execute_chain(self, chain: list[str], **_kwargs: Any) -> list[Any]:  # pragma: no cover
        self.executed.extend(chain)
        raise AssertionError("a host with no dispatch seam must refuse before running")


def test_a_host_that_cannot_be_given_the_handle_is_refused_by_name(
    tmp_path: Path, monkeypatch
) -> None:
    """HS-131-08's refusal, retargeted at the seam that is actually missing.

    An admitted child names ONE deployment revision. A host that cannot be handed
    that child's engine would run plugins against something else entirely, so the
    chain refuses by name and the plugin stays honestly unresolved.
    """
    from holdspeak.meeting_plugins import run_meeting_plugin_chain

    chain = ("decision_capture",)
    engine = _AdmittedEngine()
    db, broker, _host = _admitted_rig(tmp_path, monkeypatch, chain, engine)
    legacy = _LegacyHost()
    state = _meeting(db, "m-legacy")
    job = _job(db, broker, state.id, chain)

    summary = run_meeting_plugin_chain(db, state, host=legacy, admission=job)
    job.close()

    assert summary["plugin_statuses"]["decision_capture"] == "error"
    assert legacy.executed == [], "the chain ran on a host that could not be admitted"
    assert engine.completions == []
    # The refusal happens INSIDE the child's dispatch, so the child closes
    # `failed` and nothing it might have produced becomes durable.
    children = _children(db, job.parent.operation_id)
    assert [child["outcome"] for child in children] == ["failed"], children
    assert _rows(db, "plugin_runs") == []
    assert db.plugins.list_artifacts(state.id) == []
    assert not hasattr(legacy, "issued_dispatch")
    from holdspeak.plugins.host import PluginEngineNotInjectable

    assert PluginEngineNotInjectable("x").reason == PLUGIN_LLM_ENGINE_NOT_INJECTABLE


def test_a_plugin_provider_failure_earns_a_failed_receipt_and_materializes_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    """The dishonest case: a plugin's `{status: error}` must not close `succeeded`."""
    from holdspeak.meeting_plugins import run_meeting_plugin_chain

    def boom(_messages: Any, **_kwargs: Any) -> str:
        raise RuntimeError("endpoint down")

    chain = ("decision_capture",)
    engine = _AdmittedEngine(boom)
    db, broker, host = _admitted_rig(tmp_path, monkeypatch, chain, engine)
    state = _meeting(db, "m-fail")
    job = _job(db, broker, state.id, chain)

    summary = run_meeting_plugin_chain(db, state, host=host, admission=job)
    job.close()

    assert summary["plugin_statuses"]["decision_capture"] == "error"
    children = _children(db, job.parent.operation_id)
    assert [child["outcome"] for child in children] == ["failed"], children
    assert _rows(db, "plugin_runs") == []
    assert db.plugins.list_artifacts(state.id) == []
    staged = [row for row in _rows(db, "kernel_projection_stages") if row["state"] == "PUBLISHED"]
    assert staged == []


def test_a_dialect_retry_is_a_second_child_and_only_the_winner_materializes(
    tmp_path: Path, monkeypatch
) -> None:
    """failed r1 + succeeded r2, one physical attempt each, one surviving row."""
    from holdspeak.meeting_plugins import run_meeting_plugin_chain

    attempts: list[int] = []

    def dialect_once(_messages: Any, **_kwargs: Any) -> str:
        attempts.append(len(attempts) + 1)
        if len(attempts) == 1:
            raise ProviderCompatibilityRetry("max_completion_tokens")
        return (
            "```json\n"
            '{"decisions": [{"decision": "Adopt event sourcing", "rationale": null}],'
            ' "open_questions": []}\n```'
        )

    chain = ("decision_capture",)
    engine = _AdmittedEngine(dialect_once)
    db, broker, host = _admitted_rig(tmp_path, monkeypatch, chain, engine)
    state = _meeting(db, "m-retry")
    job = _job(db, broker, state.id, chain)

    issued: list[Any] = []
    real_issue = host.issued_dispatch

    @contextmanager
    def spy(engine_arg: Any, cancellation: Any = None) -> Any:
        with real_issue(engine_arg, cancellation) as handle:
            issued.append(handle)
            yield handle

    monkeypatch.setattr(host, "issued_dispatch", spy)

    summary = run_meeting_plugin_chain(db, state, host=host, admission=job)
    job.close()

    assert attempts == [1, 2], "the retry must be a SECOND physical attempt"
    # Each attempt got its OWN single-use handle. A reused handle would have
    # refused `plugin_dispatch_cardinality` and the retry would never have run.
    assert len(issued) == 2
    assert issued[0] is not issued[1]
    assert [handle.calls for handle in issued] == [1, 1]
    assert all(handle.released for handle in issued)
    children = _children(db, job.parent.operation_id)
    assert sorted(child["outcome"] for child in children) == ["failed", "succeeded"]
    retry = [child for child in children if str(child["native_id"]).endswith("_r2")]
    assert len(retry) == 1 and retry[0]["outcome"] == "succeeded"
    # Two distinct contexts, two distinct attempt ordinals: no hidden second call.
    assert len(engine.contexts) == 2
    assert engine.contexts[0] is not engine.contexts[1]
    assert [context.attempt_ordinal for context in engine.contexts] == [1, 2]
    # Only the winner's projection became a row.
    runs = _rows(db, "plugin_runs")
    assert [row["plugin_id"] for row in runs] == ["decision_capture"]
    assert summary["plugin_statuses"]["decision_capture"] == "success"


class _DoubleCaller(IntelligenceConsumer):
    """A plugin that asks twice — the shape that proves the signal is IN the handle."""

    id = "double_caller"
    version = "1.0.0"
    kind = "synthesizer"
    execution_mode = "deferred"
    required_capabilities = ["llm"]
    intel_temperature = 0.2
    intel_max_tokens = 64

    def __init__(self) -> None:
        self.second_refusal = ""

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        messages = [{"role": "user", "content": "x"}]
        first = self._call_intel(messages, context)
        try:
            self._call_intel(messages, context)
        except PluginDispatchRevoked as refusal:
            self.second_refusal = refusal.reason
            raise
        return {"summary": first}


def test_the_childs_cancellation_signal_is_inside_the_plugins_handle(
    tmp_path: Path, monkeypatch
) -> None:
    """Cancellation fences the plugin's NEXT completion, not just its output.

    `DeferredIntelJob.plugin` hands the child's own cancellation event down to the
    host, which mints the handle over it. Once that event is set — the runner
    acknowledging a cancel — the plugin cannot start further physical work, and
    nothing it produced is published.
    """
    from holdspeak.meeting_plugins import run_meeting_plugin_chain

    seen: dict[str, Any] = {}

    def cancel_after_first(_messages: Any, **_kwargs: Any) -> str:
        # The child is cancelled WHILE its first completion is in flight.
        seen["cancellation"].set()
        return CANNED

    chain = ("double_caller",)
    engine = _AdmittedEngine(cancel_after_first)
    db, broker, host = _admitted_rig(tmp_path, monkeypatch, chain, engine)
    plugin = _DoubleCaller()
    host.register(plugin)

    real_issue = host.issued_dispatch

    def spy(engine_arg: Any, cancellation: Any = None) -> Any:
        seen["cancellation"] = cancellation
        return real_issue(engine_arg, cancellation)

    monkeypatch.setattr(host, "issued_dispatch", spy)

    state = _meeting(db, "m-cancel")
    job = _job(db, broker, state.id, chain)
    run_meeting_plugin_chain(db, state, host=host, admission=job)
    job.close("cancelled")

    assert isinstance(seen.get("cancellation"), threading.Event)
    assert seen["cancellation"].is_set()
    assert plugin.second_refusal == PLUGIN_DISPATCH_CANCELLED
    assert len(engine.completions) == 1, "a cancelled child started a second attempt"
    assert _rows(db, "plugin_runs") == []
    assert db.plugins.list_artifacts(state.id) == []


# ============================================ 4. the deleted door stays deleted


def test_no_plugin_module_references_a_provider_construction() -> None:
    """The structural half: the fallback family cannot come back by hand.

    The executable census (`test_one_path_census.py`) fails on the CALL; this
    fails on the shape — a cached provider attribute, the deleted factory, or the
    completion leaf named anywhere under `holdspeak/plugins/**` outside the one
    admitted seam.
    """
    import ast

    root = Path(__file__).resolve().parents[2] / "holdspeak/plugins"
    seam = root / "intelligence.py"
    # Prose may NAME the deleted door (the history is worth writing down); code may
    # not USE it, so this reads the AST rather than the text.
    forbidden = {"_cached_provider", "build_configured_meeting_intel"}
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        banned = forbidden if path == seam else forbidden | {"_chat_completion_text"}
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            name = (
                node.attr if isinstance(node, ast.Attribute)
                else node.id if isinstance(node, ast.Name)
                else node.name if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                else node.value if isinstance(node, ast.Constant) and isinstance(node.value, str)
                and node.value in banned
                else None
            )
            if isinstance(name, str) and name in banned:
                offenders.append(f"{path.relative_to(root)}:{getattr(node, 'lineno', 0)} {name}")
        for alias in (
            entry
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for entry in node.names
        ):
            if alias.name.split(".")[-1] in banned:
                offenders.append(f"{path.relative_to(root)}: imports {alias.name}")
    assert offenders == [], offenders
