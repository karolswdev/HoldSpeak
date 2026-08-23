# Story 08 · Phase C slice C1 checkpoint — counsel round 1 (Sol)

Recorded verbatim, 2026-08-23. Reviewed at `a581bc1e`. Verdict: **DO-NOT-RATIFY**.
The orchestrator's disposition follows the verdict at the end of this file.

---

# DO-NOT-RATIFY

The central C1 architecture is real: new claims use stored parent/bundle IDs, the bound path does not read `Config`, all three transcript fences plus the completion guard exist, typed provider refusals terminate, and pre-C1 claims retain their legacy executor. I am not reopening the ruled design.

I would not ratify C1 as complete because its failure and lineage transitions contain two owner-visible correctness blockers, and the bound displaced-work path is under-budgeted.

## 1. BLOCKER — A successful retry resurfaces the old failure and lies on glass

**Concrete scenario**

1. Attempt 1 fails transiently.
2. `retry_intel_job` leaves that job as `failed` and creates a linked queued successor.
3. Attempt 2 succeeds; C1 marks the successor `succeeded` and the Meeting `ready`.
4. Ordinary readers exclude the successful successor before determining the current lineage, so they rediscover attempt 1 as the Meeting's "current" failed job.
5. The recovery glass says incomplete/failed, the Desk emits failed attention, and the queue summary reports a failure despite the summary being ready.
6. If the owner presses Retry, `request_intel_retry` sees the stale failed ancestor and can queue another model run for an already-ready Meeting.

**Evidence**

- Old owner becomes `failed`; fresh successor is inserted as `queued`: `holdspeak/db/intel.py:719-773`
- Successful successor alone becomes `succeeded`, while the Meeting becomes `ready`: `holdspeak/db/intel.py:608-652`
- `get_intel_job` filters out `succeeded` before selection but retains the old `failed` row: `holdspeak/db/intel.py:832-853`
- `list_intel_jobs` and queue summary repeat the same active-only ranking error: `holdspeak/db/intel.py:855-953`
- Desk projections explicitly emit that stale failed row: `holdspeak/db/projections.py:484-523`
- Recovery glass gives the stale `job_state` precedence over the Meeting's `ready` state: `holdspeak/services/meeting_intel_service.py:47-59`
- Manual retry returns `ready` only when no "current" job exists, allowing the stale ancestor to reopen work: `holdspeak/db/intel.py:1104-1167`

This also exposes the gap in amendment 1's executable inventory: the CLI is expressly named by the amendment, but `tests/unit/test_phase143_intel_queue_inventory.py` never opens or asserts `holdspeak/commands/intel.py`. Its `--retry-failed` path consumes `list_intel_jobs(status="failed")` at lines 66-78 and can therefore act on historical failed ancestors.

**Required remediation**

Make "current job" lineage-aware everywhere:

- Determine the newest lineage member including terminal successors before deciding whether unresolved work exists.
- A successful/skipped terminal successor must suppress all failed ancestors from ordinary queue, recovery, Desk, HUD, and CLI readers.
- `--retry-failed` must address only the latest unresolved failed job per Meeting, never historical failures.
- Add a bound failure → linked retry → success proof asserting:
  - `get_intel_job()` returns no unresolved job;
  - queue summary has zero failed/active jobs;
  - Desk has no failed attention;
  - recovery reports ready/not visible;
  - manual retry refuses the already-ready Meeting.

## 2. BLOCKER — A route-binding refusal makes the worker spin forever while reporting false progress

**Concrete scenario**

An exact SERVICE assignment is missing, or route policy changes between prepare and claim:

1. The binder records a refusal but deliberately leaves the same job immediately `queued`.
2. `process_next_intel_job` catches the exception and returns `True`.
3. `drain_intel_queue` interprets `True` as progress and immediately selects the same due job again.
4. The background worker calls the unbounded drain with no `max_jobs`.

The result is an infinite CPU/SQLite loop, unbounded refusal-ledger growth, starvation of later jobs, and an HTTP process request that hangs or reports a positive processed count although zero jobs were claimed. The Meeting glass remains "queued" because only attempt history changed.

**Evidence**

