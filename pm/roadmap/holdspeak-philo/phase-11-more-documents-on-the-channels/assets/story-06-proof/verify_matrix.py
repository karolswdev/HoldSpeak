#!/usr/bin/env python3
"""Check a retained PHILO-11-06 serial matrix against its actual atlas cases."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
HEADER = [
    "file", "case", "width", "verdict", "seconds", "load1", "reading",
    "run_dir", "exit_code", "source_revision", "source_dirty",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("label", help="directory name below .tmp/philo11-06")
    parser.add_argument("--verdict", choices=("pass", "fail"), required=True)
    parser.add_argument("--faces-only", action="store_true")
    parser.add_argument("atlases", nargs="+")
    args = parser.parse_args()
    expected: set[tuple[str, str, str]] = set()
    for relative in args.atlases:
        atlas_path = ROOT / relative
        atlas = json.loads(atlas_path.read_text())
        for case in atlas.get("cases", []):
            widths = case.get("viewports") or []
            if args.faces_only and not widths:
                continue
            labels = [str(width) for width in widths] or ["op"]
            expected.update((atlas_path.name, case["id"], width) for width in labels)

    run_root = ROOT / ".tmp/philo11-06" / args.label
    with (run_root / "runs.tsv").open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != HEADER:
            raise SystemExit(f"bad matrix header: {reader.fieldnames!r}")
        rows = list(reader)
    actual = [(row["file"], row["case"], row["width"]) for row in rows]
    if len(actual) != len(set(actual)):
        raise SystemExit("duplicate case × width row in runs.tsv")
    if set(actual) != expected:
        missing, extra = expected - set(actual), set(actual) - expected
        raise SystemExit(f"matrix shape mismatch: missing={sorted(missing)} extra={sorted(extra)}")
    wrong = [row for row in rows if row["verdict"] != args.verdict]
    if wrong:
        detail = "\n".join(
            f"{row['case']} {row['width']}: {row['verdict']} — {row['reading']}"
            for row in wrong
        )
        raise SystemExit(f"{len(wrong)} rows did not have verdict {args.verdict}:\n{detail}")
    counts = Counter(row["verdict"] for row in rows)
    print(f"verified {len(rows)} exact case × width runs: {dict(counts)}")
    print(f"all {len(rows)} verdicts are {args.verdict}; run details are in {run_root}/runs.tsv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
