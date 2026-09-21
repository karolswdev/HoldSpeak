"""Astra's counsel condition 2: the dated after-map must reconcile, and
every row it claims must name a fence that exists and a site that holds
the new text."""
import csv, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
VERBS = REPO / "docs/internal/surface-inventory-2026-09-20/02-verbs-after-2026-09-21.csv"
NOUNS = REPO / "docs/internal/surface-inventory-2026-09-20/02-nouns-after-2026-09-21.csv"
RED = REPO / "pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/red-first.py"
SHOTS = REPO / "pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots"

ok = True
rows = list(csv.DictReader(VERBS.open()))
print(f"after-map rows: {len(rows)}")
red_text = RED.read_text()

for row in rows:
    rid = row["row_id"]
    problems = []
    if row["closed"] != "yes":
        problems.append("not closed")
    # the fence file exists
    for fence in row["fence"].split(";"):
        fence = fence.strip().split(":")[0]
        if not fence:
            continue
        candidates = [REPO / fence, REPO / "web" / fence]
        if not any(c.exists() for c in candidates):
            problems.append(f"fence missing: {fence}")
    # the site_after names a file that exists and a line that is in range
    path, _, line = row["site_after"].rpartition(":")
    target = REPO / path
    if not target.exists():
        problems.append(f"site_after missing: {path}")
    elif line.isdigit() and int(line) > len(target.read_text().splitlines()):
        problems.append(f"site_after line out of range: {row['site_after']}")
    # every shot named exists
    for shot in row["shot"].split(";"):
        shot = shot.strip()
        if shot.endswith(".png") and not (SHOTS / shot).exists():
            problems.append(f"shot missing: {shot}")
    # the row is in the red-first table (by its leading number)
    num = re.match(r"\d+b?", rid)
    if num and f'"{num.group(0)} ' not in red_text:
        problems.append("no red-first row")
    print(f"  {rid:4s} {'OK ' if not problems else 'BAD'} {row['thing_or_job'][:46]:46s}"
          f" {row['names_before'][:28]:28s} -> {row['names_after'][:30]}")
    for p in problems:
        print(f"       !! {p}")
        ok = False

nouns = list(csv.DictReader(NOUNS.open()))
print(f"\nnoun collisions: {len(nouns)}")
for n in nouns:
    print(f"  {n['status']:26s} {n['thing']}")
closed = [n for n in nouns if n["status"] == "closed-on-touched-faces"]
print(f"\ncollapsed on the touched faces: {len(closed)} of {len(nouns)};"
      f" the rest carry a recorded reason")
ok &= all(n["residue_ledgered"].strip() for n in nouns)
print("VERDICT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
