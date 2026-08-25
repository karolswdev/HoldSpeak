# Story 08 / Phase C — deferred queue and installed plugins

**Status:** design for counsel review; implementation has not started.

## Decision boundary

- Use the existing capability registry, route-plan service, parent/bundle service, adoption service, and fallback controller. No second planner, controller, registry, or gateway.
- Phase B deliberately fences the live bundle then retains Meeting-keyed legacy enqueue (`meeting_session/intel_admission.py:466-567`). Replace it only after this atomic replacement is proven.
- Plans, manifests, parent input, receipts, and queue ledger carry IDs, hashes, dispositions, and references only; never prompt or transcript bytes.

## A. Queue job → parent/bundle binding

### Capability and authority

- A normal job declares exactly `meeting.deferred_analysis@1`, plus `meeting.bookmark_label@2` / `meeting.auto_title@2` only for displaced slugs (`inference_capabilities.py:1061-1063`).
- It declares one bundle member for each planned installed plugin: `meeting.plugin.<id>@1`, with frozen ID and exact `plugin_definition_revision` (`inference_capabilities.py:1091-1154`).
- The SERVICE queue principal remains `meeting-intel-queue`; its sealed policy permits exact capability assignments only, never group/global inheritance (`inference_service_route_policy.py:1-8,148-185`). Missing assignment is a visible refusal and zero child.

### Minimal persistence

- Evolve **existing** `intel_jobs`: durable `job_id`, lineage/origin reference, immutable work-descriptor hash, claim ID, parent operation ID, bundle ID/SHA, and lifecycle posture. Evolve **existing** `intel_job_attempts` into append-only job/ledger events keyed by `job_id`.
- This is unavoidable but adds no table. `intel_jobs.meeting_id` is currently the primary key (`db/schema.py:132-141`) and the enqueue upsert overwrites it (`db/intel.py:62-77`); a forever-reserved handoff and fresh unknown-recovery job must coexist for one Meeting.
- Preserve ordinary queue readers by returning the newest claimable/active job. Keep historical rows readable; current attempt history has only meeting, ordinal, outcome, error, retry time, and timestamp (`db/schema.py:143-152`).

### Atomic claim

1. `BEGIN IMMEDIATE`; select one exact `queued` `job_id`; verify its transcript hash against the durable Meeting source. Mismatch terminalizes this job without egress and schedules a new job; it never retargets the claim.
2. Derive deterministic claim/parent/bundle command IDs from `job_id`, not Config or an ordinal alone. On **the same connection**, freeze SERVICE routes and start one `meeting.deferred-intel-job` parent plus bundle. Extract an in-transaction form from `InferenceParentRouteBundleService.start()`, which currently owns its own transaction (`inference_parent_route_bundle_service.py:242-415`).
3. Persist job→parent/bundle references and append a claim event in that transaction. Refusal rolls back all three. A commit has exactly one parent and complete member set; members cross-bind route and principal-policy hashes (`inference_parent_route_bundle_service.py:309-412`).
4. After commit, load only stored parent/bundle/member IDs. Stage late private material and execute through `admit_on_frozen_route`, which already atomically stages, freezes operation material, and starts execution (`inference_adoption_service.py:954-1007`). Extend its authority check for this sealed SERVICE principal by verified bundle membership, never by manufacturing OWNER authority.

- Crash recovery scans claimed/running jobs, reconstructs their stored bundle, and resumes exact route IDs. It never calls `Config.load`, cloud/profile resolution, host discovery, or a route resolver; those mutable reads currently precede claim (`intel_queue.py:148-204`).
- Scheduling backoff or manual retry creates a **new `job_id`**, parent, and bundle after old-parent terminality, linked in the ledger. It is not controller retry. The legacy retry mutates one row (`db/intel.py:165-205`); controller retries remain physical children of one frozen execution.

## B. Stop-handoff adoption

