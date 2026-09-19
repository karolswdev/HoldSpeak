# R1 — the ten-workday observation period

**State: OPENED, NOT BEGUN. No observation has occurred. Every number
below is a denominator or a target, never a result.**

Opened by HS-200-16 (the machine half). This document is the instrument;
HS-200-23 closes the period and writes the verdict.

Canon: [ACCEPTANCE.md](ACCEPTANCE.md) §"Owner pilot entry",
§"Daily-practice sample", §"Usefulness targets", §"Review cadence",
§"Evidence record"; [CONTRACTS.md](CONTRACTS.md) §C12.

---

## 1. What is already proved, and what is not

Three legs, kept apart — the same separation the measured record keeps
(`assets/story-16-shots/loop-facts.json`, key `legs`):

| Leg | State on the day R1 opened |
|---|---|
| Fixture-proven | **Done.** The two-working-day loop runs end to end through the product's normal controls against a real hub, on controlled adapters, at 1440 and 393. `tests/e2e/test_phase200_daily_loop.py`; record in `assets/story-16-shots/loop-facts.json`. |
| Live model | **Not run.** No measured semantic behaviour in this phase comes from a live model on the daily path. Owed separately. The deterministic alternative is also unreachable from the face — see §9.3. |
| Owner usefulness judgment | **Does not exist.** HS-200-16's third acceptance criterion — *the user completes the path through normal controls without implementation guidance* — is the owner's own leg. It has not been walked and is not simulated anywhere. |

A fixture-proven loop says the product CAN carry work across days. It
says nothing about whether the work was worth carrying. That is what R1
measures.

## 2. Legs owed by the owner before R1 can be declared closed

1. **The attended two-day walk.** The owner completes the daily path on
   his own desk, unassisted, with no implementation guidance. Recorded
   as pass / fail / inconclusive with his own words.
2. **The live-model leg.** The same path with a real model on the
   preparation brief and the meeting extractors, so extraction precision
   and recall mean something.
3. **The keep / repair / stop judgment** for each recipe used
   (ACCEPTANCE P200-A28). Nobody else may record it for him.

## 3. The window

- **Length:** ten observed workdays. A workday counts as observed only
  if the owner was working that day; holidays and full days away are
  skipped, not scored.
- **Dating:** the window opens on the first workday the owner performs
  one predeclared task with the product, and that date is written into
  §7 below before any scoring. The window closes on the tenth observed
  workday, or later if §8's extension rule fires.
- **Build:** every observation records the build it ran on. The identity
  fields are the ones the product reports at
  `GET /api/system/identity` — `backend_revision`, `frontend_build`,
  `schema_version_loaded`, `config_revision` — never a hand-typed
  version. A build or configuration change mid-window is recorded, and
  comparisons are separated where the change materially affects
  behaviour (ACCEPTANCE §"Owner pilot entry").
- **Where it lives:** locally, in this file and its sibling observation
  rows, unless the owner names another destination. No passive
  telemetry is introduced. Anything published is synthetic or redacted.

## 4. Predeclared tasks

Tasks are selected **before** the assistant produces their results
(ACCEPTANCE §"Owner pilot entry"). Nothing is added to the sample after
seeing how well it went, and nothing is manufactured to fill a quota.

| # | Task | Denominator | Ground truth captured before scoring |
|---|---|---|---|
| T1 | Prepare a brief for a real meeting or a real piece of work | 5 sampled briefs | The owner's own statement of what he needed the brief to cover |
| T2 | Capture a real meeting and review its outcomes | 5 relevant meetings | An independent marking of the decisions and actions in that meeting, written before the extraction is read |
| T3 | Recall a decision or commitment from an earlier day | 10 recall tasks | The decision the owner was looking for, and its current status, named before the search |
| T4 | Publish a weekly Project update | 2 updates | The facts the owner intended the update to carry |
| T5 | Run an Interview session (3 of the 5 are revisits of an existing configuration) | 5 sessions | The configuration change intended, written before the session |
| T6 | Use each of the three starter recipes at least once | 3 recipes | — |

Every attempt enters its denominator, including the ones that fail, are
abandoned, or produce nothing usable.

## 5. What counts as what

These definitions are fixed now, before any observation, so they cannot
be softened later.

**A completed task.** The owner reached a result he kept — kept, sent,
published, or acted on — through the product's normal controls, without
implementation guidance and without a repair performed by anyone but
him. A result read and discarded is not completed; it is an attempt that
failed, and it stays in the denominator.

**A correction.** Any act by the owner that changes what the product
produced before he could keep it: editing a proposed sentence, naming an
owner or a date the extraction left unknown, re-pointing a citation,
re-running with a changed purpose, or fixing a field the product got
wrong. Counted per act, not per session. (The machine walk's own
correction count uses this definition: it recorded 1 — a commitment that
arrived with no due date and needed one before it could be completed.)

**An abandoned path.** The owner started a path and left it without a
kept result: pressing Stop, closing the surface, switching to doing the
work by hand, or hitting a refusal he chose not to repair. An abandoned
path is recorded with the reason and the point of abandonment. It is
never silently dropped.

