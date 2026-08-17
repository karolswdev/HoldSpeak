# Phase 134 — One Owner: final summary

**Verdict sought:** complete (10/10), one evening (2026-08-16), zero
regressions. Owner sitting pending; counsel opinion recorded alongside.

## What shipped

Issue #450 Wave 1, whole. Every placement decision now has one
precedence chain that EXECUTION obeys (not just listings), one outward
vocabulary, and provenance in every answer:

- **The keystone** (`bfcd9884`): Recipe run/chat migrated to
  `resolve_placement` — the last execution path bypassing the Phase-130
  authority. A workbench override now actually redirects an Agent's
  run. AST fence + inline-fallback guard prevent regression.
- **One API** (`eaeca3c8`): the `/api/profiles` read routes died; one
  `_target_fields`; the `profile_alias` compatibility block deleted;
  six downstream consumers re-pointed honestly (tests re-pointed, not
  weakened).
- **MCP speaks destination** (`e0a0d07d`): `profile.*` →
  `destination.*`, `holdspeak://profiles` → `holdspeak://destinations`,
  walk harness updated in the same commit — 82 tools, never red across
  a commit boundary.
- **Provenance everywhere** (`69698469`): Ask, Recipe, Workbench,
  Sequence/Workflow, and Cadence execution responses carry
  `placement: {effective_target_id, source}` from the ACTUAL resolution
  used; MCP passes it through untouched; the source vocabulary is
  fenced by test.
- **Ownership hand-offs** (`a2328776`, `18b7d1d2`): Get Info no longer
  writes `profile_id` (summary + "Edit in Agent"; writer-guard test);
  WorkbenchWindow's five skill-mutation paths deleted (read-only
  INHERITED + hand-off; guard test). Both per #450's rulings verbatim.
- **Sync understands inherit** (`19ea5ea1`): fixed a REAL merge bug —
  fields absent from a push payload were clobbering receiving values
  with NULL via kwargs defaults. Now present-null = inherit, absent =
  preserve; revocation proven on null↔value transitions; pull never
  materializes defaults. 11 new tests.
- **The routing profile stands alone** (`2af4e82a`):
  `mir_profile`/`plugin_profile` deleted from config/validation/
  runtime; the owner's real config file with legacy keys loads clean
  (test); one declared tolerant-read leniency.
- **Docs speak destination** (`3963ca6b`): MCP_SIDECAR + README, 19
  drift guards green, two honest carve-outs where code still owns a
  name.
- **The walk**: default MCP walk 25/25; live `.43` proof 37/37 — the
  control-vs-treatment provenance line (override → `source:
  "workbench"`; cleared → `source: "agent"`; same effective target;
  real Qwen3.6 inference behind both); ownership shots at 1440+393 on
  a rebuilt bundle with zero console errors unfiltered; final suite
  5829 passed.

## Judgment calls the orchestrator made alone (for review)

1. **Settled design in the charter** (null=inherit; destination as the
   outward word; internal storage keeps its name this wave) — from
   #450's own text plus the ledger-not-gate rule.
2. **Ownership extension mid-story**: HS-134-02's route deletion broke
   four consumer test files outside its grant; ownership was extended
   by causation and the re-points rode its commit.
3. **Stale-guard re-point**: the one-dial seam guard asserted the
   pre-keystone resolver; re-pointed (recipe_service → resolve_placement)
   as an HS-134-01 follow-on, named in the commit body.
4. **Manifest rider**: the wave-one gate caught API-surface manifest
   drift; regenerated under isolated HOME (see ledger for the process
   error that preceded it).
5. **Bundle rebuild + filter removal**: the first walk shots rendered a
   stale gitignored bundle and filtered a 405; re-shot on a fresh build
   with zero-error assertions honest.

## The ledger (also in the status doc)

- Three distinct single-run xdist flakes today (device-tick,
  mesh-expiry, schema-migration), each 3/3 green serially → BACKLOG
  Candidate Z.
- **P0 for the owner: the real DB (schema 59) fails the 59→60
  migration** (`no such column: node_id`) — pre-existing, surfaced by
  an orchestrator process error (script run without isolated HOME; DB
  verified unharmed, logical dump identical to backup). The owner's
  hub will hit this on next start against current main. Needs a
  migration fix — recommended as the first story of the next slice.
- Process rules learned: scripts booting the web server always run
  under isolated HOME; web walks rebuild the bundle first; parallel
  workers keep the tree importable between edit steps.

## Held for the owner sitting

1. The tolerant `mir_profile` read-fallback in settings_service
   (declared leniency — retire it or keep it).
2. The 59→60 migration P0's scheduling (rider on the next phase vs
   immediate hotfix).

## Evidence pack

Ten evidence files, the scoping audit in assets/, four ownership
screenshots (1440+393), the live-walk JSON transcript
(assets/mcp-walk-live-transcript.json), suite logs referenced from
evidence. Harnesses: `scripts/mcp_walk.py --live-43` (now with the
provenance proof), `scripts/walk_ownership_shots.py`.
