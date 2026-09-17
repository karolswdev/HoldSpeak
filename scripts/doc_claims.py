#!/usr/bin/env python3
"""HS-200-46 — print the documentation-claim registry as one markdown table.

Handover §7b used to carry this table by hand.  The list now lives in
``tests/unit/doc_claims/registry.py``, where every row has an executable
predicate, and this script renders it so the table can be pasted anywhere
without a second copy existing.

    uv run python scripts/doc_claims.py            # the table
    uv run python scripts/doc_claims.py --measure  # + run every predicate

``--measure`` re-runs the predicates and marks any row whose state no longer
matches the code; that is the same condition
``tests/unit/test_phase200_doc_claims.py`` fails on.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.unit.doc_claims.registry import (  # noqa: E402
    CLAIMS,
    KNOWN_FALSE_RATCHET,
    KNOWN_FALSE_RATCHET_DATE,
    KNOWN_FALSE_RATCHET_REASON,
    known_false_claims,
    markdown_table,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--measure",
        action="store_true",
        help="run every predicate and report rows whose state no longer matches",
    )
    args = parser.parse_args()

    print(markdown_table())
    print()
    print(
        f"{len(CLAIMS)} claims — {len(known_false_claims())} known_false against a "
        f"ratchet of {KNOWN_FALSE_RATCHET} set {KNOWN_FALSE_RATCHET_DATE}."
    )
    print(f"Ratchet reason: {KNOWN_FALSE_RATCHET_REASON}")

    if not args.measure:
        return 0

    print()
    drifted = 0
    for claim in CLAIMS:
        satisfied = bool(claim.predicate())
        expected = claim.state == "holds"
        status = "OK" if satisfied == expected else "DRIFTED"
        if status == "DRIFTED":
            drifted += 1
        line = claim.anchor_line()
        print(f"{status:8} {claim.state:12} {claim.doc}:{line}")
    print()
    print(f"{drifted} drifted row(s).")
    return 1 if drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
