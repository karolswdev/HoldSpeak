# Lane A — backend handoff

Astra session: `01a0bbc3-9bbd-7513-a76d-f6cc139fae2d`.
Worktree: `/Users/karol/dev/tools/wt-201-a`; branch: `feat/hs-201-a`.
Verification and counsel are in progress. This file records the API handoff;
it does not close lane B's face work or the owner's sitting.

## Record — B story 01

Normal web Record requests capture and transcription. Summary execution is a
later gesture. The Record response and meeting detail carry
`transcription_status` and `transcription_status_detail`. A missing assignment
returns `record_only` with:

```json
{
  "family": "meeting-route-assignments",
  "reason_code": "no_assignment",
  "repair": "repair_meeting_route_assignment"
}
```

Lane B renders the Record refusal token. Lane A does not edit Chair files.
Retry retains this cause instead of changing it to an empty-transcript error.

## Route and receipt — B story 04

Use story 03's settled contract. Read `planned_route` before Run or Retry.
Send its `selection_hash` as `expected_selection_hash`; show each disclosed
host, including fallback hosts. A missing or changed selection is a refusal.
Use `run_receipt` for past execution; do not derive execution hosts from the
current model configuration. The meeting detail, ledger, and recovery reads
serve this contract. Lane A's tests must verify all three run endpoints.

## Summary selection — B story 06

The explicit owner gesture can call
`POST /api/concierge/summary-selection` with:

```json
{
  "commandId": "unique-command-id",
  "expectedAssignmentRevision": 0,
  "profileId": "selected-model-profile",
  "profileRevision": 2
}
```

Use the real revisions from the read model. The response carries `status`,
one visible `receipt`, a `result` with `state`, `code` and `plainReason` where
needed, and `summaryAssignment`. Inspect the result; HTTP 200 alone does not
mean the selection succeeded. `GET /api/concierge/detect` also exposes
`summaryAssignment`, including the current assignment and profile revisions.

The existing Concierge Apply gesture treats its `meetings` row as selection
of the exact `meeting.deferred_analysis` capability. Connecting a model is a
separate action and must leave assignments unchanged. The summary choice
must not change the speech assignment.

## Verification boundary

Controlled fixtures replace model and audio devices. No worker records the
microphone or writes to the owner's desk. Lane A can prove persistence through
an isolated hub restart. Lane B owns the 1440/393 refusal, route, and Models
face checks, and story 07 owns the observed sitting on the owner's desk.

## Startup — B story 07

The existing startup identity capture prints `backend_commit`,
`frontend_build`, and `database_path` on one line. See
`audits/startup-astra.md` for the red fence, focused run, and actual isolated
startup-seam log. No conditional loop gate was needed or added; the sitting's
read-only before/after loop counts remain B's verification.

## Observed integration gap in the current face

The HS-170 browser probe read a ready `planned_route` but the existing Run
button sent no `expected_selection_hash`. B must send the hash for all three
gestures before this backend is merged into the combined phase. The old face
test retains its original host-chip assertions and only its fake service
signature is adapted; the new real HTTP tests enforce the backend refusal.

## Merge interlock and summary-only scope

Do not merge lane A before lane B supplies `expected_selection_hash` for Run,
Retry, and recovery Retry. The API and its consumers must land together. Every
409 carries `code`, the fresh `planned_route`, and the relevant `run_receipt`;
the response does not turn an old successful receipt into a new refusal.

Use **summary** in face labels, not intelligence. A disclosed summary request
runs analysis only. It does not run the Phase 200 plugin proposal chain. Review
must show nothing or **Not run** for that unexecuted chain; it must not imply
that extraction ran and found no proposals or show a counter of zero. Lane B
owns this face check. This is an accepted behavior change, recorded with the
peer ruling in `checks/lane-a-muaddib.md` and parked in `../BACKLOG.md`.

A legacy endpoint can have a `profileId` without a `profileRevision`. Such a row
cannot be selected for summaries. Never invent revision 1 on the face.


## Full-suite integration handoff

Two legacy integration tests still omit `expected_selection_hash`: the
queue API retry test in `tests/integration/test_web_server.py` and the partial
recovery test in `tests/integration/test_meeting_intel_recovery.py`. Both pass
on the charter baseline and now correctly receive 409. Migrate those test
fixtures to a compatible exact assignment and submit the read-model hash;
do not weaken the new endpoint requirement. They are outside A's assigned
test directories. Other inherited failures and raw baseline reproductions
are in `audits/full-suite-astra.md`.
