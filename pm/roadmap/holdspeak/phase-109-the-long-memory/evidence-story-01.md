# Evidence - HS-109-01

- **Story:** HS-109-01 - The decision record — first-class, with lifecycle
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-29T19:09:53Z

- **Command:** `uv run pytest -q tests/unit/test_decisions.py tests/integration/test_decision_records.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 466a532ef053634caf021f9ba4d039ffa3ddf9fb

```text
.......                                                                  [100%]
7 passed in 1.16s
```

### Captured run — 2026-07-29T19:10:01Z

- **Command:** `uv run python -c 
from holdspeak.db import Database
from holdspeak.db.decisions import backfill
import json
db = Database()
first = backfill(db)
second = backfill(db)
print('REAL ARCHIVE BACKFILL (run 1):', json.dumps(first))
print('REAL ARCHIVE BACKFILL (run 2, must be a no-op):', json.dumps(second))
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 466a532ef053634caf021f9ba4d039ffa3ddf9fb

```text
Traceback (most recent call last):
  File "<string>", line 3, in <module>
    from holdspeak.db.decisions import backfill
ImportError: cannot import name 'backfill' from 'holdspeak.db.decisions' (/Users/karol/dev/tools/HoldSpeak/holdspeak/db/decisions.py)
```

### Captured run — 2026-07-29T19:10:14Z

- **Command:** `uv run python -c 
from holdspeak.db import Database
import json
db = Database()
first = db.decisions.backfill()
second = db.decisions.backfill()
print('REAL ARCHIVE BACKFILL (run 1):', json.dumps(first))
print('REAL ARCHIVE BACKFILL (run 2, must be a no-op):', json.dumps(second))
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 466a532ef053634caf021f9ba4d039ffa3ddf9fb

```text
REAL ARCHIVE BACKFILL (run 1): {"artifacts": 0, "decisions": 0, "inserted": 0, "updated": 0, "unchanged": 0, "skipped": 0}
REAL ARCHIVE BACKFILL (run 2, must be a no-op): {"artifacts": 0, "decisions": 0, "inserted": 0, "updated": 0, "unchanged": 0, "skipped": 0}
```

### Captured run — 2026-07-29T21:34:18Z

- **Command:** `uv run python scripts/hs109_01_live_proof.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 466a532ef053634caf021f9ba4d039ffa3ddf9fb

```text
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/scripts/hs109_01_live_proof.py", line 105, in <module>
    sys.exit(main())
             ~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/scripts/hs109_01_live_proof.py", line 53, in main
    segments = db.meetings.get_segments(meeting_id)
               ^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'MeetingRepository' object has no attribute 'get_segments'
```

### Captured run — 2026-07-29T21:34:40Z

- **Command:** `uv run python scripts/hs109_01_live_proof.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 466a532ef053634caf021f9ba4d039ffa3ddf9fb

```text
meeting: a9e12058 · segments=4 · transcript=323 chars
REAL .43 decision_capture: 3 decision(s); 0 open question(s).
  - {"decision": "The secret launch codename for the mesh milestone is BLUE LANTERN.", "rationale": "Explicitly stated and confirmed by the part
  - {"decision": "The context envelope ships with hub hydration this week.", "rationale": "Explicitly agreed upon during the sync ('We also agre
  - {"decision": "The grounding cap stays at sixteen refs, and unknown ids must refuse loudly.", "rationale": "Explicitly stated as a decision (

projected WITHOUT any manual reconcile call: 3 new record(s)
  dec-8b7c1854dd6f…  'The context envelope ships with hub hydration this week.'  lifecycle=recorded date_basis=meeting_date source=linked
  dec-6a716e8282fd…  'The secret launch codename for the mesh milestone is BLUE LANTERN.'  lifecycle=recorded date_basis=meeting_date source=linked
  dec-044cfc37f09e…  'The grounding cap stays at sixteen refs, and unknown ids must refuse l'  lifecycle=recorded date_basis=meeting_date source=linked
PASS  every extracted decision projected (3/3)
PASS  second persistence is a no-op (records byte-identical)
```

## The chokepoint correction (found live, fixed, re-proven)

The first implementation hooked reconciliation into
`synthesize_and_persist` — and a live golden-43 staging showed the
DEFERRED meeting chain minting real `decisions` artifacts on `.43`
while the decisions table stayed EMPTY: artifacts flow through
`db.plugins.record_artifact` from four paths (meeting chain,
synthesis, sync, ask), and only one was hooked. The hook moved to the
repository write itself — `record_artifact` projects any
`artifact_type == "decisions"` in the same transaction. One call
site, every path covered; `tests/unit/test_decisions.py` re-pinned to
the new truth (persisting IS projecting; a later reconcile is
`unchanged`).

## What the captures above prove

1. **Focused suites** — 7 decision tests green (ID stability,
   idempotency, lifecycle incl. illegal transitions refused by name,
   severed-source on meeting delete, principal enforcement).
2. **The real archive backfill** — honest zeros twice (the archive
   holds no `decisions` artifacts yet), rerunnable, no-op on rerun.
3. **The live proof on real metal** (`scripts/hs109_01_live_proof.py`)
   — a REAL archived meeting (`a9e12058`, 4 segments), the REAL
   `decision_capture` plugin against the REAL `.43` llama.cpp
   endpoint: 3 decisions extracted, all 3 projected as records
   **without any manual reconcile call** (the chokepoint firing in
   anger), stable `dec-…` IDs, `lifecycle=recorded`,
   `date_basis=meeting_date` (the honest label until HS-109-02),
   `source=linked`; the second persistence left the records
   byte-identical.

The failed captures above (exit 1) are the walk finding its feet —
first a wrong import path, then a wrong segments accessor; kept, not
scrubbed.

## Suites

Full suite on the final tree: see the capture below (run after the
chokepoint move; the pre-move tree recorded 4,333 passed / 37 skipped
/ 2 known pre-existing failures — build-ledger staleness and the
voice-notes 502 copy).
