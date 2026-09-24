# Phase 4 - The Morning

**Last updated:** 2026-09-23.

## Goal

The next-day brief reaches the Arrival in one move, and it cannot crash: Generate is always reachable, a new decision is inside the visible rows, and a failure in the lookback never collides with the next brief's ids. This is the smallest set the Phase 3 closure found missing between "the loop works by protocol" and "the loop works on his desk in the morning".

## Authority

The owner, 2026-09-23, on Muad'Dib's closure question ("close Phase 3 with exit 1 open, or add a fifth story to pay the smallest set that lets the next-day brief reach the face in one move"): "yes close and open". Phase 3 closed with its exit 1 open and the six new costs ledgered (`phase-3-the-meeting-loop/final-summary.md` §"What he still cannot do"); this phase opens for the first three. Numbering: the service-layer charter draft moved from 4 to 5.

## The roots

The loop's whole point is the morning. Today the morning needs a detour (acknowledge every old row, Generate, click "1 more") and can answer 500. Tenet 3 (help and accelerate) and the council's roots verdict (the desk stops guiding where a result must come back to the face).

## Status of this charter

DRAFTED by Muad'Dib 2026-09-23 on Astra's closure counsel ("Charter A5 … 1–2 engineering days"); Astra's check of this charter owed; the owner's ratification owed. Story 01 places a verb: it is designed on the canvas and the owner ratifies before build (UX canon); stories 02 and 03 are repairs, not design.

## Scope

- **In:** the three stories below; their fences (red pre-fix); the closure chain's step 5 re-run on the rig at 1440 and 393 as written (no detour) — `case.closure.chain.*` in `atlas-phase3.json`, re-pointed; the Phase 3 exit 1 language updated to cite this phase when it passes.
- **Out (real costs, ledgered in Phase 3, not dependencies of the morning):** owners and due dates lost on the Arrival rows; raw internals in the brief view; the decision window covering the BRIEF verbs at 1440 (normal window behaviour under UX-CANON.md:111, an observation not a repair); the decision row below the fold at 393; the A4 receipt-line regression on the HS-201-12 fence; ASR instability; the aftercare overlap; exception-path queue wording; `1 WORDS`.

## Exit criteria (evidence required)

- [ ] The closure chain step 5 AS WRITTEN passes on the rig at 1440 and 393: after the producer day advances, one Generate on the Arrival, and the decision is in the visible BRIEF rows — no acknowledgement detour, no "1 more".
- [ ] A lookback with a breakage item generates the next brief with 200 (fence red pre-fix on the id collision).
- [ ] Every repaired seam has a fence that failed pre-fix.
- [ ] The owner's sitting on the morning (his Phase 3 sitting extends to it).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-4-01 | Generate is always reachable | backlog | [story-01-generate-always-reachable](./story-01-generate-always-reachable.md) | - |
| PHILO-4-02 | The new decision is in the visible rows | backlog | [story-02-decision-in-the-visible-rows](./story-02-decision-in-the-visible-rows.md) | - |
| PHILO-4-03 | A failure never collides with the next brief | backlog | [story-03-breakage-ids-never-collide](./story-03-breakage-ids-never-collide.md) | - |

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The verb (canvas first) | 01 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-4-01 | feat/philo-4-01-generate |
| The rows | 02 | Astra (Luna) | Muad'Dib | ../wt-philo-4-02 | feat/philo-4-02-rows |
| The ids | 03 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-4-03 | feat/philo-4-03-ids |

## Where we are

2026-09-23: chartered from the Phase 3 closure (`final-summary.md`, "What he still cannot do" 1–3) on the owner's word; Astra's check and the owner's ratification owed; 01's canvas next.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| 01 grows into a BRIEF-section redesign | medium | one verb, placed on the canvas, ratified; the section's rows and triage stay as built (Phase 175/200) | a second verb or a row change appears |
| 02's row cap is a ratified design, not a bug | medium | read the ratifying canvas for the three-row BRIEF (Phase 175 story 05); if the cap is ratified, the repair is ORDER (newest decision first), not the cap | the story changes the cap without his word |
| The id fix touches the schema | low | scope the id to the brief (`brief-break-pipeline-{brief_id}-{event_id}`) or make the insert idempotent; no migration (migrations stay minimal) | a schema change |

## Decisions made (this phase)

- 2026-09-23 — chartered on "yes close and open"; the service-layer draft renumbered to Phase 5 — Muad'Dib.

## Decisions deferred

- (none)
