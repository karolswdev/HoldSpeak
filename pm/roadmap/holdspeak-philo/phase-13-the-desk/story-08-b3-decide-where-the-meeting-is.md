# PHILO-13-08 - B3 Decide where the meeting is

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** PHILO-13-11's C1 canvas ratified (the material); this story's own canvas ratified
- **Unblocks:** none
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** B3 (PROPOSAL §3, Wave B)
- **Closure finding:** `grounding/faces-jobs.md` F9 (`:175`), move 7 (`:158`)
- **Canvas:** one, on the C1 material, at 1440 and 393 (the Decide verb in the meeting record and its inline title)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

He makes a decision from the meeting he is reading, in two gestures, and the decision carries its meeting and project.

## Problem

The meeting record has no decision verb (0 found). The only path is ⌘K `New Decision`, which writes a record titled `New decision` at once; each try leaves one (4 by the end of the walk) (`grounding/faces-jobs.md:67`; `grounding/shots/jobs/J2-03-decision-1440.png`, `-393.png`; `grounding/shots/surfaces/92-pullout-new-decision-pop-1440.png`). The decision window knows nothing of the meeting it came from; the meeting does not show decisions made from it (`grounding/faces-jobs.md:74-75`). `POST /api/decisions` already takes `context_markdown` (`grounding/faces-jobs.md:158`).

## Scope

- **In:**
  - The canvas; Astra checks; the owner ratifies.
  - One `Decide` library Button in the meeting record next to SEND (`web/src/desk/pullouts/MeetingPullout.tsx`, and the Meetings record), which asks the title inline (a well, no modal, A.4) and creates the decision on his confirm, with the meeting as context.
  - The decision carries its meeting and its project; the meeting shows the decisions made from it.
  - No `New decision` placeholder record is created before he names it.
- **Out:** the decision's SEND (C5); decision lifecycle states.

## Acceptance criteria

- [ ] Canvas ratified by the owner (his word recorded) before the first face commit.
- [ ] Decision from an open meeting: 5 → 2 gestures (`Decide`, type + confirm), at 1440 and 393 (touch).
- [ ] 0 orphan `New decision` records after an abandoned try (red on main: one per try).
- [ ] The new decision reads back from the hub with its meeting and its project; the meeting record lists it.
- [ ] **Gate (review evidence):** this story's PR merge record cites the owner's ratification record of its canvas (path + his quote); without it the checker refuses the merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** route/service test that the decision stores its meeting and project refs; web unit on the inline well; `uv run python scripts/check_web_baseline.py --run`.
- **Atlas:** one case (open meeting → Decide → title → the decision with its meeting), at 1440 and 393, one case per `scripts/graph_walk.py run` invocation, with an `.op` sibling reading the stored decision.
- **Shots:** the meeting record with Decide, the inline well, the decision, both widths.

## Worker-brief scars

- **Doubles that lie:** the meeting is minted through the real producer; the fence reads the stored decision from the hub, not the face.
- **Fences that name old words:** fences or atlas cases that expect `New decision` change in the same commit.

## Effort (not a promise)

Grounding size: S (`grounding/faces-jobs.md:158`). PROVISIONAL.

## Notes

- UNKNOWN: whether the desk decision already has a project reference field, or only `context_markdown`. Verify before build; Tenet 1 — no new table if a ref field or context carries it. If a backend change is needed, it is handoff **H-B3**: Astra's lane changes the decision route/service (its files); this story consumes it and edits no backend file.
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
