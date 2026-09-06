# Domain and execution contracts

Status: proposed design supporting SRS-AA. Names marked proposed are not callable APIs or installed configuration. Existing kernel schemas, qualified references, Project envelopes, and citizen services remain authoritative. This document elaborates AA-IVW, AA-TRF, AA-RUN, AA-AUT, AA-INT, and AA-NFR requirements.

## 1. Record ownership

| Record | Authority | Permitted new material |
|---|---|---|
| Project | Existing ProjectRepository/ProjectService | Optional typed architecture profile keyed by the existing Project ID. |
| Note, Thought, Meeting, Artifact | Existing citizen services | Relationships and reference manifests; no copied editable replacement. |
| Decision and decision record | Existing decision lifecycle and record services | Explicit organizational authority metadata and evidence links where absent. |
| Action and commitment | Existing Follow-Through and permitted People services | Assignment linkage; completion remains a domain command. |
| Watch, review, update, Steward run | Existing owning services | Recipe binding and assignment references through supported extensions. |
| Interview session, proposal, continuation | Proposed interview coordinator over existing services | Versioned control state, scoped fact/source references, pending questions, plan revisions, and operation/read-back links. No duplicate editable domain records. |
| Goals and working preferences | Existing scoped Note/Thought/Project records; a typed facet only if necessary | User-stated intent, scope, provenance, review criteria, and correction history. No assumed shipped Goals service or blanket execution authority. |
| Assignment definition, acceptance | Proposed AssignmentService | Immutable work contract, revision lineage, acceptance records. |
| Execution, claims, effects, receipts | Existing kernel and adapter journals | Registered assignment parent/child types and native product projections. |
| Attention | Existing Door/shade/projection authorities | Derived assignment/intervention items with stable source identity. |
| Organizational standard/ADR | Explicitly configured Git or document source | Observed revision and local discrepancy proposal; no implicit transfer of authority. |

Proposed tables are `assignment_definitions`, `assignment_run_links`, `assignment_reviews`, and `project_architecture_profiles`. The first stores immutable definition revisions. Run links map trigger identity and definition revision to kernel operation IDs; they are not another queue or execution journal. Reviews own business acceptance. Where an existing contract already stores a field, reference or extend it instead of duplicating it.

New `assignment` and `assignment_run` citizen prefixes require explicit registration in the shared qualified-ref registry and serializers before emission. Decision-record locators must use the actual canonical resolver; a string that resembles a ref is insufficient. Model/provider IDs, process targets, and external locators are typed fields, not guessed citizen refs.

### Interview coordination boundary

[INTERVIEW](INTERVIEW.md) specifies the section descriptors, fact/suggestion status, reducer, proposal preparation, authority binding, and recovery behavior. Interview storage owns conversation continuation and proposals; canonical mutations retain their domain owners. Protected People content cannot be copied into normal interview storage or model context. The Project setup service's transient session and expiry remain distinct from durable interview continuation.

Interview effects persist intent and command identity before dispatch, then retain owning-service receipts and read-back. Their R1 duplicate/recovery guarantees apply even before the later Assignment implementation. Cross-service steps are independently committed and reconciled; there is no implied global transaction. Reopening or abandoning a session never silently activates or rolls back a recipe. If interview handles become qualified citizen references, register their resolver and disclosure rules before emission.

## 2. Evidence manifest

Every prepared brief, admitted assignment, and accepted review binds a manifest:

| Field | Semantics |
|---|---|
| `manifest_id`, `schema_version`, `created_at` | Stable opaque identity, version 1, UTC creation time. |
| `project_ref`, `project_revision` | Scope and revision observed at freeze. |
| `sources[]` | Qualified source ref, version/digest, observation time, required/optional status, and authorized resolver. |
| `coverage[]` | Expected source/scope, availability, freshness threshold, actual observation time, and named omission. |
| `claims[]` | Claim ID, kind, text/artifact span, source refs, and support state. |
| `boundary` | Data classes and permitted material placement as resolved by existing policy. |

