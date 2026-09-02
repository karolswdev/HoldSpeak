# HS-162-12 — The Memory contract shell: state, consent, parity

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-162-01, HS-162-02, HS-162-03, HS-162-08, HS-162-10
- **Unblocks:** HS-162-13
- **Owner:** unassigned

## Problem

Core Memory is not only a backend. The owner must understand what HoldSpeak
knows, why it was suggested, what is pending, and what Remove/Forget will do.
Waiting for live inference to define these states would bake ambiguity into the
service and make screenshots impressive but dishonest.

## Scope

- **In:** persisted development-only Memory application shell; versioned mock
  service fixtures and typed result schema; genesis/lane/source/claim/review/
  conflict/degraded/removal/empty states; first-run and destination consent;
  disclosure/provenance; canonical deep links; keyboard, screen-reader,
  reduced-motion, range, and compact-layout contracts; 1440×900 and 393×852
  proof capture; visible CF-0 watermark.
- **Out:** real source compilation, inference, owner data, native-phone
  execution authority, production navigation/release, and hard-coded fake state
  outside the development fixture provider.

## Acceptance criteria

- [ ] Shell state survives close/reopen and renders every CF-0 product-state
  fixture from a versioned typed service response, not view-local booleans.
- [ ] Fixtures cover preflight/zero-source, running/paused/crashed/reopened,
  partial/degraded/blocked, unselected and edited review, conflict, correction,
  archive, Remove, Forget, source opening, and typed errors.
- [ ] Consent is specific to purpose/destination/scope, revocable, and
  invalidated when destination or material policy changes; no preselected
  acceptance or dark pattern exists.
- [ ] Every suggestion exposes why, sources, exact scope/time, uncertainty,
  correction, and removal paths using canonical deep links.
- [ ] Keyboard-only and assistive-technology flows have deterministic focus,
  announcements, error association, reduced motion, and normalized parity
  between 1440×900 and 393×852 fixture layouts.
- [ ] The PAR-009 proof matrix is generated from HS-162-10's ratified target
  policies and runtime-adoption states; UI/schema parity never rewrites census
  policy or represents `not_integrated` as available behavior.
- [ ] Every captured frame says `CF-0 fixture — no owner data/model behavior`;
  production bundles cannot register the fixture service or route.

## Test plan

- **Schema/state:** fixture decoder parity and exhaustive legal/illegal state
  transitions; close/reopen persistence; empty preflight and consent invalidation.
- **UI:** component/integration tests, canonical links, keyboard/focus/reader
  walkthrough, reduced motion, text scaling, 1440×900 and 393×852 captures.
- **Fence:** production build/route rejects fixture provider and watermark-free
  capture; no network/model/vector activity occurs in fixtures.

## Notes / open questions

- CF-0 UX/IA/CON/PAR/A11Y/STATE requirements and §§14/18.2 are normative.
- The compact fixture proves responsive/parity grammar, not native-phone
  authority. Native proof remains CF-3/CF-4.
