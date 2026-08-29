# Phase 150 audit — the Monday-morning walk (before-state)

Opus walk agent, 2026-08-29 (night), real hub through the 149
keystone seam (zero keychain interaction), three seeded reports
(Ewa/Marek/Ola), owned/unowned cards, a linked-able 1:1. Eight
shots in [audit-walk-shots/](./audit-walk-shots/). Companion:
[audit-census.md](./audit-census.md).

## The probe verdicts

- **DELEGATION ("what am I waiting on from Ewa?"): PAINFUL —
  backend-ready, gesture-invisible.** `GET
  /api/follow-through/board?owner=Ewa` answers perfectly (2
  cards); the UI offers ZERO filter/group/search affordances — the
  only path is scanning every card's truncatable fact line for the
  fragment "owner Ewa". Tolerable at 5 cards, impossible at 50.
  People's view shows the INVERSE only (YOU OWE — what the manager
  owes the report).
- **MONDAY ("brief me on my week"): EXISTS BUT PERSON-BLIND.**
  Generate → "2 things changed, 1 thing waiting" —
  Changed/Broke/Waiting/Decisions over anonymous receipts and
  lanes; ZERO person sections, no 1:1 schedule, no stale
  delegations, nothing about the three reports. Persistence
  CONFIRMED on glass (regenerate returns the same id).

## Defects found (fold into the charter)

- **D1 BriefLane absent on first load** (BriefLane.tsx:116 returns
  null with no brief) — the chair shows ZERO Brief presence until
  the owner finds Intelligence and clicks Generate; no prompt.
- **D2 A persisted brief item leaks a raw filesystem path** (the
  SettingsService.update_settings receipt carries the full local
  fixture path into monday_brief_items) — details must be
  summary-level.
- **D3 Wrong-era verbs for person items**: Acknowledge/Defer/Speak
  fit receipts, not people — the manager's verbs are "Follow up" /
  "Add to 1:1 agenda" (the latter EXISTS in People since 138).
- Era-mismatch: the Brief predates 138 AND the 144-148 polish;
  flat rows, no context links, frozen-at-generation by design.

## The joy judgment (verbatim)

"It tells me what changed and what broke, but not what my people
owe me, when our next conversations are, or what I should prepare.
It is a flight-recorder digest, not a chief-of-staff brief."

## Charter inputs

Chips land in cardFacts (DoorBoardLane.tsx:207-221) as clickable
elements over the EXISTING server filter; group-by-person
partitions the columns; per-person Monday sections source from
one_on_one_brief + board-by-owner + the week's linked events
(the door person-index pattern), READ-TIME ONLY.
