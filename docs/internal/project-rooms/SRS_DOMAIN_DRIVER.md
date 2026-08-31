# Project Rooms — domain, driver, and Steward requirements specification

Status: Draft for implementation planning
Version: 0.1
Date: 2026-08-30
Parent: `SRS_SYSTEM.md`

## 1. Purpose

This SRS defines the Project Room's authoritative domain model, persistence, application boundary, Delta algorithm, durable Steward execution, events, sync posture, and MCP driver family.

It is intentionally an extension of HoldSpeak's existing Project capability. It does not authorize a parallel Project model, a second task system, or an MCP-only implementation.

## 2. Existing baseline and governing decisions

The repository already contains:

- canonical `projects`, `meeting_projects`, `project_resources`, and `project_detection_log` persistence;
- `ProjectService` CRUD, archive/restore, resource and meeting association, scoped actions/artifacts, summary, and `since_last_meeting`;
- Project-scoped HTTP routes and a working `ProjectMemoryCore` Web surface;
- Desk application verbs `open-project-memory` and `surface-project-memory`;
- an operation policy whose local default is YOLO, described as a ledger rather than a gate;
- Workbench execution, conductor heartbeat, Cadence attention projection, Agents/Recipes, a service event ledger, and local stdio MCP.
- durable `connector_watches`, semantic Watch diffs/events, due refresh, Workbench Reactions, Web/MCP Watch routes, and a live GitHub PR snapshot adapter.

The implementation MUST graduate these seams. It MUST NOT treat issue #514 as a greenfield replacement.

| Decision | Ruling |
|---|---|
| Domain façade | `ProjectService` remains the transport-neutral façade. Focused internal services may be composed behind it. |
| Truth | Each first-class citizen retains its own authority. Project stores qualified references, observations, Project assessments, and review history. |
| Steward runtime | `ProjectStewardService` [proposed] owns durable run and step state. It borrows proven scheduling and inference helpers; Workbench is not the core engine. |
| Cadence | Projects attention such as review-due, source-degraded, and intervention-needed. It neither schedules nor executes Steward work. |
| MCP | A driver over the same service contract used by Web. MCP is not a second authority or autonomous runtime. |
| Watch | Existing `connector_watches` graduates to `WatchSpec@1`; no parallel Project Watch aggregate is introduced. |
| Provider | MCP/app, connector pack, and local domain are replaceable adapters under one Watch provider contract. |
| V0 protocol | Existing local stdio/protocol is sufficient. Protocol modernization and remote identity do not block the wedge. |
| Schema evolution | Use the repository's additive schema reconciliation and backup practices. Preserve existing Project IDs and relationships. |

## 3. Aggregate authority

### 3.1 Project-owned truth

Project owns:

- identity, name, description, purpose, desired outcome, owner reference;
- lifecycle, posture and posture reason;
- start/target dates, review cadence and next review time;
- template/module configuration and aggregate revision;
- Project-owned workstreams, milestones, risks, dependencies, and signals;
- Project source bindings, semantic role/materiality, and source freshness projection;
- normalized observations, evidence links, proposals, review decisions, updates, and change log;
- Steward policy, command, run, and step records.

### 3.2 Referenced truth

Project does not own the canonical body or lifecycle of:

| Citizen | Project relationship |
|---|---|
| Meeting | association, semantic role, evidence and observations |
| Decision | qualified ref, relevance and evidence; canonical decision remains external |
| Door/follow-through | qualified ref and Project context; status writes go to canonical authority |
| Person/participant | qualified ref and Project role; person identity remains canonical |
| Thread | conversation scope/ref; messages remain canonical |
| Note/artifact | resource/evidence ref; content remains canonical |
| Workbench | source/result refs and optional action collaborator; recipes/results remain canonical |
| Agent/Recipe | optional Steward inference/capability binding; configuration remains canonical |
| Repo/delivery system | source adapter and evidence refs; remote system remains canonical |
| Watch | qualified source ref and Project semantic role; Watch spec/query/baseline/cadence/evaluations remain canonical in Watch service |
| Kernel/Desk object | launch/context relationship; Project domain state remains in Project service |

