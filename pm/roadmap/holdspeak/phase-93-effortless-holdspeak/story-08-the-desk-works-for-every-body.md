# HS-93-08 — The Desk works for every body

- **Project:** holdspeak
- **Phase:** 93
- **Status:** backlog
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

- [ ] Every primary spatial, drag, hold, hover, and gesture action has a named
      keyboard/semantic/VoiceOver equivalent operating on the same record and
      producing the same outcome.
- [ ] Web keyboard-only and native screen-curtain VoiceOver users complete
      create, dictate, record/recover, organize, ground, run, inspect Runs on,
      approve/revoke, inspect Receipt, and return-to-Desk journeys.
- [ ] Reduce Motion stops continuous decorative motion while preserving state;
      Dynamic Type/accessibility text and orientation preserve every label,
      status, recovery action, and target size.
- [ ] A 1,000-item mixed Desk remains searchable, filterable, pageable or
      virtualized, with no silent truncation, stranded object, horizontal
      overflow, or focus loss.
- [ ] Automated axe/semantic/accessibility tests and direct desktop/compact/
      iPhone/iPad captures are attached; simulator and responsive Web remain
      supplementary only.

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
