"""HS-151-03: _chat_completion_deltas yields typed Delta objects.

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


# ---------------------------------------------------------------- tool-call helpers


def _fake_openai_tool_call_chunk(
    *,
    index: int = 0,
    tool_call_id: str | None = None,
    name: str | None = None,
    arguments: str = "",
    content: str | None = None,
    finish_reason: str | None = None,
) -> SimpleNamespace:
    """Simulate an OpenAI SDK ChatCompletionChunk with tool_calls."""
    tc_fn = SimpleNamespace(name=name, arguments=arguments)
    tc = SimpleNamespace(index=index, id=tool_call_id, function=tc_fn)
    delta = SimpleNamespace(
        content=content,
        reasoning_content=None,
        tool_calls=[tc],
    )
    choice = SimpleNamespace(delta=delta, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], usage=None)


def _fake_llamacpp_tool_call_chunk(
    *,
    index: int = 0,
    tool_call_id: str | None = None,
    name: str | None = None,
    arguments: str | dict = "",
) -> dict[str, Any]:
    """Simulate a llama.cpp streaming chunk with tool_calls (dict-based)."""
    tc: dict[str, Any] = {"index": index, "function": {}}
    if tool_call_id is not None:
        tc["id"] = tool_call_id
    if name is not None:
        tc["function"]["name"] = name
    tc["function"]["arguments"] = arguments
    return {"choices": [{"delta": {"tool_calls": [tc]}}]}


# ---------------------------------------------------------------- tool-call tests


def test_openai_two_tool_calls_interleaved_by_index() -> None:
    """OpenAI-shape: two tool calls interleaved by index, accumulated correctly."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        # Tool call 0 starts.
        _fake_openai_tool_call_chunk(index=0, tool_call_id="call_abc", name="get_weather", arguments='{"lo'),
        _fake_openai_tool_call_chunk(index=0, arguments='cation": "NYC"}'),
        # Tool call 1 starts while 0 is still going.
        _fake_openai_tool_call_chunk(index=1, tool_call_id="call_def", name="get_time", arguments='{"tz"'),
        _fake_openai_tool_call_chunk(index=1, arguments=': "UTC"}'),
        # Final usage chunk.
        SimpleNamespace(
            choices=[],
            usage=SimpleNamespace(prompt_tokens=30, completion_tokens=20, total_tokens=50),
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
    engine._remote_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "weather and time"}],
        temperature=0.7,
        max_tokens=1024,
        tools=[{"type": "function", "function": {"name": "get_weather"}}],
    ))

    # tool_call_delta deltas.
    tc_deltas = [d for d in deltas if d.kind == "tool_call_delta"]
    assert len(tc_deltas) == 4
    assert tc_deltas[0].meta["index"] == 0
    assert tc_deltas[0].meta["id"] == "call_abc"
    assert tc_deltas[0].meta["name"] == "get_weather"
    assert tc_deltas[0].meta["arguments_fragment"] == '{"lo'
    assert tc_deltas[2].meta["index"] == 1
    assert tc_deltas[2].meta["id"] == "call_def"
    assert tc_deltas[2].meta["name"] == "get_time"

    # Finalized tool_calls delta.
    tc_finals = [d for d in deltas if d.kind == "tool_calls"]
    assert len(tc_finals) == 1
    tool_calls = tc_finals[0].meta["tool_calls"]
    assert len(tool_calls) == 2
    assert tool_calls[0]["id"] == "call_abc"
    assert tool_calls[0]["name"] == "get_weather"
    assert tool_calls[0]["arguments"] == '{"location": "NYC"}'
    assert tool_calls[1]["id"] == "call_def"
    assert tool_calls[1]["name"] == "get_time"
    assert tool_calls[1]["arguments"] == '{"tz": "UTC"}'

    # tool_calls is before done.
    assert deltas[-1].kind == "done"
    assert deltas[-2].kind == "tool_calls" or deltas[-2].kind == "usage"


def test_llamacpp_single_tool_call() -> None:
    """llama.cpp-shape: single tool call with dict-based chunks."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_llamacpp_tool_call_chunk(
            index=0,
            tool_call_id="call_local",
            name="search",
            arguments='{"query": "test"}',
        ),
        _fake_llamacpp_chunk(
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        ),
    ]

    engine = MeetingIntel.__new__(MeetingIntel)
    engine._active_provider = "local"
    engine._llm = MagicMock()
    engine._llm.create_chat_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "search for test"}],
        temperature=0.7,
        max_tokens=1024,
        tools=[{"type": "function", "function": {"name": "search"}}],
    ))

    tc_deltas = [d for d in deltas if d.kind == "tool_call_delta"]
    assert len(tc_deltas) == 1
    assert tc_deltas[0].meta["name"] == "search"
    assert tc_deltas[0].meta["arguments_fragment"] == '{"query": "test"}'

    tc_finals = [d for d in deltas if d.kind == "tool_calls"]
    assert len(tc_finals) == 1
    assert tc_finals[0].meta["tool_calls"][0]["arguments"] == '{"query": "test"}'

    # Verify tools were forwarded to create_chat_completion.
    call_kwargs = engine._llm.create_chat_completion.call_args
    assert call_kwargs[1].get("tools") is not None or call_kwargs.kwargs.get("tools") is not None

    assert deltas[-1].kind == "done"


def test_llamacpp_tool_call_arguments_as_json_object() -> None:
    """llama.cpp defensively handles arguments as a complete JSON object (not string)."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_llamacpp_tool_call_chunk(
            index=0,
            tool_call_id="call_obj",
            name="lookup",
            arguments={"key": "value"},  # dict, not string
        ),
    ]

    engine = MeetingIntel.__new__(MeetingIntel)
    engine._active_provider = "local"
    engine._llm = MagicMock()
    engine._llm.create_chat_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "lookup"}],
        temperature=0.7,
        max_tokens=1024,
        tools=[{"type": "function", "function": {"name": "lookup"}}],
    ))

    tc_finals = [d for d in deltas if d.kind == "tool_calls"]
    assert len(tc_finals) == 1
    import json
    # Should be valid JSON string.
    parsed = json.loads(tc_finals[0].meta["tool_calls"][0]["arguments"])
    assert parsed == {"key": "value"}


