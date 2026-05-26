"""AIPI-4-01 — bookmark gesture: classifier + gating + emission.

Bridge-side coverage of the left-button quick-tap gesture wired in
phase 4. Hardware verification (firmware exposes `left_button` as a
binary_sensor; the classifier + emit + flash chain works end-to-end
against a real meeting on HoldSpeak) is the remaining acceptance
work for AIPI-4-01 — captured separately when hardware is available.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog

from bridge import DeviceLeg, HoldSpeakLeg, Settings
from bridge.device import (
    BOOKMARK_PRESS_THRESHOLD_MS,
    LEFT_DOUBLE_TAP_WINDOW_MS,
)


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


def _make_device_leg(
    *,
    is_in_meeting=None,
    is_agent_waiting=None,
    paint_bookmark_flash=None,
) -> DeviceLeg:
    leg = DeviceLeg(
        _make_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        is_in_meeting=is_in_meeting,
        is_agent_waiting=is_agent_waiting,
        paint_bookmark_flash=paint_bookmark_flash,
    )
    leg.client = MagicMock()
    leg.client.list_entities_services = AsyncMock(return_value=([], []))
    leg.client.execute_service = AsyncMock()
    leg.client.subscribe_voice_assistant = MagicMock()
    leg.client.subscribe_states = MagicMock()
    leg.client.disconnect = AsyncMock()
    leg.client.send_voice_assistant_event = MagicMock()
    return leg


def _make_hs_leg(*, on_activity_update=None) -> HoldSpeakLeg:
    return HoldSpeakLeg(
        _make_settings(),
        structlog.get_logger(),
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        on_activity_update=on_activity_update,
    )


class _FakeBinarySensor:
    """Mimics aioesphomeapi entity-info shape (`.key`, `.object_id`, `.name`)."""

    def __init__(self, key: int, object_id: str, name: str = "") -> None:
        self.key = key
        self.object_id = object_id
        self.name = name


class _FakeState:
    """Mimics aioesphomeapi BinarySensorState (`.key`, `.state`)."""

    def __init__(self, key: int, state: bool) -> None:
        self.key = key
        self.state = state


async def _drain_pending(leg: DeviceLeg) -> None:
    """Wait for any spawned bookmark tasks to complete + clean up."""
    while leg._pending_tasks:
        await asyncio.gather(*list(leg._pending_tasks), return_exceptions=True)


# ---------- _cache_button_entities ----------


@pytest.mark.asyncio
async def test_cache_button_entities_resolves_left_button_key():
    leg = _make_device_leg()
    btn = _FakeBinarySensor(key=42, object_id="left_button")
    other = _FakeBinarySensor(key=99, object_id="right_button")
    leg.client.list_entities_services = AsyncMock(return_value=([other, btn], []))

    await leg._cache_button_entities()

    assert leg._left_button_key == 42
    # No sim entity in this firmware — sim key stays None (no warning,
    # absence is the default for pre-AIPI-4-07 firmware).
    assert leg._left_button_sim_key is None


@pytest.mark.asyncio
async def test_cache_button_entities_resolves_sim_key_alongside_real():
    """AIPI-4-07: when firmware exposes both `left_button` and
    `left_button_sim`, both keys are cached."""
    leg = _make_device_leg()
    real = _FakeBinarySensor(key=42, object_id="left_button")
    sim = _FakeBinarySensor(key=43, object_id="left_button_sim")
    leg.client.list_entities_services = AsyncMock(return_value=([real, sim], []))

    await leg._cache_button_entities()

    assert leg._left_button_key == 42
    assert leg._left_button_sim_key == 43


@pytest.mark.asyncio
async def test_cache_button_entities_resolves_sim_only_when_real_missing():
    """If only the sim entity exists (e.g., test fixture, weird
    firmware), the sim key still gets cached and remote-press still
    works — just real presses won't be detected."""
    leg = _make_device_leg()
    sim = _FakeBinarySensor(key=43, object_id="left_button_sim")
    leg.client.list_entities_services = AsyncMock(return_value=([sim], []))

    await leg._cache_button_entities()

    assert leg._left_button_key is None
    assert leg._left_button_sim_key == 43


