# Phase 163 - The Steward's Hand (P4): final summary

**Exit, verbatim:** a manual run performs one real deduplicated effect
and drafts an update with a durable receipt. **MET, measured on
glass:** one press = 5 real effects (sources refreshed, proposals
created + applied through the 160 verbs, update drafted through the
162 factory, a real Door item), every step receipted with
expected/observed; a same-watermark re-run creates 0 additional items
with a visible reconciled receipt.

## The seven stories

1. **The run ledger** - schema v71 additive: steward
   policies/runs/steps/commands; STW-002 as a DB law (partial unique
   index -> typed ActiveRunExistsError); step idempotency_key +
   expected/observed = the STW-005 substrate; real-DB reconcile
   proven on a COPY (1 passed).
2. **The run engine** - six checkpointed phases on the conductor
   pattern; Stop is a durable DB read between phases and before
   every effect slot; recover_on_startup beside the house recovery
   hooks; the orchestrator closed a raw-SQL third door in-round.
3. **The bounded hand** - five V0 effects through the real verbs;
   STW-005 fault-injection proven; STW-008/010 enforced. The
   orchestrator's round found the charter's "lacking canonical
   follow-through" filter MISSING and built it
   (DoorService.has_item_for_source read-back).
4. **The wire** - six routes; immediate-id: insert_run on the
   request thread (STW-002 = synchronous 409), execute_phases on a
   daemon thread; command_id replay; api-surface 612->618 additive.
5. **The face** - the Steward posture in the Room (the
   UpdatePosture architecture, second tenant). THE OWNER'S VERDICT,
   verbatim: "PASS" (one round; the consequence round - visible
   toggle labels, PARTIAL COVERAGE chip, substance secondary lines,
   honest plurals - was the orchestrator's own shot review).
6. **The walk** - glass 8 passed x2 deterministic, both viewports.
   THE RIG EARNED ITS KEEP, three product defects fixed in-round:
   DoorService built without db= (the Door effect had never worked
   on the real app); the door idem key was a PHANTOM never stored on
   any step (a self-seeded unit fixture hid it - the 161 scar) ->
   redesigned watermark-scoped key ON the act step; step seq
   collisions scrambling chronology. Plus the honest degraded seam
   (missing watch row; WatchAdapter never calls providers) and the
   stale-bundle law (the rig must build first).
7. **The close** - this document.

## Gates (real numbers)

- Full CI-style suite (isolated HOME, -n auto): **13 failed, 8680
  passed, 61 skipped in 24:29** -> sweep: 8 names = main's recorded
  baseline (27 @ run 33459107466); 5 candidates -> **4 real, fixed
  in-round** (two v71 pins asserting ==70 under names saying 69 -
  both renamed honest; api-surface consumer annotations regenerated;
  census classification + reviewed-artifact addendum for the retry
  helper), **1 proven flake** (hs151 abort leg: untouched by branch,
  x2 green, known family). Zero unexplained.
- Web: npm check **2254 passed** + bundle gate; inherited baseline
  **zero branch-new** (5 inherited HEALED).
- Steward scoped: 108 backend + 8x2 glass, post-counsel tree.

## Counsel (adversarial, read-only, whole branch)

Verdict **RATIFY-WITH-CONDITIONS**. Paid in-round: M-1 (stop honored
between retries - a retry IS an effect slot), S-1 (StepState carries
interrupted), S-2 (cooldown_seconds ENFORCED, interrupted runs exempt
per STW-009), S-3 (policy.enabled ENFORCED, honest refusal reasons on
the face). Counsel's surprises credited the two-layer door dedup and
the rig's honesty.

## Debts

- Paid this phase: the 162 no-raw-ids law held; the follow-through
  law built; the phantom-key scar (161 family) burned out.
- New, carried to P5: counsel S-4 (route-layer command recording -
  house precedent exists), N-1 (daemon-thread pool if the steward
  leaves the single-owner desk), N-3 (recovery's second service
  instance); cooldown enforcement exists at insert_run - the
  scheduling-layer half arrives with run_due (P5).
- Carried from before (re-listed): 160 N-5 (no-fetch spy), N-1
  (Space preview), N-2 (server-side undismiss); 158 S-1/N-1/N-3;
  159 seeding walls; 161 counsel N-1 (React scope key).

## For P5 (The Unattended Desk)

run_due + the conductor block, Watch-triggered run_once with real
observation watermarks (the same-watermark dedup contract is
caller-carried - built and glass-proven this phase), cooldown at the
scheduling layer, unattended dogfooding toward Gate A.
