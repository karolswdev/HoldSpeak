"""Run a Phase 5 breakage case in a process-local evening zone.

The Monday Brief producer must see the failed read after its 17:00 close.  The
wrapper selects a fixed-offset IANA zone whose local hour is 20, sets it only
in this process and its child hub, and refuses to run outside the proof window.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time


BASE_CASE = "case.closure.chain.s5_next_day_brief_with_breakage"
VALID_CASES = frozenset({BASE_CASE, f"{BASE_CASE}.op"})


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=sorted(VALID_CASES))
    parser.add_argument("--viewport", required=True, choices=("1440", "393"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--out", required=True, help="Phase 5 output directory")
    parser.add_argument("--no-build", action="store_true")
    return parser


def _evening_zone() -> str:
    offset = (20 - datetime.now(timezone.utc).hour + 12) % 24 - 12
    return f"Etc/GMT{-offset:+d}" if offset else "Etc/GMT"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    zone = _evening_zone()
    os.environ["TZ"] = zone
    time.tzset()
    local = datetime.now()
    if not 17 <= local.hour < 23:
        print(
            f"BREAKAGE_BLOCKED TZ={zone} local={local.isoformat()} "
            "outside producer evening window [17,23)",
            flush=True,
        )
        return 2
    print(
        f"BREAKAGE_WINDOW TZ={zone} local={local.isoformat()} after_close=True",
        flush=True,
    )

    repo = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "scripts/graph_walk.py",
        "run",
        "--atlas",
        "docs/internal/philo/graph/atlas-phase3.json",
        "--case",
        args.case,
        "--brain",
        "astra",
        "--viewport",
        args.viewport,
        "--engine",
        "real",
        "--out",
        args.out,
    ]
    if args.headless:
        command.append("--headless")
    if args.no_build:
        command.append("--no-build")
    return subprocess.call(command, cwd=repo)


if __name__ == "__main__":
    raise SystemExit(main())