- Compose `HandoffEvidenceProvider("meeting-deferred-queue", 1, ...)`. The primitive requires conn-only `freeze`, read-only `reconstruct`, and `activate`; dispatch happens only after commit (`inference_parent_route_bundle_service.py:73-123`).
- `freeze(conn, ...)` inserts a reserved queue job containing only Meeting/job references, transcript hash, displaced slugs, and immutable descriptor hash. No runnable claim, network call, or worker action occurs.
- `reconstruct` derives `reserved|active` from the reservation plus a unique append-only activation event in queue-owned `intel_job_attempts`, never from handoff settlements. `activate(conn, evidence_ref)` appends that marker. This no-new-table witness mirrors the proof provider's immutable reservation, activation, and run records (`test_phase143_meeting_route_primitives.py:499-589`).
- Switch live Stop from `enqueue_intel_job` to `request_stop_handoff` only with this provider and reader. The spine server-derives/fences active work, freezes evidence in its transaction, and records the handoff (`inference_parent_route_bundle_service.py:744-925`).
- Known-safe settlement appends the marker atomically; the spine verifies reserved before and active after (`inference_parent_route_bundle_service.py:1083-1126`).
- Unknown terminal dispositions stay reserved. Reconciliation explicitly returns pending for dispatch/physical/effect unknown (`inference_parent_route_bundle_service.py:954-1008`); no sweeper, restart scan, backoff, or manual retry may activate that row.
- Unknown handoff recovery writes an owner-visible ledger line and auto-creates a linked **fresh local-boundary admission**: new job, parent, bundle, and both receipts. It never activates/claims the old reservation. Cross-boundary fresh use remains lawful only when normal exact assignment proves saved consent; otherwise visible refusal, zero child, no prompt.
- The old-reservation activation path is therefore intentionally narrow: known-safe Stop settlement only. Unknown recovery normally fresh-admits; retaining the marker is the smallest lawful A4 shape, not a second recovery system.

## C. Installed plugins

- Remove runtime-string planning. Deferred admission currently turns arbitrary `plugin_id` into a capability and calls legacy `run_admitted_capability` (`meeting_session/deferred_admission.py:332-413`); that dies for new jobs.
- Claim planning reads installed definitions from the composed registry and freezes each exact ID/revision/schema in the bundle and descriptor. Registry validation rejects non-exact `meeting.plugin.<id>` IDs and missing/bad revisions (`inference_capabilities.py:455-469`).
- Before a plugin child, require descriptor member, frozen capability, installed host ID/version, and bundle member all match. Unknown ID/revision drift writes refused/partial ledger truth and creates **no model child**.
- Preserve non-model gates first: persisted-key dedup removes completed work (`meeting_plugins.py:175-222`); fault injection records/removes a plugin before execution (`meeting_plugins.py:224-253`); skipped work is resolved (`meeting_plugins.py:37-42`). Deduped, skipped, and fault-injected work creates no child.
- Child semantic result is the plugin's exact inner `output`, not `PluginRunResult`. The semantic adapter normalizes the mapping and validates the closed capability result before election (`inference_semantic_adapters.py:104-119,204-207,219-253`). Projection separately records frozen plugin ID/revision, status, timing, and artifacts.
- Retain routing, idempotency keys, run/artifact readers, and synthesis. Remove only legacy host-list planning (`intel_queue.py:411-436`), Config-derived profile path (`intel_queue.py:148-159,305-311`), arbitrary capability construction, and direct child/fallback execution on new deferred work.

## D. What dies; what stays

- New work stops `DeferredIntelJob.admit`'s fresh `freeze_meeting_intel_plan` and direct parent start (`meeting_session/deferred_admission.py:139-219`).
- New work stops queue Config/runtime preflight, `_admit_deferred_job`, retry-in-place, and direct `admission.analyze/plugin` calls (`intel_queue.py:133-214,230-311,496-534`).
- Keep legacy Meeting-keyed upsert, `MeetingIntelPlan`, legacy adapters, DTO/history readers, and old rows readable until Phase F. Never rewrite historical bytes.

## E. Three implementation slices

1. **Bound claim, analysis, label/title.** Evolve the two queue tables; add in-connection bundle start and SERVICE frozen-route admission; shadow legacy row until atomic claim commits, then cut over. Tests: `test_meeting_deferred_admission.py`, `test_phase143_meeting_route_primitives.py`, `test_phase143_inference_route_plans.py`, `test_phase143_inference_fallback_controller.py`. Prove rollback yields no parent/bundle, assignment edits cannot retarget, and restart adopts exact IDs with zero duplicate egress.
2. **Revision-bound plugins.** Freeze installed membership; use inner-result adapters; preserve dedup/skipped/fault gates. Tests: `test_meeting_plugins.py`, `test_plugin_host_idempotency.py`, `test_plugin_disable.py`, `test_meeting_deferred_admission.py`, and registry tests. Prove unknown ID/revision drift/refusal and each non-executed status mints zero child.
3. **Stop provider and unknown recovery.** Add provider, atomic Stop cutover, activation-marker reader, owner ledger. Tests: `test_phase143_meeting_route_primitives.py`, `test_meeting_kill_recovery.py`, `test_meeting_deferred_admission.py`. Fault-inject reserve/settle/activate/claim; use fresh services and competing connections to prove one egress across restart, manual retry, and Stop handoff. Keep legacy aftercare until the proof passes, so summaries continue at every boundary.

