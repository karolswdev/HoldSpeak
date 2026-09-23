# The graph audit — the one brief (Philo Phase 2)

**Status:** DRAFT, round two. Astra's check of 2026-09-22 (DO-NOT-RATIFY, eight findings) replaced §§1–9 with the texts below; Muad'Dib accepted them (`pm/roadmap/holdspeak-philo/phase-2-the-graph/checks/charter-astra.md`). Both brains run this brief verbatim, twice each: once static (from the tree), once live (from a hub). Ratified when Astra's reply on this text is recorded.

## 0. The roots

The owner, 2026-09-22: "we're actually intended to work 90% of our time on the desk, with beautiful, cohesive interfaces that guide us, and all of this grounded in the ideology of Workbench 2.0+ on steroids." Read everything below through that, and through the Seven Tenets (CONSTITUTION.md). A dead verb is not a plumbing fault; it is a face that stopped guiding. The finding that matters is the one that costs him on a Tuesday.

## 1. Five definitions

- **Edge** — a specific trigger at a production entry point: a user
  gesture, command, timer, protocol message or external response.
  Different triggers may reach the same action.
- **Interface** — the face or protocol contract that receives a trigger
  or presents its result. Record its kind and execution owner.
- **Connection** — the actual wiring between owners. It may stay in
  the browser or cross handlers, services, stores and projections.
  No route, table or receipt is required merely to complete this shape.
- **Action** — the operation reached by a trigger, with its expected
  result, availability conditions and applicable authority rules.
  Consequential operations owe the receipts required by Articles V
  and XI. Article III governs egress.
- **State** — a reachable domain, projection, browser or lifecycle
  condition relevant to an action or presentation contract.

Reuse Phase 1 record IDs. Give each new trigger and state a stable ID.
A label or source line number is evidence, not identity.

## 2. Four questions

1. Does each reachable trigger reach its intended execution owner?
2. Does the owner perform the operation promised by that interface?
3. Can the intended user or consumer observe the correct result,
   progress, refusal or failure at the place the contract specifies?
4. Does each reachable, relevant state have the presentation or
   protocol response its contract requires?

Classify orphan candidates against their declared exposure and lifecycle.
An internal capability need not have a user button. A parked surface is
not an active edge. A local presentation action need not write a table.
Follow execution ownership before calling a registry stub a dead verb.

## 3. The outcome law

A diff is evidence to inspect, not a success criterion.

Before firing a trigger, record its preconditions, expected result,
observation location and bounded completion condition. Observe initial
feedback and terminal outcome separately. A request sent, spinner shown
or receipt created does not prove that the promised result exists.

Compare the relevant DOM text, values and accessibility state; focus and
selection; URL; window visibility, order and geometry; browser storage;
protocol responses; correlated DB rows; and applicable receipts. Scope
observations to the intended object and operation so background activity
cannot make a dead action pass.

An enabled action that promises a change and produces neither that
change nor an intelligible refusal or failure is a finding. A nonzero
diff with the wrong result is also a finding.

An unchanged result can satisfy a read, refresh, already-satisfied
presentation action or idempotent operation. Record the source-backed
contract and prove the response, resulting state or replay identity.
This is not a list of exempt verbs. An unexplained zero diff is
unresolved and cannot pass.

Reads and presentation without effects do not acquire a receipt
requirement through this audit (Article XI.5). Consequential operations
must have their applicable terminal receipts, including refusal,
failure and indeterminate outcomes (Articles V and XI).

## 4. The state atlas

Derive reachable cases from Phase 1 lifecycle and failure-state records,
current producer and transition code, API projections, and frontend
state branches. The database schema alone is not a complete state model.

For each case record: stable ID; source evidence; applicable edge IDs;
preconditions; production setup sequence; fixture and clock settings;
expected transition and presentation; and execution limits. Use reachable
tuples, not a Cartesian product. Record why an excluded combination is
unreachable or not applicable.

The initial atlas must cover:

- Desk projections: attention and receipt, with reachable unseen,
  needs_attention, acknowledged and resolved states; dismissal and
  restoration; producer/source kind; outcome; and valid, absent or
  stale detail targets. Do not use quiet as an attention_state.
- Briefs: absent, loading, generating, load/generation failure,
  generated-empty and populated; reload persistence; item-level
  untouched, acknowledged and deferred states; unavailable people
  sections; and relevant time boundaries.
- Meetings: provisional, recording, finalized, interrupted or failed
  capture; imported input; absent transcript or record-only posture;
  intelligence reserved, queued, running, ready and failure/retry
  branches supported by the producer; retained results after restart.
  Preserve capture, transcription and intelligence as separate axes.
- Engines: missing assignment, missing profile or binding, disabled
  binding, unknown readiness, ready, and supported refusal/failure
  branches. An assignment is not evidence of a reachable provider.
- First value: idle, capture, transcription, retained draft/audio,
  recovery, keep and continue-later outcomes; all accepted failure
  categories in holdspeak/db/onboarding.py::FIRST_VALUE_FAILURES,
  reconciled with web/src/lib/dictationRecovery.ts.
