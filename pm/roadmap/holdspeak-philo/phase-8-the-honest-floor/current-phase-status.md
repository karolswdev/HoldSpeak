# Phase 8 - The Honest Floor

**Last updated:** 2026-09-26 (PHILO-8-02 DONE: one delete everywhere — one listener and one receipt that survive a face change; the list's Delete works on every path at 1440 and 393; two deletes in one window both reach the hub; a face change commits a pending delete; every fence red on main, each cause mutated red; `docs/internal/philo/phase-8/one-delete/README.md`. Earlier: RATIFIED by the owner — "Ratify, build it"; Q1 (a), Q2 (c) for the Chair + the in-row field for the list, Q3 keep (a) drop (b). Earlier: round two: the Astra-role check, RATIFY-WITH-CONDITIONS (`checks/charter-astra-role-r1.md`), C1–C9 paid; the owner's ratification owed. Earlier: DRAFTED by the Fedaykin docs lane for Muad'Dib, on the owner's word closing Phase 7: "Close, and make the Floor Phase 8".)

## Goal

The owner makes zones, names them, and deletes objects on the Desk from any face he is on, and the face tells the truth about what happened. Four verified Floor defects are repaired with the idioms that already exist: the second unnamed zone that fails, the rename that lives on one face only, the list-view Delete that does nothing, and the second delete in one undo window that does not happen. Nothing else.

## Authority

The owner, 2026-09-26, by AskUserQuestion, closing Phase 7 (verbatim): "Close, and make the Floor Phase 8".

The ledger this phase pays is the Phase 7 final summary's "THE LEDGER", rows 1–4, ranked by owner cost (`../phase-7-the-desk-on-the-contract/final-summary.md`, "THE LEDGER: what he still cannot do"). Rows 9 and 11–14 are named below as Out or OPTIONAL; rows 5–8 are Out with their BACKLOG homes.

Carried, unchanged: the Seven Tenets (`docs/internal/CONSTITUTION.md:18-60`); UX-CANON §A.2 design on the canvas before build, §A.4 no modals, edit in-world, §A.11 a verb that does nothing is a lie (`docs/internal/UX-CANON.md:24-52`); the method and the laws of handover XXIX (`docs/internal/project-rooms/HANDOVER-MUADDIB-XXIX.md:33-42`); the delete receipt's seat as the owner ratified it in PR #665 (`web/src/desk/gl/WorldStage.tsx:343-348`, the receipt in flow directly above the AskBar).

## The roots

- **Tenet 2 (not even pre-alpha):** he has not used the product. The Floor is the first place he makes and removes things. One Chair New Zone blocks every further zone (`docs/internal/philo/phase-7/floor-diag/FINDING.md` S1). That is a wall on day one.
- **Tenet 3 (help and accelerate):** a verb that the face offers must do what it says. Today the list-view Delete does nothing (FINDING Finding 2), and three paths lose a delete: a second delete while the first stays selected, a second delete that clears the first one's timer, and a face change inside the undo window (`checks/charter-astra-role-r1.md` F2).
- **Tenet 1 (no over-engineering):** each repair uses an idiom that exists: the store's create, the one rename overlay's behaviour, the one undo receipt hook, the one delete verb. No new framework, no new state machine, no new screen.
- **Tenet 5 (component framework):** the rename field and the receipt are existing species; the list and the Chair compose them, they do not copy them.
- **Tenet 7 (a Senior Architect with reports):** he sorts his desk into zones and throws out what he does not need. Both must work at 1440 and at 393.

## Status of this charter

DRAFT, 2026-09-26, written by the Fedaykin docs lane (Opus 5.5) for Muad'Dib. The Astra-role check (Opus 5.5 stand-in while Codex Astra is out, per the owner's ruling 2026-09-25; if Codex Astra returns after Sep 26 20:50 it may take its role back): RATIFY-WITH-CONDITIONS (`checks/charter-astra-role-r1.md`), C1–C9 paid in round two ("Decisions made"). Owed: the owner's ratification and his answers to "Decisions for the owner". Nothing is built. The check is same-family (Opus 5.5 built and checked this draft).

## Scope

