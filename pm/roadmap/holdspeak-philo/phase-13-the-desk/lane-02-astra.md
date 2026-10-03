# PHILO-13-02 — Astra backend lane record

**Status:** DRAFT — UNCHECKED — awaiting Muad'Dib. Story 02 remains in-progress pending H-A1 and A1-F merged together in its closing record.

LANE: Data + truth, Wave 1; PHILO-13-02 H-A1. Worktree `/Users/karol/dev/tools/wt-philo-13-astra`; local branch `feat/philo-13-astra`. This half follows B0 commit `c7073f9cac59e898e53f425f4a437966a10aaa0b`; its draft PR uses a separate remote branch so the B0 PR remains bounded.

OUTCOME: Normal meeting and Workbench item removal parks the stored row. Normal lists omit parked rows; explicit parked reads and restore retain their IDs and content across DB reopen. Workbench bulk transitions validate all members in one transaction. A claimed item refuses parking; an item parked before claim is skipped by the runner. [H-A1 client contract](handoff-a1-astra.md) gives the faces lane the routes and API functions. No face or CSS changed.

PROOF:

- **335 collected; 335 passed in 60.64 s**, each pytest process under an isolated HOME. [Collection](assets/story-02-backend/a1-final-collection.txt), [run](assets/story-02-backend/a1-final-run.txt), [DW captures](assets/story-02-backend/captured-runs.md), final capture `2026-10-02T03:54:51Z`. The scoped selection includes the actual repositories, services, routes, MCP dispatch, runner, schema, API inventory and both atlas guard files. No full suite or metal tests ran.
- The two retention fences were run against the original production deletion methods from `c7073f9`. Both failed at `assert retained_row is not None`. Byte-identical method restoration then passed both tests. [Raw red/green record](assets/story-02-backend/retention-mutants.txt). These failures prove row loss, rather than a missing new method or a test double's invented field.
- Meeting proof creates non-empty transcript, summary, action, artifact and project links through the stored-state producer, then parks, reads the retained DB rows, reopens and restores. Workbench proof covers single and bulk routes, refusal atomicity, idempotence, saved results and reload. A real runner produces an artifact, run and receipt; their exact stored rows and source links survive park, DB reopen and restore. That runner test substitutes inference text only.
- All **four final actual atlas runs pass**: meetings and Workbench at 1440 and 393. Each invocation has its own HOME; the phone entry uses native touch. [Walk index](walks-02-astra.md), [selected observations](assets/story-02-backend/selected-runs.json), [SHA-256 manifest](assets/story-02-backend/manifest.json). Astra read each observation and both screenshots before the next run. The live cases use real HTTP routes and hub restart while parked. They do not certify the Parked filter or Restore Button.
- The production web build passed in 6.63 s. [Build output](assets/story-02-backend/a1-web-build.txt). Existing bundle-size notices remain. Earlier atlas failures and screenshot-readiness attempts are retained in the capture and calibration archives; all four final cases ran after the schema timeout field was corrected.

LEDGER: The destructive normal removal path is paid in H-A1, under Tenet 3 and the standing park-never-delete rule. The proposal path now distinguishes a parked parent (restore it, 409) from a genuinely missing historical parent; the historical orphan guard keeps its original assertions. The runner's park-before-claim race is fenced. A1-F owns the Parked filter, Restore Buttons, receipt in every reached branch, refusal receipt and 8-second removal window after C1's artboard. The phone's restored meeting card can be covered by the bottom action strip; that existing C7 finding remains in the B0 ledger.

AMENDMENTS: None to acceptance or ownership. The legacy normal delete entry points now perform the authorized park transition. The story and phase row stay in-progress. PMO-CONTRACT §6 forbids adding canonical closing evidence without a done flip, so exact DW captures are archived under assets; the closing commit must add `evidence-story-02.md` with the honest done flip after both halves merge. The scripts in the archive reproduce commands when copied back to `.tmp/philo-13-astra/` and run from the repository root.

UNKNOWN: Muad'Dib's built check, merged-main behavior, A1-F face transitions and the owner's desk sitting. No real send ran. Tuesday: the retained data and restore API are ready for the face handoff; the owner still needs the visible Parked and Restore controls to recover work through the desk.

## R2 counsel paid — 2026-10-02

LANE: PHILO-13-02 H-A1, Astra backend half; branch `feat/philo-13-a1-astra`, PR #727.

OUTCOME: Paid Muad'Dib's signed C1–C3 conditions. Meeting removal continues to park. Its dependent owner reads now omit the parked meeting and its action items; restore makes them visible again. Choosing an incoming sync tombstone parks the canonical row and retains its children. No face or CSS changed.

PROOF:

- **112 tests collected; 112 passed in 28.87 s**. The collect and run commands name the same nine suites, including the producer, route, sync, Monday Brief, Recall, People, Project and projection tests. The exact DW capture is archived at [r2 green capture](assets/story-02-backend/r2-green-dw-capture.md); the pending paired evidence file remains under `.tmp` because A1-F is not merged.
- The five real-producer C1 read-family cases and three C2/C3 route/state fences were run against the branch's original production files at `65d55047`. **All eight failed**: Brief, calendar coverage, Recall, proposals, and Intel claims each surfaced a parked Meeting; the projection route exposed parked actuator/artifact/job/conflict rows, a selected incoming tombstone removed the canonical Meeting, and the collected C3 reads showed linked actions and speaker/People history remained. The corrected C3 fixture stores a speaker through the real Meeting save path. Raw baseline output: [eight red fences](assets/story-02-backend/r2-baseline-red.txt).
- The same four fences pass with the implementation. The projection filter runs before projection pagination, so a parked meeting does not affect the returned page or total. The projected source families and a linked artifact are filtered from the active-meeting map.
- No live face walk or screenshot was required for this backend-only condition work. No full suite or real send ran.

LEDGER: C1 filters parked meetings from the Monday Brief, recorded calendar coverage, Recall, proposals, Intel job claims, and needs-you projection sources. C2 makes sync tombstones park and resolve the conflict while retaining the canonical row and children. C3 hides linked actions from global, Project and People reads, plus speaker history/statistics, while keeping standalone actions visible. The accepted five-column handoff table stays as written; no disagreement with Muad'Dib's conditions.

AMENDMENTS: The phase ownership/handoff table records the whole-Meeting read boundary and the A1-F dependency. PHILO-13-02 remains in-progress because A1-F has not merged. This PR remains DRAFT — r2, awaiting Muad'Dib.

UNKNOWN: The owner's face behavior and actual desk sitting remain for A1-F. The exact subset of projection data exposed on a face after its cache refresh was not inspected here. Tuesday: data parked in the backend can no longer leak through the named reads, and the separate A1-F face is still needed to restore it.
