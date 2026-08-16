# Evidence - HS-132-08

- **Story:** HS-132-08 - Intelligence tells the truth
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:51:13Z

- **Command:** `env HOME=/tmp/hs132-08-home uv run pytest -q tests/unit/test_monday_brief_service.py tests/unit/test_brief_collectors.py tests/unit/test_brief_shelf.py tests/unit/test_brief_mcp.py tests/unit/test_db.py tests/unit/test_db_schema_policy.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b729c79238b9b194cbf4caacb2fc5c4e7504cdd6

```text
........................................................................ [ 54%]
...........................................................              [100%]
131 passed in 26.51s
```

## Orchestrator notes

- Web proof (not in the captured run): IntelligenceTruth (8) +
  AftercareNote (4) + AmbientLayer (5) vitest green under the
  orchestrator; the audit's ALL-CLEAR probe is now a kept regression test.
- Schema v59 → v60 (monday_brief_item_shelf); canonical snapshot
  regenerated with exactly the two new lines; version pins updated in the
  four suites that carry them.
- The FollowThroughView em-dash vocabulary offender is gone with the
  empty-state rework; the orchestrator additionally fixed the "Intel
  queue" → "Intelligence queue" canon violation that HS-132-03's queue
  HUD introduced in AmbientLayer (this file ships whole in this commit,
  carrying 03's queue-HUD consumer per shared-file etiquette).
- Ledger (recorded, unfixed): pre-existing ~1-in-6 flake in
  IntelligenceWalk.test.tsx:129 — DecisionsView renders its searchbox
  while loading so the walk test can race; structural, owned by
  HS-132-12's net work or a later slice. MicButton:353 em dash flagged to
  the in-flight HS-132-05 worker.
