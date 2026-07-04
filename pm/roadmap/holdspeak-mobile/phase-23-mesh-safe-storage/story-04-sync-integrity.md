# HSM-23-04 — Sync integrity: the per-primitive round-trip matrix + the serialization-contract pin

- **Project:** holdspeak-mobile
- **Phase:** 23
- **Status:** in-progress
- **Depends on:** the Wave-1 live-merge (`/api/sync/push` merges into the real stores) and
  the HS-72-01 tri-guard (ChangeSet schema + pytest + Swift golden fixture) — both
  shipped; this story finishes what they left open.
- **Unblocks:** the mesh can trust that EVERY kind survives the wire, and the contract doc
  states the wire that actually ships.
- **Owner:** unassigned

## Problem

Survey-corrected (2026-07-04). The audit's two sync-integrity footnotes are mostly
pre-paid — push live-merges (Wave 1), the envelope is schema-pinned (HS-72-01). Three
holes remain:

1. **Chain and workflow are unlocked matrix rows.** They ride the generic `_MERGEABLE`
   push path with pull-serialization coverage only — no push→pull round-trip, LWW, or
   tombstone assertion of their own (every other kind has one). The audit critic's
   per-primitive matrix lands here.
2. **§11 of `SERIALIZATION-CONTRACT.md` describes a dead wire.** Still
   `change_set: {meetings, artifacts}` and `kind: "meeting"|"artifact"`, with the envelope
   schema "landing" in the future tense — the live wire carries 10 kinds and the schema
   shipped (§12 knows; §11 was never back-updated).
3. **The "lossy manual_context" finding went stale.** §12 and `agent.schema.json` still
   record `Agent.manual_context`/`use_zone_context` as "NOT persisted by the hub (lossy;
   fix is a follow-up)". Phase 77 (db v7) fixed it: the hub persists, merges, and
   re-emits both, byte-faithful (`test_agent_pinned_context.py`). The contract must state
   the fix, not the finding.

## The design

1. **The matrix, uniform:** per-kind push→pull round-trip + LWW + tombstone locks for
   chain and workflow, in the same style as the existing note/kb/agent/membership tests
   (`test_web_routes_sync_primitives.py`), so all 10 kinds carry the same lock.
2. **§11 rewritten to the shipping wire:** the 10-bucket `change_set`, the full `kind`
   enum, tombstone rule unchanged, and a pointer to §12's guards as the enforcement.
3. **The truth correction:** §12's locked-findings note and the `agent.schema.json`
   descriptions updated to record the Phase-77 fix (with the test that locks it).

## Scope

- **In:** the chain/workflow test rows; the §11 rewrite; the §12 + `agent.schema.json`
  correction. Docs and tests only — the shipping wire is already correct.
- **Out:** conflict-grade `last_modified` for meetings (pull emits `started_at`; a known,
  documented transport-grade stamp); the Swift side (the golden-fixture pin already
  covers it); any new sync kind.

## Test plan

- `uv run pytest -q tests/unit/test_web_routes_sync_primitives.py
  tests/unit/test_primitive_contract.py tests/integration/test_primitive_framework_sync.py
  tests/unit/test_agent_pinned_context.py` — the new chain/workflow rows green, no
  regression in the contract locks.
- `uv run python pm/roadmap/holdspeak-mobile/contracts/validate.py` — the standalone
  guard still green after the schema description edits.
