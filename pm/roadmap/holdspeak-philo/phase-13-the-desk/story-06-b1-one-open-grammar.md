# PHILO-13-06 - B1 One open grammar

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** done
- **Depends on:** PHILO-13-11's C1 canvas ratified (the material); this story's own canvas ratified; PHILO-13-05 (close means gone)
- **Unblocks:** none
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** B1 (PROPOSAL §3, Wave B); fork 2, "Opens its own window"
- **Closure finding:** `grounding/faces-jobs.md` F3 (`:169`), move 1 (`:152`); `grounding/structure.md` F3 (`:286`), move 2 (`:301`)
- **Canvas:** one, on the C1 material, at 1440 and 393 (the Chair rows and Intelligence BRIEF with their open)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

Every named row he reads opens its object in its own window (the owner's fork 2). Brief → People works.

## Problem

Nothing named on the Chair opens. Brief rows (`web/src/desk/chair/ChairHome.tsx:2130-2140`, `expands={false}`, no open), calendar rows (`ChairHome.tsx:2618-2630`) and commitment rows (only `Done`; `Open` only with a door card's `open_ref`, `ChairHome.tsx:2013-2018`) are read-only. Intelligence BRIEF only selects and shows a raw id (`web/src/desk/pullouts/views/BriefView.tsx:395-401`). "Open person" calls `openSurfaceOr("people", "/people", …)` with a key that dispatches nowhere (`BriefView.tsx:490`; fallback `web/src/desk/shell.ts:93`; wildcard home `web/src/App.tsx:68`; `grounding/probes/structure-person-handoff-output.txt`). J1 is 5 dead taps at 1440, 6 at 393, and works only through the palette (`grounding/faces-jobs.md:19-20`, `:44-58`; shots `grounding/shots/jobs/J1-02-brief-chair-1440.png`, `J1-04-intelligence-brief-1440.png`, `J1-06-today-opened-1440.png`).

## Scope

- **In:**
  - The canvas (UX-CANON A.2): each row kind with its open, at 1440 and 393; Astra checks; the owner ratifies.
  - Brief rows open their `source_ref` through `openPullout` (Chair `ChairHome.tsx:2092-2140`; Intelligence BRIEF `BriefView.tsx:395-401`).
  - Calendar rows open: `project_name` → `openProjectRoom` (`ROOM · <name>` is drawn, `ChairHome.tsx:2624-2628`); a linked person → People at Prep.
  - Commitment rows open their person (`ChairHome.tsx:1990-2030`).
  - Room activity rows open their object.
  - Brief → People: `open-people` with the relationship scope (`BriefView.tsx:490`).
  - The Chair verbs the library Button; the same species in each row.
- **Out:** the 1:1 link itself and Prep's contents (B4); window memory (B2); the Chair as a desk of windows (C1).

## Acceptance criteria

- [ ] Canvas ratified by the owner (his word recorded) before the first face commit.
- [ ] J1 dead taps 5 → 0 at 1440 (6 → 0 at 393); J1 known path 7 → 3 gestures (brief row → the decision; `1:1 Priya` → Priya on Prep), counted on the same populated week as `grounding/faces-jobs.md:9`.
- [ ] J3 prep 5 → 1 gesture from the Chair, on an event linked to the person (the link is B4's; with B4 not merged, the fence links the event through the existing route, `holdspeak/web/routes/people.py:193-204`).
- [ ] Brief → `Open person` opens People on that relationship (red on main: it goes to `/people` and home).
- [ ] Every board built as ratified, at both widths.
- [ ] **Gate (review evidence):** this story's PR merge record cites the owner's ratification record of its canvas (path + his quote); without it the checker refuses the merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** web unit on the row opens per kind; the People dispatch; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** the J1 and J3 walks re-run with the gesture counter of `grounding/probes/faces-jobs-*` at 1440 and 393 (touch).
- **Atlas:** one case per row kind (brief, calendar, commitment, Room activity, Brief → People), at 1440 and 393, one case per `scripts/graph_walk.py run` invocation.
- **Shots:** each open, both widths.

## Worker-brief scars

- **Doubles that lie:** the brief, calendar and people are minted through the real producers (`POST /api/brief/generate`, the ICS ingest conductor, the People routes), as the grounding week was.
- **A verb that does nothing is a lie (A.11):** a row with no object to open shows no open; never a dead tap.

## Effort (not a promise)

Grounding size: S (faces move 1) to M (structure move 2). PROVISIONAL.

## Notes

- 2026-10-01 — B1 and B4 share the J3 prep outcome: B1 owns the open (the row → People at Prep), B4 owns the link and Prep's contents.
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.

## RATIFIED by the owner — 2026-10-03

On the page https://claude.ai/artifact/BfkDkEbuo1day5d1K1DnN3 (the built B1 shots, `assets/story-06-shots/`, on the owner-ratified Workbench material), the owner answered verbatim: **"Ratify, merge it"**. This is the face's ratification record the gate requires (current-phase-status.md §gates).

## Amendment and close — 2026-10-03 (Muad'Dib, visible; the owner may overrule)

Met at 1440: J1 dead taps 5 → **0**, J1 path 7 → **3** gestures, J3 prep 5 → **1**. At 393 the dead taps are **0** but J1 is **12** and J3 prep **4** gestures: every extra tap is moving between Chair windows (one window at a time on the phone), not a row open. That cost is homed to **PHILO-13-17 (C7) the phone desk**, which owns phone window navigation; it is not counted as met here. Astra's single pass (RATIFY-WITH-CONDITIONS: a repeat Prep open stayed on Now) is paid — every person open is a numbered request PeopleCore applies even with an unchanged scope; vitest red → green, glass Prep → Now → reopen red at 1440 → green at both widths.
