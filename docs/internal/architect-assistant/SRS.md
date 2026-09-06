# System requirements

Document ID: SRS-AA. Status: proposed, version 0.2. Scope and precedence are defined in [README](README.md). All requirement rows are mandatory for their named release gate. Acceptance scenario IDs resolve in [ACCEPTANCE](ACCEPTANCE.md). Data and execution semantics resolve in [CONTRACTS](CONTRACTS.md).

## 1. Outcomes and boundaries

The system shall reduce preparation, context reconstruction, missed follow-through, and agent supervision effort for an architect working through organizational change. It shall preserve a traceable connection between evidence, decisions, commitments, delegated results, and adoption outcomes.

A repeatable, modular interview is the primary conversational entry to discovering needs, generating useful suggestions, and configuring supported outcomes. Goals, Projects, concerns, Cadences, People, Decisions, and delegation can be revisited independently. The LLM explores and proposes; deterministic application logic governs state, capability validation, execution, and proof. Existing direct controls remain available. [INTERVIEW](INTERVIEW.md) defines the interaction and implementation recipe.

Initial scope is one owner, one existing Desk, one active transformation stream, existing GitHub/Jira sources, local/private/configured model placement, and supported worker adapters. The package does not require a general graph interpreter, arbitrary recursive agents, a new workflow engine, shared enterprise administration, or a new connector to validate R1–R2. Source-specific write support is never implied by read access.

## 2. Installation and activation

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-ENV-001 | R0 | The runtime MUST expose an authenticated diagnostic attestation containing instance ID, process start, backend revision or explicit unknown, frontend build revision, schema version, opaque database identity, and model/connector readiness. Secrets and raw owner paths MUST NOT enter the ordinary Desk view. | AC-01 |
| AA-ENV-002 | R0 | Diagnostics MUST distinguish code on disk from code loaded by the live process and identify multiple instances using the same database without automatically terminating them. | AC-01 |
| AA-ENV-003 | R0 | One model-backed job MUST have an assigned, compatible, probed route. Unavailability MUST open the relevant existing setup surface and retain the user's input. | AC-02 |
| AA-ENV-004 | R0 | A configured source MUST report connection, supported read/write capabilities, scope, observed time, and recovery action separately. Authentication alone MUST NOT imply usable data. | AC-03 |
| AA-ENV-005 | R0 | Capture MUST remain possible without a model, source connector, or portfolio profile, preserving existing recovery behavior and source ownership. | AC-02 |

## 2a. Repeatable interview and intelligent suggestions

