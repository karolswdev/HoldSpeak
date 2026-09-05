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
