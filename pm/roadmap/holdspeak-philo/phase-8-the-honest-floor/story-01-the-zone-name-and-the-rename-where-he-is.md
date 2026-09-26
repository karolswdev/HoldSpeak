# PHILO-8-01 - The zone name and the rename where he is

- **Project:** holdspeak-philo
- **Phase:** 8
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter and his answer to Q1; the face build depends on the canvas ratification (Q2)
- **Unblocks:** PHILO-8-03
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra role (Opus 5.5 stand-in; Codex Astra on return) checks
- **Closure finding:** Phase 7 final summary, THE LEDGER rows 1–2; `docs/internal/philo/phase-7/floor-diag/FINDING.md` Finding 1 and S1; BACKLOG "PHILO-7-03 follow-ups" row 2
- **Canvas:** the default name none if Q1 = (a); the rename on the Chair and the list a SMALL CANVAS at 1440 and 393, ratified by the owner before build

## Problem

New Zone always posts `{name: "New zone"}` (`web/src/desk/store/dataSlice.ts:322`), and a live zone name must be unique, ignoring case (`holdspeak/operations.py:655`). After the store makes a zone it sets `renamingZoneId` (`dataSlice.ts:370`), but only the spatial Floor draws the rename field (`web/src/desk/gl/WorldStage.tsx:206-207`, `:271-280`, `:400`), and it mounts only on the spatial Floor (`web/src/desk/DeskApp.tsx:192-206`). So on the Chair (the default face) and on the list (the default at 393 when the desk holds more than 16 objects, `web/src/desk/store/types.ts:65-72`) the zone is made and nothing shows. Then every further New Zone, on every face, answers `409 zone_name_taken`, and Retry fails the same way (FINDING S1). The stale field appears later on another face and takes focus (FINDING Finding 1).

## Scope

- **In:** the default name as the owner rules Q1 (recommended: the store picks the next free "New zone N" from the zones it holds, ignoring case, inside `createPrimitive`, so Retry picks again); the rename where the owner is, on the Chair and the list, as the ratified canvas shows it, composing the spatial field's behaviour (Enter commits, blur commits, Escape cancels) rather than copying it; the rename state cleared when the face changes, so it never comes up on another face.
- **Out:** the hub's uniqueness rule; the zone's position on the Floor; the clipped field width at 1440 ("ew zone", FINDING, not examined) unless the canvas's field is the same element; any other create verb's default name.

## Acceptance criteria

- [ ] The canvas: the rename on the Chair and on the list at 1440 and 393, composed from library species, ratified by the owner before the face build (UX-CANON §A.2). If the owner picks "the Chair does not offer New Zone" (Q2 c), the verb is withheld on the Chair and the fence proves it is absent there.
- [ ] Two New Zone presses in a row with no rename between make two zones on the Chair, the list and the spatial Floor at both widths; zero `409 zone_name_taken` in the network log; the second name is as Q1 rules. Red on main (the 409).
- [ ] New Zone on the Chair and the list opens the rename with focus, as ratified; Enter writes the name (`GET /api/directories` shows it); Escape keeps the default name and closes the field.
- [ ] After a New Zone on one face and a change of face without a rename, no rename field appears on the new face (the FINDING rows "Chair, then go to the Floor" and "Floor list → Spatial view" are red on main).
- [ ] The rename field is one implementation: `grep` finds one Enter/blur/Escape commit path for zone rename.
- [ ] A 409 from a real name clash (a zone the owner named "New zone 2" himself, then New Zone twice) still ends in two zones or the existing named failure row with a Retry that succeeds.
- [ ] Shots at 1440 and 393 beside the canvas artboards.

## Effort (not a promise)

PROVISIONAL: 1–1.5 engineering days, plus the canvas and the owner's word (0.5 d in the phase estimate).

## Test plan

- **Unit (vitest):** the free-name choice (none, "New zone", "new zone" case, "New zone 2" taken); the rename state cleared on a face change.
- **Integration (glass, the real hub, isolated HOME):** the FINDING's reproduction steps at 1440 and 393 on the Chair, the list and the spatial Floor; two New Zone in sequence.
- **Web baseline:** `uv run python scripts/check_web_baseline.py --run`, zero branch-new; every `scripts/philo_*.py --check` exits 0 before push (handover XXIX law 3).

## Notes

- 2026-09-26 — drafted by the Fedaykin docs lane for Muad'Dib from the owner's word closing Phase 7; unratified.