R1 supports every section's discovery, suggestions, and honest draft/manual result or prerequisite handoff. A section does not make an unavailable R2/R3 effect executable; execution retains the downstream gate and actual capability requirements. First value does not require every section to be completed.

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-IVW-001 | R1 | The owner MUST be able to enter and independently resume Goals, Projects, concerns/attention, Cadences, People, Decision log, and delegation sections from the Desk or relevant existing record, preserving selected scope. | AC-30 |
| AA-IVW-002 | R1 | Repeated interviews MUST reconcile canonical identities and revisions, revise the intended existing configuration, and preserve lineage. Ambiguous targets MUST be resolved before dependent mutation; replay MUST NOT duplicate records or effects. | AC-31 |
| AA-IVW-003 | R1 | Interview facts MUST retain scope, provenance, time/revision, disclosure class, and stated/observed/inferred/unknown/declined/stale status. Inferred goals, responsibilities, or preferences MUST NOT silently become user-confirmed facts or execution authority. | AC-31 |
| AA-IVW-004 | R1 | A versioned deterministic controller MUST validate structured events, legal transitions, and bounded tool/model work, persisting accepted state and operation links. Replay of recorded inputs MUST reproduce state without new effects; fresh LLM wording need not be identical. | AC-32 |
| AA-IVW-005 | R1 | The LLM MUST use authorized relevant context to ask adaptive questions, ordinarily one material question at a time, while allowing section changes, corrections, skip, pause, and early finish without repeating known unchanged answers. | AC-30 |
| AA-IVW-006 | R1 | Suggestions MUST connect a concrete benefit to the owner's goals or concerns, distinguish evidence from hypotheses, describe behavior and scope, and expose material prerequisites and attention/usage uncertainty. The model MAY propose novel compositions beyond preset recipes. | AC-33 |
| AA-IVW-007 | R1 | Each section MUST use a relevant live capability palette with reviewed domain semantics, actual principal, adapter availability, policy, and catalog revision. A tool's name, schema, or untrusted annotation MUST NOT establish authority or full workflow support. | AC-34 |
| AA-IVW-008 | R1 | Proposed tool calls MUST pass schema, domain-precondition, scope, disclosure, and execution-policy validation through common owning services. Source/tool text MUST NOT expand authority. In-app execution MUST NOT gain owner rights by loopback through the stdio sidecar. | AC-34 |
| AA-IVW-009 | R1 | Configuration MUST bind the exact proposed change revision, target versions, effects, and destinations to applicable owner intent and existing policy. Stale material changes MUST invalidate the plan; an already sufficient deliberate action MUST NOT acquire a redundant confirmation step. | AC-35 |
| AA-IVW-010 | R1 | Completion claims MUST be supported by owning-record read-back and applicable source/model/first-result verification. Saved draft, configured, first result verified, and scheduled occurrence verified MUST be distinct; an LLM completion statement is insufficient. | AC-35 |
| AA-IVW-011 | R1 | Pause, timeout, expired domain setup session, browser closure, or process restart MUST preserve recoverable continuation and reconcile committed operations. Cross-service partial effects MUST remain visible; uncertain effects MUST NOT be blindly repeated or falsely described as globally rolled back. | AC-36 |
| AA-IVW-012 | R1 | Protected section content MUST be partitioned before capture persistence, prompt assembly, and invocation, using permitted People flows and model destinations. Derived suggestions and continuation metadata MUST preserve the same disclosure boundary. | AC-37 |
| AA-IVW-013 | R1 | Without a compatible model, the interview MUST retain a deterministic capture/section/prerequisite path. Necessary model, authentication, or native-permission handoffs MUST preserve continuation and verify resulting readiness without requesting credentials in ordinary chat. | AC-38 |
| AA-IVW-014 | R1 | Every suggestion MUST declare ready-to-prepare, needs-input, needs-connection, or unsupported-idea status grounded in actual capabilities. Unsupported ideas MAY be kept but MUST NOT appear executable. Initially show at most three suggestions with access to more. | AC-33 |
| AA-IVW-015 | R1 | Sections MUST have versioned descriptors declaring fact schema, canonical owners, privacy, capabilities, preconditions, proposal/verification rules, and completion evidence. Adding a section MUST reuse the controller; descriptor changes MUST NOT silently authorize saved proposals. | AC-34 |
| AA-IVW-016 | R1 | Natural-language intent MUST distinguish exploring an idea, selecting a proposal, and directing an exact effect. Missing material schedule, scope, target, or destination details MUST be resolved before dependent execution, retaining authority already supplied for independent work. | AC-35 |
| AA-IVW-017 | R1 | The owner MUST be able to inspect and correct goals/preferences, defer or dismiss suggestions, and remove optional interview context through its owning service. Changed or revoked facts MUST invalidate dependent plans and prevent stale or unwanted suggestions from silently recurring. | AC-31 |
| AA-IVW-018 | R1 | Onboarding MUST support one useful scoped outcome without a full profile, compulsory section sequence, or dependency on later orchestration gates. Finishing or abandoning the interview MUST explain any committed active setup and offer its supported controls. | AC-30, AC-36 |

## 3. Capture, context, and recall

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-CTX-001 | R1 | Voice or typed capture MUST create or update a canonical Note/Thought with original material retained under existing custody rules; capture completion MUST NOT require AI. | AC-04 |
| AA-CTX-002 | R1 | The owner MUST be able to scope an ask to a Project and explicit qualified references; source versions, omissions, and freshness MUST be visible with the result. | AC-05 |
| AA-CTX-003 | R1 | Context MUST be resolved by the hub from authorized canonical records. Missing, inaccessible, or stale required references MUST stop dependent model work with a named repair; optional omissions MUST mark coverage. | AC-05 |
| AA-CTX-004 | R1 | Search MUST retrieve decisions, rationale, source moments when available, related commitments, and superseding records without displaying a superseded decision as current. | AC-06 |
| AA-CTX-005 | R1 | Material generated claims MUST reference supplied evidence or be explicitly classified as inference, suggestion, or unknown. A source locator MUST NOT be presented as proof of semantic correctness. | AC-05 |
| AA-CTX-006 | R1 | A kept answer MUST retain its instruction, source manifest, generation receipt, and canonical destination so a later session can reopen its evidence. | AC-06 |

