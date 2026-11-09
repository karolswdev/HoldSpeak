# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_reach_wire.py to restore.

# ruff: noqa


# --- test_protocol_version_is_streamable_http: P1/P3/P8: re-types a protocol string and palette names, reads contextvar and dataclass defaults, and greps SQL text for a column name
def test_protocol_version_is_streamable_http():
    """174-02: both transports announce the Streamable HTTP revision."""
    assert MCP_PROTOCOL_VERSION == "2025-03-26"


# --- test_origin_context_vars: P1/P3/P8: re-types a protocol string and palette names, reads contextvar and dataclass defaults, and greps SQL text for a column name
def test_origin_context_vars():
    """174-04: origin context vars are set during dispatch."""
    # Verify the context vars exist and default correctly.
    assert _origin.get("local") == "local"
    assert _caller.get("") == ""
    assert _caller_identity.get("") == ""


# --- test_palette_names: P1/P3/P8: re-types a protocol string and palette names, reads contextvar and dataclass defaults, and greps SQL text for a column name
def test_palette_names():
    """174-03: the four palette names resolve without error."""
    assert set(PALETTE_NAMES) == {"PROJECT", "SWEEP", "DESK", "ALL"}
    for name in PALETTE_NAMES:
        result = resolve_palette(name)
        assert isinstance(result, frozenset)
        assert len(result) > 0


# --- test_pipeline_event_defaults_to_local: P1/P3/P8: re-types a protocol string and palette names, reads contextvar and dataclass defaults, and greps SQL text for a column name
def test_pipeline_event_defaults_to_local():
    """174-04: PipelineEvent defaults to origin=local."""
    event = PipelineEvent(
        event_id="test",
        timestamp=0.0,
        service="test",
        method="test",
        principal_kind="owner",
        principal_identity="owner",
        args_summary="{}",
        result_summary="",
        error=None,
        error_code=None,
        duration_ms=0.0,
        correlation_id="",
        is_async=False,
    )
    assert event.origin == "local"
    assert event.caller == ""
    assert event.caller_identity == ""


# --- test_schema_has_origin_column: P1/P3/P8: re-types a protocol string and palette names, reads contextvar and dataclass defaults, and greps SQL text for a column name
def test_schema_has_origin_column():
    """C6: pipeline_events.origin TEXT NOT NULL DEFAULT 'local'."""
    from holdspeak.db.schema import SCHEMA_SQL
    assert "origin TEXT NOT NULL DEFAULT 'local'" in SCHEMA_SQL


# --- test_sqlite_observer_insert_has_origin: P1/P3/P8: re-types a protocol string and palette names, reads contextvar and dataclass defaults, and greps SQL text for a column name
def test_sqlite_observer_insert_has_origin():
    """174-04: the SQLiteObserver INSERT names origin, caller, caller_identity."""
    from holdspeak.services.sqlite_observer import _INSERT_SQL
    assert "origin" in _INSERT_SQL
    assert "caller" in _INSERT_SQL
    assert "caller_identity" in _INSERT_SQL


# --- test_desk_projection_to_dict_has_origin_keys: P1/P3/P8: re-types a protocol string and palette names, reads contextvar and dataclass defaults, and greps SQL text for a column name
def test_desk_projection_to_dict_has_origin_keys():
    """174-04: DeskProjection.to_dict() includes origin, caller, caller_identity."""
    from holdspeak.db.projections import DeskProjection
    proj = DeskProjection(
        id="test", projection_kind="receipt", subject_ref="s", subject_label="S",
        title="T", summary="", reason_code="", decision_kind="",
        attention_state="resolved", actual_destination=None, authority_basis=None,
        attempt=None, outcome="ok", timestamp="2026-01-01T00:00:00Z",
        correlation_id=None, source_kind="test", source_id="test-1",
        source_api="/test", detail_url="/",
        origin="remote", caller="100.64.0.5", caller_identity="sweep-runner",
    )
    d = proj.to_dict()
    assert d["origin"] == "remote"
    assert d["caller"] == "100.64.0.5"
    assert d["caller_identity"] == "sweep-runner"


# --- test_desk_projection_defaults_none: P1/P3/P8: re-types a protocol string and palette names, reads contextvar and dataclass defaults, and greps SQL text for a column name
def test_desk_projection_defaults_none():
    """174-04: origin/caller/caller_identity default to None."""
    from holdspeak.db.projections import DeskProjection
    proj = DeskProjection(
        id="test", projection_kind="receipt", subject_ref="s", subject_label="S",
        title="T", summary="", reason_code="", decision_kind="",
        attention_state="resolved", actual_destination=None, authority_basis=None,
        attempt=None, outcome="ok", timestamp="2026-01-01T00:00:00Z",
        correlation_id=None, source_kind="test", source_id="test-1",
        source_api="/test", detail_url="/",
    )
    d = proj.to_dict()
    assert d["origin"] is None
    assert d["caller"] is None
    assert d["caller_identity"] is None


# --- TestAgentCredentialStore::test_credential_has_id: P6/P1: checks keys are present, an id has 16 characters, and a default is local
# (was a method of class TestAgentCredentialStore)
def test_credential_has_id(self):
    store = AgentCredentialStore()
    cred = store.issue("runner", ttl_seconds=3600)
    assert cred.id  # non-empty
    assert len(cred.id) == 16  # hex format


# --- test_settings_get_shape: P6/P1: checks keys are present, an id has 16 characters, and a default is local
def test_settings_get_shape():
    """174-02: GET /api/settings/remote returns the expected shape."""
    app = _make_app()
    client = TestClient(app)
    resp = client.get(
        "/api/settings/remote",
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data
    assert "credentials" in data
    assert "active_count" in data
    assert "total_count" in data


# --- TestHeartbeatRunsOn::test_runs_on_defaults_to_local: P6/P1: checks keys are present, an id has 16 characters, and a default is local
# (was a method of class TestHeartbeatRunsOn)
def test_runs_on_defaults_to_local(self, _wire_db):
    """174-08: runs_on defaults to 'local'."""
    from holdspeak.services.heartbeat_service import HeartbeatService
    hb = HeartbeatService(_wire_db)
    settings = hb.get_settings()
    assert settings["runs_on"] == "local"
    assert settings["remote_hosts"] == []
    assert settings["last_remote_run_at"] is None
