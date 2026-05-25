"""AIPI-4-08 — link-state re-trigger on device reconnect.

Covers the race where HoldSpeak handshake wins against the device-leg
API connection: the initial `update_link("[OK]")` paint silently
no-ops (service handles not cached), and without a re-trigger the
LCD's link indicator gets stuck at the firmware boot-default `[--]`.

Fix: `HoldSpeakLeg.republish_link_state()` re-fires the last-known
link state. Wired from `DeviceLeg._on_connect` via the `on_device_ready`
callback, post-cache.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog

from bridge import DeviceLeg, HoldSpeakLeg, Settings


def _make_settings() -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        holdspeak_host="127.0.0.1",
        holdspeak_port=12345,
        holdspeak_psk="test-psk",
        device_id="aipi-test",
        device_label="Test",
        log_level="ERROR",
    )


def _make_hs_leg(*, on_link_update=None) -> HoldSpeakLeg:
    return HoldSpeakLeg(
        _make_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        on_link_update=on_link_update,
    )


def _make_device_leg(*, on_device_ready=None) -> DeviceLeg:
    leg = DeviceLeg(
        _make_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        on_device_ready=on_device_ready,
    )
    leg.client = MagicMock()
    leg.client.list_entities_services = AsyncMock(return_value=([], []))
    leg.client.subscribe_voice_assistant = MagicMock()
    leg.client.subscribe_states = MagicMock()
    leg.client.disconnect = AsyncMock()
    # Skip real DNS lookup — `_refresh_allowed_ips` calls
    # `socket.getaddrinfo("aipi.local", ...)` in an executor which can
    # block for seconds on unresolvable hosts. Stub it.
    leg._refresh_allowed_ips = AsyncMock()  # type: ignore[method-assign]
    leg._allowed_ips = {"127.0.0.1"}
    return leg


# ---------- HoldSpeakLeg.republish_link_state ----------


@pytest.mark.asyncio
async def test_republish_noop_when_no_state_set():
    """No paint fired yet → republish is a no-op (idempotent)."""
    on_link = AsyncMock()
    leg = _make_hs_leg(on_link_update=on_link)

    await leg.republish_link_state()

    on_link.assert_not_awaited()
    assert leg._last_link_state is None


@pytest.mark.asyncio
async def test_call_link_stores_last_state():
    """`_call_link` records the most recent state for later republish."""
    on_link = AsyncMock()
    leg = _make_hs_leg(on_link_update=on_link)

    await leg._call_link("[OK]")

    assert leg._last_link_state == "[OK]"
    on_link.assert_awaited_once_with("[OK]")


@pytest.mark.asyncio
async def test_call_link_stores_state_even_when_handler_unset():
    """State must be tracked even if `on_link_update` is None — that's
    the racing case where the device callback gets wired *after* the
    handshake. If we didn't store, republish would have nothing to
    re-fire."""
    leg = _make_hs_leg(on_link_update=None)

    await leg._call_link("[OK]")

    assert leg._last_link_state == "[OK]"


@pytest.mark.asyncio
async def test_call_link_stores_state_even_when_handler_errors():
    """A handler that throws shouldn't prevent state tracking — the
    next republish should still know what to re-fire."""
    on_link = AsyncMock(side_effect=RuntimeError("device gone"))
    leg = _make_hs_leg(on_link_update=on_link)

    await leg._call_link("[OK]")

    assert leg._last_link_state == "[OK]"


@pytest.mark.asyncio
async def test_republish_re_fires_last_state():
    """The whole point: republish triggers the same paint that earlier
    silently no-op'd."""
    on_link = AsyncMock()
    leg = _make_hs_leg(on_link_update=on_link)

    # Simulate the race: first paint at handshake time; the actual
    # device callback isn't cached so it silently does nothing (we
    # mock the callback as no-op here just to check call count).
    await leg._call_link("[OK]")
    assert on_link.await_count == 1

    # Now the device finally finishes caching + calls republish.
    await leg.republish_link_state()

    # Same state, called again.
    assert on_link.await_count == 2
    on_link.assert_awaited_with("[OK]")


@pytest.mark.asyncio
async def test_republish_uses_current_state_not_first():
    """If the state changes (e.g. [..] → [OK] during handshake),
    republish must re-fire the *latest* state, not the first one."""
    on_link = AsyncMock()
    leg = _make_hs_leg(on_link_update=on_link)

    await leg._call_link("[..]")
    await leg._call_link("[OK]")
    on_link.reset_mock()  # ignore the racing paints

    await leg.republish_link_state()

    on_link.assert_awaited_once_with("[OK]")


