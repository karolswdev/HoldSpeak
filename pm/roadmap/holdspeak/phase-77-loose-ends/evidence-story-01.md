# Evidence — HS-77-01 — The agent's pinned context survives the hub

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-77-loose-ends`)

## What changed

- **Schema v7**: `agents.manual_context TEXT NOT NULL DEFAULT ''` +
  `agents.use_zone_context INTEGER NOT NULL DEFAULT 0`, additive via the
  guarded-ALTER recipe (the v4 `profile_id` precedent), riding the
  Phase-50 backup-then-apply path.
- **Every hub layer speaks them**: `AgentRecord` (+ `to_dict` wire keys),
  `agents.upsert` (+ the NULL-safe row parse for pre-v7 rows), the REST
  `_agent_fields` (a partial PUT that never mentions them preserves
  them), and the sync `_MERGEABLE` map (push merges them; pull re-emits
  them).
- **The Swift tolerant-decode comment updated**: the Phase-72 loss ended;
  defaults remain for pre-v7 hubs. Zero functional Swift change needed —
  the tolerant decode already reads the fields when present, which was
  the design bet HS-72-01 made.

## Verification artifacts

- `tests/unit/test_agent_pinned_context.py` — **4 passed** first try:
  1. the store round trip + the wire keys;
  2. **the full sync round trip** — a pushed iPad agent with pinned
     context pulls back byte-faithful (the exact loss Phase 72
     documented);
  3. the REST routes carry them AND a partial PUT preserves them;
  4. the v6-facsimile upgrade adds the columns (existing rows keep their
     data; the `.bak` lands first).
- The guards fired exactly as designed and were updated honestly: the
  canonical schema snapshot (regenerated with the documented literal
  normalizer) and the framework-sync contract test pinning the exact
  agent key set (gains the two keys with a v7 comment).
- Swift suite green (0 test regressions). Full suite at ship: **3092
  passed, 37 skipped, 0 failures** (3088 + the 4 new).

## Acceptance criteria — re-checked

- [x] Persisted (v7, the guarded-ALTER precedent), on the wire both
      ways, byte-faithful round trip, Swift comment updated.
