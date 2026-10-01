# PHILO-13-14 - C4 A palette that knows his week and does verbs

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** PHILO-13-11 (C1 canvas ratified); PHILO-13-15 (C5's push seam, for the `Send …` row)
- **Unblocks:** none
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** C4 (PROPOSAL §3, Wave C)
- **Closure finding:** `grounding/faces-jobs.md` move 3 (`:154`); `grounding/structure.md` move 6 (`:305`); `grounding/faces-surfaces.md` F14 (`:201`); `grounding/faces.md:36` (palette Send)
- **Canvas:** C1's (the palette rows reuse the shelf species); no separate canvas

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

The palette knows his people, the words inside his thoughts and meeting attendees, and offers verbs: `Prep 1:1 with Priya`, `Send <front document> to …`, `Draft update for …`. A `Send …` row only opens the exact preview; he presses Send.

## Problem

`Priya` finds nothing; a word from a thought finds 0 results; `send` returns 16 noise rows (`Slack NOT CONFIGURED`, unrelated programs) (`grounding/faces-jobs.md:114`, `:154`; `grounding/probes/faces-jobs-palette.out.txt`; `grounding/shots/surfaces/52-frame-palette-send-pop-1440.png`). At 393 `People` lists a note first, so Enter opens the note (`grounding/shots/surfaces/110-palette-people-pop-393.png`). Live meeting, Components and Calendar snapshot give "No matching tools" (`grounding/faces-surfaces.md:73`). At 393 one Escape does not close the shelf (`grounding/faces-surfaces.md:73`). `rankRow` already scores `terms` (`web/src/desk/components/DeskToolShelf.tsx:134-145`); contextual rows and the verb registry exist (`DeskToolShelf.tsx:335`, `:345`; `web/src/desk/verbRegistry.ts:606`).

## Scope

- **In:**
  - Feed relationships (`GET /api/people/relationships`), note and thought bodies and meeting attendees into `terms`.
  - Verb rows from the verb registry: `Prep 1:1 with <report>`, `Send <front document> to <destination>`, `Draft update for <project>`.
  - A `Send …` row opens the front document's window with the destination picked and the exact preview in view, through C5's push seam. It never sends (Article V).
  - The query `People` returns the People app first, above the `People & vocabulary` note (today the note ranks first, `grounding/shots/surfaces/110-palette-people-pop-393.png`); one Escape closes the shelf.
- **Out:** a new search index; any send without his press; palette rows for parked or unwalked surfaces.

## Acceptance criteria

- [ ] `Priya` → her window (J3: 4 → 2 gestures).
- [ ] A word inside a thought finds it (J5 find: luck → 2 gestures).
- [ ] `send` → `Send <front document> to <destination>`; picking it opens the preview in view; zero `channel_sends` rows and zero kernel operations until he presses Send.
- [ ] At 393 the query `People` → the People app first, above the `People & vocabulary` note (red on main); one Escape closes the shelf.
- [ ] At 1440 and 393 (touch); the web baseline has zero branch-new failures.
- [ ] **Gate (review evidence):** this story's PR merge record cites the owner's ratification record of the C1 canvas it is built on (path + his quote); without it the checker refuses the merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** web unit on ranking with the new terms and on the verb rows; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** real hub: the three verb rows; the send row's no-send-until-press fence reads the hub's send table.
- **Atlas:** one case per verb row and one find-in-thought case, at 1440 and 393, one case per `scripts/graph_walk.py run` invocation.
- **Shots:** each query, both widths.

## Worker-brief scars

- **Doubles that lie:** people, thoughts and attendees come from the real routes; never a stubbed row list.
- **The receipt under one branch:** after the `Send …` row opens the well, his press shows the outcome the hub records, in every branch.

## Effort (not a promise)

Grounding size: M (`grounding/faces-jobs.md:154`). PROVISIONAL.

## Notes

- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
