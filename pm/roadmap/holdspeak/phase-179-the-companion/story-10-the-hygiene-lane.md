# HS-179-10 — The hygiene lane

- **Project:** holdspeak
- **Phase:** 179
- **Status:** backlog
- **Depends on:** HS-179-07
- **Unblocks:** HS-179-11
- **Owner:** unassigned

## Problem

The dormant HSM track and 174's conditional LAN notification story
leave hygiene items that this phase's tree touches.

## Scope

- In:
  - 174 story-09 (LAN companion notifications): this phase satisfies
    its CONDITIONAL; verify the desktop side is wired and tested.
  - HSM track dormant ledger items: any open items in the HSM track
    that this phase pays (the wake-up story handles the Swift sources;
    this story handles anything else).
  - Items from THE-TUESDAY-ARC.md section 4 that this phase's tree
    touches.
- Out:
  - Hygiene items that belong to other phases.

## Acceptance criteria

- [ ] 174 story-09's conditional is satisfied; the desktop side of
      LAN notifications is tested end-to-end with the companion.
- [ ] Any open HSM track hygiene items are paid or explicitly deferred
      with rationale.
- [ ] Items from THE-TUESDAY-ARC.md section 4 that this phase touches
      are resolved.

## Test plan

- Unit: whatever the hygiene items require.
- Integration: 174 story-09 end-to-end.
- Manual: verification of each item.

## Notes / open questions

- The HSM dormant ledger (memory: project_hsm_ledger.md) should be
  read at charter time to identify any items this phase pays.
