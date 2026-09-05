# HS-175-01 — The design

- **Project:** holdspeak
- **Phase:** 175
- **Status:** done
- **Depends on:** Phase 171 merged
- **Unblocks:** HS-175-02, HS-175-03, HS-175-04, HS-175-05
- **Owner:** unassigned

## Problem

Every face in 175 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
Calendar and the Clock introduces new face regions (the calendar week
view on the desk, the event-born recording row, the meeting Watch entity
in a Room, the week brief in the shade) and modifies the Monday brief's
frame and the scheduled-recording conductor's face. Without artboards
these cannot be built to canon.

## Scope

- In: artboards at 1440 + 393 for:
  - The calendar week view on the desk (upcoming events as ledger rows;
    the next-event token in the Room; the empty state: "No calendar
    connected" with the 146 adapter verb).
  - The event-born recording row (the armed recording linked to its
    calendar event; the override/cancel verbs; the provenance chip
    naming the calendar source).
  - The meeting Watch entity in a Room (title, date, decisions count,
    commitments count, last-run status; the same entity grammar as
    GitHub PRs and Jira issues).
  - The week brief in the shade (the "This week" frame: meetings
    count, Watch changes, commitments due, next event; the day-level
    detail rows).
  - The `next` seam token (the next event or scheduled recording in
    the Room header or needs-you aggregate).
- Out: implementation; new library species (use existing ones).

## Acceptance criteria

- [ ] Artboards at 1440 + 393 on the ratified shell for every new face
      region (Article IX.2; UX-CANON.md rule E.1).
- [ ] Counsel reads the artboards before the owner (UX-CANON.md rule
      E.1).
- [ ] The owner's word on the canvas (Article IX.4).
- [ ] No prose in the artboards (Article VII.1; UX-CANON.md rule A.3).
- [ ] Every artboard uses at least three type steps (UX-CANON.md rule
      C).
- [ ] The event-born recording artboard shows the recording as ARMED,
      not started (Article IV).

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The calendar week view: does it appear as a section in the Room, a
  section in the shade, or both? Propose both (the Room shows events
  linked to the project; the shade shows all events for the week).
  The owner decides on the canvas.
- The meeting Watch entity shape: does it carry individual decisions
  as child rows or roll them into a count on the meeting row? Propose
  the count (consistency with GitHub PR / Jira issue entity grammar);
  the owner decides.
