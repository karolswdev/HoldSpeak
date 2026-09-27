# Phase 8 — The Honest Floor — final summary

<!-- owner word pending -->
**CLOSED — (the owner's word is pending).** This is the DRAFT for the close, written by the PHILO-8-03 lane (Fedaykin, Opus 5.5) for Muad'Dib. The closing line goes here in the Phase 7 form ("CLOSED <date> on the owner's word (<his words>): rehearsed, owner-reviewed; not a sitting") only after the owner reviews the rehearsal shots.

**Status: stories 01, 02 and 04 merged (01: #671 `808a9c30`, #673 `ce772ef9`; 02: #672 `a6c94db2`, after seven Codex Astra rounds; 04: #669 `26f7b005`); story 03 is PR #674, re-run on merged main `a6c94db2`.** Exits 1, 2 and 7 are flipped in `current-phase-status.md`. Exits 3–5 are met on merged main (the table below); exit 6 waits on the owner's review of the rehearsal shots. No sitting is claimed. The owner has not used this on his own desk.

## What he can do now that he could not on 2026-09-26 morning

- **Make a second zone, and a third.** New Zone names the next free default ("New zone 2", "New zone 3", …) by the hub's own rule; a name he typed is never replaced (story 01 half A; `web/src/desk/zoneName.ts`). On main before this phase the second New Zone answered `409 zone_name_taken` on every face (FINDING S1).
- **Name a zone where he is.** On the list, New Zone opens the name field in the new zone's row, with the name selected; Enter writes it; F2 on a focused zone row opens the same field (story 01 half B; the canvas the owner ratified, "Ratify as drawn").
- **See why a name was refused.** A taken name shows the library chip `✗ NAME TAKEN` under the field, on the list and on the Floor; a failed save shows `✗ NOT SAVED`; a refusal after the field closed goes to the write receipt with Retry.
- **Not be offered a verb that cannot work.** The Chair does not offer New Zone (Q2 (c)); F2 on a zone on the Chair is greyed `Open the Floor`; Delete on the Chair is greyed `Open the Floor or the list` (story 02 round two, PR #672).
- **Delete from the list, with Undo.** The row menu, the Delete key and the palette's Delete remove the object with the Floor's receipt ("Removed … Undo", then "Removal committed"), readable at both widths, and on a long list scrolled to its end at 393. While the DELETE is in flight the receipt reads "Removed …" without Undo; "Removal committed" shows only after the hub accepts it; a refused DELETE shows `DELETE FAILED · …` with Retry, in the list's foot too.
- **Delete twice in one window, or leave the face inside it, and lose nothing.** The first delete commits when the second is queued; a face change commits a pending delete; the deleted object leaves the selection; a repeated Delete of one object never offers a false Undo.
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

`assets/story-03-shots/rehearsal-a6c94db2/` — `scripts/philo8_rehearsal.py`: one real hub on an isolated HOME, one page per width, the six jobs in order, the hub read back after each (`rehearsal.json`). A rehearsal, not a sitting. See `assets/story-03-proof.md` "The closing rehearsal" for the index of shots and the hub answers. It ran on merged main `a6c94db2` (branch HEAD `b941f2e1`), load 8–13, zero page errors at both widths; every job's hub answer is the one the job promises (two zones `New zone`/`New zone 2`; the rename on the hub; 404 without Undo; 200 after Undo and after the window; A 404 and B 404; 404 after the face change). The first rehearsal, on the #672 head `b65107f5`, is kept under `assets/story-03-shots/attempts/` (superseded). **The owner reviews these shots before merge.**

## Both brains, per story

Who checked. Codex Astra (`gpt-6-astra`) was out from 2026-09-25 15:38 MDT (the Phase 7 summary). By the owner's ruling of 2026-09-25 the charter, story 01 (both halves) and story 04 (a) were checked by "Astra role (Opus 5.5 stand-in)" agents: the builder and the checker came from the same model family. Codex Astra returned for story 02: it checked story 02 in seven rounds (r1–r7) and is the checker for story 03.

| Item | Built by | Checked by | Verdicts per round | Merged |
|---|---|---|---|---|
| Charter | the Fedaykin docs lane (Opus 5.5) for Muad'Dib | Astra role (Opus 5.5 stand-in) | r1 RATIFY-WITH-CONDITIONS (C1–C9: the three verified delete causes, the repair shape, the free-name rule, Q2 (c), the long list at 393, …), paid in round two (`checks/charter-astra-role-r1.md`). The owner: "Ratify, build it"; Q1 (a), Q2 (c), Q3 keep (a) drop (b) | #668 `267f692a` |
| 01 half A — the free name, the Chair without New Zone, the canvas | the Fedaykin lane (Opus 5.5) | Astra role (Opus 5.5 stand-in) | r1 RATIFY-WITH-CONDITIONS (merge: C1, C2; the canvas: C3–C6), paid (`checks/story-01-built-astra-role-r1.md`). The owner ratified the canvas: "Ratify as drawn"; "Chip on the list and the Floor"; "Keep F2 on zone rows" | #671 `808a9c30` |
| 01 half B — the in-row field, the chip, F2 | the Fedaykin lane (Opus 5.5) | Astra role (Opus 5.5 stand-in) | r1 RATIFY-WITH-CONDITIONS (C1 the evidence, C2 the Floor failed-save glass, C3 the BACKLOG rows), paid (`checks/story-01-halfb-astra-role-r1.md`) | #673 `ce772ef9` |
| 04 (a) — the empty decision headings | the Fedaykin lane (Opus 5.5) | Astra role (Opus 5.5 stand-in) | r1 RATIFY-WITH-CONDITIONS (one test condition), paid (`checks/story-04-built-astra-role-r1.md`) | #669 `26f7b005` |
| 02 — one delete everywhere | the Fedaykin lane (Opus 5.5) | Codex Astra (`gpt-6-astra`), seven rounds | Round two (the Chair withholds Delete) is Muad'Dib's ruling (`docs/internal/philo/phase-8/one-delete/README.md` decision 3). Then Codex Astra: r1 BOUNCE @ `b65107f5` (a repeated Delete offered a false Undo; a failed refresh unmounted the host and committed early; the list foot covered the last row) → r2 BOUNCE @ `d3eab7e8` (a landed delete cleared an unrelated failure; "Removal committed" before the commit landed; a refused Workbench Remove held the item) → r3 BOUNCE @ `a84d1a37` (the Workbench Undo hidden by an old refusal; the list's refusal and Retry in the fixed foot) → r4 BOUNCE @ `daedfc99` (the Workbench lost another item's refusal on a successful Remove) → r5 BOUNCE @ `ba55892e` (the same class: the failure channel made subject-aware) → r6 BOUNCE @ `f95e03ab` (the rename chip's refusal lost its subject across a face change) → r7 **RATIFY** @ `4f419de0`, no conditions (`checks/story-02-built-astra-r1.md` … `-r7.md`; the lane's record `checks/story-02-round-three-muaddib.md`) | #672 `a6c94db2` |
| 03 — the atlas cases and the closing proof | the Fedaykin lane (Opus 5.5) | Codex Astra | <!-- pending: Codex Astra's check on PR #674 --> | PR #674 (open at this draft) |

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
| 3 | The list's Delete with the Floor's receipt, readable, the long list at 393; 404 after the window, 200 after Undo | **MET** (merged main) | `evidence-story-02.md`; atlas `case.p8.list_delete.gone`, `.undo`, `.long_list_393` pass at 1440 and 393 on `a6c94db2` and fail on main `267f692a`; the rehearsal reads 200 after Undo and after the window |
| 4 | Two deletes both reach the hub; a face change commits; Undo keeps the pending one; each cause has a mutation | **MET** (merged main) | `evidence-story-02.md` (M1, M2, M3b); atlas `case.p8.delete_twice.both_gone`, `case.p8.delete_then_leave.gone` pass at both widths on `a6c94db2`; on main `delete_then_leave` fails at both widths and `delete_twice` fails at 393 and is blocked at 1440 (the qualification in exit 5) |
| 5 | An atlas case per repaired face at both widths, `.op` siblings where durable; each new face case fails on main; the 27 Phase 7 cases still pass | **MET WITH QUALIFICATION** | `assets/story-03-proof.md`: on merged main `a6c94db2` 28/28 face runs pass, 5/5 `.op`, 27/27 Phase 7 cases (36 runs). Qualification: on main `267f692a` 27 of 28 face runs fail by assertion and 1 is blocked, not failed (`case.p8.delete_twice.both_gone` at 1440: three tries at load 26–31, the gesture outlasted A's window on main); its 393 run fails, and story 02's glass is red on main for the same fence |
| 6 | The closing proof rehearsed through the real hub at both widths; the owner reviews the shots | **PENDING the owner's review** (rehearsed on merged main `a6c94db2`) | `assets/story-03-shots/rehearsal-a6c94db2/`; `assets/story-03-proof.md` "The closing rehearsal" |
| 7 | (a) no empty decision heading; (b) dropped by the owner | **MET** (flipped) | `evidence-story-04.md`; atlas `case.p8.decision_heads.hidden` |

The exit boxes in `current-phase-status.md` stay as they are; the flips are the orchestrator's.

## The owner's rulings, in order

1. **2026-09-26 — closing Phase 7:** "Close, and make the Floor Phase 8".
2. **2026-09-26 — the charter:** "Ratify, build it"; Q1 (a) "New zone 2"; Q2 (c) the Chair does not offer New Zone, the list's in-row field (its canvas first); Q3 keep (a), drop (b).
3. **2026-09-26 — the list rename canvas:** "Ratify as drawn"; "Chip on the list and the Floor"; "Keep F2 on zone rows".
4. **2026-09-26 — Muad'Dib's ruling on #672 round two:** the Chair withholds Delete (UX-CANON §A.11).
5. **2026-09-26 — #672 merged** on Codex Astra's r7 RATIFY (no conditions).

## The numbers

- **Atlas cases (at the branch HEAD):** 148 → 167 (`atlas.json` 85, `atlas-phase3.json` 36, `atlas-phase7.json` 27 unchanged; `atlas-phase8.json` 19: 14 face, 5 `.op`).
- **Rig:** 1.4.0 → 1.5.0 (`protocol_reads`, `all_of`, `button: "right"`, a trigger's `then`).

## THE LEDGER: what he still cannot do, and the debts (ranked by owner cost)

1. **The owner has not reviewed the closing shots** (exit 6). ASSIGNED: Muad'Dib, to the owner.
2. **A selected name can hardly be seen.** New Zone and F2 open the name SELECTED (`selectionStart 0`, `selectionEnd` = the name's length, focused; `assets/story-03-shots/rehearsal-a6c94db2/rehearsal.json`), but the desk-wide `::selection` background is `--accent-soft` (the accent at 12 % alpha, `web/src/styles/global.css:68`): 1.13:1 against the field (`assets/story-03-shots/selection-probe/`). Typing still replaces the name. BACKLOG "PHILO-8-03 follow-ups". Desk-wide, not a story 01 defect.
3. **The row menu's Delete row is cut 15 px at the bottom at 393** (FINDING S2; BACKLOG "PHILO-8-02 follow-ups").
4. **A failed rename, reopened with F2 and resubmitted, shows the row chip and the old receipt together** (Codex Astra r4 MISSED 2; BACKLOG "PHILO-8-02 follow-ups").
5. **About 4.7 s from New Zone to the name field** on the rig (BACKLOG "PHILO-8-01 follow-ups"; cause not measured).
6. **The Floor's zone name field is clipped** to the zone label's width; after a refused rename each blur re-sends the refused name; a late 422 or network refusal drops the hub's reason (BACKLOG "PHILO-8-01 follow-ups").
7. **The list face's 10 px text, the plural `SHOWNS`, the Zone column cut at 393, the raw sort-header buttons** (BACKLOG "PHILO-8-01 follow-ups"). The list face repair.
8. **F2 on a zone on the Chair has no face path to reach it** (a zone is selectable only on the WebGL Floor); the ghost is unit-fenced only (`web/src/desk/__tests__/philo801ZoneVerbs.test.ts`; `atlas-phase8.json` `excluded.p8.chair_f2_face`).
9. **The doubled hairline on the Intelligence Follow-through lanes** (BACKLOG "PHILO-8-04 follow-ups").
10. **The two-delete case cannot be shown red on main at 1440 under load** (the gesture outlasts the 8 s window there); red at 393 and in story 02's glass. Recorded, not a product debt.
11. **Carried from Phase 7, unchanged:** the six non-desk two-step terminal writes; DESK palette = ALL; the tombstoned Thought's note 500; "find it cold"; the ToolSearch confound; the 11/10 px rules outside Settings; the Workbench footer linger; the privacy note; Projects on the contract (the next PHILO phase, on the owner's word).

## Laws learned

- **An atlas case can carry a hub half and a face half of one outcome.** `all_of` reads the receipt AND the hub's 404 on the same observation; a readable "Removal committed" alone does not prove the delete (the Phase 7 decision-delete case read the hub only as a record).
- **A case inside an 8 s window is one gesture.** The rig's before-capture (settle, preconditions, hub reads, a 2x screenshot) outlasted the undo window under load, so a second act written as the trigger ran after the timer: main passed two delete cases at 1440 that way. The first act is the trigger; the rest is its `then`.
- **A step that does not exist on main is optional, never the outcome.** The step records `done: false`, the predicate reads the outcome, so main runs to a `fail` verdict instead of `blocked`, and the branch cannot pass on a skipped step.
- **The general atlas fences read `atlas.json` only.** A phase file must apply them itself (`tests/unit/test_philo8_atlas.py` "the general fences"); `atlas-phase7.json` held anchors that drifted on main after story 01 (re-anchored here, three lines).