## 4. Meetings, decisions, and commitments

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-DEC-001 | R1 | Meeting intelligence MUST follow the configured policy and compatible assignment, including the Phase 172 association trigger where integrated; retries MUST not duplicate accepted outcomes. | AC-07 |
| AA-DEC-002 | R1 | Extracted decisions and actions MUST preserve source, wording, and uncertainty. Missing owner, date, or organizational approval MUST remain unknown until established. | AC-07 |
| AA-DEC-003 | R1 | Confirm/Edit/Dismiss MUST write through existing proposal and canonical decision/action services with revision checks and a receipt. The deliberate Confirm gesture MUST not require an additional confirmation solely because it is consequential. | AC-08 |
| AA-DEC-004 | R1 | A decision record MUST support rationale, alternatives, accountable decision owner, authority scope, review trigger/date, and links to affected Projects and commitments. Existing fields MUST be reused. | AC-08 |
| AA-DEC-005 | R1 | Accepting, superseding, or reopening work MUST preserve provenance and update all derived attention views. A local action MUST NOT falsely attest organizational acceptance. | AC-09 |
| AA-DEC-006 | R1 | Preparation for a follow-up or 1:1 MUST use authorized meetings, explicit shared commitments, and grounded source links; it MUST preserve the People disclosure boundary. | AC-10 |

## 5. Attention and preparation

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-ATT-001 | R1 | The opening attention view MUST show at most five ranked priorities by default, an honest remaining count, and access to all items. Each priority MUST name why it matters now and its next available action. | AC-11 |
| AA-ATT-002 | R1 | Ranking MUST use explicit due/blocked/review states and source freshness; its reason MUST be inspectable. A model MAY summarize but MUST NOT silently remove mandatory overdue, failure, or authority interventions. | AC-11 |
| AA-ATT-003 | R1 | Acknowledging or snoozing attention MUST change presentation only. Completing work MUST invoke the owning service; source state changes MUST become visible without duplicating the business item. | AC-11 |
| AA-ATT-004 | R1 | The owner MUST be able to prepare a meeting brief manually from a Project and purpose without calendar integration. Briefs MUST include decisions due, changes, open commitments, source gaps, and suggested questions. | AC-12 |
| AA-ATT-005 | R3 | Scheduled preparation and notifications MUST use a known time zone, quiet hours, bounded frequency, and explicit recipe configuration. Disabled scheduling or unavailable notification delivery MUST be visible. | AC-18 |
| AA-ATT-006 | R1 | An empty or stale source MUST be distinguished from a healthy source with no change. Brief generation time and source observation times MUST be separately visible. | AC-12 |

## 6. Transformation records

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-TRF-001 | R1 | A transformation stream MUST retain its existing Project identity and relate an outcome, affected scope, decision owner, and authoritative record location when known. Missing fields MUST not block capture. | AC-13 |
| AA-TRF-002 | R1 | Evidence MUST distinguish observation, inference, proposal, accepted domain decision, execution receipt, and outcome measurement. Dissenting evidence MUST survive acceptance of a preferred option. | AC-13 |
| AA-TRF-003 | R4 | An optional typed architecture profile MUST track initiative stage, principles, sponsor, affected capabilities/teams, and gate evidence using the lifecycle in CONTRACTS.md. A new document alone MUST not advance a stage. | AC-22 |
| AA-TRF-004 | R4 | A rollout MUST identify pilot population, enablement, owners/capacity, waves, entry/exit criteria, migration/deprecation obligations, and a rollback or revision path. | AC-22 |
| AA-TRF-005 | R4 | An exception MUST identify exact standard/control revision, scope, reason, accepted risk, decision authority/evidence, compensating measures, expiry/review, and resolution plan. Expiry MUST surface for review. | AC-23 |
| AA-TRF-006 | R4 | Adoption measures MUST state definition, population/denominator, numerator, source coverage, period, and observation time. Output counts, attendance, and approvals MUST not be mislabeled as adoption or outcomes. | AC-23 |
| AA-TRF-007 | R4 | Portfolio review MUST expose shared dependencies, conflicting accepted decisions, repeated exceptions, and unsupported stage claims with source links. Automatically detected conflicts MUST remain proposals until reviewed. | AC-24 |
| AA-TRF-008 | R4 | Reconciliation with an authoritative external record MUST show observed revision, discrepancy, proposed change, destination, and resulting revision/receipt. Local edits MUST not silently overwrite accepted external truth. | AC-24 |

