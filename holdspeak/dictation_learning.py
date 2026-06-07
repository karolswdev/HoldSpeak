"""HS-48-01: the dictation learning digest ("What HoldSpeak learned").

A read-only aggregation over the two stores the dictation loop already keeps:
the journal (`dictation_journal`, one row per run) and the correction memory
(`dictation_corrections`, kind/gist/value). It answers a single question the
raw Memory + Journal tabs never did: *what has HoldSpeak actually learned from
me, and how far does it reach?*

The one rule that makes this trustworthy: every "N similar" number comes from
the **same** matcher that nudges routing — `corrections.similarity` (Jaccard
token overlap, the function `best_match_in` thresholds on). There is no second
heuristic and no embedding model. So a correction's reported reach is exactly
the set of journal utterances the live pipeline would nudge.

This module computes; it never writes. The route layer fetches the two stores
and hands their rows here.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence

from holdspeak.plugins.dictation.corrections import similarity

#: Windows the digest accepts. "week" is the last 7 days; "all" is everything.
WINDOWS = ("week", "all")
_WEEK_DAYS = 7
#: The match threshold the live router uses (`best_match_in` default). Reusing
#: it keeps the digest's reach honest: the same bar that nudges, counts.
MIN_SIMILARITY = 0.5


def _cutoff_iso(window: str, now: datetime) -> Optional[str]:
    """The ISO lower bound for `window`, or None for 'all' (no bound).

    `created_at` is stored as a naive local ISO string, so a lexicographic
    compare against another same-format ISO string orders chronologically.
    """
    if window == "week":
        return (now - timedelta(days=_WEEK_DAYS)).isoformat()
    return None


def _in_window(created_at: Any, cutoff: Optional[str]) -> bool:
    """True if `created_at` falls within the window.

    A missing timestamp (the bare in-memory correction ring carries none) is
    kept rather than dropped — we would rather show it than silently undercount.
    """
    if cutoff is None:
        return True
    if not created_at:
        return True
    return str(created_at) >= cutoff


def _normalize_corrections(corrections: Optional[Sequence[Any]]) -> list[dict[str, Any]]:
    """Coerce store rows (`list_for_display` dicts) to a stable shape.

    The display rows key the gist as `key`; the durable rows also carry `id` +
    `created_at`. We normalize to `gist` and tolerate either source.
    """
    out: list[dict[str, Any]] = []
    for c in corrections or []:
        if not isinstance(c, dict):
            continue
        out.append(
            {
                "id": c.get("id"),
                "kind": str(c.get("kind") or ""),
                "gist": str(c.get("key") or c.get("gist") or ""),
                "value": str(c.get("value") or ""),
                "created_at": c.get("created_at"),
            }
        )
    return out


def _transcripts(journal_rows: Optional[Sequence[Any]]) -> list[str]:
    out: list[str] = []
    for r in journal_rows or []:
        if isinstance(r, dict):
            out.append(str(r.get("transcript") or ""))
        else:
            out.append(str(getattr(r, "transcript", "") or ""))
    return out


def _row_field(row: Any, name: str) -> Any:
    return row.get(name) if isinstance(row, dict) else getattr(row, name, None)


def build_learning_digest(
    *,
    corrections: Optional[Sequence[Any]],
    journal_rows: Optional[Sequence[Any]],
    window: str = "week",
    now: Optional[datetime] = None,
    enabled: bool = False,
    min_similarity: float = MIN_SIMILARITY,
) -> dict[str, Any]:
    """Aggregate the journal + corrections into a "What HoldSpeak learned" digest.

    Args:
        corrections: rows from `CorrectionStore.list_for_display()` (dicts with
            kind/key/value and, when durable, id/created_at).
        journal_rows: journal records (or dicts) carrying at least `transcript`,
            `created_at`, and `corrected`.
        window: "week" (last 7 days) or "all".
        now: clock injection for deterministic windowing in tests.
        enabled: whether `corrections_enabled` is on. The counts are real either
            way; this flag lets the view phrase coverage honestly ("now nudged"
            only when corrections actually route).
        min_similarity: the Jaccard bar; defaults to the router's own threshold.

    Returns a JSON-ready dict. **Window scopes the activity** (corrections made,
    dictations corrected, the breakdowns). **Per-correction reach ("N similar")
    is computed over the whole journal**, because a correction nudges every
    matching utterance regardless of when it was said — windowing reach would
    understate what the pipeline actually does.
    """
    window = window if window in WINDOWS else "week"
    now = now or datetime.now()
    cutoff = _cutoff_iso(window, now)

    corr = _normalize_corrections(corrections)
    windowed_corr = [c for c in corr if _in_window(c["created_at"], cutoff)]

    all_transcripts = [t for t in _transcripts(journal_rows) if t]

    # Per-correction reach: how many journal utterances this correction would
    # nudge (Jaccard >= threshold), over the whole journal.
    def _similar(gist: str) -> int:
        if not gist:
            return 0
        return sum(1 for t in all_transcripts if similarity(t, gist) >= min_similarity)

    correction_rows: list[dict[str, Any]] = []
    for c in windowed_corr:
        correction_rows.append(
            {
                "id": c["id"],
                "kind": c["kind"],
                "gist": c["gist"],
                "value": c["value"],
                "created_at": c["created_at"],
                "similar": _similar(c["gist"]),
            }
        )

    # Total reach: distinct journal utterances nudged by at least one of the
    # windowed corrections (dedup, so overlapping corrections don't inflate it).
    nudged_total = 0
    if windowed_corr:
        gists = [c["gist"] for c in windowed_corr if c["gist"]]
        for t in all_transcripts:
            if any(similarity(t, g) >= min_similarity for g in gists):
                nudged_total += 1

    # Dictations corrected: journal rows in-window flagged `corrected`.
    dictations_corrected = sum(
        1
        for r in (journal_rows or [])
        if _in_window(_row_field(r, "created_at"), cutoff) and _row_field(r, "corrected")
    )

    by_kind = Counter(c["kind"] for c in windowed_corr if c["kind"])
    by_block = Counter(c["value"] for c in windowed_corr if c["kind"] == "intent" and c["value"])
    by_target = Counter(c["value"] for c in windowed_corr if c["kind"] == "target" and c["value"])

    def _ranked(counter: Counter, label: str) -> list[dict[str, Any]]:
        # Highest count first; ties broken alphabetically for a stable order.
        return [
            {label: name, "count": count}
            for name, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

    return {
        "window": window,
        "enabled": bool(enabled),
        "generated_at": now.isoformat(),
        "totals": {
            "corrections_made": len(windowed_corr),
            "dictations_corrected": dictations_corrected,
            "similar_nudged": nudged_total,
            "journal_count": len(all_transcripts),
        },
        "by_kind": {
            "intent": int(by_kind.get("intent", 0)),
            "target": int(by_kind.get("target", 0)),
        },
        "by_block": _ranked(by_block, "block_id"),
        "by_target": _ranked(by_target, "target_profile"),
        "corrections": correction_rows,
    }
