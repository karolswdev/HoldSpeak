# PHILO-13-18 - C8 The 12 px floor

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** done
- **Depends on:** PHILO-13-11 (C1 canvas ratified: the type tokens sit in the material)
- **Unblocks:** none
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** C8 (PROPOSAL §3, Wave C)
- **Closure finding:** `grounding/faces-surfaces.md` F9 (`:196`), §3b (`:177`); `grounding/checks/proposal-astra.md` MISSED 1
- **Canvas:** C1's (the type tokens); no separate canvas

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

No readable text under 12 px anywhere on the Desk: the type tokens carry the floor, and every declaration rides the tokens.

## Problem

The 12 px floor (ruled 2026-09-21) is broken on 25 of the walked faces: captions and meta at 10–11 px nearly everywhere, 9 px in Speak, Ask, Components and Change places. There are 157 hard-coded `font-size` declarations of 9–11 px under `web/src/desk` (e.g. `web/src/desk/chair/chair.css:126`, `:167`, `:178`) (`grounding/faces-surfaces.md:177`, `:196`). Setup has 32 text nodes at 10 px; Change places 28 at 9–11 px (`grounding/faces-surfaces.md:33`, `:47`).

## Scope

- **In:** the type tokens carry a 12 px minimum; the 157 declarations under `web/src/desk` move onto the tokens; any other walked face below 12 px (the 25 faces) moves onto them too. All CSS (this lane owns it).
- **Out:** layout redesign of bodies (C1 sets the material; bodies are not redesigned here); non-text glyph sizes.

## Acceptance criteria

- [ ] Zero readable text under 12 px on a full-surface scan at 1440 and at 393, over the populated week (the `audit.small` probe of `grounding/faces-surfaces.md:13`).
- [ ] Zero hard-coded `font-size` under 12 px under `web/src/desk` (a static fence; red on main: 157).
- [ ] No text clips or overflows its window at either width after the move (the shots).
- [ ] **Gate (review evidence):** this story's PR merge record cites the owner's ratification record of the C1 canvas it is built on (path + his quote); without it the checker refuses the merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** the static font-size fence; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** the full-surface scan at 1440 and 393 (touch), every walked surface.
- **Atlas:** the Chair arrival case and one case per daily window (Intelligence, Speak, Meetings, People, the Room), at 1440 and 393, one case per `scripts/graph_walk.py run` invocation.
- **Shots:** the 25 faces, both widths.

## Worker-brief scars

- **Never rewrite a guard to match a removal:** the static fence is new; no existing typography fence is loosened to pass.
- **Fix the species once:** a size in a species is fixed in the library (`web/src/desk/surface/surface.css`), not per face.

## Effort (not a promise)

Grounding size: not sized as one move (157 declarations, 25 faces). PROVISIONAL.

## Notes

- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.

## Closed — 2026-10-03

Readable text under 12 px: 269 declarations → 0 (14 explicit, fenced glyph exemptions — icons, image-only mics, carets — UX-CANON's nontext rule); on glass 525 / 196 small texts at 1440 / 393 → 0, with zero clipped and zero overlapping text across 29 / 27 states (Chair windows, all Dock apps and wings, the meeting record, People, the Room, the Workbench, the decision window). Also paid here: the library editor wraps long lines (the B5 finding), the 393 strip menu's Escape closes only the menu, the Workbench raw buttons and the EgressChip are library Buttons, AgentAvatar no longer draws a hex colour over the name. **Muad'Dib's rulings:** the opt-in `on_glass` mode of the readable reader (scrolled-to content is not "clipped") accepted, the default reader unchanged; the 14 glyph exemptions accepted. The bundle byte budget is gone (owner ruling 2026-10-03). Capture `evidence-story-18.md` (140 passed; web baseline zero branch-new).