## 7. Assignments and supervised orchestration

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-RUN-001 | R2 | Manual, voice-confirmed, and configured automatic starts MUST compile to the same versioned Assignment contract: outcome, Project, context, constraints, worker, budget/deadline, acceptance checks, and result destination. | AC-14 |
| AA-RUN-002 | R2 | An admitted assignment revision MUST be immutable. Editing its scope MUST produce a new revision and explicit disposition of old work; it MUST not retarget an in-flight attempt. | AC-14 |
| AA-RUN-003 | R2 | Every consequential child action MUST use the existing kernel, authenticated principal, bounded authority, and physical-attempt receipt. Assignment payloads MUST not supply principal or executable authority. | AC-15 |
| AA-RUN-004 | R2 | Dispatch MUST select a registered adapter and declare enforceable identity, repository, usage, cancellation, and tool-control capabilities. Unsupported guarantees MUST be shown before launch. | AC-15 |
| AA-RUN-005 | R2 | A worker MUST return a structured result manifest containing artifacts, changed sources, verification results, unresolved issues, and receipts. Worker completion MUST not equal accepted assignment completion. | AC-16 |
| AA-RUN-006 | R2 | Acceptance MUST compare the result with frozen criteria. Deterministic checks and any reviewer judgment MUST retain their provenance; failed mandatory checks MUST block accepted completion. | AC-16 |
| AA-RUN-007 | R2 | The owner MUST be able to answer a blocker, revise future scope, inspect the supported session, cancel, and open results from the Desk, retaining the assignment/thread/attempt links. | AC-17 |
| AA-RUN-008 | R2 | A paused or disconnected browser MUST not own execution state. Restart/reconnect MUST restore the authoritative assignment projection or explicitly show indeterminate work. | AC-17 |
| AA-RUN-009 | R3 | Initial crew execution MUST be bounded to one coordinator and at most two leaf roles, worker and verifier, with depth one and shared budgets. It MUST reconcile Phase 155 rather than create a second child-thread runtime. | AC-21 |
| AA-RUN-010 | R2 | An external worker's unsupported tool interception or spend accounting MUST not be asserted by HoldSpeak. Tasks requiring such guarantees MUST refuse that adapter or remain in an explicitly supported supervised scope. | AC-15 |

## 8. Automatic operation

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-AUT-001 | R3 | An automatic recipe MUST bind a versioned trigger, source scope, template, allowed effects, route policy, limits, and expiry/review point to bounded delegation. Configuration MUST show last run, next trigger, and effective authority. | AC-18 |
| AA-AUT-002 | R3 | A durable trigger identity and source watermark MUST deduplicate equivalent firings. Changed payload under the same command identity MUST conflict without a second effect. | AC-19 |
| AA-AUT-003 | R3 | Schedules MUST define missed-run, overlap, daylight-saving, and quiet-hour semantics. A sleeping hub MUST not report uninterrupted coverage. | AC-18 |
| AA-AUT-004 | R3 | On restart, unfinished effects MUST be reconciled using persisted intent and adapter evidence. Uncertain external effects MUST not be blindly repeated; uncertainty MUST remain visible. | AC-20 |
| AA-AUT-005 | R3 | Retries MUST classify failure, obey a finite attempt/deadline budget, preserve idempotency where supported, and expose terminal failure or indeterminate outcome. | AC-20 |
| AA-AUT-006 | R3 | Stop, revocation, or budget exhaustion MUST fence new dispatch and acceptance of late results. Unsupported remote termination MUST remain explicitly indeterminate rather than reported stopped. | AC-20 |
| AA-AUT-007 | R3 | The scheduler MUST claim work with a durable lease and generation fence; multiple hub processes or concurrent ticks MUST not own the same logical fire. | AC-19 |
| AA-AUT-008 | R3 | The first unattended recipes MUST prove bounded preparation, drift analysis, or result verification before broader automatic effects. Every additional effect class MUST have its own capability, authorization, and failure evidence. | AC-21 |

