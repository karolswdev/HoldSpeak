"""Server → device status push-back (HS-14-07).

The AIPI-Lite-class device's LCD shows what HoldSpeak says it's
doing: ``Listening...`` while the user holds the button,
``Thinking...`` while transcription runs, the transcript
snippet on completion, ``Recording 12:34`` during a meeting,
``Bookmark @ 47s`` after a long-press, and so on.

This module owns the cross-thread plumbing only.
:class:`DeviceStatusEmitter` is a thread-safe registry of
per-device sender callables. The WebSocket route
(:mod:`holdspeak.device_audio_ws`) registers a sender at handshake
acceptance time that puts each status onto an asyncio queue
served by the connection's writer task; the runtime's voice and
meeting paths call :meth:`DeviceStatusEmitter.send` /
:meth:`DeviceStatusEmitter.broadcast` from any thread.

Callers may include the placeholder ``{label}`` in the status
text; the emitter substitutes it with the device's registered
label (resolved via the supplied ``DeviceRegistry``).
"""

from __future__ import annotations

import re
import threading
from typing import Callable, Iterable, Optional, Protocol

from .logging_config import get_logger

log = get_logger("device_status")

StatusSender = Callable[[str, int], None]


class _LabelLookup(Protocol):
    """Subset of ``DeviceRegistry`` we need to resolve ``{label}``."""

    def get(self, device_id: str): ...  # noqa: D401 - matches DeviceRegistry.get


class DeviceStatusEmitter:
    """Thread-safe registry of per-device status senders.

    The WebSocket handler registers a sender at handshake-accept
    time and unregisters on disconnect. Every send is fire-and-
    forget — failures (queue full, connection torn down) are
    logged but do not raise.
    """

    def __init__(self, *, label_lookup: Optional[_LabelLookup] = None) -> None:
        self._lock = threading.Lock()
        self._senders: dict[str, StatusSender] = {}
        self._label_lookup = label_lookup

    def register(self, device_id: str, sender: StatusSender) -> None:
        with self._lock:
            self._senders[device_id] = sender

    def unregister(self, device_id: str) -> None:
        with self._lock:
            self._senders.pop(device_id, None)

    def is_registered(self, device_id: str) -> bool:
        with self._lock:
            return device_id in self._senders

    def active_device_ids(self) -> list[str]:
        with self._lock:
            return list(self._senders.keys())

    def send(self, device_id: str, text: str, *, ttl_ms: int = 0) -> bool:
        """Send a status message to ``device_id``.

        Returns ``True`` when the message was handed to the
        connection's writer queue, ``False`` when no sender is
        registered for that device or the dispatch raised.
        """
        rendered = self._render(device_id, text)
        with self._lock:
            sender = self._senders.get(device_id)
        if sender is None:
            return False
        try:
            sender(rendered, int(ttl_ms))
            return True
        except Exception:
            log.exception(
                "device_status_send_failed",
                extra={"device_id": device_id},
            )
            return False

    def broadcast(
        self,
        device_ids: Iterable[str],
        text: str,
        *,
        ttl_ms: int = 0,
    ) -> int:
        """Send the same message to several devices.

        Returns the count of successful sends.
        """
        delivered = 0
        for device_id in device_ids:
            if self.send(device_id, text, ttl_ms=ttl_ms):
                delivered += 1
        return delivered

    def _render(self, device_id: str, text: str) -> str:
        if "{label}" not in text:
            return text
        label = device_id
        if self._label_lookup is not None:
            try:
                descriptor = self._label_lookup.get(device_id)
            except Exception:
                descriptor = None
            if descriptor is not None:
                resolved = getattr(descriptor, "label", None)
                if resolved:
                    label = str(resolved)
        return text.replace("{label}", label)


# HS-17-08: width budget for status text on the AIPI-Lite LCD.
# HS-17-15 / AIPI-4-12: bumped from 30 to 150 once the device-side
# middle widget grew to multi-line word-wrap (~7 lines × ~22 chars
# of Montserrat 10). The bottom widget uses SCROLL_CIRCULAR, so
# long text marquee-scrolls there instead of getting clipped.
# Short payloads still render single-line on both widgets — this
# is a ceiling, not a target.
LCD_TEXT_MAX_CHARS = 150


# HS-17-13: known Whisper hallucination patterns. Filtered out of the
# device LCD pushback path so noise doesn't compete with real content.
# Whisper produces these from silence/noise, especially with auto-
# language detection on short clips. The durable meeting transcript
# stores them unchanged — this list only applies to LCD pushback.

# Single words (case-insensitive after strip). Deliberately narrow:
# real meeting words like "hello", "yeah", "yes", "no", "ok", "thanks"
# are KEPT — false-positive cost is too high. These are only the
# clearest Whisper artifacts.
_HALLUCINATION_WORDS: frozenset[str] = frozenset(
    {
        "you",
        "uh",
        "um",
        "the",
    }
)

