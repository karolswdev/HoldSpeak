#!/usr/bin/env python3
"""HS-202-04 — proof that `check-after-map.py` rejects a wrong reference.

Astra's round-two condition 3. The first checker only asked whether
`site_after`'s line number was IN RANGE, so an anchor could point anywhere
in the file and still pass — which is exactly how row 01 came to point at a
comment about the deferred queue while claiming to anchor the Summary
section label.

This harness breaks ONE anchor on purpose, requires the checker to fail and
to NAME what it found instead, then restores the file and requires green.
The restore is verified by SHA-256; the row it breaks is the very row Astra
caught, set back to the stale number it carried.

Run:
    python3 pm/roadmap/holdspeak/phase-202-the-coherent-face/\\
assets/story-04-shots/prove-anchor-check.py
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
CSV = REPO / "docs/internal/surface-inventory-2026-09-20/02-verbs-after-2026-09-21.csv"
CHECKER = HERE / "check-after-map.py"

ROW = "01"
GOOD = "web/src/pages/cores/LiveCore.tsx:401"
# The stale anchor the first round shipped: in range, wrong line.
STALE = "web/src/pages/cores/LiveCore.tsx:375"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checker() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(CHECKER)], cwd=str(REPO),
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def row_line(text: str, anchored: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith(f"{ROW} ") or anchored in line:
            return line.strip()
    return ""


def main() -> int:
    original = CSV.read_text()
    baseline = sha(CSV)
    failures: list[str] = []

    if GOOD not in original:
        print(f"REFUSED: row {ROW} no longer anchors at {GOOD}", file=sys.stderr)
        return 2

    # What the stale anchor actually points at, so the proof is readable.
    src = (REPO / "web/src/pages/cores/LiveCore.tsx").read_text().splitlines()
    print(f"  the stale anchor {STALE} points at:")
    print(f"      {src[374].strip()[:110]}")
    print(f"  the true anchor  {GOOD} points at:")
    print(f"      {src[400].strip()[:110]}\n")

    try:
        CSV.write_text(original.replace(GOOD, STALE, 1))
        code, out = run_checker()
        print("  -- with the stale anchor back --")
        for line in out.splitlines():
            if ROW in line[:6] or "!!" in line or "wanted:" in line \
                    or "found:" in line or line.startswith("VERDICT"):
                print(f"  {line}")
        if code == 0:
            failures.append("the checker PASSED an anchor that points elsewhere")
        if "does NOT carry its string" not in out:
            failures.append("the checker did not name the mismatch")
    finally:
        CSV.write_text(original)
        if sha(CSV) != baseline:
            failures.append("the after-map did NOT restore")

    print(f"\n  -- restored: {CSV.relative_to(REPO)} {sha(CSV)[:12]} "
          f"({'identical' if sha(CSV) == baseline else 'CHANGED'}) --")
    code, out = run_checker()
    print("  -- with the true anchor --")
    print(f"  {out.strip().splitlines()[-1]}")
    if code != 0:
        failures.append("the checker is red on the corrected after-map")

    for line in failures:
        print(f"  FAIL {line}")
    print("VERDICT", "PASS — a wrong reference is rejected, a right one passes"
          if not failures else "FAIL")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
