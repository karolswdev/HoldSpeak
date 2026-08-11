"""ONE admitted speech-session model dispatch (HS-131-09).

Every ACTUAL Whisper transcription, MLX preload, or dictation provider dispatch
under a live ``dictation.session`` / ``wake.session`` / ``meeting.session``
reaches its model through :func:`run_admitted_speech_child` and nothing else.
Placement is never resolved here: the frozen
:class:`~holdspeak.speech_session.plan.SpeechSessionPlan` decided it at session
opening, and a capability missing from the plan is a named refusal raised BEFORE
any model request exists.

Audio, transcript, and prompt material ride ONLY inside the dispatched payload.
The payload is hashed into the service contract; the kernel journal records
``{contract, revision, payload_hash}`` and nothing else.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from .plan import SESSION_NOT_LIVE, SpeechSessionRefused

log = get_logger("speech_session")

DEFAULT_DEADLINE_SECONDS = 300.0


class SpeechProviderFailure(RuntimeError):
    """A model failure named by contract and a short SAFE reason only.

    Backend exception text can carry file paths, endpoint bodies, or echoed
    transcript fragments. The kernel journal must never receive that, so this is
    the only error string a speech child ever raises: the exception TYPE name, or
    an explicit sanitized reason.
    """

    def __init__(
        self, contract: str, exc: Optional[BaseException] = None, *, reason: str = ""
    ) -> None:
        short = reason or (type(exc).__name__ if exc is not None else "model_error_result")
        super().__init__(f"{contract}:{short}")
        self.contract = contract
        self.reason = short


class SpeechAdapter:
    """One admitted dispatch against an already-frozen local/remote deployment.

    The runner constructs the engine from the admitted revision; a Whisper child
    ignores it (the loaded ``Transcriber`` implementation is captured by the
    call) while a provider child uses it. Either way nothing here re-resolves a
    target.
    """

    connector_id = "inference-provider"

    def __init__(
        self,
        contract: str,
        call: Callable[[Any, Mapping[str, Any], threading.Event], Any],
    ) -> None:
        self._contract = contract
        self._call = call
        self.cancelled = threading.Event()
        self.cancel_calls = 0
        self.result: Any = None

    def dispatch(
        self, engine: Any, payload: Mapping[str, Any], cancellation: threading.Event
    ) -> dict[str, Any]:
        from ..kernel.model import KernelRefused

        try:
            self.result = self._call(engine, payload, cancellation)
        except (KernelRefused, SpeechSessionRefused):
            raise
        except BaseException as exc:  # sanitized: no backend text crosses this line
            raise SpeechProviderFailure(self._contract, exc) from None
        return {"contract": self._contract, "cancelled": self.cancelled.is_set()}

    def cancel(self) -> str:
        self.cancel_calls += 1
        self.cancelled.set()
        return "cancelled"


def invocation_id(*parts: Any) -> str:
    import hashlib

    seed = "|".join(str(part) for part in parts)
    return "speech_" + hashlib.sha256(seed.encode()).hexdigest()[:32]


def run_admitted_speech_child(
    *,
    broker: Any,
    principal: Any,
    plan: Any,
    parent: Any,
    capability: str,
    contract: str,
    material: Mapping[str, Any],
    call: Callable[[Any, Mapping[str, Any], threading.Event], Any],
    seed: Any,
    attempt_ordinal: int = 1,
    deadline_seconds: float = DEFAULT_DEADLINE_SECONDS,
    adapter: Optional[SpeechAdapter] = None,
    revision_id: str = "",
    publish: Any = None,
) -> tuple[Any, Any]:
    """Run ONE admitted model dispatch. Returns ``(outcome, result)``.

    ``parent`` is the live session parent, or ``None`` for the explicitly
    authorized pre-session service warm (which has no session to parent it).
    ``revision_id`` selects WHICH frozen entry of the capability's ordered set
    this child uses and is always re-asserted against the plan, so a child can
    only ever repeat an entry the plan already froze.

    Raises :class:`SpeechSessionRefused` when the plan or the parent refuses —
    before any model request exists.
    """
    from ..kernel.inference_runner import InvocationRequest, ServiceContract
    from ..kernel.model import KernelRefused
    from ..kernel.runtime import _as_principal

    revision_id = plan.assert_planned(capability, revision_id or plan.primary(capability))
    identifier = invocation_id(plan.session_id, capability, seed, attempt_ordinal)
    payload = {
        "payload_schema": 1,
        "capability": capability,
        "session_id": plan.session_id,
        "plan_sha256": plan.sha256,
        "deployment_revision": revision_id,
        "attempt_ordinal": int(attempt_ordinal),
        **dict(material),
    }
    dispatcher = adapter if adapter is not None else SpeechAdapter(contract, call)
    request = InvocationRequest(
        revision_id,
        ServiceContract.for_payload(contract, "1", payload),
        time.time() + float(deadline_seconds),
        payload,
        identifier,
        "" if parent is None else parent.operation_id,
        int(attempt_ordinal),
    )
    try:
        with _as_principal(principal):
            outcome = broker.inference_runner.invoke(
                request,
                dispatcher,
                publish=publish,
                parent_context=None if parent is None else parent.context,
            )
    except KernelRefused as exc:
        raise SpeechSessionRefused(exc.reason or SESSION_NOT_LIVE, capability) from None
    return outcome, dispatcher.result


def run_admitted_speech_capability(
    *, plan: Any, capability: str, attempt_ordinal: int = 1, **kwargs: Any
) -> tuple[Any, Any]:
    """Work one capability's ORDERED frozen entries, one admitted child each.

    Only a model FAILURE advances to the next frozen entry; a cancelled,
    refused, or indeterminate child is terminal — a disposition is not a licence
    to reach a second model. The next entry runs at ``attempt_ordinal + 1``, so
    its invocation identity, journal row, and receipt are all distinct.
    """
    entries = plan.revisions(capability)
    last: tuple[Any, Any] | None = None
    for index, revision_id in enumerate(entries):
        last = run_admitted_speech_child(
            plan=plan,
            capability=capability,
            revision_id=str(revision_id),
            attempt_ordinal=int(attempt_ordinal) + index,
            **kwargs,
        )
        if last[0].outcome != "failed" or index + 1 >= len(entries):
            return last
        log.warning(
            "speech entry %d/%d failed for %s; attempting the next frozen entry",
            index + 1, len(entries), capability,
        )
    assert last is not None  # a plan capability always has at least one entry
    return last


__all__ = [
    "DEFAULT_DEADLINE_SECONDS",
    "SpeechAdapter",
    "SpeechProviderFailure",
    "invocation_id",
    "run_admitted_speech_capability",
    "run_admitted_speech_child",
]
