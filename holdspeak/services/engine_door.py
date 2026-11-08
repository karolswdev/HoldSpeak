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
from dataclasses import dataclass
from typing import Any, Optional

DEFAULT_DEADLINE_SECONDS = 120.0


class EngineDoorError(RuntimeError):
    """A job did not complete. ``code`` is ``no_engine`` (no engine is
    assigned to the job) or ``failed`` (the engine ran and gave no answer).
    ``operation_id`` names the runner's receipt when the job reached it."""

    def __init__(self, code: str, detail: str, *, operation_id: str = "", outcome: str = "") -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.operation_id = operation_id
        self.outcome = outcome


@dataclass(frozen=True)
class Engine:
    """The engine a job runs on: the deployment revision, the assignment that
    named it and the profile it resolved through."""

    revision: str
    assignment: str = ""
    profile: str = ""


@dataclass(frozen=True)
class Answer:
    """The engine's answer. ``result`` is what the adapter gave (a dict with
    ``output`` and ``model`` for a prompt); ``output`` and ``model`` are read
    from it."""

    result: Any
    operation_id: str
    engine: Engine

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
    return Engine(str(revision), str(assignment or ""), str(profile or ""))


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
) -> Answer:
    """Run ``job`` once on its assigned engine (or on ``engine`` when the
    caller already holds one) and return the answer.

    ``contract`` names the payload shape in the receipt (default: the job).
    ``adapter`` turns the payload into the provider call (default: a
    system/user prompt). Raises ``EngineDoorError``.
    """
    from ..kernel.inference_runner import InvocationRequest, ServiceContract
    from ..kernel.runtime import _as_principal

    if engine is None:
        engine = engine_for(broker, job)
    if adapter is None:
        from ..kernel.prompt_adapter import CanonicalPromptAdapter

        adapter = CanonicalPromptAdapter()
    contract = contract or job
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

    with _as_principal(principal):
        outcome = broker.inference_runner.invoke(request, adapter, publish=_capture)
    return _answer(outcome, captured, engine, job)


def _answer(outcome: Any, captured: list[Any], engine: Engine, job: str) -> Answer:
    operation_id = str(getattr(outcome, "operation_id", "") or "")
    status = getattr(outcome, "outcome", None)
    failed = isinstance(status, str) and status != "succeeded"
    result = captured[0] if captured else getattr(outcome, "result", None)
    if failed or result is None:
        state = status if isinstance(status, str) else ""
        detail = str(getattr(outcome, "error", "") or state or "no answer")
        raise EngineDoorError("failed", f"{job} did not complete: {detail}", operation_id=operation_id, outcome=state)
    return Answer(result=result, operation_id=operation_id, engine=engine)

