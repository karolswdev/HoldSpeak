# HS-2-05 — Step 4: Persistence + migration

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-02, HS-2-04
- **Unblocks:** HS-2-06, HS-2-07
- **Owner:** unassigned

## Problem

Spec §9.5 — persist windows, intent labels, plugin runs, and artifact
lineage so synthesis can reconstruct the meeting after the fact and
the web UI can render lineage.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.5 + §6.2.
- **Out:** Synthesis logic (HS-2-07), UI surfacing (HS-2-08).

## Acceptance criteria

- [ ] _TBD when story is picked up._

## Test plan

- _TBD when story is picked up._

## Notes / open questions

- Schema location and storage backend (sqlite under `~/.local/share/holdspeak`?) TBD; cross-check what deferred-intel currently uses to avoid divergence.
