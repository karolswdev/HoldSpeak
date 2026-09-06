# Acceptance scenarios and owner pilot

Status: specified, not executed. Requirements resolve in [SRS](SRS.md), execution semantics in [CONTRACTS](CONTRACTS.md), and user flows in [RECIPES](RECIPES.md). Scenario IDs in requirement rows provide forward traceability. The register below provides the reverse index and the observable result needed to pass.

`T` means automated behavior/contract verification, `L` a live runtime/model/provider/device demonstration, and `U` owner usability/outcome validation. A fixture can prove deterministic mechanics; it cannot substitute for L or U evidence. Gate-specific scenarios close only the requirements available at that gate.

## 1. Scenario register

| ID | Requirements | Given / action / required result | Proof |
|---|---|---|---|
| AC-01 | AA-ENV-001, AA-ENV-002 | Given two processes sharing a database and different disk/frontend versions, inspect diagnostics. Identify each instance, loaded revision or explicit unknown, database identity, and mismatch. No automatic termination and no secret/path leak in ordinary UI. | T,L |
| AC-02 | AA-ENV-003, AA-ENV-005 | On an unconfigured model path, capture a sentence, keep it, attempt refinement, open the precise setup surface, configure a compatible model, and retry. The original persists, the failed prerequisite is named, and one real invocation receipt identifies actual placement. | T,L,U |
| AC-03 | AA-ENV-004, AA-INT-003 | Inspect a connected GitHub scope, read-only Jira scope, invalid scope, and expired credential. Capabilities and observed data differ correctly from auth status; unsupported Jira write is unavailable before any attempt. | T,L |
| AC-04 | AA-CTX-001 | Capture and edit a Thought without AI, interrupt/reopen the browser, then finish. Original custody, latest accepted edit, Project link, and findability survive; no model invocation is required. | T,L,U |
| AC-05 | AA-CTX-002, AA-CTX-003, AA-CTX-005 | Ask from selected sources containing a current fact, dissent, an optional stale source, and a required deleted source. Required deletion refuses dependent work; repaired context freezes versions. Generated claims carry evidence or explicit inference/unknown labels and retain dissent. | T,L,U |
| AC-06 | AA-CTX-004, AA-CTX-006 | Close/reopen a kept answer and search for an earlier decision by its subject. Recover instruction, source manifest, receipt, rationale, related commitments, and current superseding decision. | T,L,U |
| AC-07 | AA-DEC-001, AA-DEC-002, AA-NFR-002 | Process a 30-minute linked meeting with explicit decisions, ambiguous actions, and missing owners/dates. Show dispatch/progress within the target, measure actual completion, retain uncertainty, and extract source-linked proposals. Replay the same trigger without duplicate accepted items. | T,L,U |
| AC-08 | AA-DEC-003, AA-DEC-004 | Confirm one proposal, edit another, dismiss a third, then submit a stale edit. Canonical records and receipts reflect each gesture exactly once; metadata includes rationale/alternatives/authority context where known; stale edit makes no partial change. | T,L,U |
| AC-09 | AA-DEC-005 | Supersede an accepted decision and complete/reopen a linked action through its owning service. Room, search, and attention reflect current truth while retaining history; local acceptance does not fabricate organizational approval. | T,L |
| AC-10 | AA-DEC-006, AA-INT-005 | Prepare a 1:1 from authorized shared records with an ambiguous namesake and a protected private note present. No identity guess or private disclosure enters output, search, notification, or an impermissible model route. | T,L,U |
| AC-11 | AA-ATT-001, AA-ATT-002, AA-ATT-003 | Seed 100 ordinary observations, seven material needs, an overdue decision, and a failed run. Show five ranked priorities plus the true remainder; reach every item. Explain ranking. Snooze/dismiss affects presentation only; advancing source state surfaces the updated need. | T,L,U |
| AC-12 | AA-ATT-004, AA-ATT-006 | With no calendar connector, prepare a Project meeting brief from a purpose. Include decisions due, changes, commitments, coverage, and questions. Unreachable/stale sources cannot become “nothing changed”; observed and generated times remain distinct. | T,L,U |
| AC-13 | AA-TRF-001, AA-TRF-002 | Link a Project outcome, scope, known decision authority, dissent, and an unknown source authority. Keep the Project ID and existing records; distinguish observation, inference, decision, execution, and measure without converting missing facts into accepted state. | T,L,U |
| AC-14 | AA-RUN-001, AA-RUN-002 | Prepare equivalent manual and simulated-trigger intents against the same template. Resolve the same work contract, with trigger/authority provenance separately represented. Revise scope during execution; old work retains its original revision and receives explicit disposition. | T |
| AC-15 | AA-RUN-003, AA-RUN-004, AA-RUN-010, AA-INT-006 | Launch through a known adapter and then request an unsupported hard spend/tool-control guarantee. Successful work has parent/child authority receipts; unsupported scope refuses or remains explicitly supported/manual. Malicious source text and forged principal/target fields cannot expand rights. | T,L |
| AC-16 | AA-RUN-005, AA-RUN-006 | A worker returns “done” with one failing required test and a missing artifact. The assignment cannot be accepted. A corrected manifest supplies actual verification; acceptance retains its reviewer, criteria, sources, and receipts. | T,L,U |
| AC-17 | AA-RUN-007, AA-RUN-008, AA-UX-004 | During a real assignment, answer a blocker, disconnect/reconnect the browser, inspect output, and cancel a second run. Recover the same run and actual usage/placement; unavailable values remain unknown. Stale blocker answer and late result cannot alter new work. | T,L,U |
| AC-18 | AA-ATT-005, AA-AUT-001, AA-AUT-003 | Configure a time-zoned recipe, test a repeated/nonexistent local time, sleep/missed occurrence, overlap, quiet hours, and disabled delivery. Produce the documented occurrence/coalescing behavior, honest last/next state, and no notification storm. | T,L |
| AC-19 | AA-AUT-002, AA-AUT-007, AA-NFR-003 | Race two ticks/processes and replay a command; change the payload under the same command identity. One logical fire and terminal winner remain; changed payload conflicts. Kill between persistence/publication points and verify durable state precedes visible completion. | T,L |
| AC-20 | AA-AUT-004, AA-AUT-005, AA-AUT-006, AA-NFR-006 | Inject the failure windows below. Recover or explicitly mark uncertainty within two configured intervals, bound retries, fence late results, and continue an unrelated Project. An external effect with unknown outcome is never blindly repeated. | T,L |
| AC-21 | AA-RUN-009, AA-AUT-008, AA-NFR-005 | Exhaust model/child/deadline budgets, attempt a third child and depth-two delegation, and try an unconfigured effect. Limits refuse new dispatch; worker and verifier share accounting. Unknown external billing never appears enforceable. Prove preparation/analysis before broader automatic effects. | T,L |
| AC-22 | AA-TRF-003, AA-TRF-004 | Advance an initiative with actual gate evidence and attempt the same transition with only a new document. The latter remains unadvanced. Inspect rollout population, enablement, capacity, waves, migration/deprecation, and revision/rollback obligations. | T,L,U |
| AC-23 | AA-TRF-005, AA-TRF-006 | Expire an exception and compute adoption with complete, incomplete, revised, and zero populations. Review names the exact authority/control/scope; ratios expose denominator and coverage, zero is not-applicable, and PR counts are not labeled adoption. | T,L,U |
| AC-24 | AA-TRF-007, AA-TRF-008, AA-INT-004 | Review two Projects with a shared dependency and conflicting accepted records. Prepare a reconciliation against an external revision, then change it before publication. Show the conflict; never overwrite silently. Replay a completed publication and recover its original receipt/destination. | T,L,U |
| AC-25 | AA-INT-001, AA-INT-002 | Perform supported assignment preparation/read/run through Web and tool adapters; compare validation and domain results. A missing live reply adapter is discovered as unavailable. Project/provider tools outside a Thread palette cannot be claimed or invoked by that mode. | T,L |
| AC-26 | AA-UX-001, AA-UX-002, AA-UX-003, AA-UX-005 | Complete R1 workflows at 1440px and 393px with keyboard, then voice where capture is available. Primary actions, focus, state changes, source disclosure, and recovery work inside the Desk; no horizontal content loss or log-reading requirement. | T,L,U |
| AC-27 | AA-NFR-001 | On attested hardware with 500 linked records, measure 20 cold/warm visits as separate sets. Local action feedback p95 is at most 500 ms and useful cached content p95 at most two seconds; record dataset, instrumentation, frontend build, and cache conditions. | T,L |
| AC-28 | AA-NFR-004, AA-NFR-008 | Delete/revoke a source used in prior work; verify snapshots, previews, search and exports no longer disclose it. Retain permitted tombstones only. Migrate/restore a database copy, compare citizen IDs, and disable recipes without deleting prior work. | T,L |
| AC-29 | AA-NFR-007 | Execute the ten-workday pilot below. Local measurement includes every relevant failure and all overhead. Report target results as pass/fail/inconclusive and retain the owner verdict; no external telemetry or synthetic usage passes. | U |
| AC-30 | AA-IVW-001, AA-IVW-005, AA-IVW-018 | Enter each section from the Desk and relevant scoped record. In a live interview choose one goal/Project, skip an optional question, switch sections, and finish one useful manual result without completing a global profile. Known answers persist, adaptive questions address the current uncertainty, and direct controls remain reachable. | T,L,U |
| AC-31 | AA-IVW-002, AA-IVW-003, AA-IVW-017 | Revisit a section, change a goal/preference, correct an inferred fact, dismiss a suggestion, and modify the target through direct controls in another session. Resolve ambiguous names and rebase against actual revisions. Update the intended record once, retain provenance, invalidate dependent plans, and avoid unwanted repeated suggestions. Remove optional context and inspect all derived retrieval paths. | T,L,U |
| AC-32 | AA-IVW-004 | Replay recorded answers, model proposals, catalog versions, and tool observations through the versioned reducer; inject malformed output, an illegal transition, duplicate delivery, model timeout, and loop-budget exhaustion. State is reproducible, no effect is repeated, accepted input survives, and the next repair is explicit. Fresh model wording is not part of the deterministic assertion. | T |
| AC-33 | AA-IVW-006, AA-IVW-014 | Evaluate bottlenecked decisions, excessive notifications, and an empty decision log with missing sources. Suggestions connect to supplied goals/evidence, preserve uncertainty, show at most three initially, and distinguish executable candidates from unsupported ideas. Include a novel composition and a useful manual option. No invented tool, authority, savings, or successful setup; owner judges relevance separately. | T,L,U |
| AC-34 | AA-IVW-007, AA-IVW-008, AA-IVW-015 | Build a section palette, then remove a live adapter, alter a descriptor/catalog revision, inject misleading tool annotations/source instructions, and attempt an owner-only operation from a restricted principal. Validate schema and domain preconditions; refuse unavailable/escalated work. Prove setup-proposal selection/testing parity through the correct service, and add a fixture section without a second controller. | T,L |
| AC-35 | AA-IVW-009, AA-IVW-010, AA-IVW-016 | Compare exploratory interest with an exact Configure instruction; alter the target revision before apply and omit a material time/scope field. Resolve only necessary gaps under actual policy. After apply, inspect source/model result and owning records. A model saying done, a lost acknowledgement, or a saved disabled schedule cannot pass as active verified behavior. No redundant confirmation for sufficient existing intent. | T,L,U |
| AC-36 | AA-IVW-011, AA-IVW-018 | Interrupt before commit, after effect/before receipt, and between independently committed service steps. Expire a Project setup session, close/reopen the browser, and abandon the interview after one configuration succeeds. Resume by reconciliation with no duplicate effect, expose partial/indeterminate state, revalidate expired proposals, and show the actual controls for configuration that remains active. | T,L |
| AC-37 | AA-IVW-012 | Enter People and cross-section suggestions with permitted shared-intent and protected fixture material. Inspect capture, transcript storage, prompts, generated rationale, continuation, search, logs, and model destination. Protected content never enters the ordinary plane; a permitted handoff retains only allowed continuation metadata and does not infer personal traits or authority. | T,L |
| AC-38 | AA-IVW-013 | Start with no runnable model, an expired connector credential, and a native-permission dependency. Capture intent and choose a section, use the specific existing setup/handoff surface, and return. No chat credential collection or input loss; a real compatible probe/source result determines readiness. | T,L,U |

