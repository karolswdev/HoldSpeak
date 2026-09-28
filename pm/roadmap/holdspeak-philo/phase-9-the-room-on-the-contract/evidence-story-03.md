# Evidence - PHILO-9-03

- **Story:** PHILO-9-03 - The Room's face tells the truth (canvas first)
- **Status:** done
- **Date:** 2026-09-28

## Summary

- **The ratified design, built (the harness is not shipped).** The owner ratified the items canvas and the copy-and-confirm canvas "as drawn" on 2026-09-27 (`assets/story-03-items-canvas/`, `assets/story-03-delivery-canvas/`). The PROPOSAL blocks of `harness/ProposedProjectRoomCore.tsx`, `ProposedUpdatePosture.tsx`, `proposedUpdateController.ts` and `canvas.css` are now edits of the named product files; the shim is gone: the real backend answers (story 01's `deliveries` read-back and health/NEEDS YOU rule; story 02's `POST /api/updates/{id}/delivered` with admission).
- **F1 (one Room key).** `web/src/desk/shell.ts` `PROJECT_ROOM_KEY = "open-project-memory"` and `openProjectRoom(id)` (scope `project:<id>`, fallback `/project-memory`). All eight `openSurfaceOr("project-room", "/projects", …)` callers moved: `ChairHome.tsx` (4: the row project button, the coverage repair, the source verb, the proposal verb; the two proposal verbs lost their `?focus=proposal:` suffix, which no Room parsed), `SystemShade.tsx` (2), `RecallFace.tsx`, `MeetingReview.tsx`. Census: `web/src/desk/__tests__/projectRoomKey.test.ts` (no source file asks for `project-room`; its mutation re-adds one and the check bites).
- **F2 (the items section, Q1).** `ItemsSection` after NEEDS YOU in `ProjectRoomCore.tsx`: late `●` + `N DAYS LATE` (danger), open risk `⚠`, planned `○`, missed `✗` + `MISSED` (danger), dropped `—` + `DROPPED`; the ratified order; omitted when the read returns no item; `ITEMS UNAVAILABLE` + library `Retry` on a failed read; no control on a row; the headline `1 needs you`.
- **Copy and confirm (Q0, Q2, Q3).** `update/model.ts` (`Delivery`, `deliveries` decoded), `update/api.ts` `markDelivered`, `useUpdateController.ts` (the settled retry rule: one `{update_id, command_id, delivered_to}` held per update; a double-click is one press; a named refusal releases the key and unlocks the field; a lost answer keeps update, key and To for `Retry`), `UpdatePosture.tsx` (`DELIVERY` / `DELIVERED N` above the body of a published update, the `To` StringGadget + `Mark delivered`, the history rows, `✗ REFUSED` + the plain word with `data-code`, `⚠ NO ANSWER · RESULT UNKNOWN`, the list chip `✓ DELIVERED ×N`, `Back` in the head verbs; the claim and source ref chips are the library Button).
- **F3 (steward counts).** `StewardPosture.tsx` `runCounts`: sources from OBSERVE's coverage, `review opened` from COMPARE's `review_id`, proposals from COMPARE's count, effects from the run's EFFECT steps that completed (never a `phase:*` checkpoint); `no effect allowed` when every ACT slot was skipped `not_in_eligible_effect_kinds`; the review is shown (`REVIEW OPENED` + library `Review`, which opens the Review posture); the receipt refs are the library Button. The steward beat's face half: a refused start is named by its code (`✗ REFUSED` + `NO SAVED POLICY` for `steward_policy_required`; `useStewardController.ts` `runRefusal`).
- **F7 (RECEIPTS are writes).** A backend edit, see "Unpaid / decisions" 1: `ProjectService._read_room_receipts` adds the Room's admitted kernel receipts (publish, delivery, the steward's run, the review) by the operation's target (the project, its updates, its runs; top-level operations only; ProjectService-served operations skipped, they are already pipeline events) and the `create_project` event by its result. `egress.ts` `receiptLabel`: `mark_update_delivered` → `MARKED DELIVERED`.
- **F10.** At a narrow window (`@container surface (max-width: 559px)`) the Ask well is in the flow (`project-room.css`); a wide window keeps Condition 7 (sticky at the foot). This also pays the parked BACKLOG defect "The 393 Room: UNFINISHED opens under the ask well" (the strict xfail in `test_hs200_task_resume_glass.py` now passes; the mark is removed).
- **F11.** The update list head `UPDATES N`; the row words are separate tokens (`PUBLISHED` `REV 1`), the time in the row's time slot, the `▤` emblem.
- **F15.** The watch-source row with `suggested` set drew `Add` with no action; the hub never sets `suggested` on a source item (`project_service.py`, every source item `"suggested": False`), and the suggestion rows above carry the wired Add/Dismiss. The verb is withheld (UX-CANON §A.11); unit fence in `StewardPosture.test.tsx`.
- **Library repairs (the canvas's "PROPOSED LIBRARY REPAIRS", moved into the named files).** `surface.css` `.surface-token` 12 px; `provenance.css` `.surface-provenance-source` 12 px; `progress-plan.css` the plan rate and detail 12 px (found by this build's scan: 10 px); `inline-editor.css` the rail wraps, its chips 12 px, `.desk-editor` one shrinkable column; `gadgets.css` the mixed/cloud egress chip `--accent-hover`; `update-posture.css` the body mic and the editor column under `@container surface`; `global.css` the 44 × 44 device target for the non-`.btn` controls touched (the container-query law allows viewport media only in the shell files).
- **Fences.** `tests/e2e/test_philo9_03_room_face_glass.py` (10 tests × 1440 and 393, the real hub on an isolated HOME; every compared value read from the hub in the same test; the canvas harness's text scan, raw-button census and nine-point pointer pass by `elementFromPoint` and a real `pointermove`); vitest `projectRoomKey.test.ts`, the F3/F15/refusal cases in `StewardPosture.test.tsx`, the ratified list words in `UpdatePosture.test.tsx`, `RecallFace.test.tsx` on the new key. Atlas: four cases in `docs/internal/philo/graph/atlas-phase9.json` (`case.p9.room_items.late_row`, `case.p9.update_list.head_updates`, `case.p9.update.delivered_row`, `case.p9.room_steward_verb.owned`), both widths, written by `assets/story-03-proof/add_atlas.py`; the exclusions say why F1, F3 and F7 are glass-only.
- **Superseded fences updated in the same commit (the face they measure changed by ratification):** `test_hs162_update_glass.py` (the retired provenance secondary line → the row's ProvenanceChip), `test_hs169_room_glass.py` (Condition 7's probe holds for a wide window), `test_hs200_task_resume_glass.py` (the 393 xfail paid), `test_hs171_shade_glass.py` (three type steps → the 12 px floor puts the token at the caption's 12 px); `atlas.json` one line anchor moved by the ChairHome edit.

### The red-first matrix (red: capture 15:31:55Z on the base `aeae7bd8` = main `1f332bc3` + PHILO-9-02, its product files put in place by `swap.sh`; green: capture 15:37:52Z)

| Row | 1440 base | 393 base | 1440 branch | 393 branch |
|---|---|---|---|---|
| F1 meeting's project button | **red** (no Room) | **red** | Room opens | Room opens |
| F1 the Chair's project button / the shade's Open | **red** / **red** | **red** / **red** | green | green |
| F2 late milestone + risk as drawn | **red** "the Room shows no item"; rig `case.p9.room_items.late_row` fail | **red** | green (rig pass) | green (rig pass) |
| Mark delivered (new) | no verb (not claimed) | — | two rows read back, chip `×2`, one call per double-click, refusal / unknown / retry bound to A | the same |
| F3 steward counts | **red** `Observe 1 source · Propose 1 · Act 1 effect` | **red** | `4 sources · review opened · no proposal · no effect allowed` = the hub's run | the same |
| F7 RECEIPTS are writes | **red** `['CREATE ITEM']` only | **red** | `STEWARD RUN, MARKED DELIVERED, PUBLISH UPDATE, CREATE ITEM, CREATE PROJECT` | the same |
| F10 Steward verb / heads under the well | preservation green (rig pass) | **red** `SOURCES Steward` under the well; rig fail | green | green; mutation (sticky again at narrow) red, capture 15:46:27Z |
| F11 list words | **red** `DRAFTS 2`; rig fail | **red** | `UPDATES 2`, `PUBLISHED` `REV 1`, `▤` | the same |

- **Web unit:** baseline-subset, zero branch-new (2938 passed, capture 15:50:31Z); vitest `Test Files 324 passed`, `Tests 2938 passed`, no `Errors` line; `npm run check` green (token gate, architecture guard, typecheck, tests, build, bundle gate). Two earlier baseline runs each showed one different branch-new that passes alone 3/3 (`CapabilityAssignmentsCore` focus, `NotePullout` scroll; files this story does not touch): load flakes.
- **Preservation glass (22 files, capture 15:46:47Z):** 129 passed, 14 skipped, 4 xfailed, 1 failed: `test_hs171_rhythm_glass.py::TestRhythmFace::test_mute_toggle`, which fails the same way on the base's product files (capture 15:54:56Z: its seed posts `title` to `/api/projects`, refused by `project.create`'s schema): inherited.
- **Generated docs:** `api-reference.json`, `boundary-candidates.json`, `graph.json` regenerated; every Documentation Navigation check rc=0 (capture 15:54:21Z).
- **Shots (both widths, from the green capture):** `assets/story-03-shots/` — `items-late-first-view-*`, `items-late-section-*`, `items-empty-omitted-*`, `items-unavailable-*`, `deliver-1-after-copy-*` … `deliver-11-retried-one-row-*`, `steward-counts-*`, `receipts-writes-*`, `ask-well-first-view-*`, `update-list-words-*`, `f1-meeting-opens-room-*`, `f1-chair-opens-room-*`, `f1-shade-opens-room-*`, with the measurements beside them (`*.json`). Walked by eye at both widths.

### Round two — Codex Astra r1 on `62375d84` DO-NOT-RATIFY (`checks/story-03-built-astra-r1.md`), paid

- **Finding 1 (blocking) PAID — a refused delivery appeared successful.** `holdspeak/services/project_service.py` `_read_room_receipts` keeps the kernel receipt's named outcome as `reason` for a non-success; `web/src/desk/surface/egress.ts` `receiptFace(outcome)` draws every outcome as what happened (only `ok`/`succeeded` is the success chip; `refused` → `✗ REFUSED` + the plain reason; `error`/`failed` → `✗ FAILED`; `cancelled` → `— CANCELLED`; `indeterminate` → `⚠ RESULT UNKNOWN`), and `receiptLabel` says `MARK DELIVERED` for a mark that did not happen. `ProjectRoomCore.tsx` RECEIPTS uses both. Closed as a class: `web/src/desk/__tests__/receiptFace.test.ts` is the census of every outcome the list can carry (the pipeline's two, the kernel's five). One refusal-word table (`refusalWord`) now serves the delivery line, the steward's start and RECEIPTS. Fence `test_a_refused_delivery_receipt_says_refused_and_why[1440, 393]` through the real producer (POST `/delivered` on a draft: 400, no row): red on `62375d84` (`{'lead': 'success', 'text': '● MARKED DELIVERED REFUSED'}`), green after.
- **Finding 2 (blocking) PAID — the steward's Review opened new work.** `review/api.ts` `getReview`; `useReviewController.ts` `enterReview(reviewId?)` opens THAT review by its id (a settled one read-only, checkpointed, no verb that starts work); `StewardPosture` passes the run's `review_id`; `ReviewPosture` exposes `data-review-id` / `data-review-status`. Fence `test_review_on_a_completed_run_opens_that_review_even_after_acceptance[1440, 393]` (run, accept its review, reopen the run, press Review): red on `62375d84` (the press opened `prev_…` new: the hub's delta held a new open review), green after (the shown review is the run's, `accepted`; no open review on the hub). The existing steward fence now checks the identity too.
- **Finding 3 (inherited) PAID — a foreign project's receipt in this Room.** The LIKE is now a prefilter; `_summary_names` claims a pipeline receipt only when its summary names the project's id as a value exactly (a created project's own `id` for `create_project`; a truncated summary by an exact JSON-string match). Fence `test_receipts_hold_only_this_rooms_work[1440, 393]` (project B named `Mirror of <A's id>`): red on `62375d84` (A's read held 2 `create_project`), green after.

- **Round two proof:** red capture 16:32:22Z (the three fences on `62375d84`'s product files: 6 failed, each an assertion on the rendered face or the hub's record); green capture 16:35:53Z (374 passed: the story 03 glass, 14 tests × 2 widths, the Room backend fences and the atlas fences; the rig 8 of 8; the 16:32:48Z green attempt failed only on the atlas line anchors the edits moved, re-anchored by `add_atlas.py`); web unit 16:39:01Z (zero branch-new, vitest 325 files / 2941 tests, `npm run check` green); docs navigation 16:42:03Z (every check rc=0); preservation 16:42:20Z (129 passed; the one red is the inherited `test_mute_toggle`).

### Muad'Dib's rulings on PR #686 (2026-09-28), paid

- (1) the `_read_room_receipts` edit stays; (2) the 1440 RECEIPTS overlap stays on the BACKLOG; (4) the scheduled `steward_policy_required` stays on the BACKLOG; (5) the four fence updates stand.
- (3) BUILD WHAT WAS RATIFIED, built: `web/src/features/project-room/model.ts` `healthReasonWords` (`N OVERDUE` with every overdue input a milestone → `N MILESTONE(S) LATE`) and `needsYouWhyWords` (a `source: item`, `kind: milestone` row's `OVERDUE · 7 DAYS` → `MILESTONE · 7 DAYS LATE`); `ProjectRoomCore.tsx` renders both; the hub's words are unchanged (read back in the same fence). Fence `test_the_late_words_are_the_canvas_words[1440, 393]`: red on the PR's first head `5c7b8d06` (`['1 OVERDUE']`, capture below), green after; the items fence now asserts `1 MILESTONE LATE` too.
- The walk of the Chair's proposal verbs (`assets/story-03-proof/walk_chair_proposals.py`, isolated hub, capture below): `arrival-proposal-open` opens the Room titled "Payments ledger cutover" and the Room lists the proposal, at 1440 and 393. `arrival-source-open` was not reached: it is drawn only inside a row whose SOURCES disclosure merges several projections, and the seed produced none.

### Unpaid / decisions for Muad'Dib (as first filed; see the rulings above)

1. **A ProjectService edit in this lane.** The story says a backend change goes to story 01's lane by patch; story 01 is merged and has no live lane, and "RECEIPTS lists the writes (create, publish, steward run)" cannot be green without it (story 01's evidence: "a publication or a delivery is not yet a Room receipt"). The edit is `_read_room_receipts` plus two module constants in `holdspeak/services/project_service.py`; the Room backend fences (`test_philo9_room_contract.py`, `test_philo9_mark_delivered.py`, `test_hs174_reach_wire.py`, `test_philo9_steward_lifecycle.py`) pass in the green capture. Rule it in or send it back.
2. **The 1440 RECEIPTS overlap is NOT repaired.** The story note asks for it; the ratified items canvas draws it ("the body scrolls it clear; the round-two repair is the narrow-window one") and Condition 7 keeps the well sticky at the foot of a wide window. A repair needs a design ruling: the well out of the scroll body (the window foot) or no longer always in view. The 1440 fence asserts no VERB under the well (green); a head at the fold may lie under it (`items-late-section-1440.png`). BACKLOG row added.
3. **Health and NEEDS YOU words are story 01's, not the canvas's.** The canvas's shim drew `1 MILESTONE LATE` and `MILESTONE · 7 DAYS LATE`; the hub says `1 OVERDUE` and `OVERDUE · 7 DAYS` (`project_service.py` `_room_overdue_milestone_items`, the health reason). The face shows the hub's words; the ITEMS row says `7 DAYS LATE` as drawn. A one-line backend change if the canvas words are wanted. BACKLOG row added.
4. **The scheduler's `steward_policy_required`** lives in the trigger's receipt; no Room read carries it, so the face names it only when a start from the face is refused. Not fenced through the hub (an owner start is never refused so); unit-fenced. BACKLOG row added.

### Unknown

- The Chair's proposal verbs (`arrival-source-open`, `arrival-proposal-open`) now open the Room of the row's project, not a proposal focus (no Room parsed `?focus=proposal:`); not walked in a real hub (a proposal needs a meeting with extraction).

## Proof

### Captured run — 2026-09-28T15:17:13Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/red_base.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7687601c1a2ec35dd82d9aba78d74718ca73fac

```text
base = aeae7bd81d365b999f9b859307dc368926356545 (main 1f332bc3 + PHILO-9-02)
✓ built in 15.49s
 4 files changed, 158 insertions(+), 30 deletions(-)
(an empty diffstat above = the base's product files are in place)
E               AssertionError: the Room shows no item: the late milestone is not on the face
E               assert []
E               AssertionError: ✓ Observe 1 source | ✓ Compare | ✓ Propose 1 | ✓ Act 1 effect | ✓ Verify | ✓ Record
E               assert '4 source' in '✓ Observe 1 source | ✓ Compare | ✓ Propose 1 | ✓ Act 1 effect | ✓ Verify | ✓ Record'
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E               AssertionError: {'created': ['CREATE ITEM'], 'published': ['CREATE ITEM'], 'ran': ['CREATE ITEM']}
E               assert ('CREATE PROJECT' in ['CREATE ITEM'])
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E               AssertionError: ✓ Observe 1 source | ✓ Compare | ✓ Propose 1 | ✓ Act 1 effect | ✓ Verify | ✓ Record
E               assert '4 source' in '✓ Observe 1 source | ✓ Compare | ✓ Propose 1 | ✓ Act 1 effect | ✓ Verify | ✓ Record'
E               AssertionError: {'created': ['CREATE ITEM'], 'published': ['CREATE ITEM'], 'ran': ['CREATE ITEM']}
E               assert ('CREATE PROJECT' in ['CREATE ITEM'])
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E               AssertionError: the Room shows no item: the late milestone is not on the face
E               assert []
E               AssertionError: DRAFTS 2
E               assert 'DRAFTS 2' == 'UPDATES 2'
E                 
E                 - UPDATES 2
E                 + DRAFTS 2
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 45000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=update-list-item]:has([data-update-id='pupd_1fbad36eb12b46a794a43284747100a3'])").first
E                   AssertionError: ['SOURCES Steward', 'SOURCES', 'Steward']
E                   assert ['SOURCES Ste...S', 'Steward'] == []
E                     
E                     Left contains 3 more items, first extra item: 'SOURCES Steward'
E                     Use -v to get more diff
E               AssertionError: DRAFTS 2
E               assert 'DRAFTS 2' == 'UPDATES 2'
E                 
E                 - UPDATES 2
E                 + DRAFTS 2
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 45000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=update-list-item]:has([data-update-id='pupd_ad79841cb6cc462a85eaa3e7e7c5ca18'])").first
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 45000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=update-list-item]:has([data-update-id='pupd_5d8d985f091a4847963c2892ed7119d1'])").first
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 45000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=update-list-item]:has([data-update-id='pupd_fbf84d7b292e4d129501746a010b0fbd'])").first
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]
19 failed, 1 passed in 121.52s (0:02:01)
case.p9.room_items.late_row 1440 exit=1 VERDICT: fail terminal=settled
case.p9.room_items.late_row 393 exit=1 VERDICT: fail terminal=settled
case.p9.update_list.head_updates 1440 exit=1 VERDICT: fail terminal=settled
case.p9.update_list.head_updates 393 exit=1 VERDICT: fail terminal=settled
case.p9.update.delivered_row 1440 exit=1 VERDICT: blocked terminal=None
case.p9.update.delivered_row 393 exit=1 VERDICT: blocked terminal=None
case.p9.room_steward_verb.owned 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 393 exit=1 VERDICT: fail terminal=settled
NOTE: predicate: the named text scope is absent or hidden
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'values', 'windows']).
NOTE: predicate: the named text scope is absent or hidden
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'values', 'windows']).
NOTE: predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 731, 'y': 343, 'w': 68, 'h': 24}
NOTE: predicate: a covering element owns hit points: [{'x': 302, 'y': 495, 'owned': False, 'owner': 'div#surface-project-memory > div.desk-surface-body > div.room-body > div.room-section-rise.room-ask-container > div.roo
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['focus', 'focus_label']).
NOTE: predicate: 'UPDATES 1' NOT in observe_at text
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'values', 'visible']).
NOTE: predicate: 'UPDATES 1' NOT in observe_at text
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'values', 'visible', 'windows
NOTE: BLOCKED: ui step click on "[data-update-id='pupd_8ede2f0d8c524766a366b71498493fee']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
NOTE: BLOCKED: ui step click on "[data-update-id='pupd_c3b1daae22b84ce990bf70d225ffc12a']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
✓ built in 8.52s
 26 files changed, 891 insertions(+), 122 deletions(-)
