#!/usr/bin/env python3
"""Inventory and check Phase-93 primary-client operational copy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from holdspeak.product_copy import census  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify primary-client copy and fail on contract violations."
    )
    parser.add_argument("--check", action="store_true", help="Exit non-zero on drift")
    parser.add_argument("--output", type=Path, help="Write the full JSON inventory")
    parser.add_argument(
        "--summary", action="store_true", help="Print counts instead of full inventory"
    )
    args = parser.parse_args()

    report = census(ROOT)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    if args.summary:
        print(
            json.dumps(
                {
                    "registry_version": report["registry_version"],
                    "copy_contract_version": report["copy_contract_version"],
                    "candidate_count": report["candidate_count"],
                    "violation_count": report["violation_count"],
                    "counts_by_client": report["counts_by_client"],
                    "counts_by_classification": report[
                        "counts_by_classification"
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
    elif not args.output:
        print(payload, end="")
    if args.check and report["violation_count"]:
        for violation in report["violations"]:
            print(
                f"{violation['path']}:{violation['line']}: "
                f"{violation['rule_id']}: {violation['text']}",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