- The real-binder test explicitly asserts refusal leaves the job queued: `tests/unit/test_phase143_intel_queue_inventory.py:391-411`
- Repository refusal handling appends an event without changing job status, due time, `last_error`, or Meeting status: `holdspeak/db/intel.py:394-413`
- Worker catches the binder error and returns `True`: `holdspeak/intel_queue.py:383-389`
- Drain loops until the call returns false; its default is unbounded: `holdspeak/intel_queue.py:790-815`
- Background worker invokes that unbounded drain: `holdspeak/intel_queue.py:990-1005`
- The service returns `success: True` with the resulting processed count: `holdspeak/services/meeting_intel_service.py:30-38`

**Required remediation**

A refused claim must make durable progress:

- A typed missing-assignment/policy refusal should terminalize the exact job with an honest visible error and zero child.
- A genuinely retryable infrastructure failure must receive durable bounded backoff, not remain immediately due.
- `process_next_intel_job` must not return progress when neither ownership nor lifecycle state advanced.
- Prove an unbounded drain terminates after one refusal, produces no duplicate unchanged refusal events, and continues to a later claimable job.

## 3. HIGH — The bound bookmark-label path underfunds its parent and fails lawful meetings

**Concrete scenario**

For displaced bookmark labels, the binder creates one route member and budgets the retry policy once, regardless of how many bookmarks it will execute. The worker then executes one child for every bookmark.

The current defaults give:

- deferred analysis: four physical attempts;
- bookmark label: four physical attempts;
- total parent budget: eight children.

A Meeting with eight labelable bookmarks needs at least nine children even when every provider call succeeds on its first attempt: one analysis plus eight labels. The eighth label therefore hits `parent_child_budget_exhausted`. C1 catches that kernel budget refusal as a generic provider refusal and terminally fails otherwise valid work.

There is no product bookmark-count bound.

**Evidence**

- Work descriptor includes only the displaced slug, not the frozen bookmark count or identities: `holdspeak/db/intel.py:40-58`
- Binder deduplicates to one bookmark capability route: `holdspeak/services/meeting_deferred_queue_binding.py:61-81`
- Binder adds the policy's maximum attempts once per route: `holdspeak/services/meeting_deferred_queue_binding.py:98-118`
- Text and structured policies each permit four physical attempts: `holdspeak/inference_capabilities.py:1166-1167`
- Bound worker dispatches once per bookmark: `holdspeak/intel_queue.py:162-191`
- Kernel refuses the next child once the persisted parent budget is exhausted: `holdspeak/kernel/parent_run.py:147-163`
- The preserved legacy path already knows the correct invariant — one budgeted child per displaced bookmark: `holdspeak/intel_queue.py:692-702` and `holdspeak/meeting_session/deferred_admission.py:83-95`

**Required remediation**

Freeze a content-free set or count of displaced bookmark operations before parent admission, and budget every frozen operation instance plus its governed retry allowance. Execute that frozen set rather than an unbounded mutable bookmark list loaded after claim.

Add bound-worker proofs with more bookmarks than one route policy's attempt count, including one physical retry, and show every intended label settles without budget exhaustion.

## 4. HIGH — Fresh successors become claimable before the old bound parent is terminal

The ruled design requires retries to create a new job only after old-parent terminality, and amendment 2 permits at most one execution owner.

**Concrete scenario**

1. Worker A detects transcript drift or a retryable failure.
2. The repository commits the old queue row as `superseded`/`failed` and inserts the fresh successor as immediately `queued`.
3. The old kernel parent remains `OPEN`; it closes only later in `finally`.
4. Worker B — background worker versus HTTP/CLI drain is enough — sees no claimed/running queue owner and binds the successor to a second parent.
5. If old-parent close throws, C1 logs and suppresses the exception, making the overlap persistent until orphan recovery.

**Evidence**

- Supersession inserts the fresh successor as immediately queued: `holdspeak/db/intel.py:519-590`
- Retry does the same: `holdspeak/db/intel.py:710-773`
- A new claim checks only queue-row statuses, not the old parent's terminal receipt: `holdspeak/db/intel.py:345-353`
- Old parent closes only after those repository calls return: `holdspeak/intel_queue.py:344-346`
- Parent-close failure is swallowed: `holdspeak/meeting_session/deferred_bound.py:173-183`
- Binding law: `assets/story-08-phase-c-deferred-design.md:32-33,90-92`

