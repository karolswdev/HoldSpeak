# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_ask.py to restore.

# ruff: noqa


# --- test_dispatch_ask_cancel: P2: the stub echoes the id it was given and the test reads the echo back
def test_dispatch_ask_cancel(_patch_ask) -> None:
    stub = _patch_ask
    payload = _call_ok("ask.cancel", {"invocation_id": "ask_abc123"})
    assert payload["invocation_id"] == "ask_abc123"
    assert payload["disposition"] == "cancelled"
    assert stub.calls[-1][0] == "cancel"


# --- test_error_ask_cancel_unknown_invocation_id: P2: the stub echoes the id it was given and the test reads the echo back
def test_error_ask_cancel_unknown_invocation_id(_patch_ask) -> None:
    """Unknown invocation_id: cancel dispatches to the service which may raise;
    this test verifies the dispatch reaches the service and doesn't crash."""
    stub = _patch_ask
    # The stub returns successfully even for unknown IDs; what matters is
    # that the dispatch reaches the service.  For a real unknown-id error,
    # the service would raise and server.py would catch it as isError.
    payload = _call_ok("ask.cancel", {"invocation_id": "ask_nonexistent"})
    assert payload["invocation_id"] == "ask_nonexistent"
    assert stub.calls[-1][0] == "cancel"


# --- test_ask_run_wraps_async_via_run: P2/P5: asserts a stub's answer passes through the private _run wrapper; test_mcp_aio tests run_async for real
def test_ask_run_wraps_async_via_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """ask.run dispatches the AskService.ask coroutine through _run()."""
    canned = {
        "output": "Wrapped answer.",
        "model": "wrapped-model",
        "provider": "test",
        "actual_placement": {},
        "egress": {"scope": "local"},
    }

    async def fake_ask(principal, *, question, **kw):
        return canned

    stub = StubAskService()
    stub.ask = fake_ask  # type: ignore[assignment]
    monkeypatch.setattr(ask_family, "_service", lambda: stub)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

    payload = _call_ok("ask.run", {"question": "test wrapping"})
    assert payload["output"] == "Wrapped answer."
    assert payload["model"] == "wrapped-model"


# --- test_run_helper_works_outside_event_loop: P2/P5: asserts a stub's answer passes through the private _run wrapper; test_mcp_aio tests run_async for real
def test_run_helper_works_outside_event_loop() -> None:
    """The local _run() helper can execute a coroutine when no loop is active."""
    async def simple_coro():
        return {"ok": True}

    result = ask_family._run(simple_coro())
    assert result == {"ok": True}


# --- test_ask_tools_have_closed_schemas: P6: asserts each schema dict has type=object and additionalProperties=False
def test_ask_tools_have_closed_schemas() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    for tool in response["result"]["tools"]:
        if tool["name"].startswith("ask."):
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert schema["additionalProperties"] is False
