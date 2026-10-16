# Notice and Remote access recovery — bounded preparation

HOLD FOR SHIP. Source inspection only, 2026-10-16: no product changes, tests,
browser runs or implementation GO. Root settles the actual-library recovery
pose after the first deployment. This refines NEXT-CREATION.md; it does not
restart the audit. Anchors describe the inspected source and can drift.

Tuesday: read the current remote-access state, distinguish a failed read from
a refused/unknown write, and inspect current state without replaying a credential
or authority change. Tenets 1/3/5/7: existing components, existing authorities,
no new framework or idempotency layer.

## Ambient proposal candidate: dormant, outside the next build

The active file is `web/src/components/AmbientLayer.tsx`, not
`desk/components/AmbientLayer.tsx`. Its runtime listener at `:341–366` accepts
`actuator_proposed`, `aftercare_ready`, and `learning_event`, but every
non-learning frame triggers `refreshAmbient()` and returns. Only learning
events enter the local `cards` queue. Consequently the `actuator_proposed`
Approve/Decline branch at `:467` has no current producer path into that queue.
The exact-card/finally-only race at `:408–419` is a dormant compatibility
candidate, not an observed active owner journey.

Current actuator attention is a durable projection. Its real action is
Review source when the projection supplies a non-root detail URL (`:448–465`).
The already repaired projection dismissal pins its exact row through pending
and refusal (`:390–406`); journal exclusion and old-popup suppression remain
unchanged. Do not reconnect raw frames, expose dormant decision buttons, or
add a test that fabricates an unreachable local proposal card to claim coverage.
Ambient product edits are OUT of the next implementation. Add a current-route
assertion only if a genuine projection-route gap is demonstrated.

The dormant handler's actual API contract was checked, not invented:

- `POST /api/meetings/{meeting_id}/proposals/{proposal_id}/decision` accepts
  `{decision: "approved" | "rejected"}` with optional `decided_by`/`grant_id`
  (`web_requests.py:31`; `web/routes/meetings/aftercare.py:43`). Central
  `principals.required_right` defaults this route to OWNER (`principals.py:751–812`).
- `MeetingAftercareService.decide_proposal` (`:106–135`) requires a
  meeting-origin proposal with that exact meeting ID. Approval checks captured
  policy/grant authority; Slack approval is explicitly parked. Invalid decisions
  or illegal transitions are HTTP400; missing/wrong-scope proposals are404.
- A successful reply is `{success: true, proposal: ...}`. The stored proposal
  payload includes `id`, `status`, `review_decision`, `authorization_state`,
  `execution_state`, `result` and `error` (`meeting_aftercare_service.py:37`).
  This meeting route transitions approval/rejection; it does not invoke an
  execution leg. Never translate an approved reply into Sent/Executed. Desk
  actuator routes have distinct target/execution contracts and are not substitutes.

Preservation assertions already exist in `components/ambientDismiss.test.tsx`:
`keeps the clicked row pending while the writer's ambient refresh selects another row`,
`keeps a failed write visible and retries its exact ID after a refresh`, and
`preserves runtime learning cards when old attention is suppressed`.
`ambientDoorless202.test.tsx` asserts a doorless projection stays in its own
branch. These assertions were read; no run occurred in this preparation.

## Next E: Remote read/write ownership

`RemoteAccessModule` in `web/src/pages/cores/SettingsCore.tsx:722` stores every
generic error in one string (`:738`). `fetchRemote` GETs current state and clears
that string on success (`:753–765`). Toggle PUT (`:770–783`), issue POST
(`:785–815`), credential DELETE (`:887–915`) and unstructured grant failures
all write it. The footer error action at `:1229` says Retry but only GETs remote
state. The first-read Retry at `:924` is correctly a read recovery.

Structured desk/project grant refusals already have per-identity/per-project
records and authoritative receipts (`:833–847`, `:869–883`). Keep those. Their
`finally` reread can currently clear a generic transport-write error; a new
read must not be reported as acceptance of that write.

The row's project-choice GET at `:941–943` also uses the same error string,
while common Retry reads `/api/settings/remote`. Capture its failed read target
if touching shared Remote error ownership; Retry for that failure must reread
`/api/projects`, not replay a grant or claim the choices are empty.

Settled minimal recovery behavior:

1. Keep small read/write error provenance inside this module, including the
   failed read target or named write/subject. Existing SurfaceState/error row
   and library Button compose the recovery; no new global hook or receipt type.
2. A failed GET offers Retry for that exact read. Preserve last known remote
   material and open row context while rereading. A write failure names its
   action/subject and offers Reload current state. Reload performs only GET;
   it never resubmits PUT/POST/DELETE or reports the failed write as retried.
3. Read success clears its read failure, not a still-owned write failure or
   structured grant refusal. An automatic grant reread must not erase an
   unstructured write failure before the owner can see it. A later explicit
   writer owns its own new outcome. Do not infer original-write acceptance
   solely from the reread.
4. Retain the Issue well's name, access and expiry and the current row expansion
   through read failure/Reload. `fetchRemote` already leaves these state fields
   alone; preserve that behavior. Preserve the existing one-time token contract;
   GET never supplies the plaintext token again.

Authority and reply facts: `web/routes/mcp_http.py:321–500` gates remote
settings GET/PUT and credential POST/DELETE to OWNER. GET returns current
enabled/address/credential/grant facts without plaintext tokens. Issue returns
the token once with ID/identity/palette/expiry. Revoke can fail503 with
`credential_revoke_not_persisted`, `retry: true`, and partial grant facts; this
batch does not turn that server fact into automatic DELETE replay. Delegation
PUT/DELETE (`:520–580`) deliberately reaches the kernel through AGENT_SUBMIT
so owner-authority refusal gets its existing receipt. Do not replace that with
a blanket route-owner check.

## Exact file boundary and scoped checks after GO

Product: `web/src/pages/cores/SettingsCore.tsx`, only RemoteAccessModule error
ownership/recovery. Primary test file:
`web/src/pages/cores/__tests__/remoteAccess.test.tsx`, reusing its recorded
remote-settings wire fixtures. No backend, Ambient, shared API or draft-store
change is proposed.

Planned test titles (new assertions, not claims of existing coverage):

- `a failed remote GET retries that read and keeps the last known ledger`
- `a refused remote write offers Reload and never replays its writer`
- `Reload preserves unsaved issue name, access, expiry and row expansion`
- `an automatic grant reread retains its named transport write failure`
- `a failed project choices GET retries projects without replaying a grant`

Read these existing preservation assertions in the scoped test file:
`token appears once after issue and is not re-rendered after refetch` and
`Revoke removes the credential row`. If the grant/error branches change, also
run the existing `web/src/desk/__tests__/settings.app.test.tsx`, especially
`Allow, Stop, and a refused Stop on the rendered row; the receipt names it and outlives the act`
and `ON, issue: the token shows once with Copy; the row reads NEVER USED; Revoke removes that row only`.
Collect and run only that named budget under the lock with isolated HOME after
root GO. Existing integration wire producer is
`tests/integration/test_remote_settings_wire.py::test_the_remote_settings_answers_are_the_hubs`;
no backend behavior changes or new backend test run are needed for this label/
ownership scope.

Coverage status: current source/read assertions inspected; new recovery tests
not written or run; actual populated pending/refused/Reload 1440/393 geometry,
remote-client transport, lost-response outcome and owner visual acceptance remain
unverified. Root's canvas and isolated walkthrough must show the truthful
Read failed/Retry and named Write failed/Reload poses. No dormant proposal
decision pose belongs in that canvas.
