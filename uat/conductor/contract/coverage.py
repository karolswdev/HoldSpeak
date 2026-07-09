"""Coverage math over a pack — per surface and overall.

Given a pack (a set of scenarios) and the ledger, compute what fraction of the
live shipped surface the pack touches. A feature counts toward a surface's
coverage only if the pack cites it AND a scenario citing it is applicable on
that surface — a pack that never walks the iPhone leg does not get to claim
iPhone coverage.
"""

from __future__ import annotations

from typing import Any

from .ledger import SURFACES, FeatureLedger
from .scenarios import Scenario


def cited_keys(scenarios: list[Scenario]) -> set[str]:
    keys: set[str] = set()
    for s in scenarios:
        keys.update(s.features)
    return keys


def cited_keys_on_surface(scenarios: list[Scenario], surface: str) -> set[str]:
    keys: set[str] = set()
    for s in scenarios:
        if s.surfaces.get(surface, {}).get("applicable"):
            keys.update(s.features)
    return keys


def pack_coverage(scenarios: list[Scenario], ledger: FeatureLedger) -> dict[str, Any]:
    report: dict[str, Any] = {
        "scenario_count": len(scenarios),
        "cited_features": sorted(cited_keys(scenarios)),
        "overall": ledger.coverage_overall(cited_keys(scenarios)).to_dict(),
    }
    for s in SURFACES:
        report[s] = ledger.coverage(cited_keys_on_surface(scenarios, s), s).to_dict()
    report["unknown_cells"] = {
        s: sum(1 for f in ledger.live() if f.surfaces.get(s) == "unknown") for s in SURFACES
    }
    report["expected_verdicts"] = sum(sc.expected_verdict_count() for sc in scenarios)
    return report
