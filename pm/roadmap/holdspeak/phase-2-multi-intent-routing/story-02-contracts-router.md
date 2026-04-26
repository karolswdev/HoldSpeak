# HS-2-02 — Step 1: Contracts + router skeleton

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-01 (or directly on HS-1-11 if HS-2-01 is dropped)
- **Unblocks:** HS-2-03, HS-2-04
- **Owner:** unassigned

## Problem

Spec §9.2 introduces the new runtime concepts (`IntentWindow`,
`IntentScore`, `IntentTransition`, `PluginRun`, `ArtifactLineage`) as
typed contracts in `holdspeak/plugins/contracts.py` (extending, not
breaking, the existing surface DIR-01 already shares) and stands up
the empty `Router` interface so later steps have something to wire
into.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.2 + §5.1 + §5.2 — to be detailed when picked up.
- **Out:** Windowing logic (HS-2-03), plugin host (HS-2-04), persistence (HS-2-05).

## Acceptance criteria

- [ ] _TBD when story is picked up; cross-check spec §9.2._

## Test plan

- _TBD when story is picked up._

## Notes / open questions

- Confirm whether `IntentTag` from `holdspeak/plugins/dictation/contracts.py` is reusable for meeting-side `IntentScore`, or whether the meeting side needs its own multi-label type. Spec §5.1 frames `IntentScore` as multi-label (e.g. `architecture=0.81, delivery=0.76`), which is structurally different from DIR-01's single-tag-per-utterance model — likely separate type.
