"""PHILO-15-07 (B01): the transcript must not lie.

Whisper can fall into a loop at the end of a decode window ("finally finally
finally ..." about 250 times on the rehearsal fixture). Whisper itself names
the signal: a decode whose text compresses too well is degenerate
(``compression_ratio_threshold = 2.4``). This module reads that signal on the
text the backend returned, plus a direct repeat check (the same 1-4 word
group many times in a row), so the importer can decode the window again and,
when the second decode is also bad, put an honest mark on the span instead of
the loop: ``[unclear 0:28–0:30]``.

Pure functions, no model: the unit fences call them with synthetic text.
"""

from __future__ import annotations

import re
import zlib

#: Whisper's own threshold (``transcribe(compression_ratio_threshold=2.4)``).
COMPRESSION_RATIO_THRESHOLD = 2.4
#: Short text compresses badly whatever it says; the ratio means nothing
#: below this length, so only the repeat check applies there.
MIN_CHARS_FOR_RATIO = 60
#: The same word group this many times in a row is a loop, not speech.
REPEAT_RUN = 6
#: The longest word group the repeat check looks for.
MAX_GROUP = 4

UNCLEAR_PATTERN = re.compile(r"\[unclear \d+:\d{2}–\d+:\d{2}\]")


def compression_ratio(text: str) -> float:
    """Whisper's degenerate-output measure: raw bytes over zlib bytes."""
    data = text.encode("utf-8")
    if not data:
        return 0.0
    return len(data) / len(zlib.compress(data))


def _norm(word: str) -> str:
    return re.sub(r"[^\w']", "", word.lower())


def loop_start(text: str) -> int | None:
    """The word index where a repeat loop starts, or ``None`` when there is none.

    A loop is one group of 1..``MAX_GROUP`` words repeated at least
    ``REPEAT_RUN`` times in a row ("finally finally ...", "and multiply and
    multiply ..."). Punctuation and case do not count.
    """
    words = [_norm(w) for w in text.split()]
    count = len(words)
    for start in range(count):
        for size in range(1, MAX_GROUP + 1):
            group = words[start : start + size]
            if len(group) < size or not any(group):
                continue
            runs = 1
            cursor = start + size
            while words[cursor : cursor + size] == group:
                runs += 1
                cursor += size
            if runs >= REPEAT_RUN:
                return start
    return None


def is_degenerate(text: str) -> bool:
    """True when ``text`` is a decode loop by Whisper's measure or a direct repeat."""
    stripped = text.strip()
    if not stripped:
        return False
    if len(stripped) >= MIN_CHARS_FOR_RATIO and compression_ratio(stripped) > COMPRESSION_RATIO_THRESHOLD:
        return True
    return loop_start(stripped) is not None


def clock(seconds: float) -> str:
    """``m:ss`` for a transcript mark."""
    total = max(0, int(round(seconds)))
    return f"{total // 60}:{total % 60:02d}"


def unclear_mark(start: float, end: float) -> str:
    """The honest mark a degenerate span carries: ``[unclear 0:28–0:30]``."""
    return f"[unclear {clock(start)}–{clock(max(start, end))}]"


def mark_degenerate(text: str, start: float, end: float) -> str:
    """Keep the words before the loop; the loop itself becomes the mark.

    When the loop starts at the first word (or the text is degenerate by the
    ratio with no single repeat group), the whole text becomes the mark.
    """
    words = text.split()
    index = loop_start(text)
    prefix = " ".join(words[:index]) if index else ""
    mark = unclear_mark(start, end)
    return f"{prefix} {mark}".strip()


def count_unclear(texts) -> int:
    """How many honest marks the transcript carries."""
    return sum(len(UNCLEAR_PATTERN.findall(str(text or ""))) for text in texts)


__all__ = [
    "COMPRESSION_RATIO_THRESHOLD",
    "UNCLEAR_PATTERN",
    "clock",
    "compression_ratio",
    "count_unclear",
    "is_degenerate",
    "loop_start",
    "mark_degenerate",
    "unclear_mark",
]
