"""The feature ledger: integrity, phase exhaustiveness, and coverage math."""

from __future__ import annotations

import pytest

from uat.conductor.contract.ledger import (
    NO_UAT_MARKER,
    CoverageResult,
    Feature,
    FeatureLedger,
)


def test_shipped_ledger_loads_and_validates():
    ledger = FeatureLedger.load()
    assert len(ledger.features) > 200
    errors = ledger.validate()
    assert errors == [], errors


def test_phase_map_is_exhaustive():
    ledger = FeatureLedger.load()
    # Every phase resolves to keys or the explicit marker — none silently absent.
    for phase, keys in ledger.phase_map.items():
        assert keys, f"phase {phase} maps to nothing"
        for k in keys:
            assert k == NO_UAT_MARKER or ledger.has(k), f"phase {phase} → unknown key {k}"


def _tiny_ledger() -> FeatureLedger:
    feats = [
        Feature("a", surfaces={"web": "yes", "ipad": "yes", "iphone": "unknown"}),
        Feature("b", surfaces={"web": "yes", "ipad": "no", "iphone": "no"}),
        Feature("c", surfaces={"web": "yes", "ipad": "yes", "iphone": "yes"}),
        Feature("d", surfaces={"web": "yes", "ipad": "yes", "iphone": "yes"}, status="retired"),
    ]
    return FeatureLedger(feats, {"0": ["a"], "1": [NO_UAT_MARKER]})


def test_coverage_excludes_retired_and_non_applicable():
    ledger = _tiny_ledger()
    # Cite a and c. Retired d never counts.
    cited = {"a", "c", "d"}
    overall = ledger.coverage_overall(cited)
    assert overall.total == 3  # a, b, c (d retired)
    assert overall.covered == 2  # a, c

    web = ledger.coverage(cited, "web")
    assert web.total == 3 and web.covered == 2

    ipad = ledger.coverage(cited, "ipad")
    # applicable on ipad: a, c (b is 'no', d retired). Both cited.
    assert ipad.total == 2 and ipad.covered == 2

    iphone = ledger.coverage(cited, "iphone")
    # applicable on iphone (yes): only c. a is 'unknown' → excluded.
    assert iphone.total == 1 and iphone.covered == 1


def test_coverage_pct():
    r = CoverageResult(covered=1, total=4, uncovered=["x"])
    assert r.pct == 25.0
    assert CoverageResult(0, 0, []).pct == 0.0


def test_validate_catches_bad_surface_and_dupes():
    feats = [
        Feature("a", surfaces={"web": "maybe", "ipad": "yes", "iphone": "no"}),
        Feature("a", surfaces={"web": "yes", "ipad": "yes", "iphone": "no"}),
    ]
    ledger = FeatureLedger(feats, {"0": ["a"]})
    errors = ledger.validate()
    assert any("duplicate ledger key" in e for e in errors)
    assert any("surface web" in e for e in errors)
