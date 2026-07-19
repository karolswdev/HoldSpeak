"""HS-100-03 — the mockup census.

The thesis's acceptance bar: no unmocked application ships in the
plan. This derives the application roster from the thesis document's
§1 headings and requires a screenshot at BOTH form factors (1440 and
393) for each, plus the arrival screen.

Usage: uv run python scripts/mockup_census.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THESIS = ROOT / "docs/internal/APPLICATION_LAYER_THESIS.md"
MOCKS = (
    ROOT
    / "pm/roadmap/holdspeak/phase-100-the-application-layer/assets/hs-100-03-mockups"
)

# §1 headings name the applications; the desk's core screen is arrival.
SCREEN_FOR = {
    "Speak": "speak",
    "Meetings": "meetings",
    "Agents": "agents",
    "Settings": "settings",
    "The desk itself": "arrival",
}


def main() -> int:
    text = THESIS.read_text()
    heads = re.findall(r"^### 1\.\d+ ([^(\n]+)", text, re.M)
    missing: list[str] = []
    for head in heads:
        name = head.strip().rstrip(" —-")
        screen = SCREEN_FOR.get(name)
        if screen is None:
            missing.append(f"no screen mapping for thesis application {name!r}")
            continue
        for tag in ("1440", "393"):
            if not (MOCKS / f"{screen}-{tag}.png").exists():
                missing.append(f"{screen}-{tag}.png missing for {name}")
    print(f"mockup census: {len(heads)} thesis applications")
    if missing:
        for m in missing:
            print(f"MISSING: {m}")
        return 1
    print("mockup census: every application mocked at 1440 and 393")
    return 0


if __name__ == "__main__":
    sys.exit(main())