# Short phrases (lowercase, trailing punctuation stripped). The
# classic Whisper YouTube-training-data hallucinations.
_HALLUCINATION_PHRASES: frozenset[str] = frozenset(
    {
        "thanks for watching",
        "subscribe to my channel",
        "please subscribe",
        "like and subscribe",
        "thanks for watching subscribe",
    }
)

# Matches text that's nothing but whitespace + punctuation (any common
# Western punctuation, dots, ellipsis chars, dashes, etc.). Whisper
# outputs literal `...` strings from silence; this catches those.
_ONLY_PUNCT_RE = re.compile(r"^[\s.,!?…\-—_'\"`/\\:;]*$")


def is_pure_silence(text: str) -> bool:
    """Return True for text that represents no captured audio content.

    HS-17-14: distinguishes between *no audio* (empty / whitespace /
    only-punctuation) and *audio that produced unparseable words*
    (single-word artifacts, repeated patterns). Pure-silence
    segments get no LCD ack; word-level hallucinations get a
    `{speaker}: …` marker so the user knows the system did hear
    them but couldn't transcribe anything useful.
    """
    if not text:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    if _ONLY_PUNCT_RE.match(stripped):
        return True
    return False


def is_likely_hallucination(text: str) -> bool:
    """Return True for transcripts that are likely Whisper hallucinations.

    HS-17-13: applied to LCD pushback in `push_segment_to_devices`;
    durable meeting transcript is unaffected.

    Filters:
    - Empty / whitespace-only.
    - All-punctuation (e.g., `...`, `…`).
    - Single-word artifacts (`you`, `yeah`, `thanks`, etc.) — case-
      insensitive, trailing punctuation stripped.
    - Repeated single-word patterns (`you you you`, `the the the`).
    - Known short-phrase hallucinations (`thank you`, `thanks for watching`,
      `subscribe to my channel`, etc.).

    Returns False for real meeting content — anything longer or richer
    than the patterns above. The filter errs on the side of letting
    content through.
    """
    if not text:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    if _ONLY_PUNCT_RE.match(stripped):
        return True
    # Normalise: lowercase, drop trailing punctuation that Whisper
    # tends to add for sentence-end politeness.
    normalised = stripped.lower().rstrip(".,!?…")
    if not normalised:
        return True
    # Single-word artifacts.
    words = normalised.split()
    if len(words) == 1 and words[0] in _HALLUCINATION_WORDS:
        return True
    # Repeated single-word: "you you you", "the the".
    if len(words) >= 2 and len(set(words)) == 1:
        return True
    # Short-phrase hallucinations.
    if normalised in _HALLUCINATION_PHRASES:
        return True
    return False


def truncate_for_lcd(text: str, max_len: int = LCD_TEXT_MAX_CHARS) -> str:
    """Truncate `text` to `max_len` chars + `…` if needed.

    Stable cross-call: ASCII fast-path, single-pass length check, no
    splitting. Used by per-segment / intel / action-item pushback so
    long meeting strings don't overflow the LCD's single line.
    """
    if text is None:
        return ""
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return "…"
    return text[: max_len - 1] + "…"


def push_segment_to_devices(
    emitter: "DeviceStatusEmitter",
    attached_ids: Iterable[str],
    segment,
    *,
    ttl_ms: int = 3000,
) -> int:
    """Push a finalized transcript segment to all attached devices.

    HS-17-08: turns the AIPI-Lite LCD into a live confirmation channel
    during meetings — every finalized utterance flashes briefly on
    the device. Returns the count of successful sends (matches
    `DeviceStatusEmitter.broadcast`'s contract). No-op + returns 0
    if `attached_ids` is empty.

    `segment` is duck-typed — we read `.speaker` (optional) and
    `.text`. Built so the caller doesn't have to think about
    TranscriptSegment vs. a future SegmentDict.
    """
    ids = [d for d in attached_ids if d]
    if not ids:
        return 0
    text = getattr(segment, "text", "") or ""
    speaker = getattr(segment, "speaker", None) or "?"
    # HS-17-13: filter known Whisper hallucinations out of LCD pushback.
    # HS-17-14: split filtered cases — pure silence skips entirely;
    # word-level hallucinations still push a `{speaker}: …` marker so
    # the device's middle slot updates and the user gets feedback that
    # audio was heard (just unparseable). The durable transcript is
    # unaffected either way.
    if is_likely_hallucination(text):
        if is_pure_silence(text):
            log.debug(
                "device_status_segment_filtered",
                extra={"speaker": speaker, "text_preview": text[:60]},
            )
            return 0
        log.debug(
            "device_status_segment_filtered_acked",
            extra={"speaker": speaker, "text_preview": text[:60]},
        )
        payload = truncate_for_lcd(f"{speaker}: …")
        return emitter.broadcast(ids, payload, ttl_ms=ttl_ms)
    payload = truncate_for_lcd(f"{speaker}: {text}")
    return emitter.broadcast(ids, payload, ttl_ms=ttl_ms)


__all__ = [
    "DeviceStatusEmitter",
    "StatusSender",
    "LCD_TEXT_MAX_CHARS",
    "truncate_for_lcd",
    "push_segment_to_devices",
    "is_likely_hallucination",
    "is_pure_silence",
]