Claim kinds are `observation`, `inference`, `proposal`, `domain_decision`, `execution_result`, and `outcome_measure`. Support states are `source_linked`, `reviewed_supported`, `disputed`, and `unknown`. A syntactically valid citation sets at most `source_linked`. It does not establish entailment or acceptance.

Freeze and retention must coexist. The manifest records exact revision/digest; permitted content snapshots use existing immutable material storage with the source's disclosure class. A deleted or revoked source cannot remain readable through a snapshot, prompt, result preview, search entry, or export. Where content cannot lawfully be retained, store an unavailable/tombstone marker and minimal permitted audit metadata. “Reproduce this old run” may then correctly refuse.

## 3. Assignment definition

The owner supplies intent and requested bounds. The service resolves canonical references, capabilities, actual authority, and routing evidence. The request cannot submit an authenticated principal, warrant, raw executable, or unvalidated pane path.

| Field | Required meaning |
|---|---|
| `assignment_id`, `revision`, `schema_version` | Stable ID, monotonically increasing immutable definition revision, version 1. |
| `project_ref`, `title`, `outcome` | Existing Project and concrete requested result. |
| `origin` | Manual gesture, Thread message, Watch effect, or schedule occurrence, with source identity. |
| `template_ref`, `template_revision` | Versioned recipe/template when used; absent for a fully specified manual assignment. |
| `manifest_id` | Frozen authorized evidence manifest. |
| `constraints[]` | Explicit invariants and non-goals; source-linked where derived from an accepted decision. |
| `worker_profile_ref` | Registered adapter/profile, resolved server-side. |
| `requested_capabilities[]` | Requested read/effect classes and named scope; intersected with actual rights. |
| `requested_destination` | Canonical local result target and any exact configured external destination. |
| `limits` | Deadline, maximum attempts, model calls, child count/depth, concurrency, and optional enforceable spend cap. |
| `acceptance_checks[]` | Stable check ID, type, mandatory flag, criterion, and verification method. |
| `review_policy` | `owner_review` or a previously configured deterministic acceptance policy. Model judgment alone cannot grant organizational approval. |
| `related_commitment_refs[]` | Existing actions/commitments the result supports; no automatic completion by association. |
| `supersedes_revision` | Previous definition revision when scope changed. |

Illustrative intent payload, for specification only:

```json
{
  "schema_version": 1,
  "command_id": "sample-request-001",
  "expected_revision": 0,
  "project_ref": "project:sample-platform-migration",
  "title": "Check the first service migration",
  "outcome": "Produce a reviewable compatibility assessment and proposed patch if the evidence supports it.",
  "context_refs": ["note:sample-accepted-constraints", "artifact:sample-interface-map"],
  "constraints": ["Preserve the published API", "Do not merge or publish"],
  "worker_profile_ref": "profile-selected-by-owner",
  "requested_capabilities": ["repository.read", "worktree.edit", "checks.run", "artifact.create"],
  "limits": {"wall_seconds": 1800, "max_attempts": 2, "max_children": 0},
  "acceptance_checks": [
    {"id": "api", "kind": "deterministic", "mandatory": true, "criterion": "Existing API compatibility checks pass"},
    {"id": "rationale", "kind": "owner_review", "mandatory": true, "criterion": "Findings link to source constraints and explain any unsupported assumption"}
  ],
  "review_policy": "owner_review"
}
```

The illustrative capability names are proposed semantic classes. An adapter must map them to registered operations or refuse them. Sending this JSON to a current endpoint is not supported by this document.

## 4. Lifecycle and completion

Definition lifecycle: `draft -> ready -> active -> review -> accepted`. A definition may be `closed` with a named reason such as abandoned, failed, cancelled, or replaced. `ready` means structurally complete, not authorized to execute. Launch admission determines authority. Definition revisions never mutate after admission; a replacement retains its predecessor and explicitly cancels or lets old work finish under old terms.

