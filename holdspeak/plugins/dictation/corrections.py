"""HS-39-02: session-scoped dictation correction memory.

A bounded, thread-safe, in-process store of recent user corrections — "this
utterance should have routed to block X" / "the target was actually Y". The
dictation pipeline consults it (when `corrections_enabled`) so the same
mistake, on a similar utterance, is nudged toward the user's correction within
the session.

The in-memory ring is the fast nudge path on the live typing loop. **Phase 40
(HS-40-02)** made it optionally durable: pass a `repository`
(`db.DictationCorrectionRepository`) and the store loads the recent set on
construction and writes through on `record`, so routing learning survives a
restart. With **no** repository it behaves exactly as it did in Phase 39 —
in-process only, dying with the process. Either way corrections are gist-only
and pass the same secret check the project-doc suggestions use, so a persisted
row never carries a secret.
"""

from __future__ import annotations

import re
import threading
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from holdspeak.project_doc_suggestions import looks_like_secret

if TYPE_CHECKING:  # pragma: no cover - typing only
    from holdspeak.db.corrections import DictationCorrectionRepository

#: Kinds of correction the store accepts.
#:
#: HS-176-02 (ruling R1) adds ``"text"`` — a WORDS correction, not a routing
#: one. Its ``key`` is the phrase **as heard** (stored punctuation-stripped and
#: lowercased) and its ``value`` the phrase **as said**. It never uses Jaccard:
#: `apply_text_corrections` below is its one deterministic matcher, applied at
#: the transcript seam inside `DictationPipeline.run`.
CORRECTION_KINDS = ("intent", "target", "text")
#: The routing kinds — the only ones `best_match_in` (Jaccard) serves.
ROUTING_CORRECTION_KINDS = ("intent", "target")
DEFAULT_CAP = 20
_GIST_MAX = 200
_TOKEN_RE = re.compile(r"[a-z0-9]+")
#: Characters stripped from either edge of a stored `text` key/value (N3).
_EDGE_PUNCT = " \t\r\n\"'`.,;:!?()[]{}<>…-—–"


@dataclass(frozen=True)
class Correction:
    """One user correction. `key` is the context gist, `value` the fix."""

    kind: str          # "intent" | "target" | "text"
    key: str           # gist of the utterance ("intent"/"target"); heard phrase ("text")
    value: str         # corrected block id / target profile / the said phrase
    sequence: int      # monotonic insertion order (newest = highest)
    # HS-176-02: the durable `dictation_corrections.id` when this correction came
    # from (or was written through to) the repository; None for a ring-only
    # store (a bare server / a test), which has no stable id to address. It is
    # what `corrections_applied` records when this rule fires.
    correction_id: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "key": self.key, "value": self.value}


@dataclass(frozen=True)
class RecordOutcome:
    """What `CorrectionStore.record` did, and — when it refused — why.

    HS-176-02 (rulings R4 + R7). `record` used to return a bare `bool`, which
    could neither name the refusal (`REFUSED · ONE WORD` / `REFUSED · SECRET`)
    nor hand the caller the stored row id, so the journal route guessed the id
    from `list_for_display()[0]`. This object carries both and stays
    **truthy/falsy compatible**: `bool(outcome)` is exactly the old return, so
    both existing callers (`web/routes/dictation/pipeline.py:996` and `:1154`,
    which each wrap it in `bool(...)`) keep working unchanged.

    `correction_id` is the durable row id, or None when the store has no
    repository (a ring-only store has no id to link) or the write-through
    failed — never a fabricated id.
    """

    stored: bool
    correction_id: int | None = None
    refusal: str | None = None  # "kind" | "empty" | "secret" | "one_word"

    def __bool__(self) -> bool:
        return bool(self.stored)


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


# ── HS-176-02: the `text` kind's deterministic matcher ────────────────────
# Exact-phrase, NOT Jaccard. `best_match_in` above is untouched and keeps
# serving `intent` / `target` only.


def normalize_text_key(phrase: str) -> str:
    """A `text` correction's stored KEY: collapsed, edge-stripped, lowercased.

    N3: `Utterance.raw_text` is post-`TextProcessor` on the capture path, so
    spoken punctuation is already attached to the tokens (`postgress,` not
    `postgress` + `,`). Stripping the span's edges before storing keeps the key
    `postgress`, and the boundary rule in `_phrase_pattern` then fires it
    inside `postgress,` and `postgress.` alike.
    """
    return " ".join(str(phrase or "").split()).strip(_EDGE_PUNCT).lower()


def normalize_text_value(phrase: str) -> str:
    """A `text` correction's stored VALUE: collapsed and edge-stripped, case kept."""
    return " ".join(str(phrase or "").split()).strip(_EDGE_PUNCT)


