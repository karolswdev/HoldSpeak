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

from holdspeak.plugins.dictation.corrections import (
    CORRECTION_KINDS,
    best_match_in,
    similarity,
)

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


def reach_for_gist(
    gist: str,
    transcripts: Sequence[str],
    *,
    min_similarity: float = MIN_SIMILARITY,
) -> int:
    """How many journal transcripts a correction's gist reaches (Jaccard >= bar).

    This is the single definition of "N similar" the whole phase reuses — the
    digest, the inline trust chips, and the post-correction toast all count
    reach through this one function, so no surface can drift to a second number.
    """
    if not gist:
        return 0
    return sum(1 for t in transcripts if t and similarity(t, gist) >= min_similarity)


def reach_by_gist_map(
    corrections: Optional[Sequence[Any]],
    transcripts: Sequence[str],
    *,
    min_similarity: float = MIN_SIMILARITY,
) -> dict[str, int]:
    """Precompute reach per correction gist, so per-entry lookups stay cheap.

    Accepts `Correction` objects (`.key`) or display dicts (`key`/`gist`).
    """
    out: dict[str, int] = {}
    for c in corrections or []:
        gist = getattr(c, "key", None)
        if gist is None and isinstance(c, dict):
            gist = c.get("key") or c.get("gist")
        gist = str(gist or "")
        if gist and gist not in out:
            out[gist] = reach_for_gist(gist, transcripts, min_similarity=min_similarity)
    return out


def best_correction_signal(
    text: str,
    corrections: Optional[Sequence[Any]],
    reach_by_gist: dict[str, int],
    *,
    min_similarity: float = MIN_SIMILARITY,
) -> Optional[dict[str, Any]]:
    """The inline "learned from N similar" signal for one utterance, or None.

    Finds the correction the live router would apply to `text` (reusing
    `best_match_in`, the router's own matcher, across both kinds) and reports
    that correction's reach. Returns None when nothing matches — surfaces stay
    quiet rather than claim learning that did not happen. Pass `corrections=None`
    (the disabled / no-snapshot posture) to get None, byte-identical to routing.
    """
    if not text or not corrections:
        return None
    best = None
    best_sim = -1.0
    for kind in CORRECTION_KINDS:
        match = best_match_in(corrections, kind, text, min_similarity=min_similarity)
        if match is None:
            continue
        sim = similarity(text, match.key)
        if sim > best_sim:
            best, best_sim = match, sim
    if best is None:
        return None
    return {
        "matched": True,
        "kind": best.kind,
        "value": best.value,
        "gist": best.key,
        "similar": reach_by_gist.get(best.key, reach_for_gist(best.key, [], min_similarity=min_similarity)),
    }


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
    # nudge (Jaccard >= threshold), over the whole journal. Reuses the shared
    # reach function so the digest and the inline chips count identically.
    correction_rows: list[dict[str, Any]] = []
    for c in windowed_corr:
        correction_rows.append(
            {
                "id": c["id"],
                "kind": c["kind"],
                "gist": c["gist"],
                "value": c["value"],
                "created_at": c["created_at"],
                "similar": reach_for_gist(c["gist"], all_transcripts, min_similarity=min_similarity),
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
