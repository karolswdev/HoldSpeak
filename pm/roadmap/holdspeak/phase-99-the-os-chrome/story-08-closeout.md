# HS-99-08 — Closeout: the chrome walk

- **Project:** holdspeak
- **Phase:** 99
- **Status:** done
- **Depends on:** HS-99-01..07
- **Unblocks:** —

## Problem

The claim is "it reads as an OS now." That is only checkable by
walking the assembled chrome on the real hub and looking.

## Scope

- In:
  - a `chrome` walk leg: two-tone bars with edge-flush controls
    asserted on every window kind; the head menu; skinned selects
    (computed `appearance` asserted none) in Settings and Meetings
    filters; the pill scrollbar computed style; the dock underline;
    corners on maximize — shot at 1440 and 393;
  - the assembled chain (95 legs + 97 grammar + 98 surfaces/reflow +
    chrome) green, zero failed API responses;
  - storm within envelope; axe in suite;
  - UAT: feature row + Campaign 13 scenario extended to the chrome;
    ledger + conductor pin;
  - phase close: final-summary, README, memory.
- Out:
  - new features.

## Acceptance criteria

- [ ] Chrome leg green; shots at both viewports LOOKED AT and named.
- [ ] Assembled chain green; storm within envelope; full sweep green.
- [ ] Ledger/campaign updated; final-summary records riders (custom
      select popup, skin switching, dock badges, submenus).

## Test plan

- The full walk chain + chrome leg against a staged hub; storm; `npm
  run check`; full sweep.

## Evidence required

- Walk output, shot inventory, storm numbers, sweep output.
