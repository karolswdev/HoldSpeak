# HoldSpeak documentation audit report

Status: source audit and specification delivered; verification limits below.
Product source revision:
`675401a857b85336d4acaa8c65383dfc9636e4c8`.

## A. What HoldSpeak is

HoldSpeak is a local-first work hub with voice input, meeting processing,
retained project material, model-backed conversations and operation-specific
execution authority. The Desk presents these as objects and windows. The four
user jobs are Speak → Type, Meet → Understand, Context → Think and
Propose → Authorize → Act. These are navigation concepts, not a claim that every
operation requires a separate approval click.

The owner has not yet completed first use. The package's Beta classifier does
not establish product maturity. This audit does not promote it to Stable.

## B–D. Subsystems, capability inventory and architecture

The source-backed guides cover speech capture/transcription; dictation
transformation and delivery; meetings/plugins/aftercare; project grounding and
memory; Threads/Interview/agents; model assignment and inference; kernel and
executor; authority and credentials; Coder/Gate; connectors and actuators;
companions and Presence; Desk/window/component systems; storage and operations.

The [capability index](../CAPABILITIES.md) is generated from four curated
research shards. Counts describe registry entries at the stated granularity,
not independent end-user features. The repository file, route, schema and
outbound-call censuses are separate mechanical inventories. An inventory hit is
not proof that a feature works. The [coverage report](DOC_COVERAGE.md) separates
existing references, recorded assertions and executed tests.


The curated registry contains **77 capability records**.

| Domain | Records |
| --- | ---: |
| agents | 4 |
| authority | 3 |
| coder | 3 |
| companions | 3 |
| desk | 8 |
| integrations | 4 |
| knowledge | 2 |
| meeting | 20 |
| model | 8 |
| operations | 1 |
| runtime | 3 |
| security | 1 |
| storage | 3 |
| voice | 13 |
| workflows | 1 |

| Status | Records |
| --- | ---: |
| built_unreleased | 4 |
| experimental | 60 |
| internal | 8 |
| partial | 4 |
| planned | 1 |

Other status categories have zero records at this snapshot. This does not prove
that no unlisted or differently grouped capability exists.

The [system architecture](../SYSTEM_ARCHITECTURE.md) and
[integration map](../SYSTEM_INTEGRATION_MAP.md) locate ingress, engines,
authority, durable state and presentation. Existing registries remain runtime
owners; Philo metadata does not become another execution engine.

## E. Kernel conclusion

The kernel is concrete. It admits operations, evaluates authenticated authority,
coordinates execution, journals lifecycle facts and records outcomes. It is not
merely the Process window's journal. Process is a projection; executor recovery
and reconciliation have operation-specific limits. Parent relationships,
warrants and receipts must be read from their actual contracts. See
[KERNEL](../KERNEL.md). No replacement kernel is proposed.

## F. Trust boundaries

Data, compute, authority, secrets and audit records are separate concerns.
Local-first does not mean all branches remain on this machine. Configured
model endpoints, mesh nodes, external connectors, MCP and actuators can cross
boundaries. Voice typing and process launch are effects even when local.
[Security](../SECURITY_MODEL.md), [authority](../AUTHORITY_MODEL.md) and
[integrations](../INTEGRATIONS.md) explain the operation-specific paths.
The lexical [boundary census](boundary-candidates.json) exposes candidates and
its false-positive/false-negative limits; it is not an exhaustive security
certification.

## G–J. Ambiguities and corrected claims

