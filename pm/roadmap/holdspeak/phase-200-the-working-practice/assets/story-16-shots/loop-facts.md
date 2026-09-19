# HS-200-16 loop facts -- the two-working-day daily loop

Viewport: **1440px** (the walk runs once per width; its twin is `loop-facts-393.json` / `.md`)
Generated: 2026-09-18T20:50:17
Attended by the owner: **False**

## Three legs, kept apart

| Leg | State |
|-----|-------|
| fixture_proven | everything in `stations`, `facts` and `shots`: a real hub, real faces, controlled adapters, no live model |
| live_model | NOT RUN. R16-1 keeps the live-model leg out of this rig; no measured semantic result below comes from a real model. |
| owner_usefulness_judgment | ACCEPTED BY OWNER RULING 2026-09-19, NOT OBSERVED. The owner ruled "all walks may be considered as passed", which closes AC3 (the user completes the path through normal controls without implementation guidance) as ACCEPTED. Nobody watched a human complete this loop: no attended walk happened, none is simulated here, and no measurement below comes from one. Acceptance is the owner's judgment; it is not evidence that the path was walked. |

## Identity (read from the running product)

| Field | Value |
|-------|-------|
| backend_revision | `a8458b93cb66eb19719360e85e7e915bb3d46438` |
| backend_version | `0.4.0` |
| capture_caveat | `process_start_reported and database_id_reported come from a capture cached once per OS PROCESS (holdspeak/runtime_identity.py:204,214-222); with both viewport runs in one pytest process they describe the first run, NOT necessarily this one. The database this run actually used is database_id_this_run below, taken from the uncached `database_identity()`.` |
| config_revision | `4f4ed4bc5f9940ac` |
| database_id_reported | `bbafc4e36e2f02a6` |
| database_id_this_run | `bbafc4e36e2f02a6` |
| day2_database_id_this_run | `bbafc4e36e2f02a6` |
| frontend_build | `0fe67be374a1cd63` |
| process_start_reported | `2026-09-18T20:50:22.850121` |
| repair | `[]` |
| schema_version_loaded | `79` |

## Model identity

| Field | Value |
|-------|-------|
| brief_adapter | `controlled OpenAI-compatible probe on 127.0.0.1 (R16-1)` |
| brief_boundary | `private_network` |
| brief_generator | `model:ia_6cda2385f5314edf88ccfe95944a78db` |
| brief_generator_host | `127.0.0.1` |
| brief_generator_model | `QWEN3 35B` |
| brief_host | `127.0.0.1` |
| brief_model | `QWEN3 35B` |
| brief_route_state | `ready` |
| live_model | `False` |
| meeting_extractor_model | `test-model` |
| meeting_extractor_provider | `ScriptedIntel` |

## The day boundary

| Field | Value |
|-------|-------|
| clock_mutation | none -- the product exposes no clock-injection seam |
| day1_meeting_started_at | 2026-09-17T11:00:00 |
| earlier_day | the day-1 meeting is imported through the product's own `started_at_ms` control; the faces date its records from the meeting (holdspeak/services/recall_service.py:249-251) |
| same_seam_as | tests/e2e/test_hs200_continuity_glass.py::TestContinuityGlass::test_chain_survives_a_hub_restart |
| seam | hub restart onto the same HOME and the same database file |

## Stations

| Day | Station | Active s | Corrections | Abandoned | Source coverage |
|-----|---------|----------|-------------|-----------|-----------------|
| 1 | day1-brief — prepare and keep the preparation brief | 3.48 | 0 | 0 | 4 of 5 available · complete=False |
| 1 | day1-meeting — import, link and read the day-1 meeting | 6.95 | 0 | 0 | 5 of 6 available · complete=False |
| 1 | day1-review — confirm one decision and one commitment | 2.63 | 0 | 0 | 5 of 6 available · complete=False |
| 1 | day1-attention — the commitment is a real attention row | 1.63 | 0 | 0 | 5 of 6 available · complete=False |
| 2 | day2-recall — recall yesterday's decision and commitment | 2.79 | 0 | 0 | 5 of 6 available · complete=False |
| 2 | day2-people — the person still carries yesterday's commitment | 2.19 | 0 | 0 | 5 of 6 available · complete=False |
| 2 | day2-complete — complete the commitment by explicit acts | 2.82 | 1 | 0 | 5 of 6 available · complete=False |
| 2 | day2-carry — day 2's preparation carries day 1's decision | 2.93 | 0 | 0 | 5 of 6 available · complete=False |

