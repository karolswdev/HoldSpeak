"""Direct unit tests for HoldSpeakLeg._dispatch.

The full-session integration tests in `test_holdspeak_leg.py` exercise
the dispatch path indirectly via a real WebSocket — solid coverage for
the happy path, slow + brittle for edge cases (malformed JSON, unknown
types, error variants). These tests build a HoldSpeakLeg with stub
callbacks, call `_dispatch(payload)` directly, and assert what the
leg *would* paint.
"""

from __future__ import annotations

import asyncio

import pytest
import structlog

from bridge import HoldSpeakLeg, Settings


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


def _make_leg() -> tuple[HoldSpeakLeg, list[str], list[str], list[str]]:
    """Build a HoldSpeakLeg with capturing callbacks.

    Returns the leg + three lists that accumulate (link, activity,
    middle) paints. AIPI-4-11 split flashes off the activity slot —
    they now land in `middle_paints`.
    """
    log = structlog.get_logger()
    link_paints: list[str] = []
    activity_paints: list[str] = []
    middle_paints: list[str] = []

    async def on_link(state: str) -> None:
        link_paints.append(state)

    async def on_activity(rendered: str) -> None:
        activity_paints.append(rendered)

    async def on_middle(rendered: str) -> None:
        middle_paints.append(rendered)

    leg = HoldSpeakLeg(
        _make_settings(),
        log,
        audio_queue=asyncio.Queue(maxsize=10),
        control_queue=asyncio.Queue(maxsize=10),
        on_link_update=on_link,
        on_activity_update=on_activity,
        on_middle_update=on_middle,
    )
    return leg, link_paints, activity_paints, middle_paints


async def _drain_pending(leg: HoldSpeakLeg, timeout_s: float = 0.5) -> None:
    """Wait for any tasks _dispatch spawned to finish (with a cap).

    `_dispatch` is sync but kicks off asyncio.create_task(...) for the
    LCD paints. Tests need to yield control so those tasks run before
    asserting on the captured paints.
    """
    deadline = asyncio.get_running_loop().time() + timeout_s
    while leg._pending_tasks and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.01)


# ---------- Happy paths ----------


@pytest.mark.asyncio
async def test_dispatch_status_sticky_paints_and_records_sticky():
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch({"type": "status", "text": "Recording 00:30", "ttl_ms": 0})
    await _drain_pending(leg)

    # AIPI-4-04: Recording → LV_SYMBOL_PLAY. AIPI-4-11: sticky → bottom only.
    assert activity == [f"Recording 00:30  {chr(0xF04B)}"]
    assert _middle == []
    assert leg._sticky_activity == f"Recording 00:30  {chr(0xF04B)}"


@pytest.mark.asyncio
async def test_dispatch_status_flash_paints_middle_persist():
    """AIPI-4-11 v2: a ttl_ms > 0 status frame paints to MIDDLE
    (not bottom) and persists until the next flash replaces it.
    Bottom sticky is untouched."""
    leg, _link, activity, middle = _make_leg()
    # Seed a sticky to verify it survives the flash.
    leg._sticky_activity = f"Recording 00:30  {chr(0xF04B)}"

    leg._dispatch({"type": "status", "text": "Bookmark @ 47s", "ttl_ms": 200})
    await _drain_pending(leg)

    # AIPI-4-04: Bookmark → LV_SYMBOL_BELL.
    assert any(f"Bookmark @ 47s  {chr(0xF0E7)}" in m for m in middle)
    assert activity == []
    # Bottom sticky untouched — flash lives in a different slot.
    assert leg._sticky_activity == f"Recording 00:30  {chr(0xF04B)}"


@pytest.mark.asyncio
async def test_dispatch_session_busy_paints_busy_with_symbol():
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch(
        {
            "type": "error",
            "code": "session_busy",
            "reason": "another voice-typing session is already active",
        }
    )
    await _drain_pending(leg)

    # AIPI-4-04: Busy → LV_SYMBOL_WARNING. AIPI-4-11: flash → middle slot.
    assert _middle == [f"Busy  {chr(0xF071)}"]
    assert activity == []


@pytest.mark.asyncio
async def test_dispatch_generic_error_paints_with_error_symbol():
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch(
        {
            "type": "error",
            "code": "rate_limited",
            "reason": "slow down",
        }
    )
    await _drain_pending(leg)

    # AIPI-4-11: error flash → middle, not activity.
    assert len(_middle) == 1
    assert _middle[0].startswith("Error: slow down")
    assert chr(0xF00D) in _middle[0]
    assert activity == []


@pytest.mark.asyncio
async def test_dispatch_unknown_word_renders_with_default_symbol():
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch({"type": "status", "text": "Reticulating splines", "ttl_ms": 0})
    await _drain_pending(leg)

    # AIPI-4-04: unknown leading word → empty symbol (no glyph for unknown
    # states); `_format_activity` strips the trailing whitespace+symbol.
    assert activity == ["Reticulating splines"]


# ---------- Validation paths ----------


