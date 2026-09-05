# HS-180-01 — The measured week

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** Phase 179 merged
- **Unblocks:** HS-180-06, HS-180-07, HS-180-08
- **Owner:** unassigned

## Problem

The arc's thesis -- "will you use this on a Tuesday?" -- can only be
proved by a measured week of real use. Not a walk, not a demo, not a
test: a week where HoldSpeak is the tool he reaches for. Per face,
per day: did he use it, did it help, did it break, did he turn it off.

## Scope

- In:
  - Seven consecutive days of real use on his real desk with his real
    projects, his real team, his real meetings.
  - A daily journal entry (structured or freeform, his choice): which
    faces he used, what helped, what broke, what he turned off.
  - Per-face verdict at the end of the week: USED / HELPED / BROKE /
    OFF / NEVER OPENED -- verbatim.
  - The verdicts cover every face shipped through the arc: the Door,
    the Room, the Portfolio, the Concierge, the Heartbeat (shade,
    notifications, dock badge, brief), the Loop (decisions,
    commitments, 1:1 prep), the Steward (updates, nudges, health
    signals), Reach (the .43 runner, the third connector), the
    Calendar, Speak, the Thread, the Companion.
  - The journal and verdicts are filed as evidence.
- Out:
  - Bug fixes during the week (filed as observations, not fixed
    mid-measurement).
  - New features.
  - Automated UAT campaigns (those are separate; this story is the
    owner's subjective experience).

## Acceptance criteria

- [ ] Seven consecutive days of real use documented (Article IX.1 --
      it ran on real hub, real mic, real model, real device, real
      viewport).
- [ ] Per-face verdict recorded verbatim for every face shipped
      through the arc (Article IX.4 -- the owner's live verdict
      outranks every green suite).
- [ ] The journal and verdicts filed as evidence in the phase folder.

## Test plan

- Unit: n/a.
- Integration: n/a.
- Manual: the owner's week; the journal; the verdicts.

## Notes / open questions

- The journal format is the owner's choice. A structured template
  (face / used? / helped? / broke? / notes) is proposed; he may prefer
  freeform.
- "NEVER OPENED" is an honest verdict and a valuable data point.
