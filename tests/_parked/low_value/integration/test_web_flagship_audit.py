# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_web_flagship_audit.py to restore.

# ruff: noqa


# --- test_wfs_r_004_explicit_host_override_honored: P1/P6: a host it set reads back; key presence; 'route is mounted' accepting any of five status codes
def test_wfs_r_004_explicit_host_override_honored() -> None:
    """WFS-R-004: an explicit non-loopback host is preserved (no silent rebinding)."""
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     get_state=MagicMock(return_value={}),
                 ),
                 host="0.0.0.0",
             )
    assert server.host == "0.0.0.0"


# --- test_wfs_p_003_runtime_state_endpoint_exposes_required_shape: P1/P6: a host it set reads back; key presence; 'route is mounted' accepting any of five status codes
def test_wfs_p_003_runtime_state_endpoint_exposes_required_shape(test_client: TestClient) -> None:
    """WFS-P-003: runtime-state API exposes the documented fields.

    The normalised payload (see `_normalize_runtime_status_payload`)
    always carries `status`, `mode`, `meeting_active`, `state`. The
    presence of `mode="web"` is what makes this a *web flagship*
    runtime status surface (not a TUI status surface).
    """
    response = test_client.get("/api/runtime/status")
    assert response.status_code == 200
    body = response.json()
    assert "meeting_active" in body
    assert body.get("mode") == "web"
    assert body.get("status") == "ok"


# --- test_wfs_p_002_meeting_routes_mounted_and_return_json: P1/P6: a host it set reads back; key presence; 'route is mounted' accepting any of five status codes
def test_wfs_p_002_meeting_routes_mounted_and_return_json(test_client: TestClient) -> None:
    """WFS-P-002: `/api/meeting/start` and `/stop` routes are mounted on the runtime.

    Without an `on_meeting_start` callback wired (as is the case in
    this minimal fixture), the endpoint returns 501 — that's the
    documented "callback not wired" status, not "route not found".
    Confirms the API surface exists; happy-path coverage with the
    callback wired lives in `test_web_server.py::TestRuntimeControlEndpoints`.
    """
    start = test_client.post("/api/meeting/start")
    assert start.status_code in (200, 400, 409, 501, 503)
    assert start.status_code != 404, "/api/meeting/start route is not mounted"
    assert start.headers["content-type"].startswith("application/json")

    stop = test_client.post("/api/meeting/stop")
    assert stop.status_code in (200, 400, 409, 501, 503)
    assert stop.status_code != 404, "/api/meeting/stop route is not mounted"
    assert stop.headers["content-type"].startswith("application/json")
