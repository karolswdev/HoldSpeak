# Phase 6 - The Honest Morning

**Last updated:** 2026-09-24 night — all five stories done and merged or reconciled (01/02 lane A, 04/05 lane B, 03 placement reconciled with main in PR #649); the closing chain (exit 3) is next.

## Goal

The Phase 5 closure found six defects on the owner's morning path. This phase repairs them honestly with the existing idioms: a failed import shows FAILED, the brief tells one time and two counts that each say what they count, the toast shows no zero and covers nothing, one missing decision makes one broke row, and the decision body is readable at once after Done. Every repair has a fence that is red first, and a proof at 1440 and 393. The phase closes on a re-run of the Phase 4 closing case and the Phase 5 rehearsal.

## Authority

The owner, 2026-09-24 night (verbatim): "Let's write a handover to work the same way on the morning path repairs? And... rolling more and more capabilities of our platform through this native mcp way?" (`docs/internal/project-rooms/HANDOVER-MUADDIB-XXVIII.md:7`).

The owner's ruling D2, 2026-09-24 night (AskUserQuestion): "repairs first: Phase 6 The Honest Morning before Phase 7" (`../PHASE-6-7-CHARTER-DRAFTS.md` §"The owner's rulings").

Astra's check of the drafts, RATIFY-WITH-CONDITIONS (`../PHASE-6-7-CHECK-ASTRA.md`), is paid in this charter: finding 2's per-repair table is the scope of the five stories below; finding 3 sets the estimate and the lanes. The method is XXVIII §"The method" ("the same way").

## The roots

- **Tenet 3 (help and accelerate):** the face never lies. A failed import that says SAVED, and a brief that tells two different counts and two different times, cost the owner trust on the first screen of the day.
- **Tenet 4 (ASD-STE100):** the words are human words. A brief row that reads `MeetingIntelService.run_intelligence` is not a word for him.
- **Tenet 7 (a Senior Architect with reports):** no counter of zero (UX-CANON A.8); nothing covers what he reads (no overlap); one cause makes one row.

## Status of this charter

RATIFIED by the owner 2026-09-24 night (AskUserQuestion: "Ratify, build it"). Both lanes start: Muad'Dib 01 → 02 (owns `ChairHome.tsx`); Astra 04, 05 now and 03 canvas-first (the placement canvas comes to the owner before build).

## Scope

- **In:** the five stories below; a fence per repaired seam, red pre-fix; the two small canvases, ratified before their build; the closing chain on the rig at 1440 and 393 (exit 3).
- **Out:**
  - The Info-window rename of a decision (`web/src/desk/components/InfoWindow.tsx:31` sends `name`; `decision.update` ignores it). This is a contract question (which field), not a morning repair. BACKLOG "PHILO-5-01 follow-ups".
  - The shelf-enum drift (`holdspeak/mcp/tools.py:459` vs `holdspeak/operations.py:421-423`). Phase 7 story 01 owns it.
  - The Article XI admission of desk writes. The owner ruled D3; Phase 7 story 02 pays it.
  - MCP discoverability (the 201 s Codex search). Phase 7 story 01 / story 04.
  - Any redesign of the BRIEF section or of the toast beyond its placement. A second verb, a new row kind or a new section is a stop signal.
  - The brief's freshness on an already-open Desk (Phase 5 scope; not claimed).

## The census basis

The six defects come from retained evidence, not from taste. The source is the Phase 5 story-04 closing run and its carried observations (`../phase-5-the-one-service-layer/assets/story-04-shots/`), recorded in BACKLOG "PHILO-5-04 follow-ups" (`pm/roadmap/holdspeak/BACKLOG.md:1206`).

| # | Defect | Retained evidence | Story |
|---|---|---|---|
| 1 | A failed import shows SAVED | Phase 5 story-03 glass review; `intelBadge.ts:26`; `meeting_service.py:315` | 01 |
| 2 | Brief head count vs receipt count (5 vs 6); two time formats | `final/20260925T001407Z-his-words-real/shots/brief/1440.png`, `…/393.png` | 02 |
| 3 | Raw pipeline id stored as a brief item and in breakage titles | `final/20260925T001407Z-his-words-real/observations/brief.json` | 02 |
| 4 | `MEETING READY · N open · 0 decided`; the toast covers the summary and the capture bar at 393 | `final/20260925T001407Z-his-words-real/shots/summary/393-after.png` | 03 |
| 5 | One missing decision read, two observer failure rows | `carried/verification/missing-browser-missing-id-rows.txt` (rows 67, 68) vs `carried/verification/missing-op-missing-id-rows.txt` (row 6) | 04 |
| 6 | DECISION body empty ~1 s after Done at 393 | `carried/s4-393/20260924T233554Z-case.closure.chain.s4_saved_content-astra-393/`; `carried/verification/s4-1440-observation-summary.json` | 05 |

## Exit criteria (evidence required)

- [ ] 1. Each repair's fence is red on a `git archive origin/main` copy with the branch's tests overlaid, and green on the built branch; both transports where the seam has two (HTTP and `op`). "Unknown tool" or a missing symbol is never counted as red.
- [ ] 2. The two canvases are ratified by the owner BEFORE their build: (a) the toast placement at 1440 and 393 (story 03); (b) any count label or count meaning change, with the exact strings, at both widths (story 02). If story 02 changes no label and no meaning, (b) is recorded as not needed.
- [ ] 3. The closing chain on the rig at 1440 and 393: the Phase 4 exit-1 case `case.closure.chain.s5_next_day_brief_has_it` AS WRITTEN (`docs/internal/philo/graph/atlas-phase3.json:1946`) AND the Phase 5 rehearsal driver `scripts/philo5_his_words.py` re-run. The morning shots show: no SAVED on a failed import; one time format; counts that agree with their labels; no zero token; no overlap at 393; one broke row per cause; the decision body present at once after Done. **Assigned to this run (round 3, Astra's round-two ruling 5):** `case.closure.chain.s5_next_day_brief_with_breakage.op` (`docs/internal/philo/graph/atlas-phase3.json:4780`), whose check and capture were reworded in round 2 (row 0 is checked for `Decision did not load`, then its id is captured). It is UNVERIFIED LIVE until this run; a schema fence does not close it.
- [ ] 4. Rehearsed, owner-reviewed shots (never recorded as a sitting).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-6-01 | The honest import badge | done | [story-01-the-honest-import-badge](./story-01-the-honest-import-badge.md) | [evidence-story-01](./evidence-story-01.md) |
| PHILO-6-02 | The brief's truth (one time, honest counts, human words) | done | [story-02-the-briefs-truth](./story-02-the-briefs-truth.md) | [evidence-story-02](./evidence-story-02.md) |
| PHILO-6-03 | The toast that does not cover | done | [story-03-the-toast-that-does-not-cover](./story-03-the-toast-that-does-not-cover.md) | [evidence-story-03](./evidence-story-03.md) |
| PHILO-6-04 | One cause, one row | done | [story-04-one-cause-one-row](./story-04-one-cause-one-row.md) | [evidence-story-04](./evidence-story-04.md) |
| PHILO-6-05 | The decision body at once | done | [story-05-the-decision-body-at-once](./story-05-the-decision-body-at-once.md) | [evidence-story-05](./evidence-story-05.md) |

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The Arrival (owns `ChairHome.tsx`) | 01, 02 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-6-a | feat/philo-6-a-badge-brief |
| The toast, the row, the body (merged) | 03 zero/canvas, 04, 05 | Astra (Luna) | Muad'Dib | ../wt-philo-6-b | feat/philo-6-b-toast-rows-body |
| Ratified toast placement | 03 build | Astra (Luna) | Muad'Dib | ../wt-philo-6-03 | feat/philo-6-03-placement |

Lane law for this phase:

- Muad'Dib's lane owns `web/src/desk/chair/ChairHome.tsx`; the build brief grants Astra only the exact four-line slot patch in its own gated commit (`d1e355f2`), with lane A reconciliation. The story 03 patch adds an empty `data-aftercare-slot` at `ChairHome.tsx:1442` (`:1450-1453` after the main reconcile) before `<CaptureBar />`; it does not change the capture-clearance measurement. Astra hands the patch to lane 01/02; the two lanes never co-edit the file. The built lane adds the AmbientLayer portal, auto-scroll and off-Arrival slots separately from this exact patch.
- Shared atlas and generated files (`docs/internal/philo/graph/atlas*.json`, `docs/generated/*`) have one shipping owner per commit. The second lane rebases and regenerates.
- Two lanes do not halve the time (Astra, finding 3).

## Where we are

2026-09-24 night: PR #649 reconciled with main `e64114df` (lane A merged as PR #646). The five conflicts are resolved: the atlas takes main and re-applies the branch's placement cases with anchors regenerated on the merged tree; the generated files are regenerated. Muad'Dib's counsel on built (RATIFY-WITH-CONDITIONS, `checks/story-03-placement-built-muaddib.md`) is paid in the reconcile commit. All five stories are done; the closing chain (exit 3) and owner review remain.

Publication update — Main advanced during this build: lane A merged as PR #646 (`e64114df`). PR #649 is open but reports five conflicts: `docs/internal/philo/graph/atlas.json`, `docs/generated/graph.json`, `docs/generated/boundary-candidates.json`, this project README, and the Phase 6 status file. The read-only merge preflight auto-merges ChairHome and the atlas tests; no combined-tree test or glass result is claimed. Muad’Dib’s integration and counsel remain before merge. The table on this lane still reflects its fork’s lane-A story files; integration brings their merged status with their evidence.

2026-09-24 night: PHILO-6-03 placement verified in `feat/philo-6-03-placement`: six actual Chromium surface walks pass, one phone scroll and zero desktop scrolls; live Dismiss passes at both widths. [Lane report](../../../../docs/internal/philo/phase-6/toast/placement-proof/lane-report.md) carries per-box proof and limits. Focused tests pass (30 Vitest, 104 Python); broader scoped 235 assertions pass with one inherited fixture error, reproduced on untouched main and ledgered. Lane B is merged (04/05 done). Lane A remains in round three on the brief/import seams and reconciles the exact ChairHome slot commit. [PR #649](https://github.com/karolswdev/HoldSpeak/pull/649) is open after gated build commit `c6aafa8e`; no merge before calling Muad’Dib counsel. Phase-wide rehearsal and owner review remain open.

2026-09-24 night: lane A ROUND 3 after Astra's round-two check (BOUNCE, `checks/lane-a-built-astra.md` "Round two"). 02: a brief line states only what the record proves — the outcome is the OUTERMOST call (earliest start; a nested call sorts after its parent because the observer stores call-start time); a Changed line only from the truthful table (story 02), the follow-up line from the recorded `verb` (`Follow-up completed` only for `done`), `Decision recorded` from `create_from_*` only with its inner `create`; reads, reconciliations and a cached brief tell only their failure; an unknown success writes nothing. 01: the import cause is a short class at the producer (`LAST ERROR · NO TRANSCRIPT LINES`, no temp file name); the rig case re-run PASS at 1440 and 393. Fences on an ADVANCING clock, red on a `git archive 27ee9559` copy, green on the branch (`docs/internal/philo/phase-6/brief/round-3/`). The changed S5 `.op` case is assigned to exit 3. Astra checks round 3.

2026-09-24 night: lane A ROUND 2 after Astra's check on built (BOUNCE, `checks/lane-a-built-astra.md`). 01: the expanded well of a failed import reads `IMPORT` with the import's cause (never `SUMMARY · FAILED`); the rig case re-shot PASS at 1440 and 393 on the well head; the broad "unmapped states" claim narrowed (`importing`/`refused`/`live` → BACKLOG "PHILO-6 follow-ups"). 02: a failed operation makes only its Broke row (no success line); the fallback says `<Object> did not <verb>` with enumerated objects (no `Primitive`); the atlas selectors changed with the words; the rehearsal box replaced by a SCOPE AMENDMENT (carried to exit 3; see "Decisions made"). Fences red on a `git archive f6c0c0d1` copy, green on the branch (`docs/internal/philo/phase-6/{badge,brief}/round-2/`). Astra checks round 2.

2026-09-24 night: PHILO-6-02 DONE in lane A: ONE clock (the producer's `generated_at` in the viewer's zone, the Brief view's existing stamp, on the caption and the receipt); the counts keep their labels and meanings (no canvas needed: the raw-id filter hid raw producer rows from the head); human producer words (`Summary requested: <title>`, `Summary did not start: <title>`, no `Service.method`). Fences red on `origin/main`, green on the branch; the fold-destination walk FAIL before / PASS after at 1440 and 393. OPEN: the story's rehearsal box — `scripts/philo5_his_words.py` blocked three times before the brief stage (the Codex decision turn used `desk.create`); carried to exit 3. Astra checks on built.

2026-09-24 night: PHILO-6-01 DONE in lane A (`feat/philo-6-a-badge-brief`): a failed import reads FAILED on the Arrival (`web/src/desk/chair/intelBadge.ts:26`); the fence is red on `origin/main` (SAVED) and green on the branch; the rig case `case.philo601.import_failed.badge` PASS at 1440 and 393. Astra checks on built. Next in the lane: PHILO-6-02.
2026-09-24 night: lane B merged (04 done, 05 done; 03's zero omission + the ratified canvas); Astra builds 03's placement; lane A in round three (the brief's outcome-blind wording and the import cause line).

2026-09-24 night — lane B round two records the actual Muad’Dib counsel at `checks/lane-b-built-muaddib.md` and relabels the earlier Astra-invoked claude -p checks. Records and canvas corrections follow that counsel; 03 stays in-progress, with placement unbuilt and unratified. Off-Arrival proposal: a top-of-surface flow slot inside Meetings and the Floor. Phone ask 2 explicitly moves the reading position. The 0/0 proposal verb is withheld with a red-before-fix fence. Three follow-ups now also live in BACKLOG “PHILO-6 follow-ups”. One gated update to PR #647; no merge.

2026-09-24 night — lane B PHILO-6-05 verified: cause found before repair, 29 frontend and 143 rig checks passed, actual S4 continuous fence FAIL → PASS at 393 and 1440, first read frame and all 129 frames readable in each green run. Astra-invoked claude -p check conditions paid, including an assertion after the failed rollback read commits. PHILO-6-04 is committed; 03 zero/canvas is committed and placement remains unratified. One lane PR: https://github.com/karolswdev/HoldSpeak/pull/647; no merge. Per-box proof and handover: `docs/internal/philo/phase-6/lane-report.md`.

2026-09-24 night — Astra lane B partial 03: zero omission is verified (archive 3 failed / 6 controls passed, built 13 passed). The checked canvas has today/proposed/summary-open/capture boards at both widths and a ChairHome proposal patch. Placement remains unbuilt, pending owner ratification of normal flow and the phone auto-scroll mechanism. Muad'Dib publishes the artifact.

2026-09-24 night — Astra lane B: 04 is verified (33 focused tests; missing-decision parity 2:1 → 1:1 at 1440/393; legacy reads stop creating false failures). Astra-invoked claude -p check conditions paid. 03 placement remains canvas-only and unratified; 05 is in cause-first repair. One lane PR will carry the gated commits; no merge in this lane.

2026-09-24 night: RATIFIED; lanes started (`../wt-philo-6-a` Muad'Dib 01/02; `../wt-philo-6-b` Astra 03/04/05).

2026-09-24: CHARTERED by the two brains from handover XXVIII r2 and Astra's check of the drafts (RATIFY-WITH-CONDITIONS, paid). The owner ruled D2 (repairs first). Nothing is built. Owed next: Astra's check of this charter; then the owner's ratification; then the canvas-free parts start (01, 02 a/c, 03 zero tokens, 04, 05), and the two canvases go to the owner.

**Estimate:** story effort 3.5–5 engineering days (01 0.5 · 02 1–1.5 · 03 1–1.5 · 04 0.5 · 05 0.5–1) + the toast canvas and its ratification + the conditional count canvas + counsel rounds + the closing runs (allow 1–1.5 d) = **4.5–6.5 engineering days PROVISIONAL**; elapsed time is longer than effort (two lanes, counsel between them, the owner's canvas word).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| "One count" over-simplifies: the head count and the receipt count have different lawful meanings (the generated snapshot vs the currently unhandled rows; THIS WEEK excluded from the Arrival) | high | story 02 keeps both meanings and the historical snapshot; the labels say what each counts; a label or meaning change goes on a small canvas first | a count changes meaning without a ratified canvas |
| The toast placement is design, not a repair | high | story 03 draws the unobstructed placement at both widths; the owner ratifies before build | placement code lands before the canvas is ratified |
| Whole-desk reads overlap optimistic writes; the slow sibling is still unidentified | medium | story 05 diagnosed and fenced the delayed CREATE refresh commit; delete/rename and repeated refusals remain in the phase-local ledger | a new write seam relies only on eventual text |
| The duplicate-row fix hides failures globally | medium | story 04 changes the dispatch only; legacy decision reads stay; a real failure still makes a row | fewer failure rows for a real failure |
| Raw wording stays in breakage titles after the brief item is fixed | medium | story 02 covers `monday_brief_service.py:500` AND `:597` together | a breakage title still carries `Service.method` |
| Two lanes collide on `ChairHome.tsx` or on the atlas | medium | one owner for `ChairHome.tsx`; the seam by patch; one shipping owner per shared file per commit | a merge conflict in `ChairHome.tsx` between lanes |
| Two lanes do not halve the time | high | the estimate is effort, provisional | - |

## Decisions made (this phase)

- 2026-09-24 night — PHILO-6-03 build brief grants Astra only the provided four-line ChairHome slot patch, in its own gated commit (`d1e355f2`); lane A reconciles. The brief names three actual atlas surface cases at both widths and scoped validation. The phase-wide rehearsal remains an integration exit; spatial WebGL Floor stays a shot-backed fixed-placement limitation. This records the owner’s build scope, not a new design.

- 2026-09-24 night — **Round 3, the event-selection tie rule** (lane A): a correlated operation's outcome is the call with the EARLIEST start; on a start-time tie, the HIGHEST insertion id. The brief said "lowest insertion id"; that picks the CHILD, because the observer emits in `finally` and the enclosing call finishes (and inserts) last (`holdspeak/services/observer.py:113` stores `t0`; `:158,185` emit in `finally`). Astra may overrule.
- 2026-09-24 night — **Round 3, `Follow-up date set`** (lane A) instead of the brief's `Follow-up dated`: ASD-STE100 has no verb "date"; the face verb is `Set a date`. `dismiss` and `snooze` get no Changed line (no row names them). Astra may overrule.

- 2026-09-24 night — **SCOPE AMENDMENT, story 02** (`docs/internal/ORCHESTRATION.md:69`; the owner may overrule at the sitting): the Phase 5 rehearsal re-run (`scripts/philo5_his_words.py` at 1440 and 393) moves from story 02 to exit 3 (the closing chain). The driver failures are inherited (Astra, `checks/lane-a-built-astra.md` finding 6: main `66205729` fails on tool selection, Codex chose `door.add_item`; the branch fails MCP resource-list reconciliation after a correct `desk.create`). Homes: tool selection = BACKLOG "PHILO-5-04 follow-ups" MCP discoverability row (Phase 7 story 01/04); reconciliation = BACKLOG "PHILO-6 follow-ups" row 2 (Muad'Dib, before exit 3). Story 02 stays DONE only with this amendment — Muad'Dib (lane A, round 2).
- 2026-09-24 night — story 02 round 2: a failed operation makes NO Changed row (its one line is the Broke row), rather than a failure-worded Changed row: one cause, one row — Muad'Dib (lane A).
- 2026-09-24 night — story 02: the brief's ONE clock is the producer's `generated_at` in the viewer's zone (the Brief view's stamp, HS-175 C8), on the caption and the receipt; exit 2(b) (the count canvas) is NOT needed: no count label or meaning changed — Muad'Dib (lane A).
- 2026-09-24 night — the owner RATIFIED the story 03 placement canvas (in flow above the capture bar; top-of-surface off the Arrival; phone auto-scroll accepted). Lane B (04, 05, the zero omission, the canvas) MERGED `4d55d4d5` after Muad'Dib's counsel (conditions paid in r2). Astra builds the placement now — Muad'Dib.

- 2026-09-24 night — PHILO-6-05 Astra-invoked claude -p built check RATIFY-WITH-CONDITIONS, paid before done: post-rollback assertion, README/status updates and complete generated-file staging. Evidence and limits: `checks/story-05-built-astra-invoked-claude.md`; phase-local follow-ups in `docs/internal/philo/phase-6/ledger.md`.
- 2026-09-24 night — PHILO-6-05 criterion 2 strengthened on live evidence and the Astra-invoked claude -p design check: the first read frame is readable on main; the pre-fix red is a later stale refresh commit. Require readability on the first frame and every frame through terminal observation, with the observer armed before Done. Original passing first-frame probe retained and labelled; no first-frame red claimed. See `checks/story-05-design-astra-invoked-claude.md` and `docs/internal/philo/phase-6/body/diagnosis.md`. Owner may overrule.

- 2026-09-24 night — PHILO-6-03 Astra-invoked claude -p canvas/zero check RATIFY-WITH-CONDITIONS, paid before partial commit: sticky-phone geometry disclosed, distinct capture board, one parked rejected candidate, counsel under checks. Owner ratification still owed; `checks/story-03-canvas-zero-astra-invoked-claude.md`.


- 2026-09-24 night — the owner RATIFIED the charter ("Ratify, build it"); all five stories in progress in two lanes — Muad'Dib.

- 2026-09-24 night — Astra's check of this charter: RATIFY-WITH-CONDITIONS (`checks/charter-astra.md`), paid: story 01's diagnosis corrected (the producer writes `intel_status`; the adapter finding retracted by Astra; the repair is the badge mapping); story 02 never conflates the counts and decides one clock with an offsets fence; the estimate reconciled (4.5–6.5 d provisional); the README's Phase 5 row corrected; story 05's proof armed before Done. The owner's ratification next — Muad'Dib.

- 2026-09-24 — CHARTERED by the two brains from handover XXVIII r2; Astra's check of the drafts (RATIFY-WITH-CONDITIONS) paid: the per-repair canvas rulings (finding 2), the estimate and the lane split (finding 3), raw breakage wording covered (MISSED 2) — Muad'Dib.
- 2026-09-24 — the owner ruled D2: repairs first; Phase 6 before Phase 7.

## Decisions deferred

- S4 follow-ups (slow whole-desk refresh, delete/rename races, setup-read rejection): recorded with evidence and disposition in `docs/internal/philo/phase-6/ledger.md`; no widening of this lane's repair.

- Story 03 placement canvas ratification is resolved (2026-09-24 night); actual Muad'Dib counsel on the built PR remains before merge.
- Any change of a count label or a count meaning (story 02 canvas, only if needed) — the owner's ratification.
- The Info-window rename field (`name` vs `title`) — out; BACKLOG "PHILO-5-01 follow-ups".
