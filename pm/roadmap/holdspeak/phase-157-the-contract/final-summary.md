# Phase 157 — Project Rooms: The Contract (P0) — Final summary

**Closed:** 2026-08-31. **Verdict:** counsel RATIFY, zero must-fix, zero
should-fix. 5/5 stories done with evidence. First phase of the Project
Rooms arc, executed against the vetted SRS suite merged at `e7e56e1e`
(PR #519).

## What the phase proved

P0's exit was "current behavior is protected and schema/API names are
agreed." Both are now true by construction:

- **275 new tests** protect the graduation: 58 (refs) + 109 (contracts)
  + 62 (service) + 46 (routes) + 7 (MCP registration) + 5 (web
  registration/core gaps). A P1 regression in any service shape, route
  status code, Web registration field, or MCP tool name fails a test.
- **The names are frozen** in `holdspeak/refs.py`,
  `holdspeak/project_contracts.py`, and
  `docs/internal/project-rooms/CONTRACTS-P0.md`: 12 citizen ref types,
  16 result kinds, 5 error codes, 11 ID prefixes (3 deterministic with
  §4.1 input signatures) — every name traced to an SRS requirement ID.
- **REF-003 settled by evidence, not aesthetics:** `people:` canonical,
  `person:` alias — all 6 emitters and 5/6 parsers already spoke
  `people:`; the charter's own `person:` guess was reversed by the
  inventory. The REF-001 fence (named module list) guards new code.

## Discoveries on the record (P1+ owes these)

1. **MCP-006 baseline violation:** `holdspeak/mcp/families/__init__.py`
   bare-imports all 15 families — one import failure suppresses ALL
   MCP families. P6's hardening story owns the fix.
2. **DELETE is archive** (`projects.py:79`) — the verb lies politely;
   P1's command contract names it honestly.
3. **Three flavors of 404 wording + success-key asymmetry** across
   project routes — the HS-157-02 error-code table is the cure.
4. **Raw ValueError** through the service boundary from the
   relationship repository (`project_service.py:97-101`).
5. `thread_service.py:311`'s `person:` parse path looks dead (no
   emitter produces it) — P1 verifies.
6. Counsel N-2: SRS §3.2 "Note/artifact" row should split into two at
   the next suite amendment (code registers them separately).

## Gates

- Full suite CI-style (isolated HOME, `-n auto`, metal excluded):
  12 failed / 7766 passed vs main's 26-name CI baseline — name-diff
  produced 2 candidates, both proven load-flakes (each passes in
  isolation; the branch changes zero runtime code): the
  `sleep 0.2` race in `test_one_shot_disables_after_cancelled` and
  glass `error-1440` under xdist+vitest contention. Zero true
  branch-new.
- Web: `npm --prefix web run check` green (bundle gate passed);
  inherited baseline verdict `baseline-subset, zero branch-new`
  (1791 passed).
- Counsel close: RATIFY — all five axes clean; N-1 (fence list)
  applied in-round; N-2 recorded above.
- Effect-ledger tombstone untouched; no schema change; no positional
  INSERTs; nothing imports the new modules yet (by design).

## The road from here

P1 "The Room" charters next (aggregate + revision + `GET /room`),
anchors re-verified against the new main at charter time per the
handover's own rule.