## Open questions for counsel

1. Ratify evolving `intel_jobs`/`intel_job_attempts`, with immutability and unique-index triggers, as the independent reservation/activation witness.
2. Ratify local-first fresh-admission as a narrow mode of existing queue service policy, with saved-consent cross-boundary use only and no synthesized profile.
3. Confirm transcript mutation after claim: terminalize-and-reschedule (proposed) versus a separate immutable Meeting-source reference.
4. Confirm whether known-safe activation runs the reserved job directly or converts it into a normal claimed job while retaining evidence reference.

---

# Counsel ruling (Sol, 2026-08-22): RATIFY-WITH-AMENDMENTS

The six amendments below are the counsel's exact required text and are
binding over any conflicting statement above. Open-question answers:
(1) evolve intel_jobs/intel_job_attempts YES under amendment 1;
(2) local-first fresh admission YES under amendment 5;
(3) transcript mutation = terminalize-and-reschedule with hash fences at
claim AND staging AND publication (amendment 3);
(4) known-safe activation CONVERTS into the normal claim path (amendment 4).

## Counsel amendments — Phase C checkpoint

1. **Live-table evolution and complete reader/writer inventory.** Before changing `intel_jobs.meeting_id` from the primary key to a non-unique foreign key, produce an executable inventory of every reader and writer: the queue repository, worker, service layer, CLI, Meeting HTTP queue/recovery routes, Desk projections, import/session/recovery writers, DTOs, and the separate plugin-job service, MCP, HTTP, and projection surfaces. For each operation, define selection and mutation semantics when reserved, queued, claimed, running, failed, superseded, terminal, and historical jobs coexist for one Meeting. Migrate existing rows transactionally to deterministic `job_id` values; preserve attempt history and historical bytes; add the indexes, uniqueness constraints, and immutability enforcement required by those semantics. The migration is not complete until old-row reads, new-row reads, rollback, restart, and plugin-queue coexistence are proven.

2. **No dual execution during cutover.** One immutable work descriptor has at most one execution owner. A shadow legacy row and a new job may coexist as data, but they may never both be runnable. An already-running legacy claim blocks a new claim. The transaction that grants a new claim makes every legacy shadow for that descriptor non-claimable before commit. No worker may execute from a shadow row, and no recovery or retry may turn a running owner back into queued work. Prove this invariant with competing connections, process loss at every transition, restart, manual retry, and Stop handoff.

3. **Transcript mutation fences publication as well as claim.** Verify the durable transcript hash at claim, again immediately before private transcript bytes are staged for model execution, and again inside the projection-publication transaction. A mismatch terminalizes the old job as `superseded`, retains its parent/bundle and receipt history, and schedules a linked fresh `job_id`; it never retargets the old claim. A stale result may remain historical evidence but may not overwrite current Meeting intelligence, title, labels, or plugin artifacts.

4. **Known-safe activation enters the normal claim path.** `activate(conn, evidence_ref)` appends the unique activation event, preserves the Stop-handoff evidence reference, and converts the reserved job into the ordinary queued/claimable lifecycle in the same transaction. The standard queue claim transaction alone grants execution ownership and starts the parent/bundle. There is no separate direct executor for reserved jobs and no special claim path that bypasses the normal claim invariants.

5. **Unknown settlement uses fresh local-first admission without synthesized authority.** An old reservation whose dispatch, physical, or effect outcome is unknown remains reserved forever and can never be activated, claimed, retried, or swept. Recovery creates a linked fresh job under the normal `meeting-intel-queue` SERVICE policy. Same-device automatic re-admission uses an exact lawful assignment and needs no additional confirmation. Cross-boundary execution is allowed only through the exact saved assignment and consent already carried by that policy. Missing assignment, revision drift, or absent saved cross-boundary consent produces a visible refusal, one receipt, zero child, and no prompt. No recovery path may synthesize a profile, deployment, principal, or OWNER authority.

6. **Ledger now; surface later.** In Phase C, "owner-visible ledger line" means a durable append-only queue event or receipt recording the unknown old outcome, the fresh linked job, placement boundary, and eventual result. Phase C adds no new Desk room, queue view, card, modal, or other UI surface. Stories 12/13 own presentation of these existing ledger records.
