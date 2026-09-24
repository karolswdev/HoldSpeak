# Phase 4 - The Morning

**Last updated:** 2026-09-23 (RATIFIED; build starts).

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
- **Out (real costs, ledgered, not dependencies of the morning):** the brief view's own Generate limitation (`BriefView.tsx:297`); breakage titles carrying service/method/connector ids (Tenet 4 wording, `monday_brief_service.py:546`); owners and due dates lost on the Arrival rows; raw internals in the brief view; the decision window covering the BRIEF verbs at 1440 (normal window behaviour under UX-CANON.md:111, an observation not a repair); the decision row below the fold at 393; the A4 receipt-line regression on the HS-201-12 fence; ASR instability; the aftercare overlap; exception-path queue wording; `1 WORDS`.

## Exit criteria (evidence required)

- [ ] The closure chain step 5 AS WRITTEN passes on the rig at 1440 and 393: a populated, untriaged day-one brief → the producer day advances → ONE Generate on the Arrival → the new decision readable in the visible BRIEF rows — no Ack/Defer, no fold. Proof strengthened past text containment (the rig's predicate accepts text the observation marks invisible/off-viewport, `graph_walk.py:832`): the new brief's identity and date; the old brief's triage unchanged; the decision row's geometry visible and inside the viewport; the shots at both widths inspected; the cumulative restart evidence retained.
- [ ] A lookback with a breakage item generates the next brief with 200 (fence red pre-fix on the id collision).
- [ ] Every repaired seam has a fence that failed pre-fix.
- [ ] The owner's sitting on the morning (his Phase 3 sitting extends to it).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-4-01 | Generate is always reachable | in-progress | [story-01-generate-always-reachable](./story-01-generate-always-reachable.md) | - |
| PHILO-4-02 | The new decision is in the visible rows (order + a real recency source; the cap kept) | backlog | [story-02-decision-in-the-visible-rows](./story-02-decision-in-the-visible-rows.md) | - |
| PHILO-4-03 | A failure never collides with the next brief | in-progress | [story-03-breakage-ids-never-collide](./story-03-breakage-ids-never-collide.md) | - |
| PHILO-4-04 | The triaged headline (the generated snapshot vs the current triage state) | backlog | [story-04-the-triaged-headline](./story-04-the-triaged-headline.md) | - |

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The verb (canvas first) | 01 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-4-01 | feat/philo-4-01-generate |
| The rows | 02 | Astra (Luna) | Muad'Dib | ../wt-philo-4-02 | feat/philo-4-02-rows |
| The ids | 03 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-4-03 | feat/philo-4-03-ids |
| The headline | 04 | Astra (Luna) | Muad'Dib | ../wt-philo-4-04 | feat/philo-4-04-headline |

## Where we are

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

- 2026-09-23 — the owner RATIFIED the charter and the story 01 canvas with all six asks ("so... my walk says: yes!") — build order 01 ∥ 03 → 02 → 04.

- 2026-09-23 — chartered on "yes close and open"; the service-layer draft renumbered to Phase 5 — Muad'Dib.
- 2026-09-23 — Astra's charter check RATIFY-WITH-CONDITIONS; all five conditions paid in the charter text (this commit); the charter goes to the owner for ratification — Muad'Dib.
- 2026-09-23 — story 04 The triaged headline chartered (unratified) from Astra's round-three canvas check, finding 6: after full triage the stored headline still counts waiting items; lane Astra — Muad'Dib.

## Decisions deferred

- (none)
