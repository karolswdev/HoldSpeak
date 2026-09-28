#!/usr/bin/env python3
"""PHILO-9-05: the base atlas (atlas.json, atlas-phase3.json) on the pre-Phase-9
product (294632c0, an export) and on merged main (79fdee3c), per case and width.
Reads the two retained runs.tsv files; prints the verdict matrix and every row
whose verdict differs. Exit 1 when a case passes before and not after."""
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHOTS = HERE.parent / "story-05-shots"


def load(label):
    rows = [line.split("\t") for line in (SHOTS / label / "runs.tsv").read_text().splitlines()[1:]]
    return {(r[0], r[1], r[2]): r for r in rows}


before, after = load("base-294632c0"), load("base-merged")
assert before.keys() == after.keys(), "the two runs planned different cases"
pairs = Counter((before[k][3], after[k][3]) for k in before)
for (b, a), n in sorted(pairs.items()):
    print(f"{n:4d}  before {b:15s} after {a}")
regressed = 0
for key in sorted(before):
    b, a = before[key][3], after[key][3]
    if b != a:
        regressed += b == "pass"
        print(f"DIFF {key[0]} {key[1]} {key[2]}: {b} -> {a}\n     before: {before[key][6][:200]}\n     after:  {after[key][6][:200]}")
print(f"{len(before)} runs; {regressed} pass before and not after")
sys.exit(1 if regressed else 0)
