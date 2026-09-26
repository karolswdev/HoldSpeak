# PHILO-8-01 - The zone name and the rename where he is

- **Project:** holdspeak-philo
- **Phase:** 8
- **Status:** in-progress
- **Depends on:** the owner's ratification of the charter and his answer to Q1; the face build depends on the canvas ratification (Q2)
- **Unblocks:** PHILO-8-03
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra role (Opus 5.5 stand-in; Codex Astra on return) checks
- **Closure finding:** Phase 7 final summary, THE LEDGER rows 1–2; `docs/internal/philo/phase-7/floor-diag/FINDING.md` Finding 1 and S1; BACKLOG "PHILO-7-03 follow-ups" row 2; `checks/charter-astra-role-r1.md` F4–F6 and RULING (3)
- **Canvas:** the default name none if Q1 = (a); the rename on the Chair and the list a SMALL CANVAS at 1440 and 393, ratified by the owner before build

## Problem

New Zone always posts `{name: "New zone"}` (`web/src/desk/store/dataSlice.ts:322`), and a live zone name must be unique, ignoring case (`holdspeak/operations.py:655`). After the store makes a zone it sets `renamingZoneId` (`dataSlice.ts:370`), but only the spatial Floor draws the rename field (`web/src/desk/gl/WorldStage.tsx:206-207`, `:271-280`, `:400`), and it mounts only on the spatial Floor (`web/src/desk/DeskApp.tsx:192-206`). So on the Chair (the default face) and on the list (the default at 393 when the desk holds more than 16 objects, `web/src/desk/store/types.ts:65-72`) the zone is made and nothing shows. Then every further New Zone, on every face, answers `409 zone_name_taken`, and Retry fails the same way (FINDING S1). The stale field appears later on another face and takes focus (FINDING Finding 1). The same dead path holds for the F2 Rename key: `object.rename` sets `renamingZoneId` for a zone (`web/src/desk/verbRegistry.ts:502`), and on a face without `WorldStage` nothing draws the field (`checks/charter-astra-role-r1.md` F6).

## Scope

- **In:**
  - **The free default name (Q1 (a) unless the owner objects).** The store picks the next free "New zone N" from the zones it holds, inside `createPrimitive`. The rule that decides "free" matches the hub's name rule IN FULL: strip, collapse whitespace, NFC, casefold (`holdspeak/db/primitives.py:60-68`, `normalize_zone_name`). A name the caller passed (`overrides.name`) is never replaced; a zone the owner named "New zone 2" himself is his, and the picker skips it. After a `409 zone_name_taken`, Retry refreshes the store BEFORE it picks again (today Retry re-calls `createPrimitive` over the same store, `web/src/desk/store/dataSlice.ts:339`, so a stale store would post the same name). The ruling (`checks/charter-astra-role-r1.md` RULING (3)): the store-side free name is the smallest lawful fix; a hub-side fix (the hub picks the name) changes a declared contract (the `operations.py` descriptor and its refusal, the generated docs, the MCP args schema) and is rejected under Tenet 1.
  - **The rename where the owner is**, as the ratified canvas shows it (Q2), composing the spatial field's behaviour (Enter commits, blur commits, Escape cancels) rather than copying it. It hangs off `renamingZoneId`, not off the New Zone verb, so it covers both New Zone and the F2 Rename key (`verbRegistry.ts:502`) on every face that offers them.
  - The rename state cleared when the face changes, so it never comes up on another face.
- **Out:** the hub's uniqueness rule; the zone's position on the Floor; the clipped field width at 1440 ("ew zone", FINDING, not examined) unless the canvas's field is the same element; any other create verb's default name.

## Acceptance criteria

- [ ] The canvas: the rename on the Chair and on the list at 1440 and 393, composed from library species, ratified by the owner before the face build (UX-CANON §A.2). If the owner picks "the Chair does not offer New Zone" (Q2 c), the verb is withheld on the Chair and the fence proves it is absent there.
- [ ] Two New Zone presses in a row with no rename between make two zones on the Chair, the list and the spatial Floor at both widths; zero `409 zone_name_taken` in the network log; the second name is as Q1 rules. Red on main (the 409).
- [ ] New Zone on the Chair and the list opens the rename with focus, as ratified; Enter writes the name (`GET /api/directories` shows it); Escape keeps the default name and closes the field.
- [ ] After a New Zone on one face and a change of face without a rename, no rename field appears on the new face (the FINDING rows "Chair, then go to the Floor" and "Floor list → Spatial view" are red on main).
- [ ] The rename field is one implementation: `grep` finds one Enter/blur/Escape commit path for zone rename.
- [ ] The free-name rule matches `normalize_zone_name`: a zone named "  new   ZONE " counts as taken for "New zone".
- [ ] `createPrimitive("zone", {name: "X"})` posts "X" unchanged.
- [ ] A 409 from a zone made outside the store (by MCP or another tab, not yet refreshed): Retry refreshes, picks the next free name, and succeeds.
- [ ] The F2 Rename key on a selected zone opens the same rename on each face that offers it (the list; the Chair if Q2 keeps New Zone there), or is greyed with its reason where the face shows no zone (the Chair: `Open the Floor`; the Astra-role check r1 F7).
- [ ] Shots at 1440 and 393 beside the canvas artboards.

