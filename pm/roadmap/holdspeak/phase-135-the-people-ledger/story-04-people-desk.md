# HSEGHS001HS104-135-04 — People belongs on the Desk

- **Project:** holdspeak
- **Phase:** 135
- **Status:** ready
- **Depends on:** 135-01, 135-02, 135-03
- **Unblocks:** 135-06
- **Owner:** delegated Terra worker; primary adjudicates

## Problem

People must feel native to HoldSpeak's Desk and expose trust state at contact. A
standalone page, modal workflow, or literal desktop object per person would violate
the product ontology.

## Scope

- **In:** singleton local People primitive/surface; readiness states; responsive
  roster + relationship detail; Now/1:1s/Info lenses; in-world editors; explicit
  request acceptance; Follow-through handoff; trust facts; accessible keyboard/focus.
- **Out:** feature page, modal, person tiles, recording/model controls, growth/
  feedback dashboards, scores/traffic lights/risk ordering, custom phone shell.

## Acceptance criteria

- [ ] People opens as one Desk region. Unconfigured/locked/key-unavailable/corrupt
  never render roster/create/search/mic or stale cached People text.
- [ ] Ready state displays exactly factual `Encrypted`, `This device only`, `Notes
  only`; `shared_intent` copy does not imply participant access.
- [ ] Inline create/edit, agenda visibility/roll-forward, request acceptance, and
  commitment handoff work without a modal or route transition.
- [ ] Desktop split and narrow back-navigation have no horizontal overflow; controls
  use native labels/focus and do not encode state only by color.

## Test plan

- **Unit/web:** primitive registry, surface window, readiness clearing, PeopleCore
  interactions, no forbidden UI strings/controls.
- **Integration:** API client state/error mapping.
- **Manual/device:** desktop + iPhone-browser screenshots and keyboard walk.