@pytest.mark.asyncio
async def test_cache_button_entities_handles_missing_left_button():
    """Older firmware that doesn't expose `left_button` — bookmark
    gesture won't fire, but bridge stays up."""
    leg = _make_device_leg()
    leg.client.list_entities_services = AsyncMock(
        return_value=([_FakeBinarySensor(key=99, object_id="right_button")], [])
    )

    await leg._cache_button_entities()

    assert leg._left_button_key is None


@pytest.mark.asyncio
async def test_cache_button_entities_handles_lookup_error():
    """Transient API error during entity lookup invalidates any stale
    cached key rather than holding on to it."""
    leg = _make_device_leg()
    leg._left_button_key = 99
    leg.client.list_entities_services = AsyncMock(side_effect=RuntimeError("API down"))

    await leg._cache_button_entities()

    assert leg._left_button_key is None


# ---------- _handle_state_change dispatch ----------


@pytest.mark.asyncio
async def test_handle_state_change_ignores_when_button_key_uncached():
    """Pre-first-connect or post-disconnect — state events that arrive
    without a cached button key must not stamp anything."""
    leg = _make_device_leg()
    leg._left_button_key = None

    leg._handle_state_change(_FakeState(key=42, state=True))

    assert leg._left_button_press_at_ms is None


@pytest.mark.asyncio
async def test_handle_state_change_ignores_other_entity_keys():
    """Most state events are for other entities (sensors, switches, etc.)
    — silent skip."""
    leg = _make_device_leg()
    leg._left_button_key = 42

    leg._handle_state_change(_FakeState(key=99, state=True))

    assert leg._left_button_press_at_ms is None


@pytest.mark.asyncio
async def test_handle_state_change_dispatches_left_button_press():
    leg = _make_device_leg()
    leg._left_button_key = 42

    leg._handle_state_change(_FakeState(key=42, state=True))

    assert leg._left_button_press_at_ms is not None


@pytest.mark.asyncio
async def test_handle_state_change_dispatches_sim_key_press():
    """AIPI-4-07: state events for the simulated entity flow through
    the same classifier as real-button events."""
    leg = _make_device_leg()
    leg._left_button_key = 42
    leg._left_button_sim_key = 43

    leg._handle_state_change(_FakeState(key=43, state=True))

    assert leg._left_button_press_at_ms is not None


@pytest.mark.asyncio
async def test_handle_state_change_dispatches_real_when_sim_also_set():
    """Both real + sim configured; a real-key press still dispatches."""
    leg = _make_device_leg()
    leg._left_button_key = 42
    leg._left_button_sim_key = 43

    leg._handle_state_change(_FakeState(key=42, state=True))

    assert leg._left_button_press_at_ms is not None


# ---------- _handle_left_button_state classifier ----------


@pytest.mark.asyncio
async def test_press_stamps_timestamp():
    leg = _make_device_leg()

    leg._handle_left_button_state(pressed=True)

    assert leg._left_button_press_at_ms is not None


@pytest.mark.asyncio
async def test_short_press_spawns_bookmark_attempt():
    """Press < threshold → release → fires the async attempt task.
    Spawn-only assertion here; emission lives in `_fire_bookmark_attempt` tests."""
    leg = _make_device_leg(is_in_meeting=MagicMock(return_value=True))
    leg._left_button_press_at_ms = int(time.time() * 1000) - 50  # 50 ms ago

    leg._handle_left_button_state(pressed=False)

    assert len(leg._pending_tasks) == 1
    await _drain_pending(leg)


@pytest.mark.asyncio
async def test_long_press_does_not_spawn_bookmark():
    """Press > threshold → release → no spawn. Long-press is owned by
    AIPI-1-05's AP-mode-entry firmware handler."""
    leg = _make_device_leg(is_in_meeting=MagicMock(return_value=True))
    leg._left_button_press_at_ms = int(time.time() * 1000) - (
        BOOKMARK_PRESS_THRESHOLD_MS + 100
    )

    leg._handle_left_button_state(pressed=False)

    assert leg._pending_tasks == set()


