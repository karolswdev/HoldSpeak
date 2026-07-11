"""Unit tests for the web-runtime auth primitives (HS-25-02)."""

from __future__ import annotations

from types import SimpleNamespace

from holdspeak import web_auth


def test_generate_token_is_long_and_unique():
    a = web_auth.generate_web_token()
    b = web_auth.generate_web_token()
    assert a != b
    assert len(a) >= 24


def test_verify_token_constant_time_and_fails_closed():
    assert web_auth.verify_web_token("secret", "secret") is True
    assert web_auth.verify_web_token("secret", "other") is False
    # Empty on either side must fail, never authenticate.
    assert web_auth.verify_web_token("", "secret") is False
    assert web_auth.verify_web_token("secret", "") is False
    assert web_auth.verify_web_token(None, None) is False


def test_is_loopback_host_recognizes_local_binds():
    for host in ["127.0.0.1", "::1", "[::1]", "localhost", "", "127.0.0.5"]:
        assert web_auth.is_loopback_host(host) is True, host


def test_is_loopback_host_rejects_external_binds():
    for host in ["0.0.0.0", "192.168.1.10", "10.0.0.2", "example.com", "::"]:
        assert web_auth.is_loopback_host(host) is False, host


def test_nonloopback_bind_blocked_requires_token():
    # Loopback is always allowed, token or not.
    assert web_auth.nonloopback_bind_blocked("127.0.0.1", "") == (False, None)
    # Non-loopback without a token is refused with a reason.
    blocked, reason = web_auth.nonloopback_bind_blocked("0.0.0.0", "")
    assert blocked is True
    assert reason and "0.0.0.0" in reason
    # Non-loopback with a token is allowed.
    assert web_auth.nonloopback_bind_blocked("0.0.0.0", "tok") == (False, None)


def test_extract_request_token_priority_and_bearer():
    assert web_auth.extract_request_token(header_token="hx") == "hx"
    assert web_auth.extract_request_token(authorization="Bearer abc") == "abc"
    assert web_auth.extract_request_token(authorization="bearer abc") == "abc"
    assert web_auth.extract_request_token(query_token="qt") == "qt"
    # Header wins over query.
    assert web_auth.extract_request_token(header_token="hx", query_token="qt") == "hx"
    # Nothing / malformed → None.
    assert web_auth.extract_request_token() is None
    assert web_auth.extract_request_token(authorization="Basic xyz") is None


def test_websocket_token_uses_a_header_protocol_not_a_url():
    encoded = web_auth.websocket_auth_protocol("secret-token")
    assert encoded.startswith("holdspeak.auth.v1.")
    assert web_auth.extract_websocket_token(f"holdspeak.v1, {encoded}") == "secret-token"
    unusual = web_auth.websocket_auth_protocol("spaces / unicode café")
    assert web_auth.extract_websocket_token(unusual) == "spaces / unicode café"
    assert web_auth.extract_websocket_token("holdspeak.auth.v1.***") is None
    assert web_auth.extract_websocket_token("holdspeak.v1") is None


def test_ensure_web_token_generates_and_persists_once():
    saved: list[object] = []
    config = SimpleNamespace(
        meeting=SimpleNamespace(web_auth_token=""),
        save=lambda path=None: saved.append(path),
    )
    token = web_auth.ensure_web_token(config)
    assert token
    assert config.meeting.web_auth_token == token
    assert len(saved) == 1  # persisted on first generation

    # Second call returns the same token without saving again.
    again = web_auth.ensure_web_token(config)
    assert again == token
    assert len(saved) == 1