```

### Captured run — 2026-09-28T15:24:51Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/green.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a7687601c1a2ec35dd82d9aba78d74718ca73fac

```text
HEAD = aeae7bd81d365b999f9b859307dc368926356545; product diff vs the base aeae7bd8:
 27 files changed, 941 insertions(+), 125 deletions(-)
✓ built in 7.69s
ERROR    holdspeak.steward_contract:steward_contract.py:332 steward run pstrun_ab9742197f0c587eaee8c80ac524a301 raised outside its phases
    self._close_run(handle, run_id, "failed", "failed", type(exc).__name__[:60] or "failed",
ERROR    holdspeak.web.routes.project_updates:runtime_support.py:71 Failed to mark the update delivered: injected after the insert
_________ test_l3_a_known_failure_ends_the_run_failed_with_one_receipt _________
ERROR    holdspeak.project_steward:project_steward_service.py:783 Run pstrun_2b4913ca256453d7b96dca7458d2dfad failed: the review could not open
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[1440]
PASSED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_known_failure_ends_the_run_failed_with_one_receipt
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]
PASSED tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]
FAILED tests/unit/test_philo9_04_atlas.py::test_the_general_fences_hold_for_phase9[test_every_desk_face_case_crosses_the_gate_first]
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase9.json]
2 failed, 360 passed in 129.58s (0:02:09)
case.p9.room_items.late_row 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_items.late_row 393 exit=0 VERDICT: pass terminal=settled
case.p9.update_list.head_updates 1440 exit=0 VERDICT: pass terminal=settled
case.p9.update_list.head_updates 393 exit=0 VERDICT: pass terminal=settled
case.p9.update.delivered_row 1440 exit=0 VERDICT: pass terminal=settled
case.p9.update.delivered_row 393 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 393 exit=0 VERDICT: pass terminal=settled
rig cases not passing: 0
```

### Captured run — 2026-09-28T15:31:55Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/red_base.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 363efc93c10c0d30cf306ae7a688e29442b4e881

```text
base = aeae7bd81d365b999f9b859307dc368926356545 (main 1f332bc3 + PHILO-9-02)
✓ built in 7.83s
 4 files changed, 158 insertions(+), 30 deletions(-)