def _phrase_pattern(key: str) -> "re.Pattern[str] | None":
    """Case-insensitive, whitespace-tolerant pattern for one stored key.

    The key's tokens are joined by `\\s+` so a rule taught from a single-spaced
    phrase still fires across a newline or a double space. Word boundaries are
    checked by the caller (`isalnum()` on the neighbouring characters), not by
    `\\b`, so the rule is unicode-honest and edge-of-string safe.
    """
    parts = [re.escape(part) for part in str(key or "").split()]
    if not parts:
        return None
    return re.compile(r"\s+".join(parts), re.IGNORECASE)


def _bounded(text: str, start: int, end: int) -> bool:
    """True when [start, end) is bounded by a non-alphanumeric or a string edge.

    This is the rule the design names: `postgress` fires inside `postgress,`
    and `postgress.` and at either end of the string, and never inside
    `postgressive`.
    """
    if start > 0 and text[start - 1].isalnum():
        return False
    if end < len(text) and text[end].isalnum():
        return False
    return True


def _preserve_first_letter(matched: str, value: str) -> str:
    """Case-preserving on the FIRST letter only (the design's rule)."""
    if matched and value and matched[0].isupper():
        return value[0].upper() + value[1:]
    return value


def apply_text_corrections(
    text: str,
    corrections: "list[Correction] | None",
) -> tuple[str, tuple[int, ...]]:
    """Apply every stored `text` rule to `text`; return (new_text, applied ids).

    HS-176-02 (ruling R1). Deterministic and exact-phrase:

    - whitespace-normalized comparison (the key's tokens match across any run
      of whitespace);
    - matching is case-insensitive (the key is stored lowercased);
    - the boundary is non-alphanumeric-or-string-edge;
    - replace is case-preserving on the FIRST letter only;
    - **all** matching rules apply, longest key first (the 175 R1
      longest-wins precedent), recency breaking a length tie;
    - a rule is applied to the text as the previous rules left it.

    The returned ids are the durable `dictation_corrections.id` of the rules
    that actually changed the text. A rule with no durable id (a ring-only
    store) still fires — it simply contributes no id, because there is no row
    for the journal to name. No id is ever fabricated.
    """
    source = str(text or "")
    if not source or not corrections:
        return source, ()

    rules = [
        c
        for c in corrections
        if getattr(c, "kind", "") == "text"
        and normalize_text_key(getattr(c, "key", ""))
        and normalize_text_value(getattr(c, "value", ""))
    ]
    if not rules:
        return source, ()

    ordered = sorted(
        rules,
        key=lambda c: (len(normalize_text_key(c.key)), int(getattr(c, "sequence", 0) or 0)),
        reverse=True,
    )

    applied: list[int] = []
    current = source
    for rule in ordered:
        pattern = _phrase_pattern(normalize_text_key(rule.key))
        if pattern is None:
            continue
        value = normalize_text_value(rule.value)
        out: list[str] = []
        cursor = 0
        fired = False
        for match in pattern.finditer(current):
            if match.start() < cursor:  # overlapping match already consumed
                continue
            if not _bounded(current, match.start(), match.end()):
                continue
            out.append(current[cursor : match.start()])
            out.append(_preserve_first_letter(match.group(0), value))
            cursor = match.end()
            fired = True
        if not fired:
            continue
        out.append(current[cursor:])
        current = "".join(out)
        rule_id = getattr(rule, "correction_id", None)
        if rule_id is not None and int(rule_id) not in applied:
            applied.append(int(rule_id))

    return current, tuple(applied)


