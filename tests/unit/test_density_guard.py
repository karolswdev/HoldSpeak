"""HS-63-05, reduced 2026-11-09 (fences diet): one frontend tree.

The per-file line budgets are parked in ``tests/_parked/fences/test_density_guard.py``
(shape, not behaviour). What stays: the web has one implementation, the React
tree under ``web/src``; no Astro pages and no second script tree come back.
"""

from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "web/src"


def test_hard_cut_has_no_parallel_frontend_tree() -> None:
    assert not list(SRC.rglob("*.astro"))
    assert not (SRC / "scripts").exists() or not list((SRC / "scripts").rglob("*.*"))
