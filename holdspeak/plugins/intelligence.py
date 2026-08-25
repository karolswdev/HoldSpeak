"""The ONE seam through which a plugin reaches intelligence (HS-131-14).

Plugins CONSUME intelligence; they never construct providers. Until this story
every LLM-backed builtin carried a ``_cached_provider`` fallback: with no engine
injected it called ``build_configured_meeting_intel()``, re-read mutable
configuration, and dispatched ``_chat_completion_text`` itself. That is a side
door under Constitution Articles II.2 (a primitive exposes a contract; it does
not grow its own), V.4 (reach never outruns consent), and XI.1-3 (every model
invocation is admitted once, against an immutable payload/target/authority).

What replaces it is deliberately narrow, and deliberately NOT a slot:

* :class:`PluginDispatch` is a HANDLE, not a provider. The host issues one per
  admitted plugin run, over the exact engine
  :class:`~holdspeak.kernel.inference_runner.InferenceRunner` built for the child
  it just claimed, and it captures that child's opaque
  :class:`~holdspeak.kernel.dispatch_context.DispatchContext` plus the runner's
  cancellation signal.
* It travels as an ARGUMENT into one worker invocation — under
  :data:`PLUGIN_DISPATCH_KEY` in that invocation's own context copy — never on
  the host and never on the plugin. The previous design mutated
  ``host._llm_engine`` and ``plugin._cached_provider`` around each run, which the
  host's ``ThreadPoolExecutor`` races: a TIMED-OUT worker keeps running, and a
  shared slot means it can observe (or dispatch on) the next child's engine.
  Per-invocation state cannot be borrowed, because there is nothing to borrow
  from.
* It can be minted nowhere else: construction demands the module-private mint,
  and validation compares the engine's carried context BY IDENTITY against the
  one captured at issue. A copy, a look-alike, another child's engine, or the
  same engine after its attempt ended all refuse by name BEFORE
  ``_chat_completion_text`` is entered.
* It is SINGLE-USE. One child, one deployment revision, one attempt ordinal, one
  terminal receipt — so one physical completion. A plugin that called twice would
  hide a second physical attempt inside one receipt, which is exactly the
  cardinality Article XI.2 exists to make impossible; the second call refuses
  before the leaf. A second attempt needs a second admitted child, which is the
  runner's to admit.
* A plugin that needs intelligence and holds no handle refuses
  :data:`PLUGIN_DISPATCH_REQUIRED`. It does not degrade to a provider; a
  deterministic plugin needs no handle at all and is unaffected.

There is no ambient singleton and no plugin principal: the handle is authority
BORROWED for the duration of one dispatch, and the host releases it when that
dispatch returns.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from typing import Any, Optional, Sequence

from ..kernel.dispatch_context import (
    DispatchContext,
    dispatch_context_of,
    require_dispatch_context,
)
from ..kernel.model import KernelRefused
from ..kernel.provider_signals import CONTROL_SIGNALS

#: The plugin asked for intelligence with no handle in its invocation.
PLUGIN_DISPATCH_REQUIRED = "plugin_dispatch_required"
#: The invocation carried something that is not a host-minted handle (or one was
#: built outside the mint): a duck-typed look-alike, a copy, a stub with ``.chat``.
PLUGIN_DISPATCH_FORGED = "plugin_dispatch_forged"
#: The handle's run is over — the host released it when the dispatch returned.
#: This is what a timed-out worker's stale handle hits.
PLUGIN_DISPATCH_RELEASED = "plugin_dispatch_released"
#: The engine no longer carries the exact context this handle was issued for
#: (another child rebound it, the attempt ended), or that context no longer
#: validates for its operation / revision / destination / attempt.
PLUGIN_DISPATCH_CONTEXT_MISMATCH = "plugin_dispatch_context_mismatch"
#: The engine handed to the host is not from an admitted child at all.
PLUGIN_DISPATCH_ENGINE_UNADMITTED = "plugin_dispatch_engine_unadmitted"
#: The engine cannot serve the plugin chat seam.
PLUGIN_DISPATCH_ENGINE_INCOMPATIBLE = "plugin_dispatch_engine_incompatible"
#: The child's cancellation signal is set: no new physical work may start.
PLUGIN_DISPATCH_CANCELLED = "plugin_dispatch_cancelled"
#: The handle's ONE physical completion is already spent. A second attempt would
#: be a second physical call hiding inside one child's single terminal receipt.
PLUGIN_DISPATCH_CARDINALITY = "plugin_dispatch_cardinality"
#: A handle was offered to a chain that is not exactly one plugin. An admitted
#: handle belongs to ONE plugin child, never to a chain.
PLUGIN_DISPATCH_CHAIN_CARDINALITY = "plugin_dispatch_chain_cardinality"

#: The ONE key an admitted invocation's context carries the handle under. It
#: exists only inside the worker's private copy of the context: it is never
#: logged, never queued with a deferred run, and never seen by a plugin that did
#: not declare the ``llm`` capability.
PLUGIN_DISPATCH_KEY = "__plugin_dispatch__"


def _named(reason: str, plugin_id: str, detail: str) -> str:
    message = str(reason)
    if plugin_id:
        message = f"{message}:{plugin_id}"
    if detail:
        message = f"{message} ({detail})"
    return message


class PluginDispatchRefused(RuntimeError):
    """"You have no admitted handle" — reportable, and safe to catch.

    Raised before a handle exists (or before one is used at all), so a caller
    that has no admitted child can turn it into an honest plugin-level ``error``
    result instead of exploding a route preview. Nothing physical happened.
    """

    def __init__(self, reason: str, plugin_id: str = "", detail: str = "") -> None:
        super().__init__(_named(reason, plugin_id, detail))
        self.reason = str(reason)
        self.plugin_id = str(plugin_id or "")


class PluginDispatchRevoked(BaseException):
    """"Your authority is gone" — deliberately NOT an ``Exception``.

    Released handle, cancelled child, or a context that no longer belongs to this
    engine. Every plugin's ``run()`` wraps its intel call in ``except Exception``
    and returns a failure-shaped summary; if that swallowed a revocation, the
    admitted child would close ``succeeded`` carrying a record that describes work
    the kernel had already withdrawn permission for. Inheriting from
    ``BaseException`` makes absorbing it something a plugin author has to do ON
    PURPOSE, and the sanitizing adapter above the plugin still converts it into an
    ordinary domain failure before it can reach the runner.
    """

    def __init__(self, reason: str, plugin_id: str = "", detail: str = "") -> None:
        super().__init__(_named(reason, plugin_id, detail))
        self.reason = str(reason)
        self.plugin_id = str(plugin_id or "")


class PluginProviderFailure(BaseException):
    """A real provider exception raised by the physical completion.

    Also not an ``Exception``, for the same reason and a sharper one: a plugin
    that caught the provider's failure and returned ``{"status": "error"}`` would
    hand the admitted child a RESULT, and the child would earn a ``succeeded``
    receipt for an attempt that physically failed. The failure has to reach
    ``MeetingAdapter.dispatch``, which sanitizes it into the domain failure the
    runner closes the child ``failed`` on.

    Carries the cause's TYPE only: provider text (echoed prompts, endpoint bodies,
    transcript fragments) never rides a kernel-bound error.
    """

    def __init__(self, plugin_id: str, cause: BaseException) -> None:
        self.reason = type(cause).__name__
        self.plugin_id = str(plugin_id or "")
        super().__init__(_named("plugin_provider_failed", self.plugin_id, self.reason))


#: What a plugin's ``except Exception`` must NEVER absorb. The two dispatch-side
#: classes above are already un-absorbable by construction; the kernel's typed
#: CONTROL signals are ordinary ``RuntimeError``s owned by another module, so
#: every plugin re-raises this tuple explicitly ahead of its own handler.
PLUGIN_INTEL_SIGNALS: tuple[type[BaseException], ...] = CONTROL_SIGNALS + (
    PluginDispatchRefused,
    PluginDispatchRevoked,
    PluginProviderFailure,
)


# The private mint. A `PluginDispatch` cannot be constructed without it, so the
# handle is opaque structurally rather than by naming convention.
_MINT = object()


class PluginDispatch:
    """ONE admitted child's right to ONE physical completion. Single-use.

    Holds no configuration, resolves no placement, and constructs nothing. Every
    call re-proves the same facts the runner proved when it claimed the child:
    the handle is live, the child is not cancelled, the engine still carries THIS
    context object, that context still validates for its operation / revision /
    destination / attempt, and the engine can serve the seam.

    CARDINALITY is part of that contract, not a convention. A handle names one
    child, one deployment revision, one attempt ordinal, and one terminal receipt
    (Articles V.2, XI.2): a plugin that called ``chat`` twice would perform two
    physical attempts under one receipt, and the journal would record one. The
    single completion is therefore CLAIMED atomically, immediately before the leaf
    — so a second call, sequential or concurrent, refuses
    :data:`PLUGIN_DISPATCH_CARDINALITY` before reaching a provider. A plugin that
    genuinely needs a second attempt needs a second admitted child.

    Revocation and that claim share ONE lock and ONE state word, because they are
    the same decision seen from two sides. Validating ``_released`` and then
    claiming separately leaves a window the host's timeout wins: release lands
    between the two, and a physical request starts after the authority for it was
    withdrawn. So the claim atomically observes live + uncancelled + unconsumed and
    moves the handle to IN-FLIGHT; :meth:`release` atomically revokes while the
    handle is still unclaimed. A release that arrives once a call is in flight
    cannot un-send it — that attempt is indeterminate and fenced by the projection
    stager — but it authorizes nothing further: the handle never returns to LIVE.

    The lock is never held across the provider call, so ``release`` (the host's
    thread, mid-timeout) never waits on a completion.
    """

    #: The three states a handle passes through, in one direction only.
    _LIVE = "live"
    _IN_FLIGHT = "in-flight"
    _SPENT = "spent"

    __slots__ = (
        "_engine",
        "_context",
        "_cancellation",
        "_revision",
        "_gate",
        "_released",
        "_claimed_at_release",
        "_state",
        "_calls",
    )

    def __init__(
        self,
        *,
        engine: Any,
        context: DispatchContext,
        cancellation: Optional[threading.Event],
        mint: Any = None,
    ) -> None:
        if mint is not _MINT:
            raise PluginDispatchRefused(PLUGIN_DISPATCH_FORGED)
        self._engine = engine
        self._context = context
        self._cancellation = cancellation
        # The immutable deployment this handle is FOR, snapshotted from the
        # context at issue: `require_dispatch_context` compares a revision only
        # when it is given one, so the handle carries its own expectation rather
        # than trusting whatever it is asked about later.
        self._revision = _RevisionExpectation(
            context.revision_id, context.destination_id
        )
        # ONE lock over revocation AND the single-use claim: two threads holding
        # the same handle must not both pass "not spent yet", and a release must
        # not slip between a call's validation and its claim.
        self._gate = threading.Lock()
        self._released = False
        # The timeout election's verdict, recorded once by the first `release`.
        self._claimed_at_release: Optional[bool] = None
        self._state = self._LIVE
        self._calls = 0

    # ------------------------------------------------------------- identity

    @property
    def operation_id(self) -> str:
        return self._context.operation_id

    @property
    def revision_id(self) -> str:
        return self._context.revision_id

    @property
    def destination_id(self) -> str:
        return self._context.destination_id

    @property
    def attempt_ordinal(self) -> int:
        return self._context.attempt_ordinal

    @property
    def warrant_basis(self) -> str:
        return self._context.warrant_basis

    @property
    def released(self) -> bool:
        with self._gate:
            return self._released

    @property
    def cancelled(self) -> bool:
        return self._cancellation is not None and self._cancellation.is_set()

    @property
    def calls(self) -> int:
        """Physical completions this handle served: 0 or 1, never more."""
        with self._gate:
            return self._calls

    @property
    def spent(self) -> bool:
        """True once the single completion has been claimed."""
        with self._gate:
            return self._state is not self._LIVE

    @property
    def in_flight(self) -> bool:
        """True while the one claimed completion has not returned."""
        with self._gate:
            return self._state is self._IN_FLIGHT

    def journal_value(self) -> dict[str, Any]:
        return dict(self._context.journal_value())

    # ------------------------------------------------------------ lifecycle

    def release(self) -> bool:
        """Revoke this handle AND report, atomically, whether it was already spent.

        Returns ``True`` when the one physical completion had already been claimed
        at the instant of revocation — i.e. a request is or was in flight and its
        outcome cannot be known — and ``False`` when the handle was still LIVE, in
        which case the revocation guarantees no request will ever be sent.

        The return value exists because a caller that needs that fact CANNOT read
        it separately. ``if handle.calls: ... ; handle.release()`` is two
        observations of a moving target: the worker can claim in the gap, so the
        caller decides "nothing happened" and a physical request goes out anyway.
        Revocation and the verdict are therefore one step under one lock — this is
        the timeout ELECTION, not a getter.

        Idempotent, and the verdict is stable: the first call records it and every
        later call reports the same answer. (Recomputing would agree — a handle
        revoked while LIVE can never leave LIVE, because the claim refuses a
        revoked handle first — but storing it makes the guarantee structural
        rather than emergent.)

        Non-blocking: the lock is held for two assignments and never across a
        provider call, so the host thread timing a worker out is never parked
        behind a model.
        """
        with self._gate:
            self._released = True
            if self._claimed_at_release is None:
                self._claimed_at_release = self._state is not self._LIVE
            return self._claimed_at_release

    # ------------------------------------------------------------- dispatch

    def chat(
        self,
        messages: Sequence[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 800,
        plugin_id: str = "",
    ) -> str:
        """THE one completion on the admitted engine, after the whole fence passes.

        The provider call is wrapped exactly as the meeting and speech adapters
        wrap theirs: the kernel's typed CONTROL signals are re-raised FIRST (a
        dialect retry is the runner's second child, not a plugin's problem), and
        everything else becomes a :class:`PluginProviderFailure` that carries no
        provider text.

        The completion is CLAIMED under a lock immediately before the leaf, so the
        claim and the physical call cannot be separated by a scheduler: two threads
        sharing one handle produce exactly one attempt and one refusal.
        """
        # The elected product adopter lives behind one narrow application façade.
        # PluginDispatch stays a one-shot authority handle; it does not own the
        # ToolTurn ledger, a lease, route selection, or a provider transport.
        from ..services.agent_turn_service import AgentTurnService
        # Refusal/claim are an authority decision, not a provider result.  Keep
        # them outside the sanitizing boundary so a zero-dispatch refusal cannot
        # be laundered into PluginProviderFailure.
        self._validated_engine(plugin_id)
        self._claim_the_one_completion(plugin_id)
        try:
            return AgentTurnService.dispatch_plugin(
                self, messages, temperature=temperature, max_tokens=max_tokens,
                plugin_id=plugin_id,
            )
        except CONTROL_SIGNALS:
            raise
        except (KernelRefused, PluginDispatchRevoked):
            raise
        except BaseException as exc:  # sanitized: no provider text crosses this line
            raise PluginProviderFailure(plugin_id, exc) from None
        finally:
            self._settle_the_completion()

    # --------------------------------------------------------------- fence

    def _claim_the_one_completion(self, plugin_id: str = "") -> None:
        """Observe live + uncancelled + unconsumed and go IN-FLIGHT, atomically.

        One indivisible step, immediately before the leaf. Splitting it — read the
        state, then act — is precisely the window a concurrent ``release`` or a
        second caller wins, and the cost of losing it is a physical request sent
        under authority that no longer exists.

        Refusal order states the primary fact: a revoked handle is RELEASED even
        if it is also spent, a cancelled child is CANCELLED, and only an
        otherwise-good handle that has already been used reports CARDINALITY.
        """
        cancelled = self._cancellation is not None and self._cancellation.is_set()
        with self._gate:
            if self._released:
                raise PluginDispatchRevoked(PLUGIN_DISPATCH_RELEASED, plugin_id)
            if cancelled:
                raise PluginDispatchRevoked(PLUGIN_DISPATCH_CANCELLED, plugin_id)
            if self._state is not self._LIVE:
                raise PluginDispatchRevoked(PLUGIN_DISPATCH_CARDINALITY, plugin_id)
            self._state = self._IN_FLIGHT
            self._calls = 1

    def _settle_the_completion(self) -> None:
        """The one attempt has returned (any way at all). It is now SPENT.

        Never back to LIVE: a handle that has performed its physical attempt is
        finished whether it succeeded, failed, or was revoked mid-flight.
        """
        with self._gate:
            if self._state is self._IN_FLIGHT:
                self._state = self._SPENT

    def _validated_engine(self, plugin_id: str = "") -> Any:
        """Every check that must pass BEFORE a provider is touched.

        Liveness is checked on the HANDLE first and independently: a raw
        :class:`~holdspeak.kernel.dispatch_context.DispatchContext` stays in the
        kernel's issued registry after the runner unbinds it from the engine, so
        "the context still validates" is not, on its own, proof that this run may
        still act. The host's release is the revocation, and it is checked before
        anything else.

        These checks are DIAGNOSIS, not the decision: everything they read can
        change before the leaf, so :meth:`_claim_the_one_completion` re-reads
        revocation, cancellation, and consumption under the lock that ``release``
        also takes. What this buys is an early, precisely named refusal — and, for
        the engine/context checks, the only place they can be made at all.
        """
        # The SAME order the claim uses, so early diagnosis and the real decision
        # can never name different rules for the same handle.
        with self._gate:
            released = self._released
            state = self._state
        if released:
            raise PluginDispatchRevoked(PLUGIN_DISPATCH_RELEASED, plugin_id)
        if self._cancellation is not None and self._cancellation.is_set():
            raise PluginDispatchRevoked(PLUGIN_DISPATCH_CANCELLED, plugin_id)
        if state is not self._LIVE:
            raise PluginDispatchRevoked(PLUGIN_DISPATCH_CARDINALITY, plugin_id)
        engine = self._engine
        # IDENTITY, not equality: the runner releases the binding as each attempt
        # ends and refuses to rebind a live one, so an engine that no longer
        # carries THIS object is either a finished attempt or someone else's
        # child. Neither is authority to dispatch.
        if dispatch_context_of(engine) is not self._context:
            raise PluginDispatchRevoked(
                PLUGIN_DISPATCH_CONTEXT_MISMATCH, plugin_id, "engine context"
            )
        try:
            require_dispatch_context(
                self._context,
                self._revision,
                operation_id=self._context.operation_id,
                attempt_ordinal=self._context.attempt_ordinal,
            )
        except KernelRefused as exc:
            raise PluginDispatchRevoked(
                PLUGIN_DISPATCH_CONTEXT_MISMATCH, plugin_id, str(exc.reason or "")
            ) from None
        if not callable(getattr(engine, "_chat_completion_text", None)):
            raise PluginDispatchRefused(PLUGIN_DISPATCH_ENGINE_INCOMPATIBLE, plugin_id)
        return engine


class _RevisionExpectation:
    """The two immutable fields a factory-grade context check compares against."""

    __slots__ = ("id", "destination_id")

    def __init__(self, revision_id: str, destination_id: str) -> None:
        self.id = revision_id
        self.destination_id = destination_id


def _issue_plugin_dispatch(
    *,
    engine: Any,
    cancellation: Optional[threading.Event] = None,
    plugin_id: str = "",
) -> PluginDispatch:
    """Mint the handle for ONE admitted plugin run. The HOST is its only caller.

    Private and unexported by design: the mint reads the context the runner bound
    onto the engine it built for the claimed child, so a caller who has no such
    engine cannot produce a handle at all. An unadmitted engine (nothing bound) or
    one that cannot serve the seam refuses here — before the plugin runs, and
    therefore before any prompt exists.
    """
    context = dispatch_context_of(engine)
    if context is None:
        raise PluginDispatchRefused(PLUGIN_DISPATCH_ENGINE_UNADMITTED, plugin_id)
    try:
        require_dispatch_context(
            context,
            operation_id=context.operation_id,
            attempt_ordinal=context.attempt_ordinal,
        )
    except KernelRefused as exc:
        raise PluginDispatchRefused(
            PLUGIN_DISPATCH_CONTEXT_MISMATCH, plugin_id, str(exc.reason or "")
        ) from None
    if not callable(getattr(engine, "_chat_completion_text", None)):
        raise PluginDispatchRefused(PLUGIN_DISPATCH_ENGINE_INCOMPATIBLE, plugin_id)
    return PluginDispatch(
        engine=engine, context=context, cancellation=cancellation, mint=_MINT
    )


def plugin_dispatch_of(context: Any) -> Any:
    """The handle THIS invocation carries, or ``None``.

    Reads the reserved key only; a plugin never reaches for a host attribute, so
    two invocations in flight at once cannot see each other's authority.
    """
    if isinstance(context, Mapping):
        return context.get(PLUGIN_DISPATCH_KEY)
    return None


def require_plugin_dispatch(handle: Any, *, plugin_id: str = "") -> PluginDispatch:
    """The validator every intelligence-consuming plugin calls FIRST.

    ``type(...) is`` rather than ``isinstance``: a subclass could override
    :meth:`PluginDispatch.chat` and skip the fence, which is exactly the shape a
    look-alike would take.
    """
    if handle is None:
        raise PluginDispatchRefused(PLUGIN_DISPATCH_REQUIRED, plugin_id)
    if type(handle) is not PluginDispatch:
        raise PluginDispatchRefused(PLUGIN_DISPATCH_FORGED, plugin_id)
    return handle


class IntelligenceConsumer:
    """Mixin for a plugin that consumes intelligence through its invocation.

    Carries the plugin's own decoding envelope (a prompt property, not a provider
    choice) and the one call seam. It holds no engine, no cache, no configuration,
    and — deliberately — no injection attribute: the handle arrives with the run
    context and dies with it.
    """

    #: This plugin's decoding envelope for its single prompt.
    intel_temperature: float = 0.2
    intel_max_tokens: int = 800

    def _call_intel(
        self,
        messages: Sequence[dict[str, str]],
        context: Any,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        plugin_id = str(getattr(self, "id", "") or "")
        handle = require_plugin_dispatch(
            plugin_dispatch_of(context), plugin_id=plugin_id
        )
        return handle.chat(
            messages,
            temperature=self.intel_temperature if temperature is None else float(temperature),
            max_tokens=self.intel_max_tokens if max_tokens is None else int(max_tokens),
            plugin_id=plugin_id,
        )


__all__ = [
    "IntelligenceConsumer",
    "PLUGIN_INTEL_SIGNALS",
    "PLUGIN_DISPATCH_CANCELLED",
    "PLUGIN_DISPATCH_CARDINALITY",
    "PLUGIN_DISPATCH_CHAIN_CARDINALITY",
    "PLUGIN_DISPATCH_CONTEXT_MISMATCH",
    "PLUGIN_DISPATCH_ENGINE_INCOMPATIBLE",
    "PLUGIN_DISPATCH_ENGINE_UNADMITTED",
    "PLUGIN_DISPATCH_FORGED",
    "PLUGIN_DISPATCH_KEY",
    "PLUGIN_DISPATCH_RELEASED",
    "PLUGIN_DISPATCH_REQUIRED",
    "PluginDispatch",
    "PluginDispatchRefused",
    "PluginDispatchRevoked",
    "PluginProviderFailure",
    "plugin_dispatch_of",
    "require_plugin_dispatch",
]
