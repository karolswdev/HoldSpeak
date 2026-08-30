#!/usr/bin/env python3
"""Compare vitest desk-test failures against the inherited baseline.

Exit 0  — no new reds (known failures may still exist).
Exit 1  — at least one NEW red found (regression).

Usage:
    uv run python scripts/web_baseline_check.py
    uv run python scripts/web_baseline_check.py --baseline tests/fixtures/web-inherited-baseline.txt
    uv run python scripts/web_baseline_check.py --json /path/to/existing-vitest-output.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DEFAULT_BASELINE = ROOT / "tests" / "fixtures" / "web-inherited-baseline.txt"


def load_baseline(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        names.add(stripped)
    return names


def run_vitest(json_out: Path) -> None:
    cmd = [
        "npm",
        "--prefix",
        str(WEB),
        "run",
        "test:desk",
        "--",
        "--reporter=json",
        f"--outputFile={json_out}",
    ]
    # vitest exits non-zero when tests fail; that is expected.
    subprocess.run(cmd, capture_output=True)


def extract_failures(json_path: Path) -> set[str]:
    data = json.loads(json_path.read_text())
    failures: set[str] = set()
    for suite in data.get("testResults", []):
        suite_file = suite.get("name", "")
        # Make the path relative to the web/ directory.
        try:
            rel = str(Path(suite_file).relative_to(WEB))
        except ValueError:
            rel = suite_file
        for t in suite.get("assertionResults", []):
            if t.get("status") != "failed":
                continue
            ancestors = t.get("ancestorTitles", [])
            title = t.get("title", "")
            full = " > ".join([rel] + ancestors + [title])
            failures.add(full)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Path to baseline file (default: tests/fixtures/web-inherited-baseline.txt)",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        dest="json_file",
        help="Use an existing vitest JSON report instead of running vitest",
    )
    args = parser.parse_args()

    baseline = load_baseline(args.baseline)

    if args.json_file:
        json_path = args.json_file
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        json_path = Path(tmp.name)
        print(f"Running vitest (output -> {json_path}) ...")
        run_vitest(json_path)

    if not json_path.exists() or json_path.stat().st_size == 0:
        print("ERROR: vitest JSON report is missing or empty", file=sys.stderr)
        return 1

    failures = extract_failures(json_path)

    new_reds = failures - baseline
    fixed = baseline - failures

    rc = 0

    if new_reds:
        for name in sorted(new_reds):
            print(f"NEW RED: {name}")
        rc = 1

    if fixed:
        for name in sorted(fixed):
            print(f"FIXED (remove from baseline): {name}")

    matched = failures & baseline
    print(f"\n--- baseline check ---")
    print(f"Baseline entries:   {len(baseline)}")
    print(f"Actual failures:    {len(failures)}")
    print(f"Matched (known):    {len(matched)}")
    print(f"New reds:           {len(new_reds)}")
    print(f"Fixed:              {len(fixed)}")

    if rc == 0:
        print("\nOK — no new regressions.")
    else:
        print("\nFAIL — new regressions found.", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
