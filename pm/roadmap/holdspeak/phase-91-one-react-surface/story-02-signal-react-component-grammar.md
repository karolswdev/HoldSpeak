# HS-91-02 — Signal React: the DeskOS component grammar

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** HS-91-01
- **Unblocks:** HS-91-03, HS-91-04, HS-91-05, HS-91-06, HS-91-07, HS-91-08
- **Owner:** unassigned

## Problem

Signal exists as tokens, Astro components, page-local CSS, and Desk-specific
React styles. Without one React component grammar, route migration would merely
recreate the same inconsistency in JSX.

## Scope

- In: typed React Button, Field, TextInput, Select/Combobox, Checkbox, Radio/
  ChoiceCard, Switch, Tabs, Disclosure, Dialog, InlineMessage, EmptyState,
  StatusPill, Panel, Toolbar and navigation primitives; React component gallery;
  DeskOS-aligned material/type/spacing/motion; focus and reduced-motion rules.
- Out: route-specific business forms; wholesale palette redesign; fake native
  controls that discard browser semantics.

## Acceptance criteria

- [x] `/design/components` renders React components in every documented state
      and replaces the Astro gallery as the single review surface.
- [x] Components consume `tokens.css` and the July 10 Signal foundation; no
      duplicate control dimensions or variant definitions live in route CSS.
- [x] Primary controls/actions are 44 px; dense subordinate actions are at
      least 36 px; every effective target meets WCAG 2.2 AA minimum.
- [x] Labels, descriptions, errors, live regions, keyboard behavior, focus
      return and reduced-motion behavior have component tests.
- [x] Desk React components adopt or compose these primitives where applicable;
      there is not a “Desk button” and a separate “application button.”
- [x] Visual reference captures demonstrate the DeskOS hierarchy/material
      relationship without claiming browser evidence proves Swift behavior.

## Test plan

- Unit: component interaction and accessibility tests under Vitest.
- Integration: component-gallery Playwright state and keyboard walk.
- Manual / device: side-by-side gallery review with the actual Swift DeskOS.

## Notes / open questions

CSS modules are the default for component internals. Global CSS is reserved for
tokens, reset, typography, and truly shared state/utility contracts.
