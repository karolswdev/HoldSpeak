# Phase 8 - The Honest Floor

**Last updated:** 2026-09-26 (DRAFTED by the Fedaykin docs lane for Muad'Dib, on the owner's word closing Phase 7: "Close, and make the Floor Phase 8". Not checked; not ratified.)

## Goal

The owner makes zones, names them, and deletes objects on the Desk from any face he is on, and the face tells the truth about what happened. Four verified Floor defects are repaired with the idioms that already exist: the second unnamed zone that fails, the rename that lives on one face only, the list-view Delete that does nothing, and the second delete in one undo window that does not happen. Nothing else.

## Authority

The owner, 2026-09-26, by AskUserQuestion, closing Phase 7 (verbatim): "Close, and make the Floor Phase 8".

The ledger this phase pays is the Phase 7 final summary's "THE LEDGER", rows 1–4, ranked by owner cost (`../phase-7-the-desk-on-the-contract/final-summary.md`, "THE LEDGER: what he still cannot do"). Rows 11–13 are named below as Out or OPTIONAL.

Carried, unchanged: the Seven Tenets (`docs/internal/CONSTITUTION.md:18-60`); UX-CANON §A.2 design on the canvas before build, §A.4 no modals, edit in-world, §A.11 a verb that does nothing is a lie (`docs/internal/UX-CANON.md:24-52`); the method and the laws of handover XXIX (`docs/internal/project-rooms/HANDOVER-MUADDIB-XXIX.md:33-42`); the delete receipt's seat as the owner ratified it in PR #665 (`web/src/desk/gl/WorldStage.tsx:343-348`, the receipt in flow directly above the AskBar).

## The roots

- **Tenet 2 (not even pre-alpha):** he has not used the product. The Floor is the first place he makes and removes things. One Chair New Zone blocks every further zone (`docs/internal/philo/phase-7/floor-diag/FINDING.md` S1). That is a wall on day one.
- **Tenet 3 (help and accelerate):** a verb that the face offers must do what it says. Today the list-view Delete does nothing (FINDING Finding 2), and a second delete in one window is lost while the face said "Removed" (`../phase-7-the-desk-on-the-contract/checks/delete-receipt-astra-role-r1.md:34-37`, F7).
- **Tenet 1 (no over-engineering):** each repair uses an idiom that exists: the store's create, the one rename overlay's behaviour, the one undo receipt hook, the one delete verb. No new framework, no new state machine, no new screen.
- **Tenet 5 (component framework):** the rename field and the receipt are existing species; the list and the Chair compose them, they do not copy them.
- **Tenet 7 (a Senior Architect with reports):** he sorts his desk into zones and throws out what he does not need. Both must work at 1440 and at 393.

## Status of this charter

DRAFT, 2026-09-26, written by the Fedaykin docs lane (Opus 5.5) for Muad'Dib. Owed, in order: the Astra-role check of this draft (Opus 5.5 stand-in while Codex Astra is out, per the owner's ruling 2026-09-25; if Codex Astra returns after Sep 26 20:50 it may take its role back), then the owner's ratification and his answers to "Decisions for the owner". Nothing is built.

## Scope