**Active time vs elapsed time.** Active time is the owner's own attention
on the task — reading, correcting, deciding. Elapsed time includes model
latency, downloads and waits he did not spend attention on. They are
recorded separately, never summed into one figure (ACCEPTANCE
§"Performance targets": *Model completion time and active human effort
are separate measurements*).

**Source coverage.** Taken from the product's own coverage projection —
the `coverage` list and `complete` flag on
`GET /api/desk/needs-you?fresh=1`, in the shipped C4 vocabulary
(`available | stale | failed | forbidden | unavailable`,
`holdspeak/services/needs_you_aggregate.py:52`). Never recomputed by
hand for a report, and never rounded up to "fine".

## 6. The targets being measured

Restated from [ACCEPTANCE.md](ACCEPTANCE.md) §"Usefulness targets" so
this file is self-contained. **These are planning assumptions, not
achieved facts.** HS-200-01 may recalibrate one to the actual workload
with a recorded reason *before* scored sampling starts. Once sampling
starts, a missed target is a result and the threshold does not move.

| Measure | Target | Denominator |
|---|---|---|
| Preparation effort | Under 5 active minutes per brief | T1, 5 briefs |
| Extraction precision | ≥ 90% | T2, all proposals across 5 meetings |
| Extraction recall | ≥ 90% | T2, all independently marked decisions/actions |
| Decision recall | ≥ 8 of 10 correct within one minute | T3, 10 tasks |
| Interview first value | Under 10 active minutes | T5, first-value sessions |
| Interview revisit | Under 3 active minutes, no duplicates | T5, 3 revisits |
| Suggestion usefulness | ≥ 3 of 5 sessions | T5, 5 sessions |
| Intentional daily use | ≥ 8 of 10 observed workdays | the window |
| Attention relevance | baseline set at midpoint; missed needs reported separately | T1/T3 arrival reads |
| Net time recovered | ≥ 120 minutes per five-workday week | baseline minus all assisted effort |
| Outcome quality | ≥ 2 concrete source-supported examples | the window |

Net time subtracts capture, setup, source selection, review, correction,
supervision, repair and maintenance from the baseline. Shared setup is
allocated once. An avoided hypothetical incident is never converted into
invented savings.

## 7. The observation log

**Empty. No observation has occurred.**

Window opened: _(not yet — the first observed workday's date goes here)_
Window closes: _(the tenth observed workday)_

| # | Date | Task | Build | Model + route | Active min | Elapsed min | Corrections | Abandoned | Coverage | Result | Reason / follow-up |
|---|---|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — | — | — |

Each row carries the seven fields ACCEPTANCE §"Evidence record"
requires: Identity, Task, Execution, Review, Effort, Coverage, Result.

## 8. Review cadence and the inconclusive rule

- **Day 5.** Name the three largest causes of lost effort or wrong
  output. Route each to its owning story. The failed observations are
  preserved, not corrected away.
- **Day 10.** Classify every target in §6 as pass, fail, or
  inconclusive. Record whether the owner wants to continue each recipe,
  and why. Spontaneous return to a recipe is useful evidence; required
  daily use as a compliance exercise is not.
- **Not enough opportunities.** If the owner's real work does not supply
  the denominators in §4, the window extends. The result stays
  **inconclusive** until enough relevant observations exist. Meetings
  and assignments are never manufactured to fill a quota, and the
  easiest tasks are never selected preferentially.
- **HS-200-23** closes this period. HS-200-30 (supervised assignments)
  and HS-200-36 (unattended occurrences) are separate samples and are
  not merged into these counts; HS-200-37 combines them without
  double-counting.

## 9. Known limits of the instrument on the day it opened

Recorded here so they are not discovered as surprises later.

1. **No clock seam.** The product has no clock injection; the machine
   walk crosses its day boundary with a real earlier meeting date and a
   hub restart. R1's days are real days and need no such device, but any
   future automated multi-day rig inherits this limit.
2. **One confirmed outcome is recorded twice, and the brief shows both.**
   *For the owner to rule.* Confirming either a decision or an action
   deliberately records **both** a decision and a commitment
   (`holdspeak/services/proposal_bridge_service.py:588-590`), so day
   two's brief lists yesterday's two outcomes as four rows — each one
   once as a decision and once as a commitment
   (`assets/story-16-shots/day2-prepare-1440.png`). Every row is now
   labelled truthfully (`DEC` / `CMT`); HS-200-16 fixed a version of
   this ledger that drew the commitment as `DEC · CURRENT` and the
   decision as `CMT`. **The question left is only whether the brief
   should show the pair or fold it into one row**, and it is a design
   question, not a defect. Left as built. Anyone scoring extraction
   counts against T2's denominator counts *outcomes*, not ledger rows.
3. **No owner can choose a deterministic brief today.** The hub accepts
   `generator: "deterministic"` on
   `POST /api/projects/{id}/briefs/prepare`
   (`holdspeak/services/preparation_brief_service.py:890-912`) and the
   face never sends it
   (`web/src/features/project-room/prepare/api.ts`), so every brief
   prepared through the Room goes to a model route. R1 therefore cannot
   sample a model-free brief, and HS-200-16's machine leg proves the
   model path with a controlled local adapter rather than the
   deterministic drafter. Reaching it needs a face change.
4. **Attention relevance has no baseline yet**, by design: it is set at
   the midpoint of the window (ACCEPTANCE §"Usefulness targets").
