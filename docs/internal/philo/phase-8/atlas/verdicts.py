"""PHILO-8-03: print one row per retained rig observation (case | width | verdict | duration | revision | reading).

Usage: python3 docs/internal/philo/phase-8/atlas/verdicts.py <run folder> [...]
The run folders are the rig's `--out` directories (one subfolder per run, each
with its observation.json), retained under
pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-03-shots/.
"""
import json
import sys
from pathlib import Path

for root in sys.argv[1:]:
    rows = []
    for obs in sorted(Path(root).glob("*/observation.json")):
        r = json.loads(obs.read_text())
        notes = [n for n in r.get("notes", []) if n.startswith(("predicate:", "BLOCKED:"))]
        reading = (notes[0] if notes else "")[:230].replace("\n", " ")
        headless = not (r.get("shots") or [])
        width = "op" if r.get("case_id", "").endswith(".op") else r.get("viewport")
        rows.append((r.get("case_id"), str(width), r.get("verdict"), f"{r.get('duration_s', 0):.1f}s",
                     (r.get("provenance") or {}).get("revision") or "-", reading))
    print(f"## {root}  ({len(rows)} runs)")
    for row in rows:
        print(" | ".join(row))
    print()