@pytest.mark.asyncio
async def test_dispatch_status_missing_field_no_paint():
    """Malformed status (missing text/ttl_ms) is logged + ignored, never
    crashes the dispatch loop."""
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch({"type": "status", "text": "missing ttl_ms"})  # bad
    await _drain_pending(leg)

    assert activity == []


@pytest.mark.asyncio
async def test_dispatch_error_unknown_field_no_paint():
    """Pydantic `extra="forbid"` should reject and the dispatch should
    eat the validation error."""
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch(
        {
            "type": "error",
            "code": "x",
            "reason": "y",
            "stowaway": "field",  # not in the schema
        }
    )
    await _drain_pending(leg)

    assert activity == []


@pytest.mark.asyncio
async def test_dispatch_unknown_type_no_paint():
    """Per the protocol, unknown control types are non-fatal."""
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch({"type": "the-future-protocol", "data": [1, 2, 3]})
    await _drain_pending(leg)

    assert activity == []


@pytest.mark.asyncio
async def test_dispatch_no_type_field_no_paint():
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch({"text": "no type"})
    await _drain_pending(leg)

    assert activity == []


# ---------- Sequencing ----------


@pytest.mark.asyncio
async def test_dispatch_two_sticky_status_frames_overwrite_sticky():
    leg, _link, activity, _middle = _make_leg()
    leg._dispatch({"type": "status", "text": "Listening...", "ttl_ms": 0})
    await _drain_pending(leg)
    leg._dispatch({"type": "status", "text": "Recording 00:00", "ttl_ms": 0})
    await _drain_pending(leg)

    # AIPI-4-04: Listening → LV_SYMBOL_AUDIO; Recording → LV_SYMBOL_PLAY.
    assert activity == ["Listening...  ", "Recording 00:00  "]
    assert leg._sticky_activity == "Recording 00:00  "


@pytest.mark.asyncio
async def test_dispatch_new_flash_replaces_previous_middle_paint():
    """AIPI-4-11 v2: a newer flash overwrites the previous middle
    text immediately. No auto-clear timer is scheduled (middle
    persists until replaced)."""
    leg, _link, activity, middle = _make_leg()
    leg._sticky_activity = f"Recording 00:30  {chr(0xF04B)}"

    leg._dispatch({"type": "status", "text": "Bookmark @ 47s", "ttl_ms": 5000})
    await _drain_pending(leg)
    assert any("Bookmark" in m for m in middle)

    # Another flash. Replaces the previous middle text.
    leg._dispatch({"type": "error", "code": "session_busy", "reason": "busy"})
    await _drain_pending(leg)

    # Most recent middle paint contains "Busy".
    assert "Busy" in middle[-1]
    # Bottom sticky never changed — flashes do not touch it.
    assert leg._sticky_activity == f"Recording 00:30  {chr(0xF04B)}"


# ---------- AIPI-4-06 query timeout ----------


@pytest.mark.asyncio
async def test_last_segment_query_timeout_paints_middle():
    leg, _link, activity, middle = _make_leg()
    leg.QUERY_TIMEOUT_S = 0.01

    leg._maybe_track_outbound_query(
        '{"type":"query","name":"last_segment","at":1235}'
    )
    await _drain_pending(leg)

    assert activity == []
    assert middle == [f"Query timeout  {chr(0xF00D)}"]


@pytest.mark.asyncio
async def test_status_cancels_last_segment_query_timeout():
    leg, _link, _activity, middle = _make_leg()
    leg.QUERY_TIMEOUT_S = 0.05

    leg._maybe_track_outbound_query(
        '{"type":"query","name":"last_segment","at":1235}'
    )
    leg._dispatch({"type": "status", "text": "No transcript yet", "ttl_ms": 5000})
    await _drain_pending(leg)
    await asyncio.sleep(0.07)

    assert any("No transcript yet" in m for m in middle)
    assert not any("Query timeout" in m for m in middle)


@pytest.mark.asyncio
async def test_last_segment_query_response_is_truncated_to_lcd_width():
    leg, _link, _activity, middle = _make_leg()
    leg.QUERY_TIMEOUT_S = 0.05

    leg._maybe_track_outbound_query(
        '{"type":"query","name":"last_segment","at":1235}'
    )
    leg._dispatch(
        {
            "type": "status",
            "text": "This is a long transcript segment that should be trimmed",
            "ttl_ms": 5000,
        }
    )
    await _drain_pending(leg)

    assert middle == ["This is a long transcript seg…"]
    assert len(middle[0]) == 30


@pytest.mark.asyncio
async def test_non_query_status_is_not_truncated():
    leg, _link, _activity, middle = _make_leg()
    text = "This is a long spontaneous status that should remain intact"

    leg._dispatch({"type": "status", "text": text, "ttl_ms": 5000})
    await _drain_pending(leg)

    assert middle == [text]


@pytest.mark.asyncio
async def test_non_query_control_frame_does_not_start_timeout():
    leg, _link, activity, middle = _make_leg()
    leg.QUERY_TIMEOUT_S = 0.01

    leg._maybe_track_outbound_query('{"type":"start"}')
    await asyncio.sleep(0.03)
    await _drain_pending(leg)

    assert activity == []
    assert middle == []
