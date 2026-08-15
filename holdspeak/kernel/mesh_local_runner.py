"""Worker-local admitted execution of one mesh offer (design §4–§5).

The receiver used to call ``run_prompt`` from a hand-checked envelope. This spine
instead persists the offer's exact execution revision and gives one
``inference.invoke@1`` request to the worker-local :class:`InferenceRunner`.
The runner owns admission, claim, construction, dispatch, and the immutable
terminal receipt; this module constructs no provider itself.

The signed first ordinal permits at most one typed compatibility follow-up. Both
nodes check that bounded receipt cohort, so no third physical attempt can run.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from ..mesh_authority.refusals import (
    EXECUTION_TARGET_RECURSIVE,
    MeshAuthorityRefused,
    OFFER_EXPIRED,
    OFFER_ORDINAL_NOT_PERMITTED,
)
from ..mesh_authority.report import safe_failure_class
from .inference_runner import InferenceRunner, InvocationRequest, ServiceContract
from .inference_shared import executor_identity
from .mesh_local_authority import MESH_RECEIVER_CONTRACT, MeshLocalAuthority
from .model import KernelRefused
from .prompt_adapter import CanonicalPromptAdapter
from .provider_signals import retry_invocation_id


@dataclass(frozen=True)
class MeshLocalOutcome:
    """What the worker can honestly say about its own physical attempts."""

    terminal_outcome: str
    result: str
    failure_class: str
    attempts: tuple[dict[str, Any], ...]


def local_invocation_id(offer: Any) -> str:
    """The deterministic local id for one offer's first attempt.

    Deterministic on purpose: the stop election has to be able to name the
    invocation BEFORE ``invoke`` is called, so there is no interval between
    verification and registration in which a cancellation could be lost.
    """
    operation = "".join(
        ch for ch in str(offer.hub_operation_id or "") if ch.isalnum() or ch == "_"
    )
    return f"mesh_{operation or 'offer'}_{offer.first_ordinal}"


class MeshLocalRunner:
    """One worker, one local kernel, one admitted attempt per permitted ordinal."""

    def __init__(
        self,
        database: Any,
        broker: Any = None,
        *,
        engine_factory: Optional[Callable[..., Any]] = None,
        monotonic: Callable[[], float] = time.monotonic,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._database = database
        self._broker = broker if broker is not None else self._runtime_broker(database)
        self._monotonic = monotonic
        self._clock = clock
        self._authority: Optional[MeshLocalAuthority] = None
        self._election = threading.Lock()
        self._stopped = False
        self._active_id = ""
        factory = self._guarded_factory(engine_factory) if engine_factory else None
        self._runner = InferenceRunner(
            self._broker,
            database,
            principal_provider=self._local_principal,
            **({"engine_factory": factory} if factory is not None else {}),
        )

    @staticmethod
    def _runtime_broker(database: Any) -> Any:
        """The broker for THIS database — the worker's own, never another's.

        In production the worker's database IS the process database, so this is
        the ordinary shared broker (whose in-process registry is what makes
        cancellation reachable). A caller that supplies a different database gets
        a broker configured for exactly that one: a kernel bound to someone
        else's journal would write this node's receipts into the wrong ledger.
        """
        from ..db import get_database
        from .runtime import _configure, _service

        return _service() if database is get_database() else _configure(database)

    def _local_principal(self) -> Any:
        """The principal the OFFER derived — never one this process wrote down."""
        authority = self._authority
        if authority is None:
            raise KernelRefused("adapter_context_required")
        return authority.principal

    @staticmethod
    def _guarded_factory(factory: Callable[..., Any]) -> Callable[..., Any]:
        """Refuse a factory that resolves back onto the mesh, before any dispatch.

        The primary guard is structural — a derived execution revision can never
        carry ``kind=mesh_node`` — and this is the same fact checked at the
        injectable seam, so a test or an embedding cannot hand the worker an
        engine that relays the job straight back out of this node.
        """

        def build(revision: Any, **kwargs: Any) -> Any:
            engine = factory(revision, **kwargs)
            from ..intel.mesh_relay import MeshRelayIntel

            if isinstance(engine, MeshRelayIntel):
                raise KernelRefused(EXECUTION_TARGET_RECURSIVE)
            return engine

        return build

    # ── the stop election (design §5) ────────────────────────────────

    def stop(self, *_args: Any) -> None:
        """Set the flag and cancel whatever is visible, atomically with respect
        to :meth:`execute`'s registration. One lock owns both facts, so there is
        no verification-to-registration or registration-to-invoke gap."""
        with self._election:
            self._stopped = True
            target = self._active_id
        if target:
            try:
                self._runner.cancel(target)
            except Exception:  # pragma: no cover - cancellation is best effort
                pass

    @property
    def stopped(self) -> bool:
        with self._election:
            return self._stopped

    def _register(self, invocation_id: str) -> bool:
        """Publish the active id and learn whether stop already won."""
        with self._election:
            self._active_id = invocation_id
            return self._stopped

    def _release(self, invocation_id: str) -> None:
        with self._election:
            if self._active_id == invocation_id:
                self._active_id = ""

    # ── the one execution ────────────────────────────────────────────

    def _remaining(self, offer: Any) -> float:
        """What is LEFT of the one signed monotonic window, asked RIGHT NOW."""
        return offer.remaining_seconds(monotonic=self._monotonic())

    def execute(self, authority: MeshLocalAuthority, payload: dict[str, Any]) -> MeshLocalOutcome:
        """Run one verified offer through the admitted gateway, once."""
        offer = authority.offer
        if self._remaining(offer) <= 0:
            raise MeshAuthorityRefused(OFFER_EXPIRED)

        # The exact derived revision, persisted BEFORE admission so the runner
        # resolves construction, model, endpoint, egress, and secret slot from
        # the frozen offer rather than from any mutable local configuration.
        self._database.deployment_revisions.upsert(offer.execution_revision)

        # Recomputed AFTER that write (repair R8/R2.4). Persistence takes real
        # time, and no amount of it may extend the physical authority the hub
        # signed: the deadline is ONE monotonic instant, not a duration that
        # restarts each time somebody reads it. Every step below asks the offer
        # again, immediately before it acts.
        if self._remaining(offer) <= 0:
            raise MeshAuthorityRefused(OFFER_EXPIRED)

        invocation_id = local_invocation_id(offer)
        self._authority = authority
        captured: dict[str, str] = {}

        def publish(result: Any) -> str:
            # Provider output is captured OUTSIDE the kernel; the kernel result
            # reference is a content-free pointer at the relay job.
            captured["output"] = str(dict(result).get("output") or "")
            return f"mesh-result:{offer.job_id}"

        # Immediately before ADMISSION: the wall deadline the kernel enforces is
        # derived from the latest remainder, never from an older one.
        budget = self._remaining(offer)
        if budget <= 0:
            raise MeshAuthorityRefused(OFFER_EXPIRED)
        request = InvocationRequest(
            offer.execution_revision.id,
            ServiceContract.for_payload(MESH_RECEIVER_CONTRACT, "1", payload),
            self._clock() + budget,
            payload,
            invocation_id,
            "",
            offer.first_ordinal,
        )

        if self._register(invocation_id):
            # Stop already won. Entering the runner's pending-cancellation fence
            # BEFORE `invoke` means the child is never admitted and no provider
            # is ever reached.
            self._runner.cancel(invocation_id)

        # Immediately before the WATCHDOG. The signed budget is MONOTONIC end to
        # end (ruling 1); the runner's own watchdog is wall-clock, so this timer
        # is what a backward wall step cannot lengthen. Registration and the
        # pre-invoke cancellation both took real time, and this timer is set from
        # what is left after them, not from what was left before.
        guard_budget = self._remaining(offer)
        if guard_budget <= 0:
            self._release(invocation_id)
            self._authority = None
            raise MeshAuthorityRefused(OFFER_EXPIRED)
        guard = threading.Timer(guard_budget, lambda: self._runner.cancel(invocation_id))
        guard.daemon = True
        guard.start()
        try:
            from .runtime import _as_principal

            with _as_principal(authority.principal):
                outcome = self._runner.invoke(
                    request, CanonicalPromptAdapter(), publish=publish
                )
        finally:
            guard.cancel()
            self._release(invocation_id)
            self._authority = None

        attempts = self._collect_attempts(offer, invocation_id)
        if not attempts or len(attempts) > offer.max_attempts:
            raise MeshAuthorityRefused(OFFER_ORDINAL_NOT_PERMITTED)
        succeeded = outcome.outcome == "succeeded"
        return MeshLocalOutcome(
            terminal_outcome=outcome.outcome,
            result=captured.get("output", "") if succeeded else "",
            failure_class="" if succeeded else self._failure_class(outcome),
            attempts=tuple(attempts),
        )

    def _collect_attempts(self, offer: Any, invocation_id: str) -> list[dict[str, Any]]:
        """The ordered, receipted physical attempts — read back from the journal.

        Nothing is reported that does not have a DURABLE local receipt: an
        attempt whose receipt is missing is simply not in the cohort, and the
        hub's own contiguity check then refuses the report.
        """
        store = self._broker.store
        attempts: list[dict[str, Any]] = []
        executor = executor_identity(offer.execution_revision.destination_id)
        for index, ordinal in enumerate(offer.permitted_ordinals):
            native = invocation_id if index == 0 else retry_invocation_id(invocation_id, ordinal)
            operation = store.operation_for_native(native)
            if operation is None:
                break
            receipt = store.receipt(str(operation["operation_id"]))
            if receipt is None:
                break
            attempts.append(
                {
                    "ordinal": int(ordinal),
                    "operation_id": str(operation["operation_id"]),
                    "receipt_id": str(receipt["receipt_id"]),
                    "principal_identity": str(operation["principal_identity"]),
                    "claim_identity": executor,
                    "outcome": str(receipt["outcome"]),
                }
            )
        return attempts

    @staticmethod
    def _failure_class(outcome: Any) -> str:
        """One value out of the FIXED shared vocabulary, and nothing else.

        Repair R2.7: a lowercase-token shape was never a vocabulary — an
        unrecognised kernel control class or provider reason satisfies it while
        saying something both nodes never agreed to transport. Every unknown
        reason therefore BECOMES the fixed generic class here, and the hub
        rejects anything outside the same set at its own boundary.
        """
        reason = str(getattr(outcome, "error", "") or "")
        if outcome.outcome == "refused" and reason:
            return safe_failure_class(reason)
        return safe_failure_class(outcome.outcome)


__all__ = ["MeshLocalOutcome", "MeshLocalRunner", "local_invocation_id"]
