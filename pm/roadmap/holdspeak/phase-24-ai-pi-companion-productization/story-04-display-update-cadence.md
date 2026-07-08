# HS-24-04 — Push/repaint cadence decision

- **Project:** holdspeak
- **Phase:** 24
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The companion display's update cadence (push vs repaint) is undecided; the phase doc calls for a decision plus implementation.

## Scope

- In: cadence decision + implementation on the bridge display path
- Out: work other stories in this phase own.

## Acceptance criteria

- [ ] cadence decided, implemented, and observed live on hardware

## Test plan

- Unit: per the phase's documented commands at pickup.
- Integration / Cypress: n/a until picked up.
- Manual / device: requires the physical AI PI on-site.

## Notes / open questions

Backfilled by HS-86-01 (2026-07-07): this row existed in the phase
table without a story file. Content is taken from the phase status
doc's own description; scope stays a stub until the story is picked
up (hardware-gated per the phase doc).
