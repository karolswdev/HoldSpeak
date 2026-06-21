# HSM-8-08 — OOM-safe on-device budgeting (never gamble on RAM)

- **Project:** holdspeak-mobile
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HSM-8-04 (on-device generation), HSM-5-02 (Mode A / `LlamaProvider`)
- **Unblocks:** HSM-8-07 (chunking consumes the budget this story computes)
- **Owner:** unassigned

## Problem

On-device generation sizes the model's context with a **hard-coded** `maxTokenCount`
(8K originally, raised to 16K in HSM-8-06). That number is a bet on the device's
memory: the context window drives the **KV-cache**, and the KV-cache is RAM on top of
the ~3.2 GB model. 16K is a safe-ish bump on an 8 GB iPad Air M4 for a single meeting
— but it is still a constant we picked by hand, not a number the device vouches for.
On a smaller device, with the increased-memory entitlement absent, or with WhisperKit
also resident, a fixed 16K could push past the jetsam limit and **OOM-kill the app
mid-generation** — the exact failure the owner said we must never risk: *"Let's not
risk OOM ever."*

This story replaces the hand-picked constant with a **memory-aware budget**: pick the
largest context the *current device* can safely afford, and hand that number to
HSM-8-07 so chunking kicks in whenever a transcript would exceed it. The product stops
gambling on RAM at any meeting length.

## Scope

- **In:** a small, host-testable **budgeting policy** that, from the device's
  available memory, the model's on-disk size, and a safety margin, computes
  (1) the **safe context budget** (`maxTokenCount`) to open the provider with, and
  (2) the **chunk-or-not threshold** HSM-8-07 reads — so the single-context fast path
  is used only when the whole transcript fits the budget, and chunking is used
  otherwise; (3) wire `generate()` to size `LlamaProvider` from the policy instead of
  the hard-coded `contextTokens`, clamped to a sane floor/ceiling; (4) surface a
  one-line honest note when a meeting is large enough to route through chunking ("long
  meeting — extracting in N passes"), so the behavior is legible, not silent.
- **Out:** the chunking mechanism itself (HSM-8-07 — this story only computes *when*
  to chunk and *how big* each context may be). Quantizing the KV-cache or swapping the
  model (Phase 5 territory). The increased-memory entitlement portal work (tracked
  with device deploy). Per-token-exact KV-cache math — a calibrated estimate with a
  conservative margin is the bar, not a perfect model.

## Acceptance criteria

- [ ] A **memory-aware budget** function, pure and host-tested: given (available RAM,
      model size, margin) it returns a context-token budget that leaves a conservative
      headroom over the model + a KV-cache estimate, clamped to a floor (usable) and a
      ceiling (the model's max). Tested across representative inputs (8 GB vs more RAM;
      model present/large) — smaller RAM yields a smaller budget; it never returns a
      budget whose estimated footprint exceeds available RAM minus the margin.
- [ ] **`generate()` opens the provider at the computed budget**, not a hard-coded
      constant — the 16K from HSM-8-06 becomes the *ceiling/default*, lowered when the
      device can't afford it. Structurally asserted (the provider's `maxTokenCount`
      comes from the policy).
- [ ] **The threshold drives chunking**: HSM-8-07 routes to map-reduce exactly when
      the transcript's token estimate exceeds the budget, and uses the single-context
      path otherwise — proven by a unit test pairing the budget with a short and a long
      transcript.
- [ ] **No OOM on device**: on the physical iPad, generation over a long meeting runs
      to completion (via chunking) without a jetsam kill, and a short meeting still
      uses the fast single pass. Owner-witnessed.
- [ ] **Legible, not silent**: when a meeting is large enough to chunk, the
      INTELLIGENCE surface says so in one honest line (no privacy/■ novel — a status,
      per the egress-badge canon).

## Test plan

- Unit (host): the budget function across inputs (low/high RAM, model size, margin) —
  monotonic in RAM, clamped to floor/ceiling, never exceeds RAM−margin; the
  chunk-threshold decision (short → single pass, long → chunk) given a fixed budget.
- Device: confirm the chosen budget on the real iPad (log/inspect the opened context),
  then run a long meeting end to end with no OOM — folded into the HSM-8-07 / HSM-8-05
  device walkthroughs.

## Notes / open questions

- The KV-cache estimate need not be exact — a calibrated linear estimate (per-token
  bytes × context) with a generous safety margin is enough to stay clear of the
  jetsam limit. Bias conservative: under-fill rather than OOM.
- Honors the increased-memory entitlement when present (raises the ceiling) but never
  *requires* it — without the entitlement the budget simply lands lower and chunking
  carries the rest. That is the whole point: correctness is independent of the
  entitlement.
- This is the guardrail that lets HSM-8-06's 16K bump be aggressive *safely*: 16K is
  the ceiling we'd like, the policy lowers it when the device can't pay, and HSM-8-07
  makes any shortfall invisible to the result.
