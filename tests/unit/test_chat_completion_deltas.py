"""HS-150-03: _chat_completion_deltas yields typed Delta objects.

Tests use recorded chunk objects for both OpenAI SDK and llama.cpp shapes,
without touching the network.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.kernel.inference_stream import Delta


# ---------------------------------------------------------------- fakes


def _fake_openai_chunk(
    *,
    content: str | None = None,
    reasoning_content: str | None = None,
    usage: dict[str, int] | None = None,
) -> SimpleNamespace:
    """Simulate an OpenAI SDK ChatCompletionChunk.

    The SDK returns attribute-based objects, not dicts.
    """
    delta = SimpleNamespace(content=content, reasoning_content=reasoning_content)
    choice = SimpleNamespace(delta=delta)
    chunk = SimpleNamespace(
        choices=[choice] if content is not None or reasoning_content is not None else [],
        usage=SimpleNamespace(**usage) if usage else None,
    )
    return chunk


def _fake_llamacpp_chunk(
    *,
    content: str | None = None,
    reasoning_content: str | None = None,
    usage: dict[str, Any] | None = None,
    timings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Simulate a llama.cpp streaming chunk (dict-based)."""
    chunk: dict[str, Any] = {"choices": []}
    if content is not None or reasoning_content is not None:
        delta: dict[str, Any] = {}
        if content is not None:
            delta["content"] = content
        if reasoning_content is not None:
            delta["reasoning_content"] = reasoning_content
        chunk["choices"] = [{"delta": delta}]
    if usage is not None:
        chunk["usage"] = usage
    if timings is not None:
        chunk["timings"] = timings
    return chunk


class _FakeEngine:
    """A minimal MeetingIntel stand-in for unit tests."""

    def __init__(
        self,
        provider: str = "cloud",
        chunks: list | None = None,
    ) -> None:
        self._active_provider = provider
        self._chunks = chunks or []
        self.cloud_model = "test-model"
        self.cloud_base_url = "http://localhost:8080"
        self.cloud_reasoning_effort = None
        self.cloud_store = False
        self.temperature = 0.7
        self.max_tokens = 1024
        self._openai_client = MagicMock()
        self._llm = MagicMock()

    def _ensure_model_loaded(self) -> None:
        pass

    def _cloud_endpoint_key(self) -> str:
        return f"cloud:{self.cloud_base_url}"


# ---------------------------------------------------------------- tests


def test_openai_sdk_shape_text_reasoning_usage_done() -> None:
    """OpenAI SDK chunks: text, reasoning, usage, done."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_openai_chunk(content="Hello"),
        _fake_openai_chunk(content=" world"),
        _fake_openai_chunk(reasoning_content="Let me think..."),
        _fake_openai_chunk(content="!"),
        # Final usage chunk (choices=[]).
        SimpleNamespace(
            choices=[],
            usage=SimpleNamespace(prompt_tokens=15, completion_tokens=8, total_tokens=23),
        ),
    ]

    engine = MeetingIntel.__new__(MeetingIntel)
    engine._active_provider = "cloud"
    engine.cloud_model = "test-model"
    engine.cloud_base_url = "http://localhost:8080"
    engine.cloud_reasoning_effort = None
    engine.cloud_store = False
    engine.temperature = 0.7
    engine.max_tokens = 1024
    engine._openai_client = MagicMock()

    # Patch _remote_completion to return our fake chunks iterator.
    engine._remote_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "hi"}],
        temperature=0.7,
        max_tokens=1024,
    ))

    # Text deltas.
    text_deltas = [d for d in deltas if d.kind == "text"]
    assert len(text_deltas) == 3
    assert text_deltas[0].text == "Hello"
    assert text_deltas[1].text == " world"
    assert text_deltas[2].text == "!"

    # Reasoning delta.
    reasoning_deltas = [d for d in deltas if d.kind == "reasoning"]
    assert len(reasoning_deltas) == 1
    assert reasoning_deltas[0].text == "Let me think..."

    # Usage delta.
    usage_deltas = [d for d in deltas if d.kind == "usage"]
    assert len(usage_deltas) == 1
    assert usage_deltas[0].meta["prompt_tokens"] == 15
    assert usage_deltas[0].meta["completion_tokens"] == 8

    # Done delta (always last).
    assert deltas[-1].kind == "done"


def test_llamacpp_shape_text_usage_timings_done() -> None:
    """llama.cpp dict chunks: text, usage/timings on last chunk, done."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_llamacpp_chunk(content="Answer"),
        _fake_llamacpp_chunk(content=" is"),
        _fake_llamacpp_chunk(content=" 42"),
        # Last chunk with usage + timings (llama.cpp pattern).
        _fake_llamacpp_chunk(
            usage={"prompt_tokens": 20, "completion_tokens": 3},
            timings={"prompt_ms": 150.0, "predicted_ms": 80.0},
        ),
    ]

    engine = MeetingIntel.__new__(MeetingIntel)
    engine._active_provider = "local"
    engine._llm = MagicMock()
    engine._llm.create_chat_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "hi"}],
        temperature=0.7,
        max_tokens=1024,
    ))

    text_deltas = [d for d in deltas if d.kind == "text"]
    assert len(text_deltas) == 3
    assert "".join(d.text for d in text_deltas) == "Answer is 42"

    usage_deltas = [d for d in deltas if d.kind == "usage"]
    assert len(usage_deltas) == 1
    assert usage_deltas[0].meta["prompt_tokens"] == 20
    assert usage_deltas[0].meta["completion_tokens"] == 3
    assert usage_deltas[0].meta["timings"]["predicted_ms"] == 80.0

    assert deltas[-1].kind == "done"


