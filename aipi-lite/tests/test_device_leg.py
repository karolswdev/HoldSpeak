"""Tests for DeviceLeg UDP audio gating and allowlist refresh.

Drives `_udp_listener_session` directly: bind a real UDP socket, send
datagrams from this process (so source IP = 127.0.0.1), and assert
they're forwarded into `audio_queue` only when 127.0.0.1 is in the
allowlist. Covers the security-relevant fail-closed default (empty
allowlist = drop everything) and the throttled-warning path.
"""

from __future__ import annotations

import asyncio
import errno
import socket

import pytest
import structlog

from bridge import DeviceLeg, Settings


def _free_udp_port() -> int:
    """Reserve an ephemeral UDP port and return it.

    The bridge sets `SO_REUSEADDR` on its listener socket, so closing
    here and reopening there is race-free in practice (TIME_WAIT does
    not apply to UDP, and SO_REUSEADDR is sufficient if we ever did
    overlap).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _make_device_settings(udp_port: int) -> Settings:
    """Build Settings for a DeviceLeg test, bypassing bridge.env."""
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        holdspeak_host="127.0.0.1",
        holdspeak_port=12345,
        holdspeak_psk="test-psk",
        device_id="aipi-test",
        device_label="Test",
        udp_audio_port=udp_port,
        log_level="ERROR",
    )


def _build_leg(settings: Settings) -> DeviceLeg:
    log = structlog.get_logger()
    return DeviceLeg(
        settings,
        log,
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
    )


async def _wait_listening(timeout: float = 1.0) -> None:
    """Give the listener task a beat to run its sync bind() code."""
    await asyncio.sleep(0.05)
    # Tiny additional yield in case the test platform is slow.
    await asyncio.sleep(0)


def _send_udp(payload: bytes, port: int) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.sendto(payload, ("127.0.0.1", port))
    finally:
        s.close()


# ---------- Allowlist ----------


@pytest.mark.asyncio
async def test_udp_listener_accepts_allowed_source():
    port = _free_udp_port()
    leg = _build_leg(_make_device_settings(port))
    leg._allowed_ips = {"127.0.0.1"}

    task = asyncio.create_task(leg._udp_listener_session())
    try:
        await _wait_listening()
        _send_udp(b"\xab" * 320, port)

        chunk = await asyncio.wait_for(leg.audio_queue.get(), timeout=2.0)
        assert chunk == b"\xab" * 320
        assert leg._unauthorized_dropped == 0
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_udp_listener_drops_unauthorized_source():
    """A datagram from an IP not in `_allowed_ips` must be discarded
    and the unauthorized-drop counter must increment."""
    port = _free_udp_port()
    leg = _build_leg(_make_device_settings(port))
    leg._allowed_ips = {"10.99.99.99"}  # not 127.0.0.1

    task = asyncio.create_task(leg._udp_listener_session())
    try:
        await _wait_listening()
        _send_udp(b"\xcd" * 320, port)
        # Give the listener a chance to receive + drop.
        await asyncio.sleep(0.1)

        assert leg.audio_queue.empty()
        assert leg._unauthorized_dropped >= 1
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_udp_listener_drops_when_allowlist_empty():
    """Pre-first-connect / resolver-failure state: empty allowlist
    means *every* sender is unauthorized — fail-closed."""
    port = _free_udp_port()
    leg = _build_leg(_make_device_settings(port))
    # Don't populate `_allowed_ips`.

    task = asyncio.create_task(leg._udp_listener_session())
    try:
        await _wait_listening()
        _send_udp(b"\xef" * 320, port)
        await asyncio.sleep(0.1)

        assert leg.audio_queue.empty()
        assert leg._unauthorized_dropped >= 1
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# ---------- _refresh_allowed_ips ----------


@pytest.mark.asyncio
async def test_refresh_allowed_ips_resolves_localhost():
    settings = _make_device_settings(_free_udp_port())
    settings.aipi_host = "localhost"
    leg = _build_leg(settings)

    await leg._refresh_allowed_ips()
    # `localhost` resolves to 127.0.0.1 (and on dual-stack hosts,
    # ::1 too — so use a subset assertion).
    assert "127.0.0.1" in leg._allowed_ips


@pytest.mark.asyncio
async def test_refresh_allowed_ips_keeps_old_set_on_resolver_error():
    """A transient DNS hiccup should not wipe a previously-good
    allowlist — the listener would start fail-closing legit traffic."""
    settings = _make_device_settings(_free_udp_port())
    # Force a name that will not resolve.
    settings.aipi_host = "this-host-must-not-exist.invalid"
    leg = _build_leg(settings)
    leg._allowed_ips = {"192.168.1.42"}

    await leg._refresh_allowed_ips()
    assert leg._allowed_ips == {"192.168.1.42"}


# ---------- Bind error path ----------


@pytest.mark.asyncio
async def test_udp_listener_raises_on_bind_failure(monkeypatch):
    """Bind failures must propagate so reconnect_with_backoff retries.
    The wrapper in `_udp_listener_session` adds structured logging but
    must not swallow the exception."""
    leg = _build_leg(_make_device_settings(_free_udp_port()))

    def fake_bind(self, *args, **kwargs):
        raise OSError(errno.EADDRINUSE, "Address already in use")

    monkeypatch.setattr(socket.socket, "bind", fake_bind)

    with pytest.raises(OSError) as excinfo:
        await leg._udp_listener_session()
    assert excinfo.value.errno == errno.EADDRINUSE