- **In:**
  1. **A second unnamed zone fails 409 on every face.** New Zone always posts `{name: "New zone"}` (`web/src/desk/store/dataSlice.ts:322`). A live zone name must be unique, ignoring case (`holdspeak/operations.py:655`; `holdspeak/services/primitive_service.py:367`). So after one Chair or list create leaves a zone named "New zone", every further New Zone on every face answers `409 zone_name_taken`, and Retry fails the same way (FINDING S1). The smallest lawful repair: the store picks the next free default name ("New zone 2", "New zone 3", …) from the zones it already holds, ignoring case, inside `createPrimitive`, so Retry picks again. The hub's uniqueness rule stays; a 409 from a race with another client stays the existing named failure row. The owner chooses between this and the alternative (Decisions for the owner, Q1). Story 01.
  2. **No rename from the Chair or the list view.** `createPrimitive("zone")` sets `renamingZoneId` (`dataSlice.ts:370`), and the only reader that draws the field is `WorldStage` (`web/src/desk/gl/WorldStage.tsx:206-207`, `:271-280`, the overlay at `:400`). `WorldStage` mounts only on the spatial Floor (`web/src/desk/DeskApp.tsx:192-206`). On the Chair and the list the zone is made and nothing shows; the stale field comes up later on another face and takes focus (FINDING Finding 1, both widths). The repair: New Zone opens its rename where the owner is (UX-CANON §A.4), with the overlay's behaviour (Enter commits, blur commits, Escape cancels); the rename state never survives onto another face. A FACE change: the canvas first, ratified by the owner (Q2). Story 01.
  3. **The list view's row-menu Delete does nothing, at any width.** `object.delete` only dispatches `OBJECT_DELETE_REQUEST` (`web/src/desk/verbRegistry.ts:559-564`); its only listener is in `WorldStage` (`WorldStage.tsx:137-152`), which never mounts with `DeskListView` (`DeskApp.tsx:192-206`). No write, no receipt, the object stays (FINDING Finding 2, 1440 and 393). The repair: the list deletes through the same listener and the same undo receipt, in the seat the owner ratified in #665 (directly above the AskBar; the list renders its own AskBar at `web/src/desk/components/DeskListView.tsx:340`). A canvas only if the receipt's seat in the list cannot be that seat. Story 02.
  4. **Two deletes in one undo window keep the second.** Probe: delete A, wait 1.5 s, delete B, wait 12 s → A 404, B 200, on main and on #665's branch (`checks/delete-receipt-astra-role-r1.md:34-37`). The face said B was removed; the hub kept it. Suspected causes, NOT verified: `remove()` calls `cleanup()`, which clears the earlier pending timer without firing it (`web/src/desk/hooks/useUndoReceipt.ts:18-29`); the Floor's `revert` is a no-op (`WorldStage.tsx:144-148`); or the second Delete still targets A from the selection (`delete-receipt-astra-role-r1.md:53`). The repair: a delete the face says happened, happens; a second delete commits or keeps the first and deletes the second; the story traces the cause first and fences it. Story 02.
  5. **The atlas cases for the repaired faces and the closing proof** at 1440 and 393. Story 03.
  6. **OPTIONAL, the owner keeps or drops (Q3):** the decision window's empty CONSEQUENCES heading (`web/src/desk/pullouts/DecisionPullout.tsx:115`); the brief's people sections reading "unavailable" on a fresh hub (BACKLOG "PHILO-7-04 follow-ups", rows 1–2, `pm/roadmap/holdspeak/BACKLOG.md`). Story 04, only if kept.
- **Out (with their homes):**
  - The six NON-desk kernel two-step terminal writes (admission refusal, native failure, reject, claim refusal, `recover_invalidated`, the reaper): BACKLOG "PHILO-7-02 lifecycle beat follow-ups" (`pm/roadmap/holdspeak/BACKLOG.md:1243-1247`); a kernel story after this phase.
  - DESK palette = ALL (a DESK credential reads back as `ALL`): BACKLOG "PHILO-7-02 canvas follow-ups" (`BACKLOG.md:1249-1253`); a Remote Access repair.
  - The Workbench footer linger (a delete hides the "N ITEMS · last run" line for 6 s): BACKLOG "The Floor delete receipt follow-ups" row 2 (`BACKLOG.md:1269-1274`); the next Workbench sitting.
  - The 11 px and 10 px rules outside the Settings window (`.surface-token` without `data-chip`, the provenance chip, `.desk-wing-door`, rules in `surface.css` / `gadgets.css`): Phase 7 ledger row 11; `../phase-7-the-desk-on-the-contract/assets/story-02-canvas/README.md:73`; the library's next pass.
  - Filing a tombstoned Thought's note over HTTP answers 500: BACKLOG "PHILO-7-02 round two follow-ups".
  - "Find it cold" (a fresh client finds a note it did not file): BACKLOG "PHILO-7-04 follow-ups" row 3; the next MCP slice's closing use.
  - The receipt moving 78 px when the AskBar leaves (cosmetic, F8, `checks/delete-receipt-astra-role-r1.md:39`) and the row menu's Delete row cut at the bottom edge at 393 (FINDING S2): recorded; story 02 measures S2 because its fence clicks that row, and files a BACKLOG row if it reproduces; neither is repaired here.
  - The supersede action on the face (`web/src/desk/api.ts:259` has no caller): not a Floor defect.
  - Projects: the Phase 7 charter named Projects as "Phase 8, the owner's second job" (`../phase-7-the-desk-on-the-contract/current-phase-status.md` Scope, Out). The owner's word of 2026-09-26 makes the Floor Phase 8; Projects move to a later phase, unchartered.
  - Any other face change, any kernel change, any change to the hub's zone-name rule.

