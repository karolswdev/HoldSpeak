# Phase 4 - The Morning

**Last updated:** 2026-09-24 (PHILO-4-02 built and checked; exits 1 and 2 proved on the lane; PR to remain open).

## Goal

The next-day brief reaches the Arrival in one move, and it cannot crash: Generate is always reachable, a new decision is inside the visible rows, and a failure in the lookback never collides with the next brief's ids. This is the smallest set the Phase 3 closure found missing between "the loop works by protocol" and "the loop works on his desk in the morning".

## Authority

The owner, 2026-09-23, on Muad'Dib's closure question ("close Phase 3 with exit 1 open, or add a fifth story to pay the smallest set that lets the next-day brief reach the face in one move"): "yes close and open". Phase 3 closed with its exit 1 open and the six new costs ledgered (`phase-3-the-meeting-loop/final-summary.md` §"What he still cannot do"); this phase opens for the first three. Numbering: the service-layer charter draft moved from 4 to 5.

## The roots

The loop's whole point is the morning. Today the morning needs a detour (acknowledge every old row, Generate, click "1 more") and can answer 500. Tenet 3 (help and accelerate) and the council's roots verdict (the desk stops guiding where a result must come back to the face).

## Status of this charter

RATIFIED by the owner, 2026-09-23 ("so... my walk says: yes!") on the story 01 canvas (https://claude.ai/artifact/LHjuHKL1pVZuh4aK5J9qRU, round six, `cac98e7d`) and its six asks: (1) `Generate` in the BRIEF head after `THIS DEVICE`, every state, disabled only while a read or a generation is open; (2) the three-row cap kept, decisions first, newest by the decision record's `created_at`; (3) Arrival only; (4) the 12 px library floor (merged); (5) `No changes` replaces the empty-brief sentence (the producer string and its wording fences change together); (6) story 04 is in. Build starts: 01 and 03 in parallel, 02 after 01, 04 after 02.

## Scope

- **In:** the stories below; their fences (red pre-fix); the closure chain's step 5 re-run on the rig at 1440 and 393 as written (no detour) — `case.closure.chain.*` in `atlas-phase3.json`, re-pointed; the Phase 3 exit 1 language updated to cite this phase when it passes.
- **Out (real costs, ledgered, not dependencies of the morning):** the brief view's own Generate limitation (`BriefView.tsx:297`); breakage titles carrying service/method/connector ids (Tenet 4 wording, `monday_brief_service.py:546`); owners and due dates lost on the Arrival rows; raw internals in the brief view; the decision window covering the BRIEF verbs at 1440 (normal window behaviour under UX-CANON.md:111, an observation not a repair); the decision row below the fold at 393 outside the newly generated first Arrival row proved by 02; the A4 receipt-line regression on the HS-201-12 fence; ASR instability; the aftercare overlap; exception-path queue wording; `1 WORDS`.

## Exit criteria (evidence required)

- [x] The closure chain step 5 AS WRITTEN passes on the rig at 1440 and 393: a populated, untriaged day-one brief → the producer day advances → ONE Generate on the Arrival → the new decision readable in the visible BRIEF rows — no Ack/Defer, no fold. Proof strengthened past text containment (the rig's predicate accepts text the observation marks invisible/off-viewport, `graph_walk.py:832`): the new brief's identity and date; the old brief's triage unchanged; the decision row's geometry visible and inside the viewport; the shots at both widths inspected; the cumulative restart evidence retained.
  **Proof:** as-written `case.closure.chain.s5_next_day_brief_has_it` passes at 1440 `20260924T072614Z` and 393 `20260924T072514Z`. First decision row owns all nine hit points, has positive in-viewport geometry; new id/date and old DB rows/shelf verified. Before/after shots inspected. Separate breakage variants `20260924T072814Z`/`20260924T072722Z` pay the story-03 amendment. [Lane report](../../../../docs/internal/philo/phase-4/rows/lane-report.md), [evidence](evidence-story-02.md), [built counsel](checks/rows-built-muaddib.md).
- [x] A lookback with a breakage item generates the next brief with 200 (fence red pre-fix on the id collision).
  **Proof:** the separately named real-failure variants `20260924T072814Z` (1440) and `20260924T072722Z` (393) both return 200, retain one failure source in both briefs with different item ids, and leave the old rows/shelf unchanged. [Checked DB proof](../../../../docs/internal/philo/phase-4/rows/closure-proof.json); `test_philo4_03_breakage_ids.py` also passes in the 92-test capture.
- [ ] Every repaired seam has a fence that failed pre-fix.
- [ ] The owner's sitting on the morning (his Phase 3 sitting extends to it).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-4-01 | Generate is always reachable | done | [story-01-generate-always-reachable](./story-01-generate-always-reachable.md) | [evidence-story-01](./evidence-story-01.md) |
| PHILO-4-02 | The new decision is in the visible rows (order + a real recency source; the cap kept) | done | [story-02-decision-in-the-visible-rows](./story-02-decision-in-the-visible-rows.md) | [evidence-story-02](./evidence-story-02.md) |
| PHILO-4-03 | A failure never collides with the next brief | done | [story-03-breakage-ids-never-collide](./story-03-breakage-ids-never-collide.md) | [evidence-story-03](./evidence-story-03.md) |
| PHILO-4-04 | The triaged headline (the generated snapshot vs the current triage state) | backlog | [story-04-the-triaged-headline](./story-04-the-triaged-headline.md) | - |

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The verb (canvas first) | 01 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-4-01 | feat/philo-4-01-generate |
| The rows | 02 | Astra (Luna) | Muad'Dib | ../wt-philo-4-02 | feat/philo-4-02-rows |
| The ids | 03 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-4-03 | feat/philo-4-03-ids |
| The headline | 04 | Astra (Luna) | Muad'Dib | ../wt-philo-4-04 | feat/philo-4-04-headline |

## Where we are

2026-09-24: PHILO-4-02 BUILT AND VERIFIED on `feat/philo-4-02-rows`, based on merged 01/03 (`566495b0`). Decisions lead, newest by persisted record timestamp; cap and count law retained. The phone row clears the measured capture bar and dock after Generate. Final as-written and real-breakage walks pass at both widths; exits 1 and 2 met on this lane. Muad'Dib RATIFY-WITH-CONDITIONS; conditions paid, with the pinned-inventory condition corrected by the checker. The gated PR remains open for the invoking brain; no merge. Story 04 is next. The owner's sitting and summary usefulness remain open.

2026-09-24: PHILO-4-01 BUILT (branch `feat/philo-4-01-generate`, Astra checks on built). The head `Generate` is in every BRIEF branch; `GENERATING…`; `BRIEF DID NOT GENERATE · <cause>` with no Retry; `No changes`. Fences red on origin/main (13 vitest, 2 pytest; `docs/internal/philo/phase-4/generate/`). Rig step 5 as written at 1440 (`20260924T053019Z`) and 393 (`20260924T053350Z`): one Generate with no Ack, a new next-day brief with the decision by protocol; the face predicate FAILS on the fold (`1 more`), which is story 02. Exit 1 stays open until 02.
2026-09-24: PHILO-4-03 built on `feat/philo-4-03-ids` — breakage ids are scoped to their brief (pipeline and connector); the fence (`tests/unit/test_philo4_03_breakage_ids.py`) was red pre-fix on the IntegrityError and is green; Astra's check on built is owed before merge. Exit criterion 2 is met on this branch once merged.

2026-09-23 night: RATIFIED on his walk. Lanes 01 (Muad'Dib, `../wt-philo-4-01`, the library changes already on main) and 03 (Muad'Dib, `../wt-philo-4-03`) start; 02 (Astra) after 01 merges; 04 (Astra) after 02.

2026-09-23: chartered from the Phase 3 closure (`final-summary.md`, "What he still cannot do" 1–3) on the owner's word. Astra's check (RATIFY-WITH-CONDITIONS, `checks/charter-astra.md`) paid: the cap's provenance corrected (Phase 170 code, never canvassed); the ordering rule settled on the decision record's `created_at`; brief-scoped ids chosen over idempotent inserts; story 01 scoped to the Arrival with its states; the closure proof strengthened past containment; estimates reconciled. The owner's ratification owed; then 01's canvas (with 02's order on it).

**Estimate:** stories total 2.5–4 engineering days; with 01 → 02 and 03 in parallel the critical path is 2–3 working days, excluding the owner's canvas and sitting. This supersedes Astra's closure-counsel estimate of 1–2 days (Astra, charter check).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| 01 grows into a BRIEF-section redesign | medium | one verb with its states, placed on the canvas, ratified; the section's rows and triage stay as built | a second verb or a row change appears |
| 02 orders by an inferred recency (random item ids) and still shows old decisions | medium | the rule is the decision record's `created_at`; the fence seeds several older decisions | the fence has no older decisions |
| The id fix silently drops or moves a failure or its triage | medium | brief-scoped ids only; both briefs and the old triage read back; no `OR IGNORE`/`OR REPLACE`; no migration | a row or a triage record missing after generation |

## Decisions made (this phase)

- 2026-09-24 — SCOPE AMENDMENT (Astra's check on built, story 03): story 03 changes no face; its rig proof is assigned to exit 1 (story 02's closure-chain run carries a breakage item in the lookback). Astra: RATIFY-WITH-CONDITIONS on #624, conditions paid — Muad'Dib.

- 2026-09-23 — the owner RATIFIED the charter and the story 01 canvas with all six asks ("so... my walk says: yes!") — build order 01 ∥ 03 → 02 → 04.

- 2026-09-23 — chartered on "yes close and open"; the service-layer draft renumbered to Phase 5 — Muad'Dib.
- 2026-09-23 — Astra's charter check RATIFY-WITH-CONDITIONS; all five conditions paid in the charter text (this commit); the charter goes to the owner for ratification — Muad'Dib.
- 2026-09-23 — story 04 The triaged headline chartered (unratified) from Astra's round-three canvas check, finding 6: after full triage the stored headline still counts waiting items; lane Astra — Muad'Dib.

## Decisions deferred

- (none)
