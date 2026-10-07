"""PHILO-15-07 (B01): the transcript must not lie.

Whisper can fall into a loop at the end of a decode window ("finally finally
finally ..." about 250 times on the rehearsal fixture). The loop has one
shape: the same short group repeated many times in a row, as words ("finally
finally", "and multiply and multiply") or inside one long token
("Sukekekekeke..."). This module detects that shape, so the importer can
decode the window again and, when the second decode is also bad, put an
honest mark beside the span (its words are kept): ``[unclear 0:28–0:30]``.

Astra r1 on #982: the compression ratio alone is not the test. A count-up
("number 1 ... number 50") compresses at 4.08 and is speech; six "yes" and
"Go team!" six times are speech. Only a repeat run longer than people speak
is a loop.

Pure functions, no model: the unit fences call them with synthetic text.
"""

from __future__ import annotations

import re
import zlib

#: The same 1..``MAX_GROUP`` word group this many times in a row is a loop.
#: People repeat a word a few times ("yes yes yes", a chant of six); Whisper
#: loops repeat it tens to hundreds of times.
REPEAT_RUN = 10
#: The longest word group the repeat check looks for.
MAX_GROUP = 4
#: A loop inside one token: the same 1..12 characters this many times in a
#: row ("kekekeke..."). Laughter ("hahaha") stays well under it.
CHAR_RUN = 20
_CHAR_LOOP = re.compile(r"(.{1,12}?)\1{%d,}" % (CHAR_RUN - 1), re.S)

UNCLEAR_PATTERN = re.compile(r"\[unclear \d+:\d{2}–\d+:\d{2}\]")


def compression_ratio(text: str) -> float:
    """Whisper's compression measure: raw bytes over zlib bytes (diagnostic only)."""
    data = text.encode("utf-8")
    if not data:
        return 0.0
    return len(data) / len(zlib.compress(data))


def _norm(word: str) -> str:
    return re.sub(r"[^\w']", "", word.lower())


def _word_loop_start(words: list[str]) -> int | None:
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


def loop_start(text: str) -> int | None:
    """The word index where a repeat loop starts, or ``None`` when there is none.

    A loop is one group of 1..``MAX_GROUP`` words repeated at least
    ``REPEAT_RUN`` times in a row, or 1..12 characters repeated at least
    ``CHAR_RUN`` times in a row inside the text (then the index is the word
    the loop starts in). Punctuation and case do not count for words.
    """
    words = [_norm(w) for w in text.split()]
    found = _word_loop_start(words)
    match = _CHAR_LOOP.search(text)
    if match is not None and match.group(1).strip():
        group = match.group(1)
        begin = match.start() + (len(group) - len(group.lstrip()))
        char_word = len(text[:begin].split())
        # A loop that starts inside a word drops that whole word.
        if begin > 0 and not text[begin - 1].isspace():
            char_word = max(0, char_word - 1)
        found = char_word if found is None else min(found, char_word)
    return found


def is_degenerate(text: str) -> bool:
    """True when ``text`` holds a decode loop (Whisper's loop shape)."""
    stripped = text.strip()
    return bool(stripped) and loop_start(stripped) is not None


def clock(seconds: float) -> str:
    """``m:ss`` for a transcript mark."""
    total = max(0, int(round(seconds)))
    return f"{total // 60}:{total % 60:02d}"


def unclear_mark(start: float, end: float) -> str:
    """The honest mark a degenerate span carries: ``[unclear 0:28–0:30]``."""
    return f"[unclear {clock(start)}–{clock(max(start, end))}]"


def mark_degenerate(text: str, start: float, end: float) -> str:
    """Keep every recognised word and append the honest mark.

    Owner-side ruling on Astra's iteration 2 (#982): a mark NEVER deletes
    words. Real speech can look like a loop ("next." twelve times), so the
    guard annotates and never replaces: a true Whisper loop reads as the
    repeated word plus the mark (ugly but honest), and the WARN lamp counts it.
    """
    return f"{text.strip()} {unclear_mark(start, end)}".strip()


def count_unclear(texts) -> int:
    """How many honest marks the transcript carries.

    The ONE definition (Astra r1 on #982): the count of valid
    ``[unclear m:ss–m:ss]`` marks. The list row and the detail both use it.
    """
    return sum(len(UNCLEAR_PATTERN.findall(str(text or ""))) for text in texts)


__all__ = [
    "UNCLEAR_PATTERN",
    "clock",
    "compression_ratio",
    "count_unclear",
    "is_degenerate",
    "loop_start",
    "mark_degenerate",
    "unclear_mark",
]
