# PHILO-8-03 - The atlas cases and the closing proof

- **Project:** holdspeak-philo
- **Phase:** 8
- **Status:** backlog
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
- [ ] The 27 cases of `atlas-phase7.json` still pass; the atlas counts over the named files are reported at the branch commit.
- [ ] Face checks use `readable_text` (visible, in viewport, unobscured), never text containment.
- [ ] The closing rehearsal: two unnamed zones, a rename where he is, a list delete with Undo and without, two deletes in one window, a delete and a face change inside the window, at both widths; the hub read back after each; the owner reviews the shots before merge. Never recorded as a sitting.
- [ ] `final-summary.md` drafted for the close: exits, both checks per story labelled, the reds, the ledger.

## Effort (not a promise)

PROVISIONAL: 0.75–1 engineering days of effort (calibrated from Phase 7's record).

## Test plan

- **Integration:** `scripts/graph_walk.py run --atlas <file> --case <id> --viewport 1440|393 --engine none` for each new case, `--out` under this phase's assets; the Phase 7 atlas re-run.
- **Manual / device:** the owner's review of the shots.

## Notes

- 2026-09-26 — drafted by the Fedaykin docs lane for Muad'Dib from the owner's word closing Phase 7; unratified.