For AC-27, p95 uses the nearest-rank observation in each 20-visit set; warm cached rendering is the SRS latency gate, and cold fetch/model latency is separately reported. For AC-07, continuing progress must identify a real admitted job and current observed stage; a decorative spinner is insufficient evidence. Completion latency is measured even when it exceeds the initial observation target.

## 2. Failure-injection matrix

| Injection point | Expected invariant | Observable evidence |
|---|---|---|
| Before operation commit | No physical dispatch | No adapter call; replay can admit once. |
| After admission, before claim | Same durable operation recovered | Matching definition/revision and operation identity. |
| After claim, before worker acknowledgement | No unfenced replacement | Lease generation, reconciliation result, bounded unknown state. |
| After external effect, before receipt | No blind repeat | Read-back match or indeterminate receipt; physical effect count verified. |
| After candidate persistence, before UI event | Durable candidate recoverable | Reload/cursor replay resolves one result. |
| During verification | Unverified work not accepted | Unknown/failed checks retained, bounded retry if appropriate. |
| After cancellation, before late output | Old generation cannot publish/accept | Receipt of late attempt retained as allowed; no new accepted result. |
| During source revocation | No retained unauthorized disclosure | All supported retrieval/export paths refuse or show tombstone. |
| Provider outage | Honest partial coverage | Independent Project still evaluated; finite retry/circuit state. |
| Notification service unavailable | Work state survives delivery failure | Results available on Desk; delivery unavailable is visible. |
| Two scheduler instances | One logical fire | Unique fire key and one winning generation. |
| Hub asleep across due time | No false continuous monitoring | Missed/coalesced/skipped occurrence and actual observation time. |
| Interview target/catalog changes after plan preparation | No stale effect | Revision refusal, preserved intent, and a revised proposed change. |
| Interview interruption after one service commits | No assumed global rollback or duplicated setup | Per-step receipts, read-back, and an honest remaining-work/active-configuration view. |
| Protected interview input at a storage boundary | No disclosure before later filtering | Capture/prompt/storage inspection across permitted and ordinary planes. |

