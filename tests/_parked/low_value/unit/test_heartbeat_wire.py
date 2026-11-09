# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_heartbeat_wire.py to restore.

# ruff: noqa


# --- TestZeroEgressOnLANWatches::test_evaluate_due_local_stub_no_egress: P2: ends in 'assert True'; asserts nothing
# (was a method of class TestZeroEgressOnLANWatches)
def test_evaluate_due_local_stub_no_egress(self, db: Database) -> None:
    """Seed a watch with a local stub connector. Evaluate it with a
    snapshot_fetcher that tracks calls. Assert only the fetcher's own
    method is called (no external host)."""
    from holdspeak.services.watch_service import WatchService

    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES ('proj-lan', 'LAN Test', '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "datetime('now'), datetime('now'))",
        )
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, state, next_evaluation_at, evaluation_cadence_minutes, "
            " project_id, created_at, updated_at) "
            "VALUES ('w-lan-eval', 'local-stub', 'custom', 'local watch', "
            " '{}', '[]', 1, 'active', ?, 15, 'proj-lan', "
            " datetime('now'), datetime('now'))",
            (past,),
        )

    fetch_calls: list[str] = []

    def fake_fetcher(*args, **kwargs):
        fetch_calls.append("fetcher_called")
        return []

    ws = WatchService(db, snapshot_fetcher=fake_fetcher)

    # Patch subprocess.run to catch any CLI egress
    egress_calls: list[str] = []

    def track_subprocess(*args, **kwargs):
        egress_calls.append(f"subprocess: {args}")
        # Return a CompletedProcess with empty output so evaluation doesn't crash
        import subprocess
        return subprocess.CompletedProcess(args[0] if args else [], 0, stdout="[]", stderr="")

    with patch("subprocess.run", side_effect=track_subprocess):
        outcomes = ws.evaluate_due(OWNER)

    # The watch was evaluated (or skipped because the connector is unknown)
    # Either way, no external HTTP egress happened.
    # The snapshot_fetcher or subprocess.run may be called for the
    # connector's own adapter -- that is the consented read.
    # No ADDITIONAL host outside the connector should be contacted.
    # The key assertion: no requests module import or urllib egress.
    assert True  # structural pass -- the mock boundaries prove isolation


# --- TestHeartbeatSettings::test_default_settings: P1: five default literals
# (was a method of class TestHeartbeatSettings)
def test_default_settings(self, heartbeat_service) -> None:
    """Default settings are returned when no policy exists."""
    s = heartbeat_service.get_settings()
    assert s["sweep_every_minutes"] == 15
    assert s["quiet_hours"]["start"] == 22
    assert s["quiet_hours"]["end"] == 8
    assert s["notify"] == "edge"
    assert s["muted_projects"] == []


# --- TestMCPParity::test_heartbeat_tools_in_mcp_catalogue: P1: three names are in the tool list; the classification test beside it covers the authority
# (was a method of class TestMCPParity)
def test_heartbeat_tools_in_mcp_catalogue(self) -> None:
    """heartbeat.status, heartbeat.run_now, heartbeat.set are in the MCP catalogue."""
    from holdspeak.mcp.tools import TOOLS as MCP_TOOLS

    names = {t["name"] for t in MCP_TOOLS}
    assert "heartbeat.status" in names
    assert "heartbeat.run_now" in names
    assert "heartbeat.set" in names


# --- TestHubIntegration::test_hub_rhythm_contains_heartbeat_fields: P6: keys present and an isinstance; the after-sweep test checks the values
# (was a method of class TestHubIntegration)
def test_hub_rhythm_contains_heartbeat_fields(self, heartbeat_service) -> None:
    """hub_rhythm returns the heartbeat sweep fields."""
    rhythm = heartbeat_service.hub_rhythm()
    assert "sweepEveryMinutes" in rhythm
    assert "nextSweepAt" in rhythm
    assert "lastSweepAt" in rhythm
    assert "quiet" in rhythm
    assert "start" in rhythm["quiet"]
    assert "end" in rhythm["quiet"]
    assert "held" in rhythm["quiet"]
    assert "loops" in rhythm


# --- TestHubIntegration::test_hub_rhythm_contains_loops_key: P6: keys present and an isinstance; the after-sweep test checks the values
# (was a method of class TestHubIntegration)
def test_hub_rhythm_contains_loops_key(self, heartbeat_service) -> None:
    """Ensure loops is always present in rhythm even with no cadence."""
    rhythm = heartbeat_service.hub_rhythm()
    assert "loops" in rhythm
    assert isinstance(rhythm["loops"], int)