## 9. Interfaces and information boundaries

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-INT-001 | R2 | Web, supported Thread tools, and MCP assignment operations MUST use the same domain service and validation. Missing runtime adapters MUST return a typed unsupported result, never simulate success. | AC-25 |
| AA-INT-002 | R2 | Discovery MUST distinguish tool existence, adapter availability, permitted scope, read/effect support, and actual model/tool compatibility. A conversational mode MUST not claim tools outside its admitted palette. | AC-25 |
| AA-INT-003 | R1 | Provider reads and effects MUST preserve existing destination and credential boundaries. Jira read support MUST not be advertised as Jira write support. | AC-03 |
| AA-INT-004 | R4 | Export/publication MUST bind exact content, source revision, destination, and current policy. Replaying a publication request MUST reconcile the original result; a local published update MUST not imply an external send. | AC-24 |
| AA-INT-005 | R1 | People-derived material MUST remain within existing permitted projections and egress rules, including summaries and derived brief fields. No covert personal scoring or inferred organizational authority is permitted. | AC-10 |
| AA-INT-006 | R2 | Untrusted source text and worker results MUST be treated as evidence/data, never as authority to change tools, policy, destinations, acceptance checks, or system instructions. | AC-15 |

## 10. Experience and operational quality

| ID | Gate | Requirement | Acceptance |
|---|---|---|---|
| AA-UX-001 | R1 | All recipes MUST use existing Desk primitives and in-place windows, with compact state/action labels and generated work content in the appropriate document surface. | AC-26 |
| AA-UX-002 | R1 | Every new text field MUST support the existing voice affordance or name unavailable capture; keyboard operation, focus return, and accessible control labels MUST work. | AC-26 |
| AA-UX-003 | R1 | The same R1 jobs MUST work at 1440px and 393px browser widths without hidden primary actions or horizontal content loss. Native parity MUST be measured separately. | AC-26 |
| AA-UX-004 | R2 | Active work MUST show outcome, current state, elapsed time, next intervention, actual placement, and known usage; unknown values MUST remain unknown. Diagnostic receipts MUST be reachable through disclosure. | AC-17 |
| AA-UX-005 | R1 | Users MUST distinguish saved, running, awaiting input, stale, failed, indeterminate, and completed states without interpreting logs or internal phase names. | AC-26 |
| AA-NFR-001 | R1 | On the attested pilot hardware, local action feedback MUST appear within 500 ms p95; a Project with 500 linked records MUST show useful cached content within 2 seconds p95, measured over 20 visits. | AC-27 |
| AA-NFR-002 | R1 | For a 30-minute pilot meeting, a terminal intelligence outcome or visible continuing progress MUST appear within 60 seconds of dispatch; actual completion latency MUST be recorded for each model/hardware pair. | AC-07 |
| AA-NFR-003 | R2 | Accepted mutations MUST be durable before observable completion. Command replay MUST be idempotent, stale revision writes atomic refusals, and each logical operation have a single terminal winner. | AC-19 |
| AA-NFR-004 | R2 | Assignment material MUST follow source retention and access rules. Deletion/revocation MUST remove unauthorized cached content and preserve only permitted minimal receipt/tombstone metadata. | AC-28 |
| AA-NFR-005 | R2 | Usage MUST separate observed, estimated, and unavailable values. Limits on child calls, elapsed time, and enforceable model spend MUST be checked before dispatch, including retries and verification. | AC-21 |
| AA-NFR-006 | R3 | Failure in one project, provider, notification path, or worker MUST not stop unrelated due work. Recovery from deliberate restart MUST be observable within two configured scheduler intervals. | AC-20 |
| AA-NFR-007 | R1 | Pilot measurements MUST remain local and count setup, supervision, correction, and maintenance against savings. No external telemetry is introduced. | AC-29 |
| AA-NFR-008 | R2 | Schema changes MUST use the repository's backup/migration contract, preserve existing citizen IDs, and include a restore drill on a copy. Disabling the feature MUST preserve prior records and stop future recipe fires. | AC-28 |

## 11. Definition of useful

R1–R2 acceptance includes a ten-workday pilot, not only unit and UI checks. Initial targets: a usable pre-meeting brief in under five minutes, at least 90% recall and precision for identified meeting decisions/actions, eight of ten decision-recall tasks completed in under one minute, five bounded assignments with reviewed evidence, and at least 120 net minutes saved per working week. These are targets, not measured benefits. AC-29 defines denominators and scoring rules.

Unresolved source access, organizational authority, or actual worker capabilities are explicit missing prerequisites for the affected recipe. They do not prevent unrelated local capture, preparation, and draft work. No requirement can be closed solely by a phase merge, a screenshot, a receipt, or a model claiming success.