- Desk presentation: selection, focus, visibility, window arrangement,
  reload/reconnect and stale or missing targets where they affect a
  covered job. Include browser-owned state.
- Time: fresh state, next due sweep, next day, week boundary and the
  continuity horizon. Specify the initial instant, timezone and every
  clock source the case depends on.

Mint domain states through their real production entry points and
transitions. Do not inject finished response shapes, projection rows
or face state and call them producer evidence.

Record controlled input and boundary substitutions explicitly. A browser
permission failure is not minted by writing a backend failure receipt.
Where a state cannot be produced within the audit's scope, record it as
unexercised, with the missing mechanism and its cost. Do not manufacture
reachability or claim a clock advance that did not reach the producer.

Exercise each applicable face case at 1440 and 393. Protocol-only cases
have no invented viewport requirement.

## 5. First-use candidates — owner selection pending

The proposed coverage set is:

arrival; SETUP row; Choose an engine; Add an engine; Check;
Use this for summaries; Record; Stop; Import; open the meeting;
Run summary; Desk memory; a receipt's Open; Generate brief;
Generate again; Write a thought; Kept; restart and find the summary;
voice typing (⌥R); Continue later.

These are candidates, not an owner-ratified twenty or twenty sequential
gestures. Arrival and SETUP are observations. Record and Import are
alternative paths. Kept is an outcome.

Use phase-201-one-meeting-result/SITTING-07.md for the established
journey order: the first-use gate, arrival, engine setup, capture or
import, summary, restart/retrieval and voice delivery. Continue later
belongs at the gate. Preserve the checks for planned and actual engine,
summary content and finding the same summary in two moves after restart.

Map every candidate to a job, starting state, trigger, expected result
and source of priority: owner words, sitting evidence or auditor proposal.
Record the owner's selection in story 01. Until then, call this the
proposed set. Do not invent additional steps to preserve the number twenty.

Walk the selected first-use cases first. Use the real LAN engine for
applicable model calls and record its identity and result. A generated
text's existence is not the owner's verdict that it is useful. Report
technical completion and owner usefulness separately.

Use synthetic meeting material that makes summary errors inspectable.
Report which architect-with-reports jobs the chosen cases cover and
which remain outside the walk. This walk does not measure 90% daily use.

## 6. The static pass

From the tree alone, enumerate production entry points and their actual
execution owners. Include registries and their callers; library and raw
controls; submit/change handlers; keyboard, pointer, drag/drop and
context-menu paths; startup and deep links; timers; HTTP/WebSocket/MCP/CLI
contracts; connector inputs; and engine responses. Record active,
conditional, internal, parked and historical exposure separately.

Trace real branches rather than requiring handler → route → service →
table → projection → face for every action. Record broken wiring with
source evidence and the result it prevents.

Start from Phase 1 inventories and their owning curated shards. Reference
existing record IDs and explicit API method/path pairs. Add new semantic
records to the existing metadata ownership structure; do not duplicate
their descriptions in a second capability catalogue.

For each reviewed claim, identify the exact record and field or source
claim. Record verified, contradicted, unresolved or not-applicable, the
revision examined, evidence and limits. Source inspection, executed
behavior and owner observation remain distinct.

Each brain seals its own static graph before its live pass. Neither
reads the other brain's findings until all four pass outputs are sealed.
Shared schema, fixture recipes and rig calibration are preparation,
not shared findings.

## 7. The live pass

Both brains use one versioned scripts/graph_walk.py entry point and the
same validated case and consequence contracts. Trigger adapters may
differ by interface. Shared rig preparation and calibration must finish
before either live pass; the observations remain independent.

Drive each reachable edge/state case from the brain's static graph
through the real production entry point. A timer, tool or CLI command
is not tested by clicking a substitute button. Record missing adapters
and unexercised cases explicitly.

Each run records: source revision and dirty-tree status; frontend build;
brief, atlas and rig versions; hub identity and database path; fixture
hashes; clock settings; engine mode; and unique case/run IDs. Preserve
before/after evidence, initial feedback, terminal outcome and partial
records when a run stops. Keep unrelated scheduler activity identifiable.

Use a fresh isolated HOME and browser profile, with every subprocess
and configured data/config path scoped to the run. Verify resolved
runtime paths before exercising actions. The Playwright browser cache
may be read from /Users/karol/Library/Caches/ms-playwright.

Never access the owner's data or credentials, capture his microphone,
send native keystrokes or change the machine clock. Use the fixture WAV
tests/fixtures/core_path_smoke_16k.wav at the documented input boundary.
Native microphone, hotkey and other-application delivery remain
unverified unless separately observed under the owner's sitting scope.

Outside the selected real-engine cases, replay recorded engine responses
only at the named provider boundary. Keep production parsing, services,
persistence and rendering real. Label replay evidence; it does not prove
provider availability. External effects require a disposable destination
or an explicitly recorded boundary substitute. Otherwise mark the case
unexercised.