A cancellation test cannot pass solely because the UI says cancelled. Verify process termination where supported, effect/receipt state, and refusal of new dispatch. When the adapter cannot establish termination, indeterminate is the correct state.

## 3. Pilot protocol

Before day one, select one real transformation stream, actual sources, and the owner-approved model destinations. Record baseline effort from comparable recent tasks or a short prospective control period. Define each task and success criterion before using HoldSpeak on it. If the baseline is retrospective, label its uncertainty.

Run ten workdays. The sample includes five relevant meetings, ten decision-recall tasks, five bounded agent assignments, and two weekly updates. One person may perform all roles of product operator and result reviewer, but organizational decision authority must be recorded separately. A day without a relevant meeting does not justify inventing one; extend the sample period when necessary and mark the initial result inconclusive.

Include five naturally relevant interview sessions: one first setup, at least three revisits, and one further section chosen by the owner. Record model/configuration, capability coverage, questions asked, skipped/repeated questions, suggestion dispositions, setup changes, verification, and active human time. Fixtures establish mechanics; they do not count as useful owner sessions. Insufficient real opportunities make this part inconclusive.

| Measure | Definition | Initial target |
|---|---|---|
| Preparation time | From starting the task to an owner-usable reviewed brief, including source selection, correction, and setup incurred for that task | Under five minutes per sampled brief. |
| Extraction recall | Correct source-supported extracted decisions/actions divided by decisions/actions in the owner's independently marked meeting ground truth | At least 90% across the five meetings. |
| Extraction precision | Correct source-supported extracted decisions/actions divided by all proposed decisions/actions | At least 90%; invented acceptance, owner, or deadline is a critical defect regardless of aggregate score. |
| Decision recall | Correctly recover current decision, rationale, and source under one minute | At least eight of ten tasks. |
| Delegated result quality | Assignment with required artifact and verifiable mandatory checks, plus recorded reviewer outcome | Five assignments reach a reviewable result; report accepted, corrected, failed, and inconclusive separately. |
| Adoption of HoldSpeak | Workdays with an intentional recipe used for actual work; spontaneous returns recorded separately | At least eight of ten workdays; observed use is evidence, not an obligation to manufacture activity. |
| Net time recovered | Comparable baseline minutes minus capture/setup, preparation, correction, review, supervision, repair, and maintenance minutes | At least 120 net minutes per five-workday week. |
| Attention relevance | Priorities judged actionable/relevant divided by all opening priorities shown; dismissals and missed material needs recorded | Establish baseline at midpoint; no material need lost solely by top-five truncation. |
| Outcome quality | Owner assessment of whether evidence improved a decision or prevented lost follow-through, with an example | At least two concrete examples across the pilot; qualitative, not a fabricated score. |
| Interview first value | Start to an owner-usable first result, including questions, setup work, and review; record external download/auth waits separately and report total elapsed time | Under ten active minutes when the necessary model/source prerequisites are ready; an initial target, not an observed result. |
| Interview revisit | Active time to change the intended existing configuration and verify the change, with prerequisites ready | Under three minutes in at least three revisits; zero duplicate effects or unintended activations. |
| Suggestion usefulness | Session in which the owner identifies at least one relevant actionable suggestion and chooses to try, configure, or keep it for actual work, divided by all five sessions | At least three of five; retaining an unsupported idea is reported separately and does not prove an executable suggestion. |

