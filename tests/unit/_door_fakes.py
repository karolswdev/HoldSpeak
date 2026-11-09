"""A thread turn through the engine door, faked at the kernel runner.

The door (``engine_door.run_stream``) names the engine and calls
``broker.inference_runner.invoke_stream``; these fakes stand in for both.
A fake engine is a callable ``(request, on_delta) -> output`` that streams
its deltas and returns the answer, or raises :class:`EngineDown`.
"""
from __future__ import annotations

from typing import Any, Callable

import pytest

from holdspeak.kernel.inference_runner import InvocationOutcome
from holdspeak.kernel.inference_stream import Delta
from holdspeak.services import engine_door

ENGINE = engine_door.Engine("rev_test", "", "test-model")


class EngineDown(Exception):
    """The engine did not answer: ``outcome`` and ``send_phase`` as the runner says them."""

    def __init__(self, error: str = "engine down", *, outcome: str = "failed",
                 send_phase: str = "provider_no_generation") -> None:
        super().__init__(error)
        self.outcome, self.send_phase = outcome, send_phase


class Runner:
    """``invoke_stream`` over a fake engine; ``requests`` keeps each request."""

    def __init__(self, engine: Callable[[Any, Callable[[Delta], None]], str]) -> None:
        self.engine = engine
        self.requests: list[Any] = []

    def invoke_stream(self, request: Any, adapter: Any, *, on_delta: Any, publish: Any = None,
                      parent_context: Any = None, planned_node: str = "") -> InvocationOutcome:
        self.requests.append(request)
        operation_id = f"op_{len(self.requests)}"
        try:
            output = self.engine(request, on_delta)
        except EngineDown as down:
            return InvocationOutcome(operation_id, request.invocation_id, down.outcome, "", {}, str(down),
                                     send_phase=down.send_phase)
        ref = publish({"output": output}) if publish else ""
        return InvocationOutcome(operation_id, request.invocation_id, "succeeded", ref, {}, "",
                                 send_phase="provider_returned")


class Broker:
    """A broker with only the runner the door calls."""

    database = None

    def __init__(self, engine: Callable[[Any, Callable[[Delta], None]], str]) -> None:
        self.inference_runner = Runner(engine)


def words(output: str, *, usage: bool = True) -> Callable[[Any, Callable[[Delta], None]], str]:
    """An engine that streams ``output`` word by word."""

    def engine(_request: Any, on_delta: Callable[[Delta], None]) -> str:
        tokens = output.split(" ")
        for i, word in enumerate(tokens):
            on_delta(Delta(kind="text", text=word if i == 0 else " " + word))
        if usage:
            on_delta(Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": len(tokens)}))
        on_delta(Delta(kind="done"))
        return output

    return engine


@pytest.fixture
def door_engine(monkeypatch: pytest.MonkeyPatch) -> engine_door.Engine:
    """Every turn runs on :data:`ENGINE` (no assignment is read)."""
    monkeypatch.setattr(engine_door, "engine_for", lambda *_a, **_k: ENGINE)
    return ENGINE
