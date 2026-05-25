"""Unit tests for DeviceLeg methods that wrap aioesphomeapi calls.

The integration-shaped tests in `test_device_leg.py` cover the UDP
listener path. These tests cover the API-client-shaped paths
(`update_screen`, `update_link`, `_cache_lcd_services`,
`_handle_va_start`, `_handle_va_stop`, `_enqueue_control`) by
swapping in mocks for the APIClient methods.

Coverage here is mostly happy-path + service-missing branches —
real-hardware smoke is still required for end-to-end verification.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog

from bridge import DeviceLeg, Settings


def _make_device_settings(udp_port: int = 50000, **overrides: object) -> Settings:
    kwargs = {
        "holdspeak_host": "127.0.0.1",
        "holdspeak_port": 12345,
        "holdspeak_psk": "test-psk",
        "device_id": "aipi-test",
        "device_label": "Test",
        "udp_audio_port": udp_port,
        "log_level": "ERROR",
    }
    kwargs.update(overrides)
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        **kwargs,  # type: ignore[arg-type]
    )


def _make_leg() -> DeviceLeg:
    """DeviceLeg with the APIClient swapped for mocks."""
    leg = DeviceLeg(
        _make_device_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
    )
    # APIClient methods used by the leg. Async ones get AsyncMock;
    # sync ones get MagicMock.
    leg.client = MagicMock()
    leg.client.list_entities_services = AsyncMock(return_value=([], []))
    leg.client.execute_service = AsyncMock()
    leg.client.send_voice_assistant_event = MagicMock()
    leg.client.subscribe_voice_assistant = MagicMock()
    leg.client.disconnect = AsyncMock()
    return leg


class _FakeService:
    """Mimics the aioesphomeapi UserService shape we read (`.name`)."""

    def __init__(self, name: str) -> None:
        self.name = name


# ---------- _cache_lcd_services ----------


@pytest.mark.asyncio
async def test_cache_lcd_services_caches_both_handles():
    leg = _make_leg()
    update_screen_svc = _FakeService("update_screen")
    update_link_svc = _FakeService("update_link")
    leg.client.list_entities_services.return_value = (
        [],
        [update_screen_svc, update_link_svc, _FakeService("force_toggle_mode")],
    )
    await leg._cache_lcd_services()

    assert leg._update_screen_service is update_screen_svc
    assert leg._update_link_service is update_link_svc


@pytest.mark.asyncio
async def test_cache_lcd_services_warns_when_link_missing():
    """Older firmware doesn't have `update_link`; bridge should still
    cache `update_screen` and not crash."""
    leg = _make_leg()
    leg.client.list_entities_services.return_value = (
        [],
        [_FakeService("update_screen")],
    )
    await leg._cache_lcd_services()

    assert leg._update_screen_service is not None
    assert leg._update_link_service is None


@pytest.mark.asyncio
async def test_cache_lcd_services_clears_on_lookup_error():
    """A failed `list_entities_services` should null both handles —
    the next paint call will skip rather than blow up on a stale ref."""
    leg = _make_leg()
    leg._update_screen_service = _FakeService("stale")
    leg._update_link_service = _FakeService("stale")
    leg.client.list_entities_services.side_effect = RuntimeError("API down")
    await leg._cache_lcd_services()

    assert leg._update_screen_service is None
    assert leg._update_link_service is None


# ---------- update_screen / update_link ----------


@pytest.mark.asyncio
async def test_update_screen_calls_execute_service_with_msg():
    leg = _make_leg()
    svc = _FakeService("update_screen")
    leg._update_screen_service = svc

    await leg.update_screen("Recording 00:30   *")

    leg.client.execute_service.assert_awaited_once_with(
        service=svc, data={"msg": "Recording 00:30   *"}
    )


@pytest.mark.asyncio
async def test_update_screen_skips_when_service_not_cached():
    leg = _make_leg()
    leg._update_screen_service = None

    await leg.update_screen("Anything")
    leg.client.execute_service.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_screen_swallows_execute_errors():
    """LCD is UX, not correctness — handler must not raise."""
    leg = _make_leg()
    leg._update_screen_service = _FakeService("update_screen")
    leg.client.execute_service.side_effect = RuntimeError("API died")

    # Must not raise.
    await leg.update_screen("Boom")


@pytest.mark.asyncio
async def test_update_link_calls_execute_service_with_state():
    leg = _make_leg()
    svc = _FakeService("update_link")
    leg._update_link_service = svc

    await leg.update_link("[OK]")

    leg.client.execute_service.assert_awaited_once_with(
        service=svc, data={"msg": "[OK]"}
    )


@pytest.mark.asyncio
async def test_update_link_silent_when_service_missing():
    """Older firmware won't have update_link — bridge keeps going."""
    leg = _make_leg()
    leg._update_link_service = None

    await leg.update_link("[OK]")
    leg.client.execute_service.assert_not_awaited()