Do not double-count savings: each sampled task has one baseline and one total assisted cost. Shared setup/maintenance time is allocated once across the week, not omitted or counted against several tasks. Include failed runs and abandonments in the denominator. Report wall-clock latency separately from active human minutes. One avoided hypothetical incident is not converted into invented financial savings.

Day five: review raw results, identify the largest three sources of lost time or incorrect output, and repair only those that block the chosen recipes. Record changed configuration/model/build and split comparisons where the change affects validity. Do not remove early failed runs from the final sample.

Day ten: review per-recipe quality, net time, spontaneous use, and continued maintenance burden. A measured pass advances the relevant release gate. Insufficient sample is inconclusive. A failed workflow narrows or reshapes the next packet. R3 is assessed separately with three consecutive scheduled occurrences and failure injection; ten days of manual use cannot prove unattended reliability.

## 4. Evidence record

Store evidence through existing repository/UAT conventions. Minimum fields:

```json
{
  "scenario_id": "AC-16",
  "requirements": ["AA-RUN-005", "AA-RUN-006"],
  "result": "not_run",
  "backend_revision": null,
  "frontend_revision": null,
  "runtime_instance_id": null,
  "database_identity": null,
  "observed_at": null,
  "proof_kinds": ["T", "L", "U"],
  "inputs": [],
  "operation_and_receipt_refs": [],
  "artifacts": [],
  "measurements": {},
  "remaining_gaps": [],
  "owner_verdict": null
}
```

Nulls in this example mean evidence has not been collected. A completed evidence record requires actual values for the applicable proof, exact commands/results for T, runtime/provider/device facts for L, and the recorded owner judgment for U. Redact credentials and private content; use permitted local source locators instead of copying confidential text into a shareable repository.

Evidence status vocabulary: not_run, pass, fail, partial, blocked, inconclusive. A partially completed scenario cannot close all its requirements. The 99 baseline tests are existing implementation evidence only; none of the new AC scenarios is marked passed by authoring this specification.
