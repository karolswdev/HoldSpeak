# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_chat_completion_deltas.py to restore.

# ruff: noqa


# --- test_streaming_prompt_adapter_dispatch_stream: P2: a MagicMock engine yields three deltas and the test asserts the same three come back, plus called_once
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


# --- test_streaming_prompt_adapter_dispatch_sealed_output: P6: asserts the result's key set from a MagicMock engine
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
