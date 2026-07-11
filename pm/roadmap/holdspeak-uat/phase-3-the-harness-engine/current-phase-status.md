# Phase 3 — The Harness Engine (unlock the live-agent + device tier)

**Last updated:** 2026-07-09 (paused after HSU-3-02; active work moved to the
Phase-4 functional/usability pass and the owner explicitly declined HSU-3-03)
**Status:** paused (2/5)

> **Protocol-v2 notice:** References below to iPhone/iPad columns describe the
> historical inventory. Executable evidence now names one implementation target
> (`web_react` or an exact Swift root) and an explicit form factor. Native
> verdicts require matching pairing-verified device attestation.

## Goal

The framework and the test protocol both exist: the conductor stages worlds,
the guided site records verdicts, the debrief closes the review loop, and a
6-pack, 53-scenario protocol is authored (see
[`../phase-2-the-inventory/PROTOCOL-COVERAGE.md`](../phase-2-the-inventory/PROTOCOL-COVERAGE.md)).
The [re-evaluation](../phase-2-the-inventory/PROTOCOL-REEVALUATION.md) found the
bottleneck is no longer authorship — it is the **harness engine**: a cluster of
scenarios is authored-but-human-walked because the induction engine lacks the
verbs/probes to *stage and machine-verify* the live-agent and on-device tier.

