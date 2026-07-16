# HS-94-05 progress record — Evidence dossiers and safe asset browsing

**Captured:** 2026-07-16<br>
**Acceptance status:** done at the owner-rescoped scope (real GitHub
branch/PR/CI receipt rows in BACKLOG candidate Y, degradable per the
contract; Desk compose-path wiring of the grounding adapter rides
HS-94-08).

## What shipped

- `holdspeak/delivery/dossiers.py`: an LRU manifest cache keyed by
  bundle_id with a bounded-age window (polls inside it never shell out),
  honest `bundle_changed` service of superseded bundles, and offline
  degradation to `freshness: unavailable` with retained members.
- Story and Phase dossier read models (`dossier_schema:1`): sanitized
  Markdown (raw HTML stripped outside code fences; fenced captured output
  survives verbatim), parsed captured runs with pass/fail distinct, asset
  metadata with no paths anywhere on the wire; the Phase dossier proves
  laziness by subprocess count (zero asset reads).
- The ranged asset proxy over `dw evidence asset`: manifest-bound only,
  ETag/304, single-range 206/416, typed refusals mapped to HTTP
  (not_in_manifest/symlink/outside_root 404, oversize 413, bundle_changed
  and hub-detected hash_mismatch 409, unavailable 503 with the manifest
  still visible).
- `hydrate_dossier_refs`: dossier members hydrate into the identical capped
  GroundingBlock shape the rails picker produces.

## Verification

30 tests green against real scratch repos (standard, self-hosted, linked
worktree) with real evidence (passing and failing runs, PNG, JSON, log,
oversize, symlinks): completeness, sanitization, every typed refusal, cache
economics, wire hygiene walks, grounding caps. Combined lane 223 passed
with the legacy evidence route untouched.
Captured at close in [evidence-story-05](./evidence-story-05.md).