@pytest.mark.asyncio
async def test_release_without_press_does_nothing():
    """First state event after connect could be a state replay; don't
    speculatively fire a bookmark on a release we never saw the press for."""
    leg = _make_device_leg(is_in_meeting=MagicMock(return_value=True))

    leg._handle_left_button_state(pressed=False)

    assert leg._pending_tasks == set()
    assert leg._left_button_press_at_ms is None


@pytest.mark.asyncio
async def test_press_press_release_uses_latest_press_timestamp():
    """A press while we already think the button is down (debounce
    hiccup, missed release) overwrites the press timestamp — the
    classifier should use the latest press, not the stale one."""
    leg = _make_device_leg(is_in_meeting=MagicMock(return_value=True))
    leg._left_button_press_at_ms = int(time.time() * 1000) - 5000  # stale

    leg._handle_left_button_state(pressed=True)  # latest press, now-ish
    leg._handle_left_button_state(pressed=False)

    # Latest press → release is < 1 ms → short-press classification fires.
    assert len(leg._pending_tasks) == 1
    await _drain_pending(leg)


@pytest.mark.asyncio
async def test_release_clears_press_timestamp():
    """After a release the press timestamp is cleared, so a subsequent
    bare release (without an intervening press) doesn't re-fire."""
    leg = _make_device_leg(is_in_meeting=MagicMock(return_value=True))
    leg._left_button_press_at_ms = int(time.time() * 1000) - 50

    leg._handle_left_button_state(pressed=False)
    await _drain_pending(leg)

    assert leg._left_button_press_at_ms is None


# ---------- _fire_bookmark_attempt: gating + emission ----------


@pytest.mark.asyncio
async def test_fire_bookmark_emits_event_when_in_meeting():
    flash = AsyncMock()
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=True),
        paint_bookmark_flash=flash,
    )

    await leg._fire_bookmark_attempt()

    payload = leg.control_queue.get_nowait()
    assert '"type":"event"' in payload
    # Wire vocabulary is HoldSpeak's `long_press` (HS-14-07) regardless
    # of our local "bookmark" naming.
    assert '"name":"long_press"' in payload
    flash.assert_awaited_once()


@pytest.mark.asyncio
async def test_fire_bookmark_includes_timestamp():
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=True),
        paint_bookmark_flash=AsyncMock(),
    )

    before = time.time()
    await leg._fire_bookmark_attempt()
    after = time.time()

    payload = leg.control_queue.get_nowait()
    # `at` is a unix-seconds float per holdspeak_proto.EventFrame.at.
    # We don't parse the JSON; just confirm the field is present and
    # non-trivial.
    assert '"at":' in payload
    # Sanity: parse just enough to confirm the timestamp is between
    # before/after.
    import json

    obj = json.loads(payload)
    assert before <= obj["at"] <= after


@pytest.mark.asyncio
async def test_fire_bookmark_suppresses_outside_meeting():
    flash = AsyncMock()
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=False),
        paint_bookmark_flash=flash,
    )

    await leg._fire_bookmark_attempt()

    assert leg.control_queue.empty()
    flash.assert_not_awaited()


@pytest.mark.asyncio
async def test_fire_bookmark_suppresses_when_callback_unwired():
    """If `is_in_meeting` is None (incomplete wiring), suppress rather
    than emit. Conservative default — emitting an event without
    confirmation we're in a meeting would be the worse failure mode."""
    flash = AsyncMock()
    leg = _make_device_leg(is_in_meeting=None, paint_bookmark_flash=flash)

    await leg._fire_bookmark_attempt()

    assert leg.control_queue.empty()
    flash.assert_not_awaited()


@pytest.mark.asyncio
async def test_fire_bookmark_swallows_flash_errors():
    """The wire event still emits even if the LCD flash blows up —
    LCD is UX, not correctness."""
    flash = AsyncMock(side_effect=RuntimeError("LCD died"))
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=True),
        paint_bookmark_flash=flash,
    )

    # Must not raise.
    await leg._fire_bookmark_attempt()

    payload = leg.control_queue.get_nowait()
    assert '"type":"event"' in payload


# ---------- HoldSpeakLeg.is_in_meeting ----------


def test_holdspeak_is_in_meeting_default_false():
    leg = _make_hs_leg()
    assert leg.is_in_meeting() is False


