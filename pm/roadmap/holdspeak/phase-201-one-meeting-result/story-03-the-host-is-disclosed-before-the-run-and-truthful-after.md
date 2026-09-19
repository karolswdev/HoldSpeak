# HS-201-03 - The host is disclosed before the run and truthful after

- **Project:** holdspeak
- **Phase:** 201
- **Status:** backlog
- **Depends on:** HS-201-02
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

The displayed host and the executing route come from different stacks. `run_intelligence` enqueues, then resolves mutable meeting config and turns exceptions into `local` (`services/meeting_intel_service.py:63`, `:81`); the Chair receives that host only AFTER the POST (`ChairHome.tsx:614`, `:1716`). Execution uses the binder's frozen SERVICE route (`meeting_deferred_queue_binding.py:126`); the drainer's overwrite picks the first route leg, not the leg that ran (`intel_queue.py:425`, `deferred_bound.py:201`). Article III at the point of decision is not met (audits/runtime-astra.md fact 5; the inventory's Article III defect; 06-check-astra.md finding 3).

## Scope

- **In:** before Run, the same SERVICE route resolver (`inference_route_plan_service.py:242`) projects the route the run WILL use, INCLUDING every permitted fallback destination, and the face gets it (`planned_route` on the meeting/run read model: ordered legs with host, profile id and revision); execution binds to that disclosed selection (route selection and revisions, not a hostname) and refuses drift BEFORE provider dispatch, with a receipt; every destination actually contacted, including failed attempts, is persisted on the run and returned in the receipt; the receipt survives a restart; an unresolved route is `unavailable`, never `local`. The same contract feeds all three run entry points: Chair Run (`ChairHome.tsx:1716`), ledger Retry, record Retry (`MeetingIntelRecovery.tsx:88`, a different endpoint).
- **Out:** the chip components (04 passes the prop); the Concierge; group/global inheritance (forbidden by `inference_service_route_policy.py:93`).

## Acceptance criteria

- [ ] A meeting's run read model carries `planned_route` (ordered legs, each with host, profile, revision) computed by the SERVICE resolver before any POST, from every entry point.
- [ ] After a run, the receipt lists every destination contacted in order, failed attempts included; a forced fallback to a DISCLOSED leg shows that leg; a fallback to an undisclosed destination is impossible (fence).
- [ ] The receipt is readable after a hub restart on the same DB.
- [ ] With no resolvable route the read model says `unavailable`; the string `local` is impossible in that state (fence proven red pre-fix).
- [ ] A drift between planned and bound route refuses the run BEFORE provider dispatch, with a receipt (fence asserts no provider call).

## Test plan

- **Unit:** resolver projection; fallback host persistence; the unresolved-never-local fence.
- **Integration:** the drainer test with a stub engine; both hosts recorded.
- **Manual / device:** n/a (04 shots the face).

## The settled contract (Astra proposed, Muad'Dib checked, 2026-09-19)

Both lanes build against this and nothing else:

- Read models (meeting and run) expose `planned_route = {status, reason_code, selection_hash, legs}`. `status` is `ready | unavailable`; `unavailable` carries empty `legs`, a null hash and a `reason_code` in plain words. `legs` is ordered; each leg is `{ordinal, host, boundary, profile_id, profile_revision, deployment_revision_id}` (`boundary` is the egress class the badge shows: local, lan, cloud).
- `selection_hash` hashes the canonical selection material (assignment and policy revisions included; generated plan ids and timestamps excluded).
- Every run endpoint (Chair Run, ledger Run/Retry, record Retry) accepts `expected_selection_hash`; the server resolves and binds the selection and refuses drift BEFORE provider dispatch, with a receipt. The disclosed selection is persisted per job.
- `run_receipt = {receipt_id, job_id, meeting_id, selection_hash, outcome, attempts}`; `attempts` is ordered, each `{leg_ordinal, host, outcome, operation_id}`, failed dispatches included. It lives in the durable job record and the linked kernel receipts, survives restart, and is never reconstructed from current configuration.

Muad'Dib's check: accepted as written. One rule added for lane B: the face shows `legs[0].host` and, if more legs exist, `+ fallback <host>`; it never composes a host from config.

## Notes / open questions

Lane A (Astra to Luna). Serves exit criterion 3.