**Totals:** 8 stations · 25.42 s active (0.42 min) · 1 corrections · 0 abandoned paths.

## Facts

| Face | Field | Expected | Observed | Verdict | Why |
|------|-------|----------|----------|---------|-----|
| day1-identity | database_identity_discriminates | a different file yields a different identity | different | MATCH | an identity that cannot tell two files apart proves nothing about which file was opened |
| day1-brief | coverage_chip | COVERAGE · 1 OF 2 | COVERAGE · 1 OF 2 | MATCH | the Jira Watch cannot check; the face says so before the run |
| day1-brief | lifecycle | kept | kept | MATCH | the brief is kept work, not a draft that evaporates |
| day1-meeting | meeting_started_at | 2026-09-17 | 2026-09-17 | MATCH | day 1 is a real earlier calendar day, set through the import control |
| day1-room | proposal_caption_date | from Architecture review 09-17 | from Architecture review 09-17 / from Architecture review 09-17 | MATCH | a proposal is dated by its meeting, not by the row's write time |
| day1-room | singular_day_positive | a one-day-old row renders `… · 1 DAY` | WAITING ON YOUR REVIEW · 1 DAY | MATCH | the fence must see the singular, not just miss the plural |
| day1-room | singular_day | no `1 DAYS` / `1 HOURS` anywhere on the Room | (none) | MATCH | one day is a day; the arrival already said so |
| day1-room | target_chip_singular | TARGET <date> · 1 DAY | TARGET SEP 19 · 1 DAY | MATCH | the target chip counts one day in the singular |
| day1-room | filled_primaries | 1 (UX-CANON A.2) | 3: Draft update, Confirm, Confirm | FINDING | measured on the Room while two proposals are pending |
| day1-review | headline | 2 to review | 2 to review | MATCH | the two proposals the extractors produced |
| day1-attention | commitment_row | 1 | 1 | MATCH | yesterday's commitment is attention, not a buried row |
| day1-attention | coverage_complete | False | False | MATCH | one source cannot check; an empty partial is never an all-clear (C4) |
| day-boundary | same_database_file | bbafc4e36e2f02a6 | bbafc4e36e2f02a6 | MATCH | device+inode of the file hub #2 opened, read fresh (runtime_identity.py:96-112) -- a replaced file would read as a different database |
| day-boundary | same_data_behaviourally | hub #2 returns day 1's decision and commitment | asserted at day2-recall (current_decision, dec_token, owed_rows) | DATA | the load-bearing evidence for the boundary: records written before the restart come back after it |
| day-boundary | hub_restarted | a second hub on a new port (day 1 was http://127.0.0.1:61026) | http://127.0.0.1:61066 | MATCH | the day boundary is a real hub restart; the OS process is shared by the rig, so process_start does not move |
| day2-recall | current_decision | Rollback runbook is rehearsed on the read replica first | Rollback runbook is rehearsed on the read replica first | MATCH | AC1: recall returns the current decision first |
| day2-recall | rationale | The replica absorbs the first cut-over without touching writes | The replica absorbs the first cut-over without touching writes | MATCH | AC1: the rationale travels with the decision |
| day2-recall | dec_token | DEC 09-17 | DEC 09-17 | MATCH | the decision is dated to DAY 1, proving the boundary was crossed |
| day2-recall | source_token | MTG 09-17 · … | MTG 09-17 · 11:18 | MATCH | AC1: the original source is still reachable on day 2 |
| day2-recall | owed_rows | 1 | 1 | MATCH | yesterday's commitment is still owed today |
| day2-people | person_named | Marek Kubiak | Marek Kubiak | MATCH | AC: People preparation reflects the commitment's owner |
| day2-people | open_commitment | 1 OPEN COMMITMENT | 1 OPEN COMMITMENT | MATCH | the obligation made yesterday is on the person today |
| day2-people | receipt_rows | rows a reader can tell apart | 10 rows, 2 distinct labels (READ, READ MEETINGS), 0 carrying any token | DATA | measured on the Room's RECEIPTS ledger |
| day2-complete | commitment_status | completed | (gone from the board) | MATCH | completion is an explicit act with a receipt, never a side effect |
| day2-carry | people_after_completion | no OPEN COMMITMENT for the completed work | absent | MATCH | the completed commitment stops being owed on the People section |
| day2-carry | carried_forward_names_the_decision | Rollback runbook is rehearsed on the read replica first | Rollback runbook is rehearsed on the read replica first | MATCH | day 2's preparation carries yesterday's decision: the loop closed |
| day2-carry | carried_forward_caption | CARRIED FORWARD 4 | CARRIED FORWARD 4 | MATCH | 2 decision records + 2 commitments from 2 confirmations |
| day2-carry | carried_commitment_due | DUE 09-20 | DUE 09-20 | MATCH | a due DATE is drawn as a day, the way recall draws it |
| day2-carry | carried_forward_rows | 2 confirmed outcomes | CMT Draft the rollback runbook Open / DEC Rollback runbook is rehearsed on the read replica first ✓ CURRENT Open / CMT Draft the rollback runbook OWNER MAREK DUE 09-20 Open / DEC Rollback runbook is rehearsed on the read replica first Open | DATA | read beside the shot: the emblems cross over (`DEC Draft the rollback runbook`, `CMT Rollback runbook is rehearsed ...`) |
| day2-carry | carried_forward_kinds | every row drawn as the kind of record it is | (no swapped row) | MATCH | a commitment drawn `DEC · CURRENT` presents an action item as an accepted decision (ACCEPTANCE, critical defects: invented decision acceptance) |

## Shots

- day1-brief @ 1440: `day1-brief-1440.png`
- day1-room-proposals @ 1440: `day1-room-proposals-1440.png`
- day1-review @ 1440: `day1-review-1440.png`
- day1-reviewed @ 1440: `day1-reviewed-1440.png`
- day1-attention @ 1440: `day1-attention-1440.png`
- day2-recall @ 1440: `day2-recall-1440.png`
- day2-carried @ 1440: `day2-carried-1440.png`
- day2-people-owes @ 1440: `day2-people-owes-1440.png`
- day2-mark-done @ 1440: `day2-mark-done-1440.png`
- day2-completed @ 1440: `day2-completed-1440.png`
- day2-people-clear @ 1440: `day2-people-clear-1440.png`
- day2-prepare @ 1440: `day2-prepare-1440.png`

## Page errors

None.

## Surprises

- FOR THE CANVAS: with two proposals pending the Room draws 3 filled primaries at once -- `Draft update`, `Confirm`, `Confirm` (see day1-room-proposals-1440.png). UX-CANON asks for one filled primary per face. HS-200-14's Room fence never saw it because its seed had no pending proposal. Not touched: which verb keeps the fill is a design call (R16-4).
- FOR THE CANVAS: the Room's RECEIPTS ledger draws 10 rows with only 2 distinct labels (`READ`, `READ MEETINGS`) and 0 of them carry any token at all -- no time, outcome or egress chip -- so a reader cannot tell one receipt from another (see day2-people-owes-1440.png). The row HAS slots for outcome, egress and time (ProjectRoomCore.tsx, ReceiptsSection ~:1145-1153); they are empty because the receipt records carry no timestamp. Not touched: what a receipt row should say is a design call (R16-4).
- FOR THE OWNER TO RULE: day two's brief lists yesterday's two confirmed outcomes FOUR times -- each one appears once as a decision and once as a commitment. That is not a bug: confirming either kind deliberately records both (holdspeak/services/proposal_bridge_service.py:588-590), so the Room holds two entries per outcome and the brief lists both. Each row is now labelled truthfully (DEC / CMT), so the question left is only whether the brief should show the pair or fold it into one row. Left as built.
- PRODUCT GAP, not a rig limit: no owner can choose a DETERMINISTIC brief today. `POST /api/projects/{id}/briefs/prepare` accepts `generator: "deterministic"` (holdspeak/services/preparation_brief_service.py:890-912) and the face never sends it (web/src/features/project-room/prepare/api.ts), so every brief prepared through the Room goes to a model route. This walk therefore proves the model path with a CONTROLLED adapter on 127.0.0.1, never a live model; the deterministic path is unreachable without a face change (R16-4) and is unproved on glass.

## Defects

- FOUND AND FIXED by this walk: the Room read `WAITING ON YOUR REVIEW · 1 DAYS` where the arrival read `1 DAY` for the same row. Fix: `_count_unit` in holdspeak/services/project_service.py:253-259, used by `_format_age` and by the `OVERDUE` / `REVIEW WAITING` reasons. Fence: the `day1-room` `singular_day` assertion here, which fails pre-fix with `assert '1 DAYS' not in room_text`.
- FOUND AND FIXED by this walk: the Room's proposal caption `from <meeting> <MM-DD>` formatted the PROPOSAL's write time, not the meeting's start (web/src/features/project-room/ProjectRoomCore.tsx, the caption builder). A meeting reviewed the next morning was captioned with today's date while the review wing (`MTG 09-17`) and recall (`DEC 09-17`) both said the meeting's own day. Invisible on a same-day desk. Fix: holdspeak/services/project_service.py now carries `meeting_started_at` on the needs-you proposal row and the caption formats it. Fence: the `day1-room` `proposal_caption_date` assertion in this rig, which fails pre-fix with `assert 'Architecture review 09-17' in 'from Architecture review 09-18'`.
- FOUND AND FIXED by this walk: the preparation brief's CARRIED FORWARD ledger drew a commitment's due DATE as a wall clock -- `2026-09-20` rendered `DUE 18:00` (web/src/features/project-room/prepare/PreparePosture.tsx called `clockToken` on a date-only value, and `new Date('2026-09-20')` is UTC midnight, so a negative-offset desk also saw the wrong day). Recall says `DUE 09-20` for the same commitment (holdspeak/services/recall_service.py:93-105). Fix: `dueDayToken` in web/src/features/project-room/prepare/model.ts. Fence: the `day2-carry` `carried_commitment_due` assertion here, which fails pre-fix with `assert ['DUE 18:00'] == ['DUE 09-20']`.
- FOUND AND FIXED by this walk: the preparation brief's CARRIED FORWARD ledger drew each row as the kind of the LIST it arrived in, not the kind of the record -- the commitment read `DEC ... ✓ CURRENT` and the decision read `CMT`. Presenting an action item as an accepted decision is ACCEPTANCE's `Invented decision acceptance` line. The kind was lost in the Room's own projection, which is where it is now carried: holdspeak/services/project_service.py `_read_room_decisions` / `_read_room_commitments` add `kind` from the confirmed proposal (the column RecallService already reads, recall_service.py:193-196), `build_manifest` (holdspeak/services/preparation_brief_service.py) carries it, and PreparePosture draws the emblem and the CURRENT chip from it. Fence: the `day2-carry` `carried_forward_kinds` assertion here, which fails pre-fix with `assert ['DEC :: Draft the rollback runbook', 'CMT :: Rollback runbook is rehearsed on the read replica first'] == []`.
