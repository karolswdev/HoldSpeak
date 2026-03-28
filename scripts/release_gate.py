#!/usr/bin/env python3
"""Strict release checklist gate.

Fails with non-zero exit when required checklist items are not marked done.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CHECKBOX_RE = re.compile(r"^\s*-\s*\[(?P<state>[ xX])\]\s+(?P<text>.+?)\s*$")


def _parse_checklist(path: Path) -> tuple[list[str], list[str]]:
    checked: list[str] = []
    unchecked: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX_RE.match(raw_line)
        if not match:
            continue
        text = match.group("text").strip()
        state = match.group("state")
        if state.lower() == "x":
            checked.append(text)
        else:
            unchecked.append(text)

    return checked, unchecked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail release gate if checklist has required items still unchecked.",
    )
    parser.add_argument(
        "--checklist",
        type=Path,
        default=Path("docs/RELEASE_HARDENING_CHECKLIST.md"),
        help="Path to checklist markdown file (default: docs/RELEASE_HARDENING_CHECKLIST.md)",
    )
    args = parser.parse_args(argv)

    checklist_path: Path = args.checklist
    if not checklist_path.exists():
        print(f"ERROR: checklist file not found: {checklist_path}", file=sys.stderr)
        return 2

    checked, unchecked = _parse_checklist(checklist_path)
    total = len(checked) + len(unchecked)

    if total == 0:
        print(f"ERROR: no checklist items found in {checklist_path}", file=sys.stderr)
        return 2

    if unchecked:
        print(f"RELEASE GATE FAILED: {len(unchecked)} required checklist item(s) remain unchecked.")
        for item in unchecked:
            print(f"  - {item}")
        print(f"Checked: {len(checked)}/{total}")
        return 1

    print(f"RELEASE GATE PASSED: {len(checked)}/{total} checklist item(s) complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