Run display states are projections of native/kernel facts: queued, running, awaiting input, awaiting review, failed, cancelled, or indeterminate. They do not create an independently mutable kernel state machine. A successful worker attempt produces a candidate result. The execution parent can finish with a receipt while business acceptance remains pending in the review record.

| Command/event | Precondition | Result |
|---|---|---|
| Prepare definition | Valid Project and requested scope | Draft plus missing prerequisites; no dispatch. |
| Run | Valid immutable definition, compatible adapter, derived authority | Durable operation and run link before dispatch; async handle. |
| Worker blocks | Typed blocker tied to run/generation | One attention item; no synthetic completion. |
| Owner answers | Matching live run and blocker revision | Existing delivery path, receipted where consequential; answer does not rewrite frozen scope. |
| Result returns | Matching attempt/generation and live publication fence | Candidate result manifest; begin verification or owner review. |
| Verify | Frozen mandatory criteria and authorized verifier | Check results with evidence; incomplete/failed checks prevent acceptance. |
| Accept | Checks satisfied and applicable domain authority | Acceptance record; related commitments transition only through their own explicit command/policy. |
| Stop | Active work | Revoke future dispatch, signal supported cancellation, retain known effects, reconcile unknown ones. |
| Retry | Prior attempt settled or reconciled, budget remains | New physical attempt under the same definition and preserved logical-effect identity. |

An owner may accept a revised scope only by recording the changed criterion and new revision. An earlier failed mandatory check is not silently waived. Unknown cancellation is indeterminate, never a successful stop.

## 5. Result manifest and verification

The result manifest contains assignment/revision, run and attempt IDs, worker identity standing, input manifest, started/finished times, artifacts, changed refs, repository base/head and worktree identity when supported, check results, unresolved questions, known effects, and receipt refs. Usage records distinguish observed, estimated, and unavailable values.

Each check records `check_id`, `method`, `status` (`pass`, `fail`, `unknown`, `not_applicable`), verifier identity, evidence ref, and observation time. `not_applicable` requires a criterion-specific rationale; it cannot satisfy a mandatory check that actually applies. A worker's prose “tests pass” is not execution evidence.

For the first crew, one coordinator admits a worker and then a separate verifier leaf. Depth is at most one, there are at most two leaves, and their cumulative budget includes retries. Parallel independent read-only checks can be added under the same cap. Dynamic recursive decomposition and arbitrary graph scheduling remain outside R3.

## 6. Authority and execution topology

Manual and scheduled requests share AssignmentService and typed operation codecs. A proposed `assignment.run@1` parent uses the existing parent controller and journal; it cannot bypass immutable route plans or manufacture its own execution warrant. It adds native product lifecycle where required, rather than broadening the existing 60-second Workflow path or teaching the linearizer unsupported graphs.

Effective authority is the intersection of authenticated principal rights, explicit delegation, assignment scope, template scope, adapter capabilities, destination policy, and current control posture. YOLO may authorize eligible configured effects without another prompt. Normal/Secure and exact bounded grants keep their existing semantics. The UI reports the actual basis. Organizational decision ownership is recorded evidence, not a token that grants kernel rights.

External agents run through registered adapters. A worktree is isolation of file changes, not a security sandbox. An adapter lacking enforceable tool/spend/cancellation controls cannot support a recipe that requires those guarantees. That recipe refuses with a named capability gap or uses a scope whose guarantees the adapter can meet. HoldSpeak does not claim control over arbitrary same-user processes.

The initial automatically eligible templates request read/prepare/verify and local artifact capabilities. They carry no external-send capability unless explicitly added through its own proven contract. This is template scope, not a change to global control posture. Editing a template or route must not silently expand an existing schedule's delegated scope.

## 7. Scheduling, concurrency, and failure

