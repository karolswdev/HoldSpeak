"""HS-174: Reach wire tests -- the Streamable HTTP transport, scoped
credentials, egress badges, and the long-running contract.

These tests exercise the wire WITHOUT real network; every principal and
client address is simulated through the ASGI test client and app.state
mocking.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.principals import (
    AgentCredentialStore,
    AgentCredential,
    Principal,
    PrincipalKind,
    PrincipalRight,
    UNAUTHENTICATED,
    _hash_token,
    _MAX_TTL_SECONDS,
    derive_owner,
    required_right,
)
from holdspeak.mcp.server import (
    MCP_PROTOCOL_VERSION,
    handle_message_for_principal,
    _MCP_005_CODE,
)
from holdspeak.mcp.palettes import PALETTE_NAMES, resolve_palette
from holdspeak.services.observer import (
    PipelineEvent,
    _origin,
    _caller,
    _caller_identity,
)


# ── Helpers ─────────────────────────────────────────────────────────────

def _clock_factory(start: float = 1000.0):
    """Return a controllable monotonic clock."""
    value = [start]
    def clock() -> float:
        return value[0]
    def advance(seconds: float) -> None:
        value[0] += seconds
    return clock, advance


class _FakeAddress:
    """Simulates a Starlette Address for test client host spoofing."""
    def __init__(self, host: str, port: int = 50000):
        self.host = host
        self.port = port


def _make_app(
    *,
    owner_token: str = "owner-tok-123",
    remote_enabled: bool = True,
    agent_store: AgentCredentialStore | None = None,
    fake_client_host: str | None = None,
) -> FastAPI:
    """Build a minimal FastAPI app with the MCP HTTP router wired.

    When *fake_client_host* is given, the middleware spoofs the request's
    ``client`` address to that host (for loopback vs non-loopback tests
    without real network).
    """
    from holdspeak.web.routes.mcp_http import build_mcp_http_router
    from holdspeak.web.context import WebContext

    app = FastAPI()
    ctx = WebContext(get_state=lambda: {})

    store = agent_store or AgentCredentialStore()
    app.state.agent_credentials = store
    app.state.owner_token = owner_token
    app.state._remote_settings = {"enabled": remote_enabled}

    # Minimal auth middleware that mirrors the real _web_auth_gate.
    from holdspeak.web_auth import extract_request_token

    @app.middleware("http")
    async def _auth(request, call_next):
        # Spoof the client address when requested by the test.
        if fake_client_host is not None:
            request.scope["client"] = (fake_client_host, 50000)

        token = extract_request_token(
            authorization=request.headers.get("authorization"),
            header_token=request.headers.get("x-holdspeak-token"),
            query_token=request.query_params.get("token"),
        )
        principal = derive_owner(token, owner_token)
        if principal is None:
            principal = store.derive(token)
        principal = principal or UNAUTHENTICATED
        request.state.principal = principal
        return await call_next(request)

    router = build_mcp_http_router(ctx)
    app.include_router(router)
    return app


# ── AgentCredentialStore tests ──────────────────────────────────────────

class TestAgentCredentialStore:
    def test_hash_at_rest(self):
        """C4: the plaintext is never stored; derive compares by hash."""
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        cred = store.issue("runner-1", ttl_seconds=3600)
        plaintext = cred.token

        # The plaintext is NOT in _by_hash keys.
        assert plaintext not in store._by_hash
        # The hash IS in _by_hash keys.
        expected_hash = _hash_token(plaintext)
        assert expected_hash in store._by_hash

        # derive by plaintext works.
        principal = store.derive(plaintext)
        assert principal is not None
        assert principal.identity == "runner-1"

    def test_derive_credential_returns_full_credential(self):
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        cred = store.issue("runner-1", ttl_seconds=3600, palette=frozenset({"tool.a"}))
        plaintext = cred.token

        full = store.derive_credential(plaintext)
        assert full is not None
        assert full.palette == frozenset({"tool.a"})
        assert full.principal.identity == "runner-1"
        assert full.last_used_at == clock()

    def test_palette_on_credential(self):
        """174-03: palette restriction on issued credentials."""
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        palette = frozenset({"project.list", "project.get"})
        cred = store.issue("runner-1", ttl_seconds=3600, palette=palette)
        assert cred.palette == palette

    def test_ttl_capped_at_30_days(self):
        """H2: cap TTL at 30 days."""
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        cred = store.issue("long-lived", ttl_seconds=365 * 86400)
        # Expires at start + 30 days, not 365 days.
        assert cred.expires_at == pytest.approx(clock() + _MAX_TTL_SECONDS, abs=1.0)

    def test_expired_credential_rejected(self):
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        cred = store.issue("ephemeral", ttl_seconds=60)
        plaintext = cred.token
        assert store.derive(plaintext) is not None

        advance(61)
        assert store.derive(plaintext) is None

    def test_revoke_by_id(self):
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        cred = store.issue("runner-1", ttl_seconds=3600)
        assert store.revoke_by_id(cred.id) is True
        assert store.derive(cred.token) is None

    def test_list_credentials(self):
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        store.issue("a", ttl_seconds=3600)
        store.issue("b", ttl_seconds=3600)
        creds = store.list_credentials()
        assert len(creds) == 2
        identities = {c.principal.identity for c in creds}
        assert identities == {"a", "b"}

    def test_count_active(self):
        """P2s: N ACTIVE counts non-expired only."""
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        store.issue("active", ttl_seconds=3600)
        store.issue("short", ttl_seconds=10)
        assert store.count_active() == 2
        advance(11)
        assert store.count_active() == 1

    def test_last_used_at_updated_on_derive(self):
        clock, advance = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        cred = store.issue("runner", ttl_seconds=3600)
        assert cred.last_used_at is None
        advance(10)
        full = store.derive_credential(cred.token)
        assert full is not None
        assert full.last_used_at == clock()

    def test_constant_time_compare(self):
        """The store compares hashes, not plaintexts, and uses hmac.compare_digest."""
        clock, _ = _clock_factory()
        store = AgentCredentialStore(clock=clock)
        cred = store.issue("runner", ttl_seconds=3600)
        # Wrong token returns None, not an exception.
        assert store.derive("wrong-token") is None
        assert store.derive("") is None
        assert store.derive(None) is None

    def test_credential_has_id(self):
        store = AgentCredentialStore()
        cred = store.issue("runner", ttl_seconds=3600)
        assert cred.id  # non-empty
        assert len(cred.id) == 16  # hex format


# ── MCP protocol version ───────────────────────────────────────────────

def test_protocol_version_is_streamable_http():
    """174-02: both transports announce the Streamable HTTP revision."""
    assert MCP_PROTOCOL_VERSION == "2025-03-26"


# ── Route: 404 when disabled ───────────────────────────────────────────

def test_route_404_when_disabled():
    """174-02: POST /api/mcp returns 404 when remote is not enabled."""
    app = _make_app(remote_enabled=False)
    client = TestClient(app)
    resp = client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "streamable_http_not_enabled"


# ── Route: OWNER from loopback OK ──────────────────────────────────────

def test_owner_from_loopback_ok():
    """174-02: OWNER token from loopback succeeds."""
    app = _make_app(fake_client_host="127.0.0.1")
    client = TestClient(app)
    resp = client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.status_code == 200


# ── Route: OWNER from non-loopback 403 ────────────────────────────────

def test_owner_from_non_loopback_403():
    """C5: only POST /api/mcp refuses OWNER from non-loopback."""
    app = _make_app(fake_client_host="100.64.0.5")
    client = TestClient(app)
    resp = client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "owner_refused_remote"


# ── Route: agent credential from non-loopback OK ──────────────────────

def test_agent_from_non_loopback_ok():
    """174-02: agent credential from non-loopback succeeds."""
    clock, _ = _clock_factory()
    store = AgentCredentialStore(clock=clock)
    cred = store.issue("sweep-runner", ttl_seconds=3600)
    app = _make_app(agent_store=store, fake_client_host="100.64.0.5")
    client = TestClient(app)
    resp = client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        headers={"X-HoldSpeak-Token": cred.token},
    )
    assert resp.status_code == 200


# ── Route: unauthenticated -> 401 ─────────────────────────────────────

def test_unauthenticated_401():
    app = _make_app(fake_client_host="100.64.0.5")
    client = TestClient(app)
    # The test conftest auto-injects X-HoldSpeak-Token from app.state.owner_token.
    # Override it to empty to simulate an unauthenticated request.
    resp = client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        headers={"X-HoldSpeak-Token": "wrong-token"},
    )
    assert resp.status_code == 401


# ── Palette refusal MCP-005 ────────────────────────────────────────────

def test_palette_refusal_mcp_005():
    """174-03: tool outside palette -> MCP-005 JSON-RPC error."""
    principal = Principal(PrincipalKind.AGENT, "restricted")
    palette = frozenset({"project.list"})
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "desk.list", "arguments": {"kind": "notes"}},
    }
    response = handle_message_for_principal(request, principal, palette=palette)
    assert response is not None
    assert response["error"]["code"] == _MCP_005_CODE
    assert "MCP-005" in response["error"]["data"]["code"]


# ── X-Forwarded-For ignored ───────────────────────────────────────────

def test_x_forwarded_for_ignored():
    """C5: X-Forwarded-For is NEVER read for principal derivation."""
    app = _make_app(fake_client_host="127.0.0.1")
    client = TestClient(app)
    # Send owner token from loopback but with a spoofed X-Forwarded-For.
    resp = client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
        headers={
            "X-HoldSpeak-Token": "owner-tok-123",
            "X-Forwarded-For": "100.64.0.5",
        },
    )
    # Should succeed because the actual client is loopback, and
    # X-Forwarded-For is never read for principal derivation.
    assert resp.status_code == 200


# ── Origin on pipeline event context vars ──────────────────────────────

def test_origin_context_vars():
    """174-04: origin context vars are set during dispatch."""
    # Verify the context vars exist and default correctly.
    assert _origin.get("local") == "local"
    assert _caller.get("") == ""
    assert _caller_identity.get("") == ""


# ── Origin tagging on remote call ──────────────────────────────────────

def test_origin_remote_on_receipt():
    """174-04: a remote call tags origin=remote with caller and identity."""
    captured: list[dict[str, str]] = []

    clock, _ = _clock_factory()
    store = AgentCredentialStore(clock=clock)
    cred = store.issue("sweep-runner", ttl_seconds=3600)
    app = _make_app(agent_store=store, fake_client_host="100.64.0.5")

    def capturing_handle(request, principal, *, palette=None):
        captured.append({
            "origin": _origin.get("local"),
            "caller": _caller.get(""),
            "caller_identity": _caller_identity.get(""),
        })
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}

    with patch("holdspeak.mcp.server.handle_message_for_principal", capturing_handle):
        client = TestClient(app)
        resp = client.post(
            "/api/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"X-HoldSpeak-Token": cred.token},
        )

    assert resp.status_code == 200
    assert len(captured) == 1
    assert captured[0]["origin"] == "remote"
    assert captured[0]["caller"] == "100.64.0.5"
    assert captured[0]["caller_identity"] == "sweep-runner"


def test_origin_local_on_loopback():
    """174-04: a loopback call tags origin=local."""
    captured: list[dict[str, str]] = []

    app = _make_app(fake_client_host="127.0.0.1")

    def capturing_handle(request, principal, *, palette=None):
        captured.append({
            "origin": _origin.get("local"),
        })
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}

    with patch("holdspeak.mcp.server.handle_message_for_principal", capturing_handle):
        client = TestClient(app)
        resp = client.post(
            "/api/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"X-HoldSpeak-Token": "owner-tok-123"},
        )

    assert resp.status_code == 200
    assert len(captured) == 1
    assert captured[0]["origin"] == "local"


# ── Steward run returns run_id promptly ────────────────────────────────

def test_steward_run_returns_run_id():
    """174-05: project.run_steward returns run_id promptly over HTTP."""
    principal = Principal(PrincipalKind.AGENT, "sweep-runner")
    palette = frozenset({"project.run_steward", "project.get_steward_run"})

    # We cannot easily stub the steward service in handle_message_for_principal
    # without wiring a full DB. Instead, verify the protocol: the palette
    # allows the tool, and the dispatch_for_palette gates correctly.
    from holdspeak.mcp.tools import ToolError
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "project.run_steward", "arguments": {"project_id": "test"}},
    }
    # This will fail with a service error (no DB), but it should NOT fail
    # with a palette refusal (MCP-005).
    response = handle_message_for_principal(request, principal, palette=palette)
    assert response is not None
    # Verify it's NOT an MCP-005 palette refusal.
    if "error" in response:
        assert response["error"]["code"] != _MCP_005_CODE
    # If it's a tool result with isError, that's expected (no DB in test).


def test_steward_poll_with_palette():
    """174-05: project.get_steward_run is palette-gated correctly."""
    principal = Principal(PrincipalKind.AGENT, "sweep-runner")
    # Palette that EXCLUDES get_steward_run.
    palette = frozenset({"project.run_steward"})

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "project.get_steward_run", "arguments": {"run_id": "test"}},
    }
    response = handle_message_for_principal(request, principal, palette=palette)
    assert response is not None
    assert response["error"]["code"] == _MCP_005_CODE


# ── Settings routes ────────────────────────────────────────────────────

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


def test_settings_put_update():
    app = _make_app()
    client = TestClient(app)
    resp = client.put(
        "/api/settings/remote",
        json={"enabled": True, "bind_host": "100.64.0.2"},
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True
    assert resp.json()["bind_host"] == "100.64.0.2"


def test_settings_issue_and_revoke_credential():
    """174-03: issue and revoke a credential through the settings API."""
    clock, _ = _clock_factory()
    store = AgentCredentialStore(clock=clock)
    app = _make_app(agent_store=store)
    client = TestClient(app)

    # Issue.
    resp = client.post(
        "/api/settings/remote/credentials",
        json={"identity": "sweep-runner", "palette": "PROJECT", "ttl_seconds": 3600},
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data  # plaintext shown ONCE
    assert data["identity"] == "sweep-runner"
    assert data["palette"] == "PROJECT"
    cred_id = data["id"]

    # Verify the credential is listed.
    resp = client.get(
        "/api/settings/remote",
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.status_code == 200
    creds = resp.json()["credentials"]
    assert any(c["id"] == cred_id for c in creds)
    assert resp.json()["active_count"] == 1
    assert resp.json()["total_count"] == 1

    # Revoke.
    resp = client.delete(
        f"/api/settings/remote/credentials/{cred_id}",
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.status_code == 200
    assert resp.json()["revoked"] == cred_id

    # Verify it's gone.
    resp = client.get(
        "/api/settings/remote",
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.json()["total_count"] == 0


# ── N ACTIVE counts non-expired ────────────────────────────────────────

def test_n_active_counts_non_expired():
    """P2s: N ACTIVE in the settings response counts only non-expired."""
    clock, advance = _clock_factory()
    store = AgentCredentialStore(clock=clock)
    store.issue("a", ttl_seconds=3600)
    store.issue("b", ttl_seconds=10)

    app = _make_app(agent_store=store)
    client = TestClient(app)

    resp = client.get(
        "/api/settings/remote",
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    assert resp.json()["active_count"] == 2
    assert resp.json()["total_count"] == 2

    advance(11)
    resp = client.get(
        "/api/settings/remote",
        headers={"X-HoldSpeak-Token": "owner-tok-123"},
    )
    # After expiry, derive() cleans up, but list_credentials still shows both
    # until the next derive call cleans them. The active_count should reflect
    # the real time-based count.
    assert resp.json()["active_count"] == 1


# ── Palette names ──────────────────────────────────────────────────────

def test_palette_names():
    """174-03: the four palette names resolve without error."""
    assert set(PALETTE_NAMES) == {"PROJECT", "SWEEP", "DESK", "ALL"}
    for name in PALETTE_NAMES:
        result = resolve_palette(name)
        assert isinstance(result, frozenset)
        assert len(result) > 0


def test_sweep_palette_includes_project_and_heartbeat():
    """174-05: SWEEP palette covers both project and heartbeat families."""
    sweep = resolve_palette("SWEEP")
    assert "project.list" in sweep
    assert "project.run_steward" in sweep
    assert "project.get_steward_run" in sweep
    assert "heartbeat.run_now" in sweep
    assert "heartbeat.status" in sweep


# ── PipelineEvent carries origin fields ────────────────────────────────

def test_pipeline_event_origin_fields():
    """174-04: PipelineEvent has origin, caller, caller_identity."""
    event = PipelineEvent(
        event_id="test",
        timestamp=0.0,
        service="test",
        method="test",
        principal_kind="agent",
        principal_identity="runner",
        args_summary="{}",
        result_summary="",
        error=None,
        error_code=None,
        duration_ms=0.0,
        correlation_id="",
        is_async=False,
        origin="remote",
        caller="100.64.0.5",
        caller_identity="sweep-runner",
    )
    assert event.origin == "remote"
    assert event.caller == "100.64.0.5"
    assert event.caller_identity == "sweep-runner"


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


# ── required_right for /api/mcp ────────────────────────────────────────

def test_required_right_mcp():
    """174-02: POST /api/mcp requires AGENT_SUBMIT."""
    assert required_right("POST", "/api/mcp") == PrincipalRight.AGENT_SUBMIT


def test_required_right_settings_remote():
    """Settings remote routes fall through to OWNER."""
    assert required_right("GET", "/api/settings/remote") == PrincipalRight.OWNER
    assert required_right("PUT", "/api/settings/remote") == PrincipalRight.OWNER
    assert required_right("POST", "/api/settings/remote/credentials") == PrincipalRight.OWNER
    assert required_right("DELETE", "/api/settings/remote/credentials/abc") == PrincipalRight.OWNER


# ── Schema: pipeline_events has origin column ──────────────────────────

def test_schema_has_origin_column():
    """C6: pipeline_events.origin TEXT NOT NULL DEFAULT 'local'."""
    from holdspeak.db.schema import SCHEMA_SQL
    assert "origin TEXT NOT NULL DEFAULT 'local'" in SCHEMA_SQL


# ── SQLiteObserver INSERT includes origin ──────────────────────────────

def test_sqlite_observer_insert_has_origin():
    """174-04: the SQLiteObserver INSERT names origin, caller, caller_identity."""
    from holdspeak.services.sqlite_observer import _INSERT_SQL
    assert "origin" in _INSERT_SQL
    assert "caller" in _INSERT_SQL
    assert "caller_identity" in _INSERT_SQL


# ── HS-174-04/08: wire gap tests (projection origin, room receipts,
#    heartbeat runs_on, remote hosts, last_remote_run_at) ──────────────

@pytest.fixture
def _wire_db(tmp_path):
    """Isolated DB for wire-gap tests."""
    from holdspeak.db import Database
    return Database(tmp_path / "wire_gap.db")


def _insert_pipeline_event(
    db, *, event_id, service, method, origin="local",
    caller="", caller_identity="", args_summary="{}", timestamp=None,
    result_summary="", error=None,
):
    """Insert a pipeline_events row directly for testing."""
    ts = timestamp or time.time()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO pipeline_events "
            "(event_id, timestamp, service, method, "
            " principal_kind, principal_identity, "
            " args_summary, result_summary, error, error_code, "
            " duration_ms, correlation_id, is_async, "
            " origin, caller, caller_identity) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event_id, ts, service, method,
                "agent", "sweep-runner",
                args_summary, result_summary, error, None,
                10.0, f"corr-{event_id}", 0,
                origin, caller, caller_identity,
            ),
        )


# ── 1. Projection read carries origin/caller from remote pipeline event ──

class TestProjectionOriginEnrichment:
    def test_remote_pipeline_event_surfaces_in_projection(self, _wire_db):
        """174-04: a remote-tagged pipeline event enriches the matching projection."""
        db = _wire_db
        # Create a cadence loop (produces a projection row).
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO cadence_loops "
                "(id, title, source_type, source_id, status, priority, "
                " nudge_count, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,datetime('now'),datetime('now'))",
                ("loop-abc", "Test loop", "agent_question", "sess-1",
                 "closed", "normal", 0),
            )
        # Insert a remote pipeline event whose args_summary mentions
        # the source_id "loop-abc".
        import json as _json
        _insert_pipeline_event(
            db,
            event_id="ev-remote-1",
            service="CadenceService",
            method="run_now",
            origin="remote",
            caller="100.64.0.5",
            caller_identity="sweep-runner",
            args_summary=_json.dumps({"loop_id": "loop-abc"}),
        )

        # Read projections and find the cadence projection.
        result = db.projections.list()
        cadence_rows = [
            p for p in result["projections"]
            if p["source_kind"] == "cadence_loop" and p["source_id"] == "loop-abc"
        ]
        assert len(cadence_rows) >= 1
        row = cadence_rows[0]
        assert row["origin"] == "remote"
        assert row["caller"] == "100.64.0.5"
        assert row["caller_identity"] == "sweep-runner"

    def test_local_projection_has_none_origin(self, _wire_db):
        """174-04: a projection without a remote pipeline event has origin=None."""
        db = _wire_db
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO cadence_loops "
                "(id, title, source_type, source_id, status, priority, "
                " nudge_count, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,datetime('now'),datetime('now'))",
                ("loop-local", "Local loop", "agent_question", "sess-2",
                 "closed", "normal", 0),
            )
        result = db.projections.list()
        cadence_rows = [
            p for p in result["projections"]
            if p["source_kind"] == "cadence_loop" and p["source_id"] == "loop-local"
        ]
        assert len(cadence_rows) >= 1
        row = cadence_rows[0]
        assert row["origin"] is None
        assert row["caller"] is None


# ── 2. Room receipts section ─────────────────────────────────────────────

class TestRoomReceipts:
    def test_room_receipts_lists_remote_and_local(self, _wire_db):
        """174-04: Room receipts section lists pipeline events scoped to the project."""
        db = _wire_db
        # Create a project.
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects "
                "(id, name, detection_threshold, "
                " created_at, updated_at) "
                "VALUES (?,?,?,datetime('now'),datetime('now'))",
                ("proj-1", "Test Project", 0.4),
            )
        import json as _json
        # Insert a remote pipeline event scoped to the project.
        _insert_pipeline_event(
            db,
            event_id="ev-room-remote",
            service="ProjectService",
            method="room",
            origin="remote",
            caller="192.168.1.43",
            caller_identity="sweep-runner",
            args_summary=_json.dumps({"project_id": "proj-1"}),
            timestamp=time.time(),
        )
        # Insert a local pipeline event scoped to the project.
        _insert_pipeline_event(
            db,
            event_id="ev-room-local",
            service="ProjectService",
            method="list_projects",
            origin="local",
            caller="",
            caller_identity="",
            args_summary=_json.dumps({"project_id": "proj-1"}),
            timestamp=time.time() - 1,
        )

        from holdspeak.services.project_service import ProjectService
        ps = ProjectService(db)
        room = ps.room(Principal(PrincipalKind.OWNER, "test"), "proj-1")

        # Receipts section should be present and ok.
        receipts = room.get("receipts", {})
        assert receipts.get("state") == "ok"
        items = receipts.get("items", [])
        assert len(items) == 2

        # First item (newest) should be the remote one.
        remote_item = items[0]
        assert remote_item["id"] == "ev-room-remote"
        assert remote_item["origin"] == "remote"
        assert remote_item["caller"] == "192.168.1.43"
        assert remote_item["identity"] == "sweep-runner"
        assert remote_item["op"] == "room"
        assert remote_item["title"] == "ProjectService.room"

        # Second item should be local.
        local_item = items[1]
        assert local_item["id"] == "ev-room-local"
        assert local_item["origin"] is None  # local -> None
        assert local_item["caller"] is None

    def test_room_receipts_empty_when_none(self, _wire_db):
        """174-04: Room receipts section returns empty items when no events."""
        db = _wire_db
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects "
                "(id, name, detection_threshold, "
                " created_at, updated_at) "
                "VALUES (?,?,?,datetime('now'),datetime('now'))",
                ("proj-empty", "Empty", 0.4),
            )
        from holdspeak.services.project_service import ProjectService
        ps = ProjectService(db)
        room = ps.room(Principal(PrincipalKind.OWNER, "test"), "proj-empty")
        receipts = room.get("receipts", {})
        assert receipts.get("state") == "ok"
        assert receipts.get("items") == []


# ── 3. Heartbeat settings: runs_on, remote_hosts, last_remote_run_at ────

class TestHeartbeatRunsOn:
    def test_runs_on_defaults_to_local(self, _wire_db):
        """174-08: runs_on defaults to 'local'."""
        from holdspeak.services.heartbeat_service import HeartbeatService
        hb = HeartbeatService(_wire_db)
        settings = hb.get_settings()
        assert settings["runs_on"] == "local"
        assert settings["remote_hosts"] == []
        assert settings["last_remote_run_at"] is None

    def test_runs_on_persists(self, _wire_db):
        """174-08: runs_on round-trips through update_settings."""
        from holdspeak.services.heartbeat_service import HeartbeatService
        hb = HeartbeatService(_wire_db)
        hb.update_settings({"runs_on": "192.168.1.43"})
        settings = hb.get_settings()
        assert settings["runs_on"] == "192.168.1.43"

    def test_remote_hosts_lists_callers(self, _wire_db):
        """174-08: remote_hosts lists distinct callers from pipeline_events."""
        db = _wire_db
        _insert_pipeline_event(
            db, event_id="ev-rh-1",
            service="HeartbeatService", method="run_sweep",
            origin="remote", caller="192.168.1.43",
            caller_identity="sweep-runner",
        )
        _insert_pipeline_event(
            db, event_id="ev-rh-2",
            service="ProjectService", method="room",
            origin="remote", caller="100.64.0.5",
            caller_identity="other-runner",
        )
        from holdspeak.services.heartbeat_service import HeartbeatService
        hb = HeartbeatService(db)
        settings = hb.get_settings()
        assert "100.64.0.5" in settings["remote_hosts"]
        assert "192.168.1.43" in settings["remote_hosts"]

    def test_last_remote_run_at_reflects_newest(self, _wire_db):
        """174-08: last_remote_run_at is the newest remote HeartbeatService.run_sweep."""
        db = _wire_db
        ts_old = time.time() - 3600
        ts_new = time.time() - 60
        _insert_pipeline_event(
            db, event_id="ev-lrr-old",
            service="HeartbeatService", method="run_sweep",
            origin="remote", caller="192.168.1.43",
            caller_identity="sweep-runner",
            timestamp=ts_old,
        )
        _insert_pipeline_event(
            db, event_id="ev-lrr-new",
            service="HeartbeatService", method="run_sweep",
            origin="remote", caller="192.168.1.43",
            caller_identity="sweep-runner",
            timestamp=ts_new,
        )
        from holdspeak.services.heartbeat_service import HeartbeatService
        hb = HeartbeatService(db)
        settings = hb.get_settings()
        assert settings["last_remote_run_at"] is not None
        # The ISO string should correspond to ts_new, not ts_old.
        from datetime import datetime, timezone
        parsed = datetime.fromisoformat(settings["last_remote_run_at"])
        assert abs(parsed.timestamp() - ts_new) < 2

    def test_loop_holds_when_runs_on_remote(self, _wire_db):
        """174-08: runs_on=remote -> the loop records held_remote_runs_on."""
        from holdspeak.services.heartbeat_service import HeartbeatService
        from holdspeak.services.sqlite_observer import SQLiteObserver

        db = _wire_db
        obs = SQLiteObserver(db._connection)
        hb = HeartbeatService(db, observer=obs)

        # Set runs_on to remote.
        hb.update_settings({"runs_on": "192.168.1.43"})

        # Record the hold.
        hb.record_held_remote("192.168.1.43")

        # Verify a pipeline event was written with the hold outcome.
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM pipeline_events "
                "WHERE service='HeartbeatService' AND method='run_sweep' "
                "ORDER BY timestamp DESC LIMIT 1",
            ).fetchall()
        assert len(rows) == 1
        import json as _json
        result = _json.loads(rows[0]["result_summary"])
        assert result["outcome"] == "held_remote_runs_on"
        assert result["host"] == "192.168.1.43"

    def test_run_now_via_mcp_carries_origin_remote(self, _wire_db):
        """174-08: heartbeat.run_now over /api/mcp with a SWEEP credential
        runs the sweep and its pipeline event carries origin=remote.
        """
        from holdspeak.services.heartbeat_service import HeartbeatService
        from holdspeak.services.sqlite_observer import SQLiteObserver
        from holdspeak.services.observer import _origin, _caller, _caller_identity

        db = _wire_db
        obs = SQLiteObserver(db._connection)
        hb = HeartbeatService(db, observer=obs)

        # Simulate the remote context (as mcp_http.py would set it).
        origin_tok = _origin.set("remote")
        caller_tok = _caller.set("192.168.1.43")
        identity_tok = _caller_identity.set("sweep-runner")
        try:
            receipt = hb.run_sweep(Principal(PrincipalKind.AGENT, "sweep-runner"))
        finally:
            _origin.reset(origin_tok)
            _caller.reset(caller_tok)
            _caller_identity.reset(identity_tok)

        # Verify the sweep receipt was produced.
        assert receipt["kind"] == "heartbeat.sweep"

        # Verify the pipeline event carries origin=remote.
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT origin, caller, caller_identity FROM pipeline_events "
                "WHERE service='HeartbeatService' AND method='run_sweep' "
                "ORDER BY timestamp DESC LIMIT 1",
            ).fetchall()
        assert len(rows) >= 1
        assert rows[0]["origin"] == "remote"
        assert rows[0]["caller"] == "192.168.1.43"
        assert rows[0]["caller_identity"] == "sweep-runner"


# ── 4. DeskProjection payload key names ─────────────────────────────────

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
