"""The engine door: one job runs on its assigned engine, or raises one error."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.kernel.inference_runner import InvocationOutcome
from holdspeak.services import engine_door


class _Runner:
    def __init__(self, outcome: str = "succeeded", publish: Any = None, error: str = "") -> None:
        self.outcome, self.publish, self.error = outcome, publish, error
        self.requests: list[Any] = []

    def invoke(self, request: Any, adapter: Any, publish: Any = None) -> InvocationOutcome:
        self.requests.append((request, adapter))
        ref = ""
        if self.publish is not None and self.outcome == "succeeded":
            ref = publish(self.publish)
        return InvocationOutcome("op-1", "inv-1", self.outcome, ref, {}, self.error)


def _broker(runner: Any) -> Any:
    return SimpleNamespace(database=None, inference_runner=runner)


def test_a_job_runs_on_the_given_engine_and_returns_the_answer() -> None:
    runner = _Runner(publish={"output": "hello", "model": "m1"})
    answer = engine_door.run(
        _broker(runner), "owner", "chat.compact", {"user_prompt": "x"},
        engine=engine_door.Engine("rev-1", "asg-1"),
    )
    assert (answer.output, answer.model, answer.operation_id) == ("hello", "m1", "op-1")
    request, _adapter = runner.requests[0]
    assert request.deployment_revision == "rev-1"
    assert request.definition_origin.contract == "chat.compact"


def test_a_failed_job_raises_one_error_with_its_receipt() -> None:
    runner = _Runner(outcome="failed", error="connection refused")
    with pytest.raises(engine_door.EngineDoorError) as caught:
        engine_door.run(_broker(runner), "owner", "memory.page", {}, engine=engine_door.Engine("rev-1"))
    assert caught.value.code == "failed"
    assert caught.value.operation_id == "op-1"
    assert "memory.page did not complete: connection refused" == caught.value.detail


def test_a_job_with_no_engine_raises_no_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import project_update_service

    def _none(_broker: Any, job: str) -> Any:
        raise RuntimeError(f"No assignment for {job}")

    monkeypatch.setattr(project_update_service, "_resolve_for_capability", _none)
    with pytest.raises(engine_door.EngineDoorError) as caught:
        engine_door.run(_broker(_Runner()), "owner", "agent.plan", {})
    assert caught.value.code == "no_engine"
    assert isinstance(caught.value, RuntimeError)


def test_the_assignment_names_the_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import project_update_service

    monkeypatch.setattr(project_update_service, "_resolve_for_capability", lambda _b, _j: ("rev-9", "asg-9", "prof-9"))
    runner = _Runner(publish={"output": "ok"})
    answer = engine_door.run(_broker(runner), "owner", "agent.plan", {})
    assert answer.engine == engine_door.Engine("rev-9", "asg-9", "prof-9")
    assert runner.requests[0][0].deployment_revision == "rev-9"


class _ChainRunner:
    """Fails on rev-1 with ``first``; answers on any other revision."""

    def __init__(self, first: str) -> None:
        self.first, self.revisions = first, []

    def invoke(self, request: Any, adapter: Any, publish: Any = None) -> InvocationOutcome:
        self.revisions.append(request.deployment_revision)
        if request.deployment_revision == "rev-1":
            return InvocationOutcome("op-1", "inv-1", self.first, "", {}, "engine down")
        publish({"output": "from the next engine"})
        return InvocationOutcome("op-2", "inv-2", "succeeded", "ref", {}, "")


def test_a_plain_failure_runs_once_more_on_the_next_engine_of_the_chain() -> None:
    runner = _ChainRunner("failed")
    first = engine_door.Engine("rev-1", fallback=engine_door.Engine("rev-2"))
    answer = engine_door.run(_broker(runner), "owner", "ask.answer", {}, engine=first)
    assert runner.revisions == ["rev-1", "rev-2"]
    assert answer.output == "from the next engine" and answer.engine.revision == "rev-2"


@pytest.mark.parametrize("outcome", ["cancelled", "indeterminate"])
def test_a_stop_or_an_unknown_send_is_never_retried(outcome: str) -> None:
    runner = _ChainRunner(outcome)
    first = engine_door.Engine("rev-1", fallback=engine_door.Engine("rev-2"))
    with pytest.raises(engine_door.EngineDoorError):
        engine_door.run(_broker(runner), "owner", "ask.answer", {}, engine=first)
    assert runner.revisions == ["rev-1"]
