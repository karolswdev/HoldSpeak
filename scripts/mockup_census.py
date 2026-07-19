"""The mockup census (HS-100-03, grown by HS-101-01).

The standing bar: no unmocked thing ships in a plan. Two rosters,
each derived from its canon document, each requiring a screenshot at
BOTH form factors (1440 and 393):

- HS-100: the application roster from the thesis document's §1
  headings (plus the arrival screen).
- HS-101: the interior roster from DESIGN_SYSTEM.md's
  "The mockup roster (HS-101-01)" list.

Usage: uv run python scripts/mockup_census.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THESIS = ROOT / "docs/internal/APPLICATION_LAYER_THESIS.md"
DESIGN = ROOT / "docs/internal/DESIGN_SYSTEM.md"
MOCKS_100 = (
    ROOT
    / "pm/roadmap/holdspeak/phase-100-the-application-layer/assets/hs-100-03-mockups"
)
MOCKS_101 = (
    ROOT
    / "pm/roadmap/holdspeak/phase-101-the-native-innards/assets/hs-101-01-mockups"
)

# §1 headings name the applications; the desk's core screen is arrival.
SCREEN_FOR = {
    "Speak": "speak",
    "Meetings": "meetings",
    "Agents": "agents",
    "Settings": "settings",
    "The desk itself": "arrival",
}


def require_shots(mocks: Path, screen: str, owner: str, missing: list[str]) -> None:
    for tag in ("1440", "393"):
        if not (mocks / f"{screen}-{tag}.png").exists():
            missing.append(f"{screen}-{tag}.png missing for {owner}")


def census_100(missing: list[str]) -> int:
    text = THESIS.read_text()
    heads = re.findall(r"^### 1\.\d+ ([^(\n]+)", text, re.M)
    for head in heads:
        name = head.strip().rstrip(" —-")
        screen = SCREEN_FOR.get(name)
        if screen is None:
            missing.append(f"no screen mapping for thesis application {name!r}")
            continue
        require_shots(MOCKS_100, screen, name, missing)
    return len(heads)


def census_101(missing: list[str]) -> int:
    text = DESIGN.read_text()
    section = re.search(
        r"^### The mockup roster \(HS-101-01\)\n(.*?)(?=^#|\Z)",
        text,
        re.M | re.S,
    )
    if section is None:
        missing.append("DESIGN_SYSTEM.md has no 'The mockup roster (HS-101-01)' section")
        return 0
    screens = re.findall(r"^- `([a-z-]+)` — (.+)$", section.group(1), re.M)
    if not screens:
        missing.append("the HS-101-01 mockup roster names no screens")
    for screen, what in screens:
        require_shots(MOCKS_101, screen, what.strip(), missing)
    return len(screens)


def main() -> int:
    missing: list[str] = []
    n100 = census_100(missing)
    n101 = census_101(missing)
    print(f"mockup census: {n100} thesis applications, {n101} interior-canon screens")
    if missing:
        for m in missing:
            print(f"MISSING: {m}")
        return 1
    print("mockup census: every canon screen mocked at 1440 and 393")
    return 0


if __name__ == "__main__":
    sys.exit(main())
