"""Cut one source into chunks (MEMORY-DESIGN.md §3.1 step 3).

A chunk is at most ``CHUNK_CHARS`` characters and is cut on a unit boundary:
a speaker turn, a paragraph or a message.  A unit that is too long is cut on
a sentence end, then on a space.  Each chunk has the source title in front,
so a short row is one chunk that says what it is.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

CHUNKER_VERSION = 1
CHUNK_CHARS = 1200

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_BLANK_LINE = re.compile(r"\n\s*\n")


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    anchor: str
    text: str


def paragraphs(text: str) -> list[str]:
    return [part.strip() for part in _BLANK_LINE.split(str(text or "")) if part.strip()]


def _split_long(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(text):
        while len(sentence) > limit:
            cut = sentence.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            if current:
                pieces.append(current)
                current = ""
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if not sentence:
            continue
        if current and len(current) + 1 + len(sentence) > limit:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_units(
    title: str,
    units: Iterable[Sequence[str]],
    *,
    limit: int = CHUNK_CHARS,
) -> list[Chunk]:
    """Pack ``(anchor, text)`` units into chunks.  The anchor of a chunk is the
    anchor of its first unit."""
    head = " ".join(str(title or "").split())
    budget = max(200, limit - len(head) - 1) if head else limit
    packed: list[tuple[str, str]] = []
    anchor = ""
    current = ""
    for unit_anchor, unit_text in units:
        text = str(unit_text or "").strip()
        if not text:
            continue
        for piece in _split_long(text, budget):
            if current and len(current) + 1 + len(piece) > budget:
                packed.append((anchor, current))
                current = ""
            if not current:
                anchor = str(unit_anchor or "")
                current = piece
            else:
                current = f"{current}\n{piece}"
    if current:
        packed.append((anchor, current))
    if not packed and head:
        packed.append(("", ""))
    chunks: list[Chunk] = []
    for ordinal, (chunk_anchor, body) in enumerate(packed):
        if head and body and not body.startswith(head):
            text = f"{head}\n{body}"
        else:
            text = body or head
        chunks.append(Chunk(ordinal=ordinal, anchor=chunk_anchor, text=text))
    return chunks


__all__ = ["CHUNKER_VERSION", "CHUNK_CHARS", "Chunk", "chunk_units", "paragraphs"]
