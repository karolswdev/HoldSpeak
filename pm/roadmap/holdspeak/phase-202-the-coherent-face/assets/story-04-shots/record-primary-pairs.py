"""Astra's counsel MISSED: "Record each pair and its owner."

A record that cannot rot: every entry names a file:line, the exact text
expected there, and the lane that owns the arbitration. A drifted line is
a hard failure, so this ledger cannot quietly go stale.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]

# (face, file, line, expected text on that line, verb, owner)
PAIRS = [
    ("Chair / arrival", "web/src/desk/chair/ChairHome.tsx", 1777,
     'variant="primary"', "Continue (Thoughts, first row)",
     "story 05 — the primary arbitration on the arrival"),
    ("Chair / arrival", "web/src/desk/chair/ChairHome.tsx", 1983,
     'variant={m.id === leadRunId ? "primary" : "ghost"}',
     "Run summary (lead meeting)",
     "story 05 — the primary arbitration on the arrival"),
    ("Chair / arrival", "web/src/desk/chair/ChairHome.tsx", 2069,
     'variant="primary"', "Answer (blocked coder session)",
     "story 05 — the primary arbitration on the arrival"),
    ("Meetings Record wing", "web/src/pages/cores/history/ImportSection.tsx", 63,
     'variant="primary"', "Record meeting",
     "story 05 — one filled primary per window"),
    ("Meetings Record wing", "web/src/pages/cores/history/ImportSection.tsx", 125,
     'variant="primary"', "Import (filled even while disabled)",
     "story 05 — one filled primary per window"),
    ("Thought window", "web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx", 493,
     'variant="primary"', "Resume / Finish (note footer)",
     "story 05 — pairs with the restart banner below"),
    ("Thought window", "web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx", 540,
     'variant="primary"', "Reload Thought (restart banner)",
     "story 05 — pairs with the note footer above"),
]

# Astra's MISSED: the Sequence footer's raw controls, named so that this
# names lane's "every verb" closure does not read as species closure.
RAW = [
    ("Sequence pullout footer", "web/src/desk/pullouts/ChainPullout.tsx", 65,
     'className="desk-chip quiet"', "Dictate about this",
     "story 03 — the raw-control census"),
    ("Sequence pullout footer", "web/src/desk/pullouts/ChainPullout.tsx", 74,
     'className="desk-chip is-primary"', "Edit",
     "story 03 — the raw-control census"),
]

ok = True
for title, header, rows in (
    ("FILLED-PRIMARY PAIRS on the touched screens (U4)", None, PAIRS),
    ("RAW CONTROLS this lane touched a LABEL on but did not migrate (U1)",
     None, RAW),
):
    print(f"\n{title}")
    for face, path, line, expect, verb, owner in rows:
        target = REPO / path
        lines = target.read_text().splitlines()
        found = lines[line - 1].strip() if line <= len(lines) else "(out of range)"
        good = expect in found
        ok &= good
        print(f"  {'OK ' if good else 'BAD'} {path}:{line}")
        print(f"        {face} — {verb}")
        print(f"        owner: {owner}")
        if not good:
            print(f"        !! expected {expect!r}, found {found[:90]!r}")

print("\nNeither pair is fixed here: this is the NAMES lane, and a filled/"
      "ghost arbitration is a species decision. Every entry above is a "
      "line-checked record, not a promise.")
print("VERDICT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