(an empty diffstat above = the base's product files are in place)
E               AssertionError: ✓ Observe 1 source | ✓ Compare | ✓ Propose 1 | ✓ Act 1 effect | ✓ Verify | ✓ Record
E               assert '4 source' in '✓ Observe 1 source | ✓ Compare | ✓ Propose 1 | ✓ Act 1 effect | ✓ Verify | ✓ Record'
E               AssertionError: {'created': ['CREATE ITEM'], 'published': ['CREATE ITEM'], 'ran': ['CREATE ITEM']}
E               assert ('CREATE PROJECT' in ['CREATE ITEM'])
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E               AssertionError: the Room shows no item: the late milestone is not on the face
E               assert []
E               AssertionError: ✓ Observe 1 source | ✓ Compare | ✓ Propose 1 | ✓ Act 1 effect | ✓ Verify | ✓ Record
E               assert '4 source' in '✓ Observe 1 source | ✓ Compare | ✓ Propose 1 | ✓ Act 1 effect | ✓ Verify | ✓ Record'
E               AssertionError: {'created': ['CREATE ITEM'], 'published': ['CREATE ITEM'], 'ran': ['CREATE ITEM']}
E               assert ('CREATE PROJECT' in ['CREATE ITEM'])
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=room-body]") to be visible
E                   AssertionError: ['SOURCES Steward', 'SOURCES', 'Steward']
E                   assert ['SOURCES Ste...S', 'Steward'] == []
E                     
E                     Left contains 3 more items, first extra item: 'SOURCES Steward'
E                     Use -v to get more diff
E               AssertionError: the Room shows no item: the late milestone is not on the face
E               assert []
E               AssertionError: DRAFTS 2
E               assert 'DRAFTS 2' == 'UPDATES 2'
E                 
E                 - UPDATES 2
E                 + DRAFTS 2
E               AssertionError: DRAFTS 2
E               assert 'DRAFTS 2' == 'UPDATES 2'
E                 
E                 - UPDATES 2
E                 + DRAFTS 2
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 45000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=update-list-item]:has([data-update-id='pupd_f224b13e64fa4a24a160791faa809ef4'])").first
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 45000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=update-list-item]:has([data-update-id='pupd_aeff8eefeb4948f6a777be54b72a11e2'])").first
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 45000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=update-list-item]:has([data-update-id='pupd_bc13a293d2c64eab8ef93347edf5d0cf'])").first
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 45000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=update-list-item]:has([data-update-id='pupd_849ef6ec906546aeaa64768c2a9fb126'])").first
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]
19 failed, 1 passed in 111.77s (0:01:51)
case.p9.room_items.late_row 1440 exit=1 VERDICT: fail terminal=settled
case.p9.room_items.late_row 393 exit=1 VERDICT: fail terminal=settled
case.p9.update_list.head_updates 1440 exit=1 VERDICT: fail terminal=settled
case.p9.update_list.head_updates 393 exit=1 VERDICT: fail terminal=settled
case.p9.update.delivered_row 1440 exit=1 VERDICT: blocked terminal=None
case.p9.update.delivered_row 393 exit=1 VERDICT: blocked terminal=None
case.p9.room_steward_verb.owned 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 393 exit=1 VERDICT: fail terminal=settled
NOTE: predicate: the named text scope is absent or hidden
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'values', 'windows']).
NOTE: predicate: the named text scope is absent or hidden
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'values', 'windows']).
NOTE: predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 731, 'y': 343, 'w': 68, 'h': 24}
NOTE: predicate: a covering element owns hit points: [{'x': 302, 'y': 495, 'owned': False, 'owner': 'div#surface-project-memory > div.desk-surface-body > div.room-body > div.room-section-rise.room-ask-container > div.roo
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['focus', 'focus_label']).
NOTE: predicate: 'UPDATES 1' NOT in observe_at text
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'values', 'visible']).
NOTE: predicate: 'UPDATES 1' NOT in observe_at text
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'values', 'visible', 'windows
NOTE: BLOCKED: ui step click on "[data-update-id='pupd_f14fb7e7859446ce84ea9a2279317a0e']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
NOTE: BLOCKED: ui step click on "[data-update-id='pupd_1a10800f18fa46aa9b5ce50e2187553a']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
✓ built in 4.38s
 26 files changed, 891 insertions(+), 122 deletions(-)