The biggest unlock — **live steering** (spawn/arm/keys/audit through the
product's `/api/coders` routes) — shipped, along with the honest learning-count
and the key-never-syncs attack. This phase builds the rest of the backlog so the
authored scenarios that are currently `n/a`/human-eyeball become
machine-verifiable, and the iPhone/iPad columns get a real answer.

## Scope

- **In:** new recipe action verbs + verify probes (and the recipes that use
  them) for: the mesh handoff arc (a run driven onto the worker, read back
  badged), the cloud-egress card + a per-card egress probe, the trust-gate
  *attacks* (off-loopback token rejection, idle no-telemetry, crafted-schema DB
  refusal), a pipeline-on dictation world (spoken-symbol matcher + preview
  byte-lock), and the device pre-flight block (pair a real device, hub-reachable
  liveness). Each story flips the specific authored scenarios it unblocks from
  human-walked to staged-and-verified.
- **Out:** any change to `holdspeak` product behaviour (the harness drives the
  product's existing routes only — a product bug found here is a *finding*, not
  a fix); new scenario authorship beyond wiring the unblocked beats (the packs
  already exist); the physical-device *verdicts* themselves (owner-gated, like
  every device leg).

## Exit criteria

- [x] The mesh handoff arc is machine-staged: a desk-ask driven onto the
      `uat-worker` returns badged `⇄ mesh` with worker-log-claims-it /
      hub-shows-no-model-load provenance; pack-e's handoff beats verdicted.
      (HSU-3-01 — `dispatch_run` verb + `run_returned_badged` /
      `run_claimed_by_worker` / `run_output_contains` probes + the
      `mesh-run-on-worker` recipe; green live on `.43`.)
- [x] A cloud-egress card is staged and its egress target read back through a
      probe; the product exposes both the global chrome posture and a genuine
      per-card `☁ GitHub` badge with exact repo. Pack-d/07, pack-d/11, and
      pack-a/04 are staged. (HSU-3-02 — 40 focused tests green.)
- [ ] The trust gate is *attacked*, not imagined: off-loopback without a token
      is refused (401), an idle run emits no beacon, a crafted newer-schema DB
      is refused untouched — each a probe; pack-d/05, /09, /10 unblocked.
- [ ] A pipeline-on dictation world exists so the spoken-symbol matcher output
      and preview-verbatim byte-lock are machine-checked; pack-c/02, /05
      unblocked.
- [ ] The device pre-flight block pairs a real device and reads hub-reachable
      liveness; the iPhone/iPad columns of pack-b/pack-e become walkable (the
      device *verdicts* stay owner-gated).
- [ ] Every new probe/verb is proven on real metal and covered by a
      self-skipping `tests/uat/` test; `dw check holdspeak-uat` green.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSU-3-01 | Mesh dispatch — the handoff arc | done | [story-01](./story-01-mesh-dispatch.md) | [evidence-story-01](./evidence-story-01.md) |
| HSU-3-02 | Cloud-egress card + per-card probe | done | [story-02](./story-02-cloud-egress.md) | [evidence-story-02](./evidence-story-02.md) |
| HSU-3-03 | Trust gate attacks | blocked | [story-03](./story-03-trust-gate-attacks.md) | — |
| HSU-3-04 | Pipeline-on dictation world | backlog | [story-04](./story-04-dictation-pipeline-on.md) | — |
| HSU-3-05 | Device pre-flight block | backlog | [story-05](./story-05-device-preflight.md) | — |

## Where we are

Scaffolded 2026-07-09 after the harness-backlog top three shipped (live
steering — the #1 unlock — plus honest learning-count and the key-never-syncs
attack, all merged and proven live). The re-eval + coverage docs are the input:
`PROTOCOL-COVERAGE.md` §3 is the ranked backlog, and each story below names the
`blocked_on_engine` items it clears and the authored pack scenarios it flips
from human-walked to staged-and-verified. Priority order follows the ranking:
mesh dispatch (the Pack E headline arc) first, then cloud-egress and the trust
attacks (each unblocks 2–3 beats across packs), then the pipeline-on dictation
world, then the device pre-flight (partly manual, owner-gated).

HSU-3-01 shipped 2026-07-09: the `dispatch_run` verb drives a real ask onto
`uat-worker` through the hub's own `/api/ask`, and three probes verify the
return — `run_returned_badged` (scope `mesh`, host `uat-worker`),
`run_claimed_by_worker` (the worker's CLAIM-marker delta + hub provider `mesh`
= "the run moved, the model didn't"), and `run_output_contains` (the worker's
model surfaced `PYLON-CANARY-7`, which only the grounded note carries). The
`mesh-run-on-worker` recipe composes it over the live-worker stage and tears
down clean; pack-e `02`/`03`/`06` now cite it with the treatment leg
machine-verified. Proven live on `.43` (`test_mesh_dispatch.py`, self-skips
without the LAN).

HSU-3-02 shipped 2026-07-09: `egress-cloud-card` uses the product's sync ingress
to stage a deterministic accepted action, then the real aftercare route to
create an unapproved GitHub card. `egress_scope_is` reads the chrome's setup
truth (`local` control → `api.openai.com` treatment), while
`proposal_egress_names_target` reads the per-card `github` target, exact
`acme/holdspeak-uat` repo, and empty execution/result through the meeting
proposal API. The recipe is fully local and probe-first idempotent. Pack D `/07`
and `/11`, plus Pack A `/04`, now use the staged treatment. Next: HSU-3-03
(bounded trust-gate attacks).

**Priority override, 2026-07-09:** this phase is paused. The owner explicitly
declined HSU-3-03's drift/schema/network-hardening work and asked for an
owner-executed functional protocol with strong per-test bootstrap. Active work
moved to [Phase 4](../phase-4-the-owner-functional-pass/current-phase-status.md).
Do not resume HSU-3-03 without a fresh owner decision.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A new verb drives real product side-effects that leak residue (tmux panes, mesh workers, cloud egress) | medium | Every stateful verb tracks what it created and tears it down on run teardown (the steering precedent: `uat-<run>-` sessions, killed on teardown) | A run teardown that leaves a live worker/pane/session |
| A probe asserts a truth the product doesn't actually provide (e.g. per-card egress when the badge is global chrome) | medium | Record the mismatch in the ledger honestly rather than asserting a false truth (re-eval finding); a probe that can't verify fails loudly | A green probe over a capability the code doesn't implement |
| Device pre-flight can't be fully proven without physical glass | high | Build the LAN-bind + pairing-facts + `device_paired` probe; mark the device *verdict* owner-gated, never faked | A device leg marked passed without a device in hand |
| `.43` unreachable stalls the mesh/dictation stories | medium | Degrade to the local path and mark `.43`-blocked beats; the trust + steering stories need no LAN | The whole phase blocked on the LAN |

## Decisions made

| Date | Decision | Reason | Authority |
|---|---|---|---|
| 2026-07-09 | The harness drives the product's OWN routes for every new verb (steering via `/api/coders`, dispatch via `/api/ask`, egress via the proposal routes) — no new product code, no `holdspeak` import | The subprocess boundary is canon; a route rename breaking a verb is a real cross-surface break a failing harness test should catch | owner + agent |
| 2026-07-09 | Remaining backlog is a phase, not a long tail of overnight commits | The owner's call — ground it in stories for a focused pass rather than drift | owner |
| 2026-07-09 | Treat global cloud posture and per-card egress as separate structured truths; probe both | History does expose a real per-proposal badge and exact payload destination, resolving the inventory's mismatch question without inventing product behavior | implementation evidence |

## Decisions deferred

| Decision | Trigger | Default |
|---|---|---|
| Whether device pre-flight schedules into a specific pack or stays a manual runbook | HSU-3-05 | Build the recipe + probe; wire into pack-b/pack-e where the record supports, leave the physical verdict owner-gated |