- **In:**
  1. **A second unnamed zone fails 409 on every face.** New Zone always posts `{name: "New zone"}` (`web/src/desk/store/dataSlice.ts:322`). A live zone name must be unique after strip, collapsed whitespace, NFC and casefold (`holdspeak/db/primitives.py:60-68`; `holdspeak/operations.py:655`; `holdspeak/services/primitive_service.py:365-368`). So after one Chair or list create leaves a zone named "New zone", every further New Zone on every face answers `409 zone_name_taken`, and Retry fails the same way (FINDING S1). The repair (ruled the smallest lawful one by the Astra-role check, RULING (3)): the store picks the next free default name ("New zone 2", "New zone 3", …) inside `createPrimitive`, by the hub's rule in full; it never replaces a name the caller passed; after a 409, Retry refreshes the store before it picks again (`dataSlice.ts:339`). The hub's rule stays: a hub-side name picker changes a declared contract and is rejected under Tenet 1. Story 01.
  2. **No rename from the Chair or the list view.** `createPrimitive("zone")` sets `renamingZoneId` (`dataSlice.ts:370`), and so does the F2 Rename key for a zone (`web/src/desk/verbRegistry.ts:502`); the only reader that draws the field is `WorldStage` (`web/src/desk/gl/WorldStage.tsx:206-207`, `:271-280`, the overlay at `:400`). `WorldStage` mounts only on the spatial Floor (`web/src/desk/DeskApp.tsx:192-207`). On the Chair and the list the zone is made and nothing shows; the stale field comes up later on another face and takes focus (FINDING Finding 1, both widths). The repair: the rename opens where the owner is (UX-CANON §A.4), for New Zone and F2 alike, with the overlay's behaviour (Enter commits, blur commits, Escape cancels); the rename state never survives onto another face. A FACE change: the canvas first, ratified by the owner (Q2). Story 01.
  3. **The list view's row-menu Delete does nothing, at any width.** `object.delete` only dispatches `OBJECT_DELETE_REQUEST` (`web/src/desk/verbRegistry.ts:559-564`); its only listener is in `WorldStage` (`WorldStage.tsx:138-152`), which never mounts with `DeskListView` (`DeskApp.tsx:192-207`). No write, no receipt, the object stays (FINDING Finding 2, 1440 and 393). The repair: one delete listener and one undo receipt that survive a face change; the list wraps its AskBar (`web/src/desk/components/DeskListView.tsx:340`) and the receipt in the Floor's foot class, the seat the owner ratified in #665. No canvas. Story 02.
  4. **Deletes that do not happen: three VERIFIED causes** (the Astra-role check reproduced each through the real hub on main, `checks/charter-astra-role-r1.md` F2). (1) The deleted object stays selected, so selecting B makes 2 selected; the keymap passes no target (`web/src/desk/keymap.ts:71-74`) and Delete is ghosted silently (`keymap.ts:84`) → A 404, B 200, B's delete never sent. (2) `remove()` clears A's timer when B is queued (`web/src/desk/hooks/useUndoReceipt.ts:27`) → A 200, B 404, while the face said "Removed" for A. (3) Leaving the face inside the window drops the pending delete (`useUndoReceipt.ts:23`, the hook clears on `WorldStage` unmount) → A 200, zero requests. The no-op revert (`WorldStage.tsx:147`) is not a cause. The repair (RULING (5)): the first delete COMMITS when a second is queued; a pending delete COMMITS on a face change (or the listener and hook move to one always-mounted place); the queued object leaves the selection; the receipt keeps one slot (a second delete takes the first one's Undo: the lane's decision, recorded). Story 02.
  5. **The atlas cases for the repaired faces and the closing proof** at 1440 and 393. Story 03.
  6. **OPTIONAL, the owner keeps or drops (Q3):** (a) the decision window's empty headings: "Decision context", "Decision" and "Consequences" each show with nothing under them (`web/src/desk/pullouts/DecisionPullout.tsx:113-115`; BACKLOG "PHILO-7-04 follow-ups" row 1, homed to the Floor lane, `pm/roadmap/holdspeak/BACKLOG.md:1280`); (b) the brief's people sections reading "unavailable" on a fresh hub (row 2, homed to the Arrival lane, `BACKLOG.md:1281`; not a Floor item — offered for dropping). Story 04, only if kept.
