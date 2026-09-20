# Philo — make HoldSpeak understandable

**Status:** proposed PR delivery plan; not product canon and not a completed audit.
**Owner:** Astra. **Checker:** Muad'Dib; [initial check](checks/plan-muaddib.md) and [round 2](checks/plan-muaddib-round2.md).
**Publication verdict:** RATIFY-WITH-CONDITIONS, publication conditions applied.
This is not a merge verdict.
**Request:** the owner's two research briefs supplied on 2026-09-19:
capability audit/documentation-agent specification, and Workbench design/SRS.
[Exact request](briefs/owner-request.txt), [audit brief](briefs/capability-audit.txt),
and [Desk brief](briefs/workbench-design-srs.txt) are preserved as research inputs.
Their hashes are in the snapshot. Imported citations remain unverified.
The complete request retains conversational context; separate exact extracts
give each research lane a fixed input. These are archived inputs, not competing
maintained documents. The verbatim request is included in this public repository.
The [source checklist](source-checklist.md) preserves each section for later disposition.
**Baseline:** [snapshot.json](snapshot.json). Evidence describes that commit,
not an installed release or the owner's current desk.
**Lane:** the owner explicitly requested an independent clone in place of a linked worktree.
Independent clone `~/dev/tools/HoldSpeak-Philo`, branch
`docs/holdspeak-philo`. No work in the owner's main checkout.

## The outcome

One reviewable PR should let the owner understand the system in five minutes,
let a contributor find a capability's actual implementation, and let an agent
change it without inventing a competing contract. The two briefs supply the
research questions. Their claims and imported citation markers are not proof.

The proposed organising loops are Speak → Type, Meet → Understand,
Context → Think, and Propose → Approve → Act. Test them against actual paths.
Do not force every subsystem into them or add a confirmation click solely to
make the last loop look uniform.

The Tuesday question is: can the owner find what HoldSpeak can do, understand
what is available, and complete a useful architect's job with less effort?
The owner has been asked which outcome should lead. Until answered, use
understanding the system as this documentation lane's first outcome. Actual
usability still requires an observed job; documentation cannot certify it.

## Governing sources and the live lane

