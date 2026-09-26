# Phase 8 — The Honest Floor — final summary

<!-- owner word pending -->
**CLOSED — (the owner's word is pending).** This is the DRAFT for the close, written by the PHILO-8-03 lane (Fedaykin, Opus 5.5) for Muad'Dib. The closing line goes here in the Phase 7 form ("CLOSED <date> on the owner's word (<his words>): rehearsed, owner-reviewed; not a sitting") only after the owner reviews the rehearsal shots.

**Status: stories 01 and 04 merged (#671 `808a9c30`, #673 `ce772ef9`; #669 `26f7b005`); story 02 is PR #672 (`feat/philo-8-02-one-delete` @ `b65107f5`), under Codex Astra's check; story 03 is this PR.** Exits 1, 2 and 7 are flipped in `current-phase-status.md`. Exits 3–6 wait on #672's merge and on the owner's review of the shots (the table below). No sitting is claimed. The owner has not used this on his own desk.

## What he can do now that he could not on 2026-09-26 morning

- **Make a second zone, and a third.** New Zone names the next free default ("New zone 2", "New zone 3", …) by the hub's own rule; a name he typed is never replaced (story 01 half A; `web/src/desk/zoneName.ts`). On main before this phase the second New Zone answered `409 zone_name_taken` on every face (FINDING S1).
- **Name a zone where he is.** On the list, New Zone opens the name field in the new zone's row, with the name selected; Enter writes it; F2 on a focused zone row opens the same field (story 01 half B; the canvas the owner ratified, "Ratify as drawn").
- **See why a name was refused.** A taken name shows the library chip `✗ NAME TAKEN` under the field, on the list and on the Floor; a failed save shows `✗ NOT SAVED`; a refusal after the field closed goes to the write receipt with Retry.
- **Not be offered a verb that cannot work.** The Chair does not offer New Zone (Q2 (c)); F2 on a zone on the Chair is greyed `Open the Floor`; Delete on the Chair is greyed `Open the Floor or the list` (story 02 round two, PR #672).
- **Delete from the list, with Undo** — WHEN #672 MERGES. The row menu, the Delete key and the palette's Delete remove the object with the Floor's receipt ("Removed … Undo", then "Removal committed"), readable at both widths, and on a long list scrolled to its end at 393.
- **Delete twice in one window, or leave the face inside it, and lose nothing** — WHEN #672 MERGES. The first delete commits when the second is queued; a face change commits a pending delete; the deleted object leaves the selection.
- **Read a decision without empty headings.** "Decision context", "Decision" and "Consequences" draw only with text under them (story 04 (a)).

### Measured against the Seven Tenets

| Tenet | How this phase meets it | Where it falls short |
|---|---|---|
| 1 No over-engineering for safety | Each repair uses an idiom that existed: the store's create, one rename hook, one undo receipt hook, one delete listener. The hub's name rule is unchanged. The rig gained two predicates, one click option and a trigger's `then`; no new mode. | The atlas grew by 19 cases for four defects; the rehearsal driver is one more script (`scripts/philo8_rehearsal.py`). |
| 2 Not even pre-alpha | Every proof is a rehearsal on an isolated hub. Nothing is called a sitting. | He has still not used the product. |
| 3 Help and accelerate | The four walls on the Floor (the 409, the missing rename, the dead Delete, the lost second delete) are gone on the branch. | About 4.7 s from New Zone to the field on the rig (BACKLOG "PHILO-8-01 follow-ups", unmeasured cause). |
| 4 ASD-STE100 | The chip words are two words each (`NAME TAKEN`, `NOT SAVED`); the ghost reasons are imperatives (`Open the Floor`). | Not certified against the full STE dictionary. |
| 5 Component framework | One `ZoneRenameRow` on the list and the Floor; the library `StateChip`; one receipt seat (`DeskDeleteSeat`) in the #665 foot class. | The list's raw sort-header buttons and 10 px text stay (BACKLOG "PHILO-8-01 follow-ups"). |
| 6 Workbench 2.0+ | No new screen or panel. | The Workbench window's Remove changed on purpose (a second Remove commits the first; #672 decision 4). |
| 7 A Senior Architect with reports | He sorts his desk into zones and throws out what he does not need, at 1440 and 393. | The row menu's Delete row is cut 15 px at the bottom at 393 (FINDING S2, measured by #672; BACKLOG). |

## The closing rehearsal (story 03)

`assets/story-03-shots/rehearsal-b65107f5/` — `scripts/philo8_rehearsal.py`: one real hub on an isolated HOME, one page per width, the six jobs in order, the hub read back after each (`rehearsal.json`). A rehearsal, not a sitting. See `assets/story-03-proof.md` "The closing rehearsal" for the index of shots and the hub answers. **It ran on the #672 head `b65107f5` (a `git archive` build: main plus story 02); it is re-run on merged main before the close.**

## Both brains, per story

Who checked. Codex Astra (`gpt-6-astra`) was out from 2026-09-25 15:38 MDT (the Phase 7 summary). By the owner's ruling of 2026-09-25 the charter, story 01 (both halves) and story 04 (a) were checked by "Astra role (Opus 5.5 stand-in)" agents: the builder and the checker came from the same model family. Codex Astra returned for story 02 onward.

| Item | Built by | Checked by | Verdicts per round | Merged |
|---|---|---|---|---|
| Charter | the Fedaykin docs lane (Opus 5.5) for Muad'Dib | Astra role (Opus 5.5 stand-in) | r1 RATIFY-WITH-CONDITIONS (C1–C9: the three verified delete causes, the repair shape, the free-name rule, Q2 (c), the long list at 393, …), paid in round two (`checks/charter-astra-role-r1.md`). The owner: "Ratify, build it"; Q1 (a), Q2 (c), Q3 keep (a) drop (b) | #668 `267f692a` |
| 01 half A — the free name, the Chair without New Zone, the canvas | the Fedaykin lane (Opus 5.5) | Astra role (Opus 5.5 stand-in) | r1 RATIFY-WITH-CONDITIONS (merge: C1, C2; the canvas: C3–C6), paid (`checks/story-01-built-astra-role-r1.md`). The owner ratified the canvas: "Ratify as drawn"; "Chip on the list and the Floor"; "Keep F2 on zone rows" | #671 `808a9c30` |
| 01 half B — the in-row field, the chip, F2 | the Fedaykin lane (Opus 5.5) | Astra role (Opus 5.5 stand-in) | r1 RATIFY-WITH-CONDITIONS (C1 the evidence, C2 the Floor failed-save glass, C3 the BACKLOG rows), paid (`checks/story-01-halfb-astra-role-r1.md`) | #673 `ce772ef9` |
| 04 (a) — the empty decision headings | the Fedaykin lane (Opus 5.5) | Astra role (Opus 5.5 stand-in) | r1 RATIFY-WITH-CONDITIONS (one test condition), paid (`checks/story-04-built-astra-role-r1.md`) | #669 `26f7b005` |
| 02 — one delete everywhere | the Fedaykin lane (Opus 5.5) | Codex Astra | <!-- pending: Codex Astra's verdicts on PR #672 --> round two (the Chair withholds Delete) is Muad'Dib's ruling (`docs/internal/philo/phase-8/one-delete/README.md` decision 3) | PR #672 (open at this draft) |
| 03 — the atlas cases and the closing proof | the Fedaykin lane (Opus 5.5) | Codex Astra | <!-- pending --> | this PR (open at this draft) |

## Fences that failed pre-fix

- **01 half A:** 12 glass cases through the real hub at 1440 and 393, 10 red on main `267f692a` (2 guard legs green by design); 25 unit cases, 8 red on main (`assets/story-01-half-a-proof.md`).
- **01 half B:** 14 glass cases, all red on main `808a9c30`; 6 unit cases red on main (`evidence-story-01.md` "Red on main 808a9c30").
- **02:** the list's Delete (row menu, key, palette), Undo, the long list, two deletes in both orders on both faces, the face change, the Chair: red on main `267f692a` (+#669) through the real hub; 6 vitest red; the mutations M1, M2, M3b, M4 each turn a fence red; M3 was the wrong mutation and is recorded (`docs/internal/philo/phase-8/one-delete/README.md`).
- **04 (a):** the glass fence red on main, green on the branch (`evidence-story-04.md`).
- **03:** on main `267f692a` 27 of 28 new face runs FAIL by assertion and 1 is blocked (`case.p8.delete_twice.both_gone` at 1440: the two-delete gesture outlasted the 8 s window on main under load 26–31, three attempts; its 393 run fails); 19 of 19 cases fail under one expectation mutation each on the phase build (`assets/story-03-proof.md` "The reds").

## The exits

| # | Exit (short) | Verdict | Evidence |
|---|---|---|---|
| 1 | Two New Zone presses make two zones on every face offering it, both widths, zero 409 | **MET** (flipped) | `evidence-story-01.md`; atlas `case.p8.zone_create.second_unnamed` and `_floor` pass at both widths, fail on main |
| 2 | New Zone and F2 open the rename where he is; Enter writes; no stale field | **MET** (flipped) for the list and the Floor; the Chair withholds New Zone (Q2 (c)) | `evidence-story-01.md`; atlas `case.p8.zone_rename.list`, `.f2_row`, `.name_taken_*`, `case.p8.chair.no_new_zone` |
| 3 | The list's Delete with the Floor's receipt, readable, the long list at 393; 404 after the window, 200 after Undo | **PENDING #672's merge** | PR #672 `evidence-story-02.md`; atlas `case.p8.list_delete.*` pass on the #672 build `b65107f5` and fail on main |
| 4 | Two deletes both reach the hub; a face change commits; Undo keeps the pending one; each cause has a mutation | **PENDING #672's merge** | PR #672 (M1, M2, M3b); atlas `case.p8.delete_twice.both_gone`, `case.p8.delete_then_leave.gone` pass on `b65107f5`, fail on main |
| 5 | An atlas case per repaired face at both widths, `.op` siblings where durable; each new face case fails on main; the 27 Phase 7 cases still pass | **MET on the #672 build, with one qualification; re-run on merged main owed** | `assets/story-03-proof.md`: 28/28 pass on `b65107f5`; on main 27 fail and 1 is blocked (the two-delete case at 1440, under load) |
| 6 | The closing proof rehearsed through the real hub at both widths; the owner reviews the shots | **PENDING the owner's review** (shots on `b65107f5`; re-run on merged main owed) | `assets/story-03-proof.md` "The closing rehearsal" |
| 7 | (a) no empty decision heading; (b) dropped by the owner | **MET** (flipped) | `evidence-story-04.md`; atlas `case.p8.decision_heads.hidden` |

The exit boxes in `current-phase-status.md` stay as they are; the flips are the orchestrator's.

## The owner's rulings, in order

1. **2026-09-26 — closing Phase 7:** "Close, and make the Floor Phase 8".
2. **2026-09-26 — the charter:** "Ratify, build it"; Q1 (a) "New zone 2"; Q2 (c) the Chair does not offer New Zone, the list's in-row field (its canvas first); Q3 keep (a), drop (b).
3. **2026-09-26 — the list rename canvas:** "Ratify as drawn"; "Chip on the list and the Floor"; "Keep F2 on zone rows".
4. **2026-09-26 — Muad'Dib's ruling on #672 round two:** the Chair withholds Delete (UX-CANON §A.11).

## The numbers

- **Atlas cases:** 148 → 167 (`atlas.json` 85, `atlas-phase3.json` 36, `atlas-phase7.json` 27 unchanged; `atlas-phase8.json` 19: 14 face, 5 `.op`).
- **Rig:** 1.4.0 → 1.5.0 (`protocol_reads`, `all_of`, `button: "right"`, a trigger's `then`).

## THE LEDGER: what he still cannot do, and the debts (ranked by owner cost)

1. **The list delete and the two-delete repairs are not on main** until PR #672 merges (exits 3, 4). ASSIGNED: Muad'Dib, on Codex Astra's check.
2. **The row menu's Delete row is cut 15 px at the bottom at 393** (FINDING S2, measured `{'top': 839, 'bottom': 867, 'vh': 852}`; BACKLOG "PHILO-8-02 follow-ups", on #672).
3. **About 4.7 s from New Zone to the name field** on the rig (BACKLOG "PHILO-8-01 follow-ups"; cause not measured).
4. **The Floor's zone name field is clipped** to the zone label's width; after a refused rename each blur re-sends the refused name (BACKLOG "PHILO-8-01 follow-ups").
5. **The list face's 10 px text, the plural `SHOWNS`, the Zone column cut at 393, the raw sort-header buttons** (BACKLOG "PHILO-8-01 follow-ups"). The list face repair.
6. **F2 on a zone on the Chair has no face path to reach it** (a zone is selectable only on the WebGL Floor); the ghost is unit-fenced only (`web/src/desk/__tests__/philo801ZoneVerbs.test.ts`; `atlas-phase8.json` `excluded.p8.chair_f2_face`).
7. **The doubled hairline on the Intelligence Follow-through lanes** (BACKLOG "PHILO-8-04 follow-ups").
8. **Carried from Phase 7, unchanged:** the six non-desk two-step terminal writes; DESK palette = ALL; the tombstoned Thought's note 500; "find it cold"; the ToolSearch confound; the 11/10 px rules outside Settings; the Workbench footer linger; the privacy note; Projects on the contract (the next PHILO phase, on the owner's word).

## Laws learned

- **An atlas case can carry a hub half and a face half of one outcome.** `all_of` reads the receipt AND the hub's 404 on the same observation; a readable "Removal committed" alone does not prove the delete (the Phase 7 decision-delete case read the hub only as a record).
- **A case inside an 8 s window is one gesture.** The rig's before-capture (settle, preconditions, hub reads, a 2x screenshot) outlasted the undo window under load, so a second act written as the trigger ran after the timer: main passed two delete cases at 1440 that way. The first act is the trigger; the rest is its `then`.
- **A step that does not exist on main is optional, never the outcome.** The step records `done: false`, the predicate reads the outcome, so main runs to a `fail` verdict instead of `blocked`, and the branch cannot pass on a skipped step.
- **The general atlas fences read `atlas.json` only.** A phase file must apply them itself (`tests/unit/test_philo8_atlas.py` "the general fences"); `atlas-phase7.json` held anchors that drifted on main after story 01 (re-anchored here, three lines).
