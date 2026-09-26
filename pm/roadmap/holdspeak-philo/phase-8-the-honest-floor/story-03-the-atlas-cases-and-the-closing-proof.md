# PHILO-8-03 - The atlas cases and the closing proof

- **Project:** holdspeak-philo
- **Phase:** 8
- **Status:** in-progress
- **Depends on:** PHILO-8-01, PHILO-8-02 (and PHILO-8-04 if kept)
- **Unblocks:** the phase close
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra role (Opus 5.5 stand-in; Codex Astra on return) checks
- **Closure finding:** Phase 7 exit 4's method (`../phase-7-the-desk-on-the-contract/final-summary.md` "The exits")
- **Canvas:** none

## Problem

The repaired faces have no atlas case. The FINDING gives the reproduction steps in the rig's step vocabulary, with two assumptions it did not check: a right-click step and an HTTP-status predicate in `scripts/graph_walk.py` (`docs/internal/philo/phase-7/floor-diag/FINDING.md` "Could not verify"). The owner needs to see the four jobs work at both widths before merge.

## Scope

- **In:** new face cases at 1440 and 393 with `.op` siblings where the outcome is durable; proposed ids (fixed here against `docs/internal/philo/graph/atlas.schema.json`): `case.p8.zone_create.second_unnamed`, `case.p8.zone_rename.chair`, `case.p8.zone_rename.list`, `case.p8.list_delete.gone`, `case.p8.list_delete.undo`, `case.p8.list_delete.long_list_393`, `case.p8.delete_twice.both_gone`, `case.p8.delete_then_leave.gone`; the file (`atlas-phase7.json` or a new `atlas-phase8.json`) decided here; the rig's missing step or predicate added only if a case needs it (else the FINDING's fallback: focus the row and press Shift+F10); the closing rehearsal of the four jobs through the real hub on an isolated HOME at both widths, the shots published for the owner.
- **Out:** any product change (a failing case goes back to its story); cases for faces this phase does not touch.

## Acceptance criteria

- [ ] Every new face case fails on main and passes on the phase branch at 1440 and 393; each `.op` sibling passes headless.
- [x] The 27 cases of `atlas-phase7.json` still pass; the atlas counts over the named files are reported at the branch commit. (All 27 pass on the phase build `b65107f5`, 9 face cases at both widths + 18 `.op`: `assets/story-03-shots/phase7-on-b65107f5/`; counts 148 → 167 in `assets/story-03-proof.md`.)
- [x] Face checks use `readable_text` (visible, in viewport, unobscured), never text containment. (Fenced: `tests/unit/test_philo8_atlas.py::test_face_checks_read_what_is_readable_never_text_containment`. A field's text is its value, so two cases read `input_value` beside `hit_target` (visible, in viewport, unobscured); one absence is `text_absent` beside a `readable_text` — an absence has no readable form.)
- [ ] The closing rehearsal: two unnamed zones, a rename where he is, a list delete with Undo and without, two deletes in one window, a delete and a face change inside the window, at both widths; the hub read back after each; the owner reviews the shots before merge. Never recorded as a sitting.
- [x] `final-summary.md` drafted for the close: exits, both checks per story labelled, the reds, the ledger. (The CLOSED line waits on the owner's word; the #672 and story 03 check rows wait on Codex Astra.)

## Effort (not a promise)

PROVISIONAL: 0.75–1 engineering days of effort (calibrated from Phase 7's record).

## Test plan

- **Integration:** `scripts/graph_walk.py run --atlas <file> --case <id> --viewport 1440|393 --engine none` for each new case, `--out` under this phase's assets; the Phase 7 atlas re-run.
- **Manual / device:** the owner's review of the shots.

## Notes

- 2026-09-26 — drafted by the Fedaykin docs lane for Muad'Dib from the owner's word closing Phase 7; unratified.
- 2026-09-26 — BUILT (Fedaykin, Opus 5.5; branch `feat/philo-8-03-atlas`): `docs/internal/philo/graph/atlas-phase8.json` (a new file: 14 face cases at 1440 and 393, 5 `.op`), the rig 1.5.0 (`button: "right"`, `protocol_reads`, `all_of`, a trigger's `then`), `scripts/philo8_rehearsal.py`, the draft `final-summary.md`. The story's `case.p8.zone_rename.chair` is not a face case (Q2 (c); no face path selects a zone and reaches the Chair; excluded with its reason); `case.p8.chair.no_new_zone` is the Chair's half. On main `267f692a` 27 of 28 new face runs FAIL and 1 is blocked (the two-delete gesture outlasted the window on main at 1440 under load); all 28 PASS on the #672 head `b65107f5`; the delete cases run on merged main after #672 merges, and the owner reviews the rehearsal shots: this story stays in-progress until both. Record: `docs/internal/philo/phase-8/atlas/README.md`, `assets/story-03-proof.md`.
