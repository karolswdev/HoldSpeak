"""Line-free census keys (owner ruling 2026-10-03: a fence reads text, not lines).

A line number moves with every edit above it, so a census that pins
``path:line`` goes red on changes that touch no censused site. A key from
here names the file, the enclosing scope and the site itself. When one scope
holds the same site more than once, the later ones carry ``#2``, ``#3`` in
source order: a second call in a known scope is still a new key, and the
census still fails until someone reads it.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, NamedTuple


class Record(NamedTuple):
    path: str
    line: int
    col: int
    tail: str  # scope and site, e.g. ``dispatch|run``


def ordinal_keys(records: Iterable[Record]) -> list[str]:
    """One key per record: ``path|tail``, then ``path|tail#2`` for a repeat."""
    seen: Counter[str] = Counter()
    keys: list[str] = []
    for record in sorted(records):
        base = f"{record.path}|{record.tail}"
        seen[base] += 1
        keys.append(base if seen[base] == 1 else f"{base}#{seen[base]}")
    return sorted(keys)