For time-dependent cases, name and verify the mechanism controlling each
relevant browser, Python, scheduler and database clock. If no mechanism
exists within scope, record tooling debt rather than claiming the state.

Calibrate the rig against a dead action, a request with no promised
result, a wrong-target result, valid focus/geometry changes, an
unchanged-result contract and an operation that never completes.
None may be classified solely by the presence of a diff.

Run one state at a time on this machine. Give evidence a run-specific
output directory; do not overwrite tracked shots or use blanket restore
loops. Use pipefail for captured command pipelines.

## 8. The graph schema and Phase 1 ownership

docs/generated/graph.json is a generated join over existing Philo
inventories, new edge/state metadata, immutable pass observations and
the council's recorded resolutions. It is not a second source of truth
for capabilities, APIs, components or domain entities.

Story 01 must deliver a machine-validatable schema with these contracts:

- Root: schema_version, generator, source_commit, Phase 1 baseline,
  input paths and hashes, nodes, links, cases, observations,
  claim_reviews, findings and resolutions.
- Nodes: stable id, kind (edge/interface/connection/action/state),
  label, interface or trigger subtype where applicable, Phase 1
  references and source references. A source reference includes
  revision, path, symbol or anchor, line and the claim it supports.
- Phase 1 references: inventory path plus record ID; API references
  use method and path. Keep curated semantics in the existing shards.
- Links: from, to, relation and evidence references. Relations identify
  the actual connection, such as calls, reads, writes, produces or
  renders. Endpoints must resolve.
- Cases: stable id, edge and state IDs, applicability, preconditions,
  setup recipe, the TRIGGER step (fired through its real entry point
  after setup and the before-capture; required when applicable — a
  correction found by the rig, story 01), expected-result predicate,
  observation location and completion bound.
- Observations: unique run/case/brain/pass identity, viewport when
  applicable, runtime provenance, real/replayed boundary mode,
  before/after evidence, observed result and verdict.
- Claim reviews: referenced claim, reviewed revision, verdict,
  supporting evidence and limits.
- Findings and resolutions: stable IDs, affected cases/claims,
  product-defect/doc-drift/tooling-debt bin, owner cost, evidence,
  both brains' positions and the council disposition.

Store repeated observations separately; never overwrite one brain,
viewport or attempt with another. Verdicts distinguish pass, fail,
blocked, not-run and not-applicable. Unresolved is not pass.

Derive orphan views from typed links, declared exposure and applicability.
Keep the supporting reasons and evidence.

The generator consumes both static graphs, both live records, existing
inventories and explicit council resolutions. It must not silently union
contradictory claims. Validation checks IDs, references, evidence,
provenance, case coverage and deterministic output.

--check proves generated consistency. A current-source census comparison
must separately detect new, removed or changed entry points. Saved
observations retain their original revision; regeneration does not turn
old execution evidence into proof of current behavior.

## 9. Reports and the council

Every pass reports:

PASS: static | live
BRAIN: …
SOURCE: revision, dirty-tree status
CONTRACT: brief, schema, atlas and rig versions
RUNTIME: frontend build, hub, database, clock and engine mode, or none
JOBS: expected result; observed result; pass/fail/unverified; evidence
GRAPH: path
COVERAGE: discovered; applicable; exercised; unexercised with reasons
FINDINGS: ID; bin; owner cost; expected/actual; evidence; affected cases
ORPHANS: candidates with exposure, applicability and evidence
UNKNOWN: what could not be verified, why, and its effect on the verdict

Counts describe coverage; they do not substitute for job results.
Seal all four reports before cross-checking them. Preserve original
observations and both brains' replies.

COUNCIL.md starts with one decision page in plain English:

1. Which selected owner jobs work, fail or remain unverified.
2. The recommended next useful result and the smallest Phase 3 scope
   that enables it, with effort estimates and dependencies.
3. Each decision for the owner: the exact question, recommendation,
   alternative, cost or consequence, decisive evidence and dissent.
4. What is deferred and what the owner still cannot do.

Follow with the graph, ranked findings, one reply from each brain and
verbatim open dissents. Link evidence beside each conclusion. Judge the
observed faces against the Seven Tenets, UX-CANON and DESIGN_SYSTEM.
Do not infer 90% daily usability from first-use coverage.

The Phase 3 draft contains no more than ten stories without the scope
stop required by the phase charter. Each story names the owner result,
affected edges/states and the outcome evidence that will close it.
The owner rules dissents and the Phase 3 charter.

Story 07 corrects factual drift in the existing curated metadata and
documents, then regenerates their views. Preserve historical snapshots
and original test results. Correct false descriptions to the current
truth and retain missing product behavior in the findings and its story.
The known-false ceiling is zero; this brief does not authorize raising it.

Park a prior walk only after mapping its callers and assertions to
verified replacements or an explicit council disposition. Extend the
portable Phase 1 skills and maintenance index; tool-specific instructions
link to that shared procedure.
