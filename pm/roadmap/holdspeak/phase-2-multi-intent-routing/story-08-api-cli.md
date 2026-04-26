# HS-2-08 — Step 7: API + CLI surfaces

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-05, HS-2-06, HS-2-07
- **Unblocks:** HS-2-09
- **Owner:** unassigned

## Problem

Spec §9.8 — expose introspection + manual-override surfaces (web API
+ `holdspeak` CLI subcommand) for window state, intent transitions,
plugin runs, and lineage. DoD §11 item 7 requires the web UI surface
this story underwrites.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.8 + §6.3.
- **Out:** Feature-flag plumbing (HS-2-09); observability counters (HS-2-10).

## Acceptance criteria

- [ ] _TBD when story is picked up._

## Test plan

- _TBD when story is picked up._

## Notes / open questions

- CLI shape: mirror `holdspeak dictation …` from HS-1-08 (subcommands `runtime status`, `windows ls`, `windows show`, etc.). Web-side surface depends on web-flagship-runtime progress.
