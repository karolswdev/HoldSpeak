# HS-S25 · Keep human review meaningful while work waits

**Detailed conditional proposal; implementation not authorized.** Epic: [HS-E20](../epics/HS-E20-program-contracts.md). Existing G-REVIEW is detailed here as **G25**, still pending. Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. No unwanted merge or provider-protection bypass was reproduced.

## Job and source finding

A technical owner can let a Program wait on CI or requirements without an earlier human approval silently overriding a later request for changes. They can see what the system most recently observed, what it could not check and whether a merge request is already outstanding. Existing GitHub receipts, Program lifecycle and control levels remain the owners.

The provider already returns `latestReviews`. The receipt service derives approvers and requested changes; the observer refreshes the launch PR. Program instead stops checking both after `facts.person_approved` becomes true. Its owner Merge path also trusts that boolean. The observer drops review-read quality/head/time when projecting a PR, while failed source reads retain old rows and failed direct polls retain the previous projection. Therefore removing the latch alone would still confuse retained evidence with a usable observation.

See [review evidence](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#human-review-appendix-recorded-approval-versus-current-review-state-1500-follow-up) and [V25](../VALIDATION.md#v25-current-person-review-verification). Source-inspected positive tests already cover approval held by an owner-word requirement and one feedback round. Preserve those, then add the missing composed sequence through the real receipt/observer producers.

## G25 local policy choices

**Branch A, detailed here:** a new person-gated step merge needs the latest applied, structurally complete, matching review observation, and the latest applied attempt must be usable. Historical approval remains history. **Branch B:** retain sticky historical eligibility despite later observations. B must explicitly accept that limitation and define feedback separately; it is not silently selected. A strict commit-bound policy is another gated alternative, not implemented by this branch.

Accept these choices before A is implemented:

1. **Observation meaning.** “Latest” means local observer application order, not provider request-start order or instant GitHub truth. Failed, malformed, stale-cache, target-missing or mismatched observations make new eligibility unverified. They do not revoke historical approval. No new polling cadence, TTL or live read on Merge is added.
2. **Head behavior.** The first branch follows the provider's reported latest review after a new complete observation of the changed PR head. Approval may remain reported across a head change. An observed PR head is not the commit a reviewer approved. Missing observed head identity or disagreement with the current stored step `head_commit`/target is unverified until reconciled; exact commit-bound approval, new review-on-every-commit rules and atomic head protection require a different contract.
3. **Person matching.** Reuse current effective step/Program person and `person_logins`; no alias/name matching redesign. Missing/unreadable person identities block without diagnosing the private store. Any matching requested-change entry blocks even if another matching alias is approved or feedback was already attempted. A valid empty review list means no approval in this observation, not dismissal.
4. **Legacy and history.** Retain `person_approved` and existing checkpoints as historical evidence only. Proposed `facts.person_review` carries bounded present-state/reason/evidence identity for presentation. Legacy true without qualifying observation is unverified, not a backfill of current approval. No history rewrite or schema migration.
5. **Dispatch.** Engine and owner use the same read-only gate at actual runner merge admission, rereading current Program/step/launch evidence and binding the person-gated command to the validated canonical PR URL. Existing authority, requirements, CI/check/review and control rules remain as applicable to each existing caller/path; owner and engine currently do not share one CI policy, and this slice does not create one. Within this person-gated GitHub branch, a visible durable `merge_requested_at` prevents another dispatch; it is an outstanding request, not a completed merge or cancellable Ask row.
6. **Explicit limits.** No new global lock or transactional dispatch marker is added. Simultaneous entries before a marker, command success before failed marker persistence, provider changes after local admission and cross-process races remain unsolved. If at-most-once dispatch or atomic current-review/head enforcement is required, stop this branch for that separate design.
7. **Feedback custody.** Matching changes block independently of prompting. Preserve current reviewer words, same branch/PR, timestamp-based round dedup and owner-taken lane. A prompt attempt, skipped send, exception or ambiguous return is not proven delivery. No automatic resend/retry engine, new review ID or exactly-once feedback claim follows.

The owner can select a different policy without accepting this implementation. No Program fix depends on a shell rewrite or S32's separate final-Program delivery contract.

## Narrow target design

### Existing receipts retain review evidence

Add only review-specific quality/provenance to the existing normalized PR row. Keep current `approved_by` and `changes_requested` summaries for compatibility. A well-formed empty `latestReviews` list is complete; absent/null/non-list input, malformed member/author, deleted/unknown author or unrecognized state is incomplete for this conservative branch. Do not drop malformed rows and then claim the person's approval disappeared. Aggregate `reviewDecision` is not approval by the chosen person. No provider review ID or reviewed commit is invented.

Proposed local read tokens identify a successful raw read, not provider chronology. A source sweep's qualifying row must belong to its live source-read envelope; the pair is a coherent cache snapshot, not proof that `refresh()` returned the exact result of its own invocation; a direct view/branch read carries its own successful-call identity. Cached data retained after failure or mixed into a different source envelope cannot become a fresh success. Use the existing receipt cache and fields, not a new freshness service. Exact proposed metadata names are settled in T25-01; V25 requires both source and direct paths to prove the association.

In the launch's existing `follow_through` JSON, preserve two separate facts: latest applied attempt quality/target and last successful matching review snapshot. Include existing launch/source/PR URL+number, observed head, local observed time and a per-launch application sequence/token that distinguishes same-second applications. Provider `submittedAt` stays separate. Application order does not establish which provider request began later. Neither an absent PR in a bounded list nor failed authentication is an explicit negative review.

Both sweep and direct poll write this small projection under their existing observer serialization. Failed direct polls must record uncertainty even when the old PR remains. A stale source row cannot replace the last successful review snapshot. Preserve unrelated follow-through fields, PR discovery, terminal receipts, closure/provenance and poll limits.

### Program owns effective eligibility

A proposed small runner-owned evaluator reads current evidence without provider calls or effects. It returns eligible/blocked reason and evidence identity. Require current step launch/source association, exact PR URL+number agreement, a complete matching observation, usable latest attempt and a currently resolvable person. The current Program/step/person is reread, not copied from an old UI or mutable local dictionary. No entire private alias roster is persisted into facts or logs.

Keep `person_approved` historical. The new bounded projection may describe approved, changes requested, not approved in observation, unverified/target unavailable, or merge requested; exact internal names are proposed. Admission recomputes from the ledger; a saved presentation fact is never its authority. Reconciliation must preserve unrelated facts and newly saved request markers when later CI/checkpoint/transition code writes a copied dictionary.

While a PR waits, reconcile review on every existing Program tick even after historical approval. Matching changes always hold the gate. Call the existing feedback path only for its permitted new round; its boolean return says whether a round was attempted, not whether merge is allowed. Already-handled changes remain blocking when corrected work returns to the same PR. Preserve current dedup's timestamp/`seen` limits; missing review IDs do not support an exactly-once-per-review guarantee.

At actual `ProgramRunner.merge`, reread and enforce this gate for person-gated GitHub steps, including direct calls that bypass the earlier `_pr` decision. Owner admission also rereads Program and step under its existing `_LOCK`; do not call `_pr` there because it can prompt, transition or merge. Use the validated canonical PR URL, not a number interpreted in mutable cwd. Non-person and local-merge paths remain unchanged. The normal runner lock and owner RLock are different; this is no new shared transaction.

Within person-gated GitHub admission, if a merge request marker is already durable, issue no second command or duplicate success checkpoint. Wait for the existing actual PR observation. Do not cancel, resurrect or claim revocation of that outstanding request after a new review arrives. A real merged/closed receipt remains authoritative about what happened, even if current review evidence is unavailable; never rewrite actual merge history to match desired policy. Command exit zero can mean queued/pending, not completed merge.

### Visible state stays truthful

Use current step wait/report/Your turn surfaces and existing Program change notifications. Withdraw a now-ineligible Merge prompt or return it to existing `pr_open`; do not add a state/kind that requires a new frontend framework. An unavailable review read must not say “review did not run,” automatically ask the person again, prepare a message, Send, or imply that Not yet can cancel a dispatched merge. An eligible-but-held step still shows its separate CI/requirements hold.

Announce meaningful eligibility/reason/target/feedback changes even when the step remains `pr_open`; the current fingerprint omits these facts. Do not announce every timestamp-only refresh. UI is an eventual projection through the existing tick/subscriber path, not an instant provider guarantee. Merge admission independently rechecks the latest local evidence before dispatch.

## Acceptance matrix

| ID | Required proof |
| --- | --- |
| C25-01 | Raw complete approval, valid empty, change request and malformed/missing/unknown-author review data stay distinct through real normalization; aggregate approval cannot substitute for the selected person |
| C25-02 | Source failure after success retains history but blocks eligibility; direct-poll failure records uncertainty; bounded-list omission is target-unavailable, not dismissal |
| C25-03 | Sweep/direct applications in both orders, same-second observations and mixed cache rows retain correct read association/application identity; stale rows cannot manufacture a new successful snapshot |
| C25-04 | Approval while CI/owner-word requirement holds, then a newer matching change, keeps merge blocked after the other hold clears; historical checkpoint remains |
| C25-05 | Repeated matching change remains blocking after dedup and after work returns to the same PR; another matching alias approval cannot override it; words/round count preserve current behavior |
| C25-06 | Prompt exception, owner-taken/missing launch and ambiguous return do not claim delivery or cause automatic resend; feedback attempts never determine merge eligibility |
| C25-07 | Fresh eligible observation restores eligibility only when all other gates applicable to that existing caller/path hold; accepted head policy is exercised without claiming reviewed-commit identity |
| C25-08 | Legacy true, missing/unreadable person, wrong launch/source/PR/head, incomplete observation and later unavailable attempt issue zero new merge commands |
| C25-09 | Owner presses Merge before the next Program tick: fresh local projection is checked, stale facts cannot authorize; direct runner/engine entry uses the same gate and validated PR URL |
| C25-10 | A durable outstanding person-gated GitHub request suppresses sequential repeats/reconstruction and duplicate checkpoints; no claim that simultaneous pre-marker or command-before-persistence windows are solved |
| C25-11 | Later facts saves preserve unrelated facts, reconciled evidence and current request marker; historical approval is not cleared or relabeled as revocation |
| C25-12 | Facts-only gate change reaches current wait/report/Your turn through existing Program frames; unavailable/unknown produces neither false ready-to-merge nor false review-never-ran/automatic Ask/Send |
| C25-13 | Actual merged/closed receipts, requirements, owner control, agent-review/non-person/local merge and final-Program delivery retain existing semantics |

Real temporary Git/SQLite and fake provider boundaries are different proof layers. At least one chain must use the real receipt service and observer; current `FakeGitHub.sweep` bypasses them. No live GitHub, branch-protection or installed CLI behavior is proved by that test. Preserve [I16/I18/I19/I21/I22/I24](../INVARIANTS.md).

## Ownership and order

Exactly five existing production files: `holdspeak/delivery/pr_receipts.py`, `holdspeak/delivery/follow_through.py`, `holdspeak/services/program_runner.py`, `holdspeak/services/program_service.py`, `holdspeak/services/brief_words.py`. The existing `docs/programs.md` person-review paragraph is the one scoped guide edit. No new module, table, scheduler, poller, HTTP/MCP route, frontend structure or S32 delivery rewrite. [V25](../VALIDATION.md#v25-current-person-review-verification) gives exact symbols, test budget and commands.

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T25-01 contract](../tasks/HS-T25-01-contract.md) → accepted G25-A → [HS-T25-02 observation projection](../tasks/HS-T25-02-review-observations.md) → [HS-T25-03 gate and words](../tasks/HS-T25-03-review-admission.md) → [HS-T25-04 independent proof](../tasks/HS-T25-04-verification.md).

Producer and consumer are one logical contract, not separately completed feature releases. Coordinate shared Program/rig edits with S21/S22/S32. Other independent stories need not wait for this slice.

## Rollback and stops

The metadata is additive, but old code can still treat retained historical `person_approved` as current permission. Before downgrading, unfinished affected person-gated steps must remain held under an explicitly assigned safe mechanism or be reconciled under accepted policy; do not simply run old admission over them. If no safe hold/compatibility mechanism is available in scope, stop rollback and request that bounded decision. Preserve accepted/in-flight requests and actual merged history. A code reversal cannot cancel/reverse a provider merge or erase review/feedback records.

Stop for unsettled G25, required stronger commit/TTL/dispatch guarantees, unsupported receipt shape/caller, failed safe rig setup, extra production ownership, external provider access, uncertain effect, or an implementation that needs new lock ordering. Read unavailable evidence conservatively; do not weaken other gates to make the tests green.
