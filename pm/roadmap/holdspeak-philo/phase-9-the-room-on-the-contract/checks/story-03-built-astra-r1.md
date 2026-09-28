VERDICT: **DO-NOT-RATIFY**

Reviewed story 03 through follow-up **`62375d84`**, including the ratified wording. Two new defects block merge. No repository files changed.

FINDINGS:

1. **Blocking — a refused delivery appears as successful.** A real delivery request against a draft returns `400 / update_not_published` and creates no delivery row. The Room nevertheless shows a green success chip and **MARKED DELIVERED · REFUSED**, without the reason. Reproduced through the graph rig at both widths. The `holdspeak/services/project_service.py:2169` drops the kernel outcome reason; the `web/src/features/project-room/ProjectRoomCore.tsx:1290` always uses success; the `web/src/desk/surface/egress.ts:96` always says MARKED DELIVERED. See the [1440 shot](/tmp/astra-pr686-xxu09j56/atlas-refusal-visible-1440/20260928T161918Z-case.p9.receipt_refusal_truth-astra-1440/after.png) and [393 observation](/tmp/astra-pr686-xxu09j56/atlas-refusal-visible-393/20260928T161717Z-case.p9.receipt_refusal_truth-astra-393/observation.json). **Fails Tenets 3 and 4:** contradictory status and no useful explanation.

2. **Blocking — the steward’s Review button loses the run’s review identity.** Complete a run, accept its review, reopen that run, then press Review: the button creates another review. At 393, run review `prev_d52cb…` became newly opened `prev_90bc…`; 1440 reproduces the same error. The `web/src/features/project-room/ProjectRoomCore.tsx:2102` calls `enterReview()` without the displayed `review_id`. The `tests/e2e/test_philo9_03_room_face_glass.py:726` checks only that a review posture appears. [Actual transition and response](/tmp/astra-pr686-xxu09j56/atlas-review-393/20260928T161630Z-case.p9.steward_review_identity-astra-393/observation.json). **Fails Tenets 3 and 7:** inspecting completed work silently starts different work.

3. **Receipt isolation claim is false, but the defect is inherited.** Create project B with project A’s ID in B’s name: B’s CREATE PROJECT receipt appears in A. The textual `LIKE` scope permits this. I reproduced it through real producers on both this build and `aeae7bd8`; it is **not a new story-03 blocker**. [Current probe](/tmp/astra-pr686-xxu09j56/receipt-probe.json), [base reproduction](/tmp/astra-pr686-xxu09j56/foreign-receipt-base.json). Kernel publish/delivery/run target scoping is structurally correct; the foreign delivery in my probe did not leak. **Inherited failure of Tenet 7:** a project’s record includes another project’s work.

4. **The inspected ITEMS and delivery faces match the ratified boards.** The follow-up now supplies `1 MILESTONE LATE` and `MILESTONE · 7 DAYS LATE` from the hub fields. Steward counts agree with the run. Delivery confirmation remains bound to each update: Priya/Tomas produce two rows; double-click sends once; pending/refused/unknown render; B stays clean while A retains its uncertain confirmation; Retry uses A’s original key and recipient. Drafts have no confirmation control. These rendered transitions pass independently in the [final glass run](/tmp/astra-pr686-xxu09j56/glass-final.log). The actual atlas delivery case also passes at [1440](/tmp/astra-pr686-xxu09j56/atlas-delivery-1440/20260928T162005Z-case.p9.update.delivered_row-astra-1440/observation.json) and 393.

5. **The four older fence changes are honest.** `tests/e2e/test_hs162_update_glass.py:284` checks provenance in its replacement chip. `tests/e2e/test_hs169_room_glass.py:386` deliberately limits the sticky-well rule to wide screens; F10 supplies the narrow clearance check. `tests/e2e/test_hs200_task_resume_glass.py:200` removes the xfail while retaining the assertions, which pass at 393. `tests/e2e/test_hs171_shade_glass.py:564` enforces the 12 px floor while allowing caption and token to share that size. The accepted desktop RECEIPTS overlap remains backlog.

6. **The claimed regression reds are real.** Independently replaying the existing-behavior fences against `aeae7bd8` produced **15 failures and one pass**: the expected F1/F2/F3/F7/F10/F11 failures; wide F10 already passes. [Base log](/tmp/astra-pr686-base-we5qr60c/base-red.log). Independent green runs produced [38 passes at `5c7b8d06`](/tmp/astra-pr686-xxu09j56/glass-complete-archive.log) and [40 at `62375d84`](/tmp/astra-pr686-xxu09j56/glass-final.log), covering story 03 and the four older suites across those runs. Typecheck also passed.

CONDITIONS:

Fix findings 1 and 2. Preserve the refusal reason and render its actual state. Bind Review to the run’s review, including after acceptance. Fence both real-producer transitions red before the fix and green afterward at 1440 and 393; change the words and their fences together.

MISSED:

Ranked by owner cost: **(1)** false delivery success; **(2)** historical Review opening new work; **(3)** inherited foreign-project receipt leakage. The existing tests cover successful receipts and arrival at a review screen, leaving outcome and identity unchecked.

TUESDAY:

The normal update loop works, but the owner cannot yet trust a refused delivery receipt or the Review button on a completed run.

UNKNOWN:

No full-suite rerun or exhaustive live traversal of every Room caller; `arrival-source-open` remains unobserved. Tests and walks used isolated homes and disposable snapshots, with [source hashes checked against the final head](/tmp/astra-pr686-xxu09j56/source-manifest.json). The owner’s live desk was not exercised.