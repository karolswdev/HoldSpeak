# Phase 3 — The Harness Engine (unlock the live-agent + device tier)

**Last updated:** 2026-07-09 (scaffolded — the remaining harness backlog from
the protocol re-eval, after live steering + honest-count + key-never-syncs
shipped)
**Status:** planning (0/5)

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

- [ ] The mesh handoff arc is machine-staged: a desk-ask driven onto the
      `uat-worker` returns badged `⇄ mesh` with worker-log-claims-it /
      hub-shows-no-model-load provenance; pack-e's handoff beats verdicted.
- [ ] A cloud-egress card is staged and its egress target read back through a
      probe (or the badge-is-chrome-global mismatch is recorded honestly);
      pack-d/07, pack-d/11, pack-a/04 unblocked.
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
| HSU-3-01 | Mesh dispatch — the handoff arc | backlog | [story-01](./story-01-mesh-dispatch.md) | — |
| HSU-3-02 | Cloud-egress card + per-card probe | backlog | [story-02](./story-02-cloud-egress.md) | — |
| HSU-3-03 | Trust gate attacks | backlog | [story-03](./story-03-trust-gate-attacks.md) | — |
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
world, then the device pre-flight (partly manual, owner-gated). Next: HSU-3-01.

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

## Decisions deferred

| Decision | Trigger | Default |
|---|---|---|
| Whether per-card egress is asserted or the chrome-global badge mismatch is recorded | HSU-3-02 implementation | Probe the real read surface; if the product's badge is global, record the mismatch in the ledger, don't assert a per-card truth |
| Whether device pre-flight schedules into a specific pack or stays a manual runbook | HSU-3-05 | Build the recipe + probe; wire into pack-b/pack-e where the record supports, leave the physical verdict owner-gated |
