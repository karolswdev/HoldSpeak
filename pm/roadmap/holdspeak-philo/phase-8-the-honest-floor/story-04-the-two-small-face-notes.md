# PHILO-8-04 - The two small face notes (OPTIONAL)

- **Project:** holdspeak-philo
- **Phase:** 8
- **Status:** backlog
- **Depends on:** the owner keeps one or both notes (Q3); removed if he drops both
- **Unblocks:** PHILO-8-03 (its shots include the kept notes)
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra role (Opus 5.5 stand-in; Codex Astra on return) checks
- **Closure finding:** Phase 7 final summary, THE LEDGER row 13; BACKLOG "PHILO-7-04 follow-ups" rows 1–2 (`pm/roadmap/holdspeak/BACKLOG.md`)
- **Canvas:** none for (a) (a heading removed); the words for (b) are the owner's

## Problem

(a) The decision window draws a CONSEQUENCES heading with nothing under it when no consequences were written (`web/src/desk/pullouts/DecisionPullout.tsx:115`). UX-CANON: no empty labels. (b) On a fresh hub the brief reports the people sections as "unavailable", a word for a state that is only "none yet" (BACKLOG "PHILO-7-04 follow-ups" row 2; the producer line is not yet traced — the story traces it first).

## Scope

- **In:** only the notes the owner keeps: (a) the heading shows only when there is text under it; (b) the brief says the true state for empty people sections, in the owner's words.
- **Out:** any other section of the decision window or the brief.

## Acceptance criteria

- [ ] (a, if kept) A decision with no consequences shows no CONSEQUENCES heading; with consequences, the heading and text show; at 1440 and 393. Red on main.
- [ ] (b, if kept) On a fresh isolated hub, the brief's people sections read the owner's words for "none yet", not "unavailable"; a real failure still reads as a failure. Red on main.

## Effort (not a promise)

PROVISIONAL: 0.5 engineering days for both.

## Test plan

- **Unit:** the pullout render with and without consequences; the brief service's people sections on an empty store.
- **Integration:** a glass shot of each at both widths.

## Notes

- 2026-09-26 — drafted by the Fedaykin docs lane for Muad'Dib; OPTIONAL by the brief; the owner keeps or drops each note at ratification.