def test_openai_no_usage_tolerates_absence() -> None:
    """When the endpoint does not support stream_options, no usage delta appears."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_openai_chunk(content="response"),
        # No usage chunk at the end.
    ]

    engine = MeetingIntel.__new__(MeetingIntel)
    engine._active_provider = "cloud"
    engine.cloud_model = "test-model"
    engine.cloud_base_url = "http://localhost:8080"
    engine.cloud_reasoning_effort = None
    engine.cloud_store = False
    engine.temperature = 0.7
    engine.max_tokens = 1024
    engine._openai_client = MagicMock()
    engine._remote_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "hi"}],
        temperature=0.7,
        max_tokens=1024,
    ))

    text_deltas = [d for d in deltas if d.kind == "text"]
    assert len(text_deltas) == 1
    assert text_deltas[0].text == "response"

    usage_deltas = [d for d in deltas if d.kind == "usage"]
    assert len(usage_deltas) == 0  # tolerate absence

    assert deltas[-1].kind == "done"


def test_openai_error_yields_error_delta() -> None:
    """A connection error during stream open yields an error delta."""
    from holdspeak.intel.engine import MeetingIntel, MeetingIntelError

    engine = MeetingIntel.__new__(MeetingIntel)
    engine._active_provider = "cloud"
    engine.cloud_model = "test-model"
    engine.cloud_base_url = "http://localhost:8080"
    engine.cloud_reasoning_effort = None
    engine.cloud_store = False
    engine.temperature = 0.7
    engine.max_tokens = 1024
    engine._openai_client = MagicMock()
    engine._remote_completion = MagicMock(
        side_effect=ConnectionError("refused"),
    )
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "hi"}],
        temperature=0.7,
        max_tokens=1024,
    ))

    assert len(deltas) == 1
    assert deltas[0].kind == "error"
    assert "refused" in deltas[0].text


def test_llamacpp_reasoning_content() -> None:
    """llama.cpp chunks with reasoning_content yield reasoning deltas."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_llamacpp_chunk(reasoning_content="Step 1: ..."),
        _fake_llamacpp_chunk(content="The answer"),
    ]

    engine = MeetingIntel.__new__(MeetingIntel)
    engine._active_provider = "local"
    engine._llm = MagicMock()
    engine._llm.create_chat_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "hi"}],
        temperature=0.7,
        max_tokens=1024,
    ))

    reasoning_deltas = [d for d in deltas if d.kind == "reasoning"]
    assert len(reasoning_deltas) == 1
    assert reasoning_deltas[0].text == "Step 1: ..."

    text_deltas = [d for d in deltas if d.kind == "text"]
    assert len(text_deltas) == 1
    assert text_deltas[0].text == "The answer"

    assert deltas[-1].kind == "done"


def test_streaming_prompt_adapter_dispatch_stream() -> None:
    """StreamingPromptAdapter.dispatch_stream yields deltas from the engine."""
    import threading
    from holdspeak.kernel.prompt_adapter import StreamingPromptAdapter
    from holdspeak.kernel.inference_stream import Delta

    fake_deltas = [
        Delta(kind="text", text="hello"),
        Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 1}),
        Delta(kind="done"),
    ]

    engine = MagicMock()
    engine.run_prompt_stream = MagicMock(return_value=iter(fake_deltas))

    adapter = StreamingPromptAdapter()
    payload = {"messages": [{"role": "user", "content": "hi"}]}
    cancellation = threading.Event()

    result = list(adapter.dispatch_stream(engine, payload, cancellation))
    assert len(result) == 3
    assert result[0].kind == "text"
    assert result[0].text == "hello"
    assert result[1].kind == "usage"
    assert result[2].kind == "done"
    engine.run_prompt_stream.assert_called_once()


def test_streaming_prompt_adapter_cancellation_stops_iteration() -> None:
    """StreamingPromptAdapter stops yielding when cancellation is set."""
    import threading
    from holdspeak.kernel.prompt_adapter import StreamingPromptAdapter
    from holdspeak.kernel.inference_stream import Delta

    many_deltas = [Delta(kind="text", text=f"tok{i}") for i in range(100)]
    many_deltas.append(Delta(kind="done"))

    engine = MagicMock()

    def _slow_stream(**kwargs):
        for d in many_deltas:
            yield d

    engine.run_prompt_stream = _slow_stream

    adapter = StreamingPromptAdapter()
    payload = {"messages": [{"role": "user", "content": "hi"}]}
    cancellation = threading.Event()

    results = []
    for delta in adapter.dispatch_stream(engine, payload, cancellation):
        results.append(delta)
        if len(results) == 3:
            cancellation.set()

    # Should have stopped around 3 deltas (the check is per-chunk).
    assert len(results) <= 4


def test_existing_str_stream_untouched() -> None:
    """_chat_completion_stream still yields str, byte-compatible for analyze(stream=True)."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_openai_chunk(content="Hello"),
        _fake_openai_chunk(content=" world"),
    ]

    engine = MeetingIntel.__new__(MeetingIntel)
    engine._active_provider = "cloud"
    engine.cloud_model = "test-model"
    engine.cloud_base_url = "http://localhost:8080"
    engine.cloud_reasoning_effort = None
    engine.cloud_store = False
    engine.temperature = 0.7
    engine.max_tokens = 1024
    engine._openai_client = MagicMock()
    engine._remote_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    pieces = list(engine._chat_completion_stream(
        [{"role": "user", "content": "hi"}],
        temperature=0.7,
        max_tokens=1024,
    ))

    # Existing caller gets plain strings.
    assert all(isinstance(p, str) for p in pieces)
    assert pieces == ["Hello", " world"]