# ---------- _handle_va_start / _handle_va_stop ----------


@pytest.mark.asyncio
async def test_handle_va_start_returns_udp_port_and_enqueues_start():
    """Critical: returning the UDP port is what makes audio flow at all
    (ESPHome voice_assistant is UDP-first; returning None silently
    breaks the path — see memory entry feedback-esphome-voice-assistant-udp).
    Plus a `start` control frame should land on the queue for the WS
    leg to forward."""
    leg = _make_leg()

    port = await leg._handle_va_start(
        conversation_id="conv-1",
        sample_rate=16000,
        audio_settings=None,
        wakeword=None,
    )

    assert port == leg.settings.udp_audio_port
    assert leg._va_started_at_monotonic is not None
    assert leg._va_first_audio_logged is False
    # A start frame should be on the control queue.
    assert leg.control_queue.qsize() == 1
    payload = leg.control_queue.get_nowait()
    assert '"type":"start"' in payload


@pytest.mark.asyncio
async def test_first_audio_marks_voice_assistant_audio_seen():
    """First UDP chunk after VA start is recorded for live timing diagnostics."""
    leg = _make_leg()
    await leg._handle_va_start(
        conversation_id="conv-1",
        sample_rate=16000,
        audio_settings=None,
        wakeword=None,
    )

    leg._enqueue_audio_bytes(b"\x00" * 320)

    assert leg._va_first_audio_logged is True
    assert leg.audio_queue.qsize() == 1


@pytest.mark.asyncio
async def test_audio_monitor_queue_receives_udp_audio_when_enabled():
    settings = _make_device_settings(audio_monitor_cmd="cat >/dev/null")
    leg = DeviceLeg(
        settings,
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
    )

    leg._enqueue_audio_bytes(b"\x01" * 320)

    assert leg._audio_monitor_queue is not None
    assert leg._audio_monitor_queue.get_nowait() == b"\x01" * 320
    assert leg.audio_queue.get_nowait() == b"\x01" * 320


@pytest.mark.asyncio
async def test_handle_va_stop_enqueues_stop_and_sends_run_end():
    """`stop` control frame to HoldSpeak + RUN_END event to firmware.
    The RUN_END event is what re-arms voice_assistant.start in continuous
    mode (firmware's `voice_assistant.on_end` trigger)."""
    leg = _make_leg()

    await leg._handle_va_stop(cancelled=False)

    # Stop frame on the control queue.
    payload = leg.control_queue.get_nowait()
    assert '"type":"stop"' in payload
    # RUN_END event sent to firmware.
    leg.client.send_voice_assistant_event.assert_called_once()
    assert leg._va_started_at_monotonic is None


@pytest.mark.asyncio
async def test_handle_va_stop_swallows_run_end_send_failure():
    """If `send_voice_assistant_event` raises (e.g. API client racing
    with disconnect), the bridge logs but doesn't propagate."""
    leg = _make_leg()
    leg.client.send_voice_assistant_event.side_effect = RuntimeError("API gone")

    # Must not raise.
    await leg._handle_va_stop(cancelled=False)


# ---------- _enqueue_control overflow ----------


@pytest.mark.asyncio
async def test_enqueue_control_drops_on_full_queue():
    """When HoldSpeak is unreachable for a long time and control frames
    pile up beyond the queue cap, the bridge must drop new frames
    rather than block + back-pressure into the device leg."""
    settings = _make_device_settings()
    leg = DeviceLeg(
        settings,
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=2),  # small cap for the test
    )

    from holdspeak_proto import StartFrame

    leg._enqueue_control(StartFrame(), kind="start")
    leg._enqueue_control(StartFrame(), kind="start")
    # Third should be dropped silently (logged, not raised).
    leg._enqueue_control(StartFrame(), kind="start")

    assert leg.control_queue.qsize() == 2


# ---------- _on_disconnect invalidates caches ----------


@pytest.mark.asyncio
async def test_on_disconnect_invalidates_lcd_service_cache():
    """A device drop must clear the cached service handles so the
    next `_on_connect` re-fetches them. Otherwise a hot-restart of the
    firmware would leave the bridge holding stale refs."""
    leg = _make_leg()
    leg._update_screen_service = _FakeService("update_screen")
    leg._update_link_service = _FakeService("update_link")

    await leg._on_disconnect(expected=False)

    assert leg._update_screen_service is None
    assert leg._update_link_service is None
