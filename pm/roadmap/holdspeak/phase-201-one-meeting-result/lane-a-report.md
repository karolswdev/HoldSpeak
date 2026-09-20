# Phase 201 lane A report

**LANE:** A, Astra. Stories HS-201-02, HS-201-03, HS-201-05; 07 backend
startup line only. Worktree `/Users/karol/dev/tools/wt-201-a`, branch
`feat/hs-201-a`. PR: [#588 — HS-201 lane A](https://github.com/karolswdev/HoldSpeak/pull/588),
base `main`, open and unmerged.
Session: `01a0bbc3-9bbd-7513-a76d-f6cc139fae2d`.

**OUTCOME:** Backend built and verified; the three stories and startup backend
are committed through the gate and pushed. The single review PR is open;
Astra did not merge it. Record uses
speech without a summary model. Summary selection creates the exact capability
assignment. The route is disclosed before a run, bound before dispatch, and
actual attempts persist in a receipt across restart. The startup line identifies
the backend commit, frontend build and DB path. No merge or owner-sitting close.

**PROOF:** Astra's final focused captures: 02 — 185 passed, 11 optional-engine
skips (196 collected); 03 — 176 passed, four strict proposal xfails (180
collected); 05 — 59 passed. Startup focused suite: 23 passed; the final full
run also passed the startup test. Evidence is beside each story; startup proof
is in `audits/startup-astra.md`. Red fences and raw collection output are kept.

The quiet full run: **11,159 passed, 24 failed, 125 skipped, four xfailed**.
Nine stale contract assertions were updated and passed the final focused
captures. Twelve failures reproduce on the pristine charter baseline; two old
integration callers were migrated and pass a broader 98-test root capture; one scanner no-write failure
passes twice in a quiet tree. No full-suite green is claimed. Complete output
and classification: `audits/full-suite-astra.log` and `audits/full-suite-astra.md`.
At initial delivery, product code was unchanged after that full run.
The counsel follow-up below changes product code and has fresh focused proof.

A real isolated hub restart preserved the fixture summary and receipt. Shots:
`assets/lane-a/meeting-after-restart-1440.png` and
`assets/lane-a/meeting-after-restart-393.png`. They show the saved transcript
in the existing face. The stub engine and fixture WAV prove plumbing, not
live-model quality or the owner's usefulness verdict. B owes the new faces.

**LEDGER:** Classification a: old recording/contract expectations updated;
two integration callers were assigned to A by Muad'Dib at closure and now
submit `expected_selection_hash` from a compatible route. Their broader
98-test suite passes. Classification b: the
Web Stop auto-enqueue side door was reproduced and fixed. Classification c:
the historical dictation race did not reproduce on two baseline runs or the
current suite; the scanner status failure does not recur in two quiet runs.
Its concurrent-writer explanation is an inference, not a proved exact cause.

The shipped Phase 200 plugin → proposal bridge → Review pipeline loses its
entry on this first-use path. This is an accepted regression, not baseline
debt. Its code and original assertions remain parked. Return path:
`../BACKLOG.md`, “Phase 201 parked summary follow-through”. Hashless import
and historical recovery sites, old automatic-summary settings, inherited
suite failures and inherited DW roadmap issues are named in the phase ledger.
DW capture-index metadata is not enforced against a commit; framework
follow-up belongs to `pmo-roadmap`, as the peer correction records.

**AMENDMENTS:** Web Record requests speech only and Stop queues no text work.
A disclosed manual summary runs analysis only. Muad'Dib ratified this scope
and the accepted proposal regression. The Model Library publishes existing
adapter schema support through a new immutable manifest revision. This is
not empirical model qualification. Connect creates no assignment; the summary
gesture creates no live-analysis assignment, though the schema is shared.
Owner may overrule these amendments at the sitting.

Peer source verdict: **RATIFY-WITH-CONDITIONS**, source conditions discharged;
closure conditions, accepted B-criterion transfers and the capture-stamp correction are recorded
in `checks/lane-a-muaddib.md`. Astra ratifies backend completion for a review PR; Muad'Dib ratifies it with the recorded closure conditions. The two integration test migrations are complete in A on his assignment (98 tests passed). No open dissent. This is not counsel-on-built
of the eventual PR and does not authorize a merge.

**UNKNOWN:** The final PR CI result (checks queued/running at delivery); B's hash consumers and new refusal/Models/summary faces; real
model quality; owner desk startup/restart, actual microphone and typed
dictation; before/after loop counts and the sitting. Story 07 and all phase
exit criteria remain open. No loop was shown unable to stay inactive, so
no loop gate was added. No owner desk state was touched.

**Merge interlock:** A must not merge before B sends `expected_selection_hash`
on all three Run/Retry gestures. B uses “summary” and shows an absent/“Not run”
Review state for the unexecuted proposal chain. B owns Record token 01,
summary/route faces 04 and Models controls/labels 06. B receives `transcription_status_detail`, `planned_route`, `run_receipt`,
`summaryAssignment`, and `ConciergeSummaryAssignmentReceipt@1`; the transport
details and the completed test migration are in `lane-a-handoff.md`.


Gate commits: 02 — `183f1b5c`; 03 — `16a122ed`; 05 — `6365b7d3`.
Each flips one story and ships its evidence. Startup backend is `00a10e44`, a separate
commit with no story flip. `dw gate --porcelain` passed each; `dw check`
retains the inherited issues in the ledger and no new Phase 201 issue.

Initial-delivery source verification: `holdspeak/**` then equalled full-suite
product snapshot `18f67176`. The later counsel follow-up has separate focused
verification; that old snapshot is not a full run of the follow-up.


## Counsel-on-built follow-up — 2026-09-19

**LANE:** A, Astra; same worktree, branch, PR #588 and session above.

**OUTCOME:** All three requested backend repairs are implemented. An executed
receipt survives later refusals, `last_refusal` is separate, four reporting
surfaces say live analysis is off for Record, and post-contact exceptions keep
durable attempt evidence. No story status flips. PR #588 remains open.

**PROOF:** Astra independently captured 218 receipt/queue/HTTP passes;
152 recording/reporting/census passes and 11 optional-engine skips; 30 source
guard passes; and the real isolated hub restart (one pass). Both 1440 and 393
shots were inspected in `assets/lane-a-followup/`. The shots show the existing
lane A record face, not lane B's new summary/refusal face. Twelve new-fence
cases were collected. Raw pre-fix failures and current passes are appended to
stories 02 and 03. Post-merge verification is recorded below.

**LEDGER:** The three follow-up items are paid within their named scope. Only
stale doctor/setup expectations and source-line census anchors changed with
the reporters. The old full-suite result remains historical; no fresh full
suite or full green is claimed. The inherited DW doctor/check issues remain
outside this follow-up. No owner desk state or microphone was used.

**AMENDMENTS:** Chosen knob fix: retire its reporting on Record. No schema,
loop gate, or live-analysis reconnection. New B read-model field:
`last_refusal` on detail/list/recovery and 409. No `web/**` changes.

**UNKNOWN:** B's face completion and the copied-real-DB reconciliation are
reported by Muad'Dib/the caller; Astra did not repeat them. Real model quality,
owner sitting, and the final post-push CI verdict remain unverified. If durable
kernel evidence itself cannot be read, no public receipt is fabricated; the
error is logged. The first worker red attempts were not all retained with
reliable import provenance. Astra therefore captured historical reproductions
from archived `ae9edfde` with the actual imported path printed, followed by
current-code green runs. No historical run is presented as an untouched-tree
chronological capture.
