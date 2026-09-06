# Phase 200 technical contracts

**Status:** target contracts for implementation.
Existing APIs remain authoritative until a story implements and verifies an extension.
New field and operation names below are design terms, not advertised callable interfaces.

Read the [architect-assistant contracts](../../../../docs/internal/architect-assistant/CONTRACTS.md) with this document.
Preserve their requirement lineage and record any disagreement before dependent implementation.

## C1. Runtime identity and custody

Diagnostics identify the loaded backend build, frontend build, process start, opaque database identity, schema, and active configuration revision.
The normal Desk shows a compact repair state when incompatible parts are detected.
Detailed process and filesystem information stays in diagnostics.

Build identity is captured at process or bundle creation.
A later Git checkout cannot change the identity reported by an already running process.
Two processes cannot silently own the same scheduled work.

Upgrade creates a recoverable backup using the existing database mechanism.
Restore is first rehearsed against a copy.
The proof includes attached records and permitted protected-store recovery.
Credential handling follows the selected credential store's rules.

## C2. Claim meaning

Claim kind and support are independent.

| Axis | Values | Meaning |
|---|---|---|
| Kind | observation, inference, proposal, decision, execution result, outcome measure | What the statement asserts. |
| Support | unknown, source-linked, supported, disputed | What the evidence establishes. |
| Acceptance | unreviewed, accepted, rejected, superseded | Applicable domain or reviewer judgment. |

A valid reference establishes only source linkage.
A model score cannot establish organizational acceptance.
Supported claims name the exact source version and the validation method or reviewer.
Deterministic extraction of a recorded status can be supported by a field mapping.
Generated prose requires a separate support check.

Old `verified` values retain their original provenance.
The migration maps citation-only records conservatively and records the mapping version.
It must not rewrite history as though a human reviewed those records.
Editing a supported sentence invalidates its support until checked again.

Names, deadlines, numerical measures, and decision acceptance require explicit source support.
Missing values remain typed unknowns or visible draft placeholders.
A citation to a relevant document cannot support an unrelated invented sentence.

## C3. Evidence manifests and working context

Each kept brief and admitted assignment binds a versioned manifest.
It identifies the Project, qualified source refs, observed revisions, observation times, claims, coverage, and resolved data boundary.
The service hydrates records and freezes the permitted material.
The browser does not submit a copied replacement for canonical records.

Working context is explicitly promoted from Interview into existing Notes, Thoughts, or Project facets.
Promotion records provenance and target revision.
Other Threads attach that canonical record by reference.
Corrections change the owning record once and invalidate dependent prepared plans.
Protected People material follows its separate storage and disclosure contract.

Retention, source deletion, and revocation are evaluated at each disclosure and new execution.
Unavailable evidence becomes a named coverage gap.
Historical receipts and backups retain only what the applicable retention contract permits.
Removing current Interview context does not promise erasure of every prior message or backup.
Tests cover future prompts, cached projections, search, export, and result previews.

## C4. Coverage and attention

The aggregate owns an explicit coverage record for every expected Project or source.
States include available, stale, failed, forbidden, and unavailable.
Each record names its observation time and repair path.
Freshness of the aggregate computation is distinct from freshness of its sources.

The initial attention list shows at most five ranked items and an honest remainder.
Stable source IDs deduplicate items across meeting, Watch, and commitment projections.
Each row has a reason, a source, and the owning service's available verb.
A missing source cannot lower a known unresolved item's severity by disappearing.

An empty complete result can express an all-clear.
An empty partial result expresses incomplete coverage.
Notifications use meaningful item transitions, deduplication, quiet hours, and per-Project settings.
A changed item set with the same count must be considered explicitly.
Reading or opening the Desk does not create an external effect.

## C5. Prepared recipe configuration

The first catalog has three versioned recipes:

| Recipe | Inputs | Output | Execution owner |
|---|---|---|---|
| Meeting preparation | Project, meeting purpose, permitted relevant records | Kept brief with sources and open questions | Existing preparation and artifact services |
| Decision and commitment review | Project, review interval, decisions and open commitments | Current decisions, unresolved obligations, evidence gaps | Existing decision, follow-through, and preparation services |
| Weekly Project update | Project, bounded observation window, available source snapshots | Editable update with claim support and coverage | Existing Project update and Steward services |

Every configuration plan records its ID and revision, recipe version, target refs and expected revisions, source scope, route policy, output, trigger, and limits.
It also records resolved prerequisites, effective authority, command identity, per-step state, and resulting owning-service records.
Discovery and schema availability alone do not establish operational readiness.

The LLM may propose a supported recipe or explain an unsupported idea.
The deterministic controller validates the exact plan.
Existing sufficient authorization and runtime policy control application.
A second confirmation is not automatic.
Secrets stay in the existing configuration controls.

State progresses through proposed, prepared, applying, applied, verified, paused, or needs-repair.
An unavailable prerequisite can prevent prepared state.
Partial and indeterminate outcomes remain explicit.
A saved disabled schedule cannot be represented as verified active behavior.

## C6. Setup transactions and recovery

Accepted setup intent and command identity become durable before the first effect.
Each owning service retains its own transaction and idempotency.
The controller records step receipts and verifies the affected records.
There is no implied transaction across all services.

Replay of the same command and payload returns or reconciles the existing result.
A changed payload under the same identity conflicts.
Concurrent direct edits require revalidation against current revisions.
Expired Project setup sessions are replaced through the existing setup contract.

