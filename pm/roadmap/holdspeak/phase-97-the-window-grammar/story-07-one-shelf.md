# HS-97-07 — One shelf, quiet chrome

- **Project:** holdspeak
- **Phase:** 97
- **Status:** done
- **Depends on:** HS-97-04
- **Unblocks:** HS-97-08, HS-97-09

## Problem

The bottom edge carries four shelf fragments: running-window chips
bottom-left, a Panes pill, a Delivery pill mid-left, and a Desk memory
launcher bottom-right — plus the record orb. An OS has one dock. Above,
the title bars shout: mono eyebrows restate every window's name in a
second vocabulary ("ATTENTION AND RECEIPTS Desk memory", "DAILY COCKPIT
Dictation") against Article VII.1's fewest-words law, and the stage
floor carries instructional prose ("Select an item for actions").

## Scope

- In:
  - one dock: the running-window chips joined by fixed launcher verbs
    for Desk memory, Delivery, and Panes (launch when closed, focus/
    restore when open — running state marked); the fragments' floating
    pills deleted; the dock present whenever the desk is (launchers
    make it non-empty), centered on the bottom edge; compact keeps the
    sheet-friendly ladder;
  - the eyebrow demoted: `DeskWindowFrame` stops rendering the mono
    eyebrow in the head (the prop survives for the dock/AT naming);
    window identity is icon + title;
  - the stage prose removed: the orb's "Select an item for actions"
    line deleted per Article VII.1 (the empty-state teaching of first
    boot is out of scope and untouched);
  - existing walks and tests retargeted where they matched the deleted
    fragments.
- Out:
  - pinned/user-configurable launchers (rider); dock magnification or
    other ornament; core content changes.

## Acceptance criteria

- [x] One dock at the bottom center carries Desk memory, Delivery, and
      Panes as launchers plus a chip per open window; the floating
      pills are gone (grep + shot).
- [x] Launchers open their surface when closed and focus/restore when
      open, with a visible running mark.
- [x] No window head renders a mono eyebrow; the orb prose is gone
      (shots at 1440 and 393).
- [x] Web suite + guards + retargeted walks green.

## Test plan

- vitest dock tests; the walk's shelf leg; `npm run check`; grep
  census for the deleted fragments.

## Evidence required

- Before/after shelf shots (1440 + 393), grep census, walk output.
