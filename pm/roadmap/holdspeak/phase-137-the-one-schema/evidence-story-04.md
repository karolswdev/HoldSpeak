# Evidence - HS-137-04

- **Story:** HS-137-04 - Prove on the real DB, docs, close
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-17T16:03:14Z

- **Command:** `uv run python scripts/verify_reconcile_real_db.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7458fe095f6366ae1dcfa52f3e9077bee661cbe7

```text
copied real DB → /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs137-verify-n7rqrwqn/holdspeak.db

PRE: 133 tables, stamped version 63
  sample rows: {'meetings': 4, 'decisions': 0, 'artifacts': 0, 'workbenches': 0, 'recipes': 0, 'notes': 0, 'profiles': 0, 'activity_records': 0}
  PASS  scheduled_recordings absent before (v63 lacks it)

opening the copy through Database() (reconcile-on-open)…
Schema shape changed; backed up to /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs137-verify-n7rqrwqn/holdspeak.db.20260817-100314.bak before applying backfills
  PASS  open did not raise a version refusal (A5)

POST: 134 tables
  sample rows: {'meetings': 4, 'decisions': 0, 'artifacts': 0, 'workbenches': 0, 'recipes': 0, 'notes': 0, 'profiles': 0, 'activity_records': 0}
  PASS  no table was lost (A1/A6)  lost=[]
  PASS  scheduled_recordings was gained (A3)
  PASS  rows preserved in meetings: 4 → 4  before=4 after=4
  PASS  rows preserved in decisions: 0 → 0  before=0 after=0
  PASS  rows preserved in artifacts: 0 → 0  before=0 after=0
  PASS  rows preserved in workbenches: 0 → 0  before=0 after=0
  PASS  rows preserved in recipes: 0 → 0  before=0 after=0
  PASS  rows preserved in notes: 0 → 0  before=0 after=0
  PASS  rows preserved in profiles: 0 → 0  before=0 after=0
  PASS  rows preserved in activity_records: 0 → 0  before=0 after=0
  PASS  orphan tables survived (the 7 experimental)  (only asserted if present before)

ALL CHECKS PASSED
```
