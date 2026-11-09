# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_plugin_job.py to restore.

# ruff: noqa


# --- test_plugin_job_tools_in_catalogue: P6/P2: catalogue names and schema flags; a stub's summary echoed back
def test_plugin_job_tools_in_catalogue() -> None:
    """All four plugin_job.* tools appear in the catalogue with closed schemas."""
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    tools = response["result"]["tools"]
    names = {t["name"] for t in tools}
    expected = {"plugin_job.list", "plugin_job.summary", "plugin_job.retry", "plugin_job.cancel"}
    assert expected <= names, f"Missing: {expected - names}"

    for t in tools:
        if t["name"] in expected:
            assert t["inputSchema"]["type"] == "object"
            assert t["inputSchema"]["additionalProperties"] is False


# --- test_plugin_job_summary_dispatch: P6/P2: catalogue names and schema flags; a stub's summary echoed back
def test_plugin_job_summary_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_service(monkeypatch)
    result = _call("plugin_job.summary", {})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["total_jobs"] == 10
    assert calls["summary"] == [{}]
