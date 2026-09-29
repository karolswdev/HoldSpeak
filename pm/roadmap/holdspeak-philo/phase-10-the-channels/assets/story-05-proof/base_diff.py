#!/usr/bin/env python3
"""PHILO-10-05: the earlier atlas files BEFORE (main dce3afa9, an export with its
own rig) and AFTER (this branch: main + the rig's recording runner, `hub_home`,
`cli_calls`, `protocol_reads` count, `scroll_into_view`), per case and width.
Reads two retained runs.tsv files; prints the verdict matrix and every row whose
verdict differs. Exit 1 when a case passes before and not after.
Usage: base_diff.py <before label> <after label>"""
import sys
from collections import Counter
from pathlib import Path

SHOTS = Path(__file__).resolve().parent.parent / "story-05-shots"


def load(label):
    rows = [line.split("\t") for line in (SHOTS / label / "runs.tsv").read_text().splitlines()[1:]]
    return {(r[0], r[1], r[2]): r for r in rows}


before, after = load(sys.argv[1]), load(sys.argv[2])
assert before.keys() == after.keys(), "the two runs planned different cases"
for (b, a), n in sorted(Counter((before[k][3], after[k][3]) for k in before).items()):
    print(f"{n:4d}  before {b:15s} after {a}")
regressed = 0
for key in sorted(before):
    b, a = before[key][3], after[key][3]
    if b != a:
        regressed += b == "pass"
        print(f"DIFF {key[0]} {key[1]} {key[2]}: {b} -> {a}\n     before: {before[key][6][:200]}\n     after:  {after[key][6][:200]}")
print(f"{len(before)} runs; {regressed} pass before and not after")
sys.exit(1 if regressed else 0)
