"""Reciprocal rank fusion (MEMORY-DESIGN.md §3.2 step 3).

``score = Σ 1 / (k + rank)`` over the lists that ran, k = 60.
"""
from __future__ import annotations

from typing import Hashable, Mapping, Sequence

RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: Mapping[str, Sequence[Hashable]],
    *,
    k: int = RRF_K,
) -> list[tuple[Hashable, float, tuple[str, ...]]]:
    """Fuse named ranked lists of keys.

    Returns ``(key, score, found_by)`` best first.  A key that is in one list
    twice counts once, at its best rank.  Ties keep the order of first sight
    (the order of ``ranked_lists``, then the rank), so the result is
    deterministic.
    """
    scores: dict[Hashable, float] = {}
    found: dict[Hashable, list[str]] = {}
    first_seen: dict[Hashable, int] = {}
    counter = 0
    for name, keys in ranked_lists.items():
        seen: set[Hashable] = set()
        rank = 0
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            rank += 1
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            found.setdefault(key, []).append(name)
            if key not in first_seen:
                first_seen[key] = counter
                counter += 1
    ordered = sorted(scores, key=lambda key: (-scores[key], first_seen[key]))
    return [(key, scores[key], tuple(found[key])) for key in ordered]


__all__ = ["RRF_K", "reciprocal_rank_fusion"]