| Finding | Result |
| --- | --- |
| Research calls the kernel accounting-only | Corrected to existing admission/execution/journal responsibilities. |
| All effects appear to need a separate click | Corrected to actual operation-specific gesture, grant and approval semantics. |
| Schema version implies forward-version refusal | The version stamp is informational; storage documentation now says so. |
| Automatic backup is guaranteed before every migration change | Some shape changes occur before the conditional backup; corrected storage/release docs and added a disposable-database assertion. |
| Reconciliation never drops anything | Known legacy table/trigger rebuilds exist; preservation claims are limited to what source proves. |
| Restore test name implies crash-atomic restore | The cited invalid-input test does not prove interruption during file copy. This remains a limitation. |
| Frontend guide recommends retired modal controls | Corrected to current in-place/nonmodal component contracts. |
| Delivery Workbench MCP is described as configured | Corrected the generated rider template; no server was enabled. |
| Workbench grammar is treated as a new redesign | Existing object, window, menu and drop contracts are the design baseline. |
| iPad implementation is treated as a release | Implementation, release evidence and device observation remain distinct. |
| Kernel-owned storage is described as content-free | Parent input_json stores caller content; a real admitted-parent probe confirms a synthetic prompt persists. |
| Startup is described as reaping before route recovery | Actual startup recovers parents, then routes, then projections; projection recovery reaps internally. |
| Record-only stop implies transcript output | No admitted transcriber means no final transcript. |
| Aftercare and plugin provenance checks are conflated | Plugin rejection and defensive segment resolution are documented separately. |
| Provider keys are said never to enter the browser | Temporary password input/request handling is distinguished from persistent Web projections and backend custody. |
| Gate preview is called secret redaction | It is a 120-character JSON prefix; short inputs and prefix secrets can reach the hub. Corrected docs and added a synthetic-marker assertion. |
| MCP bind_host promises a tailnet-only listener | The value is stored and echoed; no listener/peer-address enforcement path exists. Corrected the claim without adding that behavior. |
| MCP verb catalogue promises full Web parity | It is a curated subset; the assertion now checks subset membership. |
| MCP Desk snapshot promises workspace layout | It returns seven record lists; corrected the resource description. |
| SwiftUI iPad pattern governs Web windows | Scoped the preserved document to its iPad reference; current Web contracts remain authoritative. |
| Empty Thread registry runners imply missing commands | The composer/pullout owns execution; the SRS now asks for an executor-ownership contract. |
| Plausible API/test names are accepted as evidence | Validators now check actual paths, symbols, test nodes and explicit method/route pairs. |

Additional source surfaces include Jira/Confluence enrichment, workflow control,
browser speech streaming and Thread tool activity. These are described with
source references rather than silently folded into generic “AI” support.
Desktop hosting, expanded themes/localization and missing direct-manipulation
contracts are proposed requirements. The two host probes are research fixtures,
not released desktop applications.

## K–M. Tests, sensitive gaps and platforms

A test-node reference establishes neither assertion truth nor a passing run.
The registry preserves inspected assertion text and execution status separately.
At most, a matching executed assertion partially evidences a record; it cannot
certify all branches, platforms or authority behavior.

Material limits include crash interruption during restore; automatic-backup
ordering; live provider responses/rate limits; hardware capture and injection;
paired-device failure behavior on real networks; iPad distribution/device use;
AIPI hardware; screen-reader walks; and desktop signing/updating. Existing tests
and source can support narrower claims. The [platform matrix](../PLATFORMS.md)
keeps unknown, not-applicable and setup-dependent states distinct.

The host probes load the same production web bundle from a loopback static
server with API/WebSocket requests refused. Electron evidence shows the
resulting unreachable state with renderer privileges disabled. Tauri records
page load. Neither proves populated Desk parity, startup performance or a
preferred host. See the [ADR](../internal/philo/adr/desktop-host.md).

## N–Q. Delivered artifacts and maintenance

The [delivery file index](delivery-files.json) enumerates changed and added paths.
Generated JSON/YAML inventories collapse by default in GitHub diffs; curated
metadata, prose, tests and source corrections remain ordinary review files.

The [documentation index](../README.md) links user jobs and implementation
guides. The [Philo index](../internal/philo/README.md) links source reconciliation,
SRS/design, requirements, component catalogue, external research, visual
fixtures, host probes, decisions and rollout estimates. The package includes 63 requirement records, 73 renderable Surface component
entries, and 27 authored artboards. Fourteen
[agent skills](../../agent/skills/README.md) cover navigation, verification,
subsystem changes, extensions, operations and documentation maintenance.

Six generated architecture registries and their validation schemas retain
capabilities, components, integrations, domain concepts, trust boundaries and
platforms. A portable Desk workspace schema distinguishes the saved shape from
proposed preferences and host contracts.

Maintenance tools check source/test/doc references, IDs, enums, explicit routes,
authority/egress declarations and generated drift. Mechanical inventories cover
tracked files, manifests, base SQLite schema, document classes, route handlers,
OpenAPI, doctor branches and configuration declarations. CI reuses the existing
docs and test jobs. It does not contact cloud APIs to check documentation.

## Verification record

