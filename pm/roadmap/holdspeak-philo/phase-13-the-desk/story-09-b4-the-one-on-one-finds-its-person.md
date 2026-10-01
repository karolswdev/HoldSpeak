# PHILO-13-09 - B4 The 1:1 finds its person

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** the owner's ratification of this charter
- **Unblocks:** PHILO-13-13 (the 1:1 time on the People AppIcon)
- **Owner:** Astra (Luna, xhigh); Muad'Dib checks
- **Lane:** Data + truth (`../wt-philo-13-astra`, `feat/philo-13-astra`)
- **Proposal:** B4 (PROPOSAL §3, Wave B)
- **Closure finding:** `grounding/faces-jobs.md` F10 (`:176`), move 8 (`:159`)
- **Canvas:** none new (Prep's rows reuse the existing People species); any new element goes on the C1 material

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

The calendar 1:1 links to the report it is with, and Prep shows what that report owes him.

## Problem

People says `NEXT 1:1 · No 1:1 planned` while the calendar holds `1:1 Priya / Karol` today and a 1:1 session exists (`grounding/faces-jobs.md:82`; `grounding/shots/jobs/J3-01-priya-now-1440.png`). Prep shows only 2 agenda items, not her open meeting actions (`WAITING ON PRIYA · Send the dry-run report` lives only on the Chair) nor her project (`J3-02-prep-1440.png`). A request accepted becomes **his** commitment (`holdspeak/services/people_service.py:212-214`); nothing records what a report owes him from the 1:1 (`J3-09-follow-up-1440.png`). The link route exists (`holdspeak/web/routes/people.py:193-204`); `Priya` is saved as her alias in the walk (`grounding/faces-jobs.md:159`).

## Scope

- **In:**
  - Suggest the calendar link when an event title holds a report's alias; he confirms once; the link uses the existing route.
  - `NEXT 1:1` reads the linked event.
  - Prep reads the meeting action items whose owner is the alias, and her project, beside the agenda (`web/src/pages/cores/PeopleCore.tsx`, which this lane owns for B4; `PeopleCore.tsx:304`, `:349`).
  - What a report owes him from the 1:1 is recorded as hers, not his.
- **Out:** the Chair row's open (B1); the People store's encryption; the People failure face (A3, through a brief exchange on `PeopleCore.tsx`).

## Acceptance criteria

- [ ] No false `No 1:1 planned`: with a calendar 1:1 linked to Priya, People shows it (red on main, `J3-01`).
- [ ] Prep from the Chair in 1 tap (with B1's open), and Prep lists her agenda, her open meeting actions and her project.
- [ ] A follow-up she owes from the 1:1 reads back from the hub as hers.
- [ ] Each read uses real producers: the ICS ingest conductor, meeting action items with owners, the People routes.

## Test plan

- **Focused:** People service tests for the alias suggestion, `NEXT 1:1` and the Prep read (`HOME=$(mktemp -d) uv run pytest -q <the touched test files>`); a FILE People key in the HOME (`HOLDSPEAK_PEOPLE_KEYSTORE_FILE`), as the grounding did.
- **Atlas:** one case (calendar 1:1 → Prep with her actions), at 1440 and 393 (touch), one case per `scripts/graph_walk.py run` invocation.
- **Shots:** People `Now` and `Prep` on Priya, both widths.

## Worker-brief scars

- **Doubles that lie:** the calendar event comes through the real ICS ingest, the actions through the real meeting producer; never a hand-written row that the producer would not write.
- **No real keychain:** the People key is a FILE key in the run's HOME; never the owner's keychain.

## Effort (not a promise)

Grounding size: M (`grounding/faces-jobs.md:159`). PROVISIONAL.

## Notes

- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
