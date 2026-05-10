"""HS-17-08 — truncate_for_lcd + push_segment_to_devices unit tests."""

from __future__ import annotations

import pytest

from holdspeak.device_status import (
    DeviceStatusEmitter,
    LCD_TEXT_MAX_CHARS,
    push_segment_to_devices,
    truncate_for_lcd,
)


# ---------- truncate_for_lcd ----------


@pytest.mark.parametrize(
    "text,max_len,expected",
    [
        ("", 30, ""),
        ("hello", 30, "hello"),
        ("a" * 30, 30, "a" * 30),
        ("a" * 31, 30, "a" * 29 + "…"),
        ("a" * 100, 30, "a" * 29 + "…"),
        ("hello world", 5, "hell…"),
        ("hello", 1, "…"),
        # max_len smaller than ellipsis fallback: still produce something
        ("hello", 0, "…"),
    ],
)
def test_truncate_for_lcd_handles_edges(text, max_len, expected):
    assert truncate_for_lcd(text, max_len=max_len) == expected


def test_truncate_for_lcd_handles_none():
    assert truncate_for_lcd(None) == ""


def test_truncate_for_lcd_default_max_is_30():
    assert LCD_TEXT_MAX_CHARS == 30
    assert truncate_for_lcd("a" * 31) == "a" * 29 + "…"


# ---------- push_segment_to_devices ----------


class _Segment:
    """Minimal segment duck (TranscriptSegment-shaped)."""

    def __init__(self, *, speaker: str | None = None, text: str = "") -> None:
        self.speaker = speaker
        self.text = text


class _RecordingEmitter:
    """Stand-in DeviceStatusEmitter capturing broadcasts."""

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str, int]] = []

    def broadcast(self, device_ids, text, *, ttl_ms=0):
        ids = list(device_ids)
        self.calls.append((ids, text, ttl_ms))
        return len(ids)


def test_push_segment_pushes_speaker_text_with_default_ttl():
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text="hello world")

    count = push_segment_to_devices(em, ["aipi-1"], seg)

    assert count == 1
    assert em.calls == [(["aipi-1"], "Karol: hello world", 3000)]


def test_push_segment_truncates_long_text():
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text="x" * 100)

    push_segment_to_devices(em, ["aipi-1"], seg)

    [(_, payload, _)] = em.calls
    assert len(payload) == LCD_TEXT_MAX_CHARS
    assert payload.endswith("…")
    assert payload.startswith("Karol: ")


def test_push_segment_handles_missing_speaker():
    em = _RecordingEmitter()
    seg = _Segment(speaker=None, text="hello")

    push_segment_to_devices(em, ["aipi-1"], seg)

    [(_, payload, _)] = em.calls
    assert payload == "?: hello"


def test_push_segment_handles_empty_text():
    """Empty transcript text is a no-op-ish line; still emit so users
    see *something* happened."""
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text="")

    push_segment_to_devices(em, ["aipi-1"], seg)

    [(_, payload, _)] = em.calls
    assert payload == "Karol: "


def test_push_segment_no_attached_devices_noop():
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text="hello")

    count = push_segment_to_devices(em, [], seg)

    assert count == 0
    assert em.calls == []


def test_push_segment_filters_falsy_ids():
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text="hello")

    push_segment_to_devices(em, ["aipi-1", None, "", "aipi-2"], seg)

    [(ids, _, _)] = em.calls
    assert ids == ["aipi-1", "aipi-2"]


def test_push_segment_broadcasts_to_multiple_devices():
    em = _RecordingEmitter()
    seg = _Segment(speaker="Remote", text="meeting started")

    count = push_segment_to_devices(em, ["aipi-1", "aipi-green"], seg)

    assert count == 2
    [(ids, payload, ttl)] = em.calls
    assert ids == ["aipi-1", "aipi-green"]
    assert payload == "Remote: meeting started"
    assert ttl == 3000


def test_push_segment_custom_ttl():
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text="hello")

    push_segment_to_devices(em, ["aipi-1"], seg, ttl_ms=5000)

    [(_, _, ttl)] = em.calls
    assert ttl == 5000


def test_push_segment_works_with_real_emitter():
    """Integration with the actual DeviceStatusEmitter (registers a
    sender, verifies the segment lands)."""
    em = DeviceStatusEmitter()
    received: list[tuple[str, int]] = []

    def sender(text: str, ttl_ms: int) -> None:
        received.append((text, ttl_ms))

    em.register("aipi-1", sender)
    seg = _Segment(speaker="Karol", text="real test")

    count = push_segment_to_devices(em, ["aipi-1"], seg)

    assert count == 1
    assert received == [("Karol: real test", 3000)]
