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
| HS-201-01 | The desk names the one thing it needs | backlog | [story-01-the-desk-names-the-one-thing-it-needs](./story-01-the-desk-names-the-one-thing-it-needs.md) | - |
| HS-201-02 | Record works with no summary model | done | [story-02-record-works-with-no-summary-model](./story-02-record-works-with-no-summary-model.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-201-03 | The host is disclosed before the run and truthful after | done | [story-03-the-host-is-disclosed-before-the-run-and-truthful-after](./story-03-the-host-is-disclosed-before-the-run-and-truthful-after.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-201-04 | Ask for the summary and find it again | backlog | [story-04-ask-for-the-summary-and-find-it-again](./story-04-ask-for-the-summary-and-find-it-again.md) | - |
| HS-201-05 | One engine and one assignment from the face | done | [story-05-one-engine-and-one-assignment-from-the-face](./story-05-one-engine-and-one-assignment-from-the-face.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-201-06 | Plain words on the path | backlog | [story-06-plain-words-on-the-path](./story-06-plain-words-on-the-path.md) | - |
| HS-201-07 | Run it from main and the sitting | backlog | [story-07-run-it-from-main-and-the-sitting](./story-07-run-it-from-main-and-the-sitting.md) | - |

## Lanes (TWO-BRAINS.md §4)

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| A (runtime truth) | 02, 03, 05, and 07's backend edits (startup identity line, any conditional loop gate) | Astra, Luna xhigh workers | Muad'Dib | `../wt-201-a` | `feat/hs-201-a` |
| B (the face and the sitting) | 01, 04, 06, 07 (verification and the sitting) | Muad'Dib, Opus 4.6 workers | Astra | `../wt-201-b` | `feat/hs-201-b` |

Order: 03's API contract (`planned_route`, the receipt) is settled and checked by both brains FIRST; then 02 and 01 (independent; the dictation classification rides with 02); then 05; then 03 and 04 integrate; 06 with 04; 07 last. File ownership: lane A owns `holdspeak/**` on this path; lane B owns `web/**`; a field one lane needs from the other travels as a settled contract, never a cross-lane edit.

## Owed by lane B

Muad'Dib accepts these criteria as lane B's owner in the closure check
(`checks/lane-a-muaddib.md`). He will add them to the B story files in
`wt-201-b`. The table is the authoritative transfer record until then.
A's done status proves the backend only; it does not prove these faces.

| From | Receiving story | Transferred criterion |
|---|---|---|
| HS-201-02 | HS-201-01 | The Record verb renders that refusal token at the moment of refusal; shot at 1440. |
| HS-201-05 | HS-201-06 | Models renders these results and the assigned engine at both widths. |
| HS-201-05 | HS-201-06 | The face uses one gesture with no modal; Models shots after accept at both widths. |

The HS-201-06 transfer includes the Models summary-selection control and
its conflict and partial-result rendering, not labels alone.

## Where we are

Lane A backend implementation and source counsel are complete. The quiet full suite finished with 11,159 passed, 24 failed, 125 skipped and four strict expected failures. Failure classification and affected focused reruns are recorded in `audits/full-suite-astra.md`; the raw run is `audits/full-suite-astra.log`. Gate commits and the PR follow verification. B owns the face integration and the sitting. No phase exit criterion is closed by A.

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

- 2026-09-19 — Astra's lane A amendment, ratified by Muad'Dib (see
  `checks/lane-a-muaddib.md`): ordinary Web Record forces capture/transcription
  without live summary work; its Stop hook cannot auto-enqueue analysis or
  auto-title, even when legacy config enables them. A later disclosed summary
  gesture runs analysis only. The Phase 200 plugin → proposal bridge → Review
  pipeline therefore loses its production entry on this first-use path. This
  is a deliberately accepted regression of shipped product, not an inherited
  failure. The implementation stays parked; proposal expectations remain as
  strict expected failures with summary-ready preconditions still live.
- 2026-09-19 — Lane A and B have a merge interlock: no A-only merge while any
  face Run/Retry omits `expected_selection_hash`. B uses “summary” and must
  distinguish an unexecuted proposal chain from an empty extraction result.

- 2026-09-19 — The Model Library producer may declare the closed result schema
  supported by the existing meeting adapter, through a new immutable manifest
  revision for supported provider families. Muad'Dib ratified this narrow fix
  after the real producer chain failed summary selection. It is adapter support,
  not observed model quality; invalid output must fail with a contacted-host
  receipt and no partial summary. Old profile revisions stay unchanged. Deferred
  and live analysis share the schema hash, so both become compatible, but
  connect creates no assignment and summary selection creates no live assignment.

## Lane A debt ledger

- **b — fixed:** the actual Web Stop hook could enqueue a hashless job under
  `every_meeting` or `room_linked`; both red fences are recorded in 02 evidence.
- **a — tests of the former posture:** the Phase 200 proposal pipeline on
  manual summary runs. Return path and retained code: `../BACKLOG.md`,
  “Phase 201 parked summary follow-through”.
- **c — historical, not reproduced:** dictation initialization race. Two
  pristine charter-baseline runs and current scoped runs pass; original cause
  remains unknown (02 evidence).
- Legacy automatic-summary settings still describe the parked behavior:
  `services/settings_service.py`, `doctor.py`, `setup_status.py`, and
  `trust_destinations.py`. These controls must be retired or connected to a
  future disclosed opt-in path. They do not enable Web Record summary work.
- Hashless legacy entry points remain outside the first-use Record path:
  `meeting_import.py:_persist_import` can enqueue under old config;
  `db/meetings.py:recover_capture` can enqueue historical displaced
  work without a route bundle. Neither is proof of the new disclosure contract.
  Fence or disclose these before restoring their automatic summary behavior;
  parked with follow-through in BACKLOG. `meeting_session/persistence.py` is
  inactive for ordinary Web Record because that session has intel disabled.
- Inherited suite baseline: both widths of `test_phase200_daily_loop.py` fail
  at the brief before meeting creation, including on unmodified charter
  production code (raw baseline `.tmp/hs201-daily-loop-baseline.log`).
- Delivery Workbench capture stamps describe the index at capture time, not
  pytest import provenance; the gate checks the referenced passing capture but
  does not compare its index tree. Framework follow-up belongs to `pmo-roadmap`.
  See the peer correction in `checks/lane-a-muaddib.md`.
- Full-suite classification: nine stale contract assertions updated; two legacy
  integration callers migrated under Muad'Dib's closure assignment (98 tests
  passed);
  twelve inherited failures reproduced on the charter baseline; one no-write
  scanner failure passes twice with the tree quiet. Raw logs and per-group
  homes: `audits/full-suite-astra.md`.
- Inherited DW orientation issues: stale CLAUDE managed block; phase 101
  evidence/story status mismatch; missing final summaries 152/153/154/156/200.

## Open dissents

None.
