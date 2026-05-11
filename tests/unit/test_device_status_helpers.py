"""HS-17-08 — truncate_for_lcd + push_segment_to_devices unit tests."""

from __future__ import annotations

import pytest

from holdspeak.device_status import (
    DeviceStatusEmitter,
    LCD_TEXT_MAX_CHARS,
    is_likely_hallucination,
    is_pure_silence,
    push_segment_to_devices,
    truncate_for_lcd,
)


# ---------- is_likely_hallucination (HS-17-13) ----------


@pytest.mark.parametrize(
    "text",
    [
        # Empty / whitespace.
        "",
        "   ",
        "\n\t",
        # All-punctuation (Whisper's silence outputs).
        "...",
        "....",
        "…",
        "….....",
        ",,,",
        "—",
        ". . .",
        # Single-word artifacts (case-insensitive, trailing-punct stripped).
        "you",
        "You",
        "you.",
        "You!",
        "uh",
        "um",
        "the",
        "The.",
        # Repeated same word.
        "you you",
        "you you you",
        "the the the",
        "You you you",
        # Famous Whisper YouTube hallucinations.
        "Thanks for watching",
        "thanks for watching",
        "Thanks for watching!",
        "Subscribe to my channel",
        "Please subscribe",
        "Like and subscribe!",
    ],
)
def test_is_likely_hallucination_filters_artifacts(text):
    assert is_likely_hallucination(text) is True, f"failed to filter {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        # Real content — even short common words shouldn't be filtered.
        "Hello",
        "Hello everyone",
        "Yeah",
        "Yes",
        "No",
        "OK",
        "Okay",
        "Thanks",
        "Thank you",  # short but real
        "Bye",
        "Goodbye",
        # Long sentences that happen to start with filterable words.
        "You are right about that",
        "The meeting starts at noon",
        "Um, can we discuss the timeline?",
        # Real meeting phrases.
        "Are we opening up here?",
        "What's going on?",
        "Let me know when you're ready.",
        # Other words containing "you" as substring.
        "young",
        "yours",
    ],
)
def test_is_likely_hallucination_keeps_real_content(text):
    assert is_likely_hallucination(text) is False, f"falsely filtered {text!r}"


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


def test_truncate_for_lcd_default_is_lcd_max():
    # HS-17-15 / AIPI-4-12: bumped to 150 once the middle widget grew
    # multi-line.
    assert LCD_TEXT_MAX_CHARS == 150
    assert truncate_for_lcd("a" * (LCD_TEXT_MAX_CHARS + 1)) == "a" * (LCD_TEXT_MAX_CHARS - 1) + "…"


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
    # HS-17-15: LCD_TEXT_MAX_CHARS = 150 now; use a payload that
    # clearly overflows even with the larger ceiling.
    seg = _Segment(speaker="Karol", text="x" * (LCD_TEXT_MAX_CHARS * 2))

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


def test_push_segment_filters_empty_text():
    """HS-17-13: empty transcript text is filtered out (hallucination
    bucket). HS-17-14: pure silence (empty, whitespace, only-punct)
    skips entirely — no LCD ack. Durable transcript still gets it."""
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text="")

    count = push_segment_to_devices(em, ["aipi-1"], seg)

    assert count == 0
    assert em.calls == []


# ---------- is_pure_silence (HS-17-14) ----------


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "\n\t",
        "...",
        "….....",
        ",,,",
        "—",
        ". . .",
    ],
)
def test_is_pure_silence_true_for_empty_and_punct(text):
    assert is_pure_silence(text) is True, f"failed for {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "you",
        "You.",
        "you you you",
        "Thanks for watching",
        "Hello",
        "Real meeting content",
    ],
)
def test_is_pure_silence_false_for_word_content(text):
    assert is_pure_silence(text) is False, f"falsely silent for {text!r}"


# ---------- push_segment_to_devices: HS-17-14 ack behavior ----------


@pytest.mark.parametrize(
    "text",
    [
        "you",
        "You",
        "You.",
        "the",
        "you you you",
        "Thanks for watching",
        "Subscribe to my channel",
    ],
)
def test_push_segment_acks_word_level_hallucinations(text):
    """HS-17-14: word-level hallucinations (Whisper heard *something*
    but produced unparseable artifacts) push a `{speaker}: …` marker
    so the device's middle slot updates and the user knows they were
    heard. Without the ack, persist-until-replaced leaves stale text
    on screen."""
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text=text)

    count = push_segment_to_devices(em, ["aipi-1"], seg)

    assert count == 1
    [(ids, payload, ttl)] = em.calls
    assert ids == ["aipi-1"]
    assert payload == "Karol: …"
    assert ttl == 3000


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "...",
        "….....",
        ",,,",
    ],
)
def test_push_segment_skips_pure_silence(text):
    """HS-17-14: empty / whitespace / only-punctuation segments do
    NOT push an ack — there was no audio worth acknowledging."""
    em = _RecordingEmitter()
    seg = _Segment(speaker="Karol", text=text)

    count = push_segment_to_devices(em, ["aipi-1"], seg)

    assert count == 0
    assert em.calls == []


def test_push_segment_ack_uses_unknown_speaker_when_missing():
    em = _RecordingEmitter()
    seg = _Segment(speaker=None, text="you you you")

    push_segment_to_devices(em, ["aipi-1"], seg)

    [(_, payload, _)] = em.calls
    assert payload == "?: …"


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