def test_text_then_tool_calls() -> None:
    """OpenAI-shape: text content followed by tool calls in the same stream."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_openai_chunk(content="Let me help with that."),
        _fake_openai_tool_call_chunk(index=0, tool_call_id="call_123", name="do_thing", arguments='{"x": 1}'),
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
        [{"role": "user", "content": "do it"}],
        temperature=0.7,
        max_tokens=1024,
        tools=[{"type": "function", "function": {"name": "do_thing"}}],
    ))

    text_deltas = [d for d in deltas if d.kind == "text"]
    assert len(text_deltas) == 1
    assert text_deltas[0].text == "Let me help with that."

    tc_finals = [d for d in deltas if d.kind == "tool_calls"]
    assert len(tc_finals) == 1
    assert tc_finals[0].meta["tool_calls"][0]["name"] == "do_thing"

    assert deltas[-1].kind == "done"


def test_no_tools_request_unchanged() -> None:
    """When no tools are passed, stream behaves identically to before."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_openai_chunk(content="normal response"),
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
        # No tools parameter.
    ))

    # No tool_call_delta or tool_calls deltas.
    assert not any(d.kind.startswith("tool_call") for d in deltas)
    text_deltas = [d for d in deltas if d.kind == "text"]
    assert len(text_deltas) == 1
    assert text_deltas[0].text == "normal response"
    assert deltas[-1].kind == "done"


def test_streaming_prompt_adapter_forwards_tools() -> None:
    """StreamingPromptAdapter.dispatch_stream forwards tools/tool_choice to the engine."""
    import threading
    from holdspeak.kernel.prompt_adapter import StreamingPromptAdapter
    from holdspeak.kernel.inference_stream import Delta

    fake_deltas = [
        Delta(kind="tool_call_delta", meta={"index": 0, "id": "c1", "name": "fn", "arguments_fragment": '{"a":1}'}),
        Delta(kind="tool_calls", meta={"tool_calls": [{"id": "c1", "name": "fn", "arguments": '{"a":1}'}]}),
        Delta(kind="done"),
    ]

    engine = MagicMock()
    engine.run_prompt_stream = MagicMock(return_value=iter(fake_deltas))

    adapter = StreamingPromptAdapter()
    payload = {
        "messages": [{"role": "user", "content": "use tools"}],
        "tools": [{"type": "function", "function": {"name": "fn"}}],
        "tool_choice": "auto",
    }
    cancellation = threading.Event()

    result = list(adapter.dispatch_stream(engine, payload, cancellation))
    assert len(result) == 3
    assert result[0].kind == "tool_call_delta"
    assert result[1].kind == "tool_calls"
    assert result[2].kind == "done"

    # Verify tools/tool_choice were forwarded.
    call_kwargs = engine.run_prompt_stream.call_args
    assert call_kwargs.kwargs.get("tools") is not None
    assert call_kwargs.kwargs.get("tool_choice") == "auto"


def test_streaming_prompt_adapter_dispatch_sealed_output() -> None:
    """StreamingPromptAdapter.dispatch returns sealed {output, provider, model} -- no tool_calls."""
    import threading
    from holdspeak.kernel.prompt_adapter import StreamingPromptAdapter

    engine = MagicMock()
    engine.run_prompt_messages = MagicMock(return_value="the answer")
    engine.active_provider = "cloud"
    engine.active_model = "test-model"

    adapter = StreamingPromptAdapter()
    payload = {
        "messages": [{"role": "user", "content": "hi"}],
        "tools": [{"type": "function", "function": {"name": "fn"}}],
    }
    cancellation = threading.Event()

    result = adapter.dispatch(engine, payload, cancellation)
    assert set(result.keys()) == {"output", "provider", "model"}
    assert "tool_calls" not in result


def test_openai_finish_reason_tool_calls_tolerated() -> None:
    """Providers that emit finish_reason='tool_calls' are handled correctly."""
    from holdspeak.intel.engine import MeetingIntel

    chunks = [
        _fake_openai_tool_call_chunk(
            index=0, tool_call_id="call_fr", name="action",
            arguments='{"done": true}', finish_reason="tool_calls",
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
    engine._remote_completion = MagicMock(return_value=iter(chunks))
    engine._ensure_model_loaded = lambda: None

    deltas = list(engine._chat_completion_deltas(
        [{"role": "user", "content": "act"}],
        temperature=0.7,
        max_tokens=1024,
        tools=[{"type": "function", "function": {"name": "action"}}],
    ))

    tc_finals = [d for d in deltas if d.kind == "tool_calls"]
    assert len(tc_finals) == 1
    assert tc_finals[0].meta["tool_calls"][0]["name"] == "action"
    assert deltas[-1].kind == "done"
