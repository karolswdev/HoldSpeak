# PHILO-13-16 - C6 Capture from anywhere

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** PHILO-13-11 (C1 canvas ratified)
- **Unblocks:** none
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** C6 (PROPOSAL §3, Wave C)
- **Closure finding:** `grounding/faces-jobs.md` F8 (`:174`), move 10 (`:161`)
- **Canvas:** C1's (the Thought window is an existing face); no separate canvas

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

A global key (a Commodities pop-key) opens a new thought from anywhere; the thought is titled from its first words.

## Problem

To capture a thought he goes back to the Chair, scrolls and presses `Write a thought` (`grounding/faces-jobs.md:110`, `:161`). Every thought is titled `Thought` (`web/src/desk/newThought.ts:29`), so the Chair shows `Thought ×3` and the palette shows 5+ identical rows; at 393 three THOUGHTS-row taps opened workbenches, not the thought (`grounding/faces-jobs.md:114`; `grounding/shots/jobs/J5-01-thought-open-1440.png`, `J5-03-typed-1440.png`).

## Scope

- **In:** one registered verb with a global key (the verb registry) that calls `openNewThought`; the title set from the first line on first save instead of the fixed `Thought` (`newThought.ts:29`); the key shown in the menus (C2's shortcut display).
- **Out:** voice capture itself (the engine is off; A3 owns the failure face); find-in-thought (C4).

## Acceptance criteria

- [ ] A thought in 1 key press from any window, at 1440; at 393 the same verb from the menu (no hardware key assumed).
- [ ] A saved thought's title is its first words; three thoughts show three names on the Chair and in the palette. Red on main (`Thought ×3`).
- [ ] The key does not fire inside a text field that owns it (a fence with focus in an input).

## Test plan

- **Focused:** web unit on the title rule and the verb's key binding; `uv run python scripts/check_web_baseline.py --run`.
- **Atlas:** `case.j11.write_a_thought.window_open` still passes; one new case (key → thought → typed → its title on the Chair), at 1440 and 393 (touch), one case per `scripts/graph_walk.py run` invocation.
- **Shots:** the key from a body window, the titled thoughts, both widths.

## Worker-brief scars

- **Fences that name old words:** fences and atlas predicates that expect the title `Thought` change in the same commit.
- **Doubles that lie:** jsdom lies about focus; the key-in-input fence runs on glass.

## Effort (not a promise)

Grounding size: S (`grounding/faces-jobs.md:161`). PROVISIONAL.

## Notes

- 2026-10-01 — `web/src/desk/newThought.ts` is not named in PROPOSAL §4's map; assigned to this lane (status file, map gaps).
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