| Check | Observed result |
| --- | --- |
| Full Python suite, isolated HOME, excluding metal | 11,137 passed, 115 skipped, 19 failed in 1,846.53 seconds. |
| Documentation and reference tests after fixes, including Mermaid rendering | 92 passed in 54.48 seconds. |
| Runtime follow-up on this branch | All ten non-reproducing full-suite failures passed in isolation in 13.05 seconds. |
| Pinned baseline runtime follow-up | Ten passed; four failures reproduced on the unmodified source commit. |
| Complete web quality command | 265 test files and 2,540 tests passed; tokens, architecture, TypeScript, build and bundle gate passed. |
| Focused metadata/API/document-claim tests | 64 passed in 4.25 seconds. |
| Runtime broker/backup/document-claim tests | 57 passed in 5.00 seconds. |
| Documentation navigation | 70 public and 33 internal/skill documents passed. |
| Registries and generated outputs | Four shards, 147 records, zero validation errors; ten generated outputs current. |
| Skills | All fourteen passed the skill-creator format validator. |
| Authored artboard capture | 19 wide and eight compact captures; no console errors or horizontal overflow. |
| Existing executable claim ratchet | 19 claims, zero known-false rows and zero drift after descriptive corrections. |

The first GitHub documentation job exposed filesystem-dependent ordering in
API candidate-test lists. The generator now sorts paths, and a regression test
reverses directory enumeration and checks identical output. The complete
standard-library documentation job was also rerun with Python 3.12 locally;
its captured result is appended to the verification record. This correction
does not change route membership or product execution.

A second clean-run check rejected a Qlippy source reference to a generated build
copy. References now name the tracked asset document and actual React component;
the validator rejects build/environment artifacts even when present locally.
The guide distinguishes bundled assets from rendered glyphs and static label
checks from reachable interactions. The asset document also clarifies that
remote clients still fetch bundled assets over the hub connection.

The full suite was **not green**. Five failures were documentation issues fixed
by this package: retired configuration vocabulary, dependency Markdown picked
up by the link scanner, a roadmap label in a user guide, typographic line-range
dashes, and five Mermaid blocks with parser errors. The 92-test follow-up
covers those repairs. The scanner excludes installed node_modules, not project
documents; retired configuration fields remain in the machine inventory.

Four runtime failures reproduce on the pinned baseline: a scheduled-loop
bytecode assertion, the HS-153 guardrail default, and the HS-171 zero-item badge
at 1440 and 393 widths. Eight attention tests, the real-hub kernel test and
remote Settings at 393 passed in isolation on both baseline and this branch.
Their full-suite failures remain unexplained interference/timing discrepancies;
passing follow-ups do not erase the original result. See the
[baseline investigation](../internal/philo/checks/baseline-failures.md).

The [captured verification record](../../pm/roadmap/holdspeak-philo/phase-1-audit-and-specification/evidence-story-07.md)
retains the original failed run and successful follow-ups. The
[execution index](test-execution.json) records exact Python references from the
original full run; it deliberately retains its failed kernel reference. The
coverage report consequently does not certify a complete capability.

The web command was `npm --prefix web run check` with clone-local Node 22.23.2.
It passed every web test, so there was no failing subset to compare with the
inherited web-failure list. No second identical web run was needed. Tests used
uv Python 3.14.2; the machine's Python 3.14.6 has a separate broken XML library.
No host Python or Node installation was repaired. The pinned main revision
was fetched again before publication and remained unchanged.

## R. Remaining unknowns

The audit does not assert that every named feature has been exercised by the
owner. Mechanical inventories are broader than the curated semantic records.
Some API handlers accept raw Request payloads; inferred keys do not become
formal request schemas. Lexical test/client matches are candidates. Base SQL
schema extraction does not simulate every historical migration. Source-based
platform classifications do not replace a hardware matrix.

The [scope reconciliation](../internal/philo/source-checklist.md) maps every
preserved brief section to an output owner. It is not sentence-level proof or
ratification of every example from the briefs.

## S. Next engineering actions

1. Complete the owner's first meeting-to-useful-result journey in the separately
   chartered product lane; preserve actual owner observations.
2. Define and test a Gate preview policy that does not mistake truncation for secret removal.
3. Decide and implement the intended backup-before-change and crash-recovery
   contract, with interruption tests. Documentation now describes current limits.
4. Close keyboard, simple-pointer drag alternatives and focus/compact parity
   gaps against the SRS, using existing components and command owners.
5. Replace high-value raw-request API ambiguity with explicit contracts where it
   helps callers, and extend semantic traceability from those handlers.
6. Measure the proposed performance and accessibility criteria before changing
   their status. Productize a native host only after the comparison criteria,
   permissions, packaging and recovery checks are satisfied.

The [delivery roadmap](../internal/philo/DELIVERY_ROADMAP.md) separates these
product changes from this documentation package and gives conditional estimates.
