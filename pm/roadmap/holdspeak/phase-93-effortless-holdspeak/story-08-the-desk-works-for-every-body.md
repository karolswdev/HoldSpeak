# HS-93-08 — The Desk works for every body

- **Project:** holdspeak
- **Phase:** 93
- **Status:** done
- **Depends on:** HS-93-03, HS-93-04, HS-93-05, HS-93-06, HS-93-07
- **Unblocks:** HS-93-09
- **Owner:** unassigned

## Problem

The Desk's spatial craft is a strength, but pointer, gesture, motion, and small
datasets cannot be assumed. Accessibility must preserve the same product power,
not route users to a reduced administrative substitute.

## Scope

- **In:** Web semantic list/tree mode, deterministic focus and keyboard actions,
  compact layout, pagination/virtualization/search; Swift semantic list/actions,
  screen-curtain VoiceOver, Dynamic Type, Reduce Motion, orientation; named
  alternatives to drag/hold/gesture; 1,000-item scale; create, organize, run,
  approve, recover, receipt, and return journeys.
- **Out:** Removing the spatial Desk, disabling platform-native delight for all
  users, or treating automated accessibility scans as device acceptance.
- **Paths:** projection/page APIs, Web Desk world/object/chrome/drawer/styles and
  tests, Swift DeskHome/Diorama/Queue/accessibility settings and tests, Web UI
  audit, physical-device UAT.

## Acceptance criteria

- [x] Every primary spatial action has a named keyboard/semantic equivalent
      operating on the same record: the List view is the same Desk as an
      accessible table (open, select-for-Ask, dive, surface all proven to hit
      the identical store records the spatial gestures hit), the Create menu
      and Tools shelf are fully keyboard-driven, and desk windows carry
      keyboard-reachable close affordances.
- [x] Keyboard-only Web completes create, find/open, select-and-ask, dive,
      and Desk-memory journeys (the HS-93-01 keyboard walk plus List-view
      parity tests); the native screen-curtain VoiceOver journeys are
      candidate-Y scope.
- [x] Reduce Motion stops continuous decorative motion while preserving
      state: the consolidated prefers-reduced-motion block covers the float,
      ring, pulse, print, and thinking animations, and the window entrance
      springs honor useReducedMotion; physical Dynamic Type and orientation
      walks are candidate-Y scope.
- [x] A 1,000-item mixed Desk remains searchable, pageable, and operable:
      the spatial stage bounds rendering at 200 floaters with an honest
      role=status count chip, the List view pages by 100 with focus
      preserved, Tools search finds any record, and the production scale
      runner proves it end to end with zero failed APIs.
- [x] Automated semantic accessibility assertions (named table, column
      headers, labeled checkboxes, status roles, aria-pressed persistence)
      and desktop production captures are attached; direct physical
      iPhone/iPad captures are candidate-Y scope.

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the physical iPhone/iPad VoiceOver screen-curtain, Dynamic Type, Reduce
Motion, and orientation walks move verbatim to
[BACKLOG candidate Y](../BACKLOG.md) and are not claimed here.

## Test plan

- **Unit:** focus/action equivalence, list/search/page/virtualization, motion and
  accessibility-state tests in Vitest and Swift.
- **Integration:** projection and object pagination, 1,000-item seed, Web UI
  audit, and UAT action-equivalence scenarios.
- **Manual / device:** Keyboard-only Web plus physical iPhone/iPad VoiceOver
  screen-curtain, Dynamic Type, Reduce Motion, compact/wide/orientation walks.

## Notes / open questions

Semantic mode is another expression of the Desk, not a second dashboard. Shared
identity, actions, attention, and results are mandatory.

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.
