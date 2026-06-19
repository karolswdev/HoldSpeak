# HSM-6-05 — Gate-5 parity closeout

- **Project:** holdspeak-mobile
- **Phase:** 6
- **Status:** backlog
- **Depends on:** HSM-6-01, HSM-6-02, HSM-6-03, HSM-6-04
- **Owner:** unassigned

## Problem

The charter's Track G gate (program Gate 5) is parity with the desktop quality
baseline. This story runs the HSM-6-04 harness on real hardware and records the
verdict — the proof that mobile meeting intelligence is as good as the shipped
product, or an honest finding of where it isn't.

## Scope

- **In:** running the parity harness over the agreed baseline meetings with mobile
  generation on a Tier-1 device, fully local; recording the per-type result and
  the overall parity verdict against the rubric threshold; filing any gap as a
  finding.
- **Out:** building the harness or rubric (HSM-6-04). Fixing a real model-quality
  gap (that's a decision — raise tier / tune prompt / move bar — surfaced to the
  owner, not silently done here). MIR (Phase 7).

## Acceptance criteria

- [ ] The harness runs over the full baseline set with mobile generation on a
      Tier-1 device; the per-type and overall results are recorded in evidence.
- [ ] The verdict states parity met / not-met against the pre-agreed rubric
      threshold — no post-hoc threshold change to pass.
- [ ] Any parity gap is filed as an honest finding (artifact type, size of gap,
      likely cause) rather than hidden.
- [ ] The configuration (device, model tier, engine, contract/prompt versions) is
      recorded so the result is reproducible.

## Test plan

- Manual / device: the full parity run on a Tier-1 device, local; capture the
  harness output.
- Unit: n/a (the gate is the harness run; the harness's own determinism is
  HSM-6-04).

## Notes / open questions

- If parity is missed on a type repeatedly, that's a model/prompt/gate decision
  for the owner (phase deferred decision) — surface it with the harness numbers.
- This closes Phase 6; on pass write `evidence-story-05.md` + `final-summary.md`.
