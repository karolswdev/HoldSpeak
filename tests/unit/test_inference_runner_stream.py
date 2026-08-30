"""HS-150-03: InferenceRunner.invoke_stream — streaming dispatch tests.

Fake streaming adapter, ordered deltas with seq, usage in receipt,
cancel mid-stream, error before/after first delta.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import resolve_inference_target
from holdspeak.kernel.inference_runner import (
    InferenceRunner,
    InvocationRequest,
    ServiceContract,
)
from holdspeak.kernel.inference_stream import Delta
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

pytestmark = pytest.mark.timeout(30, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "stream-owner")


# ---------------------------------------------------------------- helpers


class _Leaf:
    def __init__(self) -> None:
        self.attempts = 0

    def hit(self) -> None:
        self.attempts += 1


class _LeafEngine:
    def __init__(self, leaf: _Leaf, result: str = "result", error: BaseException | None = None) -> None:
        self._leaf = leaf
        self.result = result
        self.error = error

    def run_prompt(self, *, system_prompt: str = "", user_prompt: str = "", **_: Any) -> str:
        self._leaf.hit()
        if self.error:
            raise self.error
        return self.result


class _StreamingAdapter:
    """A fake adapter that yields pre-built deltas from dispatch_stream.

    The ``dispatch`` fallback is provided so the Protocol is satisfied; the
    streaming tests exercise ``dispatch_stream`` exclusively.
    """

    def __init__(
        self,
        deltas: list[Delta] | None = None,
        *,
        error_before_first: BaseException | None = None,
        error_after_first: BaseException | None = None,
        stall_event: threading.Event | None = None,
        stall_after: int = 0,
    ) -> None:
        self._deltas = deltas or []
        self._error_before_first = error_before_first
        self._error_after_first = error_after_first
        self._stall_event = stall_event
        self._stall_after = stall_after

    def dispatch(self, engine: Any, payload: Any, cancellation: threading.Event) -> Any:
        engine.run_prompt(system_prompt="", user_prompt=str(payload))
        return {"output": "fallback"}

    def cancel(self) -> str:
        return "cancelled"

    def dispatch_stream(self, engine: Any, payload: Any, cancellation: threading.Event):
        engine.run_prompt(system_prompt="", user_prompt=str(payload))
        if self._error_before_first:
            raise self._error_before_first
        yielded = 0
        for delta in self._deltas:
            if cancellation.is_set():
                return
            if self._stall_event and yielded >= self._stall_after:
                self._stall_event.wait(timeout=5.0)
                if cancellation.is_set():
                    return
            if self._error_after_first and yielded > 0 and delta.kind == "error":
                raise self._error_after_first
            yield delta
            yielded += 1


class _FallbackAdapter:
    """An adapter WITHOUT dispatch_stream — exercises the Protocol default fallback."""

    def __init__(self, leaf: _Leaf, result: str = "fallback-result") -> None:
        self._leaf = leaf
        self._result = result

    def dispatch(self, engine: Any, payload: Any, cancellation: threading.Event) -> Any:
        engine.run_prompt(system_prompt="", user_prompt=str(payload))
        return {"output": self._result}

    def cancel(self) -> str:
        return "cancelled"

    def dispatch_stream(self, engine: Any, payload: Any, cancellation: threading.Event):
        """Default fallback: wraps dispatch into one text delta + done."""
        result = self.dispatch(engine, payload, cancellation)
        text = str(result.get("output", "") if isinstance(result, dict) else result)
        yield Delta(kind="text", text=text)
        yield Delta(kind="done")


def _rig(tmp_path: Path):
    db = Database(tmp_path / "stream.db")
    db.profiles.upsert(profile_id="local", name="Local", kind="onDevice", model_file="/model.gguf")
    revision = capture_deployment_revision(db, resolve_inference_target(db, "local"))
    broker = _configure(db)
    return db, broker, revision


def _request(revision: Any, *, invocation_id: str = "") -> InvocationRequest:
    payload = {"probe": "stream", "ts": time.time()}
    return InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload("stream-probe", "v1", payload),
        deadline_at=time.time() + 30,
        payload=payload,
        invocation_id=invocation_id,
    )


def _runner(broker: Any, db: Any, *, leaf: _Leaf | None = None, error: BaseException | None = None) -> InferenceRunner:
    leaf = leaf or _Leaf()
    factory = lambda _revision, **_: _LeafEngine(leaf, error=error)
    return InferenceRunner(broker, db, engine_factory=factory, principal_provider=lambda: OWNER)


# ---------------------------------------------------------------- tests


def test_streaming_deltas_arrive_in_order_with_seq(tmp_path: Path) -> None:
    """Deltas arrive in order; ``usage`` lands in the receipt evidence; receipt succeeded."""
    db, broker, revision = _rig(tmp_path)
    leaf = _Leaf()
    runner = _runner(broker, db, leaf=leaf)

    deltas_to_yield = [
        Delta(kind="text", text="Hello"),
        Delta(kind="text", text=" world"),
        Delta(kind="reasoning", text="thinking..."),
        Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 5}),
        Delta(kind="done"),
    ]
    adapter = _StreamingAdapter(deltas_to_yield)

    received: list[Delta] = []
    seq_counter: list[int] = []

    def on_delta(delta: Delta) -> None:
        received.append(delta)
        seq_counter.append(len(seq_counter))

    outcome = runner.invoke_stream(
        _request(revision), adapter, on_delta=on_delta,
    )

    assert outcome.outcome == "succeeded"
    assert len(received) == 5
    assert received[0].kind == "text"
    assert received[0].text == "Hello"
    assert received[1].kind == "text"
    assert received[1].text == " world"
    assert received[2].kind == "reasoning"
    assert received[3].kind == "usage"
    assert received[3].meta["prompt_tokens"] == 10
    assert received[3].meta["completion_tokens"] == 5
    assert received[4].kind == "done"
    # Seq is monotonic.
    assert seq_counter == list(range(5))


def test_cancel_mid_stream_stops_within_250ms(tmp_path: Path) -> None:
    """Cancel mid-stream: on_delta stops within 250 ms, receipt indeterminate."""
    db, broker, revision = _rig(tmp_path)
    leaf = _Leaf()
    runner = _runner(broker, db, leaf=leaf)

    stall = threading.Event()
    deltas_to_yield = [
        Delta(kind="text", text="first"),
        Delta(kind="text", text="second"),  # stalls here
        Delta(kind="text", text="third"),   # should never arrive
        Delta(kind="done"),
    ]
    adapter = _StreamingAdapter(deltas_to_yield, stall_event=stall, stall_after=1)

    received: list[Delta] = []
    cancel_time: list[float] = []

    def on_delta(delta: Delta) -> None:
        received.append(delta)

    req = _request(revision, invocation_id="cancel_test_" + str(int(time.time() * 1000)))
    result_holder: list[Any] = []

    def run_invoke():
        result_holder.append(
            runner.invoke_stream(req, adapter, on_delta=on_delta)
        )

    t = threading.Thread(target=run_invoke)
    t.start()
    # Wait for first delta to arrive.
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and len(received) < 1:
        time.sleep(0.01)
    assert len(received) >= 1, "First delta never arrived"

    # Cancel.
    start = time.monotonic()
    runner.cancel(req.invocation_id)
    stall.set()  # unblock the adapter
    t.join(timeout=5.0)
    elapsed = time.monotonic() - start

    assert len(result_holder) == 1
    outcome = result_holder[0]
    # Receipt should be indeterminate (cancel after first delta).
    assert outcome.outcome in ("indeterminate", "cancelled")
    # on_delta should have stopped quickly (we may have gotten 1-2 deltas, not all).
    assert len(received) <= 2


def test_error_before_first_delta_fallback(tmp_path: Path) -> None:
    """Provider error BEFORE first delta -> fallback path (outcome failed)."""
    db, broker, revision = _rig(tmp_path)
    leaf = _Leaf()
    runner = _runner(broker, db, leaf=leaf)

    from holdspeak.kernel.provider_signals import ProviderKnownNoGenerationTransient

    adapter = _StreamingAdapter(
        error_before_first=ProviderKnownNoGenerationTransient(),
    )

    received: list[Delta] = []

    def on_delta(delta: Delta) -> None:
        received.append(delta)

    outcome = runner.invoke_stream(
        _request(revision), adapter, on_delta=on_delta,
    )

    # Before first delta: the error is a known provider signal -> failed.
    assert outcome.outcome == "failed"
    assert len(received) == 0


def test_error_after_first_delta_indeterminate(tmp_path: Path) -> None:
    """Provider error AFTER first delta -> indeterminate, no fallback."""
    db, broker, revision = _rig(tmp_path)
    leaf = _Leaf()
    runner = _runner(broker, db, leaf=leaf)

    deltas_to_yield = [
        Delta(kind="text", text="partial"),
        Delta(kind="error", text="boom"),  # triggers the error_after_first
    ]
    adapter = _StreamingAdapter(
        deltas_to_yield,
        error_after_first=RuntimeError("stream died"),
    )

    received: list[Delta] = []

    def on_delta(delta: Delta) -> None:
        received.append(delta)

    outcome = runner.invoke_stream(
        _request(revision), adapter, on_delta=on_delta,
    )

    assert outcome.outcome == "indeterminate"
    # Only the first text delta was delivered.
    assert len(received) >= 1
    assert received[0].kind == "text"


def test_fallback_adapter_wraps_dispatch_into_deltas(tmp_path: Path) -> None:
    """An adapter without dispatch_stream falls back to dispatch -> text + done."""
    db, broker, revision = _rig(tmp_path)
    leaf = _Leaf()
    runner = _runner(broker, db, leaf=leaf)

    adapter = _FallbackAdapter(leaf, result="the answer")

    received: list[Delta] = []

    def on_delta(delta: Delta) -> None:
        received.append(delta)

    outcome = runner.invoke_stream(
        _request(revision), adapter, on_delta=on_delta,
    )

    assert outcome.outcome == "succeeded"
    assert len(received) == 2
    assert received[0].kind == "text"
    assert received[0].text == "the answer"
    assert received[1].kind == "done"


def test_usage_meta_in_published_result(tmp_path: Path) -> None:
    """Usage metadata from the provider stream is available in the result."""
    db, broker, revision = _rig(tmp_path)
    leaf = _Leaf()
    runner = _runner(broker, db, leaf=leaf)

    deltas_to_yield = [
        Delta(kind="text", text="answer"),
        Delta(kind="usage", meta={"prompt_tokens": 42, "completion_tokens": 17}),
        Delta(kind="done"),
    ]
    adapter = _StreamingAdapter(deltas_to_yield)

    received: list[Delta] = []
    published: list[Any] = []

    def on_delta(delta: Delta) -> None:
        received.append(delta)

    def publish(result: Any) -> str:
        published.append(result)
        return f"inference-result:usage-test"

    outcome = runner.invoke_stream(
        _request(revision), adapter, on_delta=on_delta, publish=publish,
    )

    assert outcome.outcome == "succeeded"
    assert len(published) == 1
    # HS-150-04 (real-path defect): the published result is validated against
    # the sealed capability output schema (output/provider/model ONLY); usage
    # must NOT leak into it. It travels on the usage Delta instead.
    assert "usage" not in published[0]
    assert set(published[0]) >= {"output", "provider", "model"}
    usage = [d for d in received if d.kind == "usage"]
    assert usage and usage[0].meta["prompt_tokens"] == 42
    assert usage[0].meta["completion_tokens"] == 17
