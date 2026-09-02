# Phase 164 - The Unattended Desk (P5): final summary

**Exit, verbatim:** Gate A observes at least two useful unattended
runs without confirmation prompts or duplicate effects. **MET AND
COUNTED on glass:** two SCHEDULED runs completed across ticks with
nobody home - 2 door items (unique), 2 updates, 0 duplicate effects,
0 confirmation prompts - measured into
assets/story-06-effect-inventory.json.

## The seven stories

1. **The due ledger** - v72 additive: evaluation cadence + durable
   circuit on connector_watches; unattended_enabled (default OFF) as
   a real column on steward_policies. Trace-first: the graduated
   watches' due columns were REUSED (HS-159-01 had them), the legacy
   scheduler untouched, EndpointHealth left to LLM endpoints.
2. **evaluate_due** - due selection on cadence; NEVER raises; the
   durable circuit (3 strikes / 900s window / one probe / reset
   in-transaction); evaluate_once byte-identical via _evaluate_core;
   the owner's hand overrides the circuit. The boundary rule: the
   state column fences the two schedulers - never two on a row.
3. **run_due** - the STOP paid: the 161 effect machinery was DORMANT
   SCHEMA (zero production callers, no dispatcher). Ruling: wake the
   tables as designed. WatchCondition@1 matcher; effects recorded
   durably at evaluation; run_due drains with honest gate receipts
   (opt-in / disabled / cooldown / resolved_existing_run at
   watermark watch:<id>:<source_revision> / run_started); STW-002
   absorbed as resolution; manual paths byte-identical.
4. **The conductor** - two independent failure boundaries; all SS10
   steward events at their seams; Cadence attention projections
   (never the schedule of record). Two orchestrator catches: the
   blocks built CRIPPLED services (fixed with the
   set_scheduler_services injection seam; unwired = honest skip) and
   the isolation tests were THEATER (rewritten against the real
   tick).
5. **The face** - the grant law (the opt-in states its exact
   assembled grant), provenance chips (Scheduled vs Manual), circuit
   rows in the ledger's time-slot grammar. THE OWNER'S VERDICT:
   round 1 "Bounce" (scroll wells must announce themselves + his
   model-wiring question), round 2 "PASS". Both findings paid: the
   Door scroll-hint species ported vertical; the over-claiming MODEL
   chip removed (the Delta is deterministic) and the honest chip
   names project.update_draft in Settings > Models.
6. **The walk** - Gate A counted; dedup-across-ticks, circuit, and
   opt-out legs; 8 passed x2 deterministic; build-first from birth.
   Three shot rounds, each root-caused: grant grammar, attention
   ordering (a broken source outranks configuration), and the
   house-ledger 52px time-column clip (LAW: pass time= to
   SurfaceLedgerRow).
7. **The close** - this document.

## Gates (real numbers)

- Full CI-style suite: **13 failed / 8780 passed / 61 skipped in
  25:22** -> sweep: 9 names = main's 27-name baseline (still valid
  for 69e16678 - 163's close fixed only branch-new breaks); 4
  candidates -> **3 proven flakes** (hs141/hs143/hs151 glass: x2
  green, untouched by branch, known families) + **1 real fixed
  in-round** (api-surface consumers regen - the face's
  listProjectWatches call annotated). Zero unexplained.
- Web: npm check + baseline **2275 passed, zero branch-new**.
- Counsel round: 215 backend + 49 vitest post-fix.

## Counsel (adversarial, read-only, whole branch)

**RATIFY-WITH-CONDITIONS**; nine hunts verified correct. Paid
in-round: M-1 (manual evaluation now CLOSES the circuit - the
docstring promised what the code did not deliver; the owner's-hand
recovery was broken; regression-tested), S-1 (scroll-hint effect
mounts once), S-2 (closed circuits heal their stale steward_degraded
Cadence loops - no immortal attention items; idempotent, tested),
S-3 (event comments honest: best-effort, not in-transaction), S-4
(chip removal noted).

## Debts

- New, carried to P6+: counsel N-1 (effect minting outside the
  evaluation txn - tiny crash window), N-2 (older_than template
  conditions honestly unmatchable - pre-existing, invisible to the
  user), N-3 (limit-100 watermark scan), N-4 (step-event volume at
  aggressive cadence - no retention policy), N-5 (synchronous tick
  cost - lawful for the single-owner desk); the wire has NO
  scheduled-path trigger route (the rig drives the injected
  instances); per-watch cadence has no write wire (read-only on the
  face).
- Carried from before (re-listed): 163 S-4 (route-layer command
  recording), N-1 (thread pool), N-3 (recovery's second instance);
  160 N-5/N-1/N-2; 158 S-1/N-1/N-3; 159 seeding walls; 161 N-1.

## For P6 (the MCP Project family)

The same closed loop over MCP resources/tools; the scheduled-path
trigger wire and per-watch cadence editing are natural riders;
event retention and the effect-txn window deserve a look when the
desk leaves single-owner.