```

### Captured run — 2026-09-28T15:37:52Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 363efc93c10c0d30cf306ae7a688e29442b4e881

```text
HEAD = aeae7bd81d365b999f9b859307dc368926356545; product diff vs the base aeae7bd8:
 27 files changed, 941 insertions(+), 125 deletions(-)
✓ built in 4.24s
ERROR    holdspeak.steward_contract:steward_contract.py:332 steward run pstrun_f0dcec5fde3059809a11bb54c8f767af raised outside its phases
    self._close_run(handle, run_id, "failed", "failed", type(exc).__name__[:60] or "failed",
_________ test_l3_a_known_failure_ends_the_run_failed_with_one_receipt _________
ERROR    holdspeak.project_steward:project_steward_service.py:783 Run pstrun_da89d8b9f9d152d5853d4c2c842b8408 failed: the review could not open
ERROR    holdspeak.web.routes.project_updates:runtime_support.py:71 Failed to mark the update delivered: injected after the insert
PASSED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_known_failure_ends_the_run_failed_with_one_receipt
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[1440]
PASSED tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]
362 passed in 105.83s (0:01:45)
case.p9.room_items.late_row 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_items.late_row 393 exit=0 VERDICT: pass terminal=settled
case.p9.update_list.head_updates 1440 exit=0 VERDICT: pass terminal=settled
case.p9.update_list.head_updates 393 exit=0 VERDICT: pass terminal=settled
case.p9.update.delivered_row 1440 exit=0 VERDICT: pass terminal=settled
case.p9.update.delivered_row 393 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 393 exit=0 VERDICT: pass terminal=settled
rig cases not passing: 0
```

### Captured run — 2026-09-28T15:41:04Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/mutation_sticky_well.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 363efc93c10c0d30cf306ae7a688e29442b4e881

```text
307:.room-ask-container {
308-  position: sticky;
309-  bottom: 0;
310-  z-index: var(--desk-z-local);
✓ built in 4.35s
2 passed in 10.36s
✓ built in 4.49s
```

### Captured run — 2026-09-28T15:41:24Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/preserve.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 363efc93c10c0d30cf306ae7a688e29442b4e881

```text
FAILED tests/e2e/test_hs171_shade_glass.py::test_shade_artboard_1440 - Assert...
FAILED tests/e2e/test_hs171_shade_glass.py::test_shade_artboard_393 - Asserti...
FAILED tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_mute_toggle
3 failed, 127 passed, 14 skipped, 4 xfailed in 232.00s (0:03:52)
```

### Captured run — 2026-09-28T15:46:27Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/mutation_sticky_well.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9b8298971187f0f2a61ba23364717f40ab65881c

```text
307-.room-ask-container {
308:  position: sticky;
309-  bottom: 0;
310-  z-index: var(--desk-z-local);
--
319-  .room-ask-container {
320:    position: sticky;
321-  }
322-}
✓ built in 4.58s
E                   AssertionError: ['ITEMS 5', 'ITEMS 5']
E                   assert ['ITEMS 5', 'ITEMS 5'] == []
E                     
E                     Left contains 2 more items, first extra item: 'ITEMS 5'
E                     Use -v to get more diff
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[393]
1 failed, 1 passed in 10.21s
✓ built in 4.50s
```

### Captured run — 2026-09-28T15:46:47Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/preserve.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9b8298971187f0f2a61ba23364717f40ab65881c

```text
FAILED tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_mute_toggle
1 failed, 129 passed, 14 skipped, 4 xfailed in 223.18s (0:03:43)
```

### Captured run — 2026-09-28T15:50:31Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/web_unit.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9b8298971187f0f2a61ba23364717f40ab65881c

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2938 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
 Test Files  324 passed (324)
      Tests  2938 passed (2938)
   Duration  55.21s (transform 48.39s, setup 47.58s, import 160.67s, tests 164.35s, environment 186.07s)
token gate: clean (11 allow-listed exceptions, all in use)
 Test Files  324 passed (324)
      Tests  2938 passed (2938)
✓ built in 4.36s
bundle gate passed (Desk JS 1334669 B; Desk CSS 323598 B; source maps 0)
baseline=0 vitest=0 check=0
```

### Captured run — 2026-09-28T15:54:21Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9b8298971187f0f2a61ba23364717f40ab65881c

```text
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:5> python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.003s

OK
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:5> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:6> python3 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:6> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:7> python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:7> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:8> python3 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:8> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:9> python3 scripts/philo_api_reference.py --check
API reference checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:9> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:10> python3 scripts/philo_boundary_census.py --check
Boundary candidate census checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:10> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:11> python3 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:11> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:12> python3 scripts/philo_config_reference.py --check
Configuration declaration reference is current
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:12> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:13> python3 scripts/philo_graph_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:13> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:14> python3 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:14> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:15> python3 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:15> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:16> python3 scripts/check_doc_coverage.py --check
Documentation coverage checked.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:16> echo 'rc=0'
rc=0
```

### Captured run — 2026-09-28T15:54:56Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/inherited_mute.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2e5c21135ce7401d7a63ea3785bc9e00bec5015e

```text
✓ built in 4.38s
E       AssertionError: HTTP 400: {'status': 400, 'payload': {'success': False, 'error': "Invalid arguments for project.create: Additional properties are not allowed ('title' was unexpected)"}}
1 failed, 6 deselected in 9.11s
✓ built in 4.60s
```

### Captured run — 2026-09-28T16:09:24Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/red_late_words.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c1236f77bf61112cedb13b9fac9a6b3cd5303635

```text
✓ built in 4.60s
E               AssertionError: ['1 OVERDUE']
E               assert ('1 MILESTONE LATE' in ['1 OVERDUE'])
E               AssertionError: ['1 OVERDUE']
E               assert ('1 MILESTONE LATE' in ['1 OVERDUE'])
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_late_words_are_the_canvas_words[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_late_words_are_the_canvas_words[1440]
2 failed in 8.81s
✓ built in 4.34s
```

### Captured run — 2026-09-28T16:09:43Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/glass.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c1236f77bf61112cedb13b9fac9a6b3cd5303635

```text
✓ built in 4.89s
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_late_words_are_the_canvas_words[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_late_words_are_the_canvas_words[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]
22 passed in 42.92s
```

### Captured run — 2026-09-28T16:10:32Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/walk.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c1236f77bf61112cedb13b9fac9a6b3cd5303635

```text
WALK {"width": 1440, "proposal_id": "prop-aab689b15948", "chair_rows": ["NO DUE DATE · PROPOSED · CUTOVER SYNC · CHANGED JUST NOW"], "arrival-proposal-open": {"present": 1, "opened": "Payments ledger cutover", "room_names_project": true, "proposal_in_room": true}, "arrival-source-open": {"present": 0}}
WALK {"width": 393, "proposal_id": "prop-d32cf3381866", "chair_rows": ["NO DUE DATE · PROPOSED · CUTOVER SYNC · CHANGED JUST NOW"], "arrival-proposal-open": {"present": 1, "opened": "Payments ledger cutover", "room_names_project": true, "proposal_in_room": true}, "arrival-source-open": {"present": 0}}
2 passed in 23.69s
```

### Captured run — 2026-09-28T16:32:22Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/red_r2.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ce027bf0916030160a254b1205984ba034250a46

```text
✓ built in 4.62s
E               AssertionError: [{'at': 1790613150.645154, 'caller': None, 'id': '2de0c495-9e18-490c-be89-380f2a971151', 'identity': None, ...}, {'at': 1790613150.63493, 'caller': None, 'id': 'c7143287-7244-4cc4-af37-ebe38344d38a', 'identity': None, ...}]
E               assert 2 == 1
E                +  where 2 = <built-in method count of list object at 0x122ed4940>('create_project')
E                +    where <built-in method count of list object at 0x122ed4940> = ['create_project', 'create_project'].count
E               AssertionError: [{'at': 1790613150.631618, 'caller': None, 'id': '9053c948-ef96-42e3-984b-abb3f1994fbf', 'identity': None, ...}, {'at': 1790613150.6202629, 'caller': None, 'id': '1ec8ee22-a0c5-479f-8efc-fa122bd8f3cc', 'identity': None, ...}]
E               assert 2 == 1
E                +  where 2 = <built-in method count of list object at 0x10fca2a40>('create_project')
E                +    where <built-in method count of list object at 0x10fca2a40> = ['create_project', 'create_project'].count
E               AssertionError: {'code': None, 'lead': 'success', 'text': '● MARKED DELIVERED REFUSED'}
E               assert 'success' == 'failure'
E                 
E                 - failure
E                 + success
E               AssertionError: {'code': None, 'lead': 'success', 'text': '● MARKED DELIVERED REFUSED'}
E               assert 'success' == 'failure'
E                 
E                 - failure
E                 + success
E               AssertionError: {'from_sequence': 0, 'materiality_version': 'v1', 'opened_at': '2026-09-28T16:32:40+00:00', 'project_id': 'proj-323457fded18', ...}
E               assert not ('prev_d6d9ef5b96014a8ca67022d42db3f2e3')
E                +  where 'prev_d6d9ef5b96014a8ca67022d42db3f2e3' = <built-in method get of dict object at 0x12195db80>('review_id')
E                +    where <built-in method get of dict object at 0x12195db80> = {'from_sequence': 0, 'materiality_version': 'v1', 'opened_at': '2026-09-28T16:32:40+00:00', 'project_id': 'proj-323457fded18', ...}.get
E               AssertionError: {'from_sequence': 0, 'materiality_version': 'v1', 'opened_at': '2026-09-28T16:32:40+00:00', 'project_id': 'proj-5c221faeb896', ...}
E               assert not ('prev_d0952b45763d495e93f95dfedb9df9b8')
E                +  where 'prev_d0952b45763d495e93f95dfedb9df9b8' = <built-in method get of dict object at 0x11ddb2a80>('review_id')
E                +    where <built-in method get of dict object at 0x11ddb2a80> = {'from_sequence': 0, 'materiality_version': 'v1', 'opened_at': '2026-09-28T16:32:40+00:00', 'project_id': 'proj-5c221faeb896', ...}.get
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_hold_only_this_rooms_work[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_hold_only_this_rooms_work[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refused_delivery_receipt_says_refused_and_why[1440]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refused_delivery_receipt_says_refused_and_why[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_review_on_a_completed_run_opens_that_review_even_after_acceptance[393]
FAILED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_review_on_a_completed_run_opens_that_review_even_after_acceptance[1440]
6 failed in 15.69s
✓ built in 4.49s
```

### Captured run — 2026-09-28T16:32:48Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/green.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** ce027bf0916030160a254b1205984ba034250a46

```text
HEAD = 62375d847f6f0309b821c24d2926125c4daebcf3; product diff vs the base aeae7bd8:
 46 files changed, 1307 insertions(+), 179 deletions(-)
✓ built in 4.42s
ERROR    holdspeak.web.routes.project_updates:runtime_support.py:71 Failed to mark the update delivered: injected after the insert
_________ test_l3_a_known_failure_ends_the_run_failed_with_one_receipt _________
ERROR    holdspeak.project_steward:project_steward_service.py:792 Run pstrun_8f5e295d44bd5aaf8943d54fb72320e5 failed: the review could not open
ERROR    holdspeak.steward_contract:steward_contract.py:332 steward run pstrun_59f447e1e14659839169c5ef125c1d0c raised outside its phases
    self._close_run(handle, run_id, "failed", "failed", type(exc).__name__[:60] or "failed",
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[1440]
PASSED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_known_failure_ends_the_run_failed_with_one_receipt
PASSED tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_review_on_a_completed_run_opens_that_review_even_after_acceptance[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_review_on_a_completed_run_opens_that_review_even_after_acceptance[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_late_words_are_the_canvas_words[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_late_words_are_the_canvas_words[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refused_delivery_receipt_says_refused_and_why[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refused_delivery_receipt_says_refused_and_why[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_hold_only_this_rooms_work[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_hold_only_this_rooms_work[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase9.json]
1 failed, 373 passed in 92.56s (0:01:32)
case.p9.room_items.late_row 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_items.late_row 393 exit=0 VERDICT: pass terminal=settled
case.p9.update_list.head_updates 1440 exit=0 VERDICT: pass terminal=settled
case.p9.update_list.head_updates 393 exit=0 VERDICT: pass terminal=settled
case.p9.update.delivered_row 1440 exit=0 VERDICT: pass terminal=settled
case.p9.update.delivered_row 393 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 393 exit=0 VERDICT: pass terminal=settled
rig cases not passing: 0
```

### Captured run — 2026-09-28T16:35:53Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ce9e04340c7c616144e67d6a16b871ffa64f384

```text
HEAD = 62375d847f6f0309b821c24d2926125c4daebcf3; product diff vs the base aeae7bd8:
 46 files changed, 1307 insertions(+), 179 deletions(-)
✓ built in 4.57s
ERROR    holdspeak.web.routes.project_updates:runtime_support.py:71 Failed to mark the update delivered: injected after the insert
_________ test_l3_a_known_failure_ends_the_run_failed_with_one_receipt _________
ERROR    holdspeak.project_steward:project_steward_service.py:792 Run pstrun_68eb69d426b355358570cb9a70c71924 failed: the review could not open
ERROR    holdspeak.steward_contract:steward_contract.py:332 steward run pstrun_c6fa508bc18d5cbd855314b207e89802 raised outside its phases
    self._close_run(handle, run_id, "failed", "failed", type(exc).__name__[:60] or "failed",
PASSED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_known_failure_ends_the_run_failed_with_one_receipt
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[1440]
PASSED tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_meetings_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_list_the_writes_after_each_transition[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_chairs_project_button_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_shades_project_row_opens_the_room[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_ask_well_covers_no_verb_or_head[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_steward_counts_equal_the_run[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_review_on_a_completed_run_opens_that_review_even_after_acceptance[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_late_milestone_and_a_risk_show_as_drawn[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_review_on_a_completed_run_opens_that_review_even_after_acceptance[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_late_words_are_the_canvas_words[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refused_delivery_receipt_says_refused_and_why[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_the_late_words_are_the_canvas_words[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_a_refused_delivery_receipt_says_refused_and_why[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_hold_only_this_rooms_work[1440]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_receipts_hold_only_this_rooms_work[393]
PASSED tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]
374 passed in 96.86s (0:01:36)
case.p9.room_items.late_row 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_items.late_row 393 exit=0 VERDICT: pass terminal=settled
case.p9.update_list.head_updates 1440 exit=0 VERDICT: pass terminal=settled
case.p9.update_list.head_updates 393 exit=0 VERDICT: pass terminal=settled
case.p9.update.delivered_row 1440 exit=0 VERDICT: pass terminal=settled
case.p9.update.delivered_row 393 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 1440 exit=0 VERDICT: pass terminal=settled
case.p9.room_steward_verb.owned 393 exit=0 VERDICT: pass terminal=settled
rig cases not passing: 0
```

### Captured run — 2026-09-28T16:39:01Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/web_unit.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 046bc1b43344c22c3d258abc5657f4358580e880

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2941 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
 Test Files  325 passed (325)
      Tests  2941 passed (2941)
   Duration  34.69s (transform 19.19s, setup 30.61s, import 100.06s, tests 93.80s, environment 109.72s)
token gate: clean (11 allow-listed exceptions, all in use)
 Test Files  325 passed (325)
      Tests  2941 passed (2941)
✓ built in 4.49s
bundle gate passed (Desk JS 1335414 B; Desk CSS 323598 B; source maps 0)
baseline=0 vitest=0 check=0
```

### Captured run — 2026-09-28T16:42:03Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 046bc1b43344c22c3d258abc5657f4358580e880

```text
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:5> python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.003s

OK
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:5> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:6> python3 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:6> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:7> python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:7> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:8> python3 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:8> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:9> python3 scripts/philo_api_reference.py --check
API reference checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:9> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:10> python3 scripts/philo_boundary_census.py --check
Boundary candidate census checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:10> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:11> python3 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:11> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:12> python3 scripts/philo_config_reference.py --check
Configuration declaration reference is current
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:12> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:13> python3 scripts/philo_graph_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:13> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:14> python3 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:14> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:15> python3 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:15> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:16> python3 scripts/check_doc_coverage.py --check
Documentation coverage checked.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/docs_nav.sh:16> echo 'rc=0'
rc=0
```

### Captured run — 2026-09-28T16:42:20Z

- **Command:** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/preserve.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 046bc1b43344c22c3d258abc5657f4358580e880

```text
FAILED tests/e2e/test_hs171_rhythm_glass.py::TestRhythmFace::test_mute_toggle
1 failed, 129 passed, 14 skipped, 4 xfailed in 192.66s (0:03:12)
```