# ---------- DeviceLeg._on_connect → on_device_ready ----------


@pytest.mark.asyncio
async def test_on_device_ready_fires_after_cache():
    """The `on_device_ready` callback fires from `_on_connect` after
    the service caches finish — that's the load-bearing post-condition."""
    ready = AsyncMock()
    leg = _make_device_leg(on_device_ready=ready)

    await leg._on_connect()

    ready.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_device_ready_none_safe():
    """Pre-wiring (e.g., unit tests, the legacy run path) should not crash."""
    leg = _make_device_leg(on_device_ready=None)

    # Must not raise.
    await leg._on_connect()


@pytest.mark.asyncio
async def test_on_device_ready_handler_errors_swallowed():
    """A flaky republish (e.g., HoldSpeakLeg in a bad state) must not
    break the device-leg connect lifecycle. The link indicator is UX,
    not correctness."""
    ready = AsyncMock(side_effect=RuntimeError("hs in bad state"))
    leg = _make_device_leg(on_device_ready=ready)

    # Must not raise.
    await leg._on_connect()

    ready.assert_awaited_once()


# ---------- End-to-end (mocked clients) ----------


# ---------- HoldSpeakLeg.republish_sticky_activity (AIPI-4-10) ----------


@pytest.mark.asyncio
async def test_republish_sticky_activity_noop_when_no_sticky():
    """No sticky set yet → republish is a no-op."""
    on_activity = AsyncMock()
    leg = HoldSpeakLeg(
        _make_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        on_activity_update=on_activity,
    )

    await leg.republish_sticky_activity()

    on_activity.assert_not_awaited()


@pytest.mark.asyncio
async def test_republish_sticky_activity_re_fires_last_sticky():
    """Sticky paints set `_sticky_activity`; republish re-emits it."""
    activity_calls: list[str] = []

    async def on_activity(rendered: str) -> None:
        activity_calls.append(rendered)

    leg = HoldSpeakLeg(
        _make_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        on_activity_update=on_activity,
    )

    await leg._paint_activity("Ready")
    assert len(activity_calls) == 1
    # Republish should re-fire the same rendered sticky.
    await leg.republish_sticky_activity()
    assert len(activity_calls) == 2
    assert activity_calls[0] == activity_calls[1]


@pytest.mark.asyncio
async def test_republish_uses_latest_sticky_not_first():
    """Multiple sticky paints update `_sticky_activity`; republish
    uses the most recent."""
    activity_calls: list[str] = []

    async def on_activity(rendered: str) -> None:
        activity_calls.append(rendered)

    leg = HoldSpeakLeg(
        _make_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        on_activity_update=on_activity,
    )

    await leg._paint_activity("Ready")
    await leg._paint_activity("Recording 00:00")
    activity_calls.clear()  # ignore racing paints

    await leg.republish_sticky_activity()

    assert len(activity_calls) == 1
    assert "Recording 00:00" in activity_calls[0]


@pytest.mark.asyncio
async def test_republish_skips_flash_paints():
    """A flash (ttl_ms > 0) doesn't update `_sticky_activity`, so
    republish after a bookmark flash re-fires the previous sticky,
    not the flash text."""
    activity_calls: list[str] = []

    async def on_activity(rendered: str) -> None:
        activity_calls.append(rendered)

    leg = HoldSpeakLeg(
        _make_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        on_activity_update=on_activity,
    )

    await leg._paint_activity("Recording 00:30")  # sticky
    await leg._paint_activity("Bookmark", ttl_ms=2500)  # flash
    activity_calls.clear()

    await leg.republish_sticky_activity()

    assert len(activity_calls) == 1
    assert "Recording 00:30" in activity_calls[0]
    assert "Bookmark" not in activity_calls[0]


@pytest.mark.asyncio
async def test_end_to_end_race_recovers_via_republish():
    """Simulate the full race: HoldSpeakLeg.handshake fires before
    DeviceLeg connects, then DeviceLeg connects + republishes.

    Expected: on_link_update called twice — once during handshake (with
    device callback returning None or no-op'ing because service is
    uncached), once during republish (now landing). Both with `[OK]`.
    """
    link_calls: list[str] = []

    async def on_link(state: str) -> None:
        link_calls.append(state)

    hs = _make_hs_leg(on_link_update=on_link)
    device = _make_device_leg(on_device_ready=hs.republish_link_state)

    # HoldSpeak handshake "wins" — paints [OK] first.
    await hs._call_link("[OK]")
    assert link_calls == ["[OK]"]

    # Device finally connects + republishes.
    await device._on_connect()
    assert link_calls == ["[OK]", "[OK]"]
