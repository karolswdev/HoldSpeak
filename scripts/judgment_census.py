"""HS-100-02 — the judgment census.

UIUX_JUDGMENT.md claims to judge every surface and desk component.
This script makes that claim mechanical: it derives the ground truth
from the code (the SURFACES registry rows + aliases in
SurfaceWindows.tsx, and every non-test component under
web/src/desk/components/) and fails loudly on any omission.

Usage: uv run python scripts/judgment_census.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "web/src/desk/components/SurfaceWindows.tsx"
COMPONENTS = ROOT / "web/src/desk/components"
JUDGMENT = ROOT / "docs/internal/UIUX_JUDGMENT.md"


def surface_keys() -> list[str]:
    src = REGISTRY.read_text()
    keys = re.findall(r'^\s*key: "([^"]+)"', src, re.M)
    aliases = re.findall(r'^\s*"([a-z-]+)": \{ target:', src, re.M)
    return keys + aliases


def component_names() -> list[str]:
    return sorted(
        p.stem
        for p in COMPONENTS.glob("*.tsx")
        if not p.stem.endswith(".test") and not p.name.endswith(".test.tsx")
    )


def main() -> int:
    doc = JUDGMENT.read_text()
    missing: list[str] = []
    keys = surface_keys()
    comps = component_names()
    for key in keys:
        if f"`{key}`" not in doc:
            missing.append(f"surface key `{key}`")
    for comp in comps:
        if not re.search(rf"\b{re.escape(comp)}\b", doc):
            missing.append(f"component {comp}")
    print(f"census: {len(keys)} surface keys (incl. aliases), "
          f"{len(comps)} components")
    if missing:
        for m in missing:
            print(f"MISSING from UIUX_JUDGMENT.md: {m}")
        return 1
    print("census: every surface and component is judged — zero omissions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
