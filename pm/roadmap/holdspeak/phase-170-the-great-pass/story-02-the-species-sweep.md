# HS-170-02 - The species sweep (library-level fixes that lift every face at once; the canon guards made mechanical)

- **Project:** holdspeak
- **Phase:** 170
- **Status:** done
- **Depends on:** HS-170-01
- **Unblocks:** HS-170-03, HS-170-04
- **Owner:** unassigned

## Problem

Most violations are species, not faces: raw buttons, stretched tokens, prose helpers, zero counters, portaled footers, type-step collapse.

## Scope

- **In:** for each violation class in the census, the fix at the library or the shared CSS (never per face): Button everywhere a `<button>` was; token species; the footer's empty-slot law; the type steps; empty states as one line; counters of zero removed; egress chips where fetches happen; the guards added to tests/unit (raw button, zero counter, sentence, accent rail, single-step face) so the canon cannot regress; re-shoot the census after the sweep.
- **Out:** redesigning a face's composition (03+).

## Acceptance criteria

- [x] The violation count per class before/after in the evidence; the guards green on the swept tree.
- [x] The census re-shot; the orchestrator read every PNG.
- [x] Web baseline zero branch-new.

## Test plan

The new guards; `scripts/check_web_baseline.py --run`; the census rig alone.

## Delivered

_(pending)_

## Ledger (2026-09-05)

Three Fable lanes by file ownership — P pages/cores @3dbe8a82, T
thought/threads/project-room + parking @b540dd3a, D desk chrome/pullouts/
chair/voice/surface patterns @bd47897e — then the scanner's own false
positives fixed and the ratchet written.

| class | census (01) | after the sweep | after the scanner fix | ceiling |
|---|---|---|---|---|
| A1 raw `<button>` | 147 | 6 | 4 (allowlisted, reasons in the test) | 4 |
| DS6 accent rail | 8 | 0 | 0 | **0** |
| A9 egress unnamed | 1 | 0 | 0 | **0** |
| emoji | 112 | 21 | 21 | 21 |
| A8 zero counter | 118 | 49 | 28 | 28 |
| raw-ids | 140 | 65 | 20 | 20 |
| A3 prose / sentence | 43 / 12 | 12 / 4 | 12 / 1 | 12 / 1 |
| B raw control | 51 | 34 | 34 (raw textareas + password inputs; flagged `needs redesign (HS-170-04)`) | 34 |
| mic | 35 | 27 | 27 | 27 |
| C type collapse | 4 | 4 | 4 (editor faces) | 4 |
| **total** | **671** | **222** | **151** | — |

The guards: `tests/unit/test_ux_canon_ratchet.py` (ceiling
`tests/ux_canon_ceiling.json`, per rule + per face; lowering is
deliberate via `--write-ceiling`; hard zeros DS6 + A9; A1 allowlist of
four). Evidence: 34 guard tests green; vitest 2184 green, zero
branch-new (5 healed); production build ok; the census rig re-shot
(story 01's evidence). Library: `countToken`/`countLabel`
(`web/src/desk/surface/count.ts`); the retired setup wizard parked under
`web/src/features/project-room/_parked/setup/`.
