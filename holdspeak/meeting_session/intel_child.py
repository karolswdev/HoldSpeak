"""ONE admitted meeting-intelligence provider dispatch (HS-131-08).

Both callers reach a provider through :func:`run_admitted_child` and nothing
else: the live session (:mod:`.intel_admission`, parent ``meeting.session``) and
the post-close deferred queue job (:mod:`.deferred_admission`, parent
``meeting.deferred-intel-job``). Neither resolves placement — the frozen
:class:`~holdspeak.meeting_session.intel_plan.MeetingIntelPlan` decided that at
admission, and a capability missing from the plan is a named refusal raised
BEFORE any provider request exists.

Transcript, bookmark context, prompt, and plugin material ride ONLY inside the
dispatched payload. The payload is hashed into the service contract; the kernel
journal records ``{contract, revision, payload_hash}`` and nothing else.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections.abc import Mapping as _Mapping
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from .intel_plan import MeetingIntelRefused, SESSION_NOT_LIVE

log = get_logger("meeting_session")

DEFAULT_DEADLINE_SECONDS = 300.0


#: The sanitized short reason for a provider failure the engine RETURNED
#: (an ``IntelResult`` carrying ``.error``) instead of raising.
PROVIDER_ERROR_RESULT = "provider_error_result"


class MeetingProviderFailure(RuntimeError):
    """A provider failure named by contract and a short reason only.

    Adapter error text can carry transcript fragments (echoed prompts, endpoint
    bodies). The kernel journal must never receive that, so this is the only
    error string a meeting child ever raises. The reason is either the raised
    exception's TYPE name or, for a returned error result,
    :data:`PROVIDER_ERROR_RESULT` — never provider text.
    """

    def __init__(
        self, contract: str, exc: Optional[BaseException] = None, *, reason: str = ""
    ) -> None:
        short = reason or (type(exc).__name__ if exc is not None else PROVIDER_ERROR_RESULT)
        super().__init__(f"{contract}:{short}")
        self.contract = contract
        self.reason = short


def provider_error_of(result: Any) -> str:
    """The provider-level error a RETURNED result carries, if any.

    A provider failure reaches a meeting dispatch two ways, and the domain has
    always treated both as failure: an exception, and a successfully returned
    :class:`~holdspeak.intel.IntelResult` whose ``.error`` is set (the vocabulary
    :mod:`.intel_analysis` and :mod:`holdspeak.intel_queue` already read). Only
    the first used to close its child ``failed``, so an error-result attempt
    earned a ``succeeded`` receipt and stopped the frozen-entry walk.

    Bookmark-label and auto-title children return plain strings and plugin
    children return record mappings (whose own ``error`` key is the plugin's
    status, not the provider's), so neither shape is classified here.
    """
    if result is None or isinstance(result, (str, bytes, _Mapping)):
        return ""
    return str(getattr(result, "error", "") or "")


def sha(text: Any) -> str:
    return "sha256:" + hashlib.sha256(str(text).encode("utf-8", "replace")).hexdigest()


def invocation_id(*parts: Any) -> str:
    seed = "|".join(str(part) for part in parts)
    return "meeting_intel_" + hashlib.sha256(seed.encode()).hexdigest()[:32]


class MeetingAdapter:
    """One admitted meeting-intelligence dispatch against a revision-built engine."""

    connector_id = "inference-provider"

    def __init__(self, contract: str, call: Callable[[Any, Mapping[str, Any], threading.Event], Any]) -> None:
        self._contract = contract
        self._call = call
        self.cancelled = threading.Event()
        self.cancel_calls = 0
        self.result: Any = None

    def dispatch(self, engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> dict[str, Any]:
        from ..kernel.model import KernelRefused

        try:
            self.result = self._call(engine, payload, cancellation)
        except (KernelRefused, MeetingIntelRefused):
            raise
        except BaseException as exc:  # sanitized: no provider text crosses this line
            raise MeetingProviderFailure(self._contract, exc) from None
        if provider_error_of(self.result):
            # A returned error result IS a provider failure: classify it HERE, so
            # the child closes `failed` with an honest (sanitized) receipt and the
            # frozen-entry walk may advance. The result object itself is kept on
            # the adapter, so the callers still read their existing `.error`.
            raise MeetingProviderFailure(self._contract, reason=PROVIDER_ERROR_RESULT)
        return {"contract": self._contract, "cancelled": self.cancelled.is_set()}

    def cancel(self) -> str:
        self.cancel_calls += 1
        self.cancelled.set()
        return "cancelled"


def run_admitted_child(
    *,
    broker: Any,
    principal: Any,
    plan: Any,
    parent: Any,
    capability: str,
    contract: str,
    projection_kind: str,
    material: Mapping[str, Any],
    call: Callable[[Any, Mapping[str, Any], threading.Event], Any],
    encode: Callable[[Any, Mapping[str, Any]], Mapping[str, Any]],
    seed: Any,
    attempt_ordinal: int = 1,
    deadline_seconds: float = DEFAULT_DEADLINE_SECONDS,
    adapter: Optional[MeetingAdapter] = None,
    revision_id: str = "",
) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
    """Run ONE admitted provider dispatch. Returns (outcome, projection, result).

    ``revision_id`` selects WHICH frozen entry of the capability's ordered set
    this child uses; it defaults to the first. It is always re-asserted against
    the plan, so a child can only ever repeat an entry the plan already froze.

    Raises :class:`MeetingIntelRefused` when the plan or the parent refuses —
    before any provider request exists.
    """
    from ..kernel.inference_runner import InvocationRequest, ServiceContract
    from ..kernel.model import KernelRefused
    from ..kernel.runtime import _as_principal

    revision_id = plan.assert_planned(
        capability, revision_id or plan.primary(capability)
    )
    identifier = invocation_id(plan.meeting_id, capability, seed, attempt_ordinal)
    payload = {
        "payload_schema": 1,
        "capability": capability,
        "meeting_id": plan.meeting_id,
        "plan_sha256": plan.sha256,
        "deployment_revision": revision_id,
        "attempt_ordinal": int(attempt_ordinal),
        **dict(material),
    }
    dispatcher = adapter if adapter is not None else MeetingAdapter(contract, call)

    def projection(result: Any) -> Mapping[str, Any]:
        return {
            "capability": capability,
            "meeting_id": plan.meeting_id,
            "plan_sha256": plan.sha256,
            "deployment_revision": revision_id,
            "invocation_id": identifier,
            **dict(encode(dispatcher.result, payload)),
        }

    request = InvocationRequest(
        revision_id,
        ServiceContract.for_payload(contract, "1", payload),
        time.time() + float(deadline_seconds),
        payload,
        identifier,
        parent.operation_id,
        int(attempt_ordinal),
    )
    try:
        with _as_principal(principal):
            outcome = broker.inference_runner.invoke(
                request,
                dispatcher,
                publish=broker.projection_stager.publisher(
                    identifier, projection_kind, projection
                ),
                parent_context=parent.context,
            )
    except KernelRefused as exc:
        raise MeetingIntelRefused(exc.reason or SESSION_NOT_LIVE, capability) from None
    if outcome.outcome != "succeeded":
        return outcome, None, dispatcher.result
    return outcome, broker.projection_stager.finalize(identifier), dispatcher.result


def run_admitted_capability(
    *,
    plan: Any,
    capability: str,
    adapter_factory: Optional[Callable[[], MeetingAdapter]] = None,
    attempt_ordinal: int = 1,
    **kwargs: Any,
) -> tuple[Any, Optional[Mapping[str, Any]], Any]:
    """Work one capability's ORDERED frozen entries, one admitted child each.

    Sol Amendment 1: the ``auto`` local→cloud fallback is a real second plan
    entry, so taking it must be a SEPARATE admitted child that names the entry it
    actually used — never an invisible retarget inside one engine's receipt. Entry
    1 is attempted first; only a provider FAILURE moves to entry 2 (a cancelled,
    refused, or indeterminate child is terminal — the disposition is not a licence
    to reach a second provider), and the next entry runs at ``attempt_ordinal+1``
    so its invocation identity, its journal row, and its receipt are distinct.

    A provider failure is either shape: a raised exception, or an engine that
    RETURNS an error-carrying result (classified in :meth:`MeetingAdapter.dispatch`
    before the outcome is elected). When every entry fails, the last child's
    triple is returned unchanged, so the callers keep reading the failure in the
    domain vocabulary they already speak — a ``failed`` outcome and, when the
    provider returned one, the result with ``.error`` set.
    """
    entries = plan.revisions(capability)
    last: tuple[Any, Optional[Mapping[str, Any]], Any] | None = None
    for index, revision_id in enumerate(entries):
        adapter = adapter_factory() if adapter_factory is not None else None
        last = run_admitted_child(
            plan=plan,
            capability=capability,
            revision_id=str(revision_id),
            attempt_ordinal=int(attempt_ordinal) + index,
            adapter=adapter,
            **kwargs,
        )
        if last[0].outcome != "failed" or index + 1 >= len(entries):
            return last
        log.warning(
            "meeting intelligence entry %d/%d failed for %s; attempting the next frozen entry",
            index + 1, len(entries), capability,
        )
    assert last is not None  # a plan capability always has at least one entry
    return last


def discard_staged_children(broker: Any, database: Any, parent_operation_id: str) -> int:
    """Finalize every unresolved stage under one parent; a cancelled parent discards.

    ``ProjectionStager.finalize`` is the only discard path: it re-reads the
    child receipt and the parent state under its own transaction, so a
    cancelled/cancelling parent turns each staged snapshot into ``DISCARDED``
    instead of meeting state.
    """
    from ..kernel.model import KernelRefused

    if not parent_operation_id:
        return 0
    with database._connection() as conn:
        rows = conn.execute(
            """SELECT s.invocation_id FROM kernel_projection_stages s
               JOIN kernel_operations o ON o.operation_id=s.operation_id
               WHERE o.parent_operation_id=? AND s.state IN ('STAGED','FINALIZING')""",
            (parent_operation_id,),
        ).fetchall()
    discarded = 0
    for row in rows:
        try:
            broker.projection_stager.finalize(str(row["invocation_id"]))
            discarded += 1
        except KernelRefused as exc:
            log.warning("staged meeting projection not resolvable: %s", exc.reason)
    return discarded


__all__ = [
    "DEFAULT_DEADLINE_SECONDS",
    "MeetingAdapter",
    "MeetingProviderFailure",
    "PROVIDER_ERROR_RESULT",
    "discard_staged_children",
    "invocation_id",
    "provider_error_of",
    "run_admitted_capability",
    "run_admitted_child",
    "sha",
]
