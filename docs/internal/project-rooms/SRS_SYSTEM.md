# Project Rooms — integrated system requirements specification

Status: Draft for implementation planning
Version: 0.1
Date: 2026-08-30
Owner: HoldSpeak product owner
Vision epic: [#514](https://github.com/karolswdev/HoldSpeak/issues/514)

## 1. Purpose

This SRS defines the smallest coherent system that can validate HoldSpeak's Project Rooms thesis while establishing reusable boundaries for later expansion.

The V0 system shall let a local power user describe one consequential outcome, install tested Watches through an interview, understand material change, allow a local YOLO Steward to perform useful follow-through, and return to an evidence-linked Project state and update.

The goal is not generic project management and not MCP conformance. The goal is a closed operational loop:

```text
INTERVIEW → INSTALL WATCHES → OBSERVE → DISTILL DELTA
          → ACT IN YOLO → VERIFY → UPDATE
```

## 2. Product decision and wedge

Project Room is the durable operating surface. The Interview installs its operating contract. Watches define what it continuously notices. Delta is the recurring reason to open it. Steward is the leverage. Update is the portable outcome.

The V0 wedge is:

> Describe the outcome and what must not escape notice. HoldSpeak installs a tested monitoring system, continuously understands the Project, shows only what materially changed, handles obvious follow-through in local YOLO mode, and prepares an evidence-linked update.

A universal Project data model without this closed loop is insufficient for validation.

## 3. Stakeholders and operating posture

| Stakeholder | V0 role |
|---|---|
| Local owner / power user | Creates, configures, reviews, and delegates a Project. |
| Project Steward | Project-owned durable execution loop that may bind an existing Agent/Recipe for inference and focused capabilities. |
| Design partner | Later V1 user validating transfer beyond the owner. |
| External MCP client | Optional local driver of the same Project service; not a separate authority. |

V0 assumptions:

- Web is the primary product surface.
- The deployment is local and single-owner.
- YOLO is an intentional owner-selected/default power-user posture.
- Existing local stdio MCP is sufficient for V0.
- Remote, multi-user, enterprise authorization is V2+.
- Swift and native mobile work are out of scope.

## 4. Existing-system decisions

- **AD-PRJ-001:** `projects.id` remains the canonical Project identity.
- **AD-PRJ-002:** `ProjectService` graduates into the transport-neutral Project Room application boundary.
- **AD-PRJ-003:** `ProjectMemoryCore` graduates into the Project Room Web feature; it is not replaced by an unrelated page.
- **AD-PRJ-004:** Meeting, Decision, People, Door, Thread, Note, Workbench, Agent/Recipe, Calendar, Automation, and delivery systems retain their own truth. Project stores relationships and Project-owned assessments, not copies.
- **AD-PRJ-005:** `ProjectStewardService` [proposed] owns the Steward's durable run/step lifecycle. It MAY bind an existing Agent/Recipe and MUST reuse suitable conductor heartbeat, inference-routing, and event-broadcasting patterns. Workbench and Cadence are evidence/attention collaborators, not the Steward engine or Project authority.
- **AD-PRJ-006:** MCP is an adapter over `ProjectService`, not an orchestration runtime or privileged parallel implementation.
- **AD-PRJ-007:** V0 fixes reliability defects that block the closed loop. It does not pause for remote-security or full-protocol programs.
- **AD-PRJ-008:** Project-owned records use explicit typed schemas and lifecycle. The existing untyped `context_json` MUST NOT become the dumping ground for the operating model.
- **AD-PRJ-009:** Project creation is an outcome-and-Watch interview that compiles durable structured contracts; Blank is an escape hatch.
- **AD-PRJ-010:** Existing `connector_watches` is graduated to `WatchSpec@1`. Watch providers (local domain, connector pack, or MCP/app) are adapters; they do not own Watch, Project, Delta, or scheduling truth.

## 5. System context

```text
 Web interview/Room ─┐
                     ├─► Project setup/application services ─► Project store/reviews
 local MCP project.* ┘                 │                         │
                                       │                         ├─► Delta/Updates
 Provider adapters ─► Watch service ───┼─► observations/events ──┤
 MCP app | connector | local domain    │                         └─► YOLO Steward runs
                                       │
                                       └─► canonical citizen services
                                           Meeting/Decision/Door/Workbench/etc.
```

## 6. Release definitions

### V0 — owner validation slice

One real Project can be created through the interview, leave setup with a tested active Watch, be reviewed for material Delta, be acted upon by one YOLO Steward, and become an evidence-linked update.

### V1 — design-partner product

Multiple Project templates and source adapters, stronger Map/Timeline, configurable Steward recipes, durable notifications, and proof that another power user reaches recurring value.

### V2+ — ecosystem and shared deployment

Current remote MCP transport/protocol surface, scoped identity, multi-user collaboration, portfolio views, third-party extension packaging, and enterprise administration.

## 7. Integrated functional requirements

### 7.1 Project identity and room

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYS-001 | MUST/V0 | The system MUST let the owner create, open, edit, archive, and restore a Project from Web without CLI or direct API work. | T,D |
| SYS-002 | MUST/V0 | A Project MUST define name, outcome, lifecycle, posture, review cadence, and optional description; blank outcome MUST be visibly incomplete. | T,D |
| SYS-003 | MUST/V0 | Opening a Project Desk object MUST open one scoped Project Room window through the existing Desk application/compositor model. | T,D |
| SYS-004 | MUST/V0 | The Project Room MUST expose Now, Delta, Timeline, Updates, and Stewardship as coherent views of the same Project revision. | T,D |
| SYS-005 | SHOULD/V1 | Map and module/template customization SHOULD be available after the closed loop is validated. | T,D |
| SYS-006 | MUST/V0 | Primary Project creation MUST ask the outcome and what HoldSpeak should notice, then recommend concrete Watches from real provider/native capability. | T,D,U |
| SYS-007 | MUST/V0 | Setup MUST compile an inspectable source/scope, condition, cadence, and action contract and show it before activation. | T,D |
| SYS-008 | MUST/V0 | A flagship Project MUST leave setup with at least one live-tested Watch; Blank/manual-only activation MUST remain an explicit escape hatch. | T,D |

### 7.2 First-class citizen composition

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYS-010 | MUST/V0 | The owner MUST be able to link and unlink existing Meetings, Decisions, Notes/Artifacts, Door/Follow-Through items, Workbenches, Agents/Recipes, Threads, Watches, and delivery evidence where those citizens support qualified refs. | T,D |
| SYS-011 | MUST/V0 | Project relationships MUST identify source ref, relationship verb, source/provenance, and timestamps. | T,I |
| SYS-012 | MUST/V0 | Project views MUST open the canonical citizen rather than render an editable copy of its authority. | T,D |
| SYS-013 | MUST/V0 | Project action/follow-through views MUST write through to existing Follow-Through/action authority; no Project-only task status may drift from it. | T,I |
| SYS-014 | SHOULD/V1 | Automatic link proposals SHOULD remain distinguishable from owner-created/accepted links. | T,D |
| SYS-015 | MUST/V0 | A Watch MUST retain canonical observation/query/baseline/cadence authority while Project stores its qualified relationship, semantic role, and resulting Project assessments. | T,I |

### 7.3 Delta and review

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYS-020 | MUST/V0 | The system MUST compute Delta from a durable prior accepted review cursor to a frozen current source manifest; it MUST NOT define Delta only as “latest two meetings.” | T,I |
| SYS-021 | MUST/V0 | Delta MUST include relevant new/changed/closed decisions, commitments/actions, linked evidence, risks, dependencies, milestones, and source freshness available in V0. | T,D |
| SYS-022 | MUST/V0 | Every Delta item MUST state kind, change, observed time, source ref(s), and whether it is observed fact, Project-owned assessment, or model proposal. | T,I |
| SYS-023 | MUST/V0 | Accepting a review MUST advance the cursor atomically and retain the reviewed Delta for later inspection. | T,I |
| SYS-024 | MUST/V0 | Re-running from the same frozen manifest and Project revision MUST be idempotent. | T |
| SYS-025 | MUST/V0 | Missing, stale, or failed sources MUST appear as degraded coverage; they MUST NOT silently produce “no change.” | T,D |

### 7.4 Watches and provider capability

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYS-026 | MUST/V0 | A Watch MUST preserve owner intent separately from its versioned provider scope/query, normalized condition, trigger, and typed actions. | T,I |
| SYS-027 | MUST/V0 | Provider connection, discovery, read, subscription, and effect capabilities MUST be inspected and reported separately; connection MUST NOT imply Watch readiness or write ability. | T,D |
| SYS-028 | MUST/V0 | MCP/app, connector-pack, and local-domain providers MUST normalize through the same Watch adapter contract. Arbitrary tools MUST NOT become Watches without identity, query, cursor, and normalization semantics. | T,I |
| SYS-029 | MUST/V0 | Watch evaluation and effects MUST be durable, idempotent, bounded, and independently recoverable; identical observations MUST NOT repeat effects. | T |

### 7.5 Project-owned operating records

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYS-030 | MUST/V0 | Project MUST support typed milestones, risks, dependencies, signals, and updates with stable IDs, lifecycle, ordering, revision, and provenance. | T,I |
| SYS-031 | MUST/V0 | The owner and Steward MUST be able to create or update these records through the same application service used by Web and MCP. | T |
| SYS-032 | MUST/V0 | Model-generated records MUST begin as proposals unless a YOLO action explicitly invokes an effect tool whose product contract directly applies the change, with the action recorded as a committed proposal in the same transaction. | T,I |
| SYS-033 | MUST/V0 | Accepted Decisions and existing commitments MUST be linked, not re-authored as Project-owned substitutes. | T,I |
| SYS-034 | SHOULD/V1 | Workstreams and module-specific record schemas SHOULD be added without changing Project identity or relationship semantics. | T,I |

### 7.6 Steward and YOLO execution

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYS-040 | MUST/V0 | (a) The owner MUST be able to configure one Project Steward. (b) The owner MAY optionally bind an existing Agent/Recipe for inference/capabilities. (c) The Steward MUST receive a focused tool palette. (d) Manual `run_once` MUST ship before scheduling; an unattended trigger MUST be enabled for the Gate A dogfood. | T,D |
| SYS-041 | MUST/V0 | In YOLO mode, eligible configured Steward tools MUST run without per-action confirmation prompts. | T,D |
| SYS-042 | MUST/V0 | One Steward run MUST observe, compute Delta, perform at least one useful configured action, verify the result when a read path exists, record activity, and draft an update. | T,D,U |
| SYS-043 | MUST/V0 | Pause and Stop MUST be available from the Project Room and MUST not depend on the Steward's model response. | T,D |
| SYS-044 | MUST/V0 | The Project Room MUST show last run, current state, next trigger, actions/results, errors, and whether an identity/receipt is durable or degraded. | T,D |
| SYS-045 | MUST/V0 | Repeated identical failure MUST be bounded; the Steward MUST not create unbounded retries or duplicate follow-through. | T |
| SYS-046 | SHOULD/V1 | Governed Observe/Propose/Prepare/Execute modes MAY coexist with YOLO without changing the Project tool contracts. | T |

### 7.7 Updates

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYS-050 | MUST/V0 | The system MUST draft an owner-ready update from a frozen Project revision, accepted records, and explicit source manifest. | T,D,U |
| SYS-051 | MUST/V0 | The update MUST distinguish progress, decisions, risks, dependencies/blockers, next actions, and source-coverage caveats. | T,D |
| SYS-052 | MUST/V0 | Every factual claim in a generated update MUST carry or resolve to source refs; unsupported language MUST be visibly marked or omitted. | T,I |
| SYS-053 | MUST/V0 | Drafting and marking/publishing an update MUST remain separate operations. V0 MAY support copy/export rather than a remote publisher. | T,D |
| SYS-054 | MUST/V0 | Prior updates MUST remain browsable and tied to the Project/review revisions that produced them. | T,D |

### 7.8 Driver interfaces

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| SYS-060 | MUST/V0 | Web and MCP `project.*` operations MUST call the same Project application service. | T,I |
| SYS-061 | MUST/V0 | The MCP family MUST provide the V0 reads/effects needed to complete the same closed loop as Web. | T,D |
| SYS-062 | MUST/V0 | Project tools MUST return structured JSON-serializable results with stable result kind, Project revision, changed refs, and error code where applicable. | T,I |
| SYS-063 | MUST/V0 | The local stdio/owner posture MAY remain the supported V0 MCP transport. | I |
| SYS-064 | LATER/V2 | Remote HTTP identity/scopes and full current-protocol ecosystem work MUST NOT block V0. | I |

## 8. Quality requirements

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| NFR-001 | MUST/V0 | A local Project Room with 500 linked records MUST show its cached shell within 500 ms and useful content within 2 s on the supported development machine. | T,D |
| NFR-002 | MUST/V0 | Lists and timeline reads MUST be bounded and deterministically ordered. | T |
| NFR-003 | MUST/V0 | An unrelated subsystem initialization failure MUST NOT prevent Project identity, Project reads, or an unrelated Project tool from operating. | T |
| NFR-004 | MUST/V0 | All accepted state changes MUST be transactionally durable and idempotent where the caller supplies an idempotency key. | T |
| NFR-005 | MUST/V0 | The Web surface MUST meet keyboard and WCAG 2.2 AA requirements specified in the Web SRS. | T,I |
| NFR-006 | MUST/V0 | The system MUST expose honest empty, stale, partial, failed, and stopped states. | T,D |
| NFR-007 | MUST/V0 | New schema MUST follow the repository's additive reconciliation/backup policy and preserve current Project identities and relationships. | T,I |
| NFR-008 | SHOULD/V1 | Core Project contracts SHOULD be generated or shared across Python/TypeScript/MCP to prevent drift. | T,I |
| NFR-009 | MUST/V0 | Every consequential operation the Project Room performs — Watch evaluation effects, Steward step effects, provider reads that cross egress, and model invocations — MUST be admitted through the kernel before it acts and MUST end in a terminal receipt (Constitution Art XI). | T,I |

## 9. Explicit V0 non-goals

- Generic portfolio/PMO dashboards.
- Replacing Jira, GitHub, Calendar, or other source systems.
- A complete Gantt/critical-path engine.
- Arbitrary user-defined schemas or a plugin marketplace.
- Full Map visualization before Delta/Steward value is proven.
- Remote MCP, multi-user collaboration, enterprise administration, or approval-heavy policy design.
- Native Swift/mobile implementation.
- Completing all of DeskOS issue #510 before Project Room work begins.

## 10. V0 acceptance scenario

The V0 release is accepted only when this scenario passes with a real owner Project:

1. The owner describes the intended outcome and what HoldSpeak should notice.
2. Setup discovers native/provider capability, proposes a precise Watch, performs a live non-mutating test, and shows current matching entities.
3. Activation atomically creates the Project operating contract, establishes a baseline without false historical events, and opens populated Now.
4. A real source change evaluates one Watch condition and appears as evidence-linked Delta.
5. Without confirmation prompts, the Steward performs one useful non-simulated action, verifies it where possible, and records legible activity.
6. The Steward drafts an update whose claims link to evidence and whose caveats name stale/missing sources.
7. The owner edits rather than reconstructs the update and accepts the review.
8. Reopening the Room shows the advanced cursor, prior update, active Watches, current state, and next evaluation/Steward trigger.

## 11. Validation exit criteria

Technical completion alone does not validate the product. V0 proceeds to V1 only if dogfooding demonstrates the thresholds in the Product SRS, including repeat use, meaningful time saved, useful autonomous action, and update editability.

## 12. Requirement ownership

| Area | Normative detail |
|---|---|
| Product jobs, hypotheses, metrics | `SRS_PRODUCT_VALIDATION.md` |
| Web IA, interactions, states, a11y | `SRS_WEB_EXPERIENCE.md` |
| Domain, schema, service, Delta, MCP, Steward | `SRS_DOMAIN_DRIVER.md` |
| Outcome interview, provider discovery, Watches, cadence/actions | `SRS_PROJECT_INTERVIEW_WATCHES.md` |
