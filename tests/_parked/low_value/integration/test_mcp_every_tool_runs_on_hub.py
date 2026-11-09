# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_mcp_every_tool_runs_on_hub.py to restore.

# ruff: noqa


# --- test_the_sweep_fails_for_every_tool_when_no_tool_can_run: P2: a mutation test of the sweep itself (boots a second hub with every tool broken, 900 s budget); it proves the test, not the hub
@pytest.mark.timeout(900)
def test_the_sweep_fails_for_every_tool_when_no_tool_can_run(tmp_path: Path) -> None:
    """The mutation: dispatch raises ``RuntimeError("MCP executor is unavailable")`` for every tool."""
    home = tmp_path / "home"
    home.mkdir()
    hub = _Hub(home, "broken")
    try:
        count, broken = _sweep(hub)
    finally:
        hub.kill()
    assert count > 200, count
    assert len(broken) == count, f"the sweep passed {count - len(broken)} of {count} broken tools"
