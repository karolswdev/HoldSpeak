#!/usr/bin/env python3
"""Generate docs/generated/operations.json from the operation catalogue (PHILO-5-01).

The one source of truth is ``holdspeak.operations.DESCRIPTORS``: each
operation's name, version, argument schema, principal, effect, result,
refusals, completion and transport exposure. The drift guard
(tests/unit/test_philo5_one_decision.py) fails when the committed file differs.

    uv run python scripts/gen_operations_json.py          # write
    uv run python scripts/gen_operations_json.py --check  # exit 1 on drift
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "generated" / "operations.json"


def render() -> str:
    from holdspeak.operations import DESCRIPTORS

    payload = {
        "source": "holdspeak/operations.py",
        "regenerate": "uv run python scripts/gen_operations_json.py",
        "operations": [descriptor.export() for descriptor in DESCRIPTORS],
    }
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def main(argv: list[str]) -> int:
    text = render()
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"DRIFT {OUT.relative_to(REPO)}: regenerate with scripts/gen_operations_json.py")
            return 1
        print(f"OK {OUT.relative_to(REPO)}")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"WROTE {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