### 3.3 Domain invariants

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| DOM-001 | MUST/V0 | Every Project-owned entity MUST have a stable opaque ID, `project_id`, created/updated timestamps, and an explicit lifecycle where lifecycle applies. | T,I |
| DOM-002 | MUST/V0 | External citizens MUST be represented by qualified references, not copied mutable records. | T,I |
| DOM-003 | MUST/V0 | Every accepted Project mutation MUST increment `projects.revision` exactly once and append a Project change in the same transaction. | T |
| DOM-004 | MUST/V0 | An accepted proposal, its resulting mutations, review decision, aggregate revision, and service event MUST commit atomically. | T |
| DOM-005 | MUST/V0 | Observation, Project assessment, model proposal, accepted state, and canonical external truth MUST remain distinguishable in storage and API results. | T,I |
| DOM-006 | MUST/V0 | YOLO removes per-action confirmation. It MUST NOT remove input validation, optimistic concurrency, idempotency, provenance, effect verification, or durable receipts. | T |
| DOM-007 | MUST/V0 | Narrative prose alone MUST NOT complete a milestone, close a risk, or change an external action's canonical status. | T |
| DOM-008 | MUST/V0 | A stale, unavailable, or unsupported source MUST produce explicit degraded coverage and MUST NOT be interpreted as no change. | T,D |
| DOM-009 | MUST/V0 | At most one Steward run per Project may be in an active execution state. | T |
| DOM-010 | MUST/V0 | All effect commands MUST be idempotent under a caller-supplied `command_id`. | T |
| DOM-011 | MUST/V0 | Existing archived Projects and legacy relationships MUST remain readable and restorable after reconciliation. | T |
| DOM-012 | MUST/V0 | Incoming legacy sync MUST NOT erase Project Room fields that the legacy payload cannot represent. | T |
| DOM-013 | MUST/V0 | A Project Watch binding MUST NOT copy provider query, condition, cadence, baseline, evaluation, or effect truth from the canonical Watch. | T,I |
| DOM-014 | MUST/V0 | Egress posture for every provider and model call MUST be recorded with the operation receipt. | T,I |

## 4. Identifiers and references

### 4.1 ID forms

New records MUST use repository-compatible opaque identifiers with these diagnostic prefixes:

| Entity | Prefix | Stability rule |
|---|---|---|
| Project item | `pitem_` | Stable for the item's lifetime |
| Source | `psrc_` | Stable for one configured source |
| Observation | `pobs_` | Deterministic from adapter, source identity, source version, and observed fact key |
| Proposal | `pprop_` | Deterministic from Project, review window, proposal kind, target, and normalized patch |
| Review | `prev_` | Unique accepted/review session identity |
| Update | `pupd_` | Stable draft identity; revisions do not replace the ID |
| Change | `pchg_` | Bound to aggregate revision and deterministic ordinal |
| Command | `pcmd_` | Caller-supplied or generated once at initiation |
| Steward policy | `pstpol_` | Stable per Project policy |
| Steward run | `pstrun_` | Unique execution attempt |
| Steward step | `pststep_` | Unique run step/effect attempt |

### 4.2 Qualified refs

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| REF-001 | MUST/V0 | A central qualified-ref parser/formatter MUST replace feature-local string splitting for newly touched Project code. | T,I |
| REF-002 | MUST/V0 | A qualified ref MUST contain a registered citizen type and opaque local identity and MUST round-trip without loss. | T |
| REF-003 | MUST/V0 | The implementation MUST settle the existing `person:` versus persona/people naming mismatch through one canonical type plus backward-compatible aliases. | T,I |
| REF-004 | MUST/V0 | Unknown ref types MUST remain representable and inspectable but MUST NOT be mutated through an unregistered adapter. | T |

## 5. Persistence model

Column names below are the logical contract. Exact SQLite declarations MAY follow repository conventions, but semantic fields MUST not be collapsed into an untyped catch-all.

### 5.1 Extend `projects`

Add nullable/backfilled fields:

- `purpose`, `outcome_text`, `owner_ref`;
- `lifecycle`, `posture`, `posture_reason`;
- `start_at`, `target_at`;
- `review_cadence_json`, `next_review_at`;
- `template_key`, `modules_json`;
- `revision` defaulting safely for existing rows;
- `last_review_id`, `last_review_at`.

Existing `context_json` MAY remain for compatibility but MUST NOT be the source of truth for the fields above.

### 5.2 Enrich `project_resources`

Preserve current resource identity and coarse sync behavior. Add:

- `semantic_role` such as `evidence`, `delivery`, `discussion`, `reference`, `steward-input`;
- `metadata_json` for adapter-specific non-authoritative hints;
- `revision` for optimistic concurrency.

### 5.3 `project_items`

Stores Project-owned `workstream`, `milestone`, `risk`, `dependency`, and `signal` records:

```text
id, project_id, item_type, title, summary, lifecycle, severity,
owner_ref, due_at, sort_key, details_json, provenance_kind,
source_observation_id, created_by_ref, revision, created_at, updated_at
```

`details_json` MUST validate against a closed schema selected by `item_type`. It MUST NOT accept arbitrary silent fields. Common indexed/query fields remain first-class columns.

### 5.4 `project_sources`

```text
id, project_id, source_ref, label, semantic_role, materiality_policy_json,
enabled, freshness_state, last_observed_at, revision, created_at, updated_at
```

For a Watch source, `source_ref` is `watch:<watch_id>`. Provider query, connection, baseline, cadence, test, and error authority remain with the Watch. For native sources, the canonical citizen retains source cursor/content authority. Credentials or opaque external secrets MUST remain in their provider authority and be referenced, not copied here.

### 5.5 `project_observations`

Append-only normalized facts:

```text
id, project_id, source_id, observation_kind, subject_ref,
source_version, observed_at, captured_at, fact_json, content_hash,
supersedes_observation_id, coverage_state
```

An adapter retry for the same source fact/version MUST resolve to the same observation identity or no-op on uniqueness.

### 5.6 `project_evidence_links`

```text
id, project_id, target_ref, evidence_ref, relation,
observation_id, excerpt_locator_json, created_at
```

Evidence links point from an assessment, proposal, update claim, or Project item to canonical/normalized evidence. Excerpts MAY aid display but do not replace the source ref and locator.

### 5.7 `project_proposals`

```text
id, project_id, review_window_key, proposal_kind, target_ref,
title, rationale, patch_json, materiality, confidence,
producer_kind, model_receipt_ref, lifecycle, deferred_until,
dismissal_basis_hash, created_at, decided_at, decided_by_ref
```

Proposal lifecycle is `open | accepted | deferred | dismissed | superseded | failed`. An accepted proposal's patch MUST be schema validated and applied through a registered command handler.

### 5.8 `project_reviews`

```text
id, project_id, status, from_sequence, through_sequence,
source_manifest_json, project_revision_opened, project_revision_accepted,
opened_at, accepted_at, accepted_by_ref, summary_json
```

The source manifest freezes each source identity, cursor/version, success/failure, and observation watermark used for the review.

### 5.9 `project_updates`

```text
id, project_id, review_id, status, title, body_markdown,
claims_json, source_manifest_json, generated_by_kind,
model_receipt_ref, revision, created_at, updated_at, published_at
```

Status is `draft | ready | published | superseded`. V0 `published` MAY mean explicitly marked published after copy/export; it MUST NOT imply a remote effect that did not occur.

### 5.10 `project_changes`

```text
id, project_id, project_revision, change_kind, target_ref,
actor_ref, command_id, before_hash, after_hash, summary_json, created_at
```

This is the authoritative aggregate change sequence for Project-owned state. It is not a copy of all external citizen event logs.

### 5.11 Commands and Steward records

`project_commands`:

```text
id, project_id, command_kind, request_hash, status,
result_json, error_code, created_at, completed_at
```

`project_steward_policies`:

```text
id, project_id, enabled, posture, agent_ref, recipe_ref,
tool_palette_json, trigger_json, max_actions_per_run,
failure_threshold, cooldown_seconds, revision, created_at, updated_at
```

`project_steward_runs`:

```text
id, project_id, policy_id, trigger_kind, status,
input_project_revision, review_id, started_at, heartbeat_at,
stop_requested_at, completed_at, result_summary_json,
error_code, error_message
```

`project_steward_steps`:

```text
id, run_id, ordinal, phase, tool_key, command_id, status,
input_json, output_json, effect_receipt_json, verification_json,
attempt, started_at, completed_at, error_code, error_message
```

Run status is `queued | running | stopping | succeeded | partial | failed | interrupted | cancelled`. Step status is `pending | running | succeeded | failed | indeterminate | skipped | cancelled`.

### 5.12 Persistence requirements

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| DB-001 | MUST/V0 | Reconciliation MUST add/backfill Project Room schema without changing existing Project IDs or deleting legacy data. | T,I |
| DB-002 | MUST/V0 | All Project-owned write tables MUST enforce Project foreign keys and useful uniqueness/idempotency constraints. | T,I |
| DB-003 | MUST/V0 | Observation and change streams MUST be append-only through service APIs. Corrections supersede rather than silently rewrite source history. | T |
| DB-004 | MUST/V0 | JSON fields with closed semantics MUST be validated before persistence. | T |
| DB-005 | MUST/V0 | Reads for room, review, timeline, updates, and run history MUST be bounded, indexed, and deterministically ordered. | T,I |