Proposed initial pilot limits: two active assignments per hub, one per Project; one worker plus one verifier; 30 minutes per worker and 15 minutes per verifier; two physical attempts per retryable step; a two-hour absolute run ceiling. These are configurable downward or upward only within adapter-supported limits and recorded policy. Preserve narrower existing per-tool limits. A hard monetary cap is offered only where usage can be enforced; unknown CLI billing cannot masquerade as a hard cap.

The same durable scheduler/conductor is extended with leased work. A fire key is derived from recipe ID/revision, Project, and UTC occurrence identity or provider watermark. A unique database constraint admits one logical fire. A database-backed lease plus monotonic generation fences stale workers and result publication. A second process can read the state but cannot dispatch the claimed fire. Lease takeover reconciles existing effects before replacing execution.

Time policy is explicit: store the IANA time zone, compute UTC occurrences, execute once on the first occurrence of a repeated local time, and advance a nonexistent local time to the next valid instant for that date. Missed preparation runs coalesce to one latest relevant run; expired meeting preparation is skipped with a receipt. Notification quiet hours defer delivery, not already-authorized computation. Overlap coalesces a new watermark into at most one successor run and never mutates the active snapshot.

| Failure window | Required recovery |
|---|---|
| Before admission commits | No dispatch. Caller may retry the same command. |
| After admission, before worker claim | Recover the same queued work and immutable definition. |
| After claim, before effect | Resolve lease/generation; dispatch only when prior execution can be excluded. |
| Effect sent, acknowledgement lost | Read back by logical effect identity where supported; otherwise mark indeterminate and do not repeat. |
| Worker returns after stop/replacement | Preserve permitted diagnostic receipt; reject result acceptance and new effects under the old generation. |
| Verification fails | Keep candidate and failure evidence; close or request bounded correction under policy. |
| One provider or notification path fails | Mark its coverage/delivery state; continue independent work. |

Retryable examples: transient connection failure before an effect, bounded provider throttling, or explicit retryable model failure. Non-retryable examples: unsupported capability, revoked authority, invalid input, changed required evidence, failed deterministic acceptance. Exponential retry delays begin at 5 seconds, are capped at 60 seconds, honor provider retry metadata when available, and cannot exceed the absolute deadline. A result of uncertain execution is reconciled, not classified as an ordinary transport retry.

External exactly-once execution is not promised. The supported guarantee is a single logical fire, fenced dispatch, durable evidence of known attempts, and no blind repetition of uncertain effects. Every adapter documents its idempotency/read-back capability.

## 7a. Attention identity and initial ranking

For AA-ATT-001–AA-ATT-003, derive one attention identity from the canonical subject, reason kind, and relevant source revision. Repeated observations of an unchanged unresolved reason update freshness rather than create another business item. Related observations may group under one priority; the group opens its full membership and never loses individual source links.

Initial deterministic order is: (1) unresolved execution/authority interventions, (2) overdue decisions and commitments, (3) a blocker explicitly requiring this owner's input, (4) a decision or commitment due within the configured preparation horizon, and (5) other material changes. Within a class, sort by explicit due time when present, then oldest unresolved observation, then stable subject ID. A missing date sorts after dated items in its class and remains unknown. An unresolved intervention is never demoted solely because its evidence is stale; its coverage problem remains visible.

Five is the default number of opening priority groups, not a storage/query cutoff. The remaining count includes all eligible groups; a separate unresolved-intervention count remains visible when more than five groups compete. Snooze records carry a reason revision and expiry so changed source state can become eligible again. A model may phrase the summary but cannot change eligibility or silently remove a required intervention. Owner preference can later alter ranking only through a versioned, inspectable policy with the same coverage invariants.

## 8. Transformation profile and authority

The optional architecture profile extends Project identity with typed fields: problem, outcome, vision/principle refs, affected capability/team refs, explicit sponsor and decision owner, stage, decision refs, rollout refs, exception refs, and measures. Avoid a miscellaneous `context_json` payload as the authority for these fields.

