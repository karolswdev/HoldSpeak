#!/usr/bin/env python3
"""Print a fail-closed UAT closeout report; exit non-zero while blocked."""

from __future__ import annotations

import argparse
import json

from uat.conductor.closeouts import CloseoutEvaluator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("closeout_id", nargs="?", default="phase-92")
    parser.add_argument(
        "--json", action="store_true", help="print the complete machine report"
    )
    args = parser.parse_args()
    report = CloseoutEvaluator().evaluate(args.closeout_id)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['title']}: {report['status']}")
        print(
            f"repository: {report['repository']['commit'] or '(unknown)'} "
            f"({'clean' if report['repository']['clean'] else 'not clean'})"
        )
        for gap in report["gaps"]:
            context = " · ".join(
                f"{key}={value}"
                for key, value in gap.items()
                if key not in {"code", "message"} and value not in (None, [], "")
            )
            print(
                f"- [{gap['code']}] {gap['message']}"
                + (f" · {context}" if context else "")
            )
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