class CorrectionStore:
    """Bounded, thread-safe ring of recent corrections (one per session).

    Optionally durable: with a `repository` the store loads the recent set on
    construction and writes through on `record` (HS-40-02). With none it is the
    Phase-39 in-process ring, byte-identical.
    """

    def __init__(
        self,
        cap: int = DEFAULT_CAP,
        *,
        repository: "Optional[DictationCorrectionRepository]" = None,
    ) -> None:
        self._cap = max(1, int(cap))
        self._items: deque[Correction] = deque(maxlen=self._cap)
        self._lock = threading.Lock()
        self._seq = 0
        self._repository = repository
        if repository is not None:
            self._load_from_repository(repository)

    def _load_from_repository(
        self, repository: "DictationCorrectionRepository"
    ) -> None:
        """Hydrate the ring from the most recent persisted corrections.

        Loads at most `cap` rows (newest-first), then replays them oldest-first
        so `sequence` stays monotonic and `best_match_in`'s recency tie-break
        matches insertion order. Defensive: a repository read failure leaves an
        empty in-memory store rather than blocking startup.
        """
        try:
            records = repository.recent_corrections(limit=self._cap)
        except Exception:  # pragma: no cover - durability must never block boot
            return
        with self._lock:
            for record in reversed(records):  # oldest-first
                self._seq += 1
                self._items.append(
                    Correction(
                        kind=record.kind,
                        key=record.gist,
                        value=record.value,
                        sequence=self._seq,
                        correction_id=getattr(record, "id", None),
                    )
                )

    def record(self, kind: str, key: str, value: str) -> RecordOutcome:
        """Store a correction; return a `RecordOutcome` (falsy when refused).

        HS-176-02. The return was a bare `bool` through Phase 175; it is now a
        `RecordOutcome` that is **truthy exactly when the old bool was True**,
        and additionally carries the stored row id (so the journal route can
        link `correction_id` instead of guessing it from the newest row) and
        the refusal's name.

        Refusals, all of them silent no-ops that write nothing:
        `"kind"` (unknown kind), `"empty"` (blank gist or value), `"secret"`
        (the shared `looks_like_secret` check on either side), and
        `"one_word"` — a one-token gist on a **routing** kind, which can only
        reach Jaccard 0.5 against an utterance of at most two tokens and so
        cannot fire on a sentence (ruling R7). It is enforced here, in the
        store, so both HTTP routes and the MCP surface inherit it. The `text`
        kind is exact-phrase and a one-word key is legal for it.
        """
        kind = str(kind or "").strip()
        if kind == "text":
            gist = normalize_text_key(_gist(key))
            value = normalize_text_value(value)
        else:
            gist = _gist(key)
            value = str(value or "").strip()
        if kind not in CORRECTION_KINDS:
            return RecordOutcome(False, refusal="kind")
        if not gist or not value:
            return RecordOutcome(False, refusal="empty")
        if looks_like_secret(gist) or looks_like_secret(value):
            return RecordOutcome(False, refusal="secret")
        if kind in ROUTING_CORRECTION_KINDS and len(_TOKEN_RE.findall(gist.lower())) < 2:
            return RecordOutcome(False, refusal="one_word")
        with self._lock:
            self._seq += 1
            sequence = self._seq
            self._items.append(
                Correction(kind=kind, key=gist, value=value, sequence=sequence)
            )
        # Write through to the durable store after the in-memory append (the
        # ring is the nudge path; persistence is best-effort durability and must
        # never fail a record the live path already accepted).
        correction_id: int | None = None
        if self._repository is not None:
            try:
                stored = self._repository.record_correction(
                    kind=kind, gist=gist, value=value
                )
                correction_id = int(getattr(stored, "id", None) or 0) or None
            except Exception:  # pragma: no cover - durability must never block typing
                correction_id = None
            if correction_id is not None:
                # Re-stamp the ring entry with the durable id so a rule that
                # fires can name itself in the journal's `corrections_applied`.
                with self._lock:
                    for index, item in enumerate(self._items):
                        if item.sequence == sequence:
                            self._items[index] = Correction(
                                kind=item.kind,
                                key=item.key,
                                value=item.value,
                                sequence=item.sequence,
                                correction_id=correction_id,
                            )
                            break
        return RecordOutcome(True, correction_id=correction_id)

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
        """Empty the ring — and the durable store too, when one is attached."""
        with self._lock:
            self._items.clear()
            self._seq = 0
        if self._repository is not None:
            try:
                self._repository.clear()
            except Exception:  # pragma: no cover - durability must never raise
                pass

    def list_for_display(self) -> list[dict[str, object]]:
        """Corrections for the memory UI, newest-first.

        With a repository each row carries its durable `id` + `created_at` (so
        the UI can curate it); with none it falls back to the in-memory ring
        (no id — nothing to delete). The `key` field is the gist either way, so
        the API shape is stable.
        """
        if self._repository is not None:
            try:
                return [
                    {
                        "id": r.id,
                        "kind": r.kind,
                        "key": r.gist,
                        "value": r.value,
                        "created_at": r.created_at,
                    }
                    for r in self._repository.recent_corrections()
                ]
            except Exception:  # pragma: no cover - durability must never raise
                pass
        return [c.to_dict() for c in self.recent()]

    def remove(self, correction_id: object) -> bool:
        """Delete one persistent correction by id; reloads the ring to match.

        A no-op (returns False) when there is no repository — the in-memory ring
        has no stable ids to address.
        """
        if self._repository is None:
            return False
        try:
            removed = self._repository.delete_correction(int(correction_id))
        except (TypeError, ValueError):
            return False
        if removed:
            self._reload_ring()
        return removed

    def _reload_ring(self) -> None:
        """Rebuild the in-memory ring from the durable store (after a delete)."""
        with self._lock:
            self._items.clear()
            self._seq = 0
        if self._repository is not None:
            self._load_from_repository(self._repository)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
