# Phase 201 - One Meeting Result

**Last updated:** 2026-09-19. Chartered from the inventory of 2026-09-19 and
two Astra checks (`docs/internal/inventory-2026-09-19/06-check-astra.md`,
`docs/internal/checks/constitution-seven-tenets-astra.md`). Stories and
lanes follow the two read-only audits (runtime by Astra, live face walk by
an Opus worker) and Astra's check of this charter.

## Goal

The owner records one real meeting, gets a truthful, useful summary he can
find again after a restart. His first real use.

## Governing canon

The Seven Tenets (`docs/internal/CONSTITUTION.md`, top), first: 1 no
over-engineering for safety; 2 not even pre-alpha, he has not used it once;
3 help and accelerate, no unnecessary interface; 4 ASD-STE100 on every face;
5 compose the component framework; 6 Workbench 2.0+ on steroids; 7 the first
user is a Senior Software Architect with reports. Then Article III (honest
egress, at the point of decision), VI (honest by construction), IX (proof
over claim). Faces obey UX-CANON. Orchestration: TWO-BRAINS.md.

## Scope

- **In:** only what this path needs: the hub from an identified build and
  DB; record one meeting; ask for its summary; the egress host disclosed
  before the run and truthful after; a useful summary traceable to that
  meeting; found again after a hub restart. Every label on the path in
  ASD-STE100. Dictation must not regress (regression obligation, not a
  story).
- **Out (parked as first-use prerequisites, never deleted):** Room
  linking, connector setup, watch creation, the Models naming collapse,
  worktree cleanup, roadmap bookkeeping, the Go rail, config relocation,
  the run-primitive collapse, docs rewrites, any new platform scope.

## Exit criteria (evidence required)

- [ ] The hub runs from the main checkout on a stable port and prints the
      commit and the DB path it uses; a restart is observed on the
      owner's desk (shot + log line).
- [ ] The owner records one real meeting through the face, with no
      guidance from an agent (shot from his desk).
- [ ] Before the summary runs, the face names the route that will run it
      (host and any fallback); after, the receipt names every destination
      contacted, and every one belongs to the disclosed route; an
      unresolved route is never shown as `local` (shots + the run's row).
- [ ] The summary is useful to the owner and traceable to that meeting
      (his verdict, recorded; the DB row linking summary to meeting).
- [ ] After a hub restart on the same DB the owner finds the same summary
      in at most two moves (shot).
- [ ] Dictation delivers typed text after that restart (shot or log).
- [ ] Every label on the path reads in ASD-STE100 (the walk's label list,
      each fixed or justified).
- [ ] The sitting happens immediately after; its notes are this phase's
      final summary.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-201-01 | The desk names the one thing it needs | done | [story-01-the-desk-names-the-one-thing-it-needs](./story-01-the-desk-names-the-one-thing-it-needs.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-201-02 | Record works with no summary model | backlog | [story-02-record-works-with-no-summary-model](./story-02-record-works-with-no-summary-model.md) | - |
| HS-201-03 | The host is disclosed before the run and truthful after | backlog | [story-03-the-host-is-disclosed-before-the-run-and-truthful-after](./story-03-the-host-is-disclosed-before-the-run-and-truthful-after.md) | - |
| HS-201-04 | Ask for the summary and find it again | backlog | [story-04-ask-for-the-summary-and-find-it-again](./story-04-ask-for-the-summary-and-find-it-again.md) | - |
| HS-201-05 | One engine and one assignment from the face | backlog | [story-05-one-engine-and-one-assignment-from-the-face](./story-05-one-engine-and-one-assignment-from-the-face.md) | - |
| HS-201-06 | Plain words on the path | done | [story-06-plain-words-on-the-path](./story-06-plain-words-on-the-path.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-201-07 | Run it from main and the sitting | backlog | [story-07-run-it-from-main-and-the-sitting](./story-07-run-it-from-main-and-the-sitting.md) | - |

## Lanes (TWO-BRAINS.md §4)

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| A (runtime truth) | 02, 03, 05, and 07's backend edits (startup identity line, any conditional loop gate) | Astra, Luna xhigh workers | Muad'Dib | `../wt-201-a` | `feat/hs-201-a` |
| B (the face and the sitting) | 01, 04, 06, 07 (verification and the sitting) | Muad'Dib, Opus 4.6 workers | Astra | `../wt-201-b` | `feat/hs-201-b` |

Order: 03's API contract (`planned_route`, the receipt) is settled and checked by both brains FIRST; then 02 and 01 (independent; the dictation classification rides with 02); then 05; then 03 and 04 integrate; 06 with 04; 07 last. File ownership: lane A owns `holdspeak/**` on this path; lane B owns `web/**`; a field one lane needs from the other travels as a settled contract, never a cross-lane edit.

## Where we are

Chartered: seven stories from two read-only audits (`audits/`), shots in `assets/charter-walk/`. Astra's check: RATIFY-WITH-CONDITIONS, seven conditions applied (`checks/charter-astra.md`). Round two applied and the 03 contract settled. Next: commit through the gate, brief lanes.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The phase grows past one result (tenets 2, 3) | high | Every story must name the exit criterion it serves; anything else parks | A story with no exit criterion behind it |
| The summary runs but is not useful to him | medium | The exit is his verdict, not a row count | He reads it and shrugs |
| A repair touches his live desk | low | Worker rigs: isolated HOME AND keychain, env-scoped subprocesses, no desktop typing, no audio outside the walk HOME; the owner alone starts, restarts and gestures on his desk; no agent terminates a PID it did not verify | Any agent write, keystroke or capture outside a walk HOME |

## Decisions made (this phase)

- 2026-09-19 - Chartered as the smallest first-use phase, replacing the
  inventory's U1–U3 ladder and the "One Journey" re-cut - tenets 2 and 3;
  Astra's finding 7 on the tenets check - Muad'Dib, ratified by Astra
  (RATIFY-WITH-CONDITIONS, conditions absorbed).
- 2026-09-19 - Restoring the owner's Room from the retired DB (Z0) is
  parked: one meeting result does not need it - tenet 3 - Muad'Dib.

## Open dissents

None.