## Exit criteria (evidence required)

Every behavioural fence is red on main before the repair, through the real hub on an isolated HOME (no test double that lies about the field the check reads), and green after. "At both widths" means 1440x900 and 393x852.

- [ ] 1. Two New Zone presses in a row, with no rename between, make two zones on the Chair, the list view and the spatial Floor, at both widths; the network log shows zero `409 zone_name_taken`; the second zone's name is what the owner chose in Q1.
- [ ] 2. New Zone on the Chair and on the list opens the rename where the owner is, with focus, as the owner-ratified canvas shows it, at both widths; Enter writes the name on the hub (`GET /api/directories`); Escape and leaving the face clear the rename state, so no rename field appears later on another face (the FINDING's "stale field" rows fail on main).
- [ ] 3. The list view's Delete (the row menu, and the Delete key wherever the list binds it; story 02 records which paths the list offers) removes the object with the same undo receipt as the Floor: "Removed … Undo", then "Removal committed", readable in the viewport (visible, unobscured) at both widths; after the window the hub answers 404; after Undo it answers 200 and the row stays.
- [ ] 4. Two deletes (A then B) inside one undo window, on the spatial Floor and on the list: both reach the hub (A 404, B 404), and Undo on the pending one keeps only that one; the face never says "Removed" for an object the hub keeps. The cause is named in the evidence with its source line.
- [ ] 5. The atlas has a case for each repaired face at both widths, with an `.op` sibling where the outcome is durable; each new face case fails on main; the 27 cases of `docs/internal/philo/graph/atlas-phase7.json` still pass.
- [ ] 6. The closing proof: the four jobs (two zones, a rename where he is, a list delete, two deletes in one window) rehearsed through the real hub at both widths; the owner reviews the shots before merge. Never recorded as a sitting.
- [ ] 7. (Only if Q3 keeps them) the decision window shows no empty CONSEQUENCES heading, and the brief on a fresh hub says what is true for the people sections, as the owner rules the words.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-8-01 | The zone name and the rename where he is (canvas first) | backlog | [story-01-the-zone-name-and-the-rename-where-he-is](./story-01-the-zone-name-and-the-rename-where-he-is.md) | - |
| PHILO-8-02 | One delete everywhere | backlog | [story-02-one-delete-everywhere](./story-02-one-delete-everywhere.md) | - |
| PHILO-8-03 | The atlas cases and the closing proof | backlog | [story-03-the-atlas-cases-and-the-closing-proof](./story-03-the-atlas-cases-and-the-closing-proof.md) | - |
| PHILO-8-04 | The two small face notes (OPTIONAL) | backlog | [story-04-the-two-small-face-notes](./story-04-the-two-small-face-notes.md) | - |

The stories stay `backlog` until the owner ratifies the charter. Story 04 is removed if the owner drops both notes (Q3).

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The zone | 01 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Astra role (Opus 5.5 stand-in; Codex Astra on return) | ../wt-philo-8-01 | feat/philo-8-01-zone-name-rename |
| The delete | 02 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Astra role (Opus 5.5 stand-in; Codex Astra on return) | ../wt-philo-8-02 | feat/philo-8-02-one-delete |
| The proof | 03 (and 04 if kept) | Muad'Dib's lane (Fedaykin, Opus 5.5) | Astra role (Opus 5.5 stand-in; Codex Astra on return) | ../wt-philo-8-03 | feat/philo-8-03-atlas-and-proof |

01 and 02 can run in parallel: 01 touches `dataSlice.ts`, the Chair and the list's zone rows; 02 touches `useUndoReceipt.ts`, the delete listener and the list's foot. Both touch `WorldStage.tsx` and `DeskListView.tsx`, so the second to merge rebases on the first and re-runs its fences. 03 starts after both merge. A lane runs its scoped fences and rig cases only; the full suite is CI's job on the PR.

## Where we are

2026-09-26: DRAFTED from the owner's word closing Phase 7, the Phase 7 final summary's ledger (rows 1–4, 11–13), the Floor diagnostic (`docs/internal/philo/phase-7/floor-diag/FINDING.md`, PR #667), the BACKLOG tables "PHILO-7-03 follow-ups", "The Floor delete receipt follow-ups" and "PHILO-7-04 follow-ups", and `checks/delete-receipt-astra-role-r1.md` F7. The source lines above were re-read on main `6ac73757`. Owed: the Astra-role check; the owner's ratification and his answers to Q1–Q3; the story 01 canvas (before story 01's face build). Nothing is built.

**Estimate (PROVISIONAL, placed before build):** story effort **3–4.5 engineering days** (01 1–1.5 · 02 1–1.5 · 03 1–1.5) + the rename canvas and its ratification (0.5) + check rounds (0.5–1) = **4–6 engineering days PROVISIONAL**, plus 0.5 d if story 04 is kept. Grounded on Phase 6's repair phase (4.5–6.5 d provisional for five repairs, `../phase-6-the-honest-morning/current-phase-status.md:116`) and on Phase 7's calibration that agent-lane wall-clock is far shorter than engineering days (`../phase-7-the-desk-on-the-contract/current-phase-status.md` "Calibration"). Elapsed time is longer than effort: the owner's canvas word and the check rounds sit between the lanes.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope creep: other Floor or Workbench defects pulled in | high | the four defects and the optional two are the whole scope; others go to the BACKLOG | a story edits a face or file not named by its defect |
| A second rename overlay is copied instead of composed | medium | the Chair and the list compose the existing field's behaviour (one component or one hook), not a copy | two rename implementations with their own Enter/blur/Escape code |
| The list delete gets a second receipt species or seat | medium | the same `useUndoReceipt` and the #665 seat above the AskBar; a canvas only if that seat cannot hold | a new receipt markup or a new seat without a ratified canvas |
| The two-deletes fix hides the cause | medium | the cause is traced and named with its line before the repair; the fence covers both the timer and the target | a green fence with no named cause |
| A client-side free name races another client | low (one owner) | the hub's 409 stays the named failure row; Retry picks the next free name again | a 409 that Retry cannot clear |
| The stale rename state keeps jumping faces | medium | exit 2 fences the FINDING's stale-field rows | a rename field that appears on a face the owner did not press New Zone on |
| Same-family checks (Opus 5.5 builds and checks) | high while Codex Astra is out | label every check "Astra role (Opus 5.5 stand-in)"; Codex Astra may check on return | a check written as "Astra" without the label |

## Decisions for the owner

- **Q1 — "When I press New Zone and a zone called 'New zone' is already there, what should happen?"**
  - (a) The new zone is called "New zone 2" (then 3, …), and the rename opens so I can name it. *(Recommended: the smallest repair; no new step.)*
  - (b) No zone is made until I type its name: New Zone opens an empty name field first. *(Larger: it changes the create on every face, and the canvas must show it.)*
- **Q2 — "Where do I name a zone I make from the Chair or from the list?"** The canvas shows the choices at 1440 and 393; the owner ratifies one before build. Proposed for the canvas: on the list, the field opens in the new zone's row; on the Chair, either (a) the field opens in the Chair's receipt row, (b) New Zone takes me to the Floor with the field open, or (c) the Chair does not offer New Zone (UX-CANON §A.11: withhold a verb rather than ship it dead).
- **Q3 — "Do I want the two small face notes fixed now?"** Keep or drop each: (a) the empty CONSEQUENCES heading on a decision; (b) "unavailable" for the people sections of the brief on a fresh hub. Dropping both removes story 04.

## Decisions made (this phase)

- 2026-09-26 — the owner: "Close, and make the Floor Phase 8" (AskUserQuestion, closing Phase 7).
- 2026-09-26 — DRAFTED: the four verified Floor defects, three stories and one optional story; the list delete in the #665 seat without a canvas unless the seat cannot hold; Projects move out of Phase 8 — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- Q1–Q3 above: the owner, at ratification.
- The Chair and list rename face: the story 01 canvas, ratified by the owner before the face build.
- The cause of F7 (the timer, the revert, or the target): story 02 traces it before it repairs it.
- Where the new atlas cases live (`atlas-phase7.json` or a new `atlas-phase8.json`): story 03 decides against the atlas schema.