**Required remediation**

A successor must remain non-claimable until the old parent has a durable terminal receipt. Either compose parent terminality into the transition or use a recoverable two-step posture — fresh reserved successor, terminalize old parent, then promote fresh successor to queued.

Prove the boundary with competing connections, process loss between every step, and injected parent-close failure. No second parent may start while the prior parent remains open.

## 5. MEDIUM — Register the three C1 execution sites now, not in a later slice

The held census item belongs to C1. These are the new bound worker's actual model-dispatch closures, not Phase D speech work. Deferring them would knowingly ship three new doors outside the executable one-path classification.

The focused probe produced:

```text
UNREGISTERED_MODEL_EXECUTION holdspeak/intel_queue.py:180 _run_bound_displaced_work generate_bookmark_label_with_context
UNREGISTERED_MODEL_EXECUTION holdspeak/intel_queue.py:209 _run_bound_displaced_work generate_title
UNREGISTERED_MODEL_EXECUTION holdspeak/intel_queue.py:273 _process_bound_intel_job analyze
UNREGISTERED_MODEL_EXECUTION holdspeak/speech_session/provider.py:158 ProviderAdmission.dispatch_through bound_target
UNREGISTERED_MODEL_EXECUTION holdspeak/speech_session/provider.py:490 _RoutedSpeechAdapter.dispatch run_prompt
UNREGISTERED_MODEL_EXECUTION holdspeak/speech_session/provider.py:504 _RoutedSpeechAdapter.dispatch run_prompt
```

Probe result: `1 failed in 3.36s`.

The test itself says every execution site must be in exactly one literal bucket and that anything else is an unregistered execution: `tests/unit/test_one_path_census.py:13-34,670-682`.

Calling the failure "inherited" by test name masks changed failure content: the branch added three C1 entries to the output.

**Recommendation and required remediation**

Register the C1 three now under HS-143-08/C1. Prefer extracting one named `.call` dispatch closure per capability into `holdspeak/meeting_session/deferred_bound.py`. Then register those reviewed leaf scopes in `ADAPTER_ALLOWLIST` and update the exact meeting-entry assertion, rather than broadly allowlisting whole queue orchestration functions. Record the Phase-143 classification decision as the census contract requires.

The other three inherited speech-provider sites retain their already-named home: Story 08 Phase D, which is explicitly queued at `current-phase-status.md:164-165`.

## 6. LOW — The narrow physical-cancellation limitation remains valid; the successor race is separate

For one correctly fenced parent, C1c did not expand the recorded physical-cancellation blast radius:

- The durable bundle/controller fence commits before best-effort provider signalling: `holdspeak/services/inference_parent_route_bundle_service.py:887-913`
- Frozen-route admission requires the parent to remain `OPEN`, preventing later member admission after the fence: `holdspeak/services/inference_adoption_service.py:992-1009`
- Bound members execute serially rather than being fanned out.

Thus a failed physical signal still permits only the already-dispatched attempt to waste compute, with late publication fenced. No redesign or stronger physical cancellation is required.

However, finding 4 creates a separate parent outside that fence. I would not restate the broader system-level "only one bounded owner" claim until successor activation is ordered after old-parent terminality.

## Amendment disposition

- **Amendment 1:** not complete because lineage/current-reader semantics are wrong after retry success, and the required CLI inventory was omitted.
- **Amendment 2:** not complete because a successor can be claimed while the prior bound parent remains open.
- **Amendment 3:** implemented as ruled — claim, staging, publication, and completion fences are present.
- **Amendments 4 and 5:** legitimately deferred to C3, the Stop-handoff provider and unknown-settlement adopter.
- **Amendment 6:** legitimately coupled to C3's unknown-recovery ledger; presentation remains with Stories 12/13 as ruled.
- **Installed plugins:** correctly remain C2 work and are not a C1 objection.

## Human-compliance ruling

**No — not yet for a tired Tuesday.**

A first-attempt, unchanged-transcript success is strongly fenced and its summary bytes are trustworthy. But the lifecycle glass is not trustworthy after a retry: it can show a historical failure over a successful summary and can invite the owner to rerun already-completed work. Missing assignments can also produce silent non-progress while the UI continues to say queued.

