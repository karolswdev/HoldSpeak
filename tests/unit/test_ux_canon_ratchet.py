"""UX canon ratchet guard — counts can only go down.

Uses the in-process scanner (scripts/ux_canon_scan.py) against the live
web/src tree and compares to the committed ceiling file
(tests/ux_canon_ceiling.json).  Three tests:

1. ratchet  — per-rule counts must not exceed the ceiling.
2. hard_zeros — DS6, A9 must stay at 0; A1 must stay within a named
   allowlist.
3. healing — passes with a notice when a count drops below the ceiling
   (informational; reminds to lower the ceiling).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CEILING_PATH = REPO_ROOT / "tests" / "ux_canon_ceiling.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "ux_canon_scan.py"


def _load_scanner():
    """Import the scanner module from its script path."""
    spec = importlib.util.spec_from_file_location("ux_canon_scan", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Avoid registering in sys.modules to prevent import side effects
    spec.loader.exec_module(mod)
    return mod


# Module-level cache: the scanner is pure and deterministic over the same
# tree, so we run it once and share the result across the three tests.
_SCAN_RESULT: dict | None = None


def _get_scan():
    global _SCAN_RESULT
    if _SCAN_RESULT is None:
        mod = _load_scanner()
        _SCAN_RESULT = mod.scan(REPO_ROOT)
    return _SCAN_RESULT


# ---------------------------------------------------------------------------
# Test 1: ratchet
# ---------------------------------------------------------------------------

def test_ratchet():
    """For every rule, the current hit count must be <= the ceiling count.

    Failure message names the rule, the delta, and the faces whose count
    rose — so a developer sees exactly what to fix.
    """
    ceiling = json.loads(CEILING_PATH.read_text())
    result = _get_scan()
    totals = result["totals"]
    face_rule_counts = result["face_rule_counts"]
    ceiling_faces = ceiling.get("faces", {})

    regressions: list[str] = []
    for rule, current in totals["per_rule"].items():
        ceiling_val = ceiling["per_rule"].get(rule, 0)
        if current > ceiling_val:
            delta = current - ceiling_val
            risen: list[str] = []
            for face, counts in face_rule_counts.items():
                face_current = counts.get(rule, 0)
                face_ceiling = ceiling_faces.get(face, {}).get(rule, 0)
                if face_current > face_ceiling:
                    risen.append(f"  {face}: {face_ceiling} -> {face_current}")
            detail = "\n".join(risen) if risen else "  (no single face rose)"
            regressions.append(
                f"{rule}: ceiling {ceiling_val} -> current {current} (+{delta})\n{detail}"
            )

    assert not regressions, (
        "UX canon ratchet broken — new violations introduced:\n\n"
        + "\n\n".join(regressions)
        + "\n\nFix the violations, or if this is a deliberate trade-off, "
        "run: python scripts/ux_canon_scan.py --write-ceiling tests/ux_canon_ceiling.json"
    )


# ---------------------------------------------------------------------------
# Test 2: hard zeros (+ A1 allowlist)
# ---------------------------------------------------------------------------

# Named allowlist for A1 (raw <button>) residues.  Each entry is
# "Face:approximate_line" with a one-line reason.
_A1_ALLOWLIST: dict[str, str] = {
    "Pullout": "PulloutFrame fallback retry — Button lacks ref forward for this inline pattern",
    "Surface:188": "surface-row-open — library-internal species in the surface kit",
    "Surface:959": "surface-tile-ghost-btn — library-internal species in the surface kit",
    "ThoughtContextPicker": "li button list-item pattern — Button lacks a ref forward for list items",
}


def test_hard_zeros():
    """DS6 (accent rail) and A9 (egress) must be zero.

    A1 (raw <button>) must stay within the named allowlist — every
    residue is accounted for.
    """
    result = _get_scan()
    totals = result["totals"]

    ds6 = totals["per_rule"].get("DS6", 0)
    assert ds6 == 0, f"DS6 (accent left rail) must be 0, got {ds6}"

    a9 = totals["per_rule"].get("A9", 0)
    assert a9 == 0, f"A9 (missing egress chip) must be 0, got {a9}"

    a1 = totals["per_rule"].get("A1", 0)
    assert a1 <= len(_A1_ALLOWLIST), (
        f"A1 (raw <button>) is {a1}, allowlist has {len(_A1_ALLOWLIST)} entries — "
        f"new raw buttons found; fix them or extend the allowlist with a reason"
    )


# ---------------------------------------------------------------------------
# Test 3: healing (informational — always passes)
# ---------------------------------------------------------------------------

def test_healing(capsys):
    """If any rule's current count is below the ceiling, print a notice.

    This test always passes.  The notice reminds the developer to lower
    the ceiling so the gain is locked in.
    """
    ceiling = json.loads(CEILING_PATH.read_text())
    result = _get_scan()
    totals = result["totals"]

    healed = False
    for rule, ceiling_val in sorted(ceiling["per_rule"].items()):
        current = totals["per_rule"].get(rule, 0)
        if current < ceiling_val:
            healed = True
            print(f"ratchet: {rule} {ceiling_val} -> {current} -- lower the ceiling")

    if not healed:
        print("ratchet: ceiling matches current counts -- nothing to lower")
