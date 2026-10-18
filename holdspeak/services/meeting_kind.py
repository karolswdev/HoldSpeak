"""Betterment P2: is a meeting a 1:1?

Decision 18 (docs/internal/betterment/DECISIONS.md): a project update leaves
out 1:1s and People notes unless the owner adds them by hand. A meeting is a
1:1 when its title says so ("1:1 with Mira", "Mira 1:1", "1-on-1"), or when
it has exactly two speakers and one of them is one of his People.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

# "1:1", "1-1", "1-on-1", "1on1", "one-on-one", as a word of its own (so
# "11:11" or "10:15" never match).
_ONE_ON_ONE_TITLE = re.compile(
    r"(?<![\w:])(?:1\s*(?::|-|on|-on-)\s*1|one[\s-]on[\s-]one)(?!\w)",
    re.IGNORECASE,
)


def title_says_one_on_one(title: str | None) -> bool:
    return bool(_ONE_ON_ONE_TITLE.search(str(title or "")))


def meeting_speakers(meeting: Any) -> set[str]:
    """The distinct speaker names of a meeting's transcript."""
    names: set[str] = set()
    for segment in getattr(meeting, "segments", None) or []:
        name = " ".join(str(getattr(segment, "speaker", "") or "").split())
        if name:
            names.add(name)
    return names


def _name_keys(name: str) -> set[str]:
    """A person matches by full name or by first name ("Mira Okafor", "Mira")."""
    clean = " ".join(str(name or "").split()).casefold()
    if not clean:
        return set()
    return {clean, clean.split(" ", 1)[0]}


def is_one_on_one(
    title: str | None,
    speakers: Iterable[str],
    people_names: Iterable[str] = (),
) -> bool:
    if title_says_one_on_one(title):
        return True
    distinct = {" ".join(str(s).split()) for s in speakers if str(s).strip()}
    if len(distinct) != 2:
        return False
    people: set[str] = set()
    for name in people_names:
        people |= _name_keys(name)
    if not people:
        return False
    return any(_name_keys(speaker) & people for speaker in distinct)
