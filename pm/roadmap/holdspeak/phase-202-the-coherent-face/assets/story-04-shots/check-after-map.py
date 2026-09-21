"""The dated after-map must reconcile, and every row it claims must name a
fence that exists and a site that HOLDS the changed string.

Astra's round-two condition 3: the first version of this checker only asked
whether `site_after`'s line number was IN RANGE. In-range is not a
reference — it let row 01 point into a comment about the deferred queue
while claiming to anchor the Summary section label, and it would have gone
on passing as every later edit shifted the file. A consumer reference that
cannot be wrong proves nothing.

Each row now carries `anchor_text`: the exact text that must be ON the
anchored line. A drifted anchor, a renamed string or a moved line is a hard
failure naming what it found instead.

`site_before` is deliberately NOT checked: it anchors the PRE-change tree
(the census at 93f9524f) and no line of it survives here."""
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
    # `site_after` must name a file that exists AND a line that carries the
    # changed string -- not merely a line that exists.
    path, _, line = row["site_after"].rpartition(":")
    target = REPO / path
    anchor = row.get("anchor_text", "").strip()
    if not anchor:
        problems.append("no anchor_text: the reference cannot be checked")
    elif not target.exists():
        problems.append(f"site_after missing: {path}")
    elif not line.isdigit():
        problems.append(f"site_after has no line: {row['site_after']}")
    else:
        src = target.read_text().splitlines()
        n = int(line)
        if n < 1 or n > len(src):
            problems.append(
                f"site_after line out of range: {row['site_after']}"
                f" (the file has {len(src)} lines)")
        elif anchor not in src[n - 1]:
            problems.append(
                f"site_after does NOT carry its string: {row['site_after']}\n"
                f"            wanted: {anchor}\n"
                f"            found:  {src[n - 1].strip()[:110]}")
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