### 5.13 Graduate existing Watches

The complete setup/Watch schema is normative in `SRS_PROJECT_INTERVIEW_WATCHES.md`. Additively extend `connector_watches` for `WatchSpec@1` with Project, intent, provider connection, subject, trigger, condition/rule, revision, lifecycle, test, baseline, and next-evaluation state. Preserve existing Watch IDs, query/snapshot columns, cadence/error history, and attached `connector_reactions`.

Add durable setup sessions/answers/proposals, non-secret provider connection metadata, Watch rules, evaluations, and effects. Existing Watches migrate as legacy non-Project Watches and MUST continue to run.

## 6. Application service and HTTP contract

### 6.1 Service composition

`ProjectService` remains the public application façade and composes:

- `ProjectSetupService` — durable interview and atomic creation from selected tested Watch proposals;
- `ProjectEvidenceCollector` — calls registered source adapters and normalizes observations;
- `ProjectDeltaService` — freezes a review window and produces deterministic Delta/proposals;
- `ProjectUpdateService` — drafts, edits, cites, and publishes/marks updates;
- `ProjectStewardService` — owns policy, durable commands, runs, steps, verification, and scheduling eligibility.

Separate universal collaborators are `WatchService`, `WatchProviderRegistry`, and `WatchEvaluationService`. They own Watch lifecycle/provider adaptation/evaluation and call Project services through registered actions. `ReactionService` remains a compatibility façade or is absorbed without changing legacy behavior.

Repositories MUST remain below these services. Web routes, MCP tools, and conductor blocks MUST NOT perform direct Project SQL.

### 6.2 Coherent room projection

`GET /api/projects/{project_id}/room` MUST provide a coherent, revision-stamped projection suitable for the first useful render, including:

- Project header/outcome/posture/review state;
- current focus records and coverage summary;
- active or most recent review/Delta summary;
- current draft/latest update;
- Steward policy and active/latest run summary;
- per-section status/error and pagination cursors where applicable.

This endpoint replaces the current five-request fan-out as the default path. Detail endpoints MAY load timeline pages, proposal evidence, update history, or run steps progressively.

### 6.3 Command contract

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| API-001 | MUST/V0 | Every Project write MUST accept `expected_revision` and `command_id`; a stale revision MUST return a typed conflict without partial mutation. | T |
| API-002 | MUST/V0 | Repeating a completed command with the same ID and request hash MUST return the stored result; a different request hash MUST return an idempotency conflict. | T |
| API-003 | MUST/V0 | Results MUST include `result_kind`, `project_id`, `project_revision`, `changed_refs`, and typed warnings/errors. | T,I |
| API-004 | MUST/V0 | An accepted write MUST append its change and `ServiceEventLedger` event inside the same database transaction. | T |
| API-005 | MUST/V0 | Project Room reads MUST expose revision, coverage/freshness, partial-error metadata, and stable pagination cursors. | T,D |
| API-006 | MUST/V0 | Legacy Project endpoints MUST remain compatible or return a documented migration response while the Web feature graduates. | T |

## 7. Evidence collection and Delta

### 7.1 V0 adapters

The V0 collector MUST support adapters for:

1. associated meetings/transcript-derived facts;
2. `project_resources` and artifacts/notes;
3. canonical decisions;
4. follow-through/action items;
5. available watches or delivery evidence already represented in HoldSpeak.

Watch-backed Project sources consume canonical Watch observations/evaluations rather than issuing provider reads again. Native Project evidence adapters return a source cursor/version, freshness, normalized observations, and adapter-local errors. One adapter failure MUST NOT discard successful observations from others.

### 7.2 Deterministic review algorithm

For `open_review(project_id)` the system MUST:

1. acquire a stable Project revision and determine the last accepted review cursor;
2. query each enabled source adapter independently;
3. persist new normalized observations idempotently;
4. freeze `through_sequence` and a source manifest, including failures and watermarks;
5. compare observations and Project changes after the prior accepted cursor;
6. group changes by stable target/ref and classify added, changed, closed, overdue, blocked, contradicted, or coverage-degraded;
7. detect conflicts between observations without silently selecting a winner;
8. create deterministic proposals where a registered patch/action follows from explicit rules;
9. attach evidence and calculate materiality using deterministic factors;
10. sort by materiality, event time, kind, and stable ID;
11. optionally allow a model to add explanations or proposals without removing or rewriting deterministic entries;
12. store the review window for repeatable inspection.

