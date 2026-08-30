#!/usr/bin/env python3
"""Diff a vitest run's failures against the web-inherited baseline.

Usage:
  # Execute vitest and check in one shot:
  python scripts/check_web_baseline.py --run

  # Consume an existing vitest JSON results file:
  python scripts/check_web_baseline.py results.json

Speaks the sweep vocabulary:
  BASELINE-MATCHED  — a failure that appears in the baseline (inherited)
  BRANCH-NEW        — a failure NOT in the baseline (regression)
  HEALED            — a baseline entry that now passes (good news)
  Verdict           — "baseline-subset, zero branch-new" or
                      "BRANCH-NEW FAILURES: N"

Exit 0 only when zero branch-new failures.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINE = REPO / "tests" / "web-inherited-baseline.txt"
WEB_DIR = REPO / "web"


def load_baseline(path: Path) -> set[str]:
    """Read baseline file: non-empty, non-comment lines."""
    entries: set[str] = set()
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            entries.add(stripped)
    return entries


def run_vitest() -> dict:
    """Execute vitest and return the JSON result dict."""
    proc = subprocess.run(
        ["npx", "vitest", "run", "--reporter=json"],
        capture_output=True,
        text=True,
        cwd=WEB_DIR,
    )
    # vitest prints JSON on the last non-empty stdout line
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    print("ERROR: could not parse vitest JSON output", file=sys.stderr)
    sys.exit(2)


def extract_failures(data: dict) -> set[str]:
    """Extract failed test identifiers from vitest JSON."""
    failures: set[str] = set()
    web_prefix = str(WEB_DIR) + "/"
    for suite in data.get("testResults", []):
        suite_file = suite.get("name", "")
        if suite_file.startswith(web_prefix):
            rel = suite_file[len(web_prefix):]
        else:
            rel = suite_file
        for test in suite.get("assertionResults", []):
            # Only count actual failures — skip passed/pending/todo
            if test.get("status") != "failed":
                continue
            parts = [rel] + test.get("ancestorTitles", []) + [test["title"]]
            test_id = " > ".join(parts)
            failures.add(test_id)
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diff vitest failures against the web-inherited baseline."
    )
    parser.add_argument(
        "results_json",
        nargs="?",
        help="Path to an existing vitest JSON results file.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute vitest and use its output (mutually exclusive with results_json).",
    )
    parser.add_argument(
        "--baseline",
        default=str(BASELINE),
        help=f"Baseline file (default: {BASELINE}).",
    )
    args = parser.parse_args()

    if not args.run and not args.results_json:
        parser.error("Provide either --run or a results JSON path.")
    if args.run and args.results_json:
        parser.error("--run and a results JSON path are mutually exclusive.")

    baseline = load_baseline(Path(args.baseline))
    if not baseline:
        print("ERROR: baseline file is empty or missing.", file=sys.stderr)
        sys.exit(2)

    if args.run:
        print("Running vitest...", flush=True)
        data = run_vitest()
    else:
        with open(args.results_json) as f:
            data = json.load(f)

    failures = extract_failures(data)

    matched = failures & baseline
    branch_new = failures - baseline
    healed = baseline - failures

    print()
    print("=== Web baseline report ===")
    print()

    if matched:
        print(f"BASELINE-MATCHED ({len(matched)}):")
        for t in sorted(matched):
            print(f"  {t}")
        print()

    if healed:
        print(f"HEALED ({len(healed)}):")
        for t in sorted(healed):
            print(f"  {t}")
        print()

    if branch_new:
        print(f"BRANCH-NEW ({len(branch_new)}):")
        for t in sorted(branch_new):
            print(f"  BRANCH-NEW: {t}")
        print()

    total_pass = data.get("numPassedTests", 0)
    total_fail = data.get("numFailedTests", 0)
    total_skip = data.get("numPendingTests", 0) + data.get("numTodoTests", 0)
    print(f"Suite totals: {total_pass} passed, {total_fail} failed, {total_skip} skipped")
    print()

    if branch_new:
        print(f"VERDICT: BRANCH-NEW FAILURES: {len(branch_new)}")
        sys.exit(1)
    elif not healed:
        print("VERDICT: baseline-subset/exact, zero branch-new")
    else:
        print("VERDICT: baseline-subset, zero branch-new")
    sys.exit(0)


if __name__ == "__main__":
    main()
