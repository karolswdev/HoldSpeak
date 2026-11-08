"""The engine door: one way to run one AI job on the engine its assignment names.

A caller names the job (a capability id such as ``chat.compact``) and gives the
payload. The door finds the engine the owner assigned to that job, runs the job
on it through the kernel runner (which writes the one receipt, a kernel
operation), and gives back the answer. A job that does not complete raises one
typed error, :class:`EngineDoorError`.

Before the door, each caller built its own ``InvocationRequest``, its own
publish capture and its own outcome check (eight copies).
"""
from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Optional

DEFAULT_DEADLINE_SECONDS = 120.0


class EngineDoorError(RuntimeError):
    """A job did not complete. ``code`` is ``no_engine`` (no engine is
    assigned to the job) or ``failed`` (the engine ran and gave no answer).
    ``operation_id`` names the runner's receipt when the job reached it;
    ``error`` is the engine's own words."""

    def __init__(
        self, code: str, detail: str, *, operation_id: str = "", outcome: str = "",
        send_phase: str = "", error: str = "",
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.operation_id = operation_id
        self.outcome = outcome
        self.send_phase = send_phase
        self.error = error


@dataclass(frozen=True)
class Engine:
    """The engine a job runs on: the deployment revision, the assignment that
    named it and the profile it resolved through."""

    revision: str
    assignment: str = ""
    profile: str = ""
    #: The next engine in the assignment's chain: one retry when this one fails.
    fallback: Optional["Engine"] = field(default=None, compare=False)


@dataclass(frozen=True)
class Answer:
    """The engine's answer. ``result`` is what the adapter gave (a dict with
    ``output`` and ``model`` for a prompt); ``output`` and ``model`` are read
    from it."""

    result: Any
    operation_id: str
    engine: Engine
    outcome: str = "succeeded"
    send_phase: str = ""
    published: Any = None
    invocation_id: str = ""

    @property
    def output(self) -> str:
        if isinstance(self.result, dict):
            return str(self.result.get("output") or "")
        return str(self.result or "")

    @property
    def model(self) -> str:
        return str(self.result.get("model") or "") if isinstance(self.result, dict) else ""


def engine_for(broker: Any, job: str) -> Engine:
    """The engine assigned to ``job``. Raises ``EngineDoorError('no_engine')``."""
    from .project_update_service import _resolve_for_capability

    try:
        revision, assignment, profile = _resolve_for_capability(broker, job)
    except RuntimeError as exc:
        raise EngineDoorError("no_engine", str(exc)) from exc
    if not revision:
        raise EngineDoorError("no_engine", f"No engine is assigned to {job}")
    engine = Engine(str(revision), str(assignment or ""), str(profile or ""))
    return replace(engine, fallback=_next_in_chain(broker, job, engine))


def _next_in_chain(broker: Any, job: str, first: Engine) -> Optional[Engine]:
    """The second engine of the job's assignment chain, or ``None``."""
    try:
        from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
        from .project_update_service import _captured_deployment_revision

        plan = broker.inference_adoption_service.plans.resolve_route_plan(
            ROUTE_PLANNING_AUTHORITY, capability_id=job,
        )
        entries = sorted((e for e in (plan.get("entries") or ()) if e), key=lambda e: int(e.get("ordinal") or 0))
        for entry in entries:
            revision = str(entry.get("deployment_revision_id") or "")
            profile = str(entry.get("profile_id") or "")
            if not revision or revision == first.revision or (profile and profile == first.profile):
                continue
            if broker.database.deployment_revisions.get(revision) is None:
                revision = _captured_deployment_revision(broker.database, profile)
            if revision:
                return Engine(revision, first.assignment, profile)
    except Exception:
        return None
    return None


def egress_of(broker: Any, engine: Engine) -> str:
    """Where the engine's bytes go, as a lamp word: local, mesh,
    private_network or cloud (``unknown`` when the revision is not read)."""
    from ..inference_locality import deployment_lamp

    try:
        revision = broker.database.deployment_revisions.get(engine.revision)
    except Exception:
        revision = None
    if revision is None:
        return "unknown"
    return deployment_lamp(getattr(revision, "boundary", ""), getattr(revision, "endpoint", ""))


DEFAULT_CONTEXT_TOKENS = 16384


def room(broker: Any, engine: Engine, payload: Any, *, reserved_output_tokens: int) -> int:
    """Tokens left on the engine after ``payload`` and the reserved answer
    (one token for each 3.5 characters of the JSON payload, rounded up, plus
    16). Negative means the payload does not fit."""
    import json

    try:
        revision = broker.database.deployment_revisions.get(engine.revision)
        ceiling = int(getattr(revision, "context_ceiling", 0) or 0)
    except Exception:
        ceiling = 0
    ceiling = min(ceiling, DEFAULT_CONTEXT_TOKENS) if ceiling else DEFAULT_CONTEXT_TOKENS
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return ceiling - (-(-len(text) * 2 // 7) + 16 + int(reserved_output_tokens))


def with_memory(
    broker: Any, engine: Engine, payload: dict[str, Any], memory: Any, *,
    reserved_output_tokens: int, field: str = "user_prompt",
) -> dict[str, Any]:
    """``payload`` with the MEMORY block put before ``field``, cut to what the
    engine has room for. Memory never turns a job that fits into one that
    does not; any memory error leaves the payload as it is."""
    from .memory_grounding import fit_memory
    from .memory_grounding import with_memory as prefixed

    prompt = str(payload.get(field) or "")

    def build(candidate: Any) -> dict[str, Any]:
        return {**payload, field: prefixed(prompt, candidate)}

    try:
        fitted = fit_memory(memory(), lambda candidate: room(
            broker, engine, build(candidate), reserved_output_tokens=reserved_output_tokens) >= 0)
        return build(fitted)
    except Exception:
        return dict(payload)


def run(
    broker: Any,
    principal: Any,
    job: str,
    payload: Any,
    *,
    engine: Optional[Engine] = None,
    contract: str = "",
    contract_revision: str = "1",
    deadline: float = DEFAULT_DEADLINE_SECONDS,
    adapter: Any = None,
    result_ref: Optional[str] = None,
    invocation_id: str = "",
    stage: Optional[tuple[str, Callable[[Any], Mapping[str, Any]]]] = None,
) -> Answer:
    """Run ``job`` once on its assigned engine (or on ``engine`` when the
    caller already holds one) and return the answer.

    ``contract`` names the payload shape in the receipt (default: the job).
    ``adapter`` turns the payload into the provider call (default: a
    system/user prompt). ``stage`` is ``(kind, encoder)``: the answer is
    staged as that projection kind and published (``Answer.published``) only
    once the runner's receipt says the job succeeded. When the engine fails
    plainly (``failed`` or ``refused``) and the assignment names a next engine,
    the job runs once more on it; ``Answer.engine`` is the one that answered.
    Raises ``EngineDoorError``.
    """
    if engine is None:
        engine = engine_for(broker, job)
    try:
        return _run_once(
            broker, principal, job, payload, engine=engine, contract=contract,
            contract_revision=contract_revision, deadline=deadline, adapter=adapter,
            result_ref=result_ref, invocation_id=invocation_id, stage=stage,
        )
    except EngineDoorError as exc:
        # One retry on the next engine of the chain, only when the first one
        # said plainly that it did not answer.
        if engine.fallback is None or exc.outcome not in {"failed", "refused"}:
            raise
        return _run_once(
            broker, principal, job, payload, engine=engine.fallback, contract=contract,
            contract_revision=contract_revision, deadline=deadline, adapter=adapter,
            result_ref=result_ref, invocation_id=(invocation_id + "_r2") if invocation_id else "",
            stage=stage,
        )


def _run_once(
    broker: Any, principal: Any, job: str, payload: Any, *, engine: Engine, contract: str,
    contract_revision: str, deadline: float, adapter: Any, result_ref: Optional[str],
    invocation_id: str, stage: Any,
) -> Answer:
    from ..kernel.inference_runner import InvocationRequest, ServiceContract
    from ..kernel.runtime import _as_principal

    if adapter is None:
        from ..kernel.prompt_adapter import CanonicalPromptAdapter

        adapter = CanonicalPromptAdapter()
    contract = contract or job
    if stage is not None and not invocation_id:
        invocation_id = "door_" + uuid.uuid4().hex
    request = InvocationRequest(
        deployment_revision=engine.revision,
        definition_origin=ServiceContract.for_payload(contract, contract_revision, payload),
        deadline_at=time.time() + deadline,
        payload=payload,
        invocation_id=invocation_id,
    )
    captured: list[Any] = []
    ref = result_ref or f"{contract.replace('.', '-')}:{engine.assignment or engine.revision}"

    def _capture(value: Any) -> str:
        captured.append(value)
        return ref

    publish: Any = _capture
    if stage is not None:
        kind, encode = stage

        def _encode(value: Any) -> Mapping[str, Any]:
            captured.append(value)
            return encode(value)

        # The stager's publisher follows a dialect retry onto the attempt that ran.
        publish = broker.projection_stager.publisher(invocation_id, kind, _encode)
    with _as_principal(principal):
        outcome = broker.inference_runner.invoke(request, adapter, publish=publish)
    answer = _answer(outcome, captured, engine, job)
    if stage is not None:
        answer = replace(
            answer, published=broker.projection_stager.finalize(invocation_id), invocation_id=invocation_id,
        )
    return answer


def _answer(outcome: Any, captured: list[Any], engine: Engine, job: str) -> Answer:
    operation_id = str(getattr(outcome, "operation_id", "") or "")
    status = getattr(outcome, "outcome", None)
    state = str(status or "")
    send_phase = str(getattr(outcome, "send_phase", "") or "")
    failed = isinstance(status, str) and status != "succeeded"
    result = captured[0] if captured else getattr(outcome, "result", None)
    if failed or result is None:
        error = str(getattr(outcome, "error", "") or "")
        raise EngineDoorError(
            "failed", f"{job} did not complete: {error or state or 'no answer'}",
            operation_id=operation_id, outcome=state, send_phase=send_phase, error=error,
        )
    return Answer(result=result, operation_id=operation_id, engine=engine, outcome=state, send_phase=send_phase)