Materiality factors SHOULD include outcome relevance, lifecycle severity, overdue/blocked state, decision or commitment impact, novelty, and evidence confidence. The formula MUST be versioned and testable.

### 7.3 Review decisions

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| DEL-001 | MUST/V0 | Delta MUST be based on the last accepted review cursor and a frozen current source manifest, not the latest-two-meetings shortcut. | T |
| DEL-002 | MUST/V0 | Accept, edit-and-accept, defer, and dismiss MUST be durable per-proposal decisions. | T,D |
| DEL-003 | MUST/V0 | Dismissed material MUST NOT recur unless its source/version, normalized patch, or material evidence changes. | T |
| DEL-004 | MUST/V0 | Deferred material MUST reappear at its due condition without being misrepresented as new. | T |
| DEL-005 | MUST/V0 | Accepting the review MUST atomically apply accepted proposals, freeze the accepted summary, and advance Project review pointers. | T |
| DEL-006 | MUST/V0 | A review with partial sources MAY be accepted, but coverage caveats MUST remain attached to the review and generated update. | T,D |
| DEL-007 | MUST/V0 | Model unavailability MUST leave deterministic Delta fully usable. | T,D |

## 8. Update factory

Update generation MUST operate over an explicit Project revision and review/source manifest. It MUST produce editable Markdown with structured claim metadata.

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| UPD-001 | MUST/V0 | Sections MUST cover progress, decisions, risks/blockers, dependencies, next actions, and source-coverage caveats when applicable. | T,D |
| UPD-002 | MUST/V0 | Every factual claim MUST resolve to one or more evidence refs/locators. Unsupported model language MUST be omitted or visibly marked for owner review. | T,I |
| UPD-003 | MUST/V0 | A deterministic template fallback MUST remain available when inference is unavailable. | T,D |
| UPD-004 | MUST/V0 | Regeneration MUST create a new draft revision or explicitly replace only an unaccepted draft; it MUST never rewrite a published update. | T |
| UPD-005 | MUST/V0 | Save, Copy Markdown, and Mark Published MUST be separate commands with honest receipts. | T,D |

## 9. Project Steward

### 9.1 Runtime ruling

The Steward is not a prompt sent to Workbench. Workbench currently provides prompt-to-artifact batch processing, not the general durable observe/action/verification loop required here.

`ProjectStewardService` MUST own run coordination and persistence. It SHOULD reuse:

- conductor heartbeat, due-work polling, failure isolation, and event broadcasting patterns;
- frozen inference routing/model assignment helpers;
- registered Workbench outputs as evidence or explicitly configured collaborator steps;
- Cadence projection for human attention.

The main conductor SHOULD call `ProjectStewardService.run_due()` as an isolated block. A broken Project or source MUST NOT stop other conductor responsibilities.

### 9.2 Run lifecycle

`POST /api/projects/{id}/steward/runs` MUST persist and return a run ID immediately. A worker then executes:

```text
OBSERVE → COMPARE → PROPOSE → ACT → VERIFY → RECORD
```

Every phase MUST checkpoint durable run/step state. Manual `run_once` ships first. Scheduling is enabled only after deterministic action/recovery tests pass and is required for Gate A unattended dogfooding.

### 9.3 V0 eligible effects

A V0 Steward run MAY:

- refresh configured sources and persist observations;
- create deterministic proposals and evidence links;
- apply configured Project-owned proposal effects in YOLO;
- draft or replace an unaccepted Project update;
- create exactly one deduplicated Door/follow-through item for the highest-material overdue or blocking item that lacks canonical follow-through.

A Watch rule MAY request `ProjectStewardService.run_once()` with Project ID and observation watermark. Multiple requests at the same watermark MUST deduplicate to one Project run. Watch scheduling/evaluation remains in `WatchService`; Steward does not independently poll the same provider.

Remote delivery-system mutation is out of V0 where no verified actuator already exists. This is an actuator omission, not an approval-policy restriction.