def test_holdspeak_is_in_meeting_true_for_recording_sticky():
    leg = _make_hs_leg()
    leg._sticky_text = "Recording 12:34"
    assert leg.is_in_meeting() is True


def test_holdspeak_is_in_meeting_false_for_listening_sticky():
    leg = _make_hs_leg()
    leg._sticky_text = "Listening"
    assert leg.is_in_meeting() is False


def test_holdspeak_is_in_meeting_false_for_ready_sticky():
    leg = _make_hs_leg()
    leg._sticky_text = "Ready"
    assert leg.is_in_meeting() is False


# ---------- HoldSpeakLeg.paint_bookmark_flash ----------


@pytest.mark.asyncio
async def test_holdspeak_paint_bookmark_flash_calls_middle_callback():
    """AIPI-4-11: bookmark flash is transient → middle slot, NOT
    the activity (bottom) slot. Verifies the routing decision."""
    middle_calls: list[str] = []
    activity_calls: list[str] = []

    async def on_middle(rendered: str) -> None:
        middle_calls.append(rendered)

    async def on_activity(rendered: str) -> None:
        activity_calls.append(rendered)

    leg = _make_hs_leg(on_activity_update=on_activity)
    leg.on_middle_update = on_middle

    await leg.paint_bookmark_flash()

    assert len(middle_calls) == 1
    assert activity_calls == []
    rendered = middle_calls[0]
    assert "Bookmark" in rendered
    # AIPI-4-04: Bookmark → LV_SYMBOL_BELL.
    assert chr(0xF0E7) in rendered


@pytest.mark.asyncio
async def test_holdspeak_paint_bookmark_flash_does_not_overwrite_sticky():
    """A flash leaves the sticky-text probe intact so `is_in_meeting()`
    still returns True after a bookmark is fired during a meeting."""
    leg = _make_hs_leg(on_activity_update=AsyncMock())
    leg._sticky_text = "Recording 12:34"
    leg._sticky_activity = "Recording 12:34   *"

    await leg.paint_bookmark_flash()

    assert leg._sticky_text == "Recording 12:34"
    assert leg.is_in_meeting() is True


# ---------- AIPI-4-14: double-tap classifier ----------


@pytest.mark.asyncio
async def test_double_tap_fires_double_left_click_event():
    """Two short releases within `LEFT_DOUBLE_TAP_WINDOW_MS` → emit
    `double_left_click` event, suppress the bookmark fire."""
    leg = _make_device_leg(is_in_meeting=MagicMock(return_value=True))
    now_ms = int(time.time() * 1000)

    # First press + short release.
    leg._left_button_press_at_ms = now_ms - 50
    leg._handle_left_button_state(pressed=False)
    # Second press + short release inside the window.
    leg._left_button_press_at_ms = now_ms - 30
    leg._handle_left_button_state(pressed=False)

    await _drain_pending(leg)
    payloads = []
    while not leg.control_queue.empty():
        payloads.append(leg.control_queue.get_nowait())

    assert any('"name":"double_left_click"' in p for p in payloads), payloads
    # No bookmark fire was queued.
    assert not any('"name":"long_press"' in p for p in payloads), payloads


@pytest.mark.asyncio
async def test_single_tap_with_no_followup_still_fires_bookmark():
    """One short release with no second release within the window →
    the scheduled single-tap fires the bookmark after the window."""
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=True),
        paint_bookmark_flash=AsyncMock(),
    )
    leg._left_button_press_at_ms = int(time.time() * 1000) - 50

    leg._handle_left_button_state(pressed=False)

    await _drain_pending(leg)
    payload = leg.control_queue.get_nowait()
    assert '"name":"long_press"' in payload


@pytest.mark.asyncio
async def test_single_tap_outside_meeting_emits_last_segment_query():
    """AIPI-4-06: outside a meeting, the left-button single tap asks
    HoldSpeak for the most recent segment instead of suppressing."""
    leg = _make_device_leg(is_in_meeting=MagicMock(return_value=False))
    leg._left_button_press_at_ms = int(time.time() * 1000) - 50

    leg._handle_left_button_state(pressed=False)

    await _drain_pending(leg)
    payload = leg.control_queue.get_nowait()
    assert '"type":"query"' in payload
    assert '"name":"last_segment"' in payload

    import json

    obj = json.loads(payload)
    assert isinstance(obj["at"], int)