The [Seven Tenets](../CONSTITUTION.md#the-seven-tenets-the-owners-charter-2026-09-19)
come first: avoid needless safety machinery; serve first use; reduce interfaces;
use ASD-STE100 for product text and user guides; compose the component framework;
preserve Workbench behaviour; serve the Senior Software Architect's work.
Then apply [Two Brains](../TWO-BRAINS.md), [UX Canon](../UX-CANON.md),
[Orchestration](../ORCHESTRATION.md), and [working agreements](../../../CLAUDE.md).

Normative authority and evidence of implementation are separate. The
Constitution says what must be true. Executed code and assertions show what is
true. A conflict is recorded, not resolved by calling either source irrelevant.

[Phase 201](../../../pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md)
already targets one real meeting result. Philo does not change its stories,
claim its observations, or make completion of this documentation programme a
dependency for that sitting. Its runtime and face files remain owned by those
lanes. Do not edit Phase 201 status or the shared roadmap README in this opening.
A later checked charter must define Philo story ownership and serialize any shared
roadmap metadata edits. Do not change the Current phase pointer to Philo.
Reconcile changes from main before finalising source anchors.

## Corrections to the supplied premises

These are initial source observations, not a comprehensive audit.

| Premise to test | Initial evidence | Consequence for Philo |
| --- | --- | --- |
| Kernel is mainly an accounting journal | Constitution Article XI; `holdspeak/kernel/broker.py`, `admission.py`, `executor.py` | Document admission, authenticated authority, execution claims and receipts, as well as observation. Do not propose a replacement lifecycle before reading this code. |
| Approval means a separate confirmation for every action | Constitution XI.4 says the owner's gesture is approval | Trace authority per operation; distinguish explicit gesture, bounded delegation and separate proposal review. |
| The system needs its first capability census | `docs/internal/INVENTORY-2026-09-19.md` and its appendices already exist | Reconcile their dated findings and checks; do not repeat their counts as current facts. |
| API and docs drift checks must be invented | `docs/API_SURFACE.md`, `scripts/gen_api_surface.py`, `scripts/gen_mcp_sidecar_doc.py`, `scripts/check_docs.py`, `CONTRIBUTING.md` | Extend existing extraction and CI; keep one owner per generated reference. |
| Workbench needs a new architecture | `docs/internal/DESK_GRAMMAR.md`, `web/src/desk/surface/contract.md`, `docs/internal/ARCHITECTURE_WEB_FRONTEND.md` | Extract and reconcile the existing contract before designing missing behaviour. |
| Beta metadata proves maturity | `pyproject.toml` says 0.4.0/Beta; the Seven Tenets say not even pre-alpha | Record the conflict. Separate packaging label, release availability, code presence, tests and observed usability. |

## One PR, reviewable in parts

Use one umbrella draft PR at the owner's request, with separate commits and
review checkpoints. This is an explicit grouping choice, not permission to
flip multiple roadmap stories in one commit. Each story still passes its own
Delivery Workbench gate. The initial proposal commit ships no completed story.

| Part | Deliverable | What allows it to close |
| --- | --- | --- |
| 0. Reconcile | Snapshot, document ownership/disposition map, contradiction ledger, full brief coverage checklist | Each source section has a disposition; existing docs are kept, consolidated, parked or historical; both brains check the scope. |
| 0a. First useful slice | Trace Meet → Understand read-only; write the first five-minute guide | Identify capture, summary request, actual routing, stored result and retrieval; clearly mark unverified behaviour. Do this before widening the census. |
| 1. Establish reality | Source census, capability/domain/component/integration/platform registries, kernel and authority deep dives | Entries carry verified source anchors, assertions inspected, execution status and unknowns; no capability is promoted by prose alone. |
| 2. Explain | Extend the first guide with workflow maps, subsystem contracts, operations and recovery guidance | One small navigation tree; one contract owner; DOCS_STYLE editorial review and existing navigation/drift checks. |
| 3. Specify the Desk | Existing component catalogue, portable interaction contracts, requirements matrix, annotated wide/compact artboards | Current, partial, missing and proposed behaviours are distinguishable; requirements have concrete acceptance criteria. |
| 4. Keep it current | Lightweight schemas, deterministic generation, path/reference/drift checks, focused repo skills, CI reuse | Deliberately invalid fixture data fails; regenerated output is stable; paths alone are never reported as proof of behaviour. |
| 5. Review | Hostile claim audit, remaining unknowns, executive report, both verdicts | Relevant checks run; no unclassified failures or invented observations; merge-base changes reconciled. |

The first slice is **Meet → Understand**, aligned with Phase 201's path but
read-only here. It can reveal gaps without repairing the active lane's files.
Each part receives a separate Muad'Dib check under `checks/`, before it is
acted on. Final counsel checks integration and changed anchors, not every part
for the first time. Evidence pins commit plus symbol and line.

| Lane | Work | Owner | Checker | Location | Branch |
| --- | --- | --- | --- | --- | --- |
| Philo proposal | Initial scope only; no story completed | Astra | Muad'Dib | HoldSpeak-Philo clone | docs/holdspeak-philo |

Before deliverable implementation, author and check the roadmap charter and
story ownership. This planning commit is an atomic non-story proposal under
PMO-CONTRACT. No Phase 201 record changes are needed for it. Muad'Dib checks
through the CLI here; his gitignored worker configuration is absent, so no
Muad'Dib implementation-worker lane is claimed. Astra's audits use Luna xhigh.

No fixed person-week estimate yet. Measure the first fully traced vertical
slice and inventory size, then estimate the remaining work. The source briefs'
calendar chart and estimates are hypotheses, not a delivery commitment.

## Coverage of the two briefs

The final audit must account for each row below; this plan does not mark them
complete. Exact filenames are chosen after the ownership audit. Equivalent
existing documents are preferred to creating competing truth.

| Research area | Required result |
| --- | --- |
| Repository and history | Classified tree, manifests, architectural dependencies, strategic history, snapshot and canonical/historical/generated document index |
| Capabilities | Positive and negative capabilities; status, exposure, surfaces, platforms, ingress, output, storage, API, config, dependencies, boundary, effect, authority, failure and evidence |
| Domain and storage | Real entities versus projections/services/concepts; relationships, lifecycles, migrations, non-SQLite files, secrets, backup/restore and schema refusal |
| Kernel | Responsibilities and exclusions, structures, state machine, admission, identity, parent/child, journal, execution, restart, cancellation, unknown, destination and receipt semantics; proposed ADR only for a demonstrated gap |
| Dictation | Key/audio to delivery, all optional transforms, learning/replay, wake/commands, browser/remote ingress, failure and platform branches |
| Meetings | Capture/import through intelligence, source-derived complete plugin roster, typed outputs, decision/action lifecycle, aftercare and external actions |
| Models | Registry, capabilities, assignments, readiness, frozen plans, secrets, routing, attempts/fallback, context limits, cancellation, mesh and receipts |
| Authority and security | Separate data/compute/authority/secret/audit boundaries; actual side-effect paths; control modes; data-egress table; gaps without a security redesign |
| Agents and integrations | Agent/Thread/Interview/Workflow/MCP distinctions, Coder observation/replies/Gate, GitHub/Slack/OS actions, connector and actuator development |
| Companions | iPad implementation versus distribution, typed clients and storage; AIPI firmware/bridge/transport, pairing, auth and disconnect behaviour |
| Operations | Doctor checks, install/upgrade/recovery, logs, targeted troubleshooting trees and evidence-based platform matrix |
| Frontend census | Routes, GL/DOM composition, API/auth/RuntimeBus, stores/persistence, tokens/sprites, component props/consumers, verbs/drop/Info, guards and CI |
| Workbench principles | Primary-source historical principles, modern adaptations and product rules kept separate; adopt/modernise/reject matrix |
| Desk interaction | Window physics/constants, focus, selection scopes, keyboard, menus, commands, drag alternatives, motion, compact layout, errors/recovery |
| Design system | Atomic taxonomy over existing components, token graph, state/ARIA/input contracts, themes, localisation and real-content mockups at 1440 and 393 |
| SRS | IDs, rationale, authority, state/data ownership, HTTP/events, measurable NFRs with environment and method, traceability, risks, delta roadmap and acceptance |
| Desktop | Bounded host interface and proposed Electron/Tauri evaluation ADR; retain both prototype requests in the follow-up list |
| Maintenance | Single-source registries/schemas, generated coverage and API references, focused skill index, CI checks, hostile audit and executive report |

Required diagrams: component and deployment maps; trust boundaries; dictation,
meeting, actuator, Agent, Coder/Gate, assignment and mesh sequences; restart;
domain ERD; frontend composition; plugin/connector lifecycles; window/focus and
drag state machines; traceability and delivery order. Each gets prose, source
anchors and an explicit implemented/proposed label.

Required artboards: populated spatial/list Desk, selection/context menu,
drawer, overlapping windows, switch/expose, Speak, meeting review, Thread,
Agents, Settings, Info, valid/invalid drag, working/refusal, command palette,
and system shade if retained. Add compact key jobs, high contrast and long-copy
stress. Use the ratified canvas workflow. Any exported proposal outside it must say
"proposal, not ratified, not buildable". Keep current-state captures separately.

Skills must cover navigation, verification, kernel, dictation, meetings,
routing, Desk, security, plugins, connectors, API clients, troubleshooting,
release audit and doc maintenance. Use the repo's supported format and the
skill-creator instructions when authoring. Keep shared invariants in one
referenced contract; do not copy fourteen subtly different rulebooks.
Repository coding-agent skills are distinct from HoldSpeak runtime Workbench
skills. Neither substitutes for the other. Likewise the Desk operating-surface
SRS is broader than the existing Workbench object RFC; map their overlap first.

## Evidence and registry design

Keep domain-owned sources: product language, HTTP routes, MCP tools, inference
capabilities and Desk verbs already have their own owners. Extend
`tests/unit/doc_claims/registry.py` and `scripts/doc_claims.py` for executable
claims. A cross-domain capability view must reference these sources, not copy
and re-own their definitions. Add only missing product metadata after proving
that no existing home fits. No new top-level registry root is approved yet.
Generated projections have one source and a deterministic generator.

Preserve the requested status terms in the source checklist, but separate their
meaning in the design: maturity, lifecycle, platform limits, release availability,
reachability and exposure. "Internal" belongs to exposure. "Platform limited"
can coexist with "partial". Final fields require the checked schema design.
For this audit, do not assign stable without a recorded owner observation and
supporting test evidence. Package Beta metadata is not evidence of user maturity.

Evidence records source inspection, assertion inspection, focused test execution,
isolated integration observation and owner observation separately. No observation
is inferred from another. Retain exposure (user/operator/developer/integration/
internal) and effect classes (none/local_reversible/local_irreversible/
external_reversible/external_irreversible). Describe configuration-dependent
branches; a boolean cannot establish that every invocation is local or approved.

An evidence reference names the snapshot, path, symbol/line, specific claim,
test assertion and run record where available. A documented test that has not
run is labelled unrun. Count registry coverage separately from behaviour proved.
The stable criterion above applies in addition to an explicit rationale.

Validate unique IDs, enums, references, source/doc/test paths, required egress
and authority descriptions, generated freshness and links. Reuse existing
Mermaid/API checks. Test the validator with small broken fixtures. Do not add a
framework merely to validate a few structured files.

## Scope boundaries and parked implementation

This PR's proposed implementation scope is documentation tooling and agent
knowledge. Product defects discovered during tracing get evidence and a home.
They do not silently become runtime, database, control-policy or UI rewrites.
Proposed design requirements do not amend the Constitution.

Retain these requests as explicit follow-up candidates: both desktop host
prototypes and measurement, desktop packaging/signing/updating, runtime
consolidation, new interaction behaviour, theme/localisation implementation,
platform expansion and comprehensive accessibility remediation. They are not
rejected or represented as complete. Research and proposed contracts fit this
PR; each implementation needs a checked brief with a user job and evidence.

The desktop recommendation remains undecided until both requested prototypes
are measured. No fabricated Tauri/Electron comparison results. Standards and
vendor claims require primary sources inspected during that research. The
pasted research references cannot be cited as if retrieved in this session.

## Verification and delivery

Start with the existing documentation navigation, generated-reference and
copy/drift checks in CONTRIBUTING. For tool changes, collect and run focused
tests and verify negative cases. At the final lane gate run required full
suites in a quiet tree with isolated HOME and the documented browser cache;
never `tests/e2e/test_metal.py`. Record results against the same baseline and
classify failures. Prevent unrelated evidence-image churn from entering commits.

Use isolated runtime fixtures and no writes to the owner's desk. An automated
shot is not an owner observation; a proposed artboard is not a runtime shot.
Changes to faces need the canvas, checks and 1440/393 evidence required by canon.
An owner's live observation remains pending until it actually occurs.

Before ready-for-review: reconcile the snapshot with main, review all absolute
claims, compare inventories to live registrations, inspect tests claimed as
proof, run validation, record Muad'Dib's counsel on built, and list unknowns.
Merge only on verification through the existing gate. Do not merge the initial
draft plan as if the full research package were delivered.

## Existing homes to reconcile first

Start from `docs/ARCHITECTURE.md`, `AUTHORITY.md`, `SECURITY.md`, `MODELS.md`,
`GLOSSARY.md`, `API_SURFACE.md` and the public docs index. Then inspect the
September inventory and its checks, `OPERATIONAL-SURFACE-AUDIT.md`,
`WEB_UI_UX_SYSTEM_AUDIT.md`, the kernel effect census, Desk grammar and the
Workbench RFC. These names are discovery inputs, not guarantees of freshness.
Part 0 must record keep/consolidate/park/historical dispositions, preserve
provenance, and measure the change in navigation. The initial proposal adds no
public navigation entry. The final package should have one clear entry point.

## Initial operational findings

The clean clone has hooks configured. `dw doctor` finds the managed CLAUDE.md
agent-docs block stale at the baseline. This is a tooling finding, not permission
to regenerate governing instructions as unrelated cleanup. Classify whether it
blocks the eventual commit gate and record the outcome.

No runtime tests or owner walks have run for this proposal. No complete census,
capability count, design compliance, release status or security assurance is
claimed. Initial scoped audits and the other brain's check are recorded beside
this file as they arrive.

Read the [initial findings](initial-findings.md) and [review response](checks/plan-astra-response.md).