## Verification performed

```text
tests/unit/test_meeting_deferred_admission.py
tests/unit/test_db.py::TestDeferredIntelQueue
tests/integration/test_presence_learning_aftercare_broadcasts.py

38 passed in 8.86s
```

The focused census probe failed as reproduced above. Review ended at `a581bc1e`; the working tree remained unchanged.

---

## Orchestrator disposition (Muad'Dib, 2026-08-23)

All six findings accepted without dissent. Findings 1–5 briefed to a fix round
as implementation defects against the ruled design (no design reopening);
finding 6 requires no action. Finding 5 reverses the orchestrator's earlier
"inherited" framing — the counsel is right that the branch changed the failure
CONTENT under an unchanged failure name; the three C1 sites register in this
round, and the three speech-provider sites keep their Phase D home. Checkpoint
round 2 follows the fix round and its full-suite sweep.

---

# Round 2 (Sol, same counsel session, reviewed at `88d9e52c`) — DO-NOT-RATIFY

Round-one disposition: findings 1 (lineage readers), 2 (refusal progress),
and 5 (census registration) PASS under the counsel's own probes; 3 (budget)
and 4 (live successor race) PASS with the two new findings below. The
legacy→V3 conversion seam is sound for conversion/restart, transcript drift,
immediate double Stop, and record_only; NOT sound for replay after
conversion/completion. Three remaining defects:

1. **BLOCKER — receipt→promotion crash gap.** Process loss after
   `close()` durably writes the old parent receipt but before
   `promote_successors_after_parent_terminal()` strands the
   reserved/awaiting_parent_terminal successor forever: pending-close
   recovery excludes receipted parents, ordinary claims scan only
   `queued`. Remediation: an idempotent recovery scan promoting every
   reserved successor whose predecessor already has a durable terminal
   receipt (before or composed into claim selection), proven with process
   loss exactly on that boundary (one promotion, one claim, zero
   duplicate parent/egress). Evidence: intel_queue.py:339-344, 366-382;
   deferred_bound.py:203-219; db/intel.py:341-353, 493-507.
2. **BLOCKER — replay after V3 supersedes finished work.** Repeated
   Stop/`recover_capture` after V3 conversion/completion resubmits the
   legacy plain-list descriptor, which hashes differently from the V3
   object → the successful leaf is superseded, the ready Meeting reopens,
   duplicate egress permitted. Remediation: one stable Meeting-handoff
   identity across legacy and V3 descendants (or legacy enqueue
   recognizing a current V3 descendant with same Meeting/transcript/
   slugs as the same handoff); replay returns the existing descendant.
   Proofs for bundle-backed AND record_only: double Stop after conversion
   pre-admission; repeated recover_capture after V3 claim; repeated
   Stop/recovery after V3 success — one lineage, ready preserved, zero
   duplicate egress. Evidence: db/meetings.py:692-728,763-790;
   intel_admission.py:446-455,495-520; db/intel.py:90-114,267-315.
3. **HIGH — frozen bookmark identity dropped at publication.**
   Publication updates by meeting_id+timestamp (timestamps not unique);
   duplicate-timestamp bookmarks collide and delete-and-replace retargets
   the replacement while the job reports ready. Remediation: carry
   `bookmark_id` through material and projection; publish
   `WHERE id=? AND meeting_id=? AND timestamp=?`; missing/changed row =
   truthful stale/skipped outcome. Proofs: same-timestamp independence;
   delete-and-replace cannot inherit the deleted operation's result.
   Evidence: intel_queue.py:167-188; kernel/meeting_plugin_projection.py:167-185;
   db/schema.py:87-93.

Tired-Tuesday: still no — a crash can leave a retry visibly queued but
permanently unclaimable; repeated recovery can reopen a completed summary;
duplicate-timestamp bookmarks can be mislabeled under a ready status.

## Orchestrator disposition (round 2)

All three findings accepted without dissent. One fix round briefed with the
counsel's remediations as acceptance criteria plus a same-class sweep duty
(other receipt→transition crash boundaries; other publication sites dropping
frozen identity fields) so the class closes, not just the instances. Round 3
follows the fix round and its full sweep.