@pytest.mark.asyncio
async def test_single_tap_outside_meeting_with_agent_waiting_shows_question():
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=False),
        is_agent_waiting=MagicMock(return_value=True),
    )
    leg._left_button_press_at_ms = int(time.time() * 1000) - 50

    leg._handle_left_button_state(pressed=False)

    await _drain_pending(leg)
    payload = leg.control_queue.get_nowait()
    assert '"type":"query"' in payload
    assert '"name":"agent_question"' in payload


@pytest.mark.asyncio
async def test_single_tap_with_unwired_meeting_state_suppresses():
    """If the HoldSpeak leg is not wired yet, do not guess whether the
    tap should be bookmark or query."""
    leg = _make_device_leg(is_in_meeting=None)
    leg._left_button_press_at_ms = int(time.time() * 1000) - 50

    leg._handle_left_button_state(pressed=False)

    await _drain_pending(leg)
    assert leg.control_queue.empty()


@pytest.mark.asyncio
async def test_double_tap_outside_meeting_suppressed():
    """Cycle gesture without an active meeting has no meaning — the
    event is suppressed even when the classifier detects a double-tap."""
    leg = _make_device_leg(is_in_meeting=MagicMock(return_value=False))
    now_ms = int(time.time() * 1000)

    leg._left_button_press_at_ms = now_ms - 50
    leg._handle_left_button_state(pressed=False)
    leg._left_button_press_at_ms = now_ms - 30
    leg._handle_left_button_state(pressed=False)

    await _drain_pending(leg)
    assert leg.control_queue.empty()


@pytest.mark.asyncio
async def test_double_tap_outside_meeting_with_agent_waiting_cycles_target():
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=False),
        is_agent_waiting=MagicMock(return_value=True),
    )
    now_ms = int(time.time() * 1000)

    leg._left_button_press_at_ms = now_ms - 50
    leg._handle_left_button_state(pressed=False)
    leg._left_button_press_at_ms = now_ms - 30
    leg._handle_left_button_state(pressed=False)

    await _drain_pending(leg)
    payload = leg.control_queue.get_nowait()
    assert '"type":"query"' in payload
    assert '"name":"agent_next"' in payload


@pytest.mark.asyncio
async def test_two_taps_outside_window_are_two_bookmarks():
    """When the second tap arrives *after* the double-tap window has
    expired, the first scheduled single-tap should have already fired
    the bookmark; the second tap schedules its own single-tap. Two
    bookmark events total."""
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=True),
        paint_bookmark_flash=AsyncMock(),
    )

    # First tap.
    leg._left_button_press_at_ms = int(time.time() * 1000) - 50
    leg._handle_left_button_state(pressed=False)
    # Let the single-tap timer expire.
    await asyncio.sleep((LEFT_DOUBLE_TAP_WINDOW_MS + 50) / 1000.0)
    # Second tap, well outside the window.
    leg._left_button_press_at_ms = int(time.time() * 1000) - 50
    leg._handle_left_button_state(pressed=False)
    await _drain_pending(leg)

    payloads = []
    while not leg.control_queue.empty():
        payloads.append(leg.control_queue.get_nowait())
    bookmark_count = sum(1 for p in payloads if '"name":"long_press"' in p)
    assert bookmark_count == 2, payloads


@pytest.mark.asyncio
async def test_double_tap_does_not_fire_bookmark():
    """Sanity check: after a double-tap, the pending bookmark task is
    cancelled and no `long_press` event ends up on the wire."""
    flash = AsyncMock()
    leg = _make_device_leg(
        is_in_meeting=MagicMock(return_value=True),
        paint_bookmark_flash=flash,
    )
    now_ms = int(time.time() * 1000)

    leg._left_button_press_at_ms = now_ms - 50
    leg._handle_left_button_state(pressed=False)
    leg._left_button_press_at_ms = now_ms - 30
    leg._handle_left_button_state(pressed=False)
    await _drain_pending(leg)

    flash.assert_not_called()