- **Out (with their homes):**
  - The six NON-desk kernel two-step terminal writes (admission refusal, native failure, reject, claim refusal, `recover_invalidated`, the reaper): BACKLOG "PHILO-7-02 lifecycle beat follow-ups" (`pm/roadmap/holdspeak/BACKLOG.md:1243-1247`); a kernel story after this phase.
  - DESK palette = ALL (a DESK credential reads back as `ALL`): BACKLOG "PHILO-7-02 canvas follow-ups" (`BACKLOG.md:1249-1253`); a Remote Access repair.
  - The Workbench footer linger (a delete hides the "N ITEMS · last run" line for 6 s): BACKLOG "The Floor delete receipt follow-ups" row 2 (`BACKLOG.md:1269-1274`); the next Workbench sitting.
  - The 11 px and 10 px rules outside the Settings window (`.surface-token` without `data-chip`, the provenance chip, `.desk-wing-door`, rules in `surface.css` / `gadgets.css`): Phase 7 ledger row 11; `../phase-7-the-desk-on-the-contract/assets/story-02-canvas/README.md:73`; the library's next pass.
  - Filing a tombstoned Thought's note over HTTP answers 500: BACKLOG "PHILO-7-02 round two follow-ups".
  - "Find it cold" (a fresh client finds a note it did not file): BACKLOG "PHILO-7-04 follow-ups" row 3; the next MCP slice's closing use.
  - The receipt moving 78 px when the AskBar leaves (cosmetic, F8, `checks/delete-receipt-astra-role-r1.md:39`) and the row menu's Delete row cut at the bottom edge at 393 (FINDING S2): recorded; story 02 measures S2 because its fence clicks that row, and files a BACKLOG row if it reproduces; neither is repaired here.
  - The supersede action on the face (`web/src/desk/api.ts:259` has no caller): not a Floor defect.
  - Projects (42 MCP identities, the census at main `189a6b52`, `docs/internal/project-rooms/HANDOVER-MUADDIB-XXVIII.md:33`; the Phase 7 charter's Out, `../phase-7-the-desk-on-the-contract/current-phase-status.md:53`): the Phase 7 charter named Projects as "Phase 8, the owner's second job". The owner's word of 2026-09-26 makes the Floor Phase 8, so Projects move to the next MCP slice. Home: BACKLOG "Projects on the contract" (`pm/roadmap/holdspeak/BACKLOG.md`, the last table); the README phase table notes it.
  - Phase 7 ledger row 9, the ToolSearch confound (the tool names did most of the discovery; no A/B run, `docs/internal/philo/phase-7/file-and-find/rehearsal.md:149`): report only, no home in this phase; the next MCP slice's closing use may run the A/B.
  - Phase 7 ledger row 14, the privacy note (the owner's address in ten tracked files on main and in his git identity; `../phase-7-the-desk-on-the-contract/final-summary.md` THE LEDGER row 14): report only, no home; it waits for the owner's word.
  - Any other face change, any kernel change, any change to the hub's zone-name rule.

## Exit criteria (evidence required)

Every behavioural fence is red on main before the repair, through the real hub on an isolated HOME (no test double that lies about the field the check reads), and green after. "At both widths" means 1440x900 and 393x852.

- [ ] 1. Two New Zone presses in a row, with no rename between, make two zones on the Chair, the list view and the spatial Floor, at both widths; the network log shows zero `409 zone_name_taken`; the second zone's name is what the owner chose in Q1.
- [ ] 2. New Zone and the F2 Rename key open the rename where the owner is, with focus, on each face that offers them (the list, and the Chair unless Q2 withholds New Zone there), as the owner-ratified canvas shows it, at both widths; Enter writes the name on the hub (`GET /api/directories`); Escape and leaving the face clear the rename state, so no rename field appears later on another face (the FINDING's "stale field" rows fail on main).
- [ ] 3. The list view's Delete (the row menu, and the Delete key wherever the list binds it; story 02 records which paths the list offers) removes the object with the same undo receipt as the Floor: "Removed … Undo", then "Removal committed", readable in the viewport (visible, unobscured) at both widths, and at 393 also with a long list (more than 16 objects) scrolled to the end; after the window the hub answers 404; after Undo it answers 200 and the row stays.
- [ ] 4. Two deletes (A then B) inside one undo window, on the spatial Floor and on the list, in both selection orders: both reach the hub (A 404, B 404). Leave the face inside the window: the object is gone (404). Undo keeps the one pending object; a delete committed by a second delete stays gone. The face never says "Removed" for an object the hub keeps. Each of the three causes has a mutation that turns its fence red.
- [ ] 5. The atlas has a case for each repaired face at both widths, with an `.op` sibling where the outcome is durable; each new face case fails on main; the 27 cases of `docs/internal/philo/graph/atlas-phase7.json` still pass.
- [ ] 6. The closing proof: the jobs (two zones, a rename where he is, a list delete, two deletes in one window, a delete then a face change) rehearsed through the real hub at both widths; the owner reviews the shots before merge. Never recorded as a sitting.
- [ ] 7. (Only if Q3 keeps them) (a) the decision window shows no heading with nothing under it ("Decision context", "Decision", "Consequences"); (b) the brief on a fresh hub says what is true for the people sections, in the owner's words.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-8-01 | The zone name and the rename where he is (canvas first) | backlog | [story-01-the-zone-name-and-the-rename-where-he-is](./story-01-the-zone-name-and-the-rename-where-he-is.md) | - |
| PHILO-8-02 | One delete everywhere | done | [story-02-one-delete-everywhere](./story-02-one-delete-everywhere.md) | [evidence-story-02](./evidence-story-02.md) |
| PHILO-8-03 | The atlas cases and the closing proof | backlog | [story-03-the-atlas-cases-and-the-closing-proof](./story-03-the-atlas-cases-and-the-closing-proof.md) | - |
| PHILO-8-04 | The two small face notes (OPTIONAL) | backlog | [story-04-the-two-small-face-notes](./story-04-the-two-small-face-notes.md) | - |

The stories stay `backlog` until the owner ratifies the charter. Story 04 is removed if the owner drops both notes (Q3).

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The zone | 01 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Astra role (Opus 5.5 stand-in; Codex Astra on return) | ../wt-philo-8-01 | feat/philo-8-01-zone-name-rename |
| The delete | 02 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Astra role (Opus 5.5 stand-in; Codex Astra on return) | ../wt-philo-8-02 | feat/philo-8-02-one-delete |
| The proof | 03 (and 04 if kept) | Muad'Dib's lane (Fedaykin, Opus 5.5) | Astra role (Opus 5.5 stand-in; Codex Astra on return) | ../wt-philo-8-03 | feat/philo-8-03-atlas-and-proof |

01 and 02 can run in parallel: 01 touches `dataSlice.ts`, the Chair and the list's zone rows; 02 touches `useUndoReceipt.ts`, the delete listener (moved or flushed) and the list's foot, and checks the Workbench window (the same hook, `web/src/desk/components/WorkbenchWindow.tsx:968`). Both touch `WorldStage.tsx` and `DeskListView.tsx`, so the second to merge rebases on the first and re-runs its fences. 03 starts after both merge. A lane runs its scoped fences and rig cases only; the full suite is CI's job on the PR.

## Where we are

2026-09-26: DRAFTED from the owner's word closing Phase 7, the Phase 7 final summary's ledger (rows 1–4, 11–13), the Floor diagnostic (`docs/internal/philo/phase-7/floor-diag/FINDING.md`, PR #667), the BACKLOG tables "PHILO-7-03 follow-ups", "The Floor delete receipt follow-ups" and "PHILO-7-04 follow-ups", and `checks/delete-receipt-astra-role-r1.md` F7. The source lines above were re-read on main `6ac73757`. Owed: the Astra-role check; the owner's ratification and his answers to Q1–Q3; the story 01 canvas (before story 01's face build). Nothing is built.

2026-09-26, round two: the Astra-role check (Opus 5.5 stand-in, `checks/charter-astra-role-r1.md`): RATIFY-WITH-CONDITIONS. It re-read every cited line on main (all true), reproduced the lost deletes and named three causes, found a third (a face change inside the window), and ruled the free-name repair and the delete repair shape. C1–C9 are paid in this revision ("Decisions made").

**Estimate (PROVISIONAL, placed before build):** effort **2.5–4 engineering days** (01 0.75–1.25 · 02 0.75–1.25 · 03 0.75–1 · the rename canvas and the check rounds 0.25–0.5), plus about 0.25 d if story 04 (a) is kept. Calibrated from Phase 7's record (`checks/charter-astra-role-r1.md` F11): Phase 7's story 01 took about 25 agent-minutes (`../phase-7-the-desk-on-the-contract/current-phase-status.md` "Calibration"), and the whole 11–15-day phase closed in about two elapsed days, most of it check rounds and the owner's word; these repairs are small (a free-name helper, a hook flush, a selection drop, a hoisted listener, a foot wrapper, one rename composition). **Elapsed-time forecast: about 1–2 days elapsed, gated by the owner's canvas word and the checks.**

2026-09-26, story 02 built (the Fedaykin lane, `feat/philo-8-02-one-delete`): the one `OBJECT_DELETE_REQUEST` listener and the one undo hook moved to `DeskDeleteHost` (`web/src/desk/deleteReceipt.tsx`), mounted once in `DeskApp`; the spatial Floor and the list seat the receipt (`DeskDeleteSeat`) in the #665 foot, the list's foot held to the viewport; `useUndoReceipt` commits a pending removal on a second `remove()` and on unmount; the queued object leaves the selection. Glass: 25 cases green through the real hub at 1440 and 393 (the list's row menu, Delete key and palette; undo; the long list at 393; two deletes in both orders on both faces; a face change; the Chair with a Floor selection), plus the #665 fence and `case.p7.decision_delete.gone` at both widths. Red on main for every case (`docs/internal/philo/phase-8/one-delete/`); M1, M2, M3b and M4 turn their fences red. Web baseline: 2888 passed, zero branch-new. Lane decisions recorded (one slot; a face change commits; the Chair commits at once with no seat; the Workbench window's Remove now commits instead of dropping). FINDING S2 reproduces at 393 and the Chair's missing seat are BACKLOG rows ("PHILO-8-02 follow-ups"). Owed: the Astra-role check on built.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope creep: other Floor or Workbench defects pulled in | high | the four defects and the optional two are the whole scope; others go to the BACKLOG | a story edits a face or file not named by its defect |
| A second rename overlay is copied instead of composed | medium | the Chair and the list compose the existing field's behaviour (one component or one hook), not a copy | two rename implementations with their own Enter/blur/Escape code |
| The list delete gets a second receipt species or seat | medium | the same `useUndoReceipt` and the #665 foot class around the list's AskBar; exit 3 fences the long list at 393 | a new receipt markup or seat, or a receipt out of the viewport on a scrolled list |
| A delete is lost again on a path the fix does not cover | medium | the three verified causes (the stale selection, the dropped timer, the unmount) each have a fence and a mutation; the listener is ONE mount that survives a face change, never one per face | a fence green while one cause's mutation is still green, or a delete listener that unmounts with a face |
| A client-side free name races another client or a stale store | low (one owner) | the picker mirrors `normalize_zone_name`; after a 409, Retry refreshes the store before it picks; the hub's 409 stays the named failure row | a 409 that Retry cannot clear |
| The stale rename state keeps jumping faces | medium | exit 2 fences the FINDING's stale-field rows | a rename field that appears on a face the owner did not press New Zone on |
| Same-family checks (Opus 5.5 builds and checks) | high while Codex Astra is out | label every check "Astra role (Opus 5.5 stand-in)"; Codex Astra may check on return | a check written as "Astra" without the label |

## The owner's ratification (2026-09-26, AskUserQuestion)

- **Charter: "Ratify, build it".**
- **Q1: (a)** — the new zone is called "New zone 2" (then 3, …) and the rename opens.
- **Q2: (c)** — the Chair does not offer New Zone (it is a Floor-only verb, `verbRegistry.ts:203-212`); on the list, the name field opens in the new zone's row. The list's in-row field is a face change: its CANVAS is ratified by the owner before that face is built. Withholding the verb on the Chair is ratified by this answer and needs no canvas.
- **Q3: keep (a)** — the empty decision headings (Decision context, Decision, Consequences) hide when empty (story 04 keeps its part (a)); **drop (b)** — the brief's "unavailable" people sections stay with the Arrival lane (`pm/roadmap/holdspeak/BACKLOG.md:1281`).

## Decisions for the owner (answered above)

- **Q1 — "When I press New Zone and a zone called 'New zone' is already there, what should happen?"** We will do (a) unless you object.
  - (a) The new zone is called "New zone 2" (then 3, …), and the rename opens so I can name it. *(The Finder convention; the smallest repair; no new step.)*
  - (b) No zone is made until I type its name: New Zone opens an empty name field first. *(Larger: it changes the create on every face, and the canvas must show it.)*
- **Q2 — "Where do I name a zone I make from the Chair or from the list?"** On the list, the field opens in the new zone's row (the list shows zones as rows). For the Chair, the choices are: (a) the field opens in the Chair's receipt row; (b) New Zone takes me to the Floor with the field open; (c) the Chair does not offer New Zone. The fact that decides it: New Zone is declared a Floor-only verb (`scope: "floor"`, `web/src/desk/verbRegistry.ts:203-212`), yet the Chair's palette offers it, and the Chair shows no zones. So (c) is lawful (UX-CANON §A.11: withhold a verb rather than ship it dead) and consistent with the verb's own declaration; it costs one step (go to the Floor or the list, where zones are seen anyway). (a) adds a new element to the Chair for an object the Chair cannot show; (b) moves me without asking. **Recommended: (c) for the Chair, the in-row field for the list.** The canvas shows the list field (and the Chair option you pick) at 1440 and 393; you ratify it before build. The same rename serves the F2 Rename key.
- **Q3 — "Do I want the two small face notes fixed now?"** Keep or drop each: (a) the empty headings on a decision ("Decision context", "Decision", "Consequences" with nothing under them) — a Floor-lane item; (b) "unavailable" for the people sections of the brief on a fresh hub — an Arrival-lane item (`BACKLOG.md:1281`), **recommended: drop it from this phase**. Dropping both removes story 04.

## Decisions made (this phase)

- 2026-09-26 — the owner: "Close, and make the Floor Phase 8" (AskUserQuestion, closing Phase 7).
- 2026-09-26 — DRAFTED: the four verified Floor defects, three stories and one optional story; the list delete in the #665 seat without a canvas unless the seat cannot hold; Projects move out of Phase 8 — Fedaykin docs lane for Muad'Dib.
- 2026-09-26 — round two: the Astra-role check (`checks/charter-astra-role-r1.md`, RATIFY-WITH-CONDITIONS) paid — C1 story 02 and scope item 4 carry the three verified causes with their lines, and the false sentence "the face said B was removed" is struck (the receipt read "Removed Probe A" throughout); C2 the repair shape (commit, never drop; one listener that survives a face change; the selection drop; one receipt slot, the lane's decision; the list reuses the foot class, no canvas; exit 4 adds the face change; the Workbench window checked); C3 the free name matches the hub's rule in full, never replaces a passed name, Retry refreshes after a 409, the store-side fix ruled the smallest lawful one; C4 Q2 recommends (c) with the Floor-only fact, and the rename covers F2; C5 exit 3 adds the long list at 393; C6 the README "Last updated" line restored; C7 Projects homed in the BACKLOG; C8 ledger rows 9 and 14 named in Out; C9 the estimate recalibrated (2.5–4 d effort; about 1–2 days elapsed). Q1 worded "(a) unless you object"; Q3 (b) offered for dropping; Q3 (a) covers all three headings — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- Q1–Q3 above: the owner, at ratification.
- The Chair and list rename face: the story 01 canvas, ratified by the owner before the face build.
- F7's causes are VERIFIED (three, scope item 4); the lane chooses between flushing on unmount and hoisting the listener and hook, and records it.
- Where the new atlas cases live (`atlas-phase7.json` or a new `atlas-phase8.json`): story 03 decides against the atlas schema.
