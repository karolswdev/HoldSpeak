# HS-140-01 — One obvious door

- **Project:** holdspeak
- **Phase:** 140
- **Status:** ready
- **Depends on:** none
- **Unblocks:** 140-02, 140-03, 140-04
- **Owner:** delegated Terra worker; orchestrator adjudicates

## Problem

The canonical first-value composition exists, but a fresh owner reaches the
busy Chair while `FirstWords` is mounted only inside the empty Floor. The first
use presents the whole product before presenting one useful act.

## Scope

- **In:** make `arrival_required` select a first-value state across `DeskApp`
  and `ChairHome`; reuse `FirstWords` and existing onboarding APIs; make
  Dictate one sentence the single primary action; suppress Chair lanes, Ask,
  DeskChrome/Floor navigation, Dock/RecordOrb, launchers, and competing chrome
  only while first value is active; preserve direct recovery surfaces; cover
  1440×900 and 393×900.
- **Out:** new onboarding route/component, new capture path, normal-Chair
  redesign, deletion of advanced features, setup/model changes.

## Acceptance criteria

- [ ] Fresh HOME at `/` renders one Chair first-value composition without a
  detour to the Floor or `/welcome`.
- [ ] “Dictate one sentence” and its speak control are visible without scroll
  at 1440×900 and 393×900.
- [ ] No lane, Ask, Floor, launcher, or record orb competes on glass while
  `arrival_required` is true.
- [ ] The implementation reuses `FirstWords`; there is one capture/receipt path.
- [ ] Existing owners and fresh owners after dismissal/completion receive the
  normal Chair.
- [ ] Reload preserves the server-owned first-value/normal-Chair choice.

## Test plan

- **Web unit:** Desk/Chair arrival-state tests, component identity guard, and
  normal-owner regression.
- **Local browser:** fresh isolated HOME at both widths; no horizontal scroll,
  no console error, one primary action above fold.

## Notes

Do not use a modal. The Chair itself becomes quiet until first value or
Continue later.