## Effort (not a promise)

PROVISIONAL: 0.75–1.25 engineering days of effort, plus the canvas and the owner's word (calibrated from Phase 7's record, `checks/charter-astra-role-r1.md` F11).

## Test plan

- **Unit (vitest):** the free-name choice (none, "New zone", case and whitespace variants per `normalize_zone_name`, "New zone 2" taken); an explicit `overrides.name` never replaced; Retry refreshes the store after a 409; the rename state cleared on a face change; F2 Rename sets the same rename state.
- **Integration (glass, the real hub, isolated HOME):** the FINDING's reproduction steps at 1440 and 393 on the Chair, the list and the spatial Floor; two New Zone in sequence.
- **Web baseline:** `uv run python scripts/check_web_baseline.py --run`, zero branch-new; every `scripts/philo_*.py --check` exits 0 before push (handover XXIX law 3).

## Notes

- 2026-09-26 — drafted by the Fedaykin docs lane for Muad'Dib from the owner's word closing Phase 7; unratified.
- 2026-09-26 — round two: the Astra-role check (`checks/charter-astra-role-r1.md`) paid: C3 the free name matches the hub's rule in full, never replaces a passed name, and Retry refreshes after a 409 (the store-side fix ruled the smallest lawful one); C4 the rename covers the F2 Rename key.
- 2026-09-26 — half A BUILT (Fedaykin, Opus 5.5; branch `feat/philo-8-01-zone-name`): the free name (`web/src/desk/zoneName.ts`; `createPrimitive` in `web/src/desk/store/dataSlice.ts` — a caller's name is never replaced, a name in flight counts as taken, Retry refreshes before it picks); the Chair withholds New Zone (`Verb.needsZones`, `offeredHere()` in `web/src/desk/verbRegistry.ts`, honoured by `DeskToolShelf.tsx` and `DeskMenuBar.tsx`); F2 on a zone ghosts `Open the Floor` on the Chair; a face change clears `renamingZoneId` and a create landing after a face change opens no rename (`web/src/desk/DeskApp.tsx`); ONE rename behaviour `web/src/desk/hooks/useZoneRenameField.ts` (the Floor overlay composes it). Fences: `tests/e2e/test_philo8_01_zone_name_glass.py` (12, real hub, 1440 + 393; 10 red on main), `store/__tests__/zoneFreeName.test.ts`, `__tests__/philo801ZoneVerbs.test.ts`, `DeskApp.test.tsx` (8 red on main); the runs in `assets/story-01-half-a-proof.md`. Found on the way: the post-create refresh takes about 4.7 s on the isolated rig at 1440, so a second New Zone inside it read a stale store and still 409'd — paid by the in-flight name set. The list's in-row field: canvas `assets/story-01-canvas/README.md` (12 live boards at 1440 and 393, three questions); NOT built until the owner ratifies it.
- 2026-09-26 — round two: the Astra-role check on PR #671 (`checks/story-01-built-astra-role-r1.md`, RATIFY-WITH-CONDITIONS) paid: C1 the list-to-spatial fence waits for the create to land, red on true main 26f7b005 under parallel load (`assets/story-01-half-a-proof.md`); C2 origin/main merged; C3 board 7 re-shot after a reload, captioned (the Chair search still lists zones to open); C4 Limits quote `17 SHOWNS OF 17` and name the raw sort-header buttons, BACKLOG "PHILO-8-01 follow-ups"; C5 the refusal chip on its own line in a slot that adds no column width (columns measured still), the selection recorded; C6 the failed-rename line in Limits and fences; AC F2 wording "greyed with its reason"; boards 8–10 added for the MISSED states (long name, spaces only, two fast presses).