### 9.4 Reliability behavior

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| STW-001 | MUST/V0 | A run MUST be durable before asynchronous work begins and MUST expose a pollable state. | T |
| STW-002 | MUST/V0 | The active-run uniqueness invariant MUST prevent overlapping Project runs. | T |
| STW-003 | MUST/V0 | Stop MUST set a durable request checked between steps and before every new effect; it MUST not depend on a model response. | T,D |
| STW-004 | MUST/V0 | An effect with a read path MUST be verified and record expected versus observed state. | T |
| STW-005 | MUST/V0 | An indeterminate effect MUST NOT be blindly replayed. Recovery MUST first reconcile by idempotency key or read-back. | T |
| STW-006 | MUST/V0 | Source failures MUST be isolated and summarized as partial coverage. | T |
| STW-007 | MUST/V0 | Model failure MUST fall back to deterministic Delta/update behavior and retain an intelligible run receipt. | T,D |
| STW-008 | MUST/V0 | Retry counts, per-run action counts, repeated identical failure, and cooldown MUST be bounded by policy. | T |
| STW-009 | MUST/V0 | Startup recovery MUST mark abandoned running steps/runs interrupted and reconcile safe resumability. | T |
| STW-010 | MUST/V0 | YOLO runs MUST not show confirmation prompts for eligible configured effects. | T,D |
| STW-011 | MUST/V0 | A successful dogfood run MUST perform at least one real, deduplicated effect beyond summarization and record its verification/receipt. | T,D |

## 10. Events and Cadence projection

All accepted events MUST use `ServiceEventLedger.append_in_transaction`.

Minimum event kinds:

- `project.created`, `project.updated`, `project.archived`, `project.restored`;
- `project.resource.linked`, `project.resource.unlinked`;
- `project.observations.refreshed`, `project.source.degraded`;
- `project.review.opened`, `project.proposal.decided`, `project.review.accepted`;
- `project.update.drafted`, `project.update.published`;
- `project.steward.configured`, `project.steward.run_started`, `project.steward.step_completed`, `project.steward.run_completed`, `project.steward.intervention_required`.

Event payloads MUST be small and ref-oriented: Project ID/revision, target refs, command/run IDs, event-specific status, and timestamps. Large bodies and transcripts remain behind their canonical refs.

Cadence MAY project `review_due`, `source_degraded`, and `steward_intervention_required`. Cadence MUST NOT become the schedule of record, run executor, or Project state authority.

## 11. MCP Project driver family

### 11.0 Current-layer assessment

The MCP layer is a strong driver foundation, but it is not yet the self-driving Project layer.

| Dimension | Current standing | Project Room implication |
|---|---|---|
| Breadth | Strong: ~94 tools across ~20 families, plus owner resources/templates. | Reuse family registration, discovery, and transport; do not build another tool server. |
| Authority parity | Strong: the stdio sidecar opens the same database and generally dispatches through application services. | `project.*`, setup, provider, and Watch tools can be thin drivers over the same contracts as Web. |
| Watch primitives | Useful partial: MCP already lists/creates/enables/previews/refreshes Watches and manages Reactions/events (currently in the reactions MCP family module). | Graduate these tools to `WatchSpec@1`; add durable test/baseline/evaluation/effect inspection rather than replacing them. |
| Project semantics | Missing: no `project.*` family. | Add coherent Project/Delta/update/Steward/setup operations with stable results. |
| Autonomous lifecycle | Missing for Project: current Watch→Workbench reactions do not provide the Project Steward's durable observe→act→verify run contract. | MCP starts/polls the application-owned run; it does not hold orchestration inside one tool call. |
| Provider consumption | Missing: HoldSpeak is an MCP server, not a general external MCP client. | External GitHub/Jira MCP/app support requires a provider adapter/client seam; V0 may use existing local connector packs behind the same contract. |
| Remote ecosystem | Deferred: local stdio is the supported posture. | Do not block market validation on remote transport, identity, Tasks, or protocol modernization. |

Verdict: MCP already stands up well as a programmable façade and generic Watch driver. It does not yet stand up as the Project's autonomous driver layer because Project semantics, interview/provider discovery, durable Steward runs, and external provider consumption are absent. The SRS closes those exact gaps without making MCP a parallel authority.

### 11.1 Placement and behavior

Add `holdspeak/mcp/families/project.py` using the existing family registration pattern. Every tool MUST call `ProjectService` or a service-composed command; no tool may issue Project SQL or bypass event/command handling.

The V0 tool family SHOULD include:

| Tool | Effect |
|---|---|
| `project.list` / `project.get` / `project.get_room` | Read identity or coherent room projection |
| `project.create` / `project.update` / `project.archive` / `project.restore` | Project lifecycle commands |
| `project.link` / `project.unlink` | Manage qualified citizen/resource relationships |
| `project.open_review` / `project.get_delta` | Refresh/freeze and read Delta |
| `project.decide_proposal` / `project.accept_review` | Review commands |
| `project.list_updates` / `project.draft_update` / `project.update_draft` / `project.publish_update` | Update factory |
| `project.configure_steward` / `project.run_steward` / `project.stop_steward` | Steward commands |
| `project.get_steward_run` | Poll durable run/steps |
| `project.setup.*` | Start/resume/answer/suggest/finalize the same durable setup interview |
| `provider.*` | Inspect connections/capabilities and discover bounded resources through Watch adapters |
| `project.watch.*` | Propose, test, activate, inspect, evaluate, pause, and retire Project Watches |

Tool names MAY conform to the repository's exact MCP naming convention, but the domain verbs and result schemas MUST remain stable.

### 11.2 Resources

Expose compact read resources/templates for:

- `holdspeak://projects/{project_id}`;
- `holdspeak://projects/{project_id}/room`;
- `holdspeak://projects/{project_id}/delta`;
- `holdspeak://projects/{project_id}/updates/{update_id}`;
- `holdspeak://projects/{project_id}/steward/runs/{run_id}`.

### 11.3 Driver requirements

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| MCP-001 | MUST/V0 | MCP Project tools MUST use the identical service commands, revision checks, idempotency, events, and error codes as Web. | T,I |
| MCP-002 | MUST/V0 | Effect tools MUST require or generate a returned `command_id`; callers MUST be able to retry safely. | T |
| MCP-003 | MUST/V0 | Long-running Steward invocation MUST return `run_id` promptly and use explicit polling rather than holding a tool call open. | T,D |
| MCP-004 | MUST/V0 | Results MUST be structured JSON-serializable data and MUST not require parsing prose to determine success or changed refs. | T |
| MCP-005 | MUST/V0 | Unsupported citizen mutations MUST return a typed capability error, never a simulated success. | T |
| MCP-006 | MUST/V0 | Failure to initialize an unrelated MCP family MUST NOT suppress Project reads/tools. | T |
| MCP-007 | SHOULD/V1 | A focused `PROJECT_PALETTE` and Project Thread mode SHOULD make the family safely reusable by agents without exposing all MCP tools. | T,I |
| MCP-008 | LATER/V2 | Current remote transport/protocol, scoped remote identity, Tasks integration, and ecosystem publication are deferred until after product validation. | I |

## 12. Sync posture

V0 sync is `identity_only` for the Project Room additions:

- existing Project identity and coarse relationships continue to sync as they do today;
- new operating items, observations, reviews, updates, and Steward records remain local;
- imported legacy Project changes merge only fields represented by their payload and MUST preserve local-only fields;
- APIs and UI MUST be capable of reporting local-only scope honestly.

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYN-001 | MUST/V0 | Existing sync round trips MUST retain Project identity and relationships after schema extension. | T |
| SYN-002 | MUST/V0 | A legacy incoming Project payload MUST not null or reset Project Room fields absent from the payload. | T |
| SYN-003 | SHOULD/V1 | Rich Project Room sync SHOULD begin with an explicit conflict model and per-entity revision contract, not accidental JSON replication. | I |

## 13. Test and verification specification

### 13.1 Required automated suites

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| TST-001 | MUST/V0 | Schema reconciliation tests MUST cover a pre-Project-Room database, current data preservation, repeated reconciliation, backup behavior, and archive/restore. | T |
| TST-002 | MUST/V0 | Domain tests MUST cover every invariant in section 3.3, including revision conflicts and transactional event/change writes. | T |
| TST-003 | MUST/V0 | Adapter contract tests MUST cover retry deduplication, stale/failed coverage, normalized identity, and partial success. | T |
| TST-004 | MUST/V0 | Golden Delta tests MUST prove frozen-window repeatability, ordering, conflict retention, dismissal/defer recurrence, and model-independent results. | T |
| TST-005 | MUST/V0 | Steward tests MUST cover active-run exclusion, stop, crash recovery, bounded retry, effect idempotency, indeterminate reconciliation, verification, and model/source failures. | T |
| TST-006 | MUST/V0 | Contract tests MUST run equivalent Web/API and MCP commands and assert equivalent result kinds, revisions, changed refs, and errors. | T |
| TST-007 | MUST/V0 | End-to-end tests MUST cover the integrated acceptance scenario with a real persisted Project and non-simulated follow-through effect. | T,D |
| TST-008 | MUST/V0 | Legacy regression tests MUST cover current Project CRUD, meeting association, resources, summary, and archive behavior. | T |

### 13.2 Observability required for dogfood

The implementation MUST expose enough local diagnostics to calculate:

- time from create/connect to first useful Delta;
- review count and acceptance decisions;
- update generation/edit/copy timestamps and retained generated content where measurable;
- Steward runs, effects, verification outcome, retries, failures, and owner intervention;
- source coverage and freshness per review;
- duplicate prevention and idempotent replays.

Product metrics MUST be derived from durable events/records where practical, not a second analytics truth.

## 14. Implementation slices and entry/exit conditions

### P0 — contract and baseline

- Record these architecture decisions and freeze qualified-ref/result/error contracts.
- Add characterization tests for existing Project service/routes/Web/MCP registration.
- Exit: current behavior is protected and schema/API names are agreed.

### P1 — aggregate and coherent read

- Reconcile `projects`, resources, items, changes, events, qualified refs, and legacy Watch compatibility.
- Implement expected revision and command idempotency.
- Add `GET /room`; graduate Web to it without removing legacy detail routes.
- Exit: owner can create/configure/open a revisioned Project Room and legacy Projects remain intact.

### P1a — outcome interview and native Watches

- Add durable setup session/answers/proposals and deterministic native Watch suggestions.
- Graduate `connector_watches` and add provider/rule/evaluation/effect contracts.
- Finalize atomically into Project plus selected local Watches; retain Blank escape hatch.
- Exit: setup resumes after reload and opens a non-empty Project Room without external provider dependency.

### P2 — sources, observations, and deterministic Delta

- Add source/observation/evidence/review/proposal schema and native/Watch observation adapters.
- Implement frozen review algorithm and review decisions.
- Exit: one real Project produces repeatable evidence-linked Delta with honest partial coverage.

### P2a — GitHub Watch vertical slice

- Add real connection/auth status, repository discovery or typed repo validation fallback, precise PR Watch compilation, current-state test, baseline, and manual evaluation.
- Reuse the existing GitHub snapshot/diff path; preserve exact provider capability/test state.
- Exit: the owner reaches one live tested Watch and populated Now in under five prepared-fixture minutes.

### P3 — Update Factory

- Add update persistence, deterministic/model drafting, citations, edit/copy/publish.
- Exit: owner creates a usable evidence-backed update without reconstructing project truth.

### P4 — manual YOLO Steward

- Add policy/run/step/command persistence and `run_once`.
- Support the bounded V0 effect set, verification, Stop, and recovery.
- Exit: a manual run performs one real deduplicated effect and drafts an update with a durable receipt.

### P5 — unattended dogfood

- Add `WatchService.evaluate_due()` and `ProjectStewardService.run_due()` as independent conductor failure boundaries, bounded Watch-triggered Steward requests, circuit breaker, and Cadence attention projection.
- Exit: Gate A observes at least two useful unattended runs without confirmation prompts or duplicate effects.

### P6 — MCP Project family and design-partner hardening

- Expose the same setup, provider discovery, Watch, and Project closed loop through MCP resources/tools and focused palette.
- Harden partial initialization, structured errors, and contract parity.
- Exit: a local MCP client can drive the same scenario, and the product is ready for Gate B partners.

### P7 — Jira parity when selected

- Add a real Jira provider adapter for site/Project/type/status discovery and issue search; compile/test/baseline/poll semantic issue Watches.
- Exit: Jira readiness is backed by live discovery/search and the same no-duplicate Delta/action behavior, never pushed fixtures alone.

P6 tooling work MAY begin earlier in parallel after P1 contracts freeze, but it MUST NOT invent behavior ahead of the service boundary. P7 moves into the proving V0 only if Jira is the selected EverDriven delivery source.

## 15. Architecture acceptance scenario

The architecture slice is accepted when an automated/instrumented scenario proves:

1. a legacy database reconciles without identity or relationship loss;
2. a durable setup session compiles owner intent into one real tested Watch and atomically activates a Project without false baseline transitions;
3. a later provider change creates one canonical Watch evaluation and normalized observation while another source fails;
4. Delta freezes the successful evidence plus explicit degraded coverage;
5. the same window/evaluation recomputes identically and review decisions persist;
6. a YOLO Steward run is durably requested once at the observation watermark, performs one idempotent canonical follow-through effect, verifies it, drafts a cited update, and completes with a receipt;
7. retrying the Watch evaluation or command cannot duplicate the effect;
8. Web and MCP observe the same final Project/Watch revisions and refs;
9. accepting the review advances the cursor without altering canonical external truth improperly;
10. restart recovery leaves no permanently running phantom Watch evaluation or Steward step.