After interruption, successful steps remain visible.
Reconciliation determines whether an uncertain step occurred before retry.
Abandoning the conversation does not undo successful configuration.
Pause disables future triggers; stop addresses a running operation.
Compensation is performed only when the domain operation explicitly supports it.

## C7. Assignment ownership

AssignmentService owns immutable work definitions, run links, and business review.
The kernel owns execution, child operations, and receipts.
Delivery adapters own their actual session and process capabilities.
Artifacts and commitments keep their existing domain owners.

An assignment definition binds:

- Outcome, Project, source manifest, and revision.
- Target repository revision or artifact destination.
- Constraints, permitted capabilities, and selected worker profile.
- Enforceable deadline, attempts, children, concurrency, and available usage limits.
- Mandatory checks and review policy.
- Originating request and related commitment refs.

The request never supplies a trusted principal, raw executable authority, or guessed pane identity.
Register new reference types before exposing them through Web or MCP.
Unknown adapter support is a named limitation.
A task requiring an unenforceable capability must refuse that adapter.

Start with one supervised worker.
A worker-reported result, a check result, and reviewer acceptance are separate records.
Mandatory checks must pass before acceptance.
Acceptance of an assignment does not silently complete a commitment or publish a change.

## C8. Assignment lifecycle and failure windows

Definitions are draft, ready, superseded, or closed.
Execution state is projected from the kernel.
Business review is awaiting-review, accepted, changes-needed, or rejected.
These axes must not collapse into one ambiguous done flag.

Persist the run link before physical dispatch.
Bind attempts to immutable definition and target revisions.
Revising scope creates a new definition with an explicit disposition for old work.
Late results cannot replace the current accepted result.

The design review must resolve:

| Failure window | Required behavior |
|---|---|
| Before admission commit | No adapter dispatch. |
| After admission, before claim | Recover the same durable operation. |
| After claim, before worker acknowledgement | Reconcile target identity before replacement. |
| Effect occurred, receipt absent | Inspect adapter evidence; expose indeterminate when evidence is insufficient. |
| Cancel races with completion | One terminal winner; no new dispatch after the durable fence. |
| Worker cannot be terminated | Report the limitation and fence further accepted output. |
| Mandatory check fails | Result remains reviewable but cannot be accepted as passing. |
| Source or credential revoked | Refuse new disclosure or dispatch under the revoked authority. |

## C9. Scheduling and availability

Heartbeat, Cadence, Steward, and scheduled recordings retain their existing owners.
A recipe binding names which owner supplies the trigger and which executor performs the work.
A common status projection can unify their presentation.
Phase 200 does not introduce a second generic scheduler.

Each logical firing has a durable occurrence identity.
It includes the binding revision, time-zone interpretation, scheduled time or source watermark, and assignment definition where applicable.
Claims use durable leases and generation fences.
Concurrent ticks cannot own the same logical firing.

Each binding states its overlap, retry, missed-run, quiet-hour, and expiry policies.
The initial preparation policy coalesces missed occurrences into one current result.
It preserves the missed-coverage record and never invents uninterrupted monitoring.
Other policies require an explicit recipe need.

Persist stop, pause, and revocation before acknowledging them.
Retry only classified recoverable failures within finite limits.
Uncertain external effects require reconciliation, not blind replay.
At least three real scheduled occurrences must pass before an unattended recipe is accepted.

## C10. Credentials and remote deployment

Choose one owner-controlled hub as the durable execution host.
Reach clients request work from that host.
A reachable inference endpoint is not automatically the application hub.
No multi-writer SQLite arrangement is introduced.

Evaluate an always-available current Mac before moving the application hub.
A different host must preserve the required capture, text insertion, protected-store, and review paths.
Record which integrations require the desktop process.
Reject a deployment choice that removes a required daily capability without a proven supported replacement.

Separate short-lived agent credentials from durable machine enrollment.
Do not persist every current session token merely to survive restart.
The selected design uses protected storage, explicit scope, expiry, rotation, and revocation.
It defines restart behavior and clock handling.
Credentials are not embedded in prompts, logs, command lines, or exported evidence.

The runbook includes startup, sleep behavior, backup, restore, credential replacement, availability status, and pausing work.
Physical network and restart proof uses the selected deployment.
An unavailable host cannot be represented as completed overnight work.

## C11. Shared experience and interfaces

The Desk, Thread, Project Room, existing document surfaces, and shared UI library host the work.
New operations use the same service validation through Web and supported MCP tools.
Tool existence, adapter availability, model compatibility, and authority are disclosed separately.

Every text input uses the existing voice affordance or shows its named unavailable state.
Keyboard navigation, focus return, accessible names, and draft custody are part of acceptance.
Desktop and compact layouts are verified at 1440 and 393 pixels.
Primary actions remain visible during loading, failure, and review.

Routine execution detail stays in the existing Actions disclosure.
Requests for input, refusals, failures, and useful results remain visible.
Generated content belongs in document surfaces.
Implementation terms stay in diagnostics.

## C12. Release and observation

All measures name the build, model, hardware, scenario, denominator, and observation time.
Local fixtures establish deterministic behavior.
Live models establish measured semantic behavior.
Real tasks establish usefulness.
Retain failed runs and abandoned attempts.

No passive telemetry service is introduced.
Pilot observations stay local or in an explicitly selected evidence destination.
Public evidence uses synthetic or redacted material.
Release claims match the supported platform and verified gates.
