"""HS-39-02: session-scoped dictation correction memory.

A bounded, thread-safe, in-process store of recent user corrections — "this
utterance should have routed to block X" / "the target was actually Y". The
dictation pipeline consults it (when `corrections_enabled`) so the same
mistake, on a similar utterance, is nudged toward the user's correction within
the session.

Deliberately **not** persistent: the store dies with the process (no DB, no
disk). This keeps the DIR-01 "stateless utterance" posture mostly intact —
the only carried state is a small ring of explicit, user-initiated
corrections — and avoids a secret-bearing on-disk store. Corrections are
gist-only and pass the same secret check the project-doc suggestions use.
"""

from __future__ import annotations

import re
import threading
from collections import deque
from dataclasses import dataclass

from holdspeak.project_doc_suggestions import looks_like_secret

#: Kinds of correction the store accepts.
CORRECTION_KINDS = ("intent", "target")
DEFAULT_CAP = 20
_GIST_MAX = 200
_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Correction:
    """One user correction. `key` is the context gist, `value` the fix."""

    kind: str          # "intent" | "target"
    key: str           # gist of the utterance the correction applies to
    value: str         # corrected block id ("intent") or target profile ("target")
    sequence: int      # monotonic insertion order (newest = highest)

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "key": self.key, "value": self.value}


def _gist(text: str) -> str:
    """Single-line, length-bounded gist of an utterance for matching/storage."""
    collapsed = " ".join(str(text or "").split())
    return collapsed[:_GIST_MAX].strip()


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(str(text or "").lower()))


def similarity(a: str, b: str) -> float:
    """Jaccard token overlap in [0.0, 1.0] — cheap, explainable, no embeddings."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def best_match_in(
    corrections: list[Correction] | None,
    kind: str,
    text: str,
    *,
    min_similarity: float = 0.5,
) -> Correction | None:
    """Most-similar correction of `kind` for `text`, or None below threshold.

    Iterates newest-first so that, on a similarity tie, the more recent
    correction wins — recency is the tie-break for a session-scoped nudge.
    """
    if not corrections:
        return None
    best: Correction | None = None
    best_sim = -1.0
    for c in sorted(corrections, key=lambda c: c.sequence, reverse=True):
        if c.kind != kind:
            continue
        sim = similarity(text, c.key)
        if sim > best_sim:
            best, best_sim = c, sim
    if best is not None and best_sim >= min_similarity:
        return best
    return None


class CorrectionStore:
    """Bounded, thread-safe ring of recent corrections (one per session)."""

    def __init__(self, cap: int = DEFAULT_CAP) -> None:
        self._cap = max(1, int(cap))
        self._items: deque[Correction] = deque(maxlen=self._cap)
        self._lock = threading.Lock()
        self._seq = 0

    def record(self, kind: str, key: str, value: str) -> bool:
        """Store a correction. Returns False (no-op) if invalid or secret-like."""
        kind = str(kind or "").strip()
        gist = _gist(key)
        value = str(value or "").strip()
        if kind not in CORRECTION_KINDS or not gist or not value:
            return False
        if looks_like_secret(gist) or looks_like_secret(value):
            return False
        with self._lock:
            self._seq += 1
            self._items.append(Correction(kind=kind, key=gist, value=value, sequence=self._seq))
        return True

    def snapshot(self) -> list[Correction]:
        """A copy of every stored correction, oldest-first."""
        with self._lock:
            return list(self._items)

    def recent(self, kind: str | None = None, limit: int | None = None) -> list[Correction]:
        """Stored corrections newest-first, optionally filtered by kind/limited."""
        items = sorted(self.snapshot(), key=lambda c: c.sequence, reverse=True)
        if kind is not None:
            items = [c for c in items if c.kind == kind]
        if limit is not None:
            items = items[: max(0, int(limit))]
        return items

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