Stage sequence is Seed, Framed, Tested, Authorized, Enabled, Rolling out, Governed, Proven, Retired. Gates respectively require a clear problem/outcome, evaluated options and evidence, an actual authorized decision/sponsor, usable enablement, an active rollout with owners/measures, observable controls and an exception path, and measured outcomes. Retirement records reason, successor, and remaining obligations. A regression can reopen the appropriate prior stage with history retained. Stage authority is owner-entered or evidenced from the designated record; agents can propose transitions.

R1 needs only outcome, scope, decision owner, and authority locator, reusing existing fields or links. R4 introduces the richer profile. Sponsor and team information is explicit business metadata; confidential relationship content remains in People and is referenced only through permitted projections.

If an existing Vision Control workspace or another structured portfolio already owns these initiative fields, bind the Project to that initiative's stable locator and observed revision. Use an adapter/projection rather than create a competing editable initiative. The authority mapping declares which fields are local working context and which come from the approved portfolio. Updating authoritative fields becomes an explicit reconciliation proposal; an unavailable portfolio leaves an honest last-observed projection. The lifecycle vocabulary above does not authorize HoldSpeak to advance that external workspace automatically.

An adoption measure includes metric definition/revision, unit, eligible population and exclusions, numerator, denominator, coverage, observation window, evidence refs, target, and owner. Zero denominator produces `not_applicable`; incomplete coverage produces `partial`, not a falsely precise percentage. A changed population definition creates a new metric revision. Outcomes such as reduced change lead time or incidents remain distinct from adoption of a practice.

## 9. Proposed driver operations

These are design names to register through existing transport patterns, not claims about today's route roster.

| Service verb | Proposed HTTP/MCP exposure | Semantics |
|---|---|---|
| `prepare_assignment` | POST `/api/assignments`; `assignment.prepare` | Validate intent, persist definition, return missing prerequisites. |
| `get_assignment`, `list_assignments` | GET `/api/assignments/{id}` and collection; `assignment.get/list` | Bounded scope-filtered projections. |
| `revise_assignment` | POST `/api/assignments/{id}/revisions`; `assignment.revise` | New immutable definition revision with explicit prior-run disposition. |
| `run_assignment` | POST `/api/assignments/{id}/runs`; `assignment.run` | Admit and return a handle within two seconds; work proceeds through the conductor. |
| `answer_blocker` | POST `/api/assignments/{id}/answer`; `assignment.answer` | Requires a live supported delivery adapter; stale blocker conflicts. |
| `stop_assignment` | POST `/api/assignments/{id}/stop`; `assignment.stop` | Fence dispatch and reconcile cancellation. |
| `review_assignment` | POST `/api/assignments/{id}/reviews`; `assignment.review` | Record criterion results and accept/request changes under applicable authority. |
| `configure_assignment_recipe` | Existing automation configuration surface plus registered recipe binding | Configure trigger, template revision, scope, and delegated limits through the same service. |

Commands use stable command ID and expected revision, and return the existing Project result-envelope conventions with versioned assignment extensions. Domain facts, operation IDs, changed refs, warnings, and errors remain structured. Do not add optional ambiguous fields to the current envelope without versioning its contract and consumers.

Typed errors include missing required context, stale revision, idempotency conflict, unsupported adapter capability, assignment not runnable, authority expired/revoked, budget exhausted, worker unavailable, result mismatch, acceptance failed, and execution indeterminate. Map them to existing error vocabulary where equivalent. Suggested HTTP status mapping: malformed 422, unavailable dependency 503, missing record 404, authentication/authority 401/403, state/revision conflict 409; an admitted failed run remains a readable result rather than becoming a lost HTTP error.

Events project journal/domain facts with stable event identity, cursor, aggregate/ref revision, causation, and outcome. WebSocket delivery is resumable projection only. MCP or Thread calls must return the asynchronous run reference rather than hold a tool call open for the whole assignment. Missing live-runtime callbacks are advertised as unavailable. Token-bearing locators and raw prompts must not appear in general event payloads.
